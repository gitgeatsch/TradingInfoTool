"""A1 P1 (Voranalyse_A1 §5): geschichtete Stichprobe 200 Meldungen - Binance-Regel 50, Binance-Rest 30, Upbit 30, Nachrichten 90 (45 Vorfilter-
Treffer, 45 Nicht-Treffer). Schreibt NUR Titel (+ Textanfang bei Binance) - die Handeinordnung entsteht OHNE Blick auf die Ausgabe des Moduls.
Fenster: Binance und Upbit ab 2023 (E-1-Zeitraum), Nachrichten im Rueckspiel 01.12.2025-16.10.2026. Nur lesend, ohne Netz."""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agent import ereignisse as E  # noqa: E402

AUS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a1_stichprobe.csv")
SAAT = 20261101


def main():
    W = E.welt()
    B = E.meldungen("binance")
    B = B[B.zeit >= "2023-01-01"]
    B["regel"] = [E.regel(t, E.B_REGELN) for t in B.titel]
    U = E.meldungen("upbit")
    U = U[U.zeit >= "2023-01-01"]
    N = E.meldungen("nachricht")
    N = N[(N.zeit >= "2025-12-01") & (N.zeit < "2026-10-17")]
    N["vf"] = N.titel.map(E.vorfilter)
    teile = [("binance_regel", B[B.regel.notna()].sample(50, random_state=SAAT)),
             ("binance_rest", B[B.regel.isna()].sample(30, random_state=SAAT)),
             ("upbit", U.sample(30, random_state=SAAT)),
             ("nachricht_treffer", N[N.vf].sample(45, random_state=SAAT)),
             ("nachricht_kein", N[~N.vf].sample(45, random_state=SAAT))]
    S = pd.concat([t.assign(schicht=s) for s, t in teile], ignore_index=True)
    S["nr"] = range(1, len(S) + 1)
    S["textanfang"] = S.text.fillna("").str.replace(r"\s+", " ", regex=True).str[:300]
    S[["nr", "schicht", "quelle", "meldung", "zeit", "titel", "textanfang"]].to_csv(AUS, index=False, encoding="utf-8")
    print("Grundgesamtheit: Binance-Regel %d, Binance-Rest %d, Upbit %d, Nachrichten Treffer %d, kein Treffer %d" % (
        B.regel.notna().sum(), B.regel.isna().sum(), len(U), N.vf.sum(), (~N.vf).sum()))
    print("geschrieben:", AUS, len(S))


if __name__ == "__main__":
    main()
