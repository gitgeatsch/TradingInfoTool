"""G7 STUFE 0 (Voranalyse_G7_Messplan_02_11.md §3, Nutzer 02.11.: „a/a/a, Stufe 0 bauen – prüfen, gegenprüfen und doku“).

  a  SELBSTTEST PRÜFER v2 (agent/gutachten_pruefer.py) an ECHTEN Eingaben: 30 Tage Dez. 2025 – Okt. 2026, je Fehlerart 1.000 gepflanzte
     Fälle, dazu korrekte Wiedergaben (Rundungen) als Fehlalarm-Probe. Daneben DERSELBE Fall durch Z-1 (Vergleich, Gegenprobe zu G7-5).
     SOLL (Bauplan §6): 100 % erkannt, 0 Fehlalarme
  b  SELBSTTEST MESSANLAGE (g7_messanlage.py) auf den ECHTEN Zielgrößen: geballte Null-Urteile (Lauflänge 1/3/10 T) -> Fehlalarm
     (Soll ≤ 5 %, einseitig), Pflanzung 0,1–0,5 σ -> Fundquote. VOR dem ersten Blick auf ein echtes Urteil (Memory)
  c  VERGLEICHSARM OHNE LLM (erst nach b): tragen die ZUSTÄNDE allein etwas? Rang je Zustand gegen ertrag_s/tief_s von BTC und Breite,
     H = 1/3/7, 2021-03 bis 2026-10, ZWEISEITIG (keine fachliche Richtung je Zustand), je Epoche. Darin der GDELT-Ton (Auftrag 01.11.),
     auch als 7-T-Mittel (G7-3: der Tageswert flackert)
  d  POSITIVKONTROLLE WISSENSSTAND je Modell (wie p66_gegenprobe G1): BTC-Schluss an Kontrolltagen 2023/24 und Testtagen 2025/26

VORAB FESTGELEGT (02.11.2026, vor dem ersten Blick auf c):
  * c ist eine SUCHE über viele Zustände -> erwartete Fehlalarme = Zahl der Tests × 5 %. Ein einzelnes TRÄGT ist ein HINWEIS; als Befund
    gilt nur, was in ≥ 2 von 3 Epochen mit GLEICHEM Vorzeichen außerhalb des Bands liegt (zweiter Weg = andere Epoche)
  * Epochen: 2021-03..2022-12 · 2023-01..2024-12 · 2025-01..2026-10 (neutral benannt nach Jahren)
  * Breite = Median der Tages-Log-Erträge der REGEL0-Werte mit Kurs (Messbasis stundenkurse.db + stundenkurse_alle.db), ab 2021-12

    python g7_stufe0.py a|b|c|d          -> g7_stufe0_<teil>.txt
"""
import json
import os
import re
import sqlite3
import sys
import time

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, PROJ)
import g7_messanlage as M  # noqa: E402
from agent import ereignisse as EV  # noqa: E402
from agent import gegenpruefer_rollen as Z1  # noqa: E402
from agent import gutachten_pruefer as GP  # noqa: E402
from agent import zustaende as Z  # noqa: E402

SAAT = 20261102
CACHE = os.path.join(PROJ, "data", "_g7")
EPOCHEN = {"2021-22": ("2021-03-01", "2022-12-31"), "2023-24": ("2023-01-01", "2024-12-31"), "2025-26": ("2025-01-01", "2026-10-31")}
AUS = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    AUS.append(s)


def fmt(k, n):
    return "%d/%d = %.1f %%" % (k, n, 100 * k / n) if n else "0/0"


