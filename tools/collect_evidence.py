"""Collect GitHub and Git facts, traceability and dated charts for lab reports."""

import csv
import json
import subprocess
from collections import Counter
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from forge import ROOT
from forge import main as forge_main

EVIDENCE = ROOT / "docs/evidence"
IMAGES = ROOT / "docs/images/statistics"


def read(name):
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def save(name, data):
    (EVIDENCE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, encoding="utf-8").strip()


def main():
    import sys

    sys.argv = ["forge.py", "export"]
    forge_main()
    export = read("github-export.json")
    tasks = read("tasks.json")["tasks"]
    issues = {i["number"]: i for i in export["issues"] if not i.get("pull_request")}
    runs = ROOT / "artifacts/runs"
    stage = "release" if (runs / "release/test-map.json").exists() else "postgres-regression"
    tests = json.loads((runs / stage / "test-map.json").read_text(encoding="utf-8"))
    support = {
        "PR-01": ["docs/PROTOTYPE.md", "docs/images/prototype", "v0.1.0"],
        "INF-01": [
            "compose.yaml",
            ".github/workflows/ci.yml",
            "docs/evidence/protection-proof.json",
        ],
        "QA-01": ["docs/TESTING.md", "tests", "artifacts/runs/release/test-map.json"],
        "RL-01": ["Dockerfile", "infra/nginx.conf", "docs/evidence/deployment-smoke.json"],
        "QA-02": [
            "artifacts/runs/postgres-regression",
            "artifacts/runs/release",
            "docs/evidence/defects.json",
        ],
        "RL-02": ["docs/RELEASE.md", "reports", "v1.0.0"],
    }
    acceptance = []
    for task in tasks:
        matching = [test["test"] for test in tests if task["id"] in test["requirements"]]
        assert matching or task["id"] in support, task["id"]
        issue = issues[task["issue"]]
        acceptance.append(
            {
                **task,
                "state": issue["state"],
                "closed_at": issue["closed_at"],
                "tests": matching,
                "artifacts": support.get(task["id"], []),
            }
        )
    save("acceptance.json", acceptance)
    counts = Counter(task["category"] for task in tasks)
    closed = Counter(task["category"] for task in acceptance if task["state"] == "closed")
    defect_data = read("defects.json")
    defect_items = defect_data if isinstance(defect_data, list) else defect_data["defects"]
    commits = []
    for sha in git("rev-list", "--no-merges", "HEAD").splitlines():
        stamp, subject = git("show", "-s", "--format=%aI%n%s", sha).split("\n", 1)
        added = removed = 0
        for row in git("show", "--format=", "--numstat", sha).splitlines():
            a, d, _ = row.split("\t", 2)
            if a.isdigit():
                added += int(a)
                removed += int(d)
        commits.append(
            {"sha": sha, "date": stamp, "subject": subject, "added": added, "removed": removed}
        )
    files = git("ls-files").splitlines()
    extensions = Counter(Path(name).suffix or "(без расширения)" for name in files)
    authored = [
        name
        for name in files
        if Path(name).suffix in {".py", ".html", ".css", ".js", ".yaml", ".yml"}
        and "bootstrap" not in name
        and "/migrations/" not in name
    ]
    volume = {
        "tracked_files": len(files),
        "files_by_extension": dict(extensions),
        "authored_source_files": len(authored),
        "authored_physical_lines": sum(
            len((ROOT / name).read_text(encoding="utf-8").splitlines()) for name in authored
        ),
        "definition": "Tracked .py/.html/.css/.js/.yaml/.yml; excludes vendored Bootstrap and generated migrations; includes tests/tools; physical lines include blanks/comments.",
    }
    start = date(2026, 9, 7)
    today = datetime.now(UTC).date()
    weeks = []
    for index in range(16):
        begin = start + timedelta(weeks=index)
        end = begin + timedelta(days=6)
        sprint = index // 2 + 1
        due = end if index % 2 else end + timedelta(weeks=1)
        planned_remaining = sum(
            t["planned_hours"]
            for t in tasks
            if t["planned_sprint"] > sprint or (t["planned_sprint"] == sprint and end < due)
        )
        closed_week = [
            i
            for i in issues.values()
            if i.get("closed_at") and begin <= date.fromisoformat(i["closed_at"][:10]) <= end
        ]
        remaining = sum(
            t["planned_hours"]
            for t in acceptance
            if not t["closed_at"] or date.fromisoformat(t["closed_at"][:10]) > min(end, today)
        )
        weekly_commits = [c for c in commits if begin <= date.fromisoformat(c["date"][:10]) <= end]
        weeks.append(
            {
                "week": begin.isoformat(),
                "planned_remaining_hours": planned_remaining,
                "actual_remaining_plan_hours": remaining if begin <= today else None,
                "closed_issues": len(closed_week) if begin <= today else None,
                "commits": len(weekly_commits) if begin <= today else None,
                "added_lines": sum(c["added"] for c in weekly_commits) if begin <= today else None,
                "removed_lines": sum(c["removed"] for c in weekly_commits)
                if begin <= today
                else None,
            }
        )
    with (EVIDENCE / "weekly.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=weeks[0].keys())
        writer.writeheader()
        writer.writerows(weeks)
    worklog = [json.loads(line) for line in (EVIDENCE / "worklog.jsonl").read_text().splitlines()]
    active_file = ROOT / ".local/active_phase.json"
    if active_file.exists():
        active = json.loads(active_file.read_text())
        active["elapsed_seconds"] = round(
            (datetime.now(UTC) - datetime.fromisoformat(active["started_at"])).total_seconds(), 2
        )
        active["snapshot_in_progress"] = True
        worklog.append(active)
    save(
        "summary.json",
        {
            "recorded_at": datetime.now(UTC).isoformat(),
            "head": git("rev-parse", "HEAD"),
            "planned_counts": dict(counts),
            "closed_counts": dict(closed),
            "defects": len(defect_items),
            "closed_defects": sum(issues[d["issue"]]["state"] == "closed" for d in defect_items),
            "planned_hours": sum(t["planned_hours"] for t in tasks),
            "volume": volume,
            "commits": commits,
            "weeks": weeks,
            "worklog": worklog,
            "limits": [
                "План задач: Lab_3.docx.",
                "Даты закрытия задач: GitHub API; даты коммитов: Git.",
                "Строки Git включают все зафиксированные текстовые файлы.",
                "Время этапа: интервал между отметками начала и окончания.",
            ],
        },
    )
    IMAGES.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    labels = [row["week"][5:] for row in weeks]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(labels, [w["planned_remaining_hours"] for w in weeks], "o-", label="Исходный план ЛР3")
    ax.plot(
        labels,
        [w["actual_remaining_plan_hours"] for w in weeks],
        "s-",
        label="Остаток оценок по закрытию GitHub",
    )
    ax.set(
        ylabel="Плановые часы незакрытых задач",
        xlabel="Начало недели, 2026",
        title="Burndown: план и фактическое закрытие задач",
    )
    ax.tick_params(axis="x", rotation=45)
    ax.legend()
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(IMAGES / "burndown.png", dpi=180)
    plt.close(fig)
    measured = [w for w in weeks if w["commits"] is not None]
    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    x = [w["week"][5:] for w in measured]
    axes[0].bar(
        x,
        [w["closed_issues"] for w in measured],
        color="#087e8b",
        label="Закрытые карточки, включая дефекты",
    )
    axes[0].bar(
        x, [w["commits"] for w in measured], width=0.35, color="#e7aa40", label="Коммиты без merge"
    )
    axes[0].legend()
    axes[1].bar(x, [w["added_lines"] for w in measured], color="#087e8b", label="Добавлено строк")
    axes[1].bar(x, [-w["removed_lines"] for w in measured], color="#c15c5c", label="Удалено строк")
    axes[1].legend()
    axes[1].set_xlabel("Начало недели, 2026")
    fig.tight_layout()
    fig.savefig(IMAGES / "weekly-activity.png", dpi=180)
    plt.close(fig)
    print(
        f"Mapped {len(acceptance)} tasks; {sum(t['state'] == 'closed' for t in acceptance)}/30 baseline closed"
    )


if __name__ == "__main__":
    main()
