"""Stufe 0 des Plans: was aendert sich, wenn der Hebel anfaellt statt gewaehlt
zu werden? (18.08.2026, Umbauplan Kapitel 88 Fassung 2)

KEIN EINGRIFF. Dieses Werkzeug misst nur - `rechne()` bleibt unberuehrt.

ZWEI ACHSEN, NICHT EINE. Die Erstfassung des Plans nahm an, es gebe genau
einen freien Parameter (den ATR-Faktor k). Tatsaechlich gilt

    Hebel = Verlustanteil / Stopabstand   ->   Hebel > 1 <=> Stop < Verlustanteil

also ist die Spot/Hebel-Grenze der VERLUSTANTEIL. Beide Achsen werden
gemessen.

WAS HIER NICHT GEMESSEN WIRD, ist ob die Trades besser laufen. Das waere eine
Prognose, und dieses Projekt hat achtmal gemessen, dass kein Verfahren die
Basisrate schlaegt. Gemessen wird, was RECHENBAR ist:

    Stopbreite -> Rauschtreffer -> Hebel -> Etikett -> noetiger Vorsprung

DATENQUELLE ist das taegliche Notebook-Backup aus dem Austauschordner, NICHT
die Desktop-Datenbank - die endet am 19.07.2026.

    python messe_dimensionierung.py [--db PFAD] [--schnell]
"""
from __future__ import annotations

import argparse
import glob
import gzip
import os
import shutil
import statistics as st
import sys

import numpy as np

from agent import entscheidungsrechnung as ER
from agent.schreibweise import de

# Die Felder der Messung. k ist der ATR-Faktor des Rauschbodens, der
# Verlustanteil die Spot/Hebel-Grenze. 0,15 ist der heutige Wert, 0,01 und
# 0,02 sind die Literaturwerte (Nutzervorgabe 18.08.).
K_WERTE = (0.75, 1.0, 1.5, 2.0, 2.5)
VERLUSTANTEILE = (0.01, 0.02, 0.05, 0.10, 0.15)
HEUTE_K, HEUTE_VA = 0.75, 0.15          # der Ist-Zustand als Bezugspunkt
EINSATZ_EUR = 1000.0
MINDEST_EUR = 25.0
KOSTEN = 0.03                            # Ein- und Ausstieg, auf den Einsatz


def _neuestes_backup() -> str | None:
    """Das juengste Notebook-Backup, ausgepackt in den Scratchpad.

    ⚠️ DER LAUFWERKSBUCHSTABE WIRD NIE GERATEN - er kommt aus
    `extract_notebook_diagnose._google_drive_wurzel()`, der einen Stelle, die
    ihn kennt."""
    try:
        from extract_notebook_diagnose import _google_drive_wurzel
        ordner = os.path.join(str(_google_drive_wurzel()),
                              "Claude_Austauschordner", "DB_Backups")
        treffer = sorted(glob.glob(os.path.join(ordner, "*.db.gz")))
    except Exception as exc:                                 # noqa: BLE001
        print(f"  Austauschordner nicht lesbar ({exc})")
        return None
    if not treffer:
        return None
    ziel = os.path.join(os.environ.get("TEMP", "."), "nb_dimension.db")
    if not os.path.exists(ziel) or os.path.getmtime(ziel) < os.path.getmtime(treffer[-1]):
        with gzip.open(treffer[-1], "rb") as q, open(ziel, "wb") as z:
            shutil.copyfileobj(q, z)
    print(f"  Backup: {os.path.basename(treffer[-1])}")
    return ziel


def _atr_reihe(h, l, c, fenster: int = 14) -> np.ndarray:
    tr = np.maximum(h[1:] - l[1:],
                    np.maximum(abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1])))
    return np.array([tr[max(0, i - fenster + 1):i + 1].mean()
                     for i in range(fenster - 1, len(tr))])


def _reihen(db: str, schnell: bool) -> dict:
    from backtest_llm1_historisch import lade_reihen_aus_db

    aus = {}
    for s, kerzen in lade_reihen_aus_db(db).items():
        if len(kerzen) < 200:
            continue
        c = np.array([float(x.close) for x in kerzen])
        h = np.array([float(x.high) for x in kerzen])
        l = np.array([float(x.low) for x in kerzen])
        if schnell:
            c, h, l = c[-500:], h[-500:], l[-500:]
        a = _atr_reihe(h, l, c)
        if len(a) < 130:
            continue
        aus[s] = (c, h, l, a, len(c) - len(a))
    return aus


