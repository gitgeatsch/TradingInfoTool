# -*- coding: utf-8 -*-
"""Rolle BC - Aufbau beurteilen und daraus handeln. Ein Aufruf je Asset.

WARUM ZWEI ROLLEN IN EINEM AUFRUF. Der urspruengliche Entwurf trennte Trader
(bewerten) und Entscheider (handeln) - das ergab mit Selbstkonsistenz rund 162
Aufrufe taeglich gegen heute 40. Nutzer am 10.08.: nicht tragbar.

Recherchiert wurde daraufhin, welche der belegten Einwaende gegen mehrere Rollen
in einem Aufruf hier ueberhaupt greifen:

  Schema-Konfusion    nein - wir erzeugen genau ein JSON, nicht mehrere
  Anchoring           nein, hier gewollt - die Handlung SOLL auf den Belegen
                      aufbauen; das ist eine Kette, keine unabhaengige Meinung
  Selbstvalidierung   nein - es wird nichts kritisiert, es wird gefolgert
  HEDGING             JA - "ein einzelner Prompt mit mehreren Perspektiven
                      erzeugt abwaegende Beidseitigkeits-Analysen"

Das Hedging ist der reale Einwand, und er beschreibt exakt den KAS-Fall vom
15.07.: *"Technisch leichte Erholung ... ABER WEITERHIN bearishes Marktumfeld."*

DAGEGEN WIRKT DER AUFBAU DER AUSGABE. `begruendung` und `was_dagegen` sind
getrennte Felder - der Gegengrund hat einen eigenen Platz und muss nicht in die
Begruendung hineinrelativiert werden. Der Validator in `empfehlung_vertrag.py`
lehnt Begruendungen ab, die sich selbst zurueckziehen; am echten KAS-Text
getestet. Damit ist Hedging kein Risiko, sondern ein MESSBARER ZUSTAND: haeufen
sich diese Ablehnungen, ist die Zusammenlegung widerlegt.

EIN ECHTER GEGENPRUEFER DARF NIEMALS HIERHER. Dort greift die Selbstvalidierung
voll - ein Modell bestaetigt, was es gerade geschrieben hat. Falls er gebaut
wird, zwingend als eigener Aufruf mit frischem Kontext.

WAS BEWUSST NICHT GEFRAGT WIRD:

  * keine Konfidenz in Prozent - extern belegt schlecht kalibriert, im eigenen
    System 77,5 % vorhergesagt gegen 33,3 % tatsaechlich
  * keine Rechnung - Tokenisierung zerlegt Zahlen, GPT-4o faellt bei Addition
    auf 15 %. Der Erwartungswert wird spaeter deterministisch gerechnet
  * keine Positionsgroesse - nur die Wahl einer Tranche, gedeckelt durch Rolle A

STATT KONFIDENZ: die Zahl der UNABHAENGIGEN Belege. Die Praxisliteratur nennt
drei bis vier unabhaengige Faktoren als Bereich fuer einen tragfaehigen Aufbau;
eins bis zwei sind duenn. Ob drei Belege wirklich drei Dinge sagen oder dreimal
dasselbe, ist eine Sprachfrage - und damit die Aufgabe, fuer die ein
Sprachmodell hier ueberhaupt eingesetzt wird.
"""
from __future__ import annotations

from agent.empfehlung_vertrag import AKTIONEN, TRANCHEN_EUR

# "neutral" fehlte in der ersten Fassung - ein Beleg, der weder fuer noch
# gegen spricht, ist legitim und haeufig. Ihn nicht anzubieten hiesse, das
# Modell zu einer Zuordnung zu zwingen, die es nicht treffen kann.
BELEG_RICHTUNGEN = ("dafuer", "dagegen", "neutral")
BELEG_GEWICHTE = ("hoch", "mittel", "gering")

REQUIRED_FELDER = (
    "belege",
    "unabhaengige_faktoren",
    "aktion",
    "begruendung",
    "was_dagegen",
    "umgeworfen_durch",
)

# ZWEI SCHALTER, EINZELN (11.08. abends). Beide Fassungen entstehen aus
# denselben Teilen, damit ein gepaarter Lauf genau EINEN Unterschied misst.
#
# (1) BETRAGSFRAGE - Befund. Der Umbau vom 10.08. entfernte `tranche_eur` aus
#     Schema und Pflichtfeldern (siehe llm_schema.baue_trader_schema), liess
#     aber den Satz in Punkt 3 stehen. Das Modell wurde also bei jedem Aufruf
#     aufgefordert, eine Zahl zu nennen, die das Schema nicht entgegennimmt.
#     R-A2 stand im Regelwerk und war nicht gebaut. Der Text bleibt als
#     Vergleichsarm erhalten - wer ihn loescht, zerstoert die Messung vorher
#     (Arbeitsstand 7.10, K3).
#
# (2) PERSONA - offene Frage, KEIN Verbot. Nutzer am 11.08.: *"nie im prompt
#     haengt von dem Bedarf ab - das ist nur meine Meinung aber wenn die
#     Standards sagen wir brauchen die Rollen ist es kein Verbot."* Deshalb
#     bleibt die Persona VORERST eingeschaltet - der heutige Zustand wird nicht
#     ohne Beleg geaendert. Recherche und gepaarte Messung entscheiden.
_ANREDE = {
    True:  "Du bist ein erfahrener Haendler und triffst eine Entscheidung ueber "
           "genau einen Wert.",
    False: "Du triffst eine Entscheidung ueber genau einen Wert.",
}
_EINGANG = {
    True:  " Du bekommst seine Lage in Worten, deinen aktuellen Bestand darin "
           "und eine Obergrenze fuer den Einsatz.",
    False: " Du bekommst seine Lage in Worten und deinen aktuellen Bestand darin.",
}
_BETRAGSSATZ = (" Bei allem ausser NICHTS_TUN nenne den Betrag - 100, 300 oder "
                "500 Euro, hoechstens die vorgegebene Obergrenze.")

