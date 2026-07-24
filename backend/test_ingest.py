import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from sqlmodel import Session, SQLModel, create_engine, select

from ingest import (
    PLAYGROUND_ROWS_PER_PAGE,
    fetch_playgrounds,
    ingest_playgrounds,
    normalize_prfage_min,
    parse_boxoffice,
    parse_performance_detail,
    parse_performance_list,
    parse_playground_page,
    parse_venue_detail,
    record_ingest_log,
)
from genre_codes import map_genrenm_to_shcate
from models import IngestLog


class MapGenreCodeTests(unittest.TestCase):
    def test_maps_verified_genrenm_labels(self):
        cases = {
            "연극": "AAAA",
            "뮤지컬": "GGGA",
            "서양음악(클래식)": "CCCA",
            "한국음악(국악)": "CCCC",
            "무용(서양/한국무용)": "BBBC",
            "서커스/마술": "EEEB",
            "복합": "EEEA",
        }
        for genrenm, expected in cases.items():
            with self.subTest(genrenm=genrenm):
                self.assertEqual(map_genrenm_to_shcate(genrenm), expected)

    def test_leaves_unknown_genre_unset(self):
        self.assertIsNone(map_genrenm_to_shcate(None))
        self.assertIsNone(map_genrenm_to_shcate(""))
        self.assertIsNone(map_genrenm_to_shcate("대중음악"))


class ParsePerformanceListGenreTests(unittest.TestCase):
    def test_stores_mapped_shcate_from_genrenm(self):
        items = parse_performance_list(
            """
            <dbs>
              <db>
                <mt20id>PF_TEST</mt20id>
                <prfnm>테스트 공연</prfnm>
                <prfpdfrom>2026.07.01</prfpdfrom>
                <prfpdto>2026.07.31</prfpdto>
                <genrenm>뮤지컬</genrenm>
              </db>
            </dbs>
            """
        )

        self.assertEqual(items[0]["genrenm"], "뮤지컬")
        self.assertEqual(items[0]["shcate"], "GGGA")


class ParseBoxofficeTests(unittest.TestCase):
    def test_parses_kid_rankings(self):
        items = parse_boxoffice(
            """
            <boxofs>
              <boxof>
                <rnum>2</rnum>
                <mt20id>PF2</mt20id>
                <prfnm>두 번째</prfnm>
                <prfpd>2026.07.01~2026.07.31</prfpd>
                <prfplcnm>홀</prfplcnm>
                <area>서울</area>
                <poster>https://example.com/2.jpg</poster>
                <cate>아동</cate>
                <seatcnt>200</seatcnt>
                <prfdtcnt>5</prfdtcnt>
              </boxof>
              <boxof>
                <rnum>1</rnum>
                <mt20id>PF1</mt20id>
                <prfnm>첫 번째</prfnm>
                <prfpd>2026.08.01~2026.08.31</prfpd>
                <cate>아동</cate>
              </boxof>
            </boxofs>
            """,
            catecode="KID",
            stdate="2026-07-17",
            eddate="2026-07-23",
            fetched_at="2026-07-24T00:00:00+00:00",
        )

        self.assertEqual([item["mt20id"] for item in items], ["PF1", "PF2"])
        self.assertEqual(items[0]["rnum"], 1)
        self.assertEqual(items[0]["catecode"], "KID")
        self.assertEqual(items[1]["seatcnt"], 200)



