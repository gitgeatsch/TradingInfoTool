"""G7 STUFE 3b — GEGENPRÜFEN, Weg 2 OHNE das Modul: rohe Ablage (mode=ro), rohe CSV, eigener JSON-Leser, Anfragebuch.
Vorlage: Gegenprüfung 3a vom 11.11. (Scratchpad gegen_3a.py). Gesichert 13.11.2026.

⚠️ Gibt KEINE Bedenken-Werte aus, nur Abweichungszahlen.

    python -X utf8 Basisinfos/Rechenkern_02_10/g7_stufe3b_gegenpruefen.py
"""
import collections
import csv
import hashlib
import json
import os
import re
import sqlite3

PROJ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(PROJ)
RK = "Basisinfos/Rechenkern_02_10/"
START_3B = "2026-11-11T17:09"            # UTC, Start des ersten 3b-Laufs (PID 22796)

c = sqlite3.connect("file:data/_g7/finales_llm.db?mode=ro", uri=True)
R = c.execute("SELECT symbol, stunde, teil, eingabe, eingabe_sha, roh, bedenken, form_ok, felder FROM urteil WHERE phase='3b'").fetchall()
for f in ("g7_stufe3_menge_b.csv", "g7_stufe3_vorauswahl_d3.csv"):
    print(f, "Prüfsumme", hashlib.sha256(open(RK + f, "rb").read()).hexdigest()[:16], "(Soll 62a0641aeb643b46 / 314c47c3d8e06077)")
M = list(csv.DictReader(open(RK + "g7_stufe3_menge_b.csv", encoding="utf-8"), delimiter=";"))
# wie Messplan §11.5: nur Einstiege mit Zielgröße (2.435 -> 2.379); eigener Leser, nicht finales_llm.menge()
ZG = {(r["symbol"], r["stunde"]) for r in csv.DictReader(open("data/_g7/regel0/stufe3_zielgroesse_b.csv", encoding="utf-8"),
                                                          delimiter=";") if r["ertrag_s"] not in ("", "nan")}
print("Menge b roh", len(M), "· mit Zielgröße", sum((m["symbol"], m["stunde"]) in ZG for m in M), "(Soll 2.379)")
M = [m for m in M if (m["symbol"], m["stunde"]) in ZG]
V = {(v["symbol"], v["stunde"]) for v in csv.DictReader(open(RK + "g7_stufe3_vorauswahl_d3.csv", encoding="utf-8"), delimiter=";")}
soll = {(m["symbol"], m["stunde"]) for m in M} - V
ist = [(r[0], r[1]) for r in R]
print("Zeilen", len(R), "· eindeutig", len(set(ist)), "· Soll", len(soll), "· Mengengleich", soll == set(ist))
tsoll = {(m["symbol"], m["stunde"]): m["teil"] for m in M}
print("teil passt zur Mengendatei: weicht ab", sum(tsoll.get((r[0], r[1])) != r[2] for r in R))
print("Text-SHA weicht ab:", sum(hashlib.sha256(r[3].encode("utf-8")).hexdigest()[:16] != r[4] for r in R))
print("Signalzeitpunkt passt nicht zur Stunde:", sum(("Signalzeitpunkt: %s:00 UTC" % r[1][:13]) not in r[3] for r in R))


def lese(t):
    t = t.strip()
    m = re.match(r"^```(?:json)?\s*(.*?)\s*```$", t, re.S)
    return json.loads(m.group(1) if m else t)


pj = bed = fel = 0
L = [r for r in R if r[7] == 1]
for r in L:
    try:
        g = lese(r[5])
    except Exception:                                   # noqa: BLE001
        pj += 1
        continue
    bed += g.get("bedenken") != r[6]
    fel += json.loads(r[8]).get("bedenken") != r[6]
print("lesbar laut Spalte", len(L), "· davon Rohtext nicht als JSON lesbar:", pj, "· bedenken roh != Spalte:", bed,
      "· felder != Spalte:", fel, "· Spalte leer:", sum(r[6] is None for r in L))
print("Wertebereich der Bedenken-Spalte gültig (0..2):", all(isinstance(r[6], int) and 0 <= r[6] <= 2 for r in L))
A = [a for a in csv.DictReader(open("data/_g7/anfragen.csv", encoding="utf-8"), delimiter=";") if a["zeit_utc"] >= START_3B]
print("Anfragebuch seit Start 3b:", dict(collections.Counter(a["art"] for a in A)), "· PIDs", sorted({a["pid"] for a in A}),
      "· Schlüssel", sorted({a["schluessel"] for a in A}))
vs = c.execute("SELECT SUM(versuche) FROM urteil WHERE phase='3b'").fetchone()[0]
print("  200er seit Start 3b gegen Summe Versuche 3b (Soll gleich; eine Antwort ohne Form wird wiederholt, 13.11.: 1.128 = 1.128):",
      sum(a["art"] == "200" for a in A), "gegen", vs, "· Zeilen", len(R))
