"""Shared questionnaire rules; financial values use Decimal throughout."""

import re
from datetime import date

from django.core.exceptions import ValidationError


def full_name(value):
    if len(value.split()) < 2:
        raise ValidationError("Укажите фамилию и имя.")


def passport_series(value):
    if not re.fullmatch(r"[0-9]{4}", value):
        raise ValidationError("Серия должна содержать 4 цифры.")


def passport_number(value):
    if not re.fullmatch(r"[0-9]{6}", value):
        raise ValidationError("Номер должен содержать 6 цифр.")


def age_at(birth_date, today=None):
    today = today or date.today()
    return (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )


def adult_birth_date(value):
    if not 18 <= age_at(value) <= 75:
        raise ValidationError("Возраст заёмщика должен быть от 18 до 75 лет.")
