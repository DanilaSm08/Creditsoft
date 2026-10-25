"""Local development server. Docker Compose is the release deployment."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "creditsoft.settings")
os.environ.setdefault("DJANGO_SECRET_KEY_FILE", str(ROOT / ".local/django_secret"))
os.environ.setdefault("DJANGO_DEBUG", "1")

if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    execute_from_command_line(["manage.py", "runserver", "127.0.0.1:8000", "--noreload"])
