import aiohttp
import asyncio
from bs4 import BeautifulSoup
import urllib.parse

async def test_littlemom():
    # 검색어를 EUC-KR로 인코딩
    query = "정의란 무엇인가"
    encoded_query = urllib.parse.quote(query.encode('euc-kr'))
    
    url = f"https://www.littlemom.co.kr/sub/01/srclist_book.html?keyfield=item_name&key={encoded_query}"
    print(f"Requesting URL: {url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    try:
        # SSL 인증서 문제 우회 설정
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(headers=headers, connector=connector) as s:
            async with s.get(url) as r:
                print(f"[개똥이네] HTTP Status: {r.status}")
                # 응답을 바이트로 읽어서 EUC-KR로 디코딩
                html_bytes = await r.read()
                
                # HTML 파싱
                soup = BeautifulSoup(html_bytes, "html.parser", from_encoding="euc-kr")
                
                # 캡처 화면을 바탕으로 CSS 선택자 추측 (책 아이템 박스들)
                # 보통 li 태그나 class에 item, box 등이 들어감
                items = soup.select("ul.slist_book_ul li") or soup.select(".src_result_list li") or soup.select("li.book_item") or soup.select("ul > li")
                
                print(f"[개똥이네] 전체 li 개수: {len(items)}")
                
                # 제목 추출 시도
                found_books = 0
                for item in items:
                    title_tag = item.select_one(".book_name") or item.select_one(".title") or item.select_one("strong") or item.select_one("a.tit")
                    if title_tag and title_tag.get_text(strip=True):
                        print(f"  - 제목: {title_tag.get_text(strip=True)}")
                        found_books += 1
                        
                print(f"[개똥이네] 유효한 책 데이터 {found_books}건 추출 완료")
                
                # HTML 일부 저장 (분석용)
                with open("littlemom.html", "wb") as f:
                    f.write(html_bytes)
                    
    except Exception as e:
        print(f"[개똥이네] Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_littlemom())
