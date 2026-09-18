# -*- coding: utf-8 -*-
"""Was ist nach einem Ausstieg passiert? (18.09.2026, Schritt 59 Phase 1, 1.5)

⚠️⚠️ DER BEFUND, DER DAZU GEFUEHRT HAT (2.401, gezaehlt am 12.09. und am
18.09. bestaetigt): von 491 GEMAILTEN Ausstiegen stehen 485 auf
`outcome_status='nicht_anwendbar'` - also wird KEIN EINZIGER ausgewertet. Die
120 STUMMEN werden dagegen lueckenlos verfolgt. Genau die Empfehlungen, denen
der Nutzer folgen soll, sind die einzigen, ueber die nichts gelernt wird.

DER GRUND IST KEINE SCHLAMPEREI, SONDERN EINE FEHLENDE KATEGORIE. Der
Hauptarm kennt nur EINSTIEGS-Kategorien (`einstieg_nie_erreicht`,
`stop_loss_erreicht`). Ein Verkauf passt in keine davon.

⚠️ WAS EIN AUSSTIEG UEBERHAUPT BEDEUTET. Ein Einstieg hat Ziel und Stop -
daran misst man ihn. Ein Ausstieg hat beides nicht. Die einzige sinnvolle
Frage ist: WAS HAT DER KURS DANACH GEMACHT? Faellt er, war der Verkauf
richtig; steigt er, war er teuer. BEIDE Richtungen werden gemessen - sonst
misst man die haelfte, die man sehen will.

⚠️ DIESE DATEI URTEILT NICHT. Sie erfasst und verfolgt. Kein Band, kein
Nullmodell, keine Schwelle: die BEWERTUNG der Ausstiegsseite ist Phase 5 und
braucht die Messnorm. Wer hier Durchschnitte bildet, misst ohne Norm.

⚠️ DIE NAEHERUNG STEHT IN DER ZEILE, NICHT IN DER DOKU. Der Ausstiegskurs
liegt nur in wenigen Altzeilen vor (`kurs_bei_empfehlung_eur`, seit 13.09.).
Fuer die uebrigen wird der TAGESSCHLUSS des Signaltags genommen - und die
Zeile traegt dann `ausstieg_kurs_quelle='tagesschluss'`. Eine stille
Naeherung hat in diesem Projekt schon mehrfach als echter Wert
weitergelebt.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Die zwei Horizonte (Nutzerentscheidung C2 vom 18.09.).
#
# 20 Handelstage ist der Horizont der Messnorm (H20) - damit ist die Zahl
# spaeter in Phase 5 ohne Umrechnung verwendbar. 5 Handelstage faengt den
# kurzfristigen Fall ab: verkauft, und drei Tage spaeter steht der Kurs
# hoeher. Zwei Spalten kosten nichts; ein fehlender Horizont kostet Wochen.
HORIZONTE = (5, 20)

STATUS_OFFEN = "offen"
STATUS_GEMESSEN = "gemessen"
STATUS_OHNE_REIHE = "keine_kursreihe"

# Welche Zeilen ueberhaupt gemeint sind (C4): ALLE mit Ausstiegsphase, die
# gemailten UND die stummen. Die stummen sind der Vergleichsarm - ohne sie
# laesst sich nie sagen, ob das Mailen selbst etwas aendert.
AUSSTIEGS_AKTIONEN = ("VERKAUFEN", "REDUZIEREN")


def _reihe(conn, symbol: str) -> list[tuple[str, float]]:
    """Die Tagesreihe eines Symbols - (Datum, Schlusskurs), aufsteigend.

    ⚠️ EINE WAEHRUNG, NICHT ZWEI. `price_history_ohlc` fuehrt dasselbe Symbol
    in EUR und USD; gemischt ergaebe das jeden Tag doppelt, mit
    verschiedenen Kursen (derselbe Fehler, den `waehrung_je_symbol` am 07.09.
    aufgeloest hat). Genommen wird die Waehrung mit den meisten Zeilen.

    ⚠️ Prozent ist waehrungsunabhaengig, solange BEIDE Punkte aus derselben
    Reihe stammen - deshalb wird hier NICHT umgerechnet."""
    waehrung = conn.execute(
        "SELECT currency FROM price_history_ohlc WHERE symbol = ? "
        "GROUP BY currency ORDER BY COUNT(*) DESC LIMIT 1", (symbol,)).fetchone()
    if not waehrung:
        return []
    return [(str(r[0])[:10], float(r[1])) for r in conn.execute(
        "SELECT date, close FROM price_history_ohlc "
        "WHERE symbol = ? AND currency = ? ORDER BY date ASC",
        (symbol, waehrung[0]))]


def bewegung(reihe: list, tag: str, horizont: int,
             kurs_start: float | None = None) -> tuple[float | None, float | None, str]:
    """(Ausstiegskurs, Bewegung in Prozent, Herkunft des Ausstiegskurses).

    ⚠️ RICHTUNGSBEREINIGT: Ein Ausstieg ist gut, wenn der Kurs DANACH FAELLT.
    Deshalb `(start - spaeter) / start`. Ein positiver Wert heisst: der
    Verkauf hat sich gelohnt. Ein negativer: er war teuer. Wer das Vorzeichen
    andersherum legt, liest spaeter jede Auswertung verkehrt.
    """
    i = None
    for n, (d, _k) in enumerate(reihe):
        if d <= tag:
            i = n
        else:
            break
    if i is None:
        return None, None, "keine"
    start, quelle = reihe[i][1], "tagesschluss"
    if kurs_start:
        start, quelle = float(kurs_start), "empfehlung"
    j = i + horizont
    if j >= len(reihe) or not start:
        return start, None, quelle
    spaeter = reihe[j][1]
    return start, round(100.0 * (start - spaeter) / start, 4), quelle


def verfolge(conn, *, grenze: int | None = None) -> dict:
    """Alle Ausstiege nachziehen, die noch kein Ergebnis tragen.

    Auch RUECKWIRKEND (Nutzerentscheidung C5): der Kurs nach n Tagen ist eine
    historische Tatsache, kein Modellwert - anders als beim Potential, das
    sich NICHT rekonstruieren laesst (2.458-archaeologie). Die Kursreihen
    liegen vollstaendig vor.

    ⚠️ Sie haelt nichts an: ein Fehler je Zeile wird gezaehlt, nicht
    geworfen."""
    aus = {"geprueft": 0, "gemessen": 0, "ohne_reihe": 0, "offen": 0,
           "fehler": 0}
    frage = (
        "SELECT id, symbol, date(created_at) tag, action, "
        "       kurs_bei_empfehlung_eur, gate_passed "
        "  FROM signals "
        " WHERE action IN (%s) "
        "   AND (ausstieg_outcome_status IS NULL "
        "        OR ausstieg_outcome_status = ?) "
        " ORDER BY created_at" % ",".join("?" * len(AUSSTIEGS_AKTIONEN)))
    zeilen = conn.execute(frage, (*AUSSTIEGS_AKTIONEN, STATUS_OFFEN)).fetchall()
    if grenze:
        zeilen = zeilen[:grenze]
    reihen: dict = {}
    for z in zeilen:
        kennung, symbol, tag = z[0], z[1], z[2]
        aus["geprueft"] += 1
        try:
            if symbol not in reihen:
                reihen[symbol] = _reihe(conn, symbol)
            reihe = reihen[symbol]
            if not reihe:
                conn.execute("UPDATE signals SET ausstieg_outcome_status = ? "
                             "WHERE id = ?", (STATUS_OHNE_REIHE, kennung))
                aus["ohne_reihe"] += 1
                continue
            werte, quelle, start = {}, "keine", None
            for h in HORIZONTE:
                start, pct, quelle = bewegung(reihe, tag, h, z[4])
                werte[h] = pct
            # ⚠️ ERST WENN DER LAENGSTE HORIZONT VOLL IST, ist die Zeile fertig.
            # Sonst stuende ein Teilergebnis da, das spaeter niemand nachzieht.
            fertig = werte.get(max(HORIZONTE)) is not None
            conn.execute(
                "UPDATE signals SET ausstieg_outcome_status = ?, "
                "ausstieg_outcome_geprueft_am = date('now'), "
                "ausstieg_kurs_eur = ?, ausstieg_kurs_quelle = ?, "
                "ausstieg_bewegung_5_pct = ?, ausstieg_bewegung_20_pct = ? "
                "WHERE id = ?",
                (STATUS_GEMESSEN if fertig else STATUS_OFFEN, start,
                 quelle if start is not None else None,
                 werte.get(5), werte.get(20), kennung))
            aus["gemessen" if fertig else "offen"] += 1
        except Exception:                                    # noqa: BLE001
            logger.exception("Ausstieg %s (%s) nicht verfolgbar", kennung, symbol)
            aus["fehler"] += 1
    conn.commit()
    return aus
