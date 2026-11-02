"""G7 vor Stufe 3 (Voranalyse_G7 §9.1, §10): die REGEL0-Einstiege des Rückspiels aus der BETRIEBSRECHNUNG über die Betriebsmenge.

Nur lesend: Arbeitskopie ``data/_g7/kurse/`` (Desktop-Messbasis + NB-Auszug, §9.5), Desktop-Markpreis, NB-Kopien im Austauschordner.
Schreibt nur nach ``data/_g7/regel0/`` und ``g7_regel0_betrieb.txt``. Kein Netz, kein LLM, keine Produktions-DB.

  A  REPRODUKTION (R-R11): Referenz kern48jbz (Menge bestand, 127 Assets) auf der Arbeitskopie nachrechnen -> zeilengleich?
  B  BETRIEBSMENGE: dieselbe Rechnung mit den Zusatz-Assets des Betriebs (``betriebs_zusatz``: alle >= 500 h, ohne gesperrte),
     Monate bis 2026-10; Einstieg nur, wenn das Asset VOR der Stunde >= 500 Stunden hatte (Fenster-Bedingung des Stundenlaufs)
  C  ZWEITER WEG: Signalstunden des Rückspiels gegen die ECHTEN NB-Signale 03.10.-14.10. (regel0_kopie_T440) - gleiche Signale,
     gleiches v-dach?
  D  HEBELSTUFE je Einstieg (ATR-Modelle je Quartal wie der Monatsjob; Q4 2026 aus dem NB-Paket 2026-10)
  E  HEBEL-SCHALTER (Stand NB-Diagnose 01.11.) - die Menge, die live an das LLM geht (gemailt)
  F  Zahlen je Menge: Einstiege, Tage, Blöcke, A24/B24, Budget Stufe 3

    python g7_regel0_betrieb.py [--teil ABCDEF]
"""
import csv
import json
import os
import pickle
import sqlite3
import sys
import time
from datetime import datetime

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, PROJ)

import agent.regel0_rechnung as RK                                  # noqa: E402
import messe_k1_schritt2b_kombination as K2                         # noqa: E402
import messe_e2_beitraege as E2                                     # noqa: E402
from agent.regel0_stundenlauf import _binance_zu_bitpanda           # noqa: E402

KOPIE = os.path.join(PROJ, "data", "_g7", "kurse")
AUS = os.path.join(PROJ, "data", "_g7", "regel0")
REF = os.path.join(PROJ, "data", "_vergleich", "kern48jbz_einstiege_bestand.csv")
REF_GRUPPE = os.path.join(PROJ, "data", "_vergleich", "kern48jbz_gruppe_bestand.csv")
NB = r"K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten"
NB_SIGNALE = os.path.join(NB, "regel0_kopie_T440", "regel0_signale.db")
NB_PAKET = os.path.join(NB, "regel0_kopie_T440", "regel0_modelle", "regel0_modell_2026-10.pkl")
NB_DIAG = os.path.join(NB, "notebook_diagnose.json")
AB, BIS = "2025-12-01", "2026-10-31 23:00"
MONATE = list(K2.ROLL_MONATE) + [m for m in [(2026, 9), (2026, 10)] if m not in K2.ROLL_MONATE]
TXT = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    TXT.append(s)


def _txt(h):
    return RK._stunde_txt(int(h))


def _h(txt):
    return K2._h(datetime.strptime(txt, "%Y-%m-%d %H:%M"))


def stunden_vor(dateien):
    """{symbol: sortiertes Array der Stunden (int)} - für die Fenster-Bedingung (>= 500 Stunden vor T)."""
    aus = {}
    for f in dateien:
        c = RK._ro(os.path.join(KOPIE, f))
        for sym, st in c.execute("SELECT symbol, stunde FROM stundenkurse ORDER BY symbol, stunde"):
            aus.setdefault((f, sym), []).append(st)
        c.close()
    return {k: np.array([_h(x) for x in v], np.int64) for k, v in aus.items()}


