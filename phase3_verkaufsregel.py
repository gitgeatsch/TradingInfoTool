# -*- coding: utf-8 -*-
"""V3b-1: TRAEGT `funding` ALS VERKAUFSREGEL? (19.09.2026, Paket V)

⚠️⚠️ DIE ZIELGROESSE IST EINE ANDERE ALS IN V2 - und das ist der Kern.

Die Methodikrecherche (2.472) hat gezeigt, wie eine Verkaufsentscheidung
bewertet wird: nicht an der Bewegung nach dem Verkauf, sondern gegen die
ALTERNATIVE ENTSCHEIDUNG. Akepanidtaworn/Di Mascio/Imas/Schmidt, Journal of
Finance 2023, rechnen fuer Verkaeufe die *Rendite der BEHALTENEN minus die
Rendite der VERKAUFTEN*. Genau das steht hier:

    Zielgroesse = median(bewegung_r der BEHALTENEN)
                - median(bewegung_r der VERKAUFTEN)

    POSITIV heisst: die behaltenen Werte liefen besser - der Verkauf war
    richtig. NEGATIV heisst: man hat das Falsche verkauft.

⚠️ V2 hat die Bewegung NACH dem Ausstieg gemessen (2.470). Das beantwortet
Verkaufsfall 3 und 4 (Gewinnmitnahme, Absicherung). DIESE Messung
beantwortet Fall 1 - *es gibt Besseres* - und nur der steht auf einer
gemessenen Grundlage.

## Warum nur `funding`

2.474: auf der EIGENTLICHEN Haltefrage (gehalten, aber heute nicht mehr
unter den obersten 20 %) traegt allein `funding` (+0,0293 R, 21 Bloecke).
`oi_aenderung` verliert dort das Band, `turnover` ist zu duenn. Eine
Verkaufsregel auf einem Beitrag zu bauen, der die Haltefrage nicht traegt,
waere derselbe Fehler wie 2.287 (funding und oi_aenderung laufen fuer die
Akkumulation umgekehrt).

## Die Regel, die geprueft wird

    Innerhalb der Haltemenge nach `funding` rangieren; das oberste Fuenftel
    gilt als VERKAUFT, der Rest als BEHALTEN.

Das ist dieselbe Mechanik wie auf der Einstiegsseite (`RW.GRENZE`), nur mit
umgekehrter Verwendung: dort sperrt das oberste Fuenftel den Einstieg, hier
loest es den Verkauf aus.

⚠️ KEIN EINGRIFF IN DIE KETTE. Dieses Skript misst nur. Ob der `return`
nach `_sende_ausstieg` faellt, ist V3b-2 und braucht erst ein Ergebnis hier.

⚠️ Stellvertretermenge (N3 b), nur lesend, kein LLM.
"""
from __future__ import annotations

import sys
import time

import numpy as np

import messnorm
import messmenge
import messe_regel_wirksamkeit as RW
import phase3_reproduktion as R
from messe_beitrag_auf_auswahl import momentum250
from n64_schnitt_stufen import band
from phase3_haltefrage import ANTEIL_KAUF, HALTE_FENSTER, geteilt, haltemenge

AB_2023 = "2023-01-01"
KANDIDAT = "funding"
MINDEST_JE_SEITE = 3      # sonst ist ein Median ein Einzelwert
NULL_ZIEHUNGEN = messnorm.NULL_ZIEHUNGEN
VORBEHALT = ("gilt auf der Stellvertretermenge (N3 b); die Haltemenge ist ein "
             "Stellvertreter des echten Bestands")


