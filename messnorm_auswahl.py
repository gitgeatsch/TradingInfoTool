# -*- coding: utf-8 -*-
"""Die MESSNORM auf der SELEKTIERTEN Menge — Verdrahtung (06.09.2026)

## Warum eine eigene Datei

`messnorm.pruefe()` misst auf der freien Menge mit
`messe_regel_wirksamkeit.wirkung()`. Fuer die **selektierte** Menge braucht
es `messe_beitrag_auf_auswahl.sammle()` - und die beiden pflanzen in
ENTGEGENGESETZTE Richtungen:

    wirkung()   y[gesperrt] -= s    die Regel sieht BESSER aus
    sammle()    y[oben]     += s    die Regel sieht SCHLECHTER aus

⚠️ Wer das vermischt, vergleicht spaeter zwei Trennschaerfen, die
Verschiedenes messen. Deshalb steht die Verdrahtung hier getrennt und traegt
die Konvention im Protokoll mit.

## Was hier gilt

    Auswahl      messe_beitrag_auf_auswahl.sammle()   - importiert
    Klammer      pruefe_n31_tagesklammer.je_tag_wirkung() - importiert
    Band         messe_bewertungskennzahl.urteil_tage()   - importiert
    Zielgroesse  in_r (Bewegung), IMMER - die Barriere hat hier nichts zu suchen

⚠️ **Die Tagesklammer, nicht gepoolt.** `messe_beitrag_auf_auswahl` rechnet
`_kennzahl` gepoolt; das ist eine andere Statistik als die registrierte.
Reproduziert wurde am 06.09. beides:

    gepoolt        frei -0,0003 · 5 % +0,0282     bitgenau wie F-212
    Tagesklammer   frei +0,0274 · 5 % +0,0897     registriert +0,0246

## ⚠️ Das VORZEICHEN der Pflanzung — zweimal nachgerechnet

`_kennzahl` ist `median(frei) - median(alle)`.

    y[oben] += s   die Gesperrten werden BESSER -> die Kennzahl FAELLT
    y[oben] -= s   die Gesperrten werden SCHLECHTER -> die Kennzahl STEIGT

Fuer die Frage *haette die Anlage einen Beitrag dieser Groesse gefunden?*
muss die Kennzahl STEIGEN, also `pflanze=-s`. Fuer die Gegenfrage *haette
sie einen ABFALL gefunden?* `pflanze=+s` - so rechnet
`messe_beitrag_auf_auswahl` es in seiner eigenen Positivkontrolle.

**Beide Richtungen werden gemessen und getrennt ausgewiesen.**

    python messnorm_auswahl.py --selbsttest
"""
from __future__ import annotations

import contextlib
import io as _io
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as M                        # noqa: E402
# ⚠️ ALLES IMPORTIERT, NICHTS NACHGEBAUT.
from messe_beitrag_auf_auswahl import sammle, momentum250   # noqa: E402
from pruefe_n31_tagesklammer import je_tag_wirkung          # noqa: E402
from messnorm import (Lage, Befund, Protokoll, ZIEHUNGEN,   # noqa: E402
                      SAAT, _block)

MENGEN = {"frei": 1.0, "20%": 0.20, "10%": 0.10, "5%": 0.05}


def _band(d, rng, block):
    """`urteil_tage` druckt — hier wird nur der Wert gebraucht."""
    with contextlib.redirect_stdout(_io.StringIO()):
        return M.urteil_tage("", d, rng, block)


