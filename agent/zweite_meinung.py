# -*- coding: utf-8 -*-
"""Z.ai als unabhaengige Bewertungsstufe der Rollen-Kette (Kapitel 15,
13.08.2026).

DER NAME IST ABSICHT. Es gibt in diesem Projekt bereits `gegenpruefer_rollen`
(Z1) - und der Nutzer hat die beiden im Gespraech verwechselt, zu Recht:

    Z1 - gegenpruefer_rollen.py   DETERMINISTISCH. Prueft die Antwort gegen
                                  ihre eigene Faktenlage: Zahlendeckung,
                                  Richtungstreue, Zuspitzung, Leerlauf.
                                  Fragt NICHT, ob das Urteil klug ist.
    Z.ai - dieses Modul           EIN ZWEITES MODELL. Fragt genau das.

Zwei Ebenen, zwei Fragen. `zweite_meinung` heisst dieses Modul, damit die
Verwechslung nicht ueber den Dateinamen zurueckkommt.

WAS Z.AI SIEHT - Nutzervorgabe 13.08.: *"ohne Metalabels ... bzw.
zahlenangaben, konstanten etc. also Text"*:

    Konsistenz      Faktentext + Begruendungstext + Aktion
    Eigene Richtung Faktentext ALLEIN

WAS ES NICHT SIEHT, und warum jeweils:

    die gerechnete Geometrie   Stop, Ziel, Betrag, CRV liegen auf der
                               deterministischen Schiene. Das Modell hat sie
                               nicht erzeugt und soll sie nicht beurteilen.
    die Trefferbilanz          Die Tabelle entsteht AUS den Urteilen des
                               Modells. Sie ihm zurueckzugeben macht aus einer
                               Messung eine Rueckkopplung (siehe
                               trefferbilanz.py, Abschnitt Zirkularitaet).
    Aktion und Begruendung     NUR beim Richtungsabgleich. Sonst echot das
    (beim Richtungsabgleich)   zweite Modell das erste - der Anker-Effekt, den
                               `baue_objektive_fakten()` in der alten Kette
                               schon durch Weglassen vermeidet.

DER FAKTENTEXT WIRD UNVERAENDERT DURCHGEREICHT. Er ist bereits nach R-T1..R-T9
gebaut: relativ vor absolut, benanntes Fenster, keine rohen Zahlenreihen. Ihn
hier noch einmal umzubauen hiesse, dieselbe Regel an zwei Orten zu pflegen -
und einer von beiden waere irgendwann der aeltere.

WARUM DIESES MODUL NICHT `fuehre_beide_calls_im_hintergrund()` RUFT, obwohl es
genau das zu tun scheint: jene Funktion oeffnet ihre Verbindung selbst, mit
`db.get_connection()` - fest auf die PRODUKTIVDATEI. Ein Probelauf gegen eine
Kopie wuerde sein Z.ai-Ergebnis dort hineinschreiben, auf eine `signal_id`, die
in der Produktivdatei ein anderes Signal bezeichnet. Diese Kette bekommt ihre
Verbindung uebergeben, und das gilt auch fuer den Nebenweg.

DER PREIS: 3 sequenzielle Z.ai-Aufrufe je Einstieg (1 Konsistenz + 2 fuer die
positionsrobuste Richtung), typisch 12-25 s je Aufruf. Deshalb der Deckel unten
- lieber eine Mail ohne die Gegenpruefungszeilen als keine Mail (P-8)."""
from __future__ import annotations

import logging
import threading

logger = logging.getLogger(__name__)

# DIESELBE ZAHL WIE IN DER ALTEN KETTE (`scheduler/background.py:2160`), aber
# BEWUSST NICHT VON DORT IMPORTIERT: der Scheduler importiert die Agenten, nicht
# umgekehrt. Eine Abhaengigkeit zurueck waere ein Ring, und der faellt beim
# ersten Import auf, der die Reihenfolge dreht.
#
# Sie deckt den schlimmsten Fall NICHT ab (3 x 150 s Timeout = 450 s) - das ist
# keine Luecke, sondern P-8: bei einem Z.ai-Timeout geht die Mail OHNE die
# Gegenpruefungszeilen raus statt gar nicht.
WARTE_MAX_SEKUNDEN = 240

