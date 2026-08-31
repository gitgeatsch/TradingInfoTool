# -*- coding: utf-8 -*-
"""R-B: Traegt eine NICHT-KURS-Groesse als Bewertungsbeitrag? (30.08.2026)

Ein Werkzeug fuer alle Kandidaten der Optionsliste - TVL, Funding, aktive
Adressen, Gebuehren. Der Aufbau ist derselbe, der an diesem Tag viermal
gehalten hat; nur die Reihe wechselt.

## ⚠️ ZWEI VARIANTEN, UND NUR EINE IST DER KANDIDAT

    ABSOLUT       "dieses Protokoll hat viel TVL"        -> EIGENSCHAFT
    VERAENDERUNG  "bei diesem Protokoll waechst es"      -> LAGE

Sieben Asset-EIGENSCHAFTEN wurden geprueft (Volumen, Groesse, Volatilitaet,
Liquiditaet, Alter, Beta, Kapitalisierung) - **keine einzige traegt**. Drei
LAGE-Merkmale wurden geprueft, alle drei zeigten etwas. Der Kandidat ist
deshalb die VERAENDERUNG.

Die absolute Variante laeuft trotzdem mit - als eingebaute Kontrolle: traegt
sie staerker als die Veraenderung, stimmt etwas nicht (dann misst man
vermutlich Groesse, und die ist siebenmal widerlegt).

## Der Aufbau (unveraendert gegenueber den Laeufen vom 29.08.)

  Rangplatz QUER ueber die Assets desselben Kalendertags -> Marktlage fest
  Zielgroesse: Bewegung ueber H Handelstage, geteilt durch die eigene
               Schwankungsbreite (in R)
  Effektgroesse: MEDIAN des obersten minus unterstes Terzil - nie Mittelwert
               (Schiefe 2,68; Token-Umstellungen erzeugen Ausreiszer)
  Kontrolle: Bootstrap ueber die REIHEN, nicht ueber die Anker

## Vorab festgelegt, VOR dem ersten Lauf

  traegt        Bootstrap-Intervall ueber die Reihen schliesst die Null nicht
                ein, UND der Befund haelt in beiden Haelften der Historie,
                UND die Negativkontrolle liegt bei null
  traegt nicht  sonst
  ⚠️ Ein Befund, der nur in der ersten Haelfte haelt, gilt als NICHT tragend.
     Das ist an diesem Tag dreimal vorgekommen (Lage-Beitrag, K-1, R-A) und
     war jedesmal das Ende des Befunds.
"""
import sqlite3
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B

VERAENDERUNG_TAGE = 30
MIND_JE_TAG = 12
HORIZONTE = (5, 20, 60)


def lade_fremdreihe(db, tabelle, wertspalte, symbolspalte="symbol",
                    datumsspalte="datum"):
    """{symbol: {datum: wert}} aus einer beliebigen Messdatei."""
    conn = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    aus = {}
    for sym, tag, wert in conn.execute(
            "SELECT %s, %s, %s FROM %s WHERE %s IS NOT NULL"
            % (symbolspalte, datumsspalte, wertspalte, tabelle, wertspalte)):
        aus.setdefault(str(sym).upper(), {})[str(tag)[:10]] = float(wert)
    conn.close()
    return aus


def baue(reihen, fremd, horizont):
    """Je Kalendertag: absoluter Wert, Veraenderung, Bewegung in R."""
    je_tag = {}
    for sym, roh in reihen.items():
        werte = fremd.get(sym.upper())
        if not werte or len(werte) < VERAENDERUNG_TAGE + 30:
            continue
        tage = [z[0] for z in roh]
        schluss = np.array([z[1] for z in roh])
        hoch = np.array([z[2] for z in roh])
        tief = np.array([z[3] for z in roh])
        breite = B.spanne(hoch, tief, schluss, B.SCHWANKUNG)
        sortiert = sorted(werte)
        lage = {t: i for i, t in enumerate(sortiert)}
        for i in range(60, len(schluss) - horizont):
            r = breite[i]
            if not np.isfinite(r) or r <= 0:
                continue
            tag = tage[i]
            if tag not in lage:
                continue
            j = lage[tag]
            if j < VERAENDERUNG_TAGE:
                continue
            jetzt = werte[sortiert[j]]
            vorher = werte[sortiert[j - VERAENDERUNG_TAGE]]
            if jetzt <= 0 or vorher <= 0:
                continue
            je_tag.setdefault(tag, []).append({
                "sym": sym,
                "absolut": jetzt,
                "veraenderung": jetzt / vorher - 1.0,
                "in_r": float((schluss[i + horizont] - schluss[i]) / r)})
    return {t: z for t, z in je_tag.items() if len(z) >= MIND_JE_TAG}


def terzile(werte):
    r = np.argsort(np.argsort(np.asarray(werte, float)))
    return np.clip((r / max(len(r) - 1, 1) * 3).astype(int), 0, 2)