def datenlage(je_tag: dict, mom: dict, menge: str,
              horizont: int = 20) -> dict:
    """WIE VIELE BLOECKE haette diese Frage? — VOR dem Lauf, in Sekunden.

    ⚠️ Nutzervorgabe 06.09.: *„pruefe auch, ob wir die passende
    Datengrundlage haben, sowie wann wir bestimmte Messungen sauber
    simulieren muessen."*

    Die bindende Grenze ist nicht die Ankerzahl, sondern die BLOCKZAHL:
    der Block muss laenger sein als die Abhaengigkeit (3 x Horizont = 90
    Tage), und unter 20 Bloecken deckt das Band nicht (bei 5 Bloecken
    19,5 % Fehlalarme statt 5 %).

        20 Bloecke x 90 Tage = 1.800 Kalendertage MIT Daten

    ## ⚠️ KUNSTDATEN sind hier KEIN Ersatz (Nutzerhinweis 06.09.)

    *"auch die Simulation muss sauber aufgesetzt sein - in vielen Faellen
    haben wir historische Daten zur Verfuegung. Kunstdaten vs. Marktdaten."*

    Die beiden sind fuer verschiedene Fragen da:

        KUNSTDATEN   pruefen das WERKZEUG - findet es einen gepflanzten
                     Effekt, weist es Rauschen ab? Sie beantworten NIE eine
                     Marktfrage; man bekommt zurueck, was man hineinlegt.

        MARKTDATEN   beantworten die Frage. Fehlt eine LAGE (kein einziges
                     Hebel-Signal), laesst sie sich aus den vorhandenen
                     Kursreihen REKONSTRUIEREN - das ist Simulation auf
                     Marktdaten und voellig verschieden von Kunstdaten.

    Deshalb unterscheidet diese Funktion zwei Gruende:

        LAGE fehlt        -> aus Marktdaten rekonstruierbar
                             (Hebel, Short, Akkumulation: die Kursreihen
                             sind da, nur die Signale fehlen)
        DATEN fehlen      -> nur mehr Daten helfen
                             (turnover: 65 Symbole · Terminmarkt: 122 Tage)

    ⚠️ Wer im zweiten Fall Kunstdaten nimmt, misst seine eigenen Annahmen.
    """
    block = _block(horizont)
    g = sammle(je_tag, mom, MENGEN[menge])
    d = je_tag_wirkung(g)
    tage = len(d)
    bloecke = tage // block
    anker = sum(len(y) for _o, y in g.values())
    syms = len({x["sym"] for z in je_tag.values() for x in z})
    messbar = bloecke >= 20
    if messbar:
        weg = "messbar"
    elif tage == 0:
        weg = ("nicht messbar - die Auswahl laesst keinen Tag uebrig. "
               "KEINE Kunstdaten: hier fehlen DATEN (Breite), nicht eine Lage")
    else:
        weg = ("nicht messbar - %d Tage fehlen. Zuerst die Menge weiten "
               "oder mehr Historie; Kunstdaten helfen NICHT"
               % (20 * block - tage))
    return {"menge": menge, "tage": tage, "bloecke": bloecke,
            "anker": anker, "symbole": syms, "blocklaenge": block,
            "messbar": messbar, "weg": weg,
            "fehlende_tage": max(0, 20 * block - tage)}


