# -*- coding: utf-8 -*-
"""E2: welche Beitraege zeigen zum Pruefzeitpunkt eine POSITIVE oder NEGATIVE Lage?

**27.09.2026.** Nutzerauftrag: *"ermittle die notwendigen Beitraege, deren
optimale Lage positiv (oder negativ als Ausschluss, Sperre) aus der
Vergangenheit ueber den Markt aller Assets - jene, die funktionieren, werden
in unser System integriert."* Und: *"Momentaufnahme OHNE ZEIT, ohne
Geometrie ... Hebel ist kurzer Handel, eher 1 TAG - KURZ SCHNELL HOCH."*

DIE BEWERTUNG KENNT KEINE ZEIT. Um zu LERNEN, welche Lage gut war, braucht es
einmal einen Blick auf das, was danach kam - das Beobachtungsfenster ist nur
der Lehrer (24 h, Kontrolle 6 h und 72 h), nicht Teil der Bewertung. Kein
Stop, kein Trailing, kein Ziel.

DER MASSSTAB IST DAS EIGENE ASSET (Nutzervorgabe *"wir vergleichen keine
Assets"*, *"muss auch bei nur EINEM Asset funktionieren"*): jede Auswahl wird
gegen die Grundrate DESSELBEN Symbols gehalten (E1: die Grundrate schwankt je
Asset um Faktor 2,6). Die Nullwelt ist SYMBOLTREU - je Symbol so viele
Zufallsanker aus dessen eigener Zeit wie die Auswahl hat. Die tagestreue
Nullwelt laeuft nur als KONTROLLE mit (Haeufung an Markttagen), sie urteilt
nicht. ⚠️ Das weicht vom Spot-Messstandard ab (Tagesklammer) - begruendet in
2.653 und der Nutzervorgabe Assetebene.

DIE ZIELGROESSEN, je Anker, binnen 24 h (6 und 72 h als Kontrolle):
    auf5      +5 % wird erreicht, BEVOR -5 % eintritt        (Chance, Richtung)
    ab5       -5 % wird erreicht, BEVOR +5 % eintritt        (Gefahr, Richtung)
    auf10     +10 % wird erreicht, bevor -5 % eintritt       (hoch und schnell)
    mfe       groesster Anstieg in Prozent                   (Hoehe)
    maevp     groesster Rueckgang VOR dem Hoechstpunkt, %    (Risiko)
    ⚠️ Gleichstand in einer Stunde = der Rueckgang zuerst (2.583).

DIE KANDIDATEN - alle KAUSAL, zum Pruefzeitpunkt bekannt:
    Kurs     ema_abstand_atr, momentum_kurz, rsi, bandenge, vola_kausal,
             volumenschub
    Termin   oi_aenderung, konten_verh, taker_verh, top_konten_verh,
             top_summe_verh, oi_je_umsatz   (Wert ~HH:55, Anker ist der
             Schlusskurs HH:59)
    Funding  funding_vortag - die Tagessumme des VORTAGS (2.652-vorgriff)
    ⚠️ `vola_kausal` teilt die ATR durch ihren Median der VERGANGENEN 30 Tage;
    2.650 teilte durch den Median der GANZEN Reihe - ein Vorgriff.

LUECKEN: Anker, deren Rueckblick (240 h) oder Vorausblick (72 h) eine Luecke
in der Stundenreihe ueberspannt, werden ausgeschlossen (47 Symbole haben
Luecken, bis 3.701 Stunden). Die aelteren Werkzeuge zaehlen Zeilen statt
Stunden.

JE AUSWAHL (Schwellen aus den eigenen Perzentilen 1/5/95/99, absolut)
    Lift      Rate der Auswahl / Grundrate der eigenen Symbole
    z         gegen die symboltreue Nullwelt (40 Ziehungen)
    Grenze    Bestes-von-N ueber ALLE Auswahlen je Zielgroesse, zweiseitig
    Jahre     Kalenderjahre mit demselben Vorzeichen (mind. 10 erwartete
              Ereignisse)
    Weglass   Weglassen je eines Jahres - bleibt das Vorzeichen?
    je Asset  Anteil der Symbole (mind. 30 Anker) mit demselben Vorzeichen
    Spiegel   Lift(auf5) / Lift(ab5), geeichte Schwelle 1,717 (2.603)
    Kontrolle Lift gegen die tagestreue Nullwelt

TEIL 2 BESTAETIGUNG (Nutzerhinweis *"kann man kompensieren, indem man oft
prueft und ggf. die Richtung bestaetigt wird"*): fuer die Auswahlen mit
positiver Richtung - Signal vor k Stunden UND Kurs seither gestiegen, Einstieg
jetzt. Traegt die Bestaetigung mehr als das Signal allein?

NUR LESEND (`mode=ro`), importiert nichts aus `agent/`. Keine Gebuehren
(Regel 2). Ebene B (2.641).
"""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hebel_neubau import pruefe_quellen                          # noqa: E402

