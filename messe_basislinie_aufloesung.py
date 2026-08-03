"""Messung zu Task #617 - NUR LESEN, schreibt nichts in die Datenbank.

Zwei Blocker sind zu klaeren, bevor die Basislinie als Fakt ins LLM geht:

BLOCKER 1 - Aufloesungs-Asymmetrie.
  basislinie_erwartungswert() (backward_tracking.py:1771) bewertet eine
  Zufallsziehung, die weder Stop noch Ziel trifft, zum Schlusskurs und zaehlt
  sie MIT. Unsere echten Signale bekommen in derselben Lage
  'abgelaufen_unentschieden' und GAR KEINEN R-Wert - sie fliegen aus der SQN.
  Die Basislinie hat also einen Topf, den unsere Signale nicht haben.
  Dieses Skript misst, wie gross der Topf ist und was er am Erwartungswert
  aendert.

BLOCKER 2 - Vorzeichen-Widerspruch.
  Der Docstring (03.08.) sagt, der Zufallseinstieg verliere systematisch
  (-0,11 bis -0,26 R). Der Export vom 04.08. liefert fuer hebel/real +0,081 R.
  Das dreht die Schlussfolgerung um. Das Parameter-Raster unten zeigt, wie
  stark der Wert vom Parametersatz abhaengt - und ob beide Zahlen aus
  demselben Code stammen koennen.

Am NOTEBOOK laufen lassen (Produktiv-DB), ohne Umleitung:

    python messe_basislinie_aufloesung.py

Das Skript legt die Ergebnisdatei SELBST im Austauschordner ab und nennt am
Ende den vollen Pfad. Eine Shell-Umleitung wuerde im aktuellen Verzeichnis
landen, also im Repo-Ordner - genau das soll sie nicht.
"""

from __future__ import annotations

import os
import statistics
import sys

from database import db
from agent.krypto.backward_tracking import (
    _BASISLINIE_HORIZONT_TAGE,
    gap_bewusster_fill,
    lade_kursreihen,
)


# Dasselbe Raster, das der Docstring mit "je nach Parametersatz" meint.
# stop_rel = Stop-Abstand relativ zum Einstieg, crv = Ziel als Vielfaches davon.
RASTER_STOP = (0.02, 0.03, 0.05, 0.08)
RASTER_CRV = (2.0, 2.5, 3.0, 4.0)

# Der Austauschordner (reference_notebook_analyseordner_standard). Der
# Laufwerksbuchstabe der Google-Drive-Einbindung kann sich je Geraet
# unterscheiden, deshalb mehrere Kandidaten - der erste existierende gewinnt.
AUSTAUSCH_KANDIDATEN = (
    r"K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten",
    r"G:\My Drive\Claude_Austauschordner\Notebook_Analysedaten",
    r"H:\My Drive\Claude_Austauschordner\Notebook_Analysedaten",
    os.path.expanduser(r"~\Google Drive\Claude_Austauschordner\Notebook_Analysedaten"),
    os.path.expanduser(r"~\My Drive\Claude_Austauschordner\Notebook_Analysedaten"),
)
DATEINAME = "basislinie_messung.txt"


class Tee:
    """Schreibt gleichzeitig auf den Bildschirm und in die Ergebnisdatei.

    So sieht der Nutzer den Fortschritt (das Raster laeuft einige Minuten)
    UND bekommt die Datei, ohne an eine Shell-Umleitung denken zu muessen -
    die wuerde im aktuellen Verzeichnis landen statt im Austauschordner."""

    def __init__(self, ziel):
        self._ziel = ziel

    def write(self, text):
        sys.__stdout__.write(text)
        self._ziel.write(text)
        return len(text)

    def flush(self):
        sys.__stdout__.flush()
        self._ziel.flush()


def _ergebnispfad() -> tuple[str, str | None]:
    """Liefert (voller Pfad, Hinweistext bei Ausweichen).

    Faellt auf das Skriptverzeichnis zurueck, wenn kein Austauschordner
    gefunden wird - lieber eine Datei am falschen Ort als gar keine."""
    for ordner in AUSTAUSCH_KANDIDATEN:
        if os.path.isdir(ordner):
            return os.path.join(ordner, DATEINAME), None
    hier = os.path.dirname(os.path.abspath(__file__))
    return (
        os.path.join(hier, DATEINAME),
        "Kein Austauschordner gefunden - Datei liegt im Skriptverzeichnis "
        "und muss von Hand kopiert werden.",
    )


