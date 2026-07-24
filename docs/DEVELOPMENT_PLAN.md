# 키즈스테이지(KidsStage) 개발 계획

| 항목 | 내용 |
|---|---|
| 근거 문서 | `docs/PRD.md` v1.0 |
| 작성일 | 2026-07-24 |
| 대상 | MVP(1차) → Should → Later |
| 전제 | 보일러플레이트·conda 환경(`children`) 세팅 완료. 프로젝트 생성·환경 설정·scaffold는 **제외** |

---

## 0. 현재 상태 (기준점)

작업 전 확인한 최상위 구조:

```
projectChildren/
├── backend/          # FastAPI + Uvicorn + SQLModel + SQLite + CORS + /health
│   ├── main.py
│   ├── requirements.txt
│   ├── .env
│   └── app.db
├── frontend/         # React + Vite, /health 연결 확인만 구현
│   └── src/ (App.jsx, api.js, …)
└── docs/             # PRD, KOPIS/놀이시설 API 명세
```

**이미 있는 것**: 서버 기동, CORS, SQLite 엔진 연결, 프론트↔백엔드 헬스체크  
**없는 것**: 도메인 모델, Ingestion Worker, `/api/*` 비즈니스 API, 화면·라우팅·지도·즐겨찾기

이 계획은 위 뼈대 **위에서** 기능 구현만 다룬다.

---

## 1. 개발 원칙

1. **한 번에 하나의 기능** — PRD F1 → F2 → F3 → F4 → F5 → F6 순으로 진행 (`docs/TASKS.md` 체크리스트와 동기화)
2. **백엔드 먼저, 프론트 나중** — 각 기능마다 데이터 적재·서버 API를 먼저 만들고, 그다음 React 화면을 붙인다
3. **전량 사전 적재** — 사용자 요청 경로에서 KOPIS·행안부 API를 호출하지 않는다. Ingestion Worker만 외부 API를 호출한다 (PRD 8.1, AC-12)
4. **설계 의사결정 준수** — D1~D5 권장안을 그대로 따른다. 임의 대안 선택 금지
5. **미검증 항목은 실호출 후 구현** — O1~O7, `prfplc` URL 등은 1건 실호출로 확인한 뒤 매핑한다
6. **비밀값** — `service` / `serviceKey`는 `.env`만 사용, 코드·리포지토리 하드코딩 금지
7. **응답 필드** — 서버 API는 PRD 8.4의 **snake_case** 원본 필드명 유지 (camelCase 변환 금지)

---

## 2. 전체 개발 순서 (한눈에)

```
[Phase 0] 착수 검증 (O1~O5, prfplc URL)
    ↓
[Phase 1] 데이터 기반 (스키마 + Ingestion Worker)          ← M9
    ↓
[Phase 2] 서버 읽기 API (/api/*)                           ← M1~M6 백엔드
    ↓
[Phase 3] 프론트 공통 골격 (라우팅·레이아웃·API 클라이언트)
    ↓
[Phase 4] F1 공연 검색·목록                                ← M1, M3
    ↓
[Phase 5] F2 지역 필터 (+ URL 쿼리 유지)                   ← M2
    ↓
[Phase 6] F3 공연 상세                                     ← M4
    ↓
[Phase 7] F4 지도 (Leaflet)                                ← M5
    ↓
[Phase 8] F5 인근 놀이시설 목록·아코디언                   ← M6, M7
    ↓
[Phase 9] F6 즐겨찾기 (localStorage)                       ← M8
    ↓
[Phase 10] MVP 품질·DoD (AC-1~AC-12, 푸터·CORS 등)
    ↓
[Phase 11] Should (여유 시)
    ↓
[Phase 12] Later (지시 있을 때만)
```

**흐름 요약**: Ingestion(외부 API → SQLite) → FastAPI(읽기 전용 `/api/*`) → React(화면·Leaflet·localStorage)

---

## 3. Phase 0 — 착수 검증 (코드 전 확인)

