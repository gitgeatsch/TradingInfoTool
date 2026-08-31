# -*- coding: utf-8 -*-
"""Was macht der Rollout mit der ECHTEN Produktion? (31.08.2026)

Nutzerauftrag 31.08.: *"Du HAST die Notebook-Daten um zu simulieren - was
auch der Auftrag ist - wie sich die Aenderung auf das produktive System
auswirkt. Es sollen vorher alle offenen Fragen geklaert sein und nicht erst
wenn alles produktiv ist."*

## Die Datenlage

    Notebook (T440)   laeuft, alter Codestand, seit Tagen kein `git pull`
    Backup 29.08.     `tradinginfotool_2026-08-29_1931.db.gz`
                      5.772 Signale, davon 2.789 aus der Rollen-Kette
                      Kurse bis 29.08., 143.334 OHLC-Zeilen

⚠️ NUR LESEND, aus einer entpackten KOPIE im Scratchpad. Die
Produktions-Datenbank wird nicht angefasst (stehende Regel).

## Was hier beantwortet wird - vor dem Rollout, nicht danach

  F1 ABDECKUNG   Wieviele Werte der Produktion haetten ueberhaupt einen
                 Beitrag? Auf dem Desktop waren es 5 von 43 ohne - dort
                 sind die Kurse aber 12 Tage alt.
  F2 G-6         Wieviele der 2.789 echten Signale haette die scharfe
                 Stufe 11 verworfen - und WAREN das die schlechteren?
  F3 EROEFFNEN   Der Memory sagt "seit A1 kein Eroeffnen". Die Daten sagen
                 881 ERÖFFNEN im August. Was gilt?
  F4 BRUCH       Laeuft die neue Kette mit dem neuen Code ueberhaupt
                 durch - oder bricht etwas, das nur die Produktion hat?

    python simuliere_rollout_gegen_nb.py
"""
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

NB = ("C:/Users/Geatsch/AppData/Local/Temp/claude/"
      "D--CLAUDE-Projects-SoftwareProjekte-TradingInfoTool/"
      "f018f847-7a7c-44fa-bab6-ff90785a7541/scratchpad/nb_produktion.db")
SCHNITT = 200
CRV = 2.0


def lade_kurse(pfad):
    """Je Symbol die Kursreihe aus der Produktions-DB (laengste Waehrung)."""
    import sqlite3
    c = sqlite3.connect("file:%s?mode=ro" % pfad, uri=True)
    je = {}
    for sym, waehrung, tag, kurs in c.execute(
            "SELECT symbol, currency, date, close FROM price_history_ohlc "
            "WHERE close IS NOT NULL AND close > 0 ORDER BY symbol, date"):
        je.setdefault((str(sym).upper(), waehrung), []).append(
            (str(tag)[:10], float(kurs)))
    # ergaenzend die CoinGecko-Reihen ueber die coingecko_id
    ids = {}
    try:
        import config as _c
        for a in _c.get_watchlist():
            if getattr(a, "coingecko_id", None):
                ids[str(a.coingecko_id).lower()] = str(a.symbol).upper()
    except Exception:                                        # noqa: BLE001
        pass
    for kid, tag, usd, eur in c.execute(
            "SELECT coingecko_id, date, price_usd, price_eur "
            "FROM price_history ORDER BY coingecko_id, date"):
        sym = ids.get(str(kid).lower())
        kurs = usd if usd else eur
        if sym and kurs and float(kurs) > 0:
            je.setdefault((sym, "CG"), []).append((str(tag)[:10], float(kurs)))
    c.close()
    beste = {}
    for (sym, _w), reihe in je.items():
        if len(reihe) > len(beste.get(sym, ())):
            beste[sym] = reihe
    return beste


