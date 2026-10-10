# -*- coding: utf-8 -*-
"""K-BP-2 (10.10.2026, Schritt7 Par. 23.36): ROHE Bitpanda-Buchungen eines Zeitfensters ansehen - NUR LESEND.

    python nb_bitpanda_buchungen_roh.py [von] [bis]        (ISO, Vorgabe 2026-10-09T08:25:00Z bis 2026-10-09T08:35:00Z)

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


def main():
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