구현에 들어가기 전, PRD 9.3 미결 이슈를 **실호출 1건**으로 닫는다.

| ID | 확인 내용 | 결과에 따른 조치 |
|---|---|---|
| O3 | 공연시설 상세 URL: `prfplc` vs `pblprfr` | **예제 기준 `prfplc`로 구현** (PRD 8.3). 실패 시 경로 수정 |
| O1 | 놀이시설 API 좌표 필드 제공 여부 | 있으면 D2-A 사용. 없으면 D2-C(CSV) → D2-B(지오코딩) 폴백 |
| O2 | 주소·좌표 등 응답 필드명 확정 | DB·API 매핑 테이블 확정 |
| O4 | `recordCountPerPage` 상한 | 페이지 크기·적재 시간 산정 |
| O5 | 개발계정 일 10,000건으로 전국 적재 가능 여부 | 초과 시 분할 적재 또는 운영계정 신청 |

참고 문서: `docs/KOPIS_SERVICE_API.md`, `docs/PLAYGROUND_SERVICE_API.md`, `docs/kopis_openapi_code_v3.7.md`

---

## 4. Phase 1 — 데이터 기반 (백엔드 / M9)

### 4.1 목표
공연·공연장·놀이시설을 SQLite에 넣고, 배치를 재실행할 수 있게 한다.

### 4.2 작업 내용
1. **스키마** — PRD 8.6 테이블 구현  
   `performances`, `performance_relates`, `performance_images`, `venues`, `playgrounds`, `ingest_logs`  
   + 인덱스 `idx_pg_bbox`, `idx_perf_search`  
   + WAL 모드
2. **환경 변수** — KOPIS `service`, 행안부 `serviceKey`를 `.env`에서 로드
3. **Ingestion Worker** (`ingest.py` 등, 동일 코드베이스)
   - **공연**: `kidstate=Y`만 수집 (D3-A). 기간은 오늘~+90일을 **31일 단위 3회** 분할 (D5-A). `rows`≤100, 페이징
   - **공연 상세 + 시설 상세**: 목록의 `mt20id` / `mt10id`로 상세 적재. 시설은 **`/prfplc/{mt10id}`**
   - **`prfage` 정규화**: `prfage_min_norm` 컬럼에만 저장 (화면 필터에는 미사용, D3)
   - **놀이시설**: 전국 전량 적재 후 서버에서 공간 필터 (지역 파라미터 없음). 좌표는 D2 **A→C→B** 폴백. 좌표 없는 시설은 **제외**
   - **D4 화이트리스트**: `is_public_access` 플래그 (부록 B 공공 개방 코드)
   - **주기**: 공연·공연장 **1일 1회(새벽 4시) 전체 재적재**, 놀이시설 **주 1회** (D5)
   - 결과를 `ingest_logs`에 기록 (AC-11)

### 4.3 완료 조건
- 배치 1회 실행으로 SQLite에 공연·공연장·놀이시설이 들어가고 `ingest_logs`에 기록이 남는다

---

## 5. Phase 2 — 서버 읽기 API (백엔드)

사용자 요청은 **SQLite 조회만**. 외부 API 호출 없음.

| 순서 | Endpoint | 대응 기능 | 비고 |
|---|---|---|---|
| 1 | `GET /api/health` | 운영 | 기존 `/health`를 확장하거나 `/api/health` 추가 — 최종 적재 시각 포함 |
| 2 | `GET /api/regions` | F2 | 시도(2자리)·구군(4자리) 행정표준코드 |
| 3 | `GET /api/performances` | F1, F2 | `q`, `sido`, `gugun`, `from`, `to`, `state`, `sort`, `page`, `size` |
| 4 | `GET /api/performances/{mt20id}` | F3 | 공연 + 공연장 병합. PRD 4절 노출 필드 |
| 5 | `GET /api/performances/batch` | F6 | `ids=` 최대 100 |
| 6 | `GET /api/playgrounds/nearby` | F5 | `lat`, `lng`, `radius`(기본 1000), `limit`(기본 20) |

