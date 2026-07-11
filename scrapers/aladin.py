"""
모듈 1: 알라딘 Open API를 통한 중고책 데이터 수집
=============================================
2단계 접근 방식:
  1단계) ItemSearch API로 검색 → 책 목록 및 ISBN 확보
  2단계) ItemLookUp API + OptResult=usedList → 개별 중고 매물(가격, 판매자, 상태 등) 조회

반환 데이터에 표지 이미지(cover), 작가(author), 출판사(publisher) 포함
"""

import aiohttp
import asyncio
import logging

logger = logging.getLogger(__name__)

# 알라딘 Open API TTBKey
TTB_KEY = "ttb1chlalsrb0602001"

# 알라딘 API 엔드포인트
ALADIN_SEARCH_URL = "http://www.aladin.co.kr/ttb/api/ItemSearch.aspx"
ALADIN_LOOKUP_URL = "http://www.aladin.co.kr/ttb/api/ItemLookUp.aspx"


async def _search_books(session: aiohttp.ClientSession, query: str) -> list[dict]:
    """
    1단계: ItemSearch API로 책을 검색하여 ISBN 목록을 확보합니다.
    SearchTarget을 'Used'로 설정하여 중고 상품을 검색합니다.
    """
    params = {
        "TTBKey": TTB_KEY,
        "Query": query,
        "QueryType": "Keyword",       # 키워드 검색
        "MaxResults": 5,               # 상세 조회를 위해 5개로 제한
        "start": 1,
        "SearchTarget": "Used",        # ★ 중고 상품 검색 (기본값 'Book'은 새책)
        "output": "js",                # JSON 형식 응답
        "Version": "20131101",         # API 버전
        "Cover": "Big",                # ★ 큰 표지 이미지 요청
    }

    async with session.get(ALADIN_SEARCH_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
        if response.status != 200:
            logger.warning(f"[알라딘] 검색 API 응답 오류: HTTP {response.status}")
            return []

        data = await response.json(content_type=None)
        items = data.get("item", [])

        # 각 책의 기본 정보와 ISBN 추출 (표지, 작가, 출판사 포함)
        books = []
        for item in items:
            isbn = item.get("isbn13") or item.get("isbn", "")
            if isbn:
                books.append({
                    "isbn": isbn,
                    "title": item.get("title", "제목 없음"),
                    "link": item.get("link", "#"),
                    "cover": item.get("cover", ""),             # ★ 표지 이미지 URL
                    "author": item.get("author", ""),           # ★ 작가
                    "publisher": item.get("publisher", ""),     # ★ 출판사
                    "price_standard": item.get("priceStandard", 0),
                    "price_sales": item.get("priceSales", 0),
                })
        return books


async def _lookup_used_items(session: aiohttp.ClientSession, book_info: dict) -> list[dict]:
    """
    2단계: ItemLookUp API + OptResult=usedList로 개별 중고 매물을 조회합니다.
    판매자별 가격, 상태, 배송비 등 상세 정보를 가져옵니다.
    book_info에서 표지/작가/출판사 정보를 가져와 결과에 포함합니다.
    """
    isbn = book_info["isbn"]
    params = {
        "TTBKey": TTB_KEY,
        "itemIdType": "ISBN13",        # ISBN13으로 조회
        "ItemId": isbn,
        "output": "js",                # JSON 형식 응답
        "Version": "20131101",         # API 버전
        "OptResult": "usedList",       # ★ 중고 매물 리스트 포함
        "Cover": "Big",                # ★ 큰 표지 이미지
    }

    results = []

    try:
        async with session.get(ALADIN_LOOKUP_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if response.status != 200:
                logger.warning(f"[알라딘] 상세조회 API 응답 오류: HTTP {response.status} (ISBN: {isbn})")
                return results

            data = await response.json(content_type=None)
            items = data.get("item", [])

            if not items:
                return results

            item = items[0]
            title = item.get("title", book_info["title"])
            base_link = item.get("link", "#")
            # 표지/작가/출판사 — 상세조회 응답에도 있지만, 없으면 검색 결과에서 가져옴
            cover = item.get("cover", "") or book_info.get("cover", "")
            author = item.get("author", "") or book_info.get("author", "")
            publisher = item.get("publisher", "") or book_info.get("publisher", "")

            # subInfo.usedList에서 중고 매물 정보 추출
            sub_info = item.get("subInfo", {})
            used_list = sub_info.get("usedList", {})

            # 알라딘 중고 매물 카테고리별 처리
            categories = {
                "aladinUsed": "알라딘 직배송",
                "userUsed": "개인 셀러",
                "spaceUsed": "우주점",
            }

            min_overall_price = float('inf')
            best_category = "중고"
            best_link = base_link
            total_items = 0

            for category_key, category_name in categories.items():
                category_data = used_list.get(category_key, {})
                item_count = category_data.get("itemCount", 0)
                min_price = category_data.get("minPrice", 0)
                link = category_data.get("link", base_link)

                if item_count > 0 and min_price > 0:
                    total_items += item_count
                    if min_price < min_overall_price:
                        min_overall_price = min_price
                        best_category = f"중고(최저가 기준: {category_name}) {total_items}개"
                        best_link = link

            if total_items > 0 and min_overall_price != float('inf'):
                results.append({
                    "store": "알라딘",
                    "title": title,
                    "isbn": book_info.get("isbn", ""), # ★ ISBN 추가
                    "price": min_overall_price,
                    "condition": best_category,
                    "link": best_link,
                    "cover": cover,           # ★ 표지 이미지
                    "author": author,         # ★ 작가
                    "publisher": publisher,   # ★ 출판사
                })
            else:
                # usedList에 데이터가 없으면 기본 판매가로 폴백
                price = item.get("priceSales", 0) or item.get("priceStandard", 0)
                if price > 0:
                    results.append({
                        "store": "알라딘",
                        "title": title,
                        "isbn": book_info.get("isbn", ""), # ★ ISBN 추가
                        "price": price,
                        "condition": "중고",
                        "link": base_link,
                        "cover": cover,
                        "author": author,
                        "publisher": publisher,
                    })

    except Exception as e:
        logger.warning(f"[알라딘] 상세조회 실패 (ISBN: {isbn}): {e}")

    return results


async def search_aladin(query: str) -> list[dict]:
    """
    알라딘 Open API를 사용하여 중고책을 검색합니다.
    
    2단계 접근:
      1) ItemSearch로 검색 → ISBN + 표지/작가/출판사 확보
      2) 각 ISBN에 대해 ItemLookUp + usedList → 개별 중고 매물 조회
    """
    all_results = []

    try:
        async with aiohttp.ClientSession() as session:
            # 1단계: 검색하여 ISBN + 메타 정보 확보
            books = await _search_books(session, query)

            if not books:
                logger.info("[알라딘] 검색 결과 없음")
                return all_results

            # 2단계: 각 ISBN에 대해 중고 매물 상세 조회 (병렬 실행)
            lookup_tasks = [
                _lookup_used_items(session, book)
                for book in books
            ]
            lookup_results = await asyncio.gather(*lookup_tasks, return_exceptions=True)

            for result in lookup_results:
                if isinstance(result, list):
                    all_results.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"[알라딘] 개별 조회 실패: {result}")

        logger.info(f"[알라딘] 총 {len(all_results)}건 수집 완료")

    except aiohttp.ClientError as e:
        logger.error(f"[알라딘] 네트워크 오류: {e}")
    except Exception as e:
        logger.error(f"[알라딘] 수집 실패: {e}")

    return all_results
