# -*- coding: utf-8 -*-
"""Rechnet unser Prompt dem Modell etwas vor? - Dauerpruefung (16.08.2026).

DER ANLASS. Beim Bau der Boersendivergenz stand im Entwurf:

    "... an den Boersen ungleich: OKX +0.0 %, Bybit -1.3 %."
    "Die Spanne zwischen den 3 Boersen betraegt 1.3 Prozentpunkte; ..."

Drei Zahlen, und die dritte ist die Differenz der ersten beiden. Nutzerhinweis:
*"wurde der Parameter ausreichend gegengeprueft, ob es positiv fuer unsere
LLM-Config ist bzw. nicht schaedlich - da LLMs nicht mit Zahlen umgehen bzw.
auch nicht rechnen sollen."*

    Ein Modell, dem man Summand, Summand und Summe hinlegt, prueft nach
    statt zu urteilen - und rechnet dabei schlechter als jede Zeile Python.

DIE DREI FEHLERFORMEN, die dieses Werkzeug sucht:

    N1  RECHENAUFGABE   zwei Werte UND ihr Abstand/ihre Summe im selben Satz
    N2  UNGEDECKTE ZAHL eine Zahl ohne Fenster, Bezug oder Massstab (R-T1/R-T5)
    N3  OHNE EINORDNUNG ein Perzentil ohne Wort dazu, ob das viel ist

WARUM ALS SKRIPT UND NICHT ALS PAKETPRUEFUNG. Die Saetze entstehen erst aus
echten Daten - ein Blick in den Quelltext sieht die f-Strings, nicht das
Ergebnis. Genau daran ist der Sektor-Bezug am 16.08. vorbeigelaufen: im Code
richtig, im Rendern nie erreicht. Dieses Werkzeug rendert.

⚠️ ABGRENZUNG ZU `pruefe_fakten_bezugsgroessen.py` (Nutzerhinweis 16.08.:
*"pruefe ob du nicht bereits ein geeignetes Werkzeug gebaut hast"*). Es gibt
eines, vom 09.08., und es deckt N2 ab - aber auf einem ANDEREN Gegenstand:

    pruefe_fakten_bezugsgroessen.py   JSON-Faktendicts der alten Pipelines,
                                      Schluessel/Wert-Paare, sucht fehlende
                                      Bezugsgroessen je Feld
    diese Datei                       die gerenderten DEUTSCHEN SAETZE der
                                      Rollen A/BC/G, die es am 09.08. noch
                                      nicht gab (die Rollen kamen 10.-16.08.)

Ein Satz ist kein Feld: "OKX +0.0 %, Bybit -1.3 %, Spanne 1.3 Punkte" hat je
Zahl einen tadellosen Bezug und ist trotzdem eine Rechenaufgabe. Deshalb N1
und N3 hier - und deshalb KEIN dritter Scanner fuer Felder.

AUFRUF:
    python pruefe_zahlen_in_prompts.py --db <NB-Backup>
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# NUR FREISTEHENDE ZAHLEN. `(?<![A-Za-z0-9])` schliesst die Ziffern in
# Symbolnamen aus - sonst meldet "3QSS ist nicht im Bestand" eine nackte Zahl,
# und der erste Lauf am 16.08. tat genau das.
ZAHL = re.compile(r"(?<![A-Za-z0-9])-?\d+(?:[.,]\d+)?")

# Zahl MIT ihrer Einheit - fuer N1. Ohne Einheit vergleicht der Test Aepfel
# mit Birnen: im ersten Lauf galt "5 Tage -3.4 %, 20 Tage -8.4 %" als
# Rechenaufgabe, weil |5 - (-3.4)| = 8.4 ist. Ein Tageszaehler und ein Prozent
# duerfen nie in dieselbe Rechnung.
MIT_EINHEIT = re.compile(
    r"(?<![A-Za-z0-9])(-?\d+(?:[.,]\d+)?)\s*"
    r"(%|Prozentpunkte?|Punkte?|EUR|Schwankungsbreiten?|Tage[n]?|Stunden|"
    r"Handelstage[n]?|Perzentil|Messungen|Monate[n]?|Jahre[n]?|mal)")

# Woran ein Satz seinen Massstab traegt. Bewusst breit: ein falscher Alarm
# kostet einen Blick, ein uebersehener Fall kostet einen Prompt.
MASSSTAB = ("Perzentil", "Messungen", "Handelstag", "Tage", "Stunden",
            "Monat", "Jahr", "seit", "Fenster", "Durchschnitt", "Median",
            "Schwankungsbreite", "ATR", "seiner", "eigenen", "Historie",
            "hoeher", "tiefer", "ueber", "unter", "je ", "von ", "das sind",
            "Rahmen", "Bestand", "beruehrt", "Regime", "Hebel", "deckt")

# Woertliche Einordnung eines Perzentils - eines davon muss dabeistehen.
EINORDNUNG = ("gewohnt", "aussergewoehnlich", "ungewoehnlich", "auseinander",
              "beieinander", "extrem", "selten", "haeufig", "typisch")


def _zahlen(satz: str) -> list[float]:
    aus = []
    for t in ZAHL.findall(satz):
        try:
            aus.append(float(t.replace(",", ".")))
        except ValueError:
            pass
    return aus


def pruefe_satz(satz: str) -> list[str]:
    """Welche der drei Fehlerformen trifft auf diesen Satz zu?"""
    fund: list[str] = []
    zahlen = _zahlen(satz)

    # N1: ist eine Zahl die Differenz oder Summe zweier anderer?
    # NUR INNERHALB DERSELBEN EINHEIT. Prozentpunkte gelten dabei als Einheit
    # von Prozenten - genau das war der Entwurfsfehler vom 16.08.: "+0.0 %,
    # -1.3 %" und "Spanne 1.3 Prozentpunkte" im selben Block.
    je_einheit: dict[str, list[float]] = {}
    for roh, einheit in MIT_EINHEIT.findall(satz):
        e = einheit.rstrip("n").lower()
        e = "%" if e.startswith(("prozentpunkt", "punkt")) else e
        try:
            je_einheit.setdefault(e, []).append(float(roh.replace(",", ".")))
        except ValueError:
            pass
    for e, w in je_einheit.items():
        if len(w) < 3:
            continue
        for i, a in enumerate(w):
            for j, b in enumerate(w[i + 1:], i + 1):
                for k, cc in enumerate(w):
                    if k in (i, j) or cc == 0:
                        continue
                    if abs(abs(a - b) - abs(cc)) < 0.05 or abs(a + b - cc) < 0.05:
                        fund.append(
                            f"N1 Rechenaufgabe: {cc:g} ist der Abstand/die "
                            f"Summe von {a:g} und {b:g} (Einheit {e})")
                        return fund          # einer reicht als Befund

    # N2: Zahl ohne jeden Massstab im Satz.
    if zahlen and not any(w in satz for w in MASSSTAB):
        fund.append("N2 ungedeckte Zahl: kein Fenster, kein Bezug im Satz")

    # N3: Perzentil ohne Wort, ob das viel ist.
    if "Perzentil" in satz and not any(w in satz for w in EINORDNUNG):
        fund.append("N3 Perzentil ohne Einordnung - das Modell muss selbst "
                    "entscheiden, ob das viel ist")
    return fund


def _saetze_aller_rollen(conn) -> list[tuple[str, str, str]]:
    """(Rolle, Bezug, Satz) - aus ECHTEN Daten, nicht aus nachgebauten.

    DREI VERSCHIEDENE WEGE, und zwar mit Absicht:

        Rolle A   aus `lagebilder.fakten_json` - das ist der Wortlaut, der
                  in der Produktion wirklich am Modell lag. Ein Nachbau waere
                  eine zweite Definition (siehe `geteilt()`-Docstring).
        Rolle BC  gerendert, weil der Faktentext nirgends persistiert wird.
        Rolle G   gerendert, aus demselben Grund.

    ⚠️ `conn.row_factory = sqlite3.Row` IST PFLICHT fuer `get_ohlc_history` -
    sie baut `OhlcPoint(**dict(row))`. Ohne die Zeilenfabrik wirft sie, der
    breite Fang schluckt es, und Rolle BC waere hier stillschweigend leer.
    Genau dieser Fehler hat die Regime-Dauer tagelang gekostet."""
    import json

    from agent import positionierung
    from agent import lagebeschreibung as LB
    from database import db as DB

    raus: list[tuple[str, str, str]] = []
    conn.row_factory = sqlite3.Row

    # --- Rolle G ---
    for r in conn.execute(
            "SELECT DISTINCT symbol FROM open_interest_snapshot LIMIT 40"):
        sym = str(r[0])
        for s in positionierung.saetze(positionierung.lage(conn, sym)):
            raus.append(("G", sym, s))

    # --- Rolle A: der echte Produktionswortlaut ---
    try:
        for r in conn.execute(
                "SELECT fakten_json FROM lagebilder ORDER BY rowid DESC LIMIT 5"):
            roh = json.loads(r[0] or "{}")
            saetze_ = roh if isinstance(roh, list) else (
                roh.get("saetze") or roh.get("aussagen") or [])
            for s in saetze_:
                raus.append(("A", "Lagebild", str(s)))
    except Exception as exc:                              # noqa: BLE001
        print(f"  (Rolle A nicht lesbar: {exc})")

    # --- Rolle BC ---
    paare = conn.execute(
        "SELECT symbol, currency, COUNT(*) n FROM price_history_ohlc "
        "GROUP BY symbol, currency HAVING n >= 120 LIMIT 30").fetchall()
    for p in paare:
        sym, waehrung = str(p[0]), str(p[1])
        try:
            reihe = DB.get_ohlc_history(conn, sym, waehrung) or []
            if len(reihe) < 120:
                continue
            i = len(reihe) - 1
            schluss = [float(x.close) for x in reihe[-15:]]
            hoch = [float(x.high) for x in reihe[-15:]]
            tief = [float(x.low) for x in reihe[-15:]]
            # ATR nur als GROESSENORDNUNG fuer den Satzbau - dieses Werkzeug
            # prueft Formulierungen, nicht Kennzahlen. Die echte Rechnung steht
            # in `indicators`; sie hier zu wiederholen waere eine zweite Quelle.
            atr = sum(h - t for h, t in zip(hoch, tief)) / len(hoch)
            bl = LB.geteilt(symbol=sym, reihe=reihe, index=i,
                            kurs_eur=schluss[-1], atr=atr)
            for block, saetze_ in (bl or {}).items():
                for s in (saetze_ or []):
                    raus.append(("BC", f"{sym}/{block}", str(s)))
        except Exception as exc:                          # noqa: BLE001
            print(f"  (BC {sym}/{waehrung} nicht renderbar: {exc})")
    return raus


# --- SELBSTTEST -----------------------------------------------------------
#
# EIN PRUEFER OHNE PRUEFUNG IST EINE MEINUNG. Die erste Fassung dieser Datei
# meldete 33 Faelle, von denen 31 Fehlalarme waren - ein Tageszaehler gegen
# ein Prozent gerechnet, und die Ziffer in "3QSS". Beide Faelle stehen jetzt
# als Gegenprobe hier, zusammen mit dem Satz, fuer den das Werkzeug gebaut
# wurde.
#
# ERWARTUNG: die Marke, die anschlagen MUSS - oder None fuer "still bleiben".
SELBSTTEST = (
    # Der Entwurf vom 16.08., der den ganzen Anlass gab.
    ("Die Spanne betraegt 1.3 Prozentpunkte, auf OKX 0.0 Punkte, "
     "auf Bybit -1.3 Punkte.", "N1"),
    # Seine korrigierte Fassung - muss still bleiben.
    ("Die Boersen entwickeln sich dabei uneinheitlich: auf Bybit nehmen sie "
     "staerker ab als auf OKX.", None),
    # Fehlalarm 1: Tageszaehler gegen Prozent.
    ("Kursentwicklung im selben Rahmen: 5 Tage -3.4 %, 20 Tage -8.4 %, "
     "60 Tage -20.9 %.", None),
    # Fehlalarm 2: Ziffer im Symbolnamen.
    ("3QSS ist nicht im Bestand.", None),
    # N3 muss anschlagen ...
    ("66 % der Konten stehen long; das ist das 92. Perzentil der eigenen "
     "Historie.", "N3"),
    # ... und bei vorhandener Einordnung schweigen.
    ("Die Finanzierungsrate steht im 28. Perzentil der letzten 400 Messungen "
     "dieses Werts - im gewohnten Bereich.", None),
    # N2: eine Zahl voellig ohne Bezug.
    ("Der Wert liegt bei 3.2.", "N2"),
)


def selbsttest() -> int:
    fehler = 0
    for satz, erwartet in SELBSTTEST:
        marken = {f.split()[0] for f in pruefe_satz(satz)}
        ok = (erwartet in marken) if erwartet else (not marken)
        if not ok:
            fehler += 1
            print(f"  FEHLER erwartet={erwartet or 'still'} "
                  f"bekommen={sorted(marken) or 'still'}\n         {satz[:88]}")
    print(f"Selbsttest: {len(SELBSTTEST) - fehler}/{len(SELBSTTEST)} "
          f"{'BESTANDEN' if not fehler else 'FEHLGESCHLAGEN'}")
    return fehler


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db")
    p.add_argument("--selbsttest", action="store_true")
    a = p.parse_args()

    if a.selbsttest:
        return 1 if selbsttest() else 0
    if not a.db:
        p.error("--db oder --selbsttest angeben")
    if selbsttest():
        print("Selbsttest fehlgeschlagen - der Befund unten ist nicht belastbar.\n")

    conn = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    saetze = _saetze_aller_rollen(conn)
    print(f"{len(saetze)} Saetze aus echten Daten gerendert.\n")

    treffer: dict[str, list] = {}
    for rolle, bezug, satz in saetze:
        for f in pruefe_satz(satz):
            treffer.setdefault(f.split(":")[0], []).append((rolle, bezug, satz, f))

    if not treffer:
        print("KEIN BEFUND - kein Satz rechnet dem Modell etwas vor.")
        return 0

    for art in sorted(treffer):
        faelle = treffer[art]
        # Nach Satzform gruppieren, nicht je Symbol: derselbe f-String
        # erzeugt 40 gleiche Befunde und das liest niemand.
        formen: dict[str, tuple] = {}
        for rolle, bezug, satz, f in faelle:
            schluessel = (rolle, ZAHL.sub("#", satz))
            formen.setdefault(schluessel, (satz, f, 0))
            s0, f0, n = formen[schluessel]
            formen[schluessel] = (s0, f0, n + 1)
        print(f"=== {art} - {len(faelle)} Saetze, {len(formen)} Satzformen ===")
        for (rolle, _), (satz, f, n) in sorted(formen.items(),
                                               key=lambda x: -x[1][2]):
            print(f"  [{rolle}] {n:>3}x  {satz[:104]}")
            print(f"        -> {f}")
        print()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
