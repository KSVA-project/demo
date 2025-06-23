# MMR Retriever 적용
# 임베딩 모델 : OpenAIEmbeddings

# ✅ FastAPI 관련
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
import uvicorn

# ✅ LangChain - 핵심 체인 구성 요소
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser

# ✅ LangChain - 모델 및 벡터스토어
from langchain_community.chat_models import ChatOpenAI
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# ✅ Python 기본 라이브러리
from datetime import datetime
from typing import Dict, Optional, List
import asyncio
import logging
import os
import json

# ✅ APScheduler 추가
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# ✅ 크롤링 및 벡터 DB 저장 - 작업 스케줄링
from crawling import run_crawling
from service import run_service

# ✅ 환경 변수 로드
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LangChain 체인 (전역 변수)
chain = None
classifier_chain = None

# 요청 데이터 모델
class ChatRequest(BaseModel):
    message: str
    croomIdx: int
    chatter: str
    ratings: str = Field(default="5")
    createdAt: datetime = Field(default_factory=datetime.now)
    userMeta: Dict[str, Optional[str]] # 사용자 메타데이터 필드
    userTypes: List[str] = Field(default=[]) # 추가: 기업 유형 리스트


def scheduled_job():
    logger.info("🕒 APScheduler: run_crawling + run_service 실행 시작")
    try:
        run_crawling()
        run_service()
        logger.info("✅ APScheduler: 작업 완료")
    except Exception as e:
        logger.error(f"❌ APScheduler: 작업 실패 - {e}")

