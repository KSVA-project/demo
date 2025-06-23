# MMR Retriever 적용
# 임베딩 모델 : HuggingFaceEmbeddings

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

# device 확인
import torch
def get_device():
    """GPU 사용 가능 여부를 확인하고 적절한 device 반환"""
    if torch.cuda.is_available():
        device = 'cuda'
        gpu_count = torch.cuda.device_count()
        gpu_name = torch.cuda.get_device_name(0)
        print(f"✅ GPU 사용 가능: {gpu_name} ({gpu_count}개)")
    else:
        device = 'cpu'
        print("⚠️ GPU 불가능, CPU 사용")
    return device

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LangChain 체인 (전역 변수)
chain = None
classifier_chain_instance = None 

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
    global classifier_chain_instance
    logger.info("🚀 FastAPI 서버 시작 - LangChain 초기화 중...")
    
    try:
        chain = create_chain()
        logger.info("✅ LangChain 초기화 완료!")
        logger.info(f"✅ 현재 체인 타입: {type(chain)}")
        
        classifier_chain_instance = create_classifier_chain()  # ❌ 수정: 함수명 변경
        logger.info("✅ classifier_chain 초기화 완료!")
        logger.info(f"✅ 현재 분류 체인 타입: {type(classifier_chain_instance)}")
        
    except Exception as e:
        logger.error(f"❌ LangChain 초기화 실패: {e}")
        chain = None
        classifier_chain_instance = None
    
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

# 체인에서 사용자 정보 검증 함수
def validate_user_info(user_meta):
    """사용자 정보가 충분한지 검증"""
    required_fields = ["name", "industry", "employees", "location"]
    missing_fields = [field for field in required_fields if not user_meta.get(field)]
    
    if missing_fields:
        logger.warning(f"⚠️ 누락된 사용자 정보: {missing_fields}")
        return False, missing_fields
    return True, []

