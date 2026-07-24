"""
범용 보일러플레이트 - 백엔드 (FastAPI + SQLite)
================================================
'작동하는 최소 뼈대'입니다. 서버 실행 · CORS · DB 연결까지 다 되어 있어요.
여기에 **데이터 모델(도메인)만** AI(Cursor)에게 시켜서 추가하면 됩니다.

실행:
    pip install -r requirements.txt
    uvicorn main:app --reload
    → 브라우저에서 http://127.0.0.1:8000/health 로 확인
"""
import math
import logging
from contextlib import asynccontextmanager
from datetime import date
from typing import Literal

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import and_, event, func, or_
from sqlmodel import Session, SQLModel, create_engine, select
from starlette.exceptions import HTTPException

import models  # noqa: F401  # SQLModel 메타데이터에 테이블을 등록한다.
from config import get_cors_origins, get_sync_on_startup, get_sync_secret
from db_migrate import ensure_performance_shcate_column
from sync_service import (
    count_performances,
    get_sync_state,
    is_sync_running,
    start_sync_background,
)
from genre_codes import SHCATE_CODES
from models import (
    BoxofficeRanking,
    IngestLog,
    Performance,
    PerformanceImage,
    PerformanceRelate,
    Playground,
    Venue,
)
from region_codes import REGIONS
from schemas import (
    GugunResponse,
    ListResponse,
    NearbyPlaygroundsResponse,
    PerformanceDetailResponse,
    PerformanceImageResponse,
    PerformanceListItem,
    PerformanceRelateResponse,
    PlaygroundNearbyItem,
    RankingItem,
    RegionResponse,
    VenueDetailResponse,
)

logger = logging.getLogger(__name__)

REGION_BY_CODE = {
    code: (name, guguns)
    for code, name, guguns in REGIONS
}
GUGUN_BY_CODE = {
    gugun_code: (region_code, gugun_name)
    for region_code, _, guguns in REGIONS
    for gugun_code, gugun_name in guguns
}
REGION_NAME_ALIASES = {
    "45": ("전북특별자치도",),
}
EARTH_RADIUS_M = 6_371_000


def haversine_distance_m(
    lat1: float,
    lng1: float,
    lat2: float,
    lng2: float,
) -> float:
    """두 위경도 사이의 대권 거리를 미터 단위로 계산한다."""
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    haversine = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(delta_lng / 2) ** 2
    )
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(min(1.0, haversine)))

# --------------------------------------------------------------------------
# [배선] DB 연결 (SQLite) — 이 부분은 그대로 두고, 아래에 모델만 추가하면 됩니다.
#   · check_same_thread=False : FastAPI에서 SQLite를 쓸 때 필요한 설정
#     (이걸 빠뜨리면 초보가 잡기 어려운 에러가 나서, 미리 넣어 둠)
# --------------------------------------------------------------------------
engine = create_engine("sqlite:///app.db", connect_args={"check_same_thread": False})


@event.listens_for(engine, "connect")
def enable_sqlite_wal(dbapi_connection, connection_record):
    """동시 읽기와 배치 쓰기가 서로 막지 않도록 WAL 모드를 유지한다."""
    del connection_record
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


def _should_start_startup_sync() -> bool:
    """기동 시 공공 API 동기화 여부를 SYNC_ON_STARTUP 정책으로 결정한다."""
    policy = get_sync_on_startup()
    if policy == "never":
        return False
    if policy == "always":
        return True
    return count_performances(engine) == 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버가 켜질 때, 정의된 모델들의 테이블을 자동으로 만든다.
    # (아직 모델이 없으면 아무것도 안 만들어짐 → 모델을 추가하면 그때 테이블 생성)
    SQLModel.metadata.create_all(engine)
    ensure_performance_shcate_column(engine)
    if _should_start_startup_sync():
        started = start_sync_background(trigger="startup")
        if started:
            logger.info("기동 시 데이터 동기화를 백그라운드로 시작했습니다.")
        else:
            logger.info("기동 시 동기화를 건너뜁니다(이미 실행 중).")
    yield


app = FastAPI(title="My App API", lifespan=lifespan)