_SCHRITTE = """1. BELEGE sammeln. Gehe die Angaben durch und notiere, was fuer \
einen Einstieg spricht und was dagegen - je mit einem Gewicht \
(hoch/mittel/gering). Zwischen zwei und acht. Nenne den Wert, auf den sich der \
Beleg stuetzt. Erfinde nichts. Zu Schwankung, Kursentwicklung und Volumen \
bekommst du KEIN Perzentil, sondern ein Urteilswort - nenne dort auch keines.

2. UNABHAENGIGE FAKTOREN zaehlen. Wie viele deiner Belege sagen wirklich \
VERSCHIEDENE Dinge? Zwei Belege, die beide auf denselben Abwaertstrend zeigen, \
sind EIN Faktor, nicht zwei. Diese Zahl ist wichtiger als ihre Menge: drei bis \
vier unabhaengige Faktoren tragen einen Aufbau, einer oder zwei nicht.

3. HANDELN.{handeln}\
{betrag}{kurse}

4. BEGRUENDUNG. Ein bis zwei Saetze, die deine Wahl TRAGEN. Keine Einschraenkung \
im Nachsatz - was dagegen spricht, gehoert in das naechste Feld.

5. WAS DAGEGEN SPRICHT. Der staerkste Gegengrund, klar benannt. Er entwertet \
deine Entscheidung nicht; er gehoert dazu.

6. UMGEWORFEN DURCH. Welche einzelne, ueberpruefbare Beobachtung wuerde deine \
Entscheidung als falsch erweisen? Ein Kurs, ein Datum, ein Ereignis - nichts \
Allgemeines. Nenne, wo es sich sagen laesst, den Kurs und das Datum \
ZUSAETZLICH als eigene Felder - sonst null.

Antworte AUSSCHLIESSLICH mit JSON:
{{"belege": [{{"fakt": "<kurz, mit Wert>", "richtung": "dafuer|dagegen|neutral", \
"gewicht": "hoch|mittel|gering"}}],
 "unabhaengige_faktoren": <zahl>,
 "aktion": "<eine der oben genannten>",{richtungsfeld}
 "begruendung": "<ein bis zwei Saetze>",
 "was_dagegen": "<der staerkste Gegengrund>",
 "umgeworfen_durch": "<eine ueberpruefbare Beobachtung>",
 "umgeworfen_preis_eur": <zahl oder null>,
 "umgeworfen_bis": "<YYYY-MM-DD oder null>"}}"""


# SCHRITT 3 HAENGT AN DER STRATEGIE (Paket 2, 12.08.2026). Bei Akkumulation
# gibt es keinen einzelnen Einstiegszeitpunkt und keinen Stop - danach zu
# fragen hiesse, eine Zahl zu verlangen, die es nicht gibt. Genau dieser Fehler
# ist am 12.08. schon einmal passiert: die Marktbreite war aus den Fakten raus,
# die Frage danach stand noch im Prompt, daneben der Satz "erfinde nichts".
# SCHRITT 3 HAENGT AM INSTRUMENT (Paket 13, 13.08.2026). Eine gehebelte
# Position kennt zwei Zuege, die es bei Spot nicht gibt: den Hebel aendern,
# ohne die Position zu aendern.
#
# DIE RICHTUNG WIRD GEFRAGT, DER HEBELFAKTOR NICHT. Die Richtung ist ein
# URTEIL - faellt der Wert oder steigt er. Der Faktor ist ein Risikoparameter,
# und Kapitel 11.6 haelt fest, dass die nicht vom Modell kommen: er folgt aus
# Risikobudget und Liquidationsabstand und wird gerechnet.
# ⚠️ S6a (22.08.2026): SPOT UND HEBEL FRAGEN JETZT DASSELBE.
#
# Bis heute nannte der Hebel-Satz sieben Aktionen, der Spot-Satz fuenf -
# inhaltlich dieselben Vorgaenge unter zwei Namen. Damit trug das VERB eine
# Instrumentendeutung, die ihm nicht gehoert: "ERÖFFNEN" liest sich wie ein
# Hebelgeschaeft, auch wo die Rechnung Hebel 1,0 ergibt (76 % der Faelle).
#
# HEBEL_ERHÖHEN und HEBEL_SENKEN sind ersatzlos entfallen - sie liessen das
# Modell einen Risikoparameter setzen, was der Satz zwei Zeilen weiter unten
# ausdruecklich verbietet. In 1.998 Hebel-Signalen kamen sie zweimal vor.
#
# DIE RICHTUNG WIRD JETZT IN BEIDEN FAELLEN GEFRAGT. Ohne sie koennte der
# Spot-Lauf kein SHORT liefern - und die Frage "Spot oder Hebel" waere schon
# dadurch vorentschieden, dass die Richtung fehlt.
_HANDELN_GEMEINSAM = (
    " Waehle GENAU EINE: KAUFEN (neu aufbauen), NACHKAUFEN (bestehende "
    "Position vergroessern), REDUZIEREN (Teilverkauf), VERKAUFEN (ganz "
    "schliessen) oder NICHTS_TUN."
    " Bei KAUFEN und NACHKAUFEN nenne ZUSAETZLICH die Richtung: LONG, wenn "
    "du steigende Kurse erwartest, SHORT bei fallenden."
    " Nenne KEINEN Hebelfaktor und KEINE Positionsgroesse - beide folgen aus "
    "dem Risikobudget und dem Abstand zur Zwangsliquidation und werden "
    "gerechnet, nicht geschaetzt."
    " Ob daraus ein Spot-Kauf oder eine gehebelte Position wird, entscheidet "
    "die Rechnung nach deiner Antwort - nicht du.")

