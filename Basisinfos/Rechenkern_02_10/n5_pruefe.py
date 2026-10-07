"""N5 - Pruefung des Laeufers VOR dem ersten echten Aufruf (Schritt7 §23.20). PLATZHALTER statt Gemini, Wegwerf-Ablagen, eine KOPIE
der N4-Ablage (die echte wird nur gelesen und am Ende per Pruefsumme verglichen).

    python Basisinfos/Rechenkern_02_10/n5_pruefe.py

  P1 dieselben Anker in derselben Reihenfolge wie N4 (pos, symbol, std fuer alle 1.000)
  P2 Eingabe 0.2: Lage zur Signalstunde vorhanden, KEIN Terminmarkt-Satz, anonym; vor dem Aufruf Reihenfolge des Betriebs; R_v vertauscht
  P3 Plan: K_a 50 x 1, ENTSCHEID_K, T mit Blicken 250/500/750, R_v 100 x 5 - kein K_b, kein R_w
  P4 Kontingent: N4 und N5 zusammen unter dem Deckel (N4 hat 400/300 verbraucht -> N5 darf 80/0)
  P5 Start: ohne beendetes N4 verweigert; mit --warte-auf-n4 startet er, sobald N4 'ende' hat
  P6 Fassung 0.2 in der Ablage (anderer Fingerabdruck als N4); N4-Fingerabdruck unveraendert
  P7 Riegel: Platzhalter nie in die echte N5-Ablage, N5 nie in die N4-Ablage
  P8 Ende zu Ende: Orakel -> H traegt, Ziel/M-3 erfuellt; Zufall -> H traegt nicht; Bericht und JSON entstehen
  P9 Standard-DB, Messbasen und die echte N4-Ablage unberuehrt
"""
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import time

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
LAEUFER = os.path.join(HIER, "n5_rueckspiel.py")
AUSW = os.path.join(HIER, "n5_auswertung.py")
N4_ECHT = os.path.join(PROJ, "data", "_n4", "n4_ablage.db")
GROSS = {"N4_DECKEL_2": "1000000", "N4_DECKEL_1": "1000000", "N4_TAG": "2099-01-01"}
ERG = []


def ok(name, b, det=""):
    ERG.append((name, bool(b)))
    print("%s  %s  %s" % ("OK  " if b else "FEHL", name, det), flush=True)


def inhalt(p):
    """Pruefsumme des INHALTS der N4-Ablage ohne herz/ereignis - die schreibt der laufende N4 selbst (Herzschlag, Warten)."""
    c = sqlite3.connect("file:%s?mode=ro" % p.replace("\\", "/"), uri=True)
    h = hashlib.sha256()
    for t in ("meta", "eingabe", "stimme", "kontingent", "entscheid"):
        for z in c.execute("SELECT * FROM %s ORDER BY 1, 2" % t):
            h.update(repr(z).encode("utf-8"))
    c.close()
    return h.hexdigest()


def lauf(ablage, n4, modus="zufall", env=None, extra=(), timeout=3600):
    e = {**os.environ, "PYTHONIOENCODING": "utf-8", **GROSS, **(env or {})}
    cmd = [sys.executable, LAEUFER, "lauf", "--ablage", ablage, "--n4-ablage", n4, "--platzhalter", modus, "--kein-warten", *extra]
    return subprocess.run(cmd, env=e, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)


def n4_kopie(d, ende=True, kontingent=None):
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "n4_kopie.db")
    q = sqlite3.connect("file:%s?mode=ro" % N4_ECHT.replace("\\", "/"), uri=True)
    c = sqlite3.connect(p)
    q.backup(c)                                            # konsistente Kopie, auch wenn der echte N4 gerade schreibt
    q.close()
    c.execute("DELETE FROM herz")
    if ende:
        c.execute("INSERT OR REPLACE INTO meta VALUES ('ende', 'Pruefung')")
    else:
        c.execute("DELETE FROM meta WHERE k='ende'")
    for s, n in (kontingent or {}).items():
        c.execute("INSERT OR REPLACE INTO kontingent VALUES (?,?,?,0)", (s, "2099-01-01", n))
    c.commit(); c.close()
    return p


