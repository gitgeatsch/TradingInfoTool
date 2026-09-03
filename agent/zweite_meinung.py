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

WAS Z.AI HEUTE SIEHT - EIN Aufruf, EIGENE Fakten (Stand 16.08.2026):

    Rolle G   die Positionierung am Terminmarkt aus `positionierung.py`:
              offene Kontrakte, Finanzierungsrate als Perzentil, Anteil der
              Long-Konten, Marktregime mit Dauer. NICHTS davon steht im
              Faktentext von Rolle BC.

⚠️ ZWEI AUFRUFE SIND WEGGEFALLEN, und der Kopf hat es zwei Tage lang nicht
gesagt. Wer hier las, fand eine Konstruktion beschrieben, die es nicht mehr
gibt:

    Richtungsabgleich   stillgelegt 16.08. - 17x LONG in 2.469 Pruefungen,
                        dieselben Fakten wie Rolle BC (Homogeneous Debate)
    Konsistenzpruefung  entfernt 17.08. - vom Nutzer am 16.08. abgelehnt
                        ("war nie meine Anforderung") und ebenfalls auf der
                        Informationsgrenze von Rolle BC

Beide Prompts stehen unten lesbar; aufgerufen wird keiner mehr.

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

DER PREIS: EIN Z.ai-Aufruf je Einstieg. Gemessen am 13.08. ueber 60 Aufrufe
34 s je Aufruf - gegen einen Deckel von 240 s ist das reichlich Luft.

    bis 16.08.   4 Aufrufe (1 Konsistenz + 3 Stimmen)  ~137 s
    seit 17.08.  1 Aufruf  (Rolle G)                    ~34 s

