"""G7 STUFE 2 — S1 und S3: Wert des Sicht-Gutachtens gegen die Zielgröße und gegen den Vergleichsarm ohne LLM
(Voranalyse_G7_Stufe1_04_11.md §4 und §4.2, Nutzer 07.11.2026: *„OK erst messen dann Ton inkl. beschreibung“*).

    python -X utf8 Basisinfos/Rechenkern_02_10/g7_stufe2_s1s3.py --selbsttest   -> g7_stufe2_s1s3_selbsttest.txt  (KEIN Kursblick auf Urteile)
    python -X utf8 Basisinfos/Rechenkern_02_10/g7_stufe2_s1s3.py --messen       -> g7_stufe2_s1s3.txt  (verweigert sich ohne bestandenen Selbsttest)

Vorab (§4 / §4.2):
  * S1: zustand ≥ auffällig gegen BREITE tief_s, H = 3, einseitig unten · S3: dto. gegen BTC tief_s, H = 3
  * Statistik, Nullwelt, Band: ``g7_messanlage.messe`` (volle Kreisbahn, P5). Mindestmaß: ≥ 20 Blöcke à 15 T MIT „auffällig“-Tagen
  * Holm über vier (S1, S3, S8, S7); Zwischenurteil: p ≤ 0,0125 hält Holm unabhängig von S8/S7
  * Vergleichsarm: Zahl auffälliger Zustände derselben Sicht, gleiche Zahl Tage, Gleichstand per Los; gepaart über dasselbe k
  * ohne zweiten Weg (Stufe 5) heißt jedes TRÄGT „Hinweis“

⚠️ Nur lesend: gutachten.db (mode=ro), Kurs-Ablagen über g7_stufe0 (mode=ro), Zustands-Cache data/_g7. Schreibt nur die zwei .txt hier.
"""
import hashlib
import json
import os
import sqlite3
import sys
import time

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
AUS_ST = os.path.join(HIER, "g7_stufe2_s1s3_selbsttest.txt")
AUS = os.path.join(HIER, "g7_stufe2_s1s3.txt")
VON, BIS = "2025-12-01", "2026-10-31"
H = 3
MIN_JA_BLOECKE = 20
TOLERANZ = 6.5
ZIEH, ZIEH_PFL = 1000, 400
SAAT = 20261107
HOLM_N, ALPHA = 4, 0.05
SICHTEN = {"S1": ("Breite", "tief"), "S3": ("BTC", "tief")}
TXT = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    TXT.append(s)


# ══ Daten ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
_KURS = {}


KOPIE = os.path.join(PROJ, "data", "_g7", "kurse")      # Arbeitskopie bis 02.11. (Messplan §9.5), Messbasis-Dateien unberührt


def breite_kopie():
    """Breite wie ``g7_stufe0.breite_reihe`` (gleiche Werte, gleiche Dateien, 23-Uhr-Schluss, ≥ 20 Werte) — aber aus der ARBEITSKOPIE.
    Die Messbasis endet am 20.09.; ohne Sep./Okt. hätte S1 nur 19 Blöcke (Selbsttest 07.11., erster Lauf)."""
    import sqlite3 as _sq
    syms = sorted(set(pd.read_csv(os.path.join(PROJ, "data", "_vergleich", "kern48jbz_einstiege_bestand.csv"), sep=";").symbol))
    teile = []
    for db in ("stundenkurse.db", "stundenkurse_alle.db"):
        d = _sq.connect("file:%s?mode=ro" % os.path.join(KOPIE, db).replace("\\", "/"), uri=True)
        q = "SELECT symbol, substr(stunde,1,10) tag, close FROM stundenkurse WHERE substr(stunde,12,2)='23' AND symbol IN (%s)" % \
            ",".join("?" * len(syms))
        teile.append(pd.read_sql(q, d, params=syms))
        d.close()
    S = pd.concat(teile).drop_duplicates(["symbol", "tag"]).pivot_table(index="tag", columns="symbol", values="close")
    S.index = pd.to_datetime(S.index)
    r = np.log(S).diff().median(axis=1, skipna=True)
    r = r[S.notna().sum(axis=1) >= 20]
    return np.exp(r.cumsum()).rename("BREITE")


