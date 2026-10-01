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
    # ⭐ KERN SCHRITT 3 (Basisinfos/Voranalyse_Kern_Schritt3_Simulation_29_09.md): --simulation (WAHL 2024)
    # oder --simulation H,Z,g (BESTAETIGUNG 2025-01..2026-08, einmal); nur mit --einstiege und --kurs mark
    sim = "--simulation" in sys.argv
    sim_zelle = None
    if sim:
        i_ = sys.argv.index("--simulation")
        if i_ + 1 < len(sys.argv) and "," in sys.argv[i_ + 1]:
            a_, b_, c_ = sys.argv[i_ + 1].split(",")
            sim_zelle = (int(a_), (None if b_ in ("-", "ohne") else float(b_)), float(c_))
    SIM_H, SIM_Z, SIM_G = (6, 12, 24, 72), (0.03, 0.05, None), (0.005, 0.01, 0.02, 0.05)
    # ⭐ A (Basisinfos/Voranalyse_A_Positionsfuehrung_01_10.md Abschnitt 5): nachgezogener Stop k x ATR unter dem hoechsten
    # Markpreis-Hoch, Ausstieg mit Verzug v h (von Hand); Z-Platz traegt ("S", k, v), k None = ohne Stop
    STOPWAHL = "--stop-wahl" in sys.argv
    STOP_K, STOP_H, STOP_V = (None, 1.0, 1.5, 2.0, 3.0), (24, 72), (0, 1)
    if "--stop" in sys.argv:
        sim = True
        a_, b_, c_ = sys.argv[sys.argv.index("--stop") + 1].split(",")
        sim_zelle = (int(a_), ("S", None if b_ in ("-", "ohne") else float(b_), int(c_)), 0.02)
    if STOPWAHL:
        sim = True

    def fz(Z_):
        if isinstance(Z_, tuple):
            return "Stop %s v%d" % ("ohne" if Z_[1] is None else "%.1f ATR" % Z_[1], Z_[2])
        return "ohne" if Z_ is None else "+%d %%" % round(100 * Z_)
    SIM_JAHRE = (2025, 2026) if sim_zelle else (2024,)
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
    # O11 --zusatz: der Markpreis der neuen Assets liegt in einer EIGENEN Datei (hole_markpreis.py --zusatz)
    mark_z = (sqlite3.connect("file:%s?mode=ro" % os.path.join(os.path.dirname(MARK_DB), "markpreis_alle.db"), uri=True)
              if (kurs == "mark" and "--zusatz" in sys.argv) else None)
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
    SPE = {k: [] for k in ("atr", "std", "sym", "tu", "fl5", "fl3", "fl2", "mfe24", "wu", "gr")}
    # J (Voranalyse_J_Mindesthistorie_30_09.md): --gruppe <csv> markiert die NEU hinzugekommenen Einstiege (Auskunft J5)
    GR = set()
    if "--gruppe" in sys.argv:
        for zeile in open(sys.argv[sys.argv.index("--gruppe") + 1], encoding="utf-8").read().splitlines()[1:]:
            sy_, st_, g_ = zeile.split(";")
            if g_ == "1":
                GR.add((sy_, int(st_)))
    # N4 (Basisinfos/Voranalyse_N4_Simulation_Ruhe48_30_09.md): --wucht <csv> markiert *beide oben* (Auskunft N4-W)
    WU = set()
    if "--wucht" in sys.argv:
        for zeile in open(sys.argv[sys.argv.index("--wucht") + 1], encoding="utf-8").read().splitlines()[1:]:
            sy_, st_, w_ = zeile.split(";")
            if w_ == "1":
                WU.add((sy_, int(st_)))
    SIMR, SIMT, NSR, NSA = {}, {}, {}, {"atr": [], "std": [], "welt": []}
    SIM_RNG = np.random.default_rng(SAAT + 33)
    for si, (sym, rows, bis_ende) in enumerate(E2.kursreihen()):
        syms.append(sym)
        if (sym.upper() == "BTC" and "--mit-btc" not in sys.argv) or len(rows) < 500:
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
            mk_ = mark_z if (mark_z is not None and sym in E2.ZUSATZ_SYMBOLE) else mark
            gesperrt = {r[0] for r in mk_.execute(
                "SELECT monat FROM _abweichung WHERE symbol=? AND gesperrt=1", (sym,))}
            mp = {r[0]: (r[1], r[2], r[3]) for r in mk_.execute(
                "SELECT stunde, low / faktor, close / faktor, high / faktor FROM markpreis WHERE symbol=?", (sym,))
                if r[0][:7] not in gesperrt}
            tief = np.array([mp[x][0] if x in mp else np.nan for x in st], float)
            einstieg = np.array([mp[x][1] if x in mp else np.nan for x in st], float)
            hoch = np.array([mp[x][2] if x in mp else np.nan for x in st], float)
        else:
            tief = l
            einstieg = cc
            hoch = h
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
            ge_basis = ge.copy()
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
                # N4-W Auskunft: hoechstes Hoch binnen 24 h ueber dem Einstieg (MFE) und die Wucht-Marke
                mx_ = np.full(len(ae), -np.inf)
                for s in range(1, 25):
                    j = np.minimum(ae + s, n - 1)
                    mx_ = np.maximum(mx_, np.where(((ae + s) < n) & np.isfinite(hoch[j]), hoch[j] / E0e, -np.inf))
                SPE["mfe24"].append(mx_ - 1.0)
                SPE["wu"].append(np.array([(sym, int(x)) in WU for x in std[ae]], bool))
                SPE["gr"].append(np.array([(sym, int(x)) in GR for x in std[ae]], bool))
                if sim:
                    jr = np.array([int(x[:4]) for x in st], np.int16)

                    def ausgang(anker, zellen):
                        """-> {(H, Z, L): (Rendite auf den Einsatz, Ausstiegsstunde)} - Ziel am Markpreis-Hoch,
                        Liquidation am Markpreis-Tief (in derselben Stunde zaehlt die Liquidation), sonst Zeit."""
                        E0_ = einstieg[anker]
                        fl_ = {L: np.full(len(anker), 10 ** 6) for L in STUFEN}
                        fz_ = {Z: np.full(len(anker), 10 ** 6) for Z in SIM_Z if Z}
                        sm_ = max(SIM_H) + (5 if any(isinstance(z_[1], tuple) for z_ in zellen) else 0)
                        for s in range(1, sm_ + 1):
                            j = np.minimum(anker + s, n - 1)
                            gu_ = (anker + s) < n
                            lo_ = np.where(gu_, tief[j] / E0_, np.inf); hi_ = np.where(gu_, hoch[j] / E0_, -np.inf)
                            for L in STUFEN:
                                fl_[L] = np.where((fl_[L] > s) & (lo_ <= liq_schwelle(L, 0.09, s)), s, fl_[L])
                            for Z in fz_:
                                fz_[Z] = np.where((fz_[Z] > s) & (hi_ >= 1 + Z), s, fz_[Z])
                        aus = {}
                        for (H_, Z_) in [z_ for z_ in zellen if isinstance(z_[1], tuple)]:
                            # A: Stop-Linie = hoechstes Hoch bis zur VORSTUNDE minus k x ATR (Tages-ATR relativ zum Einstieg)
                            _s, k_, v_ = Z_
                            schluss = einstieg[np.minimum(anker + H_, n - 1)] / E0_
                            ts = np.full(len(anker), 10 ** 6); lv = np.full(len(anker), np.nan)
                            if k_ is not None:
                                a0 = atr[anker]; mx = np.ones(len(anker))
                                for s in range(1, H_ + 1):
                                    j = np.minimum(anker + s, n - 1); gu_ = (anker + s) < n
                                    lo_ = np.where(gu_, tief[j] / E0_, np.inf); hi_ = np.where(gu_, hoch[j] / E0_, -np.inf)
                                    lvl = mx - k_ * a0
                                    tr = (ts > s) & (lo_ <= lvl)
                                    ts = np.where(tr, s, ts); lv = np.where(tr, lvl, lv)
                                    mx = np.maximum(mx, np.where(np.isfinite(hi_), hi_, mx))
                            ausg = ts <= H_
                            te_s = np.where(ausg, ts + v_, H_)
                            if v_ == 0:
                                px = np.where(ausg, lv, schluss)
                            else:
                                px = np.where(ausg, einstieg[np.minimum(anker + te_s, n - 1)] / E0_, schluss)
                            for L in (1,) + STUFEN:
                                lt = fl_[L] if L > 1 else np.full(len(anker), 10 ** 6)
                                liq = lt <= te_s
                                te = np.where(liq, lt, te_s)
                                kosten = L * (0.003 + (0.0018 * te / 24.0 if L > 1 else 0.0))
                                r_ = np.where(liq, -1.0 - L * 0.01, L * (px - 1.0)) - kosten
                                aus[(H_, Z_, L)] = (r_, te)
                        for (H_, Z_) in [z_ for z_ in zellen if not isinstance(z_[1], tuple)]:
                            schluss = einstieg[np.minimum(anker + H_, n - 1)] / E0_
                            zt = fz_[Z_] if Z_ else np.full(len(anker), 10 ** 6)
                            for L in (1,) + STUFEN:
                                lt = fl_[L] if L > 1 else np.full(len(anker), 10 ** 6)
                                liq = (lt <= H_) & (lt <= zt)
                                zi = ~liq & (zt <= H_)
                                te = np.where(liq, lt, np.where(zi, zt, H_))
                                kosten = L * (0.003 + (0.0018 * te / 24.0 if L > 1 else 0.0))
                                roh = np.where(zi, L * (Z_ or 0.0), L * (schluss - 1.0))
                                r_ = np.where(liq, -1.0 - L * 0.01, roh) - kosten
                                aus[(H_, Z_, L)] = (r_, te)
                        return aus
                    zellen = [(sim_zelle[0], sim_zelle[1])] if sim_zelle else [(H_, Z_) for H_ in SIM_H for Z_ in SIM_Z]
                    if STOPWAHL:
                        zellen = [(24, None)] + [(H_, ("S", k_, v_)) for H_ in STOP_H for k_ in STOP_K for v_ in STOP_V]
                    elif sim_zelle and isinstance(sim_zelle[1], tuple):
                        # Bestaetigung A: dazu Auskunft v = 0/2/4 und die REGEL0-Zelle (24 h ohne Ziel) im selben Lauf
                        H0_, (_s, k0_, _v) = sim_zelle[0], sim_zelle[1]
                        zellen = zellen + [(H0_, ("S", k0_, vv)) for vv in (0, 2, 4) if vv != sim_zelle[1][2]] + [(24, None)]
                    ao = ausgang(ae, zellen)
                    for k_, (r_, te_) in ao.items():
                        SIMR.setdefault(k_, []).append(r_); SIMT.setdefault(k_, []).append(te_)
                    if sim_zelle:
                        # Nullwelt: die Einstiege je Asset ZEITVERSCHOBEN innerhalb der gueltigen Stunden 2025-26
                        W_ = np.flatnonzero(ge_basis & np.isin(jr, SIM_JAHRE))
                        # 29.09. behoben: eingestellte Paare ohne Stunden in 2025-26 haben ein LEERES W_
                        pos = np.searchsorted(W_, ae) if len(W_) else np.zeros(len(ae), int)
                        drin = ((pos < len(W_)) & (W_[np.minimum(pos, len(W_) - 1)] == ae)) if len(W_) else np.zeros(len(ae), bool)
                        if len(W_) > 2 * 1440 + 10 and drin.any():
                            for w_ in range(zieh):
                                k = int(SIM_RNG.integers(1440, len(W_) - 1440))
                                an = W_[(pos[drin] + k) % len(W_)]
                                a2 = ausgang(an, zellen)
                                for L in (1,) + STUFEN:
                                    NSR.setdefault(L, []).append(a2[(sim_zelle[0], sim_zelle[1], L)][0])
                                NSA["atr"].append(atr[an]); NSA["std"].append(std[an]); NSA["welt"].append(np.full(len(an), w_))
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
    if "--mit-btc" in sys.argv and "BTC" in syms:
        # 01.10. (BTC analog J): BTC-Anker NICHT ins ATR-Training - die Hebelstufe der uebrigen bleibt bitgleich;
        # die BTC-EINSTIEGE werden weiter simuliert (Vorhersage aus demselben Modell)
        keep_ = X["sym"] != syms.index("BTC")
        X = {k: v[keep_] for k, v in X.items()}; Y = {k: v[keep_] for k, v in Y.items()}
        print("  --mit-btc: %d BTC-Anker aus dem ATR-Training genommen" % int((~keep_).sum()))
    if "--zusatz" in sys.argv and E2.ZUSATZ_SYMBOLE:
        # O11: die neuen Assets NICHT ins ATR-Training (bewerten, nicht trainieren) - die Hebelstufe der uebrigen bleibt bitgleich
        keep_ = ~np.isin(X["sym"], [syms.index(s_) for s_ in E2.ZUSATZ_SYMBOLE if s_ in syms])
        X = {k: v[keep_] for k, v in X.items()}; Y = {k: v[keep_] for k, v in Y.items()}
        print("  --zusatz: %d Anker der neuen Assets aus dem ATR-Training genommen" % int((~keep_).sum()))
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
        if sim and sim_zelle and NSA["std"]:
            XN = {k: np.concatenate(v) for k, v in NSA.items()}
            STDn = XN["std"].astype(np.int64); MONn = monat_von(STDn)
            EEn = {"atr": XN["atr"].astype(np.float64)}
        else:
            STDn = np.zeros(0, np.int64); MONn = np.zeros(0, int); EEn = {"atr": np.zeros(0)}
        PN = {}
    for L in STUFEN:
        for H in HALTE:
            for ein, nm in (((EIN_ATR, "atr"),) if ein_datei else ((EIN_ATR, "atr"), (EIN_KOMB, "komb"))):
                y = Y[(L, H, 0.09, False)]
                p = np.full(n, np.nan)
                pe = np.full(len(STDe), np.nan) if ein_datei else None
                pn = np.full(len(STDn), np.nan) if ein_datei else None
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
                        zn = np.flatnonzero((MONn >= mi) & (MONn < mi + 3) & (MONn <= 2026 * 12 + 7))
                        if len(zn):
                            pn[zn] = expit(m_.z(EEn, zn, np.zeros(len(zn))))
                PRED[(L, H, nm)] = p
                if ein_datei:
                    PE[(L, H)] = pe
                    PN[(L, H)] = pn
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
            rb, rg, soll[0], soll[1], ("✔ bitgleich" if (rb, rg) == soll else "⛔ ABWEICHUNG") if E2.MENGE == "bestand" and kurs == "mark"
            else "(Referenz 2.681 nur fuer bestand/mark - Beschriftung korrigiert 30.09., Zahlen unveraendert)"))
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
        if sim:
            R_ = {k: np.concatenate(v) for k, v in SIMR.items()}; T_ = {k: np.concatenate(v) for k, v in SIMT.items()}
            if "--spur" in sys.argv:
                # Gegenpruefung A (nur Auskunft, aendert nichts): je Einstieg Symbol, Stunde, Spot-Rendite und Ausstiegsstunde der Stop-Zellen
                import csv as _csv
                with open(sys.argv[sys.argv.index("--spur") + 1], "w", newline="", encoding="utf-8") as f_:
                    w_ = _csv.writer(f_, delimiter=";")
                    ks_ = [k_ for k_ in R_ if k_[2] == 1]
                    w_.writerow(["symbol", "std", "jahr"] + sum([["%d_%s_r" % (k_[0], fz(k_[1])), "%d_%s_te" % (k_[0], fz(k_[1]))] for k_ in ks_], []))
                    for i_ in range(len(STDe)):
                        w_.writerow([syms[int(XE["sym"][i_])], int(STDe[i_]), int(JAHRe[i_])] + sum(
                            [["%.10g" % R_[k_][i_], "%d" % T_[k_][i_]] for k_ in ks_], []))
            bs0_, bs1_ = _h(datetime(2025, 10, 10)), _h(datetime(2025, 10, 12))

            def stufe(P, H_, g_):
                Ls = np.zeros(len(P[(5, H_)]), np.int8)
                for L in sorted(STUFEN):
                    Ls = np.where(np.isfinite(P[(L, H_)]) & (P[(L, H_)] <= g_), L, Ls)
                return Ls

            def kennz(r, stdx, te, f=0.01, maske=None):
                ok_ = np.isfinite(r) if maske is None else (np.isfinite(r) & maske)
                if not ok_.any():
                    return dict(G=np.nan, n=0, dd=np.nan, serie=0, schlecht=np.nan, mon={})
                o = np.argsort(stdx[ok_] + te[ok_]); rr = r[ok_][o]
                lg = np.log1p(f * rr); kum = np.cumsum(lg)
                dd = float(np.max(np.maximum.accumulate(np.r_[0.0, kum])[1:] - kum)) if len(kum) else 0.0
                verl = (rr < 0).astype(int); serie = 0; best = 0
                for v in verl:
                    serie = serie + 1 if v else 0; best = max(best, serie)
                mon = monat_von((stdx[ok_] + te[ok_]).astype(np.int64))[o]
                um = np.unique(mon); mw = [float(lg[mon == u].sum()) for u in um]
                return dict(G=float(kum[-1]), n=int(ok_.sum()), dd=dd, serie=best, schlecht=min(mw) if mw else np.nan,
                            mon=dict(zip(um.tolist(), mw)))
            per = np.isin(JAHRe, SIM_JAHRE)
            if "--spur-regel0" in sys.argv and sim_zelle and not isinstance(sim_zelle[1], tuple):
                # B Teil 0 (Voranalyse_B_Kern_stabilisieren_01_10.md Abschnitt 1, nur Auskunft, aendert nichts): je Handel der
                # Simulationszelle Symbol, Stunde, Hebelstufe, Hebelrendite, Kosten, Haltedauer, Liquidation und Spotrendite
                import csv as _csv
                H9_, Z9_, g9_ = sim_zelle
                L9 = stufe(PE, H9_, g9_)
                with open(sys.argv[sys.argv.index("--spur-regel0") + 1], "w", newline="", encoding="utf-8") as f_:
                    w_ = _csv.writer(f_, delimiter=";")
                    w_.writerow(["symbol", "std", "jahr", "stufe", "r", "kosten", "te", "liq", "spot"])
                    # --spur-alle: alle Jahre (L2 braucht 2024), sonst nur der Bestaetigungszeitraum
                    for i_ in np.flatnonzero(((per | ("--spur-alle" in sys.argv)) & (L9 > 0))):
                        L_ = int(L9[i_]); r_ = float(R_[(H9_, Z9_, L_)][i_]); te_ = float(T_[(H9_, Z9_, L_)][i_])
                        if not np.isfinite(r_):
                            continue
                        ko_ = L_ * (0.003 + 0.0018 * te_ / 24.0)
                        w_.writerow([syms[int(XE["sym"][i_])], int(STDe[i_]), int(JAHRe[i_]), L_, "%.10g" % r_, "%.10g" % ko_,
                                     "%d" % te_, int(r_ <= -1.0), "%.10g" % float(R_[(H9_, Z9_, 1)][i_])])
            print()
            print("=" * 120)
            if STOPWAHL:
                g_ = 0.02
                print("A · WAHL 2024 (Menge %s) - nachgezogener Stop, Grenze 2 %% (REGEL0), Kosten nach Doku; 2025-26 NICHT ausgewertet" % E2.MENGE)
                print("    %-4s %-18s %6s %7s %9s %9s %8s %9s | %9s" % ("H", "Ausstieg", "Handel", "Liq.%", "Konto", "Rueckg.", "Hebel", "schl.Mon", "Spot"))
                erg = []
                for (H_, Z_) in [(24, None)] + [(H_, ("S", k_, v_)) for H_ in STOP_H for k_ in STOP_K for v_ in STOP_V]:
                    Ls = stufe(PE, H_, g_)
                    r = np.full(len(Ls), np.nan); te = np.zeros(len(Ls))
                    for L in STUFEN:
                        w = Ls == L
                        r[w] = R_[(H_, Z_, L)][w]; te[w] = T_[(H_, Z_, L)][w]
                    r = np.where(per, r, np.nan)
                    k = kennz(r, STDe, te)
                    ks = kennz(np.where(per, R_[(H_, Z_, 1)], np.nan), STDe, T_[(H_, Z_, 1)])
                    hb = float(np.mean(Ls[per & (Ls > 0)])) if (per & (Ls > 0)).any() else np.nan
                    erg.append((H_, Z_, k))
                    print("    %-4d %-18s %6d %6.2f%% %+9.3f %9.3f %8.2f %+9.3f | %+9.3f" % (
                        H_, fz(Z_), k["n"], 100 * float(np.mean(r[per & np.isfinite(r)] <= -1.0)) if k["n"] else np.nan,
                        k["G"], k["dd"], hb, k["schlecht"], ks["G"]))
                a0_ = [e for e in erg if e[1] is None][0][2]["G"]; b0_ = [e for e in erg if e[1] == ("S", None, 1) and e[0] == 24][0][2]["G"]
                print("  R-R11 'ohne Stop, 24 h' (Stop-Rechnung, v1) %+.4f gegen die bisherige Rechnung (24 h, ohne Ziel) %+.4f -> %s" % (
                    b0_, a0_, "✔ bitgleich" if abs(a0_ - b0_) < 1e-12 else "⛔ ABWEICHUNG"))
                kand = [e for e in erg if isinstance(e[1], tuple) and e[1][2] == 1 and np.isfinite(e[2]["G"])]
                mx = max(e[2]["G"] for e in kand)
                gl = [e for e in kand if e[2]["G"] >= mx - np.log(1.01)]
                gl.sort(key=lambda e: (e[1][1] is not None, -(e[1][1] or 0.0), e[0]))
                w_ = gl[0]
                print("  REGEL (nur v = 1 h): groesstes Hebelkonto, Gleichstand < 1 % -> ohne Stop, dann groesseres k, dann kuerzeres H")
                print("    GEWAEHLT H = %d h · %s · Konto log %+.3f (x%.3f) · Rueckgang %.3f" % (
                    w_[0], fz(w_[1]), w_[2]["G"], np.exp(w_[2]["G"]), w_[2]["dd"]))
            elif not sim_zelle:
                print("KERN SCHRITT 3 · WAHL 2024 (Menge %s) - Konto f = 1 %% je Handel, Kosten nach Doku; 2025-26 NICHT ausgewertet" % E2.MENGE)
                print("    %-4s %-6s %-6s %6s %8s %9s %9s %8s %8s %9s | %9s" % ("H", "Ziel", "Grenze", "Handel", "Liq.%", "Konto", "Rueckg.", "Serie", "Hebel", "schl.Mon", "Spot"))
                erg = []
                for H_ in SIM_H:
                    for Z_ in SIM_Z:
                        rs, ts = R_[(H_, Z_, 1)], T_[(H_, Z_, 1)]
                        ks = kennz(np.where(per, rs, np.nan), STDe, ts)
                        for g_ in SIM_G:
                            Ls = stufe(PE, H_, g_)
                            r = np.full(len(Ls), np.nan); te = np.zeros(len(Ls))
                            for L in STUFEN:
                                w = Ls == L
                                r[w] = R_[(H_, Z_, L)][w]; te[w] = T_[(H_, Z_, L)][w]
                            r = np.where(per, r, np.nan)
                            k = kennz(r, STDe, te)
                            liq = np.mean([(r[(Ls == L) & per] <= -1.0).mean() if ((Ls == L) & per).any() else 0 for L in STUFEN])
                            hb = float(np.mean(Ls[per & (Ls > 0)])) if (per & (Ls > 0)).any() else np.nan
                            k05, k2 = kennz(r, STDe, te, 0.005), kennz(r, STDe, te, 0.02)
                            erg.append((H_, Z_, g_, k, k05, k2))
                            print("    %-4d %-6s %5.1f%% %6d %7.2f%% %+9.3f %9.3f %8d %8.2f %+9.3f | %+9.3f" % (
                                H_, fz(Z_), 100 * g_, k["n"],
                                100 * float(np.mean(r[per & np.isfinite(r)] <= -1.0)) if k["n"] else np.nan,
                                k["G"], k.get("dd", np.nan), k.get("serie", 0), hb, k.get("schlecht", np.nan), ks["G"]))
                gut = [e for e in erg if np.isfinite(e[3]["G"])]
                mx = max(e[3]["G"] for e in gut)
                kand = [e for e in gut if e[3]["G"] >= mx - np.log(1.01)]
                kand.sort(key=lambda e: (e[2], e[0]))
                w_ = kand[0]
                print("  REGEL groesstes Kontowachstum (Gleichstand < 1 %% Endwert -> kleinere Grenze, dann kuerzere Haltedauer):")
                print("    GEWAEHLT H = %d h · Ziel %s · Grenze %.1f %% · Konto log %+.3f (x%.3f) · Rueckgang %.3f" % (
                    w_[0], "ohne" if w_[1] is None else "+%d %%" % round(100 * w_[1]), 100 * w_[2], w_[3]["G"], np.exp(w_[3]["G"]), w_[3]["dd"]))
                for fi, nm_ in ((4, "f = 0,5 %"), (5, "f = 2 %")):
                    mb = max(gut, key=lambda e: e[fi]["G"])
                    print("    Auskunft %s: bestes H %d, Ziel %s, Grenze %.1f %% - %s" % (
                        nm_, mb[0], "ohne" if mb[1] is None else "+%d %%" % round(100 * mb[1]), 100 * mb[2],
                        "gleich" if mb[:3] == w_[:3] else "ANDERS"))
            else:
                H_, Z_, g_ = sim_zelle
                print("KERN SCHRITT 3 · BESTAETIGUNG 2025-01..2026-08 (EINMAL), H %d h, Ziel %s, Grenze %.1f %%, Menge %s" % (
                    H_, fz(Z_), 100 * g_, E2.MENGE))
                Ls = stufe(PE, H_, g_)
                r = np.full(len(Ls), np.nan); te = np.zeros(len(Ls))
                for L in STUFEN:
                    w = Ls == L
                    r[w] = R_[(H_, Z_, L)][w]; te[w] = T_[(H_, Z_, L)][w]
                r = np.where(per, r, np.nan)
                rs = np.where(per, R_[(H_, Z_, 1)], np.nan); ts = T_[(H_, Z_, 1)]
                k = kennz(r, STDe, te); ks = kennz(rs, STDe, ts)
                jz = [(jj, kennz(r, STDe, te, maske=(JAHRe == jj))["G"]) for jj in SIM_JAHRE]
                print("  Handel %d · Hebel im Mittel %.2f · Liquidationen %.2f %% · Konto log %+.4f (x%.3f) · Rueckgang %.3f · Serie %d · schlechtester Monat %+.4f" % (
                    k["n"], float(np.mean(Ls[per & (Ls > 0)])), 100 * float(np.mean(r[np.isfinite(r)] <= -1.0)),
                    k["G"], np.exp(k["G"]), k["dd"], k["serie"], k["schlecht"]))
                print("  S1 je Jahr: %s -> %s" % (" · ".join("%d %+.4f" % x for x in jz), "✔" if all(x[1] > 0 for x in jz) else "⛔"))
                # Nullwelt
                XNw = np.concatenate(NSA["welt"]) if NSA["welt"] else np.zeros(0)
                RN = {L: np.concatenate(NSR[L]) for L in NSR}
                Gn = []
                for w_ in range(zieh):
                    mw = XNw == w_
                    if not mw.any():
                        continue
                    Pw = {(L, H_): PN[(L, H_)][mw] for L in STUFEN}
                    Lw = stufe(Pw, H_, g_)
                    rw = np.full(int(mw.sum()), np.nan)
                    for L in STUFEN:
                        rw[Lw == L] = RN[L][mw][Lw == L]
                    Gn.append(float(np.nansum(np.log1p(0.01 * rw))))
                p90 = float(np.percentile(Gn, 90)) if Gn else np.nan
                print("  S2 Nullwelt (Einstiege je Asset zeitverschoben, %d Ziehungen): Mittel %+.4f, P90 %+.4f -> %s" % (
                    len(Gn), float(np.mean(Gn)) if Gn else np.nan, p90, "✔" if k["G"] > p90 else "⛔"))
                print("  S4 Hebel gegen Spot (dieselben Einstiege und Geometrie, 1x): Hebel %+.4f · Spot %+.4f -> %s" % (
                    k["G"], ks["G"], "✔ Hebel lohnt" if k["G"] > ks["G"] else "⛔ Hebel lohnt nicht"))
                oh = ~((STDe >= bs0_ - H_) & (STDe < bs1_))
                print("  S5 ohne 10./11.10.2025: Konto log %+.4f (mit %+.4f)" % (kennz(r, STDe, te, maske=oh)["G"], k["G"]))
                if isinstance(Z_, tuple):
                    # A: Auskunft Verzug und die REGEL0-Zelle im selben Lauf; Urteil *besser als REGEL0*
                    def konto_zelle(Hz, Zz):
                        Lz = stufe(PE, Hz, g_)
                        rz = np.full(len(Lz), np.nan); tz = np.zeros(len(Lz))
                        for L in STUFEN:
                            w = Lz == L
                            rz[w] = R_[(Hz, Zz, L)][w]; tz[w] = T_[(Hz, Zz, L)][w]
                        rz = np.where(per, rz, np.nan)
                        return kennz(rz, STDe, tz), rz
                    k0, r0 = konto_zelle(24, None)
                    print("  A R-R11 REGEL0-Zelle (24 h ohne Ziel) im selben Lauf: Konto log %+.4f · Rohvorteil %+.3f %%" % (
                        k0["G"], 100 * float(np.nanmean(np.where(per, R_[(24, None, 1)], np.nan) + 0.003))))
                    print("  A BESSER ALS REGEL0: Stop %+.4f gegen REGEL0 %+.4f -> %s · je Jahr Stop %s gegen REGEL0 %s" % (
                        k["G"], k0["G"], "✔" if k["G"] > k0["G"] else "⛔",
                        " · ".join("%d %+.4f" % (jj, kennz(r, STDe, te, maske=(JAHRe == jj))["G"]) for jj in SIM_JAHRE),
                        " · ".join("%d %+.4f" % (jj, kennz(r0, STDe, np.zeros(len(r0)), maske=(JAHRe == jj))["G"]) for jj in SIM_JAHRE)))
                    for vv in (0, 1, 2, 4):
                        if (H_, ("S", Z_[1], vv), 1) in R_:
                            kv_, _r = konto_zelle(H_, ("S", Z_[1], vv))
                            print("  A Auskunft Verzug %d h: Konto log %+.4f · Rueckgang %.3f" % (vv, kv_["G"], kv_["dd"]))
                # N4-R (Auskunft): Rohvorteil je Handel auf den Positionswert = Spot ohne Kosten (0,3 % zurueckgerechnet)
                roh_ = rs + 0.003
                okr = np.isfinite(roh_)
                SYMe_ = XE["sym"].astype(int)
                ga_ = [float(np.mean(roh_[okr & (SYMe_ == s_)])) > 0 for s_ in np.unique(SYMe_[okr]) if (okr & (SYMe_ == s_)).sum() >= 10]
                print("  N4-R Rohvorteil je Handel (Spot, ohne Kosten, auf den Positionswert): %+.3f %% (%d Handel) · je Jahr %s · "
                      "Kosten je Tageshandel 0,48 %% · Assets mit positivem Rohvorteil %d, %.0f %%" % (
                          100 * float(np.mean(roh_[okr])), int(okr.sum()),
                          " · ".join("%d %+.3f %%" % (jj, 100 * float(np.mean(roh_[okr & (JAHRe == jj)]))) for jj in SIM_JAHRE),
                          len(ga_), 100 * np.mean(ga_) if ga_ else np.nan))
                if "--je-asset" in sys.argv:
                    # Schritt 5 (Voranalyse_REGEL0_Hebelliste_30_09.md): je Asset Handel, Rohvorteil, Log-Beitrag zum Konto
                    # (additiv ueber Assets), Liquidationen - Auskunft fuer die Auswahl des Nutzers, keine Bewertung von Assets
                    SYMe_ = XE["sym"].astype(int)
                    lg_ = np.where(np.isfinite(r), np.log1p(0.01 * np.where(np.isfinite(r), r, 0.0)), 0.0)
                    print("  JE ASSET (symbol;handel;rohvorteil_prozent;konto_log;liquidationen;spot_log)")
                    for s_ in np.unique(SYMe_):
                        m_ = SYMe_ == s_
                        mr_ = m_ & np.isfinite(r); ms_ = m_ & np.isfinite(rs)
                        print("  ASSET;%s;%d;%.4f;%.5f;%d;%.5f" % (
                            syms[s_], int(ms_.sum()), 100 * float(np.mean(roh_[ms_])) if ms_.any() else float("nan"),
                            float(lg_[mr_].sum()), int((r[mr_] <= -1.0).sum()),
                            float(np.log1p(0.01 * rs[ms_]).sum()) if ms_.any() else 0.0))
                if GR:
                    gr_ = XE["gr"].astype(bool)
                    for nm_, m_ in (("neu", gr_), ("reif", ~gr_)):
                        mm_ = okr & m_
                        kw_ = kennz(r, STDe, te, maske=m_)
                        print("  J5 %-5s: %5d Handel · Rohvorteil %+.3f %% · Hebelkonto log %+.4f · Spotkonto log %+.4f · Liquidationen %.2f %% · je Jahr Rohvorteil %s" % (
                            nm_, int(mm_.sum()), 100 * float(np.mean(roh_[mm_])) if mm_.any() else np.nan, kw_["G"],
                            kennz(rs, STDe, ts, maske=m_)["G"], 100 * float(np.mean(r[np.isfinite(r) & m_] <= -1.0)) if (np.isfinite(r) & m_).any() else np.nan,
                            " · ".join("%d %+.3f %%" % (jj, 100 * float(np.mean(roh_[mm_ & (JAHRe == jj)]))) for jj in SIM_JAHRE if (mm_ & (JAHRe == jj)).any())))
                if "--wenig" in sys.argv:
                    # M1-2 A4 (Auskunft): Rohvorteil und Konto in den wenig-Monaten (K_IG < 1) gegen die uebrigen
                    wl_ = {z_.strip() for z_ in open(sys.argv[sys.argv.index("--wenig") + 1], encoding="utf-8") if z_.strip()}
                    wmi = np.isin(MONe, [int(x[:4]) * 12 + int(x[5:7]) - 1 for x in wl_])
                    for nm_, m_ in (("wenig", wmi), ("uebrig", ~wmi)):
                        mm_ = okr & m_
                        kw_ = kennz(r, STDe, te, maske=m_)
                        print("  M1-2 A4 %-7s: %5d Handel · Rohvorteil %+.3f %% · Hebelkonto log %+.4f · Spotkonto log %+.4f" % (
                            nm_, int(mm_.sum()), 100 * float(np.mean(roh_[mm_])) if mm_.any() else np.nan, kw_["G"],
                            kennz(rs, STDe, ts, maske=m_)["G"]))
                    print("  M1-2 A4 wenig-Monate: %s · Kosten je Tageshandel 0,48 %%" % ", ".join(sorted(wl_)))
                if WU:
                    wu_ = XE["wu"].astype(bool); mf_ = XE["mfe24"]
                    for nm_, m_ in (("beide oben", wu_), ("Rest", ~wu_)):
                        mm_ = okr & m_
                        kw_ = kennz(r, STDe, te, maske=m_)
                        print("  N4-W %-10s: %5d Handel · Rohvorteil %+.3f %% · Hoch binnen 24 h (MFE) %+.2f %% · Hebelkonto log %+.4f · je Jahr Rohvorteil %s" % (
                            nm_, int(mm_.sum()), 100 * float(np.mean(roh_[mm_])) if mm_.any() else np.nan,
                            100 * float(np.nanmean(np.where(np.isfinite(mf_[mm_]), mf_[mm_], np.nan))) if mm_.any() else np.nan, kw_["G"],
                            " · ".join("%d %+.3f %%" % (jj, 100 * float(np.mean(roh_[mm_ & (JAHRe == jj)]))) for jj in SIM_JAHRE)))
                print("  Pflichtauskunft Regime (Monatsbeitrag zum log-Konto): " + " · ".join(
                    "%d-%02d %+.4f" % (mm // 12, mm % 12 + 1, v) for mm, v in sorted(k["mon"].items())))
                h2 = np.isfinite(r) & (MONe >= 2025 * 12 + 6) & (MONe <= 2025 * 12 + 11)
                k2 = kennz(r, STDe, te, maske=h2)
                print("  Juli-Dezember 2025: %d Handel · Konto log %+.4f (x%.3f) · Rueckgang %.3f · Liquidationen %.2f %%" % (
                    k2["n"], k2["G"], np.exp(k2["G"]), k2["dd"], 100 * float(np.mean(r[h2] <= -1.0)) if h2.any() else np.nan))
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
