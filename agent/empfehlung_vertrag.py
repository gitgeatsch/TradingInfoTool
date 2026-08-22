# -*- coding: utf-8 -*-
"""Was eine Empfehlung enthalten MUSS, damit sie eine ist (10.08.2026).

DER ANLASS ist ein echtes Signal aus der Datenbank - KAS, 15.07., Konfidenz 78 %:

    aktion        NACHKAUFEN
    begruendung   "Technisch leichte Erholung ueber dem naechsten Widerstand bei
                   ~0.037 USD, Risiko-Reward >2, aber weiterhin bearishes
                   Marktumfeld."
    prognose      "Preis bleibt seitwaerts zwischen 0.025 USD und 0.037 USD"
    risiken       "... Bestehender Verlust von -14,6 % auf der Position ..."
    entry_eur     leer
    stop_loss_eur leer

Vier Maengel in einer Antwort: keine Menge, kein Kurs, kein Stop; die Begruendung
relativiert sich selbst ("aber weiterhin bearisch"); und die Prognose widerspricht
der Aktion - wer Seitwaerts erwartet, kauft nicht in eine Position mit 14,6 %
Verlust nach.

Der Nutzer dazu: *"ich brauche konkrete Handlungsempfehlung und Begruendung"* und
*"mit +1R fange ich nichts an - EURO und Prozent bitte"*.

WAS DIESE DATEI TUT: sie schreibt fest, was eine Antwort enthalten muss - und
holt nach, was fehlt, statt zu verwerfen.

DREI STUFEN, nach dem Einwand des Nutzers am 10.08. ("damit wir nichts blocken"):

  KORRIGIEREN   fehlender oder verfehlter Betrag -> kleinste Tranche
  DEGRADIEREN   Kauf ohne Ausstieg oder mit Stop ueber dem Einstieg ->
                die Handlung wird auf NICHTS_TUN zurueckgenommen, die Analyse
                bleibt erhalten. Das ist gefaehrlich, nicht nur unvollstaendig.
  WARNEN        eine Begruendung, die sich selbst zurueckzieht -> Vermerk

ABGELEHNT WIRD NUR: eine Antwort ohne `aktion` oder mit einer erfundenen. Ohne
sie gibt es keine Empfehlung, und es gibt nichts, was man daraus retten koennte.

Jede Nachbesserung steht IN der Antwort (`_korrekturen`, `_degradiert`,
`_warnung`, `_luecken`) und geht in den Datensatz. Haeufen sich dieselben,
ist das ein Befund ueber den PROMPT - dann gehoert er repariert, nicht die
Antwort weggeworfen.

WAS SIE BEWUSST NICHT TUT: Positionsgroessen rechnen. Der Nutzer setzt den Betrag
selbst (100/300/500 EUR, seit 02.08. festgehalten) - aus geringem Kapital und noch
fehlendem Vertrauen ins Regelwerk. Die vier Positionsgroessen-Deckel im Regelwerk
kappen eine Obergrenze, die er ohnehin nicht ausschoepft; das Cash-Veto hat in 118
Signalen kein einziges Mal gegriffen. Das Modell waehlt also eine Tranche, es
berechnet keine.

Cash bleibt eine INFORMATION, kein Veto: "dein Cash traegt 5 solche Tranchen".
Wenn real gehandelt wird, wird daraus eine Regel - bis dahin steht sie nicht im Weg.
"""
from __future__ import annotations

AKTIONEN = ("KAUFEN", "NACHKAUFEN", "REDUZIEREN", "VERKAUFEN", "NICHTS_TUN")