_HANDELN = {
    "spot": _HANDELN_GEMEINSAM,
    "hebel": _HANDELN_GEMEINSAM,
    # PAKET 14 (15.08.2026): DIE ABSICHERUNG FRAGT ANDERS.
    #
    # Bis heute lief sie durch den Spot-Satz - dieselbe Frage wie bei einem
    # Kauf: ist der Chart gut. Bei 3QSS und DBPK ist das die falsche Frage.
    # Ihr Chart IST das Spiegelbild des Nasdaq bzw. des S&P; ihn technisch zu
    # bewerten heisst, den Index zu bewerten und das Ergebnis umzudrehen - eine
    # Aussage, die das Lagebild schon trifft.
    #
    # WORUM ES WIRKLICH GEHT: das Depot traegt ein Risiko, und die Frage ist,
    # wieviel davon man tragen will. Die Groessenlogik steht seit dem 07.08.
    # fest - `benoetigter Einsatz = abzusicherndes Exposure / Hebelfaktor`.
    #
    # DER DECAY IST DER GRUND, WARUM "MEHR" NICHT IMMER BESSER IST. Ein
    # gehebelter inverser ETF verliert taeglich durch Rebalancing, auch wenn
    # der Index seitwaerts laeuft. Eine Absicherung, die man vergisst, kostet
    # Geld ohne Gegenleistung - deshalb steht sie ausdruecklich im Satz.
    "absicherung": (
        " Du entscheidest ueber eine ABSICHERUNG, nicht ueber einen Trade."
        " Die Frage ist NICHT, ob dieses Instrument steigen wird - es steigt,"
        " wenn der Markt faellt, das ist seine Bauart."
        " Die Frage ist, wieviel Risiko im Depot du tragen willst."
        " Waehle: KAUFEN (Absicherung aufbauen), NACHKAUFEN (bestehende"
        " ausweiten), REDUZIEREN, VERKAUFEN (Absicherung aufloesen) oder"
        " NICHTS_TUN."
        " Beziehe dich auf das ABZUSICHERNDE EXPOSURE und die bereits"
        " bestehende Abdeckung, nicht auf die Kursentwicklung des Instruments."
        " Beachte die laufende Gebuehr: eine Absicherung kostet auch dann,"
        " wenn nichts passiert."),
}

# Das Richtungsfeld erscheint NUR bei Hebel im Antwortschema. Ein Feld, das
# bei Spot nie gefuellt wird, waere eine Frage nach etwas, das es dort nicht
# gibt - derselbe Fehler wie die Kursfrage bei Akkumulation (12.08.).
# ⚠️ S6a (22.08.2026): DIE VORLAGE ZEIGT DIE RICHTUNG IN BEIDEN FAELLEN.
#
# Bis heute stand hier {"spot": "", "hebel": "..."} - das Schema verlangte die
# Richtung nur beim Hebel, und die JSON-Vorlage zeigte sie auch nur dort.
# Beides zusammen machte SHORT im Spot-Lauf UNSAGBAR, und damit war "Spot oder
# Hebel" vorentschieden, bevor das Modell ueberhaupt antwortete.
#
# ⚠️ SCHEMA UND VORLAGE MUESSEN GEMEINSAM WANDERN. Haette ich nur das Schema
# umgestellt, saehe das Modell ein Pflichtfeld, das in seiner Vorlage nicht
# vorkommt - der sicherste Weg zu einer Antwort, die am Schema scheitert.
_RICHTUNG_ZEILE = "\n \"richtung\": \"LONG|SHORT\","
_RICHTUNGSFELD = {"spot": _RICHTUNG_ZEILE, "hebel": _RICHTUNG_ZEILE}

_KURSSATZ = {
    True:  " Bei KAUFEN und NACHKAUFEN zusaetzlich den Einstiegskurs und den "
           "Ausstiegskurs, beide in Euro; der Ausstieg liegt unter dem "
           "Einstieg.",
    False: " Nenne KEINEN Einstiegs- und keinen Stopkurs - es wird gestaffelt "
           "ueber die Zeit gekauft, einen einzelnen Zeitpunkt gibt es nicht "
           "und ein fallender Kurs verbilligt die Position, statt sie zu "
           "beenden. Punkt 6 traegt hier das einzige Ausstiegskriterium.",
}


def _baue_prompt(mit_betragsfrage: bool, mit_persona: bool,
                 mit_kursen: bool = True,
                 instrument: str = "spot") -> str:
    kopf = _ANREDE[mit_persona] + _EINGANG[mit_betragsfrage]
    schritte = _SCHRITTE.format(
        handeln=_HANDELN.get(instrument, _HANDELN["spot"]),
        richtungsfeld=_RICHTUNGSFELD.get(instrument, ""),
        betrag=_BETRAGSSATZ if mit_betragsfrage else "",
        kurse=_KURSSATZ[mit_kursen])
    return f"{kopf}\n\nDEINE AUFGABE, in dieser Reihenfolge:\n\n{schritte}"


