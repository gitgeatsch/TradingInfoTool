"""WANN traegt H? - eine Regel ohne Mechanismus (20.08.2026, Umbauplan 115)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

DIE FRAGE DES NUTZERS: *"Muessen wir den tatsaechlichen Grund wissen, warum es
so ist - oder muessen wir nur wissen, DASS es so ist und wie es sich auswirkt?
Und damit es eine Regel wird: WANN wenden wir sie an? Laesst sich das
zurueckrechnen?"*

DIE ANTWORT, DIE DIESE MESSUNG PRUEFT. Sechs Kapitel (109-114) haben versucht,
H zu ERKLAEREN, und alle sechs sind gescheitert. Eine Regel braucht aber
keinen Mechanismus - sie braucht eine ANWENDBARKEITSBEDINGUNG, die am
Entscheidungstag bekannt ist. Der Mechanismus ist nur die robusteste Quelle
dafuer, nicht die einzige.

    Die billigste Bedingung, die ohne Theorie auskommt, ist H's EIGENE
    juengste Leistung: hat H zuletzt getragen, wenden wir es an - sonst
    nicht.

Das ist eine Frage nach BEHARRUNG, nicht nach Ursache. Sie ist mit unseren
Daten beantwortbar, und sie ist genau die Frage "wann".

⚠️ DER ZEITVERSATZ IST DER KERN DER SACHE - und er ist die Falle, an der eine
naive Fassung scheitern wuerde.

    Ein Anker aus Fenster w hat ein Vorwaertsfenster von MAX_TAGE. Sein
    Ausgang steht erst am Ende von Fenster w+1 fest (bei Fensterlaenge =
    MAX_TAGE). Wer den Vorsprung aus Fenster w als Signal fuer Fenster w+1
    benutzt, benutzt Ergebnisse, die es da noch nicht gab.

    DESHALB: das Signal fuer Fenster w+2 stammt aus Fenster w. ZWEI Fenster
    Versatz, 240 Handelstage. Das ist konservativ und ueberpruefbar.

DIE VORHERSAGE, VORAB FESTGELEGT:

    W1  BEHARRUNG   Fenster, denen ein POSITIVES H-Fenster vorausging (mit
                    zwei Fenstern Versatz), zeigen einen groesseren
                    H-Vorsprung als Fenster, denen ein negatives vorausging.

    W2  NUTZEN      Und der Unterschied ist gross genug, um den Abstand zum
                    Breakeven zu schliessen - sonst ist die Regel richtig
                    und trotzdem unbrauchbar (Methodik 2.53).

    Trifft W1 nicht zu, ist H eine Eigenschaft ohne Anwendungszeitpunkt:
    real, aber nicht in eine Handlung uebersetzbar.

⚠️ DIE KONTROLLE TAUSCHT DIE FENSTERREIHENFOLGE, nicht einzelne Anker. Die
Frage ist, ob die ABFOLGE Information traegt - also muss der Zufall dieselbe
Abfolge zerstoeren und sonst nichts.

⚠️ UND DER VORSPRUNG WIRD JE FENSTER GEGEN DIE ANKER DESSELBEN FENSTERS
gerechnet (2.50). Sonst misst man die Marktlage des Fensters mit.

    python messe_wann.py [--fenster 120] [--blockplacebo 200]
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys

import numpy as np

sys.path.insert(0, ".")
from messe_marken import bewerte, laufe                        # noqa: E402
from messe_struktur_bereinigt import MINDESTALTER, _reif        # noqa: E402
from simuliere_bremse import MAX_TAGE                           # noqa: E402

MIN_H_JE_FENSTER = 60
VERSATZ = 2          # Fenster - siehe Kopf, NICHT verhandelbar


def _quote(faelle) -> tuple[int, float]:
    ent = [f for f in faelle if f["ausgang"] in ("ziel", "stop")]
    if not ent:
        return 0, float("nan")
    return len(ent), sum(1 for f in ent if f["ausgang"] == "ziel") / len(ent)


def _fenster_vorspruenge(faelle, laenge: int) -> tuple[list, list, list]:
    """Je Zeitfenster: H-Vorsprung gegen die Anker DESSELBEN Fensters."""
    tage = sorted({f["datum"] for f in faelle})
    rang = {t: k for k, t in enumerate(tage)}
    eimer: dict = {}
    for f in faelle:
        eimer.setdefault(rang[f["datum"]] // laenge, []).append(f)
    nummern, vorspruenge, absolut = [], [], []
    for w in sorted(eimer):
        drin = eimer[w]
        h = [f for f in drin if f["frei"] and f["gedeckt"]]
        rest = [f for f in drin if not (f["frei"] and f["gedeckt"])]
        nh, qh = _quote(h)
        nr, qr = _quote(rest)
        if nh < MIN_H_JE_FENSTER or nr < MIN_H_JE_FENSTER:
            continue
        _n, _q, ab = bewerte(h, "krypto")
        nummern.append(w)
        vorspruenge.append(qh - qr)
        absolut.append(ab)
    return nummern, vorspruenge, absolut


def _beharrung(nummern, vorspruenge) -> tuple[float, int, int]:
    """W1: Vorsprung dort, wo das Fenster w-VERSATZ positiv war, gegen sonst."""
    nach_gut, nach_schlecht = [], []
    stand = dict(zip(nummern, vorspruenge))
    for w, v in zip(nummern, vorspruenge):
        vorher = stand.get(w - VERSATZ)
        if vorher is None:
            continue
        (nach_gut if vorher > 0 else nach_schlecht).append(v)
    if not nach_gut or not nach_schlecht:
        return float("nan"), len(nach_gut), len(nach_schlecht)
    return (float(np.mean(nach_gut)) - float(np.mean(nach_schlecht)),
            len(nach_gut), len(nach_schlecht))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/messdaten.db")
    ap.add_argument("--klasse", default="krypto")
    ap.add_argument("--fenster", type=int, default=MAX_TAGE)
    ap.add_argument("--blockplacebo", type=int, default=200)
    ap.add_argument("--datei", default="messwerte_wann.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("WANN TRAEGT H? - Beharrung statt Mechanismus")
    print(f"  Fenster {a.fenster} Handelstage, Signal mit {VERSATZ} Fenstern")
    print(f"  Versatz ({VERSATZ * a.fenster} Tage) - sonst benutzt das Signal")
    print("  Ergebnisse, die es zum Entscheidungszeitpunkt nicht gab.")
    print("=" * 78)
    faelle = _reif(laufe(a.db, a.klasse, fortschritt=True), MINDESTALTER)
    nummern, vorspruenge, absolut = _fenster_vorspruenge(faelle, a.fenster)
    print(f"  {len(faelle)} reife Anker -> {len(nummern)} brauchbare Fenster")
    if len(nummern) < 6:
        print("  Zu wenige Fenster fuer eine Aussage.")
        return 0

    v = np.array(vorspruenge)
    print(f"\n  H-Vorsprung je Fenster: Median {100 * np.median(v):+.1f}, "
          f"Spanne {100 * v.min():+.1f} bis {100 * v.max():+.1f}")
    print(f"  positiv in {int((v > 0).sum())} von {len(v)} Fenstern")
    print(f"  Abstand zum Breakeven je Fenster: Median "
          f"{100 * np.nanmedian(absolut):+.1f}, "
          f"ueber null in {int(np.nansum(np.array(absolut) > 0))} Fenstern")

    # ---- W1: BEHARRUNG --------------------------------------------------
    print("\n" + "-" * 78)
    print("W1 - BEHARRUNG")
    print("-" * 78)
    w1, n_gut, n_schlecht = _beharrung(nummern, vorspruenge)
    stand = dict(zip(nummern, vorspruenge))
    nach_gut = [x for w, x in zip(nummern, vorspruenge)
                if stand.get(w - VERSATZ, None) is not None
                and stand[w - VERSATZ] > 0]
    nach_schlecht = [x for w, x in zip(nummern, vorspruenge)
                     if stand.get(w - VERSATZ, None) is not None
                     and stand[w - VERSATZ] <= 0]
    print(f"  nach einem POSITIVEN Fenster   {n_gut:3} Fenster   "
          f"Vorsprung {100 * np.mean(nach_gut):+6.1f}")
    print(f"  nach einem negativen Fenster   {n_schlecht:3} Fenster   "
          f"Vorsprung {100 * np.mean(nach_schlecht):+6.1f}")
    print(f"  -> Unterschied {100 * w1:+.1f} Punkte")

    # ---- W2: REICHT ES? -------------------------------------------------
    print("\n" + "-" * 78)
    print("W2 - REICHT ES BIS ZUM BREAKEVEN? (Methodik 2.53)")
    print("-" * 78)
    abs_map = dict(zip(nummern, absolut))
    a_gut = [abs_map[w] for w in nummern
             if stand.get(w - VERSATZ, None) is not None
             and stand[w - VERSATZ] > 0 and abs_map[w] == abs_map[w]]
    a_schlecht = [abs_map[w] for w in nummern
                  if stand.get(w - VERSATZ, None) is not None
                  and stand[w - VERSATZ] <= 0 and abs_map[w] == abs_map[w]]
    if a_gut and a_schlecht:
        print(f"  Abstand nach positivem Fenster   "
              f"{100 * float(np.mean(a_gut)):+6.1f} Punkte")
        print(f"  Abstand nach negativem Fenster   "
              f"{100 * float(np.mean(a_schlecht)):+6.1f} Punkte")
        print(f"  -> {'UEBER dem Breakeven' if np.mean(a_gut) > 0 else 'weiterhin UNTER dem Breakeven'}")

    # ---- KONTROLLE: DIE ABFOLGE WUERFELN --------------------------------
    print("\n" + "-" * 78)
    print(f"KONTROLLE - {a.blockplacebo} Laeufe, FENSTERREIHENFOLGE getauscht")
    print("  Die Frage ist, ob die ABFOLGE Information traegt - also wird")
    print("  genau sie zerstoert und sonst nichts.")
    print("-" * 78)
    rng = np.random.default_rng(20260902)
    zieh = []
    for _lauf in range(a.blockplacebo):
        gemischt = list(rng.permutation(vorspruenge))
        x, _g, _s = _beharrung(nummern, gemischt)
        if x == x:
            zieh.append(x)
    schwelle = float(np.quantile(zieh, 0.95)) if zieh else float("nan")
    streu = float(np.std(zieh)) / math.sqrt(len(zieh)) if zieh else float("nan")
    print(f"  SCHWELLE (95 %)  {100 * schwelle:+.1f} Punkte")
    print(f"  gemessen         {100 * w1:+.1f} Punkte")
    if w1 != w1 or schwelle != schwelle:
        urteil = "zu wenige Fenster"
    elif abs(w1 - schwelle) < 2 * streu:
        urteil = "ZU KNAPP (2.48)"
    elif w1 > schwelle:
        urteil = "BEHARRUNG - H hat einen Anwendungszeitpunkt"
    else:
        urteil = "KEINE BEHARRUNG"
    print(f"  -> {urteil}")
    if urteil == "KEINE BEHARRUNG":
        print("     H ist damit real, aber nicht in eine Handlung")
        print("     uebersetzbar: es gibt keinen erkennbaren Zeitpunkt, an")
        print("     dem es eher traegt als sonst.")

    print("\n" + "=" * 78)
    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps({
            "fenster": a.fenster, "versatz": VERSATZ,
            "n_fenster": len(nummern), "vorspruenge": vorspruenge,
            "absolut": absolut, "w1": w1, "schwelle": schwelle,
            "urteil": urteil}, ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
