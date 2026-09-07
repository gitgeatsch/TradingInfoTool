# -*- coding: utf-8 -*-
"""WELCHE KRYPTO-ASSETS HABEN WELCHE ABDECKUNG? (07.09.2026)

## Warum das gebraucht wird

Am 07.09. fiel auf: von 57 Watchlist-Eintraegen sind nur 29 im
Messuniversum. Das klang nach einem schweren Befund.

**Nutzerhinweis, der ihn einordnet:** *„Wichtig sind die stabilen Werte,
Altbestand und Hochrisikowerte im Meme-/Smallcap-Bereich muessen mitlaufen
und hier ist eine fehlende Bewertung als unkritisch zu bewerten."*

⚠️ **Damit ist die Frage nicht ,wieviele fehlen', sondern WELCHE.** Fehlen
Memes und Smallcaps, ist es unkritisch. Fehlt BTC, ist es ein Notfall.

## Was gezeigt wird

Je Watchlist-Symbol, welche Quelle es abdeckt:

    Kurs       `messe_eigenschaft_beitrag.lade()` - die Messbasis
    funding    Perpetual-Finanzierung (Binance-Archiv)
    turnover   Handelsvolumen je Umlaufmenge (onchain)
    oi         Open-Interest-Aenderung (Terminmarkt)
    schnitt    200-Tage-Schnitt aus der Messbasis

    python zeige_abdeckung_krypto.py
"""
from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402

# ⚠️ Grobe Einordnung nach Marktstellung - NUR fuer die Lesbarkeit der
# Tabelle, nicht fuer irgendeine Bewertung. Regel 3 verbietet ein
# Asset-Vorurteil; hier wird nichts abgeurteilt, nur sortiert.
# ⚠️ SOL GEHOERT ZUM KERN (Nutzerhinweis 07.09.). Die erste Fassung
# fuehrte ihn unter "grosse Werte" - eine Einordnung, die der Nutzer als
# falsch benannt hat.
KERN = {"BTC", "ETH", "SOL"}
GROSS = {"BNB", "XRP", "ADA", "AVAX", "DOT", "LINK", "MATIC", "TRX",
         "LTC", "BCH", "ATOM", "UNI", "XLM", "ETC", "FIL", "APT", "ARB",
         "OP", "NEAR", "ICP", "ALGO", "VET", "HBAR", "SUI", "TON", "DOGE"}