def prompt_fuer(instrument: str = "spot", strategie: str = "einstieg", *,
                mit_persona: bool = True, mit_betragsfrage: bool = False) -> str:
    """Der Prompt fuer GENAU diesen Auftrag.

    Die Kombination wird GEPRUEFT, nicht geraten - `handelsauftrag.pruefe()`
    wirft bei einem unvorgesehenen Paar. Ein stiller Rueckfall auf "spot" waere
    hier besonders teuer: er wuerde einen Hebel-Trade wie einen Spot-Trade
    bewerten - dieselben Fakten, aber ohne die Finanzierungskosten, die ihn
    erst teuer machen."""
    from agent import handelsauftrag
    i, st = handelsauftrag.pruefe(instrument, strategie)
    return _baue_prompt(mit_betragsfrage=mit_betragsfrage,
                        mit_persona=mit_persona,
                        mit_kursen=handelsauftrag.mit_kursen(i, st),
                        instrument=i)


# Der Vorgabefall bleibt Spot/Einstieg - alle bisherigen Aufrufer und alle
# Messbefunde bis zum 12.08. gehoeren hierher.
SYSTEM_PROMPT_TRADER = _baue_prompt(mit_betragsfrage=False, mit_persona=True)

# Nur fuer gepaarte Messungen. NICHT im Betrieb verwenden.
SYSTEM_PROMPT_TRADER_MIT_BETRAG = _baue_prompt(mit_betragsfrage=True,
                                               mit_persona=True)
SYSTEM_PROMPT_TRADER_OHNE_PERSONA = _baue_prompt(mit_betragsfrage=False,
                                                 mit_persona=False)

# Siehe rolle_analyst.PROMPT_STAND - jeder Messbefund gehoert zu einem Stand.
#
#   2026-08-10a  erste Fassung, Betrag wird erfragt und ausgegeben
#   2026-08-10b  `tranche_eur` aus Schema und Pflichtfeldern entfernt - ABER
#                der Satz in Punkt 3 blieb stehen. Hierher gehoeren alle
#                Befunde vom 10./11.08.
#   2026-08-11   Betragssatz aus dem Betriebsprompt entfernt (schaltbar
#                erhalten). Persona UNVERAENDERT eingeschaltet - offene Frage,
#                kein Verbot; sie ist jetzt einzeln schaltbar und messbar.
#   2026-08-12   Paket 1: der Falsifikator bekommt zwei maschinenlesbare
#                Felder (`umgeworfen_preis_eur`, `umgeworfen_bis`). Zielkurs
#                und die Spannen um Einstieg/Stop werden ABGELEITET, nicht
#                erfragt - siehe `leite_zonen_ab()`. Die Frage an das Modell
#                ist damit unveraendert bis auf Punkt 6.
#   2026-08-16   PHASE I. DIE FRAGE IST UNVERAENDERT - die FAKTEN sind es
#                nicht. Wer hier nach einer Textaenderung sucht, findet keine;
#                sie steht in `agent/lagebeschreibung.py`. Der Stand wird
#                trotzdem HIER gefuehrt, weil jede Messung ihn von hier liest
#                und ein zweiter Stand daneben die Zuordnung nur verdoppeln
#                wuerde.
#
#                Vier Ergaenzungen, alle GRUEN (beschreibend, ohne Bewertung -
#                die Klassifizierung steht in Umbauplan 36.1):
#
#                  1  Liquidationsabstand je Grenzhebel, in Prozent UND in
#                     Schwankungsbreiten. Nur bei `instrument='hebel'`
#                  2  Finanzierung NUR noch beim Hebel. Bei Spot faellt der
#                     Block weg - er beschreibt eine Zahlung, die ein
#                     Spot-Kaeufer weder leistet noch erhaelt, und wurde
#                     trotzdem in 63 % der Spot-Urteile zitiert (O-34)
#                  3  Fehlende Angaben werden BENANNT: kein Umsatz, weniger
#                     als zwei Marken, Historie unter 250 Handelstagen.
#                     Betrifft 8 von 56 Assets (Umbauplan 34.6)
#                  4  Sektorbezug fuer Themen-ETF - relative Staerke zum
#                     breiten Markt ueber 30 und 90 Handelstage
#
#                DER FUENFTE SCHRITT DES PLANS IST NICHT GEBAUT: Regime und
#                Persistenz fuer Rolle A. Er verletzt die
#                Konstruktionsbedingung der zweiten Stufe - Rolle G hat beides
#                seit dem 16.08. frueh, und ein Parameter gehoert zu GENAU
#                EINEM Modell. Begruendung im Umbauplan, Kapitel 38.
#
#                ALLE VIER IN EINEM STAND, nicht in vieren: fuenf Aenderungen
#                an fuenf Tagen erzeugen fuenf Staende, zwischen denen niemand
#                mehr vergleichen kann (Umbauplan 36.4).
#   2026-08-16   KLASSE 1: eine woertliche DOPPELUNG entfernt. Die
#                60-Tage-Bewegung stand in `struktur` UND in `bewegung`,
#                bitgleich gerechnet - 42 von 42 Reihen, keine Ausnahme.
#                Beide Bloecke sind zu `verlauf` zusammengelegt; die
#                Nachbarschaft von Strukturaussage und 60-Tage-Zahl bleibt
#                (sie war der Fix vom 11.08.), die zweite Nennung entfaellt.
#                Ein Satz weniger, kein Fakt weniger.
# ⚠️ BUCHSTABE, WEIL DER TAG SCHON VERGEBEN IST. Phase I lief in der
# Produktion unter "2026-08-16" - 29 Signale tragen ihn. Klasse 1 kam
# am selben Tag; ohne den Buchstaben waeren genau die Signale nicht
# trennbar, deren Unterschied gemessen werden soll.
# 2026-08-17c: EIN SATZ GEGEN EINE ERFUNDENE ZAHL. In den Belegen echter
#              Signale stand vierzehnmal ein Volumen-Perzentil - "im 92.
#              Perzentil der letzten 400 Tage", samt einer Fensterlaenge,
#              die in keinem unserer Saetze vorkommt. `faktenblock.kern()`
#              haelt dieses Perzentil bewusst zurueck und gibt nur ein
#              Urteilswort; das Modell hat daraus eine plausible Zahl
#              zurueckgerechnet.
#
#              "Erfinde nichts" stand schon da und hat nicht getragen -
#              eine allgemeine Ermahnung schlaegt keine konkrete Luecke.
#              Jetzt wird die Stelle benannt, an der es passiert ist.
#              Gemessen wird es weiter von `pruefe_belege_gegen_fakten.py`:
#              14 von 1.834 Belegen (0,76 %) vor der Aenderung.
# 2026-08-17d: DIE URSACHE STATT DES SYMPTOMS. Nach Promptstand
#              aufgeschluesselt begannen die falschen Volumen-Perzentile
#              exakt mit 17b - dem Stand, der Krypto-Spot den UMSCHLAG
#              gegeben hat: 0 Belege davor, 19 von 272 danach (6,99 %).
#              Der Beleg "MON: Umsatzvolumen 6.0 % (84. Perzentil)"
#              enthaelt BEIDE unsere Zahlen - das Modell hat nichts
#              erfunden, sondern den Umschlag in "Umsatzvolumen"
#              umbenannt, den Namen des Blocks nebenan, der bewusst kein
#              Perzentil hat.
#
#              Der Umschlagsatz traegt jetzt ein eigenes Hauptwort und
#              nennt seinen Bezug (Umlaufbestand gegen eigenen
#              Durchschnitt). Die Zeile aus 17c bleibt - sie schadet
#              nicht und deckt den Rest.
# 2026-08-17e: EINE ZAHLENSCHREIBWEISE. Dieselbe Mail schrieb "2,3 % je
#              Tag" (Faktenblock) und sechs Zeilen tiefer "5 Tage -1.2 %"
#              (Lagebeschreibung). Der Faktentext ist jetzt durchgehend
#              deutsch - und damit aendert sich, was das Modell liest.
#
#              ⚠️ DER ORDNUNGSPUNKT BLEIBT: "im 84. Perzentil" ist keine
#              Dezimalzahl. `schreibweise.de()` formatiert deshalb die
#              ZAHL und bekommt nie einen Satz zu sehen - anders als das
#              `.replace(",", ".")` ueber einen ganzen Satz, das in
#              `marktlage` stand und nur solange stimmte, wie der Satz
#              kein zweites Komma hatte.
PROMPT_STAND = "2026-08-17e"


