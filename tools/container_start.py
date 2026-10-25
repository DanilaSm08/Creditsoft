"""Initialize the single-instance educational deployment and run Gunicorn."""

import os
import subprocess
import sys

for command in [("migrate", "--noinput"), ("collectstatic", "--noinput"), ("seed_catalogue",)]:
    subprocess.run([sys.executable, "manage.py", *command], check=True)
os.execvp(
    "gunicorn",
    [
        "gunicorn",
        "creditsoft.wsgi:application",
        "--bind",
        "0.0.0.0:8000",
        "--workers",
        "2",
        "--timeout",
        "30",
        "--access-logfile",
        "-",
        "--error-logfile",
        "-",
    ],
)
