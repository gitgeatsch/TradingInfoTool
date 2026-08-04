"""E2E-Pruefung der stufenlosen CRV-Abstufung, Spot (2026-08-04).

Geprueft wird post_check() SELBST, nicht nur die Formel. Grund steht in
Basisinfos/Test_und_Verifikationsmethodik.md 1.4 und im Vorfall vom 02.08.:
zwoelf gruene Tests der Hilfsfunktion liessen einen Produktionsbug durch, weil
niemand die AUFRUFENDE Funktion getestet hatte.

Sechs Pruefungen:
  1. Abstufung ist monoton in CRV
  2. Spreizung trifft den konfigurierten Wert (5x)
  3. E2E: der Deckel erscheint tatsaechlich in der post_check()-Ausgabe
  4. SICHERHEITSEIGENSCHAFT: die Position wird nie GROESSER als vorher
  5. Abschaltbar ueber Config, ohne Codeaenderung
  6. Der Hebel bleibt unberuehrt

Lauf: python pruefe_crv_positionsgroesse.py
"""
from __future__ import annotations

import copy
import sys

import config as config_module
from agent.krypto.risk_gate import CRV_MINIMUM, RiskPreCheckResult, post_check

fehler: list[str] = []


def pruefe(name: str, bedingung: bool, info: str = "") -> None:
    print(f"  {'OK  ' if bedingung else 'FEHL'}  {name}{('   ' + info) if info else ''}")
    if not bedingung:
        fehler.append(name)


class Regime:
    regime = "neutral"
    begruendung = ""


def basis_config() -> dict:
    c = copy.deepcopy(config_module.load_config())
    # Profil fuer das Testregime sicherstellen
    c.setdefault("regime", {}).setdefault("profile", {}).setdefault(
        "neutral", {"min_konfidenz_prozent": 50})
    return c


def signal(crv: float, entry: float = 100.0) -> dict:
    """Ein bullisches Spot-Signal mit exakt diesem CRV.

    Stop 5 % unter Entry, Ziel entsprechend dem gewuenschten CRV darueber.
    Konfidenz hoch gewaehlt, damit die Konfidenz-Skalierung nicht bindet und
    der CRV-Deckel isoliert sichtbar wird."""
    # ZONENFORMAT: post_check() liest result["entry"]["usd_von"], NICHT
    # result["entry_usd"]["von"]. Die erste Fassung dieses Tests nutzte die
    # falsche Schachtelung - dadurch blieb `crv` None, KEIN einziger
    # CRV-Deckel griff, und der Test meldete "Spreizung 1,00x" als
    # Codefehler. Der Fehler lag im Test. Genau deshalb steht in der
    # Methodik, dass die aufrufende Funktion echt aufgerufen werden muss:
    # eine nachgebaute Eingabe kann am Vertrag vorbeigehen.
    risiko = entry * 0.05
    return {
        "action": "KAUFEN",
        "confidence_pct": 95,
        "entry": {"usd_von": entry, "usd_bis": entry},
        "stop_loss": {"usd_von": entry - risiko, "usd_bis": entry - risiko},
        "take_profit": {"usd_von": entry + risiko * crv,
                        "usd_bis": entry + risiko * crv},
        "position_size": {"usd": 10000.0, "eur": 9200.0},
        "short_reasoning": "Test",
    }


def pre() -> RiskPreCheckResult:
    """Vorbefund mit grosszuegiger Obergrenze - der Deckel soll binden.

    Stop-Abstand 5 % passend zum Testsignal; sonst korrigiert
    _rm1_exakt_und_positionszahl() die Basis und der Vergleich verschoebe sich."""
    return RiskPreCheckResult(
        kauf_erlaubt=True, veto_reason=None,
        max_position_size_usd=1000.0, max_position_size_eur=920.0,
        stop_loss_distance_pct=5.0,
        cash_reserve_pct_current=50.0, allocation_pct_current=5.0,
        small_cap_budget_pct_applicable=None,
        total_value_usd=100000.0,
    )


def groesse(crv: float, cfg: dict) -> tuple[float | None, bool, str]:
    """(Positionsgroesse USD, veto, Deckelgrund) aus einem echten post_check()."""
    erg = post_check(signal(crv), pre(), Regime(), cfg)
    parsed = erg.get("parsed") if isinstance(erg.get("parsed"), dict) else erg
    ps = (parsed.get("position_size") or {}) if isinstance(parsed, dict) else {}
    grund = ""
    for schluessel in ("positionsgroesse_deckel_grund", "clamp_note",
                       "positionsgroesse_hinweis"):
        wert = (parsed or {}).get(schluessel) or erg.get(schluessel)
        if wert:
            grund = str(wert)
            break
    return ps.get("usd"), bool(erg.get("risk_veto")), grund


