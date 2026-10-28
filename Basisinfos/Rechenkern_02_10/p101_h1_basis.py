"""P101 Basis fuer Messplan H-1 Fassung 2 (Basisinfos/Messplan_H1_Lagegerechte_Handlung_28_10.md, E-165). Nur lesend.

Gemeinsam fuer Vorpruefung, Selbsttest, Messung (Gegenprobe rechnet bewusst NICHT hiermit):
  tabelle(menge)   je REGEL0-Einstieg mit lueckenlosen 168 h: tag, jahr, Ertraege r6/r24/r72/r120/rF (brutto, Spot-Stundenkurse),
                   Zustaende a/b/c (Tagesschluss Vortag, messdaten.db), extrem (2.648 zur Einstiegsstunde), atr
  klammer(...)     Tagesklammer: je Tag mit beiden Zustaenden Mittel(D | Zustand) - Mittel(D | nicht), Mittel ueber die Tage
  urteil(...)      Band (Block-Bootstrap), Nullpunkt (Nullwelt: Zustand im Tag vertauscht), Stufe nach messnorm

Quellen wie p62: stundenkurse.db, stundenkurse_alle.db, eingestellt_historie.db (die erste Datei gewinnt). Die ATR ist die des
Betriebs (messe_e2_beitraege._atr = agent.regel0_rechnung.atr_je_stunde); Extrem ueber messe_assetebene_und_vorhersage.merkmale.
Zwischenablage: data/_h1/ (gitignored, keine Produktion). Die Produktionsdatei data/tradinginfotool.db wird nie geoeffnet.
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
import messe_e2_beitraege as E2                                   # noqa: E402
import messnorm as N                                              # noqa: E402
from messe_assetebene_und_vorhersage import merkmale              # noqa: E402

DATEIEN = ("stundenkurse.db", "stundenkurse_alle.db", "eingestellt_historie.db")
MENGEN = ("bestand", "unverzerrt_1", "unverzerrt_2", "unverzerrt_3")
B0 = pd.Timestamp("2020-01-01")
H_MAX = 168
F_H, F_K = 120, 1.5                     # Fuehrung: nachgezogener Stop 1,5 ATR, hoechstens 120 h, Ausstieg an der Linie (Verzug 0)
MOM_X, RSI_X = 0.8509, 85.6631          # Extrem-Schwellen aus 2.648
ABLAGE = os.path.join(WURZEL, "data", "_h1")
BOOT = 2000
NULL_N = 40                             # Messstandard 09.09.: Nullpunkt = Mittel aus 40 Ziehungen
ALPHA = 0.05                            # zweiseitig, je Hypothese geteilt (Bonferroni)
GESCHUETZT = [os.path.join(WURZEL, "data", "tradinginfotool.db")]
# Instrument (Messplan Fassung 4): LOG = Differenz der Log-Ertraege statt der einfachen; BAND = "t" (cluster-robust ueber Bloecke,
# t-Quantil mit nb-1 Freiheitsgraden und Faktor sqrt(nb/(nb-1)) wie agent.regel0_messstand._kennzahl) oder "boot" (Perzentile)
LOG = True
BAND = "t"


def ro(datei):
    return sqlite3.connect("file:%s?mode=ro" % os.path.join(WURZEL, "data", datei).replace("\\", "/"), uri=True)


def fingerabdruck():
    """(Groesse, Aenderungszeit) der geschuetzten Dateien - vorher/nachher gleich (Seiteneffekt-Pruefung)."""
    return [(p, os.path.getsize(p), os.path.getmtime(p)) if os.path.exists(p) else (p, None, None) for p in GESCHUETZT]


# ── Kurse ────────────────────────────────────────────────────────────────────────────────────────────────────────────────
_con = None


def _verbindungen():
    global _con
    if _con is None:
        _con = {d: ro(d) for d in DATEIEN if os.path.exists(os.path.join(WURZEL, "data", d))}
    return _con


def stundenreihe(sym):
    """-> (a, H, L, C, atr, mom, rsi) je Stunde seit B0 ab Index a (Luecken NaN); die erste Datei gewinnt. Merkmale und ATR auf
    der gespeicherten Zeilenfolge (ohne Luecken) gerechnet, wie die Lader von 2.648 und E2."""
    d = {}
    for c in _verbindungen().values():
        for st, h, lo, cl in c.execute("SELECT stunde, high, low, close FROM stundenkurse WHERE symbol=?", (sym,)):
            d.setdefault(st, (h, lo, cl))
    if not d:
        return None
    st = sorted(d)
    hs = ((pd.to_datetime(st) - B0) / pd.Timedelta(hours=1)).astype(int).to_numpy()
    v = np.array([d[s] for s in st], float)
    h, lo, cl = v[:, 0], v[:, 1], v[:, 2]
    atr_z = E2._atr(h, lo, cl)
    mk, _ = merkmale(h, lo, cl)
    a = hs.min()
    n = hs.max() - a + 1
    aus = [np.full(n, np.nan) for _ in range(6)]
    for arr, werte in zip(aus, (h, lo, cl, atr_z, mk["momentum_kurz"], mk["rsi"])):
        arr[hs - a] = werte
    return (a, *aus)


def tagesreihe(sym, con):
    s = pd.read_sql("SELECT date, close FROM price_history_ohlc WHERE symbol=? AND assetklasse='krypto' ORDER BY date",
                    con, params=(sym,))
    if s.empty:
        return None
    s["date"] = pd.to_datetime(s.date)
    return s.set_index("date").close


def zustaende(sym, s, btc):
    """Stand VORTAG je Kalendertag: a eigener 50-T-Schnitt, b 200-T, c Ertrag 30 T gegen BTC > 0, m BTC ueber 200-T (Auskunft)."""
    a = (s > s.rolling(50).mean()).where(s.rolling(50).count() >= 50)
    b = (s > s.rolling(200).mean()).where(s.rolling(200).count() >= 200)
    rel = (s / s.shift(30)) / (btc.reindex(s.index) / btc.reindex(s.index).shift(30)) - 1
    c = (rel > 0).where(rel.notna())
    m = (btc > btc.rolling(200).mean()).reindex(s.index)
    return pd.DataFrame({"a": a, "b": b, "c": c, "m": m}).shift(1)


# ── Je Einstieg ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def _ertraege(r, i):
    a, H, L, C, A, M, R = r
    j = i - a
    if j < 0 or j + H_MAX >= len(C):
        return None
    c0 = C[j]
    hh, ll, cc = H[j + 1:j + H_MAX + 1], L[j + 1:j + H_MAX + 1], C[j + 1:j + H_MAX + 1]
    if not (np.isfinite(c0) and c0 > 0 and np.isfinite(hh).all() and np.isfinite(ll).all() and np.isfinite(cc).all()):
        return None
    aus = {"r%d" % h: cc[h - 1] / c0 - 1 for h in (6, 24, 72, 120, 168)}
    atr = A[j]
    rf = np.nan
    if np.isfinite(atr):
        mx, rf = 1.0, cc[F_H - 1] / c0 - 1
        for s in range(F_H):
            lin = mx - F_K * atr
            if ll[s] / c0 <= lin:
                rf = lin - 1
                break
            mx = max(mx, hh[s] / c0)
    aus["rF"] = rf
    aus["atr"] = atr
    aus["extrem"] = float((M[j] >= MOM_X) or (R[j] >= RSI_X)) if (np.isfinite(M[j]) or np.isfinite(R[j])) else np.nan
    aus["ext_mom"] = float(M[j] >= MOM_X) if np.isfinite(M[j]) else np.nan      # zweiter Weg H-1c (Fassung 3): je Merkmal
    aus["ext_rsi"] = float(R[j] >= RSI_X) if np.isfinite(R[j]) else np.nan
    return aus


def tabelle(menge, neu=False):
    """DataFrame je Einstieg der Menge (zwischengespeichert in data/_h1/)."""
    os.makedirs(ABLAGE, exist_ok=True)
    pfad = os.path.join(ABLAGE, "h1_%s.csv" % menge)
    if os.path.exists(pfad) and not neu:
        return pd.read_csv(pfad, sep=";")
    E = pd.read_csv(os.path.join("data", "_vergleich", "kern48jbz_einstiege_%s.csv" % menge), sep=";")
    md = ro("messdaten.db")
    btc = tagesreihe("BTC", md)
    zst, rh = {}, {}
    zeilen = []
    for e in E.itertuples():
        if e.symbol not in rh:
            rh[e.symbol] = stundenreihe(e.symbol)
            s = tagesreihe(e.symbol, md)
            zst[e.symbol] = zustaende(e.symbol, s, btc) if s is not None else None
        r = rh[e.symbol]
        if r is None:
            continue
        x = _ertraege(r, int(e.stunde))
        if x is None:
            continue
        datum = (B0 + pd.Timedelta(hours=int(e.stunde))).normalize()
        z = zst[e.symbol]
        zw = z.loc[datum] if (z is not None and datum in z.index) else None
        for k in "abcm":
            x[k] = float(zw[k]) if (zw is not None and pd.notna(zw[k])) else np.nan
        x.update(symbol=e.symbol, stunde=int(e.stunde), jahr=int(e.jahr), tag=int(e.stunde) // 24)
        zeilen.append(x)
    md.close()
    D = pd.DataFrame(zeilen).sort_values(["tag", "stunde", "symbol"]).reset_index(drop=True)
    D.to_csv(pfad, sep=";", index=False)
    return D


# ── Tagesklammer, Band, Nullwelt, Urteil ─────────────────────────────────────────────────────────────────────────────────
def je_tag(tag, zustand, delta):
    """-> (tage, d_t): je Tag mit beiden Zustaenden Mittel(delta | 1) - Mittel(delta | 0). Eingaben nach Tag sortiert."""
    ok = np.isfinite(zustand) & np.isfinite(delta)
    tag, z, d = tag[ok], zustand[ok].astype(bool), delta[ok]
    tg, inv = np.unique(tag, return_inverse=True)
    n1 = np.bincount(inv, weights=z, minlength=len(tg)); s1 = np.bincount(inv, weights=d * z, minlength=len(tg))
    n0 = np.bincount(inv, weights=~z, minlength=len(tg)); s0 = np.bincount(inv, weights=d * ~z, minlength=len(tg))
    beide = (n1 > 0) & (n0 > 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        dt = s1 / n1 - s0 / n0
    return tg[beide], dt[beide]


def klammer(tag, zustand, delta):
    tg, dt = je_tag(tag, zustand, delta)
    return float(dt.mean()) if len(dt) else float("nan")


def tausche_im_tag(tag, zustand, rng):
    """Zustaende innerhalb jedes Tages zufaellig vertauscht (Anteil und Ballung je Tag bleiben). tag sortiert."""
    o = np.lexsort((rng.random(len(tag)), tag))
    return zustand[o]


def band(tg, dt, rng, alpha, block=None):
    """Band ueber Kalenderbloecke (BAND = "t" oder "boot"); -> (unten, oben, n_bloecke, block)."""
    block = block or N._block(5)
    b = (tg - tg.min()) // block
    ub, inv = np.unique(b, return_inverse=True)
    s = np.bincount(inv, weights=dt); k = np.bincount(inv)
    nb = len(ub)
    if BAND == "t":
        from scipy.stats import t as _t
        m = s.sum() / k.sum()
        halb = _t.ppf(1 - alpha / 2, nb - 1) * np.sqrt(nb / (nb - 1)) * np.sqrt(((s - m * k) ** 2).sum()) / k.sum()
        return float(m - halb), float(m + halb), nb, block
    z = rng.integers(0, nb, size=(BOOT, nb))
    m = s[z].sum(1) / k[z].sum(1)
    return float(np.quantile(m, alpha / 2)), float(np.quantile(m, 1 - alpha / 2)), nb, block


def nullwelt(tag, zustand, delta, rng, n=NULL_N):
    w = [klammer(tag, tausche_im_tag(tag, zustand, rng), delta) for _ in range(n)]
    return float(np.mean(w)), float(np.quantile(w, 0.9)), float(np.quantile(w, 0.1))


def bewerte(tag, zustand, delta, rng, hypothesen, aufloesung=None, null=True, block=None):
    """-> dict mit Mittel, Band, Nullpunkt, Bloecken, Autokorrelation und Stufe (messnorm: TRAEGT / TRAEGT NICHT BIS X /
    NICHT TRENNBAR / KEIN BEFUND). Zweiseitig: TRAEGT, wenn das Band den Nullpunkt ausschliesst (Vorzeichen ausgewiesen).
    Nur Einstiege mit Zustand UND Delta gehen ein - auch in die Nullwelt (sonst wanderten fehlende Zustaende mit)."""
    ok = np.isfinite(zustand) & np.isfinite(delta)
    tag, zustand, delta = tag[ok], zustand[ok], delta[ok]
    tg, dt = je_tag(tag, zustand, delta)
    if len(dt) < 2:
        return {"stufe": "KEIN BEFUND - keine Klammertage", "n_tage": int(len(dt)), "n_bloecke": 0, "mittel": float("nan")}
    alpha = ALPHA / hypothesen
    u, o, nb, blk = band(tg, dt, rng, alpha, block)
    npkt, n90, n10 = nullwelt(tag, zustand, delta, rng) if null else (0.0, 0.0, 0.0)
    pb = N.pruefe_block(dict(zip(tg.tolist(), dt.tolist())), blk)
    m = float(dt.mean())
    if nb < 20:
        st = "KEIN BEFUND - nur %d Bloecke" % nb
    elif not pb["ok"] and np.isfinite(pb["ak"]):
        st = "KEIN BEFUND - Block %d zu kurz (AK %.3f)" % (blk, pb["ak"])
    elif u > npkt or o < npkt:
        st = "TRAEGT (%s)" % ("Differenz im Zustand HOEHER" if m > npkt else "Differenz im Zustand NIEDRIGER")
    elif aufloesung is not None and (o - npkt) < aufloesung and (npkt - u) < aufloesung:
        st = "TRAEGT NICHT BIS %.2f Pp" % (100 * aufloesung)
    else:
        st = "NICHT TRENNBAR"
    return {"mittel": m, "unten": u, "oben": o, "nullpunkt": npkt, "null90": n90, "null10": n10, "n_tage": int(len(dt)),
            "n_bloecke": nb, "block": blk, "ak": pb["ak"], "stufe": st}


# Vorab-Hypothesen (Messplan §4): (Name, Zustand, Delta-Spalten)
H1B = (("D72", "r72", "r24"), ("D120", "r120", "r24"), ("DF", "rF", "r24"))
H1C = (("D6", "r6", "r24"), ("D72", "r72", "r24"))


def delta(D, lang, kurz):
    """Ertragsdifferenz je Einstieg; LOG: ln(1 + r_lang) - ln(1 + r_kurz) (Untergrenze -99 % gegen log(0))."""
    if LOG:
        return (np.log1p(D[lang].clip(lower=-0.99)) - np.log1p(D[kurz].clip(lower=-0.99))).to_numpy(float)
    return (D[lang] - D[kurz]).to_numpy(float)
