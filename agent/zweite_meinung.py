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

    Konsistenz      Faktentext VOLLSTAENDIG + Begruendungstext
    Eigene Richtung Faktentext OHNE `auftrag` und OHNE den Bestandssatz
                    (`nur_markt()`, Begruendung dort)

DIE BEIDEN AUFRUFE BEKOMMEN BEWUSST NICHT DASSELBE. Die Konsistenzpruefung
haelt einen Begruendungstext gegen die Fakten - der DARF sich auf den Bestand
beziehen. Der Richtungsabruf soll unabhaengig urteilen, und dafuer ist jeder
Satz schaedlich, der von UNS handelt statt vom Markt.

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

DER FAKTENTEXT WIRD NICHT NEU GEBAUT, NUR GEFILTERT. Er entsteht nach
R-T1..R-T9 in `rollen_eingabe`: relativ vor absolut, benanntes Fenster, keine
rohen Zahlenreihen. Hier wird nur WEGGELASSEN, nie umformuliert - eine zweite
Formulierungsstelle waere die naechste, die irgendwann die aeltere ist.

WARUM DIESES MODUL NICHT `fuehre_beide_calls_im_hintergrund()` RUFT, obwohl es
genau das zu tun scheint: jene Funktion oeffnet ihre Verbindung selbst, mit
`db.get_connection()` - fest auf die PRODUKTIVDATEI. Ein Probelauf gegen eine
Kopie wuerde sein Z.ai-Ergebnis dort hineinschreiben, auf eine `signal_id`, die
in der Produktivdatei ein anderes Signal bezeichnet. Diese Kette bekommt ihre
Verbindung uebergeben, und das gilt auch fuer den Nebenweg.