def _etikett(kurs, atr, k, va, handelbar=True):
    """Nur das Etikett - ohne den vollen Aufbau, fuer die Sprungzaehlung."""
    try:
        d = ER.dimensioniere(kurs=kurs, atr=atr, k=k, verlustanteil=va,
                             einsatz_eur=EINSATZ_EUR,
                             hebel_handelbar=handelbar)
    except ER.RechnungBlockiert:
        return None
    return d["etikett"]


def feld(reihen: dict) -> None:
    """Achse 1 x Achse 2: was wird woraus."""
    print("=" * 78)
    print("A) DAS FELD - Anteil Hebel je (k, Verlustanteil), Stand des letzten Tages")
    print("=" * 78)
    kopf = "  k \\ VA " + "".join(f"{100*v:8.0f} %" for v in VERLUSTANTEILE)
    print(kopf)
    print("  " + "-" * (len(kopf) - 2))
    for k in K_WERTE:
        zeile = f"  {k:5.2f}  "
        for va in VERLUSTANTEILE:
            n = h = 0
            for s, (c, hh, ll, a, off) in reihen.items():
                e = _etikett(float(c[-1]), float(a[-1]), k, va)
                if e is None:
                    continue
                n += 1
                h += (e == "hebel")
            zeile += f"{100*h/n:7.0f} %" if n else "      - "
        print(zeile + ("   <- heute" if k == HEUTE_K else ""))
    print(f"\n  Ist-Zustand: k = {de(HEUTE_K,2)} (Klemme 0,75 ATR), "
          f"Verlustanteil = {de(100*HEUTE_VA,0)} %")


def spruenge(reihen: dict) -> None:
    """Achse: wie oft wechselt das Etikett? Das entscheidet ueber Hysterese."""
    print("\n" + "=" * 78)
    print("B) SPRUNGRATE - wie oft wechselt ein Asset das Etikett?")
    print("=" * 78)
    print("  (Wechsel je 100 Handelstage; hohe Werte verlangen eine Hysterese)")
    print(f"\n  k \\ VA " + "".join(f"{100*v:8.0f} %" for v in VERLUSTANTEILE))
    print("  " + "-" * 46)
    for k in K_WERTE:
        zeile = f"  {k:5.2f} "
        for va in VERLUSTANTEILE:
            raten = []
            for s, (c, hh, ll, a, off) in reihen.items():
                et = [_etikett(float(c[off + i]), float(a[i]), k, va)
                      for i in range(0, len(a), 1)]
                et = [x for x in et if x]
                if len(et) < 50:
                    continue
                wechsel = sum(1 for i in range(1, len(et)) if et[i] != et[i - 1])
                raten.append(100.0 * wechsel / (len(et) - 1))
            zeile += f"{st.median(raten):7.1f} " if raten else "      - "
        print(zeile + ("  <- heute" if k == HEUTE_K else ""))


def rauschen(reihen: dict) -> None:
    """Wie oft trifft das blosse Rauschen einen Stop dieser Breite?"""
    print("\n" + "=" * 78)
    print("C) RAUSCHTREFFER - der Stop wird getroffen, bevor die These zaehlt")
    print("=" * 78)
    for horizont in (5, 20):
        treffer = {k: 0 for k in K_WERTE}
        n = 0
        for s, (c, hh, ll, a, off) in reihen.items():
            for i in range(len(a) - horizont - 1):
                atr, einstieg = a[i], c[off + i]
                if atr <= 0 or einstieg <= 0:
                    continue
                tief = ll[off + i + 1: off + i + 1 + horizont].min()
                n += 1
                for k in K_WERTE:
                    if tief <= einstieg - k * atr:
                        treffer[k] += 1
        print(f"\n  Horizont {horizont} Handelstage - {n:,} Anker")
        for k in K_WERTE:
            print(f"    {de(k,2):>5} ATR   {de(100*treffer[k]/n,1):>5} %"
                  + ("   <- heute" if k == HEUTE_K else ""))


