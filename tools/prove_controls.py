"""Record real server/hook rejections without weakening repository protection."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from forge import REPO, ROOT, api

os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

parser = argparse.ArgumentParser()
parser.add_argument("--pull", type=int, required=True)
args = parser.parse_args()
pull = api("GET", REPO + f"/pulls/{args.pull}")
statuses = api("GET", REPO + f"/commits/{pull['head']['sha']}/status")
if pull["state"] != "open" or not any(
    item["status"] in ("failure", "error") for item in statuses["statuses"]
):
    raise SystemExit("Use an OPEN probe PR with an actual failing CI status; no merge attempted.")
proof = {"pull_request": args.pull, "head": pull["head"]["sha"], "statuses": statuses["statuses"]}
invalid = subprocess.run(
    ["git", "commit", "--allow-empty", "-m", "invalid message"],
    cwd=ROOT,
    capture_output=True,
    text=True,
    encoding="utf-8",
)
proof["invalid_commit"] = {
    "returncode": invalid.returncode,
    "output": invalid.stdout + invalid.stderr,
}
push = subprocess.run(
    [sys.executable, "tools/forge.py", "push", "origin", "HEAD:main"],
    cwd=ROOT,
    capture_output=True,
    text=True,
    encoding="utf-8",
)
proof["direct_push"] = {"returncode": push.returncode, "output": push.stdout + push.stderr}
try:
    api("POST", REPO + f"/pulls/{args.pull}/merge", json={"Do": "merge"})
    proof["merge_before_checks"] = {"blocked": False}
except RuntimeError as error:
    proof["merge_before_checks"] = {"blocked": True, "output": str(error)}
Path("docs/evidence/protection-proof.json").write_text(
    json.dumps(proof, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(
    json.dumps(
        {
            "invalid_commit_rejected": invalid.returncode != 0,
            "direct_push_rejected": push.returncode != 0,
            "merge_blocked": proof["merge_before_checks"]["blocked"],
        }
    )
)
