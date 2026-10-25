"""Measure actual phase wall time without inventing per-task hours."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL = ROOT / ".local" / "active_phase.json"
LOG = ROOT / "docs" / "evidence" / "worklog.jsonl"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["start", "stop"])
    parser.add_argument("phase", nargs="?")
    parser.add_argument("tasks", nargs="*")
    args = parser.parse_args()
    now = datetime.now(UTC).isoformat()
    if args.action == "start":
        if LOCAL.exists():
            raise SystemExit("A phase is already being measured")
        LOCAL.parent.mkdir(exist_ok=True)
        LOCAL.write_text(
            json.dumps({"phase": args.phase, "tasks": args.tasks, "started_at": now}),
            encoding="utf-8",
        )
    else:
        event = json.loads(LOCAL.read_text(encoding="utf-8"))
        event["finished_at"] = now
        event["elapsed_seconds"] = round(
            (
                datetime.fromisoformat(now) - datetime.fromisoformat(event["started_at"])
            ).total_seconds(),
            2,
        )
        event["method"] = "observed assisted phase wall time; shared tasks are not separately timed"
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event) + "\n")
        LOCAL.unlink()
        print(json.dumps(event))


if __name__ == "__main__":
    main()
