# -*- coding: utf-8 -*-
"""Wie die Kette JE ASSET filtert - aus den Produktionsdaten (03.09.2026)

## Der Anlass

Nutzerauftrag: *„schluessle mir auf anhand der Produktionsdaten, ob und
wie die Kette ueber die Filter je Asset (nur Krypto ist bisher angepasst)
funktioniert aktuell."*

Der Trichter im Log zaehlt **je Stufe**, nicht je Asset. Diese Datei
rekonstruiert den Weg jedes Werts aus zwei Tabellen, die beide eine Zeile
je Symbol je Lauf fuehren:

    auswahl_schatten   war im Lauf · wurde gewaehlt · welche Aktion
    signals            Signalzeile entstanden · gate_passed

## ⚠️ ABGRENZUNG — es gibt schon ein Werkzeug in der Naehe

`rechne_takt_je_asset.py` (02.09.) beantwortet **wie oft** ein Asset eine
Empfehlung bekommt. Es liest nur `signals`, rechnet den Takt je Tag und
haelt fest, was die Sperren wegnehmen WUERDEN - ausdruecklich fuer den
Zustand **vor** G-6 und N-14.

Diese Datei beantwortet **wo im Trichter** ein Asset haengenbleibt. Sie
liest zusaetzlich `auswahl_schatten`, trennt die beiden Codestaende und
zeigt je Symbol, welche Beitraege ueberhaupt vorliegen.

⚠️ Wer eine Mengenfrage hat, nimmt das andere Werkzeug. Wer wissen will,
warum ein bestimmtes Asset still ist, dieses.

## ⚠️ Was die Daten NICHT hergeben

Es gibt **keine** Spalte „an welcher Stufe ist dieses Symbol
gescheitert". `rollen_gate` fuehrt `letzte_stufe[symbol]` im Speicher,
geschrieben wird sie nicht. Rekonstruierbar sind deshalb nur die
**Durchgangspunkte**, nicht die Abbruchstelle:

    im Lauf  ->  beurteilt (Aktion vermerkt)  ->  Signal  ->  durchgelassen

Wer die Abbruchstelle je Asset braucht, muss sie schreiben lassen - das
ist ein eigener Punkt und steht nicht hier drin.

## ⚠️ Und ZWEI CODESTAENDE im Zeitraum

Das Notebook wurde am **02.09. mittags** scharf geschaltet (G-6 + N-14).
Alles davor ist der Stand vom 29.08., in dem der Entscheider nur zaehlte.
Beide Zeitraeume werden deshalb GETRENNT ausgewiesen - eine gemeinsame
Auswertung waere die Mischung, die mich am 03.09. schon einmal in einen
Scheinwiderspruch gefuehrt hat (F-187).

    python pruefe_kette_je_asset.py --db PFAD [--gruppe krypto]
"""
import argparse
import collections
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCHARF_AB = "2026-09-02T12:00"
EINSTIEG = ("KAUFEN", "NACHKAUFEN", "EROEFFNEN")
AUSSTIEG = ("REDUZIEREN", "VERKAUFEN", "SCHLIESSEN")


def _bestand(db):
    """Die gehaltenen Symbole - ueber `rollen_eingabe`, nicht selbst gefragt.

    ⚠️ `warteschlange._bestand_spot()` fragt `quantity > 0` und uebersieht
    sechs vollstaendig gestakte Werte (F-180). Eine dritte Variante haette
    eine dritte Antwort.
    """
    from agent import rollen_eingabe as RE
    aus = set()
    try:
        c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
        for (s,) in c.execute("SELECT symbol FROM holdings"):
            m, _e = RE.bestand(s, db, "spot")
            if m and float(m) > 0:
                aus.add(str(s).upper())
    except Exception:                                        # noqa: BLE001
        pass
    return aus


def _raenge():
    """Welche Beitraege gibt es je Symbol ueberhaupt? (Messbasis)"""
    from agent import marktrang as MR
    aus = {}
    for name in ("funding", "turnover", "oi"):
        try:
            aus[name] = {str(x).upper() for x in MR.messbasis(name)}
        except Exception:                                    # noqa: BLE001
            aus[name] = set()
    return aus


