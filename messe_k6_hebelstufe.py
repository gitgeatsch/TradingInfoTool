# -*- coding: utf-8 -*-
"""K6 R - die Hebelstufe aus der LIQUIDATIONSGEFAHR (28.09.2026).

Voranalyse `Basisinfos/Voranalyse_K6_Hebelstufe_28_09.md`, abgestimmt (*ja, H0
bis H10 wie empfohlen, H9 freigegeben*).

VORAB FESTGELEGT
    H0  jetzt auf ALLEN Ankern; die Gueltigkeit auf der Einstiegsauswahl ist
        PFLICHT nach K1 Schritt 2, vor jeder Verwendung (hier nur Auskunft auf
        der Teilmenge *rsi oben gestreckt*)
    H1  Liquidationsereignis je Stufe L (5x/3x/2x): das Tief einer Folgestunde s
        faellt unter  Liq(s) = E (1 - 1/L + s/24 * 0,0018) / (1 - m)
        (Bitpanda-Formel aus agent/krypto/hebel_risk_gate, Finanzierung je Stunde)
    H2  Haltedauer 24 / 72 / 120 h OHNE Stop; mit Stop -5 % als Auskunft
        (liquidiert, wenn die Liquidationsstunde nicht nach der Stopstunde liegt -
        in derselben Stunde zaehlt als liquidiert: Sprung, vorsichtig)
    H3  Kurs: --kurs spot (Stundentief; zaehlt Dochte, vorsichtig) oder
        --kurs mark (Binance-Markpreis aus data/markpreis_historie.db)
    H4  Vorhersage: ATR allein · ATR + volumenschub + oi_aenderung + ema_abstand_atr
    H5  logistisch, glatte Kurven, Daempfung per Kreuzvalidierung (Werkzeuge aus
        messe_k1_schritt2b_kombination), feste Teilung Suche 2023-2024 -> Pruefung
        2025-01..2026-08 fuer die Nullwelt; rollierend wachsend 2024-01..2026-08
    H6  Kalibrierung vorwaerts · Mehrwert ueber die ATR · Tabelle je Grenze
    H7  Nullwelt: die Nicht-ATR-Eingaenge je Asset gemeinsam verschoben, 40
        Ziehungen; Zufallseingaenge; TOR: eine gepflanzte VERDOPPLUNG der Rate im
        obersten Zehntel eines verschobenen Eingangs, 5x/72 h, >= 4 von 5
    H8  Wartungsmarge m = 0,09; m = 0,0476 als Auskunft
    H10 nur Long; Mengen unverzerrt:1..3 und bestand; Hebelwerte als Auskunft
KRITERIEN
    V0 Tor · V1 kalibriert (je Zehntel mit >= 30 Liquidationen |beob - gesch| <=
    max(0,2 gesch, 0,5 Pp); Steigung 0,7-1,3) · V2 Mehrwert ueber die ATR jenseits
    des Nullbands, >= 3 von 4 Mengen · V3 in jedem Jahr und BTC-Drittel beob/gesch
    zwischen 0,5 und 2 · R Zufall im Nullband · T Tabelle, keine Grenze gesetzt
R-R11 zuerst: E2i (2.667/2.669) - alle Stundenanker, feste Grenzen 12/27/45 %,
    Tiefstkurs, ohne Finanzierung, je ATR-Fuenftel - muss dieselben Anteile geben.

NUR LESEND (`mode=ro`). Die Finanzierung geht nur in den Abstand ein (Mechanik).

    python messe_k6_hebelstufe.py --menge bestand --kurs spot --tor
    python messe_k6_hebelstufe.py --menge unverzerrt:1 --kurs spot
"""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime

import numpy as np
import pandas as pd
from scipy.special import expit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messe_e2_beitraege as E2                                   # noqa: E402
import messe_k1_schritt2b_kombination as K2                       # noqa: E402
from messe_e3_vorwaerts import monat_von                          # noqa: E402
from messe_k3_kontextflaeche import reihe                         # noqa: E402

B0 = datetime(2020, 1, 1)
STUFEN = (5, 3, 2)
HALTE = (24, 72, 120)
MARGEN = (0.09, 0.0476)
FIN = 0.0018
GITTER = (0, 6, 12, 18)
GRENZEN_E2I = ((0.12, "5x"), (0.27, "3x"), (0.45, "2x"))
MARK_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "markpreis_historie.db")
HEBEL_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "tradinginfotool.db")
GRENZEN_TAB = (0.005, 0.01, 0.02, 0.05)
ZIEHUNGEN, SAAT = 40, 20261010
EIN_ATR = ("atr",)
EIN_KOMB = ("atr", "volumenschub", "oi", "ema")