def main():
    os.chdir(PROJ)
    vorher = {p: os.path.getmtime(p) for p in (os.path.join(PROJ, "data", f) for f in (
        "tradinginfotool.db", "stundenkurse.db", "stundenkurse_alle.db", "markpreis_historie.db", "markpreis_alle.db")) if os.path.exists(p)}
    n4_sha = inhalt(N4_ECHT)
    sys.path.insert(0, HIER)
    import n5_rueckspiel as N5
    import n4_rueckspiel as N
    import agent.regel0_llm as L
    with tempfile.TemporaryDirectory() as d:
        # P7
        r = subprocess.run([sys.executable, LAEUFER, "lauf", "--platzhalter", "zufall", "--kein-warten"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env={**os.environ, **GROSS})
        r2 = subprocess.run([sys.executable, LAEUFER, "lauf", "--ablage", N4_ECHT, "--platzhalter", "zufall", "--kein-warten"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace", env={**os.environ, **GROSS})
        ok("P7 Riegel: Platzhalter nie in die echte N5-Ablage, N5 nie in die N4-Ablage",
           "nie in die echte N5" in (r.stdout + r.stderr) and "nie in die N4" in (r2.stdout + r2.stderr) and not os.path.exists(N5.ABLAGE_N5))
        # P5
        n4_offen = n4_kopie(os.path.join(d), ende=False)
        a5 = os.path.join(d, "p5", "n5.db")
        r = lauf(a5, n4_offen, extra=("--max-aufrufe", "1"))
        ok("P5 ohne beendetes N4 verweigert", "noch nicht beendet" in (r.stdout + r.stderr) and not os.path.exists(a5), (r.stdout + r.stderr)[-160:])
        e = {**os.environ, "PYTHONIOENCODING": "utf-8", **GROSS, "N5_WARTE_S": "1"}
        pr = subprocess.Popen([sys.executable, LAEUFER, "lauf", "--ablage", a5, "--n4-ablage", n4_offen, "--platzhalter", "zufall", "--kein-warten",
                               "--warte-auf-n4", "--max-aufrufe", "3"], env=e, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                              encoding="utf-8", errors="replace")
        time.sleep(4)
        gewartet = pr.poll() is None and not os.path.exists(a5)
        c = sqlite3.connect(n4_offen); c.execute("INSERT INTO meta VALUES ('ende', 'Pruefung')"); c.commit(); c.close()
        aus = pr.communicate(timeout=1800)[0]
        c = sqlite3.connect(a5)
        n_st = c.execute("SELECT COUNT(*) FROM stimme").fetchone()[0]
        c.close()
        ok("P5 mit --warte-auf-n4: wartet, startet nach dem Ende von N4", gewartet and "N4 ist beendet" in aus and n_st == 3, "Stimmen %d" % n_st)
        # P1 / P2 / P6 auf der eingefrorenen Ablage aus P5
        c, c4 = sqlite3.connect(a5), sqlite3.connect("file:%s?mode=ro" % N4_ECHT.replace("\\", "/"), uri=True)
        e5 = c.execute("SELECT pos, symbol, std, eingabe FROM eingabe ORDER BY pos").fetchall()
        e4 = c4.execute("SELECT pos, symbol, std FROM eingabe ORDER BY pos").fetchall()
        ok("P1 dieselben 1.000 Anker in derselben Reihenfolge wie N4", [x[:3] for x in e5] == e4 and len(e4) == 1000, "%d / %d" % (len(e5), len(e4)))
        mit = [json.loads(x[3]) for x in e5 if x[3]]
        anteil = sum("lage_zur_signalstunde" in m for m in mit) / len(mit)
        termin = sum("Am Terminmarkt:" in json.dumps(m, ensure_ascii=False) for m in mit)   # nicht der Satz zum Markpreis am Terminmarkt
        ok("P2 Eingabe 0.2: Lage zur Signalstunde in %.1f %% der Anker, kein Terminmarkt-Satz" % (100 * anteil), anteil > 0.95 and termin == 0,
           "Terminmarkt %d" % termin)
        m0 = mit[0]
        t_ord, rv_ord = list(N5.variante5("T", m0, None)), list(N5.variante5("R_v", m0, None))
        ok("P2 vor dem Aufruf Reihenfolge des Betriebs; R_v Bloecke vertauscht; die eingefrorene Eingabe ist alphabetisch",
           t_ord == ["geplant", "lage_zur_signalstunde", "lage_des_werts"] and rv_ord == ["geplant", "lage_des_werts", "lage_zur_signalstunde"]
           and list(m0) == sorted(m0), "%s / %s / %s" % (t_ord, rv_ord, list(m0)))
        f5 = c.execute("SELECT v FROM meta WHERE k='fassung'").fetchone()[0]
        f4 = c4.execute("SELECT v FROM meta WHERE k='fassung'").fetchone()[0]
        soll5 = N.fassung(dict(L.lade(N5.KATALOG_N5), stimmen=N.STIMMEN))
        soll4 = N.fassung(dict(L.lade(os.path.join(PROJ, "Basisinfos", "regel0_llm_0_1e_n4.yaml")), stimmen=N.STIMMEN))
        ok("P6 Fassung 0.2 in der Ablage, anders als N4; N4-Fingerabdruck unveraendert", f5 == soll5 and f5 != f4 and soll4 == f4,
           "N5 %s · N4 %s / %s" % (f5, f4, soll4))
        p = N5.plan5(c)
        teile = {}
        for t, pos, k in p:
            teile.setdefault(t, []).append((pos, k))
        ok("P3 Plan: K_a 50x1, ENTSCHEID_K vor T, T 1000x5 mit Blicken 250/500/750, R_v 100x5, kein K_b/R_w",
           len(teile["K_a"]) == 50 and all(k == 1 for _, k in teile["K_a"]) and len(teile["T"]) == 1000 and len(teile["R_v"]) == 100
           and "K_b" not in teile and "R_w" not in teile and [x[0] for x in p].index("ENTSCHEID_K") == 50
           and all(("ENTSCHEID_T%d" % b) in teile for b in (250, 500, 750)), str({k: len(v) for k, v in teile.items()}))
        c.close(); c4.close()
        # P4
        n4_k = n4_kopie(os.path.join(d, "p4"), ende=True, kontingent={2: 400, 1: 300})
        a4 = os.path.join(d, "p4", "n5.db")
        r = lauf(a4, n4_k, env={"N4_DECKEL_2": "480", "N4_DECKEL_1": "300"})
        c = sqlite3.connect(a4)
        je = dict(c.execute("SELECT schluessel, COUNT(*) FROM stimme GROUP BY schluessel").fetchall())
        c.close()
        ok("P4 Kontingent N4 + N5 zusammen: N4 400/300 verbraucht -> N5 genau 80 auf Schluessel 2, 0 auf Schluessel 1", je == {2: 80}, str(je))
        # P8
        ber = {}
        for modus in ("orakel", "zufall"):
            n4_e = n4_kopie(os.path.join(d, modus), ende=True)
            a8 = os.path.join(d, modus, "n5.db")
            r = lauf(a8, n4_e, modus=modus)
            b = subprocess.run([sys.executable, AUSW, "--ablage", a8, "--n4-ablage", n4_e], capture_output=True, text=True, encoding="utf-8",
                               errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"}, timeout=3600)
            js = os.path.join(d, modus, "n5_bericht.json")
            ber[modus] = (json.load(open(js, encoding="utf-8")) if os.path.exists(js) else {}, b.stdout + b.stderr)
            open(os.path.join(HIER, "n5_pruefe_bericht_%s.txt" % modus), "w", encoding="utf-8").write(b.stdout + b.stderr)
        o, z = ber["orakel"][0], ber["zufall"][0]
        ok("P8 Orakel: H traegt, Ziel erreicht, M-3 erfuellt; Bericht und JSON entstehen",
           o.get("H_traegt") and o.get("ZIEL") and o.get("M3"), str({k: o.get(k) for k in ("H_traegt", "ZIEL", "M1", "M2", "M3", "n")}))
        ok("P8 Zufall: H traegt nicht, Ziel nicht erreicht", z and not z.get("H_traegt") and not z.get("ZIEL"),
           str({k: z.get(k) for k in ("H_traegt", "ZIEL", "M1", "M2", "M3", "n", "gestoppt")}))
    nachher = {p: os.path.getmtime(p) for p in vorher}
    ok("P9 Standard-DB, Messbasen und die echte N4-Ablage unberuehrt", nachher == vorher and inhalt(N4_ECHT) == n4_sha,
       "Aenderungen: %s" % [p for p in vorher if nachher[p] != vorher[p]])
    print("\n%d von %d bestanden" % (sum(b for _, b in ERG), len(ERG)))


if __name__ == "__main__":
    main()