def basislinie_mit_buckets(reihen: dict, stop_rel: float, crv: float,
                           ist_short: bool,
                           horizont: int = _BASISLINIE_HORIZONT_TAGE) -> dict:
    """Exakte Kopie der Schleife aus basislinie_erwartungswert(), aber die drei
    Ausgaenge werden GETRENNT gesammelt statt in einen Topf geworfen.

    Bewusst kopiert und nicht importiert: die Originalfunktion gibt nur den
    Mittelwert zurueck: die Aufteilung, um die es hier geht, entsteht in ihrem
    Inneren und ist von aussen nicht sichtbar. Jede Zeile der Preis-Logik ist
    unveraendert uebernommen - wird sie angepasst, misst dieses Skript etwas
    anderes als der Produktivcode."""
    r_stop: list[float] = []
    r_ziel: list[float] = []
    r_abgelaufen: list[float] = []
    ohne_ergebnis = 0

    for rr in reihen.values():
        for i in range(len(rr) - horizont - 1):
            e = rr[i]["close"]
            if not e or e <= 0:
                continue
            risiko = e * stop_rel
            stop = e + risiko if ist_short else e - risiko
            ziel = e - risiko * crv if ist_short else e + risiko * crv
            fenster = rr[i + 1:i + 2 + horizont]
            ergebnis = None
            eimer = None
            for p in fenster:
                hoch, tief, auf = p["high"], p["low"], p["open"]
                if hoch is None or tief is None:
                    continue
                hit_stop = (hoch >= stop) if ist_short else (tief <= stop)
                hit_ziel = (tief <= ziel) if ist_short else (hoch >= ziel)
                if hit_stop:
                    fill = gap_bewusster_fill(stop, auf, ist_stop=True, ist_short=ist_short)
                    ergebnis = ((e - fill) if ist_short else (fill - e)) / risiko
                    eimer = "stop"
                    break
                if hit_ziel:
                    fill = gap_bewusster_fill(ziel, auf, ist_stop=False, ist_short=ist_short)
                    ergebnis = ((e - fill) if ist_short else (fill - e)) / risiko
                    eimer = "ziel"
                    break
            if ergebnis is None and fenster and fenster[-1]["close"]:
                schluss = fenster[-1]["close"]
                ergebnis = ((e - schluss) if ist_short else (schluss - e)) / risiko
                eimer = "abgelaufen"
            if ergebnis is None:
                ohne_ergebnis += 1
                continue
            {"stop": r_stop, "ziel": r_ziel, "abgelaufen": r_abgelaufen}[eimer].append(ergebnis)

    alle = r_stop + r_ziel + r_abgelaufen
    nur_aufgeloest = r_stop + r_ziel
    return {
        "n_stop": len(r_stop),
        "n_ziel": len(r_ziel),
        "n_abgelaufen": len(r_abgelaufen),
        "n_gesamt": len(alle),
        "ohne_ergebnis": ohne_ergebnis,
        # So rechnet der Produktivcode heute:
        "ew_mit_abgelaufen": statistics.fmean(alle) if alle else None,
        # So waere es symmetrisch zu unseren echten Signalen:
        "ew_nur_aufgeloest": statistics.fmean(nur_aufgeloest) if nur_aufgeloest else None,
        # Der strittige Topf fuer sich allein:
        "ew_nur_abgelaufen": statistics.fmean(r_abgelaufen) if r_abgelaufen else None,
    }


def _median_parameter_echter_signale(conn) -> None:
    """Welchen Stop-Abstand und welches CRV haben unsere ECHTEN Hebel-Signale?

    Ohne das weiss man nicht, welche Zelle des Rasters ueberhaupt die
    relevante ist - und der Vergleich mit der Basislinie haengt genau daran."""
    cur = conn.cursor()
    cur.execute("""
        SELECT entry_usd_von, stop_loss_usd_von, take_profit_usd_von, richtung,
               outcome_status, outcome_realisiertes_crv
          FROM hebel_signals
         WHERE COALESCE(risk_veto, 0) = 0
           AND entry_usd_von IS NOT NULL
           AND stop_loss_usd_von IS NOT NULL
           AND take_profit_usd_von IS NOT NULL
    """)
    stops: list[float] = []
    crvs: list[float] = []
    status_zaehler: dict[str, int] = {}
    for entry, stop, ziel, richtung, status, r in cur.fetchall():
        try:
            entry, stop, ziel = float(entry), float(stop), float(ziel)
        except (TypeError, ValueError):
            continue
        if entry <= 0:
            continue
        risiko = abs(entry - stop)
        if risiko <= 0:
            continue
        stops.append(risiko / entry)
        crvs.append(abs(ziel - entry) / risiko)
        status_zaehler[str(status)] = status_zaehler.get(str(status), 0) + 1

    print("\n=== Parameter unserer ECHTEN Hebel-Signale (ohne Veto) ===")
    if stops:
        print(f"  n = {len(stops)}")
        print(f"  Stop-Abstand relativ: Median {statistics.median(stops):.4f}  "
              f"Mittel {statistics.fmean(stops):.4f}")
        print(f"  geplantes CRV:        Median {statistics.median(crvs):.2f}  "
              f"Mittel {statistics.fmean(crvs):.2f}")
        print("  -> das ist die relevante Zelle im Raster unten")
    else:
        print("  keine auswertbaren Zonen gefunden")

    print("\n=== Outcome-Verteilung (welcher Topf faellt bei uns weg?) ===")
    for k, v in sorted(status_zaehler.items(), key=lambda x: -x[1]):
        print(f"  {k:34s} {v:5d}")
    print("  HINWEIS: nur take_profit_erreicht / stop_loss_erreicht liefern einen")
    print("  R-Wert und landen in der SQN. 'abgelaufen_unentschieden' entspricht")
    print("  genau dem Topf, den die Basislinie MITZAEHLT.")


