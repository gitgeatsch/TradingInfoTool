# -*- coding: utf-8 -*-
"""Phase 3, Punkt 3b: WAS TRAEGT DIE STUFE `entscheider`? (19.09.2026)

M1-Kriterium 1, zweite Stufe. Dieselbe Frage wie bei `auswahl`, dasselbe
Mass:

    MIT     die Anker, die `potential.traegt_hier` durchlaesst
    OHNE    alle Anker, die die Stufe ueberhaupt erreichen

    Zielgroesse = median(bewegung_r der DURCHGELASSENEN)
                - median(bewegung_r der ERREICHENDEN)

## ⚠️ EINE FRAGE, EINE ZELLE - und warum das hier ausdruecklich steht

Die Auswahlmessung lief ueber vier Anteile. Solange die Norm den
Mehrfachvergleich nicht selbst rechnet (Schritt 64, Punkt A), bleibt jede
weitere Phase-3-Messung bei EINER Zelle - dann entsteht keine Nacharbeit,
wenn die Norm nachgezogen wird.

## ⚠️⚠️ DER ENTSCHEIDER WIRD AUFGERUFEN, NICHT NACHGEBAUT

`agent.potential.rechne()` ist die Betriebsfunktion, und `traegt_hier`
ist die Betriebsentscheidung. Ein Nachbau ist am 19.09. schon einmal
durchgefallen (2.466: die nachgebaute Auswahl traf 23,7 % statt 60,6 %).

Die Fuenftel kommen aus `marktrang._rang` und `marktrang._fuenftel` -
ebenfalls die echten Funktionen, und beide sind rein rechnend, ohne
Netzaufruf.

## Der einzige freie Parameter ist der CRV

`potential.rechne` verlangt `crv` und `stop_relativ`. Der Stopabstand
faellt heraus: er geht nur in `kosten_r = 2 x Gebuehr / stop_relativ` ein,
und `potential` ruft gebuehrenfrei auf (Nutzervorgabe 30.08.: *die
Bewertung soll ohne Wirtschaftlichkeit erfolgen*). Er muss nur positiv
sein.

Der CRV dagegen entscheidet mit: `wert_r = q x crv - (1 - q)`. Historisch
gibt es ihn nicht je Anker - er entsteht live aus der Geometrie. Er wird
deshalb auf die LIVE-DURCHLASSQUOTE kalibriert (Produktionssicherung
19.09. 12:09: 46 von 132 Zeilen mit Potential ueber ihrer Schwelle, also
34,8 %). ⚠️ Das ist eine Kalibrierung, kein gemessener Wert, und sie steht
als Vorbehalt im Befund.

⚠️ Stellvertretermenge (N3 b), Fenster ab 2023, nur lesend, kein LLM.
"""
from __future__ import annotations

import sys
import time

import numpy as np

import messe_beitrag_auf_auswahl as A
import messnorm
import messmenge
import phase3_reproduktion as R
from agent import marktrang as MR
from agent import potential as PT
from messe_beitrag_auf_auswahl import momentum250
from messnorm_auswahl import MENGEN, MIND_ANKER
from n64_schnitt_stufen import band
# ⚠️ Importiert, nicht kopiert - siehe phase3_stufen.
from phase3_verkaufsregel import blockpruefung, urteil
from phase3_verkaufsregel_basis import stabilitaet

AB = "2023-01-01"
TRAEGER = "rsi"               # liefert nur `in_r`; kursbasiert, breiteste Menge
MENGE = "20%"                 # die Auswahl der Kette (wie phase3_kette)
STOP_RELATIV = 0.08           # nur positiv noetig - gebuehrenfrei faellt er raus
ZIEL_QUOTE = 46.0 / 132.0     # Live-Durchlassquote, Sicherung 19.09. 12:09
CRV_LEITER = (1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0)
BEITRAEGE = ("funding", "turnover", "schnitt")
NULL_ZIEHUNGEN = messnorm.NULL_ZIEHUNGEN
VORBEHALT = ("gilt auf der Stellvertretermenge (N3 b); der CRV ist auf die "
             "Live-Durchlassquote KALIBRIERT, nicht gemessen")


