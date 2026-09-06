# -*- coding: utf-8 -*-
# ⛔⛔ UEBERHOLT AM 06.09.2026 — NICHT MEHR BENUTZEN
#
# Dieses Werkzeug misst auf der ZIELGROESSE "Ziel vor Stop" und/oder auf der
# FREIEN statt der SELEKTIERTEN Menge. Beides ist als falsch nachgewiesen:
#
#   Zielgroesse  `Konzept_Bewertungsstufe_29_08.md` Abschnitt 1, seit 23.08.:
#                "Wer 'Ziel vor Stop' misst, misst die eigene Zielregel
#                zurueck. Nicht der Markt war leer - das Mass war blind."
#
#   Menge        F-212 vom 04.09.: die Beitraege wirken auf 1,5 % der Anker.
#                Auf der selektierten Menge traegt funding DREIMAL staerker;
#                auf der freien liegt es bei -0,0003 R, also bei null.
#
# ⚠️ DIE RECHNUNGEN SIND KORREKT. Sie beantworten eine Frage, die laut
# eigener Dokumentation nichts ueber das Potential sagt. Wer sie erneut
# laufen laesst, bekommt wieder plausible Zahlen - und wieder die falschen.
#
# ERSATZ: `messnorm.py` (Methodik 2.110). Sie erzwingt Zielgroesse, Menge,
# Klammer, Kosten, Bootstrap und BEIDE Kontrollen - und lehnt sechs bekannte
# Irrwege ab, statt sie zu dokumentieren.
#
# Aufgehoben statt geloescht, weil die Herleitungen in den Docstrings die
# Fehler beschreiben, die dabei gefunden wurden (F-217 bis F-231).
#
"""N-52: Asset-Anteil und Relativform — mit den ETABLIERTEN Werkzeugen (06.09.2026)

## ⚠️ Der Anlass ist ein eigener Fehler

Nutzerhinweis 06.09.: *„du kannst auch in unseren zentralen Mess- und
Regelwerksdokumenten nachsehen."* `Test_und_Verifikationsmethodik.md` fuehrt
137 nummerierte Eintraege allein in Kapitel 2 — und ich habe am 05./06.09.
**zwei davon neu erfunden**, beide schlechter als das Vorhandene:

| ich baute | was seit 02.09. dasteht |
|---|---|
| Persistenz als Behelfsmass | **2.101** Asset-Anteil aus der Rangvarianz, GEEICHT mit Positiv- (95,9 %) und Negativkontrolle (0,1 %) |
| Differenz ueber 20 Tage | **2.101** Verhaeltnis zum eigenen gleitenden Median — senkte den Asset-Anteil von 69,8 % auf **1,4 %** |
| Schichtentest nur Richtung C | **2.99** verlangt C UND D — *„die Gegenrichtung, immer mit"* |

Dieses Skript benutzt die vorhandenen Funktionen aus
`messe_volumenanteil.py` — `zerlege()` und `anteile_relativ()` — statt sie
ein drittes Mal zu bauen.

## Was gemessen wird

    1  ASSET-ANTEIL   je Groesse und Form, mit beiden Kontrollen auf
                      DERSELBEN Menge (2.101: "beide Arme auf derselben
                      Menge" - der Anteil haengt an der Symbolzahl)

    2  RELATIVFORM    wert(i,t) / Median(wert(i, t-20 .. t-1))
                      -> die dokumentierte Form gegen die eigene Gewohnheit,
                         nicht meine Differenz

    3  SCHICHTENTEST  BEIDE Richtungen:
                      C  Kandidat | Niveau festgehalten
                      D  Niveau   | Kandidat festgehalten

## Die Leseart nach 2.99

    C traegt              eigener Beitrag
    C faellt, D traegt    Mitlaeufer - es war die bekannte Groesse
    beide tragen          zwei Beitraege -> R-R9
    beide fallen          die gemeinsame Ursache liegt woanders

⚠️ Und der Preis, den 2.99 selbst nennt: *„Ein Nullbefund im Schichtentest
ist schwaecher als einer in der rohen Messung — er kann Aufloesungsmangel
sein."* Die Zellenbesetzung wird deshalb ausgewiesen.

    python messe_asset_anteil_und_relativform.py
"""
from __future__ import annotations

import sys

from binascii import crc32

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                       # noqa: E402
import messe_funding_niveau as F                            # noqa: E402
import messe_kandidaten_als_regel as K                      # noqa: E402
import messe_zielregel as ZR                                # noqa: E402
from messe_bewertung_kalibrierung import _fuenftel_je_tag   # noqa: E402
# ⚠️ DIE ETABLIERTEN WERKZEUGE (2.101) - importiert, nicht nachgebaut.
from messe_volumenanteil import zerlege, anteile_relativ    # noqa: E402
from messe_fuenftel_mit_tagesklammer import (               # noqa: E402
    je_tag_und_fuenftel, abweichung_je_fuenftel, _spanne)
