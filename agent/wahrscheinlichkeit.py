# -*- coding: utf-8 -*-
"""Wie wahrscheinlich traegt dieser Trade? (22.08.2026)

DAS IST DAS EIGENTLICHE ZIEL DES SYSTEMS, und es war bis heute nicht gebaut.

Nutzereinwand, woertlich: *"Gefuehlt werden die Infos in die eMail uebernommen
- aber das System kann diese Informationen nicht SELBST in Zusammenhang
bringen und eine Bewertung bzw. Wahrscheinlichkeit zum gesamten Trade bzw.
Signal durchzufuehren - was das eigentliche Ziel des Systems ist und war."*

Er hat recht. `gesamtbild.py` ZAEHLT Etiketten ("1 spricht dafuer, 1 dagegen,
2 noch nicht bewertbar") - das ist eine Strichliste und laesst die
Zusammenfuehrung beim Leser. Genau die Arbeit, die das System machen soll.

⚠️ WARUM DAS FRUEHER RICHTIG WAR UND JETZT NICHT MEHR. Bis Kapitel 118 gab es
nichts Gemessenes zu addieren; eine Zahl zu bauen haette Sicherheit
vorgetaeuscht, wo keine war. Seit 119-122 gibt es zwei belastbare Groessen -
die Basisrate aus der Geometrie und den Vorsprung von H. Damit ist die
Zusammenfuehrung keine Behauptung mehr, sondern eine Rechnung.

DIE RECHNUNG, VOLLSTAENDIG:

    Basisrate   = 1 / (1 + CRV)          driftfreier Pfad, reine Arithmetik
    + Beitraege                          nur GEMESSENE Punkte
    = Quote                              geschaetzte Trefferquote
    Breakeven   = (1 + Kosten_R) / (1 + CRV)
    Kosten_R    = 2 * Gebuehr / Stopabstand
    Abstand     = Quote - Breakeven      DAS ist die Aussage

⚠️ WAS DIESE ZAHL NICHT IST. Keine Prognose fuer diesen einen Trade, sondern
die gemessene Haeufigkeit in einer Gruppe, zu der er gehoert. Und das LLM
steckt NICHT darin - dessen Urteil kommt daneben, nicht hinein
(Nutzervorgabe: "die LLM Bewertungen kommen dann on top").

⚠️ UND SIE IST ERWEITERBAR GEBAUT, WEIL SIE ES SEIN MUSS. Nutzervorgabe:
*"Wir muessen aus dem Fleckerteppich ein stabiles und erweiterbares System
bauen was auf einer guten Grundlage basiert."* Deshalb eine REGISTRIERUNG:
jeder Beitrag ist ein Eintrag mit Wert, Zustand, Quelle und Begruendung.
Kommt einer dazu oder wechselt seinen Zustand, ist das EINE Zeile - kein
Umbau der Rechnung, keine zweite Stelle, die auseinanderlaufen kann.

VIER ZUSTAENDE, DIE NIE VERSCHMELZEN - dieselbe Lehre wie bei
`lebendigkeit.ZUSTAENDE`:

    traegt        gemessen und ueber der Zufallsschwelle -> geht in die Zahl
    enthalten     steckt bereits in der Basisrate -> darf NICHT zweimal zaehlen
    null          gemessen und zu klein -> geht NICHT ein, wird GENANNT
    noch_nicht    die eigene Reihe ist zu kurz -> wird genannt, mit Termin
    nie           nie gemessen -> wird genannt, ohne Versprechen

Der Unterschied zwischen `null` und `nie` ist der wichtige: das eine heisst
"geprueft und zu klein", das andere "wir wissen es nicht". Wer sie
zusammenwirft, verliert genau die Information, die sagt, wo sich Arbeit lohnt.
"""
from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# DIE BASISRATE. Reine Arithmetik, kein Messwert - aber gemessen bestaetigt.
# ---------------------------------------------------------------------------
# Auf einem driftfreien Pfad trifft ein Barrierensystem sein Ziel mit
# 1/(1+CRV). Bei CRV 2,0 sind das 33,3 %; gemessen wurden 34,0 % ueber 19.891
# Anker - die 0,7 Punkte sind der leichte Aufwaertsdrift des Marktes.
#
# ⚠️ WIR RECHNEN MIT DER ARITHMETIK, NICHT MIT DEN 34,0 %. Der Drift ist
# nicht garantiert, und ihn einzurechnen hiesse, den guenstigsten der beiden
# Werte zu nehmen. Die vorsichtige Lesart ist hier die richtige.
BASISRATE_GEMESSEN = 0.340
BASISRATE_ANKER = 19891


