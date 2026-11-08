"""G7 Stufe 3 — SELBSTTEST der VORPRÜFUNG (Abbruchregel) auf der festgeschriebenen Menge b. Nutzer 08.11.: *„können wir die Prüfung
so anlegen, dass die langen läufe nur erfolgen wenn wir einen Hinweis darauf haben, dass es funktioniert“* → *„1 Vorprüfung“*.

Kein LLM, kein Urteil, kein Netz. Nur die ECHTEN Zielgrößen der Menge b (``data/_g7/regel0/stufe3_zielgroesse_b.csv``, deckungsgleich
mit ``g7_stufe3_menge_b.csv``) und KÜNSTLICHE Urteile mit bekannter Wahrheit.

DIE ZWEI STUFEN:
  3a Vorprüfung   je Einstiegstag k Einstiege aus Menge b (fester Zufall), dieselbe Statistik wie die Messung (Arm HANDEL,
                  Tagesbahn, einseitig unten) -> p_vor. WEITER, wenn p_vor ≤ c. Sonst ENDE: Stufe 3 „nicht trennbar“.
                  Die Vorprüfung kann NUR abbrechen, nie „trägt“ melden.
  3b Rest         die übrigen Einstiege; ausgewertet wird danach auf ALLEN (wie Messplan §11.5 festgelegt, Band P5).

  Weil nur für Vergeblichkeit abgebrochen wird, kann der Fehlalarm nicht steigen. Gemessen wird hier trotzdem beides.

AUSWAHLREGEL — festgelegt VOR dem Lauf:
  Kandidaten k ∈ {1, 2} · c ∈ {0,20; 0,30; 0,40; 0,50}.
  Gewählt wird das KLEINSTE k und dazu das KLEINSTE c, für das bei einem gepflanzten Unterschied von 0,2 σ (≈ 0,9 % je Handel,
  Messplan §11.3) UND bei 0,3 σ die Vorprüfung in BEIDEN Erzeugern (G-Handel 30 %, G-Tag Lauf 3 T) zu ≥ 90 % weiterläuft.
  Erfüllt keine Kombination das, wird k = 2, c = 0,50 genommen und der Verlust ausgewiesen.

    python g7_stufe3_vorpruefung_selbsttest.py
"""
import os
import sys
import time
from datetime import datetime

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, HIER)
import g7_stufe3_anlage as A                                          # noqa: E402

ZB = os.path.join(PROJ, "data", "_g7", "regel0", "stufe3_zielgroesse_b.csv")
MENGE = os.path.join(HIER, "g7_stufe3_menge_b.csv")
KS = (1, 2)
CS = (0.20, 0.30, 0.40, 0.50)
STARK = (0.1, 0.2, 0.3)
N_NULL = 1000
N_PFL = 500
TXT = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    TXT.append(s)


def lade() -> pd.DataFrame:
    Z = pd.read_csv(ZB, sep=";")
    M = pd.read_csv(MENGE, sep=";")
    assert set(zip(M.symbol, M.stunde)) == set(zip(Z.symbol, Z.stunde)), "Zielgrößen ≠ festgeschriebene Menge b"
    Z = Z.dropna(subset=["ertrag_s"]).sort_values(["stunde", "symbol"]).reset_index(drop=True)
    return Z


def vorauswahl(Z: pd.DataFrame, k: int) -> np.ndarray:
    """Je Tag k Einstiege, fester Zufall (Startwert 20261108 + k) — Indizes in Z, aufsteigend."""
    rng = np.random.default_rng(20261108 + k)
    idx = []
    for _t, g in Z.groupby("tag", sort=True):
        i = g.index.to_numpy()
        idx.extend(rng.choice(i, min(k, len(i)), replace=False))
    return np.sort(np.array(idx))


