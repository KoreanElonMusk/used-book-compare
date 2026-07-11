"""
모듈 2: 예스24 중고샵 웹 크롤링
- BeautifulSoup을 이용하여 예스24 중고 검색 결과 페이지를 파싱
- 봇 차단 방지를 위한 User-Agent 헤더 설정
- 표지 이미지, 작가, 출판사, 상태 정보 추출
"""

import aiohttp
from bs4 import BeautifulSoup
import logging
from urllib.parse import quote
import asyncio

logger = logging.getLogger(__name__)

# 예스24 중고 검색 URL 템플릿 (개별 중고 상품)
YES24_SEARCH_URL = "https://www.yes24.com/Product/Search?domain=USED_GOODS&query={query}"

# 봇 차단 방지를 위한 User-Agent 헤더
HEADERS = {
    "User-Agent": "Mozilla/5.0",
}


async def search_yes24(query: str) -> list[dict]:
    """
    예스24 중고샵에서 중고책을 검색합니다.
    표지 이미지, 작가, 출판사, 상태 정보를 함께 추출합니다.
    """
    results = []
    url = YES24_SEARCH_URL.format(query=quote(query))

    # 재시도 로직 (최대 3회)
    for attempt in range(3):
        try:
            async with aiohttp.ClientSession(headers=HEADERS) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status != 200:
                        logger.warning(f"[예스24] 응답 오류: HTTP {response.status}")
                        return results

                    html_bytes = await response.read()
            # 성공 시 반복문 탈출
            break
        except asyncio.TimeoutError:
            if attempt == 2:
                logger.error("[예스24] 3회 타임아웃 발생, 수집 실패")
                return results
            await asyncio.sleep(1)
        except Exception as e:
            if attempt == 2:
                logger.error(f"[예스24] 예외 발생 ({e}), 수집 실패")
                return results
            await asyncio.sleep(1)

    try:
        soup = BeautifulSoup(html_bytes, "html.parser")

        # 검색 결과 상품 목록 추출 (예스24 중고샵 검색 결과 리스트)
        items = soup.select("ul#yesSchList > li") or soup.select("li[data-goods-no]")

        for item in items[:10]:  # 최대 10개까지만 수집
            try:
                # 책 제목 추출
                title_tag = (
                    item.select_one("a.goods_name") or
                    item.select_one("a.gd_name") or
                    item.select_one("a[class*='name']") or
                    item.select_one("a.goods_a") or
                    item.select_one(".gd_name a") or
                    item.select_one(".gd_name")
                )
                title = title_tag.get_text(strip=True) if title_tag else "제목 없음"
                # 빈 제목 무시
                if title == "제목 없음":
                    continue
                link = "#"
                if title_tag and title_tag.get("href"):
                    href = title_tag["href"]
                    link = href if href.startswith("http") else f"https://www.yes24.com{href}"

                # ★ 표지 이미지 추출
                cover = ""
                img_tag = item.select_one("img.goods_img") or item.select_one("img[class*='img']") or item.select_one("img")
                if img_tag:
                    cover = img_tag.get("data-original") or img_tag.get("src", "")
                    if cover and not cover.startswith("http"):
                        cover = f"https:{cover}" if cover.startswith("//") else ""

                # ★ 작가 추출
                author = ""
                author_tag = (
                    item.select_one("span.info_auth") or
                    item.select_one("span.goods_auth") or
                    item.select_one("span.authPub .auth_a") or
                    item.select_one("a.auth_a")
                )
                if author_tag:
                    author = author_tag.get_text(strip=True)
                    # "저/", "역/" 등이 붙어있으므로 클린업
                    author = author.replace("저/", "").replace("원저/", "").replace("글/", "").replace("그림/", "").replace("역/", "").replace("감수", "").strip()

                # ★ 출판사 추출
                publisher = ""
                pub_tag = (
                    item.select_one("span.info_pub") or
                    item.select_one("span.goods_pub") or
                    item.select_one("span.authPub .pub_a") or
                    item.select_one("a.pub_a")
                )
                if pub_tag:
                    publisher = pub_tag.get_text(strip=True)

                # 중고 가격 추출
                price_tag = (
                    item.select_one("em.yes_b") or
                    item.select_one("span.price") or
                    item.select_one("strong.price") or
                    item.select_one("em.txt_num")
                )
                price_text = price_tag.get_text(strip=True) if price_tag else "0"
                price = int("".join(filter(str.isdigit, price_text)) or "0")

                # 상태 정보 추출
                condition_tag = item.select_one("span.goods_condition") or item.select_one("span.state")
                condition = condition_tag.get_text(strip=True) if condition_tag else "중고"

                results.append({
                    "store": "예스24",
                    "title": title,
                    "price": price,
                    "condition": condition,
                    "link": link,
                    "cover": cover,           # ★ 표지 이미지
                    "author": author,         # ★ 작가
                    "publisher": publisher,   # ★ 출판사
                })

            except Exception as e:
                logger.warning(f"[예스24] 개별 아이템 파싱 실패: {e}")
                continue

        # ★ ISBN 비동기 병렬 추출
        async def fetch_isbn(session: aiohttp.ClientSession, url: str) -> str:
            if url == "#": return ""
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as r:
                    if r.status == 200:
                        html = await r.text()
                        s = BeautifulSoup(html, 'html.parser')
                        tb = s.select_one('.tb_nor.tb_vertical')
                        if tb:
                            for tr in tb.select('tr'):
                                th = tr.select_one('th')
                                if th and 'ISBN' in th.text:
                                    td = tr.select_one('td')
                                    if td: return td.get_text(strip=True)
            except:
                pass
            return ""

        async with aiohttp.ClientSession(headers=HEADERS) as session:
            tasks = [fetch_isbn(session, res["link"]) for res in results]
            isbns = await asyncio.gather(*tasks)
            for idx, res in enumerate(results):
                res["isbn"] = isbns[idx]

        logger.info(f"[예스24] {len(results)}건 수집 및 ISBN 추출 완료")

    except aiohttp.ClientError as e:
        logger.error(f"[예스24] 네트워크 오류: {e}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"[예스24] 수집 실패: {e}")

    return results