KURS = ("ema_abstand_atr", "momentum_kurz", "rsi", "bandenge", "vola_kausal",
        "volumenschub")
TERMIN = ("oi_aenderung", "konten_verh", "taker_verh", "top_konten_verh",
          "top_summe_verh", "oi_je_umsatz")
FUNDING = ("funding_vortag",)
MERKMALE = KURS + TERMIN + FUNDING
pruefe_quellen(*[m for m in MERKMALE if m not in ("vola_kausal",
                                                   "funding_vortag")],
               "vola", "funding")

HIER = os.path.dirname(os.path.abspath(__file__))
STUNDEN_DB = os.path.join(HIER, "data", "stundenkurse.db")
TERMIN_DB = os.path.join(HIER, "data", "terminmarkt_historie.db")
FUNDING_DB = os.path.join(HIER, "data", "funding_historie.db")
EINGESTELLT_DB = os.path.join(HIER, "data", "eingestellt_historie.db")
MESSDATEN_DB = os.path.join(HIER, "data", "messdaten.db")

# ⭐ MENGENWAHL (Befund 2.668, Voranalyse Nachladen 27.09.2026). Die Vorgabe
# ist der BESTAND - jeder Befund bis 2.667 bleibt bitgleich reproduzierbar.
#   bestand          data/stundenkurse.db wie bisher (ueberlebensverzerrt)
#   mit              Bestand + alle eingestellten Paare (+ Vorgeschichte)
#   unverzerrt:<s>   nur die 100 zufaellig GEZOGENEN (ohne Watchlist) + eine
#                    Stichprobe der Eingestellten mit DERSELBEN Ziehrate, aus
#                    demselben Rahmen (in messdaten.db) - Saat <s>
# Die Ziehrate: 100 aus rund 305 (heute gehandelte Perpetuals in messdaten.db,
# Ziehtag 01.09.2026) - eine Naeherung, der Rahmen am Ziehtag ist nicht
# gespeichert.
MENGE = "bestand"
ZIEHRATE = 100.0 / 305.0
# das Ladefenster von hole_eingestellte.py endet 2026-08; eine Reihe, die in
# den letzten Tagen davor endet, ist abgeschnitten, nicht eingestellt
FENSTERENDE_EINGESTELLT = "2026-08-28 00:00"


def menge_aus_argv(argv=None) -> str:
    """Liest `--menge ...` aus der Befehlszeile und setzt MENGE."""
    global MENGE
    argv = sys.argv if argv is None else argv
    if "--menge" in argv:
        MENGE = argv[argv.index("--menge") + 1]
    return MENGE


def kursreihen() -> list:
    """-> [(symbol, rows, bis_ende)] nach MENGE; rows = (stunde, high, low, close, volumen).

    `bis_ende`: eingestellte Reihen - Anker bis zum echten Ende zugelassen
    (Nutzerentscheidung N3: eine offene Position wird bei der Einstellung
    abgerechnet; sonst fehlt genau der Absturz).
    """
    cs = sqlite3.connect("file:%s?mode=ro" % STUNDEN_DB, uri=True)
    bestand = [r[0] for r in cs.execute(
        "SELECT symbol FROM stundenkurse GROUP BY symbol "
        "HAVING COUNT(*) > 2000 ORDER BY COUNT(*) DESC")]
    q = "SELECT stunde, high, low, close, volumen FROM stundenkurse WHERE symbol=? ORDER BY stunde"
    if MENGE == "bestand":
        aus = [(sym, cs.execute(q, (sym,)).fetchall(), False) for sym in bestand]
        cs.close()
        return aus
    ce = sqlite3.connect("file:%s?mode=ro" % EINGESTELLT_DB, uri=True)
    art = {r[0]: r[1] for r in ce.execute(
        "SELECT symbol, art FROM symbole WHERE art IN ('eingestellt','vorgeschichte')")}
    eing = [r[0] for r in ce.execute(
        "SELECT s.symbol FROM stundenkurse s JOIN symbole y ON s.symbol=y.symbol "
        "WHERE y.art='eingestellt' GROUP BY s.symbol HAVING COUNT(*) > 2000 ORDER BY s.symbol")]
    if MENGE.startswith("unverzerrt"):
        ct = sqlite3.connect("file:%s?mode=ro" % TERMIN_DB, uri=True)
        gezogen = {r[0] for r in ct.execute("SELECT symbol FROM messbasis")}
        ct.close()
        md = sqlite3.connect("file:%s?mode=ro" % MESSDATEN_DB, uri=True)
        rahmen = {str(r[0]).upper() for r in md.execute(
            "SELECT DISTINCT symbol FROM price_history_ohlc WHERE currency='USD'")}
        md.close()
        saat = int(MENGE.split(":")[1]) if ":" in MENGE else 1
        rng = np.random.default_rng(saat)
        bestand = [x for x in bestand if x in gezogen or ("--mit-btc" in sys.argv and x.upper() == "BTC")]
        kand = [x for x in eing if x in rahmen]
        eing = [x for x in kand if rng.random() < ZIEHRATE]
    elif MENGE != "mit":
        raise SystemExit("unbekannte --menge %r (bestand | mit | unverzerrt:<saat>)" % MENGE)
    aus = []
    for sym in bestand:
        rows = cs.execute(q, (sym,)).fetchall()
        if art.get(sym) == "vorgeschichte":
            rows = ce.execute(q, (sym,)).fetchall() + rows
        aus.append((sym, rows, False))
    for sym in eing:
        rows = ce.execute(q, (sym,)).fetchall()
        # ⚠️ N3 nur, wenn die Reihe VOR dem Ladefenster endet (2026-08) - endet
        # sie am Fensterrand, ist das kein Einstellen, sondern unser Schnitt
        aus.append((sym, rows, bool(rows) and rows[-1][0] < FENSTERENDE_EINGESTELLT))
    cs.close(); ce.close()
    return aus


