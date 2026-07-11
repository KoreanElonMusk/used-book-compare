"""
중고책 가격 비교 웹서비스 - 메인 애플리케이션
=============================================
FastAPI 기반 백엔드 서버
- 3개 중고책 플랫폼(알라딘, 예스24, 개똥이네)의 데이터를 비동기 병렬 수집
- 정적 파일(HTML, CSS, JS) 서빙
- RESTful API 엔드포인트 제공
"""

import asyncio
import logging
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

# 각 스크래퍼 모듈 임포트
from scrapers.aladin import search_aladin
from scrapers.yes24 import search_yes24
from scrapers.gaeddong import search_gaeddong

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# FastAPI 앱 인스턴스 생성
# ──────────────────────────────────────────────
app = FastAPI(
    title="중고책 가격 비교",
    description="알라딘, 예스24, 개똥이네에서 중고책 가격을 한눈에 비교하세요.",
    version="1.0.0",
)

# 정적 파일(CSS, JS) 서빙 설정
app.mount("/static", StaticFiles(directory="static"), name="static")


# ──────────────────────────────────────────────
# 메인 페이지 라우트
# ──────────────────────────────────────────────
@app.get("/")
async def serve_index():
    """메인 HTML 페이지를 서빙합니다."""
    return FileResponse("static/index.html")


import time

# ──────────────────────────────────────────────
# 인메모리 캐시 시스템 (초고속 응답 최적화)
# ──────────────────────────────────────────────
# 형태: { "검색어": (만료_UnixTimestamp, 캐싱된_응답_딕셔너리) }
SEARCH_CACHE = {}
CACHE_TTL_SECONDS = 600  # 10분 (600초)

# ──────────────────────────────────────────────
# 검색 API 엔드포인트
# ──────────────────────────────────────────────
@app.get("/api/search")
async def search_books(q: str = Query(..., min_length=1, description="검색어 (책 제목 또는 ISBN)")):
    """
    중고책 통합 검색 API
    
    3개 사이트(알라딘, 예스24, 개똥이네)에서 비동기 병렬로 데이터를 수집하고,
    가격 오름차순으로 정렬하여 반환합니다.
    """
    now = time.time()
    q_clean = q.strip()

    # 1. 캐시 히트 (메모리에 데이터가 남아있고 만료되지 않은 경우)
    if q_clean in SEARCH_CACHE:
        expire_time, cached_data = SEARCH_CACHE[q_clean]
        if now < expire_time:
            logger.info(f"⚡ [Cache Hit] 검색어: '{q_clean}' - 즉시 반환 (0.01초 이내)")
            return JSONResponse(content=cached_data)
        else:
            # 만료된 캐시 삭제
            del SEARCH_CACHE[q_clean]

    logger.info(f"🌐 [Cache Miss] 검색 요청 수신: '{q_clean}' - 웹 크롤링 시작")

    # ── 3개 사이트 비동기 병렬 수집 ──
    tasks = [
        search_aladin(q_clean),
        search_yes24(q_clean),
        search_gaeddong(q_clean),
    ]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    # ── 결과 병합 및 에러 처리 ──
    all_results = []
    errors = []
    store_names = ["알라딘", "예스24", "개똥이네"]

    for i, result in enumerate(raw_results):
        if isinstance(result, Exception):
            error_msg = f"{store_names[i]}: 수집 실패 ({type(result).__name__})"
            logger.error(error_msg)
            errors.append(error_msg)
        elif isinstance(result, list):
            all_results.extend(result)
        else:
            errors.append(f"{store_names[i]}: 알 수 없는 응답 형식")

    # ── 가격 기준 오름차순 정렬 (최저가 우선) ──
    all_results.sort(key=lambda x: (x["price"] == 0, x["price"]))

    logger.info(f"✅ 검색 완료: 총 {len(all_results)}건, 에러 {len(errors)}건")

    # JSON 응답 데이터 구성
    response_data = {
        "query": q_clean,
        "total": len(all_results),
        "results": all_results,
        "errors": errors,
    }

    # 2. 결과 캐싱 (새로운 데이터를 메모리에 저장)
    SEARCH_CACHE[q_clean] = (now + CACHE_TTL_SECONDS, response_data)

    # 주기적인 캐시 청소 로직 (메모리 누수 방지, 오래된 항목 무작위 삭제)
    if len(SEARCH_CACHE) > 1000:
        # 캐시가 1000개를 초과하면 만료된 항목 일괄 정리
        expired_keys = [k for k, (exp, _) in SEARCH_CACHE.items() if exp < now]
        for k in expired_keys:
            del SEARCH_CACHE[k]

    return JSONResponse(content=response_data)


# ──────────────────────────────────────────────
# 서버 실행 (직접 실행 시)
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