# ⚠️ S6a (22.08.2026): EIN VOKABULAR FUER BEIDE INSTRUMENTE.
#
# Bis heute hatte Hebel sieben Aktionen und Spot fuenf. Inhaltlich waren es
# DIESELBEN fuenf Vorgaenge unter zwei Namen:
#
#     Position eroeffnen   KAUFEN      <->  ERÖFFNEN
#     vergroessern         NACHKAUFEN  <->  NACHKAUFEN
#     verkleinern          REDUZIEREN  <->  TEILVERKAUF
#     schliessen           VERKAUFEN   <->  SCHLIESSEN
#     nichts tun           NICHTS_TUN  <->  HALTEN
#
# DAS VERB TRUG DAMIT EINE INSTRUMENTENDEUTUNG, die ihm nicht gehoert. Wer
# "ERÖFFNEN" liest, denkt an eine gehebelte Position - auch dort, wo die
# Rechnung Hebel 1,0 ergibt (in 76 % der Faelle, Kapitel 129).
#
# JETZT SAGT DIE AKTION, WAS GETAN WIRD, UND DAS INSTRUMENT, WIE.
# Zwei Dinge, zwei Felder. Das Instrument faellt aus `dimensioniere()` an
# und steht in `etikett` - es muss nicht im Verb mitreisen.
#
# ⚠️ HEBEL_ERHÖHEN UND HEBEL_SENKEN ENTFALLEN ERSATZLOS, und zwar nicht aus
# Bequemlichkeit: sie lassen das MODELL den Hebelfaktor aendern. Das
# widerspricht dem Regelwerksmanual Abschnitt A ("der Hebelfaktor kommt
# nicht vom Modell, er folgt aus Risikobudget und Liquidationsabstand").
# Gemessen kamen sie in 1.998 Hebel-Signalen ZWEIMAL vor, und die neue Kette
# kannte sie ohnehin nicht.
#
# DIE ALTE KETTE BLEIBT UNBERUEHRT. `hebel_analyst.REQUIRED_HEBEL_ACTIONS`
# fuehrt weiter die sieben Namen; sie schreibt in `hebel_signals` und laeuft
# fuer Krypto nicht mehr. Ein Eingriff dort waere Arbeit an einem toten Pfad.
AKTIONEN_HEBEL = AKTIONEN

# Das alte Hebel-Vokabular - NUR fuer die Abbildung bestehender Zeilen und
# fuer die Gegenpruefung, die noch mit `hebel_signals` arbeitet.
AKTIONEN_HEBEL_ALT = ("ERÖFFNEN", "NACHKAUFEN", "HEBEL_ERHÖHEN",
                      "HEBEL_SENKEN", "TEILVERKAUF", "SCHLIESSEN", "HALTEN")

# Alt -> neu. EINE Stelle; wer sie umgeht, baut die zweite Schreibweise.
AKTION_AUS_HEBEL = {"ERÖFFNEN": "KAUFEN", "TEILVERKAUF": "REDUZIEREN",
                    "SCHLIESSEN": "VERKAUFEN", "HALTEN": "NICHTS_TUN",
                    "NACHKAUFEN": "NACHKAUFEN"}

# Nur diese eroeffnen oder vergroessern eine Position - nur sie brauchen eine
# Richtung und eine Einstiegsrechnung.
# Welche Aktionen eine Richtung BRAUCHEN. Nur die beiden Einstiege: dort
# entscheidet LONG oder SHORT, wo Stop und Ziel liegen.
#
# ⚠️ UMBENANNT (S6c, 22.08.2026). Der alte Name `HEBEL_MIT_EINSTIEG` stammt
# aus der Zeit, als nur der Hebel eine Richtung kannte. Seit S6a fragt die
# Kette sie fuer BEIDE Instrumente - der Name behauptete etwas, das nicht
# mehr stimmt, und genau dieser Name stand in der Bedingung, die den Fehler
# unten verdeckt hat.
BRAUCHT_RICHTUNG = ("KAUFEN", "NACHKAUFEN")
HEBEL_MIT_EINSTIEG = BRAUCHT_RICHTUNG          # alter Name, gleiche Sache

# Die Richtung ist die EINZIGE zusaetzliche Angabe, die das Modell fuer Hebel
# liefert. Der Hebelfaktor NICHT: er folgt aus Risikobudget und
# Liquidationsabstand (entscheidungsrechnung), und Kapitel 11.6 haelt fest,
# dass Risikoparameter nicht vom Modell kommen.
RICHTUNGEN = ("LONG", "SHORT")


