"""Ist die Terminmarkt-Positionierung ein EIGENER Kanal? (25.08.2026)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

WARUM NICHT GLEICH DIE WIRKUNG GEMESSEN WIRD. Die Datenlage laesst es nicht
zu, und das ist gerechnet, nicht vermutet:

    OI-Historie  184.584 Zeilen, 39 Symbole, 4 Boersen
                 aber nur 37 Tage: 2026-07-14 bis 2026-08-24

    Anker mit aufgeloestem Ausgang, je Horizont:
        5 HT   1.053   duenn
       10 HT     936   duenn
       20 HT     390   zu wenig
       60 HT       0
      120 HT       0   <- der Betriebshorizont

Und alle Anker liegen in EINEM 41-Tage-Fenster: eine Marktphase, keine
Blockstruktur, keine Zeitteilung. Eine Wirkungsmessung waere hier nicht
"duenn", sie waere nicht interpretierbar.

WAS STATTDESSEN HEUTE GEHT - und vor jeder Sammelzeit stehen muss.

Das Projekt hat eine teure Lektion: DER ATR-KANAL TRAT FUENFMAL UNTER NEUEM
NAMEN AUF (Kap. 100 Marktphase, 101 Geometrie, 102/113 Drift, 111
Hochabstand, 116 Liquiditaet). Jedes Mal sah es nach einem neuen Merkmal aus,
und jedes Mal war es dieselbe Groesse: hoher ATR -> weiter Stop in Prozent ->
niedrigere Kostenhuerde. Wer das nicht vorher prueft, sammelt Monate und
misst am Ende die Volatilitaet.

DIE FRAGE IST DESHALB: Traegt die Positionierung Information, die NICHT
schon in der Kursreihe steht? Das ist mit 37 Tagen beantwortbar, denn es ist
eine Frage ueber die Groessen selbst, nicht ueber ihre Wirkung.

GEPRUEFT WERDEN VIER POSITIONIERUNGSGROESSEN:

    oi_aenderung        Tagesaenderung des Open Interest (Binance)
    oi_divergenz        Spannweite der Tagesaenderung ueber die Boersen
                        - die Groesse, die es NUR bei mehreren Boersen gibt
    funding_rate        Finanzierungssatz
    long_anteil         Anteil Long-Konten

GEGEN DREI KURSGROESSEN, die den ATR-Kanal aufspannen:

    atr_relativ         Schwankungsbreite in Prozent des Kurses
    umsatz_rel          Tagesumsatz zum eigenen 20-Tage-Mittel
    rendite             Tagesrendite

VORAB FESTGELEGT, WAS WELCHES ERGEBNIS BEDEUTET:

    |rho| < 0,3 zu ALLEN drei Kursgroessen
        -> EIGENER KANAL. Die Groesse traegt Information, die in der
           Kursreihe nicht steht. Sammeln lohnt.
    0,3 <= |rho| < 0,6 zur staerksten Kursgroesse
        -> TEILWEISE ueberlappend. Sammeln lohnt, aber die Wirkungsmessung
           muss spaeter GEGEN diese Kursgroesse bereinigt werden.
    |rho| >= 0,6
        -> ⚠️ DER ATR-KANAL ZUM SECHSTEN MAL. Kandidat vor der Sammelzeit
           erledigt.

    Zusaetzlich, nicht als Ausschluss: variiert die Groesse ueberhaupt?
    Eine Groesse mit Median-Tagesaenderung nahe null kann nichts trennen
    (der Fehler von `regime` und `optionsmarkt_skew`, die ueber 1.022 Faelle
    konstant waren).

⚠️ WAS DIESE PRUEFUNG NICHT KANN. Sie sagt NICHTS darueber, ob die
Positionierung den Ausgang vorhersagt. Ein eigener Kanal zu sein ist die
VORBEDINGUNG dafuer, nicht der Nachweis. Wer aus einem niedrigen rho eine
Handelsregel ableitet, hat nichts gemessen.

    python pruefe_positionierung_kanal.py
"""
from __future__ import annotations

import argparse
import io
import json
import sqlite3
import sys
from collections import defaultdict

import numpy as np

