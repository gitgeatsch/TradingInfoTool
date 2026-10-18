"""P63 O21 Stufe 2 VORPRUEFUNG (18.10.2026, Schritt7 §23.70): Was kann ein Champion/Herausforderer-Vergleich im Schatten ueberhaupt
entscheiden - und wie schnell? Nur lesend; gerechnet wird die STREUUNG, kein Effekt eines Herausforderers.

    python Basisinfos/Rechenkern_02_10/p63_o21s2_vorpruefung.py

Daten: Referenz-Einstiege kern48jbz_einstiege_bestand.csv 2025-26 (wie p61/p62), Kurse stundenkurse.db -> stundenkurse_alle.db ->
eingestellt_historie.db (die erste gewinnt); 24-h-Ertrag ab dem Schluss der Einstiegsstunde.
Unsicherheit cluster-robust ueber TAGE (ein Tag = ein Markt, §23.64). MDE = kleinster Unterschied, der mit 80 % Trefferquote bei 99 %
zweiseitig erkannt wird: (2,576 + 0,842) x SE; SE auf T Betriebstage hochgerechnet mit sqrt(T_beob / T).
  V0 Datenmenge     Tage mit Signal je Jahr, Signale je Tag; Anteil der Tage mit gemailtem Signal (Schalter-Assets, Auskunft aus der NB-Ablage)
  V1 Niveau         Champion allein (Mittel des 24-h-Ertrags) - zum Vergleich (Stufe 1: +-0,58 Pp / 365 T, 95 %)
  V2 Filter         Herausforderer = TEILMENGE derselben Signale (Prueffilter, hoehere Schwelle): Zufallsteilmengen 50 % / 25 % / 10 %
                    als Nullmodell, Unterschied Teilmenge - alle (Tagesblock-Bootstrap)
  V3 Ausstieg       Herausforderer = DIESELBEN Einstiege, anderer Ausstieg (48 h statt 24 h): Unterschied je Einstieg, Tagescluster
  V4 Disjunkt       Herausforderer = ANDERE Signale an denselben Tagen: zwei disjunkte Zufallshaelften je Tag
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
DATEIEN = ("stundenkurse.db", "stundenkurse_alle.db", "eingestellt_historie.db")
B0 = pd.Timestamp("2020-01-01")
K = 2.576 + 0.842
T_LISTE = (90, 180, 365, 730)
rng = np.random.default_rng(18102026)
_con = {d: sqlite3.connect("file:data/%s?mode=ro" % d, uri=True) for d in DATEIEN if os.path.exists(os.path.join("data", d))}
_cache = {}


def reihe(sym):
    if sym in _cache:
        return _cache[sym]
    d = {}
    for _n, c in _con.items():
        for st, cl in c.execute("SELECT stunde, close FROM stundenkurse WHERE symbol=?", (sym,)):
            d.setdefault(st, cl)
    if not d:
        _cache[sym] = None
        return None
    hs = ((pd.to_datetime(list(d.keys())) - B0) / pd.Timedelta(hours=1)).astype(int).to_numpy()
    a = hs.min()
    C = np.full(hs.max() - a + 1, np.nan)
    C[hs - a] = np.array(list(d.values()), float)
    _cache[sym] = (a, C)
    return _cache[sym]


def se_cluster(x, tag):
    """SE eines Mittels ueber Einstiege, cluster-robust ueber Tage (CR0 mit Kleinzahl-Korrektur)."""
    x, tag = np.asarray(x, float), np.asarray(tag)
    m = np.nanmean(x)
    df = pd.DataFrame({"r": x - m, "t": tag}).dropna()
    s = df.groupby("t").r.sum()
    T = len(s)
    return float(np.sqrt((s ** 2).sum()) / len(df) * np.sqrt(T / (T - 1))), T


def boot_diff(D, frac=None, disjunkt=False, n=1000):
    """Tagesblock-Bootstrap des Unterschieds Teilmenge - alle (bzw. Haelfte A - Haelfte B), Teilmengen je Lauf neu gezogen."""
    tage = D.tag.unique()
    gruppen = {t: g.e24.to_numpy() for t, g in D.groupby("tag")}
    aus = []
    for _ in range(n):
        zt = rng.choice(tage, size=len(tage), replace=True)
        sa, na, sb, nb = 0.0, 0, 0.0, 0
        for t in zt:
            v = gruppen[t]
            if disjunkt:
                mk = rng.random(len(v)) < 0.5
                sa += v[mk].sum(); na += mk.sum(); sb += v[~mk].sum(); nb += (~mk).sum()
            else:
                mk = rng.random(len(v)) < frac
                sa += v[mk].sum(); na += mk.sum(); sb += v.sum(); nb += len(v)
        aus.append(sa / max(na, 1) - sb / max(nb, 1))
    return float(np.std(aus, ddof=1)), len(tage)


def main():
    E = pd.read_csv(os.path.join("data", "_vergleich", "kern48jbz_einstiege_bestand.csv"), sep=";")
    E = E[E.jahr >= 2025].copy()
    e24, e48 = [], []
    for r in E.itertuples():
        x = reihe(r.symbol)
        if x is None:
            e24.append(np.nan); e48.append(np.nan); continue
        a, C = x
        i = int(r.stunde) - a
        ok = 0 <= i and i + 48 < len(C) and C[i] == C[i] and C[i] > 0
        e24.append(C[i + 24] / C[i] - 1 if ok and C[i + 24] == C[i + 24] else np.nan)
        e48.append(C[i + 48] / C[i] - 1 if ok and C[i + 48] == C[i + 48] else np.nan)
    E["e24"], E["e48"] = e24, e48
    E["tag"] = (B0 + pd.to_timedelta(E.stunde, unit="h")).dt.normalize()
    D = E[E.e24.notna()].copy()
    print("P63 O21 STUFE 2 VORPRUEFUNG · Trennschaerfe eines Schattenvergleichs · Referenz 2025-26: %d Einstiege mit 24-h-Ertrag (von %d) an %d Tagen\n"
          % (len(D), len(E), D.tag.nunique()))
    g = D.groupby("tag").size()
    print("V0 DATENMENGE: je Jahr Tage mit Signal / Kalendertage · Signale je Tag Median (5 %..95 %)")
    for y, x in D.groupby(D.tag.dt.year):
        gy = x.groupby("tag").size()
        kal = 365 if y == 2025 else (pd.Timestamp(x.tag.max()) - pd.Timestamp("%d-01-01" % y)).days + 1
        print("   %d: %d von %d Tagen (%.0f %%) · %.0f (%.0f..%.0f) je Tag" % (y, len(gy), kal, 100 * len(gy) / kal, gy.median(), gy.quantile(0.05), gy.quantile(0.95)))
    try:
        abl = sqlite3.connect("file:K:/My Drive/Claude_Austauschordner/Notebook_Analysedaten/regel0_kopie_T440/regel0_signale.db?mode=ro", uri=True)
        s = pd.read_sql("SELECT signalstunde, mail_signal_am FROM signal", abl)
        abl.close()
        s["tag"] = s.signalstunde.str[:10]
        tg = s.groupby("tag").agg(n=("signalstunde", "size"), m=("mail_signal_am", lambda v: v.notna().sum()))
        print("   Auskunft Betrieb (NB-Ablage 03.-14.10.): %d Signale an %d Tagen, gemailt %d an %d Tagen (%.1f je Tag mit Mail)" % (
            int(tg.n.sum()), len(tg), int(tg.m.sum()), int((tg.m > 0).sum()), tg.m[tg.m > 0].mean()))
    except Exception as exc:  # noqa: BLE001
        print("   Auskunft Betrieb: NB-Ablage nicht lesbar (%s)" % exc)

    def zeile(name, se, T_beob):
        print("   %-46s SE %.3f Pp (%d Tage) -> MDE 99 %%/80 %%: %s" % (name, 100 * se, T_beob, " · ".join(
            "%d T %.2f Pp" % (T, 100 * K * se * np.sqrt(T_beob / T)) for T in T_LISTE)))

    print("\nV1 NIVEAU (Champion allein, Mittel 24-h-Ertrag %+.3f %%)" % (100 * D.e24.mean()))
    se, T = se_cluster(D.e24, D.tag)
    zeile("Mittel aller Signale", se, T)
    print("\nV2 FILTER-HERAUSFORDERER (Teilmenge derselben Signale - alle; Nullmodell Zufallsteilmenge, 1.000 Tagesblock-Ziehungen)")
    for f in (0.5, 0.25, 0.10):
        se, T = boot_diff(D, frac=f)
        zeile("Teilmenge %d %% der Signale" % (100 * f), se, T)
    print("\nV3 AUSSTIEGS-HERAUSFORDERER (dieselben Einstiege, 48 h statt 24 h; Unterschied je Einstieg)")
    P3 = D[D.e48.notna()]
    se, T = se_cluster(P3.e48 - P3.e24, P3.tag)
    zeile("48 h - 24 h (brutto, Mittel %+.3f %%)" % (100 * (P3.e48 - P3.e24).mean()), se, T)
    print("\nV4 DISJUNKTER HERAUSFORDERER (andere Signale an denselben Tagen; zwei Zufallshaelften)")
    se, T = boot_diff(D, disjunkt=True)
    zeile("Haelfte A - Haelfte B", se, T)
    schalter = ("AKT", "ALGO", "AVAX", "BEAMX", "BNB", "BTC", "ETH", "HYPE", "KAIA", "KAITO", "LINK", "MORPHO", "NEAR", "ONDO", "QNT", "SEI", "SOL",
                "SUI", "TAO", "TURBO", "VIRTUAL")                       # Schalter-Assets laut NB-Ablage 14.10. (hebel_schalter = 1)
    G5 = D[D.symbol.isin(schalter)].copy()
    print("\nV5 NUR DIE GEHANDELTEN (21 Schalter-Assets): %d Einstiege an %d Tagen (%.0f %% der Tage), Mittel %+.3f %%" % (
        len(G5), G5.tag.nunique(), 100 * G5.tag.nunique() / D.tag.nunique(), 100 * G5.e24.mean()))
    se, T = se_cluster(G5.e24, G5.tag)
    zeile("Niveau (gehandelt)", se, T)
    se, T = boot_diff(G5, frac=0.5)
    zeile("Filter 50 % (gehandelt)", se, T)
    se, T = boot_diff(G5, disjunkt=True)
    zeile("Disjunkt (gehandelt)", se, T)
    print("\nEinordnung der Groessen (Bestand, nicht hier gemessen): Kostenluecke 0,1-0,3 Pp (§23.64) · Halten je weiterem Tag -0,3..-0,4 % (§23.68) · "
          "LLM-Pruefblock trennt nicht (N5)")


if __name__ == "__main__":
    main()