def aktionen_fuer(instrument: str = "spot") -> tuple:
    """Das Aktionsvokabular. SEIT S6a FUER BEIDE INSTRUMENTE DASSELBE.

    Der Parameter bleibt, damit kein Aufrufer bricht - und damit die Stelle
    auffaellt, falls je wieder zwei Vokabulare gewollt sein sollten. Heute
    gibt sie fuer jedes Instrument dieselbe Liste zurueck."""
    del instrument
    return AKTIONEN

# Die Tranchen aus der Praxis des Nutzers. Eine AUSWAHL, keine Rechnung.
TRANCHEN_EUR = (100, 300, 500)

# Aktionen, die ohne Betrag sinnlos waeren. NICHTS_TUN braucht keinen.
BRAUCHT_BETRAG = ("KAUFEN", "NACHKAUFEN", "REDUZIEREN", "VERKAUFEN")

# Aktionen, die einen Einstieg und einen Stop brauchen. Beim Verkauf ist der
# Einstieg gegenstandslos - man geht raus, nicht rein.
# ⚠️ "ERÖFFNEN" FEHLTE HIER (S3, 18.08.2026). Die Pruefung unten galt nur
# fuer KAUFEN und NACHKAUFEN - die HAUPT-Hebelaktion war damit die einzige
# Einstiegsaktion ohne jede Kontrolle.
BRAUCHT_EINSTIEG = ("KAUFEN", "NACHKAUFEN", "ERÖFFNEN")

REQUIRED_FELDER = (
    "aktion",
    "begruendung",
    "was_dagegen",
    "umgeworfen_durch",
)

# Wortpaare, die eine Begruendung entwerten, wenn sie die Aktion tragen soll.
# Der KAS-Fall enthielt "aber weiterhin bearishes Marktumfeld" - ein Nachsatz,
# der die eigene Empfehlung zurueckzieht. Das gehoert nach `was_dagegen`, wo es
# sichtbar ist, nicht in die Begruendung, wo es sie aushoehlt.
RELATIVIERER = ("aber weiterhin", "allerdings weiterhin", "wenngleich",
                "trotz des", "obwohl weiterhin")


class EmpfehlungUngueltig(ValueError):
    """Die Antwort ist keine Empfehlung - mit Angabe, woran es fehlt."""


# Die Ableitung Faktoren -> Tranche. EINE SETZUNG, keine Messung - und als
# solche gekennzeichnet, damit sie spaeter pruefbar bleibt.
#
# Warum sie hier steht und nicht im Modell: extern belegt sind LLMs bei der
# Positionsgroesse am schwaechsten, und das Designmuster der Praxis entkoppelt
# ausdruecklich "Richtungslogik" von "quantitativer Positionsgroessenbestimmung".
# Das Modell liefert, was es kann - die Zahl der UNABHAENGIGEN Belege, also ob
# drei Belege drei Dinge sagen oder dreimal dasselbe. Das Rechnen machen wir.
#
# Die Schwelle bei drei stammt aus der Praxisliteratur: drei bis vier
# unabhaengige Faktoren sind der Bereich fuer einen tragfaehigen Aufbau, eins
# bis zwei sind duenn.
TRANCHE_JE_FAKTOREN = ((3, 500), (2, 300), (1, 100))


def tranche_aus_faktoren(faktoren: int) -> int | None:
    """Der Betrag folgt aus der Zahl unabhaengiger Belege - nicht aus dem Modell."""
    try:
        n = int(faktoren)
    except (TypeError, ValueError):
        return None
    for schwelle, betrag in TRANCHE_JE_FAKTOREN:
        if n >= schwelle:
            return betrag
    return None


def _zahl(wert) -> float | None:
    try:
        return float(str(wert).replace(",", ".").strip())
    except (TypeError, ValueError):
        return None


