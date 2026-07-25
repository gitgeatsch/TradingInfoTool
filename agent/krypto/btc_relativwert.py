# -*- coding: utf-8 -*-
"""BTC-Relativwert (Baustein 1, 2026-07-25, siehe Regelwerksmanual "Krypto-
Relativwert-Bausteine"): uebersetzt eine BTC-/Makro-Ebene-Einschaetzung
(z.B. `historischer_makro_vergleich`, der nur SPX/BTC-Werte liefert) in eine
coinspezifische Groessenordnung - "wenn BTC laut Makro-Analog in den
naechsten Monaten +X% macht, hat sich dieser Coin historisch mit Beta ~Y
dazu bewegt". Relativstaerke (coin_return - btc_return ueber ein kuerzeres
Fenster) zeigt zusaetzlich, ob GERADE Kapital in Alts rotiert (Tailwind)
oder zurueck zu BTC (Headwind).

Krypto Spot+Hebel, NICHT fuer BTC selbst (Self-Comparison-Guard liegt beim
Aufrufer, siehe pipeline.py/hebel_pipeline.py).

WICHTIG - Zeithorizont-Caveat (muss in der Prompt-Regel wiederholt werden):
Beta/Korrelation sind ein MEHRMONATIGER Kontext-Wert (90-Tage-Fenster),
KEINE Aussage ueber die naechsten Tage. Darf NIEMALS als Grundlage fuer eine
kurzfristige Kontrathese-/Teilverkauf-Entscheidung verwendet werden - exakt
die Verwechslung, die den Anstoss fuer diesen ganzen Baustein gab."""
from __future__ import annotations

from indicators.calculations import BtcRelativwert


def btc_relativwert_fakt(ergebnis: BtcRelativwert | None, config: dict | None) -> dict | None:
    """Baut den Fakt fuer build_facts()/build_hebel_facts(). `ergebnis` kommt
    bereits fertig berechnet vom Aufrufer (compute_btc_relativwert(), inkl.
    Self-Comparison-Guard und Datenladen) - dieses Modul ist reine
    Einordnungs-/Formatierungsschicht, keine Berechnung. None, wenn
    deaktiviert oder `ergebnis` None ist (z.B. zu wenig gemeinsame Historie,
    oder das Asset ist BTC selbst)."""
    cfg = (config or {}).get("btc_relativwert", {})
    if not cfg.get("aktiv", True):
        return None
    if ergebnis is None:
        return None

    beta = ergebnis.beta
    korrelation = ergebnis.korrelation

    if korrelation < 0.3:
        korrelation_text = "kaum korreliert mit BTC - bewegt sich weitgehend unabhängig"
    elif korrelation < 0.7:
        korrelation_text = "moderat mit BTC korreliert"
    else:
        korrelation_text = "stark mit BTC korreliert - läuft überwiegend im BTC-Gleichschritt"

    if beta < 0.7:
        beta_text = f"Beta {beta:.2f} - bewegt sich historisch schwächer als BTC (unterdurchschnittlich)"
    elif beta <= 1.3:
        beta_text = f"Beta {beta:.2f} - bewegt sich historisch etwa im gleichen Ausmaß wie BTC"
    else:
        beta_text = f"Beta {beta:.2f} - bewegt sich historisch stärker als BTC (überdurchschnittlich)"

    relativstaerke_text = ""
    if ergebnis.relativstaerke_pct is not None:
        rs = ergebnis.relativstaerke_pct
        if rs > 3:
            rs_wertung = "outperformt BTC gerade spürbar (Tailwind, Kapital rotiert relativ in diesen Coin)"
        elif rs < -3:
            rs_wertung = "underperformt BTC gerade spürbar (Headwind, Kapital rotiert relativ zurück zu BTC)"
        else:
            rs_wertung = "läuft aktuell etwa im Gleichschritt mit BTC"
        relativstaerke_text = (
            f" Relativstärke der letzten {ergebnis.fenster_tage_relativstaerke} Tage: "
            f"{rs:+.1f} Prozentpunkte ggü. BTC - {rs_wertung}."
        )

    einordnung = (
        f"{beta_text}, {korrelation_text} (Korrelation {korrelation:.2f}, "
        f"{ergebnis.fenster_tage_beta}-Tage-Fenster, {ergebnis.n_datenpunkte} Datenpunkte)."
        f"{relativstaerke_text} Mehrmonatiger Hintergrundwert - KEINE Aussage über die "
        "nächsten Tage, keine Grundlage für eine kurzfristige Entscheidung."
    )

    return {
        "beta": beta,
        "korrelation": korrelation,
        "relativstaerke_pct": ergebnis.relativstaerke_pct,
        "fenster_tage_beta": ergebnis.fenster_tage_beta,
        "fenster_tage_relativstaerke": ergebnis.fenster_tage_relativstaerke,
        "n_datenpunkte": ergebnis.n_datenpunkte,
        "einordnung": einordnung,
    }
