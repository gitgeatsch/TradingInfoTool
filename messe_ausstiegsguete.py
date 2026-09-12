# -*- coding: utf-8 -*-
"""War der Verkauf richtig? - das Erfolgsmass, das der Ausstiegsseite fehlt.

⚠️⚠️ DER BEFUND, DER DIESES WERKZEUG AUSGELOEST HAT (2.401, 12.09.2026):

    412 GEMAILTE Ausstiege   ->  409 "nicht_anwendbar", 3 NULL.  Keiner.
    105 STUMME  Ausstiege    ->   72 offen, 23 take_profit, 9 stop_loss

Es ist genau verkehrt herum: die Empfehlungen, die HERAUSGEHEN, werden nicht
ausgewertet - die unterdrueckten schon. Der Grund ist keine Nachlaessigkeit,
sondern eine fehlende Kategorie: der Hauptarm kennt nur EINSTIEGS-Zustaende.
"einstieg_nie_erreicht" ist ueber einen Verkauf keine Aussage, also faellt
alles auf "nicht_anwendbar".

WAS HIER GEMESSEN WIRD - und was ausdruecklich NICHT:

    gemessen      Was hat der Kurs NACH der Empfehlung getan? Faellt er, war
                  der Verkauf richtig; steigt er, war er falsch.
    NICHT         ob der Nutzer verkauft hat. Das weiss das System nicht, und
                  eine Empfehlung wird an ihrer Aussage gemessen, nicht an
                  ihrer Befolgung.

⚠️ DIE TAGESKLAMMER IST PFLICHT, nicht Kuer (stehende Vorgabe). Wenn der ganze
Markt an einem Tag faellt, ist ein Verkauf an diesem Tag kein Verdienst,
sondern Glueck. Deshalb wird gegen den MEDIAN aller an diesem Tag bewerteten
Werte gerechnet - nicht gegen null.

    guete = -(bewegung_asset - bewegung_median_des_tages)

    positiv   der Wert fiel STAERKER als der Markt      -> Verkauf hat getragen
    null      er fiel wie alle                          -> kein Beitrag
    negativ   er stieg staerker                         -> Verkauf war falsch

⚠️⚠️ WAS DIESES WERKZEUG NICHT KANN, und es steht hier, damit niemand mehr
hineinliest: der Kurs zum Zeitpunkt der Empfehlung ist NICHT festgehalten
(`entry_eur_von` steht nur bei den 105 stummen). Gerechnet wird deshalb mit
dem TAGESSCHLUSS des Empfehlungstages. Bei Krypto sind das einige Prozent
Unschaerfe gegen den Kurs um 14:30. Fuer einen Horizont von fuenf bis zehn
Tagen tragbar, fuer einen Tageshorizont nicht - deshalb beginnt die Tabelle
bei H3. Den exakten Referenzkurs mitzuschreiben gehoert in Schritt 43.

    python messe_ausstiegsguete.py [--db PFAD] [--tage 30]
"""
from __future__ import annotations

import argparse
import sqlite3
import statistics as st
import sys
from collections import defaultdict

# ⚠️ NICHT AUF MODULEBENE UMSTELLEN (gefunden von der eigenen Pruefung,
# 12.09.2026). `pruefe_pakete` ersetzt `sys.stdout` durch einen Mitschnitt,
# und der kennt `reconfigure` nicht - das Modul liess sich dort gar nicht
# erst importieren. Ein Messwerkzeug, das man nicht importieren kann, kann
# man auch nicht pruefen.
def _deutsch_ausgeben() -> None:
    """Umlaute auf die Konsole, ohne den Aufrufer zu stoeren."""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


# Die Horizonte. MEHRERE, weil die Horizont-Achse im Projekt offen ist und
# ein einzelner Wert eine Wahl verstecken wuerde, die niemand begruendet hat.
HORIZONTE = (3, 5, 10, 20)

AUSSTIEG = ("VERKAUFEN", "REDUZIEREN", "SCHLIESSEN", "TEILVERKAUF")


def _reihen(con, symbole) -> dict:
    """Je Symbol {datum: schlusskurs} - einmal geladen, nicht je Signal."""
    aus: dict = {}
    for s in symbole:
        r = {d: k for d, k in con.execute(
            "SELECT date, close FROM price_history_ohlc "
            "WHERE symbol=? AND close IS NOT NULL AND close > 0 "
            "ORDER BY date", (s,))}
        if len(r) > max(HORIZONTE):
            aus[s] = (r, sorted(r))
    return aus