def validiere(antwort: dict, symbol: str = "?",
              instrument: str = "spot",
              kurs: float | None = None) -> dict:
    """Prueft den Vertrag. Wirft, wenn die Antwort keine Empfehlung ist."""
    if not isinstance(antwort, dict):
        raise EmpfehlungUngueltig(f"{symbol}: Antwort ist kein Objekt")

    # NUR `aktion` ist hart: ohne sie gibt es keine Empfehlung. Fehlt eine
    # Begruendung oder ein Gegengrund, ist die Antwort duerftig - aber eine
    # duerftige Empfehlung ist mehr wert als gar keine, und die Luecke steht
    # sichtbar im Protokoll.
    if not str(antwort.get("aktion") or "").strip():
        raise EmpfehlungUngueltig(f"{symbol}: ohne 'aktion' gibt es keine Empfehlung")
    luecken = [f for f in REQUIRED_FELDER
               if f != "aktion" and not str(antwort.get(f) or "").strip()]
    if luecken:
        for f in luecken:
            antwort.setdefault(f, "")
        antwort["_luecken"] = f"ohne Angabe: {', '.join(luecken)}"

    # Schreibweise vereinheitlichen - "kaufen", "Kaufen", " KAUFEN " sind
    # dieselbe Aktion. SYNONYME werden bewusst NICHT geraten: der Unterschied
    # zwischen VERKAUFEN und REDUZIEREN ist Geld, und ein falsch geratenes Wort
    # waere hier teurer als eine abgelehnte Antwort. Das ist die einzige Stelle
    # im ganzen Vertrag, an der Strenge billiger ist als Grosszuegigkeit.
    aktion = str(antwort["aktion"]).strip().upper().replace(" ", "_").replace("-", "_")
    erlaubt = aktionen_fuer(instrument)
    if aktion not in erlaubt:
        raise EmpfehlungUngueltig(
            f"{symbol}: aktion={antwort['aktion']!r}, erlaubt {erlaubt}")
    antwort["aktion"] = aktion

    # --- Die Richtung. Nur wo sie etwas bedeutet - aber dort IMMER. -------
    #
    # ⚠️ HIER STAND `instrument == "hebel" and ...`, UND DAS WAR SEIT S6b EINE
    # TOTE PRUEFUNG. S6b laesst Krypto nur noch mit instrument="spot" laufen -
    # die Bedingung war damit nie wieder wahr, und die Richtungspflicht war
    # ersatzlos weg, ohne dass irgendwo etwas rot wurde.
    #
    # ZWEI WEGE, AUF DENEN DAS TEUER GEWORDEN WAERE:
    #
    #   1  Ein KAUFEN ohne Richtung waere durchgegangen. Die Aufloesung faellt
    #      dann auf `richtung_aus_action()` zurueck und liest LONG - bei einem
    #      gemeinten SHORT sind Stop und Ziel vertauscht, und zwar still.
    #   2  Ein REDUZIEREN MIT `richtung="LONG"` waere gespeichert worden. Das
    #      Feld beschreibt dort die BESTEHENDE Position, nicht die Zonen (so
    #      stand es schon im G-Prompt der alten Kette) - die Aufloesung haette
    #      es als Zonenrichtung gelesen und den Teilverkauf bullisch bewertet.
    #
    # GEMESSEN, NICHT VERMUTET (DB-Kopie 19.08.): 415 Zeilen der alten
    # Hebelkette, wo die Pflicht galt - 315 LONG, 100 SHORT, KEINE ohne
    # Richtung. 41 KAUFEN der Spot-Kette, wo sie nicht galt - alle ohne. Das
    # Modell liefert sie, wenn sie verlangt wird; der Prompt verlangt sie seit
    # S6a fuer beide Instrumente. Das Ablehnungsrisiko ist damit belegt klein.
    #
    # `instrument` bleibt im Aufruf - es steuert weiterhin den Aktionssatz.
    if aktion in BRAUCHT_RICHTUNG:
        richtung = str(antwort.get("richtung") or "").strip().upper()
        if richtung not in RICHTUNGEN:
            # KEINE VORSICHTIGE ANNAHME. Bei der Tranche ist die kleinste
            # Groesse die vorsichtige Antwort; bei der Richtung gibt es
            # keine - LONG statt SHORT ist nicht "weniger", sondern das
            # Gegenteil. Wer sie nicht nennt, hat nicht entschieden.
            raise EmpfehlungUngueltig(
                f"{symbol}: {aktion} ohne Richtung - erlaubt {RICHTUNGEN}, "
                f"bekommen {antwort.get('richtung')!r}")
        antwort["richtung"] = richtung
    else:
        # ⚠️ UND SONST WEG DAMIT. Bei REDUZIEREN, VERKAUFEN und NICHTS_TUN
        # beschreibt `richtung` nicht die Zonen, sondern hoechstens die
        # bestehende Position oder eine allgemeine Markterwartung. Wer sie
        # spaeter liest, kann das nicht unterscheiden - und `check_signal_
        # outcome()` liest genau dieses Feld mit Vorrang vor der Ableitung.
        #
        # EIN FELD, DAS ZWEI DINGE HEISSEN KANN, IST SCHLIMMER ALS KEINES.
        antwort.pop("richtung", None)

    # --- Der Betrag. Ohne ihn ist es eine Meinung, keine Empfehlung. --------
    if aktion in BRAUCHT_BETRAG:
        betrag = _zahl(antwort.get("tranche_eur"))
        if betrag is None or int(betrag) not in TRANCHEN_EUR:
            # KLEINSTE TRANCHE statt Ablehnung. Das Modell hat gehandelt und
            # den Betrag vergessen oder verfehlt - die kleinste Groesse ist die
            # vorsichtige Antwort darauf und rettet die Analyse.
            vorher = antwort.get("tranche_eur")
            antwort["tranche_eur"] = min(TRANCHEN_EUR)
            antwort["_korrekturen"] = ((antwort.get("_korrekturen", "") + "; ")
                                       if antwort.get("_korrekturen") else "") + (
                f"tranche_eur {vorher!r} auf {min(TRANCHEN_EUR)} gesetzt")

    # --- Der Widerlegungspreis muss zur Richtung passen. -------------------
    #
    # ⚠️ HIER STANDEN `einstieg_eur` UND `stop_eur` (bis 18.08.2026, S3).
    #
    # Beide wurden vom Modell VERLANGT, von `rechne()` NIE gelesen - und
    # konnten den Trade trotzdem toeten: fehlten sie, oder lag der Stop nicht
    # unter dem Einstieg, wurde die Aktion auf NICHTS_TUN zurueckgenommen.
    # Zwei Zahlen, die ein Sprachmodell nicht schaetzen kann, entschieden
    # ueber einen Handel, dessen Zahlen woanders gerechnet werden.
    #
    # UND DIE PRUEFUNG KANNTE KEINE RICHTUNG. Bei einem SHORT liegt der Stop
    # korrekterweise UEBER dem Einstieg - ein SHORT-NACHKAUFEN mit richtigem
    # Stop wurde damit still zu NICHTS_TUN. Dieselbe Klasse wie die 313
    # SHORT-Vorschlaege, die als HALTEN in der Datenbank lagen.
    #
    # WAS STATTDESSEN GEPRUEFT WIRD: der Widerlegungspreis - die eine Zahl,
    # die dem Modell gehoert, weil sie ein Urteil ueber die eigene
    # Begruendung ist und kein Risikoparameter.
    if aktion in BRAUCHT_EINSTIEG:
        _wid = _zahl(antwort.get("umgeworfen_preis_eur"))
        _ist_short = str(antwort.get("richtung") or "").upper() == "SHORT"
        grund = None
        # ⚠️ FEHLEN IST ERLAUBT. Das Schema laesst null ausdruecklich zu:
        # nicht jede Beobachtung hat einen Kurs, und eine erzwungene Zahl
        # waere erfunden. Nur ein WIDERSPRUCH wird beanstandet.
        if _wid is not None and isinstance(kurs, (int, float)) and kurs > 0:
            if _ist_short and _wid <= float(kurs):
                grund = (f"Widerlegungspreis {_wid} liegt bei SHORT nicht "
                         f"ueber dem Kurs {kurs}")
            elif not _ist_short and _wid >= float(kurs):
                grund = (f"Widerlegungspreis {_wid} liegt bei LONG nicht "
                         f"unter dem Kurs {kurs}")
        if isinstance(grund, tuple):
            grund = "".join(grund)
        if grund:
            antwort["aktion"] = "NICHTS_TUN"
            antwort["_degradiert"] = (
                f"'{aktion}' auf NICHTS_TUN zurueckgenommen: {grund}")
            return antwort

    # --- Die Begruendung sollte die Aktion TRAGEN --------------------------
    # WARNUNG STATT ABLEHNUNG (Nutzerentscheidung 10.08.): ein hedgender Text
    # ist unschoen, aber eine verworfene Antwort ist schlimmer - sie erzeugt
    # eine Wiederholung und am Ende kein Signal. Die Warnung geht mit der
    # Antwort weiter und wird gezaehlt; haeufen sich diese Faelle, ist der
    # Prompt schuld und gehoert repariert, nicht die Antwort weggeworfen.
    if aktion != "NICHTS_TUN":
        b = str(antwort.get("begruendung") or "").lower()
        treffer = [w for w in RELATIVIERER if w in b]
        if treffer:
            antwort["_warnung"] = (
                f"die Begruendung zieht sich selbst zurueck ({', '.join(treffer)}) - "
                f"Gegengruende gehoeren nach 'was_dagegen'")
    return antwort


