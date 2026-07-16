"""Hebel-Risiko-/Positionsgroessen-/Liquidationspreis-Formeln (RM-1/RM-10/RM-11/
AZ-7, 2026-07-14, siehe docs/hebel_positionsformel.md fuer die volle Herleitung
+ Kalibrierung gegen 311 echte Bitpanda-Margin-Positionen).

Bewusst ein EIGENES Modul, nicht in risk_gate.py gefaltet - andere Schwellenwerte
und ein anderes Timing als Spot (RM-1 fuer Hebel ist 1%, nicht die Spot-2%; die
Liquidationspreis-Formel hat eine Zeitkomponente, die es bei Spot nicht gibt).
`CRV_MINIMUM` wird trotzdem aus risk_gate.py importiert statt dupliziert - die
CRV-Pflicht selbst bleibt bei 2.0, unveraendert gegenueber Spot (Nutzer-
Entscheidung 2026-07-14: die hebel-spezifischen Zusatzrisiken sind bereits an
der Quelle adressiert, siehe unten - eine zusaetzlich verschaerfte CRV waere
Risiko-Stapelung statt gezielter Loesung).

Gleiches Grundprinzip wie risk_gate.py: pre_check_hebel() laeuft VOR dem
LLM-Call (harte Obergrenze als Fakt), post_check_hebel() erzwingt danach
dieselben Regeln nochmal deterministisch - das Modell wird nie blind vertraut."""
from __future__ import annotations

from dataclasses import dataclass, field

from agent.krypto.risk_gate import CRV_MINIMUM

RICHTUNG_LONG = "LONG"
RICHTUNG_SHORT = "SHORT"
ZWEIG_KONTRA = "kontra"

_HEBEL_ACTIONS_MIT_HEBEL = ("ERÖFFNEN", "NACHKAUFEN", "HEBEL_ERHÖHEN")


def estimate_liquidation_price(
    entry_price: float, hebel: float, richtung: str,
    days_held: float = 0.0, funding_rate_daily_pct: float = 0.18,
    sicherheitsmarge_relativ: float = 0.0,
) -> float:
    """Konservative Schaetzung (Bitpanda veroeffentlicht keine exakte Formel) -
    soll Liquidation eher zu frueh als zu spaet anzeigen (sichere Richtung fuer
    ein Warnsystem). `days_held=0` bei der Empfehlung selbst (Position existiert
    noch nicht, keine Haltedauer zu raten) - `days_held` > 0 nur, sobald eine
    Position real offen ist und die echten verstrichenen Tage bekannt sind.

    2026-07-16 KORRIGIERT: die urspruengliche Formel ignorierte den unbekannten
    Maintenance-Margin-Puffer komplett (Liquidation erst bei Eigenkapital=0) -
    live an einer echten offenen LINK-Position gegengeprueft: Bitpandas
    tatsaechlicher Liquidationspreis lag ca. 7% HOEHER (fuer einen LONG - loest
    frueher aus) als die alte Schaetzung, also GENAU in die falsche, unsichere
    Richtung (weniger statt mehr Sicherheitsabstand als angezeigt). Rueck-
    rechnung aus diesem echten Fall ergab eine implizite Wartungsmarge von
    ~6,5% Eigenkapitalanteil - mit dieser Zahl reproduziert die Formel unten
    (Long, Tag 0) den echten Bitpanda-Wert fast exakt (6,3505 vs. real 6,3515).

    Fix: `sicherheitsmarge_relativ` (config risiko.hebel.liquidations_
    sicherheitsmarge_relativ, aktuell 0.175 - bisher nur in max_safe_hebel()
    verwendet) wird jetzt als Naeherung fuer diese Wartungsmarge auch hier
    eingerechnet, indem der komplette Hebel-Abstand-Term durch (1 -
    sicherheitsmarge_relativ) geteilt wird (Long) bzw. durch (1 +
    sicherheitsmarge_relativ) (Short) - mathematisch hergeleitet aus Eigen-
    kapital(t)/Positionswert(t) = Wartungsmarge bei Liquidation, nicht nur
    eine multiplikative Naeherung. Da der konfigurierte Wert (17,5%) groesser
    ist als die empirisch beobachtete echte Marge (~6,5%), bleibt die Schaetzung
    bewusst UEBERKONSERVATIV (zeigt Liquidation noch etwas frueher an, als der
    eine beobachtete Realfall nahelegt) - passend zur dokumentierten Absicht.
    Default 0.0 (kein Puffer, altes Verhalten) fuer Rueckwaertskompatibilitaet,
    falls kein Wert uebergeben wird."""
    zeit_faktor = days_held * (funding_rate_daily_pct / 100)
    hebel_abstand = 1 / hebel
    if richtung == RICHTUNG_SHORT:
        return entry_price * (1 + hebel_abstand - zeit_faktor) / (1 + sicherheitsmarge_relativ)
    return entry_price * (1 - hebel_abstand + zeit_faktor) / (1 - sicherheitsmarge_relativ)


