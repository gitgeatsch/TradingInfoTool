"""P83 MESSPLAN R FASSUNG 1 (Voranalyse_REGEL0_Robustheit_24_10.md §5, Auslegung §5.1, vorab de529dc4): Robustheit der REGEL0 gegen den
Datenbeginn und Zerlegung nach Bausteinen.

    python -X utf8 Basisinfos/Rechenkern_02_10/p83_robustheit_r.py --selbsttest     nur R-R11 (i) und Selbsttest (vor dem ersten Blick)
    python -X utf8 Basisinfos/Rechenkern_02_10/p83_robustheit_r.py                  Selbsttest, dann R1 und R2

Z1 = 24-h-Ertrag (Schluss zu Schluss, ohne Kosten) minus Drift Coin-Jahr (Mittel aller gueltigen Stunden des Coins im Jahr = Erwartung
der p69-Nullwelt), je Handel und je Tag (Gewicht 1/Handel am Tag). Rang: p69 (1.000 Ziehungen Zufallsstunden) oder - wenn dessen
Fehlalarm im Selbsttest (a) > 5 % - der Tagesblock-Rang (7-Tage-Bloecke, 1.000 Ziehungen). Betriebscode unveraendert; R1 ueber
lade_reihen(ab=S), R2 ueber eine Quelltextkopie von rechne mit Schaltern B2-B4 (R-R11 der Kopie) und erster_anker (B1).
Liest nur; schreibt data/_hist/einstiege_R*.csv und die Ausgabe.
"""
import inspect
import os
import sqlite3
import sys
from datetime import datetime

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, HIER)
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
import agent.regel0_rechnung as R0  # noqa: E402

K2 = R0.K2
HIST = os.path.join("data", "_hist")
GRUPPE = os.path.join("data", "_vergleich", "kern48jbz_gruppe_bestand.csv")
REF = os.path.join("data", "_vergleich", "kern48jbz_einstiege_bestand.csv")
STARTS = ("2019-06", "2020-06", "2021-06", "2021-12", "2022-06", "2023-01")
KOSTEN = 0.0048
ZIEH = 1000
B0 = pd.Timestamp("2020-01-01")
TAGE = pd.date_range("2024-01-01", "2026-08-31", freq="D")
T0 = int((TAGE[0] - B0) / pd.Timedelta(hours=1))


# ── Kurse ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
class Kurse:
    def __init__(self):
        self.k = {}
        self.con = [sqlite3.connect("file:%s/%s?mode=ro" % (HIST.replace("\\", "/"), d), uri=True) for d in ("stundenkurse.db", "stundenkurse_alle.db")]

    def reihe(self, s):
        if s not in self.k:
            d = {}
            for c in self.con:
                for st, cl in c.execute("SELECT stunde, close FROM stundenkurse WHERE symbol=? AND stunde >= '2023-12-01'", (s,)):
                    d.setdefault(st, cl)
            if not d:
                self.k[s] = None
                return None
            hs = ((pd.to_datetime(list(d.keys())) - B0) / pd.Timedelta(hours=1)).astype(int).to_numpy()
            a = hs.min()
            C = np.full(hs.max() - a + 25, np.nan)
            C[hs - a] = np.array(list(d.values()), float)
            r = C[24:] / C[:-24] - 1                                   # r[i] = Ertrag ab Stunde a+i
            st = a + np.arange(len(r))
            jahr = (B0 + pd.to_timedelta(st, unit="h")).year.to_numpy()
            ok = np.isfinite(r)
            drift = {j: float(r[ok & (jahr == j)].mean()) for j in (2024, 2025, 2026) if (ok & (jahr == j)).any()}
            self.k[s] = (a, r, jahr, ok, drift)
        return self.k[s]


