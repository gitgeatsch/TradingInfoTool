# -*- coding: utf-8 -*-
"""H-3 - WAS TUT r(q)? Die Hebelverteilung ueber echte Anker (11.09.2026).

## Der Auftrag

Paket B, Schritt 19 - VOR dem Scharfschalten von `rollen_kette.
hebel_aus_quote.aktiv`. Nutzervorgabe 28.08.: *"deckle den Hebel bei ... -
vorher pruefen und simulieren."* Die Fragen:

    wie oft wird es Spot (unter 2x)?
    wie oft ein Hebel 2-5x?
    wie oft greift die Grenze 5x, wie oft der Liquidationsabstand?
    wie haengt das an der Beitragslage, am Kapital, an der Zeit?

## ⚠️ Was das beantwortet - und was NICHT

Es zeigt, was die Regel TUT, nicht ob sie TRIFFT. Ob ein hoeherer Hebel mit
einer hoeheren realen Trefferquote einhergeht, ist die Trennschaerfe-Frage
und haengt an A1 (Befund 2.238). Diese Simulation ersetzt sie nicht.

## Wie gerechnet wird - mit den ECHTEN Funktionen

    Anker          je Kalendertag alle Krypto-Reihen der eingefrorenen
                   Messmenge V1 mit 250-Tage-Momentum (`K.baue`)
    Beitraege      Funding- und Turnover-Rang als Tagesfuenftel ueber die
                   Anker, die den Wert haben (0 = niedrigster Rohwert, wie
                   `marktrang`)
    Bewertung      `potential.rechne()` - Quote, Schwelle je Datenlage,
                   Durchlass wie Stufe 11
    Stop           `entscheidungsrechnung.stop_relativ()` mit dem ATR aus
                   `atr_wilder` - dieselbe Stelle wie `rechne()`
    Hebel          `betraege.hebelrechnung()` mit der Liquidationsgrenze
                   `hebel_sicher()` und den Einstellungen aus config.yaml
    Kapital        drei Stufen: 9.942 (alter NB-Wert ohne Gestaktes),
                   18.213 (NB-Kopie nach H-1), 30.000 (Zuwachs)
    Auswahl        zusaetzlich die oberste Momentum-Menge je Tag (20 %),
                   wie die Messnorm sie fuer Beitraege verlangt

⚠️⚠️ DER STOP IM BETRIEB - und ein Irrtum im ersten Entwurf dieses Kopfes.
Hier stand: Marken und Widerlegungspreis "koennen den Stop nur WEITER
machen". FALSCH. `_stop_abstand` nimmt den Rueckfall auf 2,5 x ATR NUR,
wenn das Modell KEINEN Widerlegungspreis nennt. Nennt es einen - am
Notebook in 1.425 von 1.427 Einstiegen seit 23.08. -, gilt der Rauschboden
max(2 x ATR, 5 %), und der Stop wird ENGER. Der Vorabtest ohne
Widerlegungspreis ergab deshalb Stops um 20 % statt der echten 7,6 %.

Die Simulation rechnet den BETRIEBSFALL mit der echten Funktion: ein
Widerlegungspreis 0,1 % unter dem Kurs (liegt im Rauschen, der Rauschboden
gewinnt). Der Fall OHNE Widerlegungspreis steht als Empfindlichkeit dabei.
Ein Widerlegungspreis JENSEITS des Rauschbodens macht den Stop im Betrieb
weiter - der ist historisch nicht bekannt.

⚠️ WEITERE ABWEICHUNGEN VOM BETRIEB, benannt:
- Marken (Struktur-Boden) sind historisch nicht vorhanden; sie koennen den
  Stop nur weiter machen.
- Die Querschnitte sind die der Messbasis, nicht die 300 Funding- und 66
  Turnover-Werte des Live-Abrufs.
- Das Kapital ist je Lauf fest.

    python simuliere_hebelverteilung.py
    python simuliere_hebelverteilung.py --kapital 9942 18213 30000 --anteil 0.2
"""
from __future__ import annotations

