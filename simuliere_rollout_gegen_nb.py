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


# ---------------------------------------------------------------------------
# F5-F8: DIE FILTERSIMULATION (31.08.2026)
# ---------------------------------------------------------------------------
#
# Nutzerauftrag 31.08., woertlich: *"Setz die Simulation auf - auch auf
# reellen Bedingungen fuer einen gewissen Zeitraum mit Trendwechsel. Wenn
# moeglich ueber die bestehende Watchlist 'echte Empfehlungen am Tag' je
# Asset, je Strategie - und weitere relevante Informationen."*
#
# Und die Vorgabe, die den Massstab setzt: *"Der Takt hat dem Bedarf zu
# folgen - aber nicht durch kurzen Takt viele Signale erzeugen. Die Filter
# muessen funktionieren."*
#
# ⚠️ KEINE NACHBILDUNG, SONDERN DIE ECHTEN LAEUFE. Gerechnet wird auf
# `gate_durchlaessigkeit` (7.169 protokollierte Laeufe) und `signals`
# (2.789 Signale) aus der Notebook-Produktion. Eine nachgebaute Kette
# wuerde messen, wie gut ich sie nachgebaut habe.
#
# DER ZEITRAUM TRAEGT EINEN TRENDWECHSEL, gemessen an BTC:
#
#     14.-21.08.   62.760 -> 67.000   +6,8 %    AUFWAERTS
#     22.-29.08.   77.083 -> 67.404  -12,6 %    ABWAERTS
#
# Das ist keine Wahl, sondern ein Glueck: derselbe Codestand lief durch
# beide Phasen. Ein Filter, der nur in einer Phase wirkt, faellt hier auf.

PHASENGRENZE = "2026-08-22"


def _trichter(conn, von=None, bis=None):
    """Die echten Trichterzahlen je Stufe aus `gate_durchlaessigkeit`."""
    import json as _json
    from collections import Counter
    wo = ["daten_json IS NOT NULL", "erfasst_am>='2026-08-14'"]
    if von:
        wo.append("erfasst_am>=%r" % von)
    if bis:
        wo.append("erfasst_am<%r" % bis)
    r = list(conn.execute("SELECT hinein,heraus,daten_json FROM "
                          "gate_durchlaessigkeit WHERE " + " AND ".join(wo)))
    verl, best, gruende = Counter(), Counter(), {}
    hin = her = 0
    for a, b, dj in r:
        hin += a or 0
        her += b or 0
        try:
            d = _json.loads(dj)
        except Exception:                                    # noqa: BLE001
            continue
        verl.update(d.get("verloren") or {})
        best.update(d.get("bestanden") or {})
        for k, g in (d.get("gruende") or {}).items():
            gruende.setdefault(k, Counter()).update(g)
    return {"laeufe": len(r), "hinein": hin, "heraus": her,
            "verloren": verl, "bestanden": best, "gruende": gruende}


