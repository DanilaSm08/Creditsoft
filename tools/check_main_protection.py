"""Probe a fast-forward push to protected main and record the server rejection."""

import json
import subprocess
import sys

from forge import REPO, ROOT, api


def main():
    before = api("GET", REPO + "/branches/main")["commit"]["id"]
    subprocess.run(["git", "merge-base", "--is-ancestor", before, "HEAD"], cwd=ROOT, check=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert head != before, "Probe requires a new descendant commit"
    result = subprocess.run(
        [sys.executable, "tools/forge.py", "push", "origin", "HEAD:main"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    output = result.stdout + result.stderr
    assert result.returncode != 0 and "protected" in output.lower(), output
    after = api("GET", REPO + "/branches/main")["commit"]["id"]
    assert before == after
    path = ROOT / "docs/evidence/protection-proof.json"
    proof = json.loads(path.read_text(encoding="utf-8"))
    proof["direct_push"] = {
        "returncode": result.returncode,
        "output": output,
        "main_before": before,
        "main_after": after,
        "head": head,
        "fast_forward_candidate": True,
    }
    path.write_text(json.dumps(proof, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Protected main rejected a fast-forward candidate; main unchanged")


if __name__ == "__main__":
    main()
