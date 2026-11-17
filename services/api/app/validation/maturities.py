"""Source-only maturity context. Suppress incomplete schedules rather than display partial zeroes."""

from decimal import Decimal

from app.finance.calculations import ratio
from app.models.entities import Filing, MaturityBucket


def maturity_context(filing: Filing, buckets: list[MaturityBucket]) -> dict:
    first = filing.period_end.year + 1
    annual = [b for b in buckets if b.kind == "EXACT_YEAR"]
    complete = (
        len(buckets) == 6
        and len(annual) == 5
        and {b.year_start for b in annual} == set(range(first, first + 5))
        and all(
            b.currency == "USD"
            and b.as_of == filing.period_end
            and b.amount.is_finite()
            and b.amount >= 0
            and b.validation_state == "CROSS_CHECKED"
            for b in buckets
        )
        and all(b.year_end == b.year_start for b in annual)
        and sum(b.kind == "THEREAFTER" and b.year_start is None and b.year_end is None for b in buckets) == 1
    )
    empty = {
        "near_term_principal": None,
        "near_term_share": None,
        "near_term_years": [first, first + 1],
        "next_positive_bucket_id": None,
        "next_positive_year": None,
        "next_positive_principal": None,
    }
    if not complete:
        return empty
    near = sum((b.amount for b in annual if b.year_start in {first, first + 1}), Decimal(0))
    total = sum((b.amount for b in buckets), Decimal(0))
    positive = sorted((b for b in annual if b.amount > 0), key=lambda b: b.year_start or 0)
    next_bucket = positive[0] if positive else None
    return {
        **empty,
        "near_term_principal": near,
        "near_term_share": ratio(near, total),
        "next_positive_bucket_id": next_bucket.id if next_bucket else None,
        "next_positive_year": next_bucket.year_start if next_bucket else None,
        "next_positive_principal": next_bucket.amount if next_bucket else None,
    }
