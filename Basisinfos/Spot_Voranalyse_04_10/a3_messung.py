"""Altcoin-Spot Fassung 3 - Swing UND Zyklus (Voranalyse_Spot_Neubau_04_10.md §15.9, vorab Commit b2e88bb).

    python Basisinfos/Spot_Voranalyse_04_10/a3_messung.py

Einstieg A1 (Boden je Coin mit Wende) wie a2_messung.py; Klassen H/M/S; Kosten, Vergleich BTC, Tagesklammer wie dort.
Ausstiege X4/X5 (Swing) und X6 (Zyklus: BTC-Klima K2-Regel oder Altseason-Breite >= 75 %, hoechstens 1.095 T).
Nullwelten N1 (selbes Kalenderjahr) und N2 (+-365 T um das Ereignis). Nur lesend.

AUSLEGUNG, vor dem ersten Lauf festgelegt:
  - X4: die Ereignisse eines Tages in der Reihenfolge Gewinnmitnahme vor Nachlauf; Nachlauf auf den jeweils verbliebenen Teil ab dem Kauf
  - X6: K2 scharf, sobald q >= 0,80 ab dem Einstiegstag; Zyklushoch = Hoechstwert von q seit dem Scharfwerden;
        Altseason-Breite aus s1_messung.baue() (korrigierte Fassung, nur Coins mit beiden Kursen); fehlende Werte zaehlen nicht als Signal
  - N2: Zufallstage im Fenster [t-365, t+365] mit Kurs und mindestens 2 T vor Datenende
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import a2_messung as A  # noqa: E402
import s1_messung as S1  # noqa: E402

K, IDX, POS, BTCV, ENDE = A.K, A.IDX, A.POS, A.BTCV, A.ENDE
RNG = np.random.default_rng(20261007)
_src = open(os.path.join(HIER, "k3_gewichten.py"), encoding="utf-8").read().split("pb, mb = lade")[0]
_g = {"__file__": os.path.join(HIER, "k3_gewichten.py")}
exec(compile(_src, "k3", "exec"), _g)
_pb, _mb = _g["lade"]("btc")
QV = _g["klima"](_pb, _mb, pd.Timestamp("2013-01-01")).reindex(IDX).values
BRV = S1.baue()["breite"].reindex(IDX).values


def ausstieg3(v, art, i0):
    n = len(v)
    if art == "X5":
        hit = np.where((v >= 1.40 * v[0]) | (v <= 0.75 * v[0]))[0]
        hit = hit[hit > 0]
        return [(min(hit[0] + 1, n - 1), 1.0)] if len(hit) else [(n - 1, 1.0)]
    if art == "X4":
        out, rest, h, tp = [], 1.0, v[0], [(1.30, 0.5), (1.60, None)]
        for j in range(1, n):
            h = max(h, v[j])
            for f, a in list(tp):
                if v[j] >= f * v[0] and rest > 1e-12:
                    teil = rest if a is None else a
                    out.append((min(j + 1, n - 1), teil)); rest -= teil; tp.remove((f, a))
            if rest > 1e-12 and v[j] < 0.80 * h:
                out.append((min(j + 1, n - 1), rest)); rest = 0.0
            if rest <= 1e-12:
                break
        if rest > 1e-12:
            out.append((n - 1, rest))
        return out
    qs, br = QV[i0:i0 + n], BRV[i0:i0 + n]
    scharf = np.maximum.accumulate(np.nan_to_num(qs, nan=0.0) >= 0.80)
    qh = np.maximum.accumulate(np.where(scharf, np.nan_to_num(qs, nan=-1.0), -1.0))
    sig = (scharf & ~np.isnan(qs) & (qs < qh - 0.10)) | (np.nan_to_num(br, nan=0.0) >= 0.75)
    hit = np.where(sig)[0]
    return [(min(hit[0] + 1, n - 1), 1.0)] if len(hit) else [(n - 1, 1.0)]


def handel3(sym, i0, art, ko=A.KO_COIN):
    maxt = {"X4": 120, "X5": 90, "X6": 1095}[art]
    v, b = A.pfad(sym, i0, maxt)
    if v is None or len(v) < 2:
        return None
    vk = ausstieg3(v, art, i0)
    erl_c = sum(a * v[t] / v[0] * (1 - ko) for t, a in vk) / (1 + ko)
    erl_b = sum(a * b[t] / b[0] * (1 - A.KO_BTC) for t, a in vk) / (1 + A.KO_BTC)
    offen = (i0 + len(v) - 1 >= len(IDX) - 1) and vk[-1][0] == len(v) - 1 and len(v) < maxt + 1
    eing = (i0 + len(v) - 1 < len(IDX) - 1) and len(v) < (maxt + 1) and vk[-1][0] == len(v) - 1
    return dict(r=erl_c - 1, rb=erl_b - 1, vorteil=erl_c / erl_b - 1, tage=max(t for t, _ in vk), offen=offen, eing=eing)


def nullwelt(ereignisse, art, art_n):
    pools = []
    for t, s in ereignisse:
        reihe = K[s].dropna().index
        if art_n == "N1":
            tage = reihe[(reihe.year == t.year)]
        else:
            tage = reihe[(reihe >= t - pd.Timedelta(days=365)) & (reihe <= t + pd.Timedelta(days=365))]
        tage = tage[tage <= ENDE - pd.Timedelta(days=2)]
        if len(tage) == 0:
            pools.append(None); continue
        z = RNG.choice(tage, size=20, replace=True)
        erg = [handel3(s, POS[pd.Timestamp(x)] + 1, art) for x in z]
        pools.append([(pd.Timestamp(x), e["vorteil"]) for x, e in zip(z, erg) if e is not None])
    werte = []
    for _ in range(200):
        zz = [p[RNG.integers(len(p))] for p in pools if p]
        d = pd.DataFrame(zz, columns=["einstieg", "vorteil"])
        werte.append(d.groupby("einstieg")["vorteil"].mean().mean())
    return np.array(werte)


def messe(ereignisse, art, klasse):
    zeilen = []
    for t, s in ereignisse:
        kl, _ = A.klassen(t.replace(day=1))
        if kl.get(s) != klasse:
            continue
        i0 = POS[t] + 1
        if i0 >= len(IDX):
            continue
        e = handel3(s, i0, art)
        if e is not None:
            zeilen.append(dict(e, ereignis=t, einstieg=IDX[i0], sym=s, ep=A.epoche(t)))
    D = pd.DataFrame(zeilen)
    out = {}
    for ep in ("E1", "E2", "E3"):
        x = D[D["ep"] == ep] if len(D) else D
        if len(x) < 5:
            out[ep] = None; continue
        tk = x.groupby("einstieg")["vorteil"].mean()
        m, md = tk.mean(), tk.median()
        r1 = r2 = None
        if ep in ("E2", "E3"):
            ev = [(r.ereignis, r.sym) for r in x.itertuples()]
            r1 = float(np.mean(nullwelt(ev, art, "N1") < m)); r2 = float(np.mean(nullwelt(ev, art, "N2") < m))
        out[ep] = dict(n=len(x), tage=len(tk), mittel=m, median=md, ge100=(x["vorteil"] >= 1.0).mean(), le50=(x["r"] <= -0.5).mean(),
                       halte=x["tage"].mean(), offen=x["offen"].mean(), eing=x["eing"].mean(), r1=r1, r2=r2,
                       r_med=x["r"].median(), rb_med=x["rb"].median(), plus=(x["vorteil"] > 0).mean())
    return out


def main():
    ev = A.mit_ruhe(A.A1)
    print("Altcoin-Spot Fassung 3 (Voranalyse_Spot §15.9) - Einstieg A1 (Boden + Wende), %d Ereignisse · Daten bis %s" % (len(ev), ENDE.date()))
    gesamt = []
    for kl in ("H", "M", "S"):
        for art, name in (("X4", "Swing gestaffelt +30/+60, Nachlauf -20 %, 120 T"), ("X5", "Swing +40 % / -25 %, 90 T"),
                          ("X6", "Zyklus: Klima-Ausstieg (K2 oder Breite >= 75 %), bis 3 J")):
            out = messe(ev, art, kl)
            tr = all(out.get(e) and out[e]["mittel"] > 0 and out[e]["median"] > 0 and (out[e]["r1"] or 0) >= 0.95 and (out[e]["r2"] or 0) >= 0.95
                     for e in ("E2", "E3"))
            gesamt.append(("A1 · %s · %s" % (kl, art), tr))
            print("\nA1 · Klasse %s · %s %s  ->  %s" % (kl, art, name, "TRAEGT" if tr else "traegt nicht"))
            for e in ("E1", "E2", "E3"):
                o = out.get(e)
                if not o:
                    print("  %s  zu wenige Ereignisse" % e); continue
                print("  %s  n %4d (%3d Tage) | Vorteil gg. BTC: Mittel %+6.1f %% · Median %+6.1f %% · Handel vor BTC %3.0f %% · >= +100 %% %3.0f %% | "
                      "Ertrag Coin Median %+5.0f %% (BTC %+5.0f %%) · <= -50 %% %3.0f %% | Halten %4.0f T · offen %2.0f %% · eingestellt %2.0f %% | Rang N1 %s · N2 %s" % (
                          e, o["n"], o["tage"], 100 * o["mittel"], 100 * o["median"], 100 * o["plus"], 100 * o["ge100"], 100 * o["r_med"],
                          100 * o["rb_med"], 100 * o["le50"], o["halte"], 100 * o["offen"], 100 * o["eing"],
                          "%.2f" % o["r1"] if o["r1"] is not None else "-", "%.2f" % o["r2"] if o["r2"] is not None else "-"))
    print("\nGESAMT (vorab §15.9: E2 UND E3 Mittel > 0, Median > 0, Rang N1 UND N2 >= 0,95):")
    for n, t in gesamt:
        print("  %-22s %s" % (n, "TRAEGT" if t else "-"))


if __name__ == "__main__":
    main()