from pruefe_persistenz_und_nullpunkt import (               # noqa: E402
    persistenz, kunst_fuenftel)
from pruefe_veraenderungsformen_unabhaengig import bedingt  # noqa: E402

ARTEN = ("amihud", "schnitt50", "vola", "funding")
ZIEHUNGEN = 5
FENSTER = 20


def relativ_je_art(je_tag: dict, art: str) -> tuple[dict, str]:
    """Die Form gegen die eigene Gewohnheit - je nach VORZEICHEN.

    ⚠️ GEPRUEFT, NICHT UEBERNOMMEN (06.09.). `anteile_relativ` aus
    `messe_volumenanteil` teilt durch den eigenen gleitenden Median. Das
    ist fuer ANTEILE richtig - sie sind immer positiv. Gemessen:

        amihud      0,0 % negativ   Median 13,98      -> Quotient taugt
        vola        0,0 % negativ   Median  0,766     -> Quotient taugt
        schnitt50  62,0 % negativ   Median -0,0496    -> Quotient UNSINN
        schnitt    69,7 % negativ   Median -0,178     -> Quotient UNSINN
        funding    22,9 % negativ   Median  0,000276  -> Quotient explodiert

    Bei Vorzeichenwechseln dreht der Quotient die Ordnung, und bei einem
    Median nahe null waechst er unbegrenzt. Fuer diese Groessen nimmt das
    Projekt anderswo bereits den **MAD-Abstand** (`funding_extrem`:
    *"Abstand vom eigenen Normalzustand in MAD"*) - der ist gegen
    Vorzeichen und Nulldurchgang unempfindlich.
    """
    werte = [v for d in je_tag.values() for v in d.values()]
    neg = sum(1 for v in werte if v < 0) / max(len(werte), 1)
    if neg < 0.01:
        return anteile_relativ(je_tag, fenster=FENSTER), "Quotient"
    # MAD-Abstand, nachlaufend
    tage = sorted(je_tag)
    verlauf, aus = {}, {}
    for tag in tage:
        heute = {}
        for s, v in je_tag[tag].items():
            vor = verlauf.get(s) or []
            if len(vor) >= FENSTER:
                x = np.array(vor[-FENSTER:], float)
                m = float(np.median(x))
                mad = float(np.median(np.abs(x - m)))
                if mad > 1e-12:
                    heute[s] = (v - m) / mad
        if len(heute) >= 15:
            aus[tag] = heute
        for s, v in je_tag[tag].items():
            verlauf.setdefault(s, []).append(v)
    return aus, "MAD"


def je_tag_werte(gebaut: dict) -> dict:
    """{tag: {sym: kennzahl}} - die Form, die `zerlege` und
    `anteile_relativ` erwarten."""
    return {t: {e["sym"]: float(e["kennzahl"]) for e in liste
                if e.get("kennzahl") is not None}
            for t, liste in gebaut.items()}


def _spanne_von(zeilen, tage_je_sym, f5) -> float:
    tg, _n, _f = abweichung_je_fuenftel(
        je_tag_und_fuenftel(zeilen, tage_je_sym, f5))
    return _spanne(tg)


def _als_gebaut(je_tag: dict) -> dict:
    """zurueck in die Listenform, die `_fuenftel_je_tag` erwartet."""
    return {t: [{"sym": s, "kennzahl": v} for s, v in d.items()]
            for t, d in je_tag.items()}


