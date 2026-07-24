"""외부 공공데이터를 SQLite에 사전 적재하는 배치 진입점."""

import asyncio
import math
import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from xml.etree import ElementTree

import httpx
from sqlalchemy import delete, event
from sqlmodel import Session, SQLModel, create_engine, select

from config import get_settings
from genre_codes import map_genrenm_to_shcate
from models import (
    BoxofficeRanking,
    IngestLog,
    Performance,
    PerformanceImage,
    PerformanceRelate,
    Playground,
    Venue,
)

KOPIS_PERFORMANCE_LIST_URL = (
    "https://www.kopis.or.kr/openApi/restful/pblprfr"
)
KOPIS_VENUE_DETAIL_URL = "https://www.kopis.or.kr/openApi/restful/prfplc"
KOPIS_BOXOFFICE_URL = "https://www.kopis.or.kr/openApi/restful/boxoffice"
PLAYGROUND_LIST_URL = "https://apis.data.go.kr/1741000/pfc3/getPfctInfo3"
KOPIS_ROWS_PER_PAGE = 100
PLAYGROUND_ROWS_PER_PAGE = 1000
KOPIS_WINDOW_DAYS = 31
KOPIS_HORIZON_DAYS = 90
KOPIS_BOXOFFICE_LOOKBACK_DAYS = 7
HTTP_TIMEOUT_SECONDS = 30.0
HTTP_MAX_ATTEMPTS = 3
KOPIS_DETAIL_CONCURRENCY = 1
KOPIS_DETAIL_REQUEST_INTERVAL_SECONDS = 0.5
PUBLIC_ACCESS_PLACE_CODES = frozenset(
    {"A003", "A030", "A031", "A032", "A033", "A092", "A093"}
)

