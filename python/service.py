# google-vision OCR
# splitter: RecursiveCharacterTextSplitter : 문단-> 줄 -> 문장 -> 단어 재귀적으로 나눔
# 임베딩 모델 : ko-sroberta-nli 기반 HuggingFace
# vectorstor : chromadb, 코사인 유사도 사용

import fitz  # PyMuPDF
import pandas as pd
from langchain.schema import Document
from tabulate import tabulate
import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from chromadb import PersistentClient
from dotenv import load_dotenv
from collections import defaultdict 
import io
from pdf2image import convert_from_path
from google.cloud import vision
import hashlib

# ✅ 기업마당 API 정보
from api_data import get_bizinfo_data_by_hashtags, filter_matched_bizinfo

# ✅ 환경 변수 로드 (OpenAI 키 등)
load_dotenv()

gcp_key = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Google Cloud Vision 클라이언트 생성
client = vision.ImageAnnotatorClient()

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


# 임베딩 모델 로드
def load_embeddings_model():
    """ko-sroberta-nli 기반 HuggingFace 임베딩 모델 불러오기"""
    device = get_device()
    return HuggingFaceEmbeddings(
        model_name='jhgan/ko-sroberta-nli',
        model_kwargs={'device': device},  # GPU 사용 시 'cuda'로 변경
        encode_kwargs={'normalize_embeddings': True},
    )

# ✅ txt 해시 생성 함수, 계산
def get_pdf_hash(pdf_path):
    with open(pdf_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

# ✅ OCR 캐시 폴더
CACHE_DIR = "./ocr_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# ✅ Google Vision OCR로 PDF 텍스트 추출, txt로 저장
def extract_text_from_pdf(pdf_path, existing_hashes=None):
    
    file_hash = get_pdf_hash(pdf_path)
    file_name = os.path.splitext(os.path.basename(pdf_path))[0]
    cache_path = os.path.join(CACHE_DIR, f"{file_name}.txt")
    
    # 1. 캐시된 OCR 결과 있으면 바로 로드
    if os.path.exists(cache_path):
        print(f"⏩ OCR 캐시 불러옴: {file_name}")
        with open(cache_path, "r", encoding="utf-8") as f:
            text_by_page = f.read().split("\f")
        return text_by_page, file_hash, file_name
    
    print(f"🔍 OCR 수행: {pdf_path}")
    text_by_page = []
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    
    for i in range(total_pages):
        
        # [1] PDF 페이지를 이미지로 변환
        images = convert_from_path(pdf_path, dpi=300, first_page=i+1, last_page=i+1)
        image = images[0]
        
        # [2] 이미지 메모리로 저장 (파일 저장 없이)
        img_byte_arr = io.BytesIO() # 변환된 PIL 이미지 객체를 메모리 내 바이트 배열(BytesIO)로 저장
        image.save(img_byte_arr, format='PNG') # 파일로 디스크에 저장하지 않고 바로 메모리에서 Vision API에 넘기기 위한 준비
        img_byte_arr = img_byte_arr.getvalue() # PNG 포맷으로 저장 후 getvalue()로 실제 바이트 데이터 추출
    
        # [3] Vision API로 OCR 요청
        image_for_vision = vision.Image(content=img_byte_arr)
        response = client.text_detection(image=image_for_vision)
        texts = response.text_annotations
        
        if texts:
            text_by_page.append(texts[0].description.strip())
        else:
            text_by_page.append("")

    # OCR 결과 저장
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write("\f".join(text_by_page)) 
        # 폼 피드 (form feed) 문자, 페이지 구분자로 사용
        # text_by_page == 각 페이지의 OCR 결과 텍스트가 담긴 리스트
        
    return text_by_page, file_hash, file_name

# OCR된 text_by_page를 split documents로 반환
def split_text_to_documents(text_by_page, file_hash, file_name, matched_df=None):
    """
    OCR된 텍스트를 문서로 분할하고 메타데이터를 추가합니다.
    
    Args:
        text_by_page: 페이지별 OCR 텍스트 리스트
        file_hash: 파일 해시값
        file_name: 확장자 제거된 파일명
        matched_df: API에서 가져온 매칭된 메타데이터 DataFrame
        
    Returns:
        tuple: (split_documents, file_hash) 또는 (None, None)
    """
    
    documents = []
    meta_row = None # 해당 PDF 파일명에 해당하는 메타데이터 행 추출
    
    # 해당 파일명에 맞는 메타데이터 찾기
    if matched_df is not None and not matched_df.empty:
        # 정확한 매칭 확인
        match = matched_df[matched_df["pblancNm"] == file_name]
        
        if not match.empty:
            meta_row = match.iloc[0].to_dict()
            print(f"✔️ 메타데이터 매칭 성공: {file_name}")
        else:
            print(f"⚠️ 메타데이터 매칭 실패: {file_name}")
            # 디버깅을 위해 사용 가능한 공고명들 출력
            available_names = matched_df["pblancNm"].tolist()
            print(f"[DEBUG] 사용 가능한 공고명: {available_names[:5]}")

    # 각 페이지별로 문서 생성
    for i, text in enumerate(text_by_page):
        
        # 빈 페이지는 건너뛰기
        if not text.strip():
            continue
        
        page_num = i + 1
        
        # 기본 메타데이터
        metadata = {
            "page": page_num, 
            "pblancNm": file_name, 
            "file_hash": file_hash
        }
        
        # API 메타데이터 추가
        if meta_row:
            # 기본 메타데이터를 먼저 설정하고, API 데이터로 업데이트
            metadata.update(meta_row)
            # pblancNm은 파일명으로 유지 (API 데이터로 덮어쓰지 않음)
            metadata["pblancNm"] = file_name

        doc = Document(
            page_content=text,
            metadata=metadata
        )
        documents.append(doc)

    if not documents:
        print(f"⚠️ 추출된 문서 없음: {file_name}")
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,     # 한 조각 최대 토큰 수
        chunk_overlap=150,   # 앞뒤로 겹치는 토큰 수 (문맥 유지용)
        separators=["\n\n", "\n", ".", " ", ""],  # 문단 → 줄 → 문장 → 단어 → 문자
        )
    
    split_documents = splitter.split_documents(documents)

    if not split_documents:
        print(f"⚠️ 분할된 문서 없음: {file_name}")
        return

    return split_documents, file_hash

