"""Der feste Kennzahlen-Katalog aus Test_und_Verifikationsmethodik 2.1.

15 Punkte, die bei JEDEM neuen Export durchzugehen sind - auch wenn der Anlass
ein anderer war. Bisher wurde das von Hand gemacht, was zwei Nachteile hat: es
kostet jedes Mal Zeit, und es wird unter Zeitdruck als Erstes weggelassen.
Genau daran ist am 05.08. ein Punkt durchgerutscht (Z-3-Aufschluesselung fehlte
im Export und fiel erst bei der Erstausloesung auf).

Meldet AUFFAELLIGKEITEN, nicht Vollstaendigkeit - was in Ordnung ist, bekommt
eine Zeile, was nicht, einen Marker. Liest nur den Export, keine Produktiv-DB.
"""
from __future__ import annotations

import io
import json
import statistics
import sys
from collections import Counter

# ⚠️⚠️ OHNE DAS BRICHT DER SCHLUSSBERICHT AB (23.09.2026, am Lauf
# gefunden). Windows gibt hier cp1252 vor; das erste ⚠ im Text wirft
# UnicodeEncodeError. Getroffen hat es ausgerechnet die Zeile, die sagt,
# WELCHE PUNKTE WEGEN DER SCHLANKEN DIAGNOSE UNGEPRUEFT BLIEBEN - der
# Lauf sah bis dahin vollstaendig aus und meldete "AUFFAELLIGKEITEN: 4",
# obwohl sechs Abschnitte gar nicht geprueft worden waren.
# ⚠️ Ein Abbruch NACH dem Ergebnis ist gefaehrlicher als einer davor:
# man liest die Zahlen und merkt nicht, dass der Vorbehalt fehlt.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

STANDARD = (r'K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten'
            r'\notebook_diagnose.json')
WARN = "  [!]"
OK = "      "


def z(wert, stellen=1):
    return "-" if wert is None else f"{wert:.{stellen}f}"


AUSGELASSEN = []
"""Welche Abschnitte die SCHLANKE Diagnose nicht enthaelt."""


def hole(d, schluessel, vorgabe=None):
    """Einen Abschnitt lesen - und den PLATZHALTER erkennen.

    ⚠⚠⚠ SEIT DER SCHLANKEN DIAGNOSE (20.09.2026) steht
    in ausgelassenen Abschnitten ein STRING, keine Liste und kein
    Dict: `"__ausgelassen__: ... python extract_notebook_diagnose.py
    --voll"`. Dieser Katalog hat das nicht gewusst und ist an
    `spot_signals` mit `AttributeError` GESTORBEN - Punkt 8 bis 15
    wurden seither NIE geprueft, ohne dass es auffiel (gefunden
    22.09.2026).

    ⚠ Er liefert jetzt die Vorgabe und MERKT SICH, was fehlte.
    Am Ende steht, welche Punkte `--voll` braeuchten - ein
    ausgelassener Abschnitt ist eine Aussage, kein leeres Ergebnis.
    """
    v = d.get(schluessel, vorgabe)
    if isinstance(v, str) and v.startswith("__ausgelassen__"):
        if schluessel not in AUSGELASSEN:
            AUSGELASSEN.append(schluessel)
        return vorgabe
    return v


