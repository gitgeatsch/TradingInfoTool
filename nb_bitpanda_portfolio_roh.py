# -*- coding: utf-8 -*-
"""K-BP-1 (09.10.2026, Schritt7 Par. 23.31): ROHANTWORT von Bitpanda `/portfolio` ansehen - NUR LESEND.

    python nb_bitpanda_portfolio_roh.py

WOZU: Der Abgleich (`importer/bitpanda_bestand.abgleich_neu`) baut `{asset_id: Zeile}` und behaelt je Asset nur die LETZTE Zeile.
Bei offenem Hebel meldete Bitpanda fuer BTC genau den Hebelteil (0,02038541) und fuer EURCV genau den Kredit (-2.600). Die Frage fuer
den Fix (saubere Trennung Spot/Hebel): Liefert `/portfolio` je Asset MEHRERE Zeilen, und KENNZEICHNET jede Zeile, ob sie Spot oder Hebel
ist? Nur dann kann die Spot-Kontrolle Spot gegen Spot pruefen; sonst muss sie ueber die Wallets rechnen.

⚠️ OHNE SEITENEFFEKT (CLAUDE.md: Pruefung am Zielgeraet ohne Seiteneffekt):
  * kein Import aus dem Projekt - `api.bitpanda_public._hole` traegt `@track_api_health` und SCHREIBT in die Produktions-DB
  * keine Datenbank, keine Mail; ein einziger GET auf `/portfolio`
  * der Schluessel wird nur aus .env gelesen und nie ausgegeben
Ausgabe: Bildschirm und <Google Drive>/Claude_Austauschordner/Notebook_Analysedaten/nb_bitpanda_portfolio_roh_<GERAET>.txt
"""
import json
import os
import platform
import sys

import requests

URL = "https://api.public.bitpanda.com/v1/portfolio"
EUR_WAEHRUNG_ID = "b88b8466-efe3-11eb-b56f-0691764446a7"     # wie api/bitpanda_public.EUR_WAEHRUNG_ID
GEFRAGT = {"b86c034b-efe3-11eb-b56f-0691764446a7": "BTC", "b86c113a-efe3-11eb-b56f-0691764446a7": "ETH",
           "1ef96b30-6729-657a-aa72-7bae1036a7b1": "EURCV"}


def schluessel():
    pf = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    with open(pf, encoding="utf-8") as f:
        for z in f:
            z = z.strip()
            if z.startswith("BITPANDA_API_KEY="):
                return z.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def drive_wurzel():
    for b in ("G", "K", "H", "E", "F"):
        for o in ("My Drive", "Meine Ablage"):
            if os.path.isdir("%s:/%s" % (b, o)):
                return "%s:/%s" % (b, o)
    return None


def main():
    aus = ["K-BP-1 ROHANTWORT /portfolio - Geraet %s - nur lesend, ein GET, keine DB" % platform.node(), ""]
    k = schluessel()
    if not k:
        print("BITPANDA_API_KEY nicht in .env gefunden - Abbruch"); return 1
    r = requests.get(URL, headers={"X-Api-Key": k}, params={"equivalent_currency_id": EUR_WAEHRUNG_ID}, timeout=30)
    if r.status_code != 200:
        print("Bitpanda antwortete %d - Abbruch (Text ohne Schluessel): %s" % (r.status_code, r.text[:200].replace(k, "***"))); return 1
    js = r.json()
    daten = js.get("data") or []
    je = {}
    for z in daten:
        je.setdefault(z.get("asset_id") or ("fiat:%s" % z.get("currency_id")), []).append(z)
    felder = sorted({f for z in daten for f in z})
    aus.append("Zeilen gesamt %d · Assets %d · Felder je Zeile: %s" % (len(daten), len(je), ", ".join(felder)))
    mehrfach = {a: len(v) for a, v in je.items() if len(v) > 1}
    aus.append("Assets mit MEHR ALS EINER Zeile: %d %s" % (len(mehrfach), "" if not mehrfach else "- " + ", ".join(
        "%s x%d" % (GEFRAGT.get(a, a[:8]), n) for a, n in sorted(mehrfach.items(), key=lambda x: -x[1]))))
    aus.append("Oberste Ebene der Antwort (ohne data): %s" % json.dumps({x: y for x, y in js.items() if x != "data"}, ensure_ascii=False)[:500])
    aus.append("")
    for aid, name in GEFRAGT.items():
        zeilen = je.get(aid, [])
        aus.append("--- %s (%s): %d Zeile(n)" % (name, aid, len(zeilen)))
        for i, z in enumerate(zeilen, 1):
            aus.append("  Zeile %d (Reihenfolge in der Antwort): %s" % (i, json.dumps(z, ensure_ascii=False, sort_keys=True)))
    text = "\n".join(aus)
    print(text)
    w = drive_wurzel()
    if w is None:
        print("\n⚠️ Google Drive nicht gefunden - Ergebnis nur oben auf dem Bildschirm"); return 0
    ziel = os.path.join(w, "Claude_Austauschordner", "Notebook_Analysedaten")
    os.makedirs(ziel, exist_ok=True)
    pf = os.path.join(ziel, "nb_bitpanda_portfolio_roh_%s.txt" % platform.node())
    with open(pf, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print("\n➤ geschrieben nach %s" % pf)
    return 0


if __name__ == "__main__":
    sys.exit(main())
