"""Gemensamt för inläsningen: datamapp, nedladdning och manifest.

Rådata ligger aldrig i repot. Mappen styrs av miljövariabeln
BI_JOBB_DATA_DIR (standard: C:/data/bi-jobbmarknaden), så att flera
gigabyte annonser inte hamnar i en mapp som synkas.
"""
from __future__ import annotations

import csv
import hashlib
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(os.environ.get("BI_JOBB_DATA_DIR", "C:/data/bi-jobbmarknaden"))
LANDING = DATA_DIR / "landing"
MANIFEST = LANDING / "manifest.csv"
MANIFEST_FIELDS = ["source", "mode", "url", "file", "downloaded_at", "bytes", "sha256"]
USER_AGENT = "sweden-bi-job-market/1.0 (portfolio project)"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def remote_size(url: str) -> int | None:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        n = r.headers.get("Content-Length")
        return int(n) if n else None


def download(url: str, dest: Path) -> bool:
    """Hämtar url till dest. Returnerar False om filen redan finns komplett."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    expected = remote_size(url)
    if dest.exists() and expected is not None and dest.stat().st_size == expected:
        return False
    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    if expected is not None and tmp.stat().st_size != expected:
        raise IOError(f"{url}: fick {tmp.stat().st_size} byte, väntade {expected}")
    tmp.replace(dest)
    return True


def read_manifest() -> list[dict]:
    if not MANIFEST.exists():
        return []
    with open(MANIFEST, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def record(source: str, mode: str, url: str, path: Path) -> None:
    """Skriver eller ersätter filens rad i manifestet."""
    rows = [r for r in read_manifest() if r["file"] != path.relative_to(LANDING).as_posix()]
    rows.append({
        "source": source,
        "mode": mode,
        "url": url,
        "file": path.relative_to(LANDING).as_posix(),
        "downloaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    })
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: r["file"]))