def max_safe_hebel(stop_loss_distance_pct: float, sicherheitsmarge_relativ: float) -> float:
    """RM-11: der Hebel muss so gewaehlt sein, dass zwischen Stop-Loss und
    geschaetztem Liquidationspreis ein Sicherheitsabstand bleibt - sonst greift
    Bitpandas Zwangsliquidation, BEVOR der eigene Stop-Loss ueberhaupt ausloesen
    kann. `sicherheitsmarge_relativ` (z.B. 0.175) ist ein relativer Puffer auf
    den reinen 1/Hebel-Abstand, keine additive Prozentzahl."""
    return (1 - sicherheitsmarge_relativ) / (stop_loss_distance_pct / 100)


@dataclass
class HebelPreCheckResult:
    hebel_erlaubt: bool
    veto_reason: str | None
    risikobetrag_usd: float | None
    max_sicherer_hebel: float | None
    config_max_hebel: float
    az7_kontra_deckel_aktiv: bool
    checks: list[str] = field(default_factory=list)


def pre_check_hebel(
    asset, account_equity_usd: float, stop_loss_distance_pct: float | None,
    regime_result, config: dict, trigger_zweig: str | None,
) -> HebelPreCheckResult:
    """Laeuft VOR dem LLM-Call. Berechnet Risikobetrag (RM-1-Aequivalent, 1%
    statt Spot-2%) + maximal sicheren Hebel aus der Stop-Loss-Distanz. AZ-7:
    kompletter Deckel auf 0 bei Extrem-Krise-Regime (gilt fuer BEIDE Zweige),
    zusaetzlicher Konservativ-Faktor NUR bei trigger_zweig == 'kontra' (Sanity-
    Check-Korrektur 2026-07-14 - AZ-7 stammt aus dem antizyklischen Kontext,
    ein bestaetigter Trend ist eine andere Risikokategorie)."""
    checks: list[str] = []
    hebel_cfg = config["risiko"]["hebel"]

    if regime_result.regime == "krise_extrem":
        checks.append("AZ-7: Hebel komplett deaktiviert (Regime krise_extrem)")
        return HebelPreCheckResult(
            hebel_erlaubt=False,
            veto_reason="Hebel im Regime 'krise_extrem' komplett deaktiviert (AZ-7)",
            risikobetrag_usd=None, max_sicherer_hebel=0.0,
            config_max_hebel=hebel_cfg["max_hebel"], az7_kontra_deckel_aktiv=False,
            checks=checks,
        )

    risikobetrag_usd = account_equity_usd * hebel_cfg["risiko_pro_trade_prozent_hebel"] / 100
    checks.append(f"RM-1 (Hebel, {hebel_cfg['risiko_pro_trade_prozent_hebel']}%): Risikobetrag {risikobetrag_usd:.2f} USD")

    max_sicherer_hebel = None
    if stop_loss_distance_pct is not None and stop_loss_distance_pct > 0:
        max_sicherer_hebel = max_safe_hebel(
            stop_loss_distance_pct, hebel_cfg["liquidations_sicherheitsmarge_relativ"],
        )
        az7_kontra_aktiv = trigger_zweig == ZWEIG_KONTRA
        if az7_kontra_aktiv:
            max_sicherer_hebel *= hebel_cfg["kontra_konservativ_faktor"]
            checks.append(
                f"AZ-7-Kontra-Bremse aktiv (Faktor {hebel_cfg['kontra_konservativ_faktor']}): "
                f"max. sicherer Hebel gedaempft auf {max_sicherer_hebel:.2f}x"
            )
        else:
            checks.append(f"RM-11: max. sicherer Hebel {max_sicherer_hebel:.2f}x (Stop-Distanz {stop_loss_distance_pct:.2f}%)")
    else:
        checks.append("RM-11: max. sicherer Hebel nicht berechenbar (keine Stop-Loss-Distanz)")

    return HebelPreCheckResult(
        hebel_erlaubt=True, veto_reason=None, risikobetrag_usd=risikobetrag_usd,
        max_sicherer_hebel=max_sicherer_hebel, config_max_hebel=hebel_cfg["max_hebel"],
        az7_kontra_deckel_aktiv=trigger_zweig == ZWEIG_KONTRA, checks=checks,
    )