def bewerte(E, K):
    """Einstiege (symbol, stunde) -> DataFrame mit r, drift, tag (Index in TAGE), jahr, ex = r - drift."""
    z = []
    for s, st in zip(E.symbol, E.stunde):
        x = K.reihe(s)
        if x is None:
            continue
        a, r, jahr, ok, drift = x
        i = int(st) - a
        if 0 <= i < len(r) and ok[i] and jahr[i] in drift:
            z.append((s, int(st), r[i], drift[jahr[i]], (int(st) - T0) // 24, int(jahr[i])))
    D = pd.DataFrame(z, columns=["symbol", "stunde", "r", "drift", "tag", "jahr"])
    D = D[(D.tag >= 0) & (D.tag < len(TAGE))].reset_index(drop=True)
    D["ex"] = D.r - D.drift
    D["w_tag"] = 1.0 / D.groupby("tag").tag.transform("size")
    return D


def z1(D, gew, maske=None):
    d = D if maske is None else D[maske]
    w = np.ones(len(d)) if gew == "handel" else d.w_tag.to_numpy()
    return float((w * d.ex.to_numpy()).sum() / max(w.sum(), 1e-12))


def rang_p69(D, gew, K, rng, zieh=ZIEH):
    """p69-Nullwelt: je Einstieg eine Zufallsstunde desselben Coins im selben Jahr; Gewichte wie die echten Einstiege."""
    echt = z1(D, gew)
    w_all = np.ones(len(D)) if gew == "handel" else D.w_tag.to_numpy()
    summe = np.zeros(zieh)
    for (s, j), g in D.groupby(["symbol", "jahr"]):
        a, r, jahr, ok, drift = K.reihe(s)
        kand = np.flatnonzero(ok & (jahr == j))
        idx = rng.choice(kand, (zieh, len(g)))
        summe += ((r[idx] - drift[j]) * w_all[g.index.to_numpy()][None, :]).sum(axis=1)
    null = summe / w_all.sum()
    return float(np.mean(null < echt))


def tagesaggregat(D, gew):
    w = np.ones(len(D)) if gew == "handel" else D.w_tag.to_numpy()
    sx = np.bincount(D.tag, weights=w * D.ex.to_numpy(), minlength=len(TAGE))
    sw = np.bincount(D.tag, weights=w, minlength=len(TAGE))
    return sx, sw


def rang_block(D, gew, rng, zieh=ZIEH, maske_tage=None):
    sx, sw = tagesaggregat(D, gew)
    if maske_tage is not None:
        sx, sw = sx[maske_tage], sw[maske_tage]
    n = len(sx)
    nb = max(n // 7, 1)
    st = rng.integers(0, max(n - 7, 1), (zieh, nb))
    ix = (st[:, :, None] + np.arange(7)).reshape(zieh, -1)
    z = sx[ix].sum(axis=1) / np.maximum(sw[ix].sum(axis=1), 1e-12)
    return float(np.mean(z > 0))


# ── Zufallsregeln mit der Tagesballung der Referenz (Selbsttest a/b) ─────────────────────────────────────────────────────
def zufallsregel(D, K, rng):
    """Die Tage der Referenz werden je Jahr zufaellig auf andere Tage gelegt; je Einstieg eine gueltige Stunde des Coins am neuen Tag."""
    neu = []
    for j in (2024, 2025, 2026):
        tj = np.flatnonzero(TAGE.year == j)
        alt = np.unique(D.tag[D.jahr == j])
        ziel = rng.choice(tj, len(alt), replace=False)
        abb = dict(zip(alt, ziel))
        for s, t in zip(D.symbol[D.jahr == j], D.tag[D.jahr == j]):
            a, r, jahr, ok, drift = K.reihe(s)
            h0 = T0 + 24 * abb[t] - a
            kand = [h for h in range(h0, h0 + 24) if 0 <= h < len(r) and ok[h] and jahr[h] == j]
            if not kand:
                kand = np.flatnonzero(ok & (jahr == j))
            neu.append((s, a + int(rng.choice(kand))))
    return bewerte(pd.DataFrame(neu, columns=["symbol", "stunde"]), K)


def selbsttest(Dref, K):
    rng = np.random.default_rng(83)
    fa = {"p69": {"handel": 0, "tag": 0}, "block": {"handel": 0, "tag": 0}}
    fu = {"p69": {"handel": 0, "tag": 0}, "block": {"handel": 0, "tag": 0}}
    for i in range(100):
        Z = zufallsregel(Dref, K, rng)
        Zp = Z.copy()
        Zp["ex"] = Zp.ex + 0.005
        for gew in ("handel", "tag"):
            fa["p69"][gew] += rang_p69(Z, gew, K, rng, 200) >= 0.95
            fa["block"][gew] += rang_block(Z, gew, rng) >= 0.95
            fu["p69"][gew] += rang_p69(Zp, gew, K, rng, 200) >= 0.95
            fu["block"][gew] += rang_block(Zp, gew, rng) >= 0.95
    print("SELBSTTEST (100 Zufallsregeln mit der Tagesballung der Referenz):")
    for k in ("p69", "block"):
        print("  Rang %-5s  Fehlalarm je Handel %d %% / je Tag %d %% (Soll <= 5) · gepflanzt +0,5 Pp erkannt je Handel %d %% / je Tag %d %% (Soll >= 80)"
              % (k, fa[k]["handel"], fa[k]["tag"], fu[k]["handel"], fu[k]["tag"]))
    gilt = "p69" if max(fa["p69"].values()) <= 5 else "block"
    ok = max(fa[gilt].values()) <= 5 and min(fu[gilt].values()) >= 80
    print("  -> es gilt der Rang '%s' (%s) · Selbsttest %s\n" % (gilt, "p69-Nullwelt" if gilt == "p69" else "Tagesblock-Bootstrap",
                                                               "BESTANDEN" if ok else "NICHT BESTANDEN"))
    return gilt, ok


# ── Laeufe ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def als_df(R):
    e = R["einstiege"]
    return pd.DataFrame({"symbol": [R["syms"][int(R["SYM"][i])] for i in e], "stunde": R["STD"][e].astype(int), "jahr": R["JAHR"][e].astype(int)})


def kopie():
    src = inspect.getsource(R0.rechne)
    ers = [('        hi = np.searchsorted(st, st - 24, "right")\n        k = hi - lo\n',
            '        hi = np.searchsorted(st, st - 24, "right")\n'
            '        if _B4:\n'
            '            lo = np.minimum(np.maximum(lo, np.searchsorted(st, _REFSTART.get(syms[int(SYM[tl[0]])], -10 ** 9), "left")), hi)\n'
            '        k = hi - lo\n'),
           ("fen = BASIS & (STD >= ab) & (MON < mi) & (STD < start - 24)", "fen = BASIS & (STD >= ab) & (MON < mi) & (STD < start - 24) & (_INREF if _B2 else True)"),
           ("ixp = np.flatnonzero(BASIS & (MON == mi - 1))", "ixp = np.flatnonzero(BASIS & (MON == mi - 1) & (_INREF if _B3 else True))")]
    for a, b in ers:
        if src.count(a) != 1:
            raise SystemExit("ABBRUCH: Stelle %r kommt %d-mal vor" % (a[:50], src.count(a)))
        src = src.replace(a, b)
    ns = dict(vars(R0))
    exec(compile(src, "<rechne_r2>", "exec"), ns)  # noqa: S102 - eigener, oben geprueft ersetzter Quelltext
    return ns


def zeile(name, E, D, Dref_keys, K, rang, rng, gilt):
    k = set(zip(E.symbol, E.stunde))
    gleich = len(k & Dref_keys) / max(len(k | Dref_keys), 1)
    netto = float((D.r - KOSTEN).mean())
    out = {"name": name, "n": len(E), "gleich": gleich, "netto": netto}
    for gew in ("handel", "tag"):
        out["z1_" + gew] = z1(D, gew)
        out["rang_" + gew] = rang_p69(D, gew, K, rng) if gilt == "p69" else rang_block(D, gew, rng)
        for j in (2025, 2026):
            out["z1_%s_%d" % (gew, j)] = z1(D, gew, D.jahr == j)
    print("  %-26s %6d Einst. · gleich %5.1f %% · netto %+.3f %% · Z1 je Handel %+.3f %% (Rang %.3f; 2025 %+.3f / 2026 %+.3f) · "
          "je Tag %+.3f %% (Rang %.3f; 2025 %+.3f / 2026 %+.3f)" % (
              name, out["n"], 100 * gleich, 100 * netto, 100 * out["z1_handel"], out["rang_handel"], 100 * out["z1_handel_2025"],
              100 * out["z1_handel_2026"], 100 * out["z1_tag"], out["rang_tag"], 100 * out["z1_tag_2025"], 100 * out["z1_tag_2026"]), flush=True)
    return out


def main():
    print("P83 MESSPLAN R · %s\n" % datetime.now().strftime("%Y-%m-%d %H:%M"))
    zus = R0.zusatz_aus_gruppe(GRUPPE)
    K = Kurse()
    Eref = pd.read_csv(REF, sep=";")
    Dref = bewerte(Eref, K)
    n25 = float((Dref.r[Dref.jahr == 2025] - KOSTEN).mean())
    n26 = float((Dref.r[Dref.jahr == 2026] - KOSTEN).mean())
    rr1 = abs(n25 - 0.00132) < 5e-6 and abs(n26 + 0.00021) < 5e-6
    print("R-R11 (i) Referenz netto 2025 %+.3f %% / 2026 %+.3f %% (p69 ohne Limit +0,132 / -0,021) -> %s · bewertet %d von %d Einstiegen\n" % (
        100 * n25, 100 * n26, "ok" if rr1 else "ABWEICHUNG", len(Dref), len(Eref)))
    if not rr1:
        return 1
    gilt, ok = selbsttest(Dref, K)
    if not ok:
        print("Selbsttest nicht bestanden - es wird NICHT gemessen (§5).")
        return 1
    if "--selbsttest" in sys.argv:
        return 0
    rng = np.random.default_rng(830)
    keys = set(zip(Eref.symbol, Eref.stunde))
    E = []
    print("R1 gemeinsamer Datenbeginn (Rang: %s)" % gilt)
    E.append(zeile("Referenz (gemischt)", Eref, Dref, keys, K, gilt, rng, gilt))
    A_lang = None
    for S in STARTS:
        A = R0.anker(R0.lade_reihen(HIST, zus, ab=S + "-01 00:00"), zukunft_bekannt=True)
        R = R0.rechne(A, set(zus), K2.ROLL_MONATE)
        Es = als_df(R)
        Es.to_csv(os.path.join(HIST, "einstiege_R1_%s.csv" % S), sep=";", index=False)
        if S == "2019-06":
            A_lang = A
            a = pd.read_csv(os.path.join(HIST, "einstiege_A.csv"), sep=";")
            gl = set(zip(a.symbol, a.stunde)) == set(zip(Es.symbol, Es.stunde))
            print("  R-R11 (ii) S = 2019-06 gleich einstiege_A.csv: %s" % ("ZEILENGLEICH" if gl else "ABWEICHUNG"), flush=True)
        E.append(zeile("Start %s" % S, Es, bewerte(Es, K), keys, K, gilt, rng, gilt))
    r1 = [e for e in E if e["name"].startswith("Start")]
    k1 = sum(e["z1_handel"] > 0 and e["rang_handel"] >= 0.95 and e["z1_tag"] > 0 and e["rang_tag"] >= 0.95 for e in r1)
    k2 = sum(all(e["z1_%s_%d" % (g, j)] > 0 for g in ("handel", "tag") for j in (2025, 2026)) for e in r1)
    robust = k1 >= 5 and k2 >= 4
    print("  -> Kriterium (1) %d von 6 (Soll >= 5) · Kriterium (2) %d von 6 (Soll >= 4) -> URTEIL: %s\n" % (
        k1, k2, "ROBUST" if robust else "NICHT ROBUST"))
    # R2 Zerlegung auf S = 2019-06
    print("R2 Zerlegung auf Start 2019-06 (je Baustein auf den Referenzstand)")
    A_ref = R0.anker(R0.lade_reihen("data", zus), zukunft_bekannt=True)
    refstart = {A_ref["syms"][s]: int(A_ref["STD"][A_ref["SYM"] == s].min()) for s in np.unique(A_ref["SYM"])}
    syms = A_lang["syms"]
    rs = np.array([refstart.get(s, -10 ** 9) for s in syms])
    ns = kopie()
    ns["_INREF"] = A_lang["STD"] >= rs[A_lang["SYM"]]
    ns["_REFSTART"] = refstart
    ns["_B2"] = ns["_B3"] = ns["_B4"] = False
    R = ns["rechne"](A_lang, set(zus), K2.ROLL_MONATE)
    E0 = als_df(R)
    a = pd.read_csv(os.path.join(HIST, "einstiege_A.csv"), sep=";")
    gl = set(zip(a.symbol, a.stunde)) == set(zip(E0.symbol, E0.stunde))
    print("  R-R11 (iii) Kopie mit allen Schaltern aus gleich einstiege_A.csv: %s" % ("ZEILENGLEICH" if gl else "ABWEICHUNG"), flush=True)
    if not gl:
        return 1
    for name, b1, b2, b3, b4 in (("B1 Reife", 1, 0, 0, 0), ("B2 Trainingsmenge", 0, 1, 0, 0), ("B3 Schrumpfung", 0, 0, 1, 0),
                                 ("B4 eigenes Normal", 0, 0, 0, 1), ("B1-B4 zusammen", 1, 1, 1, 1)):
        ns["_B2"], ns["_B3"], ns["_B4"] = bool(b2), bool(b3), bool(b4)
        R = ns["rechne"](A_lang, set(zus), K2.ROLL_MONATE, erster_anker=refstart if b1 else None)
        Eb = als_df(R)
        Eb.to_csv(os.path.join(HIST, "einstiege_R2_%s.csv" % name.split()[0]), sep=";", index=False)
        e = zeile(name, Eb, bewerte(Eb, K), keys, K, gilt, rng, gilt)
        if name.startswith("B1-B4"):
            print("  -> alle vier zusammen bilden die Referenz zu %.1f %% nach (Soll >= 90 %%): %s" % (
                100 * e["gleich"], "Zerlegung vollstaendig" if e["gleich"] >= 0.90 else "UNVOLLSTAENDIG - ein weiterer Baustein"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
