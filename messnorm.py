# -*- coding: utf-8 -*-
"""DIE MESSNORM — eine Grundlage, die nicht je Messung neu gewaehlt wird
(06.09.2026)

## Warum es dieses Modul gibt

**Elf Messungen in zwei Tagen haben elf Mal die Grundlage neu gewaehlt** -
Zielgroesse, Menge, Klammer, Nullpunkt, Kontrollen. Das Ergebnis war eine
Folge von "traegt / traegt nicht", die mit jeder Methodenaenderung kippte.

Nutzervorgabe 06.09.: *„stelle sicher, dass wir danach zukuenftig Regeln und
Standards haben, die eine saubere Abgrenzung erlauben und nicht jede Messung
als Zufallsergebnis traegt oder nicht traegt."*

⚠️ **Eine Norm im Dokument wird nicht befolgt - eine im Code schon.**
Vorbild ist `wahrscheinlichkeit.Beitrag.klammer="tag"`: seit dem 31.08.
wirft der Import, wenn ein Beitrag ohne Tagesklammer registriert wird.

## Die drei Fehler, gegen die dieses Modul gebaut ist

    1  FALSCHE ZIELGROESSE   "Ziel vor Stop" misst die eigene Zielregel
                             zurueck (Konzept Bewertungsstufe, 23.08.)
    2  FALSCHE MENGE         die Beitraege wirken auf 1,5 % der Anker;
                             gemessen wurde auf 100 % (F-212, 04.09.)
    3  FEHLENDE TRENNSCHAERFE  ein "traegt nicht" ohne Positivkontrolle ist
                             keine Messung, sondern das Fehlen einer

## ⚠️ Der Kern: VIER Urteile, und nur zwei sind Aussagen ueber die Welt

Bisher gab es "traegt" und "traegt nicht". Das zweite verschweigt, ob die
Messung den Effekt ueberhaupt haette finden koennen. Hier gibt es:

    TRAEGT                 Band schliesst den Nullpunkt aus
    TRAEGT NICHT           und die Positivkontrolle beweist, dass ein
                           Effekt dieser Groesse gefunden WORDEN WAERE
    KEIN BEFUND            die Trennschaerfe reicht nicht - untermaechtig

**Nur das mittlere Urteil ist eine Aussage ueber die Welt.** Das dritte ist
eine Aussage ueber die Messung, und es wird nicht mehr als Nullbefund
ausgegeben.

## Die Norm — Z bis W

| | | Quelle |
|---|---|---|
| **Z** | ZIELGROESSE, aus geschlossener Liste, passend zur Lage | Konzept Bewertungsstufe §1 |
| **M** | MENGE, mit Dosis-Wirkungs-Kurve als Pflicht | F-212 |
| **K** | KLAMMER: Kalendertag, nie gepoolt | Vorgabe 31.08., Methodik 2.86 |
| **G** | KOSTEN 0,00 % fuer jede Rangfolge | Regel 2, Konzept §4 |
| **B** | BAND: Block-Bootstrap, Block >= 3 x Horizont | Methodik 2.95 |
| **N** | NULLKONTROLLE auf derselben Struktur | F-226 |
| **P** | POSITIVKONTROLLE -> TRENNSCHAERFE | Methodik 2.88, 2.100 |
| **W** | PFLICHTANGABEN: Anker, Tage, Bloecke, Abdeckung, Hypothesen | Zielgroessen §4 |
| **L** | AUSGANGSLAGE: Instrument x Strategie x Richtung | Nutzervorgabe 06.09. |

    python messnorm.py --selbsttest
"""
from __future__ import annotations

import dataclasses
import sys
from dataclasses import dataclass, field

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as M                        # noqa: E402
import messe_regel_wirksamkeit as W                         # noqa: E402