# 🌱 lifespan으로 초기화 로직 구현
@asynccontextmanager
async def lifespan(app: FastAPI):
    global chain
    global classifier_chain
    logger.info("🚀 FastAPI 서버 시작 - LangChain 초기화 중...")
    
    try:
        chain = create_chain()
        logger.info("✅ LangChain 초기화 완료!")
        logger.info(f"✅ 현재 체인 타입: {type(chain)}")
        logger.info(f"✅ 체인 구성: {chain}")
        classifier_chain = classifier_chain()
        logger.info("✅ classifier_chain 초기화 완료!")
        logger.info(f"✅ 현재 체인 타입: {type(classifier_chain)}")
        
    except Exception as e:
        logger.error(f"❌ LangChain 초기화 실패: {e}")
        chain = None
    
    # ✅ APScheduler 작업 시작
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        scheduled_job, 
        CronTrigger(hour=20, minute=20, timezone="Asia/Seoul")
    )
    scheduler.start()
    logger.info("🔄 APScheduler 시작 - 매일 20:20 실행")
    
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
            "user_sales": request.userMeta.get("sales", ""),
            "user_industry": request.userMeta.get("industry", ""),      # 업종 
            "user_types": ", ".join(request.userTypes) 
        }
        
        logger.info(f"🧪 invoke payload: {payload}")

        # Step 1: 질문 분류
        mode = await asyncio.to_thread(classifier_chain.invoke, {"question": request.message})
        mode = mode.strip().lower()
        payload["mode"] = mode
        logger.info(f"🧠 분류된 모드: {mode}")
        
        # 비동기 실행
        response = await asyncio.to_thread(chain.invoke, payload)
        
        logger.info(f"🔎 response type: {type(response)}", extra={"flush": True})
        logger.info(f"🔎 response raw: {response}", extra={"flush": True})
        
        # 반환 형태가 복잡한 체인일수록 dict로 응답
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
            model_kwargs={'device': 'cpu'},  # GPU 사용 시 'cuda'로 변경
            encode_kwargs={'normalize_embeddings': True},
        )
        logger.info("✅ Embeddings model initialized.")

        # Initialize ChromaDB
        logger.info("🔍 Loading ChromaDB...")
        vectorstore = Chroma(
            persist_directory="./chroma_db",  # 디스크 기반 저장소 사용
            embedding_function=embeddings_model,
            collection_metadata={
            "hnsw:space": "cosine",             # 자연어 유사도 측정에 가장 적합
            "hnsw:construction_ef": 400,        # 인덱스 품질 ↑ (기본 200 → 400)
            "hnsw:M": 32,                       # 연결 수 증가 → 검색 품질 향상 (기본 16)
            "hnsw:search_ef": 128,              # 검색 시 정확도 증가 (기본 10~100)
            "hnsw:num_threads": 4,              # 멀티스레드 인덱싱 (CPU 성능에 맞게 조절)
            "hnsw:batch_size": 64               # 벡터 삽입 속도 향상 (대용량 처리 시)
            }
        )
        
        logger.info("✅ ChromaDB loaded successfully.")

        # MMR Retriever 적용
        retriever = vectorstore.as_retriever(
            search_type="mmr",              # MMR 기반 유사도 검색
            search_kwargs={
                "k": 8,                    # 전체 후보 문서 수
                "fetch_k": 20,              # 더 많은 후보 중 다양성 고려해 k개 선택
                "lambda_mult": 0.3          # 유사도 70%, 다양성 30% 반영 (1.0: 유사도만, 0.0: 다양성만)
            }
        )

        # Define prompt
        prompt = PromptTemplate.from_template(
            """
            You are an AI assistant that supports government program analysis for companies.
            The user's intent has been classified as: {mode}
            
            If the mode is `recommend`, follow these instructions:

            - Recommend the most relevant government support programs for the company using the retrieved documents and the company's profile.
            - Use the following metadata fields (if present) to construct complete Korean sentences:
            - Program Name (pblancNm)
            - Application Period (reqstBeginEndDe)
            - Business Overview Contents (bsnsSumryCn)
            - Target Audience (trgetNm)
            - Program URL (pblancUrl)
            - Include key details from `page_content` such as eligibility, scope, funding, or specific support terms.
            - Do not skip any available metadata fields. Write them out in full sentences.
            - If no relevant programs are found, say so clearly. Otherwise, do not mention this.
            - At the end of each program, show the full URL prefixed with 👉. If `pblancUrl` is a relative path (e.g., starts with `/web/...`), prepend `https://www.bizinfo.go.kr`.

            If the mode is `summarize`, follow these instructions:

            - Provide a summary of the support programs found in the documents, regardless of company information.
            - Focus on condensing the key content from `page_content`, including funding, purpose, and eligibility.
            - Do not include user metadata or match recommendations.
            - You must include all available metadata fields (pblancNm, reqstBeginEndDe, bsnsSumryCn, trgetNm, pblancUrl) in full Korean sentences.
            - End each program's summary with the full link prefixed by 👉, converting relative URLs as noted.

            ---

            [Company Information]
            - Company Name: {user_name}
            - Business Years: {user_years}
            - Location: {user_location}
            - Number of Employees: {user_employees}
            - Annual Sales Range: {user_sales}
            - Business Industry: {user_industry}
            - Company Types: {user_types}    
            
            [User Question]
            {question}

            [Retrieved Support Program Documents]
            {context}

            Respond in Korean.
            """
        )
       
        llm = ChatOpenAI(
            openai_api_key=api_key,
            temperature=0.1,
            model_name="gpt-3.5-turbo",
            request_timeout=20,
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
                | RunnableLambda(lambda docs: "\n\n".join([
                    f"[📄 Metadata]\n{json.dumps({k: v for k, v in doc.metadata.items() if k!='file_hash'}, ensure_ascii=False, indent=2)}\n📑 Content:\n{doc.page_content}"
                    for doc in docs
                ])),
                "question": RunnablePassthrough(),
                "user_name": RunnablePassthrough(),
                "user_years": RunnablePassthrough(),
                "user_location": RunnablePassthrough(),
                "user_employees": RunnablePassthrough(),
                "user_sales": RunnablePassthrough(),
                "user_industry": RunnablePassthrough(),   
                "user_types": RunnablePassthrough(),
                "mode": RunnablePassthrough(),
            }
            | prompt
            | llm
            | StrOutputParser()
        )

        # RunnableLambda는 **MMR retriever가 반환한 문서들(List[Document])**
        # json.dumps(..., ensure_ascii=False, indent=2) : meta를 json 문자열로 반환
        # indent=2는 보기 좋게 들여쓰기

        logger.info("🚀 LangChain RAG chain created successfully.")

        return chain

    except Exception as e:
        logger.error(f"❌ Error creating LangChain chain with RAG: {e}")
        raise RuntimeError("Failed to create LangChain chain with RAG")


## 분류 체인
def classifier_chain() :
    
    classification_prompt = PromptTemplate.from_template(
    """
    다음 사용자의 질문을 읽고 아래 중 하나를 정확히 선택하세요:

    - recommend: 우리 회사에 적합한 정부 지원사업을 추천해달라는 질문인 경우
    - summarize: 특정 지원사업의 내용을 요약해달라는 질문인 경우

    반드시 위 단어 중 하나만 출력하세요. 그 외 문장이나 설명 없이 `recommend` 또는 `summarize` 중 하나로만 응답해야 합니다.

    [질문]
    {question}
    """)
            # 모델 인스턴스
    llm = ChatOpenAI(
        openai_api_key=api_key,
        temperature=0.0,  # 분류용은 변동성 제거!
        model_name="gpt-3.5-turbo"
    )

    # 분류 체인
    classifier_chain = classification_prompt | llm | StrOutputParser()
    
    return classifier_chain


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8002, reload=True)