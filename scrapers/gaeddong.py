"""
모듈 3: 개똥이네 헌책방(littlemom.co.kr) 웹 크롤링
- 개똥이네는 EUC-KR 인코딩을 사용하므로 검색어 및 HTML 파싱 시 EUC-KR 처리 필수
- 봇 차단 방지를 위한 User-Agent 헤더 설정
"""

import aiohttp
from bs4 import BeautifulSoup
import logging
import urllib.parse

logger = logging.getLogger(__name__)

# 개똥이네(littlemom) 검색 URL 템플릿
GAEDDONG_SEARCH_URL = "https://www.littlemom.co.kr/sub/01/srclist_book.html?keyfield=item_name&key={query}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}


async def search_gaeddong(query: str) -> list[dict]:
    """
    개똥이네 헌책방에서 중고책을 검색합니다.
    표지 이미지, 출판사, 최저가 정보를 추출합니다.
    """
    results = []
    
    try:
        # 1. 검색어를 EUC-KR로 인코딩 (개똥이네 필수 사항)
        encoded_query = urllib.parse.quote(query.encode('euc-kr'))
    except UnicodeEncodeError:
        logger.error(f"[개똥이네] 검색어 EUC-KR 인코딩 실패: {query}")
        return results

    url = GAEDDONG_SEARCH_URL.format(query=encoded_query)

    # 재시도 로직 (최대 3회)
    html_bytes = None
    for attempt in range(3):
        try:
            # SSL 인증서 검증 무시 (개똥이네 연결 오류 방지)
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status != 200:
                        logger.warning(f"[개똥이네] 응답 오류: HTTP {response.status}")
                        return results

                    # 바이트 코드로 읽어옴
                    html_bytes = await response.read()
            # 성공 시 탈출
            break
        except asyncio.TimeoutError:
            if attempt == 2:
                logger.error("[개똥이네] 3회 타임아웃 발생, 수집 실패")
                return results
            await asyncio.sleep(1)
        except Exception as e:
            if attempt == 2:
                logger.error(f"[개똥이네] 네트워크 오류 ({e}), 수집 실패")
                return results
            await asyncio.sleep(1)

    if not html_bytes:
        return results

    try:
        html_text = html_bytes.decode('euc-kr', errors='replace')
        soup = BeautifulSoup(html_text, "html.parser")

        # 검색 결과 상품 목록 추출
        items = soup.select("ul.slist_book_ul li") or soup.select(".list_search li") or soup.select("li.listnum_find")

        for item in items[:10]:  # 최대 10개까지만 수집
            try:
                # 책 제목과 링크 추출
                title_tag = item.select_one("p.name a[title]") or item.select_one(".name a")
                if not title_tag:
                    continue
                    
                title = title_tag.get("title") or title_tag.get_text(strip=True)
                if not title or title == "제목 없음":
                    continue

                href = title_tag.get("href", "#")
                link = href if href.startswith("http") else f"https://www.littlemom.co.kr/sub/01/{href}"

                # 표지 이미지 추출
                cover = ""
                img_tag = item.select_one(".item_thmb img") or item.select_one("img")
                if img_tag and img_tag.get("src"):
                    cover = img_tag["src"]
                    if not cover.startswith("http"):
                        cover = f"https://www.littlemom.co.kr{cover}"

                # 출판사 추출 (개똥이네는 '브랜드'로 표기)
                publisher = ""
                pub_tag = item.select_one("p.brand a") or item.select_one(".brand a")
                if pub_tag:
                    publisher = pub_tag.get_text(strip=True)

                # 작가 추출 (목록에서는 제공되지 않는 경우가 많음)
                author = ""

                # 중고 가격 추출
                price_tag = item.select_one(".price strong") or item.select_one(".price")
                price_text = price_tag.get_text(strip=True) if price_tag else "0"
                price = int("".join(filter(str.isdigit, price_text)) or "0")

                # 상태 정보 추출 (비교 상품 개수)
                condition = "중고"
                comp_tag = item.select_one(".compare_count")
                if comp_tag:
                    comp_count = comp_tag.get_text(strip=True)
                    condition = f"중고 매물 {comp_count}건"

                results.append({
                    "store": "개똥이네",
                    "title": title,
                    "price": price,
                    "condition": condition,
                    "link": link,
                    "cover": cover,
                    "author": author,
                    "publisher": publisher,
                })

            except Exception as e:
                logger.warning(f"[개똥이네] 개별 아이템 파싱 실패: {e}")
                continue

        logger.info(f"[개똥이네] {len(results)}건 수집 완료")

    except aiohttp.ClientError as e:
        logger.error(f"[개똥이네] 네트워크 오류: {e}")
    except Exception as e:
        logger.error(f"[개똥이네] 수집 실패: {e}")

    return results