# ---------------------------------------------------------------- Z
# ⚠️ GESCHLOSSENE LISTE. Wer eine neue Zielgroesse braucht, traegt sie hier
# ein - und muss dabei sagen, fuer welche Lagen sie gilt. Ein freier String
# waere genau die Beliebigkeit, gegen die dieses Modul gebaut ist.
ZIELGROESSEN = {
    "bewegung_r": {
        "text": "Rendite in R nach H Tagen, BARRIERENFREI",
        "gilt_fuer": "alle Lagen",
        "begruendung": "misst die Bewegung, nicht die eigene Zielregel",
    },
    "barriere": {
        "text": "Ziel vor Stop (CRV-Barriere)",
        "gilt_fuer": "nur Lagen, in denen ein Stop den Trade BEENDET",
        "begruendung": ("blind fuer 'wieviel ist zu holen' - der "
                        "Erwartungswert ist per Konstruktion null. Zulaessig "
                        "als VERGLEICH zweier Arme unter derselben Zielregel "
                        "und dort, wo der Stop den Trade wirklich beendet."),
    },
}

# Lagen, in denen ein Stop den Trade beendet - nur dort ist "barriere" die
# zutreffende Zielgroesse.
ZIEHUNGEN = 5
SAAT = 20260906

STOP_BEENDET = {("hebel", "einstieg"), ("hebel", "swing")}


@dataclass(frozen=True)
class Lage:
    """Instrument x Strategie x Richtung — Pflichtfeld jeder Messung.

    ⚠️ Nutzervorgabe 06.09.: *„das sind unterschiedliche Ausgangslagen,
    welche nicht unsauber vermischt werden sollten - zumindest bei Hebel."*

    Gemessen am 06.09.: `instrument='hebel'` hat es in der neuen Kette NIE
    gegeben (3.513 spot, 11 absicherung, 0 hebel), und SHORT ist nie
    gefeuert. Der Hebel entsteht INNERHALB von spot x einstieg. Deshalb
    traegt jede Hebel-Aussage die Markierung `simuliert=True`.
    """
    instrument: str
    strategie: str
    richtung: str = "long"
    simuliert: bool = False

    def __post_init__(self) -> None:
        from agent import handelsauftrag as HA
        erlaubt = HA.ERLAUBTE_PAARE.get(self.instrument)
        if not erlaubt:
            raise ValueError("unbekanntes Instrument: %r" % self.instrument)
        if self.strategie not in erlaubt:
            raise ValueError("%s + %s ist keine vorgesehene Kombination"
                             % (self.instrument, self.strategie))
        if self.richtung not in ("long", "short"):
            raise ValueError("Richtung muss long oder short sein")
        if self.richtung == "short":
            # ⚠️ SHORT IST OFFEN (Nutzerhinweis 06.09.). Null Signale in der
            # Produktion, Zielgroesse ungeklaert. Kein stiller Durchlauf.
            raise ValueError(
                "SHORT ist noch nicht geklaert - null Signale in der "
                "Produktion, Zielgroesse offen. Erst festlegen, dann messen.")

    @property
    def stop_beendet(self) -> bool:
        return (self.instrument, self.strategie) in STOP_BEENDET

    def __str__(self) -> str:
        return "%s x %s x %s%s" % (self.instrument, self.strategie,
                                   self.richtung,
                                   " (simuliert)" if self.simuliert else "")


