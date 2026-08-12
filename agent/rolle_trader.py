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
Beleg stuetzt. Erfinde nichts.

2. UNABHAENGIGE FAKTOREN zaehlen. Wie viele deiner Belege sagen wirklich \
VERSCHIEDENE Dinge? Zwei Belege, die beide auf denselben Abwaertstrend zeigen, \
sind EIN Faktor, nicht zwei. Diese Zahl ist wichtiger als ihre Menge: drei bis \
vier unabhaengige Faktoren tragen einen Aufbau, einer oder zwei nicht.

3. HANDELN. Waehle: KAUFEN (neu aufbauen), NACHKAUFEN (bestehende Position \
vergroessern), REDUZIEREN, VERKAUFEN oder NICHTS_TUN.{betrag}{kurse}

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
 "aktion": "KAUFEN|NACHKAUFEN|REDUZIEREN|VERKAUFEN|NICHTS_TUN",
 "einstieg_eur": <zahl>, "stop_eur": <zahl>,
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
_KURSSATZ = {
    True:  " Bei KAUFEN und NACHKAUFEN zusaetzlich den Einstiegskurs und den "
           "Ausstiegskurs, beide in Euro; der Ausstieg liegt unter dem "
           "Einstieg.",
    False: " Nenne KEINEN Einstiegs- und keinen Ausstiegskurs - es wird "
           "gestaffelt gekauft, einen einzelnen Zeitpunkt gibt es nicht.",
}


def _baue_prompt(mit_betragsfrage: bool, mit_persona: bool,
                 mit_kursen: bool = True) -> str:
    kopf = _ANREDE[mit_persona] + _EINGANG[mit_betragsfrage]
    schritte = _SCHRITTE.format(
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
                        mit_kursen=handelsauftrag.mit_kursen(i, st))


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
PROMPT_STAND = "2026-08-12"


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


class TraderAntwortUngueltig(ValueError):
    """Die Antwort erfuellt ihren Vertrag nicht."""


def validiere(antwort: dict, symbol: str = "?",
              max_tranche_eur: int | None = None,
              atr: float | None = None,
              instrument: str = "spot", strategie: str = "einstieg") -> dict:
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
    return vertrag_validieren(antwort, symbol)