# ---------------------------------------------------------------------------
# EIGENE PROMPTS, WEIL DIE ALTEN EINE ANDERE FAKTENFORM BESCHREIBEN.
#
# GEFUNDEN IN DER GEGENPRUEFUNG ZU DIESEM SCHRITT, an einem echten Faktentext.
# Die Prompts der alten Kette versprechen dem Modell etwas, das die Rollen-
# Kette gar nicht schickt:
#
#   SYSTEM_PROMPT_RICHTUNG  "technische Indikatoren, Marktregime,
#                           Funding-Rate, Optionsmarkt-Daten" - die Kette
#                           liefert KEINEN dieser vier Bloecke.
#   SYSTEM_PROMPT           spricht von einem "Krypto-Hebel-Signal" und
#                           erklaert ueber die halbe Laenge die Bedeutung von
#                           `richtung`/`action` - beides Felder, die im
#                           Faktentext nicht vorkommen.
#
# Ein Modell, dem man eine Struktur ankuendigt, die es nicht vorfindet, liefert
# trotzdem eine Antwort - und man sieht ihr nicht an, dass sie auf einer
# falschen Erwartung beruht. Genau deshalb sind es zwei eigene Prompts und
# keine Wiederverwendung.
#
# WAS SIE BESCHREIBEN, ist die Form, die `rollen_eingabe.baue_fall()` wirklich
# baut: benannte Bloecke aus GANZEN SAETZEN (`auftrag`, `stand`), relativ vor
# absolut, keine rohen Zahlenreihen.

SYSTEM_KONSISTENZ = (
    "Du bekommst Marktfakten zu einem Krypto-Wert als benannte Bloecke aus "
    "ganzen Saetzen, dazu einen kurzen Begruendungstext, der fuer eine "
    "Handelsentscheidung vorgebracht wurde. Deine einzige Aufgabe: pruefe, ob "
    "der Begruendungstext den gegebenen Fakten WIDERSPRICHT - unabhaengig "
    "davon, wie ueberzeugend er klingt. Die Fakten sind die einzige "
    "Wahrheitsquelle, der Text ist eine zu pruefende Behauptung. Bezieht sich "
    "der Text auf etwas, das nicht in den Fakten steht, ist das KEIN "
    "Widerspruch - dir fehlt dann nur Kontext. Erfinde NIEMALS eigene Fakten. "
    "Die Fakten nennen bewusst keine Kursziele, keine Stopkurse und keine "
    "Positionsgroessen; dass sie fehlen, ist kein Widerspruch. "
    "Antworte AUSSCHLIESSLICH mit JSON, exakt diese zwei Felder: "
    '{"urteil": "konsistent" oder "widerspruch", "kurzbegruendung": '
    '"<= 12 Woerter"}.')

SYSTEM_RICHTUNG = (
    "Du bekommst ausschliesslich Marktfakten zu einem Krypto-Wert als benannte "
    "Bloecke aus ganzen Saetzen: Kursentwicklung ueber mehrere Fenster, "
    "Marktstruktur, naechste Unterstuetzung und Widerstand, Umsatzverteilung, "
    "gegebenenfalls ein bestehender Bestand. Du kennst KEINE Empfehlung eines "
    "anderen Modells. Deine Aufgabe: leite ALLEIN aus diesen Fakten deine "
    "eigene Markteinschaetzung ab - LONG (bullisch), SHORT (baerisch) oder "
    "NEUTRAL (keine klare Tendenz). Ein bestehender Bestand und sein Gewinn "
    "oder Verlust sagen NICHTS ueber die kuenftige Richtung - beziehe ihn "
    "nicht ein. Erfinde NIEMALS eigene Fakten, nutze nur die gegebenen. "
    "Antworte AUSSCHLIESSLICH mit JSON, exakt diese zwei Felder: "
    '{"eigene_richtung": "LONG" oder "SHORT" oder "NEUTRAL", '
    '"kurzbegruendung": "<= 12 Woerter"}.')