DATABASE_PATH = Path(__file__).resolve().parent / "app.db"
engine = create_engine(
    f"sqlite:///{DATABASE_PATH.as_posix()}",
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def enable_sqlite_wal(dbapi_connection, connection_record):
    """배치 중에도 서버의 SQLite 읽기가 막히지 않게 한다."""
    del connection_record
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


def iter_date_windows(
    start: date,
    horizon_days: int = KOPIS_HORIZON_DAYS,
    window_days: int = KOPIS_WINDOW_DAYS,
) -> Iterator[tuple[date, date]]:
    """시작일~horizon_days 뒤까지 최대 window_days일 단위로 나눈다."""
    final_day = start + timedelta(days=horizon_days)
    window_start = start

    while window_start <= final_day:
        window_end = min(
            window_start + timedelta(days=window_days - 1),
            final_day,
        )
        yield window_start, window_end
        window_start = window_end + timedelta(days=1)


def _text(element: ElementTree.Element, name: str) -> str | None:
    value = element.findtext(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _normalize_date(value: str | None) -> str | None:
    if value is None:
        return None

    for date_format in ("%Y.%m.%d", "%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(value, date_format).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"지원하지 않는 KOPIS 날짜 형식입니다: {value}")


def normalize_prfage_min(prfage: str | None) -> int | None:
    """KOPIS 관람연령 원문을 최소 만 나이(세)로 정규화한다.

    명시적인 전체관람가는 0세로, ``N개월``은 해당 월령을 충족하는
    최소 정수 나이가 되도록 올림한다. 숫자로 확정할 수 없는 표현은
    추측하지 않고 None으로 남긴다.
    """
    if prfage is None:
        return None

    normalized = re.sub(r"\s+", "", prfage)
    if not normalized:
        return None

    all_ages_markers = ("전체관람가", "전연령", "모든연령")
    if any(marker in normalized for marker in all_ages_markers):
        return 0

    month_matches = [
        int(value)
        for value in re.findall(r"(\d+)\s*(?:개월|개월령)", prfage)
    ]
    year_matches = [
        int(value)
        for value in re.findall(r"(?:만\s*)?(\d+)\s*세", prfage)
    ]

    candidates = year_matches + [
        math.ceil(months / 12)
        for months in month_matches
    ]
    return min(candidates) if candidates else None


def parse_performance_list(xml: str) -> list[dict[str, str | None]]:
    """KOPIS 공연 목록 XML을 performances 목록 필드로 변환한다."""
    try:
        root = ElementTree.fromstring(xml)
    except ElementTree.ParseError as exc:
        raise RuntimeError("KOPIS 공연 목록 XML을 해석할 수 없습니다.") from exc

    error_code = root.findtext(".//errorcode") or root.findtext(".//code")
    if root.tag.lower() == "error" or error_code:
        error_message = (
            root.findtext(".//errormsg")
            or root.findtext(".//message")
            or "알 수 없는 오류"
        )
        raise RuntimeError(f"KOPIS API 오류: {error_code or '-'} {error_message}")

    performances: list[dict[str, str | None]] = []
    for item in root.findall(".//db"):
        mt20id = _text(item, "mt20id")
        prfnm = _text(item, "prfnm")
        if not mt20id or not prfnm:
            raise RuntimeError("KOPIS 공연 목록 응답에 mt20id 또는 prfnm이 없습니다.")

        genrenm = _text(item, "genrenm")
        performances.append(
            {
                "mt20id": mt20id,
                "prfnm": prfnm,
                "prfpdfrom": _normalize_date(_text(item, "prfpdfrom")),
                "prfpdto": _normalize_date(_text(item, "prfpdto")),
                "fcltynm": _text(item, "fcltynm"),
                "poster": _text(item, "poster"),
                "genrenm": genrenm,
                "shcate": map_genrenm_to_shcate(genrenm),
                "prfstate": _text(item, "prfstate"),
                "area": _text(item, "area"),
                "openrun": _text(item, "openrun"),
                "child": "Y",
            }
        )
    return performances


@dataclass(frozen=True)
class PerformanceDetailData:
    performance: dict[str, str | int | None]
    relates: list[dict[str, str | int | None]]
    images: list[dict[str, str | int | None]]


@dataclass(frozen=True)
class PlaygroundPage:
    items: list[dict[str, str | float | int | None]]
    page_index: int
    total_page_count: int
    total_count: int


def _optional_float(value: str | None, field_name: str) -> float | None:
    if value is None:
        return None
    try:
        return float(value.replace(",", ""))
    except ValueError as exc:
        raise RuntimeError(
            f"KOPIS 공연시설 상세의 {field_name} 값이 숫자가 아닙니다: {value}"
        ) from exc


def _optional_int(value: str | None, field_name: str) -> int | None:
    number = _optional_float(value, field_name)
    return int(number) if number is not None else None


def _parse_xml(xml: str, response_name: str) -> ElementTree.Element:
    try:
        root = ElementTree.fromstring(xml)
    except ElementTree.ParseError as exc:
        raise RuntimeError(f"KOPIS {response_name} XML을 해석할 수 없습니다.") from exc

    error_code = root.findtext(".//errorcode") or root.findtext(".//code")
    if root.tag.lower() == "error" or error_code:
        error_message = (
            root.findtext(".//errormsg")
            or root.findtext(".//message")
            or "알 수 없는 오류"
        )
        raise RuntimeError(f"KOPIS API 오류: {error_code or '-'} {error_message}")
    return root


def parse_performance_detail(xml: str) -> PerformanceDetailData:
    """KOPIS 공연 상세 XML을 공연·예매처·소개 이미지 데이터로 변환한다."""
    root = _parse_xml(xml, "공연 상세")
    item = root.find(".//db")
    if item is None:
        raise RuntimeError("KOPIS 공연 상세 응답에 db 요소가 없습니다.")

    mt20id = _text(item, "mt20id")
    prfnm = _text(item, "prfnm")
    if not mt20id or not prfnm:
        raise RuntimeError("KOPIS 공연 상세 응답에 mt20id 또는 prfnm이 없습니다.")

    prfage = _text(item, "prfage")
    genrenm = _text(item, "genrenm")
    performance = {
        "mt20id": mt20id,
        "prfnm": prfnm,
        "mt10id": _text(item, "mt10id"),
        "mt13id": _text(item, "mt13id"),
        "fcltynm": _text(item, "fcltynm"),
        "prfpdfrom": _normalize_date(_text(item, "prfpdfrom")),
        "prfpdto": _normalize_date(_text(item, "prfpdto")),
        "prfcast": _text(item, "prfcast"),
        "prfruntime": _text(item, "prfruntime"),
        "prfage": prfage,
        "prfage_min_norm": normalize_prfage_min(prfage),
        "pcseguidance": _text(item, "pcseguidance"),
        "poster": _text(item, "poster"),
        "sty": _text(item, "sty"),
        "area": _text(item, "area"),
        "genrenm": genrenm,
        "shcate": map_genrenm_to_shcate(genrenm),
        "openrun": _text(item, "openrun"),
        "child": _text(item, "child"),
        "updatedate": _text(item, "updatedate"),
        "prfstate": _text(item, "prfstate"),
        "dtguidance": _text(item, "dtguidance"),
    }

    relates = [
        {
            "mt20id": mt20id,
            "relatenm": _text(relate, "relatenm"),
            "relateurl": _text(relate, "relateurl"),
            "sort_no": sort_no,
        }
        for sort_no, relate in enumerate(
            item.findall("./relates/relate"),
            start=1,
        )
    ]
    images = [
        {
            "mt20id": mt20id,
            "styurl": styurl.text.strip() if styurl.text else None,
            "sort_no": sort_no,
        }
        for sort_no, styurl in enumerate(
            item.findall("./styurls/styurl"),
            start=1,
        )
    ]
    return PerformanceDetailData(
        performance=performance,
        relates=relates,
        images=images,
    )


def parse_venue_detail(xml: str) -> dict[str, str | float | int | None]:
    """KOPIS 공연시설 상세 XML을 venues 필드로 변환한다."""
    root = _parse_xml(xml, "공연시설 상세")
    item = root.find(".//db")
    if item is None:
        raise RuntimeError("KOPIS 공연시설 상세 응답에 db 요소가 없습니다.")

    mt10id = _text(item, "mt10id")
    if not mt10id:
        raise RuntimeError("KOPIS 공연시설 상세 응답에 mt10id가 없습니다.")

    return {
        "mt10id": mt10id,
        "fcltynm": _text(item, "fcltynm"),
        "adres": _text(item, "adres"),
        "telno": _text(item, "telno"),
        "relateurl": _text(item, "relateurl"),
        "la": _optional_float(_text(item, "la"), "la"),
        "lo": _optional_float(_text(item, "lo"), "lo"),
        "parkinglot": _text(item, "parkinglot"),
        "restaurant": _text(item, "restaurant"),
        "cafe": _text(item, "cafe"),
        "store": _text(item, "store"),
        "nolibang": _text(item, "nolibang"),
        "suyu": _text(item, "suyu"),
        "parkbarrier": _text(item, "parkbarrier"),
        "restbarrier": _text(item, "restbarrier"),
        "runwbarrier": _text(item, "runwbarrier"),
        "elevbarrier": _text(item, "elevbarrier"),
        "seatscale": _optional_int(_text(item, "seatscale"), "seatscale"),
        "sidonm": _text(item, "sidonm"),
        "gugunnm": _text(item, "gugunnm"),
    }


def parse_boxoffice(
    xml: str,
    *,
    catecode: str,
    stdate: str,
    eddate: str,
    fetched_at: str,
) -> list[dict[str, str | int | None]]:
    """KOPIS 예매상황판 XML을 랭킹 행으로 변환한다."""
    root = _parse_xml(xml, "예매상황판")
    rankings: list[dict[str, str | int | None]] = []

    for item in root.findall(".//boxof"):
        rnum_text = _text(item, "rnum")
        if rnum_text is None:
            raise RuntimeError("KOPIS 예매상황판 응답에 rnum이 없습니다.")
        try:
            rnum = int(rnum_text)
        except ValueError as exc:
            raise RuntimeError(
                f"KOPIS 예매상황판 rnum이 정수가 아닙니다: {rnum_text}"
            ) from exc

        rankings.append(
            {
                "catecode": catecode,
                "rnum": rnum,
                "mt20id": _text(item, "mt20id"),
                "prfnm": _text(item, "prfnm"),
                "prfpd": _text(item, "prfpd"),
                "prfplcnm": _text(item, "prfplcnm"),
                "area": _text(item, "area"),
                "poster": _text(item, "poster"),
                "cate": _text(item, "cate"),
                "seatcnt": _optional_int(_text(item, "seatcnt"), "seatcnt"),
                "prfdtcnt": _optional_int(_text(item, "prfdtcnt"), "prfdtcnt"),
                "stdate": stdate,
                "eddate": eddate,
                "fetched_at": fetched_at,
            }
        )

    rankings.sort(key=lambda row: (int(row["rnum"]), str(row.get("mt20id") or "")))
    return rankings



def _json_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _join_address(item: dict[str, object], *field_names: str) -> str | None:
    parts = [_json_text(item.get(field_name)) for field_name in field_names]
    joined = " ".join(part for part in parts if part)
    return joined or None


def _normalize_indoor_yn(code: str | None, name: str | None) -> str | None:
    if code == "O001" or name == "실내":
        return "Y"
    if code == "O002" or name == "실외":
        return "N"
    return None


def _coordinate(
    value: object,
    minimum: float,
    maximum: float,
) -> float | None:
    text = _json_text(value)
    if text is None:
        return None
    try:
        coordinate = float(text)
    except ValueError:
        return None
    if not math.isfinite(coordinate) or not minimum <= coordinate <= maximum:
        return None
    return coordinate


def _json_int(value: object, field_name: str) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            f"놀이시설 응답의 {field_name} 값이 정수가 아닙니다: {value}"
        ) from exc


def parse_playground_page(
    payload: dict[str, object],
    fetched_at: str,
) -> PlaygroundPage:
    """행안부 놀이시설 JSON 한 페이지를 DB 필드와 페이지 정보로 변환한다."""
    response = payload.get("response")
    if not isinstance(response, dict):
        raise RuntimeError("놀이시설 응답에 response 객체가 없습니다.")

    header = response.get("header")
    if not isinstance(header, dict):
        raise RuntimeError("놀이시설 응답에 header 객체가 없습니다.")
    result_code = _json_text(header.get("resultCode"))
    if result_code != "00":
        result_message = _json_text(header.get("resultMsg")) or "알 수 없는 오류"
        raise RuntimeError(
            f"놀이시설 API 오류: {result_code or '-'} {result_message}"
        )

    body = response.get("body")
    if not isinstance(body, dict):
        raise RuntimeError("놀이시설 응답에 body 객체가 없습니다.")
    raw_items = body.get("items") or []
    if not isinstance(raw_items, list):
        raise RuntimeError("놀이시설 응답의 items가 목록이 아닙니다.")

    items: list[dict[str, str | float | int | None]] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            raise RuntimeError("놀이시설 응답에 객체가 아닌 항목이 있습니다.")

        pfct_sn = _json_text(raw_item.get("pfctSn"))
        pfct_nm = _json_text(raw_item.get("pfctNm"))
        if not pfct_sn or not pfct_nm:
            raise RuntimeError("놀이시설 응답에 pfctSn 또는 pfctNm이 없습니다.")

        indoor_code = _json_text(raw_item.get("idrodrCd"))
        indoor_name = _json_text(raw_item.get("idrodrCdNm"))
        instl_place_cd = _json_text(raw_item.get("instlPlaceCd"))
        items.append(
            {
                "pfct_sn": pfct_sn,
                "pfct_nm": pfct_nm,
                "instl_place_cd": instl_place_cd,
                "instl_place_nm": _json_text(raw_item.get("instlPlaceCdNm")),
                "road_addr": _join_address(raw_item, "ronaAddr", "ronaDaddr"),
                "lotno_addr": _join_address(
                    raw_item,
                    "lotnoAddr",
                    "lotnoDaddr",
                ),
                "zip": _json_text(raw_item.get("zip")),
                "lat": _coordinate(raw_item.get("latCrtsVl"), -90.0, 90.0),
                "lng": _coordinate(raw_item.get("lotCrtsVl"), -180.0, 180.0),
                "wowa_styl_ride_cd": _json_text(
                    raw_item.get("wowaStylRideCd")
                ),
                "indoor_yn": _normalize_indoor_yn(
                    indoor_code,
                    indoor_name,
                ),
                "is_public_access": int(
                    instl_place_cd in PUBLIC_ACCESS_PLACE_CODES
                ),
                "updated_at": fetched_at,
            }
        )

    return PlaygroundPage(
        items=items,
        page_index=_json_int(body.get("pageIndex"), "pageIndex"),
        total_page_count=_json_int(
            body.get("totalPageCnt"),
            "totalPageCnt",
        ),
        total_count=_json_int(body.get("totalCnt"), "totalCnt"),
    )


async def _get_with_retry(
    client: httpx.AsyncClient,
    url: str,
    params: dict[str, str | int],
    response_name: str,
) -> str:
    last_error: Exception | None = None

    for attempt in range(HTTP_MAX_ATTEMPTS):
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.text
        except (httpx.TransportError, httpx.HTTPStatusError) as exc:
            last_error = exc
            retryable = (
                isinstance(exc, httpx.TransportError)
                or exc.response.status_code in (400, 429)
                or exc.response.status_code >= 500
            )
            if not retryable or attempt == HTTP_MAX_ATTEMPTS - 1:
                raise RuntimeError(f"KOPIS {response_name} 요청에 실패했습니다.") from exc
            await asyncio.sleep(2**attempt)

    raise RuntimeError(f"KOPIS {response_name} 요청에 실패했습니다.") from last_error


async def _get_playground_json_with_retry(
    client: httpx.AsyncClient,
    params: dict[str, str | int],
) -> dict[str, object]:
    last_error: Exception | None = None

    for attempt in range(HTTP_MAX_ATTEMPTS):
        try:
            response = await client.get(PLAYGROUND_LIST_URL, params=params)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("JSON 최상위 값이 객체가 아닙니다.")
            return payload
        except (httpx.TransportError, httpx.HTTPStatusError, ValueError) as exc:
            last_error = exc
            retryable = (
                isinstance(exc, (httpx.TransportError, ValueError))
                or exc.response.status_code >= 500
            )
            if not retryable or attempt == HTTP_MAX_ATTEMPTS - 1:
                raise RuntimeError("놀이시설 목록 요청에 실패했습니다.") from exc
            await asyncio.sleep(2**attempt)

    raise RuntimeError("놀이시설 목록 요청에 실패했습니다.") from last_error


async def fetch_performance_list(
    service_key: str,
    start: date,
) -> list[dict[str, str | None]]:
    """오늘~+90일의 아동 공연 목록을 기간 분할·페이징해 수집한다."""
    collected: dict[str, dict[str, str | None]] = {}
    timeout = httpx.Timeout(HTTP_TIMEOUT_SECONDS)

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        for window_start, window_end in iter_date_windows(start):
            page = 1
            while True:
                xml = await _get_with_retry(
                    client,
                    KOPIS_PERFORMANCE_LIST_URL,
                    {
                        "service": service_key,
                        "stdate": window_start.strftime("%Y%m%d"),
                        "eddate": window_end.strftime("%Y%m%d"),
                        "cpage": page,
                        "rows": KOPIS_ROWS_PER_PAGE,
                        "kidstate": "Y",
                    },
                    "공연 목록",
                )
                page_items = parse_performance_list(xml)
                for item in page_items:
                    collected[str(item["mt20id"])] = item

                if len(page_items) < KOPIS_ROWS_PER_PAGE:
                    break
                page += 1

    return list(collected.values())


async def fetch_performance_details(
    service_key: str,
    mt20ids: list[str],
) -> list[PerformanceDetailData]:
    """공연 ID별 상세를 제한된 동시 요청으로 수집한다."""
    timeout = httpx.Timeout(HTTP_TIMEOUT_SECONDS)
    semaphore = asyncio.Semaphore(KOPIS_DETAIL_CONCURRENCY)

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:

        async def fetch_one(mt20id: str) -> PerformanceDetailData:
            async with semaphore:
                await asyncio.sleep(KOPIS_DETAIL_REQUEST_INTERVAL_SECONDS)
                xml = await _get_with_retry(
                    client,
                    f"{KOPIS_PERFORMANCE_LIST_URL}/{mt20id}",
                    {"service": service_key},
                    f"공연 상세({mt20id})",
                )
            detail = parse_performance_detail(xml)
            if detail.performance["mt20id"] != mt20id:
                raise RuntimeError(
                    f"KOPIS 공연 상세 ID가 요청과 다릅니다: {mt20id}"
                )
            return detail

        return list(await asyncio.gather(*(fetch_one(mt20id) for mt20id in mt20ids)))


async def fetch_venue_details(
    service_key: str,
    mt10ids: list[str],
) -> list[dict[str, str | float | int | None]]:
    """공연시설 ID별 상세를 중복 없이 제한된 동시 요청으로 수집한다."""
    unique_ids = sorted(set(mt10ids))
    timeout = httpx.Timeout(HTTP_TIMEOUT_SECONDS)
    semaphore = asyncio.Semaphore(KOPIS_DETAIL_CONCURRENCY)

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:

        async def fetch_one(
            mt10id: str,
        ) -> dict[str, str | float | int | None]:
            async with semaphore:
                await asyncio.sleep(KOPIS_DETAIL_REQUEST_INTERVAL_SECONDS)
                xml = await _get_with_retry(
                    client,
                    f"{KOPIS_VENUE_DETAIL_URL}/{mt10id}",
                    {"service": service_key},
                    f"공연시설 상세({mt10id})",
                )
            venue = parse_venue_detail(xml)
            if venue["mt10id"] != mt10id:
                raise RuntimeError(
                    f"KOPIS 공연시설 상세 ID가 요청과 다릅니다: {mt10id}"
                )
            return venue

        return list(await asyncio.gather(*(fetch_one(mt10id) for mt10id in unique_ids)))


async def fetch_boxoffice(
    service_key: str,
    *,
    end: date | None = None,
    lookback_days: int = KOPIS_BOXOFFICE_LOOKBACK_DAYS,
    catecode: str = "KID",
) -> list[dict[str, str | int | None]]:
    """아동(catecode=KID) 예매상황판을 최근 lookback 구간으로 수집한다.

    실호출 결과: ``date`` 없이도 응답이 오지만, 문서상 필수이므로
    종료일(``eddate``)을 ``date``로 함께 전달한다.
    """
    ed = end or (date.today() - timedelta(days=1))
    st = ed - timedelta(days=lookback_days - 1)
    stdate = st.strftime("%Y%m%d")
    eddate = ed.strftime("%Y%m%d")
    fetched_at = datetime.now(timezone.utc).isoformat()
    timeout = httpx.Timeout(HTTP_TIMEOUT_SECONDS)

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        xml = await _get_with_retry(
            client,
            KOPIS_BOXOFFICE_URL,
            {
                "service": service_key,
                "stdate": stdate,
                "eddate": eddate,
                "date": eddate,
                "catecode": catecode,
            },
            "예매상황판",
        )

    return parse_boxoffice(
        xml,
        catecode=catecode,
        stdate=st.isoformat(),
        eddate=ed.isoformat(),
        fetched_at=fetched_at,
    )


def replace_boxoffice_rankings(
    items: list[dict[str, str | int | None]],
    *,
    catecode: str = "KID",
) -> int:
    """예매상황판 스냅샷을 전체 교체한다."""
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        session.exec(
            delete(BoxofficeRanking).where(BoxofficeRanking.catecode == catecode)
        )
        for item in items:
            session.add(BoxofficeRanking(**item))
        session.commit()
    return len(items)


async def fetch_playgrounds(
    service_key: str,
) -> list[dict[str, str | float | int | None]]:
    """행안부 놀이시설 전국 데이터를 마지막 페이지까지 순차 수집한다."""
    fetched_at = datetime.now(timezone.utc).isoformat()
    collected: dict[str, dict[str, str | float | int | None]] = {}
    fetched_record_count = 0
    page_index = 1
    total_page_count: int | None = None
    total_count: int | None = None
    timeout = httpx.Timeout(HTTP_TIMEOUT_SECONDS)

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        while total_page_count is None or page_index <= total_page_count:
            payload = await _get_playground_json_with_retry(
                client,
                {
                    "serviceKey": service_key,
                    "pageIndex": page_index,
                    "recordCountPerPage": PLAYGROUND_ROWS_PER_PAGE,
                },
            )
            page = parse_playground_page(payload, fetched_at)
            if page.page_index != page_index:
                raise RuntimeError(
                    "놀이시설 응답 페이지가 요청과 다릅니다: "
                    f"요청 {page_index}, 응답 {page.page_index}"
                )

            if total_page_count is None:
                total_page_count = page.total_page_count
                total_count = page.total_count
            elif (
                page.total_page_count != total_page_count
                or page.total_count != total_count
            ):
                raise RuntimeError("놀이시설 수집 중 전체 건수 정보가 변경되었습니다.")

            for item in page.items:
                pfct_sn = str(item["pfct_sn"])
                if item["lat"] is not None and item["lng"] is not None:
                    collected[pfct_sn] = item
            fetched_record_count += len(page.items)
            page_index += 1

    if total_count is not None and fetched_record_count != total_count:
        raise RuntimeError(
            "놀이시설 전체 건수와 수집 건수가 다릅니다: "
            f"전체 {total_count}, 수집 {fetched_record_count}"
        )
    return list(collected.values())


def replace_performance_list(
    items: list[dict[str, str | None]],
) -> tuple[int, int]:
    """목록 필드는 갱신하고 현재 수집 범위에서 사라진 공연은 제거한다."""
    from db_migrate import ensure_performance_shcate_column

    SQLModel.metadata.create_all(engine)
    ensure_performance_shcate_column(engine)
    fetched_ids = {str(item["mt20id"]) for item in items}
    upserted = 0

    with Session(engine) as session:
        existing_ids = set(session.exec(select(Performance.mt20id)).all())
        stale_ids = existing_ids - fetched_ids

        if stale_ids:
            session.exec(
                delete(PerformanceRelate).where(
                    PerformanceRelate.mt20id.in_(stale_ids)
                )
            )
            session.exec(
                delete(PerformanceImage).where(
                    PerformanceImage.mt20id.in_(stale_ids)
                )
            )
            session.exec(
                delete(Performance).where(Performance.mt20id.in_(stale_ids))
            )

        for item in items:
            mt20id = str(item["mt20id"])
            performance = session.get(Performance, mt20id)
            if performance is None:
                performance = Performance(
                    mt20id=mt20id,
                    prfnm=str(item["prfnm"]),
                )

            for field_name, value in item.items():
                setattr(performance, field_name, value)
            session.add(performance)
            upserted += 1

        session.commit()

    return upserted, len(stale_ids)


def upsert_performance_details(details: list[PerformanceDetailData]) -> int:
    """공연 상세를 갱신하고 해당 공연의 자식 목록을 응답 기준으로 교체한다."""
    fetched_at = datetime.now(timezone.utc).isoformat()

    with Session(engine) as session:
        for detail in details:
            mt20id = str(detail.performance["mt20id"])
            performance = session.get(Performance, mt20id)
            if performance is None:
                performance = Performance(
                    mt20id=mt20id,
                    prfnm=str(detail.performance["prfnm"]),
                )

            for field_name, value in detail.performance.items():
                setattr(performance, field_name, value)
            performance.detail_fetched_at = fetched_at
            session.add(performance)

            session.exec(
                delete(PerformanceRelate).where(
                    PerformanceRelate.mt20id == mt20id
                )
            )
            session.exec(
                delete(PerformanceImage).where(
                    PerformanceImage.mt20id == mt20id
                )
            )
            for relate in detail.relates:
                session.add(PerformanceRelate(**relate))
            for image in detail.images:
                session.add(PerformanceImage(**image))

        session.commit()
    return len(details)


def upsert_venue_details(
    venues: list[dict[str, str | float | int | None]],
) -> int:
    """공연시설 상세의 좌표·편의시설·무장애 필드를 갱신한다."""
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        for item in venues:
            mt10id = str(item["mt10id"])
            venue = session.get(Venue, mt10id)
            if venue is None:
                venue = Venue(mt10id=mt10id)

            for field_name, value in item.items():
                setattr(venue, field_name, value)
            session.add(venue)

        session.commit()
    return len(venues)


def replace_playgrounds(
    items: list[dict[str, str | float | int | None]],
) -> tuple[int, int]:
    """전국 놀이시설을 갱신하고 최신 응답에서 사라진 시설을 제거한다."""
    SQLModel.metadata.create_all(engine)
    fetched_ids = {str(item["pfct_sn"]) for item in items}

    with Session(engine) as session:
        existing = {
            playground.pfct_sn: playground
            for playground in session.exec(select(Playground)).all()
        }
        stale_ids = set(existing) - fetched_ids
        for pfct_sn in stale_ids:
            session.delete(existing[pfct_sn])

        for item in items:
            pfct_sn = str(item["pfct_sn"])
            playground = existing.get(pfct_sn)
            if playground is None:
                playground = Playground(
                    pfct_sn=pfct_sn,
                    pfct_nm=str(item["pfct_nm"]),
                )

            for field_name, value in item.items():
                setattr(playground, field_name, value)
            session.add(playground)

        session.commit()
    return len(items), len(stale_ids)


def record_ingest_log(
    source: str,
    started_at: str,
    fetched: int,
    upserted: int,
    failed: int,
    message: str,
) -> None:
    """배치 실행 결과를 운영 관측용 적재 이력에 남긴다."""
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(
            IngestLog(
                source=source,
                started_at=started_at,
                finished_at=datetime.now(timezone.utc).isoformat(),
                fetched=fetched,
                upserted=upserted,
                failed=failed,
                message=message,
            )
        )
        session.commit()


async def ingest_kopis_performance_list(
    start: date | None = None,
) -> tuple[int, int]:
    """KOPIS 아동 공연 목록을 수집해 SQLite에 전체 재적재한다."""
    started_at = datetime.now(timezone.utc).isoformat()
    items: list[dict[str, str | None]] = []
    try:
        settings = get_settings()
        items = await fetch_performance_list(
            service_key=settings.kopis_service,
            start=start or date.today(),
        )
        upserted, deleted = replace_performance_list(items)
    except Exception as exc:
        record_ingest_log(
            "kopis_performance_list",
            started_at,
            len(items),
            0,
            1,
            f"{type(exc).__name__}: {exc}",
        )
        raise

    record_ingest_log(
        "kopis_performance_list",
        started_at,
        len(items),
        upserted,
        0,
        f"{deleted}건 정리",
    )
    return upserted, deleted


async def ingest_kopis_performances(
    start: date | None = None,
) -> tuple[int, int, int, int]:
    """KOPIS 아동 공연과 공연시설 상세를 함께 전체 재적재한다."""
    started_at = datetime.now(timezone.utc).isoformat()
    items: list[dict[str, str | None]] = []
    try:
        settings = get_settings()
        items = await fetch_performance_list(
            service_key=settings.kopis_service,
            start=start or date.today(),
        )
        details = await fetch_performance_details(
            service_key=settings.kopis_service,
            mt20ids=[str(item["mt20id"]) for item in items],
        )
        venue_ids = [
            str(detail.performance["mt10id"])
            for detail in details
            if detail.performance["mt10id"]
        ]
        venues = await fetch_venue_details(
            service_key=settings.kopis_service,
            mt10ids=venue_ids,
        )
        upserted, deleted = replace_performance_list(items)
        venue_upserted = upsert_venue_details(venues)
        detailed = upsert_performance_details(details)
    except Exception as exc:
        record_ingest_log(
            "kopis",
            started_at,
            len(items),
            0,
            1,
            f"{type(exc).__name__}: {exc}",
        )
        raise

    record_ingest_log(
        "kopis",
        started_at,
        len(items),
        upserted,
        0,
        f"{deleted}건 정리, {detailed}건 상세, {venue_upserted}건 공연시설",
    )
    return upserted, deleted, detailed, venue_upserted


async def ingest_playgrounds() -> tuple[int, int]:
    """행안부 전국 놀이시설을 페이지 단위로 수집해 전체 동기화한다."""
    started_at = datetime.now(timezone.utc).isoformat()
    items: list[dict[str, str | float | int | None]] = []
    try:
        settings = get_settings()
        items = await fetch_playgrounds(settings.playground_service_key)
        upserted, deleted = replace_playgrounds(items)
    except Exception as exc:
        record_ingest_log(
            "playgrounds",
            started_at,
            len(items),
            0,
            1,
            f"{type(exc).__name__}: {exc}",
        )
        raise

    record_ingest_log(
        "playgrounds",
        started_at,
        len(items),
        upserted,
        0,
        f"{deleted}건 정리",
    )
    return upserted, deleted


async def ingest_boxoffice() -> int:
    """아동 예매상황판을 수집해 SQLite에 전체 재적재한다."""
    started_at = datetime.now(timezone.utc).isoformat()
    items: list[dict[str, str | int | None]] = []
    try:
        settings = get_settings()
        items = await fetch_boxoffice(settings.kopis_service)
        upserted = replace_boxoffice_rankings(items)
    except Exception as exc:
        record_ingest_log(
            "boxoffice",
            started_at,
            len(items),
            0,
            1,
            f"{type(exc).__name__}: {exc}",
        )
        raise

    record_ingest_log(
        "boxoffice",
        started_at,
        len(items),
        upserted,
        0,
        "KID 랭킹 전체 교체",
    )
    return upserted


def main() -> None:
    upserted, deleted, detailed, venue_upserted = asyncio.run(
        ingest_kopis_performances()
    )
    print(
        "KOPIS 공연 적재 완료: "
        f"{upserted}건 저장, {deleted}건 정리, {detailed}건 상세 저장, "
        f"{venue_upserted}건 공연시설 저장"
    )
    ranking_upserted = asyncio.run(ingest_boxoffice())
    print(f"KOPIS 예매상황판 적재 완료: {ranking_upserted}건 저장")
    playground_upserted, playground_deleted = asyncio.run(ingest_playgrounds())
    print(
        "행안부 놀이시설 적재 완료: "
        f"{playground_upserted}건 저장, {playground_deleted}건 정리"
    )


if __name__ == "__main__":
    main()
