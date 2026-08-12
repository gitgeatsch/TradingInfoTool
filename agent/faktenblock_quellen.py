# -*- coding: utf-8 -*-
"""Woher die Zusatzinfo kommt - Abbildung der Pipeline-Fakten (12.08.2026).

WAS DIESE DATEI NICHT TUT: sie ruft keine API. Alle Werte stehen bereits in den
`facts`-Baeumen, die die sechs Pipelines ohnehin bauen und in `facts_json`
ablegen. Hier werden sie nur GEFUNDEN und in die Form gebracht, die
`faktenblock.zusatz()` erwartet. Eine zweite Abfrage waere eine zweite Quelle,
und zwei Quellen fuer dieselbe Zahl sind der Fehler, den die alte Hebel-Mail
hatte (Umbauplan 12.5).

DIE PFADE STAMMEN AUS ECHTEN GESPEICHERTEN FAKTEN, nicht aus dem Quelltext der
Pipelines - ein `facts["antizyklisch"]["long_konten_anteil_prozent"]` im Code
sagt nicht, ob der Schluessel im Betrieb auch ankommt. Nachgesehen wurde in
`signals.facts_json` und `hebel_signals.facts_json`:

    antizyklisch.long_konten_anteil_prozent    53.14      -> Retail-Konsens
    antizyklisch.funding_rate_aktuell          -2.85e-05  -> Finanzierung
    fundamentaldaten.kgv                                  -> Bewertung

MEHRERE PFADE JE WERT, und das ist Absicht. Die Baeume haben sich ueber Monate
veraendert (Hebel-Fakten von 2026-07 tragen `optionsmarkt` noch nicht), und ein
Adapter, der beim ersten Namenswechsel still nichts mehr findet, ist schlimmer
als keiner. Der erste Pfad, der eine Zahl liefert, gewinnt.

STILL NICHTS ZU FINDEN IST DER GEFAEHRLICHE FALL. Deshalb gibt `abbilden()`
ausser den Werten auch zurueck, WAS NICHT GEFUNDEN wurde - und die Pruefung
laeuft gegen echte Faktensaetze aus der Datenbank, nicht gegen erfundene.
"""
from __future__ import annotations

# Je Zielschluessel eine Liste von Pfaden in den Pipeline-Fakten.
PFADE = {
    "retail_long_pct": (("antizyklisch", "long_konten_anteil_prozent"),),
    "put_skew": (("optionsmarkt", "skew_prozentpunkte"),
                 ("optionsmarkt", "skew"),
                 ("optionsmarkt_skew",)),
    # GERATEN WAR FALSCH. Meine ersten Pfade hiessen `relativ_30d_prozent` und
    # `relativ_prozent` - beides gibt es nicht. `btc_relativwert_fakt()` liefert
    # `relativstaerke_pct`. Aufgefallen ist es nur, weil die Pruefung gegen
    # echte Faktensaetze lief und 0 von 40 traf.
    "btc_relativwert_pct": (("btc_relativwert", "relativstaerke_pct"),),
    "kgv": (("fundamentaldaten", "kgv"),),
    "short_interest_pct": (("short_interest_finra", "anteil_streubesitz_prozent"),
                           ("short_interest_finra", "short_interest_prozent")),
    "insider_saldo": (("insider_trading", "netto_meldungen"),
                      ("insider_trading", "saldo")),
    "analysten_trend": (("analysten_trend_finnhub", "tendenz"),
                        ("analysten_trend_finnhub", "trend")),
    "lagerbestand_trend": (("lagerbestaende", "tendenz"),
                           ("lagerbestaende", "trend")),
    "cot_netto_pct": (("positionierung", "netto_long_prozent"),
                      ("positionierung", "netto_prozent")),
    "portfolio_exposure_eur": (("portfolio_exposure", "summe_eur"),
                               ("portfolio_exposure", "exposure_eur")),
}

# Die Finanzierung steht als STUNDENSATZ in den Fakten (Kraken, ueber 24 h
# gemittelt) - siehe hebel_analyst.py, Kommentar vom 22.07. Die Mail braucht
# Euro je Tag, und dafuer braucht es die Positionsgroesse. Ohne sie gibt es
# KEINEN Wert: ein Prozentsatz je Stunde ist fuer den Nutzer keine Information.
_FUNDING_PFADE = (("antizyklisch", "funding_rate_aktuell"),
                  ("antizyklisch", "funding_rate_aktuell_prozent_pro_stunde"))


def _hole(fakten: dict, pfad: tuple):
    knoten = fakten
    for teil in pfad:
        if not isinstance(knoten, dict):
            return None
        knoten = knoten.get(teil)
    return knoten


def _funding_eur_tag(fakten: dict, position_eur, hebel) -> float | None:
    """Stundensatz -> Euro je Tag auf dem GEHEBELTEN Volumen.

    Der Satz laeuft auf das gehandelte Volumen, nicht auf den Einsatz - bei
    Hebel 3 sind das drei Euro Volumen je Euro Eigenkapital. Wer das
    weglaesst, meldet ein Drittel der tatsaechlichen Kosten."""
    if not position_eur or position_eur <= 0:
        return None
    for pfad in _FUNDING_PFADE:
        w = _hole(fakten, pfad)
        if not isinstance(w, (int, float)):
            continue
        # Der zweite Pfad traegt bereits Prozent, der erste einen Bruchteil.
        satz = float(w) / 100.0 if pfad[-1].endswith("prozent_pro_stunde") else float(w)
        volumen = float(position_eur) * float(hebel or 1.0)
        return round(abs(satz) * 24.0 * volumen, 2)
    return None


def abbilden(fakten: dict | None, *, bereich: str,
             position_eur: float | None = None,
             hebel: float | None = None) -> tuple[dict, list[str]]:
    """(Werte fuer `faktenblock.zusatz()`, Liste der nicht gefundenen Schluessel).

    `bereich` bestimmt, wonach ueberhaupt gesucht wird - ein KGV bei einem
    Krypto-Signal waere kein fehlender Wert, sondern eine sinnlose Frage."""
    from agent.faktenblock import ZUSATZ_JE_BEREICH

    gesucht = ZUSATZ_JE_BEREICH.get(bereich, ())
    werte, fehlt = {}, []
    if not isinstance(fakten, dict) or not fakten:
        # LEERE FAKTEN SIND KEIN LEERER BEREICH. 78 von 118 gespeicherten
        # Spot-Signalen tragen `{}` - wer das als "nichts vorhanden" liest,
        # haelt einen Defekt fuer einen Normalzustand.
        return {}, list(gesucht)

    for schluessel in gesucht:
        if schluessel == "funding_eur_tag":
            w = _funding_eur_tag(fakten, position_eur, hebel)
        else:
            w = None
            for pfad in PFADE.get(schluessel, ()):
                w = _hole(fakten, pfad)
                if w is not None:
                    break
        if w is None or (isinstance(w, str) and not w.strip()):
            fehlt.append(schluessel)
        else:
            werte[schluessel] = w
    return werte, fehlt