def main() -> None:
    pfad = sys.argv[1] if len(sys.argv) > 1 else STANDARD
    d = json.load(io.open(pfad, encoding="utf-8"))
    funde = []

    def melde(text):
        funde.append(text)
        print(f"{WARN} {text}")

    print(f"Export: {pfad}")
    print(f"Bloecke: {len(d)}")
    print("=" * 78)

    # 1 LLM-Budget
    # ⚠⚠⚠ ZWEI ZAEHLER FUER DIESELBE GROESSE, EINER TOT (22.09.2026).
    #
    # `llm_calls_heute` meldete {groq 0, mistral 0, gemini 0,
    # openrouter 0} - und kennt `zai` gar nicht. `llm_aufrufe_heute`
    # meldete im SELBEN Export gemini 84 und zai 18. Punkt 1 hat
    # damit einen FEHLALARM erzeugt ("keine LLM-Calls"), waehrend die
    # Kette normal lief.
    #
    # ⚠ Gelesen wird jetzt der reichere der beiden, und die
    # Abweichung wird GEMELDET statt verschwiegen - ein toter Zaehler
    # faellt sonst nie auf.
    _alt = hole(d, "llm_calls_heute", {}) or {}
    _neu = hole(d, "llm_aufrufe_heute", {}) or {}
    calls = _neu if sum(_neu.values() or [0]) >= sum(
        _alt.values() or [0]) else _alt
    if _alt and _neu and _alt != _neu:
        melde("zwei LLM-Zaehler weichen ab: llm_calls_heute=%s gegen "
              "llm_aufrufe_heute=%s - gelesen wird der reichere"
              % (_alt, _neu))
    print(f"\n 1. LLM-Calls heute: {calls}")
    if calls.get("mistral", 0) > 350:
        melde(f"Mistral bei {calls['mistral']} - Limit 400 rueckt naeher")

    # 2 Signal-Volumen
    sv = hole(d, "signal_volumen_heute", {})
    print(f"\n 2. Signal-Volumen heute: {sv}")
    # DER WIDERSPRUCH, DER DEN TOTEN ZAEHLER VERRATEN HAETTE (17.08.2026).
    #
    # Der Export meldete "spot 0, hebel 0" und zwei Bloecke weiter
    # "gemini: 86 Aufrufe". Beides stand nebeneinander, monatelang, und
    # niemandem fiel es auf - weil eine Null kein Fehler ist, sondern
    # aussieht wie ein ruhiger Tag.
    #
    # Ein Modellaufruf OHNE Urteil ist entweder ein toter Zaehler oder ein
    # Ausfall der Kette. Beides gehoert gemeldet, und zwar hier.
    rk = (sv or {}).get("rollen_kette") or {}
    aufrufe = sum(int(v or 0) for v in
                  (hole(d, "llm_aufrufe_heute") or {}).values())
    if rk.get("nicht_verfuegbar"):
        melde(f"Rollen-Urteile nicht zaehlbar: {rk['nicht_verfuegbar']}")
    elif aufrufe > 20 and int(rk.get("gesamt") or 0) == 0:
        melde(f"{aufrufe} Modellaufrufe, aber NULL Urteile der Rollen-Kette "
              f"- toter Zaehler oder ausgefallene Kette")
    elif rk.get("gesamt"):
        anteil = 100.0 * int(rk.get("mit_handlung") or 0) / int(rk["gesamt"])
        print(f"     Rollen-Kette: {rk['gesamt']} Urteile "
              f"({rk['hebel']} Hebel / {rk['spot']} Spot), "
              f"{rk.get('mit_handlung')} mit Handlung ({anteil:.0f} %)")
        print(f"     Aktionen: {rk.get('aktionen')}")

    # 3 Provider-Performance
    pp = hole(d, "provider_performance", {})
    print(f"\n 3. Provider-Performance: {len(pp)} Gruppen")

    # 4 Konfidenz-Kalibrierung
    #
    # BETRIFFT NUR ALTDATEN. Die neue Rollen-Kette erhebt keine Konfidenz mehr
    # (E3, 13.08.) - sie hing mit dem Ergebnis nicht zusammen (r = +0,073,
    # n = 92) und war faktisch konstant. Der Block bleibt, weil die Altsignale
    # weiter im Export stehen; fuer Signale mit quelle_kette='rollen' ist er
    # leer, und das ist kein Fehlstand. Der Nachfolger steht unter Punkt 16.
    print("\n 4. Konfidenz-Kalibrierung (nur ALTE Kette, siehe 16.):")
    for tier, baender in (hole(d, "konfidenz_kalibrierung") or {}).items():
        for band, w in (baender or {}).items():
            if not isinstance(w, dict):
                continue
            diff = w.get("differenz_prozentpunkte")
            n = w.get("anzahl")
            print(f"      {tier:8s} {band:8s} n={n:4} "
                  f"vorhergesagt {z(w.get('avg_vorhergesagte_konfidenz_pct'))} % "
                  f"-> tatsaechlich {z(w.get('tatsaechliche_trefferquote_pct'))} % "
                  f"(Delta {z(diff)} pp)")

    # 5 Z.ai
    zg = hole(d, "zai_gegenpruefung_verlauf", {})
    print(f"\n 5. Z.ai-Gegenpruefung: {len(zg)} Bloecke")

    # 6 Gate-Vetos - NACH MUSTER, nicht nach exaktem Text.
    #
    # Punkt 6 des Katalogs verlangt "insbesondere NEUE oder sich haeufende
    # Muster". Gezaehlt wurde bis zum 10.08. nach dem exakten Grundtext, und
    # weil die Pipelines ihre Gruende mit eingesetzten Werten bauen, zerfiel
    # EIN Grund in beliebig viele Toepfe ("CRV 1.0 unter Minimum 2.0",
    # "CRV 1.4 unter Minimum 2.0", ...). Da diese Liste nach Haeufigkeit
    # sortiert und nach acht Zeilen abschneidet, konnte der GROESSTE Grund
    # dadurch komplett unsichtbar bleiben.
    #
    # Aeltere Exporte kennen den Muster-Schluessel noch nicht - fuer die wird
    # er aus den Rohschluesseln abgeleitet, damit die Auswertung nicht erst
    # auf einen neuen Export warten muss.
    print("\n 6. Gate-/Veto-Haeufigkeit (Hebel, letzte Tage) - nach MUSTER:")
    gv = hole(d, "gate_veto_haeufigkeit", {})
    fuer = gv.get("hebel_risk_veto_reason_muster")
    roh = gv.get("hebel_risk_veto_reason_letzte_tage") or gv.get("hebel_risk_veto_reason") or {}
    if not fuer and isinstance(roh, dict):
        from extract_notebook_diagnose import veto_muster
        abgeleitet: Counter = Counter()
        for grund, n in roh.items():
            if isinstance(n, int):
                abgeleitet[veto_muster(str(grund))] += n
        fuer = dict(abgeleitet.most_common())
        print("      (aus den Rohschluesseln abgeleitet - Export ist aelter "
              "als der Muster-Schluessel)")
    if isinstance(fuer, dict):
        for grund, n in sorted(fuer.items(), key=lambda x: -x[1] if isinstance(x[1], int) else 0)[:8]:
            print(f"      {n:5} x {str(grund)[:88]}")
        if isinstance(roh, dict) and roh:
            print(f"      [{len(roh)} Rohtexte -> {len(fuer)} Muster]")

    # 7 Log-Auffaelligkeiten
    lg = [l for l in hole(d, "log_auszug", []) or [] if isinstance(l, str)]
    tb = sum(1 for l in lg if "Traceback" in l)
    crit = sum(1 for l in lg if "CRITICAL" in l)
    err = sum(1 for l in lg if " ERROR " in l)
    starts = sum(1 for l in lg if 'Added job "hebel' in l)
    print(f"\n 7. Log ({len(lg)} Zeilen, {d.get('log_fenster_stunden')} h): "
          f"ERROR {err}, Traceback {tb}, CRITICAL {crit}, App-Starts ~{starts}")
    if crit:
        melde(f"{crit} CRITICAL-Zeilen im Log")
    if tb > 5:
        # ⚠️ MIT ZEITBEZUG UND HAEUFIGSTER URSACHE (16.08.2026).
        #
        # "11970 Tracebacks im Log-Fenster" liest sich wie ein akuter Ausfall.
        # Nachgesehen waren 11.953 davon EIN Fehler, alle aus 36 Minuten am
        # 14.08. - vor dem Pull, der ihn behob. Seither keiner mehr.
        #
        # Eine grosse Zahl ohne Zeitbezug ist ein Fehlalarm-Muster: sie
        # ueberdeckt die echten Funde daneben. Deshalb sagt die Meldung jetzt
        # WANN und WORAN.
        import collections as _c2
        import re as _re2
        stempel, letzte = [], None
        arten = _c2.Counter()
        for zeile in lg:
            m = _re2.match(r"(\d{4}-\d\d-\d\d \d\d:\d\d)", zeile)
            if m:
                letzte = m.group(1)
            if "Traceback" in zeile and letzte:
                stempel.append(letzte)
            f2 = _re2.search(r"(\w+(?:Error|Exception)): (.{0,60})", zeile)
            if f2:
                arten[f"{f2.group(1)}: {f2.group(2).strip()[:50]}"] += 1
        spanne = (f", alle zwischen {min(stempel)} und {max(stempel)}"
                  if stempel else "")
        haeufigste = arten.most_common(1)
        ursache = (f" - haeufigste Ursache {haeufigste[0][1]}x "
                   f"{haeufigste[0][0]}" if haeufigste else "")
        melde(f"{tb} Tracebacks im Log-Fenster{spanne}{ursache}")
    jf = hole(d, "job_fehlschlaege", []) or []
    if jf:
        # ⚠ `job`/`name` gibt es in diesen Zeilen nicht - der
        # Text steht in `nachricht`. Die Gruppierung meldete deshalb
        # stur {"?": 60} und sagte damit nichts (22.09.2026).
        arten = Counter(
            (str(x.get("job") or x.get("name")
                 or x.get("nachricht") or "?"))[:58]
            for x in jf if isinstance(x, dict))
        _tage = sorted({str(x.get("zeitstempel"))[:10] for x in jf
                        if isinstance(x, dict) and x.get("zeitstempel")})
        melde("%d Job-Fehlschlaege an %s: %s"
              % (len(jf), ", ".join(_tage) or "?",
                 "; ".join("%dx %s" % (n, k)
                           for k, n in arten.most_common(3))))

    # 8 Wartezeit bis Aufloesung
    hs = hole(d, "hebel_signals", []) or []
    dauern = []
    for s in hs:
        a, b = s.get("created_at"), s.get("outcome_entschieden_am")
        if a and b:
            dauern.append((b[:10], a[:10]))
    gleich = sum(1 for b, a in dauern if a == b)
    print(f"\n 8. Aufgeloeste Hebel-Signale: {len(dauern)}, davon "
          f"{gleich} am selben Kalendertag ({gleich/len(dauern)*100:.0f} %)" if dauern
          else "\n 8. keine aufgeloesten Hebel-Signale mit Datum")

    # 9 SL-MFE
    mfe_trotz_sl = [s for s in hs if s.get("outcome_status") == "stop_loss"
                    and isinstance(s.get("outcome_max_realisiertes_crv"), (int, float))
                    and s["outcome_max_realisiertes_crv"] >= 1.0]
    sl = [s for s in hs if s.get("outcome_status") == "stop_loss"]
    if sl:
        print(f"\n 9. Stop-Loss-Faelle: {len(sl)}, davon {len(mfe_trotz_sl)} mit MFE >= 1R "
              f"({len(mfe_trotz_sl)/len(sl)*100:.0f} %) - Ausstiegsproblem-Indikator")

    # 10 Fazit-Selbsteinschaetzung
    ff = Counter(s.get("fazit_folgen") for s in hs if s.get("fazit_folgen"))
    print(f"\n10. Fazit-Selbsteinschaetzung (Hebel): {dict(ff)}")

    # 11 Z-3
    z3 = hole(d, "z3_status", {})
    print(f"\n11. Z-3: aktuell {z(z3.get('aktuell_prozent'), 2)} % / Schwelle "
          f"{z3.get('schwelle_prozent')} % / ausgeloest={z3.get('ausgeloest')} / "
          f"{z3.get('tage_historie')} Tage")
    if z3.get("ausgeloest"):
        melde("Z-3 ist AUSGELOEST - Drawdown ueber der Schwelle")
    fx = sum(1 for l in lg if "Spannweite" in l and "verworfen" in l.lower())
    if fx:
        melde(f"{fx} verworfene FX-Ableitungen im Log - Z-3-Wert pruefen")

    # 12 Ausstiegsempfehlungen
    ae = (hole(d, "ausstiegs_empfehlungen") or {}).get("empfehlungen") or []
    offen_r = sum(x.get("sichert_r") or 0 for x in ae)
    print(f"\n12. Ausstiegsempfehlungen: {len(ae)}, zusammen {offen_r:.1f} R ungesichert")
    for x in sorted(ae, key=lambda y: -(y.get("mfe_r") or 0))[:3]:
        print(f"      {x.get('tier'):7s} {x.get('symbol'):8s} MFE {z(x.get('mfe_r'), 2)} R "
              f"-> sichert {z(x.get('sichert_r'), 2)} R")

    # 13 Score-Komponenten
    # ⚠️⚠️⚠️ EIN AUSGELASSENER ABSCHNITT DARF KEINEN BEFUND ERZEUGEN
    # (23.09.2026). Punkt 13 und 14 lesen beide aus
    # `rohdaten_fuer_backtest` - und der ist in der SCHLANKEN Diagnose
    # ausgelassen. Sie meldeten dann "0 Trigger, 0 Kandidaten" und
    # "Makro-Historie nur 0 Zeilen" als AUFFAELLIGKEIT, obwohl gar nichts
    # gemessen worden war.
    #
    # ⛔ Beim Nutzer kam das als Datenproblem an ("warum keine Makro
    # historie, nutzen wir diese nicht?"). Nachgesehen: `datenfrische`
    # meldet fuer dieselbe Sache 1.186 Zeilen, Abruf 1 Tag alt, Urteil
    # "frisch". Die Daten waren immer da.
    #
    # ⚠️ Das ist derselbe Fehlertyp wie 2.539: eine Zeile, die aussieht,
    # als haette sie geprueft. Ein Fehlalarm kostet mehr als eine Luecke,
    # weil er Arbeit ausloest.
    # ⚠️ ERST HOLEN, DANN FRAGEN: `AUSGELASSEN` wird von `hole()` gefuellt.
    # Meine erste Fassung fragte davor - da stand der Schluessel noch nicht
    # drin, und der Fehlalarm blieb genau so stehen wie vorher.
    rb = hole(d, "rohdaten_fuer_backtest", {})
    _rb_da = "rohdaten_fuer_backtest" not in AUSGELASSEN
    if _rb_da:
        print(f"\n13. Score-Rohdaten: "
              f"{len(rb.get('hebel_triggers_alle') or [])} Trigger gesamt, "
              f"{len(rb.get('hebel_triggers_kandidaten') or [])} Kandidaten")
    else:
        print("\n13. Score-Rohdaten: UNGEPRUEFT - `rohdaten_fuer_backtest` "
              "fehlt (schlanke Diagnose)")

    # 14 Makro-/OI-Reichweite
    if _rb_da:
        mh = rb.get("macro_historie") or []
        oi = rb.get("oi_historie") or []
        print(f"\n14. Makro-Historie {len(mh)} Zeilen, "
              f"OI-Historie {len(oi)} Zeilen")
        if len(mh) < 40:
            melde(f"Makro-Historie nur {len(mh)} Zeilen - Fenster bei "
                  f"jedem Mischen beachten")
    else:
        # ⚠️ NICHT SCHWEIGEN, SONDERN UMLEITEN: die Frage *,ist die
        # Makrohistorie da`* beantwortet `datenfrische` auch in der
        # schlanken Fassung - und zwar naeher an der Quelle.
        _lang = [q for q in (hole(d, "datenfrische") or {}).get("quellen", [])
                 if isinstance(q, dict) and q.get("job") == "makro_analog"]
        if _lang:
            _q = _lang[0]
            print("\n14. Makro-Historie: aus `rohdaten_fuer_backtest` "
                  "UNGEPRUEFT (fehlt), aber")
            print("    `datenfrische` meldet %s Zeilen, Datenstand %s, "
                  "Abruf %s Tage alt -> %s"
                  % (_q.get("zeilen"), _q.get("datenstand"),
                     _q.get("abrufalter_tage"), _q.get("urteil")))
            if _q.get("urteil") != "frisch":
                melde("Makro-Historie laut datenfrische NICHT frisch: %s"
                      % (_q,))
        else:
            print("\n14. Makro-Historie: UNGEPRUEFT - weder "
                  "`rohdaten_fuer_backtest` noch eine `makro_analog`-Zeile "
                  "in `datenfrische`")

    # 15 Watchlist-Stammdaten
    ws = hole(d, "watchlist_stammdaten") or {}
    print(f"\n15. Watchlist-Stammdaten: {len(ws)} Symbole")
    if not ws:
        melde("watchlist_stammdaten FEHLT - jede Spot-Auswertung waere ein Mischtopf")

    # 16 ROLLEN-KETTE - der aussagekraeftigste neue Wert ueberhaupt.
    #
    # WOZU. Ein Lauf mit 45 Symbolen hinein und 0 Signalen heraus sah bisher
    # identisch aus, egal an welcher Stufe es verschwand: am Ankertag, am
    # Urteil, an der Geometrie oder an der Rechnung. Die Durchlaessigkeit sagt
    # WO - und damit, ob ein Fund ein Modell- oder ein Rechenproblem ist.
    rk = hole(d, "rollen_kette") or {}
    laeufe = (rk.get("gate_durchlaessigkeit") or {}).get("laeufe") or []
    print(f"\n16. Rollen-Kette: {len(laeufe)} Laeufe, "
          f"{(rk.get('lagebilder') or {}).get('anzahl_gesamt', 0)} Lagebilder")
    if not rk:
        print("      (Export ist aelter als der Umbau - kein Fehlstand)")
    for lauf in laeufe[:3]:
        best = lauf.get("bestanden") or {}
        verl = lauf.get("verloren") or {}
        print(f"      {str(lauf.get('erfasst_am'))[:16]} "
              f"{lauf.get('hinein')} hinein -> {lauf.get('heraus')} heraus")
        # ⚠️⚠️⚠️ DIE STUFEN WERDEN AUS DEN DATEN ABGELEITET, NICHT
        # AUFGEZAEHLT (23.09.2026). Hier stand eine feste Liste von acht
        # Stufen - und der Export fuehrt ZWOELF. Die vier fehlenden
        # (`anlass`, `auswahl`, `terminmarkt`, `wiederholung`) sind genau
        # die, die SPERREN.
        #
        # ⛔ DARAN HING DER OFFENE FALL "N hinein, 0 heraus": er sah
        # unerklaert aus, WEIL DIE ERKLAERUNG NICHT ANGEZEIGT WURDE. Am
        # 23.09. zeigte der 46er-Lauf lagebild 46 -> anlass 41 ->
        # auswahl 23 -> wiederholung 1 -> urteil 1. Die Kette war nie
        # kaputt; die Anzeige war es.
        #
        # ⚠️ Stehende Regel `pruefung-zaehlt-zustaende-auf`: was
        # aufgezaehlt wird, veraltet still. `dict` haelt die
        # Einfuegereihenfolge, also bleibt die Kettenreihenfolge
        # erhalten; `verloren` liefert nach, was in `bestanden` fehlt.
        _stufen = list(best) + [s for s in verl if s not in best]
        for stufe in _stufen:
            if stufe in best or stufe in verl:
                print(f"        {stufe:14s} bestanden {best.get(stufe, 0):3} "
                      f"| verloren {verl.get(stufe, 0):3}")

    for lauf in laeufe[:3]:
        wann = str(lauf.get("erfasst_am"))[:16]
        best = lauf.get("bestanden") or {}
        # a) Der Deadloop ist zurueck: Urteile ja, Aktionen nein.
        if best.get("urteil", 0) >= 10 and best.get("aktion", 0) == 0:
            melde(f"{wann}: {best['urteil']} Urteile, aber 0 Aktionen - "
                  "das ist der Deadloop-Zustand von vor dem Umbau")
        # b) Das Rechenproblem: Einstiege ja, aber keiner traegt sich.
        if best.get("risikoschicht", 0) >= 5 and best.get("entscheider", 0) == 0:
            melde(f"{wann}: {best['risikoschicht']} Einstiege, keiner traegt "
                  "sich nach Kosten - Basisrate gegen Breakeven pruefen")
        # c) Die Faktorzahl sagt die Aktion voraus (Umbauplan Kap. 15).
        #    `faktorzahlen` ist eine LISTE je Urteil, kein Zaehldict - erst
        #    beim Nachlesen von rollen_gate.als_json() gesehen, und eine
        #    .items()-Annahme haette hier still nie gemeldet.
        fz = lauf.get("faktorzahlen")
        if isinstance(fz, list) and len(fz) >= 10 and len(set(fz)) <= 2:
            melde(f"{wann}: Faktorzahl nimmt ueber {len(fz)} Urteile nur "
                  f"{sorted(set(fz))} an - sie ist die Entscheidung noch "
                  "einmal, offener Punkt vor Produktivgang")
        # d) Z1 zaehlt nur, aber gezaehlt wird es. Dict Symbol -> Regelliste.
        z1 = lauf.get("z1_verstoesse")
        if isinstance(z1, dict) and z1:
            regeln: Counter = Counter(r for liste in z1.values() for r in liste)
            melde(f"{wann}: Z1-Befund bei {len(z1)} Ausgabe(n) - "
                  f"{dict(regeln.most_common())}. Verwirft nichts, steht aber")

    # Zusatz: sind die neuen Fakt-Bloecke angekommen?
    fk = hole(d, "hebel_faktensaetze") or {}
    bjt = fk.get("bloecke_je_tag")
    print(f"\n +. Fakt-Ankunft (neuer Block seit 06.08.): "
          f"{'vorhanden' if bjt else 'NOCH NICHT im Export - Notebook hat den neuen Stand nicht'}")
    if bjt:
        for tag in sorted(bjt)[-3:]:
            e = bjt[tag]
            print(f"      {tag}: {e.get('_faktensaetze')} Saetze | "
                  f"kosten={e.get('kosten',0)} ausstiegsregel={e.get('ausstiegsregel',0)} "
                  f"systemguete={e.get('systemguete',0)} crv_baender={e.get('crv_baender',0)} "
                  f"score_gesamt={e.get('score_gesamt',0)}")

    print()
    print("=" * 78)
    print(f"AUFFAELLIGKEITEN: {len(funde)}")
    for f in funde:
        print(f"  - {f}")


def schlussbericht():
    """⚠ Ein ausgelassener Abschnitt ist eine AUSSAGE."""
    print()
    print("=" * 78)
    if AUSGELASSEN:
        print("  ⚠ SCHLANKE DIAGNOSE - %d Abschnitte fehlten, "
              "die zugehoerigen Punkte sind UNGEPRUEFT:"
              % len(AUSGELASSEN))
        for k in AUSGELASSEN:
            print("      %s" % k)
        print("    Volle Fassung: python extract_notebook_diagnose.py --voll")
        print("    ⚠ Sie stoert den Betrieb (295 MB Upload) - "
              "nur anfordern, wenn ein Punkt daran haengt.")
    else:
        print("  ✔ VOLLE DIAGNOSE - alle Abschnitte lagen vor")


if __name__ == "__main__":
    main()
    schlussbericht()
