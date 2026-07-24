"""배포·기동 시 공공 API → SQLite 동기화 실행기."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Literal

from sqlmodel import Session, func, select

from ingest import (
    ingest_boxoffice,
    ingest_kopis_performances,
    ingest_playgrounds,
)
from models import Performance

logger = logging.getLogger(__name__)

SyncStatus = Literal["idle", "running", "success", "failed"]

_lock = asyncio.Lock()
_state: dict[str, Any] = {
    "status": "idle",
    "started_at": None,
    "finished_at": None,
    "trigger": None,
    "error": None,
    "result": None,
}


def get_sync_state() -> dict[str, Any]:
    """현재 동기화 상태를 복사해 반환한다."""
    return dict(_state)


def is_sync_running() -> bool:
    return _state["status"] == "running"


def count_performances(engine) -> int:
    with Session(engine) as session:
        return session.exec(select(func.count()).select_from(Performance)).one()


async def _execute_ingest(trigger: str) -> dict[str, Any]:
    """실제 적재를 수행하고 상태를 갱신한다. 호출 전 status=running 이어야 한다."""
    logger.info("데이터 동기화 시작 (trigger=%s)", trigger)
    try:
        perf_upserted, perf_deleted, detailed, venue_upserted = (
            await ingest_kopis_performances()
        )
        ranking_upserted = await ingest_boxoffice()
        playground_upserted, playground_deleted = await ingest_playgrounds()
        result = {
            "performances": {
                "upserted": perf_upserted,
                "deleted": perf_deleted,
                "detailed": detailed,
                "venues": venue_upserted,
            },
            "boxoffice": {"upserted": ranking_upserted},
            "playgrounds": {
                "upserted": playground_upserted,
                "deleted": playground_deleted,
            },
        }
        _state.update(
            {
                "status": "success",
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "result": result,
                "error": None,
            }
        )
        logger.info("데이터 동기화 완료 (trigger=%s)", trigger)
        return result
    except Exception as exc:
        _state.update(
            {
                "status": "failed",
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "error": f"{type(exc).__name__}: {exc}",
            }
        )
        logger.exception("데이터 동기화 실패 (trigger=%s)", trigger)
        raise


def start_sync_background(*, trigger: str) -> bool:
    """백그라운드에서 동기화를 시작한다. 이미 실행 중이면 False."""
    if is_sync_running():
        return False

    started_at = datetime.now(timezone.utc).isoformat()
    _state.update(
        {
            "status": "running",
            "started_at": started_at,
            "finished_at": None,
            "trigger": trigger,
            "error": None,
            "result": None,
        }
    )

    async def _runner() -> None:
        async with _lock:
            try:
                await _execute_ingest(trigger)
            except Exception:
                # 상태는 _execute_ingest에서 기록한다.
                pass

    asyncio.create_task(_runner())
    return True
