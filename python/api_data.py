import requests
import json
import pandas as pd

import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()
API_KEY = os.getenv("BIZINFO_API_KEY")
BASE_URL = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"


#  ✅ API 호출해서 전체 데이터 가져오기
def get_bizinfo_data_by_hashtags():
    """
    지정된 해시태그를 포함하는 Bizinfo 지원사업 데이터를 가져와 리스트로 반환합니다.
    """
    data = None # 초기화

    params = {
        "crtfcKey": API_KEY,
        "dataType": "json",
        "searchLclasId": "02"
    }

    print(f"[DEBUG] 요청 URL: {BASE_URL}?{requests.compat.urlencode(params)}")

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        print(f"[DEBUG] 응답 상태코드: {response.status_code}")

        if data and 'jsonArray' in data and isinstance(data['jsonArray'], list):
            print(f"✔️ 성공적으로 {len(data['jsonArray'])}건의 데이터를 가져왔습니다.")
            return data['jsonArray']
        else:
            print("⚠️ API 응답에서 'jsonArray' 데이터를 찾을 수 없거나 형식이 올바르지 않습니다.")
            print(f"전체 응답: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return []
            
    except Exception as e:
        print(f"❌ 예상치 못한 오류 발생: {e}")
        return []


## ✅ 로컬 PDF 파일명과 일치하는 공고만 DataFrame으로 반환
def filter_matched_bizinfo(data, folder_path, file_ext=".pdf"):
    """
    공고명이 로컬 폴더 내 파일 이름과 일치하는 지원사업 정보만 필터링하여 DataFrame으로 반환합니다.
    Args:
        data (list): API에서 가져온 지원사업 데이터 리스트
        folder_path (str): 파일이 저장된 로컬 폴더 경로
    Returns:
        pd.DataFrame: 매칭된 데이터만 포함된 DataFrame
    """
    
    if not data:
        print("⚠️ 데이터가 비어있습니다.")
        return pd.DataFrame()

    # 공고 리스트를 DataFrame으로 변환
    df = pd.DataFrame(data)

    # 로컬 PDF 파일 목록을 재귀적으로 수집 (중첩 폴더 포함)
    pdf_file_names = set()
    
    try:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(file_ext):
                    # 확장자 제거한 파일명 추가
                    file_name_without_ext = os.path.splitext(file)[0]
                    pdf_file_names.add(file_name_without_ext)
                    
        print(f"[DEBUG] 발견된 PDF 파일 수: {len(pdf_file_names)}")
        
    except FileNotFoundError:
        print(f"❌ 폴더 경로 '{folder_path}'를 찾을 수 없습니다.")
        return pd.DataFrame()

    # 'pblancNm' 컬럼이 있는지 확인
    if 'pblancNm' not in df.columns:
        print("❌ API 데이터에 'pblancNm' 컬럼이 없습니다.")
        print(f"사용 가능한 컬럼: {df.columns.tolist()}")
        return pd.DataFrame()

    # 공고명 기준으로 매칭
    matched_df = df[df['pblancNm'].isin(pdf_file_names)]
    
    print(f"[DEBUG] 매칭된 공고 수: {len(matched_df)}")
    if len(matched_df) > 0:
        print(f"[DEBUG] 매칭된 공고명: {matched_df['pblancNm'].tolist()}")

    # 필요한 컬럼만 추출
    columns_to_extract = [
        "pblancNm",                     # 공고명
        "refrncNm",                     # 문의처
        "excInsttNm",                   # 수행기관
        "pldirSportRealmLclasCodeNm",   # 지원분야 (대분류)
        "reqstMthPapersCn",             # 신청방법
        "reqstBeginEndDe",              # 신청기간
        "bsnsSumryCn",                  # 사업개요
        "trgetNm",                      # 지원대상
        "jrsdInsttNm",                  # 주관부처
        "pblancUrl",                    # 공고 URL
        "rceptEngnHmpgUrl"              # 접수처 URL
    ]

    return matched_df[columns_to_extract]