# ══ a ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def teil_a():
    p("a  SELBSTTEST PRÜFER v2 an ECHTEN Eingaben (30 Tage Dez. 2025 – Okt. 2026), je Art 1.000 Fälle — daneben Z-1 auf denselben Fällen")
    rng = np.random.default_rng(SAAT)
    A, E, wl = Z.Ablage(), EV.lade(), Z._watchlist_krypto()
    tage = pd.date_range("2025-12-01", "2026-10-31", freq="D")
    welt = []
    for i in sorted(rng.choice(len(tage), 30, replace=False)):
        T = tage[i].strftime("%Y-%m-%d")
        L = Z.zustaende(T, A)
        ev = EV.am(E, T, assets=wl)
        welt.append((T, L, ev, Z.text(T, A, ereignisse=E, assets=wl)))
    p("   Ereignisse an den 30 Tagen (nur Börsen, Nachrichten laufen noch): %d" % sum(len(w[2]) for w in welt))

    def fall():
        """Ein KORREKTES Gutachten einer zufälligen Sicht: 3 Zustands-Treiber (+ Ereignis, + Termin, wo vorhanden)."""
        T, L, ev, txt = welt[rng.integers(len(welt))]
        s = ["S1", "S2", "S3", "S4", "S7", "S8"][rng.integers(6)]
        zs = [z for z in L if z.sicht == s and GP.angezeigt(z) is not None]
        tr = []
        for z in (rng.choice(zs, min(3, len(zs)), replace=False) if zs else []):
            w = GP.angezeigt(z)
            tr.append({"schluessel": GP.schluessel(z), "wert": w, "rang": int(round(z.rang)), "klasse": z.klasse,
                       "aussage": "%s steht bei %s" % (z.name, w)})
        evs = ev[ev.sicht == s]
        if len(evs):
            e = evs.iloc[rng.integers(len(evs))]
            tr.append({"ereignis": e.beleg, "typ": e.typ, "aussage": "Ereignis"})
        if s == "S8":
            t8 = [z for z in L if z.sicht == "S8" and z.stand]
            if t8:
                z = t8[rng.integers(len(t8))]
                tr.append({"termin": z.symbol, "tag": z.stand[:10], "aussage": "Termin"})
        g = {"sicht": s, "horizont_t": 3, "treiber": tr, "kippt_wenn": "", "gegenargument": ""}
        return g, GP.eingabe(L, ev, s), L, s, txt

    def z1_erkennt(g, txt):
        """Z-1 auf denselben Fall: Belege = die Aussagen mit den genannten Zahlen."""
        bel = ["%s %s" % (t.get("schluessel", ""), t.get("wert", "")) for t in g["treiber"] if "wert" in t]
        bel += ["P%s" % t["rang"] for t in g["treiber"] if "rang" in t]
        return Z1.pruefe_zahlendeckung({"lage": "", "belege": bel}, txt)["verstoss"]

    def lauf(name, pflanze, n=1000):
        k = k1 = m = 0
        for _ in range(n * 3):
            if m >= n:
                break
            g, ein, L, s, txt = fall()
            g2 = pflanze(g, ein, L, s)
            if g2 is None:
                continue
            m += 1
            k += not GP.pruefe(g2, ein)["ok"]
            k1 += z1_erkennt(g2, txt)
        p("   %-52s v2 %-22s Z-1 %s" % (name, fmt(k, m), fmt(k1, m) if name.startswith(("Wert", "Rang", "Bezug")) else "—"))
        return k, m

    def mit(g, i, **neu):
        g = json.loads(json.dumps(g))
        g["treiber"][i].update(neu)
        return g

    def zust(g):
        return [i for i, t in enumerate(g["treiber"]) if "schluessel" in t]

    def p_wert(d):
        def f(g, ein, L, s):
            ix = zust(g)
            if not ix:
                return None
            i = ix[rng.integers(len(ix))]
            w = g["treiber"][i]["wert"]
            x = float("%.4g" % (w * (1 + d * rng.choice([-1, 1]))))
            return None if GP.ist_rundung(x, w) else mit(g, i, wert=x, aussage="steht bei %s" % x)
        return f

    def p_rang(d):
        def f(g, ein, L, s):
            ix = [i for i in zust(g) if 0 <= g["treiber"][i]["rang"] + d <= 100]
            if not ix:
                return None
            i = ix[rng.integers(len(ix))]
            return mit(g, i, rang=g["treiber"][i]["rang"] + d)
        return f

    def p_bezug(g, ein, L, s):
        ix = zust(g)
        if not ix:
            return None
        i = ix[rng.integers(len(ix))]
        k = g["treiber"][i]["schluessel"]
        andere = [v[0] for kk, v in ein["zustand"].items() if kk != k and v[0] is not None]
        if not andere:
            return None
        w = andere[rng.integers(len(andere))]
        return None if GP.ist_rundung(w, g["treiber"][i]["wert"]) else mit(g, i, wert=w, aussage="steht bei %s" % w)

    def p_klasse(g, ein, L, s):
        ix = zust(g)
        if not ix:
            return None
        i = ix[rng.integers(len(ix))]
        k = [x for x in ("sehr tief", "tief", "normal", "hoch", "sehr hoch") if x != g["treiber"][i]["klasse"]]
        return mit(g, i, klasse=k[rng.integers(len(k))])

    def p_schluessel(fremd):
        def f(g, ein, L, s):
            ix = zust(g)
            if not ix:
                return None
            i = ix[rng.integers(len(ix))]
            if fremd:
                ks = [GP.schluessel(z) for z in L if z.sicht != s and z.sicht != "S8"]
                k = ks[rng.integers(len(ks))]
            else:
                k = g["treiber"][i]["schluessel"].rsplit(".", 1)[0] + ".ERFUNDEN"
            return mit(g, i, schluessel=k)
        return f

    def p_ereignis(g, ein, L, s):
        g = json.loads(json.dumps(g))
        g["treiber"].append({"ereignis": "https://erfunden.example/%d" % rng.integers(1e9), "typ": "hack_exploit", "aussage": "x"})
        return g

    def p_ereignis_typ(g, ein, L, s):
        ix = [i for i, t in enumerate(g["treiber"]) if "ereignis" in t]
        if not ix:
            return None
        i = ix[0]
        k = [x for x in EV.TYPEN if x != g["treiber"][i]["typ"]]
        return mit(g, i, typ=k[rng.integers(len(k))])

    def p_termin(g, ein, L, s):
        ix = [i for i, t in enumerate(g["treiber"]) if "termin" in t]
        if not ix:
            return None
        t = pd.Timestamp(g["treiber"][ix[0]]["tag"]) + pd.Timedelta(days=int(rng.choice([-1, 1, 7])))
        return mit(g, ix[0], tag=t.strftime("%Y-%m-%d"))

    def p_text(g, ein, L, s):
        g = json.loads(json.dumps(g))
        # Zahl ohne Exponent (der erste Bau schrieb "1.5e+03" - das liest kein Mensch und keine Regel), nie 0/1 und nie der Horizont
        z = np.format_float_positional(float("%.3g" % (10 ** rng.uniform(-2, 4))), trim="-")
        g["kippt_wenn"] = "wenn der Wert über %s steigt" % z
        belegt = [t.get("wert") for t in g["treiber"] if "wert" in t] + [t.get("rang") for t in g["treiber"] if "rang" in t]
        if float(z) in GP.HARMLOS or float(z) == g["horizont_t"] or any(b is not None and GP.ist_rundung(z, b) for b in belegt):
            return None
        return g

    p("   %-52s %-25s %s" % ("gepflanzter Fehler", "erkannt", ""))
    erg = {}
    for d in (0.01, 0.05, 0.20, 0.50, 1.00):
        erg["w%d" % (100 * d)] = lauf("Wert ±%.0f %%" % (100 * d), p_wert(d))
    erg["r1"] = lauf("Rang ±1", p_rang(int(rng.choice([-1, 1]))))
    erg["r10"] = lauf("Rang ±10", p_rang(10))
    erg["bezug"] = lauf("Bezug: Wert eines anderen Zustands derselben Sicht", p_bezug)
    erg["klasse"] = lauf("Klasse falsch", p_klasse)
    erg["k_erf"] = lauf("Schlüssel erfunden", p_schluessel(False))
    erg["k_fremd"] = lauf("Schlüssel aus einer anderen Sicht", p_schluessel(True))
    erg["ev"] = lauf("Ereignis-Beleg erfunden", p_ereignis)
    erg["ev_typ"] = lauf("Ereignis-Typ falsch (Beleg echt)", p_ereignis_typ)
    erg["termin"] = lauf("Termin-Tag falsch (±1 / +7 T)", p_termin)
    erg["text"] = lauf("Zahl im Freitext ohne Beleg", p_text)
    p("   %-52s %-25s" % ("KORREKTE Wiedergabe (darf NICHT anschlagen)", "Fehlalarm"))

    def p_rund(art):
        def f(g, ein, L, s):
            g = json.loads(json.dumps(g))
            for t in g["treiber"]:
                if "wert" in t:
                    w = t["wert"]
                    t["wert"] = {"genau": w, "2 Stellen": float("%.2g" % w), "3 Stellen": float("%.3g" % w),
                                 "ganzzahlig": float(round(w)) if abs(w) >= 10 else w, "1 Nachkommastelle": round(w, 1)
                                 if abs(w) >= 1 else w}[art]
                    t["aussage"] = "steht bei %s" % str(t["wert"]).replace(".", ",") if art == "3 Stellen" else "steht bei %s" % t["wert"]
                if art == "2 Stellen" and "rang" in t:
                    t["rang"] = "P%d" % t["rang"]
            return g
        return f
    fa = {}
    for art in ("genau", "2 Stellen", "3 Stellen", "ganzzahlig", "1 Nachkommastelle"):
        fa[art] = lauf("korrekt, %s%s" % (art, " (Rang als 'P37')" if art == "2 Stellen" else " (deutsches Komma im Text)"
                                          if art == "3 Stellen" else ""), p_rund(art))
    gesamt_f = sum(k for k, m in erg.values()), sum(m for k, m in erg.values())
    gesamt_a = sum(k for k, m in fa.values()), sum(m for k, m in fa.values())
    p("   ZUSAMMEN: erkannt %s · Fehlalarm %s  ->  %s" % (fmt(*gesamt_f), fmt(*gesamt_a),
                                                        "SOLL ERFÜLLT (100 % / 0)" if gesamt_f[0] == gesamt_f[1] and gesamt_a[0] == 0
                                                        else "⚠ SOLL NICHT ERFÜLLT"))


