"""REGEL0.1-Rechenkern fuer den Betrieb (Schritt 7, S7-2 mit S7-3; Voranalyse_Schritt7_Betrieb_02_10.md Abschnitt 12, E-45, Befund 2.708).

Rechnet die REGEL0 in der Fassung 0.1 (kausale Schrumpfung) - dieselben Einstiege wie die Messung, ohne Vorgriff:

    Daten        nur lesend aus den REGEL0-Dateien (stundenkurse.db = Messbasis, stundenkurse_alle.db = Zusatz-Assets)
    Anker        Ankermaske wie messe_e2_beitraege.lade (240 h lueckenloser Vorlauf, 72 h Vorausblick). Im Betrieb ist die Zukunft
                 unbekannt: dann gelten die letzten Stunden als Anker, wenn die Reihe bis zum Ende lueckenlos ist (wie bis_ende, B-3)
    Merkmale     rsi14 (14 Zeilen) -> rsi_s (minus Median 720 h) und rsi_s24; Ereignis q5 (+5 % vor -5 % binnen 24 h)
    Normal       eigenes Normal (Jahresfenster bis t-24 h, J ab 240 h), Schrumpfung KAUSAL aus dem Vormonat (2.708)
    Modell       Kurvenmodell Form b auf rsi_s/rsi_s24, monatlich, Daempfung GITTER_NEU (messe_k1_schritt2b_kombination)
    Einstieg     v-dach >= +0,035, Ruhe 48 h (>= 40 gueltige), nicht in den ersten 24 h des Monats, Einstieg 1 h spaeter

⚠️ GLEICHHEIT IST EINGEBAUT, NICHT NACHGEBAUT: die Rechenbausteine kommen aus den Messmodulen (``E2._rsi14``, ``E2.ergebnisse``,
``K2.Modell``/``K2.fit_cv``, ``monat_von``). Die Schritte dazwischen folgen ``messe_losfahren.py`` (Zeilenangaben je Funktion).
Gepruefft wird das an der Referenz (R-R11): ``kern48jbz_einstiege_bestand.csv`` (= ``kern48jbzk``, Fassung 0.1) zeilengleich.

⚠️ SCHREIBT NICHTS ausser der angegebenen Zieldatei. Keine Produktions-DB, kein Netz.

    python -m agent.regel0_rechnung --nachrechnung --zusatz-aus data/_vergleich/kern48jbz_gruppe_bestand.csv --ziel <csv>
"""
from __future__ import annotations

import csv
import os
import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from scipy.special import expit

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HIER not in sys.path:
    sys.path.insert(0, HIER)

import messe_e2_beitraege as E2                                   # noqa: E402
import messe_k1_schritt2b_kombination as K2                       # noqa: E402
from messe_e3_vorwaerts import monat_von                          # noqa: E402
from messe_losfahren import GITTER_NEU                            # noqa: E402

