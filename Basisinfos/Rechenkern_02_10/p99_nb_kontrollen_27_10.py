"""P99 NB-KONTROLLEN des Buendels 27.10.2026 aus dem NB-Export (notebook_diagnose.json im Austauschordner, nur gelesen).

    python -X utf8 Basisinfos/Rechenkern_02_10/p99_nb_kontrollen_27_10.py

K-GM-1 Lagebild Gesamtmarkt · K-DVOL-1 L7 DVOL · K-B4-D1 B4-Fuenftel aller Bestaende · K-K4-1 Kernwerte (Kette angehalten, keine
Importfehler) · K-SP-6 Season-Ampel mit Mail-Schalter · K-R0-ST0 Reihenbeginn (Abgleich ueber p97 --nb). Dazu Git-Stand (welche
Commits sind am NB) und Jobfehler. Jede Kontrolle: erfuellt / NICHT erfuellt / nicht pruefbar (mit Grund).
"""
import json
import os
import subprocess
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(os.path.dirname(HIER))
os.chdir(WURZEL)
sys.stdout.reconfigure(encoding="utf-8")
DIAG = os.path.join("K:" + os.sep, "My Drive", "Claude_Austauschordner", "Notebook_Analysedaten", "notebook_diagnose.json")
COMMITS = {"Lagebild+HY (E-137)": "13ea2839", "K-4 (E-152)": "a7b0000a", "W-1 (E-159)": "cc5d22b2", "L7 DVOL (E-161)": "c581be8d"}


def enthalten(c, head):
    r = subprocess.run(["git", "merge-base", "--is-ancestor", c, head], capture_output=True)
    return r.returncode == 0 if r.returncode in (0, 1) else None


def main():
    d = json.load(open(DIAG, encoding="utf-8"))
    st = os.path.getmtime(DIAG)
    g = d.get("git_stand") or {}
    head = g.get("head", "")
    print("NB-Export %s · NB-Stand %s (%s) · lokale Aenderungen %s" % (
        __import__("datetime").datetime.fromtimestamp(st).strftime("%d.%m. %H:%M"), head[:8], g.get("zweig"), g.get("geaendert") or "keine"))
    for name, c in COMMITS.items():
        e = enthalten(c, head) if head else None
        print("  %-20s %s" % (name, "am NB" if e else ("FEHLT am NB" if e is False else "unbekannt (Commit lokal nicht auffindbar)")))
    log = "\n".join(str(x) for x in (d.get("log_auszug") or []))
    erg = {}
    # K-GM-1 / K-DVOL-1
    m = d.get("makro_lage") or {}
    gm = m.get("gesamtmarkt") or {}
    zeilen = gm.get("zeilen") or []
    erg["K-GM-1"] = (gm.get("zustand") == "ok" and len(zeilen) >= 6 and not gm.get("fehler"),
                     "Zustand %s · %d Zeilen · Stand %s · Fehler %s · Log 'Lagebild Gesamtmarkt' %s" % (
                         gm.get("zustand"), len(zeilen), gm.get("stand"), gm.get("fehler"), "Lagebild Gesamtmarkt" in log))
    l7 = [z for z in zeilen if z and z[0] == "L7"]
    erg["K-DVOL-1"] = (bool(l7) and "BTC-DVOL" in l7[0][2] and "DVOL nicht abrufbar" not in log and (gm.get("datenstand") or {}).get("DVOL"),
                       ("L7: %s · Datenstand %s · Log-Fehler %s" % (l7[0][2][:120], (gm.get("datenstand") or {}).get("DVOL"),
                                                                     "DVOL nicht abrufbar" in log)) if l7 else "keine Zeile L7")
    # K-B4-D1
    b4 = d.get("spot_b4_fuenftel")
    if not isinstance(b4, dict):
        erg["K-B4-D1"] = (None, "Abschnitt fehlt (Pull noch nicht am NB?)")
    else:
        jb = b4.get("je_bestand") or {}
        aus = [s for s in ("HYPE", "KAS", "SUPRA", "XDC") if s in jb]
        ob = b4.get("oberes_fuenftel") or {}
        erg["K-B4-D1"] = (not b4.get("fehler") and len(jb) > 0 and bool(b4.get("universum_stichtag")) and all(ob.get(k) for k in ("H", "M", "S")),
                          "%d Bestaende · ausserhalb Binance dabei %s · Stichtag %s · oberes Fuenftel H/M/S %s · Fehler %s" % (
                              len(jb), aus, b4.get("universum_stichtag"), [len(ob.get(k) or []) for k in ("H", "M", "S")], b4.get("fehler")))
    # K-K4-1
    angehalten = "Rollen-Kette ANGEHALTEN" in log
    importfehler = [z for z in log.splitlines() if "kernwerte" in z.lower() or ("ImportError" in z) or ("ModuleNotFoundError" in z)]
    jf = d.get("job_fehlschlaege")
    k4_da = bool(head) and enthalten(COMMITS["K-4 (E-152)"], head)
    erg["K-K4-1"] = ((angehalten and not importfehler) if k4_da else None,
                     "K-4 am NB %s · Log 'Rollen-Kette ANGEHALTEN' %s · Import-/Kernwerte-Fehler %d%s · Jobfehler %s" % (
                         k4_da, angehalten, len(importfehler), (": " + importfehler[0][:120]) if importfehler else "",
                         (json.dumps(jf, ensure_ascii=False)[:200]) if jf else "keine"))
    # K-SP-6
    sa = d.get("season_ampel") or {}
    zeilen_sa = [z for z in log.splitlines() if "Season-Ampel:" in z]
    erg["K-SP-6"] = (bool(zeilen_sa) and "Schalter aus" not in zeilen_sa[-1],             # die LETZTE Zeile zaehlt
                     "letzte Logzeile: %s · Zeile Diagnose: %s · schalter_mail %s" % (
                         (zeilen_sa[-1][:160] if zeilen_sa else "keine"), str(sa.get("zeile"))[:100], sa.get("schalter_mail")))
    # K-R0-ST0
    rb = d.get("regel0_reihenbeginn")
    if not isinstance(rb, dict):
        erg["K-R0-ST0"] = (None, "Abschnitt fehlt (W-1 noch nicht am NB)")
    else:
        r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(HIER, "p97_w1_reihenbeginn_abgleich.py"), "--nb"],
                           capture_output=True, text=True, encoding="utf-8")
        erg["K-R0-ST0"] = ("GLEICH" in r.stdout, r.stdout.strip().replace("\n", " | ")[:400])
    print()
    for k, (ok, txt) in erg.items():
        print("%-9s %-14s %s" % (k, "erfuellt" if ok else ("NICHT erfuellt" if ok is False else "nicht pruefbar"), txt))
    auff = d.get("auffaelligkeiten")
    print("\nAuffaelligkeiten der Diagnose: %s" % (json.dumps(auff, ensure_ascii=False)[:600] if auff else "keine"))


if __name__ == "__main__":
    main()
