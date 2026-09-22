# -*- coding: utf-8 -*-
"""WAS BEDEUTET DIE NAEHERUNG IM BETRIEB? - Spot und Hebel simuliert.

⚠️⚠️ NUTZERAUFTRAG 21.09.2026: *„simulieren was das für das System
bedeutet im Betrieb - Spot und Hebel"*. Vorher war gemessen, DASS die
Groesse traegt - nicht, was sie an der Kette aendert.

## Was simuliert wird

Fuer jedes echte Einstiegssignal der Notebook-Sicherung:

    HEUTE   `turnover_fuenftel` aus `umschlag_gesamt` (59 Symbole),
            Stufen (+3,15 / +0,83 / +0,22 / -1,79 / -2,40)
    NEU     aus `umschlag_naeherung` (366 Symbole), Stufen auf dem
            Fenster ab 2023 gerechnet

Daraus: Quote, Potential, Schwelle je Datenlage - mit dem ECHTEN Code
(`wahrscheinlichkeit.rechne`, `Potential.schwelle`), keine Nachbildung.

## ⚠️⚠️ WAS DIESE SIMULATION NICHT KANN

Sie rechnet den Rang je Signal aus der HISTORIE nach, nicht aus dem
Zustand, den der Betrieb an jenem Tag sah. Fuer Signale, deren Tag in
der Messbasis fehlt, gibt es keinen Rang - sie zaehlen als
*ohne Wert*, genau wie heute.

⚠️ Und sie sagt NICHT, ob die Signale besser waeren. Sie sagt, WELCHE
entstuenden und mit welchem Hebel. Ob das besser ist, beantwortet die
Wirkungsmessung (2.515, 2.516), nicht diese Rechnung.

⚠️ NUR LESEND.
"""
import os
import sqlite3
import sys
import time
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir("D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")
sys.path.insert(0, "D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")

import numpy as np                                          # noqa: E402

import agent.betraege as BE                                 # noqa: E402
import agent.marktrang as MR                                # noqa: E402
import agent.potential as P                                 # noqa: E402
import agent.wahrscheinlichkeit as WK                       # noqa: E402
import messe_bewertungskennzahl as MB                       # noqa: E402
import messe_eigenschaft_beitrag as B                       # noqa: E402
import messe_kandidaten_als_regel as K                      # noqa: E402
import phase4_c_kalibrierung_freefloat as KF                # noqa: E402
import phase4_c_naeherung_konstante_menge as NK             # noqa: E402

CRV = 2.0
# ⚠️ Die NEUE Tabelle, gerechnet auf demselben Fenster wie die Wirkung
# (`rechne_turnover_beitrag --horizont 20 --umschlag naeherung
#   --ab 2023-01-01`). NICHT hier neu gerechnet - abgeschrieben, damit
# beide Seiten dieselbe Zahl benutzen.
NEU_H20 = (2.32, 0.50, 0.34, -0.11, -3.06)
NEU_H5 = (0.76, 0.25, 0.25, -0.02, -1.24)


def _arg(a, f, v):
    return a[a.index(f) + 1] if f in a else v


def raenge_je_tag(reihen, menge, horizont, ab):
    """Das Fuenftel je Symbol und Tag - OHNE Vorwaertshorizont.

    ⚠️⚠️ WARUM OHNE (21.09.2026, gefundener Fehler der ersten Fassung).
    Die erste Fassung baute die Raenge ueber `K.baue(..., horizont=H)`.
    Das ist richtig fuer eine MESSUNG - ein Anker braucht sein Ergebnis,
    und darum enden die Anker rund einen Monat vor dem Datenende (bei
    H20 am 31.08., bei H5 am 15.09.).

    DER BETRIEB BRAUCHT DAS NICHT: `marktrang` rangt den HEUTIGEN
    Umschlag im Querschnitt - kein Blick nach vorn. Die erste Fassung
    meldete deshalb 780 Signale mit Wert statt 1.605 und ALLE 16
    Hebelsignale ohne Wert, obwohl sie im Betrieb einen haetten.

    ⚠️ Der Rang entsteht hier genau wie dort: Volumen durch (Preis mal
    Menge), Querschnitt je Kalendertag, Mindestbesetzung 12.
    """
    aus = {}
    je_tag = {}
    for sym, zeilen in reihen.items():
        m = menge.get(sym)
        if not m:
            continue
        for tag, close, _h, _l, vol in zeilen:
            t = str(tag)[:10]
            if t < ab or not vol or not close or close <= 0:
                continue
            mg = m.get(t)
            if not mg or mg <= 0:
                continue
            je_tag.setdefault(t, []).append((sym, float(vol) /
                                             (float(close) * float(mg))))
    for tag, z in je_tag.items():
        n = len(z)
        if n < 12:
            continue
        z.sort(key=lambda x: x[1])
        aus[tag] = {s: min(int(i / n * 5), 4) for i, (s, _v) in enumerate(z)}
    return aus


