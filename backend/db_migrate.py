"""기존 SQLite에 누락된 컬럼을 안전하게 추가한다."""

from __future__ import annotations

from sqlalchemy import text
from sqlmodel import Session, select

from genre_codes import map_genrenm_to_shcate
from models import Performance


def ensure_performance_shcate_column(engine) -> None:
    """performances.shcate가 없으면 추가하고 genrenm으로 백필한다."""
    with engine.begin() as connection:
        columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(performances)"))
        }
        if "shcate" not in columns:
            connection.execute(
                text("ALTER TABLE performances ADD COLUMN shcate TEXT")
            )

    with Session(engine) as session:
        rows = session.exec(
            select(Performance).where(
                Performance.shcate.is_(None),
                Performance.genrenm.is_not(None),
            )
        ).all()
        updated = False
        for performance in rows:
            mapped = map_genrenm_to_shcate(performance.genrenm)
            if mapped is not None:
                performance.shcate = mapped
                session.add(performance)
                updated = True
        if updated:
            session.commit()