# 허용한 프론트엔드 오리진만 API에 접근할 수 있다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    del request
    detail = exc.detail
    if isinstance(detail, dict):
        code = str(detail.get("code", f"HTTP_{exc.status_code}"))
        message = str(detail.get("message", "요청을 처리할 수 없습니다."))
    else:
        code = f"HTTP_{exc.status_code}"
        message = str(detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": code, "message": message},
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    del request, exc
    return JSONResponse(
        status_code=422,
        content={
            "code": "VALIDATION_ERROR",
            "message": "요청 값이 올바르지 않습니다.",
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    del request
    logger.exception("처리되지 않은 서버 오류", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_SERVER_ERROR",
            "message": "서버에서 요청을 처리하지 못했습니다.",
        },
    )


@app.get("/")
def root():
    return {"message": "API 살아있음. /api/health 로 확인하세요."}


@app.get("/api/health")
@app.get("/health")
def health():
    """서버 상태와 가장 최근에 완료된 데이터 적재 시각을 반환한다."""
    with Session(engine) as session:
        last_ingested_at = session.exec(
            select(IngestLog.finished_at)
            .where(IngestLog.finished_at.is_not(None))
            .order_by(IngestLog.finished_at.desc())
            .limit(1)
        ).first()

    sync = get_sync_state()
    return {
        "status": "ok",
        "last_ingested_at": last_ingested_at,
        "sync_status": sync["status"],
    }


def _require_sync_secret(request: Request) -> None:
    """X-Sync-Secret 헤더가 설정된 SYNC_SECRET과 일치하는지 검사한다."""
    configured = get_sync_secret()
    if not configured:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "SYNC_DISABLED",
                "message": "SYNC_SECRET이 설정되지 않아 동기화 API를 사용할 수 없습니다.",
            },
        )
    provided = request.headers.get("X-Sync-Secret", "").strip()
    if not provided or provided != configured:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "UNAUTHORIZED",
                "message": "동기화 시크릿이 올바르지 않습니다.",
            },
        )


@app.get("/api/sync/status")
def sync_status(request: Request):
    """동기화 진행 상태를 반환한다. SYNC_SECRET 필요."""
    _require_sync_secret(request)
    return get_sync_state()


@app.post("/api/sync")
async def trigger_sync(request: Request):
    """
    KOPIS·행안부 API에서 데이터를 받아 SQLite에 동기화한다.
    배포 직후나 수동 갱신 시 사용하며, 백그라운드로 실행된다.
    """
    _require_sync_secret(request)
    if is_sync_running():
        raise HTTPException(
            status_code=409,
            detail={
                "code": "SYNC_IN_PROGRESS",
                "message": "동기화가 이미 진행 중입니다.",
            },
        )
    started = start_sync_background(trigger="api")
    if not started:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "SYNC_IN_PROGRESS",
                "message": "동기화가 이미 진행 중입니다.",
            },
        )
    return {
        "code": "SYNC_STARTED",
        "message": "동기화를 시작했습니다. /api/sync/status 로 진행 상태를 확인하세요.",
        "state": get_sync_state(),
    }


@app.get("/api/regions", response_model=ListResponse[RegionResponse])
def regions():
    """KOPIS 행정표준코드 기준 시도와 하위 구군 목록을 반환한다."""
    items = [
        RegionResponse(
            code=code,
            name=name,
            guguns=[
                GugunResponse(code=gugun_code, name=gugun_name)
                for gugun_code, gugun_name in guguns
            ],
        )
        for code, name, guguns in REGIONS
    ]
    return ListResponse[RegionResponse](
        total=len(items),
        page=1,
        size=len(items),
        items=items,
    )


