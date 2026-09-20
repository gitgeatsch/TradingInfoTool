# -*- coding: utf-8 -*-
"""2d: DIE 0,18 %/TAG MESSEN - an den eigenen Hebelpositionen.

## Warum ueberhaupt

`tage_bis_liquidation_am_stop` und `estimate_liquidation_price` rechnen mit
`funding_rate_daily_pct = 0.18`, nirgends ueberschrieben. Diese eine Zahl
entscheidet allein, ob eine Hebelstufe in der Mail ,nicht sicher` heisst -
und sie geht LINEAR in die Zeit ein.

Sie ist als ,Bitpanda-Doku-Angabe` gekennzeichnet
(`bitpanda_margin_positions.py:35`), steht aber in KEINEM Befund, und das
Regelwerksmanual nennt beim Pruefen ,0,08 Prozentpunkte Abweichung im
Schnitt` - auf 0,18 sind das 44 Prozent.

## Was gemessen wird

Je GESCHLOSSENER Position ist die tatsaechliche Gebuehr beobachtbar:

    fee_pct = fee_crypto * sell_price / sell_value * 100
    Modell:   fee_pct = BASIS + RATE * haltedauer_tage

Also eine Gerade. Achsenabschnitt soll 0,3 sein, Steigung 0,18.

## ⚠️⚠️ DER ZIRKELSCHLUSS, UND WIE ER UMGANGEN WIRD

Die Liquidationserkennung benutzt GENAU diese 0,18: eine Position gilt als
,wahrscheinlich liquidiert`, wenn die Gebuehr mehr als 0,7 Prozentpunkte
ueber `0,3 + 0,18 * Tage` liegt. Wer die so Markierten ausschliesst und
dann 0,18 misst, hat die Annahme in die Messung gesteckt.

Deshalb DREI Schaetzungen nebeneinander:

    Theil-Sen   medianbasiert, vertraegt Ausreisser - auf ALLEN Positionen,
                ohne irgendetwas auszuschliessen. Das ist die Hauptzahl.
    Kleinste Q. auf allen - zum Vergleich, anfaellig fuer die 4 Liquidationen
    ohne Verd.  Kleinste Quadrate ohne die Markierten - die zirkulaere
                Variante, ausdruecklich als solche gekennzeichnet

Sagen alle drei dasselbe, ist der Zirkel folgenlos.

## ⚠️⚠️ WOHER DIE POSITIONEN KOMMEN - und warum NICHT aus der Datei

Erster Versuch: `reconstruct_margin_positions` auf die Buchungsdatei. Das
gibt nur **4** geschlossene Positionen statt 184. Grund, am Code gesehen:
917 `open`- gegen 315 `close`-Ereignisse - der Bestand laeuft ueber viele
Kaeufe auf, und eine einzelne Schliessung gilt dann als TEILVERKAUF
(`ist_vollstaendiger_verkauf`), die Position bleibt offen. Die 184 in der
Datenbank entstanden aus der VOLLEN API-Historie mit fortgeschriebenem
Zustand ueber inkrementelle Syncs.

➔ Deshalb: **Positionen aus der Datenbank** (Ergebnis des echten Syncs),
**Gebuehren aus den Buchungen**, verbunden ueber
`letzte_transaktion_unix_timestamp`. Beides nur lesend.

## ⚠️ Und die Bindung an den echten Code

Die Gebuehr je Schliessung gibt `reconstruct_margin_positions` nicht zurueck,
also muss sie hier aus denselben Buchungen gezogen werden. Damit das keine
abweichende Nachbildung ist, wird sie BEWIESEN: mit meiner Extraktion muss
die 0,7-Punkte-Regel GENAU die Positionen markieren, die der echte Code als
`wahrscheinlich_liquidiert` fuehrt - keine mehr, keine weniger.

⚠️ NUR LESEND. Die Buchungsdatei wird gelesen, nichts geschrieben, kein
Netzzugriff (`reconstruct_margin_positions` ist eine reine Funktion).
"""
import io
import json
import os
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir("D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")
sys.path.insert(0, "D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")

