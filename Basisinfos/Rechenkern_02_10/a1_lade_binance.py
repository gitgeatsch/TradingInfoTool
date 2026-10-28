"""A1 Vorarbeit V1 (Voranalyse_Dashboard_LLM_28_10.md §7): Binance-Ankuendigungen ALLER ereignistragenden Kataloge ab 2023 sichern.
Oeffentliche Website-Schnittstelle ohne Schluessel, nur lesend; Ablage am DESKTOP data/_a1/binance_ankuendigungen_alle.db (nicht die
Produktion, keine Messbasis). Fortsetzbar: bereits geholte Meldungen mit Text werden nicht erneut abgerufen. Die E-1-Ablage
(data/_e1/, Delisting + News ab 2023-06) bleibt unberuehrt - sie traegt registrierte Befunde.

    python -X utf8 Basisinfos/Rechenkern_02_10/a1_lade_binance.py            # laden bzw. fortsetzen
    python -X utf8 Basisinfos/Rechenkern_02_10/a1_lade_binance.py --stand    # nur Bestand ausgeben

KATALOGE (Abfrage 28.10.2026, Gesamtzahl seit Beginn):
  48  New Cryptocurrency Listing  2.290   Text holen  - Listing, Launchpool, HODLer-Airdrop, Futures-Neuaufnahme
  49  Latest Binance News         4.471   Text holen  - Migration, Umbenennung, Netz-Upgrade, Monitoring, Seed-Tag
  161 Delisting                     446   Text holen  - Token-, Paar-, Futures-, Margin-Delisting
  157 Maintenance Updates           613   Text holen  - Wallet-Sperren bei Hard Fork / Netz-Upgrade
  128 Crypto Airdrop                 53   Text holen
  93  Latest Activities           3.211   nur Titel   - ueberwiegend Kampagnen; der Titel genuegt fuer die Einordnung
  51  API Updates                    81   nicht geladen (kein Asset-Ereignis)
Zeitpunkt des Bekanntwerdens (PIT) = release_ms der Schnittstelle (Millisekunden, UTC). 'geholt' = Abrufzeit.
"""
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone

import requests

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
ABLAGE = os.path.join(PROJ, "data", "_a1", "binance_ankuendigungen_alle.db")
LISTE = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
DETAIL = "https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query"
H = {"User-Agent": "Mozilla/5.0 TradingInfoTool-A1"}
AB_MS = int(datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)   # Messfokus ab 2023 (2022 nur Auskunft)
KATALOGE = {48: True, 49: True, 161: True, 157: True, 128: True, 93: False}  # Katalog -> Text holen?
SEITE = 50


def text(body: str) -> str:
    out = []

    def walk(n):
        if isinstance(n, dict):
            if n.get("node") == "text":
                out.append(n.get("text", ""))
            for ch in n.get("child", []) or []:
                walk(ch)
    try:
        walk(json.loads(body))
    except Exception:                                          # noqa: BLE001
        return body or ""
    return " ".join(out).replace("&nbsp;", " ")


def hole(url, params, versuche=6):
    """Eine gescheiterte Abfrage ist KEINE leere Seite (Lehre E-1): wiederholen, sonst Abbruch (fortsetzbar)."""
    for v in range(versuche):
        try:
            r = requests.get(url, params=params, headers=H, timeout=30)
            if r.status_code == 200:
                return r.json()["data"]
        except Exception:                                      # noqa: BLE001
            pass
        time.sleep(5 * (v + 1))
    return None


def stand(c):
    print("Bestand %s" % ABLAGE)
    for kat, n, t, lo, hi in c.execute("SELECT katalog, COUNT(*), SUM(text IS NOT NULL AND text <> ''), MIN(release_ms), MAX(release_ms) "
                                       "FROM meldung GROUP BY katalog ORDER BY katalog"):
        f = lambda ms: datetime.fromtimestamp(ms / 1000, timezone.utc).strftime("%Y-%m-%d")   # noqa: E731
        print("  Katalog %3d · Meldungen %5d · mit Text %5d · %s bis %s" % (kat, n, t or 0, f(lo), f(hi)))
    print("  gesamt %d" % c.execute("SELECT COUNT(*) FROM meldung").fetchone()[0])


def main():
    os.makedirs(os.path.dirname(ABLAGE), exist_ok=True)
    c = sqlite3.connect(ABLAGE)
    c.executescript("""CREATE TABLE IF NOT EXISTS meldung (code TEXT PRIMARY KEY, katalog INTEGER, titel TEXT, release_ms INTEGER,
                                                           text TEXT, geholt TEXT);
                       CREATE INDEX IF NOT EXISTS i_release ON meldung (release_ms);""")
    if "--stand" in sys.argv:
        stand(c)
        return 0
    neu = 0
    for kat, mit_text in KATALOGE.items():
        for seite in range(1, 400):
            d = hole(LISTE, {"type": 1, "catalogId": kat, "pageNo": seite, "pageSize": SEITE})
            if d is None:
                c.commit()
                raise SystemExit("Katalog %d Seite %d nach 6 Versuchen nicht abrufbar - Abbruch (fortsetzbar)" % (kat, seite))
            arts = d["catalogs"][0]["articles"] if d.get("catalogs") else []
            if not arts:
                break
            for x in arts:
                if x["releaseDate"] < AB_MS:
                    continue
                alt = c.execute("SELECT text FROM meldung WHERE code=?", (x["code"],)).fetchone()
                if alt and (alt[0] or not mit_text):
                    continue
                txt = None
                if mit_text:
                    dd = hole(DETAIL, {"articleCode": x["code"]}, versuche=3)
                    txt = text(dd.get("body") or "") if dd else None   # None = spaeter nachholen
                    time.sleep(0.3)
                c.execute("INSERT OR REPLACE INTO meldung VALUES (?,?,?,?,?,?)",
                          (x["code"], kat, x["title"], x["releaseDate"], txt, datetime.now(timezone.utc).isoformat()))
                neu += 1
            c.commit()
            print("  Katalog %3d Seite %3d · bis %s · neu gesamt %d" % (
                kat, seite, datetime.fromtimestamp(min(x["releaseDate"] for x in arts) / 1000, timezone.utc).strftime("%Y-%m-%d"), neu),
                flush=True)
            if min(x["releaseDate"] for x in arts) < AB_MS:
                break
            time.sleep(0.5)
    print("A1 Lader · neue Meldungen %d" % neu)
    stand(c)
    fehlt = c.execute("SELECT COUNT(*) FROM meldung WHERE katalog IN (%s) AND text IS NULL"
                      % ",".join(str(k) for k, t in KATALOGE.items() if t)).fetchone()[0]
    print("  ohne Text (Abruf gescheitert, beim naechsten Lauf nachgeholt): %d" % fehlt)
    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