# --- Die abgeleiteten Zonen (Paket 1, 12.08.2026) -------------------------
#
# DREI ZAHLEN, DIE DER NUTZER BRAUCHT und die das Modell NICHT nennt:
# Zielkurs, und je eine Spanne um Einstieg und Stop ("bei ca.").
#
# WARUM ABGELEITET STATT ERFRAGT - und das ist kein Geschmack, sondern eine
# Voraussetzung fuer die Erfolgsmessung. Die gesamte Trefferbilanz laeuft auf
# der Geometrie 3 ATR Ziel / 1,5 ATR Stop (so in `baue_ankerpopulation.py`,
# `messe_degradierung.py`, `messe_zeitschranke.py`). Nennt das Modell den
# Zielkurs frei, weicht die Geometrie je Signal ab - und dann sind zwei
# Trefferquoten nicht mehr vergleichbar. Ohne feste Geometrie gibt es keine
# Kalibrierungstabelle und damit keine ehrliche Zahl fuer die E-Mail
# (Umbauplan 6.3).
#
# Das Modell entscheidet weiterhin RICHTUNG, EINSTIEG und RISIKOABSTAND - also
# das Wesentliche. Dieselbe Linie wie beim Betrag: das Modell urteilt, die Zahl
# leitet sich ab.
#
# 3,0 / 1,5 = 2,0, und exakt dieser Wert steht als `risiko.crv_minimum` in der
# config (Z-2). Die Ableitung reproduziert also die Messgeometrie, statt eine
# zweite danebenzustellen.
CRV_ZIEL = 2.0

# Die Spanne ist eine TOLERANZ, keine Prognose. Ein Kurs bewegt sich innerhalb
# eines Tages um Bruchteile des ATR; ein Viertel davon ist die Breite, in der
# "bei ca." ehrlich ist. Bewusst symmetrisch und bewusst klein - eine breite
# Spanne sieht vorsichtig aus und macht jede Angabe unpruefbar.
BAND_ATR = 0.25


