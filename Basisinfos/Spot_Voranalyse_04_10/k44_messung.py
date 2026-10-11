"""MESSUNG K-1/K-2 - H-DM: H-Momentum-Einstieg nach Dominanz-Spitze (Spot §44, vorab Commit edce4a8). Nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/k44_messung.py

Einstiege genau §37.2 (k37_machbarkeit.einstiege, Klasse H, Kauf d+1, 30 T, Sperre), Zielgroesse gegen BTC brutto, Korb je Monat.
Spitzen-Tag: BTCDOM-Tagesschluss / Schluss 30 T vorher - 1 >= 8,7 % am Signaltag.
  Teil 0  2024+: +6,3 Pp (n 71) / -0,8 Pp (+-0,1), sonst Abbruch
  A       2023: Korb(Spitze) - Korb(uebrige); Nullwelt Zeitverschiebung (Spitzen-Reihe 2023 kreisfoermig um 1.000 Versaetze 30-305 T)
  B       2023: Korb(Spitze) > 0 und gegen zufaellige Highcaps desselben Tages ohne Signal (1.000), Rang
  Urteil  TRAEGT: A Rang >= 0,975 und B Korb > 0, B Rang >= 0,975 und >= 20 Einstiege an >= 6 Monaten · SCHADET: A Rang <= 0,025 · sonst nicht entscheidbar
  Selbsttest (a) 200 Placebo-Reihen (Episoden gleicher Zahl und Laenge, zufaellig gelegt), je 1.000 Versaetze: Fehlalarm zweiseitig <= 8 %
             (b) Aufloesung: Spitzen-Einstiege 2023 ersetzt durch eine Stichprobe aller 2023-Einstiege + x Pp, x = 3 / 7 / 15, je 50 Wiederholungen;
                 x = 7 in < 80 % gefunden -> 'nicht entscheidbar - Aufloesung reicht nicht'
AUSLEGUNG (vor dem Lauf): Fenster 2023 wie die Ablage k37_einstiege_H_W (Signale 2023-01-01 bis 2023-12-01); der Versatz kreist ueber die
335 Tage dieses Fensters; Placebo-Episoden ohne Ueberlappung; (b) prueft A (die entscheidende Bedingung).
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import k37_messung as K7  # noqa: E402  (setzt das Arbeitsverzeichnis, laedt T/KM)

KM, T, IDX = K7.KM, K7.T, K7.IDX
RNG = np.random.default_rng(20261044)
AB23, BIS23 = pd.Timestamp("2023-01-01"), pd.Timestamp("2023-12-01")
KOSTEN_H = 0.0072


def lade_dom():
    c = sqlite3.connect("file:data/richtung_historie.db?mode=ro", uri=True)
    d = pd.read_sql("select substr(stunde,1,10) tag, close from btcdom where stunde in (select max(stunde) from btcdom group by substr(stunde,1,10))", c)
    return pd.Series(d.close.values, index=pd.to_datetime(d.tag)).sort_index()


def korb(E):
    return E.groupby("mon").ex.mean().mean() if len(E) else np.nan


def abstand(E, sp):
    return korb(E[sp]) - korb(E[~sp])


def episoden(serie):
    """Liste (Startindex, Laenge) zusammenhaengender True-Laeufe."""
    ep, i, v = [], 0, serie.values
    while i < len(v):
        if v[i]:
            j = i
            while j < len(v) and v[j]:
                j += 1
            ep.append((i, j - i))
            i = j
        else:
            i += 1
    return ep


def main():
    rel, F = T.merkmale()
    up, down, end, fertig = T.ziele(rel)
    m, kl = T.maske()
    m = m & fertig
    X = F["rs30"].where(m)
    pct = X.rank(axis=1, pct=True)
    pct.loc[X.notna().sum(axis=1) < 30] = np.nan
    dom = lade_dom()
    anstieg = dom / dom.shift(30) - 1

    def spitze_an(E, schwelle=0.087):
        return (anstieg.reindex(E.signal) >= schwelle).fillna(False).values

    # Teil 0
    U = K7.bewerte(KM.einstiege(pct, kl, m, "H", pd.Timestamp("2024-01-01"), T.M.ENDE), up, down)
    su = spitze_an(U)
    a0, b0 = 100 * korb(U[su]), 100 * korb(U[~su])
    print("MESSUNG K-1/K-2 H-DM (§44) · Kurse bis %s\n" % T.M.ENDE.date())
    print("TEIL 0 2024+: Spitze %+.2f Pp (n %d) / sonst %+.2f Pp (Soll +6,3 / 71 / -0,8)" % (a0, su.sum(), b0))
    if not (abs(a0 - 6.3) <= 0.1 and su.sum() == 71 and abs(b0 + 0.8) <= 0.1):
        print("TEIL 0 FEHLGESCHLAGEN - Abbruch")
        return
    print("-> Teil 0 bestanden\n")

    E = K7.bewerte(KM.einstiege(pct, kl, m, "H", AB23, BIS23), up, down)
    tage = pd.date_range(AB23, BIS23, freq="D")
    sp_reihe = (anstieg.reindex(tage) >= 0.087).fillna(False)
    pos = {d: i for i, d in enumerate(tage)}
    ipos = np.array([pos[d] for d in E.signal])
    N = len(tage)

    def sp_aus(reihe_werte):
        return reihe_werte[ipos]

    sp = sp_aus(sp_reihe.values)
    n_sp, mon_sp = int(sp.sum()), E[sp].mon.nunique()

    def versatz_null(ex_werte, reihe_werte, nz):
        F_ = E.assign(ex=ex_werte)
        a = abstand(F_, sp_aus(reihe_werte))
        off = RNG.integers(30, N - 30 + 1, size=nz)
        nl = np.array([abstand(F_, sp_aus(np.roll(reihe_werte, o))) for o in off])
        return a, nl

    # A
    a, nl = versatz_null(E.ex.values, sp_reihe.values, 1000)
    rang_a = float(np.mean(nl < a))
    # B
    Es = E[sp].copy()
    kb = korb(Es)
    kand = K7.kandidaten(Es, pct, kl, m, "H")
    nb, _ = K7.null(Es, kand, 1000)
    rang_b = float(np.mean(nb < kb))
    genug = n_sp >= 20 and mon_sp >= 6

    # Selbsttest (a)
    ep = episoden(sp_reihe)
    laengen = [l for _, l in ep]
    fa = 0
    for _ in range(200):
        r = np.zeros(N, dtype=bool)
        for l in sorted(laengen, reverse=True):
            for _v in range(1000):
                s0 = RNG.integers(0, N - l + 1)
                if not r[max(s0 - 1, 0):s0 + l + 1].any():
                    r[s0:s0 + l] = True
                    break
        ap, np_ = versatz_null(E.ex.values, r, 1000)
        rp = float(np.mean(np_ < ap))
        fa += rp >= 0.975 or rp <= 0.025
    # Selbsttest (b)
    aufl = {}
    alle_ex = E.ex.values
    for x in (0.03, 0.07, 0.15):
        f = 0
        for _ in range(50):
            ex2 = alle_ex.copy()
            ex2[sp] = RNG.choice(alle_ex, size=n_sp, replace=True) + x
            ab_, nl_ = versatz_null(ex2, sp_reihe.values, 1000)
            f += ab_ > 0 and np.mean(nl_ < ab_) >= 0.975
        aufl[x] = f / 50
    st_a = fa / 200 <= 0.08
    st_b = aufl[0.07] >= 0.80

    if genug and a > 0 and rang_a >= 0.975 and kb > 0 and rang_b >= 0.975:
        u = "TRAEGT"
    elif rang_a <= 0.025:
        u = "SCHADET"
    else:
        u = "nicht entscheidbar"
    if not st_b:
        u_end = "nicht entscheidbar - Aufloesung reicht nicht"
    elif not st_a:
        u_end = "Urteil gilt nicht (Selbsttest a)"
    else:
        u_end = u

    print("2023 (URTEIL): Einstiege H %d · an Spitzen-Tagen %d an %d Monaten (Mindestzahl %s) · Spitzen-Tage %d in %d Episoden (Laengen %s)" % (
        len(E), n_sp, mon_sp, "erfuellt" if genug else "NICHT erfuellt", int(sp_reihe.sum()), len(ep), laengen))
    print("  A Bedingung: Korb Spitze %+.2f Pp · uebrige %+.2f Pp · Abstand %+.2f Pp · Zeitverschiebung 2,5./97,5. Perz. %+.2f / %+.2f · Rang %.3f" % (
        100 * korb(E[sp]), 100 * korb(E[~sp]), 100 * a, 100 * np.percentile(nl, 2.5), 100 * np.percentile(nl, 97.5), rang_a))
    print("  B absolut: Korb Spitze gegen BTC %+.2f Pp · Zufall gleicher Tag Mittel %+.2f Pp · Rang %.3f · nach Kosten %+.2f Pp" % (
        100 * kb, 100 * nb.mean(), rang_b, 100 * (kb - KOSTEN_H)))
    print("  SELBSTTEST (a) Fehlalarm %d von 200 Placebos (%.1f %%, Soll <= 8 %%) -> %s" % (fa, 100 * fa / 200, "bestanden" if st_a else "NICHT bestanden"))
    print("  SELBSTTEST (b) Aufloesung: +3 Pp %.0f %% · +7 Pp %.0f %% · +15 Pp %.0f %% gefunden (Bedingung +7 Pp >= 80 %%) -> %s" % (
        100 * aufl[0.03], 100 * aufl[0.07], 100 * aufl[0.15], "reicht" if st_b else "reicht NICHT"))
    print("  => URTEIL (vor Selbsttest) %s  =>  GILT: %s\n" % (u, u_end))

    # Auskunft
    print("AUSKUNFT (nach dem Urteil, kein Test):")
    for s in (0.05, 0.12, 0.15):
        spx = spitze_an(E, s)
        print("  Schwelle %4.1f %%: Spitze n %d · Korb %+.2f / uebrige %+.2f Pp" % (100 * s, spx.sum(), 100 * korb(E[spx]), 100 * korb(E[~spx])))
    mk = E[sp].groupby("mon").ex.mean()
    if len(mk):
        ohne = mk.drop(mk.idxmax())
        print("  Monate Spitze: %s · Median der Monate %+.2f Pp · ohne den staerksten Monat (%s) %+.2f Pp" % (
            " · ".join("%s %+.1f" % (k, 100 * v) for k, v in mk.items()), 100 * mk.median(), mk.idxmax(), 100 * ohne.mean() if len(ohne) else np.nan))
    for h in (21, 42):
        Eh = K7.bewerte(KM.einstiege(pct, kl, m, "H", AB23, BIS23, halte=h), up, down)
        sh = spitze_an(Eh)
        print("  Zeitgrenze %d T: Spitze n %d · %+.2f / uebrige %+.2f Pp" % (h, sh.sum(), 100 * korb(Eh[sh]), 100 * korb(Eh[~sh])))
    for nm, ab, bis in (("2023", AB23, BIS23), ("2024+", pd.Timestamp("2024-01-01"), T.M.ENDE)):
        Em = K7.bewerte(KM.einstiege(pct, kl, m, "M", ab, bis), up, down)
        sm = spitze_an(Em)
        print("  M %s: Spitze n %d · %+.2f / uebrige %+.2f Pp" % (nm, sm.sum(), 100 * korb(Em[sm]), 100 * korb(Em[~sm])))
    print("  2024+ (Beschreibung, Wahlmenge): Spitze %+.2f / uebrige %+.2f Pp · Abstand %+.2f Pp" % (a0, b0, a0 - b0))
    E.assign(spitze=sp).to_csv(os.path.join("data", "_spot", "k44_einstiege_2023.csv"), sep=";", index=False)


if __name__ == "__main__":
    main()
