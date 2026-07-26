# -*- coding: utf-8 -*-
"""Optionsmarkt-Fakt (2026-07-26, Punkt 2 des Regime-Persistenz-Folge-
Vorschlags, siehe Basisinfos/Regelwerksmanual.md): uebersetzt die rohen
Deribit-Werte (DVOL + naeherungsweiser Skew, siehe api/deribit.py) in einen
Fakt fuer build_hebel_facts() - reine Einordnungs-/Formatierungsschicht,
keine Berechnung, mirrort btc_relativwert_fakt() (agent/krypto/
btc_relativwert.py). Bezieht sich IMMER auf BTC (marktweiter Barometer),
unabhaengig vom Coin des jeweiligen Signals - siehe SYSTEM_PROMPT Regel 21
in hebel_analyst.py fuer die Cross-Check-Anwendung gegen die eigene
confidence_pct des Modells.

Bewusst KEINE hart kategorisierten DVOL-Baender (anders als VIX_BANDS in
regime.py, die auf breit etablierten Finanzmarkt-Konventionen beruhen) - es
gibt keine vergleichbar etablierte DVOL-Skala. Stattdessen wird der Rohwert
direkt genannt, das Modell soll ihn selbst einordnen. Der Skew-Wertungstext
(+-1 Prozentpunkt als "symmetrisch") ist rein deskriptiv, kein Deckel/keine
Vorhersage-Regel - analog zur bereits etablierten +-3pp-Wertung in
btc_relativwert.py.

`fetch_optionsmarkt_fakt()` ist bewusst der einzige Einstiegspunkt fuer
hebel_pipeline.py - fetcht direkt bei jedem Hebel-Signal-Lauf (KEINE eigene
Caching-Tabelle/Scheduler-Job, anders als makro_analog.py), weil Hebel-
Signale selten genug entstehen (Trigger-basiertes Screening, keine Sekunden-
Taktung) und Deribits Endpunkte kein dokumentiertes Rate-Limit haben - exakt
dasselbe Live-Fetch-Muster wie agent/krypto/anticyclic.py::assess() fuer die
Kraken-Funding-Rate. Faengt Netzwerkfehler selbst ab (P-8), Aufrufer braucht
keinen eigenen try/except."""
from __future__ import annotations

import logging

from api.deribit import get_options_skew, get_volatility_index

logger = logging.getLogger(__name__)

_SKEW_SYMMETRISCH_SCHWELLE_PP = 1.0


def optionsmarkt_fakt(dvol: float | None, skew: dict | None, config: dict | None) -> dict | None:
    """`dvol`/`skew` kommen bereits fertig abgerufen vom Aufrufer
    (api/deribit.py::get_volatility_index()/get_options_skew(), beide fuer
    BTC). None, wenn deaktiviert oder beide Werte fehlen (z.B. Deribit nicht
    erreichbar oder kein passender Verfallstermin - P-8, kein harter
    Abbruch)."""
    cfg = (config or {}).get("deribit_optionsmarkt", {})
    if not cfg.get("aktiv", True):
        return None
    if dvol is None and skew is None:
        return None

    teile = []
    if dvol is not None:
        teile.append(f"Implizite Volatilität (DVOL) {dvol:.1f}% p.a. (marktgepreiste 30-Tage-Erwartung).")

    skew_prozentpunkte = None
    if skew is not None:
        skew_prozentpunkte = skew["skew_prozentpunkte"]
        if skew_prozentpunkte > _SKEW_SYMMETRISCH_SCHWELLE_PP:
            skew_wertung = "Markt preist tendenziell mehr Aufwärtsrisiko ein (Call-Skew)"
        elif skew_prozentpunkte < -_SKEW_SYMMETRISCH_SCHWELLE_PP:
            skew_wertung = "Markt preist tendenziell mehr Abwärtsrisiko ein (Put-Skew, klassisches Fear-Skew-Muster)"
        else:
            skew_wertung = "nahezu symmetrisch bepreist, kein klarer Bias erkennbar"
        teile.append(
            f"Options-Skew {skew_prozentpunkte:+.1f} Prozentpunkte "
            f"(Call-IV {skew['call_iv']:.1f}% vs. Put-IV {skew['put_iv']:.1f}%, "
            f"{skew['tage_bis_expiry']} Tage bis Verfall) - {skew_wertung}. "
            "Näherungswert (feste Moneyness-Ziele statt echtem 25-Delta), kein exakter Marktstandard-Wert."
        )

    einordnung = " ".join(teile) + (
        " Bezieht sich immer auf BTC (marktweiter Krypto-Barometer), auch bei Signalen für andere Coins."
    )

    return {
        "dvol_prozent": dvol,
        "skew_prozentpunkte": skew_prozentpunkte,
        "skew_details": skew,
        "einordnung": einordnung,
    }


def fetch_optionsmarkt_fakt(config: dict | None) -> dict | None:
    """Live-Abruf (Deribit, immer BTC) + optionsmarkt_fakt() in einem
    Aufruf - siehe Modul-Docstring fuer die Begründung gegen eine eigene
    Caching-Tabelle. None, wenn `deribit_optionsmarkt.aktiv` false ist oder
    beide Abrufe fehlschlagen."""
    cfg = (config or {}).get("deribit_optionsmarkt", {})
    if not cfg.get("aktiv", True):
        return None

    dvol = None
    skew = None
    try:
        dvol = get_volatility_index("BTC")
    except Exception as exc:
        logger.info("Deribit-DVOL-Abruf fehlgeschlagen: %s", exc)
    try:
        skew = get_options_skew("BTC")
    except Exception as exc:
        logger.info("Deribit-Options-Skew-Abruf fehlgeschlagen: %s", exc)

    return optionsmarkt_fakt(dvol, skew, config)