import numpy as np                                            # noqa: E402
from api.bitpanda import BitpandaTransaction                  # noqa: E402
import importer.bitpanda_margin_positions as MP               # noqa: E402

# ⚠️ BEIDE QUELLEN SIND ARGUMENTE, keine festen Pfade. Die Sicherung
# liegt je Geraet anderswo, und ein Werkzeug, das nur an einem Ort
# laeuft, ist keines. Vorgabe ist der Austauschordner bzw. eine
# Kopie neben dem Skript - beides wird geprueft, BEVOR gerechnet
# wird, mit einer Meldung statt eines Stapelabzugs.
#
#     python phase4_2d_finanzierungsrate.py --db <sicherung.db>
#            [--buchungen <bitpanda_transaktionen.json>]
#
# ⚠️⚠️ NIE die Standard-DB uebergeben - am Notebook ist sie die
# PRODUKTION. Das Skript oeffnet `mode=ro`, aber der Pfad gehoert
# trotzdem auf eine SICHERUNG.
QUELLE = ("K:/My Drive/Claude_Austauschordner/Notebook_Analysedaten/"
          "bitpanda_transaktionen.json")


def _pfad(flagge: str, vorgabe: str) -> str:
    """Ein Pfad aus der Befehlszeile, sonst die Vorgabe."""
    a = sys.argv[1:]
    return a[a.index(flagge) + 1] if flagge in a else vorgabe


def lade() -> list:
    q = _pfad("--buchungen", QUELLE)
    if not os.path.exists(q):
        raise SystemExit(
            "Buchungsdatei nicht gefunden: %s%s   mit --buchungen "
            "<datei> einen anderen Pfad setzen" % (q, chr(10)))
    roh = json.load(io.open(q, encoding="utf-8"))
    zeilen = roh if isinstance(roh, list) else (
        roh.get("transaktionen") or roh.get("data") or [])
    aus = []
    for z in zeilen:
        aus.append(BitpandaTransaction(
            type=z.get("type"), in_or_out=z.get("in_or_out"),
            cryptocoin_symbol=z.get("cryptocoin_symbol"),
            amount_cryptocoin_wallet=float(
                z.get("amount_cryptocoin_wallet") or 0.0),
            unix_timestamp=int(z.get("unix_timestamp") or 0),
            trade_price=z.get("trade_price"),
            trade_amount_fiat=z.get("trade_amount_fiat"),
            trade_amount_cryptocoin=z.get("trade_amount_cryptocoin"),
            trade_fiat_id=z.get("trade_fiat_id"),
            tags=list(z.get("tags") or [])))
    return aus


def theil_sen(x, y):
    """Median aller paarweisen Steigungen - vertraegt Ausreisser."""
    st = []
    for i in range(len(x)):
        for j in range(i + 1, len(x)):
            if abs(x[j] - x[i]) > 1e-9:
                st.append((y[j] - y[i]) / (x[j] - x[i]))
    if not st:
        return None, None
    m = float(np.median(st))
    b = float(np.median(np.asarray(y) - m * np.asarray(x)))
    return m, b


