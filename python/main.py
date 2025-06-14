from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import asyncio
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_chroma import Chroma
from langchain_community.embeddings.huggingface import HuggingFaceEmbeddings
from pydantic import BaseModel, Field
from datetime import datetime
import logging
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager 

import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LangChain 체인 (전역 변수)
chain = None

# 요청 데이터 모델
class ChatRequest(BaseModel):
    message: str
    croomIdx: int
    chatter: str
    ratings: str = Field(default="5")
    createdAt: datetime = Field(default_factory=datetime.now) 

# 🌱 lifespan으로 초기화 로직 구현
@asynccontextmanager
async def lifespan(app: FastAPI):
    global chain
    logger.info("🚀 FastAPI 서버 시작 - LangChain 초기화 중...")
    try:
        chain = create_chain()
        logger.info("✅ LangChain 초기화 완료!")
    except Exception as e:
        logger.error(f"❌ LangChain 초기화 실패: {e}")
        chain = None
    yield
    logger.info("🛑 FastAPI 서버 종료...")


# 🏁 FastAPI 인스턴스
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용 (필요 시 특정 도메인만 허용)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat(request: ChatRequest):
    """LangChain을 사용한 문서 기반 검색 + 답변 생성"""
    global chain
    if chain is None:
        raise HTTPException(status_code=500, detail="LangChain이 초기화되지 않았습니다.")

    try:
        logger.info(f"📥 요청 수신: {request.message}")

        # 비동기 실행
        response = await asyncio.to_thread(chain.invoke, request.message)

        # Check if 'metadata' exists in the response
        response_text = response.content  # 'AIMessage' 객체에서 content 속성 추출
        

        # 이제 텍스트에서 줄 바꿈을 처리
        formatted_response = response_text.replace("\n", "<br>")

        return {
            "response": formatted_response,
            "croomIdx": request.croomIdx,
            "chatter": request.chatter,
            "ratings": request.ratings,
            "createdAt": request.createdAt
        }

    except Exception as e:
        logger.error(f"❌ 채팅 처리 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def custom_retriever(query):
    # retriever에서 검색 결과를 가져오기
    results = retriever._retrieve(query)  # type: ignore # _retrieve() 메서드 사용

    documents_with_titles = []
    for result in results:
        # 문서 제목을 메타데이터에서 가져오기
        doc_title = result.metadata.get("title", "No Title Available")  # 'title'이 없으면 기본값을 'No Title Available'로 설정
        documents_with_titles.append({
            "title": doc_title,
            "content": result.content
        })

    return documents_with_titles

def create_chain():
    """Create and return the LangChain chain with RAG, including document title."""
    try:
        # Initialize embeddings model
        embeddings_model = HuggingFaceEmbeddings(
            model_name='jhgan/ko-sroberta-nli',
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True},
        )
        logger.info("✅ Embeddings model initialized.")

        # Initialize ChromaDB
        logger.info("🔍 Loading ChromaDB...")
        vectorstore = Chroma(
            persist_directory="./chroma_db",  # 디스크 기반 저장소 사용
            embedding_function=embeddings_model,
            collection_metadata={"hnsw:space": "cosine"},
        )
        logger.info("✅ ChromaDB loaded successfully.")

        retriever = vectorstore.as_retriever()

        # Define prompt
        prompt = PromptTemplate.from_template(
        """
        You are an assistant for question-answering tasks.
        Use the following pieces of retrieved context to answer the question.
        If you don't know the answer, just say that you don't know.
        Please answer the question in Korean.


        #Question:
        {question}

        #Context:
        {context}

        #title:
        {title}

        #Answer:
        """
        )
       
        llm = ChatOpenAI(
            openai_api_key=api_key,
            temperature=0.1,
            model_name="gpt-3.5-turbo",
            request_timeout=10
        )

        logger.info("✅ LangChain components initialized.")

        chain = (
            {"context": retriever, "question": RunnablePassthrough(), "title": retriever}
            | prompt
            | llm
        )

        logger.info("🚀 LangChain RAG chain created successfully.")

        # Assign custom retriever to the retriever's _retrieve method
        retriever._retrieve = custom_retriever

        return chain

    except Exception as e:
        logger.error(f"❌ Error creating LangChain chain with RAG: {e}")
        raise RuntimeError("Failed to create LangChain chain with RAG")
