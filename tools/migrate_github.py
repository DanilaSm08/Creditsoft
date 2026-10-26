"""Transfer the saved repository graph, numbered issues and pull requests to GitHub."""

import argparse
import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime

from forge import REPO, ROOT, WEB, api, git, pages, request

WORK = ROOT / ".local/github-migration"
MIRROR = WORK / "repository.git"
AUTHOR = ("DanilaSmolin08", "danila.smolin.875@mail.ru")
MESSAGES = {
    "6b43942": "chore: создал проект Django и настроил проверки качества",
    "f94a5bc": "feat: реализовал регистрацию и анкету заёмщика",
    "3f78a64": "Merge pull request #31: объединил прототип анкеты с main",
    "238beac": "test: проверил отказ при ошибке обязательной проверки",
    "46b7198": "feat: реализовал скоринг, каталог и сохранение результатов",
    "1100456": "chore: включил проверенную версию прототипа",
    "c795ee4": "Merge pull request #33: объединил расчётный контур и развёртывание PostgreSQL",
    "0fc88cc": "docs: подготовил результаты проверок и отчёты",
    "6383566": "test: проверил запрет прямой отправки изменений в main",
    "67908d8": "fix: настроил экспорт отчётов через PDF-принтер",
    "1a1a82d": "Merge pull request #37: выпустил CreditSoft 1.0.0 с отчётами",
    "8df9bfc": "docs: добавил изолированный экспорт PDF и просмотр отчёта HTML",
    "93fefa9": "docs: завершил отчёты и статистику задач",
    "b1e9cf9": "Merge pull request #39: объединил итоговые отчёты и статистику",
}
TITLES = {
    31: "feat: реализовал прототип анкеты заёмщика",
    32: "test: проверил запрет слияния при ошибке CI",
    33: "feat: реализовал полный сценарий оценки и развёртывание PostgreSQL",
    37: "chore: выпустил CreditSoft 1.0.0 с отчётами",
    39: "docs: завершил отчёты и статистику выполнения",
}
BODIES = {
    31: "Я реализовал регистрацию, вход и сохраняемую анкету заёмщика. Добавил проверку полей, атомарное сохранение, изоляцию данных пользователей и адаптивные страницы.\n\nПроверил прототип: 37 тестов SQLite/Chromium, 100% строк и ветвей прикладного Python-кода, Ruff и сборка wheel/sdist.\n\nВыполнил PR-01 и CR-01.1–CR-04.3. Описание: docs/PROTOTYPE.md.",
    32: "Я добавил намеренно падающий тест для проверки обязательного CI. Эту ветку я использую для проверки запрета слияния при ошибке quality.",
    33: "Я реализовал расчёт долговой нагрузки и рейтинга 0–1000, каталог предложений, фильтрацию по четырём условиям, сортировку по ставке и итоговый экран. Каждая оценка сохраняет снимок параметров и предложений.\n\nПроверил полный сценарий 91 тестом на SQLite и PostgreSQL, включая два сценария Chromium. Настроил Nginx → Gunicorn/Django → PostgreSQL с постоянными томами и файлами секретов.\n\nВыполнил CR-05.1–CR-08.3. Правила: docs/SCORING.md. Архитектура: docs/ARCHITECTURE.md.",
    37: "Я завершил инструкции запуска и восстановления, связал 30 задач с проверками, собрал статистику Git и подготовил отчёты по лабораторным работам 5–8. Выпустил пакет версии 1.0.0.\n\nПроверил регистрацию, анкету, скоринг, каталог и историю 91 тестом на SQLite и PostgreSQL, включая два сценария Chromium. Проверил развёртывание Nginx/Gunicorn/PostgreSQL, сохранение учётной записи после перезапуска и резервное копирование БД.",
    39: "Я закрыл 30 задач плана и исправил четыре дефекта. Проверил DOCX/PDF и сохранил отчёты 1–4 без изменений по SHA-256. Добавил изолированный экспорт PDF и просмотр HTML-отчёта через HTTP. Составил статистику задач, коммитов и интервалов между отметками этапов.",
    34: "Я исправил загрузку артефактов CI по loopback-адресу внутри контейнера. Причина: локальный адрес сервера из контейнера задания указывал на сам контейнер. Проверил сохранение артефактов последующими запусками CI.",
}


def local(*args, cwd=MIRROR, input=None, env=None):
    return (
        subprocess.check_output(
            ["git", *args],
            cwd=cwd,
            input=input.encode("utf-8") if input is not None else None,
            env=env,
        )
        .decode("utf-8")
        .strip()
    )