def fuenftel_je_tag(reihen: dict) -> dict:
    """tag -> {sym: {funding_fuenftel, turnover_fuenftel, schnitt_fuenftel}}.

    ⚠️ MIT DEN ECHTEN FUNKTIONEN: `marktrang._rang` und
    `marktrang._fuenftel`. Beide sind rein rechnend - `raenge()` selbst
    waere ein Netzaufruf und wuerde ueber `api_health` in die Datenbank
    schreiben (stehende Vorgabe)."""
    aus: dict = {}
    for art in BEITRAEGE:
        je = R.K.baue(reihen, art, R._zusatz(art), horizont=R.HORIZONT)
        for tag, zeilen in je.items():
            if tag < AB:
                continue
            werte = {z["sym"]: float(z["kennzahl"]) for z in zeilen
                     if np.isfinite(z["kennzahl"])}
            rang = MR._rang(werte)
            ziel = aus.setdefault(tag, {})
            for sym, r in rang.items():
                ziel.setdefault(sym, {})[art + "_fuenftel"] = MR._fuenftel(r)
    return aus


def masken(je_tag: dict, mom: dict, fuenftel: dict, crv: float) -> dict:
    """tag -> (y, erreicht, durch). EINMAL je CRV, dann wiederverwendet.

    ⚠️ Der teure Teil ist `potential.rechne` je Anker. Die Nullwelten und
    die Positivkontrolle brauchen ihn NICHT noch einmal - sie arbeiten auf
    denselben Masken."""
    anteil = MENGEN[MENGE]
    aus = {}
    for tag, zeilen in je_tag.items():
        if tag < AB or len(zeilen) < MIND_ANKER:
            continue
        y = np.array([x["in_r"] for x in zeilen], float)
        ok = np.isfinite(y)
        if ok.sum() < MIND_ANKER:
            continue
        zeilen = [z for z, g in zip(zeilen, ok) if g]
        y = y[ok]
        mt = mom.get(tag) or {}
        m = A._auswahl_maske(zeilen, mt, anteil, None)
        if m is None or m.sum() < MIND_ANKER:
            continue
        ft = fuenftel.get(tag) or {}
        durch = np.zeros(len(zeilen), bool)
        # ⚠️⚠️ `bewertbar` WIRD MITGEFUEHRT, UND ZWAR ALS KONTROLLE.
        # `traegt_hier` setzt `bewertbar` voraus, und bewertbar ist nur,
        # wer ueberhaupt ein Merkmal hat - also wer an einer Terminboerse
        # gelistet ist. Eine Nullwelt, die aus ALLEN Erreichenden zieht,
        # misst deshalb zwei Dinge auf einmal: die BEWERTUNG und die
        # DATENLAGE. Genau diese Verwechslung hat am 04.09. schon einmal
        # eine Kalibrierung erzeugt, die ein Verfuegbarkeitsartefakt war.
        bewertbar = np.zeros(len(zeilen), bool)
        for i in np.flatnonzero(m):
            merk = {k: v for k, v in (ft.get(zeilen[i]["sym"]) or {}).items()
                    if v is not None}
            try:
                p = PT.rechne(crv=crv, stop_relativ=STOP_RELATIV,
                              klasse="krypto", instrument="spot",
                              strategie="einstieg",
                              merkmale=merk or None)
            except Exception:                               # noqa: BLE001
                # ⚠️ KEINE ZAHL HEISST NICHT "TRAEGT NICHT" - dieselbe
                # Lesart wie in der Kette (rollen_lauf, Stufe 11).
                continue
            if p.bewertbar:
                bewertbar[i] = True
                if p.traegt_hier:
                    durch[i] = True
        if durch.sum() < 3 or durch.sum() == int(m.sum()):
            continue
        aus[tag] = (y, m, durch, bewertbar)
    return aus


def quote(mk: dict) -> float:
    """Anteil der Durchgelassenen an den Erreichenden - je Tag gemittelt."""
    q = [durch.sum() / max(int(m.sum()), 1)
         for _y, m, durch, _b in mk.values()]
    return float(np.mean(q)) if q else float("nan")


