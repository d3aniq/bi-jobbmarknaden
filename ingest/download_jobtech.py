"""Hämtar JobTechs historiska, berikade annonser (CC0) till landing.

    python ingest/download_jobtech.py            # stickprov, 1 % per år (~150 MB)
    python ingest/download_jobtech.py --full     # alla annonser (~10 GB)

Filerna sparas oförändrade. Varje fil registreras i manifestet med URL,
tid, storlek och SHA-256. Avbruten hämtning kan köras om; kompletta
filer hoppas över.
"""
from __future__ import annotations

import argparse
import sys

from common import LANDING, download, record

BASE = "https://data.jobtechdev.se/annonser/historiska/berikade"
PERIODS = [str(y) for y in range(2016, 2026)] + ["2026-Q1", "2026-Q2", "2026-Q3"]


def files(full: bool) -> list[tuple[str, str]]:
    if full:
        return [(f"{BASE}/kompletta/{p}_beta1_jsonl.zip", f"{p}_beta1_jsonl.zip") for p in PERIODS]
    return [(f"{BASE}/exempel/{p}_beta1_1_percent_jsonl.zip", f"{p}_beta1_1_percent_jsonl.zip")
            for p in PERIODS]


# De berikade filerna för 2018 och 2019 saknar arbetsort helt. JobTech har
# publicerat rättade orter i separata metadatafiler (utan annonstext).
# De kopplas på original_id i silver och behövs i båda körlägena.
LOCATION_PATCHES = [
    (f"{BASE}/metadata/{y}_municipality_patched_beta1_metadata_jsonl.zip",
     f"{y}_municipality_patched_beta1_metadata_jsonl.zip") for y in (2018, 2019)
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="hämta alla annonser i stället för stickprovet")
    args = ap.parse_args()
    mode = "full" if args.full else "sample"
    targets = [(u, n, mode) for u, n in files(args.full)] + [(u, n, "location_patch") for u, n in LOCATION_PATCHES]
    for url, name, folder in targets:
        dest = LANDING / "jobtech" / folder / name
        fetched = download(url, dest)
        record("jobtech", folder, url, dest)
        print(f"{'hämtad ' if fetched else 'fanns  '} {dest.name}  {dest.stat().st_size / 1e6:,.0f} MB", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
