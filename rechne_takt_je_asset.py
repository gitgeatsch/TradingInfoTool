# -*- coding: utf-8 -*-
"""Der REALE TAKT: welches Asset bekommt wie oft welche Empfehlung?
(02.09.2026)

## Warum nicht die Kettensimulation

`simuliere_kette.py` laeuft mit Attrappen gegen eine Kopie und liefert ein
bis zwei Signale - sie beweist, dass eine Stufe WIRKT, nicht wie oft sie
greift. Der Takt steht nur in der Produktion.

Grundlage ist deshalb das **Notebook-Backup vom 29.08.2026**: 2.789
Signale der Rollen-Kette ueber 15 Tage (14.08. bis 29.08.), read-only
geoeffnet.

⚠️ **DIESER BESTAND IST VOR G-6.** Die verwerfende Stufe 11 kam am 31.08.,
N-14 am 02.09. Der gemessene Takt ist also der Zustand OHNE beide - und
genau deshalb laesst sich an ihm rechnen, was sie wegnehmen wuerden.

## Was eine Mail ausloest (`verkaufsrechnung.py`)

    Einstieg    KAUFEN, NACHKAUFEN, EROEFFNEN      -> Mail
    Ausstieg    REDUZIEREN, VERKAUFEN, SCHLIESSEN  -> Mail
    Nichts      HALTEN, NICHTS_TUN                 -> KEINE Mail

## ⚠️ Worauf die Sperren ueberhaupt greifen

N-14 sperrt nur `einstieg` und nur OHNE Bestand. In der Historie heisst
das:

    EROEFFNEN, KAUFEN     kein Bestand  -> die Sperre greift
    NACHKAUFEN            Bestand       -> ausgenommen
    REDUZIEREN, VERKAUFEN Ausstieg      -> ausgenommen
    HALTEN                              -> erzeugt ohnehin keine Mail

**Das ist der Kern der Rechnung**: die Sperren treffen einen kleineren
Teil des Takts, als ihr Sperranteil von 20 % vermuten laesst.

    python rechne_takt_je_asset.py --db <pfad-zum-backup>
"""
import argparse
import collections
import sqlite3
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EINSTIEG = {"KAUFEN", "NACHKAUFEN", "ERÖFFNEN", "EROEFFNEN"}
AUSSTIEG = {"REDUZIEREN", "VERKAUFEN", "SCHLIESSEN"}
OHNE_BESTAND = {"ERÖFFNEN", "EROEFFNEN", "KAUFEN"}


def lade_signale(db):
    c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    aus = []
    for sym, tag, akt, strat, heb in c.execute(
            "SELECT symbol, substr(created_at,1,10), action, strategie, hebel "
            "FROM signals WHERE quelle_kette='rollen' AND action IS NOT NULL"):
        aus.append({"sym": str(sym).upper(), "tag": tag,
                    "aktion": str(akt).upper().strip(),
                    "strategie": strat, "hebel": heb})
    c.close()
    return aus