def main() -> int:
    print("Lade Reihen...", flush=True)
    reihen = B.lade()
    tage_je_sym = {s: [z[0] for z in roh] for s, roh in reihen.items()}
    zeilen = ZR.ergebnisse(reihen)
    print("  %d Anker · %d Reihen" % (len(zeilen), len(reihen)), flush=True)
    print("  lade funding ...", flush=True)
    quelle = {"funding": F.lade_funding()}

    gebaut = {}
    for art in ARTEN:
        print("  baue %s ..." % art, flush=True)
        gebaut[art] = K.baue(reihen, art, quelle.get(art), horizont=20)

    # ---- 1. Asset-Anteil, mit beiden Kontrollen -----------------------
    print()
    print("=" * 100)
    print("1. ASSET-ANTEIL (Methodik 2.101) — geeicht mit beiden Kontrollen")
    print("=" * 100)
    print("  %-26s %10s %11s %11s %s"
          % ("", "Asset-%", "Autokorr 1", "Autokorr 20", "Symbole"))
    for art in ARTEN:
        jt = je_tag_werte(gebaut[art])
        zerlege(jt, "%s NIVEAU" % art)
        rel, wie = relativ_je_art(jt, art)
        if rel:
            zerlege(rel, "%s RELATIV (%s)" % (art, wie))
    # ⚠️ Beide Kontrollen auf DERSELBEN Menge wie amihud - 2.101 warnt
    # ausdruecklich, dass der Anteil an der Symbolzahl haengt.
    basis = je_tag_werte(gebaut["amihud"])
    rng = np.random.default_rng(20260906)
    # ⚠️ crc32 STATT hash() - hash() ist fuer Zeichenketten prozessweise
    # zufaellig. Derselbe Fehler war heute frueh schon in `baue_gruppen`
    # (F-218); er wiederholt sich, sobald man nicht hinsieht.
    fest_wert = {}
    for t, d in basis.items():
        for s in d:
            if s not in fest_wert:
                fest_wert[s] = float(np.random.default_rng(
                    crc32(s.encode())).random())
    fest = {t: {s: fest_wert[s] for s in d} for t, d in basis.items()}
    zuf = {t: {s: float(rng.random()) for s in d} for t, d in basis.items()}
    zerlege(fest, "KONTROLLE fest je Symbol")
    zerlege(zuf, "KONTROLLE reiner Zufall")

    # ---- 2. Wirkung der Relativform ----------------------------------
    print()
    print("=" * 100)
    print("2. WIRKUNG — traegt die RELATIVFORM auf der Barriere?")
    print("=" * 100)
    print("  %-26s %7s %7s %7s %s"
          % ("", "Spanne", "Pers.", "Null", "Verhaeltnis"))
    formen = {}
    for art in ARTEN:
        jt = je_tag_werte(gebaut[art])
        rel, wie = relativ_je_art(jt, art)
        for name, g in (("%s NIVEAU" % art, gebaut[art]),
                        ("%s RELATIV" % art, _als_gebaut(rel) if rel else None)):
            if not g:
                continue
            f5 = _fuenftel_je_tag(g)
            if not f5:
                continue
            formen[name] = f5
            p = persistenz(f5, tage_je_sym)
            sp = _spanne_von(zeilen, tage_je_sym, f5)
            # Nullpunkt auf DERSELBEN Struktur, Blocklaenge nach Persistenz
            block = 1 if p < 0.5 else (5 if p < 0.9 else (20 if p < 0.97 else None))
            w = []
            for z in range(ZIEHUNGEN):
                w.append(_spanne_von(zeilen, tage_je_sym,
                                     kunst_fuenftel(g, block, salz=z)))
            null = float(np.max([x for x in w if x == x])) if w else float("nan")
            print("  %-26s %7.2f %6.1f%% %7.2f %6.1fx%s"
                  % (name, sp, 100 * p, null,
                     sp / null if null > 0 else float("nan"),
                     "" if null > 0 and sp / null > 2.5 else "  <- traegt nicht"))

    # ---- 3. Schichtentest, BEIDE Richtungen --------------------------
    print()
    print("=" * 100)
    print("3. SCHICHTENTEST (Methodik 2.99) — BEIDE Richtungen")
    print("=" * 100)
    for art in ARTEN:
        a, b = "%s RELATIV" % art, "%s NIVEAU" % art
        if a not in formen or b not in formen:
            continue
        print("  %s" % art.upper())
        for ziel, bed, marke in ((a, b, "C  Relativ | Niveau"),
                                 (b, a, "D  Niveau  | Relativ")):
            werte, nulls, zellen = [], [], []
            for g in range(5):
                fz = bedingt(formen[ziel], formen[bed], g)
                if len(fz) < 200:
                    continue
                zellen.append(len(fz))
                werte.append(_spanne_von(zeilen, tage_je_sym, fz))
                kk = []
                for z in range(ZIEHUNGEN):
                    kb = bedingt(kunst_fuenftel(gebaut[art], 5, salz=z),
                                 formen[bed], g)
                    if len(kb) >= 200:
                        kk.append(_spanne_von(zeilen, tage_je_sym, kb))
                if kk:
                    nulls.append(float(np.max(kk)))
            if werte and nulls:
                m, n0 = float(np.mean(werte)), float(np.mean(nulls))
                print("    %-22s Spanne %5.2f · Null %5.2f · %4.1fx"
                      "  (Zellen: %s Tage)"
                      % (marke, m, n0, m / n0 if n0 > 0 else float("nan"),
                         "/".join(str(x) for x in zellen)))
            else:
                print("    %-22s nicht messbar" % marke)
        print()

    print("  ⚠️ LESEART nach 2.99")
    print("     C traegt            eigener Beitrag")
    print("     C faellt, D traegt  Mitlaeufer - es war das Niveau")
    print("     beide tragen        zwei Beitraege -> R-R9")
    print("     beide fallen        die Ursache liegt woanders")
    print()
    print("  ⚠️ 2.99 selbst: ein Nullbefund im Schichtentest ist SCHWAECHER")
    print("     als einer in der rohen Messung - er kann Aufloesungsmangel")
    print("     sein. Deshalb steht die Zellenbesetzung daneben.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