def pruefe_widerspruch(antwort: dict, prognose: str | None) -> str | None:
    """Passt die Prognose zur Aktion? Gibt den Widerspruch zurueck, sonst None.

    Im KAS-Fall lautete die Prognose "Preis bleibt seitwaerts" bei Aktion
    NACHKAUFEN. Das ist kein Grenzfall, sondern ein offener Widerspruch: wer
    keine Bewegung erwartet, hat keinen Grund nachzukaufen - schon gar nicht in
    eine Position mit 14,6 % Verlust.

    Bewusst als eigene Funktion und nicht im Validator: der Widerspruch macht die
    Antwort nicht formal ungueltig, er gehoert dem Nutzer VORGELEGT. Ein hartes
    Ablehnen wuerde eine Information verschlucken, die er sehen soll."""
    if not prognose:
        return None
    p = prognose.lower()
    aktion = antwort.get("aktion")
    seitwaerts = any(w in p for w in ("seitwärts", "seitwaerts", "range",
                                      "bleibt zwischen", "keine klare richtung"))
    faellt = any(w in p for w in ("fällt", "faellt", "abwärts", "abwaerts",
                                 "rückgang", "ruecktritt", "tiefer"))
    if aktion in ("KAUFEN", "NACHKAUFEN"):
        if seitwaerts:
            return (f"Die Prognose erwartet keine Bewegung, die Empfehlung lautet "
                    f"{aktion}. Ohne erwartete Bewegung gibt es keinen Grund "
                    f"einzusteigen.")
        if faellt:
            return (f"Die Prognose erwartet fallende Kurse, die Empfehlung lautet "
                    f"{aktion}.")
    return None


def cash_hinweis(cash_eur: float | None, tranche_eur: float | None) -> str | None:
    """Cash als INFORMATION, nicht als Veto (Nutzerentscheidung 10.08.).

    *"das war noch kein problem wird aber eines wenn gehandelt wird - darum in
    unserem Konzept damit einfacher umgehen als es in der Praxis dann ist."*

    Also: eine Zeile, die sagt, wie weit das Geld reicht. Keine Regel, die eine
    Empfehlung unterdrueckt - das Cash-Veto hat in 118 Signalen ohnehin kein
    einziges Mal gegriffen."""
    if not cash_eur or not tranche_eur or tranche_eur <= 0:
        return None
    n = int(cash_eur // tranche_eur)
    if n <= 0:
        return f"Dein Cash ({cash_eur:.0f} EUR) reicht fuer diese Tranche nicht."
    return f"Dein Cash ({cash_eur:.0f} EUR) traegt {n} solche Tranchen."
