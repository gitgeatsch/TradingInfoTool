"""G7 STUFE 2 — S8 Termine: Wert des Sicht-Gutachtens (Voranalyse_G7_Stufe1_04_11.md §4/§4.2, Vorabfestlegung_Scheideweg_Ende_November
_08_11.md §2.1 M-S8; Nutzer 08.11.2026: *„Ja, S8 messen“*).

    python -X utf8 Basisinfos/Rechenkern_02_10/g7_stufe2_s8.py   -> g7_stufe2_s8.txt

Vorab (§4 / §4.2, unverändert übernommen):
  * Hauptgröße: zustand ≥ auffällig gegen BTC |ertrag_s|, H = 1, einseitig OBEN (ein Termin sagt die Größe, nicht die Richtung)
  * Statistik, Nullwelt, Band: ``g7_messanlage.messe`` (volle Kreisbahn, P95 bei „oben“)
  * Mindestmaß: ≥ 20 Blöcke à 15 T MIT „auffällig“-Tagen, sonst KEIN BEFUND — dieselbe Regel für alle vier Haupttests (§4.2)
  * Holm-Familie bleibt vier (S1, S3, S8, S7); ein KEIN BEFUND verkleinert sie nicht
  * Ein Wert unter dem Mindestmaß ist AUSKUNFT und wird nie hochgestuft (wie S3)

Ablauf: ZUERST nur gezählt (ohne Kurse) — Rate, Läufe, Blöcke, Ursache je Terminart. Der Kurs wird erst danach EINMAL gelesen,
für die Auskunftszeile, mit zweitem Weg (Mittelwerte und Kreisbahn direkt aus dem BTC-Kurs, ohne messe/zielgroesse).

⚠️ Nur lesend: gutachten.db (mode=ro), BTC-Kurs über g7_stufe0 (mode=ro). Schreibt nur g7_stufe2_s8.txt hier.
"""
import hashlib
import math
import os
import re
import sqlite3
import sys
import time
from collections import Counter

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, PROJ)
sys.path.insert(0, HIER)
import g7_messanlage as M  # noqa: E402
import g7_stufe0 as S0  # noqa: E402
import messnorm  # noqa: E402

GUTACHTEN = os.path.join(PROJ, "data", "_g7", "gutachten.db")
AUS = os.path.join(HIER, "g7_stufe2_s8.txt")
VON, BIS = "2025-12-01", "2026-10-31"
H = 1
MIN_JA_BLOECKE = 20
TXT = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    TXT.append(s)


def werkzeug_sha():
    return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()[:16]


def lade():
    c = sqlite3.connect("file:%s?mode=ro" % GUTACHTEN.replace("\\", "/"), uri=True)
    d = pd.read_sql("SELECT tag, wdh, zustand, wirkung, treue_verstoesse, felder, eingabe FROM gutachten WHERE sicht='S8' AND form_ok=1",
                    c)
    alle = c.execute("SELECT COUNT(*) FROM gutachten WHERE sicht='S8' AND wdh=0").fetchone()[0]
    c.close()
    d["tag"] = pd.to_datetime(d.tag)
    return d, alle


def naechste(e: str) -> dict:
    """je Terminart der Abstand 'in x T' aus der Eingabe (das, was das LLM sah)."""
    return {a: float(t) for a, t in re.findall(r"\[termin (\w+)\][^\n]*?, in (\d+\.\d) T", e)}