def main() -> int:
    cfg = basis_config()
    spreizung = cfg["risiko"].get("crv_positionsgroesse_spreizung")
    voll_ab = cfg["risiko"].get("crv_positionsgroesse_voll_ab")
    print("=" * 74)
    print(f"CRV-ABSTUFUNG SPOT   Spreizung {spreizung}   volle Groesse ab CRV {voll_ab}")
    print("=" * 74)
    if not spreizung or not voll_ab:
        print("Config-Schluessel fehlen - Abbruch.")
        return 1

    print()
    print(f"  {'CRV':>6s} {'Groesse USD':>12s} {'Anteil':>8s}  Veto")
    werte: list[tuple[float, float | None]] = []
    for crv in (2.0, 2.4, 3.0, 4.0, 5.0, 6.0, 8.0):
        g, veto, _grund = groesse(crv, cfg)
        werte.append((crv, g))
        anteil = f"{g / 1000.0 * 100:6.0f} %" if g else "   --  "
        print(f"  {crv:6.1f} {(g if g is not None else 0):12.1f} {anteil:>8s}  "
              f"{'JA' if veto else 'nein'}")

    gueltig = [(c, g) for c, g in werte if g is not None]
    # 1. Monotonie
    monoton = all(a[1] <= b[1] + 1e-9 for a, b in zip(gueltig, gueltig[1:]))
    print()
    pruefe("Abstufung steigt monoton mit dem CRV", monoton)

    # 2. Spreizung
    if len(gueltig) >= 2:
        klein = min(g for _c, g in gueltig)
        gross = max(g for _c, g in gueltig)
        ist = gross / klein if klein else 0.0
        pruefe("Spreizung trifft den konfigurierten Wert",
               abs(ist - spreizung) < 0.35, f"ist {ist:.2f}x, soll {spreizung:.1f}x")

    # 3. E2E - greift der Deckel ueberhaupt in post_check()?
    g_klein, _v, _grund = groesse(CRV_MINIMUM, cfg)
    pruefe("Deckel greift in post_check() (nicht nur in der Formel)",
           g_klein is not None and g_klein < 1000.0 - 1e-9,
           f"bei CRV {CRV_MINIMUM}: {g_klein:.1f} statt 1000,0 USD")

    # 4. SICHERHEIT: nie groesser als ohne die Aenderung
    aus = copy.deepcopy(cfg)
    aus["risiko"]["crv_positionsgroesse_spreizung"] = 1.0
    schlimmster = None
    for crv in (2.0, 2.4, 3.0, 4.0, 6.0, 10.0):
        mit, _v1, _g1 = groesse(crv, cfg)
        ohne, _v2, _g2 = groesse(crv, aus)
        if mit is None or ohne is None:
            continue
        if mit > ohne + 1e-9:
            schlimmster = (crv, mit, ohne)
            break
    pruefe("Position wird NIE groesser als vorher (Bauform-Sicherheit)",
           schlimmster is None,
           "" if schlimmster is None else
           f"CRV {schlimmster[0]}: {schlimmster[1]:.1f} > {schlimmster[2]:.1f}")

    # 5. Abschaltbar
    g_aus, _v, _grund = groesse(3.0, aus)
    g_an, _v2, _grund2 = groesse(3.0, cfg)
    pruefe("ueber Config abschaltbar, ohne Codeaenderung",
           g_aus is not None and g_an is not None and g_aus > g_an,
           f"aus {g_aus:.1f} gegen an {g_an:.1f} USD")

    # 6. Hebel unberuehrt
    import agent.krypto.hebel_risk_gate as hebel
    quelle = open(hebel.__file__, encoding="utf-8").read()
    pruefe("Hebel-Modul kennt die Spot-Abstufung nicht",
           "crv_positionsgroesse_spreizung" not in quelle,
           "gegenlaeufiger Befund: Hebel behaelt das Gate (SQN 3,25 gegen 1,25)")

    print()
    if fehler:
        print(f"FEHLGESCHLAGEN: {fehler}")
        return 1
    print("Alle Pruefungen bestanden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
