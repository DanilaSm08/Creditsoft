"""Attach reproducible packages, reports and verified evidence to local Gitea release."""

import hashlib
import json
import subprocess
import zipfile
from datetime import UTC, datetime

import requests
from forge import BASE, REPO, ROOT, api


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    output = ROOT / "artifacts/reports/release"
    output.mkdir(parents=True, exist_ok=True)
    reports = ROOT / "reports/CreditSoft_Labs_5-8.zip"
    with zipfile.ZipFile(reports, "w", zipfile.ZIP_DEFLATED) as archive:
        for number in range(5, 9):
            for suffix in ["docx", "pdf"]:
                path = ROOT / f"reports/Lab_{number}.{suffix}"
                assert path.exists()
                archive.write(path, path.name)
    source = output / "creditsoft-1.0.0-source.zip"
    subprocess.run(
        ["git", "archive", "--format=zip", "--prefix=CreditSoft/", "-o", str(source), "v1.0.0"],
        cwd=ROOT,
        check=True,
    )
    evidence = output / "creditsoft-1.0.0-evidence.zip"
    with zipfile.ZipFile(evidence, "w", zipfile.ZIP_DEFLATED) as archive:
        for folder in [
            "docs/evidence",
            "artifacts/runs/release",
            "artifacts/runs/postgres-regression",
            "artifacts/runs/prototype-browser",
        ]:
            for path in (ROOT / folder).rglob("*"):
                if path.is_file():
                    archive.write(path, str(path.relative_to(ROOT)).replace("\\", "/"))
        for name in ["ci-evidence.zip", "ci-run-10.log"]:
            path = ROOT / "artifacts/reports" / name
            if path.exists():
                archive.write(path, name)
    assets = [reports, source, evidence, *sorted((ROOT / "artifacts/runs/release/dist").glob("*"))]
    sums = output / "SHA256SUMS.txt"
    sums.write_text(
        "\n".join(f"{digest(path)}  {path.name}" for path in assets) + "\n", encoding="utf-8"
    )
    assets.append(sums)
    release = api("GET", REPO + "/releases/tags/v1.0.0")
    password = (ROOT / ".local/gitea_password").read_text().strip()
    existing = {
        asset["name"]: asset for asset in api("GET", REPO + f"/releases/{release['id']}/assets")
    }
    uploaded = []
    for path in assets:
        if path.name in existing:
            api("DELETE", REPO + f"/releases/{release['id']}/assets/{existing[path.name]['id']}")
        with path.open("rb") as handle:
            response = requests.post(
                BASE + REPO + f"/releases/{release['id']}/assets",
                params={"name": path.name},
                auth=("student", password),
                files={"attachment": (path.name, handle)},
                timeout=120,
            )
        response.raise_for_status()
        asset = response.json()
        downloaded = requests.get(
            asset["browser_download_url"], auth=("student", password), timeout=120
        )
        downloaded.raise_for_status()
        assert hashlib.sha256(downloaded.content).hexdigest() == digest(path)
        uploaded.append(
            {
                "name": path.name,
                "size": path.stat().st_size,
                "sha256": digest(path),
                "url": asset["browser_download_url"],
            }
        )
    manifest = {
        "recorded_at": datetime.now(UTC).isoformat(),
        "release": release["html_url"],
        "tag_commit": subprocess.check_output(
            ["git", "rev-list", "-n", "1", "v1.0.0"], cwd=ROOT, text=True
        ).strip(),
        "assets": uploaded,
        "download_checksum_verified": True,
    }
    (output / "publication.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Uploaded and downloaded for checksum verification: {len(uploaded)} release assets")


if __name__ == "__main__":
    main()