def wirkung(mk: dict, rng=None, pflanze: float = 0.0,
            aus_bewertbaren: bool = False) -> dict:
    """tag -> median(durchgelassen) minus median(erreichend), in R.

    `rng` macht daraus die NULLWELT: gleich viele werden durchgelassen,
    aber zufaellig gewaehlte.

    ⚠️⚠️ `aus_bewertbaren` IST DIE ENTSCHEIDENDE KONTROLLE. Zieht die
    Nullwelt aus ALLEN Erreichenden, misst der Vergleich zwei Dinge auf
    einmal - ob die BEWERTUNG trennt und ob BEWERTBAR besser ist als
    nicht bewertbar. Zieht sie nur aus den Bewertbaren, bleibt allein die
    Bewertung uebrig. Die Differenz beider ist der Datenlagenanteil."""
    aus = {}
    for tag, (y, m, durch, bew) in mk.items():
        idx = np.flatnonzero(m & bew) if aus_bewertbaren else np.flatnonzero(m)
        if len(idx) < int(durch.sum()):
            continue
        if rng is None:
            d = durch
        else:
            d = np.zeros(len(y), bool)
            d[rng.choice(idx, int(durch.sum()), replace=False)] = True
        y2 = y.copy()
        if pflanze:
            # ⚠️ IN DIE DURCHGELASSENEN: sie werden besser gemacht, die
            # Stufe also zu Recht gut. Die Durchgelassenen stecken in den
            # Erreichenden mit drin - wer dort pflanzt, hebt den Effekt
            # teilweise wieder auf (Lehre aus 2.476-positivkontrolle).
            y2[d] += pflanze
        aus[tag] = float(np.median(y2[d])) - float(np.median(y2[m]))
    return aus


def besetzung(mk: dict) -> tuple:
    """(Tage, durchgelassen je Tag, erreichend je Tag, kleinster Tag)."""
    d = [int(durch.sum()) for _y, _m, durch, _b in mk.values()]
    e = [int(m.sum()) for _y, m, _d, _b in mk.values()]
    b = [int((m & bew).sum()) for _y, m, _d, bew in mk.values()]
    return (len(d), float(np.mean(d)) if d else float("nan"),
            float(np.mean(e)) if e else float("nan"),
            int(np.min(d)) if d else 0,
            float(np.mean(b)) if b else float("nan"))