def teil_a():
    p("\nA  REPRODUKTION der Referenz kern48jbz (bestand) auf der Arbeitskopie (R-R11)")
    zus = RK.zusatz_aus_gruppe(REF_GRUPPE)
    t0 = time.time()
    A = RK.anker(RK.lade_reihen_iter(KOPIE, zus), zukunft_bekannt=True)
    R = RK.rechne(A, set(zus), K2.ROLL_MONATE)
    ziel = os.path.join(AUS, "a_referenz_nachgerechnet.csv")
    RK.schreibe_einstiege(R, ziel)
    ref = set(open(REF, encoding="utf-8").read().splitlines()[1:])
    neu = set(open(ziel, encoding="utf-8").read().splitlines()[1:])
    p("   Zusatz %d · Referenz %d Zeilen · nachgerechnet %d · gemeinsam %d · nur Referenz %d · nur neu %d · %.0f s"
      % (len(zus), len(ref), len(neu), len(ref & neu), len(ref - neu), len(neu - ref), time.time() - t0))
    for z in sorted(ref - neu)[:5]:
        p("     nur Referenz:", z)
    for z in sorted(neu - ref)[:5]:
        p("     nur neu:     ", z)
    p("   => %s" % ("ZEILENGLEICH" if ref == neu else "⚠ NICHT zeilengleich"))
    return R


def teil_b():
    p("\nB  BETRIEBSMENGE: Zusatz = betriebs_zusatz(Arbeitskopie), Monate bis 2026-10")
    zus = RK.betriebs_zusatz(KOPIE)
    t0 = time.time()
    A = RK.anker(RK.lade_reihen_iter(KOPIE, zus), zukunft_bekannt=True)
    t1 = time.time()
    R = RK.rechne(A, set(zus), MONATE)
    t2 = time.time()
    syms = R["syms"]
    mb = {r[0] for r in RK._ro(os.path.join(KOPIE, "stundenkurse.db")).execute(
        "SELECT symbol FROM stundenkurse GROUP BY symbol HAVING COUNT(*) > 2000")}
    p("   Assets: Messbasis %d, Zusatz %d (davon nicht in der Messbasis %d) · Anker %d · Laden %.0f s · Rechnen %.0f s"
      % (len(mb), len(zus), len(set(zus) - mb), len(R["SYM"]), t1 - t0, t2 - t1))
    st = stunden_vor(("stundenkurse.db", "stundenkurse_alle.db"))

    def vorher(sym, h):
        f = "stundenkurse.db" if sym in mb else "stundenkurse_alle.db"
        a = st.get((f, sym))
        return 0 if a is None else int(np.searchsorted(a, h, "right"))      # Zeilen bis EINSCHLIESSLICH der Signalstunde (Fenster bis jetzt-1)

    def tabelle(ix, signal):
        z = []
        for i in ix:
            s = syms[int(R["SYM"][i])]
            h = int(R["STD"][i])
            z.append(dict(symbol=s, stunde=_txt(h), h=h, signalstunde=_txt(h - 1 if not signal else h), zusatz=int(s not in mb),
                          vh=float(R["VH"][i]), vorher=vorher(s, h if signal else h - 1),
                          t_u=float(R["t_u"][i]), t_d=float(R["t_d"][i])))
        return pd.DataFrame(z)
    lo, hi = _h(AB + " 00:00") - 1, _h(BIS)
    e = R["einstiege"][(R["STD"][R["einstiege"]] >= lo + 1) & (R["STD"][R["einstiege"]] <= hi)]
    E = tabelle(e, False)
    E["fenster_ok"] = E.vorher >= 500
    p("   Einstiege %s .. %s: %d · davon Fenster-Bedingung verletzt (< 500 h vor dem Signal): %d -> ausgeschlossen"
      % (AB, BIS[:10], len(E), int((~E.fenster_ok).sum())))
    p("   Messbasis-Assets mit < 2.001 h vor dem Signal (assets_am zählt sie nicht, der Betrieb schon): %d Einstiege"
      % int(((E.zusatz == 0) & (E.vorher < 2001)).sum()))
    E = E[E.fenster_ok].drop(columns="fenster_ok")
    sg = R["signale"][(R["STD"][R["signale"]] >= _h("2026-10-03 00:00")) & (R["STD"][R["signale"]] <= _h("2026-10-14 03:00"))]
    S = tabelle(sg, True)
    S = S[S.vorher >= 500]
    E.to_csv(os.path.join(AUS, "b_einstiege_betrieb.csv"), sep=";", index=False)
    return R, E, S, mb, zus


