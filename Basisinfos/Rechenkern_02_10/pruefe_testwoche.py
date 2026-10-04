"""S7-7 (04.10.2026): die Mindestbedingungen der Testwoche - ausgewertet an einer KOPIE der REGEL0-Ablage vom Notebook.

    python Basisinfos/Rechenkern_02_10/pruefe_testwoche.py <Kopie regel0_signale.db> [--von "2026-10-03 06:00"] [--bis "2026-10-10 23:00"]

NUR LESEND (mode=ro), kein Netz, keine Mail - CLAUDE.md: *Nachgewiesen wird gegen eine KOPIE*. Jede Bedingung hat eine vorab
festgelegte Regel (Voranalyse_Schritt7 Par. 22); was nur Auskunft ist, steht als AUSKUNFT da und entscheidet nichts.

    T1  jede Stunde gerechnet        verlorene Signalstunden = 0 (ein Lauf um h+1 legt die Signalstunde h ab - regel0_rechnung:530)
    T2  Frische                      kein Lauf mit veralteten Assets (veraltet = 0)
    T3  Laufzeit                     kein Lauf ueber 1.500 s (halbe Zeitgrenze 50 min); der Monatslauf mit Training ausgenommen
    F1  Signalmail vollstaendig      jedes Signal mit Schalter an und Stufe > 0 ist gemailt ODER begruendet gesperrt (Zuordnung)
    F2  Signalmail rechtzeitig       vor dem Schluss der Einstiegsstunde verschickt
    F3  Korrektur                    weicht die endgueltige Stufe ab, ist die Korrektur verschickt
    F4  Ausstieg                     jede faellige Erinnerung ist verschickt ODER als *entfallen* vermerkt - nie beides, nie keins
    L1  Pruefblock                   zu jedem gemailten Signal eine Trader-Zeile (Urteil oder Grund), Aufrufe je Tag <= 150
    A1  AUSKUNFT Signalbilanz je Asset gegen die gemessene Rate 2025/26 (Poisson, auffaellig unter 1 %)
    A2  AUSKUNFT Korrekturquote gegen B-9 (1,6 %), gesperrte Zuordnungen mit Grund
"""
import argparse
import csv
import math
import os
import sqlite3
import sys
from datetime import datetime, timedelta

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REF = os.path.join(WURZEL, "data", "_vergleich", "kern48jbz_einstiege_bestand.csv")
B0 = datetime(2020, 1, 1)
LAUF_GRENZE_S = 1500
TAGESLIMIT = 150


def _t(s):
    return datetime.strptime(str(s)[:16], "%Y-%m-%d %H:%M")


