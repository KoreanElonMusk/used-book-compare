# 📚 BookCompare — 중고책 가격 비교 웹서비스

알라딘, 예스24, 개똥이네 3곳의 중고책 플랫폼에서 가격을 수집하여 한눈에 비교할 수 있는 웹서비스 프로토타입입니다.

## 🏗️ 기술 스택

| 구분 | 기술 |
|------|------|
| Backend | Python, FastAPI, asyncio |
| HTTP 통신 | aiohttp (비동기) |
| 크롤링 | BeautifulSoup4 |
| Frontend | HTML, CSS, Vanilla JavaScript |
| Server | Uvicorn |

## 📁 프로젝트 구조

```
used-book-compare/
├── main.py                  # FastAPI 메인 애플리케이션
├── scrapers/
│   ├── __init__.py
│   ├── aladin.py            # 알라딘 Open API 모듈
│   ├── yes24.py             # 예스24 크롤링 모듈
│   └── gaeddong.py          # 개똥이네 크롤링 모듈
├── static/
│   ├── index.html           # 메인 HTML 페이지
│   ├── style.css            # 스타일시트
│   └── script.js            # 프론트엔드 로직
├── requirements.txt         # Python 의존성 패키지
└── README.md                # 이 파일
```

## 🚀 실행 방법

### 1. 가상환경 생성 및 활성화

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# 가상환경 활성화 (Windows CMD)
.\venv\Scripts\activate.bat

# 가상환경 활성화 (macOS/Linux)
source venv/bin/activate
```

### 2. 의존성 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 서버 실행

```bash
# 방법 1: Python 직접 실행
python main.py

# 방법 2: Uvicorn으로 실행 (개발 모드 + 자동 리로드)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 브라우저 접속

서버가 실행되면 브라우저에서 아래 주소로 접속하세요:

```
http://localhost:8000
```

## ⚙️ 설정

### 알라딘 API 키 설정

알라딘 Open API를 사용하려면 TTBKey가 필요합니다:

1. [알라딘 Open API](https://www.aladin.co.kr/ttb/apiguide.aspx) 에서 키를 발급받습니다.
2. `scrapers/aladin.py` 파일의 `TTB_KEY` 변수에 발급받은 키를 입력합니다:

```python
TTB_KEY = "발급받은_TTBKey를_여기에_입력"
```

## 📌 주요 기능

- **통합 검색**: 책 제목 또는 ISBN으로 3곳의 중고책 플랫폼을 동시에 검색
- **비동기 병렬 수집**: `asyncio.gather`를 사용하여 3개 사이트의 데이터를 동시에 수집 → 빠른 응답 속도
- **최저가 정렬**: 수집된 결과를 가격 오름차순으로 자동 정렬
- **장애 격리**: 특정 사이트에서 오류가 발생해도 나머지 사이트의 결과는 정상 표시
- **반응형 UI**: 모바일/데스크톱 모두 지원하는 프리미엄 다크 테마 UI

## ⚠️ 주의 사항

- 이 프로젝트는 **프로토타입** 목적으로 만들어졌습니다.
- 웹 크롤링은 대상 사이트의 HTML 구조 변경에 따라 동작하지 않을 수 있습니다.
- 크롤링 시 대상 사이트의 `robots.txt` 및 이용약관을 확인하고 준수해 주세요.
- 상업적 사용 시 각 플랫폼의 API 이용 정책을 반드시 확인하세요.
