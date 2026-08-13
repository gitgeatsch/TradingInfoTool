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
    ("urteil", "Urteil geliefert und vertragskonform"),
    ("aktion", "Aktion ist ein Einstieg"),
    ("geometrie", "Zonen rechenbar"),
    ("risikoschicht", "Toepfe, Cash, Positionsgroesse"),
    ("entscheider", "Trefferquote schlaegt den Breakeven"),
)
STUFEN_NAMEN = tuple(s for s, _ in STUFEN)

# Die LETZTE Stufe zaehlt nur - sie verwirft nicht. Siehe trefferbilanz.py:
# "Was diese Datei nicht tut: sie verwirft nichts." Ein Waechter, der selbst
# verwirft, macht seine eigene Wirkung unsichtbar.
NUR_ZAEHLEN = ("entscheider",)


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
        self.z1_zahlen_geprueft = 0
        self.z1_ausgaben_ohne_zahl = 0
        self._offen: set = set()

    def beginne(self, symbol: str) -> None:
        self.hinein += 1
        self._offen.add(symbol)

    def bestanden(self, symbol: str, stufe: str) -> None:
        self._pruefe(stufe)
        if symbol in self._offen:
            self.bestanden_je_stufe[stufe] += 1

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

    def faktorzahl(self, anzahl: int | None) -> None:
        """Nur mitschreiben (E3). Die Faktorzahl zeigte in der Messung KEINEN
        Effekt - sie zu filtern waere ein unbelegter Filter."""
        if isinstance(anzahl, int) and anzahl >= 0:
            self.faktorzahlen.append(anzahl)

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