# ══ b / c Daten ═════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def breite_reihe():
    syms = sorted(set(pd.read_csv(os.path.join(PROJ, "data", "_vergleich", "kern48jbz_einstiege_bestand.csv"), sep=";").symbol))
    teile = []
    for db in ("stundenkurse.db", "stundenkurse_alle.db"):
        d = sqlite3.connect("file:%s?mode=ro" % os.path.join(PROJ, "data", db).replace("\\", "/"), uri=True)
        q = "SELECT symbol, substr(stunde,1,10) tag, close FROM stundenkurse WHERE substr(stunde,12,2)='23' AND symbol IN (%s)" % \
            ",".join("?" * len(syms))
        teile.append(pd.read_sql(q, d, params=syms))
        d.close()
    S = pd.concat(teile).drop_duplicates(["symbol", "tag"]).pivot_table(index="tag", columns="symbol", values="close")
    S.index = pd.to_datetime(S.index)
    r = np.log(S).diff().median(axis=1, skipna=True)
    r = r[S.notna().sum(axis=1) >= 20]                          # mindestens 20 Werte mit Kurs
    return np.exp(r.cumsum()).rename("BREITE")                  # Index der Breite (Median-Ertrag verkettet)


def kurs_btc():
    c = sqlite3.connect("file:%s?mode=ro" % EV.ABLAGE.replace("\\", "/"), uri=True)
    btc = pd.read_sql("SELECT datum, wert FROM reihe WHERE quelle='kurs' AND symbol='BTC'", c).groupby("datum").wert.last()
    c.close()
    btc.index = pd.to_datetime(btc.index)
    return btc.sort_index()


