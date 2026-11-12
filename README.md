# 키즈스테이지 (KidsStage)

전국의 **어린이 관람 가능 공연**을 검색하고, 공연 상세 정보와 함께 **공연장 주변 어린이 놀이시설**까지 지도로 한 번에 확인할 수 있는 웹서비스입니다.

> 공연 정보(KOPIS)와 놀이시설 정보(행정안전부)를 **공연장 좌표**를 기준으로 결합해, 부모가 여러 사이트를 오가지 않고 "아이와 함께하는 반나절 외출" 동선을 한 화면에서 그릴 수 있도록 합니다.

---

## 목차

- [주요 기능](#주요-기능)
- [기술 스택](#기술-스택)
- [아키텍처](#아키텍처)
- [프로젝트 구조](#프로젝트-구조)
- [시작하기](#시작하기)
- [API 명세](#api-명세)
- [데이터 모델](#데이터-모델)
- [테스트](#테스트)
- [데이터 출처](#데이터-출처)
- [참고 문서](#참고-문서)

---

## 주요 기능

| 기능 | 설명 |
|---|---|
| 🔍 공연 검색·목록 | 공연명 키워드, 지역(시도·구군), 기간, 공연상태, 장르 필터 + 정렬(임박순·이름순) |
| 🏆 아동 공연 랭킹 | KOPIS 예매상황판 아동(KID) 카테고리 순위 |
| 📄 공연 상세 | 관람연령·러닝타임·티켓가격·공연시간, 공연장 정보, 예매처 링크, 소개 이미지 |
| 🗺 지도 | Leaflet + OpenStreetMap 기반 공연장·놀이시설 마커 |
| 🛝 인근 놀이시설 | 공연장 반경(기본 1km) 안의 놀이시설을 거리순으로 표시 |
| ❤️ 즐겨찾기 | 로그인 없이 `localStorage`에 저장하고, 다시 볼 때 최신 공연 정보를 일괄 조회 |

---

## 기술 스택

| 레이어 | 사용 기술 |
|---|---|
| 프론트엔드 | React 19, Vite 5, React Router 7 |
| 지도 | Leaflet, react-leaflet (OpenStreetMap 타일) |
| 백엔드 | FastAPI, Uvicorn, SQLModel |
| DB | SQLite (WAL 모드) |
| 데이터 수집 | `httpx` (async), `xml.etree` (KOPIS XML 파싱) |
| 테스트 | Python `unittest` |

---

## 아키텍처

```
┌──────────────┐     ┌────────────────────┐     ┌──────────────┐
│ React (SPA)  │────▶│  FastAPI (/api/*)  │────▶│ SQLite       │
│ + Leaflet    │◀────│  읽기 전용 조회     │◀────│ backend/app.db│
└──────────────┘     └────────────────────┘     └──────────────┘
       │                       │                       ▲
  localStorage          POST /api/sync                 │
   (즐겨찾기)            / 기동 시 자동 동기화           │
                              ▼                        │
                     ┌─────────────────┐               │
                     │ ingest.py       │───────────────┘
                     │ (사전 적재 배치) │──▶ KOPIS OpenAPI (XML)
                     └─────────────────┘──▶ 행안부 놀이시설 API (JSON)
```

- 프론트엔드는 외부 공공 API를 직접 호출하지 않습니다.
- 서비스 키는 백엔드에서만 사용하며, 사용자 요청을 처리할 때는 외부 API를 호출하지 않습니다(전량 사전 적재).

---

## 프로젝트 구조

```
projectChildren/
├── backend/
│   ├── main.py            # FastAPI 앱, 모든 API 엔드포인트
│   ├── models.py          # SQLModel 테이블 정의
│   ├── schemas.py         # API 응답 스키마
│   ├── config.py          # 환경 변수 로딩
│   ├── ingest.py          # KOPIS·놀이시설 데이터 수집 → SQLite 적재
│   ├── sync_service.py    # 백그라운드 동기화 (API / 서버 기동 시)
│   ├── db_migrate.py      # 기존 DB에 누락 컬럼 추가·백필
│   ├── region_codes.py    # 시도·구군 행정표준코드
│   ├── genre_codes.py     # 장르(shcate) 코드
│   ├── test_main.py       # API 테스트
│   ├── test_ingest.py     # 수집 로직 테스트
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/         # HomePage, PerformanceDetailPage, FavoritesPage, NotFoundPage
│   │   ├── components/    # PerformanceCard, RankingCard, VenueMap, PlaygroundAccordion 등
│   │   ├── constants/     # 장르 코드
│   │   ├── api.js         # 백엔드 API 클라이언트
│   │   └── favorites.js   # localStorage 즐겨찾기 유틸
│   └── package.json
└── docs/                  # PRD, 개발 계획, 작업 목록, 공공 API 문서
```

---

## 시작하기

### 1. 사전 요구사항

- Python 3.10 이상
- Node.js 18 이상
- KOPIS OPEN API 서비스 키 ([공연예술통합전산망](https://www.kopis.or.kr))
- 공공데이터포털 서비스 키 — 행정안전부 전국어린이놀이시설정보서비스 ([data.go.kr](https://www.data.go.kr))

### 2. 백엔드

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   /   macOS·Linux: source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # 서비스 키 입력
```

`backend/.env` 항목:

| 변수 | 필수 | 설명 |
|---|---|---|
| `KOPIS_SERVICE_KEY` | ✅ | KOPIS 인증키 |
| `PLAYGROUND_SERVICE_KEY` | ✅ | 행안부 놀이시설 API 인증키 |
| `CORS_ALLOWED_ORIGINS` | | 쉼표로 구분한 허용 오리진. 비우면 `localhost:5173`, `127.0.0.1:5173`만 허용 (`*` 불가) |
| `SYNC_SECRET` | | `/api/sync` 보호용 시크릿. 비우면 동기화 API 비활성(503) |
| `SYNC_ON_STARTUP` | | 서버 기동 시 동기화 정책: `never`(기본) / `always` / `if_empty` |

> `.env`와 `app.db`는 커밋하지 않습니다.

**데이터 적재** (최초 1회, 이후 갱신 시마다):

```bash
python ingest.py
```

KOPIS 공연·공연시설 → 예매상황판 랭킹 → 놀이시설 순서로 수집해 `backend/app.db`에 저장합니다.

**서버 실행:**

```bash
uvicorn main:app --reload
```

- API 문서(Swagger): http://127.0.0.1:8000/docs
- 헬스체크: http://127.0.0.1:8000/api/health

### 3. 프론트엔드

```bash
cd frontend
npm install
npm run dev
```

- 개발 서버: http://localhost:5173
- 백엔드 주소는 기본값 `http://127.0.0.1:8000`이며, 바꾸려면 `frontend/.env`에 `VITE_API_BASE_URL`을 지정합니다.
- 프로덕션 빌드: `npm run build` → `frontend/dist/`

---

## API 명세

| Method | Path | 설명 | 주요 파라미터 |
|---|---|---|---|
| GET | `/api/health` | 서버 상태, 최근 적재 시각, 동기화 상태 | — |
| GET | `/api/regions` | 시도·구군 코드 목록 | — |
| GET | `/api/performances` | 공연 목록 | `q`, `sido`, `gugun`, `prfstate`(공연예정/공연중), `shcate`, `from`, `to`, `sort`(soon/name), `page`, `size`(≤100) |
| GET | `/api/performances/batch` | 공연 일괄 조회 (즐겨찾기용) | `ids=PF1,PF2,...` (최대 100) |
| GET | `/api/performances/{mt20id}` | 공연 상세 (공연장·예매처·이미지 포함) | — |
| GET | `/api/playgrounds/nearby` | 인근 놀이시설 (거리순) | `lat`, `lng`, `radius`(기본 1000m), `limit`(기본·최대 20) |
| GET | `/api/rankings` | 아동 공연 예매 랭킹 | `limit`(기본 10, 최대 50) |
| POST | `/api/sync` | 데이터 동기화 시작 (백그라운드) | 헤더 `X-Sync-Secret` |
| GET | `/api/sync/status` | 동기화 진행 상태 | 헤더 `X-Sync-Secret` |

- 응답 필드는 KOPIS 원본과 대조하기 쉽도록 **snake_case**를 유지합니다.
- 목록 응답 형식: `{ "total", "page", "size", "items": [...] }`
- 오류 응답 형식: `{ "code": "...", "message": "..." }`

---

## 데이터 모델

`backend/models.py`에 정의되어 있으며, 서버 기동 시 테이블이 자동 생성됩니다.

| 테이블 | 설명 |
|---|---|
| `performances` | 공연 기본·상세 정보 |
| `performance_relates` | 공연별 예매처 링크 |
| `performance_images` | 공연 소개 이미지 |
| `venues` | 공연시설 정보 및 좌표 |
| `playgrounds` | 어린이 놀이시설 정보 및 좌표 |
| `boxoffice_rankings` | 예매상황판 랭킹 |
| `ingest_logs` | 데이터 적재 이력 |

---

## 테스트

```bash
cd backend
python -m unittest -v
```

---

## 데이터 출처

- 공연 정보: 공연예술통합전산망(KOPIS) OPEN API
- 놀이시설 정보: 행정안전부 전국어린이놀이시설정보서비스
- 지도: © OpenStreetMap contributors

서비스 화면 하단에 위 출처와 최종 갱신일을 표기합니다.

---

## 참고 문서

| 문서 | 내용 |
|---|---|
| [docs/PRD.md](docs/PRD.md) | 제품 요구사항 정의서 |
| [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) | 개발 계획 |
| [docs/TASKS.md](docs/TASKS.md) | 작업 목록 및 진행 현황 |
| [docs/KOPIS_SERVICE_API.md](docs/KOPIS_SERVICE_API.md) | KOPIS API 정리 |
| [docs/PLAYGROUND_SERVICE_API.md](docs/PLAYGROUND_SERVICE_API.md) | 놀이시설 API 정리 |
| [docs/kopis_openapi_code_v3.7.md](docs/kopis_openapi_code_v3.7.md) | KOPIS 코드표 |
