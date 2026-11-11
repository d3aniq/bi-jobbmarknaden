"""Hämtar anställda per län och yrke (SSYK 2012, 4 siffror) från SCB (CC0).

    python ingest/download_scb.py

Tre tabeller täcker 2014–2024, med två metodbyten:

    YREG60     2014–2018   16–64 år, RAMS
    YREG60N    2019–2021   16–64 år, RAMS (ny version)
    YREG60BAS  2020–2024   alla åldrar, BAS

2020 och 2021 finns i både YREG60N och YREG60BAS. Silver behåller båda,
så att skillnaden mellan metoderna går att mäta i stället för att döljas.

Kön utelämnas i frågan, vilket ger summan för båda könen (SCB:s
"eliminering"). Svaret sparas oförändrat som JSON.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request

from common import LANDING, USER_AGENT, record

BASE = "https://api.scb.se/OV0104/v1/doris/sv/ssd/START/AM/AM0208/AM0208M"
TABLES = ["YREG60", "YREG60N", "YREG60BAS"]


def query(table: str) -> bytes:
    url = f"{BASE}/{table}"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": USER_AGENT}), timeout=60) as r:
        meta = json.load(r)
    content = next(v for v in meta["variables"] if v["code"] == "ContentsCode")["values"]
    body = {
        "query": [
            {"code": "Region", "selection": {"filter": "all", "values": ["*"]}},
            {"code": "Yrke2012", "selection": {"filter": "all", "values": ["*"]}},
            {"code": "ContentsCode", "selection": {"filter": "item", "values": content}},
            {"code": "Tid", "selection": {"filter": "all", "values": ["*"]}},
        ],
        "response": {"format": "json"},
    }
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def main() -> int:
    out_dir = LANDING / "scb"
    out_dir.mkdir(parents=True, exist_ok=True)
    for t in TABLES:
        data = query(t)
        dest = out_dir / f"{t}.json"
        dest.write_bytes(data)
        record("scb", "all", f"{BASE}/{t}", dest)
        n = len(json.loads(data.decode("utf-8-sig"))["data"])
        print(f"{t:<10} {n:>7,} celler", flush=True)
        time.sleep(2)  # SCB tillåter 10 anrop per 10 sekunder
    return 0


if __name__ == "__main__":
    sys.exit(main())
