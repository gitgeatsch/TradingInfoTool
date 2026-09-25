# -*- coding: utf-8 -*-
"""H-A Nachpruefung: halten K4 und K5 dem Messstandard stand?

Nutzerauftrag 24.09.2026: *„ja aufsetzen und pruefen und gegenpruefen"*
Vorlauf: `messe_hebel_dimension.py` fand K4 und K5 auf ALLEN fuenf
Haltedauern ueber dem Nullpunkt, `KON zufall` blieb unten.

⚠️⚠️ DAS WAR EIN HINWEIS, KEIN BEFUND. Vier Dinge fehlten:

═══════════════════════════════════════════════════════════════════════
 1  DIE ENTFLECHTUNG - und sie steht zuerst, weil sie alles andere faerbt
═══════════════════════════════════════════════════════════════════════

    K5 = konten_verh
    K4 = top_konten_verh MINUS konten_verh

➤ BEIDE ENTHALTEN `konten_verh`. Sie sind rechnerisch verwandt, und zwei
Treffer aus einer Familie sind EIN Treffer, nicht zwei.

GEMESSEN WIRD BEDINGT: innerhalb jedes K5-Fuenftels nach K4 rangen - und
umgekehrt. Traegt K4 nur, solange K5 frei variiert, war es nie K4.

═══════════════════════════════════════════════════════════════════════
 2  MONOTONIE ueber ALLE Fuenftel (B5)
═══════════════════════════════════════════════════════════════════════

Gemessen wurde bisher nur Fuenftel 4 gegen den Rest. Ein Beitrag, dessen
Wirkung nicht mit dem Rang steigt, ist ein Zufallstreffer an einem Ende -
die Stufen waeren dann nicht ableitbar.

═══════════════════════════════════════════════════════════════════════
 3  BEIDE HISTORIENHAELFTEN (B6)
═══════════════════════════════════════════════════════════════════════

⚠️ Verschaerft durch 2.585 vom selben Tag: die Basisrate schwankt zwischen
10,7 und 60,7 Prozent und ist NICHT vorhersagbar. Ein Beitrag, der nur in
einer Haelfte traegt, koennte ein Regimeeffekt sein.

═══════════════════════════════════════════════════════════════════════
 4  TRENNSCHAERFE - gepflanzte Effekte
═══════════════════════════════════════════════════════════════════════

Der Messstandard verlangt: ab WELCHER Staerke findet die Anlage etwas?
Ohne diese Zahl ist ein „traegt nicht" nicht von „zu wenig gesehen" zu
unterscheiden - und ein „traegt" nicht einzuordnen.

Gepflanzt wird ZENTRIERT (die Leiter verschiebt den Gesamtmedian nicht),
Staerken bis 0,40 R, gegen den NULLPUNKT gemessen, nicht gegen null.

⚠️ AUF ZWEI HALTEDAUERN STATT FUENF: 6h (der kuerzeste Hebeltrade, wo die
Luecke am kleinsten ist) und 24h (die Mitte). Die Nullwelten kosten je
Zelle Minuten; fuenf Haltedauern mal vier Pruefungen waeren Stunden ohne
zusaetzliche Erkenntnis.

    python messe_hebel_nachpruefung.py
    python messe_hebel_nachpruefung.py --symbole 40
"""
from __future__ import annotations

import sys
from collections import defaultdict

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_hebel_dimension as HD                           # noqa: E402

HALTEDAUERN = (6, 24)
# ⚠️⚠️ F-212: DIE SELEKTIERTE MENGE - abgeleitet, nicht gewaehlt.
#
# `messnorm_auswahl.MENGEN` und `messe_beitrag_auf_auswahl.momentum250`
# definieren sie: der Top-Anteil nach der Entwicklung ueber 250 Tage, quer
# ueber die Symbole je Termin. Genau die Groesse, nach der die
# Auswahlstufe im Betrieb rangt (`auswahl.RUECKBLICK_TAGE = 250`).
#
# ⚠️ Bei k = 2 von 43 laesst die Kette heute rund 5 Prozent durch. H-A lief
# auf `frei` - das ist derselbe Fehler, der am 07.09. eine Live-Aenderung
# ausgeloest und am selben Tag zurueckgenommen hat (N-56/N-58).
#
# 250 Handelstage sind bei Krypto 250 Kalendertage, also 6.000 Stunden.
MENGEN = {"frei": 1.0, "50%": 0.50, "20%": 0.20, "5%": 0.05}
MOM_STUNDEN = 250 * 24
STAERKEN = (0.0, 0.02, 0.05, 0.10, 0.20, 0.40)   # Messstandard: bis 0,40
PRUEFEN = (("K4 top minus retail", "_top_minus", "niveau"),
           ("K5 konten_verh", "konten_verh", "niveau"))


