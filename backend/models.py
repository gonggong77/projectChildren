"""키즈스테이지 SQLite 테이블 모델."""

from sqlalchemy import Index
from sqlmodel import Field, SQLModel


class Venue(SQLModel, table=True):
    __tablename__ = "venues"

    mt10id: str = Field(primary_key=True)
    fcltynm: str | None = None
    adres: str | None = None
    telno: str | None = None
    relateurl: str | None = None
    la: float | None = None
    lo: float | None = None
    parkinglot: str | None = None
    restaurant: str | None = None
    cafe: str | None = None
    store: str | None = None
    nolibang: str | None = None
    suyu: str | None = None
    parkbarrier: str | None = None
    restbarrier: str | None = None
    runwbarrier: str | None = None
    elevbarrier: str | None = None
    seatscale: int | None = None
    sidonm: str | None = None
    gugunnm: str | None = None


class Performance(SQLModel, table=True):
    __tablename__ = "performances"
    __table_args__ = (
        Index(
            "idx_perf_search",
            "signgucode",
            "prfpdfrom",
            "prfpdto",
            "prfstate",
        ),
    )

    mt20id: str = Field(primary_key=True)
    prfnm: str
    prfpdfrom: str | None = None
    prfpdto: str | None = None
    fcltynm: str | None = None
    mt10id: str | None = Field(default=None, foreign_key="venues.mt10id")
    mt13id: str | None = None
    poster: str | None = None
    genrenm: str | None = None
    shcate: str | None = None
    prfstate: str | None = None
    area: str | None = None
    signgucode: str | None = None
    signgucodesub: str | None = None
    prfage: str | None = None
    prfage_min_norm: int | None = None
    prfruntime: str | None = None
    pcseguidance: str | None = None
    dtguidance: str | None = None
    sty: str | None = None
    prfcast: str | None = None
    openrun: str | None = None
    child: str | None = None
    updatedate: str | None = None
    detail_fetched_at: str | None = None


class PerformanceRelate(SQLModel, table=True):
    __tablename__ = "performance_relates"

    mt20id: str = Field(primary_key=True, foreign_key="performances.mt20id")
    relatenm: str | None = None
    relateurl: str | None = None
    sort_no: int = Field(primary_key=True)


class PerformanceImage(SQLModel, table=True):
    __tablename__ = "performance_images"

    mt20id: str = Field(primary_key=True, foreign_key="performances.mt20id")
    styurl: str | None = None
    sort_no: int = Field(primary_key=True)


class Playground(SQLModel, table=True):
    __tablename__ = "playgrounds"
    __table_args__ = (Index("idx_pg_bbox", "lat", "lng"),)

    pfct_sn: str = Field(primary_key=True)
    pfct_nm: str
    instl_place_cd: str | None = None
    instl_place_nm: str | None = None
    road_addr: str | None = None
    lotno_addr: str | None = None
    zip: str | None = None
    lat: float | None = None
    lng: float | None = None
    wowa_styl_ride_cd: str | None = None
    indoor_yn: str | None = None
    is_public_access: int | None = None
    updated_at: str | None = None


class IngestLog(SQLModel, table=True):
    __tablename__ = "ingest_logs"

    id: int | None = Field(default=None, primary_key=True)
    source: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    fetched: int | None = None
    upserted: int | None = None
    failed: int | None = None
    message: str | None = None


class BoxofficeRanking(SQLModel, table=True):
    """KOPIS 예매상황판(catecode=KID) 스냅샷."""

    __tablename__ = "boxoffice_rankings"
    __table_args__ = (Index("idx_boxoffice_rank", "catecode", "rnum"),)

    id: int | None = Field(default=None, primary_key=True)
    catecode: str = "KID"
    rnum: int
    mt20id: str | None = None
    prfnm: str | None = None
    prfpd: str | None = None
    prfplcnm: str | None = None
    area: str | None = None
    poster: str | None = None
    cate: str | None = None
    seatcnt: int | None = None
    prfdtcnt: int | None = None
    stdate: str | None = None
    eddate: str | None = None
    fetched_at: str | None = None