import argparse
import random
import statistics as st
import sys
from collections import Counter, defaultdict

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

import config as C                                            # noqa: E402
import messe_bewertungskennzahl as MB                         # noqa: E402
import messe_eigenschaft_beitrag as B                         # noqa: E402
import messe_funding_niveau as F                              # noqa: E402
import messe_kandidaten_als_regel as K                        # noqa: E402
from agent import betraege as BE                              # noqa: E402
from agent import entscheidungsrechnung as ER                 # noqa: E402
from agent import potential as PT                             # noqa: E402
from indicators.calculations import atr_wilder                # noqa: E402

CRV = ER.GRENZEN["crv"]
# Der Widerlegungspreis im Betriebsfall: knapp unter dem Kurs, also IM
# Rauschen - dann gewinnt der Rauschboden, und der 2,5-ATR-Rueckfall entfaellt
# wie in `_stop_abstand`. Siehe Kopf.
THESE_ABSTAND = 0.001
KAPITAL_VORGABE = (9942.0, 18213.0, 30000.0)


def fuenftel(werte):
    """0 = niedrigster Rohwert - dieselbe Richtung wie `marktrang._rang`."""
    r = np.argsort(np.argsort(np.asarray(werte, float))) / max(len(werte) - 1, 1)
    return np.minimum((r * 5).astype(int), 4)


def kurs_und_atr(reihen) -> dict:
    """Je Symbol {Tag: (Schluss, ATR)} - ATR nach Wilder, streng kausal."""
    aus = {}
    for sym, roh in reihen.items():
        c = np.array([z[1] for z in roh], float)
        h = np.array([z[2] for z in roh], float)
        lo = np.array([z[3] for z in roh], float)
        a = atr_wilder(h, lo, c)
        if not a.available:
            continue
        w = np.asarray(a.value, float)
        aus[sym] = {z[0]: (float(c[i]), float(w[i])) for i, z in enumerate(roh)
                    if np.isfinite(w[i]) and w[i] > 0 and c[i] > 0}
    return aus


def anker(reihen, funding, mom, tu, anteil) -> list:
    ka = kurs_und_atr(reihen)
    tu_je = {t: {x["sym"]: x["kennzahl"] for x in z} for t, z in tu.items()}
    alle = []
    for tag, zeilen in sorted(mom.items()):
        syms = [x for x in zeilen if x["sym"] in ka and tag in ka[x["sym"]]]
        if len(syms) < K.MIND_JE_TAG:
            continue
        srt = sorted(syms, key=lambda x: x["kennzahl"], reverse=True)
        auswahl = {x["sym"] for x in srt[:max(1, int(round(anteil * len(srt))))]}
        tv = [(x["sym"], tu_je.get(tag, {}).get(x["sym"])) for x in syms]
        tv = [(s, v) for s, v in tv if v is not None]
        fv = [(x["sym"], funding.get(x["sym"].upper(), {}).get(tag)) for x in syms]
        fv = [(s, v) for s, v in fv if v is not None]
        t5 = (dict(zip([s for s, _ in tv], fuenftel([v for _, v in tv])))
              if len(tv) >= 5 else {})
        f5 = (dict(zip([s for s, _ in fv], fuenftel([v for _, v in fv])))
              if len(fv) >= 5 else {})
        for x in syms:
            s = x["sym"]
            kurs, atr = ka[s][tag]
            alle.append({"tag": tag, "sym": s, "kurs": kurs, "atr": atr,
                         "f5": (int(f5[s]) if s in f5 else None),
                         "t5": (int(t5[s]) if s in t5 else None),
                         "auswahl": s in auswahl})
    return alle


_CACHE: dict = {}


