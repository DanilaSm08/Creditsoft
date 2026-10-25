import os

# Playwright sync API owns a session event loop. ORM calls here use isolated test
# databases; requests still run in the separate live_server thread.
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-key-not-used-by-the-running-application")
