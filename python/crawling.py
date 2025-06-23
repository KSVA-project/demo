# PDF 전달
import os
import shutil

# ✅ 라이브러리 불러오기 및 폴더 생성
import os, time, requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# [1] PDF 저장 폴더 생성 함수
def make_pdf_folder(folder_path="./original"):
    os.makedirs(folder_path, exist_ok=True)  # 디렉토리가 없으면 생성
    return folder_path


# [2] Chrome driver 설정
def init_chrome_driver(driver_path: str) -> webdriver.Chrome:
    # 크롬 옵션 설정
    chrome_options = Options()
    
    # 창을 최대화된 상태로 시작
    chrome_options.add_argument("--start-maximized")
    
    # 웹사이트가 크롤러/봇을 차단하는 경우, User-Agent를 사람이 쓰는 브라우저처럼 위장하면 우회
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
    
    # 크롬 드라이버를 백그라운드에서 실행시키는 역할
    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# [3] 지원사업 공고 크롤링 및 파일 다운로드 함수
def crawl_bizinfo_notices(driver, pdf_folder="./original", end_page=2):
    
    """
    기업마당 사이트에서 지원사업 공고문 PDF/HWP 파일을 크롤링하여 저장하고,
    각 공고의 정보(제목, 상세 URL, 저장 파일 목록)를 리스트로 반환합니다.

    Parameters:
    - driver_path (str): 크롬드라이버 실행파일 경로
    - pdf_folder (str): PDF/HWP 저장 경로
    - end_page (int): 크롤링할 페이지 수 (기본 2)

    Returns:
    - list: 각 공고의 정보가 담긴 딕셔너리 리스트
    """
    
    for page in range(1, end_page+1):
        print(f"[{page}] 페이지 크롤링 중...")
        
        page_url = (
            "https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/list.do"
            "?hashCode=02&rowsSel=6&rows=15"
            f"&cpage={page}"
            "&cat=&article_seq=&pblancId=&schJrsdCodeTy=&schWntyAt="
            "&schAreaDetailCodes=&schEndAt=N&orderGb=&sort="
            "&condition=searchPblancNm&condition1=AND&preKeywords=&keyword="
        )
        
        
        # 리스트 페이지 열기
        driver.get(page_url)
        time.sleep(1.5)

        # 공고 목록(HTML) 파싱
        soup = BeautifulSoup(driver.page_source, "html.parser")
        rows = soup.select("div.table_Type_1 > table > tbody > tr")

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 7:
                continue

            title_tag = cols[2].find("a")
            title = title_tag.get_text(strip=True)
            href = title_tag["href"]
            if not href.startswith("/web"):
                href = "/web/lay1/bbs/S1T122C128/AS/74/" + href
            detail_url = urljoin("https://www.bizinfo.go.kr", href)
            
            # 상세 페이지 열기
            driver.get(detail_url)
            time.sleep(2)
            
            download_links = driver.find_elements(By.CSS_SELECTOR, "a.icon_download, a.basic-btn01")
            saved_files = []
            
            for i, link in enumerate(download_links):
                
                file_href = link.get_attribute("href")
                file_title = link.get_attribute("title") or link.text or ""

                if not file_href or "javascript" in file_href:
                    continue

                if file_href.startswith("/"):
                    file_href = urljoin("https://www.bizinfo.go.kr", file_href)

                # PDF 또는 HWP 확장자만 허용
                ext = None
                for vext in ['.pdf', '.hwp']:
                    if vext in file_title.lower() or vext in file_href.lower():
                        ext = vext
                        break
                if not ext:
                    continue

                # 안전한 파일 이름 생성
                safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_")).strip()
                filename = f"{safe_title}{ext}"
                filepath = os.path.join(pdf_folder, filename)

                # 다운로드
                try:
                    response = requests.get(file_href)
                    response.raise_for_status()
                    with open(filepath, "wb") as f:
                        f.write(response.content)
                    print(f"[✅] 저장 완료: {filename}")
                    saved_files.append(filename)
                except Exception as e:
                    print(f"[❌] 다운로드 실패: {file_href} - {e}")

def main():
    driver_path = "C:/Users/USER/chromedriver-win64/chromedriver.exe"
    pdf_folder = make_pdf_folder()
    driver = init_chrome_driver(driver_path)

    try:
        result = crawl_bizinfo_notices(driver, pdf_folder=pdf_folder)
        print("크롤링 및 다운로드 완료!")
    finally:
        driver.quit()

def convert_pdf_to_folder(input_folder_path, output_folder_path):
    """
    HWP는 무시하고, PDF 파일만 복사하여 지정된 경로로 이동합니다.
    Args:
        input_folder_path (str): PDF 원본 폴더 경로
        output_folder_path (str): 복사할 목적지 폴더 경로
    """
    
    # 입력 폴더가 존재하지 않으면 함수 종료
    if not os.path.isdir(input_folder_path):
        print(f"오류: '{input_folder_path}' 경로를 찾을 수 없거나 폴더가 아닙니다.")
        return

    os.makedirs(output_folder_path, exist_ok=True)
    print(f"'{input_folder_path}' → '{output_folder_path}' PDF 복사 시작...")

    copied_count = 0

    for filename in os.listdir(input_folder_path):
        ext = filename.lower().split('.')[-1]
        if ext != "pdf":
            continue  # PDF가 아니면 무시

        src_path = os.path.join(input_folder_path, filename)
        dst_path = os.path.join(output_folder_path, filename)

        if os.path.exists(dst_path):
            print(f"  - '{filename}' 이미 복사됨. 건너뜁니다.")
            continue

        try:
            shutil.copy2(src_path, dst_path)
            print(f"  - 복사 완료: {filename}")
            copied_count += 1
        except Exception as e:
            print(f"  - 복사 실패: {filename} → {e}")

    print(f"\n총 {copied_count}개의 PDF 복사 완료")

##### 랩퍼 함수
def run_crawling():
    main()
    convert_pdf_to_folder("./original", "./data")

if __name__ == "__main__":
    main()
    convert_pdf_to_folder("./original", "./data") # 변환 + 복사