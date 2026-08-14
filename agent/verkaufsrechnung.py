# -*- coding: utf-8 -*-
"""Die Verkaufsseite - was tun mit dem, was schon da ist (14.08.2026).

DER FUND, DER DIESES MODUL AUSGELOEST HAT. Im ersten Echtbetrieb fielen 45
Urteile. Elf davon waren Verkaufsseite - und keines hat den Nutzer erreicht:

    HALTEN       24    keine Mail   (richtig)
    REDUZIEREN    9    keine Mail   FALSCH
    KAUFEN        8    Mail
    VERKAUFEN     2    keine Mail   FALSCH
    NACHKAUFEN    2    Mail

Der Grund stand in einer einzigen Zeile: `AKTIONEN_MIT_EINSTIEG` kennt drei
Woerter, und alles andere fiel in `_schreibe_nein()` - gebucht als "reines
LLM-Halten", ohne Mail. **Verkaufen wurde mit Nichtstun in einen Topf
geworfen.**

Bei einem Bestand, der ueber 60 % im Minus steht, ist das die dringendere
Nachricht - nicht der neunte Kaufvorschlag.

DREI KLASSEN STATT ZWEI. Das ist die eigentliche Korrektur:

    Einstieg    KAUFEN, NACHKAUFEN, EROEFFNEN      -> Einstiegsrechnung, Mail
    Ausstieg    REDUZIEREN, VERKAUFEN, SCHLIESSEN  -> DIESES MODUL, Mail
    Nichts      HALTEN, NICHTS_TUN                 -> Schattenbuchung, keine Mail

WARUM NICHT `ausstiegsrechnung.py` - das gibt es doch schon. Es verlangt
`einstieg` UND `stop_original` und rechnet in R. Das passt fuer eine Position,
die aus einem EIGENEN Signal entstanden ist; fuer den echten Spot-Bestand passt
es nicht, denn der hat nach Nutzerangabe **keinen Stop**:

    *"es gibt einen Spot bestand und Hebel bestand"* - und beim Spot ist die
    Positionsgroesse die einzige Risikosteuerung, nicht der Stop.

Ohne Stop gibt es kein R, ohne R keine der drei Aussagen von
`ausstiegsrechnung`. Sie hier zu erzwingen hiesse, eine Zahl zu erfinden, damit
eine Formel rechnet. Dieses Modul rechnet stattdessen mit dem, was wirklich
vorliegt: Menge, Einstandspreis, aktueller Kurs.

WAS ES NICHT TUT: es entscheidet nicht, OB verkauft wird. Das Urteil kommt vom
Modell; hier wird nur ausgerechnet, was es in Stueck und Euro bedeutet.
"""
from __future__ import annotations

# Die Aktionen, die eine BESTEHENDE Position betreffen. Bewusst als Liste des
# Erlaubten, nicht als Ausschluss - genau der Fehler, der am 13.08. schon
# einmal zuschlug (der CRV-Faktor traf `absicherung` mit, weil er ueber
# `!= "hebel"` definiert war).
AKTIONEN_MIT_AUSSTIEG = ("REDUZIEREN", "VERKAUFEN", "SCHLIESSEN",
                         "TEILVERKAUF", "HEBEL_SENKEN")

# Was ein REDUZIEREN bedeutet, wenn das Modell keine Menge nennt.
#
# EIN DRITTEL IST GESETZT, NICHT GEMESSEN, und das steht hier, damit niemand es
# fuer einen Befund haelt. Die Begruendung ist die Umkehrung der Tranche: wer in
# Stufen einsteigt, steigt in Stufen aus. Sobald es eigene Ausstiegsdaten gibt,
# gehoert diese Zahl gemessen.
TEIL_ANTEIL = 1.0 / 3.0

# Unter diesem Gegenwert lohnt kein Teilverkauf - die Gebuehren fressen ihn.
# Bei Krypto sind 1,5 % je Seite bei 20 EUR gerade 60 Cent, aber der Rest der
# Position wird dadurch nicht handhabbarer.
MINDEST_GEGENWERT_EUR = 25.0