def leite_zonen_ab(antwort: dict, atr: float | None,
                   crv: float = CRV_ZIEL) -> dict:
    """Ergaenzt Zielkurs und die Spannen um Einstieg und Stop.

    Aendert die Punktwerte des Modells NICHT - `einstieg_eur` und `stop_eur`
    bleiben unberuehrt daneben stehen. Wer den Punkt braucht, findet ihn; wer
    die Spanne braucht, auch.

    Ohne ATR gibt es keine Spanne (aber sehr wohl ein Ziel - das haengt nur an
    Einstieg und Stop). Fehlt einer der beiden Punkte, passiert gar nichts:
    eine erfundene Zone waere schlimmer als keine."""
    ein = antwort.get("einstieg_eur")
    stop = antwort.get("stop_eur")
    if not isinstance(ein, (int, float)) or not isinstance(stop, (int, float)):
        return antwort
    if ein <= 0 or stop <= 0 or stop >= ein:
        # Stop ueber Einstieg ist ein Widerspruch, den der Vertrag ohnehin
        # beanstandet - hier wird er nicht durch eine Rechnung kaschiert.
        return antwort

    risiko = float(ein) - float(stop)
    antwort["ziel_eur"] = round(float(ein) + crv * risiko, 8)

    if isinstance(atr, (int, float)) and atr > 0:
        band = BAND_ATR * float(atr)
        for feld, mitte in (("einstieg", ein), ("stop", stop),
                            ("ziel", antwort["ziel_eur"])):
            antwort[f"{feld}_eur_von"] = round(max(0.0, float(mitte) - band), 8)
            antwort[f"{feld}_eur_bis"] = round(float(mitte) + band, 8)
    return antwort


# ---------------------------------------------------------------------------
# STOP-UNTERGRENZE - RM-1b UND RM-1c, PORTIERT (12.08.2026, Nachtrag zu Paket 9)
#
# WARUM DAS HIER STEHEN MUSS. Der Live-Lauf lieferte einen Stop von rund 1 % des
# Kurses. Das ist keine Feinheit, sondern gemessen der schlechteste Fall, den es
# gibt (Backtest 28.07., 61 aufgeloeste Trades):
#
#     Stopabstand    n     Trefferquote   realisiertes CRV
#     < 2 %          9         0,0 %            -1,00
#     2 - 5 %       36        16,7 %            -0,41
#     5 - 10 %      16        31,2 %            +0,31
#
# Monoton, ohne Ausnahme. Und genau deshalb gibt es seit 02.08. zwei Regeln -
# nur wirkten sie ausschliesslich in `agent/krypto/risk_gate.py`. Die neue
# Rollen-Kette hatte KEINE Untergrenze; sie ist an der alten Kette vorbei
# gebaut worden und hat diese Leitplanke dabei verloren. Das Nachziehen ist
# Wiederherstellung des Produktionsstands, nicht neue Strenge.
#
# ZWEI GRENZEN, ES GILT DIE STRENGERE:
#   RM-1b  Stop < 2,5 % des Kurses      - strukturell: Gebuehren, Spread, Rauschen
#   RM-1c  Stop < 0,75 x ATR            - symbolrelativ: 2,5 % koennen fuer DIESES
#                                         Symbol trotzdem im Rauschen liegen
#
# WARUM DAS KEIN VERSTOSS gegen "kein deterministischer Override des LLM-
# Werturteils" ist: jene Regel schuetzt die qualitative Synthese und nennt
# CRV-Floor und Positionsgroessen-Deckel ausdruecklich als erlaubte Gegen-
# beispiele - harte, objektive Finanzfakten. Ein Stopabstand ist Geometrie. Das
# Modell darf weiterhin sagen, die Lage sei guenstig; es darf nur nicht ein
# Risiko behaupten, das kleiner ist als das Grundrauschen des Marktes.
#
# ES WIRD NICHT STILL KORRIGIERT. Der Punktwert des Modells bleibt stehen, der
# Befund kommt als eigenes Feld daneben. Wer die Zahl des Modells sehen will,
# findet sie; die Entscheidung darueber faellt sichtbar.
STOP_MIN_RELATIV = 0.025          # RM-1b
STOP_MIN_ATR_FAKTOR = 0.75        # RM-1c


def pruefe_stopabstand(antwort: dict, atr: float | None = None,
                       min_relativ: float = STOP_MIN_RELATIV,
                       min_atr_faktor: float = STOP_MIN_ATR_FAKTOR) -> dict:
    """Traegt `stop_zu_eng` und `stop_min_eur` in die Antwort ein.

    Ohne Einstieg oder Stop passiert nichts - bei Akkumulation etwa gibt es
    beide gar nicht, und ein Befund ueber eine Zahl, die es nicht gibt, waere
    schlimmer als keiner."""
    ein = antwort.get("einstieg_eur")
    stop = antwort.get("stop_eur")
    if not isinstance(ein, (int, float)) or not isinstance(stop, (int, float)):
        return antwort
    if ein <= 0 or stop <= 0 or stop >= ein:
        return antwort

    grenzen = [float(ein) * (1.0 - min_relativ)]          # RM-1b
    if isinstance(atr, (int, float)) and atr > 0:
        grenzen.append(float(ein) - min_atr_faktor * float(atr))   # RM-1c
    # DIE STRENGERE GRENZE IST DIE NIEDRIGSTE STOPMARKE. Erst falsch herum
    # gebaut (`max`), und der Fehler war nur an gedruckten Zahlen zu sehen:
    # RM-1b verlangt 2,5 % Abstand, RM-1c bei ATR 1.677 nur 2,27 % - `max`
    # nahm die HOEHERE Marke und damit den GERINGEREN geforderten Abstand,
    # also die schwaechere der beiden Regeln. Wer beide erfuellen will, muss
    # unter die tiefste Marke.
    untergrenze = min(grenzen)

    antwort["stop_abstand_relativ"] = round((float(ein) - float(stop)) / float(ein), 6)
    antwort["stop_min_eur"] = round(untergrenze, 8)
    antwort["stop_zu_eng"] = bool(float(stop) > untergrenze)
    if antwort["stop_zu_eng"]:
        antwort["stop_zu_eng_grund"] = (
            f"RM-1b: unter {100 * min_relativ:g} % des Kurses"
            if untergrenze == grenzen[0] else
            f"RM-1c: unter {min_atr_faktor:g} x ATR")
    return antwort


