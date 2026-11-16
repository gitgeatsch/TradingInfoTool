"""G7 STUFE 3 — MESSUNG B5: AUSKUNFTSARME TAG und EINSTIEG gegenrechnen, reines Python (ohne numpy/pandas, ohne Modul und Anlage).
Ergänzt g7_stufe3_messung_gegen.py (12 Größen) um tag_stat, tag_traegt, einst_traegt. Gibt keine Bedenken-Werte aus. 15.11.2026.

    python -X utf8 Basisinfos/Rechenkern_02_10/g7_stufe3_messung_gegen_auskunft.py
"""
import csv, json, sqlite3, os
from collections import defaultdict
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
Z = {(r["symbol"], r["stunde"]): r for r in csv.DictReader(open("data/_g7/regel0/stufe3_zielgroesse_b.csv", encoding="utf-8"), delimiter=";")}
M = [(r["symbol"], r["stunde"], r["teil"]) for r in csv.DictReader(open("Basisinfos/Rechenkern_02_10/g7_stufe3_menge_b.csv", encoding="utf-8"), delimiter=";")]
M = [m for m in M if m[:2] in Z and Z[m[:2]]["ertrag_s"] not in ("", "nan")]
c = sqlite3.connect("file:data/_g7/finales_llm.db?mode=ro", uri=True)
U = {(s, t): b for s, t, b in c.execute("SELECT symbol, stunde, bedenken FROM urteil WHERE form_ok=1")}
W = json.loads(c.execute("SELECT ergebnis FROM messung").fetchone()[0])
def perz(x, q):
    x = sorted(x); h = (len(x)-1)*q/100; i = int(h); return x[i] + (h-i)*(x[min(i+1, len(x)-1)]-x[i])
def rang(v):
    o = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0]*len(v); i = 0
    while i < len(o):
        j = i
        while j+1 < len(o) and v[o[j+1]] == v[o[i]]: j += 1
        for k in range(i, j+1): r[o[k]] = (i+j)/2+1
        i = j+1
    return r
def norm(v):
    m = sum(v)/len(v); s = (sum((x-m)**2 for x in v)/len(v))**0.5 or 1; return [(x-m)/s for x in v]
def kreuz(a, b):
    n = len(a); return [sum(a[(i+k) % n]*b[i] for i in range(n)) for k in range(n)]
for teil, keys in (("b", [m[:2] for m in M]), ("a", [m[:2] for m in M if m[2] == "a_gemailt"])):
    keys = sorted(keys, key=lambda k: (k[1], k[0]))
    u = [float(U[k] >= 1) for k in keys]; z = [float(Z[k]["ertrag_s"]) for k in keys]
    # Arm TAG
    g = defaultdict(list)
    for k, ui, zi in zip(keys, u, z): g[k[1][:10]].append((ui, zi))
    T = sorted(g); A = [sum(x[0] for x in g[t])/len(g[t]) for t in T]; B = [sum(x[1] for x in g[t])/len(g[t]) for t in T]
    cc = [x/len(T) for x in kreuz(norm(rang(A)), norm(rang(B)))]
    st, nt = cc[0], cc[1:]
    # Arm EINSTIEG
    n, m = len(u), sum(u); ce = kreuz(u, z); sz = sum(z)
    se = [ce[k]/m - (sz-ce[k])/(n-m) for k in range(n)]
    w = W[teil]
    print(teil, "tag_stat nach", round(st, 12), "Messung", round(w["tag_stat"], 12), "· tag_traegt nach", st < perz(nt, 5), "Messung", w["tag_traegt"],
          "· einst_traegt nach", se[0] < perz(se[1:], 5), "Messung", w["einst_traegt"], "· stat Einstiegsarm = stat Tagesarm:", abs(se[0]-w["stat"]) < 1e-9)
