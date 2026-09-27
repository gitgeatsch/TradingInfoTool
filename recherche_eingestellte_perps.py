# -*- coding: utf-8 -*-
"""Recherche: welche USDT-Perpetuals kennt das Binance-Archiv, die Binance heute NICHT handelt?

**27.09.2026** · Voranalyse `Basisinfos/Voranalyse_Nachladen_Eingestellte_27_09.md`,
Befund 2.668 (die Stundenkurse sind ueberlebensverzerrt).

Liest NUR oeffentliche Listen, laedt keine Kursdaten:
    1  die Ordnerliste data/futures/um/monthly/klines/ und data/spot/monthly/klines/
       des Archivs (data.binance.vision, S3-Liste, seitenweise)
    2  fapi/v1/exchangeInfo - der heutige Status je Perpetual
    3  je heute nicht gehandeltem Perpetual die Monatsliste seiner 1h-Klines
Rund 345 Abrufe, 0,6 s Pause je Abruf (Nutzer: *vorsicht bei API-Aufrufen,
nicht zu schnell*). Schreibt nur data/_recherche_eingestellt.json.

    python recherche_eingestellte_perps.py
"""
from __future__ import annotations

import json
import os
import re
import sys
import time

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ARCHIV = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
FAPI = "https://fapi.binance.com/fapi/v1/exchangeInfo"
ZIEL = os.path.join("data", "_recherche_eingestellt.json")
PAUSE_S = 0.6
FENSTER = ("2021-12", "2026-08")
MIN_MONATE = 6


def ordner(prefix: str) -> list:
    aus, marker = [], None
    while True:
        p = {"delimiter": "/", "prefix": prefix}
        if marker:
            p["marker"] = marker
        r = requests.get(ARCHIV, params=p, timeout=60)
        r.raise_for_status()
        pre = [x for x in re.findall(r"<Prefix>([^<]+)</Prefix>", r.text)
               if x != prefix]
        aus += pre
        time.sleep(PAUSE_S)
        if "<IsTruncated>true</IsTruncated>" in r.text and pre:
            marker = pre[-1]
        else:
            break
    return [x[len(prefix):].strip("/") for x in aus]


def main() -> int:
    um = [s for s in ordner("data/futures/um/monthly/klines/")
          if s.endswith("USDT") and "_" not in s]
    sp = {s for s in ordner("data/spot/monthly/klines/") if s.endswith("USDT")}
    info = requests.get(FAPI, timeout=30).json()
    time.sleep(PAUSE_S)
    status = {s["symbol"]: s["status"] for s in info["symbols"]
              if s.get("contractType") == "PERPETUAL"
              and s.get("quoteAsset") == "USDT"}
    nicht = [s for s in um if status.get(s) != "TRADING"]
    print("Archiv: %d USDT-Perpetuals, %d mit Spot-Archiv · heute TRADING %d · "
          "nicht TRADING %d" % (len(um), len(sp & set(um)),
                                 sum(status.get(s) == "TRADING" for s in um),
                                 len(nicht)))
    monate = {}
    for s in nicht:
        r = requests.get(ARCHIV, params={
            "prefix": "data/futures/um/monthly/klines/%s/1h/" % s}, timeout=60)
        monate[s] = sorted(set(re.findall(r"%s-1h-(\d{4}-\d{2})\.zip<" % s,
                                          r.text)))
        time.sleep(PAUSE_S)
    im = {s: [m for m in ms if FENSTER[0] <= m <= FENSTER[1]]
          for s, ms in monate.items()}
    kand = {s: ms for s, ms in im.items() if len(ms) >= MIN_MONATE}
    print("davon mindestens %d Monate im Fenster %s bis %s: %d, zusammen %d "
          "Symbol-Monate, %d mit Spot-Archiv" % (
              MIN_MONATE, FENSTER[0], FENSTER[1], len(kand),
              sum(len(m) for m in kand.values()), sum(s in sp for s in kand)))
    print("  heutiger Status: %s" % {k: sum(status.get(s, "(nicht gelistet)") == k
                                            for s in kand)
                                     for k in ("SETTLING", "(nicht gelistet)")})
    with open(ZIEL, "w", encoding="utf-8") as f:
        json.dump({"um": um, "spot": sorted(sp), "status": status,
                   "monate": monate, "kandidaten": kand}, f)
    print("  geschrieben: %s (Einordnung Krypto/Aktie/Index/Umbenennung folgt "
          "in der Voranalyse, nicht hier)" % ZIEL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
