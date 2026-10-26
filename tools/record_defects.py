"""Register observed setup defects retrospectively; never invent discovery dates."""

import json
from datetime import UTC, datetime

from forge import REPO, ROOT, api, pages

defects = [
    {
        "id": "BUG-04",
        "title": "HTML-отчёт pytest не показывает строки при открытии file:// из кириллической папки",
        "cause": "Клиентский код pytest-html вызывает History.pushState с несовпадающим file:// URL; Chromium останавливает отрисовку таблицы.",
        "fix": "Отчёт просматривается через локальный HTTP-сервер с ASCII-путём. Снимок ожидает появления строк результатов; README содержит команду просмотра.",
        "evidence": "tools/capture_evidence.py; docs/images/infrastructure/tests.png; artifacts/runs/release/tests.html содержит 91 результат",
    },
    {
        "id": "BUG-01",
        "title": "CI не загружает артефакты по loopback-адресу сервера",
        "cause": "Loopback-адрес сервера указывает на контейнер задания при обращении из контейнера.",
        "fix": "Я настроил сетевой адрес сервера артефактов для изолированного контейнера и проверил загрузку файлов.",
        "evidence": "docs/evidence/defects.json; artifacts/runs/prototype-browser",
    },
    {
        "id": "BUG-02",
        "title": "Метрики Windows прерываются на чтении журнала в неверной кодировке",
        "cause": "Дочерний Python писал cp1251; tools/check.py читал UTF-8, возникал UnicodeDecodeError при выводе упавших тестов.",
        "fix": "Дочерним процессам передаются PYTHONUTF8=1 и PYTHONIOENCODING=utf-8.",
        "evidence": "tools/check.py; docs/evidence/metrics/prototype-browser.json; исходный вывод выполнения содержит UnicodeDecodeError",
    },
    {
        "id": "BUG-03",
        "title": "Изоляция Django и Playwright не настроена для проверок БД",
        "cause": "Проверка ограничений ModelForm обращалась к БД без db fixture; завершение браузерного теста сталкивалось с активным циклом Playwright.",
        "fix": "Добавлена db fixture; разрешение синхронных ORM-вызовов ограничено tests/conftest.py и изолированной тестовой БД.",
        "evidence": "docs/evidence/prototype-first-test-failure.txt; docs/evidence/browser-first-teardown-failure.txt; 91 passed SQLite/PostgreSQL",
    },
]
existing = pages(REPO + "/issues", state="all")
for defect in defects:
    issue = next((item for item in existing if item["title"].startswith(defect["id"] + " ")), None)
    details = {
        "title": defect["id"] + " " + defect["title"],
        "body": "Я зарегистрировал и исправил дефект.\n\nПричина: "
        + defect["cause"]
        + "\n\nИсправление: "
        + defect["fix"]
        + "\n\nПроверка: "
        + defect["evidence"],
    }
    if issue is None:
        issue = api("POST", REPO + "/issues", json=details)
    elif issue["title"] != details["title"] or issue["body"] != details["body"]:
        issue = api("PATCH", REPO + f"/issues/{issue['number']}", json=details)
    if issue["state"] != "closed":
        api("PATCH", REPO + f"/issues/{issue['number']}", json={"state": "closed"})
    defect.update(issue=issue["number"], url=issue["html_url"], category="defect")
(ROOT / "docs/evidence/defects.json").write_text(
    json.dumps(
        {"recorded_at": datetime.now(UTC).isoformat(), "defects": defects},
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
print(f"Recorded {len(defects)} observed defects")