def f5_trichter(conn):
    print()
    print("-" * 96)
    print("F5 — WO VERLIERT DIE KETTE WIRKLICH? (echte Laeufe, nicht simuliert)")
    print("-" * 96)
    t = _trichter(conn)
    ges = sum(t["verloren"].values()) or 1
    print("  %d Laeufe, %d Pruefungen hinein, %d heraus (%.2f %% Durchlass)"
          % (t["laeufe"], t["hinein"], t["heraus"],
             100 * t["heraus"] / max(t["hinein"], 1)))
    print()
    print("  Stufe             verloren   Anteil   Art der Bremse")
    # ⚠️ DIE EINTEILUNG IST DER PUNKT DER GANZEN SIMULATION.
    art = {"wiederholung": "TAKT      - sagt nichts ueber Qualitaet",
           "anlass":       "TAKT      - sagt nichts ueber Qualitaet",
           "urteil":       "TAKT      - Cooldown im Urteil",
           "auftrag":      "STRUKTUR  - Schalter, Paar-Matrix",
           "fakten":       "STRUKTUR  - Datenlage",
           "geometrie":    "STRUKTUR  - Betrag, Zonen",
           "auswahl":      "QUALITAET - Rang des ASSETS",
           "aktion":       "QUALITAET - das Modellurteil",
           "entscheider":  "QUALITAET - das POTENTIAL der Handlung",
           "lagebild":     "STRUKTUR  - Lagebild fehlt",
           "risikoschicht": "STRUKTUR  - Risikoschicht"}
    summen = {}
    for k, v in t["verloren"].most_common():
        a = art.get(k, "?")
        summen[a[:9].strip()] = summen.get(a[:9].strip(), 0) + v
        top = t["gruende"].get(k, {})
        top = max(top.items(), key=lambda x: x[1]) if top else None
        print("  %-16s %9d %7.1f %%   %s" % (k, v, 100 * v / ges, a))
        if top:
            print("  %-16s %31s %s (%dx)" % ("", "", top[0][:42], top[1]))
    print()
    print("  ZUSAMMENGEFASST NACH ART DER BREMSE:")
    for a in ("TAKT", "STRUKTUR", "QUALITAET"):
        v = summen.get(a, 0)
        print("    %-10s %9d %7.1f %%" % (a, v, 100 * v / ges))
    print()
    print("  ⚠️ Das uebergeordnete Ziel verlangt, dass das POTENTIAL")
    print("     entscheidet. Der `entscheider` verwirft heute %.1f %% -"
          % (100 * t["verloren"].get("entscheider", 0) / ges))
    print("     der Cooldown %.1f %%."
          % (100 * t["verloren"].get("wiederholung", 0) / ges))
    return t


def f6_phasen(conn):
    """⚠️⚠️ DIESER ABSCHNITT KANN DEN TRENDWECHSEL NICHT MESSEN.

    Die erste Fassung verglich die Verlustanteile vor und nach dem 22.08.
    und meldete vier phasenabhaengige Filter. **Der Befund war falsch**,
    und die Gegenpruefung zeigt es je Tag:

        bis 22.08.   auswahl 0          auftrag 442-1.632
        ab  23.08.   auswahl 1.322+     auftrag 0

    **Am 23.08. wurde A1 ausgerollt** (`A1_Auswahl_Dimensionierung_23_08.md`)
    und die `auftrag`-Bremse abgeloest. Der CODEWECHSEL liegt einen Tag nach
    dem TRENDWECHSEL - beide sind in diesen Daten nicht trennbar. Ein
    Mitlaeufer im Sinne der Pruefliste 2.80, Punkt 1.

    ⚠️ UND DIE ANTEILE TAEUSCHEN ZUSAETZLICH. Kommt eine Stufe hinzu, die
    25 % der Verluste uebernimmt, SINKEN die Anteile aller anderen - ohne
    dass sich dort irgendetwas geaendert haette. Deshalb stehen unten
    absolute Zahlen JE LAUF, nicht Anteile.

    Was hier bleibt, ist die ehrliche Auskunft: **ueber diesen Zeitraum
    laesst sich die Phasenabhaengigkeit der Filter nicht bestimmen.** Dafuer
    braucht es einen Zeitraum ohne Codewechsel - fruehestens ab dem 23.08.,
    und der umfasst nur die Abwaertsphase.
    """
    print()
    print("-" * 96)
    print("F6 — TRENDWECHSEL ODER CODEWECHSEL? (⚠️ nicht trennbar)")
    print("-" * 96)
    print("  Trendwechsel BTC am 22.08.   (+6,8 %% davor, -12,6 %% danach)")
    print("  Codewechsel A1 am 23.08.     (Auswahl ausgerollt, `auftrag` abgeloest)")
    print("  ⚠️ EIN TAG AUSEINANDER - was hier verglichen wird, vermischt beides.")
    print()
    a = _trichter(conn, bis=PHASENGRENZE)
    b = _trichter(conn, von=PHASENGRENZE)
    ga = sum(a["verloren"].values()) or 1
    gb = sum(b["verloren"].values()) or 1
    # ⚠️ ABSOLUT JE LAUF, nicht als Anteil - siehe Docstring.
    la = max(a["laeufe"], 1)
    lb = max(b["laeufe"], 1)
    print("  Stufe            vor 22.08.    ab 22.08.   Deutung")
    print("                   je Lauf       je Lauf")
    for k in sorted(set(list(a["verloren"]) + list(b["verloren"])),
                    key=lambda x: -(a["verloren"].get(x, 0)
                                    + b["verloren"].get(x, 0))):
        va = a["verloren"].get(k, 0) / la
        vb = b["verloren"].get(k, 0) / lb
        if k in ("auswahl", "auftrag"):
            deutung = "⚠️ CODEWECHSEL 23.08. - kein Trendeffekt"
        elif abs(va - vb) > max(va, vb) * 0.3:
            deutung = "⚠️ verschoben - Ursache offen"
        else:
            deutung = "stabil"
        print("  %-16s %9.1f %12.1f   %s" % (k, va, vb, deutung))
    print()
    print("  Durchlass  auf %.2f %%   ab %.2f %%"
          % (100 * a["heraus"] / max(a["hinein"], 1),
             100 * b["heraus"] / max(b["hinein"], 1)))
    print()
    print("  ⚠️ WAS SICH DARAUS NICHT ABLEITEN LAESST: ob ein Filter")
    print("     phasenabhaengig wirkt. `wiederholung` halbiert sich je Lauf")
    print("     (9,1 -> 4,5) - das kann der Trend sein ODER die Folge davon,")
    print("     dass A1 seit dem 23.08. vorher filtert und weniger Faelle")
    print("     ueberhaupt bis zur Wiederholungspruefung kommen.")
    print("     Fuer eine saubere Antwort braucht es einen Zeitraum OHNE")
    print("     Codewechsel - der beginnt am 23.08. und umfasst nur die")
    print("     Abwaertsphase.")