def auswerten(pfad: str, von: str | None = None, bis: str | None = None) -> dict:
    c = sqlite3.connect("file:%s?mode=ro" % pfad.replace("\\", "/"), uri=True)
    c.row_factory = sqlite3.Row
    laeufe = [dict(r) for r in c.execute("SELECT * FROM lauf ORDER BY jetzt")]
    sig = [dict(r) for r in c.execute("SELECT * FROM signal ORDER BY signalstunde")]
    tabs = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    pr = [dict(r) for r in c.execute("SELECT * FROM pruefung")] if "pruefung" in tabs else []
    c.close()
    if not laeufe:
        return {"fehler": "keine Laeufe in der Ablage"}
    v = _t(von) if von else _t(laeufe[0]["jetzt"])
    b = _t(bis) if bis else _t(laeufe[-1]["jetzt"])
    laeufe = [r for r in laeufe if v <= _t(r["jetzt"]) <= b]
    sig = [r for r in sig if v - timedelta(hours=1) <= _t(r["signalstunde"]) < b]
    erg = {"von": v, "bis": b, "bedingungen": {}, "auskunft": {}}
    B = erg["bedingungen"]

    # T1 - eine Signalstunde h ist abgelegt, wenn es einen Lauf mit jetzt = h+1 gibt
    gerechnet = {_t(r["jetzt"]) for r in laeufe}
    soll = [v + timedelta(hours=i) for i in range(int((b - v).total_seconds() // 3600) + 1)]
    fehlt = [h for h in soll if h not in gerechnet]
    B["T1 jede Stunde gerechnet"] = (not fehlt, "%d von %d Stunden gerechnet; verlorene Signalstunden: %s" % (
        len(soll) - len(fehlt), len(soll), ", ".join((h - timedelta(hours=1)).strftime("%d.%m. %H:00") for h in fehlt[:12]) or "keine"))
    # T2
    alt = [r for r in laeufe if (r.get("veraltet") or 0) > 0]
    B["T2 Frische"] = (not alt, "%d Laeufe mit veralteten Assets%s" % (len(alt), (": " + "; ".join(
        "%s %s" % (r["jetzt"], r.get("veraltet_liste") or "") for r in alt[:5])) if alt else ""))
    # T3 - der erste Lauf eines Monats trainiert (pakete wechselt) und darf laenger dauern
    lang = []
    for i, r in enumerate(laeufe):
        training = i == 0 or (r.get("pakete") or "") != (laeufe[i - 1].get("pakete") or "")
        if (r.get("sekunden") or 0) > LAUF_GRENZE_S and not training:
            lang.append(r)
    sek = sorted(r.get("sekunden") or 0 for r in laeufe)
    B["T3 Laufzeit"] = (not lang, "Median %.0f s, hoechstens %.0f s; ueber %d s (ohne Trainingslauf): %d" % (
        sek[len(sek) // 2], sek[-1], LAUF_GRENZE_S, len(lang)))
    # F1/F2/F3/F4
    an = [r for r in sig if r.get("hebel_schalter") == 1 and ((r.get("stufe") if r.get("stufe") is not None else r.get("stufe_vorlaeufig")) or 0) > 0]
    offen = [r for r in an if not r.get("mail_signal_am") and not r.get("mail_gesperrt_am")]
    B["F1 Signalmail vollstaendig"] = (not offen, "%d Signale mit Schalter an und Stufe > 0, gemailt %d, gesperrt %d, OHNE Mail %d%s" % (
        len(an), sum(1 for r in an if r.get("mail_signal_am")), sum(1 for r in an if r.get("mail_gesperrt_am")), len(offen),
        (": " + ", ".join("%s %s" % (r.get("bitpanda") or r["symbol"], r["signalstunde"]) for r in offen[:8])) if offen else ""))
    spaet = [r for r in an if r.get("mail_signal_am") and _t(r["mail_signal_am"]) >= _t(r["einstieg"]) + timedelta(hours=1)]
    verzug = sorted((_t(r["mail_signal_am"]) - _t(r["signalstunde"]) - timedelta(hours=1)).total_seconds() / 60 for r in an if r.get("mail_signal_am"))
    B["F2 Signalmail rechtzeitig"] = (not spaet, "nach Schluss der Signalstunde im Median %s min; nach dem Einstiegszeitpunkt verschickt: %d" % (
        ("%.0f" % verzug[len(verzug) // 2]) if verzug else "-", len(spaet)))
    korr = [r for r in an if r.get("mail_signal_am") and r.get("stufe") is not None and r.get("mail_signal_stufe") is not None
            and int(r["stufe"]) != int(r["mail_signal_stufe"])]
    korr_offen = [r for r in korr if not r.get("mail_korrektur_am")]
    B["F3 Korrektur"] = (not korr_offen, "%d Abweichungen vorlaeufig/endgueltig, Korrektur fehlt bei %d" % (len(korr), len(korr_offen)))
    faellig = [r for r in an if r.get("mail_signal_am") and _t(r["ausstieg"]) + timedelta(hours=2) <= b
               and ((r.get("stufe") if r.get("stufe") is not None else r.get("mail_signal_stufe")) or 0) > 0]
    weder = [r for r in faellig if not r.get("mail_erinnerung_am") and not r.get("erinnerung_entfallen_am")]
    beides = [r for r in faellig if r.get("mail_erinnerung_am") and r.get("erinnerung_entfallen_am")]
    B["F4 Ausstieg"] = (not weder and not beides, "%d faellig: verschickt %d, entfallen %d, keins %d, beides %d" % (
        len(faellig), sum(1 for r in faellig if r.get("mail_erinnerung_am")), sum(1 for r in faellig if r.get("erinnerung_entfallen_am")),
        len(weder), len(beides)))
    # L1
    gem = [r for r in an if r.get("mail_signal_am")]
    mit = {(p["symbol"], p["signalstunde"]) for p in pr if p.get("rolle") == "trader"}
    ohne = [r for r in gem if (r["symbol"], r["signalstunde"]) not in mit]
    tag = {}
    for p in pr:
        if p.get("gefragt"):
            tag[p.get("tag_pazifik")] = tag.get(p.get("tag_pazifik"), 0) + int(p.get("aufrufe") or 1)
    zuviel = {k: n for k, n in tag.items() if n > TAGESLIMIT}
    fehl = [p for p in pr if p.get("rolle") == "trader" and p.get("fehler")]
    B["L1 Pruefblock"] = (not ohne and not zuviel, "gemailt %d, ohne Trader-Zeile %d; Trader mit Fehler/Sperre %d; Aufrufe je Tag %s" % (
        len(gem), len(ohne), len(fehl), dict(sorted(tag.items())) or "-"))
    # A1 - Signalbilanz je Asset gegen die gemessene Rate 2025/26 (bestand; Zusatz-Assets ohne Rate)
    rate = {}
    if os.path.exists(REF):
        with open(REF, encoding="utf-8") as f:
            n = {}
            for z in csv.DictReader(f, delimiter=";"):
                if z["jahr"] in ("2025", "2026"):
                    n[z["symbol"]] = n.get(z["symbol"], 0) + 1
        wochen = ((datetime(2026, 9, 1) - datetime(2025, 1, 1)).days) / 7.0
        rate = {s: k / wochen for s, k in n.items()}
    wo = max((b - v).total_seconds() / (7 * 86400), 1e-9)
    beob = {}
    for r in sig:
        if r.get("hebel_schalter") == 1:
            beob[r["symbol"]] = beob.get(r["symbol"], 0) + 1
    zeilen, auff = [], []
    for s in sorted(set(beob) | {s for s in rate if s in {r["symbol"] for r in sig if r.get("hebel_schalter") == 1}}):
        lam = rate.get(s)
        k = beob.get(s, 0)
        if lam is None:
            zeilen.append("%s %d (keine Rate - Zusatz-Asset)" % (s, k))
            continue
        mu = lam * wo
        p_lo = sum(math.exp(-mu) * mu ** i / math.factorial(i) for i in range(k + 1))
        p_hi = 1 - sum(math.exp(-mu) * mu ** i / math.factorial(i) for i in range(k))
        zeilen.append("%s %d (erwartet %.1f)" % (s, k, mu))
        if p_lo < 0.01 or p_hi < 0.01:
            auff.append("%s %d bei erwartet %.1f" % (s, k, mu))
    # ⚠️ je Asset erwartet die Messung nur 0,4-0,9 Signale je Woche - eine Woche ist je Asset NICHT pruefbar; pruefbar ist die SUMME
    mu_s = sum(rate[s] * wo for s in {r["symbol"] for r in sig if r.get("hebel_schalter") == 1} if s in rate)
    k_s = sum(beob.get(s, 0) for s in rate if s in beob)
    _pl = sum(math.exp(-mu_s) * mu_s ** i / math.factorial(i) for i in range(k_s + 1)) if mu_s else 1.0
    _ph = (1 - sum(math.exp(-mu_s) * mu_s ** i / math.factorial(i) for i in range(k_s))) if mu_s else 1.0
    erg["auskunft"]["A1 Signalbilanz SUMME (Schalter an, Messbasis-Assets)"] = "beobachtet %d, erwartet %.1f (Poisson: %s)" % (
        k_s, mu_s, "AUFFAELLIG wenig" if _pl < 0.01 else ("AUFFAELLIG viel" if _ph < 0.01 else "im Rahmen"))
    erg["auskunft"]["A1 Signalbilanz je Asset (Schalter an) - je Asset in einer Woche NICHT pruefbar"] = "%s%s" % (
        "; ".join(zeilen) or "keine Signale", (" · AUFFAELLIG: " + "; ".join(auff)) if auff else " · nichts auffaellig")
    ges = [r for r in sig if r.get("mail_gesperrt_am")]
    erg["auskunft"]["A2 Korrekturquote und Sperren"] = "Korrekturen %d von %d gemailten (%.1f %%, B-9 erwartet 1,6 %%); gesperrt %d%s" % (
        len(korr), len(gem), 100.0 * len(korr) / len(gem) if gem else 0.0, len(ges),
        (": " + "; ".join("%s (%s)" % (r.get("bitpanda") or r["symbol"], (r.get("abgleich") or "")[:60]) for r in ges[:5])) if ges else "")
    return erg


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ablage")
    ap.add_argument("--von")
    ap.add_argument("--bis")
    a = ap.parse_args(argv)
    e = auswerten(a.ablage, a.von, a.bis)
    if "fehler" in e:
        print("⛔", e["fehler"])
        return 2
    print("S7-7 TESTWOCHE %s bis %s UTC (Kopie %s)" % (e["von"].strftime("%d.%m. %H:%M"), e["bis"].strftime("%d.%m. %H:%M"), os.path.basename(a.ablage)))
    ok = True
    for k, (bed, txt) in e["bedingungen"].items():
        ok &= bed
        print("  %s  %s - %s" % ("✔" if bed else "⛔", k, txt))
    for k, txt in e["auskunft"].items():
        print("  ·  %s - %s" % (k, txt))
    print("SCHLUSS: %s" % ("alle Bedingungen erfuellt" if ok else "NICHT alle Bedingungen erfuellt"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