DATEN_VORGABE = os.path.join(HIER, "data")
SCHWELLE = 0.035
RUHE = 48
HMAX = 72
RSI = ("rsi_s", "rsi_s24")
ERSTE = (("u5", 1.05, True), ("d5", 0.95, False))
MONATSANFANG = np.array([K2._h(datetime(2020 + mm // 12, mm % 12 + 1, 1)) for mm in range(0, 12 * 21)])  # bis 2040


@contextmanager
def _modellform(form, lambdas):
    """K2 haelt Form und Daempfungsraster als Modulvariablen - fuer jeden Fit setzen und danach zuruecksetzen."""
    alt = (K2.FORM, K2.LAMBDAS, K2.STETIG)
    K2.FORM, K2.LAMBDAS, K2.STETIG = form, lambdas, False
    try:
        yield
    finally:
        K2.FORM, K2.LAMBDAS, K2.STETIG = alt


def _ro(pfad):
    return sqlite3.connect("file:%s?mode=ro" % pfad.replace("\\", "/"), uri=True)


def lade_reihen_iter(ordner: str, zusatz: list, ab: str | None = None, bis: str | None = None):
    """Wie ``lade_reihen``, aber JE ASSET nacheinander (Generator): die Rohzeilen eines Assets sind nach seiner Verarbeitung frei.
    Gemessen 02.10.: alle Rohzeilen auf einmal kosten im Stundenlauf 1,5 GB (Python-Tupel), die Ankerreihe daraus 0,16 GB -
    am Notebook (8,3 GB, 1,8 GB frei) waere das der Engpass. ``bis``: einschliesslich dieser Stunde."""
    bed = "".join([" AND stunde >= '%s'" % ab if ab else "", " AND stunde <= '%s'" % bis if bis else ""])
    q = "SELECT stunde, high, low, close FROM stundenkurse WHERE symbol=?%s ORDER BY stunde" % bed
    cs = _ro(os.path.join(ordner, "stundenkurse.db"))
    try:
        bestand = [r[0] for r in cs.execute("SELECT symbol FROM stundenkurse GROUP BY symbol HAVING COUNT(*) > 2000 ORDER BY COUNT(*) DESC")]
        for s in bestand:
            yield s, cs.execute(q, (s,)).fetchall()
    finally:
        cs.close()
    if zusatz:
        ca = _ro(os.path.join(ordner, "stundenkurse_alle.db"))
        try:
            da = {r[0] for r in ca.execute("SELECT symbol FROM stundenkurse GROUP BY symbol HAVING COUNT(*) >= 500")}
            for s in sorted(set(zusatz) - set(bestand)):
                if s in da:
                    yield s, ca.execute(q, (s,)).fetchall()
        finally:
            ca.close()


def lade_reihen(ordner: str, zusatz: list, ab: str | None = None) -> list:
    """-> [(symbol, rows)] wie ``E2.kursreihen`` (Menge bestand) plus ``E2._zusatz``: zuerst die Messbasis (mehr als 2.000 Zeilen,
    Reihenfolge nach Zeilenzahl wie die Messung), dahinter die Zusatz-Assets aus stundenkurse_alle.db (mindestens 500 Zeilen),
    alphabetisch. rows = (stunde, high, low, close). Haelt ALLES im Speicher - im Betrieb ``lade_reihen_iter``."""
    return list(lade_reihen_iter(ordner, zusatz, ab))


def anker(reihen: list, zukunft_bekannt: bool = True) -> dict:
    """Ankerreihe ueber alle Assets (wie ``E2.lade``, messe_e2_beitraege.py:340-433, nur die Groessen der REGEL0).

    zukunft_bekannt=True: Messung (72 h Vorausblick noetig, die letzten 72 h sind keine Anker).
    zukunft_bekannt=False: Betrieb - eine Stunde ohne volle Zukunft zaehlt, wenn die Reihe ab ihr bis zum Ende lueckenlos ist."""
    basis = datetime(2020, 1, 1)
    STD, SYM, RSI14, TU, TD = [], [], [], [], []
    syms = []
    for si, (sym, rows) in enumerate(reihen):
        syms.append(sym)
        if len(rows) < 500:
            continue
        stunde = np.array([int((datetime.strptime(r[0], "%Y-%m-%d %H:%M") - basis).total_seconds() // 3600) for r in rows], np.int64)
        h = np.array([r[1] for r in rows], float)
        lo = np.array([r[2] for r in rows], float)
        cc = np.array([r[3] for r in rows], float)
        n = len(cc)
        idx = np.arange(n)
        gu = np.isfinite(cc) & (cc > 0)
        gu[:E2.VORLAUF] = False
        vor = np.clip(idx - E2.VORLAUF, 0, n - 1)
        nach = np.clip(idx + HMAX, 0, n - 1)
        if zukunft_bekannt:
            gu[max(0, n - HMAX):] = False
            luecke = ((stunde - stunde[vor]) != E2.VORLAUF) | ((stunde[nach] - stunde) != HMAX)
        else:
            drin = idx + HMAX < n
            rest_lueckenlos = (stunde[n - 1] - stunde) == (n - 1 - idx)
            luecke = ((stunde - stunde[vor]) != E2.VORLAUF) | np.where(drin, (stunde[nach] - stunde) != HMAX, ~rest_lueckenlos)
        gu &= ~luecke
        sel = np.flatnonzero(gu)
        if not len(sel):
            continue
        t, _m, _v = E2.ergebnisse(h, lo, cc, HMAX, ERSTE)
        STD.append(stunde[sel]); SYM.append(np.full(len(sel), si, np.int32))
        RSI14.append(E2._rsi14(cc)[sel]); TU.append(t["u5"][sel]); TD.append(t["d5"][sel])
    return dict(STD=np.concatenate(STD), SYM=np.concatenate(SYM), rsi=np.concatenate(RSI14).astype(np.float64),
                t_u=np.concatenate(TU), t_d=np.concatenate(TD), syms=syms)


def rechne(A: dict, zusatz: set, monate: list, modelle: dict | None = None, mit_btc: bool = True, jahre=(2024, 2025, 2026),
           schwelle: float = SCHWELLE, erster_anker: dict | None = None) -> dict:
    """Die REGEL0.1 auf einer Ankerreihe (Schritte wie messe_losfahren.py mit --kern --ruhe 48 --junge --mit-btc [--zusatz]
    --normal kausal). ``modelle`` {Monatsindex: Modell}: vorhandene Monatsmodelle nehmen, sonst je Monat aus ``monate`` trainieren.
    ``jahre`` None: keine Jahresgrenze (Betrieb). ``erster_anker`` {Symbol: Stunde}: der erste Anker der VOLLEN Reihe - noetig,
    wenn nur ein Fenster geladen ist (Reife und Historie haengen am Reihenbeginn, nicht am Fensterbeginn).
    -> dict mit VH, QSh, Einstiegen (Index), Signalstunden, Modellen und den Ankerspalten."""
    SYM, STD, syms = A["SYM"], A["STD"], A["syms"]
    n = len(SYM)
    t_u, t_d = A["t_u"], A["t_d"]
    A24 = ((t_u <= 24) & (t_u < t_d)).astype(np.float64)
    B24 = ((t_d <= 24) & (t_d <= t_u)).astype(np.float64)
    MON = monat_von(STD)
    JAHR = (MON // 12).astype(np.int16)
    ordnung = np.lexsort((STD, SYM))
    teile = np.split(ordnung, np.flatnonzero(np.diff(SYM[ordnung])) + 1)

    # eigenes Normal mit J (messe_losfahren.py:115-138)
    REIF = np.zeros(n, bool); HIST_T = np.full(n, np.nan)
    NA, NB = np.full(n, np.nan), np.full(n, np.nan)
    for tl in teile:
        st = STD[tl]
        st0 = int(erster_anker.get(syms[int(SYM[tl[0]])], st[0])) if erster_anker else st[0]
        ca = np.concatenate([[0.0], np.cumsum(A24[tl])]); cb = np.concatenate([[0.0], np.cumsum(B24[tl])])
        lo = np.searchsorted(st, st - K2.JAHR_H, "left")
        hi = np.searchsorted(st, st - 24, "right")
        k = hi - lo
        gut = (st - st0 >= K2.JAHR_H) & (k > 1000)
        REIF[tl] = gut; HIST_T[tl] = (st - st0) / 24.0
        gut = gut | (((st - st0) >= 240 + 24) & (k > 0))
        NA[tl] = np.where(gut, (ca[hi] - ca[lo]) / np.maximum(k, 1), np.nan)
        NB[tl] = np.where(gut, (cb[hi] - cb[lo]) / np.maximum(k, 1), np.nan)
    # BTC und die Zusatz-Assets: bewertet, nie trainiert (messe_losfahren.py:141-152)
    BTC_I = syms.index("BTC") if (mit_btc and "BTC" in syms) else -1
    REIF[SYM == BTC_I] = False
    ZUS = np.isin(SYM, [syms.index(s) for s in zusatz if s in syms])
    REIF[ZUS] = False
    with np.errstate(divide="ignore", invalid="ignore"):
        q = np.clip(NA / (NA + NB), 0.02, 0.98)
        OFF = np.log(q / (1 - q))

    # rsi_s und rsi_s24 (messe_losfahren.py:166-195)
    E = {"rsi_s": np.full(n, np.nan), "rsi_s24": np.full(n, np.nan)}
    for tl in teile:
        ser = pd.Series(A["rsi"][tl], index=pd.to_datetime(STD[tl].astype("int64") * 3600, unit="s"))
        med = ser.rolling("%dh" % K2.SELBST_H, closed="left", min_periods=240).median().to_numpy()
        E["rsi_s"][tl] = A["rsi"][tl] - med
    for tl in teile:
        ss = STD[tl]
        j = np.searchsorted(ss, ss - 24)
        jj = np.minimum(j, len(ss) - 1)
        ok = (j < len(ss)) & (ss[jj] == ss - 24)
        w = np.full(len(tl), np.nan); w[ok] = E["rsi_s"][tl][jj[ok]]
        E["rsi_s24"][tl] = w

    GRID = np.isin(STD % 24, K2.GITTER)
    BASIS = GRID & np.isfinite(OFF) & REIF & (SYM != BTC_I) & ~ZUS
    HIT = (A24 + B24) > 0
    with np.errstate(divide="ignore", invalid="ignore"):
        QN = NA / (NA + NB)
    basis = np.flatnonzero(BASIS & (MON >= 2024 * 12))

    # Schrumpfung KAUSAL aus dem Vormonat (messe_losfahren.py, Zweig --normal kausal, Befund 2.708)
    QSh = np.full(n, np.nan)
    LAGE = {}
    for mi in np.unique(MON[basis]):
        ixp = np.flatnonzero(BASIS & (MON == mi - 1))
        qp = QN[ixp]; okp = np.isfinite(qp); ixp, qp = ixp[okp], qp[okp]
        if len(ixp) < 500:
            continue
        us, inv = np.unique(SYM[ixp], return_inverse=True)
        qa = np.bincount(inv, weights=qp) / np.bincount(inv)
        rate = np.bincount(inv, weights=(NA[ixp] + NB[ixp])) / np.bincount(inv)
        rausch = qa * (1 - qa) / np.maximum(rate * 365.0, 5.0)
        mitte = float(np.mean(qa)); tau2 = max(float(np.var(qa)) - float(np.mean(rausch)), 0.0)
        LAGE[int(mi)] = (mitte, tau2)
        Bm = dict(zip(us.tolist(), (tau2 / (tau2 + rausch)).tolist()))
        ixh = np.flatnonzero((MON == mi) & np.isfinite(QN))
        mit_vm = REIF[ixh] & np.isin(SYM[ixh], us)
        hv = ixh[mit_vm]
        if len(hv):
            QSh[hv] = mitte + np.array([Bm[int(x)] for x in SYM[hv]]) * (QN[hv] - mitte)
        rest = ixh[~mit_vm]
        for sj in np.unique(SYM[rest]):
            hj = rest[SYM[rest] == sj]; hj = hj[np.argsort(STD[hj], kind="stable")]
            gj = hj[GRID[hj]]

            def _bis_t(ix_, auf_):
                k_ = np.searchsorted(STD[ix_], STD[auf_], "right")
                cq = np.concatenate([[0.0], np.cumsum(QN[ix_])])
                cr = np.concatenate([[0.0], np.cumsum(NA[ix_] + NB[ix_])])
                ct = np.concatenate([[0.0], np.cumsum(HIST_T[ix_])])
                kk = np.maximum(k_, 1)
                return k_, cq[k_] / kk, cr[k_] / kk, ct[k_] / kk
            kg, qg, rg, tg = _bis_t(gj, hj) if len(gj) else (np.zeros(len(hj), int),) * 4
            _kh, qh, rh, th = _bis_t(hj, hj)
            vor = kg > 0
            qa_j = np.where(vor, qg, qh); rate_j = np.where(vor, rg, rh)
            tage_j = np.minimum(365.0, np.where(vor, tg, th))
            r_j = qa_j * (1 - qa_j) / np.maximum(rate_j * tage_j, 5.0)
            with np.errstate(divide="ignore", invalid="ignore"):          # 0/0 wie in der Messung: QSh bleibt dort NaN
                QSh[hj] = mitte + (tau2 / (tau2 + r_j)) * (QN[hj] - mitte)

    # Monatsmodell und Beitrag (messe_losfahren.py:397-415)
    Ch = np.full(n, np.nan)
    modelle = dict(modelle or {})
    ab = K2._h(datetime(2023, 1, 1))
    for (j, mo) in monate:
        mi = j * 12 + (mo - 1)
        if mi not in modelle:
            start = K2._h(datetime(j, mo, 1))
            fen = BASIS & (STD >= ab) & (MON < mi) & (STD < start - 24)
            ra = np.flatnonzero(fen); rt = np.flatnonzero(fen & HIT)
            if len(rt) < 5000:
                continue
            with _modellform("b", GITTER_NEU):
                m, _l = K2.fit_cv(RSI, E, ra, rt, A24[rt], OFF[rt], STD)
            modelle[mi] = m
        alle_h = np.flatnonzero((MON == mi) & np.isfinite(OFF))
        if len(alle_h):
            Ch[alle_h] = modelle[mi].z(E, alle_h, OFF[alle_h]) - OFF[alle_h]
    with np.errstate(divide="ignore", invalid="ignore"):
        VH = expit(np.log(QSh / (1 - QSh)) + Ch) - QSh

    # Ersteintritt mit Ruhe 48 h, Einstieg eine Stunde spaeter (messe_losfahren.py:438-455)
    aus, sig = [], []
    for tl in teile:
        st = STD[tl]; vv = VH[tl]
        fin = np.isfinite(vv)
        ab_ = np.where(fin, vv >= schwelle, False)
        cs = np.concatenate([[0], np.cumsum(ab_)]); cf = np.concatenate([[0], np.cumsum(fin)])
        lo = np.searchsorted(st, st - RUHE, "left")
        ix = np.arange(len(tl))
        erst = ab_ & ((cs[ix] - cs[lo]) == 0) & ((cf[ix] - cf[lo]) >= int(RUHE * 20 / 24))
        erst &= (st - MONATSANFANG[np.clip(MON[tl] - 2020 * 12, 0, len(MONATSANFANG) - 1)]) >= 24
        i_ = np.flatnonzero(erst)
        sig.append(tl[i_])                 # Signalstunden (im Betrieb: die juengste abgeschlossene Stunde)
        i_ = i_[i_ + 1 < len(tl)]
        i_ = i_[st[i_ + 1] == st[i_] + 1]
        aus.append(tl[i_ + 1])
    e_ = np.concatenate(aus) if aus else np.zeros(0, int)
    e_ = np.sort(e_[(np.isin(JAHR[e_], jahre) if jahre else np.ones(len(e_), bool)) & np.isfinite(QSh[e_])])
    s_ = np.sort(np.concatenate(sig)) if sig else np.zeros(0, int)
    return dict(SYM=SYM, STD=STD, JAHR=JAHR, MON=MON, VH=VH, QSh=QSh, Ch=Ch, OFF=OFF, REIF=REIF, ZUS=ZUS,
                einstiege=e_, signale=s_, modelle=modelle, lage=LAGE, syms=syms, t_u=t_u, t_d=t_d)


# ══ HEBELSTUFE (Rolle C) - wie messe_k6_hebelstufe.py mit --kurs mark --mit-btc --simulation 24,ohne,0.02 ═══════════════════
HEBEL_H, MARGE, GRENZE, HEBEL_FENSTER = 24, 0.09, 0.02, 120


def _k6():
    import messe_k6_hebelstufe as K6                            # Bausteine (liq_schwelle, STUFEN) - Import ohne Seiteneffekt
    return K6


def _markpreis(con, sym, st):
    """(tief, einstieg) je Stunde aus dem Markpreis, gesperrte Monate fehlen (messe_k6_hebelstufe.py:201-209)."""
    gesperrt = {r[0] for r in con.execute("SELECT monat FROM _abweichung WHERE symbol=? AND gesperrt=1", (sym,))}
    mp = {r[0]: (r[1], r[2]) for r in con.execute(
        "SELECT stunde, low / faktor, close / faktor FROM markpreis WHERE symbol=?", (sym,)) if r[0][:7] not in gesperrt}
    return (np.array([mp[x][0] if x in mp else np.nan for x in st], float),
            np.array([mp[x][1] if x in mp else np.nan for x in st], float))


def hebel_anker(ordner: str, reihen: list, zusatz) -> dict:
    """Trainingsanker des ATR-Modells (messe_k6_hebelstufe.py:238-275): Gitterstunden der Messbasis ohne BTC und ohne die
    Zusatz-Assets, 240 h Vorlauf, VOLLES 120-h-Fenster ohne Luecke und ohne fehlende Markpreis-Stunde, Einstieg am Markpreis.
    Ziel je Stufe: erste Liquidation binnen 24 h (Marge 0,09, Finanzierung je Stunde).
    Im Betrieb (B-10) schraenkt ``hebel_modelle(bis_stunde=...)`` auf Anker ein, deren 120-h-Fenster schon vorbei ist."""
    K6 = _k6()
    basis = datetime(2020, 1, 1)
    con = _ro(os.path.join(ordner, "markpreis_historie.db"))
    HM = HEBEL_FENSTER
    X = {"std": [], "sym": [], "atr": []}
    Y = {L: [] for L in K6.STUFEN}
    for si, (sym, rows) in enumerate(reihen):
        if sym in zusatz or (sym.upper() == "BTC") or len(rows) < 500:
            continue
        st = [r[0] for r in rows]
        h = np.array([r[1] for r in rows], float); lo = np.array([r[2] for r in rows], float); cc = np.array([r[3] for r in rows], float)
        std = np.array([int((datetime.strptime(x, "%Y-%m-%d %H:%M") - basis).total_seconds() // 3600) for x in st], np.int64)
        n = len(cc); idx = np.arange(n)
        tief, einstieg = _markpreis(con, sym, st)
        atr = E2._atr(h, lo, cc)
        g2 = np.isfinite(atr) & (cc > 0) & np.isin(std % 24, K6.GITTER)
        g2[:E2.VORLAUF] = False
        nachH = np.clip(idx + HM, 0, n - 1)
        g2[max(0, n - HM):] = False
        g2 &= (std[nachH] - std) == HM
        fehlt = np.concatenate([[0], np.cumsum(~np.isfinite(tief))])
        g2 &= (fehlt[np.minimum(idx + HM + 1, n)] - fehlt[np.minimum(idx + 1, n)]) == 0
        g2 &= np.isfinite(einstieg)
        a = np.flatnonzero(g2)
        if not len(a):
            continue
        E0 = einstieg[a]
        erste = {L: np.full(len(a), 10 ** 6) for L in K6.STUFEN}
        for s in range(1, HM + 1):
            j = np.minimum(a + s, n - 1)
            r = np.where((a + s) < n, tief[j] / E0, np.inf)
            r = np.where(np.isfinite(r), r, np.inf)
            for L in K6.STUFEN:
                erste[L] = np.where((erste[L] > s) & (r <= K6.liq_schwelle(L, MARGE, s)), s, erste[L])
        X["std"].append(std[a]); X["sym"].append(np.full(len(a), si, np.int32)); X["atr"].append(atr[a])
        for L in K6.STUFEN:
            Y[L].append((erste[L] <= HEBEL_H).astype(np.float64))
    con.close()
    X = {k: np.concatenate(v) for k, v in X.items()}
    X["y"] = {L: np.concatenate(v) for L, v in Y.items()}
    return X


def hebel_modelle(X: dict, quartale: list, bis_stunde: int | None = None) -> dict:
    """ATR-Modell je Quartal und Stufe (messe_k6_hebelstufe.py:555-570): Training MON < Quartal und Stunde < Start - 24 h,
    mindestens 5.000 Anker und 30 Liquidationen, sonst kein Modell (dann keine Stufe L). Standard-Daempfung (20 ... 20.000).
    ``bis_stunde`` (Betrieb, B-10): nur Anker, deren 120-h-Fenster vor dieser Stunde abgeschlossen ist."""
    K6 = _k6()
    STD = X["std"]; MON = monat_von(STD)
    E = {"atr": X["atr"].astype(np.float64)}
    ok = np.isfinite(E["atr"])
    null0 = np.zeros(len(STD))
    aus = {}
    for (j, mo) in quartale:
        mi = j * 12 + (mo - 1)
        start = K2._h(datetime(j, mo, 1))
        fen = ok & (MON < mi) & (STD < start - HEBEL_H)
        if bis_stunde is not None:
            fen &= (STD + HEBEL_FENSTER) < bis_stunde
        fen = np.flatnonzero(fen)
        for L in K6.STUFEN:
            y = X["y"][L]
            if len(fen) < 5000 or y[fen].sum() < 30:
                continue
            with _modellform("b", (20.0, 200.0, 2000.0, 20000.0)):
                m_, _l = K2.fit_cv(("atr",), E, fen, fen, y[fen], null0[fen], STD)
            aus[(mi, L)] = m_
    return aus


def quartal(mi: int) -> int:
    """Monatsindex -> Monatsindex des Quartalsbeginns (Januar, April, Juli, Oktober)."""
    return mi - ((mi % 12) % 3)


def hebelstufe(atr_einstieg: np.ndarray, mon_einstieg: np.ndarray, modelle: dict) -> tuple:
    """-> (p je Stufe, gewaehlte Stufe): die HOECHSTE Stufe mit P(Liquidation binnen 24 h) <= 2 %, sonst 0 (kein Handel).
    Wie stufe() in messe_k6_hebelstufe.py:673-677 - ohne Monotonie, eine fehlende Vorhersage zaehlt nicht."""
    K6 = _k6()
    n = len(atr_einstieg)
    P = {L: np.full(n, np.nan) for L in K6.STUFEN}
    q_ = np.array([quartal(int(m)) for m in mon_einstieg])
    da = np.isfinite(atr_einstieg)          # ⚠️ ohne ATR KEINE Stufe - das Modell wuerde einen fehlenden Wert still einordnen
    for (mi, L), m_ in modelle.items():
        ze = np.flatnonzero((q_ == mi) & da)
        if len(ze):
            P[L][ze] = expit(m_.z({"atr": atr_einstieg.astype(np.float64)}, ze, np.zeros(len(ze))))
    Ls = np.zeros(n, np.int8)
    for L in sorted(K6.STUFEN):
        Ls = np.where(np.isfinite(P[L]) & (P[L] <= GRENZE), L, Ls)
    return P, Ls


def atr_je_stunde(reihen: list, mindest: int = 500) -> dict:
    """{symbol: {stunde: ATR}} aus den Spot-Kerzen (E2._atr, 24 Zeilen) - die ATR zum Einstieg. ``mindest``: Reihen mit weniger
    Zeilen werden uebersprungen (500 wie die Messung; der Stundenlauf gibt nur die letzten Zeilen, dort genuegen 24)."""
    basis = datetime(2020, 1, 1)
    aus = {}
    for sym, rows in reihen:
        if len(rows) < mindest:
            continue
        h = np.array([r[1] for r in rows], float); lo = np.array([r[2] for r in rows], float); cc = np.array([r[3] for r in rows], float)
        std = [int((datetime.strptime(r[0], "%Y-%m-%d %H:%M") - basis).total_seconds() // 3600) for r in rows]
        aus[sym] = dict(zip(std, E2._atr(h, lo, cc).tolist()))
    return aus


# ══ BETRIEB: Monatsjob (S7-3) und Stundenlauf (S7-2) ═══════════════════════════════════════════════════════════════════════
REGELVERSION = "REGEL0.1"
# Fenster des Stundenlaufs: Jahresnormal (8.760 h) + Vormonat fuer die Schrumpfung (bis 31 Tage) + Ruhe 48 h + rsi-Median
# 720 h + Vorlauf 240 Zeilen, mit Reserve. Mit `erster_anker` aus der Modelldatei rechnet das Fenster wie die volle Reihe.
FENSTER_H = 460 * 24
AKTIV_H = 48            # ein Asset, dessen letzte Stunde aelter ist, wird nicht mehr gehandelt (kein Frischefehler)


def _stunde_txt(h: int) -> str:
    return (datetime(2020, 1, 1) + pd.Timedelta(hours=int(h))).strftime("%Y-%m-%d %H:%M")


def betriebs_zusatz(ordner: str) -> list:
    """Alle Assets aus stundenkurse_alle.db mit mindestens 500 Stunden, ohne die gesperrten (Basisinfos/symbol_zuordnung.csv,
    markt=gesperrt: anderer Coin unter gleichem Kuerzel) - bewertet, nie trainiert (E-40, F-d: bewertet werden alle mit Daten)."""
    gesperrt = set()
    pz = os.path.join(HIER, "Basisinfos", "symbol_zuordnung.csv")
    if os.path.exists(pz):
        with open(pz, encoding="utf-8") as f_:
            for r in csv.DictReader(f_, delimiter=";"):
                if r.get("markt") == "gesperrt":
                    gesperrt |= {r.get("bitpanda", ""), r.get("binance", "")}
    ca = _ro(os.path.join(ordner, "stundenkurse_alle.db"))
    da = [r[0] for r in ca.execute("SELECT symbol FROM stundenkurse GROUP BY symbol HAVING COUNT(*) >= 500")]
    ca.close()
    return sorted(s for s in da if s not in gesperrt)


def trainiere_monat(ordner: str, jahr: int, monat: int, zusatz: list | None = None) -> dict:
    """Monatsjob: das rsi-Modell fuer den Monat (und den Vormonat, fuer die Ruhe am Monatsanfang), zu Quartalsbeginn die
    ATR-Modelle, dazu der erste Anker je Asset. Rechnet auf den Daten, die ZUM MONATSBEGINN vorliegen (Kerzen < Monatsbeginn,
    Ankermaske ohne Zukunft) - im Betrieb ist es dieselbe Lage. -> Paket fuer ``speichere_paket``."""
    import time
    t0 = time.time()
    zusatz = betriebs_zusatz(ordner) if zusatz is None else zusatz
    start = K2._h(datetime(jahr, monat, 1))
    A = anker(lade_reihen_iter(ordner, zusatz, bis=_stunde_txt(start - 1)), zukunft_bekannt=False)
    mi = jahr * 12 + monat - 1
    vm = ((mi - 1) // 12, (mi - 1) % 12 + 1)
    R = rechne(A, set(zusatz), [vm, (jahr, monat)], jahre=None)
    erster = {}
    for si in np.unique(A["SYM"]):
        erster[A["syms"][int(si)]] = int(A["STD"][A["SYM"] == si].min())
    qi = quartal(mi)
    qj, qm = qi // 12, qi % 12 + 1
    X = hebel_anker(ordner, lade_reihen_iter(ordner, [], bis=_stunde_txt(start - 1)), set(zusatz))   # Zusatz nie im ATR-Training
    atr_m = hebel_modelle(X, [(qj, qm)], bis_stunde=K2._h(datetime(qj, qm, 1)))
    return dict(version=REGELVERSION, monat="%04d-%02d" % (jahr, monat), trainiert_am=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
                rsi={k: v for k, v in R["modelle"].items() if k in (mi - 1, mi)}, atr=atr_m, quartal=qi,
                erster_anker=erster, lage={k: v for k, v in R["lage"].items() if k in (mi - 1, mi)},
                assets=len(erster), zusatz=len(zusatz), sekunden=round(time.time() - t0))


def speichere_paket(paket: dict, pfad: str) -> str:
    """Modelldatei mit Pruefsumme (``<pfad>.sha256``). -> Pruefsumme."""
    import hashlib
    import pickle
    roh = pickle.dumps(paket, protocol=4)
    with open(pfad, "wb") as f_:
        f_.write(roh)
    sha = hashlib.sha256(roh).hexdigest()
    with open(pfad + ".sha256", "w", encoding="utf-8") as f_:
        f_.write(sha + "\n")
    return sha


def lade_paket(pfad: str) -> dict:
    """Modelldatei laden - bricht ab, wenn die Pruefsumme nicht stimmt oder die Regelversion eine andere ist."""
    import hashlib
    import pickle
    roh = open(pfad, "rb").read()
    soll = open(pfad + ".sha256", encoding="utf-8").read().strip()
    if hashlib.sha256(roh).hexdigest() != soll:
        raise SystemExit("⛔ Modelldatei %s: Pruefsumme stimmt nicht" % pfad)
    paket = pickle.loads(roh)
    if paket.get("version") != REGELVERSION:
        raise SystemExit("⛔ Modelldatei %s: Regelversion %s, erwartet %s" % (pfad, paket.get("version"), REGELVERSION))
    return paket


def bewerte(ordner: str, pakete: dict, jetzt: int, zusatz: list | None = None, nachholen: tuple = ()) -> dict:
    """Stundenlauf zur Stunde ``jetzt`` (Stunden seit 2020-01-01): bewertet wird die juengste ABGESCHLOSSENE Stunde jetzt-1.

    -> neu:      Signale zur Stunde jetzt-1 (Einstieg zum Schluss der Stunde jetzt, also jetzt+1:00), vorlaeufige Stufe aus der
                 ATR der Signalstunde (die ATR der Einstiegsstunde ist noch nicht bekannt, B-9)
       endgueltig: Signale der Stunde jetzt-2 mit der Stufe aus der ATR der Einstiegsstunde jetzt-1 - wie die Messung
       frische:  je Asset die letzte Stunde; ein aktives Asset ohne die Stunde jetzt-1 bekommt KEIN Signal (B-8)
    ``pakete`` {"JJJJ-MM": Paket}: das rsi-Modell kommt aus dem Paket des Monats der SIGNALstunde, das ATR-Modell aus dem
    Paket des Monats der EINSTIEGSstunde (an der Monats- und Quartalsgrenze sind das zwei verschiedene) - wie die Messung.

    N-1 (E-57, 04.10.2026): ``nachholen`` = verpasste Signalstunden (aelter als jetzt-2, von keinem Lauf abgelegt). Sie werden aus
    DEMSELBEN Fenster bewertet wie zur richtigen Zeit, mit der Stufe aus der ATR der Einstiegsstunde (wie *endgueltig*) ->
    ``nachgeholt``. Fehlt das Modellpaket eines Monats, wird die Stunde ausgelassen und genannt (``nachholen_ausgelassen``)."""
    zusatz = betriebs_zusatz(ordner) if zusatz is None else zusatz
    unterwegs = {}

    def _strom():
        for s_, rows_ in lade_reihen_iter(ordner, zusatz, ab=_stunde_txt(jetzt - FENSTER_H), bis=_stunde_txt(jetzt - 1)):
            unterwegs[s_] = (rows_[-1][0] if rows_ else None, rows_[-30:])
            yield s_, rows_
    A = anker(_strom(), zukunft_bekannt=False)
    letzte = {s: (K2._h(datetime.strptime(lt, "%Y-%m-%d %H:%M")) if lt else None) for s, (lt, _r) in unterwegs.items()}
    aktiv = {s for s, h in letzte.items() if h is not None and h >= jetzt - AKTIV_H}
    frisch = {s for s in aktiv if letzte[s] == jetzt - 1}
    def _paket(h):
        m_ = int(monat_von(np.array([h]))[0])
        k_ = "%04d-%02d" % (m_ // 12, m_ % 12 + 1)
        if k_ not in pakete:
            raise SystemExit("⛔ keine Modelldatei fuer %s (Monatsjob gelaufen?)" % k_)
        return m_, pakete[k_]
    rsi_m = {}
    for sh in (jetzt - 2, jetzt - 1):
        mi_, pk_ = _paket(sh)
        rsi_m.update(pk_["rsi"])
    nach_ok, nach_weg = [], []
    for sh in sorted(set(int(h) for h in nachholen) - {jetzt - 1, jetzt - 2}):
        try:
            mi_, pk_ = _paket(sh)
            _paket(sh + 1)
        except SystemExit:
            nach_weg.append(_stunde_txt(sh))
            continue
        rsi_m.update(pk_["rsi"])
        nach_ok.append(sh)
    mi, paket = _paket(jetzt - 1)
    monate = [((m_ // 12), (m_ % 12) + 1) for m_ in sorted({mi - 1, mi, int(monat_von(np.array([jetzt - 2]))[0])}
                                                          | {int(monat_von(np.array([h]))[0]) for h in nach_ok})]
    R = rechne(A, set(zusatz), monate, modelle=rsi_m, jahre=None, erster_anker=paket["erster_anker"])
    atr = atr_je_stunde([(s, r30) for s, (_lt, r30) in unterwegs.items()], mindest=24)     # die letzten 24 Zeilen genuegen
    aus = {}
    _kurs_von = {}
    for s_, (_lt, r30) in unterwegs.items():
        _kurs_von[s_] = {row[0]: row[3] for row in r30}
    aus["nachgeholt"] = []
    for name, sh, atr_h in [("neu", jetzt - 1, jetzt - 1), ("endgueltig", jetzt - 2, jetzt - 1)] + [("nachgeholt", h, h + 1) for h in nach_ok]:
        ix = R["signale"][R["STD"][R["signale"]] == sh]
        syms = [R["syms"][int(R["SYM"][i])] for i in ix]
        ok = [s in frisch for s in syms]
        ix = ix[np.array(ok, bool)] if len(ix) else ix
        syms = [s for s, o in zip(syms, ok) if o]
        a_ = np.array([atr.get(s, {}).get(atr_h, np.nan) for s in syms])
        me_, pe_ = _paket(sh + 1)                      # Quartal der EINSTIEGSstunde
        P, L = hebelstufe(a_, np.full(len(syms), me_), pe_["atr"]) if syms else ({2: [], 3: [], 5: []}, [])
        liste = [dict(symbol=s, signalstunde=_stunde_txt(sh), einstieg=_stunde_txt(sh + 1), ausstieg=_stunde_txt(sh + 25),
                      vh=float(R["VH"][i]), stufe=int(L[k]), p2=float(P[2][k]), p3=float(P[3][k]), p5=float(P[5][k]),
                      zusatz=s in zusatz, btc=s.upper() == "BTC",
                      # Schlusskurs der Signalstunde (Binance, USDT) - die Zeile DIESER Stunde, auch fuer endgueltig/nachgeholt
                      # (bis 04.10. nur fuer die juengste Stunde - die endgueltig angelegte Zeile einer verpassten Stunde hatte keinen)
                      kurs=(float(_kurs_von[s][_stunde_txt(sh)]) if _kurs_von.get(s, {}).get(_stunde_txt(sh)) is not None else None))
                 for k, (s, i) in enumerate(zip(syms, ix))]
        if name == "nachgeholt":
            aus["nachgeholt"] += liste
        else:
            aus[name] = liste
    aus["nachgeholt_stunden"] = [_stunde_txt(h) for h in nach_ok]
    aus["nachholen_ausgelassen"] = nach_weg
    aus["frische"] = dict(jetzt=_stunde_txt(jetzt), aktiv=len(aktiv), frisch=len(frisch),
                          veraltet=sorted(aktiv - frisch), nicht_im_handel=len(letzte) - len(aktiv))
    aus["R"] = R
    return aus


def schreibe_einstiege(R: dict, ziel: str) -> int:
    """Einstiege im Format der Referenz (symbol;stunde;jahr;t_u;t_d) - wie messe_losfahren.py:1232-1237."""
    with open(ziel, "w", encoding="utf-8", newline="") as f_:
        f_.write("symbol;stunde;jahr;t_u;t_d\n")
        for i in R["einstiege"]:
            tu, td = R["t_u"][i], R["t_d"][i]
            f_.write("%s;%d;%d;%s;%s\n" % (R["syms"][int(R["SYM"][i])], int(R["STD"][i]), int(R["JAHR"][i]),
                                           "%.0f" % tu if np.isfinite(tu) else "", "%.0f" % td if np.isfinite(td) else ""))
    return len(R["einstiege"])


def zusatz_aus_gruppe(pfad: str) -> list:
    """Die Zusatz-Assets einer Referenz (Gruppendatei der Messung, neu=1)."""
    with open(pfad, encoding="utf-8") as f_:
        return sorted({r["symbol"] for r in csv.DictReader(f_, delimiter=";") if r["neu"] == "1"})


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    a = sys.argv
    ordner = a[a.index("--ordner") + 1] if "--ordner" in a else DATEN_VORGABE
    if "--nachrechnung" not in a or "--ziel" not in a:
        print(__doc__)
        return 2
    zus = zusatz_aus_gruppe(a[a.index("--zusatz-aus") + 1]) if "--zusatz-aus" in a else []
    import time
    t0 = time.time()
    A = anker(lade_reihen(ordner, zus), zukunft_bekannt=True)
    t1 = time.time()
    R = rechne(A, set(zus), K2.ROLL_MONATE)
    t2 = time.time()
    k = schreibe_einstiege(R, a[a.index("--ziel") + 1])
    print("REGEL0.1-RECHENKERN Nachrechnung 2024-01..2026-08: %d Anker, %d Assets (Zusatz %d), %d Monatsmodelle, %d Einstiege "
          "· Laden %.0f s · Rechnen %.0f s" % (len(A["SYM"]), len(np.unique(A["SYM"])), len(zus), len(R["modelle"]), k, t1 - t0, t2 - t1))
    print("  Schrumpfung kausal: tau2 = 0 in %d von %d Monaten" % (sum(1 for _m, t in R["lage"].values() if t == 0.0), len(R["lage"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
