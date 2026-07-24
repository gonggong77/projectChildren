"""서버 API에서 공통으로 사용하는 응답 스키마."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: str
    message: str


ItemT = TypeVar("ItemT")


class ListResponse(BaseModel, Generic[ItemT]):
    """목록 API가 공통으로 반환할 페이징 응답."""

    total: int = Field(ge=0)
    page: int = Field(ge=1)
    size: int = Field(ge=1)
    items: list[ItemT]


class GugunResponse(BaseModel):
    code: str = Field(pattern=r"^\d{4}$")
    name: str


class RegionResponse(BaseModel):
    code: str = Field(pattern=r"^\d{2}$")
    name: str
    guguns: list[GugunResponse]


class PerformanceListItem(BaseModel):
    mt20id: str
    prfnm: str
    prfpdfrom: str | None
    prfpdto: str | None
    poster: str | None
    fcltynm: str | None
    area: str | None
    prfstate: str | None


class PerformanceRelateResponse(BaseModel):
    relatenm: str | None
    relateurl: str | None


class PerformanceImageResponse(BaseModel):
    styurl: str | None


class VenueDetailResponse(BaseModel):
    mt10id: str
    fcltynm: str | None
    adres: str | None
    telno: str | None
    la: float | None
    lo: float | None
    parkinglot: str | None
    restaurant: str | None
    cafe: str | None
    store: str | None
    nolibang: str | None
    suyu: str | None
    parkbarrier: str | None
    restbarrier: str | None
    runwbarrier: str | None
    elevbarrier: str | None


class PerformanceDetailResponse(BaseModel):
    mt20id: str
    prfnm: str
    poster: str | None
    genrenm: str | None
    prfstate: str | None
    prfage: str | None
    prfruntime: str | None
    pcseguidance: str | None
    prfpdfrom: str | None
    prfpdto: str | None
    dtguidance: str | None
    fcltynm: str | None
    sty: str | None
    prfcast: str | None
    venue: VenueDetailResponse | None
    relates: list[PerformanceRelateResponse]
    images: list[PerformanceImageResponse]


class PlaygroundNearbyItem(BaseModel):
    pfct_sn: str
    pfct_nm: str
    instl_place_cd: str | None
    instl_place_nm: str | None
    road_addr: str | None
    lotno_addr: str | None
    zip: str | None
    lat: float
    lng: float
    wowa_styl_ride_cd: str | None
    indoor_yn: str | None
    distance_m: int = Field(ge=0)


class NearbyPlaygroundsResponse(BaseModel):
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    size: int = Field(ge=1)
    fallback_used: bool
    items: list[PlaygroundNearbyItem]


class RankingItem(BaseModel):
    rnum: int = Field(ge=1)
    mt20id: str | None
    prfnm: str | None
    prfpd: str | None
    prfplcnm: str | None
    area: str | None
    poster: str | None
    cate: str | None
    seatcnt: int | None
    prfdtcnt: int | None
    stdate: str | None
    eddate: str | None
