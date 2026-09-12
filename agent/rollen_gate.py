# -*- coding: utf-8 -*-
"""Das Gate der Rollen-Kette - und vor allem: wo sie Signale verliert.

DIE KONFIDENZ-SCHWELLE FAELLT ERSATZLOS (E3). Sie fiel nicht durch Wahl,
sondern als Folge: sie prueft `confidence_pct`, und die neue Kette produziert
keine Konfidenz. Sie hat auch nie gewirkt, und das ist belegt -
Regelwerk_Entscheidungslog 15526: **Korrelation Konfidenz x realisiertes CRV
r = +0,073 (n = 92)**. Dazu stand das Regime ueber 1.022 Faelle konstant auf
"baer", die Schwelle also faktisch immer bei 75. Eine konstante Schwelle auf
einer nutzlosen Groesse.

DER ERSATZ IST KEINE NEUE SCHWELLE, SONDERN DER ENTSCHEIDER. Die kalibrierte
Trefferquote gegen den Kosten-Breakeven IST der Filter. Eine Mechanik statt
zwei - und die einzige, die gemessen statt gesetzt ist.

DIE FAKTORZAHL WIRD NUR MITGESCHRIEBEN, NICHT SCHARF GESCHALTET. Drei Gruende
stehen im Plan: ein unbelegter Filter ist schlechter als keiner (die Faktorzahl
zeigte in der Messung KEINEN Effekt, Arbeitsstand 7.26); ein Filter
verkleinert die Stichprobe, die zum Kalibrieren gebraucht wird; und das System
hat monatelang nicht gekauft - ein zusaetzlicher unbegruendeter Filter ist
genau das Risiko, das gerade beseitigt wurde.

WOFUER DIESES MODUL WIRKLICH DA IST: DIE DURCHLAESSIGKEIT ZU ZAEHLEN.

Der Deadloop ist die Frage "warum kauft das System nie?", und die laesst sich
ohne Zahlen nicht beantworten. Bisher konnte man am Ende sehen, dass nichts
herauskam - aber nicht, an welcher Stufe es verschwand. Ein Lauf, bei dem 40
Assets hineingehen und 0 Signale herauskommen, sieht identisch aus, egal ob
das Gate sie abgewiesen hat, das Modell NICHTS_TUN sagte oder die Geometrie
nicht rechenbar war.

    hinein            40
      Auftrag         40   ( 0 verloren)
      Fakten          38   ( 2 verloren)
      Lagebild        38   ( 0 verloren)
      Urteil          37   ( 1 verloren)
      Aktion           4   (33 verloren)   <- hier
      Geometrie        4   ( 0 verloren)
      Risikoschicht    3   ( 1 verloren)
    heraus             3

DAS IST KEIN FILTER, SONDERN EIN ZAEHLWERK. Es weist nichts ab; es haelt fest,
was die anderen Stufen tun. Ein Zaehler, der selbst eingreift, faelscht seine
eigene Messung.
"""
from __future__ import annotations

import json