def funding_je_tag(sym: str) -> dict:
    """funding-Tagessummen - Bestand, bei MENGE != bestand ergaenzt um die Eingestellten."""
    cf = sqlite3.connect("file:%s?mode=ro" % FUNDING_DB, uri=True)
    fu = {str(d)[:10]: float(v) for d, v in cf.execute(
        "SELECT datum, wert FROM funding WHERE symbol=? AND wert IS NOT NULL", (sym,))}
    cf.close()
    if MENGE != "bestand" and os.path.exists(EINGESTELLT_DB):
        ce = sqlite3.connect("file:%s?mode=ro" % EINGESTELLT_DB, uri=True)
        for d, v in ce.execute("SELECT datum, wert FROM funding WHERE symbol=?", (sym,)):
            fu.setdefault(str(d)[:10], float(v))
        ce.close()
    return fu

EMA_L, VORLAUF, HMAX, H = 48, 240, 72, 24
KONTROLL_H = (6, 72)
PERZENTILE = (1, 5, 95, 99)
ZIEHUNGEN, SAAT = 40, 20260927
SPIEGEL = 1.717
MIN_ASSET, MIN_EREIGNISSE = 30, 10
BESTAETIGUNG_K = (1, 3)
ZIELE = ("auf5", "ab5", "auf10", "mfe", "maevp")


def _ema(x, p):
    a = 2.0 / (p + 1.0)
    return pd.Series(x).ewm(alpha=a, adjust=False).mean().to_numpy()


def _atr(h, l, cc):
    """Wie `messe_hebel_geometrie_neutral.atr_tag_relativ` - streng kausal."""
    sp = (h - l) / np.maximum(cc, 1e-12)
    m = pd.Series(sp).rolling(24, min_periods=24).mean().to_numpy()
    return m * np.sqrt(24.0)


def _rsi14(cc):
    """Wie `messe_lage_vor_der_bewegung.rsi14`."""
    d = np.diff(cc, prepend=cc[0])
    auf = pd.Series(np.where(d > 0, d, 0.0)).rolling(14, min_periods=1).sum() / 14
    ab = pd.Series(np.where(d < 0, -d, 0.0)).rolling(14, min_periods=1).sum() / 14
    with np.errstate(divide="ignore", invalid="ignore"):
        return (100.0 - 100.0 / (1.0 + auf / np.maximum(ab, 1e-12))).to_numpy()


def kursmerkmale(h, l, cc, vol):
    atr = _atr(h, l, cc)
    e = _ema(cc, EMA_L)
    with np.errstate(divide="ignore", invalid="ignore"):
        w = (cc - e) / np.maximum(atr * cc, 1e-12)
        vor6 = np.concatenate([np.full(6, np.nan), cc[:-6]])
        mom = (cc / vor6 - 1.0) / np.maximum(atr, 1e-12)
        sd = pd.Series(cc).rolling(EMA_L, min_periods=1).std(ddof=0).to_numpy()
        bandenge = 4.0 * sd / np.maximum(atr * cc, 1e-12)
        med = pd.Series(atr).rolling(720, min_periods=240).median().to_numpy()
        vola = atr / np.maximum(med, 1e-12)
        mit = pd.Series(vol).rolling(168, min_periods=168).mean().to_numpy()
        vs = vol / np.maximum(mit, 1e-12)
    return {"ema_abstand_atr": w, "momentum_kurz": mom, "rsi": _rsi14(cc),
            "bandenge": bandenge, "vola_kausal": vola, "volumenschub": vs,
            "atr": atr}