@dataclass(frozen=True)
class Protokoll:
    """DER WEG, nicht das Ergebnis — hier passieren die Fehler.

    ⚠️ Nutzerhinweis 06.09.: *„zur Urteilslogik gehoert nicht nur das
    Ergebnis, sondern der Weg dorthin, wo die eigentlichen Fehler
    passieren."*

    Beleg aus zwei Tagen: KEIN einziger Fehler war im Ergebnis sichtbar.
    Jeder erzeugte eine plausible Zahl.

        gepoolt statt Tagesklammer   ->  12,4 Punkte auf einem Nulleffekt
        Nullpunkt aus EINER Ziehung  ->  eine saubere Kurve
        Maximum statt Streuungsmass  ->  ein "strengerer" Test
        Pflanzung auf echte Daten    ->  eine gute Trennschaerfe
        Kunstwelt nach Rohwert       ->  ein bestandener Selbsttest

    Deshalb traegt jeder Befund seinen Weg mit sich, und die Norm prueft
    ihn - nicht nur die Zahl am Ende.
    """
    wirkung_funktion: str            # welche Funktion die Wirkung rechnete
    band_funktion: str               # welche das Band rechnete
    null_konstruktion: str           # wie der Nullpunkt entstand
    null_ziehungen: int
    positiv_konstruktion: str        # wie die Positivkontrolle entstand
    positiv_ziehungen: int
    positiv_treffer: dict            # {staerke: gefunden in x von n}
    blocklaenge: int
    saat: int

    def __post_init__(self) -> None:
        # ⚠️ BEKANNTE FALSCHE WEGE WERDEN ABGELEHNT, nicht nur vermerkt.
        if "gemischt" not in self.positiv_konstruktion:
            raise ValueError(
                "die Positivkontrolle muss in die GEMISCHTE Welt pflanzen. "
                "Auf die echten Daten gepflanzt misst sie Effekt PLUS "
                "Pflanzung - die Trennschaerfe faellt dann zu gut aus "
                "(06.09. gemessen: eine Welt mit 0,05 R wurde als "
                "'traegt nicht bis 0,02 R' gemeldet).")
        if self.null_ziehungen < 3 or self.positiv_ziehungen < 3:
            raise ValueError(
                "eine Ziehung ist kein Nullpunkt (Methodik 2.104). Die "
                "Basislinie wandert je Saat um denselben Betrag wie die "
                "gesuchten Effekte - gemessen -0,0055 bis +0,0010.")

    def zeilen(self) -> list:
        return [
            "  Wirkung ueber   %s" % self.wirkung_funktion,
            "  Band ueber      %s · Block %d" % (self.band_funktion,
                                                 self.blocklaenge),
            "  Nullpunkt       %s · %d Ziehungen" % (self.null_konstruktion,
                                                     self.null_ziehungen),
            "  Positivkontr.   %s · %d Ziehungen" % (self.positiv_konstruktion,
                                                     self.positiv_ziehungen),
            "  gefunden        %s" % " · ".join(
                "%.2f R: %d/%d" % (k, v, self.positiv_ziehungen)
                for k, v in sorted(self.positiv_treffer.items())),
            "  Saat            %d" % self.saat,
        ]


