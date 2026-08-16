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
WARTE_MAX_SEKUNDEN = 240

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

# Wie lange ein Faden auf einen freien Platz wartet, bevor er aufgibt.
# Grosszuegig, weil ein Aufruf selten laenger als 30 s braucht - aber ENDLICH,
# damit ein haengender Aufruf nicht die ganze Reihe blockiert.
WARTE_AUF_PLATZ_SEKUNDEN = 180


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
    if not _PLATZ.acquire(timeout=WARTE_AUF_PLATZ_SEKUNDEN):
        raise Andrang("kein Z.ai-Platz binnen "
                      f"{WARTE_AUF_PLATZ_SEKUNDEN:.0f} s frei")
    try:
        return fn(*a, **kw)
    finally:
        _PLATZ.release()


class Andrang(RuntimeError):
    """Es war kein Platz frei - der Aufruf hat NICHT stattgefunden."""


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
            symbol: str | None = None) -> dict | None:
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
        lage = PO.lage(eigene, sym)
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
    if not saetze or len(lage.get("fehlt") or []) >= 3:
        return None

    eingabe = {
        "geplant": {"aktion": urteil.get("aktion"),
                    "richtung": urteil.get("richtung")},
        "positionierung": saetze,
    }
    roh = client.chat(
        [{"role": "system", "content": SYSTEM_ROLLE_G},
         {"role": "user", "content": json.dumps(eingabe, ensure_ascii=False)}],
        temperature=0.2, response_format={"type": "json_object"})
    a = json.loads(extrahiere_inhalt(roh) if not isinstance(roh, str) else roh)
    wort = str(a.get("einwand") or "").strip().lower()
    if wort not in ("ja", "nein", "unklar"):
        return None
    return {"einwand": wort,
            "grund": str(a.get("grund") or "").strip()[:400],
            "grundlage": saetze}


def hole(*, faktentext: dict, urteil: dict, zai_client,
         symbol: str | None = None,
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
            r = _mit_platz(rolle_g, zai_client, urteil,
                           symbol=symbol or faktentext.get('asset'))
            if r:
                aus["einwand"] = r.get("einwand")
                aus["einwand_grund"] = r.get("grund")
                aus["grundlage"] = r.get("grundlage")
        except Andrang as e:
            # UEBERSPRUNGEN IST NICHT FEHLGESCHLAGEN. Wer nicht drankam, muss
            # sich vom Rest unterscheiden lassen - sonst zaehlen wir Ausfaelle
            # spaeter als Zustimmung.
            aus["uebersprungen"] = str(e)
            logger.info("Rolle G uebersprungen: %s", e)
        except Exception:                                    # noqa: BLE001
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
        kopf = {
            "ja": "EINWAND - die Positionierung spricht dagegen",
            "nein": "kein Einwand - die Positionierung stuetzt den Handel",
            "unklar": "nicht eindeutig - die Positionierung laesst beides zu",
        }.get(ergebnis["einwand"])
        if kopf:
            z.append(kopf + (f": {ergebnis['einwand_grund']}"
                             if ergebnis.get("einwand_grund") else "."))
        # WORAUF ES BERUHT - die Saetze, die das zweite Modell gesehen hat.
        # Ohne sie waere auch die Bestaetigung eine Behauptung.
        for satz in (ergebnis.get("grundlage") or []):
            z.append(f"  {satz}")
        z.append("Dieses Modell kennt NUR die Positionierung am Terminmarkt, "
                 "nicht die Kurslage - es ist eine zweite Quelle, keine "
                 "zweite Meinung zum selben Chart.")
    return z
