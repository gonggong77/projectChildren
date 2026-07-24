import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

import main
from models import (
    IngestLog,
    Performance,
    PerformanceImage,
    PerformanceRelate,
    Playground,
    Venue,
    BoxofficeRanking,
)
from schemas import ListResponse


class HealthApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "test.db"
        self.engine = create_engine(
            f"sqlite:///{db_path.as_posix()}",
            connect_args={"check_same_thread": False},
        )
        SQLModel.metadata.create_all(self.engine)
        self.engine_patch = patch.object(main, "engine", self.engine)
        self.engine_patch.start()
        self.client = TestClient(main.app)

    def tearDown(self):
        self.engine_patch.stop()
        self.engine.dispose()
        self.temp_dir.cleanup()

    def test_returns_status_and_null_when_ingestion_has_not_run(self):
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "last_ingested_at": None, "sync_status": "idle"},
        )

    def test_returns_latest_finished_ingestion_time(self):
        with Session(self.engine) as session:
            session.add_all(
                [
                    IngestLog(
                        source="performances",
                        finished_at="2026-07-24T01:00:00+00:00",
                    ),
                    IngestLog(
                        source="playgrounds",
                        finished_at="2026-07-24T02:00:00+00:00",
                    ),
                ]
            )
            session.commit()

        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "ok",
                "last_ingested_at": "2026-07-24T02:00:00+00:00",
                "sync_status": "idle",
            },
        )


class PerformancesApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "test.db"
        self.engine = create_engine(
            f"sqlite:///{db_path.as_posix()}",
            connect_args={"check_same_thread": False},
        )
        SQLModel.metadata.create_all(self.engine)
        self.engine_patch = patch.object(main, "engine", self.engine)
        self.engine_patch.start()
        self.client = TestClient(main.app)

        with Session(self.engine) as session:
            session.add_all(
                [
                    Venue(
                        mt10id="FC1",
                        fcltynm="첫 번째 극장",
                        adres="서울특별시 강남구 테헤란로 1",
                    ),
                    Performance(
                        mt20id="PF1",
                        prfnm="공룡 대모험",
                        prfpdfrom="2026-08-10",
                        prfpdto="2026-08-20",
                        fcltynm="첫 번째 극장",
                        mt10id="FC1",
                        poster="https://example.com/1.jpg",
                        area="서울특별시",
                        genrenm="뮤지컬",
                        shcate="GGGA",
                        prfstate="공연예정",
                    ),
                    Performance(
                        mt20id="PF2",
                        prfnm="가나다 공연",
                        prfpdfrom="2026-07-30",
                        prfpdto="2026-08-05",
                        fcltynm="두 번째 극장",
                        area="경기도",
                        signgucode="41",
                        signgucodesub="4111",
                        genrenm="연극",
                        shcate="AAAA",
                        prfstate="공연중",
                    ),
                    Performance(
                        mt20id="PF3",
                        prfnm="공룡뮤지컬",
                        prfpdfrom="2026-08-21",
                        prfpdto="2026-08-25",
                        area="부산광역시",
                        signgucode="26",
                        signgucodesub="2635",
                        genrenm="뮤지컬",
                        shcate="GGGA",
                        prfstate="공연예정",
                    ),
                ]
            )
            session.commit()

    def tearDown(self):
        self.engine_patch.stop()
        self.engine.dispose()
        self.temp_dir.cleanup()

    def test_returns_soonest_performances_with_paging_metadata(self):
        response = self.client.get("/api/performances?page=1&size=2")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(
            (body["total"], body["page"], body["size"]),
            (3, 1, 2),
        )
        self.assertEqual(
            [item["mt20id"] for item in body["items"]],
            ["PF2", "PF1"],
        )
        self.assertEqual(body["items"][1]["poster"], "https://example.com/1.jpg")

    def test_search_ignores_whitespace_in_performance_name(self):
        response = self.client.get(
            "/api/performances",
            params={"q": " 공 룡 "},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total"], 2)

    def test_filters_performances_overlapping_requested_period(self):
        response = self.client.get(
            "/api/performances",
            params={"from": "2026-08-06", "to": "2026-08-20"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["mt20id"] for item in response.json()["items"]],
            ["PF1"],
        )

    def test_filters_by_performance_state(self):
        response = self.client.get(
            "/api/performances",
            params={"prfstate": "공연중"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total"], 1)
        self.assertEqual(
            [item["mt20id"] for item in response.json()["items"]],
            ["PF2"],
        )

    def test_filters_by_shcate(self):
        response = self.client.get(
            "/api/performances",
            params={"shcate": "GGGA"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total"], 2)
        self.assertEqual(
            [item["mt20id"] for item in response.json()["items"]],
            ["PF1", "PF3"],
        )

    def test_rejects_unknown_shcate_code(self):
        response = self.client.get(
            "/api/performances",
            params={"shcate": "ZZZZ"},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "INVALID_SHCATE")

    def test_rejects_unsupported_performance_state(self):
        response = self.client.get(
            "/api/performances",
            params={"prfstate": "공연완료"},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "VALIDATION_ERROR")

    def test_filters_by_sido_code(self):
        response = self.client.get(
            "/api/performances",
            params={"sido": "11"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["mt20id"] for item in response.json()["items"]],
            ["PF1"],
        )

    def test_filters_by_sido_and_gugun_codes(self):
        response = self.client.get(
            "/api/performances",
            params={"sido": "26", "gugun": "2635"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["mt20id"] for item in response.json()["items"]],
            ["PF3"],
        )

    def test_filters_legacy_rows_by_area_and_venue_address(self):
        response = self.client.get(
            "/api/performances",
            params={"sido": "11", "gugun": "1168"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["mt20id"] for item in response.json()["items"]],
            ["PF1"],
        )

    def test_rejects_malformed_region_codes(self):
        response = self.client.get(
            "/api/performances",
            params={"sido": "서울", "gugun": "116"},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "VALIDATION_ERROR")

    def test_sorts_by_performance_name(self):
        response = self.client.get(
            "/api/performances",
            params={"sort": "name"},
        )

        names = [item["prfnm"] for item in response.json()["items"]]
        self.assertEqual(names, sorted(names))

    def test_rejects_reversed_date_range(self):
        response = self.client.get(
            "/api/performances",
            params={"from": "2026-08-20", "to": "2026-08-01"},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json(),
            {
                "code": "INVALID_DATE_RANGE",
                "message": "from은 to보다 늦을 수 없습니다.",
            },
        )


class PerformanceBatchApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "test.db"
        self.engine = create_engine(
            f"sqlite:///{db_path.as_posix()}",
            connect_args={"check_same_thread": False},
        )
        SQLModel.metadata.create_all(self.engine)
        self.engine_patch = patch.object(main, "engine", self.engine)
        self.engine_patch.start()
        self.client = TestClient(main.app)

        with Session(self.engine) as session:
            session.add_all(
                [
                    Performance(mt20id="PF1", prfnm="첫 번째 공연"),
                    Performance(mt20id="PF2", prfnm="두 번째 공연"),
                ]
            )
            session.commit()

    def tearDown(self):
        self.engine_patch.stop()
        self.engine.dispose()
        self.temp_dir.cleanup()

    def test_returns_found_performances_in_requested_order(self):
        response = self.client.get(
            "/api/performances/batch",
            params={"ids": "PF2,UNKNOWN,PF1"},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(
            (body["total"], body["page"], body["size"]),
            (2, 1, 3),
        )
        self.assertEqual(
            [item["mt20id"] for item in body["items"]],
            ["PF2", "PF1"],
        )

    def test_deduplicates_repeated_ids(self):
        response = self.client.get(
            "/api/performances/batch",
            params={"ids": "PF1,PF1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["size"], 1)
        self.assertEqual(
            [item["mt20id"] for item in response.json()["items"]],
            ["PF1"],
        )

    def test_rejects_empty_ids(self):
        response = self.client.get(
            "/api/performances/batch",
            params={"ids": ", ,"},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "EMPTY_PERFORMANCE_IDS")

    def test_rejects_more_than_one_hundred_ids(self):
        response = self.client.get(
            "/api/performances/batch",
            params={"ids": ",".join(f"PF{index}" for index in range(101))},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "TOO_MANY_PERFORMANCE_IDS")


class PerformanceDetailApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "test.db"
        self.engine = create_engine(
            f"sqlite:///{db_path.as_posix()}",
            connect_args={"check_same_thread": False},
        )
        SQLModel.metadata.create_all(self.engine)
        self.engine_patch = patch.object(main, "engine", self.engine)
        self.engine_patch.start()
        self.client = TestClient(main.app)

        with Session(self.engine) as session:
            session.add(
                Venue(
                    mt10id="FC1",
                    fcltynm="어린이 극장",
                    adres="서울특별시 종로구 대학로 1",
                    telno="02-123-4567",
                    la=37.58,
                    lo=127.0,
                    parkinglot="Y",
                    suyu="Y",
                    elevbarrier="Y",
                )
            )
            session.add(
                Performance(
                    mt20id="PF1",
                    prfnm="공룡 대모험",
                    poster="https://example.com/poster.jpg",
                    genrenm="뮤지컬",
                    prfstate="공연중",
                    prfage="36개월 이상",
                    prfruntime="60분",
                    pcseguidance="전석 30,000원",
                    prfpdfrom="2026-07-01",
                    prfpdto="2026-08-31",
                    dtguidance="토요일 11:00",
                    fcltynm="어린이 극장",
                    mt10id="FC1",
                    sty="공룡 친구들의 모험",
                    prfcast="배우 어린이",
                    updatedate="2026-07-24",
                )
            )
            session.add_all(
                [
                    PerformanceRelate(
                        mt20id="PF1",
                        relatenm="두 번째 예매처",
                        relateurl="https://example.com/ticket-2",
                        sort_no=2,
                    ),
                    PerformanceRelate(
                        mt20id="PF1",
                        relatenm="첫 번째 예매처",
                        relateurl="https://example.com/ticket-1",
                        sort_no=1,
                    ),
                    PerformanceImage(
                        mt20id="PF1",
                        styurl="https://example.com/image-1.jpg",
                        sort_no=1,
                    ),
                ]
            )
            session.commit()

    def tearDown(self):
        self.engine_patch.stop()
        self.engine.dispose()
        self.temp_dir.cleanup()

    def test_returns_merged_performance_detail_in_source_order(self):
        response = self.client.get("/api/performances/PF1")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["mt20id"], "PF1")
        self.assertEqual(body["prfage"], "36개월 이상")
        self.assertEqual(body["venue"]["adres"], "서울특별시 종로구 대학로 1")
        self.assertEqual(body["venue"]["suyu"], "Y")
        self.assertEqual(
            [item["relatenm"] for item in body["relates"]],
            ["첫 번째 예매처", "두 번째 예매처"],
        )
        self.assertEqual(
            body["images"],
            [{"styurl": "https://example.com/image-1.jpg"}],
        )
        self.assertNotIn("updatedate", body)

    def test_returns_null_venue_when_performance_has_no_venue(self):
        with Session(self.engine) as session:
            session.add(Performance(mt20id="PF2", prfnm="공연장 미정 공연"))
            session.commit()

        response = self.client.get("/api/performances/PF2")

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["venue"])

    def test_returns_common_not_found_error(self):
        response = self.client.get("/api/performances/UNKNOWN")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "code": "PERFORMANCE_NOT_FOUND",
                "message": "공연 정보를 찾을 수 없습니다.",
            },
        )


class NearbyPlaygroundsApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "test.db"
        self.engine = create_engine(
            f"sqlite:///{db_path.as_posix()}",
            connect_args={"check_same_thread": False},
        )
        SQLModel.metadata.create_all(self.engine)
        self.engine_patch = patch.object(main, "engine", self.engine)
        self.engine_patch.start()
        self.client = TestClient(main.app)

        with Session(self.engine) as session:
            session.add_all(
                [
                    Playground(
                        pfct_sn="PG_NEAR",
                        pfct_nm="가까운 놀이터",
                        instl_place_cd="A010",
                        instl_place_nm="주택단지",
                        road_addr="서울특별시 가까운길 1",
                        lat=37.504,
                        lng=127.0,
                        is_public_access=0,
                    ),
                    Playground(
                        pfct_sn="PG_FAR",
                        pfct_nm="먼 놀이터",
                        instl_place_cd="A003",
                        instl_place_nm="도시공원",
                        lat=37.508,
                        lng=127.0,
                        is_public_access=1,
                    ),
                    Playground(
                        pfct_sn="PG_FARTHEST",
                        pfct_nm="가장 먼 공개 놀이터",
                        instl_place_cd="A030",
                        instl_place_nm="자연휴양림",
                        lat=37.5085,
                        lng=127.0,
                        is_public_access=1,
                    ),
                    Playground(
                        pfct_sn="PG_OUTSIDE",
                        pfct_nm="반경 밖 놀이터",
                        lat=37.52,
                        lng=127.0,
                        is_public_access=1,
                    ),
                ]
            )
            session.commit()

    def tearDown(self):
        self.engine_patch.stop()
        self.engine.dispose()
        self.temp_dir.cleanup()

    def test_returns_only_public_playgrounds_in_distance_order(self):
        response = self.client.get(
            "/api/playgrounds/nearby",
            params={"lat": 37.5, "lng": 127.0},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual((body["total"], body["page"], body["size"]), (2, 1, 20))
        self.assertFalse(body["fallback_used"])
        self.assertEqual(
            [item["pfct_sn"] for item in body["items"]],
            ["PG_FAR", "PG_FARTHEST"],
        )
        self.assertLess(
            body["items"][0]["distance_m"],
            body["items"][1]["distance_m"],
        )
        self.assertNotIn("is_public_access", body["items"][0])

    def test_applies_result_limit_after_distance_sorting(self):
        response = self.client.get(
            "/api/playgrounds/nearby",
            params={"lat": 37.5, "lng": 127.0, "limit": 1},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total"], 2)
        self.assertEqual(
            [item["pfct_sn"] for item in response.json()["items"]],
            ["PG_FAR"],
        )

    def test_falls_back_to_all_facilities_only_when_public_result_is_empty(self):
        response = self.client.get(
            "/api/playgrounds/nearby",
            params={"lat": 37.5, "lng": 127.0, "radius": 600},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["fallback_used"])
        self.assertEqual(body["total"], 1)
        self.assertEqual(
            [item["pfct_sn"] for item in body["items"]],
            ["PG_NEAR"],
        )

    def test_rejects_invalid_coordinates_radius_and_limit(self):
        response = self.client.get(
            "/api/playgrounds/nearby",
            params={"lat": 91, "lng": 127.0, "radius": 0, "limit": 21},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "VALIDATION_ERROR")


class CorsTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)

    def test_allows_configured_frontend_origin(self):
        response = self.client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["access-control-allow-origin"],
            "http://localhost:5173",
        )

    def test_rejects_unlisted_origin(self):
        response = self.client.options(
            "/api/health",
            headers={
                "Origin": "https://untrusted.example",
                "Access-Control-Request-Method": "GET",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertNotIn("access-control-allow-origin", response.headers)


class RegionsApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)

    def test_returns_sido_and_nested_gugun_codes(self):
        response = self.client.get("/api/regions")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total"], 17)
        self.assertEqual(body["page"], 1)
        self.assertEqual(body["size"], 17)

        seoul = next(item for item in body["items"] if item["code"] == "11")
        self.assertEqual(seoul["name"], "서울특별시")
        self.assertIn(
            {"code": "1168", "name": "강남구"},
            seoul["guguns"],
        )

    def test_keeps_codes_as_zero_preserving_strings(self):
        body = self.client.get("/api/regions").json()

        self.assertTrue(all(len(item["code"]) == 2 for item in body["items"]))
        self.assertTrue(
            all(
                len(gugun["code"]) == 4
                for item in body["items"]
                for gugun in item["guguns"]
            )
        )


class RankingsApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "test.db"
        self.engine = create_engine(
            f"sqlite:///{db_path.as_posix()}",
            connect_args={"check_same_thread": False},
        )
        SQLModel.metadata.create_all(self.engine)
        self.engine_patch = patch.object(main, "engine", self.engine)
        self.engine_patch.start()
        self.client = TestClient(main.app)

        with Session(self.engine) as session:
            session.add_all(
                [
                    BoxofficeRanking(
                        catecode="KID",
                        rnum=2,
                        mt20id="PF2",
                        prfnm="두 번째",
                        prfpd="2026.07.01~2026.07.31",
                        poster="https://example.com/2.jpg",
                    ),
                    BoxofficeRanking(
                        catecode="KID",
                        rnum=1,
                        mt20id="PF1",
                        prfnm="첫 번째",
                        prfpd="2026.08.01~2026.08.31",
                        poster="https://example.com/1.jpg",
                        area="서울",
                        seatcnt=100,
                        prfdtcnt=10,
                    ),
                    BoxofficeRanking(
                        catecode="KID",
                        rnum=3,
                        mt20id="PF3",
                        prfnm="세 번째",
                    ),
                ]
            )
            session.commit()

    def tearDown(self):
        self.engine_patch.stop()
        self.engine.dispose()
        self.temp_dir.cleanup()

    def test_returns_rankings_in_rnum_order_with_limit(self):
        response = self.client.get("/api/rankings", params={"limit": 2})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual((body["total"], body["page"], body["size"]), (3, 1, 2))
        self.assertEqual(
            [item["mt20id"] for item in body["items"]],
            ["PF1", "PF2"],
        )
        self.assertEqual(body["items"][0]["rnum"], 1)
        self.assertEqual(body["items"][0]["prfnm"], "첫 번째")


class CommonResponseTests(unittest.TestCase):
    def test_formats_not_found_error(self):
        response = TestClient(main.app).get("/api/does-not-exist")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {"code": "HTTP_404", "message": "Not Found"},
        )

    def test_formats_unhandled_server_error(self):
        client = TestClient(main.app, raise_server_exceptions=False)
        with self.assertLogs(main.logger, level="ERROR"):
            with patch.object(main, "Session", side_effect=RuntimeError("DB 오류")):
                response = client.get("/api/health")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "서버에서 요청을 처리하지 못했습니다.",
            },
        )

    def test_list_response_has_common_paging_fields(self):
        response = ListResponse[str](
            total=1,
            page=1,
            size=20,
            items=["PF1"],
        )

        self.assertEqual(
            response.model_dump(),
            {
                "total": 1,
                "page": 1,
                "size": 20,
                "items": ["PF1"],
            },
        )


class SyncApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "test.db"
        self.engine = create_engine(
            f"sqlite:///{db_path.as_posix()}",
            connect_args={"check_same_thread": False},
        )
        SQLModel.metadata.create_all(self.engine)
        self.engine_patch = patch.object(main, "engine", self.engine)
        self.engine_patch.start()
        self.client = TestClient(main.app)

    def tearDown(self):
        self.engine_patch.stop()
        self.engine.dispose()
        self.temp_dir.cleanup()

    def test_sync_disabled_without_secret(self):
        with patch("main.get_sync_secret", return_value=None):
            response = self.client.post("/api/sync")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["code"], "SYNC_DISABLED")

    def test_sync_rejects_wrong_secret(self):
        with patch("main.get_sync_secret", return_value="correct-secret"):
            response = self.client.post(
                "/api/sync",
                headers={"X-Sync-Secret": "wrong"},
            )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["code"], "UNAUTHORIZED")

    def test_sync_starts_in_background(self):
        with (
            patch("main.get_sync_secret", return_value="correct-secret"),
            patch("main.is_sync_running", return_value=False),
            patch("main.start_sync_background", return_value=True) as start_sync,
            patch(
                "main.get_sync_state",
                return_value={
                    "status": "running",
                    "started_at": "2026-07-24T03:00:00+00:00",
                    "finished_at": None,
                    "trigger": "api",
                    "error": None,
                    "result": None,
                },
            ),
        ):
            response = self.client.post(
                "/api/sync",
                headers={"X-Sync-Secret": "correct-secret"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["code"], "SYNC_STARTED")
        start_sync.assert_called_once_with(trigger="api")

    def test_sync_conflict_when_already_running(self):
        with (
            patch("main.get_sync_secret", return_value="correct-secret"),
            patch("main.is_sync_running", return_value=True),
        ):
            response = self.client.post(
                "/api/sync",
                headers={"X-Sync-Secret": "correct-secret"},
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "SYNC_IN_PROGRESS")

    def test_sync_status_requires_secret(self):
        with patch("main.get_sync_secret", return_value="correct-secret"):
            response = self.client.get("/api/sync/status")

        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