def main() -> int:
    print("=" * 92)
    print("ABDECKUNG DER KRYPTO-ASSETS — welche Quelle kennt welches Symbol?")
    print("=" * 92)

    reihen = B.lade()
    kurs = {s.upper() for s in reihen}
    fu = {s.upper() for s in F.lade_funding()}
    tu = {s.upper() for s in MB.reihe("data/onchain_historie.db", "splycur")}
    oi = {s.upper() for s in K.lade_terminmarkt()["oi_aenderung"]}

    import config
    # ⚠️⚠️ NUR KRYPTO (Nutzerhinweis 07.09.: "keine Mischung von
    # Nicht-Krypto und Krypto"). Die Watchlist fuehrt 57 Eintraege, davon
    # sind 13 Aktien, ETF und Rohstoffe - sie gehoeren in die
    # Nicht-Krypto-Klassen und haben in dieser Rechnung nichts zu suchen.
    # Die erste Fassung zaehlte sie mit und kam auf "29 von 57"; richtig
    # ist "29 von 44".
    alle_wl = config.get_watchlist()
    nicht_krypto = sorted({str(getattr(a, "symbol", a)).upper()
                           for a in alle_wl
                           if str(getattr(a, "assetklasse", "")).lower()
                           != "krypto"})
    wl = sorted({str(getattr(a, "symbol", a)).upper() for a in alle_wl
                 if str(getattr(a, "assetklasse", "")).lower() == "krypto"})
    print("  ⚠️ %d Nicht-Krypto-Eintraege ausgeschlossen: %s"
          % (len(nicht_krypto), ", ".join(nicht_krypto)))

    print("  Messuniversum %d Krypto · Watchlist %d Krypto"
          % (len(kurs), len(wl)))
    print("  funding %d · turnover %d · oi %d (je im Messuniversum)"
          % (len(fu & kurs), len(tu & kurs), len(oi & kurs)))

    def rang(s):
        return 0 if s in KERN else (1 if s in GROSS else 2)

    print()
    print("  DIE WATCHLIST, nach Marktstellung sortiert")
    print("     %-12s %-6s %-8s %-9s %-5s  %s"
          % ("Symbol", "Kurs", "funding", "turnover", "oi", "Bewertung moeglich?"))
    zahl = {0: [0, 0], 1: [0, 0], 2: [0, 0]}
    for s in sorted(wl, key=lambda x: (rang(x), x)):
        hat_kurs = s in kurs
        b = [s in fu, s in tu, s in oi]
        # Die Bewertung braucht MINDESTENS einen Beitrag - das System
        # arbeitet ausdruecklich auch mit 1, 2 oder 3 (Nutzervorgabe 31.08.)
        moeglich = hat_kurs and any(b)
        gruppe = rang(s)
        zahl[gruppe][0] += 1
        zahl[gruppe][1] += 1 if moeglich else 0
        print("     %-12s %-6s %-8s %-9s %-5s  %s"
              % (s, "✔" if hat_kurs else "—",
                 "✔" if b[0] else "—", "✔" if b[1] else "—",
                 "✔" if b[2] else "—",
                 "✔ ja" if moeglich else
                 ("⚠️ NEIN - kein Beitrag" if hat_kurs else
                  "⚠️ NEIN - keine Kursreihe")))

    print()
    print("  ZUSAMMENFASSUNG nach Marktstellung")
    for g, lab in ((0, "Kern (BTC, ETH)"), (1, "grosse Werte"),
                   (2, "uebrige (Meme/Smallcap/neu)")):
        ges, ok = zahl[g]
        if not ges:
            continue
        print("     %-30s %2d von %2d bewertbar (%3.0f %%)"
              % (lab, ok, ges, 100 * ok / ges))

    print()
    print("  ⚠️ EINORDNUNG (Nutzerhinweis 07.09.): fehlende Bewertung bei")
    print("     Meme- und Smallcap-Werten ist UNKRITISCH - sie laufen mit.")
    print("     Kritisch waere eine Luecke bei den stabilen Werten.")
    fehlt_oben = [s for s in wl if rang(s) < 2 and not (s in kurs and
                  (s in fu or s in tu or s in oi))]
    # ⚠️ Wer Zusatzdaten hat, aber KEINE Kursreihe - das ist eine
    # behebbare Luecke: die Kurse wurden nie geladen, das Symbol ist
    # richtig (07.09. einzeln geprueft: HYPE/MORPHO/KAS/BRETT haben in
    # `price_history_ohlc` NULL Zeilen, in keiner Schreibweise).
    behebbar = sorted(s for s in wl
                      if s not in kurs and (s in fu or s in tu or s in oi))
    if behebbar:
        print()
        print("  ⚠️ ZUSATZDATEN DA, ABER KEINE KURSREIHE (behebbar - die")
        print("     Kurse wurden nie geladen, die Symbole stimmen):")
        print("     %s" % ", ".join(behebbar))
    if fehlt_oben:
        print("     ⚠️⚠️ LUECKE BEI STABILEN WERTEN: %s"
              % ", ".join(sorted(fehlt_oben)))
    else:
        print("     ✔ Bei Kern und grossen Werten ist KEINE Luecke.")

    print()
    print("  DIE MESSBASIS (516 Symbole) - wieviele haben wieviele Beitraege?")
    verteilung = {0: 0, 1: 0, 2: 0, 3: 0}
    for s in kurs:
        verteilung[sum((s in fu, s in tu, s in oi))] += 1
    for n in (3, 2, 1, 0):
        print("     %d Beitraege: %3d Symbole (%4.1f %%)"
              % (n, verteilung[n], 100 * verteilung[n] / len(kurs)))
    print()
    print("  ⚠️ Die Kette arbeitet ausdruecklich auch mit 1, 2 oder 3")
    print("     Beitraegen (Nutzervorgabe 31.08.) - die Schwelle richtet")
    print("     sich nach der Datenlage. Ein Symbol mit NULL Beitraegen")
    print("     bekommt aber kein Potential und damit keine Empfehlung.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