# Die Stufen in der Reihenfolge, in der sie durchlaufen werden. Der Text ist
# der, der in der Auswertung steht - er soll ohne Codekenntnis lesbar sein.
# ⚠️⚠️ DER NAMENSSCHATTEN: DIE BEWERTUNGSSTUFE HEISST UEBERALL "STUFE 11",
# IST ABER DIE ZWOELFTE (07.09.2026 aufgefallen).
#
# Grund: `terminmarkt` wurde nachtraeglich eingefuegt (N-14, 02.09.). Vorher
# waren es elf Stufen und `entscheider` war die 11. Die alte Nummer steht
# seither in Dutzenden Kommentaren und Dokumentabschnitten:
#
#     "Stufe 11 verwirft" · "Stufe 11 sperrt den ganzen Lauf" ·
#     "Stufe 11 zaehlt dort heute nur" · G-6
#
# ⚠️ WER "STUFE 11" LIEST, MEINT DEN ENTSCHEIDER - also Nummer 12 dieser
# Liste. Die Namen (`entscheider`, `terminmarkt`) sind eindeutig, die
# Nummern sind es nicht. Deshalb wird im Code mit NAMEN gearbeitet, nie
# mit Indizes - und diese Notiz steht hier, damit die naechste Lesung
# nicht wieder danach suchen muss.
STUFEN = (
    ("auftrag", "Instrument und Strategie erlaubt"),
    ("fakten", "Faktenlage ausreichend"),
    ("lagebild", "Lagebild geliefert"),
    # EIGENE STUFE SEIT 14.08.2026 - vorher buchte der Cooldown auf "urteil".
    #
    # DORT STANDEN ZWEI VOELLIG VERSCHIEDENE DINGE NEBENEINANDER:
    #
    #     "Cooldown bis 22:14"     wir haben NICHT GEFRAGT   - kostet nichts
    #     <Validierungsfehler>     wir haben gefragt und die Antwort verworfen
    #                              - kostet einen Modellaufruf
    #
    # In der Auswertung sahen beide gleich aus. Am ersten Betriebstag hat genau
    # das die Diagnose um Stunden verzoegert: die Zusammenfassung zeigte
    # "Verlust bei urteil", und ob dahinter 41 gesparte oder 41 verbrannte
    # Aufrufe standen, war nicht zu sehen.
    #
    # DAS PROJEKT KENNT DIE UNTERSCHEIDUNG BEREITS - drei Arten von "nicht
    # jetzt": Kostenfilter, Nutzerentscheidung, Qualitaetsfilter. Nur der
    # dritte traegt Deadloop-Risiko. Sie in einer Stufe zu mischen macht genau
    # die Messung unmoeglich, fuer die das Gate gebaut wurde.
    # EIGENE STUFE SEIT 16.08.2026 - und aus demselben Grund wie der Cooldown
    # eine eigene bekam: sie kostet KEINEN Modellaufruf. Wer sie mit
    # `wiederholung` zusammenlegt, kann hinterher nicht mehr sagen, ob eine
    # Zeitregel oder ein identischer Faktensatz gebremst hat - und das sind
    # zwei verschiedene Aussagen ueber dieselbe Zahl.
    ("anlass", "Faktensatz hat sich geaendert"),
    # EIGENE STUFE SEIT 23.08.2026 (A1) - und wieder aus demselben Grund:
    # sie kostet KEINEN Modellaufruf. Vorher waehlte die UHR aus (der
    # Cooldown), und zwar ohne jeden Beleg - von 41 Symbolen passierten 30
    # den Fingerabdruck und NULL den Cooldown. Jetzt waehlt der Rangplatz
    # aus, und der Cooldown verhindert nur noch die Wiederholung derselben
    # Frage. Beides in einer Stufe zu zaehlen hiesse, den Unterschied
    # zwischen "nicht ausgewaehlt" und "gerade erst gefragt" wieder
    # unsichtbar zu machen.
    ("auswahl", "gehoert zu den besten k der Gruppe"),
    # EIGENE STUFE SEIT 02.09.2026 (N-14) - und zum dritten Mal aus
    # demselben Grund wie "anlass" (16.08.) und "auswahl" (23.08.): sie
    # kostet KEINEN Modellaufruf.
    #
    # WARUM SIE NICHT IN "auswahl" GEHOERT, obwohl beide auf einem
    # Querschnittsrang stehen: "auswahl" sagt, WELCHE Werte heute beurteilt
    # werden - eine Aussage ueber das Asset im Vergleich zu den anderen.
    # Diese Stufe sagt etwas ueber den ZEITPUNKT: der Terminmarkt ist
    # ueberhitzt. Zusammengelegt waere hinterher nicht mehr zu trennen, ob
    # ein Wert nicht gut genug war oder ob der Moment schlecht war - und
    # genau diese Trennung ist der Grund, aus dem beide Vorgaenger eigene
    # Stufen bekommen haben.
    #
    # GRUNDLAGE F-168: kein Einstieg im obersten Fuenftel des OI-Aufbaus.
    # +0,0145 R ueber 126.491 Anker, kein Mitlaeufer von Funding
    # (Schichtentest +0,0136 R bei festgehaltenem Funding).
    ("terminmarkt", "OI-Aufbau nicht im obersten Fuenftel"),
    ("wiederholung", "nicht kuerzlich schon gefragt"),
    ("urteil", "Urteil geliefert und vertragskonform"),
    ("aktion", "Aktion ist ein Einstieg"),
    ("geometrie", "Zonen rechenbar"),
    ("risikoschicht", "Toepfe, Cash, Positionsgroesse"),
    ("entscheider", "Trefferquote schlaegt den Breakeven"),
)
STUFEN_NAMEN = tuple(s for s, _ in STUFEN)

