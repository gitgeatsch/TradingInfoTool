# -*- coding: utf-8 -*-
"""K7 - Abgleich der Liquidationsformel am ECHTEN Bitpanda-Hebelbuch.

**28.09.2026.** Voranalyse `Basisinfos/Voranalyse_K7_Abgleich_echte_Positionen_28_09.md`,
J1 bis J10 abgestimmt (Nutzer: *ja, J1 bis J10 wie empfohlen, bauen und messen*).

FRAGE  Haetten Binance-Markpreis und Binance-Spot-Tief mit der Bitpanda-Formel
       dieselben Liquidationen ausgeloest wie in echt - zur selben Zeit - und
       keine, die es nicht gab?

⛔ ZAEHLEINHEIT KORRIGIERT (erste Fassung, 28.09. abends): sie rechnete auf den
188 Positionen aus `hebel_positions`. Der Importer schliesst dort bei JEDER
Schlussbuchung die Position ab - aber 278 von 315 Schlussbuchungen sind
TEILSCHLIESSUNGEN (der Kredit bleibt stehen). Nur bei 15 von 188 Positionen
war die Rueckzahlung gleich dem summierten Kredit. Das BUCH je Symbol dagegen
geht auf: Menge und Kredit laufen fuer jedes Symbol exakt auf 0 zurueck, in
37 Abschnitten. Einheit ist darum der ABSCHNITT des Buchs (Kredit von 0 bis 0);
die Frage und die Kriterien J5/J6 sind unveraendert.

J1  Buch je Symbol, Ereignis fuer Ereignis: ein KAUF erhoeht Menge Q, Kredit K
    und setzt einen Posten fuer die Finanzierung; eine TEILSCHLIESSUNG kuerzt Q
    und K im gebuchten Verhaeltnis (Posten anteilig mit). Liquidation, sobald
    Tief <= (K + F) / (Q (1 - m)). Bei einem Kauf und einem Schluss ist das genau
    E (1 - 1/L + t f) / (1 - m)  (K6 `liq_schwelle`, geprueft in P3).
    F = Summe der Posten x 0,18 %/Tag x angefangene Stunden seit dem Kauf.
J2  Faktor je Kauf = Bitpanda-Kurs (EUR) / Kurs der Reihe zur Kaufsekunde
    (linear in der Stunde); Kredit und Kaufwert mit dem Faktor DIESES Kaufs.
J3  Reihen: Binance-MARKPREIS (Hauptmass), Binance-SPOT, dazu am Schluss der
    Bitpanda-AUSFUEHRUNGSPREIS.
J4  gezaehlt ab der Stunde NACH dem ersten Kauf bis zur Stunde VOR dem letzten
    Schluss; die Schlussstunde gesondert; in einer Stunde mit Buchung gilt der
    Stand VOR der Buchung (Kennzeichen Buchungsstunde).
J5  je Reihe und m in {0,09; 0,0476}: Treffer, Zeitfehler, Fehlalarme (Abschnitte
    ohne Liquidation mit Treffer VOR dem Schluss), m-Intervall (m_krit = 1 -
    (K + F) / (Q Tief); Untergrenze max ueber die Liquidationen, Obergrenze min
    ueber die Gegenfaelle). Crash und Ruhe getrennt.
J6  Markpreis Hauptmass, wenn er alle trifft, Zeitfehler <= und Fehlalarme <= Spot;
    m = 0,09 haelt, wenn es im Intervall liegt. Sonst beide mitfuehren, vorlegen.
J7  Nullwelt: die Abschnitte um +-7..60 Tage verschoben, 40 Ziehungen.
J8  Abgleich, kein Nachweis; ein Abschnitt ohne vollstaendige Reihe faellt heraus.
J9  liest Sicherungskopie (`immutable=1`) und Buchungsdatei, schreibt NICHTS;
    Standard-DB verweigert; unveraendert nachgewiesen (P0).
J10 jede Zahl mit und ohne den 10./11.10.2025 (Nutzer: *Black Swan*).

    python messe_k7_abgleich.py --db <sicherung.db> [--buchungen <json>] [--spur <nr>]
"""
from __future__ import annotations

import argparse
import io
import json
import math
import os
import random
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone

HIER = os.path.dirname(os.path.abspath(__file__))
STANDARD_DB = os.path.join(HIER, "data", "tradinginfotool.db")
STUNDEN_DB = os.path.join(HIER, "data", "stundenkurse.db")
EINGESTELLT_DB = os.path.join(HIER, "data", "eingestellt_historie.db")
MARK_DB = os.path.join(HIER, "data", "markpreis_historie.db")
BUCHUNGEN = "K:/My Drive/Claude_Austauschordner/Notebook_Analysedaten/bitpanda_transaktionen.json"
FIN = 0.0018                      # 0,18 %/Tag (2.493: die Rate haelt)
MARGEN = (0.09, 0.0476)           # H8/K6b
SCHWARZ = ("2025-10-10 00:00", "2025-10-12 00:00")   # J10
ZIEHUNGEN, VERSATZ = 40, (7, 60)  # J7
SAAT = 20260928