@app.get(
    "/api/performances",
    response_model=ListResponse[PerformanceListItem],
)
def performances(
    q: str | None = Query(default=None, max_length=100),
    sido: str | None = Query(default=None, pattern=r"^\d{2}$"),
    gugun: str | None = Query(default=None, pattern=r"^\d{4}$"),
    prfstate: Literal["공연예정", "공연중"] | None = None,
    shcate: str | None = Query(default=None, pattern=r"^[A-Z]{4}$"),
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    sort: Literal["soon", "name"] = "soon",
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    """공연명·공연 기간 조건에 맞는 공연 목록을 정렬해 반환한다."""
    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INVALID_DATE_RANGE",
                "message": "from은 to보다 늦을 수 없습니다.",
            },
        )
    if shcate and shcate not in SHCATE_CODES:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INVALID_SHCATE",
                "message": "지원하지 않는 장르 코드입니다.",
            },
        )

    filters = []
    if q:
        normalized_q = "".join(q.split()).lower()
        if normalized_q:
            normalized_name = func.lower(
                func.replace(
                    func.replace(
                        func.replace(
                            func.replace(Performance.prfnm, " ", ""),
                            "\t",
                            "",
                        ),
                        "\r",
                        "",
                    ),
                    "\n",
                    "",
                )
            )
            filters.append(normalized_name.contains(normalized_q))
    if sido:
        region = REGION_BY_CODE.get(sido)
        if region is None:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "INVALID_REGION_CODE",
                    "message": "존재하지 않는 시도 코드입니다.",
                },
            )
        region_names = (region[0], *REGION_NAME_ALIASES.get(sido, ()))
        filters.append(
            or_(
                Performance.signgucode == sido,
                and_(
                    Performance.signgucode.is_(None),
                    Performance.area.in_(region_names),
                ),
            )
        )
    if gugun:
        gugun_info = GUGUN_BY_CODE.get(gugun)
        if gugun_info is None:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "INVALID_REGION_CODE",
                    "message": "존재하지 않는 구군 코드입니다.",
                },
            )
        parent_code, gugun_name = gugun_info
        if sido and sido != parent_code:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "REGION_CODE_MISMATCH",
                    "message": "구군 코드가 선택한 시도에 속하지 않습니다.",
                },
            )
        parent_name = REGION_BY_CODE[parent_code][0]
        if gugun.endswith("00"):
            address_filters = [
                Venue.adres.startswith(name)
                for name in (
                    parent_name,
                    *REGION_NAME_ALIASES.get(parent_code, ()),
                )
            ]
        else:
            address_filters = [
                Venue.adres.startswith(f"{name} {gugun_name}")
                for name in (
                    parent_name,
                    *REGION_NAME_ALIASES.get(parent_code, ()),
                )
            ]
        filters.append(
            or_(
                Performance.signgucodesub == gugun,
                and_(
                    Performance.signgucodesub.is_(None),
                    or_(*address_filters),
                ),
            )
        )
    if from_date:
        filters.append(Performance.prfpdto >= from_date.isoformat())
    if to_date:
        filters.append(Performance.prfpdfrom <= to_date.isoformat())
    if prfstate:
        filters.append(Performance.prfstate == prfstate)
    if shcate:
        filters.append(Performance.shcate == shcate)

    statement = (
        select(Performance)
        .outerjoin(Venue, Performance.mt10id == Venue.mt10id)
        .where(*filters)
    )
    if sort == "name":
        statement = statement.order_by(
            Performance.prfnm.asc(),
            Performance.mt20id.asc(),
        )
    else:
        statement = statement.order_by(
            Performance.prfpdfrom.is_(None),
            Performance.prfpdfrom.asc(),
            Performance.prfnm.asc(),
            Performance.mt20id.asc(),
        )
    statement = statement.offset((page - 1) * size).limit(size)

    with Session(engine) as session:
        total = session.exec(
            select(func.count())
            .select_from(Performance)
            .outerjoin(Venue, Performance.mt10id == Venue.mt10id)
            .where(*filters)
        ).one()
        rows = session.exec(statement).all()

    return ListResponse[PerformanceListItem](
        total=total,
        page=page,
        size=size,
        items=[
            PerformanceListItem.model_validate(row, from_attributes=True)
            for row in rows
        ],
    )


@app.get(
    "/api/performances/batch",
    response_model=ListResponse[PerformanceListItem],
)
def performance_batch(
    ids: str = Query(max_length=5000),
):
    """쉼표로 구분한 공연 ID를 최대 100건까지 요청 순서대로 반환한다."""
    requested_ids = [item.strip() for item in ids.split(",") if item.strip()]
    if not requested_ids:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "EMPTY_PERFORMANCE_IDS",
                "message": "공연 ID를 한 건 이상 입력해주세요.",
            },
        )
    if len(requested_ids) > 100:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "TOO_MANY_PERFORMANCE_IDS",
                "message": "공연 ID는 최대 100건까지 조회할 수 있습니다.",
            },
        )

    unique_ids = list(dict.fromkeys(requested_ids))
    with Session(engine) as session:
        rows = session.exec(
            select(Performance).where(Performance.mt20id.in_(unique_ids))
        ).all()

    performance_by_id = {row.mt20id: row for row in rows}
    found = [
        performance_by_id[mt20id]
        for mt20id in unique_ids
        if mt20id in performance_by_id
    ]
    return ListResponse[PerformanceListItem](
        total=len(found),
        page=1,
        size=len(unique_ids),
        items=[
            PerformanceListItem.model_validate(row, from_attributes=True)
            for row in found
        ],
    )