def teil_b():
    p("b  SELBSTTEST MESSANLAGE (g7_messanlage) auf den ECHTEN Zielgrößen — VOR dem ersten Blick auf ein Urteil")
    p("   Null: geballte Ja/Nein-Urteile (Rate 20 %, mittlere Lauflänge 1/3/10 T) ohne Bezug zur Zukunft, einseitig 'unten'; Soll ≤ 5 %. "
      "Pflanzung: Zielgröße an den Ja-Tagen um 0,1–0,5 σ gesenkt (Lauflänge 3 T)")
    rng = np.random.default_rng(SAAT)
    btc, br = kurs_btc(), breite_reihe()
    faelle = [("BTC", btc, "ertrag", 3, "2025-12-01", "2026-10-31"), ("BTC", btc, "tief", 3, "2025-12-01", "2026-10-31"),
              ("BTC", btc, "ertrag", 1, "2025-12-01", "2026-10-31"), ("Breite", br, "ertrag", 3, "2025-12-01", "2026-09-10"),
              ("BTC", btc, "ertrag", 7, "2025-01-01", "2026-10-31"), ("BTC", btc, "ertrag", 3, "2021-03-01", "2026-10-31")]
    alle_ok = True
    for name, k, art, H, a, b in faelle:
        z = M.zielgroesse(k, H, art).loc[a:b]
        t0 = time.time()
        r = M.selbsttest(z, H, rng, ziehungen=1000)
        if r["bloecke"] < M.MIN_BLOECKE:
            p("   %-6s %-6s H=%d %s..%s  %d Tage, %d Blöcke · KEIN BEFUND möglich (Daten fehlen, G7-1) — nicht bewertet" % (
                name, art, H, a, b, r["tage"], r["bloecke"]))
            continue
        ok = all(v <= 0.065 for v in r["fehlalarm"].values())
        alle_ok &= ok
        p("   %-6s %-6s H=%d %s..%s  %d Tage, %d Blöcke · Fehlalarm %s · Fund %s · %s (%.0f s)" % (
            name, art, H, a, b, r["tage"], r["bloecke"], " ".join("L%d %.1f %%" % (L, 100 * v) for L, v in r["fehlalarm"].items()),
            " ".join("%.1fσ %.0f %%" % (s, 100 * v) for s, v in r["fund"].items()), "OK" if ok else "⚠ ZU VIELE FEHLALARME",
            time.time() - t0))
    p("   => %s" % ("MESSANLAGE BESTANDEN (Fehlalarm ≤ 6,5 % = 5 % + 2 Standardfehler bei 1.000 Ziehungen)" if alle_ok
                    else "⚠ MESSANLAGE NICHT BESTANDEN — Teil c darf nicht laufen"))
    return alle_ok


