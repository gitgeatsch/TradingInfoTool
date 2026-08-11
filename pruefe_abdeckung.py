# -*- coding: utf-8 -*-
"""Welche Assets kann die Rollen-Ebene ueberhaupt beschreiben - und welche nicht?

DER ANLASS (11.08.2026, Nutzerhinweis "alle muessen funktionieren"): Von 57
Watchlist-Assets hat die Rollen-Ebene fuer 16 keine Kursreihe. `reihen.get(sym)`
liefert None, `beschreibe_lage()` bekommt keine Eingabe - und die Kette
ueberspringt das Asset STUMM. Kein Fehler, kein Protokolleintrag, es kommt
einfach nicht vor. Fuer die gesamte Assetklasse Rohstoffe gilt das ausnahmslos.

    Nutzer am 11.08.: "ein Ausrutscher innerhalb der Kette kann im worst case
    das ganze System kippen - oder als U-Boot unterschwellig massive
    Verschiebung erzeugen."

Genau diese Sorte. Ein stumm uebersprungenes Viertel der Watchlist sieht in
jeder Auswertung aus wie "kein Signal", nicht wie "nicht geprueft".

WAS DIESES SKRIPT NICHT TUT, UND WARUM

Es fuellt keine Luecke durch Ersatz. Naheliegend waere, fuer OD7C die Reihe
`_ROHSTOFF_FUTURES_OD7C` zu nehmen - 26 Jahre Historie, direkt daneben. Das
waere der Fehler vom 06.08. zurueckgeholt: bis dahin lag die Futures-Historie
unter dem ETC-Symbol, und alles Nachgelagerte hielt sie fuer den ETC. Ergebnis
war ein OD7C-Signal mit Kursen, die es an der Boerse nie gab.

Die Trennung ist Absicht (`agent/rohstoff/pipeline.py::_futures_symbol`, dazu
die Migration in `database/db.py`): der Future traegt die technische Struktur,
der ETC traegt den handelbaren Kurs. Die ETC-Reihe entsteht aus beidem, wenn
die Pipeline laeuft. Solange sie steht, ist "ohne Kurs" der EHRLICHE Zustand -
so steht es dort woertlich: "sichtbar statt falsch".

Dieses Skript macht "sichtbar" wahr. Es ersetzt nichts.

REGELN, DIE HIER GELTEN (Nutzerhinweis 11.08.: "immer die LLM-Regeln mit Text
beruecksichtigen und nicht wieder in bestimmte Fallen laufen")

  * Eine fehlende Reihe wird als FEHLEND benannt, nicht durch einen Ersatz
    verdeckt. Ein Ersatzwert, der wie ein Kurs aussieht, ist schlimmer als eine
    Luecke - er ist nicht als falsch erkennbar.
  * Der Hinweis "keine Historie" unterscheidet ZWISCHEN Assets (manche haben
    eine, manche nicht) und ist damit kein konstantes Feld im Sinne von
    `finde_konstanten()`. Waere er fuer alle gleich, gehoerte er nicht in den
    Faktensatz.
  * Fuer die Uebergabe an ein Modell gilt die bestehende Konvention
    `nicht_verfuegbar` - kein neues Vokabular erfinden.

    python pruefe_abdeckung.py
"""
from __future__ import annotations

import sqlite3
import sys
from collections import defaultdict

DB = "data/tradinginfotool.db"
MIN_KERZEN = 220   # dieselbe Schranke wie bei der Ankerpruefung


def _reihen_laengen(db: str = DB) -> dict[str, int]:
    """Wie viele brauchbare USD-Kerzen hat jedes Symbol? Gleicher Filter wie
    `lade_reihen_aus_db()` - sonst misst dieses Skript etwas anderes als das,
    was die Kette spaeter liest."""
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    # Waehrungswahl wie im Lader: USD bevorzugt, EUR als Rueckfall. Wer hier
    # nur USD zaehlt, meldet die gesamte Assetklasse ETF als fehlend, obwohl
    # sie mit bis zu 4.722 Kerzen vorliegt (Befund 11.08.).
    q = ("select symbol, currency, count(*) from price_history_ohlc "
         "where currency in ('USD','EUR') and close is not null "
         "and high is not null and low is not null group by symbol, currency")
    je = {}
    for sym, cur, n in c.execute(q):
        je.setdefault(sym, {})[cur] = n
    return {s: v.get('USD', v.get('EUR', 0)) for s, v in je.items()}


def _preis_vorhanden(db: str = DB) -> set[str]:
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    return {r[0] for r in c.execute(
        "select distinct symbol from price_cache where price_eur is not null "
        "or price_usd is not null")}


