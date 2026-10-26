"""Capture actual GitHub pages and locally served test reports."""

import argparse
import json
import zipfile
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

from forge import BASE, REPO, ROOT, WEB, api, request, token
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-ref", default="main")
    args = parser.parse_args()
    folder = ROOT / "docs/images/infrastructure"
    folder.mkdir(parents=True, exist_ok=True)
    runs = api("GET", REPO + "/actions/runs", params={"branch": "main", "per_page": 100})[
        "workflow_runs"
    ]
    completed = [run for run in runs if run["conclusion"] == "success"]
    if not completed:
        raise RuntimeError("A successful GitHub Actions run is required before capture")
    run = max(completed, key=lambda value: value["id"])
    paths = {
        "repository": WEB + "/tree/" + args.repository_ref,
        "actions": WEB + "/actions",
        "tasks": WEB + "/issues?q=is%3Aissue%20is%3Aclosed",
        "merged-prototype": WEB + "/pull/31",
        "blocked-pr": WEB + "/pull/32",
        "releases": WEB + "/releases",
        "ci-detail": run["html_url"],
    }
    handler = partial(SimpleHTTPRequestHandler, directory=str(ROOT / "artifacts/runs"))
    with (
        ThreadingHTTPServer(("127.0.0.1", 0), handler) as report_server,
        sync_playwright() as playwright,
    ):
        Thread(target=report_server.serve_forever, daemon=True).start()
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, locale="ru-RU")
        for name, url in paths.items():
            response = page.goto(url, wait_until="domcontentloaded", timeout=90000)
            if response is None or response.status >= 400:
                raise RuntimeError(f"GitHub page unavailable: {name}")
            page.locator("main").first.wait_for()
            page.evaluate("document.fonts.ready")
            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except PlaywrightTimeoutError:
                pass
            page.wait_for_timeout(1500)
            page.screenshot(path=str(folder / f"{name}.png"), full_page=False)
        # This is a real API response from GitHub, with authorization limited to the API host.
        context = browser.new_context(
            viewport={"width": 1440, "height": 1000},
            extra_http_headers={"Authorization": f"Bearer {token()}"},
        )
        protection = context.new_page()
        response = protection.goto(BASE + REPO + "/branches/main/protection")
        if response is None or response.status != 200:
            raise RuntimeError("Cannot capture the GitHub branch protection API response")
        protection.screenshot(path=str(folder / "branches.png"), full_page=False)
        context.close()
        stage = (
            "release"
            if (ROOT / "artifacts/runs/release/tests.html").exists()
            else "postgres-regression"
        )
        for name, relative in {"tests": "tests.html", "coverage": "coverage/index.html"}.items():
            page.goto(f"http://127.0.0.1:{report_server.server_port}/{stage}/{relative}")
            if name == "tests":
                page.locator("#results-table .results-table-row").first.wait_for()
            page.screenshot(path=str(folder / f"{name}.png"), full_page=False)
        browser.close()
        report_server.shutdown()
    artifacts = api("GET", REPO + f"/actions/runs/{run['id']}/artifacts")
    (ROOT / "docs/evidence/ci-artifacts.json").write_text(
        json.dumps(artifacts, indent=2),
        encoding="utf-8",
    )
    entries = artifacts["artifacts"]
    artifact = next(item for item in entries if item["name"] == "quality-evidence")
    output = ROOT / "artifacts/reports/ci-evidence.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(request("GET", artifact["archive_download_url"]).content)
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        metrics_name = next(name for name in archive.namelist() if name.endswith("metrics.json"))
        (ROOT / "docs/evidence/metrics/github-ci.json").write_bytes(archive.read(metrics_name))
    (output.parent / "github-ci-logs.zip").write_bytes(
        request("GET", REPO + f"/actions/runs/{run['id']}/logs").content,
    )
    (ROOT / "docs/evidence/ci-download.json").write_text(
        json.dumps(
            {
                "run": run["run_number"],
                "run_id": run["id"],
                "head": run["head_sha"],
                "url": run["html_url"],
                "artifact": "quality-evidence",
                "bytes": output.stat().st_size,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Captured {len(paths) + 2} pages and downloaded GitHub CI evidence")


if __name__ == "__main__":
    main()