class TraderAntwortUngueltig(ValueError):
    """Die Antwort erfuellt ihren Vertrag nicht."""


def validiere(antwort: dict, symbol: str = "?",
              max_tranche_eur: int | None = None,
              atr: float | None = None,
              instrument: str = "spot", strategie: str = "einstieg",
              kurs: float | None = None) -> dict:
    """Prueft die Rollen-eigenen Felder; der Handlungsteil laeuft danach durch
    `empfehlung_vertrag.validiere()`.

    `instrument`/`strategie` (12.08.2026, Paket 2): entscheiden, ob Einstiegs-
    und Ausstiegskurs ueberhaupt zur Sache gehoeren. Bei Akkumulation gehoeren
    sie es nicht - und wenn das Modell sie trotz gegenteiliger Anweisung
    liefert, werden sie hier ENTFERNT statt in eine Zielzone weitergerechnet.
    Sonst entstuende ein Zielkurs fuer eine Strategie, die keinen hat, und die
    Erfolgsmessung wuerde ihn spaeter als Trefferquote lesen.

    `atr` (12.08.2026, Paket 1): wird durchgereicht an `leite_zonen_ab()`.
    Die Ableitung steht ABSICHTLICH hier drin und nicht in einer Funktion, die
    der Aufrufer zusaetzlich rufen muss - eine Ergaenzung, die man vergessen
    kann, fehlt irgendwann in genau einem der sechs Pfade. Ohne `atr` entsteht
    der Zielkurs trotzdem (er haengt nur an Einstieg und Stop), nur die Spannen
    fehlen.

    `max_tranche_eur` wird nicht mehr verwendet - Rolle A nennt keinen Betrag
    mehr. Der Parameter bleibt vorerst in der Signatur, damit bestehende
    Aufrufer nicht brechen."""
    from agent.antwort_normalisierung import (Protokoll, kappe_auf,
                                              kuerze_liste, naechstes_wort)
    from agent.empfehlung_vertrag import validiere as vertrag_validieren

    if not isinstance(antwort, dict):
        raise TraderAntwortUngueltig(f"{symbol}: Antwort ist kein Objekt")

    prot = Protokoll()
    # Fehlende Felder werden VERMERKT, nicht abgelehnt - der Vertrag entscheidet
    # danach, was ohne sie noch traegt. Nur `aktion` ist dort hart.
    fehlend = [f for f in REQUIRED_FELDER if antwort.get(f) in (None, "", [])]
    if fehlend:
        prot.dazu(f"ohne Angabe: {', '.join(fehlend)}")

    # --- Belege: Form zurechtruecken, nicht verwerfen ----------------------
    belege = antwort["belege"]
    if not isinstance(belege, list):
        raise TraderAntwortUngueltig(f"{symbol}: belege ist keine Liste")
    sauber = []
    for b in belege:
        if not isinstance(b, dict) or not str(b.get("fakt") or "").strip():
            prot.dazu("Beleg ohne Fakt verworfen")
            continue
        r, hinweis = naechstes_wort(b.get("richtung"), BELEG_RICHTUNGEN)
        if r is None:
            # Erfundene Richtung: als neutral werten statt den Beleg oder die
            # ganze Antwort zu verlieren. Der Fakt bleibt lesbar, sein Vorzeichen
            # ist dann eben unbestimmt.
            r = "neutral"
            hinweis = f"Beleg-Richtung {b.get('richtung')!r} als neutral gewertet"
        prot.dazu(hinweis)
        g, hinweis2 = naechstes_wort(b.get("gewicht"), BELEG_GEWICHTE)
        if g is None:
            g = "mittel"
            hinweis2 = f"Beleg-Gewicht {b.get('gewicht')!r} als mittel gewertet"
        prot.dazu(hinweis2)
        sauber.append({"fakt": str(b["fakt"]).strip(), "richtung": r, "gewicht": g})
    if not sauber:
        raise TraderAntwortUngueltig(f"{symbol}: kein einziger brauchbarer Beleg")
    # Zu WENIGE werden nicht abgelehnt - ein einzelner starker Beleg kann eine
    # richtige Entscheidung tragen, und die Zahl steht ohnehin in der Ausgabe.
    if len(sauber) < 2:
        prot.dazu(f"nur {len(sauber)} Beleg statt der erbetenen zwei")
    sauber, hinweis = kuerze_liste(sauber, 8, "Belege")
    prot.dazu(hinweis)
    antwort["belege"] = sauber

    # --- Unabhaengige Faktoren: hart, weil logisch pruefbar ----------------
    try:
        faktoren = int(float(antwort.get("unabhaengige_faktoren")))
    except (TypeError, ValueError):
        # Keine Zahl geliefert: die Belege sind trotzdem da und zaehlbar. Als
        # Rueckfall gilt jeder Beleg als eigener Faktor - das ist die
        # groesszuegige Annahme, aber sie steht im Protokoll und faellt auf.
        faktoren = len(sauber)
        prot.dazu(f"unabhaengige_faktoren {antwort.get('unabhaengige_faktoren')!r} "
                  f"unbrauchbar - auf {faktoren} gesetzt")
    if faktoren < 0:
        faktoren = 0
        prot.dazu("negative Faktorenzahl auf 0 gesetzt")
    if faktoren > len(sauber):
        # Mehr unabhaengige Faktoren als Belege ist unmoeglich. Frueher eine
        # Ablehnung - jetzt gedeckelt: die Zahl war falsch, die Analyse deshalb
        # nicht wertlos. Der Deckel steht im Protokoll und ist damit sichtbar.
        prot.dazu(f"{faktoren} unabhaengige Faktoren bei {len(sauber)} Belegen "
                  f"auf {len(sauber)} gedeckelt")
        faktoren = len(sauber)
    antwort["unabhaengige_faktoren"] = faktoren

    # --- Betrag: an der Obergrenze aus Rolle A kappen, nicht verwerfen -----
    # DER BETRAG KOMMT NICHT VOM MODELL (Umbau 10.08. abends). Er wird aus der
    # Zahl unabhaengiger Faktoren abgeleitet - siehe `tranche_aus_faktoren()`.
    # Nennt das Modell trotzdem einen, wird er verworfen, nicht uebernommen.
    from agent.empfehlung_vertrag import tranche_aus_faktoren
    antwort.pop("tranche_eur", None)
    if str(antwort.get("aktion") or "").strip().upper() != "NICHTS_TUN":
        betrag = tranche_aus_faktoren(faktoren)
        if betrag is None:
            # Kein einziger unabhaengiger Faktor: die Handlung traegt nicht.
            antwort["_degradiert"] = (
                f"'{antwort.get('aktion')}' auf NICHTS_TUN zurueckgenommen: "
                f"kein unabhaengiger Faktor")
            antwort["aktion"] = "NICHTS_TUN"
        else:
            antwort["tranche_eur"] = betrag
            prot.dazu(f"{faktoren} unabhaengige Faktoren -> {betrag} EUR")

    # Bei NICHTS_TUN wird der Betrag NICHT nachgebessert - im ersten echten Lauf
    # lieferte das Modell dort eine 0, und die Korrektur machte daraus brav
    # "100 EUR" fuer eine Handlung, die gar nicht stattfindet. Ein Betrag ohne
    # Handlung ist Rauschen in der Anzeige.
    if str(antwort.get("aktion") or "").strip().upper() == "NICHTS_TUN":
        for feld in ("tranche_eur", "einstieg_eur", "stop_eur",
                     "ziel_eur", "einstieg_eur_von", "einstieg_eur_bis",
                     "stop_eur_von", "stop_eur_bis",
                     "ziel_eur_von", "ziel_eur_bis"):
            antwort.pop(feld, None)
    else:
        from agent import handelsauftrag
        if handelsauftrag.mit_kursen(*handelsauftrag.pruefe(instrument, strategie)):
            # ZONEN ABLEITEN, erst NACH der Faktoren- und Degradierungslogik:
            # eine auf NICHTS_TUN zurueckgenommene Handlung traegt keinen
            # Zielkurs.
            leite_zonen_ab(antwort, atr)
            # RM-1b/RM-1c NACH der Ableitung: das Ziel haengt am Stop des
            # Modells, und der bleibt stehen. Der Befund kommt daneben.
            pruefe_stopabstand(antwort, atr)
            if antwort.get("stop_zu_eng"):
                prot.dazu(f"Stopabstand "
                          f"{100 * antwort['stop_abstand_relativ']:.2f} % - "
                          f"{antwort.get('stop_zu_eng_grund', 'zu eng')} "
                          f"(Untergrenze {antwort['stop_min_eur']:.8g} EUR)")
        else:
            # Akkumulation: der Prompt hat ausdruecklich KEINE Kurse verlangt.
            # Kommen trotzdem welche, sind sie eine Antwort auf eine nicht
            # gestellte Frage - vermerkt, nicht weitergerechnet.
            uebrig = [f for f in ("einstieg_eur", "stop_eur")
                      if antwort.pop(f, None) is not None]
            if uebrig:
                prot.dazu(f"{', '.join(uebrig)} entfernt - bei Strategie "
                          f"'{strategie}' gibt es keinen einzelnen Einstieg")

    if prot:
        antwort["_korrekturen"] = ((antwort.get("_korrekturen", "") + "; ")
                                   if antwort.get("_korrekturen") else "") + str(prot)
    # DAS INSTRUMENT GEHT MIT (Paket 13). Ohne es prueft der Vertrag ein
    # Hebel-Signal gegen das Spot-Vokabular und wirft bei ERÖFFNEN -
    # dieselbe Antwort waere je nach Aufrufer gueltig oder nicht.
    # `kurs` seit S3 (18.08.2026): der Vertrag prueft den Widerlegungspreis
    # gegen die Richtung, und dafuer braucht er einen Bezugspunkt.
    return vertrag_validieren(antwort, symbol, instrument=instrument,
                              kurs=kurs)