# ══ c ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def zustaende_taeglich(a="2021-03-01", b="2026-10-31") -> pd.DataFrame:
    """Je Tag und Zustand Rang, Klasse, auffällig — einmal gerechnet, im Cache (data/_g7)."""
    os.makedirs(CACHE, exist_ok=True)
    pf = os.path.join(CACHE, "zustaende_taeglich_%s_%s.csv" % (a, b))
    if os.path.exists(pf):
        return pd.read_csv(pf, parse_dates=["tag"])
    A = Z.Ablage()
    zeilen = []
    for T in pd.date_range(a, b, freq="D"):
        for z in Z.zustaende(T.strftime("%Y-%m-%d"), A):
            if z.sicht != "S8" and z.rang is not None:
                zeilen.append((T, GP.schluessel(z), z.sicht, z.name, z.rang, z.klasse, int(z.auffaellig)))
    D = pd.DataFrame(zeilen, columns=["tag", "schluessel", "sicht", "name", "rang", "klasse", "auffaellig"])
    D.to_csv(pf, index=False, encoding="utf-8")
    return D


def teil_c():
    p("c  VERGLEICHSARM OHNE LLM — tragen die ZUSTÄNDE allein? Rang je Zustand gegen ertrag_s/tief_s, zweiseitig, je Epoche")
    rng = np.random.default_rng(SAAT + 1)
    D = zustaende_taeglich()
    btc, br = kurs_btc(), breite_reihe()
    R = D.pivot_table(index="tag", columns="schluessel", values="rang")
    namen = D.drop_duplicates("schluessel").set_index("schluessel").name
    for k in [c for c in R.columns if ".gdelt_ton." in c]:          # G7-3: der Tageswert flackert -> zusätzlich 7-T-Mittel
        R[k + "~7T"] = R[k].rolling(7, min_periods=5).mean()
        namen[k + "~7T"] = namen[k] + " (7-T-Mittel des Rangs)"
    auff = D.pivot_table(index="tag", columns="sicht", values="auffaellig", aggfunc="sum")
    for s in auff.columns:
        R["ANZAHL●." + s] = auff[s]
        namen["ANZAHL●." + s] = "Zahl auffälliger Zustände in %s" % s
    p("   %d Tage, %d Urteilsreihen (Zustände + GDELT-7T + Zahl ● je Sicht) · Zielreihen BTC, Breite (ab %s)" % (
        len(R), R.shape[1], br.index.min().date()))
    tests = treffer = 0
    zeilen = []
    for ziel_name, kurs in (("BTC", btc), ("Breite", br)):
        for art in ("ertrag", "tief"):
            for H in (1, 3, 7):
                z = M.zielgroesse(kurs, H, art)
                for k in R.columns:
                    je = {}
                    for ep, (a, b) in EPOCHEN.items():
                        r = M.messe(R[k].loc[a:b], z.loc[a:b], H, richtung="beide")
                        if r["urteil"] == "KEIN BEFUND":
                            continue
                        tests += 1
                        treffer += r["urteil"] == "TRÄGT"
                        je[ep] = r
                    aussen = {ep: np.sign(r["abstand"]) for ep, r in je.items() if r["urteil"] == "TRÄGT"}
                    if aussen:
                        zeilen.append((k, ziel_name, art, H, je, aussen))
    p("   %d Tests, davon außerhalb des Bands %d — erwartet ohne jede Wirkung ≈ %.0f (5 %%)" % (tests, treffer, 0.05 * tests))
    befund = [(k, zn, art, H, je, au) for k, zn, art, H, je, au in zeilen
              if max(sum(v > 0 for v in au.values()), sum(v < 0 for v in au.values())) >= 2]
    p("   BEFUND nach Vorab-Regel (≥ 2 von 3 Epochen, gleiches Vorzeichen): %d" % len(befund))
    for k, zn, art, H, je, au in sorted(befund, key=lambda x: x[0]):
        p("     %-46s %-6s %-6s H=%d  %s" % (namen.get(k, k)[:46], zn, art, H, " · ".join(
            "%s %+.3f (Band %+.3f..%+.3f)%s" % (ep, r["stat"], r["band"][0], r["band"][1], " ✱" if ep in au else "")
            for ep, r in je.items())))
    p("   HINWEISE (nur 1 Epoche außerhalb):")
    for k, zn, art, H, je, au in sorted(zeilen, key=lambda x: x[0]):
        if (k, zn, art, H) in {(b[0], b[1], b[2], b[3]) for b in befund}:
            continue
        ep = list(au)[0]
        p("     %-46s %-6s %-6s H=%d  %s %+.3f" % (namen.get(k, k)[:46], zn, art, H, ep, je[ep]["stat"]))
    p("   GDELT-TON im Einzelnen (Auftrag 01.11.: erst messen, ob er trägt):")
    for k in [c for c in R.columns if "gdelt" in c]:
        z = [x for x in befund if x[0] == k]
        h = [x for x in zeilen if x[0] == k]
        p("     %-50s Befund %d · Hinweise %d" % (namen.get(k, k)[:50], len(z), len(h) - len(z)))


