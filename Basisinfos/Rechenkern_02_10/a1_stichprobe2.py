"""A1 P1, ZWEITE Stichprobe (Validierung des geschaerften Prompts): 60 Nachrichten (30 Vorfilter-Treffer, 30 ohne), ohne die 90 der ersten.
Grund: der Prompt wurde nach der ersten Auswertung geschaerft (Bereiche fehlten ganz) - gemessen auf derselben Stichprobe waere das
Ergebnis geschoent. Die Handeinordnung a1_stichprobe2_hand.csv entsteht VOR jedem Blick auf die Ausgabe. Nur lesend, ohne Netz."""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agent import ereignisse as E  # noqa: E402

HIER = os.path.dirname(os.path.abspath(__file__))
SAAT = 20261102


def main():
    alt = set(pd.read_csv(os.path.join(HIER, "a1_stichprobe.csv")).meldung)
    N = E.meldungen("nachricht")
    N = N[(N.zeit >= "2025-12-01") & (N.zeit < "2026-10-17") & ~N.meldung.isin(alt)]
    N["vf"] = N.titel.map(E.vorfilter)
    S = pd.concat([N[N.vf].sample(30, random_state=SAAT).assign(schicht="nachricht_treffer"),
                   N[~N.vf].sample(30, random_state=SAAT).assign(schicht="nachricht_kein")], ignore_index=True)
    S["nr"] = range(301, 301 + len(S))
    S[["nr", "schicht", "quelle", "meldung", "zeit", "titel"]].to_csv(os.path.join(HIER, "a1_stichprobe2.csv"), index=False, encoding="utf-8")
    print(len(S))


if __name__ == "__main__":
    main()
