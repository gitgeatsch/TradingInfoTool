"""Traegt die Entwickleraktivitaet als Indikator - ueber ALLE Assets?
(19.08.2026, Umbauplan Kapitel 91 P2)

DIE FRAGE. Die Literatur nennt die Entwickleraktivitaet als besten Indikator
dafuer, ob ein Projekt lebt oder eingestellt ist - genau die Unterscheidung,
die ein Spot-Kauf braucht ("tot oder Bodenbildung"). CoinGecko liefert sie
frei, und WIR HABEN DIE ZUORDNUNG BEREITS: jedes Asset der Watchlist traegt
eine `coingecko_id`, und CoinGecko verknuepft selbst das Repository. Die
GitHub-API direkt haette dieselbe Kennzahl, aber keine Zuordnung.

⚠️ WARUM DIESES WERKZEUG UEBERHAUPT EXISTIERT. Mein erster Versuch fragte 43
Symbole im Abstand von 2,2 s ab, lief ins Rate-Limit und zaehlte JEDE
Fehlerantwort als "kein Repository" - Ergebnis "0 von 43", waehrend BTC zwei
Minuten zuvor 73.168 Sterne gemeldet hatte. Ein Abbruch war zu einem
plausibel aussehenden Messwert geworden.

DESHALB DREI ZUSTAENDE, DIE NIE VERSCHMELZEN:

    repo          ein Repository ist verknuepft und liefert Zahlen
    kein_repo     die Antwort kam an und sagt: kein Repository hinterlegt
    fehler        wir haben es NICHT erfahren - Netz, 429, unerwartete Form

Der dritte ist der wichtige. Wer ihn mit dem zweiten verrechnet, erklaert
lebendige Ketten fuer tot.

⚠️ UND "0 COMMITS" IST NICHT "TOT". AVAX meldet 0 Sterne, 0 Forks, 0 Commits -
das ist ein FEHLENDER LINK, kein eingestelltes Projekt. Die Auswertung
unterscheidet deshalb "kein Repo hinterlegt" von "Repo vorhanden, aber ruhig".

    python messe_entwickleraktivitaet.py [--abstand 5] [--nur 5]
"""
from __future__ import annotations

import argparse
import sys
import time

import requests

BASIS = "https://api.coingecko.com/api/v3/coins/{}"
# CoinGeckos Gratis-Tier nennt 10-30 Aufrufe je Minute. 5 s Abstand sind
# 12/min - bewusst am unteren Rand, weil ein 429 die Messung wertlos macht
# und ein langsamer Lauf nur Zeit kostet.
ABSTAND_S = 5.0
VERSUCHE_BEI_429 = 3


