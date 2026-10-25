"""Versioned educational rules; this is not a bank scoring model."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

RULES_VERSION = "edu-1.0"
HUNDRED = Decimal("100")


@dataclass(frozen=True)
class ScoreResult:
    score: int
    burden_amount: Decimal
    burden_percent: Decimal
    details: dict[str, int]


def calculate(
    monthly_income: Decimal,
    current_payments: Decimal,
    requested_amount: Decimal,
    experience_months: int,
) -> ScoreResult:
    values = (monthly_income, current_payments, requested_amount)
    if any(not value.is_finite() for value in values):
        raise ValueError("Financial values must be finite")
    if (
        monthly_income <= 0
        or current_payments < 0
        or requested_amount <= 0
        or experience_months < 0
    ):
        raise ValueError("Invalid financial or employment input")
    # Classification uses the unrounded ratio; rounding is for display only.
    burden = current_payments / monthly_income * HUNDRED
    burden_points = next(
        (
            points
            for ceiling, points in [(10, 450), (30, 350), (50, 200), (70, 80)]
            if burden <= ceiling
        ),
        0,
    )
    tenure_points = next(
        (
            points
            for floor, points in [(36, 250), (12, 180), (6, 100), (1, 40)]
            if experience_months >= floor
        ),
        0,
    )
    income_ratio = requested_amount / (monthly_income * 12)
    amount_points = next(
        (
            points
            for ceiling, points in [(Decimal("0.5"), 300), (Decimal("1"), 220), (Decimal("2"), 100)]
            if income_ratio <= ceiling
        ),
        0,
    )
    details = {"burden": burden_points, "tenure": tenure_points, "amount": amount_points}
    return ScoreResult(
        sum(details.values()),
        current_payments.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        burden.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        details,
    )
