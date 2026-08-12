# -*- coding: utf-8 -*-
"""Fear-&-Greed-Historie nachladen (Paket 3, 12.08.2026).

DER ANLASS. Beim Bau von Paket 3 fiel auf, dass `macro_snapshot` genau **10**
Fear-&-Greed-Werte traegt, vom 07. bis 19.07.2026. Keine Historie, ein halber
Monat - und ich hatte den Regime-Score kurz zuvor als "variiert 0,250 bis
0,750" gemeldet. Diese Messung lief mit **Fear & Greed = 50 eingesetzt**, weil
nichts anderes da war; sie mass also den Preisanteil und nannte ihn Score.

Die Quelle gibt die Historie her, und zwar vollstaendig: `alternative.me/fng/`
mit `limit=0` liefert **3.111 Werte ab 2018-02-01**, Median-Abstand 1 Tag,
groesste Luecke 4 Tage. Ein einziger Aufruf.

WARUM DAS MEHR IST ALS EINE LUECKENFUELLUNG. Alle Fakten der Rollen-Ebene
stammen bisher aus derselben Kursreihe - Trend, Volatilitaet und Liquiditaet
lesen dieselben Kerzen. Der Fachstandard nennt das "illusion of confirmation":
drei Kennzahlen aus einer Quelle sind ein Faktor, nicht drei.

Fear & Greed ist **keine Kursgroesse**. Er ist damit einer der wenigen wirklich
unabhaengigen Faktoren, die wir kostenlos bekommen koennen - und der einzige
davon, der taeglich und rueckwirkend verfuegbar ist.

BESTEHENDE ZEILEN WERDEN NICHT UEBERSCHRIEBEN. Das Skript schreibt nur, wo noch
kein Wert steht: die zehn vorhandenen Tage stammen aus dem Livebetrieb und sind
die Referenz, an der die Naht geprueft wird.

    python lade_fear_greed_nach.py              Trockenlauf
    python lade_fear_greed_nach.py --schreiben
"""
from __future__ import annotations

import argparse
import sqlite3
from datetime import date, datetime, timezone

import requests

DB = "data/tradinginfotool.db"
URL = "https://api.alternative.me/fng/"


def hole_alles(session: requests.Session | None = None) -> dict[str, tuple[int, str]]:
    """`limit=0` heisst bei dieser API: alles, was es gibt."""
    session = session or requests.Session()
    r = session.get(URL, params={"limit": 0}, timeout=30)
    r.raise_for_status()
    aus = {}
    for eintrag in r.json().get("data") or []:
        tag = datetime.fromtimestamp(int(eintrag["timestamp"]),
                                     tz=timezone.utc).date().isoformat()
        aus[tag] = (int(eintrag["value"]),
                    str(eintrag.get("value_classification") or ""))
    return aus


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--schreiben", action="store_true")
    ap.add_argument("--db", default=DB)
    a = ap.parse_args()

    con = sqlite3.connect(a.db)
    vorher = dict(con.execute(
        "SELECT date, fear_greed_value FROM macro_snapshot "
        "WHERE fear_greed_value IS NOT NULL"))
    print(f"Bestand: {len(vorher)} Tage mit Fear & Greed"
          + (f"  {min(vorher)} .. {max(vorher)}" if vorher else ""))

    print("Abruf   alternative.me/fng/ mit limit=0 ...")
    alle = hole_alles()
    if not alle:
        print("   nichts erhalten.")
        return 1
    tage = sorted(alle)
    d = [date.fromisoformat(t) for t in tage]
    ab = sorted((d[i + 1] - d[i]).days for i in range(len(d) - 1))
    print(f"   {len(tage)} Werte  {tage[0]} .. {tage[-1]}  "
          f"Median-Abstand {ab[len(ab)//2]}, groesste Luecke {ab[-1]}")

    # DIE NAHT MESSEN, bevor irgendetwas geschrieben wird - dieselbe Disziplin
    # wie beim BTC-Nachladen (L6). Hier ist sie sogar strenger pruefbar: es ist
    # DIESELBE Quelle, also muessen die Werte EXAKT uebereinstimmen. Tun sie es
    # nicht, hat sich die Definition geaendert, und dann taugt die Historie
    # nicht als Fortsetzung des Bestands.
    gemeinsam = [(t, alle[t][0], vorher[t]) for t in tage if t in vorher]
    abweichend = [(t, n, alt) for t, n, alt in gemeinsam if n != alt]
    print(f"   Naht: {len(gemeinsam)} ueberlappende Tage, "
          f"{len(abweichend)} abweichend")
    for t, n, alt in abweichend[:5]:
        print(f"      {t}: Historie {n} gegen Bestand {alt}")
    if gemeinsam and abweichend:
        print("   ABBRUCH: dieselbe Quelle liefert andere Werte als der "
              "Bestand - die Definition hat sich geaendert.")
        return 1

    neu = [t for t in tage if t not in vorher]
    print(f"\nNachzuladen: {len(neu)} Tage"
          + (f"  ({neu[0]} .. {neu[-1]})" if neu else ""))
    if not neu:
        print("   nichts zu tun.")
        return 0
    if not a.schreiben:
        print("\nTROCKENLAUF - nichts geschrieben. Mit --schreiben ausfuehren.")
        return 0

    jetzt = datetime.now(timezone.utc).isoformat()
    con.executemany(
        "INSERT INTO macro_snapshot (date, fear_greed_value, fear_greed_label, "
        "fetched_at) VALUES (?, ?, ?, ?) "
        # Nur fuellen, nie ueberschreiben: `COALESCE` laesst einen vorhandenen
        # Wert stehen. Die zehn Live-Tage bleiben damit die Referenz.
        "ON CONFLICT(date) DO UPDATE SET "
        "fear_greed_value = COALESCE(macro_snapshot.fear_greed_value, excluded.fear_greed_value), "
        "fear_greed_label = COALESCE(macro_snapshot.fear_greed_label, excluded.fear_greed_label)",
        [(t, alle[t][0], alle[t][1], jetzt) for t in neu])
    con.commit()
    n, a1, b1 = con.execute(
        "SELECT COUNT(*), MIN(date), MAX(date) FROM macro_snapshot "
        "WHERE fear_greed_value IS NOT NULL").fetchone()
    print(f"\nGeschrieben. Bestand jetzt: {n} Tage  {a1} .. {b1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