def regel(je_tag: dict, menge: dict, rng=None, pflanze: float = 0.0,
          mindest_verkauft: int = 1) -> dict:
    """tag -> (behalten minus verkauft) in R.

    `rng` macht daraus die NULLWELT: gleich viele werden verkauft, aber
    zufaellig gewaehlte. Ohne sie misst man, DASS verkauft wurde, nicht
    WONACH.

    ⚠️⚠️ `mindest_verkauft` - DIE BESETZUNG DER KLEINEN SEITE (nachgetragen
    19.09.2026). Die verkaufte Seite ist das oberste Fuenftel und damit
    VIERMAL KLEINER als die behaltene. Genau davor warnt die stehende
    Vorgabe vom 07.09.: `median(Gruppe) minus median(Rest)` ist bei
    UNGLEICH grossen Gruppen verzerrt, und unter zwei Ankern je Gruppe ist
    die Statistik nicht brauchbar - dort kamen +0,10 bis +0,16 R aus einer
    Welt ohne jede Information. Die erste Fassung liess `verkauft >= 1` zu,
    also Tage mit einem EINZIGEN verkauften Wert.

    ⚠️ DIE VERZERRUNG IST NICHT DER FEHLER - sie steckt gleichermassen in
    der Nullwelt und wird durch den Vergleich mit ihr abgezogen. Der Fehler
    waere, sie nicht zu KENNEN. Die Vorgabe von 1 laesst jeden bestehenden
    Aufruf unveraendert rechnen (R-R11); wer sie hochsetzt, misst dieselbe
    Frage auf besser besetzten Tagen."""
    aus = {}
    for tag, zeilen in je_tag.items():
        if tag < AB_2023:
            continue
        erlaubt = menge.get(tag) or set()
        z = [x for x in zeilen if x["sym"] in erlaubt]
        if len(z) < 2 * MINDEST_JE_SEITE:
            continue
        kz = np.array([x["kennzahl"] for x in z], float)
        y = np.array([x["in_r"] for x in z], float)
        ok = np.isfinite(kz) & np.isfinite(y)
        if ok.sum() < 2 * MINDEST_JE_SEITE:
            continue
        kz, y = kz[ok], y[ok]
        if rng is None:
            # ⚠️ DER RANG KOMMT AUS DER MENGE SELBST - wer innerhalb der
            # Haltemenge verkauft, vergleicht mit dem, was er haelt.
            verkauft = RW.rang(kz) >= RW.GRENZE
        else:
            n = int(max(1, round(len(kz) * (1.0 - RW.GRENZE))))
            verkauft = np.zeros(len(kz), bool)
            verkauft[rng.choice(len(kz), min(n, len(kz) - 1),
                                replace=False)] = True
        if (verkauft.sum() < max(1, int(mindest_verkauft))
                or (~verkauft).sum() < MINDEST_JE_SEITE):
            continue
        y2 = y.copy()
        if pflanze:
            # ⚠️ GEPFLANZT WIRD IN DIE VERKAUFTEN: sie werden schlechter
            # gemacht, der Verkauf also zu Recht richtig. Dieselbe
            # Konstruktion wie in `messnorm`.
            #
            # ⚠️ WAS DARAN NICHT PRUEFBAR IST (19.09.2026, Gegenpruefung):
            # die Zielgroesse ist eine DIFFERENZ, also waere +p in die
            # Behaltenen dasselbe. Die Seite ist eine Frage der Lesbarkeit,
            # nicht der Rechnung. Schiefgehen kann nur: in ALLE pflanzen
            # (Differenz bleibt 0) oder das Vorzeichen drehen.
            y2[verkauft] -= pflanze
        aus[tag] = (float(np.median(y2[~verkauft]))
                    - float(np.median(y2[verkauft])))
    return aus