### 공간 검색 (D1-A)
1. Bounding Box로 SQL 1차 필터  
2. Python Haversine으로 거리 계산·정렬  
3. 놀이시설 5만 건 초과 또는 p95 > 300ms 전까지 R*Tree(B안)로 **전환하지 않음**

### 놀이시설 노출 (D4)
- 기본: 화이트리스트(`is_public_access=1`)만  
- 0건일 때만 전량 노출 폴백(또는 “다른 놀이시설도 보기”용 결과) — PRD 권장안 준수

### 공통
- 목록 응답: `total`, `page`, `size`
- 오류: `{"code": "...", "message": "..."}`
- CORS: 허용 오리진 화이트리스트로 축소 (교육용 `*`에서 이행)

---

## 6. Phase 3 — 프론트 공통 골격

기능 화면 전에 공통 뼈대만 잡는다. (아직 도메인 UI 최소화)

1. React Router — S1 `/`, S2 `/performances/:mt20id`, S3 `/favorites`, S4 `*`
2. 상단 헤더(로고, 즐겨찾기 진입) · 하단 푸터(KOPIS·행안부 출처, 최종 갱신일)
3. `/api/*`만 호출하는 API 클라이언트 (기존 `api.js` 확장). 외부 공공 API 직접 호출 금지
4. (선택) TanStack Query 또는 fetch 래퍼 훅 — PRD 8.2
5. 공통 상태: 스켈레톤·빈 결과·5xx 재시도·부분 실패 격리 패턴

**추가 의존성**: `react-router-dom`, `leaflet` + `react-leaflet` (지도 Phase에서 도입 가능). PRD 8.2 밖 라이브러리는 꼭 필요할 때만.

---

## 7. Phase 4~9 — MVP 기능 (프론트, F1→F6)

각 Phase는 **해당 `/api`가 준비된 뒤** UI를 붙인다.

### Phase 4 — F1 어린이 공연 검색·목록 (M1, M3)
- 포스터 카드 그리드 (모바일 2 / 태블릿 3 / 데스크톱 4)
- 공연명 키워드 검색 (부분 일치)
- 정렬: 임박순(기본), 공연명순
- **더 보기** 버튼, 20건 단위
- 카드: 포스터, 공연명, 기간, 시설명, 지역, 상태 배지 (하트는 F6에서)
- 빈 상태 + 필터 초기화
- 스켈레톤(3:4), 포스터 실패 시 플레이스홀더, `loading="lazy"`

### Phase 5 — F2 지역 필터 (M2)
- 시도 → 구군 2단계 (`/api/regions`)
- 선택값을 URL 쿼리(`sido`, `gugun`, `q`, `page` 등)에 반영 — 공유·새로고침·뒤로가기 유지

### Phase 6 — F3 공연 상세 (M4)
- PRD 4절 표의 노출 필드만 표시 (MVP 제외 KOPIS 필드는 화면 미노출; `updatedate`는 DB만)
- 관람 핵심·공연장·편의시설 배지·무장애·예매 링크(외부 탭)·줄거리 접기/펼치기·소개 이미지
- 좌표 없음: 지도·놀이시설 대신 안내 문구 (AC-10) — F4/F5와 함께 Graceful degradation

### Phase 7 — F4 지도 (M5)
- Leaflet, 줌 15, 공연장 강조 마커 + 놀이시설 마커(최대 20)
- OSM 타일 + 출처 표기 (O6 정책 확인)
- 지도 ↔ 목록 양방향 연동은 F5와 함께 완성

### Phase 8 — F5 인근 놀이시설 (M6, M7)
- 반경 1km 기본, 0건 시 3km 1회 재조회
- 거리순 아코디언(단일 확장), 접힘/펼침 필드, 도보 근사(÷67m/분)
- 놀이시설 섹션 실패 시 상세 나머지는 유지 (부분 실패 격리)