def hole(*, faktentext: dict, urteil: dict, zai_client,
         warte_max_s: float = WARTE_MAX_SEKUNDEN) -> dict:
    """Beide Z.ai-Aufrufe, begrenzt auf `warte_max_s`. Nie eine Ausnahme.

    KEIN POLLING, anders als in der alten Kette - und das ist kein Stilfrage.
    Dort wird gepollt, weil der Z.ai-Thread anderswo gestartet wird und der
    Versand keinen Griff darauf hat: er kann nur wiederholt in die Datenbank
    schauen. Hier gehoeren beide Seiten demselben Aufrufer, also genuegt ein
    `join(timeout=...)`. Das spart im Normalfall bis zu drei Sekunden je Signal
    und macht den Zeitpunkt exakt statt gerastert.

    Gibt immer ein Dict zurueck; leer heisst 'nichts bekommen'. Ein Fehlschlag
    der Gegenpruefung darf ein Signal nicht verhindern (P-8) - sie ist eine
    Zusatzinformation, keine Bedingung."""
    if zai_client is None:
        return {}
    from agent.krypto import gegenpruefung as G

    aktion = str(urteil.get("aktion") or "")
    aus: dict = {}

    def arbeite() -> None:
        # ZWEI GETRENNTE try-BLOECKE, kein gemeinsamer. Faellt der
        # Konsistenz-Aufruf aus, soll der Richtungsabgleich trotzdem laufen -
        # ein gemeinsamer Block wuerde beim ersten Fehler beide verlieren.
        try:
            k = G.pruefe_konsistenz(zai_client, faktentext,
                                    urteil.get("begruendung"),
                                    system_prompt=SYSTEM_KONSISTENZ)
            if k:
                aus["urteil"] = k.get("urteil")
                aus["kurzbegruendung"] = k.get("kurzbegruendung")
        except Exception:                                    # noqa: BLE001
            logger.info("Z.ai-Konsistenzpruefung fehlgeschlagen (P-8)",
                        exc_info=True)
        try:
            # OHNE Aktion und Begruendung - siehe Modul-Docstring. Der
            # Faktentext geht unveraendert hinein.
            r = G.leite_eigene_richtung_positionsrobust(
                zai_client, faktentext, system_prompt=SYSTEM_RICHTUNG)
            if r:
                aus["eigene_richtung"] = r.get("eigene_richtung")
                aus["richtung_kurzbegruendung"] = r.get("kurzbegruendung")
                erwartet = G.richtung_aus_action(aktion)
                # KEIN VERGLEICH OHNE VERGLEICHSBASIS. Bei HALTEN/NICHTS_TUN
                # liefert `richtung_aus_action()` bewusst None - dort ein
                # "nein" zu buchen hiesse, eine Abweichung zu zaehlen, wo gar
                # keine Richtung behauptet wurde.
                if erwartet is not None:
                    aus["uebereinstimmung"] = (
                        "ja" if r.get("eigene_richtung") == erwartet else "nein")
        except Exception:                                    # noqa: BLE001
            logger.info("Z.ai-Richtungsabgleich fehlgeschlagen (P-8)",
                        exc_info=True)

    faden = threading.Thread(target=arbeite, daemon=True,
                             name="zweite-meinung")
    faden.start()
    faden.join(timeout=warte_max_s)
    if faden.is_alive():
        # DIESE ZEILE IST DIE MESSUNG. Bis zum 05.08. gab es nur die Faelle,
        # die rechtzeitig fertig wurden - der SCHWANZ der Verteilung war
        # unsichtbar, und damit liess sich der Deckel nie an Daten kalibrieren.
        logger.info("Z.ai nach %.0fs nicht fertig - Mail geht ohne die "
                    "Gegenpruefungszeilen raus", warte_max_s)
    return aus


def schreibe(conn, signal_id: int, ergebnis: dict) -> bool:
    """Das Ergebnis auf die Signalzeile - durch die UEBERGEBENE Verbindung."""
    if not ergebnis or signal_id is None:
        return False
    from database import db as DB
    try:
        DB.update_signal_zai_gegenpruefung(
            conn, signal_id, ergebnis.get("urteil"),
            ergebnis.get("kurzbegruendung"), ergebnis.get("eigene_richtung"),
            ergebnis.get("uebereinstimmung"),
            ergebnis.get("richtung_kurzbegruendung"))
        return True
    except Exception:                                        # noqa: BLE001
        logger.info("Z.ai-Ergebnis nicht schreibbar (P-8)", exc_info=True)
        return False


def zeilen(ergebnis: dict) -> list[str]:
    """Die Zeilen fuer die Mail. Leer, wenn nichts vorliegt.

    KEINE ZEILE OHNE INHALT. Ein Abschnitt "Zweite Meinung: -" saehe aus wie
    ein Befund und waere nur ein Ausfall - der Leser kann beides nicht
    unterscheiden, also steht dort dann gar nichts."""
    if not ergebnis:
        return []
    z: list[str] = []
    if ergebnis.get("urteil"):
        satz = f"Ein zweites Modell nennt die Begruendung {ergebnis['urteil']}"
        if ergebnis.get("kurzbegruendung"):
            satz += f": {ergebnis['kurzbegruendung']}"
        z.append(satz + ".")
    if ergebnis.get("eigene_richtung"):
        satz = ("Ohne unsere Empfehlung zu kennen, liest dasselbe Modell die "
                f"Lage als {ergebnis['eigene_richtung']}")
        if ergebnis.get("richtung_kurzbegruendung"):
            satz += f" ({ergebnis['richtung_kurzbegruendung']})"
        # WIDERSPRUCH ZUERST BENANNT, nicht in einem Nebensatz versteckt.
        if ergebnis.get("uebereinstimmung") == "nein":
            satz += " - das WIDERSPRICHT der Empfehlung oben"
        elif ergebnis.get("uebereinstimmung") == "ja":
            satz += " - das deckt sich"
        z.append(satz + ".")
    return z
