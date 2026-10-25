from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client

from core.models import Assessment, LoanOffer
from core.offers import select_offers

from .factories import VALID_DATA

D = Decimal


@pytest.fixture
def prepared(db, client):
    user = User.objects.create_user("borrower", password="StudyPassword!4581")
    client.force_login(user)
    client.post("/", VALID_DATA)
    call_command("seed_catalogue", verbosity=0)
    return user


@pytest.mark.requirement("CR-07.1", "CR-07.2", "CR-07.3")
def test_catalogue_idempotence_and_sorted_selection(prepared):
    call_command("seed_catalogue", verbosity=0)
    assert LoanOffer.objects.count() == 4
    offers = list(select_offers(900, D("100000"), D("15000"), D("300000"), 36))
    assert [o.annual_rate for o in offers] == [D("12.90"), D("15.50"), D("18.90"), D("24.00")]
    assert str(offers[0]) == "Север · Стандарт"


@pytest.mark.requirement("CR-07.2", "CR-07.3")
@pytest.mark.parametrize(
    ("score", "payments", "amount", "term", "included"),
    [
        (850, "30000", "50000", 12, True),
        (849, "30000", "50000", 12, False),
        (850, "30000.01", "50000", 12, False),
        (850, "30000", "49999.99", 12, False),
        (850, "30000", "1000000", 60, True),
        (850, "30000", "1000000.01", 60, False),
        (850, "30000", "50000", 11, False),
        (850, "30000", "50000", 61, False),
    ],
)
def test_every_offer_filter_boundary(prepared, score, payments, amount, term, included):
    names = list(
        select_offers(score, D("100000"), D(payments), D(amount), term).values_list(
            "name", flat=True
        )
    )
    assert ("Север · Стандарт" in names) is included


@pytest.mark.requirement("CR-07.2", "CR-07.3")
def test_inactive_no_results_and_stable_tie(prepared):
    first = LoanOffer.objects.first()
    LoanOffer.objects.filter(pk=first.pk).update(active=False)
    assert first.pk not in select_offers(1000, D("100000"), D("0"), D("100000"), 36).values_list(
        "pk", flat=True
    )
    assert not select_offers(0, D("100000"), D("100000"), D("100000"), 36).exists()
    LoanOffer.objects.update(annual_rate=D("20"))
    ids = list(
        select_offers(1000, D("100000"), D("0"), D("100000"), 36).values_list("pk", flat=True)
    )
    assert ids == sorted(ids)


@pytest.mark.requirement("CR-08.1", "CR-08.2", "CR-08.3", "CR-05.3")
def test_result_snapshot_recalculation_and_catalogue_independence(prepared, client):
    response = client.post("/assess/")
    original = Assessment.objects.get()
    assert response.url == f"/results/{original.pk}/"
    assert original.score == 900
    assert original.burden_percent == D("15.00")
    assert len(original.offers_snapshot) == 4
    assert "passport_number" not in original.input_snapshot
    assert str(original) == f"Оценка {original.pk}: 900/1000"
    page = client.get(response.url)
    assert page.status_code == 200
    assert "Север" in page.content.decode()
    assert not page.context["changed"]
    assert client.get("/results/").url == response.url
    LoanOffer.objects.update(annual_rate=99)
    client.post("/", {**VALID_DATA, "current_payments": "110000"})
    assert client.get(response.url).context["changed"]
    second_response = client.post("/assess/")
    original.refresh_from_db()
    assert original.score == 900
    assert original.offers_snapshot[0]["annual_rate"] == "12.90"
    latest = Assessment.objects.first()
    assert latest.pk != original.pk
    assert latest.burden_percent == D("110.00")
    assert not latest.offers_snapshot
    assert "Подходящих предложений нет" in client.get(second_response.url).content.decode()


@pytest.mark.requirement("CR-08.3", "CR-01.3")
def test_missing_questionnaire_empty_result_and_authorization(db, client):
    assert client.post("/assess/").status_code == 302
    user = User.objects.create_user("empty")
    client.force_login(user)
    assert "Оценка ещё не рассчитана" in client.get("/results/").content.decode()
    assert client.post("/assess/").url == "/"
    assert not Assessment.objects.exists()
    assert client.get("/assess/").status_code == 405
    assert client.get("/results/999/").status_code == 404


@pytest.mark.requirement("CR-08.3", "CR-01.3")
def test_result_owner_enforced_and_evaluation_csrf(prepared, client):
    response = client.post("/assess/")
    other = User.objects.create_user("other")
    client.force_login(other)
    assert client.get(response.url).status_code == 404
    browser = Client(enforce_csrf_checks=True)
    browser.force_login(prepared)
    assert browser.post("/assess/").status_code == 403
    client.force_login(prepared)
    assert client.post(response.url).status_code == 405
    assert client.post("/results/").status_code == 405
