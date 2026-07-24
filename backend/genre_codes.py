"""KOPIS 장르 코드(shcate) 상수와 genrenm 역매핑.

docs/PRD.md 부록 A · docs/kopis_openapi_code_v3.7.md §2 기준.
목록/상세 XML에는 shcate가 없으므로 genrenm으로 코드를 확정한다.
"""

from __future__ import annotations

# PRD 부록 A 허용 코드 (필터 화이트리스트)
SHCATE_CODES: tuple[str, ...] = (
    "AAAA",
    "GGGA",
    "CCCA",
    "CCCC",
    "BBBC",
    "EEEB",
    "EEEA",
)

SHCATE_LABELS: dict[str, str] = {
    "AAAA": "연극",
    "GGGA": "뮤지컬",
    "CCCA": "서양음악",
    "CCCC": "한국음악",
    "BBBC": "무용",
    "EEEB": "서커스·마술",
    "EEEA": "복합",
}

# 실측 genrenm → shcate (추측 없이 확인된 표기만)
_GENRENM_TO_SHCATE: dict[str, str] = {
    "연극": "AAAA",
    "뮤지컬": "GGGA",
    "서양음악": "CCCA",
    "서양음악(클래식)": "CCCA",
    "한국음악": "CCCC",
    "한국음악(국악)": "CCCC",
    "무용": "BBBC",
    "무용(서양/한국무용)": "BBBC",
    "서커스/마술": "EEEB",
    "서커스·마술": "EEEB",
    "복합": "EEEA",
}


def map_genrenm_to_shcate(genrenm: str | None) -> str | None:
    """장르명으로 shcate를 반환한다. 알 수 없으면 None."""
    if genrenm is None:
        return None
    normalized = genrenm.strip()
    if not normalized:
        return None
    return _GENRENM_TO_SHCATE.get(normalized)
