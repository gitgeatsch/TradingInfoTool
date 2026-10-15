"""O53 VORPRUEFUNG (Stufe 1): Sagt das Makro-Regime das RISIKO voraus - ueber die eigene juengste Schwankung hinaus? (15.10.2026)

    python Basisinfos/Rechenkern_02_10/o53_vorpruefung.py > Basisinfos/Rechenkern_02_10/o53_vorpruefung.txt

Messplan: Schritt7 §23.55 (vorab festgelegt, zweiseitig). Nur lesend: data/_spot/p51_eingang.pkl (Kanaele, BTC CoinMetrics) und
data/_spot/p51_bank_n2.pkl (1.000 gemeinsame Surrogat-Scores N2 aus p51_messung_n2, monatliche Stichtage).

  Ziele      (a) Schwankung der naechsten 30 T (Std der Tages-log-Renditen ab dem Folgetag)
             (b) tiefster Stand der naechsten 30 T gegen den Einstieg am Folgetag (log)
  Fortschr.  Schwankung der letzten 30 T. Ziel = REST nach der Regression auf die Fortschreibung, geschaetzt NUR aus Stichtagen,
             deren Zielfenster schon abgeschlossen ist (zwei Monate Abstand), ab 36 Stichtagen
  Merkmal    Gesamt lang, Gesamt kurz (Rueckenwind +1 / Mitte 0 / Gegenwind -1); Groesse: Rest(Rueckenwind) - Rest(Gegenwind)
  Nullwelt   N2-Bank; p je Seite; Bonferroni 0,025/2 = 0,0125 je Test und Seite (2 Merkmale x 2 Ziele: 4 Tests -> 0,00625)
  Selbsttest 200 synthetische Welten ohne Makro-Bezug: Renditen z_t * sigma_t, log sigma_t = phasen-randomisierte echte
             log-30-T-Schwankung (gleiches Spektrum: Ballung und langsame Phasen bleiben), z t-verteilt (4 FG). Fehlalarm je Seite
             muss im Binomialband liegen. Pflanzung: log sigma += beta * Gesamt-Score -> Fundquote je beta
  Auskunft   Epochen E1 (bis 2020) / E2 (2021-23) / E3 (ab 2024)
"""
import os
import pickle
import sys
import time

import numpy as np
import pandas as pd
from scipy.stats import binom

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
os.chdir(PROJ)
sys.path.insert(0, os.path.join(PROJ, "Basisinfos", "Spot_Voranalyse_04_10"))
sys.stdout.reconfigure(encoding="utf-8")

RNG = np.random.default_rng(20261053 + 53)
H = 30
START = pd.Timestamp("2013-01-01")
ALPHA = 0.025 / 4                                        # 4 Tests, je Seite
N_SELBST, N_PFL = 200, 40
MERK = ("Gesamt lang", "Gesamt kurz")

with open(os.path.join("data", "_spot", "p51_eingang.pkl"), "rb") as f:
    D = pickle.load(f)
with open(os.path.join("data", "_spot", "p51_bank_n2.pkl"), "rb") as f:
    B = pickle.load(f)
namen, stich, bank, echt = B["namen"], pd.DatetimeIndex(B["stich"]), B["bank"], B["echt"]
btc = D["preise"]["BTC"].dropna().sort_index()
btc = btc.reindex(pd.date_range(btc.index[0], btc.index[-1], freq="D")).ffill()
lr = np.log(btc).diff()


def ziele(r):
    """r: Tages-log-Renditen (Series, taeglich). -> DataFrame je Stichtag: vor (Schwankung 30 T bis t), a, b."""
    aus = []
    for t in stich:
        if t - pd.Timedelta(days=H) < r.index[0] or t + pd.Timedelta(days=H + 1) > r.index[-1]:
            aus.append((np.nan, np.nan, np.nan))
            continue
        vor = r.loc[t - pd.Timedelta(days=H - 1):t].std()
        nach = r.loc[t + pd.Timedelta(days=2):t + pd.Timedelta(days=H + 1)]      # ab Schluss des Folgetags
        pfad = nach.cumsum()
        aus.append((vor, nach.std(), min(0.0, pfad.min())))
    return pd.DataFrame(aus, index=stich, columns=["vor", "a", "b"])


def rest(Z, spalte):
    """Rest nach rollierender Regression auf log(vor) - nur Stichtage mit abgeschlossenem Ziel (j <= i-2), ab 36."""
    x = np.log(Z["vor"].values)
    y = np.log(Z["a"].values) if spalte == "a" else Z["b"].values
    out = np.full(len(Z), np.nan)
    for i in range(len(Z)):
        j = np.arange(max(0, i - 1))
        j = j[np.isfinite(x[j]) & np.isfinite(y[j])]
        if len(j) < 36 or not (np.isfinite(x[i]) and np.isfinite(y[i])) or stich[i] < START:
            continue                                     # Urteil ab 2013 wie §51.7 T1; frueher nur Lernmenge der Regression
        b, a = np.polyfit(x[j], y[j], 1)
        out[i] = y[i] - (a + b * x[i])
    return out


def abstand(s, y):
    p, m = s == 1, s == -1
    np_, nm = p.sum(-1), m.sum(-1)
    a = (p * y).sum(-1) / np.maximum(np_, 1) - (m * y).sum(-1) / np.maximum(nm, 1)
    return np.where((np_ >= 5) & (nm >= 5), a, np.nan)


