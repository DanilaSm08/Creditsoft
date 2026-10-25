"""Capture real repository and test-report pages; never render credential fields."""

import json

import requests
from forge import BASE, REPO, ROOT, api
from playwright.sync_api import sync_playwright


def main():
    folder = ROOT / "docs/images/infrastructure"
    folder.mkdir(parents=True, exist_ok=True)
    password = (ROOT / ".local/gitea_password").read_text().strip()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, locale="ru-RU")
        page.goto("http://localhost:3030/user/login")
        page.locator("#user_name").fill("student")
        page.locator("#password").fill(password)
        page.locator("#password").press("Enter")
        page.wait_for_url(lambda url: "/user/login" not in url)
        paths = {
            "repository": "",
            "actions": "/actions",
            "tasks": "/issues?state=closed",
            "branches": "/settings/branches",
            "merged-prototype": "/pulls/31",
            "blocked-pr": "/pulls/32",
            "releases": "/releases",
        }
        for name, path in paths.items():
            page.goto("http://localhost:3030/student/CreditSoft" + path)
            page.locator("body").wait_for()
            page.screenshot(path=str(folder / f"{name}.png"), full_page=False)
        completed = [
            run
            for run in api("GET", REPO + "/actions/tasks")["workflow_runs"]
            if run["status"] == "success"
        ]
        if completed:
            run = max(completed, key=lambda value: value["run_number"])
            page.goto(run["url"])
            page.screenshot(path=str(folder / "ci-detail.png"), full_page=False)
            link = page.get_by_role("link", name="quality-evidence", exact=True)
            if link.count():
                with page.expect_download() as download:
                    link.click()
                output = ROOT / "artifacts/reports/ci-evidence.zip"
                output.parent.mkdir(parents=True, exist_ok=True)
                download.value.save_as(output)
                (ROOT / "docs/evidence/ci-download.json").write_text(
                    json.dumps(
                        {
                            "run": run["run_number"],
                            "head": run["head_sha"],
                            "artifact": "quality-evidence",
                            "bytes": output.stat().st_size,
                        }
                    ),
                    encoding="utf-8",
                )
        stage = (
            "release"
            if (ROOT / "artifacts/runs/release/tests.html").exists()
            else "postgres-regression"
        )
        for name, relative in {"tests": "tests.html", "coverage": "coverage/index.html"}.items():
            page.goto((ROOT / "artifacts/runs" / stage / relative).as_uri())
            page.screenshot(path=str(folder / f"{name}.png"), full_page=False)
        browser.close()
    artifacts = api("GET", REPO + "/actions/artifacts")
    (ROOT / "docs/evidence/ci-artifacts.json").write_text(
        json.dumps(artifacts, indent=2), encoding="utf-8"
    )
    entries = artifacts.get("artifacts", [])
    if entries:
        artifact = max(entries, key=lambda value: value["id"])
        response = requests.get(
            BASE + REPO + f"/actions/artifacts/{artifact['id']}/zip",
            auth=("student", password),
            timeout=60,
        )
        response.raise_for_status()
        output = ROOT / "artifacts/reports/ci-evidence.zip"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(response.content)
    print(f"Captured {len(paths) + 2} real pages; {len(entries)} CI artifacts listed")


if __name__ == "__main__":
    main()
