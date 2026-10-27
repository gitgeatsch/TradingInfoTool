"""W-3 S-1 (27.10.2026, E-164) am SEITENEFFEKT: die alte Spot-Kette ist fest stillgelegt - auch bei unlesbarer regel0_betrieb.yaml
oder fehlendem `rollen_kette.aktiv_fuer`; H15 laeuft weiter; der Terminmarkt-Waechter laeuft vor jeder Verzweigung; umkehrbar.

    python -X utf8 Basisinfos/Rechenkern_02_10/pruefe_w3_s1.py

Ersetzt werden nur Modulwerte in DIESEM Prozess: kein Netz, keine Datei, keine Mail, keine Produktion.
"""
import os
import sqlite3
import sys

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.getcwd())
sys.stdout.reconfigure(encoding="utf-8")
import config as CFG  # noqa: E402
import scheduler.background as BG  # noqa: E402
import scheduler.rollen_job as RJ  # noqa: E402
import agent.regel0_groesse as R0G  # noqa: E402
import agent.krypto.budget_allocator as BA  # noqa: E402
import agent.assetklassen as AK  # noqa: E402
import agent.hebelfuehrung as HF  # noqa: E402
import agent.betriebslage as BL  # noqa: E402

z = {"umlauf": 0, "allocator": 0, "waechter": 0, "fehler": []}
CFG.load_config = lambda *a, **k: {"hebel_screening": {"aktiv": False}, "watchlist": []}
CFG.get_watchlist = lambda *a, **k: []
AK.laeufe = lambda *a, **k: [("krypto", None, None)]
RJ.betriebsart_aus_config = lambda c: "test"
RJ.fuehre_umlauf = lambda **k: z.__setitem__("umlauf", z["umlauf"] + 1)
BA.run_budget_allocator = lambda *a, **k: z.__setitem__("allocator", z["allocator"] + 1)
BG._pruefe_terminmarkt_frische = lambda *a, **k: z.__setitem__("waechter", z["waechter"] + 1)
BG._notify_job_failure = lambda *a, **k: z["fehler"].append(a)
_echt_bedient = RJ.bedient_neue_kette


def lauf(stillgelegt, bedient, angehalten):
    z.update(umlauf=0, allocator=0, waechter=0, fehler=[])
    RJ.ALTE_KETTE_STILLGELEGT = stillgelegt
    RJ.bedient_neue_kette = lambda g, c: bedient
    if angehalten == "kaputt":                                  # unlesbare Datei: die Funktion faellt auf ihre Vorgabe False
        R0G.spot_kette_angehalten = lambda: False
    else:
        R0G.spot_kette_angehalten = lambda an=angehalten: an
    rv = BG.hebel_screening_job(None, None, lambda: None, lambda: [], gemini_client=object())
    return rv, z["umlauf"], z["allocator"], z["waechter"], len(z["fehler"]), BG.hebel_screening_lock.locked()


ERG = []


def pruefe(name, ok, detail):
    ERG.append(ok)
    print("%-4s %-9s %s" % (name, "bestanden" if ok else "FEHLER", detail))


# T1-T4 Umlauf / Allocator / Waechter
for name, args, soll, text in (
        ("T1", (True, True, "kaputt"), (True, 0, 0, 1), "stillgelegt · yaml kaputt (Halt faellt auf False) -> kein Umlauf"),
        ("T2", (True, False, False), (True, 0, 0, 1), "stillgelegt · aktiv_fuer leer (alter Weg waere frei) -> kein Allocator"),
        ("T3", (False, True, False), (True, 1, 0, 1), "UMKEHRBAR: Konstante False, Halt aus -> Umlauf laeuft wie vor S-1, Waechter genau 1x"),
        ("T4", (False, True, True), (True, 0, 0, 1), "Konstante False, Halt an -> wie R-4: kein Umlauf, Waechter 1x")):
    e = lauf(*args)
    pruefe(name, e[:4] == soll and e[4] == 0 and not e[5], "%s · Rueckgabe/Umlauf/Allocator/Waechter %s · Fehler %d · Sperre frei %s" % (
        text, e[:4], e[4], not e[5]))
RJ.ALTE_KETTE_STILLGELEGT = True
RJ.bedient_neue_kette = _echt_bedient

# T5 Multi-Asset-Batch (und damit sein Nachholen) bei leerem aktiv_fuer
import agent.multi_asset_batch as MAB  # noqa: E402
_batch = {"n": 0}
for _fn in [n for n in dir(MAB) if n.startswith("run")]:
    setattr(MAB, _fn, lambda *a, **k: _batch.__setitem__("n", _batch["n"] + 1))
rv5 = BG.multi_asset_batch_job(None, lambda: [], None, gemini_client=object())
pruefe("T5", rv5 is True and _batch["n"] == 0 and not BG.multi_asset_batch_lock.locked(),
       "Multi-Asset-Batch bei leerem aktiv_fuer (CFG ohne Schluessel): Rueckgabe %s · Batch-Laeufe %d" % (rv5, _batch["n"]))

# T6 H15 bei unlesbarer regel0_betrieb.yaml
_lade_echt = R0G.lade
R0G.lade = lambda *a, **k: (_ for _ in ()).throw(ValueError("regel0_betrieb.yaml: unbekannte Schluessel ['kaputt']"))
HF.lade = lambda conn, nahe_grenze=None: z.__setitem__("h15_grenze", nahe_grenze) or []
HF.laut_bitpanda_geschlossen = lambda conn: []
HF.neue_meldungen = lambda conn, trades: []
HF.sammel_mail = lambda *a, **k: None
a6 = BG._hebelfuehrung_lauf(lambda: sqlite3.connect(":memory:"), versand=lambda b, t: True)
pruefe("T6", a6.get("grund") != "Schalter aus" and not a6.get("fehler") and z.get("h15_grenze") == R0G.VORGABE["liquidations_warnung_abstand"],
       "H15 bei kaputter yaml: %s · Warnschwelle aus der Vorgabe %s" % ({k: a6[k] for k in list(a6)[:4]}, z.get("h15_grenze")))

# T7 GUI-Sperre und Hinweis - auch ohne aktiv_fuer und bei kaputter Datei
R0G.spot_kette_angehalten = lambda: (_ for _ in ()).throw(RuntimeError("kaputt"))
h1, h2 = RJ.alte_analyse_hinweis("krypto", {}), RJ.kette_angehalten_hinweis()
pruefe("T7", bool(h1) and "stillgelegt" in h1 and "stillgelegt" in h2,
       "Knopf-Sperre ohne aktiv_fuer: %s · Hinweis: %s" % ((h1 or "FREI")[:60], h2[:60]))

# T8 Statusseite: die Stilllegung steht als Schalter, auch wenn sie im Code steht
R0G.lade = _lade_echt
sch = BL.schalter()
pruefe("T8", sch.get("alte_kette_stillgelegt") is True and list(sch)[0] == "alte_kette_stillgelegt",
       "Schalter-Karte: erste Zeile %s = %s" % (list(sch)[0], sch.get("alte_kette_stillgelegt")))
print("\nW-3 S-1 am Seiteneffekt: %d von %d bestanden" % (sum(ERG), len(ERG)))
