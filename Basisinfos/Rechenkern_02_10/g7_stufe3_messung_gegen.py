"""G7 STUFE 3 — MESSUNG B5 GEGENRECHNEN, zweiter Weg in reinem Python (csv, sqlite3, datetime) — ohne finales_llm, ohne
g7_stufe3_anlage, ohne numpy/pandas. Vorlage: gegen_b5.py vom 11.11. (gleiche Rechnung, dort gegen erfundene Urteile, 12 Größen
je Menge ohne Abweichung). Gesichert 13.11.2026.

Liest das Ergebnis der EINEN Messung aus der Tabelle `messung` und rechnet a und b unabhängig nach. Ablage nur lesend.

    python -X utf8 Basisinfos/Rechenkern_02_10/g7_stufe3_messung_gegen.py                 -> echte Ablage
    python -X utf8 Basisinfos/Rechenkern_02_10/g7_stufe3_messung_gegen.py <ablage.db>     -> Prüfstand (Wegwerf-Ablage)
"""
import csv
import datetime as dt
import json
import os
import sqlite3
import sys
from collections import defaultdict

PROJ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(PROJ)
DB = sys.argv[1] if len(sys.argv) > 1 else "data/_g7/finales_llm.db"
Z = {(r["symbol"], r["stunde"]): r for r in csv.DictReader(open("data/_g7/regel0/stufe3_zielgroesse_b.csv", encoding="utf-8"),
                                                          delimiter=";")}
M = [(r["symbol"], r["stunde"], r["teil"]) for r in csv.DictReader(open("Basisinfos/Rechenkern_02_10/g7_stufe3_menge_b.csv",
                                                                        encoding="utf-8"), delimiter=";")]
M = [m for m in M if m[:2] in Z and Z[m[:2]]["ertrag_s"] not in ("", "nan")]
c = sqlite3.connect("file:%s?mode=ro" % os.path.abspath(DB).replace("\\", "/"), uri=True)
zeilen = c.execute("SELECT am, prompt_sha, messung_sha, ergebnis FROM messung").fetchall()
print("Messungszeilen:", len(zeilen), "(Soll genau 1)")
am, psha, msha, erg = zeilen[0]
W = json.loads(erg)
print("am", am, "· prompt_sha", psha, "· messung_sha", msha, "· Ergebnis", W["ergebnis"], "· n", W["n"], "· unlesbar", W["unlesbar"])
U = {(s, t): b for s, t, b in c.execute("SELECT symbol, stunde, bedenken FROM urteil WHERE form_ok=1 AND phase IN ('3a','3b')")}
alle = {(s, t) for s, t in c.execute("SELECT symbol, stunde FROM urteil WHERE phase IN ('3a','3b')")}
print("Urteile 3a+3b", len(alle), "· Menge mit Zielgröße", len(M), "· gleich:", alle == {m[:2] for m in M})
print("unlesbar nachgezählt", len(alle) - len(U), "gegen", W["unlesbar"])


def perz(x, q):                               # lineare Interpolation (Typ 7, wie numpy.percentile)
    x = sorted(x)
    h = (len(x) - 1) * q / 100
    i = int(h)
    return x[i] + (h - i) * (x[min(i + 1, len(x) - 1)] - x[i])


def rechne(keys, nur_zaehlen=False):
    keys = sorted(keys, key=lambda k: (k[1], k[0]))
    tage = defaultdict(list)
    for k in keys:
        tage[k[1][:10]].append(k)
    T = sorted(tage)
    D_ = len(T)
    z = {k: float(Z[k]["ertrag_s"]) for k in keys}
    r24 = {k: float(Z[k]["ertrag24"]) for k in keys}
    u = {k: int(U[k] >= 1) for k in keys}

    def diff(lab, w):
        ja = [w[k] for k in keys if lab[k]]
        ne = [w[k] for k in keys if not lab[k]]
        return sum(ja) / len(ja) - sum(ne) / len(ne) if ja and ne else None

    bl = len({(dt.date.fromisoformat(t) - dt.date(2025, 12, 1)).days // 15 for t in T})
    if nur_zaehlen:                           # KEIN BEFUND: keine Statistik (bei Anteil 0/1 gibt es keine Differenz)
        return dict(n=len(keys), tage=D_, bloecke=bl, anteil=sum(u.values()) / len(u))
    s = diff(u, z)
    null = []
    for sh in range(1, D_):
        lab = {}
        for d, t in enumerate(T):
            q = tage[T[(d + sh) % D_]]
            for j, k in enumerate(tage[t]):
                lab[k] = u[q[j % len(q)]]
        v = diff(lab, z)
        if v is not None:
            null.append(v)
    bl = len({(dt.date.fromisoformat(t) - dt.date(2025, 12, 1)).days // 15 for t in T})
    return dict(n=len(keys), tage=D_, bloecke=bl, anteil=sum(u.values()) / len(u), stat=s, p=sum(x <= s for x in null) / len(null),
                p_oben=sum(x >= s for x in null) / len(null), band_unten=perz(null, 5), band_oben=perz(null, 95),
                null_mitte=sum(null) / len(null), roh24_diff=diff(u, r24), verschiebungen=len(null))


if W["ergebnis"] != "gemessen":
    print("kein Nachrechnen der Mengen:", W["ergebnis"])
    sys.exit(0)
for teil, keys in (("b", [m[:2] for m in M if m[:2] in U]), ("a", [m[:2] for m in M if m[2] == "a_gemailt" and m[:2] in U])):
    w = W[teil]
    if w["urteil"] == "KEIN BEFUND":
        print(teil, "KEIN BEFUND laut Messung:", w.get("grund"), "· n/Tage/Blöcke/Anteil nachgerechnet:",
              rechne(keys, nur_zaehlen=True))
        continue
    g = rechne(keys)
    ab = {k: (g[k], w[k]) for k in g if k in w and abs(g[k] - w[k]) > 1e-9}
    nicht = [k for k in g if k not in w]
    print(teil, "Größen verglichen:", len(g) - len(nicht), "· Abweichungen:", ab or "keine", "· fehlen in der Messung:", nicht or "keine",
          "· Urteil Messung:", w["urteil"])
