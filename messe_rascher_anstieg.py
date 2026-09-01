# -*- coding: utf-8 -*-
"""Trennt ein Merkmal den RASCHEN ANSTIEG? (01.09.2026)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

## Die Frage, und warum sie neu ist

Nutzervorgabe 01.09.: *„Hebel ist fuer kurzfristige Trades gedacht und auch
nur dort anzuwenden. Das System MUSS auf Basis der Wahrscheinlichkeit und des
Potentials entscheiden, ob ein rascher schneller Anstieg zu erwarten ist -
und nur dann ist ein Hebel sinnvoll."* Praezisiert: *„1-3 Tage ist relativ
rasch. Optimal waere ein Einstieg VOR der Bewegung."*

⚠️ **DAS IST EINE ECHTE LUECKE, nichts Vorhandenes.** Geprueft am 01.09.:
`Anforderungen_Umbau_28_08.md` legt fuer `hebel x einstieg` dasselbe
Erfolgsmass fest wie fuer Spot ("Ziel vor Stop"). Die Unterscheidung nach
GESCHWINDIGKEIT steht in keinem Plandokument - solange der Hebel als "Spot
mit Faktor" galt (Kapitel 88), stellte sich die Frage nicht.

## Was hier ANDERS gefragt wird als in allen bisherigen Messungen

    bisher   Median der Bewegung ueber H Tage   "wie weit im Mittel"
    HIER     Anteil mit Bewegung > 1,0 R in 3   "kommt ein SPRUNG"

**Der Median verdeckt genau das, was den Hebel rechtfertigt.** Ein Asset kann
im Median +0,0 R machen und in 16 % der Faelle +1,0 R springen. Fuer Spot ist
der Median richtig, fuer den Hebel der Ausschlag.

⚠️ Und damit ist der Grundbefund vom 10.08. NICHT beruehrt: *„die Information
steckt nicht in den Kursdaten"* beruht auf Median-Messungen. Er schliesst
nicht aus, dass Merkmale die AUSSCHLAEGE trennen.

## Die Zielgroesse - und warum 1,0 R

    Treffer = (Kurs[t+3] - Kurs[t]) / R  >  1,0
    R       = mittlere Tagesspanne der letzten 14 Handelstage

Gemessen am 01.09. an 370.207 Ankern:

    Schwelle   Basisrate   Faelle je Fuenftel und Kalendertag
     +1,0 R      16,5 %       ~5
     +1,5 R       9,3 %       ~2      <- zu duenn fuer einen Wert je Tag
     +2,0 R       5,4 %       ~1

**1,0 R ist aus MAECHTIGKEIT gewaehlt, nicht weil es die beste Zahl waere.**
Bei 1,5 R bleiben zwei Treffer je Fuenftel und Tag - daraus laesst sich kein
stabiler Wert bilden, und ein Nullbefund waere nicht deutbar.

In Euro heisst 1,0 R binnen 3 Tagen: BTC +2,19 %, ETH +3,05 %, TAO +4,13 %.

## ⚠️⚠️ ZWEI FALLSTRICKE, beide vorab benannt

**1 KEIN MEDIAN AUF EINER 0/1-GROESSE.** `messe_regel_wirksamkeit.wirkung()`
rechnet `np.median(y[frei]) - np.median(y)`. Bei einer binaeren Zielgroesse
kann der Median je Tag nur 0 oder 1 sein. **Hier wird die QUOTE gerechnet,
also der Mittelwert.**

⚠️ PRAEZISIERT AM 01.09. NACH DER KUNSTDATENPROBE - meine erste Fassung
dieses Absatzes war zu scharf. Ich hatte geschrieben, der Median waere
"fast immer exakt null". Gegen Kunstdaten mit gepflanztem Effekt gemessen:

    gepflanzt +0,20 im besten Fuenftel
      QUOTE  +0,1315      MEDIAN  +0,1758

Der Median ist NICHT blind - ueber viele Kalendertage gemittelt zeigt er
an, an wie vielen Tagen die Mehrheit traf. Er ist nur GROB: je Tag kennt er
zwei Werte statt einer stetigen Quote, und bei kleineren Effekten verliert
er die Aufloesung. Die Quote ist die feinere Groesse, nicht die einzig
moegliche.

Der Fehler vom 30.08. bleibt davon unberuehrt: dort war die Zielgroesse
"Ziel vor Stop" innerhalb von BLOECKEN gemittelt, nicht ueber Tage - und
dort ergab der Median tatsaechlich +0,0000 in jedem Block.

**2 DIE VOLATILITAET IST EIN CONFOUNDER - und zwar umgekehrt als erwartet.**
Gemessen am 01.09.:

    Volatilitaets-Fuenftel   R/Kurs    Trefferquote +1,0 R
      0 (ruhig)              1,51 %       **24,0 %**
      4 (wild)              13,58 %        **9,3 %**

**Ruhige Werte springen HAEUFIGER ueber 1,0 R als wilde** - sie laufen
stetiger, waehrend wilde hin und her schwanken. Ein Merkmal, das mit Ruhe
korreliert, saehe deshalb wie ein Treffer aus. Der Rangvergleich je
Kalendertag haelt die MARKTLAGE konstant, nicht die ASSET-Volatilitaet -
deshalb laeuft sie hier als eigene Kontrolle mit.

## Vorab festgelegt - was als Befund gilt

  traegt         Quotenvorsprung > 0, ausserhalb des Placebo-Bandes, beide
                 Historienhaelften gleiches Vorzeichen, UND er bleibt
                 innerhalb der Volatilitaetsklassen bestehen
  Confounder     er verschwindet, sobald die Volatilitaet konstant gehalten
                 wird -> dann misst er Ruhe, nicht Signal
  traegt nicht   sonst

    python messe_rascher_anstieg.py
"""
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

