# -*- coding: utf-8 -*-
"""Darf der Rauschboden das Modellurteil überstimmen? (22.08.2026, Kapitel 130)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

DER ANLASS. Kapitel 129 hat gemessen: 99,9 % der Kauf-Signale tragen einen
Widerlegungspreis des Modells, aber nur 13,2 % haben ihren Stop dort. In
86,8 % gewinnt ein anderer Boden - meist der Rauschboden bei k = 2,0 ATR.

    Stop wenn die These bindet    4,81 %   -> Hebel entsteht
    Stop sonst                    8,04 %   -> kein Hebel

Kapitel 88.1 hatte genau das schon als Defekt benannt ("in 10 von 12 Faellen
die Klemme, nicht das Urteil"). S5 hat den Defekt nicht behoben, sondern die
Klemme ersetzt. Bevor an k oder am Verlustanteil gedreht wird, gehoert die
vorgelagerte Frage beantwortet.

DIE FRAGE, VORAB FESTGELEGT - UND ES IST GENAU EINE:

    Traegt ein Trade besser, wenn der Stop auf dem Widerlegungspreis des
    Modells liegt, oder wenn ihn der Rauschboden bestimmt?

⚠️ GEPAART AUF DENSELBEN ANKERN. Beide Varianten laufen ueber DENSELBEN
Kurspfad desselben Signals. Das ist der einzige Weg, den Markt aus dem
Vergleich herauszuhalten - und er ist hier zwingend, weil der Messzeitraum
eine Aufwaertsphase von +15,8 % Median ist (Kapitel 127).

DIE ZWEI ARME:

    A  BETRIEB    Stop wie gesetzt (der weiteste Boden gewinnt)
    B  THESE      Stop auf dem Widerlegungspreis des Modells

⚠️ DAS CRV BLEIBT IN BEIDEN ARMEN GLEICH. Das Ziel wandert mit dem Stop:
`ziel = einstieg + CRV x (einstieg - stop)`. Sonst vergliche man zwei
Geometrien statt zwei Stopquellen, und Kapitel 101 hat gemessen, dass die
Geometrie allein reine Kostenarithmetik ist.

⚠️ UND DER EINSTIEG MUSS ERREICHT SEIN (E1, Kapitel 128). Ohne diese Regel
zaehlt ein Ziel, das nie gekauft wurde - der Fehler, der 21,1 % der
aufgeloesten Signale betraf.

WAS ZUSAETZLICH BERICHTET WIRD, weil es die eigentliche Frage des Nutzers ist:

    der Hebel je Arm      hebel = verlustanteil / stop_rel
    die Finanzierung      0,03 %/Tag, nur wo Hebel > 1
    beide Gebuehrensaetze Referenz 0,30 % und Betrieb 1,50 %

DIE ABBRUCHREGEL:

    Unterschied ueber der Bootstrap-Schwelle UND ueber 0,01 R (2.56)
        -> die Stopquelle traegt, und die Richtung sagt, welche
    sonst
        -> sie traegt nicht, und k bleibt eine reine Risikoentscheidung

⚠️ DIE KONTROLLE IST EIN BLOCK-BOOTSTRAP (2.55), keine Permutation: beide
Arme sind deterministische Umrechnungen desselben Pfades.

⚠️ UND DIE HAEUFUNG GILT AUCH HIER (2.60). Die Bloecke werden je SYMBOL UND
TAG gebildet, nicht je Signal - fuenf Bewertungen desselben Symbols am selben
Tag sind eine Beobachtung.

    python messe_stopquelle.py [--ziehungen 400]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys

import numpy as np

sys.path.insert(0, ".")
from simuliere_bremse import SAETZE_ZUM_BERICHTEN              # noqa: E402

VERLUSTANTEIL = 0.06          # config.yaml rollen_kette.verlustanteil
FINANZIERUNG_JE_TAG = 0.0003  # 0,03 %/Tag, nur bei Hebel > 1
AB_DATUM = "2026-08-18"       # S5 - davor galt eine andere Geometrie
RELEVANZ_R = 0.01


def _lade(pfad: str):
    roh = io.open(pfad, encoding="utf-8").read()
    dec = json.JSONDecoder()

    def hol(n):
        m = re.search(r'"%s"\s*:\s*' % re.escape(n), roh)
        return dec.raw_decode(roh, m.end())[0] if m else None

    return hol("spot_signals") or [], hol("preishistorie_signal_symbole") or {}


def _kerzen(hist: dict) -> dict:
    """symbol -> [(datum, hoch, tief)] in EUR.

    ⚠️ EUR, WEIL DER WIDERLEGUNGSPREIS IN EUR STEHT. Die Historie traegt
    beide Waehrungen als getrennte Zeilen; sie zu mischen waere der Fehler,
    den `pruefe_waehrungen.py` seit dem 20.08. sucht."""
    aus = {}
    for sym, zeilen in (hist.get("preishistorie_je_symbol") or {}).items():
        reihe = [(z["date"], z["high"], z["low"]) for z in zeilen
                 if str(z.get("currency")).upper() == "EUR"
                 and z.get("high") is not None and z.get("low") is not None]
        if reihe:
            aus[sym] = sorted(reihe)
    return aus


def _lauf(reihe, ab: str, e_von, e_bis, stop, ziel) -> tuple:
    """('ziel'|'stop'|'offen', Tage) - E1 und vorsichtige Lesart."""
    eingestiegen = False
    tage = 0
    for datum, hoch, tief in reihe:
        if datum < ab:
            continue
        hoch, tief = float(hoch), float(tief)
        if not eingestiegen:
            if tief <= e_bis and hoch >= e_von:
                eingestiegen = True
            else:
                continue
        tage += 1
        if tief <= stop:
            return "stop", tage
        if hoch >= ziel:
            return "ziel", tage
    return "offen", tage


def _r(ausgang, tage, stop_rel, crv, satz) -> float | None:
    """Ergebnis in R nach Kosten. None, wenn unentschieden."""
    if ausgang == "offen":
        return None
    hebel = max(1.0, VERLUSTANTEIL / stop_rel)
    kosten = 2.0 * satz / stop_rel
    if hebel > 1.0:
        kosten += FINANZIERUNG_JE_TAG * tage * hebel / stop_rel
    return (crv if ausgang == "ziel" else -1.0) - kosten


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", default=None)
    ap.add_argument("--ziehungen", type=int, default=400)
    ap.add_argument("--datei", default="messwerte_stopquelle.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    pfad = a.export
    if not pfad:
        from extract_notebook_diagnose import _google_drive_wurzel
        pfad = os.path.join(_google_drive_wurzel(), "Claude_Austauschordner",
                            "Notebook_Analysedaten", "notebook_diagnose.json")
    print("=" * 78)
    print("DARF DER RAUSCHBODEN DAS MODELLURTEIL UEBERSTIMMEN?")
    print("  Gepaart auf denselben Ankern - der Markt ist damit heraus.")
    print(f"  Nur Signale ab {AB_DATUM} (S5); Kurse in EUR.")
    print("=" * 78)

    signale, hist = _lade(pfad)
    kerzen = _kerzen(hist)
    faelle = []
    for x in signale:
        if x.get("quelle_kette") != "rollen":
            continue
        if x.get("action") not in ("ERÖFFNEN", "KAUFEN", "NACHKAUFEN"):
            continue
        if (x.get("created_at") or "")[:10] < AB_DATUM:
            continue
        ev, eb = x.get("entry_eur_von"), x.get("entry_eur_bis")
        sv, tv = x.get("stop_loss_eur_von"), x.get("take_profit_eur_von")
        u = x.get("umgeworfen_preis_eur")
        reihe = kerzen.get(x.get("symbol"))
        if None in (ev, eb, sv, tv, u) or not reihe:
            continue
        e = (float(ev) + float(eb)) / 2.0
        sv, tv, u = float(sv), float(tv), float(u)
        # ⚠️ NUR SAUBERE LONG-AUFBAUTEN. Eine These ueber dem Einstieg ist
        # kein Stop, sondern ein Widerspruch - sie gehoert nicht in die
        # Messung, sondern in eine eigene Frage.
        if not (0 < u < e < tv) or sv >= e:
            continue
        faelle.append({
            "sym": x["symbol"], "tag": (x["created_at"] or "")[:10],
            "e": e, "e_von": float(ev), "e_bis": float(eb),
            "stop_a": sv, "stop_b": u,
            "crv": (tv - e) / (e - sv), "reihe": reihe})

    print(f"  {len(faelle)} Kauf-Signale ab {AB_DATUM} pruefbar")
    if len(faelle) < 50:
        print("  ⚠️ ZU WENIGE")
        return 2

    for f in faelle:
        for arm, stop in (("a", f["stop_a"]), ("b", f["stop_b"])):
            # ⚠️ DAS CRV BLEIBT GLEICH - das Ziel wandert mit dem Stop.
            ziel = f["e"] + f["crv"] * (f["e"] - stop)
            aus, tage = _lauf(f["reihe"], f["tag"], f["e_von"], f["e_bis"],
                              stop, ziel)
            f[f"aus_{arm}"] = aus
            f[f"tage_{arm}"] = tage
            f[f"stop_rel_{arm}"] = (f["e"] - stop) / f["e"]

    print(f"\n{'-' * 78}\nDIE ZWEI ARME\n{'-' * 78}")
    print(f"  {'Arm':26}{'Stop':>9}{'Hebel':>8}{'Ziel':>7}{'Stop':>7}"
          f"{'offen':>7}{'Quote':>9}")
    for arm, name in (("a", "A Betrieb (Rauschboden)"),
                      ("b", "B These (Modell)")):
        sr = float(np.median([f[f"stop_rel_{arm}"] for f in faelle]))
        heb = max(1.0, VERLUSTANTEIL / sr)
        z = [f[f"aus_{arm}"] for f in faelle]
        ent = z.count("ziel") + z.count("stop")
        print(f"  {name:26}{100 * sr:8.2f} %{heb:8.2f}{z.count('ziel'):>7}"
              f"{z.count('stop'):>7}{z.count('offen'):>7}"
              f"{(100 * z.count('ziel') / ent if ent else float('nan')):8.1f} %")

    print(f"\n{'-' * 78}\nERWARTUNGSWERT JE TRADE IN R\n{'-' * 78}")
    print(f"  {'Arm':26}" + "".join(f"{n:>22}" for n, _s in
                                    SAETZE_ZUM_BERICHTEN))
    werte = {}
    for arm, name in (("a", "A Betrieb (Rauschboden)"),
                      ("b", "B These (Modell)")):
        zeile = f"  {name:26}"
        for _n, satz in SAETZE_ZUM_BERICHTEN:
            r = [_r(f[f"aus_{arm}"], f[f"tage_{arm}"], f[f"stop_rel_{arm}"],
                    f["crv"], satz) for f in faelle]
            r = [v for v in r if v is not None]
            werte[(arm, satz)] = r
            zeile += f"{(np.mean(r) if r else float('nan')):+21.3f}"
        print(zeile)

    # ---- BLOCK-BOOTSTRAP AUF DEN PAARWEISEN DIFFERENZEN (2.55/2.60) ----
    print(f"\n{'-' * 78}")
    print(f"BLOCK-BOOTSTRAP - {a.ziehungen} Ziehungen, Bloecke je (Symbol, Tag)")
    print(f"{'-' * 78}")
    satz = SAETZE_ZUM_BERICHTEN[0][1]
    paare, bloecke = [], {}
    for f in faelle:
        ra = _r(f["aus_a"], f["tage_a"], f["stop_rel_a"], f["crv"], satz)
        rb = _r(f["aus_b"], f["tage_b"], f["stop_rel_b"], f["crv"], satz)
        if ra is None or rb is None:
            continue
        bloecke.setdefault((f["sym"], f["tag"]), []).append(len(paare))
        paare.append(rb - ra)
    paare = np.array(paare)
    gruppen = [np.array(v) for v in bloecke.values()]
    print(f"  {len(paare)} Paare in {len(gruppen)} Bloecken "
          f"(Haeufung {len(paare) / max(len(gruppen), 1):.2f})")
    if len(gruppen) < 10:
        print("  ⚠️ ZU WENIGE BLOECKE")
        return 2
    rng = np.random.default_rng(20260822)
    zieh = [float(paare[np.concatenate(
        [gruppen[j] for j in rng.integers(0, len(gruppen), len(gruppen))])
    ].mean()) for _ in range(a.ziehungen)]
    d = float(paare.mean())
    unten, oben = float(np.quantile(zieh, 0.025)), float(np.quantile(zieh, 0.975))
    print(f"  These gegen Betrieb: {d:+.3f} R")
    print(f"  95-%-Intervall [{unten:+.3f}, {oben:+.3f}]")
    if abs(d) < RELEVANZ_R:
        urteil = f"kein Unterschied von Belang (unter {RELEVANZ_R:.2f} R)"
    elif unten > 0:
        urteil = "DIE THESE TRAEGT BESSER"
    elif oben < 0:
        urteil = "DER RAUSCHBODEN TRAEGT BESSER"
    else:
        urteil = "nicht unterscheidbar"
    print(f"  -> {urteil}")
    print("\n  ⚠️ Der Messzeitraum ist eine Aufwaertsphase (+15,8 % Median,")
    print("     Kapitel 127). Die PAARUNG haelt den Markt aus dem Vergleich,")
    print("     aber die absoluten Quoten beider Arme traegt er mit.")

    print("\n" + "=" * 78)
    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps(
            {"faelle": len(faelle), "paare": len(paare),
             "bloecke": len(gruppen), "diff": d, "unten": unten,
             "oben": oben, "urteil": urteil},
            ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