@dataclass(frozen=True)
class Befund:
    """Ein Messergebnis, das ohne seine Kontrollen nicht entstehen kann."""
    kandidat: str
    lage: Lage
    zielgroesse: str
    menge: str
    # Ergebnis
    wirkung: float
    unten: float
    oben: float
    # Kontrollen — Pflicht
    nullpunkt: float
    null_unten: float
    null_oben: float
    trennschaerfe: float | None          # kleinste GEFUNDENE gepflanzte Staerke
    # ⚠️ EINHEITEN (06.09., vom Vorabtest des Randmassstabs gefunden).
    #
    # `urteil` vergleicht `wirkung` gegen `trennschaerfe`. Solange beide in
    # R stehen, geht das auf. Beim Randmassstab steht `wirkung` aber in
    # ANTEILSPUNKTEN, waehrend gepflanzt wird in R - der Vergleich war
    # sinnlos (0,0008 Anteilspunkte gegen 0,05 R) und haette jedes Urteil
    # verfaelscht.
    #
    # Regel ab jetzt: `trennschaerfe` steht IMMER in der Einheit von
    # `wirkung`. Die gepflanzte Staerke in R - die einzige Groesse, die
    # ZWISCHEN den Massstaeben vergleichbar ist - steht in
    # `trennschaerfe_in_r`.
    trennschaerfe_in_r: float | None = None
    gepflanzt: tuple = ()
    # Pflichtangaben
    n_anker: int = 0
    n_tage: int = 0
    n_bloecke: int = 0
    abdeckung_symbole: int = 0
    hypothesen: int = 1
    klammer: str = "tag"
    kosten_je_seite: float = 0.0
    protokoll: Protokoll | None = None

    def __post_init__(self) -> None:
        if self.zielgroesse not in ZIELGROESSEN:
            raise ValueError("unbekannte Zielgroesse: %r" % self.zielgroesse)
        if self.zielgroesse == "barriere" and not self.lage.stop_beendet:
            raise ValueError(
                "Zielgroesse 'barriere' ist fuer %s nicht zulaessig - dort "
                "beendet kein Stop den Trade. Sie misst dann die eigene "
                "Zielregel zurueck (Konzept Bewertungsstufe, 23.08.)."
                % self.lage)
        if self.klammer != "tag":
            raise ValueError("nur die Tagesklammer ist zulaessig (31.08.)")
        if self.kosten_je_seite != 0.0:
            raise ValueError("jede Rangfolge rechnet gebuehrenfrei (Regel 2)")
        # ⚠️ DIE KONTROLLEN SIND PFLICHT, NICHT OPTION.
        if self.protokoll is None:
            raise ValueError(
                "kein Befund ohne PROTOKOLL - der Weg gehoert zum Urteil, "
                "weil dort die Fehler passieren (Nutzervorgabe 06.09.)")
        if not self.gepflanzt:
            raise ValueError(
                "ohne Positivkontrolle kein Befund - ein 'traegt nicht' "
                "ohne Trennschaerfe ist keine Messung, sondern das Fehlen "
                "einer (Methodik 2.88, 2.100)")

    @property
    def traegt(self) -> bool:
        return self.unten > max(0.0, self.null_oben)

    @property
    def urteil(self) -> str:
        """VIER Urteile — und nur zwei davon sind Aussagen ueber die Welt.

        ⚠️ DER KERN DIESES MODULS. Bisher gab es "traegt" und "traegt
        nicht", und das zweite verschwieg, ob die Messung den Effekt
        ueberhaupt haette finden koennen. Hier gilt:

            TRAEGT              Band schliesst den Nullpunkt aus
            TRAEGT NICHT BIS X  die Positivkontrolle hat X gefunden, die
                                Messung sieht nichts -> Effekte ab X sind
                                AUSGESCHLOSSEN. Eine echte Aussage.
            NICHT TRENNBAR      die Wirkung liegt ueber X, aber das Band
                                schliesst die Null ein - zu unpraezise
            KEIN BEFUND         zu wenige Bloecke, oder selbst die groesste
                                gepflanzte Staerke wurde nicht gefunden.
                                Eine Aussage ueber die MESSUNG, nicht ueber
                                die Welt - und sie wird nicht als
                                Nullbefund ausgegeben.

        ⚠️ Der Unterschied zwischen "TRAEGT NICHT BIS X" und "KEIN BEFUND"
        ist genau der, den zwei Tage lang gefehlt hat.
        """
        if self.n_bloecke < 20:
            return ("KEIN BEFUND - nur %d Bloecke, das Band deckt nicht "
                    "(bei 5 Bloecken 19,5 %% Fehlalarme statt 5 %%)"
                    % self.n_bloecke)
        if self.trennschaerfe is None:
            return ("KEIN BEFUND - untermaechtig: selbst %+.2f R gepflanzt "
                    "wurde nicht gefunden" % max(self.gepflanzt))
        einheit = ZIELGROESSEN[self.zielgroesse].get("einheit", "R")
        if self.traegt:
            return "TRAEGT"
        if abs(self.wirkung) < self.trennschaerfe:
            return ("TRAEGT NICHT bis %.4f %s%s (Effekte ab dieser Groesse "
                    "sind ausgeschlossen)"
                    % (self.trennschaerfe, einheit,
                       ("" if (self.trennschaerfe_in_r is None
                                or einheit == "R")
                        else " = %.2f R gepflanzt" % self.trennschaerfe_in_r)))
        return ("NICHT TRENNBAR - Wirkung %+.4f ueber der Trennschaerfe "
                "%.4f %s, aber das Band schliesst die Null ein"
                % (self.wirkung, self.trennschaerfe, einheit))

    def zeile(self) -> str:
        return ("%-16s %-28s %-11s %-6s %+8.4f R [%+.4f .. %+.4f] · "
                "Null %+.4f · Trennsch. %s · %d Tage/%d Bl. · %d Sym · %s"
                % (self.kandidat, str(self.lage), self.zielgroesse, self.menge,
                   self.wirkung, self.unten, self.oben, self.nullpunkt,
                   ("%.4f" % self.trennschaerfe) if self.trennschaerfe
                   else "KEINE", self.n_tage, self.n_bloecke,
                   self.abdeckung_symbole, self.urteil))