def ist_ausstieg(aktion: str | None) -> bool:
    """Betrifft dieses Urteil eine bestehende Position?"""
    return str(aktion or "").strip().upper() in AKTIONEN_MIT_AUSSTIEG


def rechne(*, aktion: str, menge: float, kurs_eur: float,
           einstand_eur: float | None = None,
           gestakt: float | None = None) -> dict | None:
    """Was das Urteil in Stueck und Euro bedeutet.

    `None`, wenn nichts zu verkaufen ist. Das ist der Normalfall bei einem
    Symbol, das der Nutzer gar nicht haelt - und dort ist ein VERKAUFEN kein
    Auftrag, sondern eine Aussage ueber die Qualitaet des Urteils. Der Aufrufer
    bucht es dann als Schatten, so wie ein HALTEN.

    DER GESTAKTE TEIL WIRD ABGEZOGEN. Er laesst sich nicht ohne Weiteres
    verkaufen, und eine Empfehlung ueber eine Menge, an die man nicht
    herankommt, ist keine."""
    menge = float(menge or 0.0)
    frei = max(0.0, menge - float(gestakt or 0.0))
    if frei <= 0 or not kurs_eur or kurs_eur <= 0:
        return None

    a = str(aktion or "").strip().upper()
    anteil = 1.0 if a in ("VERKAUFEN", "SCHLIESSEN") else TEIL_ANTEIL
    verkaufsmenge = frei * anteil
    gegenwert = verkaufsmenge * float(kurs_eur)

    aus = {
        "aktion": a,
        "menge_gesamt": menge,
        "menge_frei": frei,
        "menge_verkauf": verkaufsmenge,
        "anteil": anteil,
        "gegenwert_eur": gegenwert,
        "wert_gesamt_eur": frei * float(kurs_eur),
        "zu_klein": gegenwert < MINDEST_GEGENWERT_EUR,
    }
    if gestakt:
        aus["gestakt"] = float(gestakt)

    # DAS ERGEBNIS DER POSITION, wenn wir es kennen. Es steht in der Mail,
    # weil es die Frage beantwortet, die der Nutzer zuerst stellt - und NICHT,
    # weil es die Entscheidung begruenden soll. Ein Verlust ist kein Grund zu
    # halten und kein Grund zu verkaufen; er ist die Ausgangslage.
    if einstand_eur and einstand_eur > 0:
        aus["einstand_eur"] = float(einstand_eur)
        aus["ergebnis_eur"] = (float(kurs_eur) - float(einstand_eur)) * frei
        aus["ergebnis_prozent"] = 100.0 * (float(kurs_eur) / float(einstand_eur) - 1.0)
        aus["realisiert_eur"] = ((float(kurs_eur) - float(einstand_eur))
                                 * verkaufsmenge)
    return aus