def je_reihe(je_tag, merkmal, mische=None):
    """Je Symbol: Median(oberstes Terzil) minus Median(unterstes) ueber alle Tage."""
    oben, unten = {}, {}
    for z in je_tag.values():
        t = terzile([x[merkmal] for x in z])
        if mische is not None:
            t = mische.permutation(t)
        for x, k in zip(z, t):
            if k == 2:
                oben.setdefault(x["sym"], []).append(x["in_r"])
            elif k == 0:
                unten.setdefault(x["sym"], []).append(x["in_r"])
    aus = {}
    for sym in set(oben) & set(unten):
        if len(oben[sym]) >= 20 and len(unten[sym]) >= 20:
            aus[sym] = st.median(oben[sym]) - st.median(unten[sym])
    return aus


def urteil(titel, werte, rng):
    if len(werte) < 10:
        print("    %-32s zu wenige Reihen (%d)" % (titel, len(werte)))
        return None
    w = np.array(list(werte.values()))
    n = len(w)
    boot = np.array([w[rng.integers(0, n, n)].mean() for _ in range(20000)])
    u, o = np.quantile(boot, [0.025, 0.975])
    haelt = u > 0 or o < 0
    print("    %-32s %+.4f R  [%+.4f .. %+.4f]  %3d/%3d positiv  %s"
          % (titel, w.mean(), u, o, int((w > 0).sum()), n,
             "TRAEGT" if haelt else "nicht trennbar"))
    return haelt


def laufe(name, db, tabelle, wertspalte, **spalten):
    reihen = B.lade()
    fremd = lade_fremdreihe(db, tabelle, wertspalte, **spalten)
    print("=" * 92)
    print("R-B — TRAEGT %s ALS BEWERTUNGSBEITRAG?" % name.upper())
    print("=" * 92)
    print("Fremdreihe: %d Symbole  ·  Veraenderung ueber %d Tage  ·  "
          "Effektgroesse = Median oberstes minus unterstes Terzil"
          % (len(fremd), VERAENDERUNG_TAGE))
    rng = np.random.default_rng(20260830)
    for horizont in HORIZONTE:
        je_tag = baue(reihen, fremd, horizont)
        if not je_tag:
            print("\nHORIZONT %d: keine Ueberschneidung" % horizont)
            continue
        n = sum(len(z) for z in je_tag.values())
        symbole = len({x["sym"] for z in je_tag.values() for x in z})
        print()
        print("-" * 92)
        print("HORIZONT %d Handelstage — %d Anker, %d Symbole, %d Kalendertage"
              % (horizont, n, symbole, len(je_tag)))
        print("-" * 92)
        for merkmal, klar in (("veraenderung", "VERAENDERUNG (der Kandidat)"),
                              ("absolut", "absolut (Kontrolle: Eigenschaft)")):
            urteil(klar, je_reihe(je_tag, merkmal), rng)
        urteil("Negativkontrolle (gemischt)",
               je_reihe(je_tag, "veraenderung", rng), rng)
        # Zeitstabilitaet nur fuer den Kandidaten
        tage = sorted(je_tag)
        mitte = tage[len(tage) // 2]
        for titel, teil in (("davon erste Haelfte",
                             {t: z for t, z in je_tag.items() if t < mitte}),
                            ("davon zweite Haelfte",
                             {t: z for t, z in je_tag.items() if t >= mitte})):
            urteil(titel, je_reihe(teil, "veraenderung"), rng)


QUELLEN = {
    "tvl": ("TVL", "data/tvl_historie.db", "tvl_historie", "tvl_usd"),
    "adressen": ("AKTIVE ADRESSEN", "data/onchain_historie.db", "adractcnt", "wert"),
    "funding": ("FUNDING-RATE", "data/funding_historie.db", "funding", "wert"),
}


def positivkontrolle(name, db, tabelle, wertspalte, staerke=0.15):
    """Findet das Werkzeug einen EINGEPFLANZTEN Effekt dieser Groesse?

    Pflicht bei jedem Nullbefund: sonst heisst "nichts gefunden" nur
    "nicht hingesehen". Gepflanzt wird auf das oberste Terzil der
    VERAENDERUNG - also genau dort, wo ein echter Beitrag saesse.
    """
    reihen = B.lade()
    fremd = lade_fremdreihe(db, tabelle, wertspalte)
    rng = np.random.default_rng(4711)
    print()
    print("=" * 92)
    print("POSITIVKONTROLLE %s — findet das Werkzeug %+.2f R?" % (name, staerke))
    print("=" * 92)
    je_tag = baue(reihen, fremd, 20)
    for z in je_tag.values():
        t = terzile([x["veraenderung"] for x in z])
        for x, k in zip(z, t):
            if k == 2:
                x["in_r"] += staerke
    urteil("gepflanzt auf oberstes Terzil", je_reihe(je_tag, "veraenderung"), rng)


if __name__ == "__main__":
    was = sys.argv[1] if len(sys.argv) > 1 else "tvl"
    name, db, tabelle, spalte = QUELLEN[was]
    laufe(name, db, tabelle, spalte)
    if len(sys.argv) > 2 and sys.argv[2] == "kontrolle":
        for s in (0.05, 0.10, 0.15):
            positivkontrolle(name, db, tabelle, spalte, s)
