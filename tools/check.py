"""Reproducible quality pipeline and stage metrics."""

import argparse
import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

from radon.complexity import cc_visit
from radon.raw import analyze

ROOT = Path(__file__).resolve().parent.parent


def execute(command, log, environment):
    with log.open("w", encoding="utf-8") as output:
        result = subprocess.run(
            command, cwd=ROOT, env=environment, stdout=output, stderr=subprocess.STDOUT
        )
    if result.returncode:
        print(log.read_text(encoding="utf-8")[-10000:])
    return result.returncode


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", default="working")
    parser.add_argument("--e2e", action="store_true")
    args = parser.parse_args()
    started = time.monotonic()
    output = ROOT / "artifacts" / "runs" / args.stage
    output.mkdir(parents=True, exist_ok=True)
    environment = {**os.environ, "DJANGO_SECRET_KEY": "isolated-test-key-not-a-deployment-secret"}
    environment["SCREENSHOT_DIR"] = str(output / "screenshots")
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["TEST_MAP_PATH"] = str(output / "test-map.json")
    lint = subprocess.run(
        [sys.executable, "-m", "ruff", "check", ".", "--output-format=json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    (output / "lint.json").write_text(lint.stdout, encoding="utf-8")
    formatting = execute(
        [sys.executable, "-m", "ruff", "format", "--check", "."], output / "format.log", environment
    )
    migration_check = execute(
        [sys.executable, "manage.py", "makemigrations", "--check", "--dry-run"],
        output / "migrations.log",
        environment,
    )
    test_command = [
        sys.executable,
        "-m",
        "pytest",
        "--cov=core",
        "--cov-branch",
        f"--cov-report=json:{output / 'coverage.json'}",
        f"--cov-report=html:{output / 'coverage'}",
        f"--cov-report=xml:{output / 'coverage.xml'}",
        f"--junitxml={output / 'junit.xml'}",
        f"--html={output / 'tests.html'}",
        "--self-contained-html",
        "-q",
    ]
    if not args.e2e:
        test_command += ["-m", "not e2e"]
    else:
        test_command += [
            "--tracing=retain-on-failure",
            "--screenshot=only-on-failure",
            f"--output={output / 'browser'}",
        ]
    tests_status = execute(test_command, output / "tests.log", environment)
    passed = not any([lint.returncode, formatting, migration_check, tests_status])
    build_status = (
        execute(
            [sys.executable, "-m", "build", "--outdir", str(output / "dist")],
            output / "build.log",
            environment,
        )
        if passed
        else 1
    )
    coverage_path = output / "coverage.json"
    coverage = json.loads(coverage_path.read_text()) if coverage_path.exists() else {"totals": {}}
    junit_path = output / "junit.xml"
    suites = ET.parse(junit_path).getroot().findall("testsuite") if junit_path.exists() else []
    counts = {
        name: sum(int(s.get(name, 0)) for s in suites)
        for name in ["tests", "errors", "failures", "skipped"]
    }
    counts["passed"] = counts["tests"] - counts["errors"] - counts["failures"] - counts["skipped"]
    code = list((ROOT / "core").rglob("*.py")) + list((ROOT / "creditsoft").glob("*.py"))
    code = [path for path in code if "migrations" not in path.parts]
    complexity = [
        block.complexity for path in code for block in cc_visit(path.read_text(encoding="utf-8"))
    ]
    totals = coverage["totals"]
    git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    metrics = {
        "stage": args.stage,
        "recorded_at": datetime.now(UTC).isoformat(),
        "commit": git.stdout.strip(),
        "passed": passed and build_status == 0,
        "lint_issues": len(json.loads(lint.stdout or "[]")),
        "format_exit": formatting,
        "migration_exit": migration_check,
        "build_exit": build_status,
        "line_coverage_percent": round(
            100 * totals.get("covered_lines", 0) / max(totals.get("num_statements", 0), 1), 2
        ),
        "branch_coverage_percent": round(
            100 * totals.get("covered_branches", 0) / max(totals.get("num_branches", 0), 1), 2
        ),
        "tests": counts,
        "test_duration_seconds": round(sum(float(s.get("time", 0)) for s in suites), 3),
        "mean_complexity": round(sum(complexity) / max(len(complexity), 1), 2),
        "max_complexity": max(complexity, default=0),
        "source_files": len(code),
        "source_lines": sum(analyze(path.read_text(encoding="utf-8")).sloc for path in code),
        "pipeline_seconds": round(time.monotonic() - started, 3),
        "database": "PostgreSQL" if os.getenv("POSTGRES_HOST") else "SQLite",
        "browser_included": args.e2e,
    }
    metrics_dir = ROOT / "docs" / "evidence" / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    (metrics_dir / f"{args.stage}.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    return 0 if metrics["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
