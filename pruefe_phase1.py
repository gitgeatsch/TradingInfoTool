# -*- coding: utf-8 -*-
"""GEGENPRUEFUNG PHASE I an ECHTEN Reihen, nicht an Testdaten (16.08.2026).

`pruefe_pakete.py` prueft die vier Ergaenzungen an konstruierten Kerzen - das
sagt, ob die Logik stimmt. Es sagt NICHT, ob sie bei UNSEREN Assets greift.
Genau dieser Unterschied hat heute zugeschlagen: die Abgrenzung des
Sektorbezugs stand auf `assetklasse == "etf"` und haette nie gegriffen, weil
der Aufrufer die GRUPPE uebergibt. Kein Test schlug an - erst das Rendern.

Dieses Skript rendert den Faktensatz fuer JEDES Symbol der Watchlist und
beantwortet vier Fragen mit Ja oder Nein:

    1  Steht der Liquidationsabstand in JEDEM Hebel-Faktensatz und in KEINEM
       anderen?
    2  Ist die Finanzierung aus allen Spot-Faktensaetzen verschwunden?
    3  Bekommen GENAU die Assets einen Luecken-Satz, die in der
       Bestandserhebung (Umbauplan 34.6) unvollstaendig waren?
    4  Bekommen GENAU die Themen-ETF einen Sektorbezug - und die beiden
       Absicherungen NICHT?

OHNE NETZ: `mit_finanzierung=False`. Der Finanzierungsblock wird damit auch
beim Hebel leer bleiben; dass er dort ueberhaupt entsteht, prueft
`pruefe_pakete.py` am Einzelfall. Hier geht es um die ABGRENZUNG.

NUR LESEND. Alle Verbindungen laufen ueber `mode=ro`.

AUFRUF:  python pruefe_phase1.py [--db PFAD]
"""
from __future__ import annotations

import argparse
import sys

# Was die Bestandserhebung vom 16.08. als unvollstaendig gefunden hat
# (Umbauplan 34.6) - als ORIENTIERUNG, nicht als Sollwert.
#
# ⚠️ MEINE ERSTE FASSUNG HAT GENAU DAS VERWECHSELT und gegen diese Liste
# geprueft. Sie ist an einer anderen Datenbank erhoben worden: auf dem
# Entwicklungsrechner fehlen den vier Rohstoff-Zertifikaten, 3QSS und X136 die
# Reihen ganz, also kann dort kein Luecken-Satz entstehen - und die Pruefung
# meldete einen Fehler, den es nicht gab. Umgekehrt fand sie drei Assets, die
# in 34.6 gar nicht vorkommen (CAT, HYPE, MON), und haette sie als "zuviel"
# verworfen.
#
# Ein Sollwert aus einer FREMDEN Datenlage ist kein Sollwert. Geprueft wird
# deshalb gegen die Reihe selbst - unabhaengig nachgerechnet, nicht aus
# derselben Funktion geholt.
ERWARTET_LUECKE = {"3QSS", "OD7C", "OD7H", "OD7L", "OD7N", "X136"}

