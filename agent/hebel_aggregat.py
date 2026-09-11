# -*- coding: utf-8 -*-
"""H-5 - DER AGGREGAT-DECKEL: alle offenen Hebelrisiken zusammen (11.09.2026).

DIE VORGABE (Paket B, Nutzerentscheidung 11.09.): *"alle Hebelrisiken zusammen
hoechstens 3 % des Kapitals"*. Und P-4 (10.09.): *"der Markt ist korreliert,
das ist ein Fakt. Der Hebel soll auf ein einzelnes Asset angewendet werden"* -
die Korrelation gehoert in DIESEN Deckel, nicht in eine Schrumpfung von r(q).

WARUM ES IHN BRAUCHT. r(q) bemisst EINEN Trade (0,50-1,25 % des Kapitals).
Kelly gilt fuer eine wiederholte, UNABHAENGIGE Wette; gemessen waren am NB 32
gleichzeitige Positionen in einem stark korrelierten Markt (P-4). Fallen alle
zugleich an den Stop, addieren sich die Verluste.

DIE KORRELATION STECKT IN DER SUMME. Die Risiken werden schlicht ADDIERT - das
unterstellt, dass alles gleichzeitig verliert (Korrelation 1). Fuer Krypto ist
das die ehrliche Annahme, und sie braucht keine Korrelationsschaetzung, die
selbst wieder falsch sein kann.

WAS ALS OFFENES HEBELRISIKO ZAEHLT:

    offene Positionen   aus `hebel_positions` (echter Bitpanda-Abgleich), ueber
                        die Hebelfuehrung (H-4): Verlust bis zum Plan-Stop,
                        hoechstens das Eigenkapital. Mit der Liquidation vor
                        dem Stop: das EIGENKAPITAL - mehr kann eine
                        Margin-Position nicht verlieren. OHNE Plan: ein
                        ANGENOMMENER Stop (`STOP_ANGENOMMEN`), hoechstens das
                        Eigenkapital - siehe unten.
    offene Signale      Hebelsignale der Rollen-Kette, die noch zu einer
                        Position werden KOENNEN: noch nicht aufgeloest, Frist
                        nicht abgelaufen, juenger als das Zuordnungsfenster der
                        Hebelfuehrung, keiner offenen Position zugeordnet. Der
                        Nutzer kann jedes gemailte Signal eroeffnen - wer sie
                        nicht mitzaehlt, erlaubt drei Signale zu je 1,25 %.
    Signale DIESES Laufs  die im Trockenlauf nicht geschrieben werden

WAS DER DECKEL TUT: er BEGRENZT, er verhindert nicht - dieselbe Linie wie die
Toepfe. Ein neuer Hebeltrade bekommt hoechstens das freie Restrisiko. Faellt
sein Hebel dadurch unter 2x, wird er Spot mit dem gewohnten Betrag - die
Paket-B-Regel "unter 2x ist Spot" gilt unveraendert.

⚠️ ANNAHMEN (Befund 2.380-annahmen): das Zuordnungsfenster
(`hebelfuehrung.KOPPEL_TAGE`) bestimmt, wie lange ein nicht eroeffnetes Signal
Risiko belegt - Nutzerentscheidung 11.09.: 24 Stunden (vorher 3 Tage).

⚠️ POSITION OHNE BEKANNTEN STOP - NUTZERENTSCHEIDUNG 11.09.2026: VARIANTE B
(Befund 2.380-ohne-stop). Sie zaehlt mit einem angenommenen Stop von 11,7 %
ab Einstand, hoechstens mit dem Eigenkapital. Die erste Fassung nahm das
ganze Eigenkapital (A) - vom Nutzer abgelehnt: *"eine Position blockiert
alles, das passt nicht zu unserem Vorgehen. Initial haben wir angedacht, dass
zumindest drei Hebelpositionen offen sein koennen."* An den echten NB-
Positionen: A im Median 222 EUR, B 166 EUR; im Median passen 2,5 gegen 3,3
Positionen in den Deckel.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

AUFGELOEST_NICHT = (None, "", "offen")

# DER ANGENOMMENE STOP einer Position ohne zugeordnetes Signal, relativ zum
# Einstand. HERKUNFT: die Stopregel des Codes auf 1.289 echte NB-Einstiege
# angewandt, mit deren Widerlegungspreis - Median 11,7 % (10 % 5,9 · 90 %
# 16,0; Befund 2.378-gegenpruefung). Es ist der Stop, den das System fuer
# einen solchen Trade im Median selbst gesetzt haette - keine Vorsichtszahl.
STOP_ANGENOMMEN = 0.117


def _risiko_position(t: dict) -> tuple[float, str]:
    """(Risiko in EUR, Grund) einer gefuehrten Position."""
    from agent.schreibweise import de

    pw = float(t.get("positionswert_eur") or 0.0)
    ek = t.get("eigenkapital_eur")
    L = t.get("hebel")
    ek = float(ek) if ek else ((pw / float(L)) if L and float(L) > 0 else pw)
    if t.get("einstand_eur") is None:
        return ek, "unvollstaendig rekonstruiert - Eigenkapital als Hoechstverlust"
    if not t.get("plan"):
        # VARIANTE B (Nutzer 11.09.): angenommener Stop, hoechstens das
        # Eigenkapital. ⚠️ Die Liquidation wird hier NICHT gegen den
        # angenommenen Stop geprueft - so wurde B vorgelegt und bestaetigt;
        # die Frage steht zur Abstimmung (Befund 2.382-liquidation).
        risiko = min(STOP_ANGENOMMEN * pw, ek)
        return risiko, ("ohne bekannten Stop - angenommen %s %% ab Einstand%s"
                        % (de(100 * STOP_ANGENOMMEN, 1),
                           ", begrenzt auf das Eigenkapital"
                           if risiko >= ek - 1e-9 else ""))
    if t.get("liquidation_vor_stop"):
        return ek, "Liquidation vor dem Stop - Eigenkapital als Hoechstverlust"
    s = float(t.get("stop_abstand_einstand") or 0.0)
    return min(max(0.0, s) * pw, ek), "bis zum Stop"


def _risiko_signal(zeile: dict, hebelnenner_eur: float) -> tuple[float, str]:
    """(Risiko in EUR, Grund) eines offenen Hebelsignals."""
    v = zeile.get("verlust_am_stop_eur")
    if v is not None:
        return float(v), "Verlust am Stop laut Rechnung"
    # RUECKFALL fuer Zeilen vor der Spalte: Einsatz x Hebel x Stopabstand. Der
    # Einsatz ist der Hebelnenner - `rechne()` kann ihn nur verkleinern, die
    # Schaetzung liegt also eher darueber (die vorsichtige Richtung).
    from agent.krypto.backward_tracking import _zonen_absolut

    z = _zonen_absolut({
        "entry_usd_von": zeile.get("entry_eur_von"),
        "entry_usd_bis": zeile.get("entry_eur_bis"),
        "stop_loss_usd_von": zeile.get("stop_loss_eur_von"),
        "stop_loss_usd_bis": zeile.get("stop_loss_eur_bis"),
        "take_profit_usd_von": zeile.get("take_profit_eur_von"),
        "take_profit_usd_bis": zeile.get("take_profit_eur_bis")})
    if z is None or not zeile.get("hebel"):
        return 0.0, "ohne Zonen - nicht bewertbar"
    return (float(hebelnenner_eur) * float(zeile["hebel"]) * float(z["stop_rel"]),
            "geschaetzt: Einsatz x Hebel x Stop")


def _ist_eroeffnung(aktion, richtung) -> bool:
    from agent import hebelfuehrung as HF

    a = str(aktion or "").upper()
    short = str(richtung or "").upper() == "SHORT"
    return a in HF.EROEFFNUNG or (short and a not in ("HALTEN", "NICHTS_TUN"))


def offene_signale(conn, *, jetzt=None, ausgenommen=(),
                   hebelnenner_eur: float = 500.0) -> list:
    """Hebelsignale, die noch zu einer Position werden koennen."""
    from agent import hebelfuehrung as HF

    jetzt = HF._zeit(jetzt) or datetime.now(timezone.utc)
    vorhanden = {r[1] for r in conn.execute("PRAGMA table_info(signals)")}
    if not {"instrument", "quelle_kette", "outcome_status"} <= vorhanden:
        return []
    felder = ["id", "symbol", "action", "created_at", "outcome_status"] + [
        c for c in ("richtung", "hebel", "verlust_am_stop_eur", "umgeworfen_bis",
                    "entry_eur_von", "entry_eur_bis", "stop_loss_eur_von",
                    "stop_loss_eur_bis", "take_profit_eur_von",
                    "take_profit_eur_bis") if c in vorhanden]
    ab = jetzt - timedelta(days=HF.KOPPEL_TAGE)
    cur = conn.execute(
        "SELECT %s FROM signals WHERE quelle_kette = 'rollen' "
        "AND instrument = 'hebel'" % ", ".join(felder))
    namen = [d[0] for d in cur.description]
    aus = []
    for werte in cur.fetchall():
        r = dict(zip(namen, werte))
        erzeugt = HF._zeit(r.get("created_at"))
        if erzeugt is None or erzeugt < ab or erzeugt > jetzt:
            continue
        if r.get("id") in set(ausgenommen):
            continue
        if r.get("outcome_status") not in AUFGELOEST_NICHT:
            continue
        if not _ist_eroeffnung(r.get("action"), r.get("richtung")):
            continue
        frist = str(r.get("umgeworfen_bis") or "")[:10]
        if frist and jetzt.date().isoformat() > frist:
            continue
        risiko, grund = _risiko_signal(r, hebelnenner_eur)
        aus.append({"art": "signal", "symbol": r.get("symbol"),
                    "signal_id": r.get("id"), "risiko_eur": risiko,
                    "grund": grund, "erzeugt_am": r.get("created_at")})
    return aus


def aggregat(conn, *, kapital_eur: float, anteil: float, jetzt=None,
             lauf_signale=None, hebelnenner_eur: float = 500.0,
             marge: float | None = None) -> dict:
    """Der Stand des Deckels: offen, Deckel, frei - und woraus es sich ergibt."""
    from agent import hebelfuehrung as HF
    from agent.schreibweise import de

    posten = []
    plan_ids = set()
    for t in HF.lade(conn, jetzt=jetzt, marge=marge):
        risiko, grund = _risiko_position(t)
        posten.append({"art": "position", "symbol": t.get("symbol"),
                       "position_id": t.get("position_id"),
                       "risiko_eur": risiko, "grund": grund})
        if t.get("plan"):
            plan_ids.add(t["plan"].get("signal_id"))
    posten += offene_signale(conn, jetzt=jetzt, ausgenommen=plan_ids,
                             hebelnenner_eur=hebelnenner_eur)
    # SIGNALE DIESES LAUFS, die (noch) keine Zeile haben - im Trockenlauf wird
    # nicht geschrieben. Geschriebene tragen eine Kennung und sind oben schon
    # gezaehlt; sie hier ein zweites Mal zu nehmen waere eine Doppelbuchung.
    for e in lauf_signale or []:
        f = (e or {}).get("felder") or {}
        if e.get("id") is not None or f.get("instrument") != "hebel":
            continue
        if not _ist_eroeffnung(f.get("action"), f.get("richtung")):
            continue
        posten.append({"art": "lauf", "symbol": e.get("symbol"),
                       "risiko_eur": float(f.get("verlust_am_stop_eur") or 0.0),
                       "grund": "Signal dieses Laufs"})
    offen = sum(p["risiko_eur"] for p in posten)
    deckel = float(anteil) * float(kapital_eur)
    frei = max(0.0, deckel - offen)
    satz = ("Aggregat-Deckel: offene Hebelrisiken %s EUR (%d Posten) von %s EUR "
            "(%s %% von %s EUR Kapital) - frei %s EUR"
            % (de(offen, 0), len(posten), de(deckel, 0), de(100 * float(anteil), 1),
               de(float(kapital_eur), 0), de(frei, 0)))
    return {"offen_eur": offen, "deckel_eur": deckel, "frei_eur": frei,
            "anteil": float(anteil), "kapital_eur": float(kapital_eur),
            "posten": posten, "satz": satz}