# ---------------------------------------------------------------------------
# G-6: DIE ENTSCHEIDERSTUFE VERWIRFT (31.08.2026)
# ---------------------------------------------------------------------------
#
# ⚠️ HIER STAND `("entscheider",)`, und die Begruendung war ueberholt:
# *"Siehe trefferbilanz.py - was diese Datei nicht tut: sie verwirft
# nichts."* Seit U-1 (30.08.2026) entscheidet Stufe 11 nicht mehr mit
# `trefferbilanz`, sondern mit `potential.traegt()`. Die alte Begruendung
# galt einem Modul, das an dieser Stelle nicht mehr steht.
#
# WAS DAS VORHER BEDEUTETE: die gesamte Bewertungsarbeit - Basisrate,
# Funding, Turnover, die Schwelle 0,010 R - wurde gerechnet, gebucht und
# dann verworfen. Kein Signal wurde je verhindert. Nutzervorgabe 30.08.:
# *"Der Filter muss gleich nach dem Umbau scharf sein und funktionieren."*
#
# ⚠️ DER WIRKUNGSNACHWEIS LAG VOR DER AENDERUNG VOR
# (`vorschau_g6_scharfschaltung.py`, 623.000 Anker mit Funding-Rang):
#
#     Schwelle 0,010   Durchlass 40,0 %
#     bleibt           -0,2518 R
#     gesperrt         -0,2749 R
#     Unterschied      +0,0231 R  -> die Sperre trifft die SCHLECHTEREN
#
# Ueber den Takt: aus rund 30,7 Empfehlungen/Jahr (A1-Schaetzung) wuerden
# ~12,3 - achtzehn weniger. Das ist eine grosse Verengung und war dem
# Nutzer vor der Umsetzung vorgelegt.
#
# ⚠️ ES WIRKT ERST MIT B1. Die Rollen-Kette hat bis heute keinen
# Betriebsaufrufer (15 von 15 Modulen); das letzte Signal in `signals`
# stammt vom 21.07.2026 aus der alten Kette. Diese Zeile legt fest, was
# beim Verdrahten gilt - sie aendert fuer sich genommen nichts.
#
# ZURUECKNEHMEN ist eine Zeile: `NUR_ZAEHLEN = ("entscheider",)`. Wer das
# tut, sollte den Grund danebenschreiben - sonst steht in einem Jahr wieder
# eine Bewertung im Code, die nichts bewirkt.
NUR_ZAEHLEN: tuple = ()

# ---------------------------------------------------------------------------
# ⚠️⚠️ DIE VIER ARTEN VON "NEIN" (Schritt 44, Punkt 1, 12.09.2026)
# ---------------------------------------------------------------------------
#
# NUTZEREINWAND, der das ausgeloest hat: *"nichts tun ist heikel bzw.
# 'gemischte Stufe' hoert sich schon seltsam an"*. Er hat recht, und die
# Ursache steht seit dem 16.08. im Kopf dieses Moduls, ohne je gebaut
# worden zu sein:
#
#     "drei Arten von 'nicht jetzt': Kostenfilter, Nutzerentscheidung,
#      Qualitaetsfilter. Nur der dritte traegt Deadloop-Risiko."
#
# `verloren()` kannte bis heute EINEN Verlust. Gebucht wurden vier Dinge:
#
#     nicht_gefragt     wir haben nicht gefragt - spart einen Modellaufruf.
#                       anlass, auswahl, terminmarkt, wiederholung
#     nicht_moeglich    wir konnten nicht - Daten fehlen oder die Antwort
#                       war unbrauchbar. fakten, lagebild, urteil, geometrie
#     bewertet_nein     wir haben gefragt UND bewertet, und die Antwort ist
#                       nein. Das EINZIGE, was den Deadloop erklaert
#     betriebszustand   die Lage des Depots oder ein Schalter des Nutzers -
#                       gar kein Urteil ueber das Asset
#
# ⚠️ WARUM DIE ART AN DER STUFE HAENGT UND NICHT AM AUFRUF: damit sich
# KEINE der zwanzig Aufrufstellen aendern muss. Wer eine Buchhaltung
# umbaut und dabei zwanzig Stellen anfasst, hat hinterher zwanzig
# Gelegenheiten fuer einen Fehler. Nur wo eine Stufe WIRKLICH gemischt ist
# - `aktion` - gibt der Aufrufer die Art ausdruecklich mit.
#
# ⚠️⚠️ UND DIE ZEITREIHE BLEIBT HEIL. Die Zahlen unter `verloren` aendern
# sich durch diese Aenderung NICHT - `arten` kommt additiv daneben. Wer
# NICHTS_TUN aus `verloren.aktion` herausnaehme, machte alte und neue
# Laeufe unvergleichbar (R-R11).
ARTEN = ("nicht_gefragt", "nicht_moeglich", "bewertet_nein", "betriebszustand")