import messe_eigenschaft_beitrag as B                          # noqa: E402

HORIZONT = 3
SCHWELLE_R = 1.0
MIND_JE_TAG = 15
PLACEBO = 40
RUECKBLICK = 252


def baue(reihen, menge=None, funding=None):
    """Je Anker: Merkmale, Treffer (0/1) und die Volatilitaet."""
    je_tag = {}
    for sym, roh in reihen.items():
        tage = [z[0] for z in roh]
        c = np.array([z[1] for z in roh])
        h = np.array([z[2] for z in roh])
        t_ = np.array([z[3] for z in roh])
        v = np.array([z[4] for z in roh])
        breite = B.spanne(h, t_, c, B.SCHWANKUNG)
        umsatz = v * c
        rendite = np.zeros(len(c))
        rendite[1:] = np.abs(c[1:] / np.maximum(c[:-1], 1e-12) - 1.0)
        f_je = (funding or {}).get(sym.upper()) or {}
        m_je = (menge or {}).get(sym.upper()) or {}
        for i in range(RUECKBLICK + 40, len(c) - HORIZONT):
            r = breite[i]
            if not np.isfinite(r) or r <= 0 or c[i] <= 0:
                continue
            e = {"sym": sym,
                 # ⚠️ DIE ZIELGROESSE IST BINAER - deshalb QUOTE, nie Median.
                 "treffer": 1.0 if (c[i + HORIZONT] - c[i]) / r > SCHWELLE_R
                            else 0.0,
                 # der Confounder, als eigene Spalte
                 "vola": float(r / c[i])}
            fw = f_je.get(tage[i])
            if fw is not None:
                e["funding"] = float(fw)
            mw = m_je.get(tage[i])
            if mw and mw > 0:
                e["turnover"] = float(v[i] / mw)
            u = umsatz[i - RUECKBLICK:i]
            rr = rendite[i - RUECKBLICK:i]
            gut = u > 0
            if gut.sum() >= RUECKBLICK // 2:
                e["amihud"] = float(np.mean(rr[gut] / u[gut]) * 1e9)
            if c[i - 252] > 0:
                e["momentum"] = float(c[i - 21] / c[i - 252] - 1.0)
            if i >= 200 and c[i - 200:i].mean() > 0:
                e["schnitt"] = float(c[i] / c[i - 200:i].mean() - 1.0)
            je_tag.setdefault(tage[i], []).append(e)
    return {t: z for t, z in je_tag.items() if len(z) >= MIND_JE_TAG}


