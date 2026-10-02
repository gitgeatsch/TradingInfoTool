"""Gegenpruefung Monatsjob und Stundenlauf des REGEL0.1-Rechenkerns (S7-2/S7-3 Schritte 4 und 5, 02.10.2026) - nur lesend.

Wie im Betrieb: alle Assets (Messbasis + alle aus stundenkurse_alle.db ohne die gesperrten), Modelldateien nur aus den Daten
zum Monatsbeginn, Stundenlauf auf dem 460-Tage-Fenster mit dem ersten Anker aus der Modelldatei.

1  Monatsjob   Modelldateien 2026-03 und 2026-04 (Quartalsbeginn): rsi-Modelle gleich der Nachrechnung (z auf allen Ankern
               des Monats), ATR-Modelle gleich der Betriebsform aus B-10; Pruefsumme schuetzt die Datei (Gegenprobe)
2  Stundenlauf an Einstiegen der Referenz und an der Monats- und Quartalsgrenze: neue Signale = Referenz-Einstiege der
               Folgestunde, v-dach gleich, endgueltige Stufe gleich der Betriebsform (B-10)
3  Frische     ein aktives Asset ohne die juengste Stunde bekommt KEIN Signal und steht in der Liste veraltet
4  Laufzeit    des Stundenlaufs (Desktop)
"""
import os
import sys
import tempfile
import time

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, HIER)
os.chdir(HIER)
sys.stdout.reconfigure(encoding="utf-8")
import agent.regel0_rechnung as RK                                 # noqa: E402
import messe_k1_schritt2b_kombination as K2                        # noqa: E402

ergebnis = []


def pruef(name, ok, info=""):
    ergebnis.append(bool(ok))
    print("  %s %s%s" % ("✔" if ok else "⛔", name, (" - " + info) if info else ""), flush=True)


t0 = time.time()
ref = pd.read_csv("data/_vergleich/kern48jbz_einstiege_bestand.csv", sep=";")
zus_ref = RK.zusatz_aus_gruppe("data/_vergleich/kern48jbz_gruppe_bestand.csv")
zus = RK.betriebs_zusatz(RK.DATEN_VORGABE)
print("Betrieb bewertet zusaetzlich %d Assets (Referenz: %d) - %s" % (len(zus), len(zus_ref), ", ".join(zus_ref)), flush=True)

# Referenz: Nachrechnung (rsi-Modelle) und Stufen in Betriebsform (B-10)
reihen_ref = RK.lade_reihen(RK.DATEN_VORGABE, zus_ref)
Aref = RK.anker(reihen_ref, zukunft_bekannt=True)
Rref = RK.rechne(Aref, set(zus_ref), K2.ROLL_MONATE)
vh_ref = {(Rref["syms"][int(Rref["SYM"][i])], int(Rref["STD"][i])): Rref["VH"][i] for i in range(len(Rref["SYM"]))}
Xh = RK.hebel_anker(RK.DATEN_VORGABE, reihen_ref, set(zus_ref))
MB = RK.hebel_modelle(Xh, [(2026, 1)], bis_stunde=K2._h(pd.Timestamp(2026, 1, 1).to_pydatetime()))
MB.update(RK.hebel_modelle(Xh, [(2026, 4)], bis_stunde=K2._h(pd.Timestamp(2026, 4, 1).to_pydatetime())))
print("Referenz gerechnet in %.0f s" % (time.time() - t0), flush=True)

