"""Beispiel des geplanten Mailabschnitts 'Altcoin-Watchlist' aus ECHTEN Daten (Voranalyse_Spot §22.4, E-73) - nur Anschauung, kein Signal, nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/beispiel_watchlist_mail.py

Stichtag = letzter Monatserster der Desktop-Daten. Watchlist kurz (alle H + beste 10 je M/S, §22.2), Begruendung je Faktor, Verlauf (seit wann
in der Liste, neu/raus gegen den Vormonat), Nachlauf-Marke fuer den Fall 'am Folgetag gekauft', Phase als Fakt (Klima, MACD, Liquiditaet,
Stablecoins, Breite). Kein Zugriff auf Bestand oder Produktionsdatenbank.
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import as_messung as M  # noqa: E402
import wl_messung as W  # noqa: E402

A = M.A
K, POS, ENDE = M.K, M.POS, M.ENDE


def monat(t):
    z = [dict(t=t, sym=s, kl=k) for s, k in A.klassen(t)[0].items() if not np.isnan(K[s].values[POS[t]])]
    D = pd.DataFrame(z)
    F = M.merkmale(D)
    Zl = W.Leicht(D)
    w = W.wert(Zl, F)
    p = M.pct_in_zelle(Zl, w)
    P = {k: (M.pct_in_zelle(Zl, F[k]) if s == "oben" else 1 - M.pct_in_zelle(Zl, F[k])) for k, s in W.WAHL}
    return D.assign(wert=w, p=p, **{"r_" + k: v for k, v in P.items()}, **{k: F[k] for k in ("F1", "F2", "F8", "F9")})


def kurz(D):
    out = []
    for kl in ("H", "M", "S"):
        x = D[(D.kl == kl) & (D.p > 0.8)].sort_values("wert", ascending=False)
        out.append(x if kl == "H" else x.head(10))
    return pd.concat(out)


def main():
    t = ENDE.replace(day=1)
    hist = {m: monat(m) for m in [t - pd.DateOffset(months=k) for k in range(5, -1, -1)]}
    D = hist[t]
    L = kurz(D)
    vor = kurz(hist[t - pd.DateOffset(months=1)])
    i_kauf = POS[t] + 1
    print("=" * 100)
    print("BEISPIEL Mailabschnitt  ALTCOIN-WATCHLIST  zum %s   (Datenstand %s · nur Anschauung, KEIN Signal)" % (t.date(), ENDE.date()))
    print("=" * 100)
    # Phase
    q = pd.Series(M.QV if hasattr(M, "QV") else [], dtype=float)
    try:
        import a3_messung as A3
        qv = pd.Series(A3.QV, index=A.IDX).dropna()
        br = pd.Series(A3.BRV, index=A.IDX).dropna()
        print("PHASE (Fakten, kein Ausloeser):  BTC-Klima q %.2f (%s) · Altseason-Breite %.0f %% (Top 50 gegen BTC ueber 90 T)" % (
            qv.iloc[-1], "billig" if qv.iloc[-1] < 1 / 3 else "mittel" if qv.iloc[-1] < 2 / 3 else "teuer", 100 * br.iloc[-1]))
    except Exception as ex:                                                  # noqa: BLE001
        print("PHASE: Klima nicht berechnet (%s)" % ex)
    try:
        import l_messung as LM
        n = LM.NETTO
        print("                                 Netto-Liquiditaet USA %.2f Bio. USD, 13 Wochen %s (%+.1f %%)" % (
            n.iloc[-1], "steigend" if n.iloc[-1] > n.iloc[-14] else "fallend", 100 * (n.iloc[-1] / n.iloc[-14] - 1)))
    except Exception as ex:                                                  # noqa: BLE001
        print("                                 Liquiditaet nicht abrufbar (%s)" % ex)
    print("                                 MACD Altcoins/BTC (monatlich): unter Null, Histogramm steigend - Kreuz nahe, nicht vollzogen (Voranalyse_Spot §20.2)")
    print("\nWATCHLIST (Rang innerhalb der Klasse; 1,00 = bester; Faktoren: Alter · Absturz · Hoch lange her · TVL gegen Kurs)")
    for kl in ("H", "M", "S"):
        x = L[L.kl == kl]
        print("\n  %s - %s" % (kl, {"H": "Highcaps (alle im obersten Fuenftel)", "M": "Midcaps (beste 10)", "S": "Smallcaps (beste 10)"}[kl]))
        for r in x.itertuples():
            seit = 0
            for k in range(0, 6):
                hm = hist[t - pd.DateOffset(months=k)]
                if r.sym in set(hm[(hm.kl == kl) & (hm.p > 0.8)].sym):
                    seit += 1
                else:
                    break
            neu = "NEU " if r.sym not in set(vor.sym) else "    "
            v = K[r.sym].values[i_kauf:]
            v = v[~np.isnan(v)]
            if len(v):
                hoch = v.max(); marke = 0.65 * hoch; bremse = 0.5 * v[0]; jetzt = v[-1]
                fuehr = "Kauf %.4g · jetzt %+.0f %% · Nachlauf-Marke %.4g (%+.0f %% von jetzt) · Notbremse %.4g" % (
                    v[0], 100 * (jetzt / v[0] - 1), max(marke, bremse), 100 * (max(marke, bremse) / jetzt - 1), bremse)
            else:
                fuehr = "kein Kurs nach dem Stichtag"
            print("   %s%-7s Wert %.2f | Alter %4.1f J (%.2f) · %3.0f %% unter Hoch (%.2f) · Hoch vor %3.0f Mon. (%.2f) · TVL %s | seit %d Mon. in der Liste | %s" % (
                neu, r.sym, r.wert, r.F8 / 365, r.r_F8, -100 * r.F1, r.r_F1, r.F2 / 30.4, r.r_F2,
                ("%+.2f (%.2f)" % (r.F9, r.r_F9)) if not np.isnan(r.F9) else "   -      ", seit, fuehr))
    raus = sorted(set(vor.sym) - set(L.sym))
    print("\n  Gegen den Vormonat nicht mehr in der kurzen Liste: %s" % (", ".join(raus) or "-"))
    print("\nVORWAERTSPROTOKOLL (ohne Geld): Korb der kurzen Liste ab %s gegen ganze Klasse und BTC, bis Datenstand:" % (t + pd.Timedelta(days=1)).date())
    for kl in ("H", "M", "S"):
        def korb(syms):
            r = []
            for s in syms:
                v = K[s].values[i_kauf:]; v = v[~np.isnan(v)]
                if len(v) > 1:
                    r.append(v[-1] / v[0] - 1)
            return np.mean(r) if r else np.nan
        b = K["BTC"].values[i_kauf:]; b = b[~np.isnan(b)]
        print("   %s  Liste %+5.1f %% · ganze Klasse %+5.1f %% · BTC %+5.1f %%  (%d Tage, vor Kosten)" % (
            kl, 100 * korb(L[L.kl == kl].sym), 100 * korb(D[D.kl == kl].sym), 100 * (b[-1] / b[0] - 1), len(b) - 1))
    print("\nWas dieser Abschnitt NICHT ist: kein Kaufsignal, kein Hebel, keine Aussage 'Altcoins statt BTC'. Abrechnung nach 6 und 12 Monaten.")


if __name__ == "__main__":
    main()
