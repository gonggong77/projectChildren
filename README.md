# 키즈스테이지(Kids Stage) – 어린이 공연 & 주변 놀이시설 찾기

전국의 **어린이 관람 가능 공연**을 한 곳에서 검색하고, 공연 상세 정보와 함께 **공연장 주변 어린이 놀이시설**까지 지도로 확인할 수 있는 웹서비스입니다.

> **현재 범위(MVP):** 공연 검색·상세·랭킹, 공연장 주변 놀이시설 지도, 즐겨찾기까지. 로그인·예매 기능은 포함하지 않습니다.

## 왜 만들었나

- 부모가 실제로 고민하는 건 "공연 티켓"이 아니라 **"아이와 함께하는 반나절 외출"**입니다.
- 어린이 공연 정보는 예매처마다 흩어져 있고, 관람연령·러닝타임·가격 같은 정보를 모으기 어렵습니다.
- 공연이 끝난 뒤 아이와 갈 놀이터는 지도 앱에서 따로 찾아야 합니다.
- 키즈스테이지는 `공연 → 공연장 좌표 → 반경 내 놀이시설`을 하나의 흐름으로 묶어 한 화면에서 보여 줍니다.

## 동작 흐름

1. 배치 수집(`ingest.py`) → KOPIS 어린이 공연·공연장·예매 랭킹, 행안부 놀이시설 데이터를 SQLite에 미리 적재
2. 사용자가 지역·기간·장르·공연상태로 공연 검색
3. 공연 상세 진입 → 공연 정보 + 공연장 정보 + 예매처 링크 표시
4. 공연장 좌표 기준 반경 1km 안의 놀이시설을 거리순으로 조회해 지도에 표시
5. 마음에 드는 공연은 즐겨찾기에 저장(로그인 없이 브라우저에 저장)

## 주요 기능

- **어린이 공연 검색:** 공연명 키워드, 시도·구군, 기간, 공연상태(공연예정/공연중), 장르 필터와 임박순·이름순 정렬
- **인기 랭킹:** KOPIS 예매상황판의 아동 공연 순위
- **공연 상세:** 관람연령·러닝타임·티켓가격·공연시간, 공연장 정보, 예매처 링크, 소개 이미지
- **주변 놀이시설 지도:** 공연장 반경 안의 놀이시설을 거리순 목록과 Leaflet 지도로 함께 표시 (핵심 차별 기능)
- **즐겨찾기:** `localStorage`에 저장하고, 다시 열 때 최신 공연 상태로 갱신
- **사전 적재 방식:** 외부 API는 배치에서만 호출하고, 사용자 요청은 로컬 DB에서 바로 응답

## 구조

```text
backend/                  API 서버 (FastAPI + SQLite)
├── main.py               진입점, API 엔드포인트
├── models.py             DB 테이블 정의
├── ingest.py             KOPIS·놀이시설 데이터 수집 → SQLite 적재
├── sync_service.py       백그라운드 동기화 (/api/sync, 서버 기동 시)
└── test_*.py             테스트
frontend/                 웹 화면 (React + Vite)
├── src/pages/            공연 목록, 공연 상세, 즐겨찾기
├── src/components/       공연 카드, 랭킹, 지도, 놀이시설 목록
└── src/api.js            백엔드 API 호출
docs/                     PRD, 개발 계획, 공공 API 정리 문서
```

## 기술 스택

| 영역 | 기술 |
| --- | --- |
| 웹 UI | React 19, Vite, React Router |
| 지도 | Leaflet, react-leaflet, OpenStreetMap |
| API 서버 | FastAPI, Uvicorn |
| 저장 | SQLite (WAL 모드), SQLModel |
| 데이터 수집 | httpx (비동기), KOPIS OpenAPI, 행정안전부 어린이놀이시설 API |

## 실행 방법

### 1. 백엔드

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env      # KOPIS_SERVICE_KEY, PLAYGROUND_SERVICE_KEY 입력
python ingest.py          # 공공 데이터 수집 → app.db 생성
uvicorn main:app --reload
```

### 2. 프론트엔드

```bash
cd frontend
npm install
npm run dev
```

- 브라우저에서 <http://localhost:5173> 접속 (API 문서: <http://127.0.0.1:8000/docs>)
- 서비스 키(`.env`)와 DB 파일(`app.db`)은 저장소에 포함되어 있지 않습니다. [KOPIS](https://www.kopis.or.kr)와 [공공데이터포털](https://www.data.go.kr)에서 키를 발급받아 넣어야 합니다.
- 백엔드 주소를 바꾸려면 `frontend/.env`에 `VITE_API_BASE_URL`을 지정합니다.

## 데이터 출처

- 공연 정보: 공연예술통합전산망(KOPIS)
- 놀이시설 정보: 행정안전부 전국어린이놀이시설정보서비스
- 지도: © OpenStreetMap contributors

## 향후 과제

- 축제 목록(KOPIS `/prffest`) 연계
- 공연장 편의시설(수유실·주차 등) 필터
- 배포 환경 자동 데이터 갱신 스케줄링
