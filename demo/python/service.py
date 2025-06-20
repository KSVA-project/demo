import camelot
import fitz  # PyMuPDF
import pandas as pd
from langchain.schema import Document
from tabulate import tabulate
import os
import win32com.client

from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import NLTKTextSplitter
from langchain_community.vectorstores import Chroma
from chromadb import PersistentClient


# 텍스트 추출 함수 (PyMuPDF 사용)
def extract_text_with_fitz(pdf_path):
    doc = fitz.open(pdf_path)
    texts = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        texts.append(text.strip() if text else "")
    return texts

# 페이지별 📊 표 추출 함수 (Camelot 사용)
def extract_tables_lattice_per_page(pdf_path):
    tables_per_page = {}
    tables = camelot.read_pdf(pdf_path, pages="1-end", flavor="lattice")
    for table in tables:
        page_num = table.page
        df = table.df.map(lambda x: x.replace('\n', ' ') if isinstance(x, str) else x)
        if page_num not in tables_per_page:
            tables_per_page[page_num] = []
        tables_per_page[page_num].append(df)
    return tables_per_page

# 표를 마크다운으로 변환
def convert_tables_to_markdown(tables):
    markdowns = []
    for i, df in enumerate(tables):
        try:
            markdown_table = tabulate(df.values.tolist(), headers=df.iloc[0].tolist(), tablefmt="github")
            markdowns.append(f"▼ 표 {i + 1}:\n{markdown_table}")
        except Exception as e:
            markdowns.append(f"▼ 표 {i + 1}: 변환 실패 ({e})")
    return "\n\n".join(markdowns)

# 임베딩 모델 로드
def load_embeddings_model():
    """ko-sroberta-nli 기반 HuggingFace 임베딩 모델 불러오기"""
    return HuggingFaceEmbeddings(
        model_name='jhgan/ko-sroberta-nli',
        model_kwargs={'device': 'cpu'},  # GPU 사용 시 'cuda'로 변경
        encode_kwargs={'normalize_embeddings': True},
    )

# PDF 1개 처리 -> 텍스트 + 표 추출 -> 벡터화 -> ChromaDB 저장
def process_pdf(pdf_path, embeddings_model):
    
    file_name = os.path.splitext(os.path.basename(pdf_path))[0]
    texts = extract_text_with_fitz(pdf_path)
    tables_per_page = extract_tables_lattice_per_page(pdf_path)

    documents = []

    for i, text in enumerate(texts):
        page_num = i + 1
        tables = tables_per_page.get(page_num, [])
        tables_str = convert_tables_to_markdown(tables)

        combined_text = text  # ✅ 여기서 정의해야 함

        if tables_str:
            combined_text += "\n\n---\n\n📊 페이지 내 표 정보:\n" + tables_str

        doc = Document(
            page_content=combined_text,
            metadata={"page": page_num, "title": file_name}
        )
        documents.append(doc)

    if not documents:
        print(f"⚠️ 추출된 문서 없음: {pdf_path}")
        return

    splitter = NLTKTextSplitter()
    split_documents = splitter.split_documents(documents)

    if not split_documents:
        print(f"⚠️ 분할된 문서 없음: {pdf_path}")
        return

    return split_documents

# 🔍 모든 PDF 폴더 처리 및 하나의 chromaDB에 저장
def process_all_pdfs(root_dir="./data", chroma_root="./chroma_db"):
    
    embeddings_model = load_embeddings_model()

    # ✅ PersistentClient: ChromaDB를 디스크에 지속적으로 저장하기 위한 클라이언트
    client = PersistentClient(path=chroma_root)
    vectorstore = Chroma(
        client=client,
        embedding_function=embeddings_model,
        collection_metadata={"hnsw:space": "cosine"}
    )
    # ✅ Chroma: 벡터 임베딩을 저장/조회할 수 있는 LangChain vectorstore
    # - client: 디스크 기반 저장을 위한 PersistentClient 객체
    # - embedding_function: 텍스트 임베딩에 사용할 모델
    # - collection_metadata: 검색에 사용할 거리 함수(hnsw:space) 지정
    
    for dirpath, _, filenames in os.walk(root_dir):
    # dirpath: 현재 폴더 경로 / _ : 이 변수는 사용 안할꺼라고 선언 / filenames: 파일 리스트  
        
        for filename in filenames:
            
            ext = filename.lower().split('.')[-1]
            
            # pdf만 처리
            if ext == "pdf":
                pdf_path = os.path.join(dirpath, filename)
                
                try:
                    split_docs = process_pdf(pdf_path, embeddings_model=embeddings_model)
                    if not split_docs:
                        continue

                    # 기존 벡터 중복 제거
                    existing = vectorstore.get(include=["metadatas"]) # 현재 벡터 DB에 저장된 문서들의 id와 metadata 정보를 가져옴
                    
                    doc_ids_to_delete = [
                        doc_id for doc_id, meta in zip(existing["ids"], existing["metadatas"]) # 각 문서의 (id, metadata)를 짝지어 순회함
                        if meta and meta.get("title") == split_docs[0].metadata["title"] # 지금처리 중인 문서 제목
                    ]
                    # existing["ids"]: 문서의 고유 ID 리스트
                    
                    if doc_ids_to_delete:
                        vectorstore.delete(doc_ids_to_delete) # 기존 문서 삭제

                    # 백터 스토어 저장
                    vectorstore.add_documents(split_docs)
                    
                    print(f"✅ 저장됨: {filename} ({len(split_docs)} 청크)")
                    
                except Exception as e:
                    print(f"❌ 오류 발생 - {pdf_path}: {e}")
            elif ext == "hwp":
                print(f"⚠️ HWP 파일 무시됨: {filename}")

# ✅ 8. 실행 엔트리 포인트
if __name__ == "__main__":
    process_all_pdfs()