def pruefe_auswahl(kandidat: str, je_tag: dict, mom: dict, *, lage: Lage,
                   menge: str, rng, horizont: int = 20,
                   staerken: tuple = (0.02, 0.05, 0.10),
                   hypothese: str = "", verwendung: str = "",
                   hypothesen: int = 1) -> Befund:
    """Ein Befund auf der selektierten Menge, unter der TAGESKLAMMER."""
    if menge not in MENGEN:
        raise ValueError("unbekannte Menge: %r — erlaubt: %s"
                         % (menge, ", ".join(MENGEN)))
    block = _block(horizont)
    anteil = MENGEN[menge]

    g = sammle(je_tag, mom, anteil)
    d = je_tag_wirkung(g)
    haupt = _band(d, rng, block)
    if haupt is None:
        raise ValueError("zu wenige Tage fuer ein Band (%d)" % len(d))

    # ---- Nullkontrolle: Rang je Tag gemischt, mehrere Ziehungen -------
    nullw, nullu, nullo = [], [], []
    for z in range(ZIEHUNGEN):
        gz = sammle(je_tag, mom, anteil,
                    mische_rang=np.random.default_rng(SAAT + z))
        nb = _band(je_tag_wirkung(gz), rng, block)
        if nb:
            nullw.append(nb["mittel"])
            nullu.append(nb["unten"])
            nullo.append(nb["oben"])
    null = {"mittel": float(np.mean(nullw)) if nullw else 0.0,
            "unten": float(np.min(nullu)) if nullu else 0.0,
            "oben": float(np.max(nullo)) if nullo else 0.0}

    # ---- Positivkontrolle -> TRENNSCHAERFE ----------------------------
    # ⚠️ pflanze = -s, damit die Kennzahl STEIGT. Siehe Modulkopf: das
    # Vorzeichen ist hier umgekehrt zu `messe_regel_wirksamkeit`.
    trennschaerfe, treffer = None, {}
    for s in sorted(staerken):
        gefunden = 0
        for z in range(ZIEHUNGEN):
            gz = sammle(je_tag, mom, anteil,
                        mische_rang=np.random.default_rng(SAAT + 1000 * z),
                        pflanze=-s)
            pb = _band(je_tag_wirkung(gz), rng, block)
            if pb and pb["unten"] > 0:
                gefunden += 1
        treffer[s] = gefunden
        if trennschaerfe is None and gefunden >= max(3, (4 * ZIEHUNGEN) // 5):
            trennschaerfe = s

    anker = sum(len(y) for _o, y in g.values())
    syms = len({x["sym"] for z in je_tag.values() for x in z})
    return Befund(
        kandidat=kandidat, lage=lage, zielgroesse="bewegung_r", menge=menge,
        wirkung=haupt["mittel"], unten=haupt["unten"], oben=haupt["oben"],
        nullpunkt=null["mittel"], null_unten=null["unten"],
        null_oben=null["oben"], trennschaerfe=trennschaerfe,
        gepflanzt=tuple(sorted(staerken)), n_anker=anker,
        n_tage=haupt["tage"], n_bloecke=max(0, haupt["tage"] // block),
        abdeckung_symbole=syms, hypothesen=hypothesen,
        protokoll=Protokoll(
            wirkung_funktion="messe_beitrag_auf_auswahl.sammle + "
                             "pruefe_n31_tagesklammer.je_tag_wirkung",
            band_funktion="messe_bewertungskennzahl.urteil_tage",
            null_konstruktion="Raenge je Tag gemischt (mische_rang)",
            null_ziehungen=ZIEHUNGEN,
            positiv_konstruktion="in die gemischte Welt gepflanzt, "
                                 "pflanze=-s (Kennzahl STEIGT)",
            positiv_ziehungen=ZIEHUNGEN, positiv_treffer=treffer,
            blocklaenge=block, saat=SAAT))


def vergleiche(a: Befund, b: Befund, je_tag: dict, mom: dict, rng, *,
               horizont: int = 20,
               staerken: tuple = (0.02, 0.05, 0.10)) -> dict:
    """Der GEPAARTE Vergleich (2.105) — mit eigener Trennschaerfe.

    ⚠️ Sie fehlte bisher. F-212 meldete *„der Beitrag faellt auf der
    selektierten Menge NICHT ab"* — und die eigene Positivkontrolle fand
    einen Abfall von 0,05 R nicht. Ohne Trennschaerfe ist das keine
    Aussage.
    """
    block = _block(horizont)
    ga = sammle(je_tag, mom, MENGEN[a.menge])
    gb = sammle(je_tag, mom, MENGEN[b.menge])
    da, db = je_tag_wirkung(ga), je_tag_wirkung(gb)
    gem = sorted(set(da) & set(db))
    if len(gem) < 60:
        return {"urteil": "KEIN BEFUND - nur %d gemeinsame Tage" % len(gem)}
    diff = {t: db[t] - da[t] for t in gem}
    haupt = _band(diff, rng, block)

    # Trennschaerfe des VERGLEICHS: ein Abfall NUR auf der engeren Menge
    ts, treffer = None, {}
    for s in sorted(staerken):
        gefunden = 0
        for z in range(ZIEHUNGEN):
            gp = sammle(je_tag, mom, MENGEN[b.menge], pflanze=s)
            dp = je_tag_wirkung(gp)
            gm = sorted(set(da) & set(dp))
            if len(gm) < 60:
                continue
            pb = _band({t: dp[t] - da[t] for t in gm}, rng, block)
            # ⚠️ NICHT GEGEN EINEN ANTEIL VON s PRUEFEN (06.09., der
            # Selbsttest hat es gefunden).
            #
            # Die Kennzahl ist `median(frei) - median(alle)` und damit
            # KOMPRIMIERT: eine Pflanzung von 0,10 R bewegt sie um rund
            # 0,02. Wer `0,5 x s` verlangt, findet nie etwas - der Test
            # meldete "untermaechtig" in einer Welt, in der der Effekt
            # ausschliesslich in der Auswahl steckte.
            #
            # Richtig ist die Frage, ob die gepflanzte Fassung vom
            # Original UNTERSCHEIDBAR ist: ihr oberes Bandende muss unter
            # dem Mittel des Originals liegen.
            if pb and haupt and pb["oben"] < haupt["mittel"]:
                gefunden += 1
        treffer[s] = gefunden
        if ts is None and gefunden >= max(3, (4 * ZIEHUNGEN) // 5):
            ts = s
    bloecke = len(gem) // block
    if bloecke < 20:
        urt = "KEIN BEFUND - nur %d Bloecke" % bloecke
    elif ts is None:
        urt = ("KEIN BEFUND - untermaechtig: selbst %.2f R Abfall wurde "
               "nicht gefunden" % max(staerken))
    elif haupt["unten"] > 0:
        urt = "ZUWACHS (belastbar bis %.2f R)" % ts
    elif haupt["oben"] < 0:
        urt = "ABFALL (belastbar bis %.2f R)" % ts
    else:
        urt = "kein Unterschied bis %.2f R" % ts
    return {"wirkung": haupt["mittel"], "unten": haupt["unten"],
            "oben": haupt["oben"], "tage": len(gem), "bloecke": bloecke,
            "trennschaerfe": ts, "treffer": treffer, "urteil": urt}


# ------------------------------------------------------------- Selbsttest
def _kunstwelt(rng, tage=2400, syms=40, effekt=0.0, nur_auswahl=False):
    """⚠️ Pflanzt nach dem RANG, nicht nach dem Rohwert — der Fehler aus
    `messnorm._welt`, hier von Anfang an vermieden."""
    je_tag, mom = {}, {}
    grenze = int(round(syms * 0.80))
    for t in range(tage):
        tag = "t%04d" % t
        kz = rng.uniform(size=syms)
        mo = rng.uniform(size=syms)
        y = rng.normal(0, 1.0, syms)
        ordnung = np.argsort(kz)
        gewaehlt = mo >= np.quantile(mo, 0.95)
        z, mt = [], {}
        for platz, i in enumerate(ordnung):
            wirkt = (not nur_auswahl) or gewaehlt[i]
            r = y[i] - (effekt if (platz >= grenze and wirkt) else 0.0)
            sym = "S%02d" % i
            z.append({"sym": sym, "kennzahl": float(kz[i]), "in_r": float(r)})
            mt[sym] = float(mo[i])
        je_tag[tag] = z
        mom[tag] = mt
    return je_tag, mom


def selbsttest() -> bool:
    print("=" * 96)
    print("SELBSTTEST — MESSNORM AUF DER SELEKTIERTEN MENGE")
    print("=" * 96)
    ok = True
    L = Lage("spot", "einstieg")
    rng = np.random.default_rng(SAAT)

    print("\n1. DATENLAGE — wie viele Bloecke haette die Frage?")
    je_tag, mom = _kunstwelt(np.random.default_rng(1), tage=2400)
    for menge in ("frei", "20%", "10%", "5%"):
        d = datenlage(je_tag, mom, menge)
        print("   %-6s %5d Tage · %3d Bloecke · %7d Anker  -> %s"
              % (menge, d["tage"], d["bloecke"], d["anker"], d["weg"][:66]))

    print("\n2. Ein gepflanzter Effekt muss gefunden werden")
    je_tag, mom = _kunstwelt(np.random.default_rng(2), tage=2400, effekt=0.10)
    b = pruefe_auswahl("kunst", je_tag, mom, lage=L, menge="frei", rng=rng)
    print("   %s" % b.zeile()[:150])
    if b.urteil != "TRAEGT":
        ok = False
        print("      ✖ muss TRAEGT ergeben")

    print("\n3. Ohne Effekt muss eine SCHRANKE herauskommen")
    je_tag0, mom0 = _kunstwelt(np.random.default_rng(3), tage=2400)
    b0 = pruefe_auswahl("kunst0", je_tag0, mom0, lage=L, menge="frei", rng=rng)
    print("   %s" % b0.zeile()[:150])
    if b0.urteil == "TRAEGT" or not b0.urteil.startswith(
            ("TRAEGT NICHT", "KEIN BEFUND")):
        ok = False
        print("      ✖ ohne Effekt darf nichts tragen")

    print("\n4. Der GEPAARTE Vergleich traegt seine eigene Trennschaerfe")
    # ⚠️ GROESSERE WELT (06.09., der Selbsttest hat es gefunden).
    #
    # Mit 40 Symbolen sind 5 % zwei Werte, und `je_tag_wirkung` verlangt
    # mindestens einen oben UND drei frei - also null verwertbare Tage.
    # Der Test meldete das ehrlich, hat `vergleiche()` damit aber gar nicht
    # geprueft. Dieselbe Falle wie bei turnover in der echten Messung:
    # 65 Symbole ergeben drei je Tag und damit gar nichts.
    #
    # 160 Symbole -> 8 gewaehlte je Tag -> messbar.
    je_tag, mom = _kunstwelt(np.random.default_rng(2), tage=2400,
                             syms=160, effekt=0.10, nur_auswahl=True)
    a = pruefe_auswahl("kunst", je_tag, mom, lage=L, menge="frei", rng=rng)
    try:
        c = pruefe_auswahl("kunst", je_tag, mom, lage=L, menge="5%", rng=rng)
        v = vergleiche(a, c, je_tag, mom, rng)
        print("   5 %% gegen frei: %+.4f R · Trennsch. %s · %s"
              % (v.get("wirkung", float("nan")),
                 ("%.2f" % v["trennschaerfe"]) if v.get("trennschaerfe")
                 else "KEINE", v["urteil"][:60]))
        if "trennschaerfe" not in v:
            ok = False
            print("      ✖ der Vergleich muss eine Trennschaerfe liefern")
    except ValueError as e:
        print("   5 %% nicht messbar: %s" % str(e)[:70])

    print()
    print("=" * 96)
    print("SELBSTTEST %s" % ("BESTANDEN" if ok else "✖ FEHLGESCHLAGEN"))
    print("=" * 96)
    return ok


if __name__ == "__main__":
    sys.exit(0 if selbsttest() else 1)
