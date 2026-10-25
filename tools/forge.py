"""Manage the local educational Git host; credentials stay in .local."""

import argparse
import base64
import json
import os
import subprocess
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
BASE = "http://localhost:3030/api/v1"
REPO = "/repos/student/CreditSoft"
DOCKER = r"C:\Program Files\Docker\Docker\resources\bin\docker.exe"


def api(method, path, **kwargs):
    password = (ROOT / ".local/gitea_password").read_text().strip()
    response = requests.request(
        method, BASE + path, auth=("student", password), timeout=60, **kwargs
    )
    if not response.ok:
        raise RuntimeError(f"Gitea {method} {path}: {response.status_code}: {response.text[:400]}")
    return response.json() if response.content else None


def git(*arguments):
    password = (ROOT / ".local/gitea_password").read_text().strip()
    header = base64.b64encode(f"student:{password}".encode()).decode()
    environment = dict(
        os.environ,
        GIT_CONFIG_COUNT="1",
        GIT_CONFIG_KEY_0="http.http://localhost:3030/.extraHeader",
        GIT_CONFIG_VALUE_0=f"Authorization: Basic {header}",
        GIT_TERMINAL_PROMPT="0",
    )
    subprocess.run(["git", *arguments], cwd=ROOT, env=environment, check=True)


def initialize():
    password = (ROOT / ".local/gitea_password").read_text().strip()
    command = [
        DOCKER,
        "compose",
        "-f",
        "infra/forge.compose.yaml",
        "exec",
        "-T",
        "-u",
        "git",
        "gitea",
        "gitea",
        "--config",
        "/data/gitea/conf/app.ini",
        "admin",
        "user",
        "create",
        "--username",
        "student",
        "--email",
        "student@creditsoft.local",
        "--password",
        password,
        "--admin",
        "--must-change-password=false",
    ]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if result.returncode and "already exists" not in result.stdout + result.stderr:
        raise RuntimeError("Local forge administrator creation failed")
    repositories = api("GET", "/user/repos")
    if not any(repo["name"] == "CreditSoft" for repo in repositories):
        api(
            "POST",
            "/user/repos",
            json={
                "name": "CreditSoft",
                "description": "КПО: учебная оценка кредитоспособности",
                "private": False,
                "default_branch": "main",
            },
        )
    api("PATCH", REPO, json={"has_actions": True, "has_issues": True, "has_pull_requests": True})
    remotes = subprocess.check_output(["git", "remote"], cwd=ROOT, text=True).split()
    if "origin" not in remotes:
        subprocess.run(
            ["git", "remote", "add", "origin", "http://localhost:3030/student/CreditSoft.git"],
            cwd=ROOT,
            check=True,
        )
    token = (
        subprocess.check_output(
            [
                DOCKER,
                "compose",
                "-f",
                "infra/forge.compose.yaml",
                "exec",
                "-T",
                "-u",
                "git",
                "gitea",
                "gitea",
                "--config",
                "/data/gitea/conf/app.ini",
                "actions",
                "generate-runner-token",
            ],
            cwd=ROOT,
            text=True,
        )
        .strip()
        .splitlines()[-1]
    )
    (ROOT / ".local/runner_token").write_text(token)
    print("Local repository ready: http://localhost:3030/student/CreditSoft")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action", choices=["init", "push", "pr", "protect", "export", "merge", "release"]
    )
    parser.add_argument("arguments", nargs="*")
    args = parser.parse_args()
    if args.action == "init":
        initialize()
    elif args.action == "push":
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
        print(
            json.dumps(
                {key: result[key] for key in ["number", "html_url", "head"]}, ensure_ascii=False
            )
        )
    elif args.action == "protect":
        result = api(
            "POST",
            REPO + "/branch_protections",
            json={
                "branch_name": "main",
                "rule_name": "main",
                "enable_push": False,
                "enable_status_check": True,
                "status_check_contexts": ["CreditSoft CI / quality (pull_request)"],
                "required_approvals": 0,
                "block_on_rejected_reviews": True,
                "block_on_outdated_branch": True,
                "enable_force_push": False,
                "block_admin_merge_override": True,
            },
        )
        print(json.dumps(result, ensure_ascii=False))
    elif args.action == "merge":
        api(
            "POST",
            REPO + f"/pulls/{args.arguments[0]}/merge",
            json={"Do": "merge", "delete_branch_after_merge": False},
        )
        print("Pull request merged")
    elif args.action == "release":
        result = api(
            "POST",
            REPO + "/releases",
            json={
                "tag_name": args.arguments[0],
                "target_commitish": "main",
                "name": args.arguments[0],
                "body": Path(args.arguments[1]).read_text(encoding="utf-8"),
                "draft": False,
                "prerelease": args.arguments[0] != "v1.0.0",
            },
        )
        print(result["html_url"])
    else:
        data = {
            "repository": api("GET", REPO),
            "branches": api("GET", REPO + "/branches"),
            "protections": api("GET", REPO + "/branch_protections"),
            "pulls": api("GET", REPO + "/pulls?state=all&limit=100"),
            "issues": api("GET", REPO + "/issues?state=all&limit=100&type=issues"),
            "releases": api("GET", REPO + "/releases"),
            "runs": api("GET", REPO + "/actions/tasks?limit=100"),
        }
        path = ROOT / "docs/evidence/forge-export.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()