def teil_c2():
    """GEGENPROBE zu c: wie viele „Befunde“ liefert die Vorab-Regel, wenn ALLE Zustände GEMEINSAM um j Tage verschoben werden (kein Bezug
    zur Zukunft, aber derselbe Zusammenhang zwischen den Reihen und Tests)? Je Verschiebung j wird jeder Test mit SEINEM Wert der vollen
    Bahn an Stelle j gelesen - dieselben Bänder wie in c. Zuerst muss c reproduziert werden (R-R11)."""
    p("c2 GEGENPROBE DER SUCHE — gemeinsame Verschiebung aller Zustände (globale Nullwelt), Vorab-Regel wie in c")
    D = zustaende_taeglich()
    btc, br = kurs_btc(), breite_reihe()
    R = D.pivot_table(index="tag", columns="schluessel", values="rang")
    for k in [c for c in R.columns if ".gdelt_ton." in c]:
        R[k + "~7T"] = R[k].rolling(7, min_periods=5).mean()
    auff = D.pivot_table(index="tag", columns="sicht", values="auffaellig", aggfunc="sum")
    for s_ in auff.columns:
        R["ANZAHL●." + s_] = auff[s_]
    T = {}
    for zn, kurs in (("BTC", btc), ("Breite", br)):
        for art in ("ertrag", "tief"):
            for H in (1, 3, 7):
                z = M.zielgroesse(kurs, H, art)
                for k in R.columns:
                    for ep, (a, b) in EPOCHEN.items():
                        r = M.messe(R[k].loc[a:b], z.loc[a:b], H, richtung="beide", mit_null=True)
                        if r["urteil"] != "KEIN BEFUND":
                            T[(k, zn, art, H, ep)] = (r["stat"], r["band"], r["null"], r["urteil"] == "TRÄGT")

    def zaehle(werte):
        """werte: {test: (stat, außerhalb)} -> (außerhalb, Befunde nach Vorab-Regel)."""
        gruppen = {}
        for (k, zn, art, H, ep), (st, aus, mitte) in werte.items():
            if aus:
                gruppen.setdefault((k, zn, art, H), []).append(np.sign(st - mitte))
        bef = sum(1 for v in gruppen.values() if max(sum(x > 0 for x in v), sum(x < 0 for x in v)) >= 2)
        return sum(1 for v in werte.values() if v[1]), bef
    beob = {t: (v[0], v[3], float(np.mean(v[2]))) for t, v in T.items()}
    a0, b0 = zaehle(beob)
    p("   Reproduktion von c: %d Tests, außerhalb %d, Befunde %d" % (len(T), a0, b0))
    n_min = min(len(v[2]) for v in T.values())
    aus_null, bef_null = [], []
    for j in range(1, n_min, 2):
        w = {}
        for t, (st, band, null, _) in T.items():
            x = null[(j - 1) % len(null)]
            w[t] = (x, x < band[0] or x > band[1], float(np.mean(null)))
        a, b = zaehle(w)
        aus_null.append(a)
        bef_null.append(b)
    aus_null, bef_null = np.array(aus_null), np.array(bef_null)
    p("   globale Nullwelt (%d Verschiebungen): außerhalb Mittel %.0f, 95. Perzentil %.0f, max %d · Befunde Mittel %.1f, 95. Perzentil %.0f, "
      "max %d" % (len(bef_null), aus_null.mean(), np.percentile(aus_null, 95), aus_null.max(), bef_null.mean(),
                  np.percentile(bef_null, 95), bef_null.max()))
    p("   beobachtet: außerhalb %d (Anteil der Nullwelten mit ≥ so vielen: %.1f %%) · Befunde %d (Anteil ≥: %.1f %%)" % (
        a0, 100 * (aus_null >= a0).mean(), b0, 100 * (bef_null >= b0).mean()))