def _momentum(kurse: dict) -> dict:
    """{stunde: {sym: Entwicklung ueber 250 Tage}} - die AUSWAHLgroesse.

    ⚠️ Nachbau von `messe_beitrag_auf_auswahl.momentum250` auf
    Stundenaufloesung. Nachlaufend, kein Blick nach vorn.
    """
    aus: dict = {}
    for sym, rows in kurse.items():
        st = [r[0] for r in rows]
        cl = np.array([r[3] for r in rows], float)
        for i in range(MOM_STUNDEN, len(cl)):
            if cl[i - MOM_STUNDEN] > 0:
                aus.setdefault(st[i], {})[sym] = float(
                    cl[i] / cl[i - MOM_STUNDEN] - 1.0)
    return aus


def _waehle(samml: dict, mom: dict, anteil: float) -> dict:
    """Nur die besten `anteil` je Stunde - die SELEKTIERTE Menge (F-212).

    ⚠️ Die Auswahl greift NACH der Fuenftelbildung, genau wie in
    `messe_beitrag_auf_auswahl.sammle`. Wer vorher filtert, rangt ueber
    eine andere Grundgesamtheit - und das dreht gemessen das Vorzeichen.

    ⚠️ Die Rueckgabe ist IMMER ein 2-Tupel (fuenftel, ergebnis) - auch bei
    `frei`. Die Symbolspalte wird nur zum AUSWAEHLEN gebraucht; sie dann
    weiterzureichen hiesse, jede Messfunktion daran anzupassen, und genau
    dieser Bruch ist mir beim Einbauen schon einmal passiert.
    """
    if anteil >= 1.0:
        return {s: (f, y) for s, (f, y, _syms) in samml.items()}
    aus = {}
    for stunde, (f, y, syms) in samml.items():
        m_st = mom.get(stunde) or {}
        da = [i for i, s in enumerate(syms) if s in m_st]
        if len(da) < 8:
            continue
        k = max(1, int(round(len(da) * anteil)))
        best = sorted(da, key=lambda i: -m_st[syms[i]])[:k]
        if len(best) >= 4:
            aus[stunde] = (f[np.array(best)], y[np.array(best)])
    return aus


def _sammle(kurse, tm, h, feld, art, rng):
    """{stunde: (fuenftel, ergebnis_r)} plus die Rohwerte je Stunde."""
    anker, roh = {}, {}
    for sym, rows in kurse.items():
        st = [r[0] for r in rows]
        hi = np.array([r[1] for r in rows], float)
        lo = np.array([r[2] for r in rows], float)
        cl = np.array([r[3] for r in rows], float)
        atr = HD._atr(st, hi, lo, cl)
        if atr is None:
            continue
        idx = np.arange(0, len(cl) - h, HD.TAKT)
        idx = idx[np.isfinite(atr[idx]) & (atr[idx] > 0)]
        if not len(idx):
            continue
        e, _z, _s, _o, _u = HD._barrieren(hi, lo, cl, atr, idx, h, False)
        for k, j in enumerate(idx):
            w = HD._merkmal(tm.get(sym) or {}, st[j], art, feld)
            if w is None or not np.isfinite(w):
                continue
            anker.setdefault(st[j], []).append((sym, float(e[k])))
            roh.setdefault(st[j], {})[sym] = w
    f5 = HD._fuenftel_je_stunde(roh)
    aus = {}
    for stunde, liste in anker.items():
        zu = f5.get(stunde)
        if not zu:
            continue
        p = [(zu[s], y, s) for s, y in liste if s in zu]
        if len(p) >= 4:
            aus[stunde] = (np.array([x[0] for x in p]),
                           np.array([x[1] for x in p], float),
                           [x[2] for x in p])
    return aus, roh, anker