def teil_c(S):
    p("\nC  ZWEITER WEG: Signale des Rückspiels gegen die ECHTEN NB-Signale (Kopie 14.10., T440)")
    c = sqlite3.connect("file:%s?mode=ro" % NB_SIGNALE.replace("\\", "/"), uri=True)
    N = pd.read_sql("SELECT symbol, signalstunde, vh, zusatz, coalesce(stufe, stufe_vorlaeufig) stufe, hebel_schalter FROM signal", c)
    L = pd.read_sql("SELECT * FROM lauf", c)
    c.close()
    lo, hi = N.signalstunde.min(), N.signalstunde.max()
    S = S[(S.signalstunde >= lo) & (S.signalstunde <= hi)]
    m = N.merge(S, on=["symbol", "signalstunde"], how="outer", suffixes=("_nb", "_r"), indicator=True)
    beide = m[m._merge == "both"]
    p("   Zeitraum %s .. %s · NB %d Signale · Rückspiel %d · gemeinsam %d · nur NB %d · nur Rückspiel %d"
      % (lo, hi, len(N), len(S), len(beide), int((m._merge == "left_only").sum()), int((m._merge == "right_only").sum())))
    if len(beide):
        d = (beide.vh_nb - beide.vh_r).abs()
        p("   v-dach gemeinsam: |NB - Rückspiel| Median %.2e, max %.2e" % (d.median(), d.max()))
    laeufe = set(L.iloc[:, 0])
    for art, teil in (("nur NB", m[m._merge == "left_only"]), ("nur Rückspiel", m[m._merge == "right_only"])):
        if len(teil):
            ohne_lauf = sum(1 for x in teil.signalstunde if _txt(_h(x) + 1) not in laeufe)
            p("   %s: %d (davon Stunde ohne NB-Lauf %d) · Beispiele: %s" % (
                art, len(teil), ohne_lauf, ", ".join("%s %s" % (a, b) for a, b in teil[["symbol", "signalstunde"]].head(6).values)))
    return m


