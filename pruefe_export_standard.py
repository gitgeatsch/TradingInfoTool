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

STANDARD = (r'K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten'
            r'\notebook_diagnose.json')
WARN = "  [!]"
OK = "      "


def z(wert, stellen=1):
    return "-" if wert is None else f"{wert:.{stellen}f}"


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
    calls = d.get("llm_calls_heute", {})
    print(f"\n 1. LLM-Calls heute: {calls}")
    if calls.get("mistral", 0) > 350:
        melde(f"Mistral bei {calls['mistral']} - Limit 400 rueckt naeher")

    # 2 Signal-Volumen
    sv = d.get("signal_volumen_heute", {})
    print(f"\n 2. Signal-Volumen heute: {sv}")

    # 3 Provider-Performance
    pp = d.get("provider_performance", {})
    print(f"\n 3. Provider-Performance: {len(pp)} Gruppen")

    # 4 Konfidenz-Kalibrierung
    #
    # BETRIFFT NUR ALTDATEN. Die neue Rollen-Kette erhebt keine Konfidenz mehr
    # (E3, 13.08.) - sie hing mit dem Ergebnis nicht zusammen (r = +0,073,
    # n = 92) und war faktisch konstant. Der Block bleibt, weil die Altsignale
    # weiter im Export stehen; fuer Signale mit quelle_kette='rollen' ist er
    # leer, und das ist kein Fehlstand. Der Nachfolger steht unter Punkt 16.
    print("\n 4. Konfidenz-Kalibrierung (nur ALTE Kette, siehe 16.):")
    for tier, baender in (d.get("konfidenz_kalibrierung") or {}).items():
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
    zg = d.get("zai_gegenpruefung_verlauf", {})
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
    gv = d.get("gate_veto_haeufigkeit", {})
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
    lg = [l for l in d.get("log_auszug", []) if isinstance(l, str)]
    tb = sum(1 for l in lg if "Traceback" in l)
    crit = sum(1 for l in lg if "CRITICAL" in l)
    err = sum(1 for l in lg if " ERROR " in l)
    starts = sum(1 for l in lg if 'Added job "hebel' in l)
    print(f"\n 7. Log ({len(lg)} Zeilen, {d.get('log_fenster_stunden')} h): "
          f"ERROR {err}, Traceback {tb}, CRITICAL {crit}, App-Starts ~{starts}")
    if crit:
        melde(f"{crit} CRITICAL-Zeilen im Log")
    if tb > 5:
        melde(f"{tb} Tracebacks im Log-Fenster")
    jf = d.get("job_fehlschlaege", [])
    if jf:
        arten = Counter((str(x.get("job") or x.get("name") or "?")) for x in jf
                        if isinstance(x, dict))
        melde(f"{len(jf)} Job-Fehlschlaege: {dict(arten.most_common(5))}")

    # 8 Wartezeit bis Aufloesung
    hs = d.get("hebel_signals", [])
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
    z3 = d.get("z3_status", {})
    print(f"\n11. Z-3: aktuell {z(z3.get('aktuell_prozent'), 2)} % / Schwelle "
          f"{z3.get('schwelle_prozent')} % / ausgeloest={z3.get('ausgeloest')} / "
          f"{z3.get('tage_historie')} Tage")
    if z3.get("ausgeloest"):
        melde("Z-3 ist AUSGELOEST - Drawdown ueber der Schwelle")
    fx = sum(1 for l in lg if "Spannweite" in l and "verworfen" in l.lower())
    if fx:
        melde(f"{fx} verworfene FX-Ableitungen im Log - Z-3-Wert pruefen")

    # 12 Ausstiegsempfehlungen
    ae = (d.get("ausstiegs_empfehlungen") or {}).get("empfehlungen") or []
    offen_r = sum(x.get("sichert_r") or 0 for x in ae)
    print(f"\n12. Ausstiegsempfehlungen: {len(ae)}, zusammen {offen_r:.1f} R ungesichert")
    for x in sorted(ae, key=lambda y: -(y.get("mfe_r") or 0))[:3]:
        print(f"      {x.get('tier'):7s} {x.get('symbol'):8s} MFE {z(x.get('mfe_r'), 2)} R "
              f"-> sichert {z(x.get('sichert_r'), 2)} R")

    # 13 Score-Komponenten
    rb = d.get("rohdaten_fuer_backtest", {})
    print(f"\n13. Score-Rohdaten: {len(rb.get('hebel_triggers_alle') or [])} Trigger gesamt, "
          f"{len(rb.get('hebel_triggers_kandidaten') or [])} Kandidaten")

    # 14 Makro-/OI-Reichweite
    mh, oi = rb.get("macro_historie") or [], rb.get("oi_historie") or []
    print(f"\n14. Makro-Historie {len(mh)} Zeilen, OI-Historie {len(oi)} Zeilen")
    if len(mh) < 40:
        melde(f"Makro-Historie nur {len(mh)} Zeilen - Fenster bei jedem Mischen beachten")

    # 15 Watchlist-Stammdaten
    ws = d.get("watchlist_stammdaten") or {}
    print(f"\n15. Watchlist-Stammdaten: {len(ws)} Symbole")
    if not ws:
        melde("watchlist_stammdaten FEHLT - jede Spot-Auswertung waere ein Mischtopf")

    # 16 ROLLEN-KETTE - der aussagekraeftigste neue Wert ueberhaupt.
    #
    # WOZU. Ein Lauf mit 45 Symbolen hinein und 0 Signalen heraus sah bisher
    # identisch aus, egal an welcher Stufe es verschwand: am Ankertag, am
    # Urteil, an der Geometrie oder an der Rechnung. Die Durchlaessigkeit sagt
    # WO - und damit, ob ein Fund ein Modell- oder ein Rechenproblem ist.
    rk = d.get("rollen_kette") or {}
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
        for stufe in ("auftrag", "fakten", "lagebild", "urteil", "aktion",
                      "geometrie", "risikoschicht", "entscheider"):
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
    fk = d.get("hebel_faktensaetze") or {}
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


if __name__ == "__main__":
    main()
