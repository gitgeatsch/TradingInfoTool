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

    def verloren(self, symbol: str, stufe: str, grund: str = "") -> None:
        self._pruefe(stufe)
        if symbol not in self._offen:
            return
        self.verloren_je_stufe[stufe] += 1
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
        return len(self._offen)

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
        z.append(f"heraus          {self.heraus:>4}")
        if self.z1_verstoesse:
            von = len(self.z1_verstoesse)
            regeln: dict = {}
            for liste in self.z1_verstoesse.values():
                for r in liste:
                    regeln[r] = regeln.get(r, 0) + 1
            z.append(f"Treuepruefung Z1: {von} Ausgabe(n) mit Befund - "
                     + ", ".join(f"{r} {n}x" for r, n in sorted(regeln.items())))
        if self.faktorzahlen:
            schnitt = sum(self.faktorzahlen) / len(self.faktorzahlen)
            z.append(f"unabhaengige Faktoren: Schnitt {schnitt:.1f} ueber "
                     f"{len(self.faktorzahlen)} Urteile (nur gezaehlt, kein Filter)")
        return z

    def als_json(self) -> str:
        return json.dumps({"lauf": self.lauf, "hinein": self.hinein,
                           "heraus": self.heraus,
                           "bestanden": self.bestanden_je_stufe,
                           "verloren": self.verloren_je_stufe,
                           "gruende": self.gruende,
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
