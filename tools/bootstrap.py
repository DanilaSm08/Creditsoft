"""Create local secrets, never commit them to Git."""

import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
local = ROOT / ".local"
local.mkdir(exist_ok=True)
for name in ("django_secret", "postgres_password"):
    path = local / name
    if not path.exists():
        path.write_text(secrets.token_urlsafe(40), encoding="utf-8")
        path.chmod(0o600)
print("Local configuration ready in .local (excluded from Git).")