def bewerte(fu, tu, stufen, stop, kapital):
    """Quote, Potential, Schwelle und Hebel - mit dem ECHTEN Code."""
    m = {"funding_fuenftel": fu}
    if tu is not None:
        m["turnover_fuenftel"] = tu
    # ⚠️⚠️ `Beitrag` ist ein FROZEN dataclass - die Registrierung ist
    # gegen Zuweisung geschuetzt, und das ist richtig so. Fuer die
    # Simulation wird deshalb eine KOPIE der Beitragsliste gebaut
    # (`dataclasses.replace`), nicht das Original veraendert. So kann
    # kein Lauf die laufende Tabelle beschaedigen.
    import dataclasses as _dc
    alt_liste = WK.BEITRAEGE
    try:
        if stufen is not None:
            WK.BEITRAEGE = [
                _dc.replace(x, stufen=tuple(stufen))
                if x.merkmal == "turnover_fuenftel" else x
                for x in alt_liste]
        d = WK.rechne(crv=CRV, stop_relativ=stop, gebuehr_je_seite=0.0,
                      klasse="krypto", strategie="einstieg",
                      instrument="spot", richtung="long", merkmale=m)
    finally:
        WK.BEITRAEGE = alt_liste
    q = d["quote"]
    pot = P.Potential(wert_r=q * CRV - (1.0 - q), quote=q,
                      basisrate=d["basisrate"], crv=CRV,
                      zuschlag_punkte=d["zuschlag_punkte"],
                      instrument="spot", strategie="einstieg",
                      beitraege=d["beitraege"], klasse="krypto")
    h = BE.hebelrechnung(quote=q, crv=CRV, kapital_eur=kapital,
                         stop_rel=stop)
    return pot, h


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    db = _arg(args, "--db", "")
    if not db or not os.path.exists(db):
        raise SystemExit("Sicherung nicht gefunden - mit --db setzen "
                         "(NIE die Standard-DB)")
    H = int(_arg(args, "--horizont", "20"))
    stufen_neu = NEU_H20 if H == 20 else NEU_H5
    kapital = float(_arg(args, "--kapital", "17987"))
    t0 = time.time()

    print("=" * 106)
    print("BETRIEBSSIMULATION - was aendert `umschlag_naeherung` an der "
          "Kette? (H%d)" % H)
    print("=" * 106)
    _b = next(x for x in WK.BEITRAEGE if x.merkmal == "turnover_fuenftel")
    print("  HEUTE  %s   aus `umschlag_gesamt`" % (_b.stufen,))
    print("  NEU    %s   aus `umschlag_naeherung`, Fenster ab %s"
          % (stufen_neu, NK.AB))
    print()

    reihen = B.lade()
    heute_m, _r = NK.mengen_heute()
    umst = NK.umstellungen(reihen)
    naeh = {}
    for s, m in heute_m.items():
        if s in umst:
            continue
        z = reihen.get(s)
        if z:
            naeh[s] = {str(x[0])[:10]: m for x in z}
    echt = MB.reihe("data/onchain_historie.db", "splycur")

    r_neu = raenge_je_tag(reihen, naeh, H, NK.AB)
    r_alt = raenge_je_tag(reihen, echt, H, NK.AB)
    print("  Raenge gebaut: %d Tage (neu), %d Tage (alt)"
          % (len(r_neu), len(r_alt)))

    c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    zeilen = list(c.execute(
        "SELECT symbol, substr(created_at,1,10), COALESCE(instrument,'-'), "
        "       hebel, position_size_eur, verlust_am_stop_eur "
        "  FROM signals WHERE strategie='einstieg' ORDER BY created_at"))
    print("  %d Einstiegssignale" % len(zeilen))
    print()

    # ⚠️⚠️ DAS ECHTE funding-FUENFTEL, nicht ein angenommenes.
    # Der erste Lauf setzte es auf 2 (mittleres) und meldete daraufhin
    # "NEU: 0 Signale kommen durch" - das war ein Artefakt der Annahme:
    # mit funding 2 (+0,12 Punkte) reicht die neue Tabelle nicht ueber
    # die Schwelle, mit funding 1 (+1,30) sehr wohl. Eine Simulation,
    # deren Ergebnis an einer Annahme haengt, misst die Annahme.
    import messe_funding_niveau as _F
    _fund = _F.lade_funding()
    _fr = {}
    for _t in set(list(r_neu) + list(r_alt)):
        _w = [(_s, _d[_t]) for _s, _d in _fund.items() if _t in _d]
        if len(_w) < 12:
            continue
        _w.sort(key=lambda x: x[1])
        _n = len(_w)
        _fr[_t] = {_s: min(int(_i / _n * 5), 4)
                   for _i, (_s, _v) in enumerate(_w)}
    print("  funding-Raenge gebaut: %d Tage" % len(_fr))
    FU_VORGABE = 2          # nur noch Rueckfall, wenn kein Rang da ist
    z_alt = Counter()
    z_neu = Counter()
    hebel_alt, hebel_neu = [], []
    durch_alt = durch_neu = ohne_fund = 0
    for sym, tag, inst, heb, pos, verl in zeilen:
        s = str(sym).upper()
        stop = (verl / (pos * heb)) if (heb and pos and verl) else 0.08
        stop = min(max(stop, 0.02), 0.25)
        ta = r_alt.get(tag, {}).get(s)
        tn = r_neu.get(tag, {}).get(s)
        fu = _fr.get(tag, {}).get(s)
        if fu is None:
            fu = FU_VORGABE
            ohne_fund += 1
        z_alt["mit" if ta is not None else "ohne"] += 1
        z_neu["mit" if tn is not None else "ohne"] += 1
        pa, ha = bewerte(fu, ta, None, stop, kapital)
        pn, hn = bewerte(fu, tn, stufen_neu, stop, kapital)
        durch_alt += pa.wert_r >= pa.schwelle
        durch_neu += pn.wert_r >= pn.schwelle
        if inst == "hebel":
            hebel_alt.append(ha.get("hebel") or 0.0)
            hebel_neu.append(hn.get("hebel") or 0.0)

    n = len(zeilen)
    print("  %-34s %10s %10s" % ("", "HEUTE", "NEU"))
    print("  " + "-" * 58)
    print("  %-34s %9d %10d" % ("Signale mit turnover-Wert",
                                z_alt["mit"], z_neu["mit"]))
    print("  %-34s %8.1f %% %9.1f %%"
          % ("  Anteil", 100.0 * z_alt["mit"] / n, 100.0 * z_neu["mit"] / n))
    print("  %-34s %9d %10d"
          % ("auf GESENKTER Schwelle", z_alt["ohne"], z_neu["ohne"]))
    print("  %-34s %9d %10d" % ("erreichen die Schwelle", durch_alt,
                                durch_neu))
    print("  %-34s %8.1f %% %9.1f %%"
          % ("  Durchlass", 100.0 * durch_alt / n, 100.0 * durch_neu / n))
    print("  " + "-" * 58)
    if hebel_alt:
        import statistics as st
        ja_a = [x for x in hebel_alt if x]
        ja_n = [x for x in hebel_neu if x]
        print()
        print("  HEBELSIGNALE (%d)" % len(hebel_alt))
        print("  %-34s %10d %10d" % ("davon mit Hebel > 0",
                                     len(ja_a), len(ja_n)))
        if ja_a and ja_n:
            print("  %-34s %10.2f %10.2f"
                  % ("Median Hebelfaktor", st.median(ja_a), st.median(ja_n)))
            print("  %-34s %10.2f %10.2f"
                  % ("Maximum", max(ja_a), max(ja_n)))
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60))
    print()
    print("  ⚠️ `funding_fuenftel` ist aus der Historie REKONSTRUIERT")
    print("     (Querschnittsrang je Tag, wie `marktrang` ihn bildet).")
    print("     Bei %d von %d Signalen (%.1f %%) fehlte der Rang - dort"
          % (ohne_fund, n, 100.0 * ohne_fund / n))
    print("     steht der Rueckfall %d." % FU_VORGABE)
    print("  ⚠️⚠️ Der erste Lauf nahm durchgehend %d an und meldete"
          % FU_VORGABE)
    print("     daraufhin *NEU: 0 Signale* - ein Artefakt der Annahme.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