def _grund(symbol: str, laengen: dict, preise: set) -> str:
    """Warum kann dieses Asset nicht beschrieben werden? Der Grund entscheidet,
    was zu tun ist - deshalb wird er benannt und nicht nur gezaehlt."""
    n = laengen.get(symbol, 0)
    if n >= MIN_KERZEN:
        return ""
    futures = f"_ROHSTOFF_FUTURES_{symbol}"
    if laengen.get(futures, 0) >= MIN_KERZEN:
        return (f"ETC-Reihe fehlt, Futures-Referenz vorhanden "
                f"({laengen[futures]} Kerzen) - die Pipeline rekonstruiert sie. "
                f"KEIN Ersatz verwenden (Fehler vom 06.08.)")
    if n:
        return f"nur {n} Kerzen, unter der Schranke von {MIN_KERZEN}"
    if symbol in preise:
        return "aktueller Preis vorhanden, aber KEINE OHLC-Historie"
    return "weder Historie noch Preis"


def main() -> int:
    import argparse
    import config
    p = argparse.ArgumentParser(description=__doc__)
    # WARUM EIN PFAD-ARGUMENT (11.08.): Der erste Lauf ging gegen die
    # Desktop-DB, deren Daten am 19.07. enden - zwei Wochen VOR dem
    # CoinGecko-Rueckfall (03.08.), der genau die gemeldeten Luecken schliesst.
    # Das Ergebnis war eine Luecke, die es in der Produktion nicht gibt. Eine
    # Abdeckungspruefung ist nur so gut wie der Datenstand, auf dem sie laeuft -
    # deshalb muss er waehlbar und im Kopf der Ausgabe sichtbar sein.
    p.add_argument("--db", default=DB, help="Pfad zur zu pruefenden Datenbank")
    args = p.parse_args()

    laengen = _reihen_laengen(args.db)
    preise = _preis_vorhanden(args.db)
    watchlist = config.get_watchlist()
    stand = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True).execute(
        "select max(date) from price_history_ohlc").fetchone()[0]
    print(f"DATENSTAND: {args.db} - juengste Kerze {stand}")

    je_klasse: dict[str, list] = defaultdict(list)
    for a in watchlist:
        je_klasse[a.assetklasse].append(a.symbol)

    print(f"ABDECKUNG DER ROLLEN-EBENE - {len(watchlist)} Watchlist-Assets")
    print(f"Schranke: {MIN_KERZEN} USD-Kerzen (wie bei der Ankerpruefung)\n")

    gesamt_ok = gesamt_fehlt = 0
    luecken: list[tuple[str, str, str]] = []
    for klasse in sorted(je_klasse):
        syms = sorted(je_klasse[klasse])
        ok = [s for s in syms if laengen.get(s, 0) >= MIN_KERZEN]
        fehlt = [s for s in syms if s not in ok]
        gesamt_ok += len(ok); gesamt_fehlt += len(fehlt)
        anteil = 100.0 * len(ok) / len(syms) if syms else 0.0
        marke = "  " if not fehlt else "!!"
        print(f"{marke} {klasse:12} {len(ok):3} von {len(syms):3} beschreibbar "
              f"({anteil:5.1f} %)")
        for s in fehlt:
            g = _grund(s, laengen, preise)
            luecken.append((klasse, s, g))
            print(f"      {s:10} {g}")

    print(f"\n{'=' * 72}")
    print(f"beschreibbar {gesamt_ok} · nicht beschreibbar {gesamt_fehlt} "
          f"({100.0 * gesamt_fehlt / len(watchlist):.0f} % der Watchlist)")

    # Eine ganze Klasse ohne Abdeckung ist etwas anderes als einzelne Luecken -
    # dann laeuft die Kette fuer diese Klasse ueberhaupt nicht.
    for klasse, syms in sorted(je_klasse.items()):
        if not any(laengen.get(s, 0) >= MIN_KERZEN for s in syms):
            print(f"\n!! KLASSE '{klasse}' VOLLSTAENDIG OHNE ABDECKUNG - die "
                  f"Kette laeuft fuer sie nicht an.")

    print("\nLESART: Das ist keine Fehlerliste zum Wegarbeiten, sondern die")
    print("Vorflugkontrolle. Wer eine Messung faehrt, ohne sie gesehen zu")
    print("haben, misst ein Viertel der Watchlist nicht - und merkt es nicht,")
    print("weil ein stumm uebersprungenes Asset wie 'kein Signal' aussieht.")
    return 1 if gesamt_fehlt else 0


if __name__ == "__main__":
    sys.exit(main())
