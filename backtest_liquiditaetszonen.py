# -*- coding: utf-8 -*-
"""Phase A (2026-07-24): validiert das Liquiditaetszonen-Konzept (Stufe 1,
Marketmaker-/Smart-Money-Theorie) gegen echte historische Kursdaten MIT
Kontrollgruppe - reine Erkenntnisphase, KEINE Vorentscheidung fuer Stufe 2
(Order Blocks/Fair Value Gaps). Ergebnis ist offen (Nutzer-Vorgabe).

Kernfrage: sagt die Naehe zu einer noch NICHT gefegten Liquiditaetszone
(Swing-Extrema mit >= N Beruehrungen) eine echte Kursbewegung IN DIE
ERWARTETE RICHTUNG voraus (weg von der Zone), oder ist die beobachtete
Trefferquote nicht besser als eine Zufalls-Baseline?

Methodik (bewusste Vorkehrungen gegen ein "totes Pferd"):
- Ereignis- statt tagesbasiert: nur der ERSTE Tag, an dem der Kurs in die
  Naehe einer ungefegten Zone kommt, zaehlt als Ereignis (Flanken-Trigger,
  analog agent/krypto/backtesting.py) - sonst blaehen viele Folgetage an
  derselben Zone die Stichprobe kuenstlich auf.
- Kontrollgruppe (KEIN Vergleich ohne sie): der erste Tag, an dem der Kurs
  NICHT mehr in der Naehe irgendeiner Zone ist (Gegenflanke, dieselbe
  Ereignis-Logik). Fuer Kontroll-Ereignisse wird die "erwartete Richtung"
  deterministisch zufaellig (fixer Seed) zugeordnet - simuliert die
  Nullhypothese "Richtung haengt nicht von Zonen-Naehe ab".
- Kein Lookahead-Bias bei der Zonen-Berechnung: exakt dieselben Tag-fuer-Tag-
  Slices wie in backtesting.py, dieselbe build_technical_snapshot()/
  liquiditaetszonen_fakt()-Logik wie live (eine Quelle der Wahrheit, keine
  zweite, potenziell driftende Zonen-Berechnung).
- Ein einziger, vorab festgelegter Test (Bewegungs-Schwelle, Vorwaerts-
  Fenster) statt mehrerer Parameter-Varianten, aus denen man sich im
  Nachhinein die guenstigste aussucht (kein p-Hacking).

Bekannte Grenzen (P-10, keine Ueberzeugungskraft vortaeuschen, die nicht da
ist):
- Alle Krypto-Symbole sind untereinander stark korreliert (gemeinsame
  Marktbewegungen, insbesondere mit BTC) - die Stichprobe ist NICHT so
  unabhaengig, wie die reine Symbolanzahl suggeriert.
- Zeitraum ist ein einzelner ~2-Jahres-Marktzyklus (2024-07 bis 2026-07,
  einzige durchgehend verfuegbare Historie) - ein Nullergebnis heisst "kein
  grosser Effekt in DIESEM Zeitraum gefunden", nicht "fuer alle Zeit
  widerlegt". Ein positives Ergebnis ist ebenso auf diesen Zeitraum
  beschraenkt, bis es sich in weiterer Historie reproduziert.
- Reine Analysefunktion, kein Seiteneffekt auf Live-Verhalten."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

import numpy as np

import config as config_module
import database.db as db
from agent.krypto.liquidity_zones import liquiditaetszonen_fakt
from indicators.calculations import build_technical_snapshot

MIN_LOOKBACK_TAGE = 210  # identisch zu backtesting.py (EMA-200 + Puffer)
FORWARD_FENSTER_TAGE = 10
BEWEGUNG_SCHWELLE_RELATIV = 0.03  # 3% - Reversal-Mindestgroesse
ZUFALLS_SEED = 42  # fixe Kontrollgruppen-Richtungszuordnung, reproduzierbar

# Symbole mit ausreichender durchgehender Historie (>= 2 Jahre) fuer diesen
# Backtest - kuerzere Historien (z.B. HYPE, CAT, ASTER) bewusst ausgeschlossen,
# statt sie mit zu wenig Lookback-Puffer zu verzerren.
SYMBOLE = (
    "BTC", "ETH", "SOL", "NEAR", "AVAX", "LINK", "SUI", "TAO", "ONDO", "INJ",
    "ALGO", "APT", "FLOKI", "IMX", "SEI", "W",
)


@dataclass
class Ereignis:
    symbol: str
    typ: str  # "treatment" | "control"
    datum: str
    seite: str | None  # "buyside" | "sellside" | None (nur control)
    erwartete_richtung: str  # "hoch" | "runter"
    treffer: bool


@dataclass
class Ergebnis:
    ereignisse: list[Ereignis] = field(default_factory=list)

    def gruppe(self, typ: str) -> list[Ereignis]:
        return [e for e in self.ereignisse if e.typ == typ]

    def trefferquote(self, typ: str) -> tuple[int, int, float | None]:
        gruppe = self.gruppe(typ)
        n = len(gruppe)
        if n == 0:
            return 0, 0, None
        treffer = sum(1 for e in gruppe if e.treffer)
        return treffer, n, treffer / n


def _zwei_proportionen_z_test(x1: int, n1: int, x2: int, n2: int) -> tuple[float, float] | None:
    """Zweistichproben-Anteilsvergleich (Normalapproximation) - bewusst ohne
    scipy-Abhaengigkeit, reine Standardformel. Gibt (z, p_zweiseitig) zurueck,
    None falls nicht berechenbar (leere Gruppe)."""
    if n1 == 0 or n2 == 0:
        return None
    p1, p2 = x1 / n1, x2 / n2
    p_pool = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    if se == 0:
        return None
    z = (p1 - p2) / se
    p_wert = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    return z, p_wert


def _future_erreicht_richtung(closes: np.ndarray, start_idx: int, fenster: int, richtung: str, schwelle: float) -> bool:
    basis = closes[start_idx]
    future = closes[start_idx + 1: start_idx + 1 + fenster]
    if len(future) < fenster:
        return False
    if richtung == "hoch":
        return bool(np.max(future) >= basis * (1 + schwelle))
    return bool(np.min(future) <= basis * (1 - schwelle))


def run(conn, symbole: tuple[str, ...] = SYMBOLE) -> Ergebnis:
    config_dict = config_module.load_config()
    rng = random.Random(ZUFALLS_SEED)
    ergebnis = Ergebnis()

    for symbol in symbole:
        ohlc_history = db.get_ohlc_history(conn, symbol, "USD")
        if len(ohlc_history) < MIN_LOOKBACK_TAGE + FORWARD_FENSTER_TAGE + 1:
            print(f"  {symbol}: zu wenig Historie ({len(ohlc_history)} Tage), uebersprungen")
            continue

        dates_all = [p.date for p in ohlc_history]
        closes_all = np.array([p.close for p in ohlc_history], dtype=float)
        end_idx = len(dates_all) - 1 - FORWARD_FENSTER_TAGE

        war_nahe = False
        n_treatment = n_control = 0
        idx = MIN_LOOKBACK_TAGE
        while idx <= end_idx:
            closes_slice = closes_all[: idx + 1]
            dates_slice = np.array(dates_all[: idx + 1])
            ohlc_slice = ohlc_history[: idx + 1]
            snapshot = build_technical_snapshot(closes_slice, dates_slice, ohlc_slice)
            current_price = float(closes_all[idx])

            fakt = liquiditaetszonen_fakt(snapshot, current_price, config_dict)
            ist_nahe = bool(fakt and fakt["in_naehe_ungefegter_zone"])

            if ist_nahe and not war_nahe:
                seite = fakt["seite"]
                richtung = "runter" if seite == "buyside" else "hoch"
                treffer = _future_erreicht_richtung(
                    closes_all, idx, FORWARD_FENSTER_TAGE, richtung, BEWEGUNG_SCHWELLE_RELATIV,
                )
                ergebnis.ereignisse.append(Ereignis(symbol, "treatment", dates_all[idx], seite, richtung, treffer))
                n_treatment += 1
            elif not ist_nahe and war_nahe:
                richtung = rng.choice(("hoch", "runter"))
                treffer = _future_erreicht_richtung(
                    closes_all, idx, FORWARD_FENSTER_TAGE, richtung, BEWEGUNG_SCHWELLE_RELATIV,
                )
                ergebnis.ereignisse.append(Ereignis(symbol, "control", dates_all[idx], None, richtung, treffer))
                n_control += 1

            war_nahe = ist_nahe
            idx += 1

        print(f"  {symbol}: {n_treatment} Treatment-, {n_control} Control-Ereignisse")

    return ergebnis


def haupt() -> None:
    conn = db.get_connection()
    print(f"Lade Historie fuer {len(SYMBOLE)} Symbole...\n")
    ergebnis = run(conn)

    print("\n=== Ergebnis ===")
    x_t, n_t, q_t = ergebnis.trefferquote("treatment")
    x_c, n_c, q_c = ergebnis.trefferquote("control")
    print(f"Treatment (nahe ungefegter Zone): {x_t}/{n_t} Treffer" + (f" ({q_t:.1%})" if q_t is not None else ""))
    print(f"Control   (Zufalls-Baseline):     {x_c}/{n_c} Treffer" + (f" ({q_c:.1%})" if q_c is not None else ""))

    test = _zwei_proportionen_z_test(x_t, n_t, x_c, n_c)
    if test is not None:
        z, p_wert = test
        print(f"\nZwei-Proportionen-Z-Test: z={z:.2f}, p={p_wert:.4f}")
        if p_wert < 0.05:
            print("=> Unterschied statistisch signifikant (p<0.05) bei diesem Test/Zeitraum.")
        else:
            print("=> KEIN statistisch signifikanter Unterschied gefunden (p>=0.05).")
    else:
        print("\nZ-Test nicht berechenbar (zu wenige Ereignisse in einer Gruppe).")

    print("\n--- Aufschluesselung Treatment nach Zonen-Seite ---")
    for seite in ("buyside", "sellside"):
        teilgruppe = [e for e in ergebnis.gruppe("treatment") if e.seite == seite]
        n = len(teilgruppe)
        treffer = sum(1 for e in teilgruppe if e.treffer)
        quote = f"{treffer / n:.1%}" if n else "-"
        print(f"  {seite}: {treffer}/{n} ({quote})")

    print(
        "\nHinweis: Krypto-Symbole sind untereinander stark korreliert, Zeitraum "
        "ist ein einzelner ~2-Jahres-Marktzyklus (2024-07 bis 2026-07) - siehe "
        "Modul-Docstring fuer die vollstaendigen Einschraenkungen."
    )


if __name__ == "__main__":
    haupt()