# 🔍 모든 PDF 폴더 처리 및 하나의 chromaDB에 저장
def process_cached_txt_files(root_dir="./data", chroma_root="./chroma_db"):
    
    embeddings_model = load_embeddings_model()

    # 기업마당 메타데이터 matched_df 불러오기
    api_data = get_bizinfo_data_by_hashtags()
    
    if not api_data:
        print("⚠️ API 데이터를 가져올 수 없습니다. 메타데이터 없이 진행합니다.")
        matched_df = None
    else:
        print("🔍 로컬 파일과 매칭 중...")
        matched_df = filter_matched_bizinfo(api_data, folder_path=root_dir)
        
        if matched_df.empty:
            print("⚠️ 매칭되는 파일이 없습니다. 메타데이터 없이 진행합니다.")
            matched_df = None
        else:
            print(f"✔️ {len(matched_df)}개 파일의 메타데이터를 찾았습니다.")

    # ChromaDB 초기화
    # PersistentClient: ChromaDB를 디스크에 지속적으로 저장하기 위한 클라이언트
    client = PersistentClient(path=chroma_root)
    vectorstore = Chroma(
        persist_directory="./chroma_db", # ChromaDB 벡터 데이터를 디스크에 영구 저장할 디렉토리 경로
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
    
    # ✅ Chroma: 벡터 임베딩을 저장/조회할 수 있는 LangChain vectorstore
    # - client: 디스크 기반 저장을 위한 PersistentClient 객체
    # - embedding_function: 텍스트 임베딩에 사용할 모델
    # - collection_metadata: 검색에 사용할 거리 함수(hnsw:space) 지정
    
    # 기존 벡터 중복 제거
    # 기존에 저장된 해시 로딩
    existing = vectorstore.get(include=["metadatas"])
    existing_hashes = {
        meta["file_hash"]
        for meta in existing["metadatas"]
        if meta and "file_hash" in meta
    }
    # if meta and "file_hash" in meta ->  meta가 None이 아니고, "file_hash"라는 키를 퐇함하고 있을 경우에만 실행
    
    all_documents = []
    
    for dirpath, _, filenames in os.walk(root_dir):
    # dirpath: 현재 폴더 경로 / _ : 이 변수는 사용 안할꺼라고 선언 / filenames: 파일 리스트  
        
        for filename in filenames:
            
            # PDF 만 처리
            if not filename.lower().endswith(".pdf"):
                continue
            
            pdf_path = os.path.join(dirpath, filename)
            
            try:
                # Step 1: OCR + 캐시 로딩 또는 수행
                text_by_page, file_hash, file_name = extract_text_from_pdf(pdf_path, existing_hashes)
                
                # 벡터화된 파일이면 건너뜀
                if file_hash in existing_hashes:
                    print(f"⏩ 이미 벡터화 완료된 파일입니다. 건너뜀: {file_name}")
                    continue
                
                if text_by_page is None:
                    continue  # 중복된 경우
                
                # Step 2: split documents
                split_docs, _ = split_text_to_documents(
                    text_by_page=text_by_page,
                    file_hash=file_hash,
                    file_name=file_name,
                    matched_df=matched_df
                )
                
                if split_docs:
                    all_documents.extend(split_docs)  # ✅ 모든 문서 수집
                    print(f"📄 OCR 처리됨: {filename} ({len(split_docs)} 청크)")
                
            except Exception as e:
                print(f"❌ 오류 발생 - {pdf_path}: {e}")
                
    print(f"📦 전체 OCR 처리된 문서: {len(all_documents)}개 청크")
    documents_to_save = all_documents  # 모든 문서 저장
    
    # ✅ 그룹화 및 저장 (중복 방지)
    
    doc_groups = defaultdict(list)
    for doc in documents_to_save:
        title = doc.metadata.get("pblancNm")
        doc_groups[title].append(doc)

    added_count = 0
    for title, doc_list in doc_groups.items():
        file_hash = doc_list[0].metadata.get("file_hash")
        if file_hash in existing_hashes:
            print(f"⏩ 이미 저장된 파일: {title} (hash: {file_hash}) → 스킵됨")
            continue

        vectorstore.add_documents(doc_list)
        added_count += 1
        print(f"✅ 벡터DB 저장됨: {title} ({len(doc_list)} 청크)")

    print(f"\n📦 최종 저장 완료: {added_count}개 문서 (중복 제외)")
    print(f"🎯 전체 처리: {len(all_documents)}개 청크")
    print(f"🎯 벡터DB 저장: {len(documents_to_save)}개 청크")

### 랩퍼 함수
def run_service():
    """FastAPI 등에서 import 해서 실행할 수 있는 엔트리 포인트 함수"""
    process_cached_txt_files()


# ✅ 8. 실행 엔트리 포인트
if __name__ == "__main__":
    process_cached_txt_files()
    