### Phase 9 — F6 즐겨찾기 (M8)
- `localStorage` 키 `kidsstage:favorites` (ID 배열 + 저장 시각)
- 목록·상세 하트 토글(낙관적 업데이트)
- `/favorites`에서 `/api/performances/batch`로 최신 정보 재조회
- 삭제·조회 실패 ID 자동 정리 + 토스트
- 기기 간 비동기화 한계 문구 1줄

---

## 8. Phase 10 — MVP 출시 품질 (DoD)

PRD 9.1~9.2를 통과할 때까지 점검한다.

| 구분 | 확인 |
|---|---|
| AC-1~AC-12 | 기능 수용 기준 전부 |
| 성능 | 목록 p95 &lt; 300ms, 상세 p95 &lt; 500ms (로컬 SQLite) |
| 보안 | 브라우저에 서비스 키·외부 API 호출 0건 |
| 접근성 | 아코디언 키보드, `alt`, 명도 대비 |
| 문서 | README에 키 발급 → 배치 → 서버 기동 (conda `children`) 절차 |

---

## 9. Phase 11 — Should (여유 시, Must 완료 후)

지시 없이 선행하지 않는다. Must(M1~M9) 완료 후 여유 있을 때만.

| 항목 | 내용 |
|---|---|
| S-1 | 공연상태 필터 (공연예정/공연중) — `state` 파라미터 UI |
| S-2 | 놀이시설 반경 1km / 3km 토글 |
| S-3 | 헤더 즐겨찾기 개수 배지 |

---

## 10. Phase 12 — Later (지시 있을 때만)

| 항목 | 내용 |
|---|---|
| L-1 | 장르 필터 (`shcate`) |
| L-2 | 예매상황판 기반 인기 어린이 공연 랭킹 (`/boxoffice`, `catecode=KID`) |
| L-3 | 축제 목록 API (`/prffest`) 연계 |

**명시적 제외(만들지 않음)**: 로그인, 리뷰, 결제/예매, 관리자 화면, 푸시, 네이티브 앱, 다국어, SSR/SEO 최적화 등 (PRD 7절)

---

## 11. 권장 구현 단위 (작업 시 참고)

에이전트·개발자 모두 **한 체크리스트 항목 = 한 세션**을 권장한다.

예:
1. Phase 0 검증 메모 → 스키마 → 공연 배치 → 놀이시설 배치  
2. `/api/performances` → 목록 UI  
3. `/api/regions` + 지역 필터 UI  
4. 상세 API → 상세 UI → nearby API → 지도·아코디언 → 즐겨찾기

세부 체크박스는 `docs/TASKS.md`를 따른다. 작업 완료 시 해당 항목을 체크한다.

---

## 12. 리스크·의존성 요약

| 리스크 | 완화 |
|---|---|
| 놀이시설 좌표 미제공 (O1) | D2 A→C→B, 좌표 없는 시설 제외 |
| 일 호출 한도 (O5) | 페이지 크기 최적화, 분할 적재, 필요 시 운영계정 |
| OSM 타일 정책 (O6) | 출처 표기, 트래픽 증가 시 타일 제공처 재검토 |
| `kidstate` 누락 (D3) | MVP는 A안 유지, `prfage_min_norm`만 적재해 출시 후 측정 |
| 화이트리스트 0건 (D4) | 0건일 때만 전량 폴백 |

---

## 13. 산출물 맵

| 단계 | 주요 산출물 (예상) |
|---|---|
| Phase 1 | `backend` 스키마, `ingest.py`(또는 동등), SQLite 데이터, `ingest_logs` |
| Phase 2 | `GET /api/performances`, `.../{id}`, `.../batch`, `/api/playgrounds/nearby`, `/api/regions`, `/api/health` |
| Phase 3~9 | `frontend` 라우트·페이지·컴포넌트, Leaflet, localStorage 즐겨찾기 |
| Phase 10 | AC 통과, README 운영 절차 갱신 |
