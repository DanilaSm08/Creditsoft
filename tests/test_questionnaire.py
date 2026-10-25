from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from core.forms import FinanceForm, ProfileForm
from core.models import BorrowerProfile, FinancialData
from core.validation import adult_birth_date, age_at

from .factories import VALID_DATA


@pytest.fixture
def borrower(db, client):
    user = User.objects.create_user("borrower", password="StudyPassword!4581")
    client.force_login(user)
    return user


@pytest.mark.requirement("CR-02.1", "CR-02.2", "CR-03.1", "CR-03.2", "CR-04.1", "CR-04.2")
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("full_name", "Иван"),
        ("passport_series", "123"),
        ("passport_series", "１２３４"),
        ("passport_number", "12345a"),
        ("birth_date", "2015-01-01"),
        ("birth_date", "1900-01-01"),
        ("employer", ""),
        ("experience_months", "900"),
        ("experience_months", "400"),
        ("experience_months", "-1"),
        ("monthly_income", "0"),
        ("monthly_income", "-1"),
        ("monthly_income", "NaN"),
        ("monthly_income", "abc"),
        ("monthly_income", "10000001"),
        ("current_payments", "-1"),
        ("requested_amount", "9999.99"),
        ("requested_amount", "5000000.01"),
        ("term_months", "5"),
        ("term_months", "85"),
        ("term_months", "6.5"),
    ],
)
def test_invalid_fields_are_reported_without_partial_save(borrower, client, field, value):
    response = client.post("/", {**VALID_DATA, field: value})
    assert response.status_code == 200
    form = (
        response.context["profile_form"]
        if field in ProfileForm.Meta.fields
        else response.context["finance_form"]
    )
    assert field in form.errors
    assert "Изменения не сохранены" in response.content.decode()
    assert not BorrowerProfile.objects.exists()
    assert not FinancialData.objects.exists()


@pytest.mark.requirement("CR-02.3", "CR-03.3", "CR-04.3")
def test_save_reload_edit_and_isolation(borrower, client):
    assert client.post("/", VALID_DATA).status_code == 302
    response = client.get("/")
    assert response.context["profile_form"].instance.full_name == VALID_DATA["full_name"]
    assert response.context["finance_form"].instance.monthly_income == Decimal("100000")
    assert (
        client.post(
            "/", {**VALID_DATA, "monthly_income": "120000", "employer": "Новое место"}
        ).status_code
        == 302
    )
    assert FinancialData.objects.get(user=borrower).monthly_income == Decimal("120000")
    assert BorrowerProfile.objects.get(user=borrower).employer == "Новое место"
    other = User.objects.create_user("other")
    client.force_login(other)
    assert not client.get("/").context["profile_form"].instance.pk
    client.post("/", {**VALID_DATA, "full_name": "Петров Пётр", "user": borrower.pk})
    assert BorrowerProfile.objects.get(user=borrower).full_name == VALID_DATA["full_name"]
    assert BorrowerProfile.objects.get(user=other).full_name == "Петров Пётр"


@pytest.mark.requirement("CR-04.1", "CR-04.2", "CR-04.3")
def test_invalid_edit_keeps_saved_data_and_displays_both_forms(borrower, client):
    client.post("/", VALID_DATA)
    response = client.post("/", {**VALID_DATA, "full_name": "", "monthly_income": ""})
    assert response.context["profile_form"].errors
    assert response.context["finance_form"].errors
    assert FinancialData.objects.get(user=borrower).monthly_income == Decimal("100000")


@pytest.mark.requirement("CR-04.1")
def test_empty_form_and_methods(borrower, client):
    response = client.post("/", {})
    assert len(response.context["profile_form"].errors) == 6
    assert len(response.context["finance_form"].errors) == 4
    assert client.delete("/").status_code == 405


@pytest.mark.requirement("CR-03.1", "CR-03.2")
@pytest.mark.parametrize(("amount", "term"), [("10000", 6), ("5000000", 84)])
def test_inclusive_financial_boundaries_and_payments_above_income(db, amount, term):
    form = FinanceForm(
        {
            **VALID_DATA,
            "requested_amount": amount,
            "term_months": term,
            "current_payments": "150000",
        }
    )
    assert form.is_valid(), form.errors


@pytest.mark.requirement("CR-02.1", "CR-02.2")
def test_birthday_age_and_zero_tenure():
    assert age_at(date(2008, 10, 26), date(2026, 10, 25)) == 17
    assert age_at(date(2008, 10, 25), date(2026, 10, 25)) == 18
    with pytest.raises(ValidationError):
        adult_birth_date(date.today())
    form = ProfileForm({**VALID_DATA, "experience_months": "0", "employer": "Не работаю"})
    assert form.is_valid(), form.errors


@pytest.mark.requirement("CR-03.3", "CR-04.1")
def test_database_constraints_and_model_labels(borrower, client):
    client.post("/", VALID_DATA)
    assert str(BorrowerProfile.objects.get()) == VALID_DATA["full_name"]
    assert str(borrower.finances) == f"Анкета пользователя {borrower.pk}"
    with pytest.raises(IntegrityError), transaction.atomic():
        FinancialData.objects.filter(user=borrower).update(monthly_income=-1)
