"""Manage CreditSoft through the GitHub REST API and Git CLI."""

import argparse
import base64
import json
import os
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://api.github.com"
REPO = "/repos/DanilaSm08/Creditsoft"
WEB = "https://github.com/DanilaSm08/Creditsoft"
DOCKER = r"C:\Program Files\Docker\Docker\resources\bin\docker.exe"
GH = ROOT / ".local/github-cli/gh.exe"
if not GH.exists():
    GH = shutil.which("gh")


@lru_cache(maxsize=1)
def token():
    if not GH:
        raise RuntimeError("Install the GitHub CLI and run gh auth login")
    environment = dict(os.environ)
    configuration = ROOT / ".local/github-config"
    if (configuration / "hosts.yml").exists():
        environment["GH_CONFIG_DIR"] = str(configuration)
    result = subprocess.run(
        [str(GH), "auth", "token", "--hostname", "github.com"],
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode or not result.stdout.strip():
        raise RuntimeError("GitHub authorization is required; run gh auth login first")
    return result.stdout.strip()


def request(method, path, **kwargs):
    headers = {
        "Authorization": f"Bearer {token()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    headers.update(kwargs.pop("headers", {}))
    url = path if path.startswith("https://") else BASE + path
    response = requests.request(method, url, headers=headers, timeout=120, **kwargs)
    if not response.ok:
        raise RuntimeError(f"GitHub {method} {path}: {response.status_code}: {response.text[:600]}")
    return response


def api(method, path, **kwargs):
    response = request(method, path, **kwargs)
    return response.json() if response.content else None


def pages(path, **params):
    result = []
    number = 1
    while True:
        chunk = api("GET", path, params=dict(params, per_page=100, page=number))
        result.extend(chunk)
        if len(chunk) < 100:
            return result
        number += 1


def git(*arguments, cwd=ROOT, capture_output=False):
    header = base64.b64encode(f"x-access-token:{token()}".encode()).decode()
    environment = dict(
        os.environ,
        GIT_CONFIG_COUNT="2",
        GIT_CONFIG_KEY_0="http.https://github.com/.extraHeader",
        GIT_CONFIG_VALUE_0=f"Authorization: Basic {header}",
        GIT_CONFIG_KEY_1="credential.helper",
        GIT_CONFIG_VALUE_1="",
        GIT_TERMINAL_PROMPT="0",
    )
    return subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        env=environment,
        check=True,
        capture_output=capture_output,
        text=True,
        encoding="utf-8",
    )


def protect():
    return api(
        "PUT",
        REPO + "/branches/main/protection",
        json={
            "required_status_checks": {"strict": True, "contexts": ["quality"]},
            "enforce_admins": True,
            "required_pull_request_reviews": {
                "dismiss_stale_reviews": True,
                "require_code_owner_reviews": False,
                "required_approving_review_count": 0,
            },
            "restrictions": None,
            "allow_force_pushes": False,
            "allow_deletions": False,
        },
    )


def export():
    data = {
        "repository": api("GET", REPO),
        "branches": pages(REPO + "/branches"),
        "protections": api("GET", REPO + "/branches/main/protection"),
        "pulls": pages(REPO + "/pulls", state="all"),
        "issues": [i for i in pages(REPO + "/issues", state="all") if "pull_request" not in i],
        "releases": pages(REPO + "/releases"),
        "runs": api("GET", REPO + "/actions/runs", params={"per_page": 100}),
    }
    path = ROOT / "docs/evidence/github-export.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(path)
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["push", "pr", "protect", "export", "merge", "release"])
    parser.add_argument("arguments", nargs="*")
    args = parser.parse_args()
    if args.action == "push":
        git("push", *args.arguments)
    elif args.action == "pr":
        result = api(
            "POST",
            REPO + "/pulls",
            json={
                "head": args.arguments[0],
                "base": "main",
                "title": args.arguments[1],
                "body": Path(args.arguments[2]).read_text(encoding="utf-8"),
            },
        )
        print(result["html_url"])
    elif args.action == "protect":
        protect()
        print("main: required pull request and quality check; force push and deletion disabled")
    elif args.action == "merge":
        result = api(
            "PUT", REPO + f"/pulls/{args.arguments[0]}/merge", json={"merge_method": "merge"}
        )
        print(result["message"])
    elif args.action == "release":
        result = api(
            "POST",
            REPO + "/releases",
            json={
                "tag_name": args.arguments[0],
                "name": args.arguments[0],
                "body": Path(args.arguments[1]).read_text(encoding="utf-8"),
                "draft": False,
                "prerelease": args.arguments[0] != "v1.0.0",
            },
        )
        print(result["html_url"])
    else:
        export()


if __name__ == "__main__":
    main()
