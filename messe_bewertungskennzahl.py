# -*- coding: utf-8 -*-
"""Die dritte Kategorie: traegt eine BEWERTUNGSkennzahl? (30.08.2026)

## Warum dieses Werkzeug noetig wurde

Nutzerfrage: *"warum liefern TVL und aktive Adressen keine Aussage, werden
diese nicht in der Praxis angewendet?"* - und sie trifft. Gemessen wurde die
VERAENDERUNG der Rohgroesse. Die Praxis nutzt durchgehend VERHAELTNISSE:

    MC/TVL   Marktkapitalisierung / hinterlegtes Kapital   "teuer je Kapital"
    NVM      Marktkapitalisierung / (aktive Adressen)^2    Metcalfe
    NVT      Marktkapitalisierung / Transaktionswert       Preis gegen Nutzung

Das Projekt hatte bis dahin nur zwei Kategorien geprueft:

    EIGENSCHAFT  "was IST dieses Asset"        7 geprueft, keine traegt
    LAGE         "wo STEHT es gerade"          3 geprueft, alle zeigten etwas
    BEWERTUNG    "ist es TEUER oder BILLIG"    ⚠️ nie geprueft

Die dritte ist die, auf der die klassische Fundamentalanalyse ruht.

## Die Leserichtung - und warum sie umgedreht ist

Bei Lage-Merkmalen war "hoher Wert besser?" die Frage. Hier ist es umgekehrt:
ein NIEDRIGES Verhaeltnis heisst GUENSTIG. Ausgegeben wird deshalb

    Median(unterstes Terzil) minus Median(oberstes Terzil)

Ein POSITIVER Wert heisst: die guenstigen Werte liefen besser - die Kennzahl
traegt in der Richtung, die die Praxis behauptet.

## Vorab festgelegt, VOR dem Lauf

  traegt        Bootstrap ueber die Reihen schliesst die Null nicht ein, UND
                der Befund haelt in beiden Haelften, UND die Negativkontrolle
                liegt bei null
  traegt nicht  sonst
  ⚠️ Ein NEGATIVES Vorzeichen waere ebenfalls ein Befund - dann waeren teure
     Werte die besseren, und die Praxislesart stuende auf dem Kopf.
"""
import sqlite3
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B

MIND_JE_TAG = 10
HORIZONTE = (5, 20, 60)


def reihe(db, tabelle, spalte="wert"):
    conn = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    aus = {}
    for sym, tag, wert in conn.execute(
            "SELECT symbol, datum, %s FROM %s WHERE %s IS NOT NULL"
            % (spalte, tabelle, spalte)):
        aus.setdefault(str(sym).upper(), {})[str(tag)[:10]] = float(wert)
    conn.close()
    return aus


def baue(reihen, menge, nenner, horizont, quadrat=False):
    """Je Kalendertag: Bewertungskennzahl und Bewegung in R."""
    je_tag = {}
    for sym, roh in reihen.items():
        s = sym.upper()
        if s not in menge or s not in nenner:
            continue
        tage = [z[0] for z in roh]
        schluss = np.array([z[1] for z in roh])
        hoch = np.array([z[2] for z in roh])
        tief = np.array([z[3] for z in roh])
        breite = B.spanne(hoch, tief, schluss, B.SCHWANKUNG)
        for i in range(60, len(schluss) - horizont):
            r = breite[i]
            if not np.isfinite(r) or r <= 0:
                continue
            tag = tage[i]
            m = menge.get(s, {}).get(tag)
            n = nenner.get(s, {}).get(tag)
            if not m or not n or m <= 0 or n <= 0:
                continue
            kap = schluss[i] * m                      # Marktkapitalisierung
            teiler = n * n if quadrat else n
            je_tag.setdefault(tag, []).append({
                "sym": sym,
                "kennzahl": kap / teiler,
                "in_r": float((schluss[i + horizont] - schluss[i]) / r)})
    return {t: z for t, z in je_tag.items() if len(z) >= MIND_JE_TAG}


def terzile(werte):
    r = np.argsort(np.argsort(np.asarray(werte, float)))
    return np.clip((r / max(len(r) - 1, 1) * 3).astype(int), 0, 2)