# Klartext fuer die Laufmeldung - sie soll ohne Codekenntnis lesbar sein.
ARTKUERZEL = {
    "nicht_gefragt": "nicht gefragt (spart einen Modellaufruf)",
    "nicht_moeglich": "nicht moeglich (Daten oder Antwort unbrauchbar)",
    "bewertet_nein": "BEWERTET und verneint",
    "betriebszustand": "Betriebszustand (Depot oder Schalter)",
}

ART_JE_STUFE = {
    # Schalter des Nutzers und unvorgesehene Paare - kein Urteil ueber das Asset
    "auftrag": "betriebszustand",
    "fakten": "nicht_moeglich",
    "lagebild": "nicht_moeglich",
    # die vier Kostenfilter - jeder hat genau deshalb eine eigene Stufe
    "anlass": "nicht_gefragt",
    "auswahl": "nicht_gefragt",
    "terminmarkt": "nicht_gefragt",
    "wiederholung": "nicht_gefragt",
    # ⚠️ NICHT "bewertet_nein": hier verwirft der VERTRAG die Antwort, nicht
    # das Sprachmodell die Empfehlung. Gemessen ueber 7 Tage waren es 8x
    # ungueltig und 1x Netz - null Ablehnungen durch Rolle BC.
    "urteil": "nicht_moeglich",
    # ⚠️ DIE GEMISCHTE STUFE. Vorgabe ist das Urteil des Sprachmodells
    # (NICHTS_TUN); die beiden Betriebsfaelle geben ihre Art selbst mit.
    "aktion": "bewertet_nein",
    "geometrie": "nicht_moeglich",
    "risikoschicht": "betriebszustand",
    # der haerteste Filter der Kette - und er ist gerechnet, nicht geurteilt
    "entscheider": "bewertet_nein",
}


def art_fuer(stufe: str, art: str | None = None) -> str:
    """Die Verlustart - ausdruecklich mitgegeben oder aus der Stufe.

    Eine unbekannte Art faellt auf, statt still zu verschwinden: das war der
    Fehler, den `fail-soft ist fail-silent` in diesem Projekt schon zweimal
    teuer gemacht hat."""
    if art is None:
        return ART_JE_STUFE.get(stufe, "nicht_moeglich")
    if art not in ARTEN:
        raise ValueError("unbekannte Verlustart '%s' - bekannt: %s"
                         % (art, ", ".join(ARTEN)))
    return art