def teil_d(E, zus, mb):
    p("\nD  HEBELSTUFE je Einstieg (ATR-Modell je Quartal wie der Monatsjob; Q4 2026 aus dem NB-Paket)")
    modelle = {}
    for (j, mo) in [(2025, 10), (2026, 1), (2026, 4), (2026, 7)]:
        start = K2._h(datetime(j, mo, 1))
        X = RK.hebel_anker(os.path.join(PROJ, "data"), RK.lade_reihen_iter(KOPIE, [], bis=_txt(start - 1)), set(zus))
        modelle.update(RK.hebel_modelle(X, [(j, mo)], bis_stunde=start))
    pk = pickle.loads(open(NB_PAKET, "rb").read())
    modelle.update(pk["atr"])
    p("   Modelle (Quartal, Stufe): %s" % sorted("%d-%02d/%dx" % (k[0] // 12, k[0] % 12 + 1, k[1]) for k in modelle))
    atr = np.full(len(E), np.nan)
    con = {f: RK._ro(os.path.join(KOPIE, f)) for f in ("stundenkurse.db", "stundenkurse_alle.db")}
    for sym, g in E.groupby("symbol"):
        rows = con["stundenkurse.db" if sym in mb else "stundenkurse_alle.db"].execute(
            "SELECT stunde, high, low, close FROM stundenkurse WHERE symbol=? AND stunde >= '2025-10-01 00:00' ORDER BY stunde", (sym,)).fetchall()
        a = RK.atr_je_stunde([(sym, rows)], mindest=24).get(sym, {})
        atr[g.index.to_numpy()] = [a.get(int(h), np.nan) for h in g.h]      # ATR der EINSTIEGSstunde (wie 'endgueltig')
    for c_ in con.values():
        c_.close()
    mon = RK.monat_von(E.h.to_numpy())
    _P, Ls = RK.hebelstufe(atr, mon, modelle)
    E = E.assign(stufe=Ls)
    p("   Stufe je Einstieg: %s · ohne ATR %d" % (dict(pd.Series(Ls).value_counts().sort_index()), int(np.isnan(atr).sum())))
    return E


def teil_e(E):
    p("\nE  HEBEL-SCHALTER (NB-Diagnose 01.11.) - live geht nur 'Schalter an und Stufe > 0' an Mail und LLM")
    d = json.load(open(NB_DIAG, encoding="utf-8"))
    an = {str(x["symbol"]).upper() for x in d["hebel_pruefung_toggles"] if x["hebel_pruefung_erlaubt"]}
    zu_bp, _f = _binance_zu_bitpanda()
    bp = E.symbol.map(lambda s: zu_bp.get(s, s))
    E = E.assign(bitpanda=bp, schalter=bp.map(lambda x: bool(x) and str(x).upper() in an))
    p("   Schalter an: %d Bitpanda-Symbole · Einstiege mit Schalter an %d von %d (%.1f %%) · davon Stufe > 0: %d"
      % (len(an), int(E.schalter.sum()), len(E), 100 * E.schalter.mean(), int((E.schalter & (E.stufe > 0)).sum())))
    return E


def teil_f(E, ref_syms):
    p("\nF  ZAHLEN JE MENGE (%s .. %s) - Zielgröße wie die REGEL0-Messung: A24 = +5 %% vor -5 %% binnen 24 h, B24 umgekehrt" % (AB, BIS[:10]))
    E = E.assign(tag=E.stunde.str[:10], a24=((E.t_u <= 24) & (E.t_u < E.t_d)), b24=((E.t_d <= 24) & (E.t_d <= E.t_u)))
    tage_ges = pd.date_range(AB, BIS[:10]).size
    mengen = [("alle (Betriebsmenge)", E), ("Referenz-Menge (127)", E[E.symbol.isin(ref_syms)]),
              ("nur Zusatz-Assets", E[E.zusatz == 1]), ("Stufe > 0", E[E.stufe > 0]),
              ("Schalter an + Stufe > 0 (= live gemailt)", E[E.schalter & (E.stufe > 0)])]
    p("   %-42s %7s %6s %10s %8s %7s %7s %12s" % ("Menge", "Einst.", "Tage", "je Tag Md", "max", "A24", "B24", "Gemini-Tage"))
    for name, g in mengen:
        jt = g.groupby("tag").size()
        p("   %-42s %7d %6d %10.0f %8d %6.1f%% %6.1f%% %12.1f" % (
            name, len(g), len(jt), jt.median() if len(jt) else 0, jt.max() if len(jt) else 0,
            100 * g.a24.mean() if len(g) else 0, 100 * g.b24.mean() if len(g) else 0, len(g) / 500.0))
    p("   Blöcke (messnorm, H = 24 h -> Block 15 T): %d Kalendertage = %d Blöcke" % (tage_ges, tage_ges // 15))
    E.to_csv(os.path.join(AUS, "f_einstiege_betrieb_mit_stufe_schalter.csv"), sep=";", index=False)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    teile = sys.argv[sys.argv.index("--teil") + 1] if "--teil" in sys.argv else "ABCDEF"
    os.makedirs(AUS, exist_ok=True)
    p("G7 REGEL0-Einstiege aus der Betriebsrechnung · %s · Arbeitskopie %s" % (datetime.now().strftime("%Y-%m-%d %H:%M"), KOPIE))
    if "A" in teile:
        teil_a()
    if set(teile) & set("BCDEF"):
        _R, E, S, _mb, zus = teil_b()
        if "C" in teile:
            teil_c(S)
        if set(teile) & set("DEF"):
            E = E.reset_index(drop=True)
            E = teil_d(E, zus, _mb)
            E = teil_e(E)
            ref_syms = set(pd.read_csv(REF, sep=";").symbol)
            teil_f(E, ref_syms)
    with open(os.path.join(HIER, "g7_regel0_betrieb%s.txt" % ("" if teile == "ABCDEF" else "_" + teile)), "w", encoding="utf-8") as f_:
        f_.write("\n".join(TXT) + "\n")


if __name__ == "__main__":
    main()
