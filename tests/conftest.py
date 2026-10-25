import json
import os
from pathlib import Path

# Playwright sync API owns a session event loop. ORM calls here use isolated test
# databases; requests still run in the separate live_server thread.
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"


def pytest_collection_finish(session):
    rows = []
    for item in session.items:
        requirement = item.get_closest_marker("requirement")
        rows.append(
            {
                "test": item.nodeid,
                "requirements": list(requirement.args) if requirement else [],
                "browser": bool(item.get_closest_marker("e2e")),
            }
        )
    destination = Path(os.getenv("TEST_MAP_PATH", "artifacts/test-map.json"))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-key-not-used-by-the-running-application")
