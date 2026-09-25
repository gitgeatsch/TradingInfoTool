# -*- coding: utf-8 -*-
"""Warum nur 18 Symbole je Termin? Messstandard oder fehlende Daten?

**Nutzerfrage 25.09.2026:** *"pruefe warum nur 18 Symbole ist das
Messstandard oder nur fehlende Daten"*

Befund 2.592 hat gezeigt: die Nachweisgrenze auf `barriere` ist Arithmetik.
Die Streuung der TAGESspannen liegt bei rund 0,25, und sie sinkt mit der
Wurzel der Symbole JE TERMIN. Damit ist die Symbolzahl je Termin die
einzige Groesse, die die Grenze wirklich senkt - und die Frage, WO sie
verloren geht, ist die entscheidende.

═══════════════════════════════════════════════════════════════════════
 DIE ZWEI MOEGLICHKEITEN, und sie fuehren zu VERSCHIEDENEN Massnahmen
═══════════════════════════════════════════════════════════════════════

    FEHLENDE DATEN     die Quelle hat je Termin nur so viele Symbole
                       ➤ Massnahme: mehr abrufen (Abdeckung)

    MESSSTANDARD       die Quelle hat mehr, die Filterkette wirft sie weg
                       ➤ Massnahme: die Filter pruefen

⚠️ Der Trichter weist JEDE Stufe einzeln aus, damit die Antwort nicht
geraten werden muss. Eine Stufe, die nichts wegnimmt, ist unschuldig.

⚠️ NUR LESEN.

    python pruefe_symbole_je_termin.py
"""
from __future__ import annotations

import os
import sqlite3
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messe_eigenschaft_beitrag as B                          # noqa: E402
import messnorm_auswahl as MA                                  # noqa: E402

MIND_JE_TAG = 12          # die Besetzung, auf die die Messungen filtern
FENSTER = 90              # messe_funding_niveau.baue
VORLAUF = 60              # dito
HORIZONT = 3


def _perz(x):
    if not len(x):
        return "-"
    a = np.array(sorted(x), float)
    return ("Median %5.1f · 10./90. Perz %5.1f / %5.1f · Max %4.0f"
            % (np.median(a), np.percentile(a, 10), np.percentile(a, 90),
               a.max()))


def stufe(nam, je_termin, vorher=None):
    """Eine Trichterstufe ausgeben. `je_termin` = {termin: Symbolzahl}."""
    werte = [v for v in je_termin.values() if v > 0]
    txt = "   %-46s %6d Termine · %s" % (nam, len(werte), _perz(werte))
    if vorher is not None:
        v0 = [v for v in vorher.values() if v > 0]
        if v0 and werte:
            d = np.median(werte) - np.median(v0)
            txt += "   %+.1f" % d
    print(txt)
    return je_termin


def funding_trichter(reihen):
    print()
    print("=" * 100)
    print("A) FUNDING, TAEGLICH - der Trichter der Beitragsmessung")
    print("=" * 100)
    c = sqlite3.connect("file:data/funding_historie.db?mode=ro", uri=True)
    roh = {}
    for s, t, w in c.execute("SELECT symbol, datum, wert FROM funding"):
        roh.setdefault(str(s).upper(), {})[str(t)[:10]] = float(w)
    c.close()
    print("   Quelle: %d Symbole, %d Werte"
          % (len(roh), sum(len(v) for v in roh.values())))

    # 1) rohe Besetzung je Tag
    s1 = {}
    for sym, d in roh.items():
        for t in d:
            s1[t] = s1.get(t, 0) + 1
    stufe("1 Quelle: Symbole mit funding-Wert je Tag", s1)

    # 2) nur Symbole, fuer die es eine KURSREIHE gibt
    hat_kurs = {k.upper() for k in reihen}
    s2 = {}
    for sym, d in roh.items():
        if sym not in hat_kurs:
            continue
        for t in d:
            s2[t] = s2.get(t, 0) + 1
    stufe("2 + eine Kursreihe vorhanden (B.lade)", s2, s1)

    # 3) Mindestlaenge der funding-Historie je Symbol (baue: >= 120)
    s3 = {}
    for sym, d in roh.items():
        if sym not in hat_kurs or len(d) < FENSTER + 30:
            continue
        for t in d:
            s3[t] = s3.get(t, 0) + 1
    stufe("3 + funding-Historie >= %d Tage je Symbol" % (FENSTER + 30),
          s3, s2)

    # 4) Vorlauf und Horizont je Symbol wegschneiden, Tage der Kursreihe
    s4 = {}
    for sym, reihe in reihen.items():
        d = roh.get(sym.upper())
        if not d or len(d) < FENSTER + 30:
            continue
        tage = [z[0] for z in reihe]
        sortiert = sorted(d)
        lage = {t: i for i, t in enumerate(sortiert)}
        for i in range(VORLAUF, len(tage) - HORIZONT):
            t = tage[i]
            if t not in lage or lage[t] < FENSTER:
                continue
            s4[t] = s4.get(t, 0) + 1
    stufe("4 + Kursvorlauf %d, Horizont %d, funding-Fenster %d"
          % (VORLAUF, HORIZONT, FENSTER), s4, s3)

    # 5) die Mindestbesetzung
    s5 = {t: v for t, v in s4.items() if v >= MIND_JE_TAG}
    stufe("5 + Mindestbesetzung >= %d je Tag" % MIND_JE_TAG, s5, s4)
    print("     ➤ %d von %d Tagen fallen hier weg (%.1f %%)"
          % (len(s4) - len(s5), len(s4),
             100.0 * (len(s4) - len(s5)) / max(1, len(s4))))

    # 6) Fuenftel brauchen je >= 2 Werte -> mindestens 10
    s6 = {t: v for t, v in s5.items() if v >= 10}
    stufe("6 + fuenf Fuenftel mit je >= 2 Werten (>= 10)", s6, s5)
    return s4


