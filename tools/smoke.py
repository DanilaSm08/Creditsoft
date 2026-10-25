"""Exercise the deployed Nginx/Gunicorn/PostgreSQL stack in a real browser."""

import json
import os
import secrets
import sys
from datetime import UTC, datetime
from pathlib import Path

import requests
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tests.test_browser import BorrowerPage, screenshot  # noqa: E402

URL = "http://127.0.0.1:8080"
OUT = ROOT / "artifacts/reports/deployment"
OUT.mkdir(parents=True, exist_ok=True)
os.environ["SCREENSHOT_DIR"] = str(OUT)
credentials_file = ROOT / ".local/demo_credentials.json"
existing = credentials_file.exists()
credentials = (
    json.loads(credentials_file.read_text())
    if existing
    else {"username": "demo", "password": secrets.token_urlsafe(20)}
)
health = requests.get(URL + "/health/", timeout=10)
health.raise_for_status()
assert health.json() == {"status": "ok", "database": "postgresql"}
with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 1000}, locale="ru-RU")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(URL + "/accounts/login/")
    screenshot(page, "deployment-login.png")
    if existing:
        page.get_by_label("Логин", exact=True).fill(credentials["username"])
        page.get_by_label("Пароль", exact=True).fill(credentials["password"])
        page.get_by_role("button", name="Войти", exact=True).click()
    else:
        page.get_by_role("link", name="Регистрация", exact=True).click()
        page.get_by_label("Логин", exact=True).fill(credentials["username"])
        page.get_by_label("Пароль", exact=True).fill(credentials["password"])
        page.get_by_label("Подтверждение пароля", exact=True).fill(credentials["password"])
        page.get_by_role("button", name="Создать аккаунт").click()
        expect(page.get_by_role("heading", name="Анкета заёмщика")).to_be_visible()
        credentials_file.write_text(json.dumps(credentials), encoding="utf-8")
    screen = BorrowerPage(page, URL)
    screen.fill_questionnaire()
    screen.save()
    screenshot(page, "deployment-questionnaire.png")
    page.get_by_role("button", name="Рассчитать оценку").click()
    expect(page.get_by_test_id("score")).to_have_text("900")
    expect(page.locator(".offer-card")).to_have_count(4)
    assert page.locator(".offer-bank img").evaluate_all(
        "images => images.every(i => i.complete && i.naturalWidth > 0)"
    )
    screenshot(page, "deployment-results.png")
    page.reload()
    expect(page.get_by_test_id("score")).to_have_text("900")
    assert not errors, errors
    page.get_by_role("button", name="Выйти").click()
    expect(page.get_by_role("heading", name="Вход", exact=True)).to_be_visible()
    browser.close()
result = {
    "recorded_at": datetime.now(UTC).isoformat(),
    "url": URL,
    "health": health.json(),
    "browser": "Chromium",
    "passed": True,
    "reused_existing_account": existing,
    "score": 900,
    "offer_count": 4,
    "javascript_errors": errors,
    "credential_file": ".local/demo_credentials.json",
}
(ROOT / "docs/evidence/deployment-smoke.json").write_text(
    json.dumps(result, indent=2), encoding="utf-8"
)
print(json.dumps(result, indent=2))
