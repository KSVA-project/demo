from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import asyncio
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_chroma import Chroma
from langchain_community.embeddings.huggingface import HuggingFaceEmbeddings
from pydantic import BaseModel, Field
from datetime import datetime
import logging
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager 
from typing import Dict, Optional
import os
from dotenv import load_dotenv
import uvicorn

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
    userMeta: Dict[str, Optional[str]] # 사용자 메타데이터 필드

# 🌱 lifespan으로 초기화 로직 구현
@asynccontextmanager
async def lifespan(app: FastAPI):
    global chain
    logger.info("🚀 FastAPI 서버 시작 - LangChain 초기화 중...")
    try:
        chain = create_chain()
        logger.info("✅ LangChain 초기화 완료!")
        logger.info(f"✅ 현재 체인 타입: {type(chain)}")
        logger.info(f"✅ 체인 구성: {chain}")
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

        payload = {
            "question": request.message,
            "user_name": request.userMeta.get("name", ""),
            "user_years": request.userMeta.get("years", ""),
            "user_location": request.userMeta.get("location", ""),
            "user_employees": request.userMeta.get("employees", ""),
            "user_sales": request.userMeta.get("sales", "")
        }
        
        logger.info(f"🧪 invoke payload: {payload}")


        # 비동기 실행
        response = await asyncio.to_thread(chain.invoke, payload)
        
        logger.info(f"🔎 response type: {type(response)}", extra={"flush": True})
        logger.info(f"🔎 response raw: {response}", extra={"flush": True})

        # Check if 'metadata' exists in the response 
        # [줄바꿈 가공]
        if isinstance(response, str):
            formatted_response = response.replace("\n\n", "<br><br>").replace("\n", "<br>")
        elif isinstance(response, dict):
            value = response.get("result") or response.get("output") or response.get("text")
            formatted_response = value.replace("\n\n", "<br><br>").replace("\n", "<br>") if isinstance(value, str) else str(response)
        else:
            formatted_response = str(response)
            
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

        # MMR Retriever 적용
        retriever = vectorstore.as_retriever(
            search_type="mmr",              # MMR 기반 유사도 검색
            search_kwargs={
                "k": 10,                    # 전체 후보 문서 수
                "fetch_k": 30,              # 더 많은 후보 중 다양성 고려해 k개 선택
                "lambda_mult": 0.7          # 유사도 vs 다양성 균형 (1.0: 유사도만, 0.0: 다양성만)
            }
        )

        # Define prompt
        prompt = PromptTemplate.from_template(
            """
            You are an AI assistant that recommends suitable government support programs for companies.
            Use the retrieved documents and the following company information to filter and suggest the most relevant support programs.
            If none of the programs match the company's profile, say you couldn't find a suitable one.

            [Company Information]
            - Company Name: {user_name}
            - Business Years: {user_years}
            - Location: {user_location}
            - Number of Employees: {user_employees}
            - Annual Sales Range: {user_sales}

            [User Question]
            {question}

            [Retrieved Support Program Documents]
            {context}

            Answer in Korean.
            """
        )
       
        llm = ChatOpenAI(
            openai_api_key=api_key,
            temperature=0.1,
            model_name="gpt-3.5-turbo",
            request_timeout=10
        )

        logger.info("✅ LangChain components initialized.")

        # Runnable 체인의 조합, | 파이프 연산자를 써서 순차적으로 처리 ->  RunnableSequence
        # 1. Input으로는 전체 dict이 들어와, question 값만 꺼냄
        # 2. retriever: query 문자열을 받아서 chroma 벡터 DB에서 유사한 문서들을 검색 -> 결과는 List[Document] 객체
        # 3. RunnableLambda(lambda docs: "\n\n".join([doc.page_content for doc in docs]))
        #    retriever의 검색된 문서리스트 doc가 하나로 합쳐짐
        
        # 최종 전체 dict 입력 -> "question"만 추출 (query string) -> Chroma에서 관련 문서 검색
        # -> 문서 내용만 꺼내서 하나로 합침 -> PromptTemplate에 전달될 context가 됨
        chain = (
            {
                "context": RunnableLambda(lambda x: x["question"]) 
                | retriever 
                | RunnableLambda(lambda docs: "\n\n".join([doc.page_content for doc in docs])),
                "question": RunnablePassthrough(),
                "user_name": RunnablePassthrough(),
                "user_years": RunnablePassthrough(),
                "user_location": RunnablePassthrough(),
                "user_employees": RunnablePassthrough(),
                "user_sales": RunnablePassthrough(),
            }
            | prompt
            | llm
            | StrOutputParser()
        )

        logger.info("🚀 LangChain RAG chain created successfully.")

        return chain

    except Exception as e:
        logger.error(f"❌ Error creating LangChain chain with RAG: {e}")
        raise RuntimeError("Failed to create LangChain chain with RAG")


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8002, reload=True)