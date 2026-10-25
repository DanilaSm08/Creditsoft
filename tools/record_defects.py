"""Register observed setup defects retrospectively; never invent discovery dates."""

import json
from datetime import UTC, datetime

from forge import REPO, ROOT, api

defects = [
    {
        "id": "BUG-01",
        "title": "CI не загружает артефакты по loopback-адресу Gitea",
        "cause": "URL localhost:3030 относится к контейнеру задания, а не к серверу Gitea.",
        "fix": "tools/ci_local_proxy.py отображает адрес внутри изолированного контейнера; последующие запуски CI сохранили артефакты.",
        "evidence": "docs/evidence/ci-first-run.log; Gitea Actions runs 2–4",
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
existing = api("GET", REPO + "/issues?state=all&type=issues&limit=100")
for defect in defects:
    issue = next((item for item in existing if item["title"].startswith(defect["id"] + " ")), None)
    if issue is None:
        issue = api(
            "POST",
            REPO + "/issues",
            json={
                "title": defect["id"] + " " + defect["title"],
                "body": "Зарегистрировано после исправления по сохранённым журналам; время создания карточки не является временем обнаружения.\n\nПричина: "
                + defect["cause"]
                + "\n\nИсправление: "
                + defect["fix"]
                + "\n\nПроверка: "
                + defect["evidence"],
            },
        )
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