def _block(horizont: int) -> int:
    """Der Block muss laenger sein als die ABHAENGIGKEIT - gemessen, nicht
    gesetzt (06.09.2026).

    ⚠️ `messe_regel_wirksamkeit` rechnet `max(90, 3 x HORIZONT)`. Der Boden
    von 90 Tagen ist eine SETZUNG, keine Messung - und er macht den einzigen
    vergleichbaren Marktabschnitt unmessbar:

        2024-2026 sind rund 960 Kalendertage
        Block 90 -> 10 Bloecke   unter der Grenze von 20, fuer JEDE Menge

    Nachgemessen (Autokorrelation der Tageswirkung, `schnitt50`):

        H     lag 1   lag 5   lag 10  lag 15  lag 30
         5    0,634   0,037  -0,032  -0,004  -0,024    weg nach 5 Tagen
        10    0,702   0,319   0,004  -0,020  -0,101    weg nach 10
        20    0,733   0,486   0,247   0,109  -0,064    weg nach 30

    **Die Abhaengigkeit reicht genau so weit wie der Horizont** - wie die
    Theorie ueberlappender Fenster es verlangt. `3 x Horizont` ist damit
    dreifach konservativ; der Boden von 90 ist es nicht, er ist willkuerlich.

    ⚠️ ABER: die Blocklaenge wird je Messung NACHGEPRUEFT (`pruefe_block`),
    nicht angenommen. Wer sie nur setzt, hat sie geraten.
    """
    return max(15, 3 * int(horizont))


def pruefe_block(d: dict, block: int, grenze: float = 0.15) -> dict:
    """Ist der Block laenger als die ABHAENGIGKEIT? — je Messung belegt.

    Gibt die Autokorrelation der Tageswirkung beim Abstand `block` zurueck.
    Liegt sie ueber `grenze`, ist der Block zu kurz und das Band zu eng.
    """
    tage = sorted(d)
    if len(tage) < block + 30:
        return {"lag": block, "ak": float("nan"), "ok": False,
                "grund": "zu wenige Tage fuer die Pruefung"}
    x = np.array([d[t] for t in tage], float)
    a, b = x[:-block], x[block:]
    if a.std() < 1e-12 or b.std() < 1e-12:
        return {"lag": block, "ak": 0.0, "ok": True, "grund": "keine Streuung"}
    ak = float(np.corrcoef(a, b)[0, 1])
    return {"lag": block, "ak": ak, "ok": abs(ak) <= grenze,
            "grund": ("Abhaengigkeit abgeklungen" if abs(ak) <= grenze
                      else "⚠️ Block ZU KURZ - das Band waere zu eng")}