class NormalizePerformanceAgeTests(unittest.TestCase):
    def test_normalizes_common_kopis_age_formats(self):
        cases = {
            "전체 관람가": 0,
            "만 3세 이상": 3,
            "48개월 이상": 4,
            "13개월 이상": 2,
            "만 7세 이상(미취학아동 입장불가)": 7,
        }

        for raw_age, expected in cases.items():
            with self.subTest(raw_age=raw_age):
                self.assertEqual(normalize_prfage_min(raw_age), expected)

    def test_leaves_unknown_age_unset(self):
        for raw_age in (None, "", "미취학아동 입장불가"):
            with self.subTest(raw_age=raw_age):
                self.assertIsNone(normalize_prfage_min(raw_age))

    def test_detail_parser_stores_raw_and_normalized_age(self):
        detail = parse_performance_detail(
            """
            <dbs>
              <db>
                <mt20id>PF_TEST</mt20id>
                <prfnm>테스트 공연</prfnm>
                <prfage>36개월 이상</prfage>
              </db>
            </dbs>
            """
        )

        self.assertEqual(detail.performance["prfage"], "36개월 이상")
        self.assertEqual(detail.performance["prfage_min_norm"], 3)
        self.assertEqual(detail.performance["shcate"], None)



class ParseVenueDetailTests(unittest.TestCase):
    def test_parses_coordinates_amenities_and_accessibility(self):
        venue = parse_venue_detail(
            """
            <dbs>
              <db>
                <mt10id>FC001247</mt10id>
                <fcltynm>올림픽공원</fcltynm>
                <adres>서울특별시 송파구 올림픽로 424</adres>
                <telno>02-410-1114</telno>
                <relateurl>https://example.com</relateurl>
                <la>37.52112</la>
                <lo>127.1283636</lo>
                <seatscale>32,349</seatscale>
                <parkinglot>Y</parkinglot>
                <restaurant>Y</restaurant>
                <cafe>Y</cafe>
                <store>Y</store>
                <nolibang>N</nolibang>
                <suyu>N</suyu>
                <parkbarrier>Y</parkbarrier>
                <restbarrier>Y</restbarrier>
                <runwbarrier>N</runwbarrier>
                <elevbarrier>N</elevbarrier>
                <sidonm>서울특별시</sidonm>
                <gugunnm>송파구</gugunnm>
              </db>
            </dbs>
            """
        )

        self.assertEqual(venue["mt10id"], "FC001247")
        self.assertEqual(venue["la"], 37.52112)
        self.assertEqual(venue["lo"], 127.1283636)
        self.assertEqual(venue["seatscale"], 32349)
        self.assertEqual(venue["parkinglot"], "Y")
        self.assertEqual(venue["suyu"], "N")
        self.assertEqual(venue["parkbarrier"], "Y")
        self.assertEqual(venue["gugunnm"], "송파구")

    def test_allows_missing_optional_fields(self):
        venue = parse_venue_detail(
            "<dbs><db><mt10id>FC_TEST</mt10id></db></dbs>"
        )

        self.assertIsNone(venue["la"])
        self.assertIsNone(venue["parkinglot"])


def _playground_payload(
    page_index: int,
    total_page_count: int,
    total_count: int,
    items: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "response": {
            "header": {
                "resultCode": "00",
                "resultMsg": "NORMAL SERVICE",
            },
            "body": {
                "pageIndex": page_index,
                "recordCountPerPage": PLAYGROUND_ROWS_PER_PAGE,
                "totalPageCnt": total_page_count,
                "totalCnt": total_count,
                "items": items,
            },
        }
    }


