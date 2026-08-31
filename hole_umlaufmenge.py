# -*- coding: utf-8 -*-
"""Holt Umlaufmenge und Transaktionswert - fuer die BEWERTUNGSkennzahlen.

Nutzerfrage 30.08.: "warum liefern TVL und aktive Adressen keine Aussage,
werden diese nicht in der Praxis angewendet?"

Die Antwort: sie werden angewendet - aber als VERHAELTNIS, nicht als Rohgroesse.

    MC/TVL   Marktkapitalisierung / TVL          "teuer relativ zum Kapital"
    NVT      Marktkapitalisierung / Transaktionswert
    NVM      Marktkapitalisierung / Adressen^2   (Metcalfe)

Dafuer fehlt die Umlaufmenge. Coin Metrics Community liefert sie frei.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import hole_fremdreihen as H
import messe_eigenschaft_beitrag as B

unsere = {s.upper() for s in B.lade().keys()}
for metrik in ("SplyCur", "TxTfrValAdjUSD"):
    try:
        H.onchain(unsere, metrik=metrik)
    except Exception as e:
        print("  %s: %s" % (metrik, str(e)[:90]))