DAS WAR NICHT DER GRUND, ABER DIE FOLGE: am 15.08. bekamen 35 von 39 Signalen
GAR KEINE zweite Meinung, weil die Warteschlange doppelt so lang war wie die
Wartezeit."""
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
# ⚠️ 240 -> 540 (17.08.2026). Der alte Wert war KLEINER als das, worauf ein
# Faden warten durfte: 180 s auf einen Platz plus 150 s Aufruf = 330 s, aber
# `rollen_lauf` gab nach WARTE_MAX_SEKUNDEN + 60 = 300 s auf. Der Hauptfaden
# stieg also aus, bevor die Warteschlange es tat - der Faden lief als Daemon
# weiter, seine Mail ging MIT dem Einwand raus, und `ZM.schreibe` fiel aus.
# Die Mail zeigte dann einen Befund, den die Datenbank nicht kennt.
#
# Die Regel dahinter: die Warteschlange muss VOR dem Hauptfaden aufgeben.
# Schlimmster Fall neu 480 + 75 = 555 s, Aufgabegrenze 540 + 60 = 600 s.
WARTE_MAX_SEKUNDEN = 540

# WIE VIELE Z.AI-AUFRUFE GLEICHZEITIG LAUFEN DUERFEN (14.08.2026).
#
# DIE ANNAHME WAR, die drei Stimmen liefen nacheinander und kosteten deshalb
# Zeit. Sie tun es - aber das ist nicht die Stelle, an der es klemmt.
#
# `rollen_lauf` startet EINEN FADEN JE SIGNAL. Bei zehn Signalen laufen also
# zehn Faeden, und jeder macht seine Aufrufe: der Andrang bei Z.ai ist die
# ZAHL DER SIGNALE, nicht die Stimmenzahl. Wer glaubt, drei Stimmen seien das
# Problem, sucht am falschen Ende - die Parallelitaet war schon da, nur
# unbegrenzt.
#
# ZWEI GLEICHZEITIG ist die Zahl, die der Nutzer fuer Z.ai nennt. Sie hier zu
# halten ist besser als in `rollen_lauf`: dort waere sie eine Regel ueber
# Faeden, hier ist sie eine Eigenschaft des Anbieters - und gilt auch fuer
# jeden kuenftigen Aufrufer, der von der Begrenzung nichts weiss.
MAX_GLEICHZEITIG = 2
_PLATZ = threading.Semaphore(MAX_GLEICHZEITIG)

# WIE LANGE EIN ROLLE-G-AUFRUF LAUFEN DARF (17.08.2026).
#
# NICHT die globale Zeitgrenze von Z.ai (150 s) - die ist an einem Prompt mit
# 34.611 Zeichen gemessen und gilt weiter fuer die alten Pipelines. Rolle G
# schickt 1.495 Zeichen; live gemessen kam die Antwort nach 22,4 / 29,7 /
# 33,1 s, der einzige Ausreisser lag bei 65,5 s.
#
# 75 s decken den Ausreisser und schneiden alles ab, was danach kommt. Der
# Grund ist die Knappheit: bei zwei Plaetzen kostet ein haengender Aufruf
# die halbe Kapazitaet, und zwar so lange wie fuenf normale Aufrufe.
ZEITGRENZE_ROLLE_G_SEKUNDEN = 75

# Wie lange ein Faden auf einen freien Platz wartet, bevor er aufgibt.
# Grosszuegig, weil ein Aufruf selten laenger als 30 s braucht - aber ENDLICH,
# damit ein haengender Aufruf nicht die ganze Reihe blockiert.
# ⚠️ 180 -> 480 (17.08.2026) - DIE EIGENTLICHE URSACHE DER AUSFAELLE.
#
# 85 von 159 Urteilen bekamen keine Gegenpruefung. Der Grund war NICHT das
# Limit des Anbieters, sondern unsere Geduld:
#
#   Kapazitaet  2 Plaetze * 3600 s / 30 s  =  ~240 Aufrufe je Stunde
#   gebraucht   20-40 je Umlauf
#
# Die Kapazitaet ist also reichlich da. Wir sind nur nach 180 s aus der
# Schlange gegangen: 2 * 180/30 = 12 Signale kamen dran, der Rest bekam
# `Andrang`. Das Limit begrenzt, wie viele GLEICHZEITIG laufen - nicht, wie
# viele insgesamt drankommen.
#
# 480 s reichen fuer 2 * 480/30 = ~32 Signale. Ein Andrang von 40 (der Fall
# NACH einem Neustart, nicht der Normalbetrieb) bleibt teilweise unbedient -
# sichtbar als `Andrang`, nicht als stille Zustimmung.
#
# PASST IN DEN TAKT: die Kette laeuft alle 15 Minuten
# (`HEBEL_SCREENING_INTERVAL_MINUTES`). Schlimmster Fall 480 + 75 = 555 s,
# Aufgabegrenze 600 s - zehn von fuenfzehn Minuten, fuenf Minuten Luft.
WARTE_AUF_PLATZ_SEKUNDEN = 480

# WIE VIELE TRANSPORTFEHLER IN FOLGE DEN UMLAUF ABBRECHEN (17.08.2026).
#
# DER PREIS DER LANGEN WARTEZEIT. Mit 180 s wartete ein Faden bei einem
# Ausfall drei Minuten aufs Nichts; mit 480 s waeren es acht - mal vierzig
# Faeden. Die Wartezeit hilft gegen Andrang und schadet bei Ausfall, also
# braucht sie einen Gegenspieler, der Andrang von Ausfall unterscheidet.
#
# IN FOLGE, NICHT INSGESAMT. Ein Anbieter, der weg ist, laesst ALLES
# scheitern; ein wackliger laesst Erfolge dazwischen zu. Eine Gesamtzahl
# wuerde einen Umlauf mit drei verstreuten Aussetzern genauso abbrechen wie
# einen mit totem Anbieter - und das sind zwei verschiedene Lagen.
#
# DREI, nicht eins: einzelne HTTP-Fehler kamen in den Messungen am 17.08.
# vereinzelt vor, ohne dass der Anbieter weg war. Drei in Folge bei zwei
# gleichzeitigen Plaetzen sind kein Zufall mehr.
AUSFALL_SCHWELLE = 3

_ausfall = {"folge": 0, "aus": None}
_AUSFALL_SPERRE = threading.Lock()


def beginne_umlauf() -> None:
    """Setzt den Abbruch zurueck - EIN Umlauf, EINE Entscheidung.

    Der Abbruch gilt fuer den laufenden Umlauf, nicht fuer immer. Beim
    naechsten Takt (alle 15 Minuten) wird wieder probiert: dann kostet ein
    fortdauernder Ausfall drei Aufrufe statt vierzig."""
    with _AUSFALL_SPERRE:
        _ausfall["folge"] = 0
        _ausfall["aus"] = None


def _ist_transportfehler(exc: BaseException) -> bool:
    """Hat der Anbieter geantwortet - oder war er nicht erreichbar?

    NUR TRANSPORT ZAEHLT. Eine unbrauchbare Antwort (kaputtes JSON, fehlendes
    Feld) ist ein INHALTSPROBLEM: der Anbieter lebt, er hat geantwortet. Sie
    zu zaehlen hiesse, wegen schlechter Antworten das Fragen einzustellen -
    und genau die Faelle sind die, die man sehen will."""
    import requests

    return isinstance(exc, (requests.exceptions.RequestException, OSError))


def _buche(exc: BaseException | None) -> None:
    """Zaehlt Fehlschlaege in Folge und loest bei der Schwelle aus."""
    if exc is not None and not _ist_transportfehler(exc):
        exc = None          # der Anbieter hat geantwortet - er lebt
    with _AUSFALL_SPERRE:
        if exc is None:
            _ausfall["folge"] = 0
            return
        _ausfall["folge"] += 1
        if _ausfall["folge"] < AUSFALL_SCHWELLE or _ausfall["aus"]:
            return
        _ausfall["aus"] = f"{AUSFALL_SCHWELLE} Transportfehler in Folge " \
                          f"(zuletzt: {type(exc).__name__})"
        gruende = _ausfall["aus"]
    # EINMAL LAUT, nicht vierzigmal. Ausserhalb der Sperre, damit das Logging
    # nicht die Bremse selbst blockiert.
    logger.warning("Rolle G fuer diesen Umlauf abgebrochen: %s", gruende)


def _abgebrochen() -> str | None:
    with _AUSFALL_SPERRE:
        return _ausfall["aus"]


def _mit_platz(fn, *a, **kw):
    """Ruft `fn` auf, sobald ein Z.ai-Platz frei ist.

    GIBT AUF STATT ZU DRAENGELN. Bekommt der Faden binnen
    `WARTE_AUF_PLATZ_SEKUNDEN` keinen Platz, wirft er `Andrang` - und der
    Aufrufer bucht das als *uebersprungen*, nicht als *fehlgeschlagen*.

    Der Unterschied ist der Grund fuer diese Klasse. "Fail-soft ist
    fail-silent": ein Signal ohne Gegenpruefungszeilen sieht in der Mail
    genauso aus wie eines, das die Pruefung bestanden hat. Wer nicht drankam,
    muss sich vom Rest unterscheiden lassen - sonst zaehlen wir spaeter
    Ausfaelle als Zustimmung."""
    # ⚠️ VOR DEM WARTEN. Steht der Anbieter, hat Warten keinen Zweck -
    # der Faden ginge acht Minuten in eine Schlange, an deren Ende
    # dieselbe Zeitgrenze steht, die schon dreimal ablief.
    grund = _abgebrochen()
    if grund:
        raise Ausfall(grund)
    if not _PLATZ.acquire(timeout=WARTE_AUF_PLATZ_SEKUNDEN):
        raise Andrang("kein Z.ai-Platz binnen "
                      f"{WARTE_AUF_PLATZ_SEKUNDEN:.0f} s frei")
    try:
        # ⚠️ UND NOCH EINMAL NACH DEM WARTEN. Wer beim Eintritt in die
        # Schlange stand, hat den Abbruch nicht gesehen - bei 480 s
        # Wartezeit sind das im Andrangfall fast alle. Ohne diese zweite
        # Frage brennt jeder wartende Faden nach dem Abbruch noch seine
        # eigene Zeitgrenze ab, und der Abbruch spart nichts.
        grund = _abgebrochen()
        if grund:
            raise Ausfall(grund)
        ergebnis = fn(*a, **kw)
    except Ausfall:
        raise
    except BaseException as exc:
        _buche(exc)
        raise
    else:
        _buche(None)
        return ergebnis
    finally:
        _PLATZ.release()


class Andrang(RuntimeError):
    """Es war kein Platz frei - der Aufruf hat NICHT stattgefunden."""


class Ausfall(Andrang):
    """Der Anbieter ist weg - fuer diesen Umlauf wird nicht mehr gefragt.

    ERBT VON `Andrang`, WEIL DIE FOLGE DIESELBE IST: der Aufruf hat nicht
    stattgefunden, und der Aufrufer bucht ihn als *uebersprungen*, nicht als
    *fehlgeschlagen*. Jeder bestehende `except Andrang` behandelt ihn damit
    richtig, ohne dass eine Stelle nachgezogen werden muss.

    UNTERSCHEIDBAR BLEIBT ER TROTZDEM - am Typ und am Text. Andrang heisst
    'zu viele auf einmal', Ausfall heisst 'der Anbieter antwortet nicht'.
    Das sind zwei verschiedene Lagen mit zwei verschiedenen Massnahmen, und
    sie in einer Zahl zu verruehren waere genau das Verschlucken, gegen das
    diese Klassen gebaut sind."""


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
        r = _mit_platz(G.leite_eigene_richtung, client, eingabe,
                       temperature=0.0, system_prompt=SYSTEM_RICHTUNG)
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


SYSTEM_ROLLE_G = """Du pruefst einen geplanten Handel - aber du siehst NICHT, worauf er sich stuetzt. Du bekommst ausschliesslich Angaben zur POSITIONIERUNG am Terminmarkt: offene Kontrakte, Finanzierungsrate und die Verteilung der Konten. Diese Angaben standen dem Entscheider NICHT zur Verfuegung.

