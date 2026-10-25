from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from . import validation


class BorrowerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="borrower"
    )
    full_name = models.CharField("Фамилия и имя", max_length=150, validators=[validation.full_name])
    birth_date = models.DateField("Дата рождения", validators=[validation.adult_birth_date])
    passport_series = models.CharField(
        "Серия паспорта", max_length=4, validators=[validation.passport_series]
    )
    passport_number = models.CharField(
        "Номер паспорта", max_length=6, validators=[validation.passport_number]
    )
    employer = models.CharField("Место работы", max_length=200)
    experience_months = models.PositiveIntegerField(
        "Стаж на текущем месте, мес.", validators=[MaxValueValidator(684)]
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name


class FinancialData(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="finances"
    )
    monthly_income = models.DecimalField(
        "Ежемесячный доход, ₽",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(1), MaxValueValidator(10000000)],
    )
    current_payments = models.DecimalField(
        "Платежи по действующим кредитам, ₽/мес.",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(10000000)],
    )
    requested_amount = models.DecimalField(
        "Сумма нового кредита, ₽",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(10000), MaxValueValidator(5000000)],
    )
    term_months = models.PositiveIntegerField(
        "Срок нового кредита, мес.", validators=[MinValueValidator(6), MaxValueValidator(84)]
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(monthly_income__gte=1), name="income_positive"
            ),
            models.CheckConstraint(
                condition=models.Q(current_payments__gte=0), name="payments_nonnegative"
            ),
            models.CheckConstraint(
                condition=models.Q(requested_amount__gte=10000, requested_amount__lte=5000000),
                name="amount_range",
            ),
            models.CheckConstraint(
                condition=models.Q(term_months__gte=6, term_months__lte=84), name="term_range"
            ),
        ]

    def __str__(self):
        return f"Анкета пользователя {self.user_id}"