def je_reihe(je_tag, mische=None, pflanze=0.0):
    """Je Symbol: Median(guenstig) minus Median(teuer)."""
    guenstig, teuer = {}, {}
    for z in je_tag.values():
        t = terzile([x["kennzahl"] for x in z])
        if mische is not None:
            t = mische.permutation(t)
        for x, k in zip(z, t):
            if k == 0:                                # niedrigste Kennzahl
                guenstig.setdefault(x["sym"], []).append(x["in_r"] + pflanze)
            elif k == 2:
                teuer.setdefault(x["sym"], []).append(x["in_r"])
    aus = {}
    for sym in set(guenstig) & set(teuer):
        if len(guenstig[sym]) >= 20 and len(teuer[sym]) >= 20:
            aus[sym] = st.median(guenstig[sym]) - st.median(teuer[sym])
    return aus


def je_tag_quer(je_tag, mische=None, pflanze=0.0):
    """QUERSCHNITT: je Kalendertag guenstig minus teuer - ueber ALLE Symbole.

    ⚠️ Warum diese Variante noetig ist (30.08.2026): `je_reihe` verlangt, dass
    ein Symbol in BEIDEN Terzilen vorkommt. Bei einer Kennzahl, die je Symbol
    stabil ist - und MC/TVL ist das -, passiert das fast nie: von 19 Symbolen
    blieben 4. Die Praxis meint aber genau den Querschnitt: "kaufe die
    guenstigsten Protokolle", nicht "kaufe dieses, wenn es fuer sich selbst
    guenstig steht".

    Die ehrliche Einheit bleibt der KALENDERTAG (Methodik 2.84) - Krypto laeuft
    synchron, Symbole sind keine unabhaengigen Ziehungen.
    """
    aus = {}
    for tag, z in je_tag.items():
        t = terzile([x["kennzahl"] for x in z])
        if mische is not None:
            t = mische.permutation(t)
        g = [x["in_r"] + pflanze for x, k in zip(z, t) if k == 0]
        te = [x["in_r"] for x, k in zip(z, t) if k == 2]
        if len(g) >= 3 and len(te) >= 3:
            aus[tag] = st.median(g) - st.median(te)
    return aus


def urteil_tage(titel, werte, rng, block=30):
    """Bootstrap ueber BLOECKE von Kalendertagen - benachbarte Tage haengen zusammen."""
    if len(werte) < 60:
        print("    %-34s zu wenige Tage (%d)" % (titel, len(werte)))
        return None
    tage = sorted(werte)
    bl = [np.array([werte[t] for t in tage[i:i + block]])
          for i in range(0, len(tage), block)]
    mittel = np.array([b.mean() for b in bl])
    n = len(mittel)
    boot = np.array([mittel[rng.integers(0, n, n)].mean() for _ in range(20000)])
    u, o = np.quantile(boot, [0.025, 0.975])
    w = np.array(list(werte.values()))
    urteil = "TRAEGT" if u > 0 else ("UMGEKEHRT" if o < 0 else "nicht trennbar")
    # ⚠️⚠️ ZU WENIGE BLOECKE - DAS BAND DECKT DANN NICHT (01.09.2026).
    #
    # Gemessen an reinem Rauschen, 200 Wiederholungen je Zeile:
    #
    #      5 Bloecke  ->  19,5 %  Fehlalarme      (nominal 5 %)
    #     12 Bloecke  ->  10,0 %
    #     14 Bloecke  ->   6,5 %
    #     34 Bloecke  ->   2,5 %
    #
    # Der Bootstrap zieht `n` Blockmittel aus `n` Blockmitteln. Bei n=5 ist
    # die Bootstrap-Verteilung so grob, dass das 95-%-Band systematisch zu
    # eng ausfaellt - jede vierte reine Rauschgroesse erscheint dann als
    # Befund. Gefunden hat es der Selbsttest von `messe_form_kurz_gegen_-
    # lang.py`, nicht eine Ueberlegung: dort feuerten 5 von 20 Rauschgroessen.
    #
    # ⚠️ Die Blockgroesse darf NICHT einfach verkleinert werden, um mehr
    # Bloecke zu bekommen - sie muss laenger sein als die Abhaengigkeit im
    # Ertrag (Vorgabe: 3 x Horizont). Wer zu kleine Bloecke nimmt, tauscht
    # ein zu enges Band gegen ein zu enges Band aus anderem Grund. Der
    # richtige Weg ist mehr Kalendertage - oder die Zahl ehrlich als
    # untermaechtig auszuweisen.
    if n < 20:
        print("    %-34s ⚠️ NUR %d BLOECKE - das Band deckt nicht "
              "(bei 5 Bloecken 19,5 %% Fehlalarme statt 5 %%). "
              "Dieses Urteil ist untermaechtig." % ("", n))
    print("    %-34s %+.4f R  [%+.4f .. %+.4f]  %3d/%3d Tage +  %s"
          % (titel, w.mean(), u, o, int((w > 0).sum()), len(w), urteil))
    # ⚠️ GIBT DAS URTEIL JETZT AUCH ZURUECK (01.09.2026). Bis hierher hat
    # diese Funktion es nur GEDRUCKT - wer es weiterverarbeiten wollte,
    # musste die Zahlen ein zweites Mal rechnen, und damit haette es zwei
    # Bootstrap-Implementierungen gegeben, die auseinanderlaufen koennen.
    # Bestehende Aufrufer ignorieren den Rueckgabewert und aendern sich
    # nicht.
    return {"mittel": float(w.mean()), "unten": float(u), "oben": float(o),
            "tage": len(w), "tage_positiv": int((w > 0).sum()),
            "urteil": urteil, "traegt": bool(u > 0)}