print("1) Monatsjob")
pakete, d = {}, tempfile.mkdtemp()
for (j, m) in ((2026, 3), (2026, 4)):
    t1 = time.time()
    pk = RK.trainiere_monat(RK.DATEN_VORGABE, j, m, zusatz=zus)
    pf = os.path.join(d, "regel0_modell_%04d-%02d.pkl" % (j, m))
    RK.speichere_paket(pk, pf)
    pakete[pk["monat"]] = RK.lade_paket(pf)
    mi = j * 12 + m - 1
    # Vergleich der Modelle ueber die Vorhersage auf denselben Merkmalen: Ch der Nachrechnung gegen Ch mit dem Paketmodell
    Rp = RK.rechne(Aref, set(zus_ref), [((mi - 1) // 12, (mi - 1) % 12 + 1), (j, m)], modelle=pakete[pk["monat"]]["rsi"])
    w = np.flatnonzero(np.isin(Rref["MON"], [mi - 1, mi]) & np.isfinite(Rref["Ch"]))
    dz = float(np.nanmax(np.abs(Rp["Ch"][w] - Rref["Ch"][w])))
    pruef("Paket %s: rsi-Modelle (Vormonat und Monat) gleich der Nachrechnung" % pk["monat"], dz <= 1e-9,
          "max |dBeitrag| %.1e ueber %d Anker · %d Assets mit erstem Anker · %.0f s" % (dz, len(w), pk["assets"], time.time() - t1))
    q = RK.quartal(mi)
    pa = {L: pk["atr"].get((q, L)) for L in (2, 3, 5)}
    probe = {"atr": np.linspace(0.005, 0.2, 200)}
    da_ = max((float(np.max(np.abs(pa[L].z(probe, np.arange(200), np.zeros(200)) - MB[(q, L)].z(probe, np.arange(200), np.zeros(200)))))
               if (pa[L] is not None and (q, L) in MB) else (0.0 if (pa[L] is None and (q, L) not in MB) else np.inf)) for L in (2, 3, 5))
    pruef("Paket %s: ATR-Modelle (Quartal %d-%02d) gleich der Betriebsform B-10" % (pk["monat"], q // 12, q % 12 + 1), da_ <= 1e-9,
          "max |dz| %.1e" % da_)
with open(pf, "r+b") as f_:
    f_.seek(100); b = f_.read(1); f_.seek(100); f_.write(bytes([b[0] ^ 1]))
try:
    RK.lade_paket(pf); geschuetzt = False
except SystemExit:
    geschuetzt = True
pruef("Gegenprobe: ein veraendertes Byte in der Modelldatei wird erkannt", geschuetzt)

print("2) Stundenlauf (Fenster 460 Tage, alle Assets)")
B0 = pd.Timestamp(2020, 1, 1)
h = lambda ts: int((pd.Timestamp(ts) - B0) / pd.Timedelta(hours=1))
kand = ref[(ref.stunde >= h("2026-03-02")) & (ref.stunde < h("2026-04-30"))].stunde.unique()
rng = np.random.default_rng(2)
zeiten = sorted(set(int(x) for x in rng.choice(kand, 4, replace=False)) | {h("2026-04-01 00:00"), h("2026-04-01 01:00"), h("2026-04-02 01:00")})
LBref = {}
a_ref = RK.atr_je_stunde(reihen_ref)
for s_, e_ in zip(ref.symbol, ref.stunde):
    if h("2026-03-01") <= e_ < h("2026-05-01"):
        mo_ = int(RK.monat_von(np.array([e_]))[0])
        _P, L_ = RK.hebelstufe(np.array([a_ref.get(s_, {}).get(int(e_), np.nan)]), np.array([mo_]), MB)
        LBref[(s_, int(e_))] = int(L_[0])
gl_neu = gl_end = 0; dv = 0.0; dauer = []
for T in zeiten:
    t1 = time.time()
    B = RK.bewerte(RK.DATEN_VORGABE, pakete, T, zusatz=zus)
    dauer.append(time.time() - t1)
    neu = sorted(x["symbol"] for x in B["neu"] if x["symbol"] in set(ref.symbol))
    soll = sorted(ref.symbol[ref.stunde == T])
    end = {(x["symbol"], h(x["einstieg"])): x["stufe"] for x in B["endgueltig"] if x["symbol"] in set(ref.symbol)}
    soll_end = {k: v for k, v in LBref.items() if k[1] == T - 1}
    R = B["R"]
    ix = np.flatnonzero(R["STD"] == T - 1)
    d_ = [abs(R["VH"][i] - vh_ref[(R["syms"][int(R["SYM"][i])], T - 1)]) for i in ix
          if (R["syms"][int(R["SYM"][i])], T - 1) in vh_ref and np.isfinite(R["VH"][i])]
    dv = max([dv] + d_)
    gl_neu += neu == soll; gl_end += end == soll_end
    print("    jetzt %s: neu %s (Referenz %s) · endgueltig %s (B-10 %s) · zusaetzlich %d · frisch %d/%d · %.0f s%s" % (
        B["frische"]["jetzt"], neu or "-", soll or "-", end or "-", soll_end or "-",
        sum(1 for x in B["neu"] if x["symbol"] not in set(ref.symbol)), B["frische"]["frisch"], B["frische"]["aktiv"], dauer[-1],
        "" if (neu == soll and end == soll_end) else "  ⛔"), flush=True)
pruef("neue Signale = Referenz-Einstiege an allen %d Zeitpunkten" % len(zeiten), gl_neu == len(zeiten), "%d von %d" % (gl_neu, len(zeiten)))
pruef("endgueltige Stufe = Betriebsform B-10 an allen Zeitpunkten", gl_end == len(zeiten), "%d von %d" % (gl_end, len(zeiten)))
pruef("v-dach zur juengsten Stunde gleich der Nachrechnung (Toleranz 1e-9)", dv <= 1e-9, "max %.1e" % dv)

print("3) Frische: einem Signal-Asset fehlt die juengste Stunde")
T = zeiten[0]
opfer = sorted(ref.symbol[ref.stunde == T])[0] if (ref.stunde == T).any() else "BTC"
orig = RK.lade_reihen


def ohne_letzte(ordner, zusatz, ab=None):
    aus = orig(ordner, zusatz, ab)
    grenze = RK._stunde_txt(T - 1)
    return [(s, [r for r in rows if not (s == opfer and r[0] >= grenze)]) for s, rows in aus]


RK.lade_reihen = ohne_letzte
try:
    Bf = RK.bewerte(RK.DATEN_VORGABE, pakete, T, zusatz=zus)
finally:
    RK.lade_reihen = orig
pruef("%s ohne die Stunde %s: kein Signal, steht unter veraltet" % (opfer, RK._stunde_txt(T - 1)),
      opfer not in [x["symbol"] for x in Bf["neu"]] and opfer in Bf["frische"]["veraltet"], str(Bf["frische"]["veraltet"][:5]))

print("4) Laufzeit Stundenlauf (Desktop): Median %.0f s, max %.0f s - am NB rund Faktor 3,5" % (np.median(dauer), max(dauer)))
print("SCHLUSS: %s (%d von %d) · %.0f s" % ("✔ bestanden" if all(ergebnis) else "⛔ NICHT bestanden", sum(ergebnis), len(ergebnis), time.time() - t0))
