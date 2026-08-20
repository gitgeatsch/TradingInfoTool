"""Heisst hoher Umschlag nach einem Anstieg etwas anderes als in der Ruhe?
(20.08.2026, Umbauplan 97)

DIE BEHAUPTUNG, DIE GEPRUEFT WIRD. Das Modell begruendet denselben Fakt in
zwei Richtungen, und es nennt jedes Mal seinen Grund:

    ETH  ▼  "extrem hoher Umschlag signalisiert ein moegliches
            Erschoepfungsrisiko"        - nach einem grossen Anstieg
    TAO  ▲  "extrem hohe Handelsaktivitaet deutet auf einen bevorstehenden
            Ausbruch aus der Konsolidierung hin"  - aus einer Seitwaertsphase

Beide Lesarten sind gaengig. GEMESSEN hat sie in diesem Projekt nie jemand -
und genau das steht als [BEHAUPTET] ueber dem Abschnitt.

⚠️ WARUM DAS MESSBAR IST, OBWOHL DER UMLAUFBESTAND FEHLT.

Der Umschlag ist Umsatz geteilt durch Umlaufbestand. Den Bestand fuehrt nur
`price_cache`, und der reicht Tage zurueck, nicht Jahre.

Gebraucht wird er aber nicht: gemessen wird das PERZENTIL innerhalb der
eigenen Historie eines Symbols, und ein je Symbol konstanter Nenner kuerzt
sich in einem Rang vollstaendig heraus. Das Perzentil des Umsatzes ist
dasselbe wie das Perzentil von Umsatz/Bestand.

⚠️ NICHT GANZ KONSTANT: Emissionen erhoehen den Bestand, bei den meisten
Werten um einige Prozent im Jahr. Ueber ein rollendes 250-Tage-Fenster ist
die Verschiebung klein gegen die Streuung des Umsatzes, aber sie ist nicht
null - der Befund gilt fuer den Umsatzrang, nicht buchstaeblich fuer den
Umschlagrang.

DER AUFBAU, VORAB FESTGELEGT:

    Anker       Tage, an denen der Umsatz im eigenen 250-Tage-Fenster im
                90. Perzentil oder darueber steht.
    Zusammen-   die Bewegung der 20 Handelstage DAVOR:
    hang          nach Anstieg   ueber +10 %
                  seitwaerts     -10 bis +10 %
                  nach Rueckgang unter -10 %
    Ergebnis    Vorwaertsrendite ueber 5 und 20 Handelstage, MARKTBEREINIGT
                (der Tagesmittelwert aller Symbole wird abgezogen - sonst
                misst man, ob der Markt gestiegen ist).

⚠️ DIE SIGNIFIKANZ LAEUFT UEBER TERMINE, nicht ueber Anker, und der
Standardfehler ist nach Newey-West korrigiert - dieselbe Rechnung wie in
`messe_drift.py`, aus demselben Grund: an einem Tag bewegt sich alles
gemeinsam, und ueberlappende Vorwaertsfenster sind autokorreliert.

UND DIE ZWEI KONTROLLEN, OHNE DIE EIN BEFUND NICHTS WERT IST:

    --positivkontrolle  pflanzt einen Effekt ein. Findet die Messung ihn
                        nicht, sagt auch ihr "nichts" nichts.
    --placebo N         wuerfelt die Zusammenhangs-Etiketten neu. Was dann
                        noch anschlaegt, ist der Fehler der Methode.

    python messe_umschlag_kontext.py [--placebo 40] [--positivkontrolle 0.02]
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys

import numpy as np

sys.path.insert(0, ".")
from messe_drift import _newey_west, _reihen  # noqa: E402

# Vorab festgelegt, aus der Behauptung selbst abgeleitet - nicht aus einem
# Blick in die Daten.
FENSTER = 250          # worin der Umsatz sein Perzentil bekommt
HOCH_AB = 90           # ab wann "hoher Umschlag"
RUECKBLICK = 20        # die Bewegung davor
SCHWELLE = 0.10        # was "Anstieg" bzw. "Rueckgang" heisst
HORIZONTE = (5, 20)
MINDEST_SYMBOLE = 10
LAGEN = ("nach Anstieg", "seitwaerts", "nach Rueckgang")


def _lage(rendite: float) -> str:
    if rendite > SCHWELLE:
        return "nach Anstieg"
    if rendite < -SCHWELLE:
        return "nach Rueckgang"
    return "seitwaerts"


def _tafeln(db: str, klasse: str) -> tuple:
    """(termine, schluss, volumen, symbole) auf gemeinsamer Zeitachse."""
    from backtest_llm1_historisch import lade_reihen_aus_db

    import config as C
    kl = {x.symbol: str(getattr(x, "assetklasse", "") or "").lower()
          for x in C.get_watchlist()}
    roh = {}
    for sym, kerzen in lade_reihen_aus_db(db).items():
        if sym.startswith("_") or kl.get(sym) != klasse or len(kerzen) < 400:
            continue
        roh[sym] = kerzen
    symbole = sorted(roh)
    termine = sorted({str(k.date)[:10] for s in symbole for k in roh[s]})
    platz = {d: i for i, d in enumerate(termine)}
    c = np.full((len(symbole), len(termine)), np.nan)
    v = np.full((len(symbole), len(termine)), np.nan)
    for i, s in enumerate(symbole):
        for k in roh[s]:
            j = platz[str(k.date)[:10]]
            c[i, j] = float(k.close)
            # ⚠️ VOLUMEN NULL IST KEIN VOLUMEN. Einige Reihen fuehren an
            # handelsfreien Tagen eine 0; als Umsatz gelesen waere das der
            # niedrigste Rang und damit ein erfundener Anker.
            vol = float(k.volume or 0)
            v[i, j] = vol if vol > 0 else np.nan
    return np.array(termine), c, v, symbole


def messe(c, v, horizont: int, kontrolle: float = 0.0, mischen=None) -> dict:
    """Je Termin und Lage die marktbereinigte Vorwaertsrendite der Anker."""
    n_sym, n_t = c.shape
    je_lage: dict = {l: [] for l in LAGEN}
    for t in range(FENSTER, n_t - horizont):
        jetzt, spaeter = c[:, t], c[:, t + horizont]
        frueher = c[:, t - RUECKBLICK]
        gut = (~np.isnan(jetzt) & ~np.isnan(spaeter) & ~np.isnan(frueher)
               & (jetzt > 0) & (frueher > 0))
        if gut.sum() < MINDEST_SYMBOLE:
            continue
        kuenftig = spaeter[gut] / jetzt[gut] - 1.0
        # Marktbereinigt - sonst misst man den Markt und nicht die Auswahl.
        kuenftig = kuenftig - kuenftig.mean()
        davor = jetzt[gut] / frueher[gut] - 1.0
        # Umsatzperzentil im eigenen Fenster, je Symbol.
        fenster = v[:, t - FENSTER:t + 1][gut]
        heute = v[:, t][gut]
        with np.errstate(invalid="ignore"):
            rang = np.nanmean(fenster[:, :-1] < heute[:, None], axis=1) * 100
        lagen = np.array([_lage(x) for x in davor])
        if mischen is not None:
            lagen = mischen.permutation(lagen)
        if kontrolle:
            kuenftig = kuenftig + kontrolle * np.where(
                lagen == "nach Anstieg", -1.0,
                np.where(lagen == "seitwaerts", 1.0, 0.0))
        anker = np.isfinite(rang) & (rang >= HOCH_AB)
        for l in LAGEN:
            m = anker & (lagen == l)
            if m.sum():
                je_lage[l].append(float(kuenftig[m].mean()))
    aus = {}
    for l, reihe in je_lage.items():
        a = np.array(reihe)
        if len(a) < 30:
            aus[l] = {"termine": len(a), "mittel": None, "t": None}
            continue
        se = _newey_west(a, horizont - 1)
        aus[l] = {"termine": len(a), "mittel": float(a.mean()),
                  "t": float(a.mean() / se) if se > 0 else None,
                  "se": float(se)}
    return aus


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="data/tradinginfotool.db")
    p.add_argument("--klasse", default="krypto")
    p.add_argument("--placebo", type=int, default=0)
    p.add_argument("--positivkontrolle", type=float, default=0.0)
    p.add_argument("--datei", default="messwerte_umschlag.json")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("HOHER UMSCHLAG - HEISST ER JE NACH LAGE ETWAS ANDERES?")
    print("=" * 78)
    termine, c, v, symbole = _tafeln(a.db, a.klasse)
    print(f"  {len(symbole)} Reihen, {len(termine)} Termine "
          f"({termine[0]} bis {termine[-1]})")
    print(f"  Anker: Umsatz im {HOCH_AB}. Perzentil des eigenen "
          f"{FENSTER}-Tage-Fensters")
    if a.positivkontrolle:
        print(f"  ⚠️ POSITIVKONTROLLE {100 * a.positivkontrolle:.1f} % - "
              f"diese Zahlen pruefen das Werkzeug, nicht den Markt")

    bericht = {"reihen": len(symbole), "horizonte": {}}
    for hz in HORIZONTE:
        r = messe(c, v, hz, kontrolle=a.positivkontrolle)
        bericht["horizonte"][hz] = r
        print("\n" + "-" * 78)
        print(f"HORIZONT {hz} HANDELSTAGE   (marktbereinigt, je Termin "
              f"gemittelt)")
        print("-" * 78)
        for l in LAGEN:
            x = r[l]
            if x["mittel"] is None:
                print(f"  {l:16} {x['termine']:5} Termine - zu wenige, "
                      f"KEIN URTEIL")
                continue
            print(f"  {l:16} {x['termine']:5} Termine   "
                  f"{100 * x['mittel']:+6.2f} %   t = {x['t']:+5.2f}")
        # Der eigentliche Vergleich: Anstieg GEGEN Seitwaerts.
        an, sw = r["nach Anstieg"], r["seitwaerts"]
        if an["mittel"] is not None and sw["mittel"] is not None:
            d = an["mittel"] - sw["mittel"]
            se = math.sqrt(an["se"] ** 2 + sw["se"] ** 2)
            tt = d / se if se > 0 else 0.0
            print(f"\n  UNTERSCHIED (Anstieg minus Seitwaerts): "
                  f"{100 * d:+.2f} %   t = {tt:+.2f}")
            bericht["horizonte"][hz]["unterschied"] = {
                "wert": float(d), "t": float(tt)}

    if a.placebo:
        print("\n" + "-" * 78)
        print(f"PLACEBO - {a.placebo} Laeufe mit gewuerfelten Lagen")
        print("-" * 78)
        rng = np.random.default_rng(20260820)
        hoechste = []
        for _ in range(a.placebo):
            beste = 0.0
            for hz in HORIZONTE:
                r = messe(c, v, hz, mischen=rng)
                an, sw = r["nach Anstieg"], r["seitwaerts"]
                if an["mittel"] is None or sw["mittel"] is None:
                    continue
                se = math.sqrt(an["se"] ** 2 + sw["se"] ** 2)
                if se > 0:
                    beste = max(beste,
                                abs(an["mittel"] - sw["mittel"]) / se)
            hoechste.append(beste)
        schwelle = float(np.quantile(hoechste, 0.95))
        print(f"  groesster Zufallswert {max(hoechste):.2f}")
        print(f"  EMPIRISCHE SCHWELLE (95 %): |t| >= {schwelle:.2f}")
        bericht["placebo_schwelle"] = schwelle

    print("\n" + "=" * 78)
    print("Der Vergleich, um den es geht, steht in der Zeile UNTERSCHIED.")
    print("Ein negativer Wert hiesse: nach einem Anstieg folgt auf hohen")
    print("Umsatz eine SCHLECHTERE Entwicklung als in der Seitwaertsphase -")
    print("also genau das, was das Modell bei ETH behauptet hat.")
    print("=" * 78)
    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(
            json.dumps(bericht, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
