import re


def safe_pct(part: int | float, whole: int | float, precision: int = 1) -> float:
    if not whole:
        return 0.0
    return round((part / whole) * 100, precision)


def normalize_key(value: str | None) -> str:
    if not value:
        return ''
    return re.sub(r'\s+', ' ', str(value).strip().lower())


def booth_ranking_score(coverage_pct: float, positive_pct: float, followup_pct: float) -> float:
    return round((coverage_pct * 0.5) + (positive_pct * 0.35) + ((100 - followup_pct) * 0.15), 1)


def telecaller_efficiency_score(
    reach_pct: float,
    positive_pct: float,
    followup_not_required_pct: float,
) -> float:
    return round(
        (reach_pct * 0.55)
        + (positive_pct * 0.25)
        + (followup_not_required_pct * 0.20),
        1,
    )