def _rang(werte):
    return np.argsort(np.argsort(np.asarray(werte, float))) / max(
        len(werte) - 1, 1)


def wirkung(je_tag, merkmal, oben_gut=True, mische=None, pflanze=0.0,
            nur=None):
    """Je Kalendertag: QUOTE im besten Fuenftel minus Quote insgesamt.

    ⚠️ QUOTE, NICHT MEDIAN. Die Zielgroesse ist 0/1 - ein Median waere
    fast immer exakt null und der Befund unlesbar (Fehler vom 30.08.).
    """
    aus = {}
    for tag, z in je_tag.items():
        w = [x for x in z if merkmal in x and (nur is None or nur(x))]
        if len(w) < MIND_JE_TAG:
            continue
        r = _rang([x[merkmal] for x in w])
        if mische is not None:
            r = mische.permutation(r)
        y = np.array([x["treffer"] for x in w])
        if pflanze:
            gut = (r >= 0.8) if oben_gut else (r < 0.2)
            y = y.copy()
            y[gut] = np.minimum(1.0, y[gut] + pflanze)
        beste = (r >= 0.8) if oben_gut else (r < 0.2)
        if beste.sum() < 3:
            continue
        aus[tag] = float(y[beste].mean() - y.mean())
    return aus


def urteil(name, je_tag, merkmal, rng, oben_gut=True, mit_kontrollen=True,
           nur=None, klar=""):
    d = wirkung(je_tag, merkmal, oben_gut, nur=nur)
    if len(d) < 100:
        print("  %-34s zu wenige Tage (%d)" % (name, len(d)))
        return None
    werte = np.array(list(d.values()))
    n = len(werte)
    # Blockbootstrap ueber Kalendertage (Block > Horizont)
    tage = sorted(d)
    bl = 20
    bloecke = [tage[i:i + bl] for i in range(0, len(tage), bl)]
    zieh = []
    for _ in range(400):
        w = []
        for _b in range(len(bloecke)):
            for t in bloecke[rng.integers(len(bloecke))]:
                w.append(d[t])
        zieh.append(float(np.mean(w)))
    u, o = np.quantile(zieh, [0.025, 0.975])
    traegt = u > 0
    print("  %-34s %+7.4f  [%+.4f .. %+.4f]  %4d Tage  %s"
          % (name, float(werte.mean()), u, o, n,
             "TRAEGT" if traegt else ("UMGEKEHRT" if o < 0
                                      else "nicht trennbar")))
    if not mit_kontrollen:
        return float(werte.mean())
    # Negativkontrolle: Rang je Tag gemischt
    p = []
    for _ in range(min(PLACEBO, 20)):
        dd = wirkung(je_tag, merkmal, oben_gut, mische=rng, nur=nur)
        if dd:
            p.append(float(np.mean(list(dd.values()))))
    if p:
        print("  %-34s %+7.4f  (Placebo-Band %+.4f .. %+.4f)"
              % ("  Negativkontrolle", float(np.mean(p)),
                 float(np.quantile(p, 0.025)), float(np.quantile(p, 0.975))))
    # Positivkontrolle: gepflanzter Effekt
    for s in (0.05, 0.10):
        dd = wirkung(je_tag, merkmal, oben_gut, pflanze=s, nur=nur)
        if dd:
            print("  %-34s %+7.4f  (gepflanzt +%.2f)"
                  % ("  Positivkontrolle", float(np.mean(list(dd.values()))),
                     s))
    # beide Historienhaelften
    mitte = tage[len(tage) // 2]
    for kl, teil in (("  erste Haelfte", [t for t in tage if t < mitte]),
                     ("  zweite Haelfte", [t for t in tage if t >= mitte])):
        w = [d[t] for t in teil]
        if w:
            print("  %-34s %+7.4f  (%d Tage)" % (kl, float(np.mean(w)),
                                                 len(w)))
    return float(werte.mean())


def main():
    print("Lade Reihen...", flush=True)
    reihen = B.lade()
    import sqlite3
    funding = {}
    try:
        c = sqlite3.connect("file:data/funding_historie.db?mode=ro", uri=True)
        for s, d, w in c.execute("SELECT symbol,datum,wert FROM funding"):
            funding.setdefault(str(s).upper(), {})[str(d)[:10]] = float(w)
        c.close()
    except Exception as exc:                                 # noqa: BLE001
        print("⚠️ Funding nicht lesbar: %s" % str(exc)[:60])
    menge = {}
    try:
        import messe_bewertungskennzahl as MB
        menge = MB.reihe("data/onchain_historie.db", "splycur")
    except Exception as exc:                                 # noqa: BLE001
        print("⚠️ Umlaufmenge nicht lesbar: %s" % str(exc)[:60])

    je_tag = baue(reihen, menge, funding)
    alle = [x for z in je_tag.values() for x in z]
    quote = st.mean([x["treffer"] for x in alle])
    print("%d Anker, %d Kalendertage, Basisrate %.1f %%"
          % (len(alle), len(je_tag), 100 * quote))

    print()
    print("=" * 96)
    print("TRENNT EIN MERKMAL DEN RASCHEN ANSTIEG? (> %.1f R binnen %d Tagen)"
          % (SCHWELLE_R, HORIZONT))
    print("=" * 96)
    print("  Gerechnet wird die QUOTE im besten Fuenftel minus Gesamtquote,")
    print("  je Kalendertag. ⚠️ NICHT der Median - die Zielgroesse ist 0/1.")
    print()
    rng = np.random.default_rng(20260901)
    ergebnis = {}
    for merkmal, name, oben in (
            ("funding", "FUNDING-Rang (tief = gut)", False),
            ("turnover", "TURNOVER-Rang", True),
            ("vola", "⚠️ VOLATILITAET (Kontrollgroesse)", False),
            ("amihud", "Amihud-Illiquiditaet", True),
            ("momentum", "Momentum 12-1", True),
            ("schnitt", "Abstand zum 200-Schnitt", False)):
        print()
        ergebnis[merkmal] = urteil(name, je_tag, merkmal, rng, oben_gut=oben)

    # ---- die Confounder-Probe ---------------------------------------
    print()
    print("=" * 96)
    print("⚠️ DIE CONFOUNDER-PROBE — haelt der Befund innerhalb einer")
    print("   Volatilitaetsklasse? (ruhig traf 24,0 %, wild 9,3 %)")
    print("=" * 96)
    vs = sorted(x["vola"] for x in alle)
    g1, g2 = vs[len(vs) // 3], vs[2 * len(vs) // 3]
    for merkmal, name, oben in (("funding", "FUNDING", False),
                                ("turnover", "TURNOVER", True)):
        if ergebnis.get(merkmal) is None:
            continue
        print()
        for kl, bed in (("ruhiges Drittel", lambda x: x["vola"] <= g1),
                        ("mittleres Drittel",
                         lambda x: g1 < x["vola"] <= g2),
                        ("wildes Drittel", lambda x: x["vola"] > g2)):
            urteil("%s / %s" % (name, kl), je_tag, merkmal, rng,
                   oben_gut=oben, mit_kontrollen=False, nur=bed)


if __name__ == "__main__":
    main()
