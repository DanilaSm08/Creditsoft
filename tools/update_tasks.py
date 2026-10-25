"""Close verified local tracker tasks with explicit acceptance evidence."""

import argparse
import json

from forge import REPO, ROOT, api

parser = argparse.ArgumentParser()
parser.add_argument("--evidence", required=True)
parser.add_argument("ids", nargs="+")
args = parser.parse_args()
tasks = json.loads((ROOT / "docs/evidence/tasks.json").read_text(encoding="utf-8"))["tasks"]
for identifier in args.ids:
    task = next(item for item in tasks if item["id"] == identifier)
    issue = api("GET", REPO + f"/issues/{task['issue']}")
    if issue["state"] == "closed":
        continue
    api(
        "PATCH",
        REPO + f"/issues/{task['issue']}",
        json={"state": "closed", "body": issue["body"] + "\n\nПроверено: " + args.evidence},
    )
    print(identifier + " closed")