DEINE EINZIGE AUFGABE: sage, ob in DIESEN Angaben etwas gegen den geplanten Handel spricht.

Antworte AUSSCHLIESSLICH mit JSON:
{"einwand": "ja|nein|unklar", "grund": "<ein Satz, mit der Zahl, auf die du dich stuetzt>"}

Kein Einwand ist eine gueltige Antwort und die haeufigere. Erfinde nichts hinzu; steht eine Angabe nicht da, ist sie kein Argument."""


def rolle_g(client, urteil: dict, conn=None, db: str | None = None,
            symbol: str | None = None, assetklasse: str | None = None,
            instrument: str | None = None,
            db_config: dict | None = None) -> dict | None:
    """Rolle G - die Gegenrede mit EIGENER Informationsgrundlage (16.08.2026).

    DER UNTERSCHIED ZUM ALTEN RICHTUNGSABGLEICH ist nicht die Frage, sondern
    die Grundlage. Der alte bekam dieselben Marktfakten wie Rolle BC und sollte
    daraus eine eigene Richtung ableiten - zwei Leser derselben Seite. Diese
    Rolle bekommt, was BC NICHT hatte: die Positionierung am Terminmarkt.

    EIN AUFRUF STATT DREI. Die drei Stimmen des Richtungsabgleichs waren der
    Versuch, das Eigenrauschen eines Modells auszumitteln, das ohnehin nichts
    Neues wusste. Bei einer eigenen Faktengrundlage ist die Frage konkret und
    die Antwort pruefbar - Mehrheiten ersetzen keine Information.

    SIE ENTSCHEIDET NICHTS. Der Einwand steht in der Mail und in der Zeile; er
    kippt die Empfehlung nicht. Nutzervorgabe vom 29.07., unveraendert."""
    # LOKALE IMPORTE: `rolle_g` ist eine Funktion auf Modulebene und
    # sieht die Importe von `hole()` nicht. Genau diese Falle hat am
    # 14./15.08. dreimal zugeschlagen - `VK`, `_wl`, `assetklasse` -,
    # und `finde_freie_namen.py` hat sie hier sofort gemeldet.
    import json

    from agent import positionierung as PO
    from api.llm_basis import extrahiere_inhalt

    # ⚠️ DAS SYMBOL KOMMT VOM AUFRUFER, NICHT AUS DEM URTEIL (16.08.2026).
    #
    # DIESE ZEILE HAT ROLLE G VOLLSTAENDIG TOTGELEGT, vom ersten Tag an.
    # `urteil` ist die validierte Antwort von Rolle BC, und die traegt WEDER
    # `symbol` NOCH `asset` - nachgezaehlt sind es 20 Schluessel, das Symbol
    # ist keiner davon. `sym` war also immer leer, und die Funktion kehrte in
    # der zweiten Zeile zurueck. Kein Fehler, kein Logeintrag, keine Zeile in
    # der Mail: die zweite Stufe war seit ihrem Bau am 16.08. ein Aufruf, der
    # nie stattfand.
    #
    # GEFUNDEN VON `simuliere_kette.py`, NICHT VON DEN 853 PAKETPRUEFUNGEN.
    # Die pruefen `lage()`, `saetze()` und `zeilen()` einzeln, und alle drei
    # sind in Ordnung. Erst der Lauf von Anfang bis Ende hat gefragt, ob der
    # Abschnitt in der fertigen Mail steht - und er stand in keiner einzigen.
    #
    # Das ist dieselbe Lehre wie beim Sektorbezug und bei der Regime-Dauer,
    # zum dritten Mal an einem Tag: was in jedem Einzelteil stimmt, kann als
    # Ganzes reissen.
    #
    # DER RUECKFALL AUF DAS URTEIL BLEIBT STEHEN - er kostet nichts und
    # bedient Aufrufer, die ein angereichertes Urteil uebergeben. Aber der
    # Betriebspfad verlaesst sich nicht mehr darauf.
    sym = str(symbol or urteil.get("symbol") or urteil.get("asset")
              or "").strip().upper()
    if not sym:
        logger.info("Rolle G ohne Symbol - uebersprungen. Der Aufrufer muss "
                    "es uebergeben; das Urteil von Rolle BC traegt keines.")
        return None
    eigene = conn
    try:
        if eigene is None:
            import sqlite3
            eigene = sqlite3.connect(
                f"file:{db or 'data/tradinginfotool.db'}?mode=ro", uri=True)
        # DIE KLASSE WIRD DURCHGEREICHT, NICHT ERRATEN. Sie entscheidet
        # ueber den Boersenfluss (BTC-weit, nur fuer Krypto sinnvoll).
        # Fehlt sie, bleibt er weg - fail-closed, siehe `PO.lage`.
        lage = PO.lage(eigene, sym, assetklasse=assetklasse,
                       instrument=instrument)
        saetze = PO.saetze(lage)
    finally:
        if conn is None and eigene is not None:
            try:
                eigene.close()
            except Exception:                                # noqa: BLE001
                pass
    # KEINE FRAGE OHNE GRUNDLAGE. Liegt zu diesem Wert gar keine
    # Positionierung vor - bei Aktien, ETF und Rohstoffen der Regelfall -,
    # wird nicht gefragt. Ein Modell, das ueber nichts urteilt, urteilt
    # trotzdem, und das waere die naechste Konstante.
    #
    # ⚠️ SEIT DEM 17.08. TRAEGT DIESER WAECHTER ALLEIN. Weiter unten stand
    # eine zweite, groebere Schranke: `len(lage["fehlt"]) >= 3`. Sie
    # funktionierte nur, solange JEDE Assetklasse dieselben drei
    # Terminmarktluecken meldete - auch dort, wo es die Groessen gar nicht
    # gibt. Seit `positionierung._melde()` diese Nicht-Luecken filtert,
    # steht bei einem Themen-ETF `fehlt = []`, und die alte Schranke
    # haette durchgelassen.
    #
    # Die Zahl der SAETZE ist ohnehin die richtige Groesse: sie misst, was
    # das Modell zu sehen bekommt, statt was wir vermissen.
    if not saetze:
        return None
    # MINDESTGRUNDLAGE (R-R3, 16.08.2026 abends). Hier stand `len(fehlt) >= 3`
    # - eine grobe Regel, die zufaellig funktionierte: die drei Terminmarkt-
    # zahlen kommen aus EINER Tabelle und sind alle da oder alle weg.
    #
    # `mindestkriterien` zaehlt stattdessen QUELLEN. Das ist die Bedingung, um
    # die es geht: die Pruefung traegt nur, wenn der Pruefer Information hat,
    # die dem Urteilenden fehlt - drei Zahlen aus einer Tabelle sind eine.
    #
    # STAND 16.08. ABENDS: fuer KRYPTO ist G1 erfuellt - Terminmarkt UND
    # Boersenzu-/-abfluesse, zwei Erhebungen mit zwei Fragen. Fuer Aktien,
    # Rohstoffe und ETF steht es weiter bei NULL. Deshalb wird weiterhin
    # nur GEMELDET, nicht gesperrt: eine scharfe Schranke legte drei von
    # fuenf Gruppen still. Wer sperren will, traegt "G" in
    # `config.yaml mindestkriterien.sperren` ein.
    from agent import mindestkriterien as MK

    if MK.melde("G", MK.pruefe_g(lage), db_config, bezug=sym):
        return None

    eingabe = {
        "geplant": {"aktion": urteil.get("aktion"),
                    "richtung": urteil.get("richtung")},
        "positionierung": saetze,
    }
    roh = client.chat(
        [{"role": "system", "content": SYSTEM_ROLLE_G},
         {"role": "user", "content": json.dumps(eingabe, ensure_ascii=False)}],
        temperature=0.2, response_format={"type": "json_object"},
        timeout=ZEITGRENZE_ROLLE_G_SEKUNDEN)
    a = json.loads(extrahiere_inhalt(roh) if not isinstance(roh, str) else roh)
    wort = str(a.get("einwand") or "").strip().lower()
    if wort not in ("ja", "nein", "unklar"):
        return None
    return {"einwand": wort,
            "grund": str(a.get("grund") or "").strip()[:400],
            "grundlage": saetze}


def hole(*, faktentext: dict, urteil: dict, zai_client,
         symbol: str | None = None, assetklasse: str | None = None,
         instrument: str | None = None,
         config: dict | None = None,
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
        # ⚠️ HIER STAND DIE KONSISTENZPRUEFUNG - entfernt am 16.08.2026.
        #
        # SIE HAETTE AM 16.08. GEHEN SOLLEN und ist beim Umbau uebersehen
        # worden. Der Nutzer war unmissverstaendlich:
        #
        #     "Also das was ich bekomme ist eine Konsistenzpruefung von was -
        #      dass die Informationen der Text konsistent ist, das brauche ich
        #      nicht - war nie meine Anforderung. Anforderung war immer eine
        #      Gegenpruefung einer zweiten Stelle."
        #
        # Ich habe darauf Rolle G gebaut und die alte Pruefung WEITERLAUFEN
        # LASSEN. Sie kostete seither einen Z.ai-Aufruf je Signal und schrieb
        # in jede Mail die Zeile "Ein zweites Modell nennt die Begruendung ...".
        #
        # UND SIE VERLETZT DIE KONSTRUKTIONSBEDINGUNG IN REINFORM (R-R2). Sie
        # bekommt den VOLLSTAENDIGEN Faktentext von Rolle BC plus deren
        # Begruendung - identische Informationsgrenze, also der Fall, in dem
        # die Debatte nachweislich ein Martingal bildet. Sie war damit nicht
        # nur unerwuenscht, sondern konstruktiv wertlos.
        #
        # `SYSTEM_KONSISTENZ` und `gegenpruefung.pruefe_konsistenz` bleiben
        # lesbar stehen - wie `mehrheit()` seit dem 16.08. Wer sie je wieder
        # anschliesst, findet hier, warum sie abgeschaltet wurde.
        try:
            # HIER STAND DER RICHTUNGSABGLEICH - drei Stimmen auf DENSELBEN
            # Marktfakten, die auch Rolle BC bekam. Entfernt am 16.08.2026,
            # aus vier unabhaengigen Gruenden:
            #
            #   1. KEINE EIGENE QUELLE. Dasselbe Modell auf denselben
            #      Kursdaten ist kein zweites Gutachten - die Literatur nennt
            #      das "Homogeneous Debate": teilen zwei Pruefer die
            #      Informationsgrenze, verliert die Pruefung ihren Wert.
            #   2. ER UNTERSCHIED NICHT. Ueber 2.469 Pruefungen: SHORT 1.246,
            #      NEUTRAL 1.206, LONG 17. Bei LONG-Signalen stimmte er in
            #      ZWEI von 377 Faellen zu - ein fast konstantes Feld kann
            #      nichts trennen (R-T6).
            #   3. SEINE ZUSTIMMUNG TRENNTE DIE AUSGAENGE NICHT: 0 von 7
            #      Treffern gegen 17,2 % bei Abweichung.
            #   4. SEINE GEMESSENE GUETE WAR DIE MARKTRICHTUNG. Wer im
            #      Baerenregime immer SHORT sagt, hat oft recht - das ist
            #      keine Leistung des Pruefers.
            #
            # ER KOSTETE DREI VON VIER AUFRUFEN. Am 15.08. bekamen deshalb
            # 35 von 39 Signalen GAR KEINE zweite Meinung - die Warteschlange
            # war doppelt so lang wie die Wartezeit.
            #
            # AN SEINE STELLE TRITT ROLLE C: dieselbe Idee, aber mit einer
            # EIGENEN Grundlage - der Positionierung am Terminmarkt, die
            # Rolle BC nicht sieht.
            # DAS SYMBOL DURCHREICHEN - siehe die Notiz in `rolle_g`.
            # Ohne diesen Wert kehrt sie in der zweiten Zeile zurueck,
            # und das ist sie vom 16. bis zum 17.08. auch.
            # ⚠️ DURCH `_mit_platz`, NICHT DIREKT (16.08.2026).
            #
            # Der Andrangdeckel `MAX_GLEICHZEITIG = 2` haengt an dieser
            # Funktion - und er umschloss bis heute NUR die
            # Konsistenzpruefung. Weder der Richtungsabgleich noch Rolle G
            # liefen je durch ihn. Solange die Konsistenzpruefung mitlief,
            # fiel das nicht auf; mit ihrer Entfernung waere der Deckel
            # ersatzlos verschwunden, und `rollen_lauf` startet EINEN FADEN
            # JE SIGNAL: bei zehn Signalen zehn gleichzeitige Z.ai-Aufrufe.
            #
            # Genau der Zustand vom 14.08., der zu dieser Klasse gefuehrt hat.
            # Gefunden von der Paketpruefung, nicht von mir - sie bestand auf
            # "die Bremse sitzt am Anbieter, nicht am Lauf".
            # ⚠️ `config` MUSS MIT. Der Parameter stand in `rolle_g`, der
            # Weg dorthin fehlte - `mindestkriterien.sperren` erreichte die
            # Rolle nie. Der Gegentest hat es gezeigt: mit `sperren=[G]`
            # aenderte sich nichts. Zum zweiten Mal an einem Tag dasselbe
            # Muster wie beim Symbol.
            r = _mit_platz(rolle_g, zai_client, urteil,
                           symbol=symbol or faktentext.get('asset'),
                           assetklasse=assetklasse,
                           instrument=instrument,
                           db_config=config)
            if r:
                aus["einwand"] = r.get("einwand")
                aus["einwand_grund"] = r.get("grund")
                aus["grundlage"] = r.get("grundlage")
        except Andrang as e:
            # UEBERSPRUNGEN IST NICHT FEHLGESCHLAGEN. Wer nicht drankam, muss
            # sich vom Rest unterscheiden lassen - sonst zaehlen wir Ausfaelle
            # spaeter als Zustimmung.
            aus["uebersprungen"] = str(e)
            # DIE ART, NICHT NUR DER TEXT. "Zu viele auf einmal" und "der
            # Anbieter ist weg" verlangen zwei verschiedene Massnahmen; sie
            # spaeter aus einem Satz zurueckzulesen waere Raten.
            aus["uebersprungen_art"] = ("ausfall" if isinstance(e, Ausfall)
                                        else "andrang")
            logger.info("Rolle G uebersprungen: %s", e)
        except Exception as e:                               # noqa: BLE001
            # ⚠️ AUCH DER FEHLSCHLAG MUSS SICHTBAR SEIN (17.08.2026).
            # Beim Nachweis am toten Anbieter aufgefallen: die ersten drei
            # Signale - die VOR dem Abbruch - landeten hier und setzten gar
            # nichts. Ihre Mails gingen ohne Gegenpruefung UND ohne Hinweis
            # raus, also genau so, wie sie aussaehen, wenn es zu diesem Wert
            # keine Gegenquelle gibt.
            aus["uebersprungen"] = f"{type(e).__name__}"
            aus["uebersprungen_art"] = "fehler"
            logger.info("Z.ai-Rolle G fehlgeschlagen (P-8)", exc_info=True)

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


# ---------------------------------------------------------------------------
# G-a: EIN EINDEUTIGES FELD FUER DEN EINWAND (03.09.2026, N-18)
# ---------------------------------------------------------------------------
#
# ⚠️⚠️ DIE URSPRUENGLICHE SORGE - "vier Woerter, zwei Bedeutungen,
# gleichzeitig live" - war beim Nachpruefen NICHT die Lage. Belegt an den
# echten Daten:
#
#     konsistent/widerspruch   14.08. - 16.08.   (dann abgeschaltet)
#     ja/nein/unklar           17.08. - heute    (durchgehend, live)
#
# Seit dem 16.08. produziert die Rollen-Kette nur noch EINE Antwort: den
# Einwand. Das echte, WEITERHIN aktuelle Problem ist etwas anderes: "ja"
# heisst hier "es gibt einen Einwand" - nicht "ja, ich stimme zu". Wer
# `zai_gegenpruefung_urteil == "ja"` liest, ohne diese Umkehrung zu
# kennen, liest das Gegenteil dessen, was gemeint ist.
#
# ⚠️⚠️ WARUM DIE ALTEN FELDER (`zai_eigene_richtung`, `zai_uebereinstimmung`,
# die Werte `konsistent`/`widerspruch`) NICHT ENTFERNT WERDEN - Nutzerfrage
# 03.09.: "sauber entfernt oder stillgelegt". Geprueft, welches von beiden
# sicher ist:
#
# `pruefe_pakete.py` haelt seit dem 16.08. AUSDRUECKLICH fest, dass diese
# Konstanten/Funktionen lesbar STEHEN BLEIBEN MUESSEN: "und die alten
# bleiben fuer die sechs alten Pipelines gueltig" - `agent/aktien/
# pipeline.py`, `agent/hedge/pipeline.py`, `agent/krypto/pipeline.py`,
# `agent/krypto/hebel_pipeline.py`, `agent/rohstoff/pipeline.py`,
# `agent/themen_etf/pipeline.py` importieren `gegenpruefung.
# fuehre_beide_calls_im_hintergrund`, das `pruefe_konsistenz()` und
# `leite_eigene_richtung()` weiterhin aufruft. Diese sechs Pipelines sind
# heute abgeschaltet (config.yaml `aktiv_fuer` deckt alle fuenf Klassen ab,
# `multi_asset_batch_job` uebersprungen) - aber sie sind der DOKUMENTIERTE
# RUECKFALLWEG, falls eine Klasse je von der neuen Kette zurueckgestuft
# wird ("GEPRUEFT WIRD JE GRUPPE... solange EINE der vier noch auf der
# alten Kette steht, laeuft der Batch fuer sie weiter").
#
# Ein Entfernen wuerde also nicht totes Gewebe wegschneiden, sondern den
# einzigen Weg kappen, eine Klasse im Notfall zurueckzustufen - UND eine
# bestehende Pruefung brechen. Deshalb: STILLGELEGT, nicht entfernt - mit
# einem Kanarienvogel-Test (Paket "Terminmarkt", unten), der SOFORT
# anschlaegt, wenn die alten Werte je wieder NEU geschrieben werden. Genau
# diese Stille war das eigentliche Risiko: `extract_notebook_diagnose.py`
# hat drei Wochen lang eine tote Kennzahl gezaehlt, ohne dass es auffiel.
def einwand_liegt_vor(urteil: str | None) -> bool | None:
    """DIE EINDEUTIGE FORM des rohen `zai_gegenpruefung_urteil`.

    ⚠️ NUR fuer die live gestellte Frage (Einwand der Positionierung).
    `konsistent`/`widerspruch` beantworten eine ANDERE Frage (widerspricht
    der Begruendungstext den Fakten?) - sie hier hineinzurechnen waere
    genau die Vermischung, die dieses Feld verhindern soll. Fuer sie gibt
    es bewusst KEINE Abbildung: `None` heisst dann "diese Frage wurde
    nicht gestellt", nicht "unklar beantwortet".

        True    Einwand liegt vor       (roh: "ja")
        False   kein Einwand            (roh: "nein")
        None    unklar / nicht gestellt (roh: "unklar", "konsistent",
                                          "widerspruch", None, alles andere)
    """
    w = str(urteil or "").strip().lower()
    if w == "ja":
        return True
    if w == "nein":
        return False
    return None


def schreibe(conn, signal_id: int, ergebnis: dict) -> bool:
    """Das Ergebnis auf die Signalzeile - durch die UEBERGEBENE Verbindung.

    ⚠️ DER SCHREIBPFAD WAR BEIM UMBAU LIEGENGEBLIEBEN (gefunden 17.08.2026
    an den echten Signalen). `hole()` liefert seit dem 16.08. die
    Schluessel `einwand`, `einwand_grund` und `grundlage`; hier standen
    ausschliesslich die ALTEN - `urteil`, `kurzbegruendung`,
    `eigene_richtung`. Der Kommentar in `zeilen()` sagt es sogar
    ausdruecklich: *"erzeugt werden sie nicht mehr"*.

    DIE FOLGE WAR EINE MESSLUECKE, KEIN AUSFALL. Die Mail zeigte den
    Einwand (dort liest `zeilen()` die richtigen Schluessel), die
    Datenbank bekam NICHTS. Am 17.08. gingen zwoelf EROEFFNEN-Signale
    raus, und keine einzige Zeile trug eine Gegenpruefung - obwohl Rolle
    G gelaufen ist.

    Damit war jede Auswertung der zweiten Stufe unmoeglich, auch die
    unter R-R6 geplante (Einwandrate gegen Fluss-Perzentil).

    DIE ALTEN SCHLUESSEL BLEIBEN als Rueckfall: Zeilen aus der alten
    Kette sollen weiter geschrieben werden koennen, solange es sie gibt."""
    if not ergebnis or signal_id is None:
        return False
    from database import db as DB
    try:
        DB.update_signal_zai_gegenpruefung(
            conn, signal_id,
            ergebnis.get("einwand") or ergebnis.get("urteil"),
            ergebnis.get("einwand_grund") or ergebnis.get("kurzbegruendung"),
            ergebnis.get("eigene_richtung"),
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


# WAS IN DER MAIL STEHT, WENN DIE GEGENPRUEFUNG NICHT LIEF.
#
# ● UND NICHT ▼: das Zeichen faerbt die Zeile grau, nicht rot. Ein Ausfall
# unserer Technik ist kein Befund ueber den Handel - ihn rot zu setzen
# hiesse, dem Leser eine Warnung ueber sein Geschaeft zu geben, wo eine
# ueber unser Werkzeug gemeint ist.
#
# KEINE ZAHLEN, KEINE ANBIETERNAMEN IM GRUND: der Leser kann mit "Z.ai
# ConnectTimeout nach 3 Versuchen" nichts anfangen. Was er wissen muss, ist,
# dass dieses Signal OHNE Gegenpruefung zu ihm kommt.
_UEBERSPRUNGEN = {
    "andrang": "● Gegenpruefung nicht gelaufen - zu viele Signale in diesem "
               "Umlauf. Dieses Signal ist NICHT gegengeprueft.",
    "fehler": "● Gegenpruefung nicht gelaufen - die Gegenquelle hat nicht "
              "geantwortet. Dieses Signal ist NICHT gegengeprueft.",
    "ausfall": "● Gegenpruefung nicht gelaufen - die Gegenquelle war in "
               "diesem Umlauf nicht erreichbar. Dieses Signal ist NICHT "
               "gegengeprueft.",
}


def zeilen(ergebnis: dict) -> list[str]:
    """Die Zeilen fuer die Mail. Leer, wenn nichts vorliegt.

    KEINE ZEILE OHNE INHALT. Ein Abschnitt "Zweite Meinung: -" saehe aus wie
    ein Befund und waere nur ein Ausfall - der Leser kann beides nicht
    unterscheiden, also steht dort dann gar nichts."""
    if not ergebnis:
        return []
    z: list[str] = []
    # ⚠️ WER NICHT DRANKAM, MUSS SICH VOM REST UNTERSCHEIDEN LASSEN
    # (17.08.2026). Bis heute setzte `hole()` ein Feld `uebersprungen`, das
    # NIRGENDS gelesen wurde: bei Andrang oder Ausfall fehlte der Abschnitt
    # ersatzlos, und eine ausgefallene Gegenpruefung sah aus wie eine, die
    # es zu diesem Wert nicht gibt.
    #
    # Das ist nicht dasselbe wie der leere Abschnitt, vor dem der Docstring
    # warnt: dort stuende ein Befund ohne Inhalt, hier steht ein Grund.
    _art = ergebnis.get("uebersprungen_art")
    if _art and not ergebnis.get("einwand"):
        return [_UEBERSPRUNGEN.get(_art, _UEBERSPRUNGEN["andrang"])]
    # ⚠️ HIER STAND DIE KONSISTENZZEILE - "Ein zweites Modell nennt die
    # Begruendung schluessig". Entfernt am 16.08.2026 zusammen mit dem Aufruf,
    # der sie erzeugte: der Nutzer hat sie am 16.08. ausdruecklich abgelehnt
    # ("war nie meine Anforderung"), und sie stand auf derselben
    # Informationsgrenze wie Rolle BC. `urteil`/`kurzbegruendung` bleiben im
    # Ergebnis-dict zulaessig, damit alte Zeilen aus der Datenbank weiterhin
    # lesbar sind - erzeugt werden sie nicht mehr.
    if ergebnis.get("einwand"):
        # IMMER EINE AUSSAGE, AUCH OHNE EINWAND (Nutzervorgabe 16.08.2026).
        #
        # Meine erste Fassung liess "kein Einwand" weg - aus Sorge vor einem
        # konstanten Feld (R-T6). Der Nutzer hat widersprochen, und er hat
        # recht: eine Gegenpruefung, die nur bei Widerspruch sichtbar ist,
        # laesst den Leser im Unklaren, ob sie ueberhaupt gelaufen ist.
        #
        # DIE SORGE BLEIBT ABER BERECHTIGT, und sie ist hier anders geloest:
        # die Bestaetigung nennt die Zahlen, auf die sie sich stuetzt. Damit
        # ist sie KEIN konstantes Feld - der Text bewegt sich mit den Daten.
        # MIT MARKER (17.08.2026). `ui.formatting.render_detail_html` faerbt
        # ▼ rot, ▲ gruen, ● grau - das Urteil ist die wichtigste Zeile des
        # Abschnitts und stand bisher in derselben Farbe wie der Beitext.
        kopf = {
            "ja": "▼ EINWAND - die Positionierung spricht dagegen",
            "nein": "▲ kein Einwand - die Positionierung stuetzt den Handel",
            "unklar": "● nicht eindeutig - die Positionierung laesst beides zu",
        }.get(ergebnis["einwand"])
        # ⚠️ EIN UNBEKANNTES URTEIL VERSCHWAND LAUTLOS (17.08.2026,
        # Nutzerfund an einer BTC-Mail). Stand in `einwand` etwas anderes
        # als ja/nein/unklar, war `kopf` None - und der Abschnitt zeigte
        # die FAKTEN samt Schlusssatz, aber kein Urteil. Der Leser sieht
        # eine gelaufene Gegenpruefung ohne Ergebnis und kann nicht
        # unterscheiden, ob sie nichts gefunden hat oder ob etwas fehlt.
        #
        # Nachgestellt: mit `einwand="keine"` entsteht exakt die Mail, die
        # gemeldet wurde. Wo der Wert herkommt, ist noch offen - `rolle_g`
        # laesst nur die drei Woerter durch. Diese Zeile macht den Fall
        # sichtbar, statt auf die Ursache zu warten.
        if kopf:
            z.append(kopf + (f": {ergebnis['einwand_grund']}"
                             if ergebnis.get("einwand_grund") else "."))
        else:
            logger.warning("Gegenpruefung mit unbekanntem Urteil %r - die "
                           "Mail nennt es jetzt, statt es wegzulassen",
                           ergebnis.get("einwand"))
            z.append(f"⚠ Die Gegenpruefung lief, ihr Urteil ist aber nicht "
                     f"lesbar ({ergebnis.get('einwand')!r}) - bitte nur "
                     f"die Angaben darunter werten.")
        # WORAUF ES BERUHT - die Saetze, die das zweite Modell gesehen hat.
        # Ohne sie waere auch die Bestaetigung eine Behauptung.
        for satz in (ergebnis.get("grundlage") or []):
            z.append(f"  {satz}")
        z.append("Dieses Modell kennt NUR die Positionierung am Terminmarkt, "
                 "nicht die Kurslage - es ist eine zweite Quelle, keine "
                 "zweite Meinung zum selben Chart.")
    return z