def raenge_je_tag(werte_je_tag):
    """{tag: {symbol: Fuenftel 0..4}} - Querschnitt wie in der Produktion."""
    aus = {}
    for tag, w in werte_je_tag.items():
        if len(w) < 15:
            continue
        syms = sorted(w)
        v = np.array([w[s] for s in syms], float)
        r = np.argsort(np.argsort(v)) / max(len(v) - 1, 1)
        aus[tag] = {s: min(int(x * 5), 4) for s, x in zip(syms, r)}
    return aus


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", required=True)
    a = p.parse_args()

    sig = lade_signale(a.db)
    tage = sorted({s["tag"] for s in sig})
    n_tage = len(tage)
    print("=" * 92)
    print("DER REALE TAKT — Notebook-Produktion %s bis %s (%d Tage)"
          % (tage[0], tage[-1], n_tage))
    print("=" * 92)
    print("  %d Signale der Rollen-Kette, %d Assets"
          % (len(sig), len({s["sym"] for s in sig})))
    print()

    # ---- 1: Ist-Zustand -------------------------------------------------
    je_aktion = collections.Counter(s["aktion"] for s in sig)
    mails = [s for s in sig if s["aktion"] in EINSTIEG | AUSSTIEG]
    print("  Aktion          gesamt   je Tag   Mail?")
    for akt, n in je_aktion.most_common():
        art = ("Mail" if akt in EINSTIEG | AUSSTIEG else "keine Mail")
        print("  %-14s %6d   %6.1f   %s" % (akt, n, n / n_tage, art))
    print("  %-14s %6d   %6.1f" % ("-> MAILS", len(mails), len(mails) / n_tage))
    print()
    print("  ⚠️ Das ist der Zustand VOR G-6 (31.08.) und VOR N-14 (02.09.).")

    # ---- 2: die Sperren rueckwirkend ------------------------------------
    import messe_kandidaten_als_regel as K
    import messe_volumenanteil as V
    import messe_eigenschaft_beitrag as B

    print()
    print("  Lade die beiden Sperrgroessen fuer denselben Zeitraum...",
          flush=True)
    reihen = B.lade()
    tm = K.lade_terminmarkt()["oi_aenderung"]
    oi_roh = {}
    for sym, je in tm.items():
        for tag, wert in je.items():
            if wert is not None:
                oi_roh.setdefault(tag, {})[sym.upper()] = float(wert)
    oi_f = raenge_je_tag(oi_roh)
    va_roh = V.anteile_relativ(V.anteile(reihen))
    va_f = raenge_je_tag({t: {s.upper(): v for s, v in w.items()}
                          for t, w in va_roh.items()})

    abgedeckt_oi = sum(1 for s in sig if (oi_f.get(s["tag"]) or {}).get(s["sym"]) is not None)
    abgedeckt_va = sum(1 for s in sig if (va_f.get(s["tag"]) or {}).get(s["sym"]) is not None)
    print("  Abdeckung der Signale: OI %d von %d (%.0f %%) · "
          "Volumenanteil %d (%.0f %%)"
          % (abgedeckt_oi, len(sig), 100 * abgedeckt_oi / len(sig),
             abgedeckt_va, 100 * abgedeckt_va / len(sig)))

    def gesperrt(s, welche):
        """Greift die Sperre auf DIESES Signal?"""
        if s["aktion"] not in OHNE_BESTAND:
            return False          # NACHKAUFEN/Ausstieg/HALTEN: ausgenommen
        f = (welche.get(s["tag"]) or {}).get(s["sym"])
        return f is not None and f >= 4

    w_oi = [s for s in sig if gesperrt(s, oi_f)]
    w_va = [s for s in sig if gesperrt(s, va_f)]
    w_beide = [s for s in sig if gesperrt(s, oi_f) or gesperrt(s, va_f)]
    ein_ob = [s for s in sig if s["aktion"] in OHNE_BESTAND]

    print()
    print("=" * 92)
    print("WORAUF DIE SPERREN GREIFEN")
    print("=" * 92)
    print("  Signale insgesamt                       %5d  (%.1f/Tag)"
          % (len(sig), len(sig) / n_tage))
    print("  davon Einstieg OHNE Bestand             %5d  (%.1f/Tag)  "
          "<- nur hier greifen die Sperren"
          % (len(ein_ob), len(ein_ob) / n_tage))
    print()
    print("  N-14 (OI) sperrt davon                  %5d  (%.1f/Tag)"
          % (len(w_oi), len(w_oi) / n_tage))
    print("  N-13-1' (Volumenanteil) sperrt davon    %5d  (%.1f/Tag)"
          % (len(w_va), len(w_va) / n_tage))
    print("  BEIDE zusammen                          %5d  (%.1f/Tag)"
          % (len(w_beide), len(w_beide) / n_tage))
    print()
    print("  -> Mails vorher                         %5d  (%.1f/Tag)"
          % (len(mails), len(mails) / n_tage))
    m2 = [s for s in mails if s not in w_beide]
    print("  -> Mails nach beiden Sperren            %5d  (%.1f/Tag)  "
          "= -%.1f %%" % (len(m2), len(m2) / n_tage,
                          100 * (1 - len(m2) / max(len(mails), 1))))

    # ---- 3: je Asset ----------------------------------------------------
    print()
    print("=" * 92)
    print("JE ASSET — wie oft welche Empfehlung, auf 30 Tage hochgerechnet")
    print("=" * 92)
    je_sym = collections.defaultdict(collections.Counter)
    for s in sig:
        je_sym[s["sym"]][s["aktion"]] += 1
    nach = collections.defaultdict(collections.Counter)
    for s in sig:
        if s not in w_beide:
            nach[s["sym"]][s["aktion"]] += 1
    f30 = 30.0 / n_tage
    print("  %-9s %6s %6s %6s %6s %6s %6s | %7s %7s"
          % ("Asset", "EROEFF", "NACHK", "KAUF", "REDUZ", "VERK", "HALT",
             "Mails", "danach"))
    reihenfolge = sorted(je_sym, key=lambda s: -sum(je_sym[s].values()))
    for sym in reihenfolge:
        c_ = je_sym[sym]
        m_vor = sum(v for k, v in c_.items() if k in EINSTIEG | AUSSTIEG)
        m_nach = sum(v for k, v in nach[sym].items() if k in EINSTIEG | AUSSTIEG)
        print("  %-9s %6.1f %6.1f %6.1f %6.1f %6.1f %6.1f | %7.1f %7.1f"
              % (sym,
                 (c_.get("ERÖFFNEN", 0) + c_.get("EROEFFNEN", 0)) * f30,
                 c_.get("NACHKAUFEN", 0) * f30, c_.get("KAUFEN", 0) * f30,
                 c_.get("REDUZIEREN", 0) * f30, c_.get("VERKAUFEN", 0) * f30,
                 c_.get("HALTEN", 0) * f30, m_vor * f30, m_nach * f30))
    print()
    print("  ⚠️ Alle Zahlen sind auf 30 Tage hochgerechnet (gemessen: %d Tage)."
          % n_tage)


if __name__ == "__main__":
    main()