def pruefe(kandidat: str, je_tag: dict, *, lage: Lage, zielgroesse: str,
           menge: str, rng, horizont: int = 20,
           staerken: tuple = (0.02, 0.05, 0.10), hypothesen: int = 1,
           oben_sperren: bool = True, still: bool = True) -> Befund:
    """DIE eine Messung. Alles andere ruft sie.

    ⚠️ Sie benutzt `messe_regel_wirksamkeit.wirkung()` und
    `messe_bewertungskennzahl.urteil_tage()` — dieselben Funktionen, mit
    denen F-212 gerechnet und reproduziert wurde. Keine Nachbildung.
    """
    if zielgroesse not in ZIELGROESSEN:
        raise ValueError("unbekannte Zielgroesse: %r" % zielgroesse)
    block = _block(horizont)

    def _band(d, titel):
        if still:
            import io
            import contextlib
            with contextlib.redirect_stdout(io.StringIO()):
                return M.urteil_tage(titel, d, rng, block)
        return M.urteil_tage(titel, d, rng, block)

    d, _anteil, _g, _u = W.wirkung(je_tag, oben_sperren)
    haupt = _band(d, kandidat)
    if haupt is None:
        raise ValueError("zu wenige Tage fuer ein Band (%d)" % len(d))

    # ⚠️ MEHRERE ZIEHUNGEN, NICHT EINE (06.09., gemessen).
    # Die Basislinie wandert je Saat zwischen -0,0055 und +0,0010 - also um
    # denselben Betrag wie die gesuchten Effekte. Eine Ziehung ist kein
    # Nullpunkt (Methodik 2.104).
    nullwerte, nullunten, nulloben = [], [], []
    for z in range(ZIEHUNGEN):
        n0, _a, _g2, _u2 = W.wirkung(
            je_tag, oben_sperren, mische=np.random.default_rng(SAAT + z))
        nb = _band(n0, "null %d" % z)
        if nb:
            nullwerte.append(nb["mittel"])
            nullunten.append(nb["unten"])
            nulloben.append(nb["oben"])
    null = {"mittel": float(np.mean(nullwerte)) if nullwerte else 0.0,
            "unten": float(np.min(nullunten)) if nullunten else 0.0,
            "oben": float(np.max(nulloben)) if nulloben else 0.0}

    # ⚠️ DIE TRENNSCHAERFE: die KLEINSTE gepflanzte Staerke, die gefunden
    # wird. Sie ist die eigentliche Neuerung - ohne sie ist "traegt nicht"
    # nicht von "haetten wir gar nicht sehen koennen" zu unterscheiden.
    trennschaerfe = None
    treffer = {}
    for s in sorted(staerken):
        # ⚠️ IN DIE GEMISCHTE WELT PFLANZEN (06.09., von der Gegenpruefung
        # gefunden).
        #
        # Die erste Fassung pflanzte auf die ECHTEN Daten obendrauf. Steckt
        # im Kandidaten schon ein Effekt, misst die Kontrolle dann
        # `Effekt + Pflanzung` statt der Pflanzung allein - und die
        # Trennschaerfe faellt zu gut aus. Sichtbar wurde es an einer
        # Kunstwelt mit 0,03 R Effekt: die Norm meldete "traegt nicht bis
        # 0,02 R", also eine Schranke UNTER dem tatsaechlich vorhandenen
        # Effekt. Ein Widerspruch in sich.
        #
        # `mische` zerstoert das echte Signal, `pflanze` legt ein bekanntes
        # hinein. Erst dann beantwortet die Zahl die Frage, die sie stellen
        # soll: haette diese Anlage einen Effekt DIESER Groesse gefunden?
        gefunden = 0
        for z in range(ZIEHUNGEN):
            misch_rng = np.random.default_rng(SAAT + 1000 * z + int(s * 1000))
            p, _a2, _g3, _u3 = W.wirkung(je_tag, oben_sperren,
                                         mische=misch_rng, pflanze=s)
            pb = _band(p, "pflanze %.2f/%d" % (s, z))
            if pb and pb["unten"] > 0:
                gefunden += 1
        treffer[s] = gefunden
        # ⚠️ MEHRHEIT, NICHT EIN TREFFER. Bei einer Ziehung entscheidet die
        # Saat - gemessen wanderte die Basislinie um den Betrag des
        # gesuchten Effekts.
        if trennschaerfe is None and gefunden >= max(3, (4 * ZIEHUNGEN) // 5):
            trennschaerfe = s

    n_anker = sum(len(z) for z in je_tag.values())
    syms = len({x["sym"] for z in je_tag.values() for x in z})
    return Befund(
        kandidat=kandidat, lage=lage, zielgroesse=zielgroesse, menge=menge,
        wirkung=haupt["mittel"], unten=haupt["unten"], oben=haupt["oben"],
        nullpunkt=null["mittel"], null_unten=null["unten"],
        null_oben=null["oben"], trennschaerfe=trennschaerfe,
        trennschaerfe_in_r=trennschaerfe,   # beim Mittel dieselbe Einheit
        gepflanzt=tuple(sorted(staerken)), n_anker=n_anker,
        n_tage=haupt["tage"], n_bloecke=max(1, haupt["tage"] // block),
        abdeckung_symbole=syms, hypothesen=hypothesen,
        protokoll=Protokoll(
            wirkung_funktion="messe_regel_wirksamkeit.wirkung",
            band_funktion="messe_bewertungskennzahl.urteil_tage",
            null_konstruktion="Raenge je Tag gemischt",
            null_ziehungen=ZIEHUNGEN,
            positiv_konstruktion="in die gemischte Welt gepflanzt, "
                                 "auf die Gesperrten",
            positiv_ziehungen=ZIEHUNGEN, positiv_treffer=treffer,
            blocklaenge=block, saat=SAAT))


# ------------------------------------------------------------- Selbsttest
def _welt(rng, tage=2400, syms=40, effekt=0.0):
    # ⚠️ 2400 TAGE, NICHT 900 (06.09., der Selbsttest hat es gefunden).
    # Der Block ist 3 x Horizont = 90 Tage; 900 Tage ergeben 10 Bloecke, und
    # bei unter 20 verweigert die Norm das Urteil - zu Recht (bei 5 Bloecken
    # 19,5 % Fehlalarme statt 5 %). Die Kunstwelt muss also mindestens so
    # gross sein wie die echte Anforderung, sonst prueft der Test die Norm
    # gar nicht, sondern nur ihre Schutzschwelle.
    """Kunstwelt: die obersten 20 % nach Kennzahl sind um `effekt` schlechter."""
    # ⚠️ NACH DEM RANG PFLANZEN, NICHT NACH DEM ROHWERT (06.09., von der
    # Gegenpruefung gefunden).
    #
    # Erste Fassung pflanzte auf `k >= 0.80`. `wirkung` sperrt aber nach dem
    # RANG innerhalb des Tages (`rang(w) >= GRENZE`). Bei 40 Symbolen fallen
    # beide Gruppen nur teilweise zusammen - der gepflanzte Effekt verduennt
    # sich, und die Kunstwelt prueft etwas anderes als das Werkzeug tut.
    # Sichtbar wurde es daran, dass eine Welt mit 0,03 R Effekt als "traegt
    # nicht bis 0,02 R" gemeldet wurde: eine Schranke UNTER dem vorhandenen
    # Effekt.
    je_tag = {}
    grenze = int(round(syms * 0.80))
    for t in range(tage):
        ks = [float(rng.random()) for _ in range(syms)]
        rs = [float(rng.normal(0, 1.0)) for _ in range(syms)]
        ordnung = sorted(range(syms), key=lambda i: ks[i])
        z = []
        for platz, i in enumerate(ordnung):
            r = rs[i] - (effekt if platz >= grenze else 0.0)
            z.append({"sym": "S%02d" % i, "kennzahl": ks[i], "in_r": r})
        je_tag["t%04d" % t] = z
    return je_tag


def selbsttest() -> bool:
    print("=" * 96)
    print("SELBSTTEST DER MESSNORM")
    print("=" * 96)
    ok = True
    L = Lage("spot", "einstieg")

    # 1 — die Lage
    print("\n1. Die AUSGANGSLAGE wird erzwungen")
    for inst, strat, erw in (("spot", "einstieg", True),
                             ("hebel", "akkumulation", False),
                             ("quatsch", "einstieg", False)):
        try:
            Lage(inst, strat)
            got = True
        except ValueError:
            got = False
        gut = got is erw
        ok &= gut
        print("   %-24s -> %-9s %s" % ("%s x %s" % (inst, strat),
                                       "erlaubt" if got else "abgelehnt",
                                       "OK" if gut else "✖"))
    try:
        Lage("spot", "einstieg", richtung="short")
        ok = False
        print("   short                    -> erlaubt   ✖ (muss abgelehnt werden)")
    except ValueError:
        print("   short                    -> abgelehnt OK")

    # ein gueltiges Protokoll, damit die anderen Pruefungen isoliert greifen
    def _prot(**aend):
        werte = dict(
            wirkung_funktion="messe_regel_wirksamkeit.wirkung",
            band_funktion="messe_bewertungskennzahl.urteil_tage",
            null_konstruktion="Raenge je Tag gemischt", null_ziehungen=5,
            positiv_konstruktion="in die gemischte Welt gepflanzt",
            positiv_ziehungen=5, positiv_treffer={0.02: 5},
            blocklaenge=90, saat=1)
        werte.update(aend)
        return Protokoll(**werte)

    def _befund(**aend):
        werte = dict(kandidat="x", lage=L, zielgroesse="bewegung_r",
                     menge="frei", wirkung=0.0, unten=0.0, oben=0.0,
                     nullpunkt=0.0, null_unten=0.0, null_oben=0.0,
                     trennschaerfe=0.02, gepflanzt=(0.02,), protokoll=_prot())
        werte.update(aend)
        return Befund(**werte)

    # 2 — die Zielgroesse an der Lage
    print("")
    print("2. 'barriere' nur, wo ein Stop den Trade beendet")
    for lage, erw in ((Lage("spot", "akkumulation"), False),
                      (Lage("hebel", "einstieg", simuliert=True), True)):
        try:
            _befund(lage=lage, zielgroesse="barriere")
            got = True
        except ValueError:
            got = False
        ok &= got is erw
        print("   %-36s -> %-9s %s"
              % (lage, "erlaubt" if got else "abgelehnt",
                 "OK" if got is erw else "✖"))

    # 3 — DER WEG wird geprueft, nicht nur das Ergebnis
    #
    # ⚠️ Nutzerhinweis 06.09.: *„zur Urteilslogik gehoert nicht nur das
    # Ergebnis, sondern der Weg dorthin, wo die eigentlichen Fehler
    # passieren."* Jeder dieser sechs Irrwege hat am 05./06.09. eine
    # plausible Zahl erzeugt - keiner war am Ergebnis erkennbar.
    print("")
    print("3. Der WEG wird geprueft - sechs bekannte Irrwege")
    # ⚠️ TRAEGE, nicht vorgebaut: das Protokoll lehnt einen Irrweg schon bei
    # der eigenen Konstruktion ab. Wer die Faelle vorher baut, faellt beim
    # AUFBAU des Tests durch statt im Test.
    faelle = (
        ("ohne Protokoll", lambda: _befund(protokoll=None)),
        ("ohne Positivkontrolle",
         lambda: _befund(gepflanzt=(), trennschaerfe=None)),
        ("Pflanzung auf ECHTE Daten",
         lambda: _befund(protokoll=_prot(
             positiv_konstruktion="auf die echten Daten"))),
        ("Nullpunkt aus EINER Ziehung",
         lambda: _befund(protokoll=_prot(null_ziehungen=1))),
        ("mit Gebuehren gerechnet", lambda: _befund(kosten_je_seite=0.015)),
        ("gepoolt statt Tagesklammer", lambda: _befund(klammer="gepoolt")),
    )
    for name, bauen in faelle:
        try:
            bauen()
            ok = False
            print("   %-30s -> DURCHGELASSEN  ✖" % name)
        except ValueError:
            print("   %-30s -> abgelehnt      OK" % name)

    # 4 — die drei Urteile an Kunstwelten
    print("\n4. Die DREI Urteile")
    rng = np.random.default_rng(20260906)
    faelle = (("klarer Effekt +0,10 R", 0.10),
              ("kein Effekt", 0.0))
    for name, eff in faelle:
        b = pruefe("kunst", _welt(rng, effekt=eff), lage=L,
                   zielgroesse="bewegung_r", menge="frei", rng=rng)
        print("   %-24s %+7.4f R · Trennsch. %s · %s"
              % (name, b.wirkung,
                 ("%.2f" % b.trennschaerfe) if b.trennschaerfe else "KEINE",
                 b.urteil))
        # ⚠️ DIE WIRKUNG IST KOMPRIMIERT. `wirkung` rechnet
        # median(frei) - median(alle); ein Effekt auf den obersten 20 %
        # verschiebt den Gesamtmedian nur zu einem Bruchteil. Geprueft wird
        # deshalb das URTEIL, nicht die Hoehe.
        if eff > 0 and b.urteil != "TRAEGT":
            ok = False
            print("      ✖ ein gepflanzter Effekt muss gefunden werden")
        if eff == 0 and b.urteil == "TRAEGT":
            ok = False
            print("      ✖ ohne Effekt darf nichts tragen")
        if eff == 0 and not b.urteil.startswith("TRAEGT NICHT"):
            ok = False
            print("      ✖ ohne Effekt muss eine SCHRANKE herauskommen, "
                  "kein Achselzucken")

    # 5 — untermaechtig wird als KEIN BEFUND ausgewiesen
    print("\n5. Wenige Tage -> KEIN BEFUND statt 'traegt nicht'")
    b = pruefe("kunst_kurz", _welt(rng, tage=200), lage=L,
               zielgroesse="bewegung_r", menge="frei", rng=rng)
    gut = b.urteil.startswith("KEIN BEFUND")
    ok &= gut
    print("   %d Tage / %d Bloecke -> %s  %s"
          % (b.n_tage, b.n_bloecke, b.urteil, "OK" if gut else "✖"))

    print()
    print("=" * 96)
    print("SELBSTTEST %s" % ("BESTANDEN" if ok else "✖ FEHLGESCHLAGEN"))
    print("=" * 96)
    return ok


if __name__ == "__main__":
    sys.exit(0 if selbsttest() else 1)