def terminmarkt_trichter(reihen, spalte="konten_verh"):
    print()
    print("=" * 100)
    print("B) TERMINMARKT, STUENDLICH - `%s` (der 18-Symbol-Befund 2.587)"
          % spalte)
    print("=" * 100)
    p = "data/terminmarkt_historie.db"
    if not os.path.exists(p):
        print("   ⛔ %s fehlt" % p)
        return
    c = sqlite3.connect("file:%s?mode=ro" % p, uri=True)
    marke = [r[0] for r in c.execute(
        "select name from sqlite_master where type='table' "
        "and name like '\\_%' escape '\\'")]
    if marke:
        print("   ⚠️⚠️ MARKERTABELLE(N) %s - das ist KEINE volle Messbasis, "
              "sondern eine Betriebs-/Symbolliste (CLAUDE.md). Die Zahlen "
              "unten gelten dann nur fuer diese Datei." % marke)
    ges, sym_ges = c.execute(
        "select count(*), count(distinct symbol) from terminmarkt").fetchone()
    nn = c.execute("select count(*) from terminmarkt where %s is not null"
                   % spalte).fetchone()[0]
    print("   Quelle: %d Zeilen, %d Symbole · davon %s nicht null: %d "
          "(%.1f %%)" % (ges, sym_ges, spalte, nn, 100.0 * nn / max(1, ges)))

    s1 = {}
    for st, n in c.execute(
            "select stunde, count(distinct symbol) from terminmarkt "
            "where %s is not null group by stunde" % spalte):
        s1[str(st)] = int(n)
    stufe("1 Quelle: Symbole mit `%s` je Stunde" % spalte, s1)

    hat_kurs = {k.upper() for k in reihen}
    s2 = {}
    for st, sy in c.execute(
            "select stunde, symbol from terminmarkt where %s is not null"
            % spalte):
        if str(sy).upper() in hat_kurs:
            s2[str(st)] = s2.get(str(st), 0) + 1
    stufe("2 + eine Kursreihe vorhanden", s2, s1)
    c.close()

    s3 = {t: v for t, v in s2.items() if v >= MIND_JE_TAG}
    stufe("3 + Mindestbesetzung >= %d je Stunde" % MIND_JE_TAG, s3, s2)
    print("     ➤ %d von %d Stunden fallen hier weg (%.1f %%)"
          % (len(s2) - len(s3), len(s2),
             100.0 * (len(s2) - len(s3)) / max(1, len(s2))))

    # ⭐ Die Frage nach der ZEIT: waechst die Abdeckung?
    print()
    print("   ⭐ Entwicklung der Abdeckung je Jahr (Stufe 2):")
    je_jahr = {}
    for st, v in s2.items():
        je_jahr.setdefault(st[:4], []).append(v)
    for j in sorted(je_jahr):
        a = np.array(je_jahr[j], float)
        print("      %-6s %6d Stunden · Median %5.1f · Max %4.0f"
              % (j, len(a), np.median(a), a.max()))


def main() -> int:
    print("=" * 100)
    print("WARUM NUR 18 SYMBOLE JE TERMIN?  MESSSTANDARD ODER FEHLENDE DATEN")
    print("=" * 100)
    print("  Nutzerfrage 25.09.2026 · nur lesend")
    print("  ⚠️ MIND_ANKER aus messnorm_auswahl: %d · hier gefilterte "
          "Besetzung: %d" % (MA.MIND_ANKER, MIND_JE_TAG))

    reihen = B.lade()
    print("  Kursreihen (B.lade): %d Symbole" % len(reihen))

    s_fund = funding_trichter(reihen)
    terminmarkt_trichter(reihen)

    print()
    print("=" * 100)
    print("DIE ANTWORT")
    print("=" * 100)
    werte = [v for v in s_fund.values() if v > 0]
    if werte:
        print("  funding, vor jeder Mindestbesetzung: Median %.1f Symbole "
              "je Tag" % float(np.median(werte)))
    print("  ➤ Liegt der Median schon in Stufe 1 bis 4 niedrig, sind es")
    print("    FEHLENDE DATEN. Bricht er erst in Stufe 5 oder 6 ein, ist")
    print("    es der MESSSTANDARD.")
    print()
    print("  ⚠️ Die Streuung sinkt mit der WURZEL: von 18 auf 72 Symbole")
    print("     je Termin halbiert sie - das ist der Faktor, den 2.592 als")
    print("     Bedingung fuer einen Nachweis von 0,01 in q genannt hat.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