def stunde(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:00")


def hstart(ts: float) -> int:
    return int(ts // 3600) * 3600


def lade_liquidationen(pfad: str) -> list:
    """Die als `wahrscheinlich_liquidiert` gefuehrten Schluesse (Symbol, Zeit, id)."""
    c = sqlite3.connect("file:%s?immutable=1" % pfad, uri=True)
    r = [(s, datetime.fromisoformat(z).timestamp(), i) for i, s, z in c.execute(
        "SELECT id, symbol, geschlossen_am FROM hebel_positions WHERE status='wahrscheinlich_liquidiert'")]
    n = c.execute("SELECT COUNT(*) FROM hebel_positions").fetchone()[0]
    c.close()
    return r, n


def lade_buch(pfad: str) -> dict:
    """-> {symbol: [(ts, art, dict)]}, art 'auf' (Kauf) oder 'zu' (Schluss, auch teilweise)."""
    roh = json.load(io.open(pfad, encoding="utf-8"))
    tx = [t for t in roh["transaktionen"] if any("margin" in g.lower() for g in t.get("tags", []))]
    g = defaultdict(list)
    for t in tx:
        g[t["unix_timestamp"]].append(t)
    aus = defaultdict(list)
    for ts, grp in sorted(g.items()):
        tags = {x for t in grp for x in t.get("tags", [])}
        sym = next((t["cryptocoin_symbol"] for t in grp
                    if t.get("cryptocoin_symbol") and t["cryptocoin_symbol"] != "EURCV"), None)
        if not sym:
            continue
        if "margin_trading.close" in tags:
            rep = [t for t in grp if "margin_trading.repay" in t.get("tags", [])]
            aus[sym].append((ts, "zu", dict(
                raus=sum(t["amount_cryptocoin_wallet"] for t in grp
                         if t["cryptocoin_symbol"] == sym and t["in_or_out"] == "outgoing"),
                repay=sum(t["trade_amount_fiat"] or 0 for t in rep),
                preis=next((t["trade_price"] for t in rep if t.get("trade_price")), None))))
        elif "margin_trading.open" in tags:
            kauf = [t for t in grp if t["type"] == "buy" and t.get("cryptocoin_symbol") == sym]
            if kauf:
                aus[sym].append((ts, "auf", dict(
                    menge=sum(t["trade_amount_cryptocoin"] for t in kauf),
                    wert=sum(t["trade_amount_fiat"] for t in kauf),
                    preis=kauf[0]["trade_price"],
                    kredit=sum(t["amount_cryptocoin_wallet"] for t in grp
                               if "margin_trading.borrow" in t.get("tags", [])))))
    return aus


def abschnitte(buch: dict) -> list:
    """Das Buch je Symbol in Abschnitte (Kredit von 0 bis 0); je Schluss das
    gebuchte Verhaeltnis rQ (Menge danach / vorher) und rK (Kredit)."""
    aus = []
    for sym, ev in buch.items():
        Q = K = 0.0
        cur = None
        for ts, art, e in ev:
            if art == "auf":
                if cur is None:
                    cur = dict(symbol=sym, ereignisse=[], max_hebel=0.0)
                Q += e["menge"]; K += e["kredit"]
                cur["ereignisse"].append((ts, "auf", e))
                cur["max_hebel"] = max(cur["max_hebel"], Q * e["preis"] / max(Q * e["preis"] - K, 1e-9))
            else:
                if cur is None:
                    continue
                Qn, Kn = Q - e["raus"], K - e["repay"]
                rQ = max(Qn, 0.0) / Q if Q > 0 else 0.0
                rK = max(Kn, 0.0) / K if K > 0 else 0.0
                cur["ereignisse"].append((ts, "zu", dict(e, rQ=rQ, rK=rK, Q_vor=Q, K_vor=K)))
                Q, K = Qn, Kn
                # Ende, sobald der Kredit zurueckgezahlt ist (unter 1 EUR). Ein Staubrest an
                # Menge bleibt stehen (18.11. SUI: 0,1 Stueck gegen 0,26 EUR Kredit) - er
                # zaehlte sonst als tiefe Unterdeckung und hielt den Abschnitt kuenstlich offen
                if abs(K) < 1.0:
                    cur.update(auf=cur["ereignisse"][0][0], zu=ts, rest=(Q, K), staub=Q * (e["preis"] or 0),
                               kaeufe=sum(1 for x in cur["ereignisse"] if x[1] == "auf"),
                               teil=sum(1 for x in cur["ereignisse"] if x[1] == "zu") - 1)
                    aus.append(cur); cur = None; Q = K = 0.0
        if cur is not None:
            cur.update(auf=cur["ereignisse"][0][0], zu=None, rest=(Q, K))
            aus.append(cur)
    aus.sort(key=lambda a: a["auf"])
    return aus


class Reihe:
    """Stundenkurse je Symbol: {stunde: (open, low, close)}; fehlende oder
    gesperrte Stunden sind nicht da."""

    def __init__(self, art: str):
        self.art, self.cache = art, {}
        if art == "spot":
            self.dbs = [sqlite3.connect("file:%s?mode=ro" % STUNDEN_DB, uri=True),
                        sqlite3.connect("file:%s?mode=ro" % EINGESTELLT_DB, uri=True)]
        else:
            self.dbs = [sqlite3.connect("file:%s?mode=ro" % MARK_DB, uri=True)]
            self.sperre = {(r[0], r[1]) for r in self.dbs[0].execute(
                "SELECT symbol, monat FROM _abweichung WHERE gesperrt=1")}

    def daten(self, sym: str) -> dict:
        if sym not in self.cache:
            d = {}
            if self.art == "spot":
                for db in self.dbs:
                    for st, o, l, cl in db.execute("SELECT stunde, open, low, close FROM stundenkurse "
                                                   "WHERE symbol=?", (sym,)):
                        if o and l and cl:
                            d.setdefault(st, (o, l, cl))
            else:
                for st, o, l, cl in self.dbs[0].execute(
                        "SELECT stunde, open/faktor, low/faktor, close/faktor FROM markpreis WHERE symbol=?", (sym,)):
                    if o and l and cl and (sym, st[:7]) not in self.sperre:
                        d[st] = (o, l, cl)
            self.cache[sym] = d
        return self.cache[sym]

    def kurs_zu(self, sym: str, ts: float):
        """Kurs zur Sekunde: linear zwischen Oeffnung und Schluss der Stunde."""
        z = self.daten(sym).get(stunde(ts))
        if not z:
            return None
        a = (ts - hstart(ts)) / 3600.0
        return z[0] + (z[2] - z[0]) * a


def verlauf(ab: dict, reihe: Reihe, verschiebung: float = 0.0, spur: bool = False, ohne_schwarz: bool = False):
    """-> dict(stunden=[(h, m_krit, buchungsstunde, schlussstunde)], faktoren) oder
    None, wenn der Reihe eine Stunde fehlt. In der Nullwelt kauft derselbe
    Betrag zum Kurs der verschobenen Zeit; die Schluesse kuerzen im echten
    Verhaeltnis."""
    sym = ab["symbol"]
    d = reihe.daten(sym)
    schritte, faktoren = [], []        # (t, art, daten in Einheiten der Reihe)
    for ts, art, e in ab["ereignisse"]:
        t2 = ts + verschiebung
        if art == "auf":
            ref_echt = reihe.kurs_zu(sym, ts)
            ref = reihe.kurs_zu(sym, t2) if verschiebung else ref_echt
            if not ref_echt or not ref:
                return None
            fak = e["preis"] / ref_echt
            faktoren.append(fak)
            schritte.append((t2, "auf", (e["kredit"] / fak, e["wert"] / fak, e["wert"] / fak / ref)))
        else:
            schritte.append((t2, "zu", (e["rQ"], e["rK"])))
    h0 = hstart(schritte[0][0]) + 3600
    hz = hstart(schritte[-1][0])
    buchung = {hstart(s[0]) for s in schritte[1:-1]}
    posten, K, Q, i, hebel_kauf = [], 0.0, 0.0, 0, 0.0
    out = []
    for h in range(h0, hz + 3600, 3600):
        while i < len(schritte) - 1 and schritte[i][0] < h:      # Stand VOR einer Buchung in dieser Stunde
            t, art, x = schritte[i]
            if art == "auf":
                K += x[0]; Q += x[2]; posten.append([t, x[1]])
                preis = x[1] / x[2]                         # Kaufkurs in Einheiten der Reihe
                hebel_kauf = Q * preis / max(Q * preis - K, 1e-9)
            else:
                K *= x[1]; Q *= x[0]
                for p in posten:
                    p[1] *= x[0]
            i += 1
        z = d.get(stunde(h))
        if not z:
            return None
        if Q <= 0 or K * min(faktoren) < 1.0:          # kein nennenswerter Kredit (unter 1 EUR)
            continue
        if ohne_schwarz and SCHWARZ[0] <= stunde(h) < SCHWARZ[1]:
            continue
        F = sum(v * FIN * math.ceil((h + 3600 - t) / 3600.0) / 24.0 for t, v in posten)
        mk = 1.0 - (K + F) / (Q * z[1])
        out.append((h, mk, h in buchung, h == hz, hebel_kauf))   # Hebel des Buchs nach dem letzten Kauf
        if spur:
            print("   %s  Tief %.6g  K %.4f  F %.4f  Q %.6f  Grenze m=0,09: %.6g  m_krit %.4f%s%s" % (
                stunde(h), z[1], K, F, Q, (K + F) / (Q * 0.91), mk,
                "  (Buchungsstunde)" if h in buchung else "", "  (Schlussstunde)" if h == hz else ""))
    return dict(stunden=out, faktoren=faktoren)


def auswerten(v: dict, m: float):
    """-> (erste Stunde mit Treffer vor dem Schluss | None, Treffer in der Schlussstunde, in Buchungsstunde)"""
    vor = [s for s in v["stunden"] if not s[3] and s[1] <= m]
    schluss = any(s[3] and s[1] <= m for s in v["stunden"])
    return (vor[0][0] if vor else None), schluss, bool(vor and vor[0][2])


def eur_grenze(ab: dict, m: float = 0.09):
    """Liquidationsgrenze in EUR (Bitpanda) unmittelbar vor dem letzten Schluss."""
    K = Q = 0.0
    posten = []
    tz = ab["zu"]
    for ts, art, e in ab["ereignisse"][:-1]:
        if art == "auf":
            K += e["kredit"]; Q += e["menge"]; posten.append([ts, e["wert"]])
        else:
            K *= e["rK"]; Q *= e["rQ"]
            for p in posten:
                p[1] *= e["rQ"]
    F = sum(v * FIN * math.ceil((tz - t) / 3600.0) / 24.0 for t, v in posten)
    return K, F, Q, (K + F) / (Q * (1 - m))


SIGNATUR = 0.5      # Prozentpunkte ueber dem Modell - Bitpanda-Zwangsgebuehr 1 %


def gebuehr_signatur(abs_: list, pfad: str) -> list:
    """Schlussgebuehr gegen das Modell 0,30 % + 0,18 %/Tag, mit dem ALTER DER
    POSTEN (mengengewichtet, bei Teilschliessungen anteilig gekuerzt) statt
    ab dem ersten Kauf. -> [(differenz, k, ts, vollschluss, rest_anteil)].
    Nutzerfrage 28.09. (AVAX/MORPHO am 10.10.): die alte Erkennung rechnet die
    Haltedauer ab dem ersten Kauf - bei Nachkaeufen zu lang, das Modell zu
    hoch, und die +1 % gehen darin unter."""
    roh = json.load(io.open(pfad, encoding="utf-8"))
    byts = defaultdict(list)
    for t in roh["transaktionen"]:
        if any("margin" in g for g in t.get("tags", [])):
            byts[t["unix_timestamp"]].append(t)
    aus = []
    for k, ab in enumerate(abs_):
        for ts, art, e in ab["ereignisse"]:
            if art != "zu" or not e["raus"]:
                continue
            grp = byts[ts]
            fee = sum(t["amount_cryptocoin_wallet"] for t in grp if "margin_trading.fee" in t["tags"])
            zur = sum(t["amount_cryptocoin_wallet"] for t in grp
                      if "margin_trading.close" in t["tags"] and t["in_or_out"] == "incoming")
            posten = []
            for ts2, a2, e2 in ab["ereignisse"]:
                if ts2 >= ts:
                    break
                if a2 == "auf":
                    posten.append([ts2, e2["menge"]])
                else:
                    for q in posten:
                        q[1] *= e2["rQ"]
            q = sum(x[1] for x in posten)
            alter = sum(x[1] * (ts - x[0]) for x in posten) / q / 86400.0 if q else 0.0
            aus.append((100 * fee / e["raus"] - (0.30 + 0.18 * alter), k, ts, ts == ab["zu"], zur / e["raus"]))
    return aus


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help="die SICHERUNGSKOPIE, nie die Standard-DB")
    ap.add_argument("--buchungen", default=BUCHUNGEN)
    ap.add_argument("--spur", type=int, help="nur dieser Abschnitt (Nummer aus der Liste), mit Stundenspur")
    ap.add_argument("--wahrheit", choices=("gefuehrt", "gebuehr"), default="gefuehrt",
                    help="gefuehrt = status wahrscheinlich_liquidiert (vorab festgelegt); gebuehr = Gebuehrensignatur "
                         "mit dem Alter der Posten (R1-Korrektur, Nutzerfrage AVAX/MORPHO)")
    a = ap.parse_args()
    if os.path.abspath(a.db).lower() == os.path.abspath(STANDARD_DB).lower() \
            or os.path.basename(a.db).lower() == "tradinginfotool.db":
        raise SystemExit("⛔ verweigert: %s ist die Standard-/Produktionsdatei - eine Sicherungskopie angeben" % a.db)
    vorher = (os.path.getsize(a.db), os.path.getmtime(a.db))

    liqs, n_imp = lade_liquidationen(a.db)
    buch = lade_buch(a.buchungen)
    abs_ = abschnitte(buch)
    print("=" * 110)
    print("K7 - ABGLEICH AM ECHTEN BITPANDA-HEBELBUCH · Sicherung %s · Buchungen %s" % (
        os.path.basename(a.db), os.path.basename(a.buchungen)))
    print("=" * 110)

    # ── P1/P2: das Buch geht auf
    offen = [x for x in abs_ if x["zu"] is None]
    rest = max(abs(x["rest"][1]) for x in abs_ if x["zu"])
    staub = max(x.get("staub", 0.0) for x in abs_ if x["zu"])
    print("P1 Buch: %d Symbole · %d Abschnitte (Kredit von 0 bis 0) · offen am Dateiende %d · "
          "Kaeufe %d · Teilschliessungen %d · Importer-Positionen dagegen %d" % (
              len(buch), len(abs_), len(offen), sum(x.get("kaeufe", 0) for x in abs_),
              sum(x.get("teil", 0) for x in abs_), n_imp))
    print("P2 jeder Abschnitt endet mit Kredit unter 1 EUR: groesster Restkredit %.2f EUR, groesster Staubrest %.2f EUR %s" % (
        rest, staub, "✔" if rest < 1 and staub < 5 and not offen else "⛔"))
    for ab in abs_:
        ab["liq"] = next((str(i) for s, z, i in liqs if s == ab["symbol"] and ab["zu"] and abs(z - ab["zu"]) <= 1), None)
        # J10: ein CRASH-Fall ENDET am 10./11.10.; bei allen anderen fallen in der
        # Ansicht OHNE die Stunden dieser zwei Tage heraus
        ab["schwarz"] = ab["zu"] is not None and SCHWARZ[0] <= stunde(ab["zu"]) < SCHWARZ[1]
    zugeordnet = sum(1 for ab in abs_ if ab["liq"])
    sig = gebuehr_signatur(abs_, a.buchungen)
    hoch = [x for x in sig if x[0] > SIGNATUR]
    rest_d = sorted(x[0] for x in sig if x[0] <= SIGNATUR)
    print("P4 Gebuehrensignatur (Alter der Posten): %d Schluesse · ueber +%.1f Punkte: %d (%s) · alle uebrigen "
          "zwischen %+.2f und %+.2f, Median %+.2f" % (
              len(sig), SIGNATUR, len(hoch), ", ".join("%s %s %+.2f" % (abs_[x[1]]["symbol"], stunde(x[2]), x[0]) for x in hoch),
              rest_d[0], rest_d[-1], rest_d[len(rest_d) // 2]))
    gef = {k for k, ab in enumerate(abs_) if ab["liq"]}
    sigk = {x[1] for x in hoch if x[3]}
    print("   gefuehrte Liquidationen mit Signatur: %d von %d · Signatur ohne Vermerk: %s · alle Signaturen sind Vollschluesse: %s" % (
        len(gef & sigk), len(gef), ", ".join("%s %s" % (abs_[k]["symbol"], stunde(abs_[k]["zu"])) for k in sorted(sigk - gef)) or "keine",
        "✔" if all(x[3] for x in hoch) else "⛔"))
    if a.wahrheit == "gebuehr":
        for k in sigk - gef:
            abs_[k]["liq"] = "neu%d" % k
        print("   ➤ WAHRHEIT = Gebuehrensignatur: %d Liquidationen" % sum(1 for ab in abs_ if ab["liq"]))
    else:
        print("   ➤ WAHRHEIT = gefuehrter Status (vorab festgelegt): %d Liquidationen" % zugeordnet)
    print("   die %d gefuehrten Liquidationen beenden je einen Abschnitt: %d %s" % (
        len(liqs), zugeordnet, "✔" if zugeordnet == len(liqs) else "⛔ nicht alle"))

    reihen = {"mark": Reihe("mark"), "spot": Reihe("spot")}

    # ── P3: ein Kauf, ein Schluss -> genau liq_schwelle aus K6
    from messe_k6_hebelstufe import liq_schwelle
    dmax, n3 = 0.0, 0
    for ab in abs_:
        if ab.get("kaeufe") != 1 or ab.get("teil") != 0:
            continue
        v = verlauf(ab, reihen["spot"])
        if not v:
            continue
        ts, _, e = ab["ereignisse"][0]
        L = e["wert"] / (e["wert"] - e["kredit"])
        E = e["preis"] / v["faktoren"][0]
        for h, mk, *_ in v["stunden"]:
            z = reihen["spot"].daten(ab["symbol"])[stunde(h)]
            s = math.ceil((h + 3600 - ts) / 3600.0)
            dmax = max(dmax, abs((1 - mk) * z[1] / 0.91 / E - liq_schwelle(L, 0.09, s)))
        n3 += 1
    print("P3 Formelgleichheit (ein Kauf, ein Schluss; %d Abschnitte) gegen K6 liq_schwelle: max. Abweichung %.2e %s" % (
        n3, dmax, "✔" if n3 and dmax < 1e-9 else "⛔"))

    print("\nDIE ABSCHNITTE")
    for k, ab in enumerate(abs_):
        print("  %2d %-6s %s bis %s · %3d Kaeufe · %3d Teilschliessungen · Hebel bis %.1fx%s%s" % (
            k, ab["symbol"], stunde(ab["auf"]), stunde(ab["zu"]) if ab["zu"] else "offen",
            ab.get("kaeufe", 0), ab.get("teil", 0), ab["max_hebel"],
            "  ⚡ LIQUIDIERT (%s)" % ab["liq"] if ab["liq"] else "", "  · 10./11.10." if ab["schwarz"] else ""))

    if a.spur is not None:
        ab = abs_[a.spur]
        print("\nSPUR Abschnitt %d %s" % (a.spur, ab["symbol"]))
        for ts, art, e in ab["ereignisse"]:
            print("   %s %s %s" % (datetime.fromtimestamp(ts, timezone.utc).isoformat(), art,
                                  {k: (round(v, 6) if isinstance(v, float) else v) for k, v in e.items()}))
        for art, r in reihen.items():
            print("  Reihe %s:" % art)
            v = verlauf(ab, r, spur=True)
            if v:
                print("   Faktoren EUR/Reihe je Kauf: %s" % ", ".join("%.5f" % f for f in v["faktoren"]))
        return 0

    # ── J5
    erg_alle = {art: {k: verlauf(ab, r) for k, ab in enumerate(abs_) if ab["zu"]} for art, r in reihen.items()}
    erg_ohne = {art: {k: verlauf(ab, r, ohne_schwarz=True) for k, ab in enumerate(abs_) if ab["zu"]}
                for art, r in reihen.items()}
    erg = erg_alle
    beide = [k for k in erg["mark"] if erg["mark"][k] and erg["spot"][k]]
    heraus = ["%d %s" % (k, abs_[k]["symbol"]) for k in erg["mark"] if k not in beide]
    print("\nJ8 in beiden Reihen vollstaendig: %d von %d Abschnitten · heraus: %s" % (
        len(beide), len(erg["mark"]), ", ".join(heraus) or "keine"))
    for art in ("spot", "mark"):
        f = sorted(x for k in beide for x in erg[art][k]["faktoren"])
        print("J2 Faktor EUR (Bitpanda) / USDT je Kauf, %s: Median %.4f · 5.-95. Perzentil %.4f-%.4f · Kaeufe %d" % (
            art, f[len(f) // 2], f[len(f) // 20], f[19 * len(f) // 20], len(f)))

    ergebnis = {}
    for teil, name in ((lambda ab: True, "ALLE"), (lambda ab: not ab["schwarz"], "OHNE 10./11.10.2025")):
        print("\n" + "=" * 110)
        erg = erg_alle if name == "ALLE" else erg_ohne
        L_ = [k for k in beide if abs_[k]["liq"] and teil(abs_[k])]
        G_ = [k for k in beide if not abs_[k]["liq"] and teil(abs_[k])]
        print("J5 %s - Liquidationen %d (%s) · Gegenfaelle %d Abschnitte" % (
            name, len(L_), ", ".join("%s/%s %s" % (abs_[k]["symbol"], abs_[k]["liq"],
                                                   "Crash" if abs_[k]["schwarz"] else "ruhig") for k in L_), len(G_)))
        for art in ("mark", "spot"):
            for m in MARGEN:
                tr, zf, zeilen = 0, [], []
                for k in L_:
                    erst, sch, bh = auswerten(erg[art][k], m)
                    hz = hstart(abs_[k]["zu"])
                    nm = "%s/%s" % (abs_[k]["symbol"], abs_[k]["liq"])
                    if erst is not None:
                        tr += 1; zf.append((hz - erst) / 3600)
                        zeilen.append("%s %.0f h vorher%s" % (nm, (hz - erst) / 3600, " (Buchungsstunde)" if bh else ""))
                    elif sch:
                        tr += 1; zf.append(0.0); zeilen.append("%s in der Schlussstunde" % nm)
                    else:
                        zeilen.append("%s KEIN Treffer" % nm)
                fa = [k for k in G_ if auswerten(erg[art][k], m)[0] is not None]
                fs = [k for k in G_ if auswerten(erg[art][k], m)[0] is None and auswerten(erg[art][k], m)[1]]
                print("  %-4s m %.4f: Treffer %d von %d (%s) · Fehlalarme %d von %d%s · nur in der Schlussstunde %d" % (
                    art, m, tr, len(L_), "; ".join(zeilen), len(fa), len(G_),
                    (" [" + ", ".join("%d %s %.0f h vor dem Schluss, Hebel nach dem letzten Kauf %.1fx" % (
                        k, abs_[k]["symbol"], (hstart(abs_[k]["zu"]) - auswerten(erg[art][k], m)[0]) / 3600,
                        next(s[4] for s in erg[art][k]["stunden"] if s[0] == auswerten(erg[art][k], m)[0]))
                        for k in fa) + "]") if fa else "",
                    len(fs)))
                ergebnis[(name, art, m)] = (tr, len(L_), sum(zf) / len(zf) if zf else float("nan"), len(fa), len(G_))
            unten = max((min(s[1] for s in erg[art][k]["stunden"]) for k in L_), default=float("nan"))
            oben = min((min(s[1] for s in erg[art][k]["stunden"] if not s[3]) for k in G_
                        if any(not s[3] for s in erg[art][k]["stunden"])), default=float("nan"))
            print("  %-4s m-Intervall: m >= %.4f (alle Liquidationen loesen aus) und m < %.4f (kein Fehlalarm) -> %s" % (
                art, unten, oben, ("vereinbar, m = 0,09 %s" % ("liegt DRIN" if unten <= 0.09 < oben else "liegt NICHT drin"))
                if unten < oben else "⛔ KEIN m ist mit allen Faellen vereinbar"))
            ergebnis[(name, art, "intervall")] = (unten, oben)

    # ── J3
    print("\n" + "=" * 110)
    print("J3 BITPANDA-AUSFUEHRUNG DER LIQUIDATIONEN (EUR, Bitpanda-Kurs, Buch unmittelbar vor dem Schluss)")
    for ab in abs_:
        if not ab["liq"]:
            continue
        e = ab["ereignisse"][-1][2]
        K, F, Q, grenze = eur_grenze(ab)
        m_exec = 1 - (K + F) / (Q * e["preis"])
        print("  %s/%s %s · Buch Menge %.4f, Kredit %.2f EUR · Ausfuehrung %.4f EUR · Grenze (m 0,09) %.4f EUR · "
              "Ausfuehrung %+.2f %% zur Grenze · Marge zur Ausfuehrung %.2f %%" % (
                  ab["symbol"], ab["liq"], "Crash" if ab["schwarz"] else "ruhig", Q, K, e["preis"], grenze,
                  100 * (e["preis"] / grenze - 1), 100 * m_exec))
    print("  R-R11 zur Kalibrierung vom 19.07. (hebel_risk_gate.py): SUI 6,75 %, TAO/87 8,4 % - ⚠️ die stand auf den "
          "Importer-Positionen (zu kleines Buch)")

    # ── Gegenpruefung 1: Schluesse in der Crash-Zeit ohne Liquidationsvermerk (R1)
    print("\n" + "=" * 110)
    print("GEGENPRUEFUNG R1 - Schluesse am 10./11.10. OHNE Liquidationsvermerk: Ausfuehrung gegen die Grenze, "
          "Schlussgebuehr gegen das Modell 0,30 + 0,18 x Tage")
    roh = json.load(io.open(a.buchungen, encoding="utf-8"))
    for ab in abs_:
        if not ab["schwarz"] or ab["liq"]:
            continue
        ts_z, _, e = ab["ereignisse"][-1]
        K, F, Q, grenze = eur_grenze(ab)
        gebuehr = sum(t["amount_cryptocoin_wallet"] for t in roh["transaktionen"]
                      if t["unix_timestamp"] == ts_z and "margin_trading.fee" in t.get("tags", []))
        verkauf = sum(t["amount_cryptocoin_wallet"] for t in roh["transaktionen"]
                      if t["unix_timestamp"] == ts_z and "margin_trading.repay" in t.get("tags", []))
        tage = (ts_z - ab["auf"]) / 86400.0
        print("  %s %s · %d Kaeufe · Ausfuehrung %s EUR · Grenze (m 0,09) %.4f EUR%s · Gebuehr %.2f %% des Verkaufs "
              "gegen Modell %.2f %% (ab dem ersten Kauf, %.1f Tage)" % (
                  ab["symbol"], datetime.fromtimestamp(ts_z, timezone.utc).strftime("%d.%m. %H:%M"), ab["kaeufe"],
                  "%.4f" % e["preis"] if e["preis"] else "-", grenze,
                  " -> Ausfuehrung %+.2f %% zur Grenze" % (100 * (e["preis"] / grenze - 1)) if e["preis"] else "",
                  100 * gebuehr / verkauf if verkauf else float("nan"), 0.30 + 0.18 * tage, tage))

    # ── Gegenpruefung 2: m je Symbol (NACHTRAEGLICH, nicht vorab festgelegt - nur Auskunft)
    print("\n" + "=" * 110)
    print("GEGENPRUEFUNG m JE SYMBOL - ⚠️ nachtraeglich, nicht vorab festgelegt, nur Auskunft (Bitpanda-Doku: "
          "Schwelle je Asset verschieden) · Reihe Markpreis, alle Stunden")
    for sym in sorted({abs_[k]["symbol"] for k in beide}):
        ks = [k for k in beide if abs_[k]["symbol"] == sym]
        lq = [k for k in ks if abs_[k]["liq"]]
        gg = [k for k in ks if not abs_[k]["liq"] and any(not s[3] for s in erg_alle["mark"][k]["stunden"])]
        u_ = max((min(s[1] for s in erg_alle["mark"][k]["stunden"]) for k in lq), default=None)
        o_ = min((min(s[1] for s in erg_alle["mark"][k]["stunden"] if not s[3]) for k in gg), default=None)
        print("  %-5s Abschnitte %2d, davon liquidiert %d · m >= %s · m < %s -> %s" % (
            sym, len(ks), len(lq), "%.4f" % u_ if u_ is not None else "-", "%.4f" % o_ if o_ is not None else "-",
            ("vereinbar" if u_ < o_ else "⛔ nicht vereinbar") if u_ is not None and o_ is not None else "nur eine Seite"))

    # ── J7
    print("\n" + "=" * 110)
    print("J7 NULLWELT - Abschnitte um +-%d..%d Tage verschoben, %d Ziehungen, m 0,09" % (VERSATZ[0], VERSATZ[1], ZIEHUNGEN))
    rnd = random.Random(SAAT)
    for art in ("mark", "spot"):
        tl = nl = tg = ng = 0
        je = defaultdict(lambda: [0, 0])
        for _ in range(ZIEHUNGEN):
            for k in beide:
                for _v in range(5):
                    v = verlauf(abs_[k], reihen[art], verschiebung=rnd.choice((-1, 1)) * rnd.randint(*VERSATZ) * 86400)
                    if v and v["stunden"]:
                        break
                else:
                    continue
                erst, sch, _b = auswerten(v, 0.09)
                if abs_[k]["liq"]:
                    t = erst is not None or sch
                    nl += 1; tl += t; je[abs_[k]["liq"]][0] += t; je[abs_[k]["liq"]][1] += 1
                else:
                    ng += 1; tg += erst is not None
        e_ = ergebnis[("ALLE", art, 0.09)]
        print("  %-4s verschobene Liquidationen loesen aus in %.1f %% (%s) · verschobene Gegenfaelle mit Treffer vor dem "
              "Schluss %.1f %% · echt: %d von %d, Fehlalarme %d von %d" % (
                  art, 100 * tl / max(nl, 1), ", ".join("%s: %d/%d" % (i, x[0], x[1]) for i, x in sorted(je.items())),
                  100 * tg / max(ng, 1), e_[0], e_[1], e_[3], e_[4]))

    # ── J6
    print("\n" + "=" * 110)
    mk, sp = ergebnis[("ALLE", "mark", 0.09)], ergebnis[("ALLE", "spot", 0.09)]
    haupt = mk[0] == mk[1] and mk[2] <= sp[2] and mk[3] <= sp[3]
    u, o = ergebnis[("ALLE", "mark" if haupt else "spot", "intervall")]
    print("J6 Markpreis: Treffer %d/%d, Zeitfehler im Mittel %.1f h, Fehlalarme %d/%d · Spot-Tief: %d/%d, %.1f h, %d/%d" % (
        mk[0], mk[1], mk[2], mk[3], mk[4], sp[0], sp[1], sp[2], sp[3], sp[4]))
    print("   -> %s" % ("✔ der MARKPREIS wird Hauptmass fuer K6" if haupt else
                         "◐ Regel nicht erfuellt - beide Reihen mitfuehren und vorlegen"))
    print("   -> m = 0,09 %s (Intervall %.4f bis %.4f, Reihe %s)" % (
        "HAELT" if u <= 0.09 < o else "HAELT NICHT", u, o, "mark" if haupt else "spot"))

    nachher = (os.path.getsize(a.db), os.path.getmtime(a.db))
    print("\nP0 Sicherung unveraendert (Groesse, Zeitstempel): %s" % ("✔ ja" if vorher == nachher else "⛔ NEIN"))
    print("SCHLUSS: vollstaendig")
    return 0


if __name__ == "__main__":
    sys.exit(main())