def test(merk, y):
    j = namen.index(merk)
    s = echt[j].astype(float)
    ok = np.isfinite(s) & np.isfinite(y)
    a = float(abstand(s[ok], y[ok]))
    bk = np.where(np.isnan(bank[:, j, :]), 0.0, bank[:, j, :])[:, ok]
    nul = abstand(bk, y[ok])
    nul = nul[np.isfinite(nul)]
    return a, (np.sum(nul >= a) + 1) / (len(nul) + 1), (np.sum(nul <= a) + 1) / (len(nul) + 1), int((s[ok] == 1).sum()), int((s[ok] == -1).sum()), ok


def epoche(t):
    return "E1" if t < pd.Timestamp("2021-01-01") else ("E2" if t < pd.Timestamp("2024-01-01") else "E3")


def phasen(v):
    mu = v.mean()
    F = np.fft.rfft(v - mu)
    ph = RNG.uniform(0, 2 * np.pi, len(F))
    ph[0] = 0.0
    if len(v) % 2 == 0:
        ph[-1] = 0.0
    return np.fft.irfft(np.abs(F) * np.exp(1j * (np.angle(F) + ph)), n=len(v)) + mu


lsig = np.log(lr.rolling(H).std()).dropna()
z_std = np.sqrt(4 / 2)                                      # Std einer t(4)


def welt(beta=0.0, merk="Gesamt lang"):
    ls = pd.Series(phasen(lsig.values), index=lsig.index)
    if beta:
        s = pd.Series(echt[namen.index(merk)].astype(float), index=stich).reindex(ls.index, method="ffill").fillna(0.0)
        ls = ls + beta * s
    z = RNG.standard_t(4, len(ls)) / z_std
    return pd.Series(z * np.exp(ls.values), index=ls.index)


t0 = time.time()
Z = ziele(lr)
REST = {"a": rest(Z, "a"), "b": rest(Z, "b")}
EP = np.array([epoche(t) for t in stich])
print("O53 VORPRUEFUNG · Makro gegen RISIKO (Rest nach der eigenen 30-T-Schwankung) · BTC · Stichtage %d (mit Rest a: %d) · "
      "N2-Surrogate %d · alpha je Test und Seite %.5f\n" % (len(stich), np.isfinite(REST["a"]).sum(), bank.shape[0], ALPHA))
print("Fortschreibung allein (Rangkorrelation vor -> a): %.2f  - so viel weiss die eigene Schwankung schon\n"
      % pd.Series(Z["vor"]).rank().corr(pd.Series(Z["a"]).rank()))
print("Vorzeichen: Abstand = Rest(Rueckenwind) - Rest(Gegenwind). Bei (a) heisst NEGATIV: Gegenwind schwankt MEHR als die Fortschreibung "
      "sagt; bei (b) heisst POSITIV: Gegenwind faellt TIEFER.\n")
ERG = {}
for zi, name in (("a", "(a) Schwankung 30 T"), ("b", "(b) tiefster Stand 30 T")):
    for m in MERK:
        a, ph, pt, npl, nmi, ok = test(m, REST[zi])
        ep = {e: float(abstand(echt[namen.index(m)][ok & (EP == e)], REST[zi][ok & (EP == e)])) for e in ("E1", "E2", "E3")}
        ERG[(zi, m)] = (a, ph, pt)
        u = "BELEGT (hoch)" if ph <= ALPHA else ("BELEGT (tief)" if pt <= ALPHA else "nicht belegt")
        print("  %-24s %-12s n+ %3d n- %3d · Abstand %+.4f · E1 %+.4f E2 %+.4f E3 %+.4f · p hoch %.4f tief %.4f · %s"
              % (name, m, npl, nmi, a, ep["E1"], ep["E2"], ep["E3"], ph, pt, u))

# Selbsttest
print("\nSELBSTTEST: %d Welten ohne Makro-Bezug (Ballung und langsame Phasen wie BTC) gegen die echten Scores und die N2-Bank" % N_SELBST)
fa = {k: [0, 0] for k in ERG}
for w in range(N_SELBST):
    Zs = ziele(welt())
    for zi in ("a", "b"):
        y = rest(Zs, zi)
        for m in MERK:
            _a, ph, pt, *_ = test(m, y)
            fa[(zi, m)][0] += ph <= ALPHA
            fa[(zi, m)][1] += pt <= ALPHA
    if (w + 1) % 50 == 0:
        print("  ... %d Welten (%.0f s)" % (w + 1, time.time() - t0), flush=True)
oben = binom.ppf(0.975, N_SELBST, ALPHA)
for k, (h, t) in fa.items():
    print("  %-3s %-12s Fehlalarm hoch %d tief %d von %d (Soll %.1f je Seite, Band bis %d) %s"
          % (k[0], k[1], h, t, N_SELBST, N_SELBST * ALPHA, oben, "✔" if max(h, t) <= oben else "✘"))

print("\nAUFLOESUNG (Pflanzung log sigma += beta * Gesamt lang, %d Welten je beta, Fundquote Ziel a bei p tief <= alpha):" % N_PFL)
for beta in (0.05, 0.10, 0.20, 0.30):
    fund = 0
    for _ in range(N_PFL):
        y = rest(ziele(welt(-beta)), "a")      # Rueckenwind (+1) -> weniger Schwankung: Abstand negativ
        _a, ph, pt, *_ = test("Gesamt lang", y)
        fund += pt <= ALPHA
    print("  beta %.2f (Gegen- gegen Rueckenwind %.0f %% mehr Schwankung)  Fundquote %d %%" % (beta, 100 * (np.exp(2 * beta) - 1), 100 * fund / N_PFL))
print("\nLaufzeit %.0f s" % (time.time() - t0))