@app.post("/chat")
async def chat(request: ChatRequest):
    """LangChain을 사용한 문서 기반 검색 + 답변 생성"""
    global chain, classifier_chain_instance
    
    if chain is None or classifier_chain_instance is None:
        raise HTTPException(status_code=500, detail="LangChain이 초기화되지 않았습니다.")

    try:
        logger.info(f"📥 요청 수신: {request.message}")
        logger.info(f"🏢 회사 정보: {request.userMeta}")
        logger.info(f"🎯 기업 유형: {request.userTypes}")

        # ✅ 추가: 사용자 정보 검증
        is_valid, missing_fields = validate_user_info(request.userMeta)
        if not is_valid:
            return {
                "response": f"더 정확한 추천을 위해 다음 정보를 추가로 입력해주세요: {', '.join(missing_fields)}",
                "missing_fields": missing_fields,
                "croomIdx": request.croomIdx,
                "chatter": request.chatter,
                "ratings": request.ratings,
                "createdAt": request.createdAt
            }

        # Step 1: 질문 분류
        mode = await asyncio.to_thread(classifier_chain_instance.invoke, {"question": request.message})
        mode = mode.strip().lower()
        logger.info(f"🧠 분류된 모드: {mode}")

        payload = {
            "question": request.message,
            "user_name": request.userMeta.get("name", ""),
            "user_years": request.userMeta.get("years", ""),
            "user_location": request.userMeta.get("location", ""),
            "user_employees": request.userMeta.get("employees", ""),
            "user_sales": request.userMeta.get("sales", ""),
            "user_industry": request.userMeta.get("industry", ""),
            "user_types": ", ".join(request.userTypes),
            "mode": mode
        }
        
        logger.info(f"🧪 invoke payload: {payload}")
        
        # 비동기 실행
        response = await asyncio.to_thread(chain.invoke, payload)
        
        logger.info(f"🔎 response type: {type(response)}")
        logger.info(f"🔎 response raw: {response}")
        
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
        device = get_device()
        
        # Initialize embeddings model
        embeddings_model = HuggingFaceEmbeddings(
            model_name='jhgan/ko-sroberta-nli',
            model_kwargs={'device': device},  # GPU 사용 시 'cuda'로 변경
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

        # 모드별 세부 지침을 동적으로 생성하는 함수 - 자세한 정보 제공 버전
        def get_mode_instructions(mode_value):
            if mode_value == "recommend":
                return """
                🎯 추천 모드 수행사항:
                
                1. 회사 프로필 분석부터 시작:
                   - 해당 기업의 특성을 명시적으로 언급하고 분석
                   - 해당 기업의 업종과 규모에 특화된 지원사업 필요성 분석
                   - 기업의 성장 단계와 현재 상황에 맞는 지원 필요성 설명
                
                2. 맞춤 추천 제공:
                   - 검색된 각 지원사업이 이 회사에 왜 적합한지 구체적 매칭 근거 제시
                   - 기업 규모, 연매출, 업종과의 연관성 상세 설명
                   - 지역 기반 지원사업이 있다면 우선 추천하고 지역적 장점 설명
                   - 신청 가능성과 경쟁률, 선정 가능성까지 고려한 추천
                
                3. 각 프로그램별 상세 정보 (반드시 모든 항목을 자세히 설명):
                   - 사업명 (pblancNm): "[사업명]" - 사업의 목적과 배경까지 설명
                   - 📅 신청기간 (reqstBeginEndDe): "[기간]" - 신청 마감일까지 남은 시간과 준비 기간 안내
                   - 📋 사업개요 (bsnsSumryCn): 
                     * 사업의 전체적인 목표와 방향성
                     * 지원 내용의 구체적인 범위와 한계
                     * 예상되는 성과와 기대 효과
                     * 사업 참여 시 얻을 수 있는 혜택들을 구체적으로 나열
                   - 🎯 대상 (trgetNm): "[대상]" - 우리 회사가 해당 대상에 포함되는 이유와 자격 요건 분석
                   -  지원 규모: 문서에서 찾을 수 있는 지원금액, 지원 비율, 지원 방식 등 상세 정보
                   -  신청 절차: 필요한 서류, 심사 과정, 선정 기준 등 실무적 정보
                   -  주의사항: 신청 시 유의할 점, 제외 대상, 의무사항 등
                   -  링크* [전체URL]
                
                4. 우선순위 정렬 및 상세 분석:
                   - 가장 적합한 프로그램부터 순서대로 제시
                   - 각각에 대해 이 회사에 적합한 이유를 구체적으로 설명
                   - 신청 난이도와 성공 가능성 평가
                   - 동시 신청 가능한 프로그램들의 조합 제안
                """
            else:  # summarize
                return """
                📊 요약 모드 수행사항:
                
                1. 회사 맥락에서의 상세 요약:
                   - 일반적 요약이 아닌, 해당 업종 기업 관점에서 상세 요약
                   - 해당 규모 기업이 활용할 수 있는 모든 관점과 가능성 분석
                   - 비슷한 규모/업종 기업의 활용 사례나 성공 패턴 언급 (문서에 있다면)
                
                2. 핵심 정보 상세 구조화:
                   -  **사업명 (pblancNm)**: "[사업명]" - 사업명의 의미와 배경 설명
                   -  **신청기간 (reqstBeginEndDe)**: "[기간]" - 신청 일정과 관련 중요 날짜들
                   -  **사업개요 (bsnsSumryCn)**: 
                     * 사업의 전체 목표와 추진 배경
                     * 지원 내용의 상세 범위 (자금지원, 멘토링, 교육, 네트워킹 등)
                     * 사업 기간과 단계별 진행 과정
                     * 참여 기업이 얻게 되는 구체적 혜택들
                     * 의무사항과 조건들
                   -  대상 (trgetNm): "[대상]" - 대상 조건의 상세 분석과 우리 회사 적합성
                   -  지원 조건: 지원금액, 지원 비율, 매칭펀드 여부 등 재정적 조건
                   -  신청 요건: 필요 서류, 자격 조건, 제출 방법 등
                   -  심사 기준: 평가 항목, 가점 요소, 우대 조건 등
                   -  링크: [전체URL]
                
                3. 실용적 상세 분석:
                   - 지원 규모, 조건, 절차 등 모든 핵심 실무 정보
                   - 이 회사가 지원 가능한지 여부를 판단할 수 있는 모든 정보 제공
                   - 신청 전 준비해야 할 사항들과 소요 시간 예상
                   - 선정 후 진행 과정과 기대할 수 있는 결과물
                   - 다른 지원사업과의 중복 지원 가능 여부
                """

        # 개선된 프롬프트 - 사용자 정보 활용 강화
         # 개선된 프롬프트 - 더욱 자세한 정보 제공
        prompt = PromptTemplate.from_template(
            """
            당신은 정부지원사업 전문 AI 컨설턴트입니다. 
            사용자의 질문 유형: {mode}
            
            반드시 아래 회사 정보를 상세히 분석하여 답변하세요:
            
            🏢 분석할 회사 정보
            - 회사명: {user_name}
            - 사업 연수: {user_years}년 ← 이 업종을 반드시 고려하세요!
            - 소재지: {user_location}   ← 이 소재지을 반드시 고려하세요!
            - 직원 수: {user_employees}명
            - 연매출 규모: {user_sales}
            - 업종: {user_industry}
            - 기업 유형: {user_types}
            
            📋 사용자 질문
            {question}

            ---
            
            '{mode}' 모드 수행 지침:
            
            {mode_instructions}
            
            📑 검색된 정부지원사업 문서:
            {context}
            
            ⚠️ 중요 지침 (자세한 정보 제공):
            1. 반드시 위 회사 정보를 기반으로 맞춤형 분석을 제공하되, 모든 정보를 상세히 설명하세요
            2. 회사의 업종, 규모, 지역을 고려한 구체적 매칭 이유를 자세히 설명하세요
            3. 일반적인 답변이 아닌, 해당 기업만을 위한 특화된 상세 답변을 하세요
            4. 메타데이터의 모든 필드를 한국어로 완전한 문장으로 작성하되, 단순 나열이 아닌 설명형으로 작성하세요
            5. 사업개요(bsnsSumryCn)는 특히 자세히 풀어서 설명하고, 실무진이 이해하기 쉽게 구체적으로 작성하세요
            6. 지원 조건, 신청 방법, 심사 기준 등 실무에 필요한 모든 정보를 포함하세요
            7. URL은 👉 마크와 함께 제공하고, 상대경로는 https://www.bizinfo.go.kr를 앞에 붙이세요
            8. 각 지원사업에 대해 "왜 이 회사에 도움이 되는지"를 구체적으로 설명하세요
            9. 신청 시 예상되는 경쟁률이나 선정 가능성도 언급하세요 (문서에 정보가 있다면)
            10. 절대로 정보를 축약하거나 생략하지 말고, 문서에 있는 모든 유용한 정보를 포함하세요
            
            한국어로 자세하고 상세하게 답변하세요.
            """
        )

        llm = ChatOpenAI(
            openai_api_key=api_key,
            temperature=0.0,
            model_name="gpt-3.5-turbo",
            request_timeout=30,
            max_tokens=2000,
        )

        logger.info("✅ LangChain components initialized.")

        # 체인 구성 시 모드별 지침을 동적으로 삽입
        chain = (
            {
                "context": RunnableLambda(lambda x: x["question"]) 
                | retriever 
                | RunnableLambda(lambda docs: "\n\n".join([
                    f"📄 **문서 {i+1}**\n"
                    f"📋 **메타데이터:**\n{json.dumps({k: v for k, v in doc.metadata.items() if k!='file_hash'}, ensure_ascii=False, indent=2)}\n\n"
                    f"📑 **내용:**\n{doc.page_content}\n"
                    f"{'='*50}"
                    for i, doc in enumerate(docs)
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
                "mode_instructions": RunnableLambda(lambda x: get_mode_instructions(x.get("mode", "recommend")))
            }
            | prompt
            | llm
            | StrOutputParser()
        )

        logger.info("🚀 개선된 LangChain RAG chain 생성 완료")
        return chain

    except Exception as e:
        logger.error(f"❌ Error creating improved LangChain chain: {e}")
        raise RuntimeError("Failed to create improved LangChain chain")


# 개선된 분류 체인
def create_classifier_chain():  # ❌ 수정: 함수명 변경
    classification_prompt = PromptTemplate.from_template(
        """
        다음 사용자 질문을 분석하여 정확한 모드를 선택하세요.
        
        **분류 기준:**
        - `recommend`: 
          * "추천해주세요", "적합한", "우리 회사에", "맞는", "찾아주세요" 등의 표현
          * 회사 상황에 맞는 지원사업을 찾아달라는 요청
          * 예: "우리 회사에 맞는 정부지원사업 추천해주세요"
          
        - `summarize`:
          * "요약해주세요", "정리해주세요", "설명해주세요", "알려주세요" 등의 표현
          * 특정 프로그램이나 일반적인 정보의 요약을 원하는 요청
          * 예: "창업지원사업에 대해 설명해주세요"

        **중요:** 아래 단어 중 하나만 정확히 출력하세요.
        - recommend
        - summarize

        질문: {question}
        
        답변:"""
    )
    
    llm = ChatOpenAI(
        openai_api_key=api_key,
        temperature=0.0,
        model_name="gpt-3.5-turbo"
    )

    return classification_prompt | llm | StrOutputParser()


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8002, reload=True)