def bewertung(f5, t5):
    """(Quote, Durchlass, Potential, Schwelle) - aus `potential.rechne()`.

    Die Quote haengt nicht am Stop (N-40); zwischengespeichert wird deshalb
    je Beitragslage. Die Gegenpruefung G5 vergleicht Stichproben mit dem
    direkten Aufruf."""
    key = (f5, t5)
    if key not in _CACHE:
        m = {}
        if f5 is not None:
            m["funding_fuenftel"] = int(f5)
        if t5 is not None:
            m["turnover_fuenftel"] = int(t5)
        p = PT.rechne(crv=CRV, stop_relativ=ER.GRENZEN["stop_min_relativ"],
                      klasse="krypto", instrument="spot",
                      strategie="einstieg", h=None, merkmale=m or None)
        _CACHE[key] = (p.quote, bool(p.bewertbar and p.traegt_hier),
                       p.wert_r, p.schwelle)
    return _CACHE[key]


def lage(a) -> str:
    if a["f5"] is not None and a["t5"] is not None:
        return "funding + turnover"
    if a["f5"] is not None:
        return "nur funding"
    if a["t5"] is not None:
        return "nur turnover"
    return "keine"


def pct(n, d) -> str:
    """Deutsche Schreibweise - der Bericht wird zitiert (Nutzervorgabe)."""
    from agent.schreibweise import de as _de
    return ("%6s %%" % _de(100.0 * n / d, 1)) if d else "     - "


def de(x, n=1) -> str:
    from agent.schreibweise import de as _de
    return _de(x, n)


