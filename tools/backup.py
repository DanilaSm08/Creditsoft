"""Explicit backup/restore of the local Compose database without shell redirection."""

import argparse
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from forge import DOCKER, ROOT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["backup", "restore"])
    parser.add_argument("path", nargs="?")
    parser.add_argument("--replace-database", action="store_true")
    args = parser.parse_args()
    command = [DOCKER, "compose", "exec", "-T", "postgres"]
    if args.action == "backup":
        folder = ROOT / ".local/backups"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / (datetime.now(UTC).strftime("creditsoft-%Y%m%dT%H%M%SZ") + ".dump")
        data = subprocess.check_output(
            [*command, "pg_dump", "-U", "creditsoft", "-d", "creditsoft", "-Fc"], cwd=ROOT
        )
        path.write_bytes(data)
        listing = subprocess.run(
            [*command, "pg_restore", "--list"],
            input=data,
            capture_output=True,
            cwd=ROOT,
            check=True,
        )
        (path.with_suffix(".txt")).write_bytes(listing.stdout)
        print(f"Backup verified: {path.name}, {len(data)} bytes")
    else:
        if not args.replace_database or not args.path:
            parser.error("restore requires a dump path and --replace-database")
        subprocess.run(
            [
                *command,
                "pg_restore",
                "-U",
                "creditsoft",
                "-d",
                "creditsoft",
                "--clean",
                "--if-exists",
                "--exit-on-error",
            ],
            input=Path(args.path).read_bytes(),
            cwd=ROOT,
            check=True,
        )


if __name__ == "__main__":
    main()