def _bedingt(anker, roh_a, roh_b):
    """Fuenftel von A INNERHALB der Fuenftel von B - die Entflechtung.

    ⚠️ Gerangt wird A nur gegen Symbole mit demselben B-Fuenftel. Bleibt
    die Wirkung, ist sie A zuzuschreiben; verschwindet sie, war es B.
    """
    f_a = HD._fuenftel_je_stunde(roh_a)
    f_b = HD._fuenftel_je_stunde(roh_b)
    aus = {}
    for stunde, liste in anker.items():
        za, zb = f_a.get(stunde), f_b.get(stunde)
        if not za or not zb:
            continue
        # je B-Schicht die A-Werte neu rangen
        schicht = defaultdict(list)
        for s, y in liste:
            if s in za and s in zb:
                schicht[zb[s]].append((s, za[s], y))
        paare = []
        for _b, gruppe in schicht.items():
            if len(gruppe) < 5:
                continue
            gruppe.sort(key=lambda x: x[1])
            n = len(gruppe) - 1
            for i, (_s, _a, y) in enumerate(gruppe):
                paare.append((min(int((i / n) * 5), 4), y))
        if len(paare) >= 4:
            aus[stunde] = (np.array([p[0] for p in paare]),
                           np.array([p[1] for p in paare], float))
    return aus


def _neutral(samml, rng):
    """Die Fuenftelzuordnung je Stunde MISCHEN - eine Welt ohne Effekt.

    ⚠️⚠️ OHNE DIESEN SCHRITT IST DIE TRENNSCHAERFE WERTLOS, und genau das
    war mein Fehler im ersten Lauf: gepflanzt wurde in die ECHTEN Daten,
    die den K5-Effekt bereits enthalten. Bei gepflanzter Staerke NULL
    meldete die Anlage deshalb +0,0072 und "gefunden" - gemessen wurde
    Effekt PLUS Pflanzung, nicht die Pflanzung.

    Gemischt wird INNERHALB der Stunde: die Marktbewegung bleibt, nur die
    Zuordnung faellt weg. Dieselbe Neutralisierung wie im Nullpunkt.
    """
    return {stunde: (rng.permutation(f), y) for stunde, (f, y) in samml.items()}