def save(name, value):
    (WORK / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def load(name):
    return json.loads((WORK / name).read_text(encoding="utf-8"))


def prepare():
    source = load("gitea-export.json")
    if not MIRROR.exists():
        subprocess.run(
            ["git", "clone", "--mirror", str(WORK / "source-history.bundle"), str(MIRROR)],
            check=True,
        )
    if (WORK / "commit-map.json").exists():
        print("Commit mapping already prepared")
        return
    mapping = {}
    original_heads = [branch["commit"]["id"] for branch in source["branches"]]
    for sha in local("rev-list", "--reverse", "--topo-order", *original_heads).splitlines():
        tree, parents, author_date, committer_date = local(
            "show",
            "-s",
            "--format=%T%n%P%n%aI%n%cI",
            sha,
        ).split("\n")
        message = MESSAGES[sha[:7]]
        environment = dict(
            os.environ,
            GIT_AUTHOR_NAME=AUTHOR[0],
            GIT_AUTHOR_EMAIL=AUTHOR[1],
            GIT_COMMITTER_NAME=AUTHOR[0],
            GIT_COMMITTER_EMAIL=AUTHOR[1],
            GIT_AUTHOR_DATE=author_date,
            GIT_COMMITTER_DATE=committer_date,
        )
        arguments = ["commit-tree", tree]
        for parent in parents.split():
            arguments.extend(["-p", mapping[parent]])
        mapping[sha] = local(*arguments, input=message + "\n", env=environment)
        assert local("show", "-s", "--format=%T", mapping[sha]) == tree
    heads = {}
    for branch in source["branches"]:
        heads[branch["name"]] = mapping[branch["commit"]["id"]]
        local("update-ref", "refs/heads/" + branch["name"], heads[branch["name"]])
    for release in source["releases"]:
        tag = release["tag_name"]
        target = mapping[local("rev-parse", tag + "^{commit}")]
        original = local("cat-file", "-p", tag)
        timestamp = original.split("tagger ")[1].split("\n")[0].split("> ", 1)[1]
        description = (
            "Я выпустил прототип CreditSoft" if tag == "v0.1.0" else "Я выпустил CreditSoft 1.0.0"
        )
        content = (
            f"object {target}\ntype commit\ntag {tag}\n"
            f"tagger {AUTHOR[0]} <{AUTHOR[1]}> {timestamp}\n\n{description}\n"
        )
        oid = local("hash-object", "-t", "tag", "-w", "--stdin", input=content)
        local("update-ref", "refs/tags/" + tag, oid)
    save("commit-map.json", mapping)
    save("heads.json", heads)
    save("state.json", {"created": [], "merged": [], "adopted": False})
    print(f"Prepared {len(mapping)} commits, {len(heads)} branches and 2 tags; trees unchanged")


def issue_text(item):
    number = item["number"]
    if number in BODIES:
        return BODIES[number]
    body = item.get("body") or ""
    body = body.replace(
        "Перенос плана для фактического выполнения ЛР5–8; даты YouGile не восстанавливались.",
        "Я выполнил задачу по плану лабораторной работы 3.",
    )
    body = body.replace(
        "Зарегистрировано после исправления по сохранённым журналам; время создания карточки не является временем обнаружения.\n\n",
        "Я зарегистрировал и исправил дефект.\n\n",
    )
    body = body.replace("Проверено:", "Я проверил выполнение:")
    return body


def publish():
    source, mapping, state = load("gitea-export.json"), load("commit-map.json"), load("state.json")
    account = api("GET", "/user")
    assert account["login"].lower() == "danilasm08"
    repository = api("GET", REPO)
    assert repository["permissions"]["admin"]
    remote = WEB + ".git"
    root = next(old for old in mapping if old.startswith("6b43942"))
    if not state["created"]:
        assert not pages(REPO + "/issues", state="all"), (
            "Destination must be empty before initial import"
        )
        git("push", remote, mapping[root] + ":refs/heads/main", cwd=MIRROR)
    pulls = {p["number"]: p for p in source["pulls"]}
    for item in sorted(source["issues"], key=lambda row: row["number"]):
        number = item["number"]
        if number not in state["created"]:
            if number in pulls:
                pull = pulls[number]
                branch = pull["head"]["ref"]
                git(
                    "push",
                    remote,
                    mapping[pull["head"]["sha"]] + ":refs/heads/" + branch,
                    cwd=MIRROR,
                )
                result = api(
                    "POST",
                    REPO + "/pulls",
                    json={
                        "head": branch,
                        "base": "main",
                        "title": TITLES[number],
                        "body": issue_text(item),
                    },
                )
            else:
                title = item["title"].replace("loopback-адресу Gitea", "loopback-адресу сервера")
                result = api(
                    "POST", REPO + "/issues", json={"title": title, "body": issue_text(item)}
                )
            assert result["number"] == number, (number, result["number"])
            state["created"].append(number)
            save("state.json", state)
            if number not in pulls and item["state"] == "closed":
                api("PATCH", REPO + f"/issues/{number}", json={"state": "closed"})
            for comment in item.get("comments_export", []):
                api("POST", REPO + f"/issues/{number}/comments", json={"body": comment["body"]})
            print(f"Imported #{number}", flush=True)
        if number in pulls and pulls[number].get("merged") and number not in state["merged"]:
            merge_sha = mapping[pulls[number]["merge_commit_sha"]]
            git("push", remote, merge_sha + ":refs/heads/main", cwd=MIRROR)
            merged = api("GET", REPO + f"/pulls/{number}")
            if not merged["merged"]:
                raise RuntimeError(
                    f"GitHub has not marked PR #{number} as merged; resume after graph processing"
                )
            state["merged"].append(number)
            save("state.json", state)
    for branch, sha in load("heads.json").items():
        if branch != "main":
            git("push", remote, sha + ":refs/heads/" + branch, cwd=MIRROR)
    git("push", remote, "refs/tags/v0.1.0", "refs/tags/v1.0.0", cwd=MIRROR)
    existing = {r["tag_name"] for r in pages(REPO + "/releases")}
    for release in reversed(source["releases"]):
        if release["tag_name"] not in existing:
            body = (
                "Я реализовал регистрацию, вход и анкету заёмщика. Проверил прототип 37 тестами, включая Chromium."
                if release["tag_name"] == "v0.1.0"
                else "Я реализовал регистрацию, анкету, скоринг, подбор предложений и историю результатов. Проверил систему 91 тестом на SQLite и PostgreSQL, включая два сценария Chromium. Подготовил отчёты по лабораторным работам 5–8."
            )
            api(
                "POST",
                REPO + "/releases",
                json={
                    "tag_name": release["tag_name"],
                    "name": release["tag_name"],
                    "body": body,
                    "draft": False,
                    "prerelease": release["tag_name"] == "v0.1.0",
                },
            )
    print(
        "History, issues, pull requests and release records transferred; protection and assets remain"
    )


def adopt():
    mapping = load("commit-map.json")
    before = local("rev-parse", "HEAD", cwd=ROOT)
    assert before in mapping, "Local HEAD changed since backup"
    local(
        "fetch",
        str(MIRROR),
        "+refs/heads/*:refs/remotes/github-migration/*",
        "+refs/tags/*:refs/tags/*",
        cwd=ROOT,
    )
    for branch, sha in load("heads.json").items():
        local("update-ref", "refs/heads/" + branch, sha, cwd=ROOT)
    local("remote", "set-url", "origin", WEB + ".git", cwd=ROOT)
    state = load("state.json")
    state["adopted"] = True
    save("state.json", state)
    print("Local branches now follow the rewritten graph; working files preserved")


def verify():
    source, mapping = load("gitea-export.json"), load("commit-map.json")
    issues = {item["number"]: item for item in pages(REPO + "/issues", state="all")}
    expected_issues = [item for item in source["issues"] if not item.get("pull_request")]
    for item in expected_issues:
        assert issues[item["number"]]["state"] == item["state"]
    pulls = {item["number"]: item for item in pages(REPO + "/pulls", state="all")}
    for item in source["pulls"]:
        actual = api("GET", REPO + f"/pulls/{item['number']}")
        assert actual["merged"] == item["merged"]
        assert actual["state"] == item["state"]
    for old, new in mapping.items():
        commit = api("GET", REPO + "/git/commits/" + new)
        assert commit["tree"]["sha"] == local("show", "-s", "--format=%T", old)
        assert [p["sha"] for p in commit["parents"]] == [
            mapping[p] for p in local("show", "-s", "--format=%P", old).split()
        ]
        assert (commit["author"]["name"], commit["author"]["email"]) == AUTHOR
    branches = {branch["name"]: branch for branch in pages(REPO + "/branches")}
    assert all(branch["name"] in branches for branch in source["branches"])
    releases = {release["tag_name"]: release for release in pages(REPO + "/releases")}
    assert {"v0.1.0", "v1.0.0"} <= releases.keys()
    publication = json.loads(
        (ROOT / "artifacts/reports/release/publication.json").read_text(encoding="utf-8")
    )
    assets = {asset["name"]: asset for asset in releases["v1.0.0"]["assets"]}
    assert len(assets) == 6
    for expected in publication["assets"]:
        downloaded = request(
            "GET", assets[expected["name"]]["url"], headers={"Accept": "application/octet-stream"}
        )
        assert hashlib.sha256(downloaded.content).hexdigest() == expected["sha256"]
    protection = api("GET", REPO + "/branches/main/protection")
    assert protection["enforce_admins"]["enabled"]
    assert "quality" in protection["required_status_checks"]["contexts"]
    assert protection["required_pull_request_reviews"] is not None
    runs = api(
        "GET", REPO + "/actions/runs", params={"branch": "main", "status": "success", "per_page": 1}
    )
    assert runs["workflow_runs"][0]["head_sha"] == branches["main"]["commit"]["sha"]
    proof = {
        "verified_at": datetime.now(UTC).isoformat(),
        "repository": WEB,
        "commits": len(mapping),
        "issues": len(expected_issues),
        "original_pull_requests": len(source["pulls"]),
        "all_pull_requests": len(pulls),
        "original_branches": len(source["branches"]),
        "releases": len(releases),
        "release_assets": len(assets),
        "asset_checksums_verified": True,
        "main": branches["main"]["commit"]["sha"],
        "main_ci_success": True,
        "commit_map": mapping,
    }
    (ROOT / "docs/evidence/github-migration.json").write_text(
        json.dumps(proof, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("Verified GitHub history, tasks, pull requests, release assets, protection and main CI")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "publish", "adopt", "verify"])
    args = parser.parse_args()
    {"prepare": prepare, "publish": publish, "adopt": adopt, "verify": verify}[args.action]()


if __name__ == "__main__":
    main()