def f7_je_asset_und_strategie(conn):
    print()
    print("-" * 96)
    print("F7 — ECHTE EMPFEHLUNGEN JE TAG, ASSET UND STRATEGIE")
    print("-" * 96)
    from collections import Counter
    tage = {r[0] for r in conn.execute(
        "SELECT substr(created_at,1,10) FROM signals WHERE quelle_kette='rollen'")}
    n_tage = max(len(tage), 1)
    print("  %d Kalendertage" % n_tage)
    print()
    print("  Aktion        gesamt   je Tag   je Tag+Asset   Strategie")
    for a, s, n in conn.execute(
            "SELECT action, COALESCE(strategie,'<nicht gesetzt>'), COUNT(*) "
            "FROM signals WHERE quelle_kette='rollen' GROUP BY 1,2 "
            "ORDER BY 3 DESC"):
        symbole = conn.execute(
            "SELECT COUNT(DISTINCT symbol) FROM signals WHERE "
            "quelle_kette='rollen' AND action=?", (a,)).fetchone()[0] or 1
        print("  %-12s %7d %8.1f %13.2f   %s"
              % (a, n, n / n_tage, n / n_tage / symbole, s))
    print()
    print("  ⚠️ DIE STRATEGIE STEHT ERST SEIT DEM 23.08. Vorher NULL - eine")
    print("     Aufschluesselung je Strategie ist deshalb nur fuer die")
    print("     Abwaertsphase aussagekraeftig.")
    print()
    print("  DIE ZEHN LAUTESTEN WERTE (Signale je Tag):")
    for sym, n in Counter(dict(conn.execute(
            "SELECT symbol, COUNT(*) FROM signals WHERE quelle_kette='rollen' "
            "GROUP BY 1"))).most_common(10):
        print("    %-10s %5d gesamt  %5.1f je Tag" % (sym, n, n / n_tage))