def ergebnisse(h, l, cc, hmax=None, erste=()):
    """-> erste Treffer (Stunden) und MFE/MAE-vor-Hoechstpunkt je Fenster.

    `erste`: weitere Schwellen als (Name, Faktor, oben) - fuer E2c.
    """
    hmax = HMAX if hmax is None else hmax
    stufen = (("up5", 1.05, True), ("dn5", 0.95, False),
              ("up10", 1.10, True)) + tuple(erste)
    n = len(cc)
    idx = np.arange(n)
    t = {k: np.full(n, 999, np.int16) for k, _g, _o in stufen}
    hoch = np.full(n, -np.inf)
    tief = np.full(n, np.inf)
    maevp = np.zeros(n)
    mfe_h, maevp_h = {}, {}
    for s in range(1, hmax + 1):
        j = np.minimum(idx + s, n - 1)
        hj, lj = h[j], l[j]
        for k, grenze, oben in stufen:
            neu = (t[k] == 999) & ((hj >= cc * grenze) if oben
                                   else (lj <= cc * grenze))
            t[k][neu] = s
        tief = np.minimum(tief, lj)
        neuhoch = hj > hoch
        hoch = np.where(neuhoch, hj, hoch)
        # Rueckgang VOR dem Hoechstpunkt: der tiefste Kurs bis einschliesslich
        # der Stunde des neuen Hoechstpunkts (konservativ - Reihenfolge in der
        # Stunde unbekannt)
        maevp = np.where(neuhoch, 1.0 - tief / cc, maevp)
        if s in (6, 24, 72, 120):
            mfe_h[s] = hoch / cc - 1.0
            maevp_h[s] = maevp.copy()
    return t, mfe_h, maevp_h


def zielwerte(t, mfe_h, maevp_h, fenster):
    return {"auf5": ((t["up5"] <= fenster) & (t["up5"] < t["dn5"])).astype(float),
            "ab5": ((t["dn5"] <= fenster) & (t["dn5"] <= t["up5"])).astype(float),
            "auf10": ((t["up10"] <= fenster) & (t["up10"] < t["dn5"])).astype(float),
            "mfe": 100.0 * mfe_h[fenster], "maevp": 100.0 * maevp_h[fenster]}