def _h(d):
    return int((d - B0).total_seconds() // 3600)


SUCHE = (_h(datetime(2023, 1, 1)), _h(datetime(2025, 1, 1)))
PRUEF = (_h(datetime(2025, 1, 1)), _h(datetime(2026, 9, 1)))
# rollierend je QUARTAL neu geschaetzt (wachsend, nur Vergangenheit) und auf
# die drei Monate danach angewandt - ein Drittel des Aufwands gegen monatlich
# (3 Stufen x 3 Haltedauern x 2 Modelle, je mit Kreuzvalidierung)
ROLL = [(j, m) for j in (2024, 2025, 2026) for m in (1, 4, 7, 10) if (j, m) <= (2026, 7)]


def liq_schwelle(L, m, s):
    """Liquidationspreis / Einstieg nach s Stunden (Long)."""
    return (1.0 - 1.0 / L + (s / 24.0) * FIN) / (1.0 - m)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    E2.menge_aus_argv()
    kurs = sys.argv[sys.argv.index("--kurs") + 1] if "--kurs" in sys.argv else "spot"
    tor = "--tor" in sys.argv
    probe = "--probe" in sys.argv
    # ⭐ KERN SCHRITT 2 / H0 (Basisinfos/Voranalyse_Kern_Schritt2_H0_29_09.md): --einstiege <csv> wertet das
    # ATR-Risikomodell zusaetzlich an den Ersteintritten aus, Fensterachse 6/12/24 h (72 h Anschluss an K6)
    ein_datei = sys.argv[sys.argv.index("--einstiege") + 1] if "--einstiege" in sys.argv else None
    global HALTE
    EIN, TU = {}, {}
    if ein_datei:
        HALTE = (6, 12, 24, 72, 120)
        for zeile in open(ein_datei, encoding="utf-8").read().splitlines()[1:]:
            sy, st_, _j, tu_, _td = zeile.split(";")
            EIN.setdefault(sy, set()).add(int(st_))
            TU[(sy, int(st_))] = float(tu_) if tu_ else np.inf
    zieh = 3 if probe else ZIEHUNGEN
    monate = ROLL[:3] if probe else ROLL
    K2.FORM = "b"
    print("=" * 120)
    print("K6 R - HEBELSTUFE AUS DER LIQUIDATIONSGEFAHR · MENGE %s · KURS %s%s" % (
        E2.MENGE, kurs, " · TOR" if tor else (" · WERKZEUGTEST" if probe else "")))
    print("=" * 120)
    mark = None
    if kurs == "mark":
        mark = sqlite3.connect("file:%s?mode=ro" % MARK_DB, uri=True)
    ct = sqlite3.connect("file:%s?mode=ro" % E2.TERMIN_DB, uri=True)
    ce = (sqlite3.connect("file:%s?mode=ro" % E2.EINGESTELLT_DB, uri=True)
          if E2.MENGE != "bestand" and os.path.exists(E2.EINGESTELLT_DB) else None)
    HM = max(HALTE)
    rr11 = {f: {g: [] for g, _n in GRENZEN_E2I} for f in (24, 72)}
    rr11_atr = []
    SP = {k: [] for k in ("std", "sym", "atr", "volumenschub", "oi", "ema", "rsi_s", "jahr")}
    EV = {}          # (L, H, m, stop) -> Liste
    for L in STUFEN:
        for H in HALTE:
            for m in MARGEN:
                for stop in (False, True):
                    EV[(L, H, m, stop)] = []
    syms = []
    SPE = {k: [] for k in ("atr", "std", "sym", "tu", "fl5", "fl3", "fl2")}
    for si, (sym, rows, bis_ende) in enumerate(E2.kursreihen()):
        syms.append(sym)
        if sym.upper() == "BTC" or len(rows) < 500:
            continue
        st = [r[0] for r in rows]
        h = np.array([r[1] for r in rows], float)
        l = np.array([r[2] for r in rows], float)
        cc = np.array([r[3] for r in rows], float)
        vol = np.array([(r[4] or 0.0) for r in rows], float)
        std = np.array([int((datetime.strptime(x, "%Y-%m-%d %H:%M") - B0).total_seconds() // 3600)
                        for x in st], np.int64)
        n = len(cc)
        idx = np.arange(n)
        if mark is not None:
            # ⚠️ 28.09. abends (Markpreis-Kontrolle, K7): Einstieg UND Tief aus
            # DERSELBEN Reihe - der Markpreis liegt gleichbleibend rund -0,05 %
            # neben dem Spot, mit dem Spot-Schluss als Einstieg stuende dieser
            # Aufschlag als Fehler in der Liquidationsdistanz. Monate mit einem
            # FREMDEN Instrument (hole_markpreis --sperre) zaehlen als fehlend.
            gesperrt = {r[0] for r in mark.execute(
                "SELECT monat FROM _abweichung WHERE symbol=? AND gesperrt=1", (sym,))}
            mp = {r[0]: (r[1], r[2]) for r in mark.execute(
                "SELECT stunde, low / faktor, close / faktor FROM markpreis WHERE symbol=?", (sym,))
                if r[0][:7] not in gesperrt}
            tief = np.array([mp[x][0] if x in mp else np.nan for x in st], float)
            einstieg = np.array([mp[x][1] if x in mp else np.nan for x in st], float)
        else:
            tief = l
            einstieg = cc
        km = E2.kursmerkmale(h, l, cc, vol)
        atr = km["atr"]
        # R-R11: genau wie E2i (alle Stundenanker, 24/72 h, feste Grenzen, Spot-Tief)
        gu = np.isfinite(E2._atr(h, l, cc)) & (cc > 0)
        gu[:E2.VORLAUF] = False
        nach72 = np.clip(idx + 72, 0, n - 1)
        if bis_ende:
            drin = idx + 72 < n
            rest = (std[n - 1] - std) == (n - 1 - idx)
            gu &= np.where(drin, (std[nach72] - std) == 72, rest)
        else:
            gu[max(0, n - 72):] = False
            gu &= (std[nach72] - std) == 72
        sel = np.flatnonzero(gu)
        if len(sel):
            tmin = np.full(n, np.inf)
            for s in range(1, 73):
                tmin = np.minimum(tmin, l[np.minimum(idx + s, n - 1)])
                if s in (24, 72):
                    mae = (1.0 - tmin / cc)[sel]
                    for g, _n in GRENZEN_E2I:
                        rr11[s][g].append(mae >= g)
            rr11_atr.append(E2._atr(h, l, cc)[sel])
        # ── K6: Gitteranker mit vollem Fenster HM, ohne Luecke
        g2 = np.isfinite(atr) & (cc > 0) & np.isin(std % 24, GITTER)
        g2[:E2.VORLAUF] = False
        nachH = np.clip(idx + HM, 0, n - 1)
        if bis_ende:
            drin = idx + HM < n
            rest = (std[n - 1] - std) == (n - 1 - idx)
            g2 &= np.where(drin, (std[nachH] - std) == HM, rest)
        else:
            g2[max(0, n - HM):] = False
            g2 &= (std[nachH] - std) == HM
        if mark is not None:
            # eine fehlende Markpreis-Stunde im Fenster darf nicht als *nicht
            # liquidiert* zaehlen - solche Anker fallen heraus
            fehlt = np.concatenate([[0], np.cumsum(~np.isfinite(tief))])
            g2 &= (fehlt[np.minimum(idx + HM + 1, n)] - fehlt[np.minimum(idx + 1, n)]) == 0
            g2 &= np.isfinite(einstieg)          # der Einstieg braucht den Markpreis der Ankerstunde
        a = np.flatnonzero(g2)
        if not len(a):
            continue
        E0 = einstieg[a]                        # spot: cc; mark: Markpreis-Schluss (dieselbe Reihe wie das Tief)
        erste_liq = {(L, m): np.full(len(a), 10 ** 6) for L in STUFEN for m in MARGEN}
        erste_stop = np.full(len(a), 10 ** 6)
        for s in range(1, HM + 1):
            j = np.minimum(a + s, n - 1)
            gueltig = (a + s) < n
            r = np.where(gueltig, tief[j] / E0, np.inf)
            r = np.where(np.isfinite(r), r, np.inf)
            erste_stop = np.where((erste_stop > s) & (r <= 0.95), s, erste_stop)
            for L in STUFEN:
                for m in MARGEN:
                    k = (L, m)
                    erste_liq[k] = np.where((erste_liq[k] > s) & (r <= liq_schwelle(L, m, s)), s, erste_liq[k])
        for L in STUFEN:
            for m in MARGEN:
                fl = erste_liq[(L, m)]
                for H in HALTE:
                    EV[(L, H, m, False)].append(fl <= H)
                    EV[(L, H, m, True)].append((fl <= H) & (fl <= erste_stop))
        if ein_datei and sym in EIN:
            ge = np.isfinite(atr) & (cc > 0)
            ge[:E2.VORLAUF] = False
            if bis_ende:
                ge &= np.where(idx + HM < n, (std[nachH] - std) == HM, (std[n - 1] - std) == (n - 1 - idx))
            else:
                ge[max(0, n - HM):] = False
                ge &= (std[nachH] - std) == HM
            if mark is not None:
                fehlt_e = np.concatenate([[0], np.cumsum(~np.isfinite(tief))])
                ge &= (fehlt_e[np.minimum(idx + HM + 1, n)] - fehlt_e[np.minimum(idx + 1, n)]) == 0
                ge &= np.isfinite(einstieg)
            ge &= np.isin(std, np.fromiter(EIN[sym], np.int64))
            ae = np.flatnonzero(ge)
            if len(ae):
                E0e = einstieg[ae]
                fle = {L: np.full(len(ae), 10 ** 6) for L in STUFEN}
                for s in range(1, HM + 1):
                    j = np.minimum(ae + s, n - 1)
                    r = np.where((ae + s) < n, tief[j] / E0e, np.inf)
                    r = np.where(np.isfinite(r), r, np.inf)
                    for L in STUFEN:
                        fle[L] = np.where((fle[L] > s) & (r <= liq_schwelle(L, 0.09, s)), s, fle[L])
                for L in STUFEN:
                    SPE["fl%d" % L].append(fle[L])
                SPE["atr"].append(atr[ae]); SPE["std"].append(std[ae]); SPE["sym"].append(np.full(len(ae), si))
                SPE["tu"].append(np.array([TU.get((sym, int(x)), np.inf) for x in std[ae]]))
        # Merkmale
        tm = {str(r_[0]): r_[1] for r_ in ct.execute("SELECT stunde, oi FROM terminmarkt WHERE symbol=?", (sym,))}
        if ce is not None:
            for r_ in ce.execute("SELECT stunde, oi FROM terminmarkt WHERE symbol=?", (sym,)):
                tm.setdefault(str(r_[0]), r_[1])
        oi = np.array([tm.get(x) if tm.get(x) is not None else np.nan for x in st], float)
        with np.errstate(divide="ignore", invalid="ignore"):
            oi24 = np.concatenate([np.full(24, np.nan), oi[:-24]])
            oich = oi / np.maximum(oi24, 1e-12) - 1.0
        ser = pd.Series(km["rsi"], index=pd.to_datetime(std * 3600, unit="s"))
        rsi_s = km["rsi"] - ser.rolling("720h", closed="left", min_periods=240).median().to_numpy()
        SP["std"].append(std[a]); SP["sym"].append(np.full(len(a), si, np.int32))
        SP["atr"].append(atr[a]); SP["volumenschub"].append(km["volumenschub"][a])
        SP["oi"].append(oich[a]); SP["ema"].append(km["ema_abstand_atr"][a]); SP["rsi_s"].append(rsi_s[a])
        SP["jahr"].append(np.array([int(st[i][:4]) for i in a], np.int16))
    ct.close()
    # ── R-R11
    ra = np.concatenate(rr11_atr)
    q = np.percentile(ra, [20, 40, 60, 80]); sch = np.searchsorted(q, ra)
    print("R-R11 E2i (alle Stundenanker, Spot-Tief, feste Grenzen, ohne Finanzierung): %d Anker" % len(ra))
    for f in (24, 72):
        teil = []
        for g, nm in GRENZEN_E2I:
            v = np.concatenate(rr11[f][g])
            teil.append("%s ATR-S1 %.2f %% / S5 %.2f %%" % (nm, 100 * v[sch == 0].mean(), 100 * v[sch == 4].mean()))
        print("  %3d h: %s" % (f, " · ".join(teil)))
    X = {k: np.concatenate(v) for k, v in SP.items()}
    Y = {k: np.concatenate(v).astype(np.float64) for k, v in EV.items()}
    STD, SYM, JAHR = X["std"], X["sym"], X["jahr"]
    n = len(STD)
    MON = monat_von(STD)
    E = {k: X[k].astype(np.float64) for k in EIN_KOMB}
    E["rsi_s"] = X["rsi_s"].astype(np.float64)
    ok = np.isfinite(E["atr"])
    such = ok & (STD >= SUCHE[0]) & (STD < SUCHE[1]); pruef = ok & (STD >= PRUEF[0]) & (STD < PRUEF[1])
    print()
    print("K6-Anker (Gitter, volles Fenster %d h): %d · Suche %d · Pruefung %d · Symbole %d" % (
        HM, n, such.sum(), pruef.sum(), len(np.unique(SYM))))
    print("  Liquidationsraten (alle Anker, m 0,09 / 0,0476, ohne Stop | mit Stop -5 %):")
    for L in STUFEN:
        print("   %dx: %s" % (L, " · ".join("%3d h %.3f%% / %.3f%% | %.3f%%" % (
            H, 100 * Y[(L, H, 0.09, False)][ok].mean(), 100 * Y[(L, H, 0.0476, False)][ok].mean(),
            100 * Y[(L, H, 0.09, True)][ok].mean()) for H in HALTE)))
    rng = np.random.default_rng(SAAT)
    ordnung = np.lexsort((STD, SYM))
    teile = np.split(ordnung, np.flatnonzero(np.diff(SYM[ordnung])) + 1)
    r_sa = np.flatnonzero(such); r_pa = np.flatnonzero(pruef)
    null0 = np.zeros(n)

    def g_fest(EE, namen, y):
        m_, lam = K2.fit_cv(namen, EE, r_sa, r_sa, y[r_sa], null0[r_sa], STD)
        b_ = K2.Modell(()).fit(EE, r_sa, r_sa, y[r_sa], null0[r_sa])
        return 1000 * (K2.logloss(b_.z(EE, r_pa, null0[r_pa]), y[r_pa]) -
                       K2.logloss(m_.z(EE, r_pa, null0[r_pa]), y[r_pa])), m_

    def verschoben(EE, ausser=("atr",)):
        aus = dict(EE)
        rr = {int(SYM[tl[0]]): (int(rng.integers(360, len(tl) - 360)) if len(tl) > 720 else 0) for tl in teile}
        for k in EE:
            if k in ausser:
                continue
            v = np.empty(n)
            for tl in teile:
                v[tl] = np.roll(EE[k][tl], rr[int(SYM[tl[0]])])
            aus[k] = v
        return aus
    # 360 Gitteranker = 90 Tage Mindestversatz (vier Anker je Tag)

    haupt = (5, 72, 0.09, False)
    if tor:
        yH = Y[haupt]
        nd = []
        for _ in range(zieh):
            EV_ = verschoben(E)
            nd.append(g_fest(EV_, EIN_KOMB, yH)[0] - g_fest(EV_, EIN_ATR, yH)[0])
        grenze = float(np.percentile(nd, 90))
        print()
        print("TOR (H7) 5x / 72 h: Nullwelt Mehrwert ueber ATR Mittel %+.3f, 90. Perzentil %+.3f (%d Ziehungen)" % (
            float(np.mean(nd)), grenze, zieh))
        gef = 0
        for _ in range(5):
            EV_ = verschoben(E)
            y = yH.copy()
            oben = np.flatnonzero(EV_["volumenschub"] >= np.nanpercentile(EV_["volumenschub"][r_sa], 90))
            rate = y[oben].mean()
            kand = oben[y[oben] == 0]
            w = rng.choice(kand, size=min(int(round(rate * len(oben))), len(kand)), replace=False)
            y[w] = 1.0
            d = g_fest(EV_, EIN_KOMB, y)[0] - g_fest(EV_, EIN_ATR, y)[0]
            gef += int(d > grenze)
            print("  gepflanzte Verdopplung (Rate %.3f -> %.3f) im obersten Zehntel von volumenschub (verschoben): "
                  "Mehrwert %+.3f -> %s" % (rate, y[oben].mean(), d, "gefunden" if d > grenze else "nicht gefunden"))
        print("  TOR: %s" % ("✔ BESTANDEN (%d von 5) - die Risikokurven werden gemessen" % gef if gef >= 4 else
                            "⛔ NICHT BESTANDEN (%d von 5) - es gilt nur die ATR-Tabelle" % gef))
        print("SCHLUSS: vollstaendig")
        return 0

    if not ein_datei:
        # ══ V2 Mehrwert ueber die ATR (feste Teilung), je Stufe, Hauptfall 72 h ══
        print()
        print("=" * 120)
        print("V2 MEHRWERT UEBER DIE ATR - feste Teilung, Log-Loss-Gewinn in tausendstel nat, Hauptfall 72 h, m 0,09")
        v2 = {}
        for L in (5, 3):
            y = Y[(L, 72, 0.09, False)]
            ga, _m = g_fest(E, EIN_ATR, y); gk, _m = g_fest(E, EIN_KOMB, y)
            nd = []
            for _ in range(zieh):
                EV_ = verschoben(E)
                nd.append(g_fest(EV_, EIN_KOMB, y)[0] - g_fest(EV_, EIN_ATR, y)[0])
            gr = float(np.percentile(nd, 90))
            v2[L] = (gk - ga) > gr
            print("  %dx: ATR allein %+.3f · Kombination %+.3f · Mehrwert %+.3f gegen Nullband %+.3f -> %s" % (
                L, ga, gk, gk - ga, gr, "✔ traegt" if v2[L] else "· nicht"))
        ez = dict(E)
        rz = np.random.default_rng(SAAT + 1)
        for k in ("volumenschub", "oi", "ema"):
            ez[k] = rz.standard_normal(n)
        y = Y[haupt]
        zd = g_fest(ez, EIN_KOMB, y)[0] - g_fest(ez, EIN_ATR, y)[0]
        print("  R  Zufallseingaenge statt der Risikokurven (5x/72 h): Mehrwert %+.3f" % zd)

    # ══ ROLLIEREND: Kalibrierung (V1/V3) und Tabelle (T) ═════════════════
    btc = reihe([(E2.EINGESTELLT_DB, "SELECT stunde, close FROM stundenkurse WHERE symbol='BTC'"),
                 (E2.STUNDEN_DB, "SELECT stunde, close FROM stundenkurse WHERE symbol='BTC'")])
    b30 = np.full(n, np.nan)
    okb = (STD < len(btc)) & (STD >= 720)
    with np.errstate(divide="ignore", invalid="ignore"):
        b30[okb] = btc[STD[okb]] / btc[STD[okb] - 720] - 1.0
    PRED = {}
    if ein_datei:
        XE = {k: np.concatenate(v) if v else np.zeros(0) for k, v in SPE.items()}
        STDe = XE["std"].astype(np.int64); MONe = monat_von(STDe); JAHRe = (MONe // 12)
        EEe = {"atr": XE["atr"].astype(np.float64)}
        PE = {}
    for L in STUFEN:
        for H in HALTE:
            for ein, nm in (((EIN_ATR, "atr"),) if ein_datei else ((EIN_ATR, "atr"), (EIN_KOMB, "komb"))):
                y = Y[(L, H, 0.09, False)]
                p = np.full(n, np.nan)
                pe = np.full(len(STDe), np.nan) if ein_datei else None
                for (j, mo) in monate:
                    mi = j * 12 + (mo - 1)
                    start = _h(datetime(j, mo, 1))
                    fen = np.flatnonzero(ok & (MON < mi) & (STD < start - H))
                    ziel = np.flatnonzero(ok & (MON >= mi) & (MON < mi + 3) & (MON <= 2026 * 12 + 7))
                    if len(fen) < 5000 or not len(ziel) or y[fen].sum() < 30:
                        continue
                    m_, _l = K2.fit_cv(ein, E, fen, fen, y[fen], null0[fen], STD)
                    p[ziel] = expit(m_.z(E, ziel, null0[ziel]))
                    if ein_datei:
                        ze = np.flatnonzero((MONe >= mi) & (MONe < mi + 3) & (MONe <= 2026 * 12 + 7))
                        if len(ze):
                            pe[ze] = expit(m_.z(EEe, ze, np.zeros(len(ze))))
                PRED[(L, H, nm)] = p
                if ein_datei:
                    PE[(L, H)] = pe
    print()
    print("=" * 120)
    print("V1/V3 KALIBRIERUNG VORWAERTS (rollierend, wachsend, m 0,09, ohne Stop)")
    for L in STUFEN:
        for H in HALTE:
            for nm in ("atr", "komb"):
                if (L, H, nm) not in PRED:
                    continue
                p = PRED[(L, H, nm)]; y = Y[(L, H, 0.09, False)]
                ix = np.flatnonzero(np.isfinite(p))
                if not len(ix):
                    continue
                dz = np.quantile(p[ix], np.linspace(0, 1, 11))
                kb = np.clip(np.searchsorted(dz, p[ix], "right") - 1, 0, 9)
                cnt = np.bincount(kb, minlength=10)
                mp_ = np.bincount(kb, weights=p[ix], minlength=10) / np.maximum(cnt, 1)
                mo_ = np.bincount(kb, weights=y[ix], minlength=10) / np.maximum(cnt, 1)
                ev = np.bincount(kb, weights=y[ix], minlength=10)
                gut = [abs(mo_[i] - mp_[i]) <= max(0.2 * mp_[i], 0.005) for i in range(10) if ev[i] >= 30]
                w = cnt / cnt.sum(); xm = np.sum(w * mp_); ym = np.sum(w * mo_)
                sl = np.sum(w * (mp_ - xm) * (mo_ - ym)) / max(np.sum(w * (mp_ - xm) ** 2), 1e-12)
                v1 = bool(gut) and all(gut) and 0.7 <= sl <= 1.3
                ratios = []
                for jj in (2024, 2025, 2026):
                    s_ = ix[JAHR[ix] == jj]
                    if y[s_].sum() >= 30:
                        ratios.append(y[s_].mean() / max(p[s_].mean(), 1e-9))
                bb = b30[ix]; fin = np.isfinite(bb)
                if fin.sum():
                    q1, q2 = np.quantile(bb[fin], (1 / 3, 2 / 3))
                    for lo_, hi_ in ((-np.inf, q1), (q1, q2), (q2, np.inf)):
                        s_ = ix[fin & (bb > lo_) & (bb <= hi_)]
                        if y[s_].sum() >= 30:
                            ratios.append(y[s_].mean() / max(p[s_].mean(), 1e-9))
                v3 = bool(ratios) and min(ratios) >= 0.5 and max(ratios) <= 2.0
                tm_ = np.isfinite(E["rsi_s"][ix]) & (E["rsi_s"][ix] >= np.nanpercentile(E["rsi_s"][r_sa], 90))
                tq = y[ix][tm_].mean() / max(p[ix][tm_].mean(), 1e-9) if tm_.sum() else np.nan
                print("  %dx %3d h %-4s Rate beob %.3f %% gesch %.3f %% · Steigung %.2f · Zehntel ok %d/%d · V1 %s · "
                      "V3 %s (beob/gesch %s) · rsi oben beob/gesch %.2f" % (
                          L, H, nm, 100 * y[ix].mean(), 100 * p[ix].mean(), sl, sum(gut), len(gut),
                          "✔" if v1 else "·", "✔" if v3 else "·",
                          " ".join("%.2f" % r_ for r_ in ratios), tq))
    if ein_datei:
        print()
        print("=" * 120)
        soll = (17.493, 17.627)
        yy = Y[(5, 72, 0.09, False)]; pp = PRED[(5, 72, "atr")]; ii = np.flatnonzero(np.isfinite(pp))
        rb, rg = round(100 * yy[ii].mean(), 3), round(100 * pp[ii].mean(), 3)
        print("H0-0 R-R11 (Gitter, 5x/72 h atr, derselbe Codepfad): beob %.3f %% gesch %.3f %% · 2.681 %.3f / %.3f -> %s" % (
            rb, rg, soll[0], soll[1], "✔ bitgleich" if (rb, rg) == soll or E2.MENGE != "bestand" or kurs != "mark" else "⛔ ABWEICHUNG"))
        n_datei = sum(len(v) for v in EIN.values())
        print("H0 · EINSTIEGE aus %s: %d in der Datei, %d mit vollstaendigem Fenster und Markpreis ausgewertet" % (
            os.path.basename(ein_datei), n_datei, len(STDe)))
        bs0, bs1 = _h(datetime(2025, 10, 10)), _h(datetime(2025, 10, 12))
        for L in STUFEN:
            fl = XE["fl%d" % L]
            for H in (6, 12, 24, 72):
                y = (fl <= H).astype(np.float64); pe = PE[(L, H)]
                ok_ = np.isfinite(pe)
                if not ok_.any():
                    continue
                nl_ = int(y[ok_].sum()); beob = y[ok_].mean(); ges = pe[ok_].mean()
                vj = []
                for jj in (2024, 2025, 2026):
                    sj = ok_ & (JAHRe == jj)
                    if y[sj].sum() >= 30:
                        vj.append("%d %.2f" % (jj, y[sj].mean() / max(pe[sj].mean(), 1e-12)))
                    else:
                        vj.append("%d (%d Liq., zu wenige)" % (jj, int(y[sj].sum())))
                oh = ok_ & ~((STDe >= bs0 - H) & (STDe < bs1))
                vor5 = np.mean((XE["tu"][ok_] <= H) & (XE["tu"][ok_] < fl[ok_]))
                urteil = ""
                if L == 5 and H in (6, 12, 24):
                    q = beob / max(ges, 1e-12)
                    # Beschriftung korrigiert 29.09. (nach dem Lauf, Zahlen unveraendert): H0-2 gilt nur UEBER 1,25;
                    # unter 0,5 ist *sicherer als geschaetzt* - nach Abschnitt 4 bleibt die Tabelle dann vorsichtig
                    urteil = " -> H0-1 %s" % ("✔" if nl_ >= 30 and 0.5 <= q <= 1.25 else (
                        "zu wenige" if nl_ < 30 else ("⛔ H0-2 Aufschlag %.2f" % q if q > 1.25 else
                                                      "unter 0,5: sicherer als geschaetzt, Tabelle bleibt")))
                print("  %dx %3d h: %6d Einstiege · Liq. %5d · beob %.3f %% · gesch %.3f %% · beob/gesch %.2f · je Jahr %s · ohne 10./11.10. %.2f · +5 %% vor Liq. %.1f %%%s" % (
                    L, H, int(ok_.sum()), nl_, 100 * beob, 100 * ges, beob / max(ges, 1e-12), " · ".join(vj),
                    y[oh].mean() / max(pe[oh].mean(), 1e-12), 100 * vor5, urteil))
        print("  ⚠️ Kalibrierung nur aus der Liquidation; '+5 % vor Liq.' ist NUR Vergleich (Nutzer 29.09.)")
        print("SCHLUSS: vollstaendig")
        return 0
    print()
    print("=" * 120)
    print("TABELLE JE GRENZE (T: Ausgabe, KEINE Grenze gesetzt) - rollierend, gewaehlt wird die HOECHSTE Stufe mit "
          "geschaetzter Liquidationswahrscheinlichkeit <= Grenze")
    try:
        c = sqlite3.connect("file:%s?mode=ro" % HEBEL_DB, uri=True)
        hebel = {r_[0].upper() for r_ in c.execute("SELECT symbol FROM asset_hebel_settings")}
        c.close()
    except Exception:                                         # noqa: BLE001
        hebel = set()
    in_h = np.array([s.upper() in hebel for s in syms])[SYM] if hebel else np.zeros(n, bool)
    for H in HALTE:
        for nm in ("atr", "komb"):
            P = {L: PRED[(L, H, nm)] for L in STUFEN}
            ix = np.flatnonzero(np.all([np.isfinite(P[L]) for L in STUFEN], axis=0))
            if not len(ix):
                continue
            for g in GRENZEN_TAB:
                wahl = np.zeros(len(ix), np.int8)
                for L in sorted(STUFEN):
                    wahl = np.where(P[L][ix] <= g, L, wahl)
                teil = []
                for L in STUFEN:
                    s_ = ix[wahl == L]
                    teil.append("%dx %4.1f%% (liq %.2f%% / m0,0476 %.2f%%)" % (
                        L, 100 * np.mean(wahl == L), 100 * Y[(L, H, 0.09, False)][s_].mean() if len(s_) else np.nan,
                        100 * Y[(L, H, 0.0476, False)][s_].mean() if len(s_) else np.nan))
                kein = 100 * np.mean(wahl == 0)
                s5 = ix[(wahl == 5)]
                j_ = " ".join("%d %.2f%%" % (jj, 100 * Y[(5, H, 0.09, False)][s5[JAHR[s5] == jj]].mean())
                              for jj in (2024, 2025, 2026) if (JAHR[s5] == jj).sum() >= 100)
                hb = ix[in_h[ix]]
                print("  %3d h %-4s Grenze %4.1f %%: %s · kein Hebel %4.1f%% · 5x je Jahr %s · Hebelwerte: 5x %.1f%%" % (
                    H, nm, 100 * g, " · ".join(teil), kein, j_ or "-",
                    100 * np.mean(wahl[in_h[ix]] == 5) if len(hb) else np.nan))
    print()
    print("  ⚠️ Kurs %s: %s" % (kurs, "Spot-Tief zaehlt Dochte - eher zu viele Liquidationen (vorsichtig)"
                               if kurs == "spot" else "Binance-Markpreis"))
    print("  ⚠️ Gueltigkeit fuer die Anwendung erst auf der Einstiegsauswahl aus K1 Schritt 2 (H0, Pflicht).")
    print("SCHLUSS: vollstaendig")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