def main() -> int:
    txs = lade()
    print("=" * 96)
    print("2d - DIE FINANZIERUNGSRATE MESSEN (eigene Hebelpositionen)")
    print("=" * 96)
    print("  %d Buchungen geladen" % len(txs))
    import sqlite3
    from types import SimpleNamespace
    dbp = _pfad("--db", os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "prod_1432.db")).replace("\\", "/")
    if not os.path.exists(dbp):
        raise SystemExit(
            "Sicherung nicht gefunden: %s%s   mit --db <sicherung.db> "
            "setzen - NIE die Standard-DB, am Notebook ist sie "
            "die PRODUKTION" % (dbp, chr(10)))
    c = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True)
    c.row_factory = sqlite3.Row
    zu = [SimpleNamespace(**dict(r)) for r in c.execute(
        "SELECT symbol, status, eroeffnet_am, geschlossen_am, "
        "letzte_transaktion_unix_timestamp FROM hebel_positions "
        "WHERE geschlossen_am IS NOT NULL")]
    print("  %d geschlossene Positionen aus der Produktionssicherung "
          "(Ergebnis des echten Syncs)" % len(zu))
    markiert = {(p.symbol, p.geschlossen_am) for p in zu
                if p.status == "wahrscheinlich_liquidiert"}
    print("  davon `wahrscheinlich_liquidiert`: %d" % len(markiert))

    # ---- Die Gebuehr je Schliessung, aus denselben Buchungen -----------
    margin = [t for t in txs if any("margin" in g.lower() for g in t.tags)]
    by_ts = defaultdict(list)
    for t in margin:
        by_ts[t.unix_timestamp].append(t)
    schliessungen = {}
    for ts, gruppe in sorted(by_ts.items()):
        flach = [g.lower() for t in gruppe for g in t.tags]
        if not any("close" in g for g in flach):
            continue
        sym = next((t.cryptocoin_symbol for t in gruppe
                    if t.cryptocoin_symbol and t.cryptocoin_symbol != "EURCV"),
                   None)
        if sym is None:
            continue
        verkauf = [t for t in gruppe
                   if t.type == "sell" and t.cryptocoin_symbol == sym]
        gebuehr = [t for t in gruppe
                   if any("fee" in g.lower() for g in t.tags)]
        wert = sum(t.trade_amount_fiat or 0.0 for t in verkauf)
        preis = next((t.trade_price for t in verkauf if t.trade_price), None)
        menge = sum(abs(t.amount_cryptocoin_wallet) for t in gebuehr)
        if wert and preis:
            schliessungen[(sym, ts)] = 100.0 * menge * preis / wert

    # ---- ⚠️ DIE BINDUNG: reproduziert meine Extraktion die Markierung? -
    from datetime import datetime, timezone
    paare = []
    for p in zu:
        ts = p.letzte_transaktion_unix_timestamp
        pct = schliessungen.get((p.symbol, ts))
        if pct is None:
            continue
        auf = datetime.fromisoformat(p.eroeffnet_am).timestamp()
        tage = (ts - auf) / 86400.0
        paare.append((p.symbol, p.geschlossen_am, tage, pct,
                      p.status == "wahrscheinlich_liquidiert"))
    print("  %d davon mit ablesbarer Gebuehr" % len(paare))

    schwelle = MP._LIQUIDATIONS_VERDACHT_SCHWELLE_PROZENTPUNKTE
    basis = MP._ERWARTETE_GEBUEHR_BASIS_PROZENT
    rate = MP._ERWARTETE_GEBUEHR_PRO_TAG_PROZENT
    meine = {(s, g) for s, g, t, p, _ in paare
             if (p - (basis + rate * t)) > schwelle}
    echte = {(s, g) for s, g, t, p, m in paare if m}
    print()
    print("  ⚠️ BINDUNG AN DEN ECHTEN CODE: meine Extraktion markiert %d, "
          "der Code %d" % (len(meine), len(echte)))
    print("     %s" % ("✔ DECKUNGSGLEICH - die Extraktion ist die des Codes"
                       if meine == echte else
                       "✖ ABWEICHUNG: nur bei mir %s / nur im Code %s"
                       % (sorted(meine - echte), sorted(echte - meine))))
    if meine != echte:
        return 1

    # ---- Die drei Schaetzungen ----------------------------------------
    x = np.array([t for _, _, t, _, _ in paare], float)
    y = np.array([p for _, _, _, p, _ in paare], float)
    frei = np.array([not m for _, _, _, _, m in paare])
    print()
    print("=" * 96)
    print("DIE SCHAETZUNGEN - Modell  Gebuehr %% = BASIS + RATE x Haltetage")
    print("=" * 96)
    print("  Vorgabe im Code:  BASIS %.2f   RATE %.2f" % (basis, rate))
    print()
    m1, b1 = theil_sen(x, y)
    print("  %-38s RATE %s   BASIS %s   n=%d"
          % ("Theil-Sen (robust, ALLE)",
             "%+.4f" % m1 if m1 is not None else "-",
             "%+.4f" % b1 if b1 is not None else "-", len(x)))
    if len(x) >= 2:
        m2, b2 = np.polyfit(x, y, 1)
        print("  %-38s RATE %+.4f   BASIS %+.4f   n=%d"
              % ("kleinste Quadrate (ALLE)", m2, b2, len(x)))
    if frei.sum() >= 2:
        m3, b3 = np.polyfit(x[frei], y[frei], 1)
        print("  %-38s RATE %+.4f   BASIS %+.4f   n=%d"
              % ("kleinste Quadrate OHNE Markierte ⚠️zirkulaer",
                 m3, b3, int(frei.sum())))
    # ---- ⚠️⚠️ DIE ZERLEGUNG - eine Regression auf einer schiefen Achse
    # verbirgt mehr, als sie zeigt. Median-Haltedauer 0,30 Tage: die
    # Steigung haengt an wenigen langen Positionen, der Achsenabschnitt
    # an sehr vielen kurzen. Also beides getrennt ansehen.
    print()
    print("=" * 96)
    print("DIE ZERLEGUNG NACH HALTEDAUER - Modell = %.2f + %.2f x Tage"
          % (basis, rate))
    print("=" * 96)
    print("  %-16s %5s %10s %10s %10s %10s"
          % ("Haltedauer", "n", "Median Geb.", "Modell", "Differenz", "Median t"))
    kanten = [(0, 0.25), (0.25, 1), (1, 2), (2, 5), (5, 10), (10, 99)]
    for u, o in kanten:
        m = (x >= u) & (x < o)
        if not m.any():
            continue
        mt = float(np.median(x[m]))
        mg = float(np.median(y[m]))
        mod = basis + rate * mt
        print("  %-16s %5d %10.3f %10.3f %+10.3f %10.2f"
              % ("%g bis %g Tage" % (u, o), int(m.sum()), mg, mod,
                 mg - mod, mt))
    # ---- GEGENPROBE: haengt der Versatz an einem Mass, einem Symbol
    # oder einer Zeit? Ein konstanter Versatz muss ueberall derselbe sein.
    rest = y - (basis + rate * x)
    print()
    print("=" * 96)
    print("GEGENPROBE ZUM VERSATZ (Gebuehr minus Modell)")
    print("=" * 96)
    print("  Median %+.4f · Mittelwert %+.4f · ohne die 4 Markierten "
          "Median %+.4f"
          % (float(np.median(rest)), float(np.mean(rest)),
             float(np.median(rest[frei]))))
    je = {}
    for (sym, _, _, _, _), r in zip(paare, rest):
        je.setdefault(sym, []).append(r)
    gross = sorted(((k, v) for k, v in je.items() if len(v) >= 8),
                   key=lambda t: -len(t[1]))
    print("  je Symbol (mindestens 8 Faelle):")
    for k, v in gross[:8]:
        print("    %-8s n=%-4d Median %+.4f" % (k, len(v), float(np.median(v))))
    jahr = {}
    for (_, g, _, _, _), r in zip(paare, rest):
        jahr.setdefault(str(g)[:7], []).append(r)
    print("  je Monat (mindestens 8 Faelle):")
    for k in sorted(jahr):
        if len(jahr[k]) >= 8:
            print("    %-8s n=%-4d Median %+.4f"
                  % (k, len(jahr[k]), float(np.median(jahr[k]))))
    print()
    print("  Haltedauer: Median %.2f Tage, Spanne %.2f bis %.2f"
          % (float(np.median(x)), float(x.min()), float(x.max())))
    print("  Gebuehr:    Median %.3f %%, Spanne %.3f bis %.3f"
          % (float(np.median(y)), float(y.min()), float(y.max())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