def p_wert(Zs: pd.DataFrame, u: np.ndarray) -> tuple:
    s, null = A.arm_handel_tage(u, Zs.ertrag_s.to_numpy(), A.bahn_tage(Zs))
    if not np.isfinite(s) or not len(null):
        return np.nan, False
    return float((null <= s).mean()), bool(s < np.percentile(null, 5))


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    t0 = time.time()
    rng = np.random.default_rng(20261108)
    Z = lade()
    p("G7 STUFE 3 — SELBSTTEST DER VORPRÜFUNG · %s · Werkzeug-Prüfsumme siehe Doku" % datetime.now().strftime("%Y-%m-%d %H:%M"))
    p("Menge b: %d Einstiege mit Zielgröße · %d Tage · %d Blöcke · σ Median %.2f %%" % (
        len(Z), Z.tag.nunique(), A.bloecke(Z.tag), 100 * Z.sigma.median()))
    V = {}
    for k in KS:
        i = vorauswahl(Z, k)
        Zk = Z.loc[i].reset_index(drop=True)
        V[k] = (i, Zk)
        p("  Vorprüfung k = %d je Tag: %d Einstiege · %d Tage · %d Blöcke · Rest %d" % (
            k, len(i), Zk.tag.nunique(), A.bloecke(Zk.tag), len(Z) - len(i)))
    # Gegenprobe: dieselbe Statistik wie die Messanlage (messe) auf der vollen Menge
    u0 = A.g_handel(Z, rng, 0.3)
    r0 = A.messe(Z, u0)
    pw, tr = p_wert(Z, u0)
    p("  Gegenprobe gegen g7_stufe3_anlage.messe: p %.4f gegen %.4f · trägt %s gegen %s" % (pw, r0["p"], tr, r0["traegt"]))

    gens = {"G-Handel 30 %": lambda: A.g_handel(Z, rng, 0.3), "G-Tag Lauf 3 T": lambda: A.g_tag(Z, rng, 3),
            "G-Tag Lauf 1 T": lambda: A.g_tag(Z, rng, 1)}

    def lauf(gen, s, n):
        """-> je k: Array p_vor; dazu traegt_voll (Messung auf allen)."""
        pv = {k: np.empty(n) for k in KS}
        tv = np.empty(n, bool)
        for j in range(n):
            u = gen()
            Zp = Z.assign(ertrag_s=Z.ertrag_s - s * u) if s else Z
            _pf, tv[j] = p_wert(Zp, u)
            for k in KS:
                i, Zk = V[k]
                pv[k][j], _ = p_wert(Zk.assign(ertrag_s=Zp.ertrag_s.to_numpy()[i]), u[i])
        return pv, tv

    p("\n1  OHNE WIRKUNG (%d Ziehungen): Anteil WEITER je c · Fehlalarm voll / mit Vorprüfung (Soll ≤ 5 %%, Toleranz 6,5 %%)" % N_NULL)
    for name in ("G-Tag Lauf 1 T", "G-Tag Lauf 3 T", "G-Handel 30 %"):
        pv, tv = lauf(gens[name], 0.0, N_NULL)
        for k in KS:
            p("   %-15s k=%d  weiter: %s · Fehlalarm voll %.1f %% · mit Vorprüfung %s" % (
                name, k, " ".join("c%.2f %3.0f %%" % (c, 100 * np.mean(pv[k] <= c)) for c in CS), 100 * tv.mean(),
                " ".join("%.1f" % (100 * np.mean(tv & (pv[k] <= c))) for c in CS)))

    p("\n2  MIT WIRKUNG (%d Ziehungen je Stärke): Fundquote voll · Anteil WEITER je c · Fundquote mit Vorprüfung je c" % N_PFL)
    ok = {(k, c): True for k in KS for c in CS}
    for name in ("G-Handel 30 %", "G-Tag Lauf 3 T"):
        for s in STARK:
            pv, tv = lauf(gens[name], s, N_PFL)
            for k in KS:
                w = {c: float(np.mean(pv[k] <= c)) for c in CS}
                if s >= 0.2:
                    for c in CS:
                        ok[(k, c)] &= w[c] >= 0.90
                p("   %-15s %.1fσ (≈%.2f %%) k=%d  voll %3.0f %% · weiter %s · mit Vorprüfung %s" % (
                    name, s, 100 * s * Z.sigma.median(), k, 100 * tv.mean(),
                    " ".join("c%.2f %3.0f" % (c, 100 * w[c]) for c in CS),
                    " ".join("%3.0f" % (100 * np.mean(tv & (pv[k] <= c))) for c in CS)))

    wahl = next(((k, c) for k in KS for c in CS if ok[(k, c)]), None)
    p("\n3  AUSWAHL nach der Regel im Kopf: %s" % (
        "k = %d je Tag, c = %.2f" % wahl if wahl else "keine Kombination erfüllt ≥ 90 %% → k = 2, c = 0,50 (Verlust oben ausgewiesen)"))
    p("   Rechenzeit %.0f s" % (time.time() - t0))
    with open(os.path.join(HIER, "g7_stufe3_vorpruefung_selbsttest.txt"), "w", encoding="utf-8") as f_:
        f_.write("\n".join(TXT) + "\n")


if __name__ == "__main__":
    main()
