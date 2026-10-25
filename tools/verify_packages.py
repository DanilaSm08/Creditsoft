"""Verify the downloaded CI archive and installed wheel package resources."""

import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    wheel = next((ROOT / "artifacts/runs/release/dist").glob("*.whl"))
    target = ROOT / "artifacts/reports/installed-wheel"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--upgrade",
            "--target",
            str(target),
            str(wheel),
        ],
        check=True,
        capture_output=True,
    )
    environment = dict(
        os.environ,
        PYTHONPATH=str(target),
        DJANGO_SECRET_KEY="artifact-check-only",
        DJANGO_SETTINGS_MODULE="creditsoft.settings",
    )
    code = "import django; django.setup(); from django.template.loader import get_template; from django.contrib.staticfiles.finders import find; import core; assert 'installed-wheel' in core.__file__; get_template('core/results.html'); assert find('core/app.css'); print('installed wheel templates/static OK')"
    result = subprocess.check_output(
        [sys.executable, "-c", code], cwd=target, env=environment, text=True
    )
    archive = ROOT / "artifacts/reports/ci-evidence.zip"
    with zipfile.ZipFile(archive) as packed:
        assert packed.testzip() is None
        names = packed.namelist()
        assert all(
            name in names for name in ["metrics.json", "junit.xml", "tests.html", "coverage.json"]
        )
        metrics = json.loads(packed.read("metrics.json"))
        assert metrics["passed"] and metrics["tests"]["passed"] == 91
    evidence = {
        "wheel": wheel.name,
        "installed_resource_check": result.strip(),
        "ci_archive_valid": True,
        "ci_metrics": metrics,
    }
    (ROOT / "docs/evidence/package-validation.json").write_text(
        json.dumps(evidence, indent=2), encoding="utf-8"
    )
    print(result.strip(), "; CI ZIP valid, 91 tests passed")


if __name__ == "__main__":
    main()
