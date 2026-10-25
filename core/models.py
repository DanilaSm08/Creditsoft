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


class LoanOffer(models.Model):
    name = models.CharField("Название", max_length=100, unique=True)
    logo = models.CharField(
        max_length=24,
        choices=[("north", "Север"), ("axis", "Ось"), ("horizon", "Горизонт"), ("pulse", "Пульс")],
    )
    annual_rate = models.DecimalField(
        max_digits=5, decimal_places=2, validators=[MinValueValidator(0)]
    )
    min_score = models.PositiveIntegerField(validators=[MaxValueValidator(1000)])
    max_burden = models.DecimalField(
        max_digits=5, decimal_places=2, validators=[MinValueValidator(0)]
    )
    min_amount = models.DecimalField(max_digits=12, decimal_places=2)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2)
    min_term = models.PositiveIntegerField()
    max_term = models.PositiveIntegerField()
    active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ("annual_rate", "pk")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(min_amount__lte=models.F("max_amount")),
                name="offer_amount_order",
            ),
            models.CheckConstraint(
                condition=models.Q(min_term__lte=models.F("max_term")), name="offer_term_order"
            ),
        ]

    def __str__(self):
        return self.name


class Assessment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assessments"
    )
    score = models.PositiveIntegerField(validators=[MaxValueValidator(1000)])
    burden_amount = models.DecimalField(max_digits=12, decimal_places=2)
    burden_percent = models.DecimalField(max_digits=12, decimal_places=2)
    input_snapshot = models.JSONField()
    score_details = models.JSONField()
    offers_snapshot = models.JSONField()
    rules_version = models.CharField(max_length=20, default="edu-1.0")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at", "-pk")
        indexes = [models.Index(fields=["user", "-created_at"], name="assessment_user_date")]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(score__gte=0, score__lte=1000), name="score_range"
            )
        ]

    def __str__(self):
        return f"Оценка {self.pk}: {self.score}/1000"