def _bewegung(reihe, tage_sortiert, tag: str, h: int):
    """Relative Bewegung vom Tagesschluss `tag` bis `h` Handelstage spaeter.

    `None`, wenn der Tag nicht in der Reihe steht oder die Zukunft fehlt -
    ein fehlender Wert ist KEINE Null (das war Fehler N-40 in anderer Form)."""
    # DEN LETZTEN TAG NEHMEN, DER NICHT NACH `tag` LIEGT. Ein Wochenende oder
    # eine Datenluecke darf den Fall nicht verwerfen.
    i = None
    for j, d in enumerate(tage_sortiert):
        if d[:10] <= tag:
            i = j
        else:
            break
    if i is None or i + h >= len(tage_sortiert):
        return None
    a = reihe[tage_sortiert[i]]
    b = reihe[tage_sortiert[i + h]]
    if not a or a <= 0:
        return None
    return b / a - 1.0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="data/tradinginfotool.db")
    p.add_argument("--tage", type=int, default=45,
                   help="wie weit zurueck Empfehlungen gelesen werden")
    a = p.parse_args()
    _deutsch_ausgeben()

    con = sqlite3.connect(a.db)
    zeilen_db = list(con.execute(
        "SELECT id, symbol, date(created_at) AS tag, action, "
        "       COALESCE(ist_reines_llm_halten, 0) AS stumm "
        "  FROM signals "
        " WHERE quelle_kette='rollen' AND action IN (%s) "
        "   AND created_at >= date('now', ?) "
        " ORDER BY created_at" % ",".join("?" * len(AUSSTIEG)),
        (*AUSSTIEG, "-%d day" % a.tage)))
    print("=" * 78)
    print("GUETE DER AUSSTIEGSEMPFEHLUNGEN - %d Faelle der letzten %d Tage"
          % (len(zeilen_db), a.tage))
    print("=" * 78)
    if not zeilen_db:
        print("keine Ausstiegsempfehlungen im Zeitraum.")
        return 0

    reihen = _reihen(con, {z[1] for z in zeilen_db})
    print("Kursreihen vorhanden fuer %d von %d Symbolen"
          % (len(reihen), len({z[1] for z in zeilen_db})))

    # ---- DIE TAGESKLAMMER: was tat der Markt an diesem Tag? --------------
    #
    # ⚠️ GEBILDET UEBER DIE AN DIESEM TAG BEURTEILTEN WERTE, nicht ueber
    # einen Index. Der Vergleich muss dieselbe Menge treffen, aus der auch
    # ausgewaehlt wurde - sonst misst man die Assetklasse, nicht die Wahl.
    tage = sorted({z[2] for z in zeilen_db})
    markt: dict = {}
    for h in HORIZONTE:
        for tag in tage:
            werte = [b for s in reihen
                     for b in (_bewegung(reihen[s][0], reihen[s][1], tag, h),)
                     if b is not None]
            if len(werte) >= 5:
                markt[(tag, h)] = st.median(werte)

    # ---- die Guete je Fall ------------------------------------------------
    roh: dict = defaultdict(list)
    for _id, sym, tag, aktion, stumm in zeilen_db:
        if sym not in reihen:
            continue
        r, ts = reihen[sym]
        for h in HORIZONTE:
            b = _bewegung(r, ts, tag, h)
            m = markt.get((tag, h))
            if b is None or m is None:
                continue
            roh[(h, "stumm" if stumm else "gemailt")].append(-(b - m))
            roh[(h, "alle")].append(-(b - m))
            roh[(h, aktion)].append(-(b - m))

    def zeige(schluessel, name):
        print("\n%s" % name)
        print("  %-6s %6s %10s %10s %10s"
              % ("Horiz", "n", "Median", "Mittel", "Anteil >0"))
        for h in HORIZONTE:
            w = roh.get((h, schluessel)) or []
            if len(w) < 10:
                print("  H%-5d %6d   zu wenige Faelle" % (h, len(w)))
                continue
            pos = 100.0 * sum(1 for x in w if x > 0) / len(w)
            print("  H%-5d %6d %9.2f %% %9.2f %% %9.1f %%"
                  % (h, len(w), 100 * st.median(w), 100 * st.fmean(w), pos))

    zeige("alle", "ALLE AUSSTIEGE (Guete = wieviel der Wert SCHLECHTER lief "
                  "als der Markt)")
    zeige("gemailt", "⚠️ NUR DIE GEMAILTEN - die, die den Nutzer erreicht haben")
    zeige("stumm", "die STUMMEN (gestakt, ohne Mail) - der Gegenarm")
    for akt in ("REDUZIEREN", "VERKAUFEN"):
        if roh.get((HORIZONTE[0], akt)):
            zeige(akt, "nach Aktion: %s" % akt)

    # ---- DIE ZUFALLSKONTROLLE ------------------------------------------
    #
    # ⚠️⚠️ OHNE SIE IST DIE TABELLE OBEN EINE BEHAUPTUNG. Stehende Vorgabe:
    # "das LLM muss den Zufall schlagen, und das muss messbar sein". Und die
    # zweite: eine Zufallskontrolle faengt Kontamination - hier konkret die
    # Frage, ob die hohen Anteile bei VERKAUFEN aus dem URTEIL kommen oder
    # daher, dass an genau diesen Tagen fast alles fiel.
    #
    # DAS NULLMODELL: dieselbe ANZAHL Faelle an denselben TAGEN, aber ein
    # zufaellig gezogenes Symbol. Damit bleibt die Tagesverteilung erhalten
    # und nur die WAHL faellt weg - genau die Groesse, die zu pruefen ist.
    import random

    ZIEHUNGEN = 200
    rng = random.Random(20260912)
    alle_sym = sorted(reihen)
    print("")
    print("-" * 78)
    print("DIE ZUFALLSKONTROLLE - %d Ziehungen, gleiche Tage, zufaellige Wahl"
          % ZIEHUNGEN)
    print("  %-12s %-6s %10s %12s %10s"
          % ("Menge", "Horiz", "echt >0", "Zufall >0", "Abstand"))
    for schluessel, name in (("VERKAUFEN", "VERKAUFEN"),
                             ("REDUZIEREN", "REDUZIEREN"),
                             ("gemailt", "gemailt")):
        tage_fall = [z[2] for z in zeilen_db
                     if z[1] in reihen
                     and (z[3] == schluessel
                          or (schluessel == "gemailt" and not z[4]))]
        for h in HORIZONTE:
            echt = roh.get((h, schluessel)) or []
            if len(echt) < 20:
                continue
            anteile = []
            for _ in range(ZIEHUNGEN):
                w = []
                for tag in tage_fall:
                    s2 = rng.choice(alle_sym)
                    b = _bewegung(reihen[s2][0], reihen[s2][1], tag, h)
                    m = markt.get((tag, h))
                    if b is not None and m is not None:
                        w.append(-(b - m))
                if len(w) >= 10:
                    anteile.append(100.0 * sum(1 for x in w if x > 0) / len(w))
            if not anteile:
                continue
            e = 100.0 * sum(1 for x in echt if x > 0) / len(echt)
            z_med = st.median(anteile)
            z_hi = sorted(anteile)[min(int(0.95 * len(anteile)),
                                       len(anteile) - 1)]
            marke = "  <- schlaegt den Zufall" if e > z_hi else ""
            print("  %-12s H%-5d %8.1f %% %10.1f %% %9.1f %s"
                  % (name, h, e, z_med, e - z_med, marke))
    print("  (,schlaegt den Zufall' heisst: ueber dem 95. Perzentil der")
    print("   Ziehungen - eine Schranke, kein p-Wert)")

    print("\n" + "-" * 78)
    print("⚠️ WIE DAS ZU LESEN IST")
    print("   Median 0,00 %% heisst: der verkaufte Wert lief wie der Markt -")
    print("   die Empfehlung hat NICHTS getrennt. Ein Anteil >0 nahe 50 %% ist")
    print("   ein Muenzwurf. Erst deutlich darueber traegt die Auswahl.")
    print("⚠️⚠️ KEIN BEFUND NACH NORM: ohne Trennschaerfe, ohne Nullmodell aus")
    print("   Ziehungen, mit Tagesschluss statt Empfehlungskurs. Ein Hinweis,")
    print("   der sagt, ob sich die volle Messung lohnt - mehr nicht.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