def besetzung(je_tag: dict, menge: dict, mindest_verkauft: int = 1) -> tuple:
    """Wie viele Werte stehen je Tag auf jeder Seite? (Tage, verkauft, behalten)

    ⚠️ STEHENDE VORGABE (07.09.2026): *vor jeder Gruppenstatistik die
    Besetzung je Gruppe und Tag ausgeben, bevor irgendeine Zahl gedeutet
    wird.* V3b-1 hat das nicht getan - nachgetragen am 19.09."""
    v, b = [], []
    for tag, zeilen in je_tag.items():
        if tag < AB_2023:
            continue
        erlaubt = menge.get(tag) or set()
        z = [x for x in zeilen if x["sym"] in erlaubt]
        kz = np.array([x["kennzahl"] for x in z], float)
        y = np.array([x["in_r"] for x in z], float)
        if len(z) < 2 * MINDEST_JE_SEITE:
            continue
        ok = np.isfinite(kz) & np.isfinite(y)
        if ok.sum() < 2 * MINDEST_JE_SEITE:
            continue
        kz = kz[ok]
        verkauft = RW.rang(kz) >= RW.GRENZE
        if (verkauft.sum() < max(1, int(mindest_verkauft))
                or (~verkauft).sum() < MINDEST_JE_SEITE):
            continue
        v.append(int(verkauft.sum()))
        b.append(int((~verkauft).sum()))
    return (len(v), float(np.mean(v)) if v else float("nan"),
            float(np.mean(b)) if b else float("nan"),
            int(np.min(v)) if v else 0)


def blockpruefung(echt: dict, block: int) -> str:
    """⚠️ DIE BLOCKLAENGE WIRD BELEGT, NICHT GESETZT (nachgetragen 19.09.2026).

    `messnorm._block` schreibt es seit dem Bau vor: *die Blocklaenge wird je
    Messung NACHGEPRUEFT, nicht angenommen. Wer sie nur setzt, hat sie
    geraten.* Die erste Fassung dieses Moduls hat sie gesetzt - derselbe
    Fehler, den `messnorm.pruefe()` am 06.09. an sich selbst gefunden hat
    (Schritt 4a, G1). Ein zu kurzer Block macht das Band ZU ENG, und genau
    an einer Bandbreite haengt hier das Urteil.
    """
    bp = messnorm.pruefe_block(echt, block)
    return ("Block %d · Autokorrelation %+.3f (Grenze 0,15) · %s"
            % (block, bp["ak"], bp["grund"]))


def urteil(name: str, echt: dict, nullwerte: list, block: int,
           trennschaerfe: float | None) -> None:
    b = band(echt, block)
    tage = len(echt)
    punkt = b[0] if b else float("nan")
    nw = float(np.mean(nullwerte)) if nullwerte else float("nan")
    oben = (float(np.percentile(nullwerte, messnorm.NULL_PERZENTIL))
            if nullwerte else float("nan"))
    # ⚠️ DIE REIHENFOLGE IST DIE VON `messnorm` (korrigiert 19.09.2026, beim
    # ersten Lauf aufgefallen): erst das Band gegen den Nullpunkt, dann die
    # Trennschaerfe. Meine erste Fassung schrieb "TRAEGT NICHT bis 0,02 R",
    # obwohl die Wirkung mit +0,1382 weit DARUEBER lag - das ist der Fall
    # "NICHT TRENNBAR", und der sagt etwas ganz anderes: die Groesse ist da,
    # das Band deckt sie nur nicht.
    wirkung = punkt - nw
    if not b:
        text = "KEIN BAND (%d Tage, %d noetig)" % (tage, 2 * block)
    elif b[1] > oben:
        text = "TRAEGT - das Band schliesst den Nullpunkt aus"
    elif trennschaerfe is None:
        text = "KEIN BEFUND - die Positivkontrolle findet nichts"
    elif abs(wirkung) < trennschaerfe:
        text = ("TRAEGT NICHT bis %.2f R (Wirkung %+.4f entzerrt)"
                % (trennschaerfe, wirkung))
    else:
        text = ("NICHT TRENNBAR - Wirkung %+.4f ueber der Trennschaerfe "
                "%.2f R, aber das Band schliesst den Nullpunkt ein"
                % (wirkung, trennschaerfe))
    spanne = ("[%+.4f .. %+.4f]" % (b[1], b[2])) if b else "-"
    # ⚠️ DIE OBERE NULLGRENZE GEHOERT IN DIE AUSGABE - ohne sie ist das
    # Urteil nicht nachpruefbar, und genau daran haengt es.
    print("     %-30s %+9.4f %-22s %+9.4f (oben %+.4f) %5d   %s"
          % (name, punkt, spanne, nw, oben, tage, text))