class ParsePlaygroundPageTests(unittest.TestCase):
    def test_maps_verified_api_fields(self):
        page = parse_playground_page(
            _playground_payload(
                page_index=1,
                total_page_count=1,
                total_count=1,
                items=[
                    {
                        "pfctSn": "1008026",
                        "pfctNm": "황간초등학교 놀이시설",
                        "zip": "29115",
                        "lotnoAddr": "충북 영동군 황간면",
                        "lotnoDaddr": "남성리 123",
                        "ronaAddr": "충북 영동군 황간면 남성1길 25",
                        "ronaDaddr": "(황간초등학교)",
                        "instlPlaceCd": "A011",
                        "instlPlaceCdNm": "학교",
                        "idrodrCd": "O002",
                        "idrodrCdNm": "실외",
                        "latCrtsVl": "36.2273960",
                        "lotCrtsVl": "127.9130288",
                        "wowaStylRideCd": "X002",
                    }
                ],
            ),
            fetched_at="2026-07-24T00:00:00+00:00",
        )

        self.assertEqual(page.total_count, 1)
        self.assertEqual(page.items[0]["pfct_sn"], "1008026")
        self.assertEqual(
            page.items[0]["road_addr"],
            "충북 영동군 황간면 남성1길 25 (황간초등학교)",
        )
        self.assertEqual(
            page.items[0]["lotno_addr"],
            "충북 영동군 황간면 남성리 123",
        )
        self.assertEqual(page.items[0]["indoor_yn"], "N")
        self.assertEqual(page.items[0]["lat"], 36.227396)
        self.assertEqual(page.items[0]["lng"], 127.9130288)
        self.assertEqual(page.items[0]["is_public_access"], 0)
        self.assertEqual(page.items[0]["updated_at"], "2026-07-24T00:00:00+00:00")

    def test_sets_public_access_from_d4_whitelist(self):
        public_codes = ("A003", "A030", "A031", "A032", "A033", "A092", "A093")
        items = [
            {
                "pfctSn": f"PG{index}",
                "pfctNm": f"공공 놀이터 {index}",
                "instlPlaceCd": code,
            }
            for index, code in enumerate(public_codes, start=1)
        ]
        items.extend(
            [
                {
                    "pfctSn": "PRIVATE",
                    "pfctNm": "주택단지 놀이터",
                    "instlPlaceCd": "A010",
                },
                {
                    "pfctSn": "UNKNOWN",
                    "pfctNm": "장소 미상 놀이터",
                },
            ]
        )

        page = parse_playground_page(
            _playground_payload(
                page_index=1,
                total_page_count=1,
                total_count=len(items),
                items=items,
            ),
            fetched_at="2026-07-24T00:00:00+00:00",
        )

        self.assertTrue(
            all(
                item["is_public_access"] == 1
                for item in page.items[: len(public_codes)]
            )
        )
        self.assertEqual(page.items[-2]["is_public_access"], 0)
        self.assertEqual(page.items[-1]["is_public_access"], 0)


class FetchPlaygroundsTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetches_every_page_using_api_page_count(self):
        responses = [
            _playground_payload(
                1,
                2,
                2,
                [
                    {
                        "pfctSn": "PG1",
                        "pfctNm": "첫 번째 놀이터",
                        "latCrtsVl": "37.1",
                        "lotCrtsVl": "127.1",
                    }
                ],
            ),
            _playground_payload(
                2,
                2,
                2,
                [
                    {
                        "pfctSn": "PG2",
                        "pfctNm": "두 번째 놀이터",
                        "latCrtsVl": "37.2",
                        "lotCrtsVl": "127.2",
                    }
                ],
            ),
        ]

        with patch(
            "ingest._get_playground_json_with_retry",
            new=AsyncMock(side_effect=responses),
        ) as request:
            items = await fetch_playgrounds("test-key")

        self.assertEqual([item["pfct_sn"] for item in items], ["PG1", "PG2"])
        self.assertEqual(request.await_count, 2)
        self.assertEqual(
            request.await_args_list[1].args[1]["pageIndex"],
            2,
        )
        self.assertEqual(
            request.await_args_list[1].args[1]["recordCountPerPage"],
            1000,
        )

    async def test_excludes_playgrounds_without_valid_coordinate_pair(self):
        response = _playground_payload(
            1,
            1,
            3,
            [
                {
                    "pfctSn": "PG1",
                    "pfctNm": "좌표 있는 놀이터",
                    "latCrtsVl": "37.1",
                    "lotCrtsVl": "127.1",
                },
                {
                    "pfctSn": "PG2",
                    "pfctNm": "경도 없는 놀이터",
                    "latCrtsVl": "37.2",
                    "lotCrtsVl": None,
                },
                {
                    "pfctSn": "PG3",
                    "pfctNm": "유효하지 않은 좌표 놀이터",
                    "latCrtsVl": "91",
                    "lotCrtsVl": "127.3",
                },
            ],
        )

        with patch(
            "ingest._get_playground_json_with_retry",
            new=AsyncMock(return_value=response),
        ):
            items = await fetch_playgrounds("test-key")

        self.assertEqual([item["pfct_sn"] for item in items], ["PG1"])

    async def test_deduplicates_repeated_facility_ids_across_pages(self):
        responses = [
            _playground_payload(
                1,
                2,
                2,
                [
                    {
                        "pfctSn": "PG1",
                        "pfctNm": "중복 놀이터",
                        "latCrtsVl": "37.1",
                        "lotCrtsVl": "127.1",
                    }
                ],
            ),
            _playground_payload(
                2,
                2,
                2,
                [
                    {
                        "pfctSn": "PG1",
                        "pfctNm": "중복 놀이터",
                        "latCrtsVl": "37.1",
                        "lotCrtsVl": "127.1",
                    }
                ],
            ),
        ]

        with patch(
            "ingest._get_playground_json_with_retry",
            new=AsyncMock(side_effect=responses),
        ):
            items = await fetch_playgrounds("test-key")

        self.assertEqual([item["pfct_sn"] for item in items], ["PG1"])