# ══ d ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def teil_d():
    import requests
    from dotenv import dotenv_values
    p("d  POSITIVKONTROLLE WISSENSSTAND — erzwungene Schätzung des BTC-Schlusskurses (wie p66_gegenprobe G1)")
    env = dotenv_values(os.path.join(PROJ, ".env"))
    btc = kurs_btc()
    tage = [("Kontrolle", "2023-06-15"), ("Kontrolle", "2024-03-14"), ("Kontrolle", "2024-11-11"), ("Test", "2025-04-07"),
            ("Test", "2025-08-15"), ("Test", "2025-10-10"), ("Test", "2025-11-20"), ("Test", "2025-12-15"), ("Test", "2026-02-05"),
            ("Test", "2026-06-04")]
    r = requests.get("https://generativelanguage.googleapis.com/v1beta/models", params={"key": env.get("GEMINI_API_KEY_2")}, timeout=30)
    gem = sorted(m["name"].split("/")[1] for m in r.json().get("models", []) if "flash" in m["name"] and "gemini-3" in m["name"]
                 and "generateContent" in m.get("supportedGenerationMethods", []) and not any(x in m["name"] for x in
                                                                                             ("image", "tts", "audio", "live", "preview")))
    p("   Gemini-Modelle am Schlüssel 2 (flash, 3.x, Text): %s" % ", ".join(gem))
    modelle = [("gemini", m) for m in gem] + [("groq", "openai/gpt-oss-120b")]

    def frage(art, modell, text):
        body = {"model": modell, "temperature": 0, "messages": [{"role": "user", "content": text}]}
        if art == "gemini":
            url, key = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", env.get("GEMINI_API_KEY_2")
        else:
            url, key = "https://api.groq.com/openai/v1/chat/completions", env.get("GROQ_API_KEY")
            body["reasoning_effort"] = "low"
        for _ in range(6):
            x = requests.post(url, headers={"Authorization": "Bearer %s" % key}, json=body, timeout=120)
            if x.status_code == 429 or x.status_code >= 500:
                time.sleep(30)
                continue
            x.raise_for_status()
            return x.json()["choices"][0]["message"].get("content") or ""
        return ""
    for art, m in modelle:
        zeile = []
        for k, d in tage:
            echt = float(btc.asof(pd.Timestamp(d)))
            t = ("Schätze den Bitcoin-Schlusskurs in USD am %s (UTC). Du MUSST eine Zahl nennen, auch wenn du unsicher bist. "
                 "Antworte nur als JSON {\"btc_usd\": Zahl}." % d)
            try:
                g = float(json.loads(re.search(r"\{.*?\}", frage(art, m, t), re.S).group(0))["btc_usd"])
                f = abs(g / echt - 1)
            except Exception:  # noqa: BLE001
                f = None
            zeile.append((k, d, f))
            time.sleep(4 if art == "gemini" else 8)
        p("   %-34s %s" % (m, " · ".join("%s %s" % (d[2:7], ("%.0f%%" % (100 * f)) if f is not None else "–") for k, d, f in zeile)))
    p("   Lesart: Kontrolltage müssen klein sein (sonst taugt die Probe nicht). Ein Testtag mit kleinem Fehler (< 10 %) heißt: das Modell "
      "KENNT diesen Kurs — für ein Rückspiel ab dort ungeeignet. Massstab: BTC schwankte im Monat typisch 10–20 %")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    t = sys.argv[1]
    {"a": teil_a, "b": teil_b, "c": teil_c, "c2": teil_c2, "d": teil_d}[t]()
    open(os.path.join(HIER, "g7_stufe0_%s.txt" % t), "w", encoding="utf-8").write("\n".join(AUS) + "\n")


if __name__ == "__main__":
    main()