EXPORT = (r"K:/My Drive/Claude_Austauschordner/Notebook_Analysedaten"
          r"/notebook_diagnose.json")
LEIT_BOERSE = "binance"
MIN_PAARE = 100          # unter dieser Zahl wird kein rho berichtet


def _tagesreihen(h: list) -> dict:
    """Je (Symbol, Tag): letzter Messwert je Boerse."""
    letzt: dict = {}
    for x in h:
        tag = x["fetched_at"][:10]
        k = (x["symbol"], tag, x["exchange"])
        if k not in letzt or x["fetched_at"] > letzt[k]["fetched_at"]:
            letzt[k] = x
    je: dict = defaultdict(dict)
    for (sym, tag, boerse), x in letzt.items():
        je[(sym, tag)][boerse] = x
    return je


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", default=EXPORT)
    ap.add_argument("--db", default="data/messdaten.db")
    ap.add_argument("--datei", default="messwerte_positionierung_kanal.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("IST DIE TERMINMARKT-POSITIONIERUNG EIN EIGENER KANAL?")
    print("=" * 78)
    h = json.load(io.open(a.export, encoding="utf-8"))
    h = h["rohdaten_fuer_backtest"]["oi_historie"]
    je = _tagesreihen(h)
    syms = sorted({s for s, _t in je})
    print(f"  {len(h)} Rohzeilen -> {len(je)} (Symbol, Tag)-Punkte, "
          f"{len(syms)} Symbole")

    # ---- Kursgroessen aus der Messdatenbank --------------------------
    c = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    kurs: dict = {}
    for sym in syms:
        r = c.execute("select date, high, low, close, volume "
                      "from price_history_ohlc where symbol=? "
                      "and currency in ('USD','EUR') and close is not null "
                      "order by date", (sym,)).fetchall()
        if len(r) < 30:
            continue
        d = [x[0][:10] for x in r]
        hi = np.array([float(x[1]) for x in r])
        lo = np.array([float(x[2]) for x in r])
        cl = np.array([float(x[3]) for x in r])
        vo = np.array([float(x[4] or 0) for x in r])
        spanne = hi - lo
        atr = np.array([spanne[max(0, i - 13):i + 1].mean()
                        for i in range(len(cl))])
        um20 = np.array([vo[max(0, i - 19):i + 1].mean()
                         for i in range(len(vo))])
        kurs[sym] = {t: {"atr_relativ": float(atr[i] / cl[i]) if cl[i] else None,
                         "umsatz_rel": (float(vo[i] / um20[i])
                                        if um20[i] else None),
                         "rendite": (float(cl[i] / cl[i - 1] - 1.0)
                                     if i else None)}
                     for i, t in enumerate(d)}
    print(f"  Kursreihen geladen: {len(kurs)} von {len(syms)} Symbolen")

    # ---- Positionierungsgroessen je (Symbol, Tag) --------------------
    reihen: dict = defaultdict(list)
    fehlt = defaultdict(int)
    for sym in syms:
        tage = sorted(t for s, t in je if s == sym)
        for i, t in enumerate(tage):
            b = je[(sym, t)]
            if LEIT_BOERSE not in b:
                fehlt["ohne_leitboerse"] += 1
                continue
            k = kurs.get(sym, {}).get(t)
            if not k or k["atr_relativ"] is None:
                fehlt["ohne_kurs"] += 1
                continue
            satz = {"funding_rate": b[LEIT_BOERSE].get("funding_rate"),
                    "long_anteil": b[LEIT_BOERSE].get("long_account_pct")}
            # Tagesaenderung je Boerse - braucht den Vortag
            if i:
                vor = je.get((sym, tage[i - 1]), {})
                aend = {}
                for bo, x in b.items():
                    v = vor.get(bo)
                    if v and v.get("open_interest") and x.get("open_interest"):
                        aend[bo] = x["open_interest"] / v["open_interest"] - 1.0
                if LEIT_BOERSE in aend:
                    satz["oi_aenderung"] = aend[LEIT_BOERSE]
                if len(aend) >= 2:
                    satz["oi_divergenz"] = max(aend.values()) - min(aend.values())
            satz.update(k)
            reihen[sym].append(satz)

    alle = [s for v in reihen.values() for s in v]
    print(f"  auswertbare Punkte: {len(alle)}   "
          f"(verworfen: {dict(fehlt)})")

    # ---- Variiert die Groesse ueberhaupt? ----------------------------
    POS = ("oi_aenderung", "oi_divergenz", "funding_rate", "long_anteil")
    KURSG = ("atr_relativ", "umsatz_rel", "rendite")
    print("\n" + "-" * 78)
    print("VARIIERT DIE GROESSE? (eine konstante Groesse traegt nichts)")
    print("-" * 78)
    print(f"  {'Groesse':16}{'n':>7}{'Median':>12}{'10 %':>12}{'90 %':>12}")
    streu = {}
    for p in POS:
        w = np.array([s[p] for s in alle if s.get(p) is not None], float)
        if len(w) < MIN_PAARE:
            print(f"  {p:16}{len(w):>7}   zu wenige Werte")
            continue
        streu[p] = {"n": len(w), "median": float(np.median(w)),
                    "p10": float(np.quantile(w, 0.1)),
                    "p90": float(np.quantile(w, 0.9))}
        print(f"  {p:16}{len(w):>7}{np.median(w):>12.5f}"
              f"{np.quantile(w, 0.1):>12.5f}{np.quantile(w, 0.9):>12.5f}")

    # ---- Die Kernfrage: Korrelation zu den Kursgroessen ---------------
    print("\n" + "-" * 78)
    print("RANGKORRELATION zu den Kursgroessen (Spearman)")
    print("-" * 78)
    print(f"  {'Groesse':16}" + "".join(f"{g:>14}" for g in KURSG)
          + f"{'max |rho|':>12}  Urteil")

    def rho(x, y):
        x, y = np.asarray(x, float), np.asarray(y, float)
        rx = np.argsort(np.argsort(x)).astype(float)
        ry = np.argsort(np.argsort(y)).astype(float)
        rx -= rx.mean(); ry -= ry.mean()
        n = float(np.sqrt((rx ** 2).sum() * (ry ** 2).sum()))
        return float((rx * ry).sum() / n) if n else float("nan")

    erg = {}
    for p in POS:
        zeile, werte = f"  {p:16}", {}
        for g in KURSG:
            paare = [(s[p], s[g]) for s in alle
                     if s.get(p) is not None and s.get(g) is not None]
            if len(paare) < MIN_PAARE:
                zeile += f"{'zu wenig':>14}"
                continue
            r = rho([x for x, _ in paare], [y for _, y in paare])
            werte[g] = r
            zeile += f"{r:>+14.3f}"
        if not werte:
            print(zeile + f"{'':>12}  nicht auswertbar")
            continue
        mx = max(abs(v) for v in werte.values())
        urteil = ("EIGENER KANAL" if mx < 0.3
                  else "teilweise ueberlappend" if mx < 0.6
                  else "⚠️ ATR-KANAL, erledigt")
        erg[p] = {"rho": werte, "max_abs": mx, "urteil": urteil,
                  "n": len(alle)}
        print(zeile + f"{mx:>12.3f}  {urteil}")

    print("\n" + "=" * 78)
    print("LESART - vorab festgelegt")
    print("=" * 78)
    print("  Diese Pruefung sagt NICHTS ueber Wirkung. Ein eigener Kanal zu")
    print("  sein ist die VORBEDINGUNG dafuer, nicht der Nachweis.")
    eigen = [p for p, v in erg.items() if v["urteil"] == "EIGENER KANAL"]
    if eigen:
        print(f"\n  Eigenstaendig: {', '.join(eigen)}")
        print("  -> fuer diese lohnt die Sammelzeit bis zur Wirkungsmessung.")
    tot = [p for p, v in erg.items() if v["urteil"].startswith("⚠️")]
    if tot:
        print(f"\n  ⚠️ Vor der Sammelzeit erledigt: {', '.join(tot)}")

    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps(
            {"punkte": len(alle), "symbole": len(syms),
             "streuung": streu, "korrelationen": erg},
            ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
