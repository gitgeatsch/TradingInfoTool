# -*- coding: utf-8 -*-
"""K-BP-2 (10.10.2026, Schritt7 Par. 23.36): ROHE Bitpanda-Buchungen eines Zeitfensters ansehen - NUR LESEND.

    python nb_bitpanda_buchungen_roh.py [von] [bis]        (ISO, Vorgabe 2026-10-09T08:25:00Z bis 2026-10-09T08:35:00Z)
    python nb_bitpanda_buchungen_roh.py --voll [von] [bis] (P11b, 16.10.: alle Seiten, ungekuerzt als JSON in den Austauschordner)

WOZU: Nach dem Importer-Fix (0995cc3) meldet der Abgleich fuer EURCV *"Buchungen ergeben Spot 696,04 / Hebel -2600, Bitpanda
meldet 296,04 + -2600"*. Die Differenz ist genau das Eigenkapital (400) der ETH-Position, eroeffnet 09.10. 08:29:58 UTC. Vermutung:
mehrere Buchungen derselben Wallet in derselben Sekunde, und `aktualisiere_wallet_salden` (`zeit >= ...`) nahm den ZWISCHENSTAND.
Diese Ausgabe zeigt die Buchungen in der Reihenfolge der Antwort, mit Zeitstempel und Saldo danach - damit die Vermutung gemessen wird.

⚠️ OHNE SEITENEFFEKT: kein Projekt-Import (`api.bitpanda_public._hole` schreibt ueber `@track_api_health` in die Produktions-DB),
keine DB, keine Mail, ein Abruf je Seite; der Schluessel nur aus .env, nie ausgegeben.
"""
import json
import os
import platform
import sys

import requests

URL = "https://api.public.bitpanda.com/v1/operations"
ASSETS = {"1ef96b30-6729-657a-aa72-7bae1036a7b1": "EURCV", "b86c113a-efe3-11eb-b56f-0691764446a7": "ETH",
          "b86c034b-efe3-11eb-b56f-0691764446a7": "BTC"}


def schluessel():
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), encoding="utf-8") as f:
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


def voll(k, von, bis):
    """P11b-Voranalyse (16.10.2026): ALLE Vorgaenge des Fensters VOLLSTAENDIG (Vorgangs- UND Buchungsfelder, ungekuerzt) als JSON.
    Seitenweise ueber Datumsfenster wie api.bitpanda_public.hole_buchungen_mit_stand (`to` wandert auf den aeltesten Zeitpunkt der
    Seite, eine Millisekunde zurueck, wenn nichts Neues kam). Nur lesend; die Antwort enthaelt keinen Schluessel."""
    from datetime import datetime, timedelta
    vorgaenge, grenze = {}, bis
    for _ in range(500):
        r = requests.get(URL, headers={"X-Api-Key": k}, params={"page_size": 100, "from": von, "to": grenze}, timeout=60)
        if r.status_code != 200:
            raise RuntimeError("Bitpanda antwortete %d: %s" % (r.status_code, r.text[:200].replace(k, "***")))
        seite = r.json().get("data") or []
        neu = 0
        for o in seite:
            if o.get("operation_id") and o["operation_id"] not in vorgaenge:
                vorgaenge[o["operation_id"]] = o
                neu += 1
        zeiten = [t.get("credited_at") for o in seite for t in o.get("transactions") or [] if t.get("credited_at")]
        if not seite or not zeiten:
            break
        aeltest = min(zeiten)
        if neu == 0:
            d = datetime.fromisoformat(aeltest.replace("Z", "+00:00")) - timedelta(milliseconds=1)
            aeltest = d.isoformat().replace("+00:00", "Z")
        if aeltest == grenze:
            break
        grenze = aeltest
        if len(seite) < 100 and neu:
            break
    return list(vorgaenge.values())


def main():
    if "--voll" in sys.argv:
        argv = [x for x in sys.argv[1:] if x != "--voll"]
        von = argv[0] if argv else "2025-01-01T00:00:00Z"
        bis = argv[1] if len(argv) > 1 else "2030-01-01T00:00:00Z"
        k = schluessel()
        if not k:
            print("BITPANDA_API_KEY nicht in .env - Abbruch"); return 1
        ops = voll(k, von, bis)
        w = drive_wurzel()
        ziel = os.path.join(w or ".", "Claude_Austauschordner", "Notebook_Analysedaten",
                            "nb_bitpanda_buchungen_voll_%s.json" % platform.node()) if w else "nb_bitpanda_buchungen_voll.json"
        with open(ziel, "w", encoding="utf-8") as f:
            json.dump({"von": von, "bis": bis, "geraet": platform.node(), "vorgaenge": ops}, f, ensure_ascii=False)
        typen = {}
        for o in ops:
            typen[o.get("operation_type")] = typen.get(o.get("operation_type"), 0) + 1
        print("K-BP-2 VOLL %s bis %s - %d Vorgaenge · %s" % (von, bis, len(ops), ", ".join("%s %d" % kv for kv in sorted(typen.items()))))
        print("-> geschrieben nach %s" % ziel)
        return 0
    von = sys.argv[1] if len(sys.argv) > 1 else "2026-10-09T08:25:00Z"
    bis = sys.argv[2] if len(sys.argv) > 2 else "2026-10-09T08:35:00Z"
    k = schluessel()
    if not k:
        print("BITPANDA_API_KEY nicht in .env - Abbruch"); return 1
    r = requests.get(URL, headers={"X-Api-Key": k}, params={"page_size": 100, "from": von, "to": bis}, timeout=30)
    if r.status_code != 200:
        print("Bitpanda antwortete %d: %s" % (r.status_code, r.text[:200].replace(k, "***"))); return 1
    ops = r.json().get("data") or []
    aus = ["K-BP-2 ROHE BUCHUNGEN %s bis %s - Geraet %s - nur lesend, keine DB" % (von, bis, platform.node()),
           "Vorgaenge im Fenster: %d (Reihenfolge der Antwort)" % len(ops), ""]
    nr = 0
    for o in ops:
        for t in o.get("transactions") or []:
            aid = (t.get("asset_amount") or {}).get("asset_id") or (t.get("asset_balance_after") or {}).get("asset_id")
            nr += 1
            felder = {x: t.get(x) for x in sorted(t) if x not in ("asset_amount", "asset_balance_after")}
            aus.append("%3d op %s %-28s | %-6s | %-22s | %s | Menge %s | Saldo danach %s | %s" % (
                nr, (o.get("operation_id") or "")[:8], o.get("operation_type"), ASSETS.get(aid, (aid or "?")[:8]), t.get("wallet_owner"),
                t.get("credited_at"), (t.get("asset_amount") or {}).get("value"), (t.get("asset_balance_after") or {}).get("value"),
                json.dumps({x: felder[x] for x in felder if x not in ("wallet_owner", "credited_at")}, ensure_ascii=False)[:300]))
    text = "\n".join(aus)
    print(text)
    w = drive_wurzel()
    if w:
        pf = os.path.join(w, "Claude_Austauschordner", "Notebook_Analysedaten", "nb_bitpanda_buchungen_roh_%s.txt" % platform.node())
        with open(pf, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print("\n➤ geschrieben nach %s" % pf)
    return 0


if __name__ == "__main__":
    sys.exit(main())
