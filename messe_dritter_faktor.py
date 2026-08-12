# -*- coding: utf-8 -*-
"""Der kausale Test: hebt ein DRITTER unabhaengiger Faktor die Handlungsquote?

WAS DIESE MESSUNG BEANTWORTET, und warum die vorherige es nicht konnte.

`messe_faktorzahl.py` zeigte einen Zusammenhang: bei drei gezaehlten Faktoren
handelte das System in 78 % der Faelle, bei zwei in 18 % - kein einziger Kauf
unterhalb von drei (p = 0,0035). Aber Faktorzahl und Aktion stammen aus
DEMSELBEN Modellaufruf. Das Modell koennte auch erst entscheiden und die Zahl
danach passend berichten; die Richtung war nicht belegt.

Hier wird die EINGABE veraendert, nicht die Ausgabe gelesen. Zwei Arme,
bitgleich bis auf einen Satz:

    OHNE   die heutige Beschreibung - Preis und Umsatz, zwei Faktoren
    MIT    zusaetzlich die Finanzierungsrate am Terminmarkt

Die Finanzierung ist der erste Fakt in dieser Beschreibung, der NICHT aus
unserer Kursreihe stammt (Faktenmappe 12.9). Steigen mit ihm sowohl die
gezaehlte Faktorzahl als auch die Handlungsquote, ist die Ursache belegt und
nicht mehr nur die Korrelation.

DREI ENTWURFSENTSCHEIDUNGEN

  EIN Lagebild je Anker, fuer beide Arme dasselbe. Es haengt nicht vom Asset ab
  und wuerde sonst zwischen den Armen schwanken - dann maesse der Lauf zwei
  Unterschiede statt einem. Spart zugleich ein Drittel der Aufrufe.

  KAUSAL ABGESCHNITTEN. Die Finanzierungshistorie wird mit `endzeit_ms` am
  Ankertag begrenzt. Ohne das saehe ein Anker von 2025 die Finanzierung von
  heute - derselbe Fehler, den `_reihe_bis()` bei den Kursen von Anfang an
  verhindert. Live geprueft: bis 2025-10-30 endet die Reihe am 29.10.2025,
  ohne Schranke am 11.08.2026.

  NUR KRYPTO. Finanzierungsraten gibt es nur fuer Perpetuals. Anker auf Aktien,
  ETF und Rohstoffen koennen den Faktor nicht bekommen und gehoeren nicht in
  diesen Lauf - sie wuerden den Arm MIT verwaessern, ohne ihn zu veraendern.

    python messe_dritter_faktor.py --db <pfad> --trocken
"""
# GESTRICHEN AM 12.08. (L1). Dieses Skript rief `beschreibe_marktbreite()`
# direkt. Nach dem Tausch waere es ein Skript, das eine ANDERE Lage misst als
# die Produktion - genau die Umgehung, die ein glatter Schnitt ausschliessen
# soll. Es geht jetzt ueber `rollen_eingabe.baue_lagebild_eingabe()`, die
# einzige Stelle, an der die Eingabe des Lagebilds entsteht.
#
# WICHTIG FUER ALTE ERGEBNISSE: alles, was vor dem 12.08. mit diesem Skript
# gemessen wurde, traegt die Marktbreite. Ein Vergleich alt/neu ueber diese
# Grenze hinweg misst den Umbau mit, nicht die Sache.
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone

import numpy as np
import requests


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="data/tradinginfotool.db")
    p.add_argument("--anker", default="ankerpopulation.json")
    p.add_argument("--anbieter", default="gemini35")
    p.add_argument("--ausgabe", default="dritter_faktor.json")
    p.add_argument("--trocken", action="store_true")
    args = p.parse_args()

    import pruefe_rollenkette as PR
    PR.DB = args.db                      # EINE Datenquelle, siehe messe_faktorzahl

    import config
    import agent.rolle_analyst as RA
    import agent.rolle_trader as RT
    from agent.lagebeschreibung import beschreibe_lage
    from api.derivatives import get_funding_history, summarize_funding
    from backtest_llm1_historisch import lade_reihen_aus_db
    from indicators.calculations import atr_wilder, latest_value

    klasse = {a.symbol: a.assetklasse for a in config.get_watchlist()}
    anker = json.load(open(args.anker, encoding="utf-8"))["anker"]
    reihen = lade_reihen_aus_db(args.db)
    sess = requests.Session()
    sess.headers["User-Agent"] = "TradingInfoTool"

    print(f"DATENSTAND: {args.db}   PROMPT_STAND: {RA.PROMPT_STAND}")
    print(f"{len(anker)} Anker, davon Krypto: "
          f"{sum(1 for a in anker if klasse.get(a['symbol']) == 'krypto')}\n")

    # --- Vorflug: welche Anker koennen den dritten Faktor ueberhaupt bekommen?
    tauglich = []
    for a in anker:
        if klasse.get(a["symbol"]) != "krypto":
            continue
        r = reihen.get(a["symbol"])
        if not r or a["index"] >= len(r) or r[a["index"]].date[:10] != a["datum"][:10]:
            print(f"  {a['symbol']:8} {a['datum']}  Anker loest nicht auf")
            continue
        ende = int(datetime.fromisoformat(a["datum"]).replace(
            tzinfo=timezone.utc).timestamp() * 1000)
        try:
            hist = get_funding_history(f"{a['symbol']}USDT", 100, sess, ende)
        except Exception:                                        # noqa: BLE001
            hist = []
        z = summarize_funding(hist)
        if not z or (z.get("beobachtungen") or 0) < 20:
            print(f"  {a['symbol']:8} {a['datum']}  keine Finanzierungshistorie "
                  f"({len(hist)} Perioden) - faellt raus")
            continue
        a["_funding"] = z
        tauglich.append(a)

    print(f"\nVorflug: {len(tauglich)} Anker koennen den dritten Faktor bekommen")
    print(f"KONTINGENT: {len(tauglich)} x (1 Lagebild + 2 Arme) = "
          f"{len(tauglich)*3} Aufrufe")
    print(f"  Gemini 10/min, 500/Tag -> rund {len(tauglich)*3/10:.0f} Minuten\n")
    if args.trocken:
        if tauglich:
            print("Beispiel des neuen Satzes:")
            from agent.lagebeschreibung import _finanzierung
            for s in _finanzierung(tauglich[0]["_funding"]):
                print(f"  {tauglich[0]['symbol']}: {s}")
        print("\nTROCKEN - keine Aufrufe.")
        return 0

    client, modell = PR._client(args.anbieter)
    ergebnisse = []
    for a in tauglich:
        sym, i = a["symbol"], a["index"]
        r = reihen[sym]
        zeile = {k: v for k, v in a.items() if k != "_funding"}
        try:
            # EIN Lagebild fuer beide Arme
            lage = RA.validiere(PR.frage(
                client, modell, RA.SYSTEM_PROMPT_ANALYST,
                RE.baue_lagebild_eingabe(reihen, a["datum"]),
                "agent.rolle_analyst"))
            menge, einstand = PR._bestand(sym)
            hh = np.array([k.high for k in r[:i + 1]], dtype=float)
            ll = np.array([k.low for k in r[:i + 1]], dtype=float)
            cc = np.array([k.close for k in r[:i + 1]], dtype=float)
            atr = float(latest_value(atr_wilder(hh, ll, cc)) or 0.0)
            # DIE ZONEN BRAUCHEN DEN ATR IN EUR (Paket 7): die Kurse, die
            # das Modell nennt, sind EUR - der ATR aus der Reihe ist USD.
            # `beschreibe_lage` bekommt weiterhin den USD-Wert, weil sie
            # durchgehend in der Quellwaehrung rechnet.
            atr_e = atr * RE.fx_eur_je_usd(sym, r, i)
            gemeinsam = dict(symbol=sym, reihe=r, index=i,
                             kurs_eur=PR._kurs_eur(sym, r, i) or 0.0, atr=atr,
                             menge=menge, einstand_eur=einstand)
            for arm, fin in (("ohne", None), ("mit", a["_funding"])):
                ein = {"asset": sym,
                       "stand": beschreibe_lage(**gemeinsam, finanzierung=fin),
                       "marktlage_beurteilung": {"lage": lage["lage"], "gleichlauf": lage.get("gleichlauf")}}
                ent = RT.validiere(dict(PR.frage(
                    client, modell, RT.SYSTEM_PROMPT_TRADER, ein,
                    "agent.rolle_trader")), sym, atr=atr_e)
                zeile[arm] = {"faktoren": ent.get("unabhaengige_faktoren"),
                              "aktion": ent.get("aktion"),
                              "belege": len(ent.get("belege") or []),
                              "begruendung": ent.get("begruendung")}
        except Exception as e:                                   # noqa: BLE001
            zeile["fehler"] = f"{type(e).__name__}: {str(e)[:90]}"
        o, m = zeile.get("ohne", {}), zeile.get("mit", {})
        print(f"  {sym:8} {a['datum']}  OHNE F={o.get('faktoren')} "
              f"{str(o.get('aktion')):12}  MIT F={m.get('faktoren')} "
              f"{str(m.get('aktion')):12}"
              + ("  <<<" if o.get("aktion") != m.get("aktion") else ""))
        ergebnisse.append(zeile)
        with open(args.ausgabe, "w", encoding="utf-8") as fh:
            json.dump(ergebnisse, fh, ensure_ascii=False, indent=1)

    ok = [z for z in ergebnisse if "fehler" not in z]
    print("\n" + "=" * 66)
    for arm in ("ohne", "mit"):
        f = [z[arm]["faktoren"] for z in ok if z[arm].get("faktoren") is not None]
        h = [z for z in ok if z[arm].get("aktion") not in (None, "NICHTS_TUN")]
        k = [z for z in ok if z[arm].get("aktion") in ("KAUFEN", "NACHKAUFEN")]
        schnitt = sum(f) / len(f) if f else 0
        print(f"ARM {arm.upper():5}  Faktoren im Schnitt {schnitt:.2f}  "
              f"{dict(Counter(f))}   Handlungen {len(h)}/{len(ok)}  "
              f"davon Kaeufe {len(k)}")
    gedreht = [z for z in ok if z["ohne"].get("aktion") != z["mit"].get("aktion")]
    print(f"\nAktion geaendert: {len(gedreht)} von {len(ok)}")
    for z in gedreht:
        print(f"   {z['symbol']:8} {z['datum']}  "
              f"{z['ohne'].get('aktion')} -> {z['mit'].get('aktion')}")
    print("\nLESART: Steigen Faktorzahl UND Handlungsquote im Arm MIT, ist die")
    print("Ursache belegt - der dritte unabhaengige Faktor fehlte, nicht das")
    print("Urteilsvermoegen des Modells.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
