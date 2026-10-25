from decimal import Decimal

import pytest

from core.scoring import calculate

D = Decimal


@pytest.mark.requirement("CR-05.1", "CR-05.2", "CR-05.3")
@pytest.mark.parametrize(
    ("income", "payments", "percent"),
    [
        ("100000", "15000", "15.00"),
        ("30000", "10000", "33.33"),
        ("100", "0", "0.00"),
        ("100", "100", "100.00"),
        ("100", "150", "150.00"),
        ("1", "10000000", "1000000000.00"),
    ],
)
def test_burden_formula(income, payments, percent):
    result = calculate(D(income), D(payments), D("300000"), 48)
    assert result.burden_percent == D(percent)
    assert result.burden_amount == D(payments)


@pytest.mark.requirement("CR-06.1", "CR-06.2", "CR-06.3")
@pytest.mark.parametrize(
    ("payments", "points"),
    [
        ("0", 450),
        ("10000", 450),
        ("10000.01", 350),
        ("30000", 350),
        ("30000.01", 200),
        ("50000", 200),
        ("50000.01", 80),
        ("70000", 80),
        ("70000.01", 0),
        ("200000", 0),
    ],
)
def test_burden_score_boundaries(payments, points):
    assert calculate(D("100000"), D(payments), D("300000"), 48).details["burden"] == points


@pytest.mark.requirement("CR-06.1", "CR-06.2", "CR-06.3")
@pytest.mark.parametrize(
    ("months", "points"),
    [(0, 0), (1, 40), (5, 40), (6, 100), (11, 100), (12, 180), (35, 180), (36, 250), (684, 250)],
)
def test_tenure_score_boundaries(months, points):
    assert calculate(D("100000"), D("15000"), D("300000"), months).details["tenure"] == points


@pytest.mark.requirement("CR-06.1", "CR-06.2", "CR-06.3")
@pytest.mark.parametrize(
    ("amount", "points"),
    [
        ("600000", 300),
        ("600000.01", 220),
        ("1200000", 220),
        ("1200000.01", 100),
        ("2400000", 100),
        ("2400000.01", 0),
    ],
)
def test_amount_score_boundaries(amount, points):
    assert calculate(D("100000"), D("15000"), D(amount), 48).details["amount"] == points


@pytest.mark.requirement("CR-06.2", "CR-06.3")
def test_extremes_determinism_and_example():
    assert calculate(D("100000"), D("0"), D("10000"), 48).score == 1000
    assert calculate(D("1000"), D("1000"), D("5000000"), 0).score == 0
    first = calculate(D("100000"), D("15000"), D("300000"), 48)
    assert first.score == 900
    assert first == calculate(D("100000"), D("15000"), D("300000"), 48)


@pytest.mark.requirement("CR-05.1", "CR-06.3")
@pytest.mark.parametrize(
    ("income", "payments", "amount", "months"),
    [
        ("0", "0", "1", 0),
        ("-1", "0", "1", 0),
        ("1", "-1", "1", 0),
        ("1", "0", "0", 0),
        ("1", "0", "1", -1),
        ("NaN", "0", "1", 0),
        ("1", "Infinity", "1", 0),
        ("1", "0", "-Infinity", 0),
    ],
)
def test_invalid_direct_service_inputs(income, payments, amount, months):
    with pytest.raises(ValueError):
        calculate(D(income), D(payments), D(amount), months)