def main() -> int:
    t0 = time.time()
    print("=" * 112)
    print("PHASE 3 · PUNKT 3b - WAS TRAEGT DIE STUFE `entscheider`?")
    print("=" * 112)
    print("  " + messmenge.zeile())
    print("  " + messnorm.standardzeile().replace("\n", "\n  "))
    print("  Zielgroesse: median(DURCHGELASSEN) minus median(ERREICHEND) - "
          "POSITIV heisst, die Stufe laesst die besseren durch")
    print("  ⚠️ EINE Frage, EINE Zelle (Schritt 64 Punkt A steht aus)")
    print("  ⚠️ %s" % VORBEHALT)

    print("\n  Kursreihen und Fuenftel bauen ...")
    reihen = R.B.lade("krypto", "V1")
    mom = momentum250(reihen)
    je_tag = R.K.baue(reihen, TRAEGER, None, horizont=R.HORIZONT)
    ft = fuenftel_je_tag(reihen)
    print("  %d Reihen · %d Tage mit Fuenfteln (%.0f s)"
          % (len(reihen), len(ft), time.time() - t0))

    # ---- Der CRV wird auf die Live-Durchlassquote kalibriert -------------
    print("\n  KALIBRIERUNG des CRV auf die Live-Durchlassquote %.1f %%"
          % (100 * ZIEL_QUOTE))
    bester, mk, alle = None, None, {}
    for crv in CRV_LEITER:
        m_ = masken(je_tag, mom, ft, crv)
        q = quote(m_)
        alle[crv] = m_
        print("     CRV %.2f -> Durchlassquote %.1f %% (%d Tage)"
              % (crv, 100 * q, len(m_)), flush=True)
        if m_ and (bester is None or abs(q - ZIEL_QUOTE) < bester[1]):
            bester, mk = (crv, abs(q - ZIEL_QUOTE)), m_
    if not mk:
        print("  ⚠️ keine Maske gebaut - Abbruch")
        return 1
    crv = bester[0]
    print("     ➔ gewaehlt: CRV %.2f (Abstand %.1f Punkte)"
          % (crv, 100 * bester[1]))
    if bester[1] > 0.05:
        print("     ⚠️⚠️ DIE ZIELQUOTE WIRD NICHT ERREICHT - der gewaehlte "
              "Wert liegt am RAND")
        print("        der Leiter. Das Urteil darf deshalb nicht an EINEM "
              "CRV haengen; die")
        print("        Empfindlichkeit wird unten ueber die ganze Leiter "
              "ausgewiesen.")

    block = messnorm._block(R.HORIZONT)
    echt = wirkung(mk)
    print("\n  %-26s %9s %-22s %9s %5s   %s"
          % ("Stufe", "R", "Band", "Nullwelt", "Tage", "Urteil"))
    if len(echt) < 2 * block:
        print("     zu wenige Tage (%d, %d noetig)" % (len(echt), 2 * block))
        return 1
    nullwerte = []
    for i in range(NULL_ZIEHUNGEN):
        n = wirkung(mk, rng=np.random.default_rng(messnorm.SAAT + i))
        nb = band(n, block, zieh=300, saat=messnorm.SAAT + i)
        if nb:
            nullwerte.append(nb[0])
    oben = (float(np.percentile(nullwerte, messnorm.NULL_PERZENTIL))
            if nullwerte else float("nan"))
    ts = None
    for staerke in messnorm.STAERKEN:
        treffer = 0
        for i in range(messnorm.ZIEHUNGEN):
            pb = band(wirkung(mk, pflanze=staerke), block, zieh=300,
                      saat=messnorm.SAAT + 1000 + i)
            if pb and pb[1] > oben:
                treffer += 1
        if treffer >= max(3, (4 * messnorm.ZIEHUNGEN) // 5):
            ts = staerke
            break
    urteil("entscheider (CRV %.2f)" % crv, echt, nullwerte, block, ts)
    tage, md, me, mn, mb = besetzung(mk)
    print("     %-26s Besetzung je Tag: durchgelassen %.1f (kleinster %d) "
          "von %.1f (davon bewertbar %.1f) · Trennschaerfe %s · %s"
          % ("", md, mn, me, mb, ("%.2f R" % ts) if ts else "KEINE",
             blockpruefung(echt, block)))

    # ---- ⚠️⚠️ DIE DATENLAGEN-KONTROLLE ---------------------------------
    #
    # Dieselbe Messung, aber die Nullwelt zieht NUR aus den Bewertbaren.
    # Bleibt die Wirkung, trennt die BEWERTUNG. Faellt sie zusammen, war
    # der Effekt die DATENLAGE - wer ein Merkmal hat, ist an einer
    # Terminboerse gelistet, und das ist kein Beitrag, sondern eine
    # Eigenschaft des Symbols (Regel 4).
    print()
    print("  ⚠️⚠️ DATENLAGEN-KONTROLLE - die Nullwelt zieht nur aus den "
          "BEWERTBAREN")
    null_b = []
    for i in range(NULL_ZIEHUNGEN):
        n = wirkung(mk, rng=np.random.default_rng(messnorm.SAAT + i),
                    aus_bewertbaren=True)
        nb = band(n, block, zieh=300, saat=messnorm.SAAT + i)
        if nb:
            null_b.append(nb[0])
    oben_b = (float(np.percentile(null_b, messnorm.NULL_PERZENTIL))
              if null_b else float("nan"))
    nw_b = float(np.mean(null_b)) if null_b else float("nan")
    b0 = band(echt, block)
    traegt_b = bool(b0) and b0[1] > oben_b
    print("     Nullwelt aus ALLEN Erreichenden   %+.4f (oben %+.4f)"
          % (float(np.mean(nullwerte)), oben))
    print("     Nullwelt nur aus den BEWERTBAREN  %+.4f (oben %+.4f)"
          % (nw_b, oben_b))
    print("     gemessen                          %+.4f [%+.4f .. %+.4f]"
          % tuple(b0[:3]))
    print("     ➔ gegen die bewertbare Nullwelt: %s"
          % ("TRAEGT - die BEWERTUNG trennt"
             if traegt_b else
             "TRAEGT NICHT - der Effekt war die DATENLAGE, nicht die "
             "Bewertung"))
    print("     Davon Datenlagenanteil: %+.4f R (Abstand der beiden "
          "Nullwelten)" % (nw_b - float(np.mean(nullwerte))))

    # ---- ⚠️ EMPFINDLICHKEIT GEGEN DEN CRV -------------------------------
    #
    # Stehende Vorgabe: eine Pruefung auf EINEM Parameterwert ist keine.
    # Der CRV ist hier kalibriert, nicht gemessen - also muss das Urteil
    # ueber die ganze Leiter stehen, sonst haengt es am Kalibrierpunkt.
    # ⚠️ Das sind KEINE acht Hypothesen: die Frage bleibt eine, und
    # geprueft wird ihre Robustheit. Berichtet wird der SCHLECHTESTE Wert,
    # nicht der beste.
    print()
    print("  ⚠️ EMPFINDLICHKEIT GEGEN DEN CRV (gegen die BEWERTBARE "
          "Nullwelt, %d Werte)" % len(CRV_LEITER))
    traegt_alle, schlechtester = 0, None
    for c2 in CRV_LEITER:
        m2 = alle.get(c2) or {}
        if not m2:
            continue
        e2 = wirkung(m2)
        bb = band(e2, block)
        if not bb:
            continue
        nb2 = []
        for i in range(NULL_ZIEHUNGEN):
            n2 = wirkung(m2, rng=np.random.default_rng(messnorm.SAAT + i),
                         aus_bewertbaren=True)
            x = band(n2, block, zieh=300, saat=messnorm.SAAT + i)
            if x:
                nb2.append(x[0])
        if not nb2:
            continue
        o2 = float(np.percentile(nb2, messnorm.NULL_PERZENTIL))
        ok2 = bb[1] > o2
        traegt_alle += int(ok2)
        if schlechtester is None or (bb[1] - o2) < schlechtester[1]:
            schlechtester = (c2, bb[1] - o2)
        print("     CRV %.2f  %+.4f R [%+.4f .. %+.4f]  Nullgrenze %+.4f  %s"
              % (c2, bb[0], bb[1], bb[2], o2,
                 "TRAEGT" if ok2 else "traegt nicht"), flush=True)
    print("     ➔ %d von %d CRV-Werten tragen · schlechtester Abstand "
          "%+.4f R bei CRV %.2f"
          % (traegt_alle, len(CRV_LEITER), schlechtester[1],
             schlechtester[0]) if schlechtester else "     ➔ kein Wert")

    b = band(echt, block)
    if b and nullwerte and abs(b[1] - oben) < 0.005:
        print("\n  ⚠️ SAATPROBE - das Urteil liegt mit %.4f R an der Grenze"
              % abs(b[1] - oben))
        print("     %s" % stabilitaet(
            echt, lambda r, _m=mk: wirkung(_m, rng=r), block))
    else:
        print("\n  Saatprobe nicht noetig - Abstand Bandunterkante zu "
              "Nullgrenze %.4f R" % (abs(b[1] - oben) if b else float("nan")))

    print("\n  LESEART")
    print("     R          median(durchgelassen) minus median(erreichend).")
    print("                POSITIV = die Stufe laesst die besseren durch.")
    print("     Nullwelt   gleich viele durchgelassen, aber ZUFAELLIG")
    print("                (%d Ziehungen)." % NULL_ZIEHUNGEN)
    print("     ⚠️ Der CRV ist KALIBRIERT, nicht gemessen - historisch gibt")
    print("        es ihn nicht je Anker.")
    print("\n  ⚠️ %s" % VORBEHALT)
    print("  (%.0f s)" % (time.time() - t0))
    print("=" * 112)
    return 0


if __name__ == "__main__":
    sys.exit(main())