def main() -> int:
    pfad, hinweis = _ergebnispfad()
    ziel = open(pfad, "w", encoding="utf-8")
    alt = sys.stdout
    sys.stdout = Tee(ziel)
    conn = db.get_connection()
    try:
        if hinweis:
            print(f"HINWEIS: {hinweis}")
        _median_parameter_echter_signale(conn)

        print("\n=== Kursreihen laden ===")
        reihen = lade_kursreihen(conn)
        zeilen = sum(len(r) for r in reihen.values())
        print(f"  {len(reihen)} Reihen, {zeilen} Zeilen, Horizont "
              f"{_BASISLINIE_HORIZONT_TAGE} Tage")
        if not reihen:
            print("  ABBRUCH: keine Kursreihen - Messung nicht moeglich")
            return 1

        for ist_short in (False, True):
            titel = "SHORT" if ist_short else "LONG"
            print(f"\n\n=== BASISLINIE {titel}: Ausgaenge getrennt ===")
            print(f"{'stop_rel':>9} {'crv':>5} | {'n ges':>8} {'%Stop':>6} "
                  f"{'%Ziel':>6} {'%abgel':>7} | {'EW mit':>8} {'EW ohne':>8} "
                  f"{'EW abgel':>9} | {'Diff':>7}")
            print("  " + "-" * 92)
            for stop_rel in RASTER_STOP:
                for crv in RASTER_CRV:
                    b = basislinie_mit_buckets(reihen, stop_rel, crv, ist_short)
                    n = b["n_gesamt"]
                    if not n:
                        print(f"{stop_rel:9.3f} {crv:5.1f} |  (keine Ziehungen)")
                        continue
                    mit = b["ew_mit_abgelaufen"]
                    ohne = b["ew_nur_aufgeloest"]
                    abg = b["ew_nur_abgelaufen"]
                    diff = (mit - ohne) if (mit is not None and ohne is not None) else None
                    print(
                        f"{stop_rel:9.3f} {crv:5.1f} | {n:8d} "
                        f"{b['n_stop'] / n * 100:5.1f}% {b['n_ziel'] / n * 100:5.1f}% "
                        f"{b['n_abgelaufen'] / n * 100:6.1f}% | "
                        f"{'-' if mit is None else format(mit, '+8.4f')} "
                        f"{'-' if ohne is None else format(ohne, '+8.4f')} "
                        f"{'-' if abg is None else format(abg, '+9.4f')} | "
                        f"{'-' if diff is None else format(diff, '+7.4f')}"
                    )

        print("\n\n=== SO IST DAS ZU LESEN ===")
        print("BLOCKER 1: Spalte '%abgel' ist der Topf, den die Basislinie mitzaehlt")
        print("  und unsere Signale nicht haben. Spalte 'Diff' ist der Betrag, um den")
        print("  die Basislinie dadurch verschoben wird - also die Verzerrung des")
        print("  Signalbeitrags. Ist Diff nahe null, war der Verdacht folgenlos.")
        print("BLOCKER 2: streuen die 'EW mit'-Werte ueber das Raster von -0,26 bis")
        print("  +0,08, erklaert allein der Parametersatz den Widerspruch zwischen")
        print("  Docstring und Export. Sind sie durchweg positiv, stimmt die")
        print("  Docstring-Begruendung nicht mehr und gehoert korrigiert.")
        print("\nNICHT vergessen: dieses Skript beantwortet NICHT, welche der beiden")
        print("Angleichungen richtig ist (Basislinie kuerzen vs. unsere Signale")
        print("mitbewerten). Das ist die Gegenfrage NACH der Messung - Variante (b)")
        print("wuerde die SQN-Basis aller bisherigen Auswertungen aendern.")
        return 0
    finally:
        conn.close()
        sys.stdout = alt
        ziel.close()
        print(f"\nErgebnisdatei geschrieben:\n  {pfad}")
        if hinweis:
            print(f"  ACHTUNG: {hinweis}")


if __name__ == "__main__":
    sys.exit(main())