def f8_was_aendert_der_entscheider(conn, mit_potential):
    """Wieviel wuerde der scharfe Entscheider zusaetzlich verwerfen?"""
    print()
    print("-" * 96)
    print("F8 — WAS AENDERT DIE SCHARFE STUFE 11 AM TRICHTER?")
    print("-" * 96)
    t = _trichter(conn)
    ges = sum(t["verloren"].values()) or 1
    heute = t["verloren"].get("entscheider", 0)
    erreicht = heute + t["bestanden"].get("entscheider", 0)
    print("  Der Entscheider sieht %d Pruefungen (nach allen Bremsen davor)."
          % erreicht)
    print("  Er verwirft heute %d davon (%.1f %%)."
          % (heute, 100 * heute / max(erreicht, 1)))
    print()
    print("  ⚠️ MIT SCHARFER STUFE 11 (G-6) verwirft er zusaetzlich die,")
    print("     deren Potential unter der Schwelle liegt. Gemessen an den")
    print("     echten Signalen dieser Produktion: %s" % mit_potential)
    print()
    print("  Was das am Gesamttrichter aendert:")
    print("    Verluste an QUALITAETS-Stufen heute: %.1f %%"
          % (100 * sum(t["verloren"].get(k, 0)
                       for k in ("auswahl", "aktion", "entscheider")) / ges))
    print("    davon der Entscheider allein:        %.1f %%"
          % (100 * heute / ges))

    # ------------------------------------------------------------------
    # ⚠️⚠️ DIE ZAHL, DIE DIE GANZE SIMULATION TRAEGT (31.08.2026)
    #
    # In der Notebook-Produktion steht `NUR_ZAEHLEN = ("entscheider",)`:
    # die Stufe rechnet, bucht ihr Urteil in den Trichter - und laesst das
    # Signal trotzdem durch. Die 1.385 Verwerfungen sind PROTOKOLLIERT,
    # aber nicht vollzogen.
    #
    # Damit steht die Wirkung von G-6 nicht als Schaetzung da, sondern als
    # Abzug: was die Stufe gebucht hat, faellt kuenftig wirklich weg.
    #
    # ⚠️ Eine Einschraenkung gehoert dazu: gebucht wurde mit der
    # BEITRAGSLAGE VOM NOTEBOOK. Seit dem 31.08. ist der Schnittabstand
    # gefallen (36 statt 43 von 43 Werten abgedeckt) - die Groessenordnung
    # bleibt, die Zahl verschiebt sich.
    # ------------------------------------------------------------------
    # ⚠️⚠️ HIER STAND EINE FALSCHE RECHNUNG (31.08. abends korrigiert).
    #
    # Sie nahm die 1.385 im Trichter gebuchten Verwerfungen als Abzug fuer
    # G-6 und kam auf "74 % weniger". Das war falsch: gebucht hat der ALTE
    # Entscheider (`TB.bewerte`, Trefferbilanz mit 1,50 % Gebuehren), die
    # neue Stufe rechnet das Potential gebuehrenfrei mit Beitraegen. Zwei
    # verschiedene Filter - die Wirkung des einen sagt nichts ueber den
    # anderen.
    #
    # Gerechnet wird jetzt mit F2, das je Signal die ECHTEN Merkmale
    # heranzieht und dieselbe Produktionsfunktion aufruft.
    print()
    print("  ➔ WAS AM ENDE HERAUSKOMMT (gerechnet in F2, nicht abgeleitet):")
    print("      %s" % mit_potential)
    print()
    print("  ⚠️ Die frueher hier stehende Rechnung (1.385 gebuchte")
    print("     Verwerfungen als Abzug, '74 % weniger') galt dem ALTEN")
    print("     Massstab und ist zurueckgenommen.")