def _pflanze(samml, staerke, rng):
    """Zentrierte Leiter: Fuenftel 0..4 bekommen -2s..+2s in Schritten.

    ⚠️ ZENTRIERT, damit der Gesamtmedian sich NICHT verschiebt - sonst
    misst man die Verschiebung statt der Trennung (Messstandard).
    """
    aus = {}
    for stunde, (f, y) in samml.items():
        zuschlag = (f.astype(float) - 2.0) * (staerke / 2.0)
        aus[stunde] = (f, y + zuschlag)
    return aus


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])
    rng = np.random.default_rng(HD.SAAT)

    print("=" * 100)
    print("H-A NACHPRUEFUNG - halten K4 und K5 dem Messstandard stand?")
    print("=" * 100)
    kurse = HD._lade_kurse(grenze)
    tm = HD._lade_terminmarkt(set(kurse))
    print("  %d Symbole · %d mit Merkmalen · Haltedauern %s"
          % (len(kurse), len(tm), HALTEDAUERN), flush=True)

    print("  Momentum 250 Tage rechnen (die AUSWAHLgroesse, F-212)...",
          flush=True)
    mom = _momentum(kurse)
    print("    %d Stunden mit Momentum" % len(mom), flush=True)

    daten, frei = {}, {}
    for h in HALTEDAUERN:
        for name, feld, art in PRUEFEN:
            daten[(h, feld)] = _sammle(kurse, tm, h, feld, art, rng)
            frei[(h, feld)] = _waehle(daten[(h, feld)][0], mom, 1.0)
            print("    %s / %dh: %d Stunden"
                  % (name, h, len(frei[(h, feld)])), flush=True)

    # ───────────────────── 1 DIE ENTFLECHTUNG ──────────────────────────
    print()
    print("=" * 100)
    print("1 - DIE ENTFLECHTUNG: sind K4 und K5 ZWEI Funde oder EINER?")
    print("=" * 100)
    for h in HALTEDAUERN:
        _s4, roh4, anker4 = daten[(h, "_top_minus")]
        _s5, roh5, _a5 = daten[(h, "konten_verh")]
        s4, s5 = frei[(h, "_top_minus")], frei[(h, "konten_verh")]
        # Korrelation der Rohwerte ueber gemeinsame (Stunde, Symbol)
        a, b = [], []
        for stunde, je in roh4.items():
            je5 = roh5.get(stunde) or {}
            for sym, w in je.items():
                if sym in je5:
                    a.append(w); b.append(je5[sym])
        r = float(np.corrcoef(a, b)[0, 1]) if len(a) > 100 else float("nan")
        print()
        print("  %dh · %s gemeinsame Punkte · Rohwert-Korrelation r = %+.4f"
              % (h, f"{len(a):,}".replace(",", "."), r))
        w4, _n = HD._wirkung(s4, 4)
        w5, _n = HD._wirkung(s5, 4)
        b4 = _bedingt(anker4, roh4, roh5)      # K4 innerhalb K5-Schichten
        b5 = _bedingt(anker4, roh5, roh4)      # K5 innerhalb K4-Schichten
        print("  Schichten gebildet: K4|K5 %d Stunden · K5|K4 %d Stunden"
              % (len(b4), len(b5)))
        wb4, nb4 = HD._wirkung(b4, 4)
        wb5, nb5 = HD._wirkung(b5, 4)
        n4 = HD._nullpunkt(b4, 4, rng) if nb4 else np.array([])
        n5 = HD._nullpunkt(b5, 4, rng) if nb5 else np.array([])
        print("  %-34s %10s %12s %10s" % ("", "frei", "BEDINGT", "Nullpunkt"))
        for nm, wf, wb, nu, nb in (("K4 (top minus retail)", w4, wb4, n4, nb4),
                                   ("K5 (konten_verh)", w5, wb5, n5, nb5)):
            # ⚠️ NICHT MESSBAR IST NICHT GEFALLEN. Die Doppelsortierung
            # braucht je Schicht mindestens 5 Symbole - bei 5 Schichten also
            # 25 im Querschnitt. Darunter entsteht keine Schicht, und ein
            # `nan` als "faellt bedingt" auszugeben waere die Sorte stiller
            # Fehlschluss, die dieses Projekt schon zweimal gekostet hat.
            if not nb or not np.isfinite(wb) or not len(nu):
                print("  %-34s %+10.4f %12s %10s   ⚠️ NICHT MESSBAR "
                      "(zu wenige Symbole je Schicht)" % (nm, wf, "-", "-"))
                continue
            p90 = float(np.percentile(nu, 90))
            urteil = "TRAEGT auch bedingt" if wb > p90 else "FAELLT bedingt"
            print("  %-34s %+10.4f %+12.4f %+10.4f   %s"
                  % (nm, wf, wb, p90, urteil))

    # ───────────────────── 2 DIE MONOTONIE ─────────────────────────────
    print()
    print("=" * 100)
    print("2 - MONOTONIE (B5): steigt die Wirkung mit dem Rang?")
    print("=" * 100)
    for h in HALTEDAUERN:
        for name, feld, _art in PRUEFEN:
            samml = frei[(h, feld)]
            zeile, werte = [], []
            for f in range(5):
                w, _n = HD._wirkung(samml, f)
                werte.append(w)
                zeile.append("%+8.4f" % w if np.isfinite(w) else "       -")
            gut = [x for x in werte if np.isfinite(x)]
            mono = (len(gut) == 5 and all(gut[i] <= gut[i + 1]
                                          for i in range(4)))
            # ⚠️ Auch die UMGEKEHRTE Monotonie zaehlt - ein Beitrag darf
            # fallen, solange er es durchgehend tut.
            mono_ab = (len(gut) == 5 and all(gut[i] >= gut[i + 1]
                                             for i in range(4)))
            print("  %-24s %2dh  %s   %s"
                  % (name, h, " ".join(zeile),
                     "MONOTON steigend" if mono else
                     "MONOTON fallend" if mono_ab else "⚠️ NICHT monoton"))

    # ───────────────────── 3 BEIDE HAELFTEN ────────────────────────────
    print()
    print("=" * 100)
    print("3 - BEIDE HISTORIENHAELFTEN (B6)")
    print("=" * 100)
    for h in HALTEDAUERN:
        for name, feld, _art in PRUEFEN:
            samml = frei[(h, feld)]
            st = sorted(samml)
            mitte = len(st) // 2
            for txt, teil in (("1. Haelfte", {k: samml[k] for k in st[:mitte]}),
                              ("2. Haelfte", {k: samml[k] for k in st[mitte:]})):
                w, ns = HD._wirkung(teil, 4)
                nu = HD._nullpunkt(teil, 4, rng)
                p90 = float(np.percentile(nu, 90)) if len(nu) else float("nan")
                print("  %-24s %2dh  %-11s %+8.4f gegen %+8.4f   %s  (%s bis %s)"
                      % (name, h, txt, w, p90,
                         "TRAEGT" if np.isfinite(w) and w > p90 else "traegt nicht",
                         st[0][:10] if txt.startswith("1") else st[mitte][:10],
                         st[mitte - 1][:10] if txt.startswith("1") else st[-1][:10]))

    # ───────────────────── 4 DIE TRENNSCHAERFE ─────────────────────────
    print()
    print("=" * 100)
    print("4 - TRENNSCHAERFE: ab welcher Staerke findet die Anlage etwas?")
    print("=" * 100)
    print("  ⚠️ Zentriert gepflanzt - der Gesamtmedian verschiebt sich NICHT.")
    for h in HALTEDAUERN:
        samml = frei[(h, "konten_verh")]
        nu = HD._nullpunkt(samml, 4, rng)
        p90 = float(np.percentile(nu, 90)) if len(nu) else float("nan")
        print()
        print("  %dh · Nullpunkt %+.4f · 90. Perzentil %+.4f"
              % (h, float(nu.mean()) if len(nu) else float("nan"), p90))
        print("  ⚠️ Gepflanzt wird in eine NEUTRALISIERTE Menge (Fuenftel")
        print("     gemischt) - sonst misst man Effekt PLUS Pflanzung.")
        print("  %10s %12s %10s %12s"
              % ("gepflanzt", "gemessen", "gefunden?", "Fundquote"))
        gefunden_ab = None
        for st in STAERKEN:
            # ⚠️ MEHRERE ZIEHUNGEN je Staerke - eine einzelne Neutralisierung
            # ist selbst eine Zufallsziehung. Die Fundquote sagt, wie
            # VERLAESSLICH gefunden wird, nicht nur ob einmal.
            treffer, werte = 0, []
            for _ in range(20):
                w, _n = HD._wirkung(_pflanze(_neutral(samml, rng), st, rng), 4)
                if np.isfinite(w):
                    werte.append(w)
                    if w > p90:
                        treffer += 1
            if not werte:
                continue
            quote = treffer / len(werte)
            if gefunden_ab is None and quote >= 0.8 and st > 0:
                gefunden_ab = st
            print("  %10.2f %+12.4f %10s %11.0f %%"
                  % (st, float(np.mean(werte)),
                     "JA" if quote >= 0.8 else "nein", 100 * quote))
        print("  ➤ zuverlaessig gefunden (80 %%) ab: %s"
              % ("%.2f R" % gefunden_ab if gefunden_ab else "keiner der Werte"))
    print()
    print("  ⚠️ Die kleinste Staerke mit JA ist die AUFLOESUNG der Anlage.")
    print("     Ein `traegt nicht` unterhalb davon heisst NICHT ,kein Effekt`,")
    print("     sondern ,zu wenig gesehen`.")

    # ───────────────── 5 DIE SELEKTIERTE MENGE (F-212) ─────────────────
    print()
    print("=" * 100)
    print("5 - DIE SELEKTIERTE MENGE (F-212): traegt K5 auch dort, wo die")
    print("    Kette tatsaechlich hinschaut?")
    print("=" * 100)
    print("  ⚠️ H-A lief auf `frei`. Die Auswahlstufe laesst bei k=2 von 43")
    print("     rund 5 Prozent durch - gerangt nach momentum250.")
    for h in HALTEDAUERN:
        print()
        print("  %dh · %-10s %10s %12s %10s %9s"
              % (h, "Menge", "Wirkung", "Nullpunkt", "Urteil", "Stunden"))
        for name, anteil in MENGEN.items():
            samml = _waehle(daten[(h, "konten_verh")][0], mom, anteil)
            if len(samml) < 30:
                print("     %-10s %10s %12s %10s %9d"
                      % (name, "-", "-", "zu duenn", len(samml)))
                continue
            w, ns = HD._wirkung(samml, 4)
            nu = HD._nullpunkt(samml, 4, rng)
            if not np.isfinite(w) or not len(nu):
                print("     %-10s %10s %12s %10s %9d"
                      % (name, "-", "-", "kein Nullpkt", len(samml)))
                continue
            p90 = float(np.percentile(nu, 90))
            print("     %-10s %+10.4f %+12.4f %10s %9d"
                  % (name, w, p90, "TRAEGT" if w > p90 else "traegt nicht", ns))
    print()
    print("  ⚠️⚠️ ENTSCHEIDEND IST DIE ZEILE, DIE DER BETRIEB SIEHT.")
    print("     Traegt K5 nur auf `frei`, gilt der Befund fuer eine Menge,")
    print("     die es im Betrieb nicht gibt - genau der Fehler N-56/N-58")
    print("     vom 07.09., der am selben Tag zurueckgenommen wurde.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