def _hole(cid: str, sitzung) -> tuple[str, dict]:
    """Ein Abruf, drei moegliche Zustaende. GIBT NIE STILL EINE NULL ZURUECK."""
    for versuch in range(1, VERSUCHE_BEI_429 + 1):
        try:
            r = sitzung.get(BASIS.format(cid), timeout=30, params={
                "localization": "false", "tickers": "false",
                "market_data": "false", "community_data": "false",
                "developer_data": "true", "sparkline": "false"})
        except Exception as exc:                             # noqa: BLE001
            return "fehler", {"grund": f"{type(exc).__name__}"}
        if r.status_code == 429:
            if versuch < VERSUCHE_BEI_429:
                time.sleep(ABSTAND_S * 3 * versuch)
                continue
            return "fehler", {"grund": "429 nach drei Versuchen"}
        if r.status_code != 200:
            return "fehler", {"grund": f"HTTP {r.status_code}"}
        try:
            d = r.json()
        except Exception:                                    # noqa: BLE001
            return "fehler", {"grund": "Antwort ist kein JSON"}
        if "developer_data" not in d:
            # ⚠️ NICHT als "kein Repo" werten. Eine Antwort ohne das Feld ist
            # eine unerwartete Form - vielleicht ein Fehlerkoerper mit 200.
            return "fehler", {"grund": "Feld developer_data fehlt"}
        dev = d.get("developer_data") or {}
        zahlen = {k: dev.get(k) for k in
                  ("stars", "forks", "subscribers", "commit_count_4_weeks",
                   "total_issues", "closed_issues")}
        hat_repo = any(bool(zahlen.get(k)) for k in
                       ("stars", "forks", "subscribers", "total_issues"))
        return ("repo" if hat_repo else "kein_repo"), zahlen
    return "fehler", {"grund": "unerreichbar"}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--abstand", type=float, default=ABSTAND_S)
    p.add_argument("--nur", type=int, default=0, help="nur die ersten N")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    import config as C

    wl = [(x.symbol, getattr(x, "coingecko_id", None)) for x in C.get_watchlist()
          if str(getattr(x, "assetklasse", "") or "").lower() == "krypto"
          and not getattr(x, "ist_cash_aequivalent", False)]
    ohne_id = [s for s, c in wl if not c]
    mit_id = [(s, c) for s, c in wl if c]
    if a.nur:
        mit_id = mit_id[:a.nur]

    print("=" * 74)
    print("ENTWICKLERAKTIVITAET - TRAEGT SIE UEBER ALLE ASSETS?")
    print("=" * 74)
    print(f"  {len(wl)} Kryptowerte, davon {len(mit_id)} mit coingecko_id"
          + (f", {len(ohne_id)} OHNE: {', '.join(ohne_id)}" if ohne_id else ""))
    print(f"  Abstand {a.abstand:.1f} s - der Lauf dauert rund "
          f"{len(mit_id) * a.abstand / 60:.0f} Minuten\n")

    eimer: dict[str, list] = {"repo": [], "kein_repo": [], "fehler": []}
    s = requests.Session()
    for i, (sym, cid) in enumerate(mit_id, 1):
        zustand, werte = _hole(cid, s)
        eimer[zustand].append((sym, werte))
        if zustand == "repo":
            print(f"  {i:3d}/{len(mit_id)}  {sym:10} Commits/4W "
                  f"{str(werte.get('commit_count_4_weeks')):>5}  "
                  f"Sterne {str(werte.get('stars')):>7}")
        else:
            print(f"  {i:3d}/{len(mit_id)}  {sym:10} {zustand.upper():10} "
                  f"{werte.get('grund', '')}")
        if i < len(mit_id):
            time.sleep(a.abstand)

    print("\n" + "=" * 74)
    print("ERGEBNIS - die drei Zustaende bleiben getrennt")
    print("=" * 74)
    for name, wort in (("repo", "Repository verknuepft"),
                       ("kein_repo", "kein Repository hinterlegt"),
                       ("fehler", "NICHT ERFAHREN (Netz, 429, Form)")):
        print(f"  {wort:34} {len(eimer[name]):3d} von {len(mit_id)}")
    if eimer["fehler"]:
        print(f"\n  ⚠️ {len(eimer['fehler'])} Symbole sind UNBEKANNT, nicht "
              f"'ohne Repo': {', '.join(s for s, _ in eimer['fehler'][:12])}")
        print("     Eine Abdeckungszahl darf sie NICHT als Nein zaehlen.")

    mit = eimer["repo"]
    if mit:
        ruhig = [s for s, w in mit if not (w.get("commit_count_4_weeks") or 0)]
        print(f"\n  davon ruhig (Repo da, 0 Commits in 4 Wochen): {len(ruhig)}"
              + (f"  {', '.join(ruhig[:10])}" if ruhig else ""))
        print("  ⚠️ 'ruhig' ist eine Aussage, 'kein Repo' ist keine - der "
              "erste Fall taugt als Indikator, der zweite nicht.")

    belastbar = len(mit) + len(eimer["kein_repo"])
    print(f"\n  BELASTBAR BEANTWORTET: {belastbar} von {len(mit_id)}"
          f"  ({100 * belastbar / len(mit_id):.0f} %)")
    return 0 if not eimer["fehler"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