def bloecke(tage: pd.Series) -> int:
    """zweiter Weg zum Blockzähler: Kalendertage ab Beginn // Blocklänge (nicht über Positionen)."""
    return len(set((pd.to_datetime(tage) - pd.Timestamp(VON)).dt.days // messnorm._block(H)))


def main():
    t0 = time.time()
    d, alle = lade()
    w0 = d[d.wdh == 0].set_index("tag").sort_index()
    u = (w0.zustand >= 1).astype(float).rename("S8")
    p("G7 STUFE 2 S8 — MESSUNG · %s · Werkzeug %s · Vorabfestlegung Voranalyse_G7_Stufe1_04_11.md §4/§4.2" % (
        time.strftime("%Y-%m-%d %H:%M"), werkzeug_sha()))
    p("Geltungsbereich: Dez. 2025 – Okt. 2026, gemini-3.5-flash-lite. Hauptgröße zustand ≥ auffällig gegen BTC |ertrag_s| H=1, oben.")
    p("")
    p("1  GEZÄHLT, OHNE KURSE")
    ja = u[u == 1].index
    laeufe, k = [], 0
    for x in u.values:
        if x:
            k += 1
        elif k:
            laeufe.append(k)
            k = 0
    if k:
        laeufe.append(k)
    jb_pos = len(set(np.flatnonzero(u.values == 1) // messnorm._block(H)))
    jb_kal = bloecke(pd.Series(ja))
    p("   Tage wdh 0: %d lesbar von %d · zustand %s · wirkung %s · Treue-Verstöße %d" % (
        len(w0), alle, dict(w0.zustand.value_counts().sort_index()), dict(w0.wirkung.value_counts().sort_index()),
        int((w0.treue_verstoesse > 0).sum())))
    p("   'auffällig': %d Tage (%.1f %%) · %d Läufe, mittlere Länge %.1f T" % (len(ja), 100 * u.mean(), len(laeufe),
                                                                            np.mean(laeufe) if laeufe else 0))
    p("   Blöcke à %d T mit 'auffällig': %d (über Positionen) · %d (über Kalendertage, zweiter Weg) · Mindestmaß %d" % (
        messnorm._block(H), jb_pos, jb_kal, MIN_JA_BLOECKE))
    befund = jb_pos >= MIN_JA_BLOECKE and jb_kal >= MIN_JA_BLOECKE
    p("   => %s" % ("Mindestmaß erreicht -> Hauptmessung" if befund else
                    "KEIN BEFUND — Mindestmaß verfehlt (%d < %d Blöcke). Alles unten ist AUSKUNFT, nie hochgestuft" % (
                        min(jb_pos, jb_kal), MIN_JA_BLOECKE)))

    # Ursache je Terminart (aus der Eingabe, die das LLM sah)
    w0 = w0.assign(n=w0.eingabe.map(naechste))
    import json
    arten_ja = Counter(t.get("termin") for f in w0[w0.zustand >= 1].felder for t in json.loads(f).get("treiber", []))
    nah, nah_ja = Counter(), Counter()
    for _, z in w0.iterrows():
        for a, t in z.n.items():
            if t <= 1:
                nah[a] += 1
                nah_ja[a] += int(z.zustand >= 1)
    p("   Ursache: Treiber an den 'auffällig'-Tagen %s · Tage mit Termin ≤ 1 T je Art %s, davon 'auffällig' %s" % (
        dict(arten_ja), dict(nah), dict(nah_ja)))
    for tag in ja:
        p("     %s  %s  nächster Termin in %s" % (tag.date(), [t.get("termin") for t in json.loads(w0.loc[tag].felder)["treiber"]],
                                                 {a: t for a, t in w0.loc[tag].n.items() if t <= 3}))
    m1 = w0.n.map(lambda x: min(x.values(), default=9.0)) <= 1
    p("   Zum Vergleich ohne LLM (nur gezählt, NICHT gemessen): Tage mit irgendeinem Termin ≤ 1 T: %d in %d Blöcken" % (
        int(m1.sum()), bloecke(pd.Series(w0.index[m1.values]))))
    w1 = d[d.wdh == 1].set_index("tag")
    if len(w1):
        b = w0.loc[w1.index]
        p("   Eigenrauschen: %d Wiederholungen, 'auffällig' gleich %.0f %%" % (len(w1), 100 * ((w1.zustand >= 1) == (b.zustand >= 1)).mean()))

    # 2 EINMAL gegen den Kurs — Auskunft (oder Hauptmessung, falls Mindestmaß erreicht)
    p("")
    p("2  GEGEN DEN KURS (einmal) — %s" % ("HAUPTMESSUNG" if befund else "AUSKUNFT"))
    btc = S0.kurs_btc()
    z = M.zielgroesse(btc, H, "ertrag").abs().loc[VON:BIS]
    m = M.messe(u, z, H, richtung="oben")
    if "stat" in m:
        p("   messe(): Stat %+.3f · Nullpunkt %+.3f · Band %+.3f/%+.3f · p %.3f · Anteil ja %.3f · %d Tage · %s%s" % (
            m["stat"], m["nullpunkt"], m["band"][0], m["band"][1], m["p"], m["anteil_ja"], m["tage"], m["urteil"],
            "" if befund else " (Auskunft)"))
    else:
        p("   messe(): %s (%s)" % (m["urteil"], m.get("grund")))

    # zweiter Weg: Zielgröße und Kreisbahn von Hand, ohne zielgroesse/messe
    k_ = btc.sort_index().astype(float)
    lr = np.log(k_).diff()
    sig = lr.rolling(M.SIGMA_TAGE).std().shift(1)
    x = (np.log(k_.shift(-H) / k_) / (sig * math.sqrt(H))).abs().loc[VON:BIS]
    dd = pd.concat([u.rename("u"), x.rename("z")], axis=1).dropna()
    uu, zz = dd.u.values, dd.z.values
    s2 = zz[uu == 1].mean() - zz[uu == 0].mean()
    null = []
    for kk in range(1, len(uu)):
        v = np.roll(uu, kk)
        null.append(zz[v == 1].mean() - zz[v == 0].mean())
    null = np.array(null)
    p2 = float((null >= s2).mean())
    p("   zweiter Weg (von Hand): Stat %+.3f · P95 %+.3f · p %.3f · Mittel |ertrag_s| ja %.3f (n %d) / nein %.3f (n %d) · %d Tage" % (
        s2, np.percentile(null, 95), p2, zz[uu == 1].mean(), int(uu.sum()), zz[uu == 0].mean(), int((uu == 0).sum()), len(uu)))
    gleich = "stat" in m and abs(m["stat"] - s2) < 1e-9 and abs(m["p"] - p2) < 1e-9
    p("   Gegenprobe messe() = von Hand: %s" % ("GLEICH" if gleich else "⚠ ABWEICHUNG"))
    p("")
    p("ERGEBNIS M-S8: %s · Holm-Familie bleibt vier (S1, S3, S8, S7) · %.0f s" % (
        ("siehe Hauptmessung" if befund else "KEIN BEFUND (Mindestmaß, %d Blöcke)" % min(jb_pos, jb_kal)), time.time() - t0))
    open(AUS, "w", encoding="utf-8").write("\n".join(TXT) + "\n")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    main()
