"""Record actual GitHub protection and local commit-message rejections."""

import argparse
import json
import os
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from forge import REPO, ROOT, api, git


def prove(pull_number):
    protection = api("GET", REPO + "/branches/main/protection")
    assert protection["enforce_admins"]["enabled"]
    assert protection["required_pull_request_reviews"] is not None
    assert "quality" in protection["required_status_checks"]["contexts"]
    pull = api("GET", REPO + f"/pulls/{pull_number}")
    assert pull["state"] == "open"
    checks = api("GET", REPO + f"/commits/{pull['head']['sha']}/check-runs")["check_runs"]
    assert any(c["name"] == "quality" and c["conclusion"] == "failure" for c in checks)
    proof = {
        "recorded_at": datetime.now(UTC).isoformat(),
        "repository": "DanilaSm08/Creditsoft",
        "pull_request": pull_number,
        "head": pull["head"]["sha"],
        "checks": checks,
    }
    with tempfile.TemporaryDirectory(dir=ROOT / ".local") as temporary:
        message = Path(temporary) / "message.txt"
        message.write_text("invalid message\n", encoding="utf-8")
        invalid = subprocess.run(
            [
                str(ROOT / ".venv/Scripts/python.exe"),
                str(ROOT / "tools/commit_message.py"),
                str(message),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert invalid.returncode != 0
    proof["invalid_commit"] = {
        "returncode": invalid.returncode,
        "output": invalid.stdout + invalid.stderr,
    }
    before = api("GET", REPO + "/branches/main")["commit"]["sha"]
    git("fetch", "origin", "main")
    tree = subprocess.check_output(
        ["git", "show", "-s", "--format=%T", before], cwd=ROOT, encoding="utf-8"
    ).strip()
    environment = dict(
        os.environ,
        GIT_AUTHOR_NAME="DanilaSmolin08",
        GIT_AUTHOR_EMAIL="danila.smolin.875@mail.ru",
        GIT_COMMITTER_NAME="DanilaSmolin08",
        GIT_COMMITTER_EMAIL="danila.smolin.875@mail.ru",
    )
    candidate = (
        subprocess.check_output(
            ["git", "commit-tree", tree, "-p", before],
            input="test: проверил запрет прямой отправки в main\n".encode(),
            cwd=ROOT,
            env=environment,
        )
        .decode()
        .strip()
    )
    try:
        git("push", "origin", candidate + ":main", capture_output=True)
        raise AssertionError("Protected main unexpectedly accepted the direct push")
    except subprocess.CalledProcessError as error:
        output = (error.stdout or "") + (error.stderr or "")
        assert "GH006" in output or "protected" in output.lower() or "GH013" in output
        proof["direct_push"] = {
            "returncode": error.returncode,
            "output": output,
            "head": candidate,
            "main_before": before,
            "fast_forward_candidate": True,
        }
    after = api("GET", REPO + "/branches/main")["commit"]["sha"]
    assert before == after
    proof["direct_push"]["main_after"] = after
    try:
        api("PUT", REPO + f"/pulls/{pull_number}/merge", json={"merge_method": "merge"})
        raise AssertionError("GitHub unexpectedly merged the failing pull request")
    except RuntimeError as error:
        proof["merge_before_checks"] = {"blocked": True, "output": str(error)}
    assert not api("GET", REPO + f"/pulls/{pull_number}")["merged"]
    (ROOT / "docs/evidence/protection-proof.json").write_text(
        json.dumps(proof, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("Verified: invalid subject rejected, direct push rejected, failing PR merge rejected")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pull", type=int, required=True)
    prove(parser.parse_args().pull)


if __name__ == "__main__":
    main()
