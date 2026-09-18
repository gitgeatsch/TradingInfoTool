# -*- coding: utf-8 -*-
"""Live-Zählung der Kette (Schritt 59 Phase 2, 18.09.2026).

⚠️⚠️ DAS IST EINE ZAEHLUNG, KEIN URTEIL. Frageart `zaehlung` nach der
Messnorm: *"Wieviele/wie oft? (deskriptiv, kein Urteil)"* - verlangt wird
genau eines: SAGEN, WORUEBER gezaehlt wird. Kein Band, keine Trennschaerfe,
keine Schwelle, kein Nullmodell.

⚠️ WARUM DER VORBEHALT AN JEDER ZAHL STEHT UND NICHT IN EINER FUSSNOTE:
in diesem Projekt sind Quotentabellen schon zweimal als Befund gelesen
worden. Eine Zahl, die man ohne ihren Vorbehalt zitieren kann, wird ohne
ihren Vorbehalt zitiert.

⚠️ ZWEI SCHICHTUNGEN SIND PFLICHT (Nutzerentscheidung D2, 18.09.):

  PROMPT-STAND. 3.431 Zeilen stammen aus `2026-08-17e`, 266 aus dem heute
  laufenden `2026-09-11a`. Eine gemeinsame Quote mischt zwei Modelle
  (Regler_Signal_Pipeline_Abhaengigkeiten Z. 202-204).

  DIE LINIE 01.09. Seither sieht Rolle BC dieselben Terminmarktdaten wie
  Rolle G (2.457-w1). Eine gemeinsame G-Zahl mischt die unabhaengige mit
  der abhaengigen Gegenpruefung.

⚠️ KRYPTO UND NICHT-KRYPTO IMMER GETRENNT (D3): fuer Nicht-Krypto gibt es
keine Messbasis; in einer gemeinsamen Quote verschwindet genau das.

NUR LESEND (`mode=ro`) - am Notebook ist die Datei die Produktion.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys

# ⚠️ Die Linie, an der Rolle G ihre Unabhaengigkeit verloren hat (2.457-w1).
LINIE_G = "2026-09-01"
ENTSCHIEDEN = ("take_profit_erreicht", "stop_loss_erreicht")
VORBEHALT = "HINWEIS, kein Urteil (Frageart zaehlung - kein Band, keine Schwelle)"


def _verbindung(pfad: str) -> sqlite3.Connection:
    con = sqlite3.connect("file:%s?mode=ro" % pfad, uri=True)
    con.row_factory = sqlite3.Row
    return con


def _kopf(titel: str, menge: str) -> None:
    print("\n" + "=" * 100)
    print(titel)
    print("=" * 100)
    print("  Menge:    %s" % menge)
    print("  ⚠️        %s" % VORBEHALT)


def _quote(treffer: int, gesamt: int) -> str:
    """Anteil in Prozent - oder ein Strich, wenn die Menge zu klein ist.

    ⚠️ KEINE QUOTE UNTER ZEHN FAELLEN. Nicht als Schwelle (die waere ein
    Urteil), sondern weil `1 von 2 = 50 %` eine Genauigkeit vortaeuscht, die
    die Menge nicht hergibt."""
    if gesamt < 10:
        return "  -  "
    return "%4.0f %%" % (100.0 * treffer / gesamt)


def trichter(con: sqlite3.Connection) -> None:
    _kopf("1  DER TRICHTER - wo die Kette Zellen verliert, und woran",
          "Zeilen aus `zellen_lauf` (seit 18.09.2026, Phase 1 Paket 1.1); "
          "die Stufen davor stehen je Lauf in `gate_durchlaessigkeit`")
    try:
        zeilen = con.execute(
            "SELECT COALESCE(gruppe,'?') g, stufe, ergebnis, COUNT(*) n "
            "FROM zellen_lauf GROUP BY 1,2,3 ORDER BY n DESC").fetchall()
    except sqlite3.OperationalError:
        print("  (Tabelle `zellen_lauf` fehlt - Pull und Neustart am Notebook?)")
        return
    if not zeilen:
        print("  (noch keine Zeilen)")
        return
    for bereich, prueft in (("KRYPTO", lambda g: g == "krypto"),
                            ("NICHT-KRYPTO", lambda g: g != "krypto")):
        teil = [z for z in zeilen if prueft(z["g"])]
        print("\n  --- %s ---" % bereich)
        if not teil:
            print("     (keine Zeilen)")
            continue
        print("     %-9s %-14s %-10s %6s" % ("Gruppe", "Stufe", "Ergebnis", "Anzahl"))
        for z in teil[:14]:
            print("     %-9s %-14s %-10s %6d"
                  % (z["g"], z["stufe"], z["ergebnis"], z["n"]))


def vierfeld(con: sqlite3.Connection) -> None:
    _kopf("2  DAS VIERFELD - durchgelassen gegen verworfen, je mit Ausgang",
          "Zeilen der Rollen-Kette mit ENTSCHIEDENEM Ausgang (Ziel oder Stop "
          "erreicht); je Prompt-Stand getrennt, weil zwei Staende zwei "
          "Modelle sind")
    print("     %-14s %-10s %5s %5s %7s   %s"
          % ("prompt_stand", "Zeitraum", "Ziel", "Stop", "Anteil", "Zeilen"))
    for gate, name in ((1, "durchgelassen"), (0, "verworfen")):
        print("\n  --- %s (gate_passed=%d) ---" % (name, gate))
        for z in con.execute(
                "SELECT COALESCE(prompt_stand,'?') p, "
                "       MIN(date(created_at)) a, MAX(date(created_at)) b, "
                "       SUM(outcome_status='take_profit_erreicht') tp, "
                "       SUM(outcome_status='stop_loss_erreicht') sl, "
                "       COUNT(*) n "
                "  FROM signals "
                " WHERE quelle_kette='rollen' AND gate_passed=? "
                "   AND outcome_status IN (?,?) "
                " GROUP BY 1 ORDER BY n DESC", (gate, *ENTSCHIEDEN)):
            print("     %-14s %-10s %5d %5d %7s   %d"
                  % (z["p"], "%s..%s" % (z["a"][5:], z["b"][5:]), z["tp"],
                     z["sl"], _quote(z["tp"], z["tp"] + z["sl"]), z["n"]))


def modellurteil(con: sqlite3.Connection) -> None:
    _kopf("3  WAS ROLLE BC EMPFIEHLT - und was daraus wurde",
          "Zeilen der Rollen-Kette mit entschiedenem Ausgang, je Aktion und "
          "Prompt-Stand")
    print("     %-14s %-12s %5s %5s %7s" % ("prompt_stand", "Aktion", "Ziel", "Stop", "Anteil"))
    for z in con.execute(
            "SELECT COALESCE(prompt_stand,'?') p, action, "
            "       SUM(outcome_status='take_profit_erreicht') tp, "
            "       SUM(outcome_status='stop_loss_erreicht') sl "
            "  FROM signals WHERE quelle_kette='rollen' "
            "   AND outcome_status IN (?,?) "
            " GROUP BY 1,2 ORDER BY (tp+sl) DESC LIMIT 12", ENTSCHIEDEN):
        print("     %-14s %-12s %5d %5d %7s"
              % (z["p"], z["action"], z["tp"], z["sl"],
                 _quote(z["tp"], z["tp"] + z["sl"])))


def gegenpruefung(con: sqlite3.Connection) -> None:
    _kopf("4  ROLLE G - Einwand gegen Folge",
          "Zeilen mit Urteil von Rolle G und entschiedenem Ausgang. ⚠️ "
          "GETRENNT an der Linie %s: seither sieht BC dieselben "
          "Terminmarktdaten wie G (2.457-w1), die Gegenpruefung ist ab dann "
          "NICHT mehr unabhaengig" % LINIE_G)
    print("     %-22s %-14s %5s %5s %7s"
          % ("Zeitraum", "G-Urteil", "Ziel", "Stop", "Anteil"))
    for a, b, name in (("0000-00-00", LINIE_G, "vor %s (unabhaengig)" % LINIE_G),
                       (LINIE_G, "9999-99-99", "ab %s (NICHT unabh.)" % LINIE_G)):
        for z in con.execute(
                "SELECT zai_gegenpruefung_urteil u, "
                "       SUM(outcome_status='take_profit_erreicht') tp, "
                "       SUM(outcome_status='stop_loss_erreicht') sl "
                "  FROM signals WHERE quelle_kette='rollen' "
                "   AND zai_gegenpruefung_urteil IS NOT NULL "
                "   AND date(created_at) >= ? AND date(created_at) < ? "
                "   AND outcome_status IN (?,?) "
                " GROUP BY 1 ORDER BY (tp+sl) DESC", (a, b, *ENTSCHIEDEN)):
            print("     %-22s %-14s %5d %5d %7s"
                  % (name, z["u"], z["tp"], z["sl"],
                     _quote(z["tp"], z["tp"] + z["sl"])))


def fuehrung(con: sqlite3.Connection) -> None:
    _kopf("5  DIE FUEHRUNG - Stop-Nachziehen",
          "Zeilen aus `fuehrung_lauf` (seit 18.09.2026, Phase 1 Paket 1.4): "
          "Empfehlungen UND gepruefte Positionen ohne Empfehlung")
    try:
        zeilen = con.execute(
            "SELECT date(erfasst_am) tag, art, COUNT(*) n, "
            "       ROUND(AVG(sichert_r),3) s FROM fuehrung_lauf "
            "GROUP BY 1,2 ORDER BY 1 DESC, 2 LIMIT 14").fetchall()
    except sqlite3.OperationalError:
        print("  (Tabelle `fuehrung_lauf` fehlt - der Ausstiegs-Job laeuft "
              "frueh morgens; vorher entsteht sie nicht)")
        return
    if not zeilen:
        print("  (noch keine Zeilen)")
        return
    print("     %-12s %-12s %6s %10s" % ("Tag", "Art", "Anzahl", "sichert R"))
    for z in zeilen:
        print("     %-12s %-12s %6d %10s" % (z["tag"], z["art"], z["n"], z["s"]))


def ausstiege(con: sqlite3.Connection) -> None:
    _kopf("6  DIE AUSSTIEGE - was der Kurs danach gemacht hat",
          "Zeilen mit Ausstiegsverfolgung (seit 18.09.2026, Phase 1 Paket "
          "1.5). ⚠️ POSITIV heisst: der Kurs FIEL nach dem Ausstieg, der "
          "Verkauf war also richtig")
    try:
        zeilen = con.execute(
            "SELECT COALESCE(ausstieg_outcome_status,'(offen)') st, "
            "       COALESCE(ausstieg_kurs_quelle,'-') q, COUNT(*) n, "
            "       ROUND(AVG(ausstieg_bewegung_5_pct),2) b5, "
            "       ROUND(AVG(ausstieg_bewegung_20_pct),2) b20 "
            "  FROM signals WHERE action IN ('VERKAUFEN','REDUZIEREN') "
            " GROUP BY 1,2 ORDER BY n DESC").fetchall()
    except sqlite3.OperationalError:
        print("  (Ausstiegsfelder fehlen - Pull und Neustart am Notebook?)")
        return
    print("     %-14s %-13s %6s %9s %9s"
          % ("Status", "Kursquelle", "Anzahl", "5 Tage %", "20 Tage %"))
    for z in zeilen:
        print("     %-14s %-13s %6d %9s %9s"
              % (z["st"], z["q"], z["n"], z["b5"], z["b20"]))
    print("     ⚠️ `tagesschluss` heisst: der eigene Ausstiegskurs lag nicht "
          "vor, genommen wurde der Tagesschluss des Signaltags")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="data/tradinginfotool.db")
    a = p.parse_args()
    con = _verbindung(a.db)
    try:
        print("=" * 100)
        print("LIVE-ZAEHLUNG DER KETTE - Schritt 59 Phase 2")
        print("=" * 100)
        print("  Quelle:   %s (nur lesend)" % a.db)
        print("  ⚠️        Jede Zahl hier ist eine ZAEHLUNG. Sie sagt, WIE OFT "
              "etwas vorkam -")
        print("            nicht, ob es TRAEGT. Dafuer braucht es die Messnorm "
              "(Phase 3 und 8).")
        trichter(con)
        vierfeld(con)
        modellurteil(con)
        gegenpruefung(con)
        fuehrung(con)
        ausstiege(con)
        print("\n" + "=" * 100)
        print("ENDE - %s" % VORBEHALT)
        print("=" * 100)
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