def erhebe(db, gruppe, ab, bis=None):
    """Je Symbol: im Lauf · beurteilt · Signal · durchgelassen."""
    c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    w = collections.defaultdict(lambda: collections.Counter())
    zeit = " AND lauf >= ?" + (" AND lauf < ?" if bis else "")
    args = [gruppe, ab] + ([bis] if bis else [])
    for sym, n, gew, akt in c.execute(
            "SELECT symbol, COUNT(*), SUM(gewaehlt), "
            "SUM(aktion IS NOT NULL) FROM auswahl_schatten "
            "WHERE gruppe = ?" + zeit + " GROUP BY symbol", args):
        s = sym.upper()
        w[s]["im_lauf"] = n
        w[s]["gewaehlt"] = gew or 0
        w[s]["beurteilt"] = akt or 0
    zeit2 = " AND created_at >= ?" + (" AND created_at < ?" if bis else "")
    args2 = [ab] + ([bis] if bis else [])
    for sym, a, n, ok in c.execute(
            "SELECT symbol, action, COUNT(*), SUM(COALESCE(gate_passed,0)) "
            "FROM signals WHERE quelle_kette='rollen'" + zeit2
            + " GROUP BY symbol, action", args2):
        s = sym.upper()
        if s not in w:
            continue
        w[s]["signale"] += n
        w[s]["durch"] += ok or 0
        if a in EINSTIEG:
            w[s]["ein"] += ok or 0
        elif a in AUSSTIEG:
            w[s]["aus"] += ok or 0
    return w


def zeige(titel, w, best, raenge):
    print()
    print("=" * 92)
    print(titel)
    print("=" * 92)
    if not w:
        print("  keine Daten in diesem Fenster")
        return
    print("  %-8s %-5s %6s %6s %7s %7s %6s %5s %5s  %s"
          % ("Symbol", "Best.", "Lauf", "gewaehlt", "beurt.", "Signale",
             "durch", "ein", "aus", "Beitraege"))
    ein = aus = 0
    for s in sorted(w, key=lambda x: (-w[x]["durch"], x)):
        z = w[s]
        ein += z["ein"]
        aus += z["aus"]
        bt = "".join(("F" if s in raenge["funding"] else "·",
                      "T" if s in raenge["turnover"] else "·",
                      "O" if s in raenge["oi"] else "·"))
        print("  %-8s %-5s %6d %8d %7d %7d %6d %5d %5d  %s"
              % (s, "JA" if s in best else "—", z["im_lauf"], z["gewaehlt"],
                 z["beurteilt"], z["signale"], z["durch"], z["ein"],
                 z["aus"], bt))
    print("  %-8s %-5s %6s %8s %7s %7s %6d %5d %5d"
          % ("SUMME", "", "", "", "", "",
             sum(z["durch"] for z in w.values()), ein, aus))
    print()
    print("  Beitraege: F=Funding · T=Turnover · O=Open Interest")
    ohne = [s for s in w if not any(s in raenge[k]
                                    for k in ("funding", "turnover", "oi"))]
    if ohne:
        print("  ⚠️ OHNE JEDEN BEITRAG (%d): %s" % (len(ohne),
                                                    ", ".join(sorted(ohne))))
        print("     Fuer sie kann Stufe 11 nicht bewerten - sie zaehlt nur.")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", required=True)
    p.add_argument("--gruppe", default="krypto")
    a = p.parse_args()

    best, raenge = _bestand(a.db), _raenge()
    print("KETTE JE ASSET — Gruppe %s" % a.gruppe)
    print("⚠️ Zwei Codestaende: scharf geschaltet am %s" % SCHARF_AB)
    zeige("VORHER — Stand 29.08. (der Entscheider zaehlte nur)",
          erhebe(a.db, a.gruppe, "2026-08-31", SCHARF_AB), best, raenge)
    zeige("NACHHER — scharfer Stand ab %s" % SCHARF_AB,
          erhebe(a.db, a.gruppe, SCHARF_AB), best, raenge)

    print()
    print("=" * 92)
    print("⚠️ WAS DIESE TABELLE NICHT ZEIGT")
    print("=" * 92)
    print("  An WELCHER Stufe ein Symbol scheitert, steht nirgends: das Gate")
    print("  fuehrt `letzte_stufe[symbol]` nur im Speicher. Sichtbar sind")
    print("  die Durchgangspunkte, nicht die Abbruchstelle.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
