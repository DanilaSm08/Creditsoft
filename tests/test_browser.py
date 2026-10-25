import os
from pathlib import Path

import pytest
from playwright.sync_api import expect

from .factories import VALID_DATA


class BorrowerPage:
    def __init__(self, page, base_url):
        self.page = page
        self.base_url = base_url

    def register(self, username="browser-borrower"):
        self.page.goto(self.base_url + "/accounts/register/")
        self.page.get_by_label("Логин", exact=True).fill(username)
        self.page.get_by_label("Пароль", exact=True).fill("StudyPassword!4581")
        self.page.get_by_label("Подтверждение пароля", exact=True).fill("StudyPassword!4581")
        self.page.get_by_role("button", name="Создать аккаунт").click()
        expect(self.page.get_by_role("heading", name="Анкета заёмщика")).to_be_visible()

    def fill_questionnaire(self, data=None):
        values = {**VALID_DATA, **(data or {})}
        labels = {
            "full_name": "Фамилия и имя",
            "birth_date": "Дата рождения",
            "passport_series": "Серия паспорта",
            "passport_number": "Номер паспорта",
            "employer": "Место работы",
            "experience_months": "Стаж на текущем месте, мес.",
            "monthly_income": "Ежемесячный доход, ₽",
            "current_payments": "Платежи по действующим кредитам, ₽/мес.",
            "requested_amount": "Сумма нового кредита, ₽",
            "term_months": "Срок нового кредита, мес.",
        }
        for field, label in labels.items():
            self.page.get_by_label(label, exact=True).fill(str(values[field]))

    def save(self):
        self.page.get_by_role("button", name="Сохранить анкету", exact=True).click()
        expect(self.page.get_by_role("status")).to_contain_text("Анкета сохранена")


def screenshot(page, name):
    directory = Path(os.getenv("SCREENSHOT_DIR", "artifacts/screenshots"))
    directory.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(directory / name), full_page=True, animations="disabled")


@pytest.mark.e2e
@pytest.mark.requirement("PR-01", "CR-01.2", "CR-01.3", "CR-02.3", "CR-03.3", "CR-04.2", "CR-04.3")
def test_browser_questionnaire_round_trip(page, live_server):
    page.set_viewport_size({"width": 1440, "height": 1000})
    screen = BorrowerPage(page, live_server.url)
    page.goto(live_server.url + "/accounts/login/")
    screenshot(page, "login-desktop.png")
    screen.register()
    screen.fill_questionnaire()
    screen.save()
    screenshot(page, "questionnaire-desktop.png")
    page.reload()
    expect(page.get_by_label("Ежемесячный доход, ₽", exact=True)).to_have_value("100000.00")
    page.get_by_label("Ежемесячный доход, ₽", exact=True).fill("0")
    page.get_by_role("button", name="Сохранить анкету", exact=True).click()
    expect(page.locator("#id_monthly_income_errors")).not_to_be_empty()
    screenshot(page, "validation-desktop.png")
    page.set_viewport_size({"width": 390, "height": 844})
    screen.fill_questionnaire({"monthly_income": "120000"})
    screen.save()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    screenshot(page, "questionnaire-mobile.png")
    page.get_by_role("button", name="Выйти").click()
    expect(page.get_by_role("heading", name="Вход", exact=True)).to_be_visible()
    page.goto(live_server.url + "/")
    expect(page.get_by_role("heading", name="Вход", exact=True)).to_be_visible()
