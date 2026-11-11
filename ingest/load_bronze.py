"""Läser zip-filerna i landing till bronze som Parquet, en fil per period.

    python ingest/load_bronze.py            # stickprovet
    python ingest/load_bronze.py --full     # alla annonser

Bronze tolkar ingenting. Datum, koder och flaggor sparas som de står i
källan, och nästlade objekt (yrke, nyckelord, krav) sparas som JSON-text.
Silver gör tolkningen.

Ett undantag: kontaktfälten läses aldrig in. Dataminimering sker vid
källan, inte i efterhand. Det gäller application_contacts,
application_details, arbetsgivarens e-post, telefon och webbadress,
gatuadress, postnummer och koordinater.

Varje rad får filnamn och radnummer. Rader som inte går att tolka som
JSON sparas i en separat karantänfil, och antalet rader per fil skrivs
till en logg som dbt testar mot.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from common import DATA_DIR, LANDING, read_manifest

BATCH = 20_000

SCHEMA = pa.schema([
    ("source_file", pa.string()),
    ("line_number", pa.int64()),
    ("id", pa.string()),
    ("original_id", pa.string()),
    ("headline", pa.string()),
    ("description_text", pa.string()),
    ("publication_date", pa.string()),
    ("last_publication_date", pa.string()),
    ("application_deadline", pa.string()),
    ("removed", pa.string()),
    ("removed_date", pa.string()),
    ("number_of_vacancies", pa.string()),
    ("experience_required", pa.string()),
    ("remote_work", pa.string()),
    ("detected_language", pa.string()),
    ("source_type", pa.string()),
    ("employer_name", pa.string()),
    ("employer_workplace", pa.string()),
    ("employer_organization_number", pa.string()),
    ("municipality", pa.string()),
    ("municipality_code", pa.string()),
    ("region", pa.string()),
    ("region_code", pa.string()),
    ("country_code", pa.string()),
    ("occupation_json", pa.string()),
    ("occupation_group_json", pa.string()),
    ("occupation_field_json", pa.string()),
    ("employment_type_json", pa.string()),
    ("working_hours_type_json", pa.string()),
    ("duration_json", pa.string()),
    ("scope_of_work_json", pa.string()),
    ("keywords_json", pa.string()),
    ("must_have_json", pa.string()),
    ("nice_to_have_json", pa.string()),
])


def s(v) -> str | None:
    """Skalärt värde som text, exakt som i källan (None förblir None)."""
    if v is None:
        return None
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def j(v) -> str | None:
    return None if v is None else json.dumps(v, ensure_ascii=False)


def to_row(d: dict, source_file: str, line_number: int) -> dict:
    desc = d.get("description") or {}
    emp = d.get("employer") or {}
    addr = d.get("workplace_address") or {}
    return {
        "source_file": source_file,
        "line_number": line_number,
        "id": s(d.get("id")),
        "original_id": s(d.get("original_id")),
        "headline": s(d.get("headline")),
        "description_text": s(desc.get("text")),
        "publication_date": s(d.get("publication_date")),
        "last_publication_date": s(d.get("last_publication_date")),
        "application_deadline": s(d.get("application_deadline")),
        "removed": s(d.get("removed")),
        "removed_date": s(d.get("removed_date")),
        "number_of_vacancies": s(d.get("number_of_vacancies")),
        "experience_required": s(d.get("experience_required")),
        "remote_work": s(d.get("remote_work")),
        "detected_language": s(d.get("detected_language")),
        "source_type": s(d.get("source_type")),
        "employer_name": s(emp.get("name")),
        "employer_workplace": s(emp.get("workplace")),
        "employer_organization_number": s(emp.get("organization_number")),
        "municipality": s(addr.get("municipality")),
        "municipality_code": s(addr.get("municipality_code")),
        "region": s(addr.get("region")),
        "region_code": s(addr.get("region_code")),
        "country_code": s(addr.get("country_code")),
        "occupation_json": j(d.get("occupation")),
        "occupation_group_json": j(d.get("occupation_group")),
        "occupation_field_json": j(d.get("occupation_field")),
        "employment_type_json": j(d.get("employment_type")),
        "working_hours_type_json": j(d.get("working_hours_type")),
        "duration_json": j(d.get("duration")),
        "scope_of_work_json": j(d.get("scope_of_work")),
        "keywords_json": j(d.get("keywords")),
        "must_have_json": j(d.get("must_have")),
        "nice_to_have_json": j(d.get("nice_to_have")),
    }


def load_zip(zpath: Path, out_dir: Path, schema: pa.Schema = SCHEMA, row_fn=None) -> dict:
    row_fn = row_fn or to_row
    period = zpath.name.split("_beta1")[0].replace("_municipality_patched", "")
    out = out_dir / f"{period}.parquet"
    quarantine = out_dir / f"{period}.quarantine.jsonl"
    lines = parsed = failed = 0
    writer = pq.ParquetWriter(out, schema, compression="zstd")
    batch: list[dict] = []
    with zipfile.ZipFile(zpath) as z, open(quarantine, "w", encoding="utf-8") as qf:
        (inner,) = z.namelist()
        with z.open(inner) as raw:
            for n, line in enumerate(io.TextIOWrapper(raw, encoding="utf-8"), start=1):
                if not line.strip():
                    continue
                lines += 1
                try:
                    batch.append(row_fn(json.loads(line), zpath.name, n))
                    parsed += 1
                except (json.JSONDecodeError, AttributeError) as e:
                    failed += 1
                    qf.write(json.dumps({"file": zpath.name, "line": n, "error": str(e)}) + "\n")
                if len(batch) >= BATCH:
                    writer.write_table(pa.Table.from_pylist(batch, schema))
                    batch.clear()
    if batch:
        writer.write_table(pa.Table.from_pylist(batch, schema))
    writer.close()
    if failed == 0:
        quarantine.unlink()
    return {"source_file": zpath.name, "period": period, "lines": lines,
            "parsed": parsed, "failed": failed}


PATCH_SCHEMA = pa.schema([
    ("source_file", pa.string()),
    ("line_number", pa.int64()),
    ("original_id", pa.string()),
    ("publication_date", pa.string()),
    ("municipality", pa.string()),
    ("municipality_code", pa.string()),
    ("region", pa.string()),
    ("region_code", pa.string()),
    ("occupation_json", pa.string()),
    ("occupation_group_json", pa.string()),
    ("occupation_field_json", pa.string()),
])


def patch_row(d: dict, source_file: str, line_number: int) -> dict:
    """Komplettering för 2018–2019: ort och yrke, som saknas i de berikade filerna."""
    addr = d.get("workplace_address") or {}
    return {
        "source_file": source_file,
        "line_number": line_number,
        "original_id": s(d.get("original_id")),
        "publication_date": s(d.get("publication_date")),
        "municipality": s(addr.get("municipality")),
        "municipality_code": s(addr.get("municipality_code")),
        "region": s(addr.get("region")),
        "region_code": s(addr.get("region_code")),
        "occupation_json": j(d.get("occupation")),
        "occupation_group_json": j(d.get("occupation_group")),
        "occupation_field_json": j(d.get("occupation_field")),
    }


def load_folder(folder: str, schema: pa.Schema, row_fn) -> int:
    src = LANDING / "jobtech" / folder
    out_dir = DATA_DIR / "bronze" / "jobtech" / folder
    out_dir.mkdir(parents=True, exist_ok=True)
    known = {r["file"] for r in read_manifest()}
    zips = sorted(src.glob("*.zip"))
    if not zips:
        print(f"Inga filer i {src}. Kör download_jobtech.py först.")
        return 1
    for z in zips:
        rel = z.relative_to(LANDING).as_posix()
        if rel not in known:
            raise SystemExit(f"{rel} saknas i manifestet. Bronze läser bara registrerade filer.")
    # En process per fil. Filerna är oberoende och JSON-tolkningen är
    # det som tar tid.
    log = []
    with ProcessPoolExecutor(max_workers=min(6, len(zips))) as pool:
        futures = {pool.submit(load_zip, z, out_dir, schema, row_fn): z for z in zips}
        for fut in as_completed(futures):
            r = fut.result()
            log.append(r)
            print(f"{folder:>14} {r['period']:>8}  {r['parsed']:>9,} rader  {r['failed']} fel", flush=True)
    log.sort(key=lambda r: r["source_file"])
    with open(out_dir / "_load_log.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["source_file", "period", "lines", "parsed", "failed"])
        w.writeheader()
        w.writerows(log)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--skip-patch", action="store_true", help="läs inte om ortsfilerna")
    args = ap.parse_args()
    rc = load_folder("full" if args.full else "sample", SCHEMA, to_row)
    if rc == 0 and not args.skip_patch:
        rc = load_folder("location_patch", PATCH_SCHEMA, patch_row)
    return rc


if __name__ == "__main__":
    sys.exit(main())