DER PREIS: 4 sequenzielle Z.ai-Aufrufe je Einstieg (1 Konsistenz + 3 Stimmen
fuer die Richtung, siehe `mehrheit()`). GEMESSEN am 13.08. ueber 60 Aufrufe:
34 s je Aufruf, nicht die dokumentierten 12-25 s. Vier Aufrufe sind damit rund
137 s gegen einen Deckel von 240 s - es passt, aber mit weniger Luft als bisher
angenommen. Wer die Stimmenzahl erhoeht, muss diese Rechnung mitziehen."""
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
    "Du bekommst ausschliesslich Marktfakten zu einem Krypto-Wert als Saetze: "
    "Marktstruktur, Kursentwicklung ueber mehrere Fenster, naechste "
    "Unterstuetzung und Widerstand, Umsatzverteilung. Du kennst KEINE "
    "Empfehlung eines anderen Modells und KEINE Position. Deine Aufgabe: leite "
    "ALLEIN aus diesen Fakten deine eigene Markteinschaetzung ab - LONG "
    "(bullisch), SHORT (baerisch) oder NEUTRAL (keine klare Tendenz). "
    "Erfinde NIEMALS eigene Fakten, nutze nur die gegebenen. "
    "Antworte AUSSCHLIESSLICH mit JSON, exakt diese zwei Felder: "
    '{"eigene_richtung": "LONG" oder "SHORT" oder "NEUTRAL", '
    '"kurzbegruendung": "<= 12 Woerter"}.')

# Woran der Bestandssatz erkannt wird. Er ist der einzige im Block `stand`, der
# von UNS handelt und nicht vom Markt - `lagebeschreibung._bestand()` baut ihn
# in genau drei Formen ("ist nicht im Bestand", "ist im Bestand (...)",
# "ist bereits im Bestand: ...").
_BESTAND_MERKMAL = "im Bestand"


def nur_markt(faktentext: dict) -> dict:
    """Der Faktentext OHNE alles, was nicht vom Markt handelt.

    NUR FUER DEN RICHTUNGSABRUF. Die Konsistenzpruefung bekommt weiter alles:
    dort wird ein Begruendungstext gegen die Fakten gehalten, und der DARF sich
    auf den Bestand beziehen ("wir liegen hier schon 17 % hinten").

    ZWEI DINGE FLIEGEN RAUS, beide gefunden beim Vergleich des Prompts mit dem
    echten Nutzinhalt:

      auftrag        "Es geht um einen einzelnen Einstieg mit einem Ziel und
                     einem Ausstiegskurs." Das ist eine ABSICHTSERKLAERUNG,
                     kein Marktfakt - und sie sagt dem Modell, dass ein
                     Einstieg erwogen wird. Genau der Anker, den dieser Aufruf
                     vermeiden soll.
      Bestandssatz   "BTC ist bereits im Bestand: 3453 EUR investiert ...
                     609 EUR im Minus (-17,6 %)." Unsere Position, keine
                     Marktevidenz - und im Block `stand` steht sie an ERSTER
                     Stelle, also an der staerksten.

    WARUM WEGLASSEN UND NICHT "IGNORIERE DAS" IN DEN PROMPT. Ein Modell
    anzuweisen, Information zu uebergehen, die man ihm gerade gegeben hat, ist
    der schwaechere Weg - die erste Fassung dieses Moduls hat genau das
    versucht. Die alte Kette macht es richtig: `baue_objektive_fakten()`
    LAESST `richtung`/`action`/`confidence` weg, statt sie zu erklaeren."""
    aus = {k: v for k, v in (faktentext or {}).items() if k != "auftrag"}
    stand = aus.get("stand")
    if isinstance(stand, list):
        aus["stand"] = [s for s in stand
                        if _BESTAND_MERKMAL not in str(s)]
    return aus


STIMMEN = 3


def mehrheit(client, fakten: dict) -> dict | None:
    """Drei Stimmen, die Mehrheit gilt - und wie knapp sie war, steht dabei.

    GEMESSEN AM 13.08. (`messe_namensanker.py`, 20 Symbole, 60 Aufrufe): bei
    IDENTISCHER Eingabe und `temperature=0.0` kippt das Richtungsurteil in
    30 % der Faelle. Nicht bei Grenzfaellen - im Schnitt.

        A gegen A' (nichts geaendert) : 6/20 = 30 %
        A gegen B  (Name geaendert)   : 3/20 = 15 %

    Der Namenseffekt lag also UNTER dem Eigenrauschen; die eigentliche
    Nachricht der Messung war das Rauschen selbst.

    WAS DAS FUER DIE ALTE MECHANIK BEDEUTET. `leite_eigene_richtung_
    positionsrobust()` ruft ZWEIMAL und faellt bei Uneinigkeit auf NEUTRAL
    zurueck - gedacht als Test, ob die Anordnung der Fakten das Urteil dreht.
    Bei 30 % Eigenrauschen passiert dieser Rueckfall aber ueberwiegend
    ZUFAELLIG. Der Test misst nicht, was auf ihm steht.

    WAS HIER STATTDESSEN PASSIERT: drei Stimmen, davon eine auf umgekehrter
    Satzreihenfolge. Beides zusammen - Anordnung und Wiederholung - beantwortet
    die Frage, die im Betrieb zaehlt: IST DIESES URTEIL BELASTBAR? Warum es das
    nicht ist, waere eine eigene Untersuchung; fuer die Mail genuegt, dass die
    Knappheit sichtbar wird.

    DIE STIMMENZAHL WIRD MITGELIEFERT UND NICHT VERSTECKT. Ein 2:1 darf nicht
    aussehen wie ein 3:0 - sonst steht ein Muenzwurf als Befund in der Mail.

    Gibt None, wenn keine einzige Stimme zurueckkam."""
    from agent.krypto import gegenpruefung as G

    stimmen, begruendungen = [], []
    for i in range(STIMMEN):
        # DIE MITTLERE STIMME AUF UMGEKEHRTER REIHENFOLGE - so steckt der alte
        # Positionstest weiter drin, ohne einen eigenen Aufruf zu kosten.
        eingabe = kehre_saetze_um(fakten) if i == 1 else fakten
        r = G.leite_eigene_richtung(client, eingabe, temperature=0.0,
                                    system_prompt=SYSTEM_RICHTUNG)
        if r and r.get("eigene_richtung"):
            stimmen.append(r["eigene_richtung"])
            if r.get("kurzbegruendung"):
                begruendungen.append(r["kurzbegruendung"])
    if not stimmen:
        return None
    haeufigste = max(set(stimmen), key=stimmen.count)
    return {"eigene_richtung": haeufigste,
            "stimmen": stimmen.count(haeufigste),
            "von": len(stimmen),
            "kurzbegruendung": begruendungen[0] if begruendungen else None}


def kehre_saetze_um(faktentext: dict) -> dict:
    """Umkehr fuer den Positions-Bias-Test - auf SATZEBENE.

    DIE STANDARD-UMKEHR GREIFT HIER INS LEERE. `_kehre_objektive_fakten_um()`
    dreht die Schluesselreihenfolge; das passt zur flachen Faktenform der alten
    Kette mit sechs Schluesseln. Gemessen am echten Nutzinhalt der Rollen-Kette:

        vorher : ['asset', 'auftrag', 'stand']
        nachher: ['stand', 'auftrag', 'asset']
        'stand' danach identisch: True        <- die 8 Saetze bleiben gleich

    Der zweite Aufruf prueft damit fast dieselbe Eingabe noch einmal und kostet
    trotzdem Kontingent - von drei Z.ai-Aufrufen je Einstieg war einer
    weitgehend wirkungslos.

    Gedreht wird die Reihenfolge der SAETZE, nicht ihr Inhalt: der Test fragt,
    ob dasselbe Material in anderer Anordnung dasselbe Urteil ergibt."""
    aus = dict(faktentext or {})
    for schluessel, wert in aus.items():
        if isinstance(wert, list) and len(wert) > 1:
            aus[schluessel] = list(reversed(wert))
    return aus


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
            # NUR MARKTFAKTEN, und DREI Stimmen statt zwei - beides oben
            # begruendet. Die Konsistenzpruefung darueber bekommt bewusst
            # den vollen Text.
            r = mehrheit(zai_client, nur_markt(faktentext))
            if r:
                aus["eigene_richtung"] = r.get("eigene_richtung")
                aus["richtung_kurzbegruendung"] = r.get("kurzbegruendung")
                aus["stimmen"] = r.get("stimmen")
                aus["von"] = r.get("von")
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
        # DIE STIMMENZAHL IN EINER EIGENEN SPALTE, nicht im Begruendungstext.
        # Bei 30 % Eigenrauschen ist der Unterschied zwischen 3:0 und 2:1 die
        # wichtigste Zusatzangabe, die es hier gibt - jede spaetere Auswertung
        # muss danach filtern koennen, ohne einen Freitext zu zerlegen.
        if ergebnis.get("stimmen"):
            conn.execute("UPDATE signals SET zai_stimmen = ? WHERE id = ?",
                         (int(ergebnis["stimmen"]), signal_id))
            conn.commit()
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
        # DIE KNAPPHEIT GEHOERT IN DIE ZEILE. Bei 30 % Eigenrauschen (gemessen
        # 13.08.) ist ein 2-von-3 ein Muenzwurf, ein 3-von-3 eine Aussage - und
        # der Leser kann beides nicht unterscheiden, wenn es nicht dasteht.
        st, von = ergebnis.get("stimmen"), ergebnis.get("von")
        if st and von:
            satz += f" ({st} von {von}" + (", uneinheitlich" if st < von else "")
            satz += ")"
        if ergebnis.get("richtung_kurzbegruendung"):
            satz += f", Begruendung: {ergebnis['richtung_kurzbegruendung']}"
        # WIDERSPRUCH ZUERST BENANNT, nicht in einem Nebensatz versteckt.
        if ergebnis.get("uebereinstimmung") == "nein":
            satz += " - das WIDERSPRICHT der Empfehlung oben"
        elif ergebnis.get("uebereinstimmung") == "ja":
            satz += " - das deckt sich"
        z.append(satz + ".")
    return z
