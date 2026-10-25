"""Import the baseline from the supplied Lab 3 extraction, without changing dates."""

import json

from forge import REPO, ROOT, api


def main():
    source = json.loads((ROOT.parent / ".codex_tmp/labs5_8/lab_3.json").read_text(encoding="utf-8"))
    table = next(
        block["table"]
        for block in source["blocks"]
        if block.get("table", [[]])[0][:2] == ["№", "ID"]
    )
    existing = api("GET", REPO + "/issues?state=all&limit=100&type=issues")
    records = []
    for row in table[1:]:
        _, identifier, title, priority, hours, depends, sprint = row
        issue = next(
            (item for item in existing if item["title"].startswith(identifier + " ")), None
        )
        if not issue:
            issue = api(
                "POST",
                REPO + "/issues",
                json={
                    "title": f"{identifier} {title}",
                    "body": f"Источник: таблица плана ЛР3.\n\nПлан: {hours} ч. Приоритет: {priority}. Спринт: {sprint}. Зависимости: {depends}.\n\nПеренос плана для фактического выполнения ЛР5–8; даты YouGile не восстанавливались.",
                },
            )
        records.append(
            {
                "id": identifier,
                "title": title,
                "planned_hours": float(hours.replace(",", ".")),
                "priority": priority,
                "dependencies": depends,
                "planned_sprint": int(sprint),
                "category": "original" if identifier.startswith("CR-") else "planned_additional",
                "issue": issue["number"],
                "url": issue["html_url"],
            }
        )
    target = ROOT / "docs/evidence/tasks.json"
    target.write_text(
        json.dumps(
            {"source": source["source"], "source_sha256": source["sha256"], "tasks": records},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        f"Imported {len(records)} tasks, {sum(item['planned_hours'] for item in records)} planned hours"
    )


if __name__ == "__main__":
    main()