def lade(hmax=None, erste=(), mit_atr=False, ab=None, bis=None):
    """-> dict mit Merkmalen F, Zielwerten Z je Fenster und den Ankerspalten - NUR LESEND.

    Ohne Argumente genau die Menge von E2 (72 h Vorausblick). `hmax` und
    `erste` (weitere Schwellen, siehe `ergebnisse`) fuer E2c; dann kommen
    zusaetzlich T (erste Treffer je Schwelle), MFE/MAEVP bis `hmax` und X
    (eigene Rendite der letzten 24 und 120 h, kausal) zurueck.
    `mit_atr`: zusaetzlich ATR (Tagesmass, relativ, kausal) je Anker - fuer
    die Hoehe in ATR statt Prozent (2.662).
    `ab` / `bis`: nur Anker in [ab, bis) (Stunden seit 2020-01-01) behalten -
    spart Speicher (E2f mit den Eingestellten: 5,5 Mio Anker). Die Merkmale
    werden weiter aus der GANZEN Reihe gerechnet; die behaltenen Anker sind
    bitgleich zu einem Lauf ohne Grenze.
    """
    HMAX = globals()["HMAX"] if hmax is None else hmax
    ct = sqlite3.connect("file:%s?mode=ro" % TERMIN_DB, uri=True)
    ce_tm = None
    if MENGE != "bestand" and os.path.exists(EINGESTELLT_DB):
        ce_tm = sqlite3.connect("file:%s?mode=ro" % EINGESTELLT_DB, uri=True)
        if not ce_tm.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='terminmarkt'").fetchone()[0]:
            ce_tm.close(); ce_tm = None
    reihen = kursreihen()
    syms = [r[0] for r in reihen]
    basis = datetime(2020, 1, 1)
    F = {m: [] for m in MERKMALE}
    Z = {f: {z: [] for z in ZIELE} for f in (H,) + KONTROLL_H}
    STD, SYM, CC, JAHR = [], [], [], []
    ATR = []
    T = {k: [] for k, _g, _o in erste}
    X = {k: [] for k in ("vor24", "vor120", "mfe_max", "maevp_max")}
    ausgeschlossen = 0
    for si, (sym, rows, bis_ende) in enumerate(reihen):
        if sym.upper() == "BTC" and "--mit-btc" not in sys.argv:   # 01.10.: BTC als Asset nur mit --mit-btc (Leitwert)
            continue
        if len(rows) < 500:
            continue
        st = [r[0] for r in rows]
        h = np.array([r[1] for r in rows], float)
        l = np.array([r[2] for r in rows], float)
        cc = np.array([r[3] for r in rows], float)
        vol = np.array([(r[4] or 0.0) for r in rows], float)
        stunde = np.array([int((datetime.strptime(x, "%Y-%m-%d %H:%M") - basis)
                               .total_seconds() // 3600) for x in st], np.int64)
        n = len(cc)
        idx = np.arange(n)
        gu = np.isfinite(cc) & (cc > 0)
        gu[:VORLAUF] = False
        vor = np.clip(idx - VORLAUF, 0, n - 1)
        nach = np.clip(idx + HMAX, 0, n - 1)
        if bis_ende:
            # N3: Anker bis zum echten Ende. ⚠️ Auch dann muss der Rest der
            # Reihe LUECKENLOS sein - sonst schaut ein Anker ueber die Luecke
            # in ein anderes Asset (LUNA: das neue LUNA unter altem Ticker,
            # Anstieg 50 Mio Prozent; gefunden 28.09. im Vergleich)
            drin = idx + HMAX < n
            rest_lueckenlos = (stunde[n - 1] - stunde) == (n - 1 - idx)
            luecke = ((stunde - stunde[vor]) != VORLAUF) | np.where(
                drin, (stunde[nach] - stunde) != HMAX, ~rest_lueckenlos)
        else:
            gu[max(0, n - HMAX):] = False
            luecke = ((stunde - stunde[vor]) != VORLAUF) | ((stunde[nach] - stunde) != HMAX)
        ausgeschlossen += int((gu & luecke).sum())
        gu &= ~luecke
        if ab is not None:
            gu &= stunde >= ab
        if bis is not None:
            gu &= stunde < bis
        sel = np.flatnonzero(gu)
        if not len(sel):
            continue
        km = kursmerkmale(h, l, cc, vol)
        tm = {str(r[0]): r[1:] for r in ct.execute(
            "SELECT stunde, oi, oi_wert, taker_verh, konten_verh, "
            "top_konten_verh, top_summe_verh FROM terminmarkt WHERE symbol=?",
            (sym,))}
        if ce_tm is not None:
            # Teil B (28.09.): Terminmarkt der Eingestellten und der
            # Vorgeschichte - ergaenzt, was im Bestand fehlt; bei derselben
            # Stunde gilt der Bestand
            for r in ce_tm.execute(
                    "SELECT stunde, oi, oi_wert, taker_verh, konten_verh, "
                    "top_konten_verh, top_summe_verh FROM terminmarkt WHERE symbol=?",
                    (sym,)):
                tm.setdefault(str(r[0]), r[1:])
        leer = (None,) * 6

        def spalte(i):
            return np.array([(tm.get(x, leer)[i] if tm.get(x, leer)[i]
                              is not None else np.nan) for x in st], float)
        oi, oiw = spalte(0), spalte(1)
        with np.errstate(divide="ignore", invalid="ignore"):
            oi24 = np.concatenate([np.full(24, np.nan), oi[:-24]])
            km["oi_aenderung"] = oi / np.maximum(oi24, 1e-12) - 1.0
            km["oi_je_umsatz"] = oiw / np.maximum(vol * cc, 1e-12)
        km["taker_verh"], km["konten_verh"] = spalte(2), spalte(3)
        km["top_konten_verh"], km["top_summe_verh"] = spalte(4), spalte(5)
        fu = funding_je_tag(sym)
        vortag = {}
        km["funding_vortag"] = np.array([
            fu.get(vortag.setdefault(x[:10], (datetime.strptime(x[:10], "%Y-%m-%d")
                                              - timedelta(days=1)).strftime("%Y-%m-%d")),
                   np.nan) for x in st], float)
        t, mfe_h, maevp_h = ergebnisse(h, l, cc, HMAX, erste)
        for f in (H,) + KONTROLL_H:
            zw = zielwerte(t, mfe_h, maevp_h, f)
            for z in ZIELE:
                Z[f][z].append(zw[z][sel])
        if erste:
            for k, _g, _o in erste:
                T[k].append(t[k][sel])
            with np.errstate(divide="ignore", invalid="ignore"):
                v24 = np.concatenate([np.full(24, np.nan), cc[:-24]])
                v120 = np.concatenate([np.full(120, np.nan), cc[:-120]])
                X["vor24"].append((cc / v24 - 1.0)[sel])
                X["vor120"].append((cc / v120 - 1.0)[sel])
            X["mfe_max"].append(100.0 * mfe_h[max(mfe_h)][sel])
            X["maevp_max"].append(100.0 * maevp_h[max(maevp_h)][sel])
        for m in MERKMALE:
            F[m].append(km[m][sel])
        if mit_atr:
            ATR.append(km["atr"][sel])
        STD.append(stunde[sel])
        SYM.append(np.full(len(sel), si, np.int32))
        CC.append(cc[sel])
        JAHR.append(np.array([int(st[i][:4]) for i in sel], np.int16))
    ct.close()
    if ce_tm is not None:
        ce_tm.close()
    F = {m: np.concatenate(v) for m, v in F.items()}
    Z = {f: {z: np.concatenate(v) for z, v in d.items()} for f, d in Z.items()}
    STD = np.concatenate(STD); SYM = np.concatenate(SYM)
    CC = np.concatenate(CC); JAHR = np.concatenate(JAHR)
    TAG = STD // 24
    n = len(SYM)
    aus = dict(F=F, Z=Z, STD=STD, SYM=SYM, CC=CC, JAHR=JAHR, TAG=TAG,
               n=n, ausgeschlossen=ausgeschlossen)
    if mit_atr:
        aus["ATR"] = np.concatenate(ATR)
    if erste:
        aus["T"] = {k: np.concatenate(v) for k, v in T.items()}
        aus["X"] = {k: np.concatenate(v) for k, v in X.items()}
        aus["syms"] = syms
    return aus


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    print("=" * 118)
    print("E2 - WELCHE BEITRAEGE ZEIGEN EINE POSITIVE ODER NEGATIVE LAGE? "
          "(Momentaufnahme, Lehrer-Fenster %d h)" % H)
    print("=" * 118)
    print("  Massstab: das EIGENE Asset · Nullwelt symboltreu, %d Ziehungen · "
          "Kontrolle tagestreu · kein Stop, kein Trailing" % ZIEHUNGEN)
    print("  ⚠️ Gleichstand in einer Stunde = Rueckgang zuerst · ohne "
          "Gebuehren und Finanzierung (Regel 2)")
    print()

    D = lade()
    F, Z, STD, SYM, CC, JAHR, TAG = (D[k] for k in ("F", "Z", "STD", "SYM", "CC", "JAHR", "TAG"))
    n, ausgeschlossen = D["n"], D["ausgeschlossen"]
    print("  %d Anker · %d Symbole · %d Tage · %d Anker wegen Luecken "
          "ausgeschlossen" % (n, len(np.unique(SYM)), len(np.unique(TAG)),
                              ausgeschlossen))
    print("  Abdeckung je Merkmal: " + " · ".join(
        "%s %.1f%%" % (m, 100 * np.mean(np.isfinite(F[m]))) for m in MERKMALE))
    print()
    rng = np.random.default_rng(SAAT)
    ZH = Z[H]

    # Grundrate je Symbol und Zielgroesse
    nsym = int(SYM.max()) + 1
    anz = np.maximum(np.bincount(SYM, minlength=nsym), 1)
    basis_sym = {z: np.bincount(SYM, weights=ZH[z], minlength=nsym) / anz
                 for z in ZIELE}

    # symboltreue Ziehung: zu jedem Auswahlanker ein Zufallsanker DESSELBEN
    # Symbols aus dessen verfuegbaren Ankern (Merkmal vorhanden)
    def sym_pool(verfuegbar):
        ids = np.flatnonzero(verfuegbar)
        o = ids[np.argsort(SYM[ids], kind="stable")]
        s = SYM[o]
        start = np.searchsorted(s, np.arange(nsym), "left")
        ende = np.searchsorted(s, np.arange(nsym), "right")
        return o, start, ende - start

    def ziehe_sym(maske, pool):
        o, start, laenge = pool
        s = SYM[maske]
        r = (rng.random(len(s)) * np.maximum(laenge[s], 1)).astype(np.int64)
        return o[start[s] + r]

    tsort = np.argsort(TAG, kind="stable")
    tt = TAG[tsort]
    ut = np.unique(tt)
    t_start = np.searchsorted(tt, ut, "left")
    t_len = np.searchsorted(tt, ut, "right") - t_start
    t_pos = {int(u): i for i, u in enumerate(ut)}

    def ziehe_tag(maske):
        ti = np.array([t_pos[int(x)] for x in TAG[maske]])
        r = (rng.random(len(ti)) * t_len[ti]).astype(np.int64)
        return tsort[t_start[ti] + r]

    # Auswahlen
    AUS = []
    for m in MERKMALE:
        v = F[m]
        ok = np.isfinite(v)
        if ok.mean() < 0.5:
            print("  ⚠️ %s: nur %.1f%% Abdeckung - trotzdem gemessen, "
                  "Pool nur verfuegbare Anker" % (m, 100 * ok.mean()))
        q = np.percentile(v[ok], PERZENTILE)
        pool = sym_pool(ok)
        for p, sw in zip(PERZENTILE, q):
            maske = ok & ((v <= sw) if p < 50 else (v >= sw))
            AUS.append((m, p, float(sw), maske, pool))

    def lift(maske, z, werte=None):
        x = ZH[z] if werte is None else werte
        b = basis_sym[z][SYM[maske]].mean()
        wert = x[maske].mean()
        return (wert / b if z in ("auf5", "ab5", "auf10") and b > 0
                else wert - b)

    # Nullwelten
    null = {z: np.zeros((ZIEHUNGEN, len(AUS))) for z in ZIELE}
    for zi in range(ZIEHUNGEN):
        for ai, (_m, _p, _sw, maske, pool) in enumerate(AUS):
            idx = ziehe_sym(maske, pool)
            for z in ZIELE:
                b = basis_sym[z][SYM[idx]].mean()
                w = ZH[z][idx].mean()
                null[z][zi, ai] = (w / b if z in ("auf5", "ab5", "auf10")
                                   and b > 0 else w - b)
    grenze = {}
    for z in ZIELE:
        mu, sd = null[z].mean(axis=0), np.maximum(null[z].std(axis=0, ddof=1), 1e-12)
        grenze[z] = (mu, sd, float(np.percentile(
            np.max(np.abs((null[z] - mu) / sd), axis=1), 90)))

    print("=" * 118)
    print("TEIL 1 - JE AUSWAHL: Lift gegen das EIGENE Asset (Raten) bzw. "
          "Differenz in Prozentpunkten (mfe, maevp), Lehrer-Fenster %d h" % H)
    print("  Grenzen (Bestes-von-%d, zweiseitig, z): %s"
          % (len(AUS), " · ".join("%s %.2f" % (z, grenze[z][2]) for z in ZIELE)))
    print("  * = jenseits der Grenze · Jahre/Weglass/Asset beziehen sich auf "
          "auf5 (Richtung) - fuer Risiko-Rollen noch NICHT geprueft")
    print()
    kopf = ("  %-16s %4s %9s %7s %6s | %8s %8s %7s %8s | %7s %7s | %5s %5s %5s | %7s | %s"
            % ("Merkmal", "Perz", "Schwelle", "Anker", "Tage%", "auf5",
               "ab5", "Spiegel", "auf10", "mfe", "maevp", "Jahre", "Wegl",
               "Asset", "Kontr.", "Rolle"))
    print(kopf)
    urteile = []
    for ai, (m, p, sw, maske, pool) in enumerate(AUS):
        k = int(maske.sum())
        werte, stern = {}, {}
        for z in ZIELE:
            mu, sd, g = grenze[z]
            werte[z] = lift(maske, z)
            stern[z] = abs((werte[z] - mu[ai]) / sd[ai]) > g
        spiegel = werte["auf5"] / werte["ab5"] if werte["ab5"] > 0 else np.nan
        # Stabilitaet fuer die Richtung (auf5-Lift > 1 ?)
        richtung = 1.0 if werte["auf5"] > 1 else -1.0
        jahre_ok, jahre_n = 0, 0
        for j in np.unique(JAHR[maske]):
            mj = maske & (JAHR == j)
            if basis_sym["auf5"][SYM[mj]].sum() < MIN_EREIGNISSE:
                continue
            jahre_n += 1
            jahre_ok += int(richtung * (lift(mj, "auf5") - 1.0) > 0)
        wegl_ok, wegl_n = 0, 0
        for j in np.unique(JAHR[maske]):
            mj = maske & (JAHR != j)
            if mj.sum() < 30:
                continue
            wegl_n += 1
            wegl_ok += int(richtung * (lift(mj, "auf5") - 1.0) > 0)
        diff = ZH["auf5"][maske] - basis_sym["auf5"][SYM[maske]]
        je = np.bincount(SYM[maske], weights=diff, minlength=nsym)
        je_n = np.bincount(SYM[maske], minlength=nsym)
        gueltig = je_n >= MIN_ASSET
        asset = (np.mean(richtung * je[gueltig] > 0) if gueltig.any()
                 else np.nan)
        kidx = ziehe_tag(maske)
        kontr = ZH["auf5"][maske].mean() / max(ZH["auf5"][kidx].mean(), 1e-12)
        stabil = (jahre_n >= 3 and jahre_ok >= jahre_n - 1 and
                  wegl_ok == wegl_n and asset >= 0.6)
        if stern["auf5"] and werte["auf5"] > 1 and spiegel >= SPIEGEL and stabil:
            rolle = "✔ RICHTUNG +"
        elif stern["ab5"] and werte["ab5"] > 1 and spiegel <= 1 / SPIEGEL:
            rolle = "⛔ SPERRE"
        elif stern["mfe"] and stern["maevp"] and werte["mfe"] > 0 and werte["maevp"] > 0:
            rolle = "↕ HOEHE (mehr Bewegung)"
        elif stern["maevp"] and werte["maevp"] < 0:
            rolle = "⬇ RISIKO kleiner"
        elif stern["maevp"] and werte["maevp"] > 0:
            rolle = "⬆ RISIKO groesser"
        else:
            rolle = "· neutral"
        if rolle.startswith("✔") and not stabil:
            rolle += " (instabil)"
        tage = 100.0 * len(np.unique(TAG[maske])) / len(ut)
        print("  %-16s %4s %9.4f %7d %5.1f%% | %7.2f%s %7.2f%s %7.2f %7.2f%s | %+6.2f%s %+6.2f%s | %2d/%-2d %2d/%-2d %4.0f%% | %6.2f | %s"
              % (m, "P%d" % p, sw, k, tage,
                 werte["auf5"], "*" if stern["auf5"] else " ",
                 werte["ab5"], "*" if stern["ab5"] else " ", spiegel,
                 werte["auf10"], "*" if stern["auf10"] else " ",
                 werte["mfe"], "*" if stern["mfe"] else " ",
                 werte["maevp"], "*" if stern["maevp"] else " ",
                 jahre_ok, jahre_n, wegl_ok, wegl_n,
                 100 * asset if np.isfinite(asset) else float("nan"),
                 kontr, rolle))
        urteile.append((ai, m, p, sw, rolle))
    print()
    print("  Grundrate des Marktes (%d h): auf5 %.4f · ab5 %.4f · auf10 %.4f "
          "· mfe %.2f %% · maevp %.2f %%"
          % (H, ZH["auf5"].mean(), ZH["ab5"].mean(), ZH["auf10"].mean(),
             ZH["mfe"].mean(), ZH["maevp"].mean()))
    print()

    # ══ TEIL 1b: Fenster-Kontrolle fuer die nicht neutralen ══════════
    print("=" * 118)
    print("TEIL 1b - FENSTER-KONTROLLE fuer alle nicht neutralen Auswahlen: "
          "auf5- und ab5-Lift bei 6 / 24 / 72 h")
    for ai, m, p, sw, rolle in urteile:
        if rolle.startswith("·"):
            continue
        maske = AUS[ai][3]
        teile = []
        for f in (6, 24, 72):
            zf = Z[f]
            bs = {z: (np.bincount(SYM, weights=zf[z], minlength=nsym) / anz)
                  for z in ("auf5", "ab5")}
            l5 = zf["auf5"][maske].mean() / max(bs["auf5"][SYM[maske]].mean(), 1e-12)
            a5 = zf["ab5"][maske].mean() / max(bs["ab5"][SYM[maske]].mean(), 1e-12)
            teile.append("H%-2d auf5 %5.2f ab5 %5.2f" % (f, l5, a5))
        print("  %-16s P%-3d %-26s %s" % (m, p, rolle, " | ".join(teile)))
    print()

    # ══ TEIL 2: BESTAETIGUNG ════════════════════════════════════════
    print("=" * 118)
    print("TEIL 2 - BESTAETIGUNG: Signal vor k Stunden UND Kurs seither "
          "gestiegen, Einstieg JETZT - gegen das Signal allein")
    # Index desselben Symbols k Stunden frueher (nur wenn lueckenlos)
    ordnung = np.lexsort((STD, SYM))
    for ai, m, p, sw, rolle in urteile:
        if not rolle.startswith("✔"):
            continue
        maske = AUS[ai][3]
        print("  %s P%d (%s)" % (m, p, rolle))
        print("     %-34s %8s %8s %8s %8s" % ("", "Anker", "auf5", "ab5",
                                             "Spiegel"))
        a5 = lift(maske, "auf5"); b5 = lift(maske, "ab5")
        print("     %-34s %8d %8.2f %8.2f %8.2f" % ("Signal jetzt", int(maske.sum()),
                                                  a5, b5, a5 / max(b5, 1e-12)))
        for k in BESTAETIGUNG_K:
            vorher = np.full(n, False)
            o = ordnung
            gleich = (SYM[o][k:] == SYM[o][:-k]) & (STD[o][k:] - STD[o][:-k] == k)
            spaeter, frueher = o[k:][gleich], o[:-k][gleich]
            best = np.full(n, False)
            best[spaeter] = maske[frueher] & (CC[spaeter] > CC[frueher])
            nur = np.full(n, False)
            nur[spaeter] = maske[frueher] & (CC[spaeter] <= CC[frueher])
            for name, mm in (("vor %dh, seither gestiegen" % k, best),
                             ("vor %dh, seither NICHT gestiegen" % k, nur)):
                if mm.sum() < 200:
                    print("     %-34s %8d  (zu duenn)" % (name, int(mm.sum())))
                    continue
                a5 = lift(mm, "auf5"); b5 = lift(mm, "ab5")
                print("     %-34s %8d %8.2f %8.2f %8.2f"
                      % (name, int(mm.sum()), a5, b5, a5 / max(b5, 1e-12)))
        print()

    # ══ TEIL 3: POSITIVKONTROLLE ════════════════════════════════════
    print("=" * 118)
    print("TEIL 3 - POSITIVKONTROLLE: symboltreue Zufallsauswahl, auf5 um d "
          "Prozentpunkte angehoben - findet die Grenze sie?")
    ai = 0
    maske, pool = AUS[ai][3], AUS[ai][4]
    mu, sd, g = grenze["auf5"]
    for d in (0.01, 0.02, 0.04, 0.08):
        gef = 0
        for _ in range(5):
            idx = ziehe_sym(maske, pool)
            x = ZH["auf5"][idx].copy()
            heben = (x == 0) & (rng.random(len(x)) < d / max(1 - x.mean(), 1e-12))
            x[heben] = 1.0
            wert = x.mean() / basis_sym["auf5"][SYM[idx]].mean()
            gef += int((wert - mu[ai]) / sd[ai] > g)
        print("  +%2d Prozentpunkte auf5 (Auswahlgroesse wie %s P%d, %d Anker): "
              "gefunden %d von 5" % (round(100 * d), AUS[ai][0], AUS[ai][1],
                                     int(maske.sum()), gef))
    print()
    print("  ⚠️ Gebuehren und Finanzierung sind nicht eingerechnet (Regel 2).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