def kurs(name):
    if name not in _KURS:
        _KURS[name] = breite_kopie() if name == "Breite" else S0.kurs_btc()
    return _KURS[name]


def ziel(name, art, h=H):
    return M.zielgroesse(kurs(name), h, art).loc[VON:BIS]


def gutachten(sicht):
    c = sqlite3.connect("file:%s?mode=ro" % GUTACHTEN.replace("\\", "/"), uri=True)
    d = pd.read_sql("SELECT tag, wdh, zustand, wirkung, treue_verstoesse, ereignisse FROM gutachten WHERE sicht=? AND form_ok=1",
                    c, params=(sicht,))
    c.close()
    d["tag"] = pd.to_datetime(d.tag)
    return d


def urteil_zustand(sicht):
    d = gutachten(sicht)
    d = d[d.wdh == 0].set_index("tag").sort_index()
    return (d.zustand >= 1).astype(float).rename(sicht), d


def vergleich(sicht, u: pd.Series, rng) -> pd.Series:
    """Zahl auffälliger Zustände derselben Sicht; die höchsten Tage bis zur GLEICHEN Zahl Tage wie das LLM, Gleichstand per Los."""
    D = S0.zustaende_taeglich()
    a = D[D.sicht == sicht].groupby("tag").auffaellig.sum()
    a.index = pd.to_datetime(a.index)
    a = a.reindex(u.index)
    n = int(u.sum())
    los = rng.random(len(a))
    ordn = np.lexsort((los, -a.fillna(-1).values))
    v = np.zeros(len(a))
    v[ordn[:n]] = 1.0
    return pd.Series(v, index=u.index, name="V_" + sicht)


# ══ schnelle Bahn (für Selbsttest und gepaarten Vergleich) — gegengeprüft gegen messe() ═══════════════════════════════════════
def bahn(u: np.ndarray, z: np.ndarray) -> np.ndarray:
    """Stat für k = 0 … n−1 mit np.roll(u, k) gegen z: Mittel(z | ja) − Mittel(z | nein). Kreis per FFT."""
    n = len(z)
    nj = u.sum()
    s1 = np.fft.irfft(np.conj(np.fft.rfft(u)) * np.fft.rfft(z), n=n)       # [k] = Σ_i u[i] z[i+k] = Σ_j roll(u,k)[j] z[j]
    mj = s1 / nj
    mn = (z.sum() - s1) / (n - nj)
    return mj - mn


def ausgerichtet(u: pd.Series, z: pd.Series):
    d = pd.concat([u.rename("u"), z.rename("z")], axis=1).dropna()
    return d.u.values.astype(float), d.z.values.astype(float), d.index


def entscheid(b: np.ndarray, richtung="unten") -> tuple[bool, float]:
    null = b[1:][np.isfinite(b[1:])]
    if richtung == "unten":
        return bool(b[0] < np.percentile(null, 5)), float((null <= b[0]).mean())
    return bool(b[0] > np.percentile(null, 95)), float((null >= b[0]).mean())