@app.get(
    "/api/performances/{mt20id}",
    response_model=PerformanceDetailResponse,
)
def performance_detail(mt20id: str):
    """SQLite에 적재된 공연·공연장·예매처·소개 이미지를 병합해 반환한다."""
    with Session(engine) as session:
        performance = session.get(Performance, mt20id)
        if performance is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "PERFORMANCE_NOT_FOUND",
                    "message": "공연 정보를 찾을 수 없습니다.",
                },
            )

        venue = (
            session.get(Venue, performance.mt10id)
            if performance.mt10id
            else None
        )
        relates = session.exec(
            select(PerformanceRelate)
            .where(PerformanceRelate.mt20id == mt20id)
            .order_by(PerformanceRelate.sort_no.asc())
        ).all()
        images = session.exec(
            select(PerformanceImage)
            .where(PerformanceImage.mt20id == mt20id)
            .order_by(PerformanceImage.sort_no.asc())
        ).all()

    return PerformanceDetailResponse(
        **performance.model_dump(),
        venue=(
            VenueDetailResponse.model_validate(venue, from_attributes=True)
            if venue
            else None
        ),
        relates=[
            PerformanceRelateResponse.model_validate(
                relate,
                from_attributes=True,
            )
            for relate in relates
        ],
        images=[
            PerformanceImageResponse.model_validate(image, from_attributes=True)
            for image in images
        ],
    )


@app.get(
    "/api/playgrounds/nearby",
    response_model=NearbyPlaygroundsResponse,
)
def nearby_playgrounds(
    lat: float = Query(ge=-90, le=90),
    lng: float = Query(ge=-180, le=180),
    radius: int = Query(default=1000, ge=1),
    limit: int = Query(default=20, ge=1, le=20),
):
    """Bounding Box로 후보를 줄인 뒤 Haversine 거리순으로 반환한다."""
    angular_distance = radius / EARTH_RADIUS_M
    lat_delta = math.degrees(angular_distance)
    min_lat = max(-90.0, lat - lat_delta)
    max_lat = min(90.0, lat + lat_delta)

    candidate_filters = [
        Playground.lat.is_not(None),
        Playground.lng.is_not(None),
        Playground.lat.between(min_lat, max_lat),
    ]
    cos_lat = abs(math.cos(math.radians(lat)))
    if cos_lat > 0 and lat_delta < 180:
        lng_delta = min(180.0, math.degrees(angular_distance / cos_lat))
        if lng_delta < 180:
            min_lng = lng - lng_delta
            max_lng = lng + lng_delta
            if min_lng < -180:
                candidate_filters.append(
                    or_(
                        Playground.lng >= min_lng + 360,
                        Playground.lng <= max_lng,
                    )
                )
            elif max_lng > 180:
                candidate_filters.append(
                    or_(
                        Playground.lng >= min_lng,
                        Playground.lng <= max_lng - 360,
                    )
                )
            else:
                candidate_filters.append(
                    Playground.lng.between(min_lng, max_lng)
                )

    with Session(engine) as session:
        candidates = session.exec(
            select(Playground).where(*candidate_filters)
        ).all()

    nearby = []
    for playground in candidates:
        if playground.lat is None or playground.lng is None:
            continue
        distance = haversine_distance_m(
            lat,
            lng,
            playground.lat,
            playground.lng,
        )
        if distance <= radius:
            nearby.append((distance, playground))
    nearby.sort(key=lambda item: (item[0], item[1].pfct_sn))
    public_nearby = [
        item for item in nearby if item[1].is_public_access == 1
    ]
    fallback_used = not public_nearby and bool(nearby)
    selected = nearby if fallback_used else public_nearby

    return NearbyPlaygroundsResponse(
        total=len(selected),
        page=1,
        size=limit,
        fallback_used=fallback_used,
        items=[
            PlaygroundNearbyItem(
                **playground.model_dump(),
                distance_m=round(distance),
            )
            for distance, playground in selected[:limit]
        ],
    )


@app.get(
    "/api/rankings",
    response_model=ListResponse[RankingItem],
)
def rankings(
    limit: int = Query(default=10, ge=1, le=50),
    catecode: Literal["KID"] = "KID",
):
    """사전 적재된 예매상황판 아동 공연 랭킹을 순위순으로 반환한다."""
    with Session(engine) as session:
        rows = session.exec(
            select(BoxofficeRanking)
            .where(BoxofficeRanking.catecode == catecode)
            .order_by(BoxofficeRanking.rnum.asc(), BoxofficeRanking.id.asc())
            .limit(limit)
        ).all()
        total = session.exec(
            select(func.count())
            .select_from(BoxofficeRanking)
            .where(BoxofficeRanking.catecode == catecode)
        ).one()

    return ListResponse[RankingItem](
        total=total,
        page=1,
        size=limit,
        items=[
            RankingItem.model_validate(row, from_attributes=True)
            for row in rows
        ],
    )


# ==========================================================================
# 여기서부터 여러분이 (AI에게 시켜서) 만듭니다.
#   DB 연결은 위에 이미 되어 있으니, 데이터 모델과 API만 추가하면 됩니다.
#   예: "축제(Festival) 모델을 만들어줘. 이름·장소·기간·좌표를 담고 SQLite에 저장되게."
# ==========================================================================