def basisrate(crv: float) -> float:
    """Trefferquote eines Barrierensystems auf driftfreiem Pfad."""
    if not crv or float(crv) <= 0:
        raise WahrscheinlichkeitUnbekannt(f"CRV {crv!r} ist nicht positiv")
    return 1.0 / (1.0 + float(crv))


class WahrscheinlichkeitUnbekannt(RuntimeError):
    """Lieber keine Zahl als eine erfundene."""


@dataclass(frozen=True)
class Beitrag:
    """Ein Merkmal und was es zur Trefferquote beitraegt."""
    name: str
    zustand: str          # traegt | null | noch_nicht | nie
    punkte: float         # Prozentpunkte; nur bei `traegt` ungleich null
    quelle: str           # woher die Zahl stammt
    warum: str            # warum sie so ist, in einem Satz
    klassen: tuple = ()   # leer = alle; sonst nur diese Anlageklassen


ZUSTAENDE = ("traegt", "enthalten", "null", "noch_nicht", "nie")


# ---------------------------------------------------------------------------
# DIE REGISTRIERUNG. Hier wird erweitert - nirgends sonst.
# ---------------------------------------------------------------------------
BEITRAEGE = (
    Beitrag(
        name="Vorfilter H (Weg frei, Stop gedeckt)",
        zustand="traegt", punkte=4.5,
        quelle="Kapitel 108-122, 523 Reihen, Schwelle +2,6",
        warum="der einzige gemessene Kandidat, der die Zufallsschwelle nimmt",
        klassen=("krypto",)),
    Beitrag(
        name="Rangplatz in der Anlageklasse",
        zustand="null", punkte=0.0,
        quelle="messe_drift.py, 40 Reihen, 3.290 Termine",
        warum=("+0,51 % Vorteil auf fuenf Tage gegen 0,60 % Rundenkosten "
               "zum Referenzsatz - verfehlt um 0,10 Punkte"),
        klassen=("krypto",)),
    Beitrag(
        name="Lebendigkeit des Projekts",
        zustand="noch_nicht", punkte=0.0,
        quelle="93 C, sammelt seit 20.08.2026",
        warum="30 Tagesmessungen noetig, auswertbar ab 18.09.2026",
        klassen=("krypto",)),
    Beitrag(
        name="Bekannte Termine",
        zustand="nie", punkte=0.0,
        quelle="93 D",
        warum="Anzeige, nie gegen den Zufall gemessen"),
    Beitrag(
        name="Trichter (uebliche Kursbewegung)",
        zustand="enthalten", punkte=0.0,
        quelle="Kapitel 101",
        warum=("er BESTIMMT die Geometrie und damit die Basisrate - er ist "
               "schon drin und darf nicht zweimal zaehlen")),
)


def _gilt(b: Beitrag, klasse: str) -> bool:
    return not b.klassen or str(klasse or "").lower() in b.klassen


def rechne(*, crv: float, stop_relativ: float, gebuehr_je_seite: float,
           klasse: str = "", h: bool | None = None) -> dict:
    """Die vollstaendige Rechnung. WIRFT, statt zu raten.

    `h` ist das Ergebnis von `vorfilter.bewerte()["h"]` - `None` heisst
    unbekannt und traegt dann nichts bei, ohne als Nein zu gelten."""
    if not stop_relativ or float(stop_relativ) <= 0:
        raise WahrscheinlichkeitUnbekannt(
            f"Stopabstand {stop_relativ!r} ist nicht positiv")
    if gebuehr_je_seite is None or float(gebuehr_je_seite) < 0:
        raise WahrscheinlichkeitUnbekannt("Gebuehr fehlt")
    basis = basisrate(crv)

    zeilen, zuschlag = [], 0.0
    for b in BEITRAEGE:
        if not _gilt(b, klasse):
            zeilen.append({"name": b.name, "zustand": "nie", "punkte": 0.0,
                           "warum": f"auf {klasse or '?'} nie gemessen - "
                                    f"{b.quelle} steht auf Krypto"})
            continue
        zustand, punkte, warum = b.zustand, 0.0, b.warum
        # ⚠️ H IST DER EINZIGE BEITRAG, DER VOM SIGNAL ABHAENGT. Alle
        # anderen tragen aus ihrem Zustand heraus nichts bei; H nur dann,
        # wenn die Bedingung an DIESEM Anker auch wirklich zutrifft.
        if b.zustand == "traegt" and b.name.startswith("Vorfilter H"):
            if h is True:
                punkte = b.punkte
            elif h is False:
                zustand, warum = "null", "trifft an diesem Anker NICHT zu"
            else:
                zustand, warum = "nie", "an diesem Anker nicht bestimmbar"
        elif b.zustand == "traegt":
            punkte = b.punkte
        zuschlag += punkte
        zeilen.append({"name": b.name, "zustand": zustand,
                       "punkte": punkte, "warum": warum})

    quote = basis + zuschlag / 100.0
    kosten_r = 2.0 * float(gebuehr_je_seite) / float(stop_relativ)
    breakeven = (1.0 + kosten_r) / (1.0 + float(crv))
    return {"crv": float(crv), "basisrate": basis, "zuschlag_punkte": zuschlag,
            "quote": quote, "kosten_r": kosten_r, "breakeven": breakeven,
            "abstand_punkte": 100.0 * (quote - breakeven),
            "erwartungswert_r": quote * float(crv) - (1.0 - quote) - kosten_r,
            "beitraege": zeilen, "klasse": str(klasse or "").lower()}