def ja_bloecke(u: np.ndarray) -> int:
    return len(set(np.flatnonzero(u == 1) // messnorm._block(H)))


# ══ Selbsttest ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def laeufe_rate(u: np.ndarray):
    r, k = [], 0
    for x in u:
        if x:
            k += 1
        elif k:
            r.append(k)
            k = 0
    if k:
        r.append(k)
    return float(u.mean()), float(np.mean(r)) if r else 1.0


def neu_losen(c: np.ndarray, anteil: float, rate: float, lauf: float, rng) -> np.ndarray:
    """Ein Arm mit WENIGER Information: ein Anteil der Tage wird durch ein unabhängiges geballtes Urteil ersetzt (in Läufen)."""
    maske = M.geballt(len(c), anteil, lauf, rng).astype(bool)
    x = c.copy()
    x[maske] = M.geballt(len(c), rate, lauf, rng)[maske]
    return x


def selbsttest():
    t0 = time.time()
    rng = np.random.default_rng(SAAT)
    p("G7 STUFE 2 S1/S3 — SELBSTTEST · %s · KEIN Urteil gegen Kurse: Urteile künstlich mit der ECHTEN Rate/Lauflänge, Zielgrößen echt"
      % time.strftime("%Y-%m-%d %H:%M"))
    alles_ok = True
    for sicht, (zn, art) in SICHTEN.items():
        u_echt, _ = urteil_zustand(sicht)
        z = ziel(zn, art)
        u0, zz, idx = ausgerichtet(u_echt, z)
        rate, lauf = laeufe_rate(u0)
        n = len(zz)
        p("")
        p("%s gegen %s %s H=%d · %d Tage (%s..%s) · Rate %.1f %% · mittlere Lauflänge %.1f T · Blöcke %d" % (
            sicht, zn, art, H, n, idx.min().date(), idx.max().date(), 100 * rate, lauf, n // messnorm._block(H)))

        # 0 Gegenprobe schnelle Bahn gegen messe()
        abw = 0.0
        gleich = knapp = gezogen = 0
        while gezogen < 20:                     # 20 GÜLTIGE Ziehungen (erster Lauf 07.11.: eine leere Reihe übersprungen -> "19/20")
            u = M.geballt(n, rate, lauf, rng)
            if len(np.unique(u)) < 2:
                continue
            gezogen += 1
            b = bahn(u, zz)
            m = M.messe(pd.Series(u, index=idx), pd.Series(zz, index=idx), H, richtung="unten")
            if "stat" not in m:
                sys.exit("%s: messe() sagt %s (%s) — nicht messbar, Selbsttest abgebrochen" % (sicht, m["urteil"], m.get("grund")))
            naiv = np.array([M._stat(np.roll(u, k), zz) for k in range(n)])          # die GANZE Bahn, nicht nur k = 0
            abw = max(abw, abs(b[0] - m["stat"]), float(np.nanmax(np.abs(b - naiv))))
            # Gleichstand an der Grenze (|Stat − P5| < 1e-9) entscheidet die Rundung (FFT ±1e-15), nicht die Rechnung -> eigens gezählt
            if abs(m["stat"] - m["band"][0]) < 1e-9:
                gleich += 1
                knapp += 1
            else:
                gleich += entscheid(b)[0] == (m["urteil"] == "TRÄGT")
        p("  0 Gegenprobe Bahn (FFT) gegen messe(): größte Abweichung %.1e · gleiche Entscheidung %d/20 (davon %d Gleichstand an "
          "der Grenze)" % (abw, gleich, knapp))
        ok0 = abw < 1e-9 and gleich == 20

        # 1 Fehlalarm Hauptstatistik
        fa = {}
        # Lauf 1 ist bei Rate > 1/3 KEIN gültiger Erzeuger: geballt() braucht p_ein = rate/((1−rate)·L) ≤ 1; bei Rate 60 % und L = 1
        # wird p_ein 1,5 und die Reihe zur starren Wechselfolge 0101… (erster Lauf 07.11.: 39,8 % "Fehlalarm" = Artefakt des Erzeugers)
        l_min = 1.0 if rate <= 1 / 3 else 2.0
        for L in sorted({l_min, round(lauf, 1), 10.0}):
            f = k = 0
            while k < ZIEH:
                u = M.geballt(n, rate, L, rng)
                if len(np.unique(u)) < 2:
                    continue
                k += 1
                f += entscheid(bahn(u, zz))[0]
            fa[L] = 100 * f / ZIEH
        ok1 = all(v <= TOLERANZ for v in fa.values())
        p("  1 Fehlalarm Hauptstatistik (Soll ≤ %.1f %%): %s" % (TOLERANZ, " · ".join("Lauf %.1f T: %.1f %%" % kv for kv in fa.items())))

        # 2 Fehlalarm gepaart: zwei Arme mit GLEICHER Information
        fp = {}
        for name, wirkung in (("mit Wirkung 0,3 σ", 0.3), ("ohne Wirkung", 0.0)):
            f = k = 0
            while k < ZIEH:
                c = M.geballt(n, rate, lauf, rng)
                a, b = neu_losen(c, 0.3, rate, lauf, rng), neu_losen(c, 0.3, rate, lauf, rng)
                if min(len(np.unique(a)), len(np.unique(b))) < 2:
                    continue
                k += 1
                zp = zz - wirkung * c
                f += entscheid(bahn(a, zp) - bahn(b, zp))[0]
            fp[name] = 100 * f / ZIEH
        ok2 = all(v <= TOLERANZ for v in fp.values())
        p("  2 Fehlalarm gepaart 'bringt etwas' bei gleicher Information (Soll ≤ %.1f %%): %s" % (
            TOLERANZ, " · ".join("%s: %.1f %%" % kv for kv in fp.items())))

        # 3 Auflösung Hauptstatistik
        fund = {}
        for s in (0.1, 0.2, 0.3, 0.5):
            f = k = 0
            while k < ZIEH_PFL:
                u = M.geballt(n, rate, lauf, rng)
                if len(np.unique(u)) < 2:
                    continue
                k += 1
                f += entscheid(bahn(u, zz - s * u))[0]
            fund[s] = 100 * f / ZIEH_PFL
        p("  3 Auflösung Hauptstatistik (Fundquote): %s" % " · ".join("%.1f σ: %.0f %%" % kv for kv in fund.items()))

        # 4 Auflösung gepaart: A trägt s, B ist A mit einem Teil neu gelost
        zeile = []
        for s in (0.3, 0.5):
            for anteil in (0.5, 1.0):
                f = k = 0
                while k < ZIEH_PFL // 2:
                    c = M.geballt(n, rate, lauf, rng)
                    b = neu_losen(c, anteil, rate, lauf, rng) if anteil < 1 else M.geballt(n, rate, lauf, rng)
                    if min(len(np.unique(c)), len(np.unique(b))) < 2:
                        continue
                    k += 1
                    zp = zz - s * c
                    f += entscheid(bahn(c, zp) - bahn(b, zp))[0]
                zeile.append("%.1f σ, B %3.0f %% neu: %.0f %%" % (s, 100 * anteil, 100 * f / (ZIEH_PFL // 2)))
        p("  4 Auflösung gepaart (Fundquote 'bringt etwas'): %s" % " · ".join(zeile))
        ok = ok0 and ok1 and ok2
        alles_ok &= ok
        p("  => %s (%.0f s)" % ("BESTANDEN" if ok else "⚠ NICHT BESTANDEN — Band eichen, nicht messen", time.time() - t0))
    p("")
    p("SELBSTTEST %s · Prüfsumme Werkzeug %s" % ("BESTANDEN" if alles_ok else "NICHT BESTANDEN", werkzeug_sha()))
    open(AUS_ST, "w", encoding="utf-8").write("\n".join(TXT) + "\n")
    return alles_ok


def werkzeug_sha():
    return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()[:16]


# ══ Messung ═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def holm_zwischen(p_wert, traegt):
    if not traegt:
        return "trägt nicht"
    if p_wert <= ALPHA / HOLM_N:
        return "TRÄGT (Hinweis) — hält Holm unabhängig von S8/S7"
    return "TRÄGT vorbehaltlich Holm (S8/S7 offen) — Hinweis"


def zeile_messe(name, u, z, h, richtung="unten"):
    m = M.messe(u, z, h, richtung=richtung)
    if m["urteil"] == "KEIN BEFUND":
        p("    %-44s KEIN BEFUND (%s)" % (name, m["grund"]))
        return m
    p("    %-44s Stat %+.3f · Nullpunkt %+.3f · Band %+.3f/%+.3f · p %.3f · Anteil ja %.2f · %d Tage · %s" % (
        name, m["stat"], m["nullpunkt"], m["band"][0], m["band"][1], m["p"], m["anteil_ja"], m["tage"], m["urteil"]))
    return m


def messen():
    if not os.path.exists(AUS_ST) or "SELBSTTEST BESTANDEN" not in open(AUS_ST, encoding="utf-8").read():
        sys.exit("Selbsttest fehlt oder nicht bestanden — erst --selbsttest")
    if werkzeug_sha() not in open(AUS_ST, encoding="utf-8").read():
        sys.exit("Werkzeug seit dem Selbsttest geändert — Selbsttest neu laufen lassen")
    rng = np.random.default_rng(SAAT + 1)
    p("G7 STUFE 2 S1/S3 — MESSUNG · %s · Werkzeug %s · Vorabfestlegung Voranalyse_G7_Stufe1_04_11.md §4/§4.2" % (
        time.strftime("%Y-%m-%d %H:%M"), werkzeug_sha()))
    p("Geltungsbereich: Dez. 2025 – Okt. 2026, gemini-3.5-flash-lite, Sicht MIT GDELT-Ton (§4.2). Ohne zweiten Weg (Stufe 5) = Hinweis.")
    for sicht, (zn, art) in SICHTEN.items():
        u, d = urteil_zustand(sicht)
        z = ziel(zn, art)
        u0, zz, idx = ausgerichtet(u, z)
        jb = ja_bloecke(u0)
        p("")
        p("%s  Hauptgröße: zustand ≥ auffällig gegen %s %s_s H=%d, einseitig unten · Blöcke mit 'auffällig' %d (Mindestmaß %d)" % (
            sicht, zn, art, H, jb, MIN_JA_BLOECKE))
        haupt = zeile_messe("HAUPT" if jb >= MIN_JA_BLOECKE else "Auskunft (Mindestmaß verfehlt)", u, z, H)
        if jb < MIN_JA_BLOECKE:
            p("  => %s: KEIN BEFUND — Mindestmaß verfehlt (%d Blöcke < %d). Der Wert oben ist Auskunft über EINE Phase" % (
                sicht, jb, MIN_JA_BLOECKE))
        elif haupt["urteil"] != "KEIN BEFUND":
            p("  => %s: %s" % (sicht, holm_zwischen(haupt["p"], haupt["urteil"] == "TRÄGT")))

        # Vergleichsarm
        v = vergleich(sicht, u, rng)
        p("  Vergleichsarm ohne LLM (Zahl ● in %s, gleiche Zahl Tage %d):" % (sicht, int(v.sum())))
        zeile_messe("Vergleich allein", v, z, H)
        v0, _, _ = ausgerichtet(v, z)
        dbahn = bahn(u0, zz) - bahn(v0, zz)
        besser, pd_ = entscheid(dbahn)
        null = dbahn[1:]
        p("    %-44s D %+.3f · Nullpunkt %+.3f · P5 %+.3f · p %.3f · %s%s" % (
            "gepaart LLM − Vergleich", dbahn[0], null.mean(), np.percentile(null, 5), pd_, "BRINGT ETWAS" if besser else
            "bringt nichts darüber hinaus", "" if jb >= MIN_JA_BLOECKE else " (Auskunft)"))

        # Auskunft
        p("  Auskunft (nie hochgestuft):")
        for h in (1, 5):
            zeile_messe("H=%d %s" % (h, art), u, ziel(zn, art, h), h)
        zeile_messe("H=3 ertrag", u, ziel(zn, "ertrag"), H)
        if sicht == "S1":
            zeile_messe("H=3 tief gegen BTC", u, ziel("BTC", "tief"), H)
        else:
            zeile_messe("H=3 tief gegen Breite", u, ziel("Breite", "tief"), H)
        ohne = u.copy()
        ohne[d.treue_verstoesse.reindex(u.index).fillna(0) > 0] = np.nan
        zeile_messe("ohne Tage mit Treue-Verstoß (%d)" % int((d.treue_verstoesse > 0).sum()), ohne, z, H)
        w = (d.wirkung == 1).astype(float).rename("w")
        zeile_messe("wirkung 'belastet' gegen Rest", w, z, H)
        wegb = d.ereignisse.fillna("{}").map(lambda s: any(e.get("herkunft") == ["weg_b"] for e in json.loads(s).values())
                                             if s.strip().startswith("{") else False)
        if wegb.any():
            p("    Weg b: Tage mit Zeile nur aus Weg b %d — Anteil auffällig %.2f · ohne %d — %.2f" % (
                int(wegb.sum()), u[wegb.values].mean(), int((~wegb).sum()), u[(~wegb).values].mean()))
        r = gutachten(sicht)
        w1 = r[r.wdh == 1].set_index("tag")
        if len(w1):
            b = d.loc[w1.index]
            p("    Eigenrauschen: %d Wiederholungen, 'auffällig' gleich %.0f %%" % (
                len(w1), 100 * ((w1.zustand >= 1) == (b.zustand >= 1)).mean()))
    open(AUS, "w", encoding="utf-8").write("\n".join(TXT) + "\n")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    if "--selbsttest" in sys.argv:
        selbsttest()
    elif "--messen" in sys.argv:
        messen()
    else:
        print(__doc__)