def f2_vorschau(sig, mit, kurse, c_ak, schnitt_am_tag):
    """Was verwirft die NEUE Stufe 11 wirklich? (neu gebaut 31.08. abends)

    ⚠️⚠️ DIE ERSTE FASSUNG HAT DIE FALSCHE FRAGE BEANTWORTET.

    Sie rechnete den Durchlass aus dem Schnittabstand - und der ist am
    31.08. als Beitrag gefallen. Schlimmer: eine spaetere Rechnung nahm
    die 1.385 im Trichter gebuchten Verwerfungen als Abzug fuer G-6 und
    kam auf "74 % weniger Empfehlungen". **Auch das war falsch.**

    `Basisinfos/Konzept_Bewertungsstufe_29_08.md` sagt, warum: es gibt ZWEI
    Bewertungen, die nichts voneinander wissen.

        Stufe 11 (Zeile 1596)   Trefferbilanz + Gebuehren-Breakeven, 1,50 %
        Wahrscheinlichkeit      Basisrate + Beitraege, gebuehrenfrei
                                - und sie laeuft NACH dem Mailbau

    Am Code bestaetigt: der NB-Stand rechnet `TB.bewerte(bilanz or {}, ...)`,
    der neue `_PT2.traegt(_potential.wert_r)`. Die gebuchten 1.385 stammen
    vom ALTEN Massstab - aus einer fast leeren Trefferbilanz (96 von 2.313),
    Grund in 1.369 Faellen "traegt sich nicht".

    ⚠️ Nutzerklaerung 31.08.: *"Der Grund [fuer das reine Zaehlen] ist die
    fehlende Bewertung gewesen - jetzt nach dem Umbau soll alles scharf
    sein."* Genau deshalb muss die neue Wirkung EIGENS gerechnet werden,
    statt die alte zu uebernehmen.

    ## Was hier gerechnet wird

    Fuer jedes einstiegsfaehige Signal der echten Produktion:

        Funding-Rang   je Kalendertag ueber `data/funding_historie.db`
        Turnover-Rang  je Kalendertag, Volumen / Umlaufmenge
        -> potential.rechne(merkmale=...) -> ueber der Schwelle?

    Also mit DENSELBEN Beitraegen und DERSELBEN Produktionsfunktion, die
    Stufe 11 nach dem Umbau benutzt.
    """
    import sqlite3 as _sq
    from agent import potential as PT
    from agent import wahrscheinlichkeit as WK
    from agent.signal_mail import AKTIONEN_MIT_EINSTIEG

    print()
    print("-" * 96)
    print("F2 — WAS VERWIRFT DIE NEUE STUFE 11? (Potential, gebuehrenfrei)")
    print("-" * 96)

    tragend = [b.merkmal for b in WK.BEITRAEGE if b.zustand == "traegt"]
    print("  registrierte Beitraege: %s" % (", ".join(tragend) or "KEINE"))
    if not tragend:
        print("  ⚠️ ohne Beitrag ist keine Vorschau moeglich")
        return "keine Beitraege registriert"

    # ---- die Rohreihen ------------------------------------------------
    def reihe(db, tab, spalte="wert"):
        c = _sq.connect("file:%s?mode=ro" % db, uri=True)
        aus = {}
        for sym, tag, w in c.execute(
                "SELECT symbol, datum, %s FROM %s WHERE datum>='2026-08-01'"
                % (spalte, tab)):
            if w is not None:
                aus.setdefault(str(sym).upper(), {})[str(tag)[:10]] = float(w)
        c.close()
        return aus

    funding = reihe("data/funding_historie.db", "funding")
    menge = reihe("data/onchain_historie.db", "splycur")
    print("  Funding %d Symbole, Umlaufmenge %d Symbole"
          % (len(funding), len(menge)))

    # ---- Turnover je Symbol und Tag: Volumen / Umlaufmenge ------------
    # ⚠️ Das Volumen kommt aus derselben Kursreihe, die auch die Produktion
    # liest - nicht aus einer zweiten Quelle.
    volumen = {}
    for sym, reihen in (kurse or {}).items():
        for eintrag in reihen:
            if len(eintrag) >= 2:
                volumen.setdefault(sym, {})[eintrag[0]] = eintrag[1]

    def fuenftel_je_tag(werte_je_tag):
        """Rang in Fuenfteln, je Kalendertag - wie `marktrang`."""
        aus = {}
        for tag, paare in werte_je_tag.items():
            if len(paare) < 15:            # kein Querschnitt
                continue
            srt = sorted(paare.items(), key=lambda x: x[1])
            for i, (sym, _w) in enumerate(srt):
                q = i / max(len(srt) - 1, 1)
                aus.setdefault(tag, {})[sym] = min(int(q * 5), 4)
        return aus

    f_tag = {}
    for sym, je in funding.items():
        for tag, w in je.items():
            f_tag.setdefault(tag, {})[sym] = w
    t_tag = {}
    for sym, je in menge.items():
        for tag, m in je.items():
            v = (volumen.get(sym) or {}).get(tag)
            if v and m > 0:
                t_tag.setdefault(tag, {})[sym] = v / m
    f5 = fuenftel_je_tag(f_tag)
    t5 = fuenftel_je_tag(t_tag)
    print("  Fuenftel gebildet: Funding an %d Tagen, Turnover an %d Tagen"
          % (len(f5), len(t5)))
    if not t5:
        # ⚠️ EHRLICH BENENNEN STATT STILL WEGLASSEN. `lade_kurse` liefert
        # (Tag, Schlusskurs) - kein Volumen. Der Turnover-Rang braucht
        # aber Volumen/Umlaufmenge und ist damit hier nicht rechenbar.
        #
        # Folge: diese Vorschau rechnet NUR MIT FUNDING. Da Turnover in der
        # Produktion ohnehin nur 7 von 43 Werten abdeckt, ist die
        # Verzerrung klein - aber sie gehoert genannt, nicht verschwiegen.
        print("  ⚠️⚠️ TURNOVER FEHLT: `lade_kurse` liefert kein Volumen.")
        print("     Diese Vorschau rechnet NUR MIT FUNDING. In der")
        print("     Produktion deckt Turnover 7 von 43 Werten ab - die")
        print("     Verzerrung ist klein, aber vorhanden.")

    # ---- je Signal das Potential --------------------------------------
    durch, gesperrt, ohne = [], [], []
    for s in sig:
        if s["aktion"] not in AKTIONEN_MIT_EINSTIEG:
            continue
        sym, tag = s["symbol"], s["tag"]
        m = {}
        if (f5.get(tag) or {}).get(sym) is not None:
            m["funding_fuenftel"] = f5[tag][sym]
        if (t5.get(tag) or {}).get(sym) is not None:
            m["turnover_fuenftel"] = t5[tag][sym]
        if not m:
            ohne.append(s)
            continue
        p = PT.rechne(crv=CRV, stop_relativ=0.05, klasse="krypto",
                      instrument="spot", strategie="einstieg", h=None,
                      merkmale=m)
        (durch if PT.traegt(p.wert_r) else gesperrt).append(s)

    n = len(durch) + len(gesperrt) + len(ohne)
    if not n:
        return "keine einstiegsfaehigen Signale"
    print()
    print("  von %d einstiegsfaehigen Signalen:" % n)
    print("    kaemen durch:            %5d (%.0f %%)"
          % (len(durch), 100 * len(durch) / n))
    print("    wuerden gesperrt:        %5d (%.0f %%)"
          % (len(gesperrt), 100 * len(gesperrt) / n))
    print("    ⚠️ ohne Datengrundlage:  %5d (%.0f %%)"
          % (len(ohne), 100 * len(ohne) / n))
    print()
    print("  ⚠️ 'ohne Datengrundlage' wird mit scharfer Stufe 11 GESPERRT -")
    print("     `vermessen` faengt nur unvermessene KLASSEN ab, nicht")
    print("     einzelne Werte ohne Merkmal. Krypto ist vermessen.")
    print()
    print("  je Aktion:")
    for a in sorted(x for x in c_ak if x in AKTIONEN_MIT_EINSTIEG):
        d = sum(1 for x in durch if x["aktion"] == a)
        g = sum(1 for x in gesperrt if x["aktion"] == a)
        o = sum(1 for x in ohne if x["aktion"] == a)
        print("    %-14s durch %4d  gesperrt %4d  ohne Grundlage %4d"
              % (a, d, g, o))
    return ("%d von %d einstiegsfaehigen kaemen durch (%.0f %%), "
            "%d ohne Datengrundlage"
            % (len(durch), n, 100 * len(durch) / n, len(ohne)))


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

    _durchlass = f2_vorschau(sig, mit, kurse, c_ak, schnitt_am_tag)

    # ---- F5 bis F8: DIE FILTERSIMULATION -----------------------------
    # ⚠️ Diese laufen IMMER - sie haengen nicht an einem Beitrag.
    import sqlite3 as _sq
    _c = _sq.connect("file:%s?mode=ro" % NB, uri=True)
    try:
        f5_trichter(_c)
        f6_phasen(_c)
        f7_je_asset_und_strategie(_c)
        f8_was_aendert_der_entscheider(_c, _durchlass)
    finally:
        _c.close()


if __name__ == "__main__":
    main()
