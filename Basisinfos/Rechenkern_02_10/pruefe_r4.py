"""R-4 am SEITENEFFEKT: hebel_screening_job mit Platzhaltern - startet der Umlauf, startet der alte Weg?"""
import os
import sys
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))   # Projektwurzel, auf jedem Geraet
# Ersetzt werden nur Modulwerte in DIESEM Prozess: kein Netz, keine Datei, keine Mail (_notify_job_failure ist ersetzt)
sys.path.insert(0, os.getcwd())
import config as CFG
import scheduler.background as BG
import scheduler.rollen_job as RJ
import agent.regel0_groesse as R0G
import agent.krypto.budget_allocator as BA

aufrufe = {"umlauf": 0, "allocator": 0, "fehler": []}
CFG.load_config = lambda *a, **k: {"hebel_screening": {"aktiv": False}, "watchlist": []}
CFG.get_watchlist = lambda *a, **k: []
RJ.bedient_neue_kette = lambda g, c: True
import agent.assetklassen as AK
AK.laeufe = lambda *a, **k: [("krypto", None, None)]
RJ.betriebsart_aus_config = lambda c: "test"
RJ.fuehre_umlauf = lambda **k: aufrufe.__setitem__("umlauf", aufrufe["umlauf"] + 1)
BA.run_budget_allocator = lambda *a, **k: aufrufe.__setitem__("allocator", aufrufe["allocator"] + 1)
BG._pruefe_terminmarkt_frische = lambda *a, **k: None
BG._notify_job_failure = lambda *a, **k: aufrufe["fehler"].append(a)

erg = {}
for an in (True, False):
    aufrufe.update(umlauf=0, allocator=0, fehler=[])
    R0G.spot_kette_angehalten = lambda an=an: an
    rv = BG.hebel_screening_job(None, None, lambda: None, lambda: [], gemini_client=object())
    erg[an] = (rv, aufrufe["umlauf"], aufrufe["allocator"], list(aufrufe["fehler"]), BG.hebel_screening_lock.locked())
    print("Schalter %-5s -> Rueckgabe %s, Umlauf %d, alter Weg %d, Fehler %s, Sperre gehalten %s" % ((an,) + erg[an]))
ok = (erg[True][:3] == (True, 0, 0) and erg[False][:3] == (True, 1, 0)
      and not erg[True][3] and not erg[False][3] and not erg[True][4] and not erg[False][4])
print("R-4 am Seiteneffekt:", "BESTANDEN" if ok else "NICHT BESTANDEN")