def post_check_hebel(parsed: dict, pre_result: HebelPreCheckResult, regime_result, config: dict) -> dict:
    """Nimmt die bereits schema-validierte LLM-Antwort und erzwingt AZ-7/RM-1/
    RM-11/CRV noch einmal deterministisch, analog risk_gate.py::post_check().
    Haengt zusaetzlich die rein deterministisch berechneten Felder an
    (hebel_final, liquidationspreis_geschaetzt, eigenkapitalbedarf,
    ausfuehrbarkeit_hinweis) - die KI sieht/entscheidet diese Werte nicht."""
    result = dict(parsed)
    risk_veto = False
    risk_veto_reason = None
    action = str(result.get("action", "")).upper()
    richtung = str(result.get("richtung", "")).upper()

    if not pre_result.hebel_erlaubt:
        risk_veto = True
        risk_veto_reason = pre_result.veto_reason
        action = "HALTEN"

    if action in _HEBEL_ACTIONS_MIT_HEBEL and pre_result.hebel_erlaubt:
        entry = result.get("entry") or {}
        stop = result.get("stop_loss") or {}
        take = result.get("take_profit") or {}
        entry_von, entry_bis = entry.get("usd_von"), entry.get("usd_bis")
        stop_von, stop_bis = stop.get("usd_von"), stop.get("usd_bis")
        take_von, take_bis = take.get("usd_von"), take.get("usd_bis")

        if None not in (entry_von, entry_bis, stop_von, stop_bis, take_von, take_bis):
            entry_mid = (entry_von + entry_bis) / 2
            # CRV unveraendert 2.0 (Nutzer-Entscheidung 2026-07-14) - Short spiegelbildlich
            if richtung == RICHTUNG_SHORT:
                crv = (entry_mid - take_bis) / (stop_bis - entry_mid) if stop_bis > entry_mid else None
            else:
                crv = (take_von - entry_mid) / (entry_mid - stop_von) if entry_mid > stop_von else None

            if crv is None or crv < CRV_MINIMUM:
                risk_veto = True
                reason = f"CRV {crv} unter Minimum {CRV_MINIMUM} (unveraendert ggü. Spot)"
                risk_veto_reason = f"{risk_veto_reason}; {reason}" if risk_veto_reason else reason
                action = "HALTEN"
            else:
                hebel_vorschlag = result.get("hebel_vorschlag")
                deckel = [pre_result.config_max_hebel]
                if pre_result.max_sicherer_hebel is not None:
                    deckel.append(pre_result.max_sicherer_hebel)
                hebel_final = min([hebel_vorschlag] + deckel) if hebel_vorschlag is not None else None

                if hebel_final is not None and hebel_vorschlag is not None and hebel_final < hebel_vorschlag:
                    result["hebel_korrektur_hinweis"] = (
                        f"KI schlug {hebel_vorschlag:.2f}x vor, auf {hebel_final:.2f}x reduziert "
                        f"(Deckel: max. sicherer Hebel/Config-Maximum/AZ-7)."
                    )
                else:
                    result["hebel_korrektur_hinweis"] = None

                result["hebel_final"] = hebel_final
                if hebel_final is not None and hebel_final > 0 and entry_mid > 0:
                    result["liquidationspreis_geschätzt"] = estimate_liquidation_price(
                        entry_mid, hebel_final, richtung,
                        sicherheitsmarge_relativ=config["risiko"]["hebel"]["liquidations_sicherheitsmarge_relativ"],
                    )
                    positionsgroesse = pre_result.risikobetrag_usd / (
                        abs(entry_mid - stop_von) / entry_mid
                    ) if pre_result.risikobetrag_usd and entry_mid != stop_von else None
                    result["eigenkapitalbedarf"] = (
                        positionsgroesse / hebel_final if positionsgroesse is not None else None
                    )
        else:
            risk_veto = True
            reason = "Zonen unvollständig - Hebel-Empfehlung kann nicht sicher berechnet werden"
            risk_veto_reason = f"{risk_veto_reason}; {reason}" if risk_veto_reason else reason
            action = "HALTEN"

    result["ausführbarkeit_hinweis"] = (
        "Aktuell nicht über Bitpanda ausführbar (Short-Positionen werden dort noch nicht unterstützt)."
        if richtung == RICHTUNG_SHORT else None
    )

    result["action"] = action
    result["_risk_veto"] = risk_veto
    result["_risk_veto_reason"] = risk_veto_reason
    return result