def saetze(e: dict) -> list[str]:
    """Die Rechnung in der Form, in der sie in die E-Mail gehoert.

    ABSOLUTE ZAHLEN VOR RELATIVEN - dieselbe Regel wie beim Einstieg
    (Nutzervorgabe 12.08.): erst wieviel Stueck und wieviel Euro, dann der
    Prozentsatz."""
    from agent.signal_mail import eur, preis

    m = e["menge_verkauf"]
    # Mengen sind keine Kurse: bei 12.000 Stueck sind Nachkommastellen Unsinn,
    # bei 0,004 BTC sind sie die ganze Information.
    menge_txt = (f"{m:,.0f}".translate(str.maketrans(",.", ".,"))
                 if m >= 100 else f"{m:,.6f}".translate(str.maketrans(",.", ".,")))
    z = []
    if e["anteil"] >= 1.0:
        z.append(f"Verkaufen        die GANZE Position - {menge_txt} Stueck "
                 f"zu etwa {preis(e['gegenwert_eur'] / e['menge_verkauf'])} EUR")
    else:
        z.append(f"Verkaufen        {menge_txt} Stueck - ein Drittel der "
                 f"Position (gesetzt, nicht gemessen)")
    z.append(f"Gegenwert        {eur(e['gegenwert_eur'], 2)} EUR "
             f"von {eur(e['wert_gesamt_eur'], 2)} EUR Gesamtwert")
    if e.get("gestakt"):
        z.append(f"                 (der gestakte Teil ist abgezogen - "
                 f"er ist nicht frei verfuegbar)")
    if "ergebnis_prozent" in e:
        vz = "+" if e["ergebnis_eur"] >= 0 else ""
        z.append(f"Stand            {vz}{eur(e['ergebnis_eur'], 2)} EUR "
                 f"({vz}{eur(e['ergebnis_prozent'], 1)} %) auf die freie Menge")
        vzr = "+" if e["realisiert_eur"] >= 0 else ""
        z.append(f"Davon realisiert {vzr}{eur(e['realisiert_eur'], 2)} EUR "
                 f"bei diesem Verkauf")
    if e.get("zu_klein"):
        z.append(f"!! Der Gegenwert liegt unter {eur(MINDEST_GEGENWERT_EUR, 0)} "
                 f"EUR - die Gebuehren stehen in keinem Verhaeltnis. Entweder "
                 f"ganz oder gar nicht.")
    return z


def _rang(p: dict) -> tuple:
    """Wonach die Sammelmail sortiert. NICHT nach Gegenwert.

    KORREKTUR 14.08. NACH DEM NACHLESEN. Meine erste Fassung sortierte nach
    Euro. Die dokumentierte Regel sortiert nach DRINGLICHKEIT
    (`backward_tracking`, Zeile 4930):

        "Dringlichstes zuerst: SCHLIESSEN, dann STOP NACHZIEHEN, dann der Rest
         - NICHT nach Buchgewinn. Der groesste ungesicherte Gewinn ist nicht
         automatisch der dringendste Fall."

    Dieselbe Logik gilt hier. Ein VERKAUFEN ueber eine kleine Position ist
    dringender als ein REDUZIEREN ueber eine grosse: das eine sagt "raus", das
    andere "weniger davon". Der Gegenwert entscheidet nur noch INNERHALB
    derselben Dringlichkeit."""
    v = p["verkauf"]
    # 0 = die deterministische Fuehrung sagt ebenfalls "schliessen" - das ist
    #     der einzige Fall, in dem sich beide Ebenen einig sind
    # 1 = ganze Position raus
    # 2 = Teilverkauf
    stufe = 1 if v["anteil"] >= 1.0 else 2
    if str((p.get("fuehrung") or {}).get("empfehlung", "")).startswith("SCHLIESSEN"):
        stufe = 0
    return (stufe, -v["gegenwert_eur"])


