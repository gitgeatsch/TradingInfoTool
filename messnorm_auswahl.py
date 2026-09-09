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

if hasattr(sys.stdout, "reconfigure"):        # ⚠️ Suite ersetzt stdout
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as M                        # noqa: E402
# ⚠️ ALLES IMPORTIERT, NICHTS NACHGEBAUT.
from messe_beitrag_auf_auswahl import sammle, momentum250   # noqa: E402
from pruefe_n31_tagesklammer import je_tag_wirkung          # noqa: E402
from messnorm import (Lage, Befund, Protokoll, ZIEHUNGEN,   # noqa: E402
                      SAAT, _block, NULL_ZIEHUNGEN, NULL_PERZENTIL,
                      TRENNSCHAERFE_GEGEN_NULLPUNKT, STAERKEN, _bezug,
                      ZIELGROESSE_JE_LAGE)

MENGEN = {"frei": 1.0, "50%": 0.50, "20%": 0.20, "10%": 0.10,
          "5%": 0.05}
# ⚠️⚠️ `50%` KAM AM 07.09.2026 DAZU - und zwar wegen eines Fehlbefunds.
#
# `turnover` schien ab 2022 das Vorzeichen zu drehen (-0,0112 / -0,0307).
# `pruefe_auswahl` reproduzierte das NICHT und sagte woertlich "KEIN
# BEFUND - untermaechtig". Der Grund: turnover deckt 66 von 524 Symbolen
# ab, und 20 % davon sind 10,1 Anker je Tag. Auf 50 % sind es 25,5 - dort
# ist er ab 2022 POSITIV (+0,0598 [+0,0066 .. +0,1139]).
#
# ⚠️ Die Menge ist kein Geschmack, sie folgt der DATENLAGE - siehe
# `menge_nach_datenlage` unten.

MIND_ANKER = 12
"""Untergrenze fuer die Ankerzahl je Tag - NICHT neu erfunden.

`messe_beitrag_auf_auswahl.sammle` verwirft Tage mit weniger als 12
Werten (`if len(zeilen) < 12: continue`). Dieselbe Zahl gilt hier fuer
die GEWAEHLTEN Anker: eine Auswahl, die weniger uebrig laesst, als die
Rohmenge mindestens haben muss, ist keine Grundlage.

⚠️ Warum es diese Grenze braucht (N-65, 07.09.2026): `median(Gruppe) -
median(alle)` ist bei kleinen Gruppen nach oben verzerrt. Gemessen mit
GEMISCHTEN Raengen - also ohne jede Information - lieferte die Statistik
+0,10 bis +0,16 R statt null. Das ist groesser als jeder gesuchte
Effekt."""


def zulaessige_mengen(je_tag: dict, mom: dict, mindest: int = MIND_ANKER,
                      horizont: int = 20, bloecke: int = 20) -> list:
    """ALLE Mengen, die die Datenlage traegt - nicht nur die schmalste.

    ⚠️⚠️ WARUM ES DIESE FUNKTION NEBEN `menge_nach_datenlage` GIBT
    (07.09.2026, aus der Durchsicht N-73 gelernt).

    `menge_nach_datenlage` gibt die SCHMALSTE zulaessige Menge zurueck -
    weil die Betriebsmenge schmal ist (F-212). Aber die schmalste
    zulaessige ist zugleich die RAUSCHENDSTE: weniger Anker, breiteres
    Band. Sie zum alleinigen Massstab zu machen, bestraft jeden
    Kandidaten mit guter Abdeckung.

    Gemessen an `schnitt` (N-73): bei 10 % +0,1780 [+0,0274 .. +0,3361]
    "nicht trennbar", bei 20 % +0,1759 [+0,0715 .. +0,2907] "TRAEGT".
    **Fast derselbe Punktschaetzer, anderes Urteil** - allein wegen der
    Bandbreite.

    > Die Zulaessigkeit sortiert aus, was zu duenn ist. Das URTEIL sollte
    > ueber ALLE zulaessigen Mengen halten. Ein Kandidat, der nur auf
    > einer von ihnen traegt, ist nicht robust - und das ist ein Befund
    > ueber ihn, kein Grund, sich die passende Menge auszusuchen.

    Angewandt:

        turnover   zulaessig {50 %, frei}       traegt in BEIDEN   ✔
        schnitt    zulaessig {10 %, 20 %, frei} traegt nur bei 20 % ✖

    ⚠️ `frei` ist mit aufgefuehrt, beantwortet aber die MARKT-Frage
    (P6) - sie zaehlt als Vergleichsbasis, nicht als Beitragsurteil.
    """
    aus = []
    for name in ("5%", "10%", "20%", "50%", "frei"):
        if _traegt_die_menge(je_tag, mom, name, mindest, horizont, bloecke):
            aus.append(name)
    return aus