class Durchlauf:
    """Ein Zaehlwerk fuer EINEN Lauf ueber alle Assets.

    Benutzung: je Asset `beginne()`, dann je Stufe `bestanden()` oder
    `verloren()`. Wer `verloren()` meldet, ist fuer diesen Lauf raus - alle
    folgenden Stufen werden fuer dieses Asset nicht mehr gezaehlt. Sonst
    stuende ein Asset in einer Stufe, die es nie erreicht hat."""

    def __init__(self, lauf: str | None = None):
        self.lauf = lauf
        self.hinein = 0
        self.bestanden_je_stufe = {s: 0 for s in STUFEN_NAMEN}
        self.verloren_je_stufe = {s: 0 for s in STUFEN_NAMEN}
        self.gruende: dict[str, dict[str, int]] = {s: {} for s in STUFEN_NAMEN}
        # DIE VIER ARTEN JE STUFE (Schritt 44). Additiv neben `verloren` -
        # die Summe ueber die Arten einer Stufe ist immer ihr Verlust.
        self.arten: dict[str, dict[str, int]] = {s: {} for s in STUFEN_NAMEN}
        self.faktorzahlen: list[int] = []
        # Z1-BEFUNDE (Paket 12d): je Symbol die verletzten Regeln.
        # Sie nehmen NICHTS aus dem Lauf - ein Treuebruch ist ein Befund
        # an der Ausgabe, kein Ausscheiden.
        self.z1_verstoesse: dict[str, list] = {}
        # WORAUF DIE Z1-BILANZ BERUHT (15.5a). "Null Verstoesse" heisst wenig,
        # wenn die Regel nichts zu pruefen hatte: sechs von neun echten
        # Begruendungen enthielten keine einzige Zahl.
        self.letzte_stufe: dict[str, str] = {}
        self.z1_zahlen_geprueft = 0
        self.z1_ausgaben_ohne_zahl = 0
        self._offen: set = set()
        # NOTIZEN JE STUFE (31.08.2026): ein Symbol kam durch, aber nicht
        # weil die Stufe geurteilt haette - sie konnte es nicht. Das ist
        # weder "bestanden" noch "verloren", und ohne eigene Zeile waere
        # es ein stilles Durchwinken.
        self.notizen: dict[str, dict[str, int]] = {}
        # LLM-2 ROLLE G (Schritt 44, 4b): sie hatte bis heute keine Zeile.
        self.zai: dict[str, int] = {}
        self.zai_symbole: list = []
        self.zai_gruende: dict[str, int] = {}

    def beginne(self, symbol: str) -> None:
        self.hinein += 1
        self._offen.add(symbol)

    def bestanden(self, symbol: str, stufe: str) -> None:
        self._pruefe(stufe)
        if symbol in self._offen:
            self.bestanden_je_stufe[stufe] += 1
            # WIE WEIT DIESES SYMBOL GEKOMMEN IST. Gebraucht, wenn ein Asset
            # mit einer Ausnahme abbricht: die Stufe muss stimmen, sonst zeigt
            # die Tabelle auf die falsche Stelle - und genau dafuer gibt es sie.
            self.letzte_stufe[symbol] = stufe

    def verloren(self, symbol: str, stufe: str, grund: str = "",
                 art: str | None = None) -> None:
        """`art` nur dort mitgeben, wo eine Stufe WIRKLICH gemischt ist.

        Sonst gilt `ART_JE_STUFE` - siehe den Abschnitt oben. Der Vorgabewert
        `None` heisst "nimm die Art der Stufe", nicht "unbekannt"."""
        self._pruefe(stufe)
        if symbol not in self._offen:
            return
        # ⚠️ DIE ART ZUERST - SIE KANN WERFEN (gefunden von der eigenen
        # Pruefung, 12.09.2026). Stand sie hinter dem Zaehler, hinterliess
        # eine ungueltige Art einen HALB gebuchten Verlust: `verloren` um
        # eins hoeher, `arten` leer. Genau die Sorte stiller Schieflage, die
        # diese Buchhaltung beseitigen soll.
        _a = art_fuer(stufe, art)
        self.verloren_je_stufe[stufe] += 1
        self.arten[stufe][_a] = self.arten[stufe].get(_a, 0) + 1
        if grund:
            self.gruende[stufe][grund] = self.gruende[stufe].get(grund, 0) + 1
        # NUR-ZAEHLEN-STUFEN NEHMEN NICHTS AUS DEM LAUF. Der Entscheider
        # meldet, dass sich ein Trade rechnerisch nicht traegt - er verwirft
        # ihn nicht. Wer das verwechselt, baut aus einem Messinstrument einen
        # Filter und misst danach seine eigene Wirkung.
        if stufe not in NUR_ZAEHLEN:
            self._offen.discard(symbol)

    def notiz(self, symbol: str, stufe: str, text: str) -> None:
        """Durchgelassen, aber NICHT beurteilt - und das muss man sehen.

        ⚠️ GEBAUT AM 31.08.2026, weil Stufe 11 einen dritten Zustand hat.

            bestanden  die Stufe hat geprueft und durchgelassen
            verloren   die Stufe hat geprueft und verworfen
            notiz      die Stufe KONNTE NICHT PRUEFEN

        Der dritte Fall entstand mit G-6: fuer vier der fuenf Assetklassen
        ist kein einziger Beitrag registriert. Sie zu sperren waere eine
        Sperre nach Datenlage statt nach Qualitaet (Regel 4). Sie
        wortlos durchzulassen waere schlimmer - dann sieht die Tabelle
        aus, als haette der Entscheider zugestimmt.

        Eine Notiz nimmt NICHTS aus dem Lauf und faelscht keine Bilanz.
        Sie steht in der Trichtertabelle als eigene Zeile.
        """
        if symbol not in self._offen or not text:
            return
        self.notizen.setdefault(stufe, {})
        self.notizen[stufe][text] = self.notizen[stufe].get(text, 0) + 1

    def gegenpruefung(self, symbol: str, einwand) -> None:
        """LLM-2 Rolle G (Z.ai) - VERMERKEN, nicht filtern (Schritt 44, 4b).

        ⚠️ NUTZEREINWAND 12.09.: *"ZAI hat keine Stufe?"* - richtig, sie hatte
        gar keine. Sie laeuft nebenlaeufig, hat kein Veto und stand deshalb in
        keiner Zeile des Trichters. Ueber 7 Tage waren das 60 Einwaende bei
        163 Antworten, die niemand sah.

        KEINE STUFE, SONDERN EIN VERMERK - aus demselben Grund wie bei Z1: sie
        nimmt nichts aus dem Lauf, und ein Zaehler, der eingreift, faelscht
        seine eigene Messung. `einwand` ist das Ergebnis von
        `zweite_meinung.einwand_liegt_vor()`:

            True    Einwand liegt vor      (roh "ja")
            False   kein Einwand           (roh "nein")
            None    unklar oder nicht gestellt

        ⚠️ "ja" heisst EINWAND, nicht Zustimmung - diese Umkehrung hat im
        Projekt schon einmal zur falschen Lesart gefuehrt (G-a, 03.09.)."""
        if einwand is True:
            self.zai["einwand"] = self.zai.get("einwand", 0) + 1
            self.zai_symbole.append(symbol)
        elif einwand is False:
            self.zai["kein_einwand"] = self.zai.get("kein_einwand", 0) + 1
        else:
            self.zai["unklar"] = self.zai.get("unklar", 0) + 1

    def gegenpruefung_entfaellt(self, grund: str = "keine eigene Grundlage") -> None:
        """Nicht gefragt - und das ist der HAEUFIGSTE Fall (G5).

        Ohne symbolspezifische Terminmarktdaten wird Rolle G gar nicht erst
        gefragt. Wer das mit "kein Einwand" verwechselt, liest Zustimmung, wo
        niemand gefragt wurde."""
        self.zai["nicht_gefragt"] = self.zai.get("nicht_gefragt", 0) + 1
        if grund:
            self.zai_gruende[grund] = self.zai_gruende.get(grund, 0) + 1

    def faktorzahl(self, anzahl: int | None) -> None:
        """Nur mitschreiben (E3). Die Faktorzahl zeigte in der Messung KEINEN
        Effekt - sie zu filtern waere ein unbelegter Filter."""
        if isinstance(anzahl, int) and anzahl >= 0:
            self.faktorzahlen.append(anzahl)

    def naechste_stufe(self, symbol: str) -> str:
        """Die Stufe, an der dieses Symbol GERADE ARBEITET.

        NICHT die letzte bestandene - die naechste. Wer beim Modellaufruf der
        Urteilsstufe abstuerzt, hat das Lagebild bestanden und ist am URTEIL
        gescheitert; die Tabelle muss auf das Urteil zeigen.

        Gefunden im zweiten Watchlist-Probelauf (13.08.): zwei Symbole starben
        an einem Gemini-503 waehrend des Trader-Aufrufs und wurden als Verlust
        des LAGEBILDS gebucht - eine Stufe zu frueh. Dieselbe Falle wie vorher,
        nur um eins verschoben."""
        letzte = self.letzte_stufe.get(symbol)
        if letzte is None:
            return STUFEN_NAMEN[0]
        i = STUFEN_NAMEN.index(letzte)
        return STUFEN_NAMEN[min(i + 1, len(STUFEN_NAMEN) - 1)]

    def z1_zahlen(self, geprueft: int) -> None:
        """Wie viele Zahlen Z-1 an dieser Ausgabe pruefen KONNTE."""
        self.z1_zahlen_geprueft += int(geprueft or 0)
        if not geprueft:
            self.z1_ausgaben_ohne_zahl += 1

    def z1_verstoss(self, symbol: str, regeln: list) -> None:
        """Nur vermerken. Siehe gegenpruefer_rollen.pruefe_und_zaehle()."""
        if regeln:
            self.z1_verstoesse[symbol] = list(regeln)

    def _pruefe(self, stufe: str) -> None:
        if stufe not in self.bestanden_je_stufe:
            raise ValueError(f"unbekannte Stufe '{stufe}' - bekannt: "
                             f"{', '.join(STUFEN_NAMEN)}")

    @property
    def heraus(self) -> int:
        """Wieviele PRUEFUNGEN sind durchgekommen - nicht wieviele Symbole.

        ⚠️⚠️ HIER STAND `len(self._offen)` - UND `_offen` IST EINE MENGE VON
        SYMBOLEN (01.09.2026).

        Solange ein Asset genau einmal durch die Kette lief, war das
        dasselbe. Seit Schritt 3 laeuft es je ZELLE durch: ein Kern-Asset
        hat zwei (Akkumulation und die taktische), und beide koennen
        herauskommen. Die Menge kannte das Symbol dann trotzdem nur einmal.

        Gefunden hat es die Suite mit einer Zahl, die nicht aufging:
        **Mails 2, heraus 1.** Eine Mail ohne Signal waere die
        Gegenrichtung und faellt sofort auf - dieser Fall lag anders herum
        und haette einen zu engen Trichter gemeldet, dauerhaft und leise.

        `hinein` zaehlt die `beginne`-Aufrufe, also die Zellen; jedes
        `verloren` nimmt genau eine davon heraus. Die Differenz ist die
        richtige Zahl - und sie ist im Einzelzellen-Fall dieselbe wie
        vorher, weshalb sich fuer bestehende Laeufe nichts aendert.
        """
        return max(0, self.hinein - sum(self.verloren_je_stufe.values()))

    def bericht(self) -> list[str]:
        """Die Tabelle, die sagt, WO die Kette verliert."""
        # DIE MARKE GILT NUR FUER STUFEN, DIE WIRKLICH VERWERFEN. Erst ueber
        # alle gerechnet - dann bekam keine echte Stufe die Marke, weil der
        # Entscheider (der nichts herausnimmt) die groesste Zahl hatte. Eine
        # Marke auf einer Stufe, die nichts verwirft, zeigt auf die falsche
        # Stelle.
        _echte = [v for s_, v in self.verloren_je_stufe.items()
                  if s_ not in NUR_ZAEHLEN]
        _groesster = max(_echte) if _echte else 0
        z = [f"hinein          {self.hinein:>4}"]
        for stufe, text in STUFEN:
            v = self.verloren_je_stufe[stufe]
            b = self.bestanden_je_stufe[stufe]
            marke = "  <- hier" if v and v == _groesster else ""
            z.append(f"  {text:<34}{b:>4}   ({v} verloren)"
                     + ("  [nur gezaehlt]" if stufe in NUR_ZAEHLEN else marke))
            for grund, n in sorted(self.gruende[stufe].items(),
                                   key=lambda x: -x[1])[:3]:
                z.append(f"        {n}x {grund}")
            for text, n in sorted((self.notizen.get(stufe) or {}).items(),
                                  key=lambda x: -x[1])[:3]:
                z.append(f"        {n}x ⚠️ {text} [nicht beurteilt]")
            # ⚠️ DIE ARTEN NUR DORT, WO SIE ETWAS TRENNEN (Schritt 44). Eine
            # Stufe mit genau einer Art sagt dasselbe wie ihre Zeile darueber;
            # sie zweimal zu drucken macht die Tabelle laenger, nicht klarer.
            _a = self.arten.get(stufe) or {}
            if len(_a) > 1:
                z.append("        davon " + ", ".join(
                    f"{n}x {ARTKUERZEL.get(k, k)}"
                    for k, n in sorted(_a.items(), key=lambda x: -x[1])))
        z.append(f"heraus          {self.heraus:>4}")
        z.extend(self.bericht_arten())
        z.extend(self.bericht_llm())
        if self.faktorzahlen:
            schnitt = sum(self.faktorzahlen) / len(self.faktorzahlen)
            z.append(f"unabhaengige Faktoren: Schnitt {schnitt:.1f} ueber "
                     f"{len(self.faktorzahlen)} Urteile (nur gezaehlt, kein Filter)")
        return z

    def bericht_arten(self) -> list[str]:
        """Die vier Arten ueber den GANZEN Lauf - die Zeile, die erklaert.

        ⚠️ SIE BEANTWORTET DIE FRAGE, DIE DER TRICHTER BISHER NICHT KONNTE:
        von allem, was nicht herauskam - wieviel haben wir gar nicht erst
        gefragt, wieviel konnten wir nicht, und wieviel ist wirklich BEWERTET
        und verneint worden? Nur das Letzte traegt Deadloop-Risiko."""
        gesamt: dict = {}
        for je_stufe in self.arten.values():
            for k, n in je_stufe.items():
                gesamt[k] = gesamt.get(k, 0) + n
        if not gesamt:
            return []
        summe = sum(gesamt.values())
        z = ["Verlustarten (%d):" % summe]
        for k in ARTEN:
            n = gesamt.get(k, 0)
            if n:
                z.append("    %-16s %4d  %5.1f %%   %s"
                         % (k, n, 100.0 * n / summe, ARTKUERZEL[k]))
        return z

    def bericht_llm(self) -> list[str]:
        """Die drei Sprachmodell-Stellen und Z1 - IMMER, auch bei null.

        ⚠️ NUTZEREINWAND 12.09.: *"Z1 kommt gar nicht vor bzw. sehe ich diese
        in der Kette nicht. ZAI hat keine Stufe?"* Beides stimmte. Z1 stand nur
        in der Zeile, WENN es angeschlagen hat - "keine Zeile" hiess also
        entweder "sauber" oder "gar nicht gelaufen", und das ist nicht
        dasselbe. Z.ai stand nirgends.

        KEINE VON BEIDEN IST EINE STUFE. Sie verwerfen nichts; sie werden
        vermerkt. Genau das soll man hier ablesen koennen."""
        z = []
        von = len(self.z1_verstoesse)
        _urteile = self.bestanden_je_stufe.get("urteil", 0)
        if _urteile or von:
            regeln: dict = {}
            for liste in self.z1_verstoesse.values():
                for r in liste:
                    regeln[r] = regeln.get(r, 0) + 1
            _teil = (" - " + ", ".join(f"{r} {n}x"
                                       for r, n in sorted(regeln.items()))
                     ) if regeln else ""
            z.append("Z1 Treue zur Eingabe (Rechnung, kein Filter): "
                     f"{_urteile - von} sauber, {von} angeschlagen{_teil}")
            z.append(f"    {self.z1_zahlen_geprueft} Zahlen geprueft, "
                     f"{self.z1_ausgaben_ohne_zahl} Ausgabe(n) ohne jede Zahl")
        if self.zai:
            z.append("LLM-2 Rolle G / Z.ai (kein Veto): "
                     + ", ".join(f"{n}x {k}" for k, n in sorted(
                         self.zai.items(), key=lambda x: -x[1])))
            for grund, n in sorted(self.zai_gruende.items(),
                                   key=lambda x: -x[1])[:2]:
                z.append(f"        {n}x {grund}")
        return z

    def als_json(self) -> str:
        return json.dumps({"lauf": self.lauf, "hinein": self.hinein,
                           "heraus": self.heraus,
                           "bestanden": self.bestanden_je_stufe,
                           "verloren": self.verloren_je_stufe,
                           "gruende": self.gruende,
                           # ⚠️ ADDITIV (Schritt 44): `verloren` bleibt Zahl
                           # fuer Zahl, wie sie war - sonst waeren alte und
                           # neue Laeufe unvergleichbar (R-R11).
                           "arten": self.arten,
                           "zai": self.zai,
                           "zai_gruende": self.zai_gruende,
                           "faktorzahlen": self.faktorzahlen,
                           "z1_verstoesse": self.z1_verstoesse,
                           "z1_zahlen_geprueft": self.z1_zahlen_geprueft,
                           "z1_ausgaben_ohne_zahl": self.z1_ausgaben_ohne_zahl},
                          ensure_ascii=False)


TABELLE = "gate_durchlaessigkeit"


def migriere(conn) -> list[str]:
    """Additiv und idempotent, wie jede Migration hier."""
    getan = []
    vorhanden = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    if TABELLE not in vorhanden:
        conn.execute(f"""CREATE TABLE {TABELLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lauf TEXT NOT NULL,
            erfasst_am TEXT NOT NULL,
            hinein INTEGER NOT NULL,
            heraus INTEGER NOT NULL,
            daten_json TEXT NOT NULL)""")
        getan.append(f"Tabelle {TABELLE} angelegt")
    conn.commit()
    return getan


def schreibe(conn, durchlauf: Durchlauf, zeitpunkt: str) -> int:
    migriere(conn)
    cur = conn.execute(
        f"INSERT INTO {TABELLE} (lauf, erfasst_am, hinein, heraus, daten_json) "
        f"VALUES (?,?,?,?,?)",
        (durchlauf.lauf or "rollen", zeitpunkt, durchlauf.hinein,
         durchlauf.heraus, durchlauf.als_json()))
    conn.commit()
    return int(cur.lastrowid)