def main() -> int:
    t0 = time.time()
    print("=" * 112)
    print("V3b-1 - TRAEGT `%s` ALS VERKAUFSREGEL? (behalten minus verkauft)"
          % KANDIDAT)
    print("=" * 112)
    print("  " + messmenge.zeile())
    print("  " + messnorm.standardzeile().replace("\n", "\n  "))
    print("  Zielgroesse nach 2.472: POSITIV = die Behaltenen liefen besser, "
          "der Verkauf war richtig")
    print("  ⚠️ %s" % VORBEHALT)

    print("\n  Kursreihen laden ...")
    reihen = R.B.lade("krypto", "V1")
    mom = momentum250(reihen)
    halte = haltemenge(mom)
    drin, raus = geteilt(mom, halte)
    je_tag = R.K.baue(reihen, KANDIDAT, R._zusatz(KANDIDAT),
                      horizont=R.HORIZONT)
    print("  %d Reihen · Haltemenge %.0f je Tag · davon nicht mehr in der "
          "Auswahl %.0f (%.0f s)"
          % (len(reihen),
             float(np.mean([len(v) for v in halte.values() if v])),
             float(np.mean([len(v) for v in raus.values() if v])),
             time.time() - t0))

    block = messnorm._block(R.HORIZONT)
    rng = np.random.default_rng(messnorm.SAAT)
    print("\n  %-30s %9s %-22s %9s %5s   %s"
          % ("Menge", "R", "Band", "Nullwelt", "Tage", "Urteil"))
    for name, menge in (("ganze Haltemenge", halte),
                        ("nur: nicht mehr in der Auswahl", raus),
                        ("nur: noch in der Auswahl", drin)):
        echt = regel(je_tag, menge)
        if len(echt) < 30:
            print("     %-30s zu wenige Tage (%d)" % (name, len(echt)))
            continue
        nullwerte = []
        for i in range(NULL_ZIEHUNGEN):
            n = regel(je_tag, menge,
                      rng=np.random.default_rng(messnorm.SAAT + i))
            nb = band(n, block, zieh=300, saat=messnorm.SAAT + i)
            if nb:
                nullwerte.append(nb[0])
        # Positivkontrolle: ab welcher gepflanzten Staerke findet die Anlage?
        oben = (float(np.percentile(nullwerte, messnorm.NULL_PERZENTIL))
                if nullwerte else float("nan"))
        ts = None
        for staerke in messnorm.STAERKEN:
            treffer = 0
            for i in range(messnorm.ZIEHUNGEN):
                pw = regel(je_tag, menge, pflanze=staerke)
                pb = band(pw, block, zieh=300, saat=messnorm.SAAT + 1000 + i)
                if pb and pb[1] > oben:
                    treffer += 1
            if treffer >= max(3, (4 * messnorm.ZIEHUNGEN) // 5):
                ts = staerke
                break
        urteil(name, echt, nullwerte, block, ts)
        print("     %-30s Positivkontrolle: Trennschaerfe %s · %s"
              % ("", ("%.2f R" % ts) if ts else "KEINE",
                 blockpruefung(echt, block)))

    print("\n  LESEART")
    print("     R          behalten minus verkauft. POSITIV = der Verkauf war")
    print("                richtig (die Behaltenen liefen besser).")
    print("     Nullwelt   gleich viele verkauft, aber ZUFAELLIG gewaehlt")
    print("                (%d Ziehungen) - sonst misst man, DASS verkauft"
          % NULL_ZIEHUNGEN)
    print("                wurde, nicht WONACH.")
    print("\n  ⚠️ %s" % VORBEHALT)
    print("  (%.0f s)" % (time.time() - t0))
    print("=" * 112)
    return 0


if __name__ == "__main__":
    sys.exit(main())
