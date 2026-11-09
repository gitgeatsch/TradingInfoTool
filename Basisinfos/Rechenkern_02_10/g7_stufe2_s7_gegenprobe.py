"""G7 STUFE 2 S7 — Zählung OHNE Kurse und zweiter Weg zur Messung (Voranalyse_G7_Stufe1_04_11.md §4.1; Nutzer 09.11.2026: *„Ja, S7 messen“*).

    python -X utf8 Basisinfos/Rechenkern_02_10/g7_stufe2_s7_gegenprobe.py   -> g7_stufe2_s7_gegenprobe.txt

Die Messung selbst ist das VORAB gebaute ``g7_s7_anlage.py --messen`` (-> g7_s7_messung.txt). Hier nur:
  1  ZÄHLEN ohne Kurse (Zellentabelle nur Spalten tag/asset): Urteile je Seite, Blöcke über Positionen und Kalendertage
  2  ZWEITER WEG: Urteile direkt aus dem JSON (statt urteile()), Rang per naiver np.roll-Schleife über alle 334 Verschiebungen
     (statt FFT), Zielgröße aus der Spalte ertrag_s der Zellentabelle (statt panel())
⚠️ Nur lesend (gutachten.db, Kurs-Arbeitskopie mode=ro). Schreibt nur die .txt hier.
"""
import io, contextlib
_PUFFER = io.StringIO()
def _teil1():
    import json, os, sqlite3, sys
    import numpy as np, pandas as pd
    PROJ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, PROJ); sys.path.insert(0, os.path.join(PROJ, "Basisinfos", "Rechenkern_02_10"))
    import g7_s7_anlage as A
    C = pd.read_csv(A.ZELLEN, sep=";", usecols=["tag", "asset"])
    assets = sorted(C.asset.unique()); ai = {a: i for i, a in enumerate(assets)}
    ti = {t.strftime("%Y-%m-%d"): j for j, t in enumerate(A.TAGE)}
    E = np.zeros((len(assets), len(A.TAGE)), dtype=bool)
    for r in C.itertuples(): E[ai[r.asset], ti[r.tag]] = True
    print("Ereigniszellen", int(E.sum()), "Assets", len(assets), "Tage mit Zellen", int(E.any(0).sum()))
    U = {}
    for s in ("S7", "S7w"):
        U[s] = A.urteile(s, ai, ti, E)
        u = U[s]; tage = np.flatnonzero((u != 0).any(0))
        print(s, A.URTEIL_ZAEHLUNG[s], "| stuetzt", int((u == 1).sum()), "belastet", int((u == -1).sum()),
              "| Tage mit Urteil", len(tage), "| Bloecke (Pos.)", len(set(tage // A.BLOCK)),
              "| Bloecke je Seite st/bel", len(set(np.flatnonzero((u == 1).any(0)) // 15)), len(set(np.flatnonzero((u == -1).any(0)) // 15)),
              "| Assets mit Urteil", int((u != 0).any(1).sum()))
        # zweiter Weg Bloecke: Kalendertage
        d = (A.TAGE[tage] - A.TAGE[0]).days
        print("   Bloecke (Kalender, zweiter Weg)", len(set(np.asarray(d) // 15)))
    a, b = U["S7"], U["S7w"]
    m = (a != 0) | (b != 0)
    print("Uebereinstimmung S7/S7w auf Zellen mit Urteil in einem der beiden:", int(m.sum()), "gleich", int((a[m] == b[m]).sum()),
          "| Gegenrichtung", int(((a * b) == -1).sum()))
    kern = [ai[k] for k in A.KERN if k in ai]
    print("Kern-Urteile S7", int((a[kern] != 0).sum()), "S7w", int((b[kern] != 0).sum()))

def _teil2():
    import json, os, sqlite3, sys
    import numpy as np, pandas as pd
    PROJ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, PROJ); sys.path.insert(0, os.path.join(PROJ, "Basisinfos", "Rechenkern_02_10"))
    import g7_s7_anlage as A
    Z, E, assets, ai, ti, M = A.panel(H=(3,))
    Z3 = Z[3]
    # (c) Urteile direkt
    c = sqlite3.connect("file:%s?mode=ro" % os.path.join(PROJ, "data", "_g7", "gutachten.db").replace("\\", "/"), uri=True)
    def roh(s):
        U = np.zeros(E.shape)
        for tag, f in c.execute("SELECT tag, felder FROM gutachten WHERE sicht=? AND wdh=0 AND form_ok=1", (s,)):
            for e in json.loads(f).get("assets") or []:
                w = {"stützt": 1, "stuetzt": 1, "belastet": -1}.get(str(e.get("wirkung") or "").strip().lower(), 0)
                a = str(e.get("asset") or "").strip().upper()
                if a in ai and E[ai[a], ti[tag]]:
                    U[ai[a], ti[tag]] += w
        return np.sign(U).astype(int)
    for s in ("S7", "S7w"):
        U = roh(s); U2 = A.urteile(s, ai, ti, E)
        print(s, "Urteile direkt = urteile():", bool((U == U2).all()))
        # (b) naive Bahn
        naiv = np.array([A.t_naiv(np.roll(U, k, axis=1), Z3) for k in range(E.shape[1])])
        n = naiv[1:][np.isfinite(naiv[1:])]
        print("   naiv: t %+.4f  Rang %.4f  p %.4f  P96,5 %+.3f" % (naiv[0], (n < naiv[0]).mean(), 1 - (n < naiv[0]).mean(), np.percentile(n, 96.5)))
        # (a) Zielgroesse aus der Zellentabelle (nur Zellen, k = 0)
        C = pd.read_csv(A.ZELLEN, sep=";")
        C["u"] = [U[ai[a], ti[t]] for a, t in zip(C.asset, C.tag)]
        st, be = C[(C.u == 1)].ertrag_s.dropna(), C[(C.u == -1)].ertrag_s.dropna()
        t2 = (st.mean() - be.mean()) / np.sqrt(st.var() / len(st) + be.var() / len(be))
        zp = np.array([Z3[ai[a], ti[t]] for a, t in zip(C.asset, C.tag)])
        print("   Zellentabelle ertrag_s: t %+.4f (n %d/%d) · Mittel stuetzt %+.3f belastet %+.3f · max |csv - panel| %.2e" % (
            t2, len(st), len(be), st.mean(), be.mean(), np.nanmax(np.abs(C.ertrag_s.values - zp))))


if __name__ == "__main__":
    import hashlib, sys, time
    with contextlib.redirect_stdout(_PUFFER):
        print("G7 STUFE 2 S7 GEGENPROBE · %s · Werkzeug %s" % (time.strftime("%Y-%m-%d %H:%M"),
              hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:16]))
        print("1  GEZÄHLT, OHNE KURSE"); _teil1()
        print(""); print("2  ZWEITER WEG (gegen g7_s7_messung.txt)"); _teil2()
    sys.stdout.reconfigure(encoding="utf-8"); print(_PUFFER.getvalue())
    import os
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "g7_stufe2_s7_gegenprobe.txt"), "w", encoding="utf-8").write(_PUFFER.getvalue())