def sammel_mail(alle: list, modell: str | None = None,
                zeitpunkt: str | None = None) -> tuple | None:
    """EINE Mail fuer alle Ausstiege eines Laufs. `None`, wenn keiner anfiel.

    NUTZEREINWAND 14.08., NOCH WAEHREND DIESER UMBAU LIEF: *"45 Signale sind
    durchgekommen - 9 Spot, Rest irgendwas z.B. Verkaufen - das ist zu viel."*

    Er hat recht, und meine erste Fassung hat es SCHLIMMER gemacht: elf
    Einzelmails fuer die Verkaufsseite waeren zu den zehn Kaufmails
    dazugekommen. Einundzwanzig Mails aus einem Lauf - und die Verkaufsseite
    ist genau die, die man nicht uebersehen darf.

    DAS PROJEKT KENNT DIE ANTWORT SCHON. `ausstiegsrechnung.sammel_mail()`
    schreibt sie seit dem 13.08. auf:

        "Wer fuer eine nie eroeffnete Position geweckt wird, hoert nach der
         dritten Mail auf hinzusehen."

    Deshalb hier dieselbe Form: ein Ueberblick fuer den ganzen Lauf, nach
    Gegenwert sortiert - was am meisten Geld bewegt, steht oben. Die
    Einstiegsmails bleiben einzeln; sie sind seltener und tragen eine
    vollstaendige Planung, die sich nicht buendeln laesst.

    WARUM NICHT `ausstiegsrechnung.sammel_mail` DIREKT: die rechnet in R und
    verlangt Einstieg und Originalstop. Der Spot-Bestand hat keinen Stop -
    siehe Modulkopf.
    """
    from agent.signal_mail import eur, preis

    if not alle:
        return None
    posten = sorted(alle, key=_rang)
    summe = sum(p["verkauf"]["gegenwert_eur"] for p in posten)
    ganz = sum(1 for p in posten if p["verkauf"]["anteil"] >= 1.0)

    kopf = [f"{len(posten)} Positionen zum Verkauf vorgeschlagen - "
            f"{eur(summe, 2)} EUR Gegenwert"]
    if zeitpunkt or modell:
        kopf.append(" · ".join(x for x in (zeitpunkt,
                                           f"Modell {modell}" if modell else None)
                               if x))
    kopf += ["",
             "DIES IST KEINE GEWINNMITNAHME. Das Modell haelt diese Positionen",
             "fuer schwaecher als die Alternative - mehr sagt es nicht.",
             "Ausfuehrung manuell ueber die Bitpanda-App.", ""]

    zeilen = list(kopf) + ["--- WAS ZU TUN IST ---"]
    for p in posten:
        v = p["verkauf"]
        art = "GANZ" if v["anteil"] >= 1.0 else "ein Drittel"
        zeile = f"{p['symbol']:<10} {v['aktion']:<11} {art:<12} " \
                f"{eur(v['gegenwert_eur'], 2):>10} EUR"
        if "ergebnis_prozent" in v:
            vz = "+" if v["ergebnis_prozent"] >= 0 else ""
            zeile += f"   Stand {vz}{eur(v['ergebnis_prozent'], 1)} %"
        if v.get("zu_klein"):
            zeile += "   !! zu klein fuer einen Teilverkauf"
        zeilen.append(zeile)
        # DIE ZWEITE EBENE IN DERSELBEN ZEILE - der eigentliche Grund fuer
        # diesen Umbau. Fuer BTC liefen am 14.08. zwei Ausstiegswege parallel:
        # die deterministische Fuehrung (Trailing, taeglich 7:15) und dieses
        # Modellurteil aus dem 15-Minuten-Lauf. Der Nutzer haette zwei Mails
        # mit zwei Aussagen zum selben Symbol bekommen und keine Angabe,
        # welche gilt.
        #
        # SIE WIDERSPRECHEN EINANDER NICHT - sie beantworten verschiedene
        # Fragen ("gibt die Position Gewinn zurueck" gegen "traegt die These
        # noch"). Genau deshalb muessen sie nebeneinander stehen: getrennt
        # gelesen sehen sie aus wie zwei Meinungen, zusammen sind sie zwei
        # Befunde.
        f = p.get("fuehrung") or {}
        if f:
            teil = [f"Fuehrung: {f['empfehlung']}"] if f.get("empfehlung") else []
            if f.get("mfe_r") is not None:
                teil.append(f"hoechster Stand {f['mfe_r']:+.2f} R".replace(".", ","))
            if f.get("stop_neu") is not None:
                teil.append(f"Stop nachziehen auf {preis(f['stop_neu'])}")
            if teil:
                zeilen.append("           " + " · ".join(teil))

    zeilen += ["", "--- WARUM ---"]
    for p in posten:
        zeilen.append(f"{p['symbol']}: {p.get('begruendung') or '(keine Begruendung)'}")

    betreff = (f"TradingInfoTool: {len(posten)} Verkaufsvorschlaege "
               f"({eur(summe, 0)} EUR"
               + (f", davon {ganz} ganz" if ganz else "") + ")")
    return betreff, "\n".join(zeilen)