def verteilung(zeilen, kap, titel, feld="h"):
    """Die Tabelle je Kapitalstufe - Spot, Hebel, Grenzen."""
    n = len(zeilen)
    hs = [a[feld][kap] for a in zeilen]
    spot = sum(1 for h in hs if not h["ist_hebel"])
    hebel = [h for h in hs if h["ist_hebel"]]
    g5 = sum(1 for h in hebel if h["grenze_greift"])
    liq = sum(1 for h in hebel if h["liquidation_greift"])
    frei = len(hebel) - g5 - liq
    print("  %-34s %8d   Spot %s   Hebel %s   davon frei 2-5x %s · Grenze 5x %s · Liquidation %s"
          % (titel, n, pct(spot, n), pct(len(hebel), n), pct(frei, n),
             pct(g5, n), pct(liq, n)))
    return hebel


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kapital", nargs="+", type=float, default=list(KAPITAL_VORGABE))
    ap.add_argument("--anteil", type=float, default=0.20)
    ap.add_argument("--saat", type=int, default=20260911)
    # NUR EIN ZEITFENSTER (11.09.2026): die Schwankung der fruehen Jahre war
    # groesser, die Stops damit weiter. `--ab 2026-01-01` zeigt die Lage
    # nahe am heutigen Betrieb. Die Tagesfuenftel entstehen trotzdem ueber
    # den vollen Querschnitt des jeweiligen Tages.
    ap.add_argument("--ab", default=None)
    # NUR DIE WATCHLIST (11.09.2026): gezaehlt werden nur die Krypto-Werte
    # der Watchlist - die Tagesfuenftel entstehen WEITER ueber den vollen
    # Querschnitt, wie im Betrieb der Rang ueber rund 300 Werte.
    ap.add_argument("--nur-watchlist", action="store_true")
    arg = ap.parse_args()
    kapital = [float(k) for k in arg.kapital]
    cfg = C.load_config() or {}
    ein = {**BE.hebel_aus_quote_einstellungen(cfg), "aktiv": True}
    k_stop = BE.stop_min_atr(cfg)

    print("=" * 100)
    print("H-3 · DIE HEBELVERTEILUNG AUS r(q) - ueber echte historische Anker")
    print("=" * 100)
    print("Einstellungen: r %s-%s %% des Kapitals · Einsatz %s EUR · Hebel ab %sx · Grenze %sx · Stopboden %s ATR"
          % (de(100 * ein["r_min"], 2), de(100 * ein["r_max"], 2),
             de(ein["hebelnenner_eur"], 0), de(ein["hebel_ab"], 1),
             de(ein["hebel_grenze"], 1), k_stop))
    reihen = B.lade()
    menge = MB.reihe("data/onchain_historie.db", "splycur")
    funding = F.lade_funding()
    mom = K.baue(reihen, "momentum")
    tu = K.baue(reihen, "turnover", menge)
    alle = anker(reihen, funding, mom, tu, arg.anteil)
    if arg.ab:
        alle = [a for a in alle if a["tag"] >= arg.ab]
        print("ZEITFENSTER ab %s" % arg.ab)
    if arg.nur_watchlist:
        _wl = {str(w.symbol).upper() for w in C.get_watchlist()
               if getattr(w, "assetklasse", "krypto") == "krypto"}
        alle = [a for a in alle if str(a["sym"]).upper() in _wl]
        print("NUR WATCHLIST: %d Krypto-Werte, davon mit Ankern %d"
              % (len(_wl), len({a["sym"] for a in alle})))
    tage = sorted({a["tag"] for a in alle})
    print("Anker %d · Kalendertage %d (%s bis %s) · Symbole %d"
          % (len(alle), len(tage), tage[0], tage[-1], len({a["sym"] for a in alle})))

    durch = []
    for a in alle:
        q, ok, wert_r, schwelle = bewertung(a["f5"], a["t5"])
        a.update(quote=q, durch=ok)
        if not ok:
            continue
        a["stop"] = ER.stop_relativ(
            kurs=a["kurs"], atr=a["atr"], stop_min_atr=k_stop,
            umgeworfen_preis_eur=a["kurs"] * (1.0 - THESE_ABSTAND))
        a["stop_ohne"] = ER.stop_relativ(kurs=a["kurs"], atr=a["atr"],
                                         stop_min_atr=k_stop)
        a["sicher"] = ER.hebel_sicher(a["stop"])
        a["h"] = {k: BE.hebelrechnung(quote=q, crv=CRV, kapital_eur=k,
                                      stop_rel=a["stop"], einstellungen=ein,
                                      hebel_sicher=a["sicher"])
                  for k in kapital}
        a["h_ohne"] = {k: BE.hebelrechnung(
            quote=q, crv=CRV, kapital_eur=k, stop_rel=a["stop_ohne"],
            einstellungen=ein, hebel_sicher=ER.hebel_sicher(a["stop_ohne"]))
            for k in kapital}
        durch.append(a)

    # ---- 1. Beitragslage und Durchlass --------------------------------
    print()
    print("1. BEITRAGSLAGE UND DURCHLASS DURCH DIE BEWERTUNG (wie Stufe 11)")
    je_lage = Counter(lage(a) for a in alle)
    je_lage_d = Counter(lage(a) for a in durch)
    for l_ in ("funding + turnover", "nur funding", "nur turnover", "keine"):
        print("  %-20s %8d Anker   durch die Schwelle %8d  (%s)"
              % (l_, je_lage[l_], je_lage_d[l_], pct(je_lage_d[l_], je_lage[l_])))
    print("  gesamt               %8d Anker   durch die Schwelle %8d  (%s)"
          % (len(alle), len(durch), pct(len(durch), len(alle))))
    qs = [a["quote"] for a in durch]
    if qs:
        print("  Quote der Durchgelassenen: Median %s %% · 10 %% %s · 90 %% %s"
              % (de(100 * st.median(qs), 1), de(100 * np.percentile(qs, 10), 1),
                 de(100 * np.percentile(qs, 90), 1)))
        for _f, _t in (("stop", "Betriebsfall (mit Widerlegungspreis)"),
                       ("stop_ohne", "ohne Widerlegungspreis (2,5 x ATR)")):
            ss = [a[_f] for a in durch]
            print("  Stop, %-38s Median %s %% · 10 %% %s · 90 %% %s"
                  % (_t + ":", de(100 * st.median(ss), 1),
                     de(100 * np.percentile(ss, 10), 1),
                     de(100 * np.percentile(ss, 90), 1)))

    # ---- 2. Die Verteilung je Kapital ---------------------------------
    for k in kapital:
        print()
        print("2. VERTEILUNG BEI %s EUR KAPITAL (nur Anker, die die Schwelle passieren)" % de(k, 0))
        hebel = verteilung(durch, k, "alle Durchgelassenen")
        aus = [a for a in durch if a["auswahl"]]
        verteilung(aus, k, "davon Auswahl (oberste %d %%)" % round(100 * arg.anteil))
        for l_ in ("funding + turnover", "nur funding", "nur turnover"):
            z = [a for a in durch if lage(a) == l_]
            if z:
                verteilung(z, k, "   Lage: " + l_)
        if hebel:
            hw = [h["hebel"] for h in hebel]
            rw = [h["risiko_eur"] for h in hebel]
            print("  Hebel, wo einer entsteht: Median %sx · 10 %% %sx · 90 %% %sx · Risiko je Trade Median %s EUR"
                  % (de(st.median(hw), 1), de(np.percentile(hw, 10), 1),
                     de(np.percentile(hw, 90), 1), de(st.median(rw), 0)))
        stufen = Counter()
        for a in durch:
            h = a["h"][k]
            if not h["ist_hebel"]:
                stufen["Spot"] += 1
            else:
                stufen["%dx" % min(5, int(h["hebel"]))] += 1
        print("  Stufen: " + " · ".join("%s %s" % (s, pct(stufen[s], len(durch)))
                                         for s in ("Spot", "2x", "3x", "4x", "5x")))

    # ---- 2b. Empfindlichkeit: ohne Widerlegungspreis --------------------
    print()
    print("2b. EMPFINDLICHKEIT - OHNE Widerlegungspreis (Stop 2,5 x ATR)")
    for k in kapital:
        verteilung(durch, k, "bei %s EUR Kapital" % de(k, 0), feld="h_ohne")

    # ---- 3. Ueber die Zeit ----------------------------------------------
    k_mitte = kapital[len(kapital) // 2]
    print()
    print("3. UEBER DIE ZEIT, bei %s EUR - Anteil Hebel unter den Durchgelassenen" % de(k_mitte, 0))
    je_jahr = defaultdict(list)
    for a in durch:
        je_jahr[a["tag"][:4]].append(a["h"][k_mitte]["ist_hebel"])
    for j in sorted(je_jahr):
        w = je_jahr[j]
        print("  %s  %7d durchgelassen   Hebel %s" % (j, len(w), pct(sum(w), len(w))))
    je_tag_aus = defaultdict(int)
    for a in durch:
        if a["auswahl"] and a["h"][k_mitte]["ist_hebel"]:
            je_tag_aus[a["tag"]] += 1
    werte = [je_tag_aus.get(t, 0) for t in tage]
    print("  Hebelkandidaten je Tag in der Auswahl: Median %s · 90 %% %s · Tage ohne %s"
          % (de(st.median(werte), 1), de(float(np.percentile(werte, 90)), 1),
             pct(sum(1 for w in werte if w == 0), len(werte))))

    # ---- 4. Gegenpruefung -----------------------------------------------
    print()
    print("4. GEGENPRUEFUNG")
    rnd = random.Random(arg.saat)
    fehler = []

    def pruefe(name, ok, info=""):
        print("  %s  %s%s" % ("OK  " if ok else "FEHL", name, ("  - " + info) if info else ""))
        if not ok:
            fehler.append(name)

    stich = rnd.sample(durch, min(2000, len(durch))) if durch else []
    abw = 0
    for a in stich:
        for k in kapital:
            h = a["h"][k]
            kel = (a["quote"] * (1 + CRV) - 1) / CRV
            if kel <= 0:
                exp = (False, 1.0)
            else:
                r = min(max(kel / 2, ein["r_min"]), ein["r_max"])
                roh = r * k / a["stop"] / ein["hebelnenner_eur"]
                mo = min(roh, a["sicher"])
                ist = mo >= ein["hebel_ab"] - 1e-9
                exp = (ist, min(mo, ein["hebel_grenze"]) if ist else 1.0)
            if h["ist_hebel"] != exp[0] or abs(h["hebel"] - exp[1]) > 1e-9:
                abw += 1
    pruefe("G1 Hebel unabhaengig nachgerechnet (%d Anker x %d Kapitalstufen)"
           % (len(stich), len(kapital)), abw == 0, "%d Abweichungen" % abw)
    if len(kapital) >= 2 and durch:
        k0, k1 = kapital[0], kapital[-1]
        faktor = k1 / k0
        bruch = sum(1 for a in durch if a["h"][k0]["hebel_roh"] > 0
                    and abs(a["h"][k1]["hebel_roh"] / a["h"][k0]["hebel_roh"] - faktor) > 1e-9)
        pruefe("G2 der Rohhebel waechst linear mit dem Kapital (Faktor %s)" % de(faktor, 3),
               bruch == 0, "%d Brueche" % bruch)
        anteile = [sum(1 for a in durch if a["h"][k]["ist_hebel"]) for k in kapital]
        pruefe("G3 mehr Kapital, nie weniger Hebelgeschaefte",
               all(anteile[i] <= anteile[i + 1] for i in range(len(anteile) - 1)),
               str(anteile))
    # G4: ATR wie in der Produktion (`rollen_eingabe.atr_bis`)
    from types import SimpleNamespace
    from agent import rollen_eingabe as RE
    abw_atr = 0
    for a in rnd.sample(durch, min(25, len(durch))):
        roh = reihen[a["sym"]]
        idx = [z[0] for z in roh].index(a["tag"])
        kerzen = [SimpleNamespace(high=z[2], low=z[3], close=z[1]) for z in roh[:idx + 1]]
        wert = RE.atr_bis(kerzen, idx)
        if abs(wert - a["atr"]) > 1e-9 * max(1.0, a["atr"]):
            abw_atr += 1
    pruefe("G4 ATR wie `rollen_eingabe.atr_bis` (25 Stichproben)", abw_atr == 0,
           "%d Abweichungen" % abw_atr)
    # G5: Quote aus dem Zwischenspeicher = direkter Aufruf
    abw_q = 0
    for a in rnd.sample(alle, min(50, len(alle))):
        m = {}
        if a["f5"] is not None:
            m["funding_fuenftel"] = a["f5"]
        if a["t5"] is not None:
            m["turnover_fuenftel"] = a["t5"]
        p = PT.rechne(crv=CRV, stop_relativ=0.137, klasse="krypto",
                      instrument="spot", strategie="einstieg", h=None,
                      merkmale=m or None)
        if abs(p.quote - a["quote"]) > 1e-12:
            abw_q += 1
    pruefe("G5 Quote je Beitragslage = direkte Bewertung (50 Stichproben, anderer Stop)",
           abw_q == 0, "%d Abweichungen" % abw_q)
    # G6: der Stop ist der von `rechne()`
    abw_s = 0
    for a in rnd.sample(durch, min(50, len(durch))):
        for _umg, _feld in ((a["kurs"] * (1.0 - THESE_ABSTAND), "stop"),
                            (None, "stop_ohne")):
            r = ER.rechne(kurs=a["kurs"], atr=a["atr"], risiko_eur=48.0,
                          betrag_wunsch_eur=800.0, stop_min_atr=k_stop,
                          umgeworfen_preis_eur=_umg,
                          hebel_handelbar=False, assetklasse="krypto")
            if abs(r["stop_relativ"] - round(a[_feld], 5)) > 1e-5:
                abw_s += 1
    pruefe("G6 Stop = `rechne()`, mit und ohne Widerlegungspreis (50 x 2)",
           abw_s == 0, "%d Abweichungen" % abw_s)
    print()
    print("GEGENPRUEFUNG: %s" % ("alle bestanden" if not fehler else "FEHLGESCHLAGEN: %s" % fehler))
    return 0 if not fehler else 1


if __name__ == "__main__":
    raise SystemExit(main())