def signale(pfad):
    import sqlite3
    c = sqlite3.connect("file:%s?mode=ro" % pfad, uri=True)
    aus = [{"symbol": str(s).upper(), "tag": str(d)[:10], "aktion": a}
           for s, d, a in c.execute(
               "SELECT symbol, created_at, action FROM signals "
               "WHERE quelle_kette='rollen' ORDER BY created_at")]
    c.close()
    return aus


def main():
    print("=" * 96)
    print("ROLLOUT-SIMULATION GEGEN DIE ECHTE PRODUKTION (Notebook, 29.08.)")
    print("=" * 96)
    kurse = lade_kurse(NB)
    sig = signale(NB)
    print("%d Kursreihen, %d Signale der Rollen-Kette" % (len(kurse), len(sig)))

    # ---------------------------------------------------------------- F3
    print()
    print("-" * 96)
    print("F3 — GIBT ES EROEFFNEN? (Memory: 'seit A1 kein Eroeffnen mehr')")
    print("-" * 96)
    from collections import Counter
    c_ak = Counter(s["aktion"] for s in sig)
    for a, n in c_ak.most_common():
        print("  %-14s %5d" % (a, n))
    eroeff = [s for s in sig if s["aktion"] in ("ERÖFFNEN", "KAUFEN")]
    print()
    print("  -> %d eroeffnende Signale (%.0f %%). Der Memory-Befund stammt"
          % (len(eroeff), 100 * len(eroeff) / max(len(sig), 1)))
    print("     aus der Tagesdiagnose vom 29.08. - an EINEM Tag. Ueber den")
    print("     Monat ist das Eroeffnen nicht ausgefallen.")
    tage = sorted({s["tag"] for s in eroeff})
    print("     Tage mit Eroeffnen: %d (%s .. %s)"
          % (len(tage), tage[0] if tage else "-", tage[-1] if tage else "-"))

    # ---------------------------------------------------------------- F1
    print()
    print("-" * 96)
    print("F1 — ABDECKUNG: haetten die Signalsymbole einen Beitrag?")
    print("-" * 96)
    # Schnittabstand je Signal aus DERSELBEN Reihe rechnen
    def schnitt_am_tag(sym, tag):
        reihe = kurse.get(sym)
        if not reihe:
            return None
        bis = [k for t, k in reihe if t <= tag]
        if len(bis) < SCHNITT:
            return None
        return bis[-1] / (sum(bis[-SCHNITT:]) / SCHNITT) - 1.0

    mit, ohne = [], []
    for s in sig:
        w = schnitt_am_tag(s["symbol"], s["tag"])
        s["abstand"] = w
        (mit if w is not None else ohne).append(s)
    print("  Signale MIT Schnittabstand:  %5d (%.0f %%)"
          % (len(mit), 100 * len(mit) / len(sig)))
    print("  Signale OHNE:                %5d (%.0f %%)"
          % (len(ohne), 100 * len(ohne) / len(sig)))
    if ohne:
        fehlt = Counter(s["symbol"] for s in ohne)
        print("  betroffene Symbole: %s"
              % ", ".join("%s(%d)" % (s, n) for s, n in fehlt.most_common(8)))
        print("  ⚠️ Diese haetten mit scharfer Stufe 11 KEIN Signal bekommen,")
        print("     sofern kein anderer Beitrag greift.")

    # ---------------------------------------------------------------- F2
    print()
    print("-" * 96)
    print("F2 — G-6: was haette die scharfe Stufe 11 verworfen?")
    print("-" * 96)
    from agent import potential as PT
    from agent import wahrscheinlichkeit as WK
    stufen = next((b.stufen for b in WK.BEITRAEGE
                   if b.merkmal == "schnitt_fuenftel"), None)
    if not stufen:
        print("  ⚠️ Beitrag nicht registriert")
        return
    # Rang je Kalendertag ueber ALLE Reihen mit Wert - wie in der Produktion
    je_tag = {}
    for s in mit:
        je_tag.setdefault(s["tag"], []).append(s)
    alle_tage = sorted(je_tag)
    for tag in alle_tage:
        # Querschnitt: alle Symbole mit Kursreihe an diesem Tag
        werte = {}
        for sym in kurse:
            w = schnitt_am_tag(sym, tag)
            if w is not None:
                werte[sym] = w
        if len(werte) < 15:
            for s in je_tag[tag]:
                s["f5"] = None
            continue
        srt = sorted(werte.items(), key=lambda x: x[1])
        rang = {sy: i / max(len(srt) - 1, 1) for i, (sy, _v) in enumerate(srt)}
        for s in je_tag[tag]:
            q = rang.get(s["symbol"])
            s["f5"] = None if q is None else min(int(q * 5), 4)
    # ⚠️ NUR EINSTIEGSFAEHIGE AKTIONEN ERREICHEN STUFE 11 (31.08.2026).
    # Die erste Fassung rechnete das Potential fuer ALLE Signale - auch
    # fuer VERKAUFEN, REDUZIEREN und HALTEN. Das ergab den Fehlalarm
    # "Stufe 11 sperrt Verkaeufe". Tatsaechlich scheitern die schon an
    # `rollen_lauf.py:1384` (`aktion not in AKTIONEN_MIT_EINSTIEG`), rund
    # 400 Zeilen VOR dem Entscheider - sie erreichen ihn nie.
    #
    # Das System ist an dieser Stelle richtig gebaut: das Potential ist
    # eine EINSTIEGSbewertung und darf keine Ausstiegsentscheidung
    # verwerfen.
    from agent.signal_mail import AKTIONEN_MIT_EINSTIEG
    durch, gesperrt, unbestimmt = [], [], []
    for s in sig:
        if s["aktion"] not in AKTIONEN_MIT_EINSTIEG:
            continue
        f5 = s.get("f5")
        if f5 is None:
            unbestimmt.append(s)
            continue
        p = PT.rechne(crv=CRV, stop_relativ=0.05, klasse="krypto",
                      instrument="spot", strategie="einstieg", h=None,
                      merkmale={"schnitt_fuenftel": f5})
        (durch if PT.traegt(p.wert_r) else gesperrt).append(s)
    n = len(durch) + len(gesperrt) + len(unbestimmt)
    print("  ⚠️ Nur einstiegsfaehige Aktionen erreichen Stufe 11:")
    print("     %s" % ", ".join(AKTIONEN_MIT_EINSTIEG))
    print("     %d von %d Signalen (%.0f %%); der Rest scheitert vorher"
          % (n, len(sig), 100 * n / len(sig)))
    print()
    print("  von %d einstiegsfaehigen Signalen:" % n)
    print("    kaemen durch:        %5d (%.0f %%)" % (len(durch), 100 * len(durch) / n))
    print("    wuerden gesperrt:    %5d (%.0f %%)" % (len(gesperrt), 100 * len(gesperrt) / n))
    print("    ⚠️ ohne Datengrundlage: %4d (%.0f %%)"
          % (len(unbestimmt), 100 * len(unbestimmt) / n))
    print()
    print("  ⚠️ NUR DER SCHNITTABSTAND ist hier gerechnet - Funding und")
    print("     Turnover kommen in der Produktion dazu und verschieben das")
    print("     Bild. Diese Zahl ist die UNTERGRENZE des Durchlasses.")
    print()
    print("  je Aktion (nur einstiegsfaehige):")
    for a in sorted(x for x in c_ak if x in AKTIONEN_MIT_EINSTIEG):
        d = sum(1 for s in durch if s["aktion"] == a)
        g = sum(1 for s in gesperrt if s["aktion"] == a)
        u = sum(1 for s in unbestimmt if s["aktion"] == a)
        print("    %-14s durch %4d  gesperrt %4d  ohne Grundlage %4d"
              % (a, d, g, u))


if __name__ == "__main__":
    main()