def urteil(titel, werte, rng):
    if len(werte) < 8:
        print("    %-34s zu wenige Reihen (%d)" % (titel, len(werte)))
        return
    w = np.array(list(werte.values()))
    n = len(w)
    boot = np.array([w[rng.integers(0, n, n)].mean() for _ in range(20000)])
    u, o = np.quantile(boot, [0.025, 0.975])
    print("    %-34s %+.4f R  [%+.4f .. %+.4f]  %3d/%3d positiv  %s"
          % (titel, w.mean(), u, o, int((w > 0).sum()), n,
             "TRAEGT" if u > 0 else ("UMGEKEHRT" if o < 0 else "nicht trennbar")))


def laufe(name, menge, nenner, quadrat=False):
    reihen = B.lade()
    rng = np.random.default_rng(20260830)
    print("=" * 94)
    print("BEWERTUNGSKENNZAHL: %s" % name)
    print("=" * 94)
    print("Gelesen wird: GUENSTIG (niedrigstes Terzil) minus TEUER (hoechstes).")
    print("Ein POSITIVER Wert bestaetigt die Praxislesart.")
    for horizont in HORIZONTE:
        je_tag = baue(reihen, menge, nenner, horizont, quadrat)
        if not je_tag:
            print("\nHORIZONT %d: keine Ueberschneidung" % horizont)
            continue
        n = sum(len(z) for z in je_tag.values())
        syms = len({x["sym"] for z in je_tag.values() for x in z})
        print()
        print("-" * 94)
        print("HORIZONT %d — %d Anker, %d Symbole, %d Kalendertage"
              % (horizont, n, syms, len(je_tag)))
        print("-" * 94)
        print("  QUERSCHNITT — die Form, die die Praxis meint")
        urteil_tage("guenstig minus teuer", je_tag_quer(je_tag), rng)
        urteil_tage("Negativkontrolle (gemischt)", je_tag_quer(je_tag, rng), rng)
        tage = sorted(je_tag)
        mitte = tage[len(tage) // 2]
        urteil_tage("davon erste Haelfte",
                    je_tag_quer({t: z for t, z in je_tag.items() if t < mitte}), rng)
        urteil_tage("davon zweite Haelfte",
                    je_tag_quer({t: z for t, z in je_tag.items() if t >= mitte}), rng)
        if horizont == 20:
            for s in (0.05, 0.10):
                urteil_tage("Positivkontrolle %+.2f R" % s,
                            je_tag_quer(je_tag, pflanze=s), rng)
        print("  JE REIHE — dasselbe Symbol ueber die Zeit (Kontrollsicht)")
        urteil("guenstig minus teuer", je_reihe(je_tag), rng)


if __name__ == "__main__":
    menge = reihe("data/onchain_historie.db", "splycur")
    was = sys.argv[1] if len(sys.argv) > 1 else "mctvl"
    if was == "mctvl":
        laufe("MC / TVL", menge, reihe("data/tvl_historie.db", "tvl_historie",
                                       "tvl_usd"))
    elif was == "nvm":
        laufe("NVM  (MC / Adressen^2, Metcalfe)", menge,
              reihe("data/onchain_historie.db", "adractcnt"), quadrat=True)
    elif was == "nvt":
        laufe("NVT-Ersatz (MC / Transaktionszahl)", menge,
              reihe("data/onchain_historie.db", "txcnt"))