def saetze(*, crv: float, stop_relativ: float, klasse: str = "",
           h: bool | None = None, saetze_zum_berichten=None) -> list[str]:
    """Die Zeilen fuer den Kopf der Mail.

    ⚠️ SIE SPERREN NICHTS. Auch "traegt nicht" ist kein Veto - es ist die
    Zusammenfassung dessen, was weiter unten ohnehin steht."""
    from agent.schreibweise import de

    if saetze_zum_berichten is None:
        saetze_zum_berichten = (("Referenz 0,30 %", 0.003),
                                ("Betrieb 1,50 %", 0.015))
    try:
        erste = rechne(crv=crv, stop_relativ=stop_relativ, klasse=klasse,
                       h=h, gebuehr_je_seite=saetze_zum_berichten[0][1])
    except WahrscheinlichkeitUnbekannt as exc:
        return ["Wie wahrscheinlich traegt dieser Trade?",
                f"   Nicht berechenbar: {exc}"]

    # ⚠️ EINE FESTE SPALTE FUER DIE ZAHLEN. Wer drei Prozentwerte
    # untereinander lesen soll, darf sie nicht suchen muessen.
    def _zeile(text: str, wert: str) -> str:
        return f"   {text:<52}{wert:>7}"

    aus = ["Wie wahrscheinlich traegt dieser Trade? (gerechnet, kein Urteil)",
           _zeile(f"Ausgangspunkt aus der Geometrie (CRV "
                  f"{de(erste['crv'], 1)})",
                  f"{de(100 * erste['basisrate'], 1)} %")]
    for z in erste["beitraege"]:
        if z["zustand"] == "traegt":
            aus.append(_zeile(f"+ {z['name']}", f"+{de(z['punkte'], 1)}"))
            aus.append(f"     ({z['warum']})")
    aus.append(_zeile("= geschaetzte Trefferquote",
                      f"{de(100 * erste['quote'], 1)} %"))

    # ⚠️ BEIDE SAETZE NEBENEINANDER - seit Kapitel 119 die Vorgabe. Ein
    # einzelner Satz beantwortet je nur eine der beiden Fragen.
    for name, satz in saetze_zum_berichten:
        r = rechne(crv=crv, stop_relativ=stop_relativ, klasse=klasse, h=h,
                   gebuehr_je_seite=satz)
        marke = "   " if r["abstand_punkte"] > 0 else "⚠️ "
        aus.append(f"{marke}noetig bei {name}: "
                   f"{de(100 * r['breakeven'], 1)} % -> "
                   f"{de(r['abstand_punkte'], 1)} Punkte, "
                   f"{'traegt' if r['abstand_punkte'] > 0 else 'traegt NICHT'}"
                   f" ({de(r['erwartungswert_r'], 3)} R je Trade)")

    # ⚠️ WAS NICHT DRINSTECKT, GEHOERT IN DIESELBE ZUSAMMENFASSUNG.
    # Ohne diese Zeilen liest sich die Quote, als waere alles beruecksichtigt
    # worden, was in der Mail steht - und drei Merkmale sind es nicht.
    enthalten = [z for z in erste["beitraege"]
                 if z["zustand"] == "enthalten"]
    for z in enthalten:
        aus.append(f"   Bereits enthalten: {z['name']} - {z['warum']}")
    offen = [z for z in erste["beitraege"]
             if z["zustand"] not in ("traegt", "enthalten")]
    if offen:
        aus.append("   Nicht eingerechnet, und warum:")
        for z in offen:
            aus.append(f"      {z['name']}: {z['warum']}")
    aus.append("⚠️ KEINE PROGNOSE FUER DIESEN TRADE, sondern die gemessene "
               "Haeufigkeit in einer Gruppe, zu der er gehoert. Das Urteil "
               "der Modelle steckt NICHT in dieser Zahl - es steht daneben.")
    return aus
