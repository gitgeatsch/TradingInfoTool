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

WAS DIESE DATEI TUT: sie schreibt fest, was eine Antwort enthalten muss, und lehnt
ab, was das nicht erfuellt - so wie `szenario_analyst._validate_szenario()` es fuer
die Verteilung tut. Eine Empfehlung ohne Betrag ist keine Empfehlung, sondern eine
Meinung.

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

# Die Tranchen aus der Praxis des Nutzers. Eine AUSWAHL, keine Rechnung.
TRANCHEN_EUR = (100, 300, 500)

# Aktionen, die ohne Betrag sinnlos waeren. NICHTS_TUN braucht keinen.
BRAUCHT_BETRAG = ("KAUFEN", "NACHKAUFEN", "REDUZIEREN", "VERKAUFEN")

# Aktionen, die einen Einstieg und einen Stop brauchen. Beim Verkauf ist der
# Einstieg gegenstandslos - man geht raus, nicht rein.
BRAUCHT_EINSTIEG = ("KAUFEN", "NACHKAUFEN")

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


def _zahl(wert) -> float | None:
    try:
        return float(str(wert).replace(",", ".").strip())
    except (TypeError, ValueError):
        return None


def validiere(antwort: dict, symbol: str = "?") -> dict:
    """Prueft den Vertrag. Wirft, wenn die Antwort keine Empfehlung ist."""
    if not isinstance(antwort, dict):
        raise EmpfehlungUngueltig(f"{symbol}: Antwort ist kein Objekt")

    fehlend = [f for f in REQUIRED_FELDER if not str(antwort.get(f) or "").strip()]
    if fehlend:
        raise EmpfehlungUngueltig(f"{symbol}: Felder fehlen oder sind leer: {fehlend}")

    aktion = antwort["aktion"]
    if aktion not in AKTIONEN:
        raise EmpfehlungUngueltig(
            f"{symbol}: aktion={aktion!r}, erlaubt {AKTIONEN}")

    # --- Der Betrag. Ohne ihn ist es eine Meinung, keine Empfehlung. --------
    if aktion in BRAUCHT_BETRAG:
        betrag = _zahl(antwort.get("tranche_eur"))
        if betrag is None:
            raise EmpfehlungUngueltig(
                f"{symbol}: '{aktion}' ohne tranche_eur - eine Empfehlung ohne "
                f"Betrag ist keine")
        if int(betrag) not in TRANCHEN_EUR:
            raise EmpfehlungUngueltig(
                f"{symbol}: tranche_eur={betrag}, erlaubt {TRANCHEN_EUR} - "
                f"das Modell waehlt eine Tranche, es rechnet keine aus")

    # --- Kurs und Stop, beide in EUR. --------------------------------------
    if aktion in BRAUCHT_EINSTIEG:
        for feld in ("einstieg_eur", "stop_eur"):
            if _zahl(antwort.get(feld)) is None:
                raise EmpfehlungUngueltig(
                    f"{symbol}: '{aktion}' ohne {feld} - im KAS-Fall vom 15.07. "
                    f"waren genau diese beiden Felder leer")
        einstieg, stop = _zahl(antwort["einstieg_eur"]), _zahl(antwort["stop_eur"])
        if stop >= einstieg:
            raise EmpfehlungUngueltig(
                f"{symbol}: stop_eur {stop} liegt nicht unter einstieg_eur "
                f"{einstieg} - bei einem Kauf muss der Stop darunter liegen")

    # --- Die Begruendung muss die Aktion TRAGEN. ---------------------------
    if aktion != "NICHTS_TUN":
        b = str(antwort["begruendung"]).lower()
        treffer = [w for w in RELATIVIERER if w in b]
        if treffer:
            raise EmpfehlungUngueltig(
                f"{symbol}: die Begruendung zieht sich selbst zurueck ({treffer}) - "
                f"Gegengruende gehoeren nach 'was_dagegen', wo sie sichtbar sind")
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