def _traegt_die_menge(je_tag, mom, name, mindest, horizont, bloecke) -> bool:
    """Haelt DIESE Menge beide Kriterien? — Anker je Tag UND Bloecke."""
    import numpy as _np
    from messe_beitrag_auf_auswahl import _auswahl_maske as _maske
    anteil = MENGEN[name]
    n = []
    for tag, zeilen in je_tag.items():
        if len(zeilen) < 12:
            continue
        m = _maske(zeilen, mom.get(tag) or {}, anteil, None)
        if m is not None and m.any():
            n.append(int(m.sum()))
    if not n or float(_np.mean(n)) < mindest:
        return False
    return datenlage(je_tag, mom, name, horizont).get("bloecke", 0) >= bloecke


def menge_nach_datenlage(je_tag: dict, mom: dict,
                         mindest: int = MIND_ANKER,
                         horizont: int = 20,
                         bloecke: int = 20) -> str | None:
    """Die SCHMALSTE Menge, die noch `mindest` Anker je Tag liefert.

    ⚠️ WARUM SCHMAL UND NICHT BREIT. F-212: die Beitraege wirken erst am
    Ende des Trichters, auf einer bereits ausgewaehlten Menge. Die
    Messmenge soll die Betriebsmenge nachbilden - also so schmal wie
    moeglich. Aber nur so schmal, wie die Datenlage es traegt.

    ⚠️ UND DIE REGEL GILT FUER ALLE BEITRAEGE GLEICH. Gemessen am
    07.09.2026 fuer die spaete Aera:

        turnover       50 %   (bei 20 % nur 10,1 Anker/Tag)
        funding        10 %
        oi_aenderung   20 %

    Dass `turnover` eine breitere Menge braucht, ist kein Sonderrecht -
    es ist dieselbe Regel auf eine duennere Abdeckung angewandt. Wer alle
    auf dieselbe Menge zwingt, misst bei einem von ihnen Rauschen.

    ⚠️ ZWEI Bedingungen: `mindest` Anker JE TAG **und** `bloecke`
    Bloecke insgesamt. Eine schmale Auswahl verwirft auch TAGE - bei
    `schnitt` haelt 5 % zwar die Ankerzahl (16,1), laesst aber nur 11
    Bloecke uebrig. Die Norm antwortet dort "KEIN BEFUND".

    Gibt `None` zurueck, wenn KEINE Auswahl beide Kriterien haelt - dann
    ist die Frage auf dieser Datenlage nicht als Beitragsfrage zu
    stellen, und das ist ein Ergebnis, kein Zwischenschritt.
    """
    import numpy as _np
    from messe_beitrag_auf_auswahl import _auswahl_maske as _maske
    # ⚠️ Von SCHMAL nach BREIT, und beim ersten Treffer abbrechen. Die
    # erste Fassung lief weiter und waehlte damit immer die breiteste -
    # genau das Gegenteil (07.09., vom Vorabtest gefangen).
    for name in ("5%", "10%", "20%", "50%"):
        anteil = MENGEN[name]
        n = []
        for tag, zeilen in je_tag.items():
            if len(zeilen) < 12:
                continue
            m = _maske(zeilen, mom.get(tag) or {}, anteil, None)
            if m is not None and m.any():
                n.append(int(m.sum()))
        if not n or float(_np.mean(n)) < mindest:
            continue
        # ⚠️⚠️ ZWEI BEDINGUNGEN, NICHT EINE (07.09., nachgetragen).
        #
        # Die erste Fassung prueft nur die Ankerzahl. Bei `schnitt` waehlte
        # sie damit 5 % (16,1 Anker/Tag) - dort bleiben aber nur 11
        # BLOECKE uebrig, und die Norm antwortet "KEIN BEFUND".
        #
        # ⚠️ UND DIE BLOCKZAHL WIRD NICHT SELBST GEZAEHLT. Die zweite
        # Fassung zaehlte Tage mit nichtleerer Maske - `je_tag_wirkung`
        # verwirft aber weitere (es braucht >= 1 oben und >= 3 unten).
        # Deshalb 27 statt 11 Bloecke, und das Kriterium griff nicht.
        # `datenlage()` rechnet es ueber die ECHTE Kette - sie steht seit
        # dem 06.09. genau dafuer da. R-R10: nachsehen, nicht neu bauen.
        if datenlage(je_tag, mom, name, horizont).get("bloecke", 0) >= bloecke:
            return name
    return None


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
                   staerken: tuple = STAERKEN,
                   hypothese: str = "", verwendung: str = "",
                   hypothesen: int = 1,
                   null_ziehungen: int = NULL_ZIEHUNGEN,
                   null_perzentil: float = NULL_PERZENTIL,
                   trennschaerfe_gegen_nullpunkt: bool =
                   TRENNSCHAERFE_GEGEN_NULLPUNKT,
                   auswahl_saat: int | None = None,
                   nur: set | None = None,
                   zielgroesse: str = "bewegung_r") -> Befund:
    """Ein Befund auf der selektierten Menge, unter der TAGESKLAMMER.

    ⚠️⚠️ DIE VORGABEWERTE SIND DER MESSSTANDARD (`messnorm`, 08.09.2026)

    `null_ziehungen` · `null_perzentil` · `trennschaerfe_gegen_nullpunkt`
    · `staerken` kommen aus `messnorm` und stehen dort begruendet. Wer
    sie hier ueberschreibt, misst NICHT nach Norm und muss das im Befund
    vermerken.

    Der kurze Grund, warum sie so stehen: das MAXIMUM ueber fuenf
    Ziehungen war kein Schaetzer - es waechst mit der Ziehungszahl und
    hat keinen Grenzwert (N-81, auf Kunstdaten UND echt gezeigt). Daran
    hing `funding` bei 50 %: Abstand +0,0002 R bei fuenf Ziehungen,
    gekippt ab zehn.

    ⚠️ Die Umstellung wurde Ziffer fuer Ziffer gegen die Vorgaengerfassung
    geprueft, BEVOR sie Standard wurde (N-82: 14 von 16 Urteilen
    unveraendert, `zufall` unter beiden Regeln sauber).

    ## ⚠️⚠️ `auswahl_saat` — die Menge ZUFAELLIG statt nach Momentum

    Fuer die Kettenfrage K-1b (09.09.2026). Die Kette beurteilt 27 von 43
    Werten, davon 25 **weil der Nutzer sie haelt** - nach NICHTS
    selektiert. Die Beitraege sind aber alle auf momentum-verengten
    Mengen belegt. Ob sie sich auf eine unselektierte Menge uebertragen,
    ist nie geprueft worden.

    `auswahl_saat` waehlt je Tag GLEICH VIELE Werte, aber zufaellig. Alles
    andere bleibt: der Rang kommt weiter aus dem vollen Tagesquerschnitt
    (wie `marktrang` in der Produktion), Nullkontrolle und
    Positivkontrolle laufen unveraendert.

    ⚠️ ES IST EINE SAAT, KEIN GENERATOR. `sammle` verbraucht je Tag
    Zufall; ein durchgereichter Generator lieferte fuer Hauptmessung,
    Nullkontrolle und Positivkontrolle DREI VERSCHIEDENE Auswahlen - und
    der Vergleich waere verwaschen. Aus der Saat wird an jeder Stelle
    derselbe Generator neu gebaut.

    ⚠️ Ein Zufallsausschnitt ist ein STELLVERTRETER, kein Abbild: eine
    Bestands-Historie gibt es nicht (`holdings` hat 55 Zeilen ohne
    Zeitachse, `portfolio_wert_historie` ist leer). Der echte Bestand ist
    vom Nutzer gewaehlt, also nicht neutral - aber auch nicht gegen den
    Beitrag gerichtet. Traegt ein Beitrag auf dem Zufallsausschnitt, wird
    er es auf dem Bestand auch tun; traegt er NUR auf der Momentumspitze,
    haengt sein Beleg an einer Auswahl, die der Bestand nicht durchlaeuft.
    """
    def _aw():
        """Frischer Generator aus der Saat - oder None fuer 'wie bisher'."""
        return (None if auswahl_saat is None
                else np.random.default_rng(int(auswahl_saat)))
    if menge not in MENGEN:
        raise ValueError("unbekannte Menge: %r — erlaubt: %s"
                         % (menge, ", ".join(MENGEN)))
    # ⚠️⚠️ DIE ZIELGROESSE MUSS ZUR LAGE PASSEN (09.09.2026). Vorher stand
    # hier `zielgroesse="bewegung_r"` FEST VERDRAHTET, und die `lage` wurde
    # nur an den Befund durchgereicht. Eine Messung mit
    # `lage=Lage("hebel","einstieg")` haette damit Spot-Bewegung gemessen
    # und "Hebel" daraufgeschrieben - eine Etikettenluege.
    soll = ZIELGROESSE_JE_LAGE.get((lage.instrument, lage.strategie))
    if soll and zielgroesse != soll:
        raise ValueError(
            "%s verlangt die Zielgroesse %r, bekommen %r. Wer bewusst eine "
            "andere misst, ruft `messnorm.pruefe` und begruendet es im "
            "Befund." % (lage, soll, zielgroesse))
    block = _block(horizont)
    anteil = MENGEN[menge]

    g = sammle(je_tag, mom, anteil, mische_auswahl=_aw(), nur=nur)
    d = je_tag_wirkung(g)
    haupt = _band(d, rng, block)
    if haupt is None:
        raise ValueError("zu wenige Tage fuer ein Band (%d)" % len(d))

    # ---- Nullkontrolle: Rang je Tag gemischt, mehrere Ziehungen -------
    nullw, nullu, nullo = [], [], []
    nz = int(null_ziehungen) if null_ziehungen else ZIEHUNGEN
    for z in range(nz):
        gz = sammle(je_tag, mom, anteil,
                    mische_rang=np.random.default_rng(SAAT + z),
                    mische_auswahl=_aw(), nur=nur)
        nb = _band(je_tag_wirkung(gz), rng, block)
        if nb:
            nullw.append(nb["mittel"])
            nullu.append(nb["unten"])
            nullo.append(nb["oben"])
    # ⚠️ Ohne `null_perzentil` bleibt es beim MAXIMUM - unveraendert.
    if nullo and null_perzentil:
        oben = float(np.percentile(nullo, float(null_perzentil)))
        unten = float(np.percentile(nullu, 100.0 - float(null_perzentil)))
    else:
        oben = float(np.max(nullo)) if nullo else 0.0
        unten = float(np.min(nullu)) if nullu else 0.0
    null = {"mittel": float(np.mean(nullw)) if nullw else 0.0,
            "unten": unten, "oben": oben}

    # ---- Positivkontrolle -> TRENNSCHAERFE ----------------------------
    # ⚠️ pflanze = -s, damit die Kennzahl STEIGT. Siehe Modulkopf: das
    # Vorzeichen ist hier umgekehrt zu `messe_regel_wirksamkeit`.
    # ⚠️⚠️ ZWEI SKALEN (Fehler 5, 08.09.2026) - ausfuehrlich begruendet im
    # Kopf von `messnorm.pruefe`. Kurz: `s` ist die GEPFLANZTE Staerke, die
    # Anlage misst davon aber nur (1 - GRENZE) = 20 %. An echten Daten
    # nachgemessen: 20,3 / 20,1 / 19,6 / 19,2 % fuer 0,05 / 0,10 / 0,20 /
    # 0,40. `urteil` vergleicht `wirkung` mit `trennschaerfe` - stand dort
    # die gepflanzte Zahl, war der Vergleich um Faktor 5 daneben.
    trennschaerfe, trennschaerfe_in_r, treffer = None, None, {}
    for s in sorted(staerken):
        gefunden, werte = 0, []
        for z in range(ZIEHUNGEN):
            gz = sammle(je_tag, mom, anteil,
                        mische_rang=np.random.default_rng(SAAT + 1000 * z),
                        pflanze=-s, mische_auswahl=_aw(), nur=nur)
            pb = _band(je_tag_wirkung(gz), rng, block)
            # ⚠️ 2.188-inkonsistenz: die Trennschaerfe prueft gegen NULL,
            # das URTEIL (`Befund.traegt`) gegen `null_oben`. Sind beide
            # verschieden, widersprechen sich Trennschaerfe und Urteil im
            # SELBEN Satz - live sichtbar an `turnover`. Der Vorgabewert
            # laesst das alte Verhalten unveraendert.
            # ⚠️ DERSELBE BEZUG WIE DAS URTEIL - siehe `messnorm._bezug`.
            latte = (_bezug(null) if trennschaerfe_gegen_nullpunkt else 0.0)
            if pb:
                werte.append(pb["mittel"])
                if pb["unten"] > latte:
                    gefunden += 1
        treffer[s] = gefunden
        if trennschaerfe is None and gefunden >= max(3, (4 * ZIEHUNGEN) // 5):
            trennschaerfe_in_r = s
            trennschaerfe = float(np.mean(werte)) if werte else None

    anker = sum(len(y) for _o, y in g.values())
    syms = len({x["sym"] for z in je_tag.values() for x in z})
    return Befund(
        # ⚠️ DIE FRAGEART FAELLT AUS DER MENGE (07.09.2026, Methodik 2.143).
        # `menge="frei"` ist hier die VERGLEICHSBASIS und beantwortet die
        # MARKT-Frage (P6: breiter als das Portfolio). Die selektierten
        # Mengen beantworten die BETRIEBS-Frage (F-212). Beides in einem
        # Lauf - genau dafuer gibt es dieses Modul.
        frageart=("markt" if menge == "frei" else "beitrag"),
        kandidat=kandidat, lage=lage, zielgroesse=zielgroesse, menge=menge,
        wirkung=haupt["mittel"], unten=haupt["unten"], oben=haupt["oben"],
        nullpunkt=null["mittel"], null_unten=null["unten"],
        null_oben=null["oben"], trennschaerfe=trennschaerfe,
        trennschaerfe_in_r=trennschaerfe_in_r,
        gepflanzt=tuple(sorted(staerken)), n_anker=anker,
        n_tage=haupt["tage"], n_bloecke=max(0, haupt["tage"] // block),
        abdeckung_symbole=syms, hypothesen=hypothesen,
        protokoll=Protokoll(
            wirkung_funktion="messe_beitrag_auf_auswahl.sammle + "
                             "pruefe_n31_tagesklammer.je_tag_wirkung",
            band_funktion="messe_bewertungskennzahl.urteil_tage",
            null_konstruktion="Raenge je Tag gemischt (mische_rang)",
            null_ziehungen=nz,
            positiv_konstruktion="in die gemischte Welt gepflanzt, "
                                 "pflanze=-s (Kennzahl STEIGT)",
            positiv_ziehungen=ZIEHUNGEN, positiv_treffer=treffer,
            blocklaenge=block, saat=SAAT))


def vergleiche(a: Befund, b: Befund, je_tag: dict, mom: dict, rng, *,
               horizont: int = 20,
               staerken: tuple = STAERKEN) -> dict:
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