def kostenbild(reihen: dict) -> None:
    """Der noetige Vorsprung vor dem Zufall - und der Vergleich zu heute."""
    print("\n" + "=" * 78)
    print("D) WAS WIRD BESSER, WAS SCHLECHTER")
    print("=" * 78)
    basis = 1.0 / (1.0 + ER.GRENZEN["crv"])
    print(f"  Basisrate auf driftfreiem Pfad: {de(100*basis,1)} %   "
          f"(CRV {de(ER.GRENZEN['crv'],1)}, Kosten {de(100*KOSTEN,0)} %)\n")
    print(f"  {'k':>5} {'VA':>6} {'Stop':>7} {'Tage':>6} {'Hebel':>7} "
          f"{'Betrag':>8} {'zu klein':>9} {'Vorsprung':>11}")
    print("  " + "-" * 70)
    zeilen = []
    for k in K_WERTE:
        for va in VERLUSTANTEILE:
            stops, tage, hebel, betraege, klein = [], [], [], [], 0
            for s, (c, hh, ll, a, off) in reihen.items():
                try:
                    d = ER.dimensioniere(kurs=float(c[-1]), atr=float(a[-1]),
                                         k=k, verlustanteil=va,
                                         einsatz_eur=EINSATZ_EUR,
                                         mindestgroesse_eur=MINDEST_EUR)
                except ER.RechnungBlockiert:
                    continue
                stops.append(d["stop_rel"]); tage.append(d["tage"])
                hebel.append(d["hebel"]); betraege.append(d["betrag_eur"])
                klein += d["unter_mindestgroesse"]
            if not stops:
                continue
            ms = st.median(stops)
            vorsprung = (KOSTEN / ms) / (1.0 + ER.GRENZEN["crv"])
            zeilen.append((k, va, ms, st.median(tage), st.median(hebel),
                           st.median(betraege), klein, vorsprung))
    for k, va, ms, tg, hb, bt, kl, vs in zeilen:
        mark = "   <- HEUTE" if (k == HEUTE_K and va == HEUTE_VA) else ""
        print(f"  {de(k,2):>5} {de(100*va,0):>5} % {de(100*ms,1):>6} % "
              f"{tg:6.0f} {de(hb,2):>7} {bt:8.0f} {kl:9d} "
              f"{de(100*vs,1):>9} pp{mark}")
    heute = [z for z in zeilen if z[0] == HEUTE_K and z[1] == HEUTE_VA]
    if heute:
        h = heute[0]
        print(f"\n  BEZUGSPUNKT HEUTE: Stop {de(100*h[2],1)} %, Hebel {de(h[4],2)}, "
              f"Vorsprung {de(100*h[7],1)} pp")
        besser = [z for z in zeilen if z[7] < h[7] * 0.5]
        print(f"  Felder mit weniger als der HAELFTE des heutigen Vorsprungs: "
              f"{len(besser)} von {len(zeilen)}")
        if besser:
            b = min(besser, key=lambda z: z[7])
            print(f"    bestes: k = {de(b[0],2)}, VA = {de(100*b[1],0)} %  ->  "
                  f"Stop {de(100*b[2],1)} %, Hebel {de(b[4],2)}, "
                  f"Vorsprung {de(100*b[7],1)} pp, {b[6]} unter Mindestgroesse")
        print("\n  ⚠️ WAS DIESE SPALTE NICHT SAGT: dass die Trades besser laufen.")
        print("     Sie sagt, wie viel Treffsicherheit UEBER dem Zufall noetig")
        print("     waere, damit sie sich tragen. Kleiner ist leichter, nicht gut.")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db", default=None)
    p.add_argument("--schnell", action="store_true",
                   help="nur die letzten 500 Kerzen je Symbol")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("STUFE 0 - DIMENSIONIERUNG GEMESSEN, NICHTS GEAENDERT")
    print("=" * 78)
    db = a.db or _neuestes_backup() or "data/tradinginfotool.db"
    reihen = _reihen(db, a.schnell)
    print(f"  {len(reihen)} Symbole mit ausreichender Reihe\n")
    if not reihen:
        print("  keine Daten")
        return 1
    feld(reihen)
    spruenge(reihen)
    rauschen(reihen)
    kostenbild(reihen)
    print("\n" + "=" * 78)
    print("ENDE - `rechne()` ist unveraendert, es wurde nichts gehandelt")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