class IngestLogTests(unittest.IsolatedAsyncioTestCase):
    async def test_records_successful_playground_ingestion(self):
        items = [{"pfct_sn": "PG1", "pfct_nm": "테스트 놀이터"}]

        with (
            patch(
                "ingest.get_settings",
                return_value=SimpleNamespace(playground_service_key="test-key"),
            ),
            patch(
                "ingest.fetch_playgrounds",
                new=AsyncMock(return_value=items),
            ),
            patch("ingest.replace_playgrounds", return_value=(1, 2)),
            patch("ingest.record_ingest_log") as record_log,
        ):
            result = await ingest_playgrounds()

        self.assertEqual(result, (1, 2))
        record_log.assert_called_once()
        self.assertEqual(record_log.call_args.args[0], "playgrounds")
        self.assertEqual(record_log.call_args.args[2:], (1, 1, 0, "2건 정리"))

    async def test_records_failed_playground_ingestion_and_reraises(self):
        error = RuntimeError("API 장애")

        with (
            patch(
                "ingest.get_settings",
                return_value=SimpleNamespace(playground_service_key="test-key"),
            ),
            patch(
                "ingest.fetch_playgrounds",
                new=AsyncMock(side_effect=error),
            ),
            patch("ingest.record_ingest_log") as record_log,
        ):
            with self.assertRaisesRegex(RuntimeError, "API 장애"):
                await ingest_playgrounds()

        record_log.assert_called_once()
        self.assertEqual(record_log.call_args.args[0], "playgrounds")
        self.assertEqual(
            record_log.call_args.args[2:],
            (0, 0, 1, "RuntimeError: API 장애"),
        )


class RecordIngestLogTests(unittest.TestCase):
    def test_persists_ingestion_result(self):
        test_engine = create_engine("sqlite://")
        SQLModel.metadata.create_all(test_engine)

        with patch("ingest.engine", test_engine):
            record_ingest_log(
                source="playgrounds",
                started_at="2026-07-24T00:00:00+00:00",
                fetched=10,
                upserted=9,
                failed=1,
                message="검증용",
            )

        with Session(test_engine) as session:
            log = session.exec(select(IngestLog)).one()

        self.assertEqual(log.source, "playgrounds")
        self.assertEqual(log.fetched, 10)
        self.assertEqual(log.upserted, 9)
        self.assertEqual(log.failed, 1)
        self.assertEqual(log.message, "검증용")
        self.assertIsNotNone(log.finished_at)


if __name__ == "__main__":
    unittest.main()
