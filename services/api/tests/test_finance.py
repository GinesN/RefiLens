from datetime import date
from decimal import Decimal as D

import pytest

from app.finance.calculations import (
    Observation,
    annual_interest,
    difference,
    ratio,
    scenario,
    select_bucket,
    stress_earnings,
)

# All values below are SYNTHETIC DEMO_FIXTURE test inputs, not company observations.


@pytest.mark.parametrize(
    "principal,old,new,expected",
    [
        ("100000000", ".04", ".06", "2000000"),
        ("100000000", ".06", ".04", "-2000000"),
        ("0", ".04", ".06", "0"),
        ("100", "0", "0", "0"),
        ("123456789.12", ".01234567", ".07654321", "7925622.1578027648"),
    ],
)
def test_interest(principal, old, new, expected):
    assert annual_interest(D(principal), D(old), D(new)) == D(expected)


@pytest.mark.parametrize("old,new", [(None, D(".05")), (D("-.01"), D(".05")), (D("0"), D("NaN"))])
def test_invalid_rates(old, new):
    with pytest.raises(ValueError):
        annual_interest(D(100), old, new)


def test_zero_missing_and_negative_denominator():
    assert ratio(D(0), D(10)) == 0
    assert ratio(D(10), D(0)) is None
    assert ratio(D(10), D(-1)) is None
    assert ratio(None, D(5)) is None
    assert stress_earnings(D(0), D(100)) == 0
    assert stress_earnings(None, D(20)) is None


@pytest.mark.parametrize(
    "currency,start,end",
    [
        ("EUR", None, date(2025, 12, 31)),
        ("USD", None, date(2024, 12, 31)),
        ("USD", date(2025, 1, 1), date(2025, 12, 31)),
    ],
)
def test_incompatible_observations(currency, start, end):
    a = Observation(D(100), "USD", None, date(2025, 12, 31))
    with pytest.raises(ValueError):
        difference(a, Observation(D(30), currency, start, end))


@pytest.mark.parametrize("kind", ["RANGE", "THEREAFTER", "UNALLOCATED"])
def test_broad_bucket_never_allocated_to_one_year(kind):
    b = {"kind": kind, "year_start": None, "amount": "1000"}
    with pytest.raises(ValueError):
        select_bucket(b, 2030)
    assert select_bucket(b, None) == 1000


def test_scenario_and_double_counting():
    inputs = dict(
        principal=D("100000000"),
        previous_rate=D(".04"),
        new_rate=D(".06"),
        baseline_interest=D("10000000"),
        baseline_ebit=D("50000000"),
        ebit_decline=D(20),
        baseline_ebitda=D("60000000"),
        ebitda_decline=D(25),
        already_refinanced=False,
    )
    result = scenario(**inputs)
    assert result["scenario_interest_expense"] == D("12000000")
    assert result["scenario_ebit_proxy"] == D("40000000")
    assert result["scenario_ebitda"] == D("45000000")
    assert result["spread_basis_points"] == 200
    assert result["interest_expense_delta"] == D("2000000")
    assert result["ebit_proxy_delta"] == D("-10000000")
    assert result["ebitda_delta"] == D("-15000000")
    with pytest.raises(ValueError, match="double count"):
        scenario(**{**inputs, "already_refinanced": True})
    with pytest.raises(ValueError, match="negative"):
        scenario(**{**inputs, "new_rate": D(0), "baseline_interest": D(1)})