# Dieselbe Grenze wie in `lagebeschreibung._luecken` - hier BEWUSST noch
# einmal, weil eine Pruefung, die ihren Sollwert vom Prueflung importiert,
# nur bestaetigt, dass er sich selbst gleicht.
MINDEST_HANDELSTAGE = 250


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="data/tradinginfotool.db")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    from agent import assetklassen as AK
    from agent import rollen_eingabe as RE
    from backtest_llm1_historisch import lade_reihen_aus_db

    reihen = lade_reihen_aus_db(a.db)
    zeilen, fehler = [], []
    mit_geometrie, mit_finanz, mit_ref, mit_luecke = set(), set(), set(), set()
    soll_umsatz, soll_kurz = set(), set()
    abweichung_umsatz, abweichung_kurz = [], []
    ohne_reihe = []

    for gruppe, instrument, symbole in AK.laeufe():
        for sym in symbole:
            r = reihen.get(sym)
            if not r:
                ohne_reihe.append(f"{gruppe}/{instrument} {sym}")
                continue
            idx = len(r) - 1
            bloecke: dict = {}
            try:
                RE.baue_fall(symbol=sym, reihe=r, index=idx,
                             reihen={sym: r}, db=a.db, mit_finanzierung=False,
                             instrument=instrument, assetklasse=gruppe,
                             bloecke_ziel=bloecke)
            except Exception as exc:                         # noqa: BLE001
                fehler.append(f"{gruppe}/{instrument} {sym}: "
                              f"{type(exc).__name__}: {str(exc)[:70]}")
                continue
            schluessel = f"{sym}/{instrument}"
            if bloecke.get("hebelgeometrie"):
                mit_geometrie.add(schluessel)
            if bloecke.get("finanzierung"):
                mit_finanz.add(schluessel)
            if bloecke.get("referenz"):
                mit_ref.add(sym)
            if bloecke.get("luecken"):
                mit_luecke.add(sym)
                zeilen.append((gruppe, sym, bloecke["luecken"]))
            # UNABHAENGIG NACHGERECHNET, aus der Reihe statt aus dem Block.
            texte = " ".join(bloecke.get("luecken") or [])
            if all(not k.volume for k in r[:idx + 1]):
                soll_umsatz.add(sym)
                if "KEIN Umsatz ausgewiesen" not in texte:
                    abweichung_umsatz.append(
                        f"{sym}: kein Umsatzwert ueber null in der Reihe, "
                        f"aber kein Luecken-Satz")
            if len(r[:idx + 1]) < MINDEST_HANDELSTAGE:
                soll_kurz.add(sym)
                if "Handelstage" not in texte:
                    abweichung_kurz.append(
                        f"{sym}: nur {len(r)} Handelstage, aber kein "
                        f"Luecken-Satz")

    hebel_alle = {f"{s}/hebel" for g, i, syms in AK.laeufe()
                  if i == "hebel" for s in syms if reihen.get(s)}
    themen = {s for g, i, syms in AK.laeufe() if g == "themen_etf"
              for s in syms if reihen.get(s)}
    hedge = {s for g, i, syms in AK.laeufe() if g == "hedge" for s in syms}

    def urteil(name: str, ok: bool, zusatz: str = "") -> bool:
        print(f"  {'OK  ' if ok else 'FEHL'}  {name}")
        if zusatz:
            print(f"          {zusatz}")
        return ok

    print("=" * 74)
    print(f"GEGENPRUEFUNG PHASE I   ({a.db})")
    print("=" * 74)
    alles = True

    print("\n1. LIQUIDATIONSABSTAND")
    alles &= urteil("steht in JEDEM Hebel-Faktensatz",
                    mit_geometrie == hebel_alle,
                    f"fehlt: {sorted(hebel_alle - mit_geometrie)}"
                    if hebel_alle - mit_geometrie else "")
    alles &= urteil("und in KEINEM anderen",
                    not (mit_geometrie - hebel_alle),
                    f"zuviel: {sorted(mit_geometrie - hebel_alle)}")

    print("\n2. FINANZIERUNG")
    alles &= urteil("kein Spot-Faktensatz traegt sie",
                    not any(not k.endswith("/hebel") for k in mit_finanz),
                    f"noch drin: {sorted(mit_finanz)}" if mit_finanz else "")

    print("\n3. FEHLENDE ANGABEN")
    alles &= urteil("jede Reihe ohne Umsatzwerte bekommt ihren Satz",
                    not abweichung_umsatz,
                    "; ".join(abweichung_umsatz) if abweichung_umsatz
                    else f"betroffen: {sorted(soll_umsatz) or 'keine in dieser DB'}")
    alles &= urteil(f"jede Reihe unter {MINDEST_HANDELSTAGE} Handelstagen auch",
                    not abweichung_kurz,
                    "; ".join(abweichung_kurz) if abweichung_kurz
                    else f"betroffen: {sorted(soll_kurz) or 'keine in dieser DB'}")
    alles &= urteil("und der Block bleibt bei vollstaendigen Assets leer",
                    bool(set(reihen) - mit_luecke),
                    f"{len(set(reihen) - mit_luecke)} von {len(reihen)} Assets "
                    f"ohne Luecken-Satz - waere er ueberall, waere er ein "
                    f"stehendes Feld (R-T6)")
    print(f"          Referenz aus Umbauplan 34.6: "
          f"{sorted(ERWARTET_LUECKE)}")
    print(f"          davon in DIESER Datenbank mit Reihe: "
          f"{sorted(ERWARTET_LUECKE & set(reihen)) or 'keines'}")
    for gruppe, sym, saetze in sorted(zeilen):
        for s in saetze:
            print(f"          {gruppe:11} {sym:7} {s[:78]}")

    print("\n4. SEKTORBEZUG")
    alles &= urteil("nur Themen-ETF", not (mit_ref - themen),
                    f"zuviel: {sorted(mit_ref - themen)}")
    alles &= urteil("und KEINE Absicherung", not (mit_ref & hedge),
                    f"drin: {sorted(mit_ref & hedge)}")
    if themen - mit_ref:
        print(f"          ohne Bezug (Historie oder Vergleichsreihe zu kurz): "
              f"{sorted(themen - mit_ref)}")

    if ohne_reihe:
        print(f"\nOhne Kursreihe (faellt an der Faktenstufe heraus): "
              f"{len(ohne_reihe)}")
        for z in ohne_reihe:
            print(f"          {z}")
    if fehler:
        alles = False
        print("\nFEHLER BEIM RENDERN:")
        for f in fehler:
            print(f"          {f}")

    print("\n" + "=" * 74)
    print("ALLE BESTANDEN" if alles else "NICHT BESTANDEN")
    return 0 if alles else 1


if __name__ == "__main__":
    raise SystemExit(main())
