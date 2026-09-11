# -*- coding: utf-8 -*-
"""H-4 - DIE HEBELFUEHRUNG: ein Hebel ist ein TRADE, kein Bestand (11.09.2026).

DER AUFTRAG (Anforderungen O5, Paket B Schritt 20): *"Hebel ist ein TRADE mit
Lebenszyklus, Spot ein Bestand. Stop, Ziel, Liquidationsabstand und taegliche
Finanzierung werden gefuehrt; Schliessen und Reduzieren kommen als Mail."*

WAS ES VORHER GAB - UND WAS FEHLTE (Sichtung 11.09.):

    `hebel_positions`         die ECHTEN Positionen, alle 15 Minuten aus den
                              Bitpanda-Transaktionen rekonstruiert, mit
                              Liquidationspreis ueber die echten Haltetage
    `ausstiegsrechnung`       Trailing, Widerlegung, Frist, Ziel - aber je
                              SIGNAL, in R, ohne Liquidation und Finanzierung
    `positionsfuehrung`       eine Position je Symbol - fuer SPOT (Einstand,
                              Break-even), ausdruecklich ohne Stop

    Niemand verband die echte Position mit ihrem Plan. Die Liquidation stand
    in der Datenbank und wurde nirgends gelesen; die Finanzierung, die sie
    jeden Tag naeher an den Einstieg schiebt, stand nirgends in einer Mail.

WAS DIESES MODUL TUT - fuer jede OFFENE Position aus `hebel_positions`:

    1. den PLAN zuordnen: das juengste Hebelsignal der Rollen-Kette desselben
       Symbols und derselben Richtung aus den Tagen vor der Eroeffnung
    2. rechnen: Einstand, Tage, Ergebnis, Finanzierung bisher und je Tag,
       Liquidationspreis mit den echten Tagen, Abstand dorthin
    3. den Plan pruefen: `ausstiegsrechnung.bewerte()` - DIESELBE Funktion
       wie fuer jedes Signal, keine zweite Fassung
    4. RM-11 im Lebenszyklus: liegt die Liquidation inzwischen VOR dem Stop?
    5. EINE Empfehlung, nach Dringlichkeit

DIE EMPFEHLUNGEN, dringendste zuerst:

    LIQUIDATION ERREICHT  der Kurs steht jenseits des geschaetzten
                          Liquidationspreises
    SCHLIESSEN            der Plan ist gefallen: Widerlegung, nachgezogener
                          Stop unterschritten, Signal laut Verfolgung am Stop
                          oder am Ziel
    HEBEL SENKEN          die Liquidation liegt VOR dem Stop - der Stop
                          schuetzt nicht mehr. Mit Nachschussbetrag.
    STOP NACHZIEHEN       Trailing ab +1 R (gemessen, `ausstiegsregel`)
    HALTEN                sonst - mit Hinweisen (Frist, Ziel nah, ab wann
                          die Liquidation den Stop erreicht)

⚠️ DIE FINANZIERUNG IST INFORMATION, KEIN AUSLOESER (Regel 2: Gebuehren
gehoeren nicht in die Bewertung). Sie steht in EUR in der Mail. Wirksam wird
sie nur ueber die Liquidation - dort ist sie keine Gebuehr, sondern
Mechanik: sie verschiebt den Preis, bei dem Bitpanda aufloest.

⚠️ HEBEL SENKEN IST KEINE BEWERTUNG, sondern RM-11 - dieselbe Regel, die den
Hebel bei der Eroeffnung deckelt (Regel 4 betrifft Einstiegssignale; das
hier ist der Schutz des Stops einer bestehenden Position).

ADVISORY-ONLY (P-7): es rechnet und meldet. Keine Handels-API, kein Auftrag.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from agent.ausstiegsrechnung import HALTEN, SCHLIESSEN, STOP_NACHZIEHEN

logger = logging.getLogger(__name__)

LIQUIDIERT = "LIQUIDATION ERREICHT"
HEBEL_SENKEN = "HEBEL SENKEN"
KURS_FEHLT = "KURS FEHLT"

# Dringlichkeit, nicht Wichtigkeit - dieselbe Ordnung wie in der
# Ausstiegsrechnung: was die Position beendet, steht vor dem, was sie aendert.
DRINGLICHKEIT = (LIQUIDIERT, SCHLIESSEN, HEBEL_SENKEN, KURS_FEHLT,
                 STOP_NACHZIEHEN, HALTEN)
# Was eine Mail ausloest. HALTEN nicht - eine taegliche "nichts zu tun"-Mail
# erzieht dazu, die Mail nicht mehr zu oeffnen (`ausstiegs_job`).
MELDEN = (LIQUIDIERT, SCHLIESSEN, HEBEL_SENKEN, KURS_FEHLT, STOP_NACHZIEHEN)

# WIE WEIT EIN SIGNAL VOR DER EROEFFNUNG LIEGEN DARF, um als ihr Plan zu gelten.
#
# ⚠️ GESETZT, NICHT GEMESSEN - die Rollen-Kette hat bis heute kein
# Hebelsignal geschrieben, es gibt keinen Fall, an dem sich das eichen liesse.
# Die Groessenordnung kommt aus den 188 echten Positionen am NB: gehalten im
# Median 0,3 Tage, 90 % unter 3,3 Tagen. Wer drei Tage nach dem Signal
# eroeffnet, handelt auf eine andere Lage. Die Zuordnung steht deshalb IN DER
# MAIL (Signalnummer und Datum), damit sie nachpruefbar ist.
KOPPEL_TAGE = 3.0
# Uhrenversatz zwischen Bitpanda-Zeitstempel und Signalzeit.
KOPPEL_NACHLAUF = timedelta(hours=1)
EROEFFNUNG = ("KAUFEN", "NACHKAUFEN", "EROEFFNEN")


def _zeit(wert) -> datetime | None:
    """ISO-Zeit als UTC-bewusstes datetime - `None`, wenn nicht lesbar."""
    if isinstance(wert, datetime):
        return wert if wert.tzinfo else wert.replace(tzinfo=timezone.utc)
    if wert is None:
        return None
    try:
        d = datetime.fromisoformat(str(wert).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def plan_zu(conn, symbol: str, richtung: str, eroeffnet_am) -> dict | None:
    """Das Hebelsignal, auf das hin die Position eroeffnet wurde - oder None.

    NUR `signals` MIT `instrument = 'hebel'` - die Tabelle der Rollen-Kette.
    ⚠️ KORREKTUR 11.09.2026 (H-5, Befund 2.379-instrument-korrektur): bis
    dahin schrieb die Kette das Instrument NIE; die Start-Migration setzte
    "spot" - diese Abfrage haette im Betrieb nichts gefunden. Jetzt schreibt
    `signal_abbildung` "hebel" fuer ein Hebelgeschaeft aus r(q) oder SHORT.
    `hebel_signals` (alte Kette) fuehrt ihre Zonen in USD und endet am
    10.08.; eine Position daraus ist vor dem Rollout eroeffnet und hat keinen
    Plan in EUR. Sie wird trotzdem gefuehrt - Liquidation und Finanzierung
    brauchen keinen Plan.

    DIE ZONEN KOMMEN AUS `backward_tracking._zonen_absolut` - dieselbe
    Kantenwahl wie bei jedem anderen Signal. Uebergeben werden ihr die
    EUR-Spalten unter den Namen, die sie liest: die Position ist in EUR
    denominiert, und eine Umrechnung waere eine zweite Fehlerquelle."""
    from agent.krypto.backward_tracking import _zonen_absolut

    auf = _zeit(eroeffnet_am)
    if auf is None:
        return None
    vorhanden = {r[1] for r in conn.execute("PRAGMA table_info(signals)")}
    noetig = ("instrument", "entry_eur_von", "stop_loss_eur_von",
              "take_profit_eur_von")
    if not all(c in vorhanden for c in noetig):
        return None
    optional = [c for c in (
        "entry_eur_bis", "stop_loss_eur_bis", "take_profit_eur_bis",
        "umgeworfen_preis_eur", "umgeworfen_bis", "umgeworfen_durch",
        "outcome_status", "outcome_max_realisiertes_crv", "strategie",
        "richtung", "hebel") if c in vorhanden]
    cur = conn.execute(
        "SELECT id, action, created_at, entry_eur_von, stop_loss_eur_von, "
        "take_profit_eur_von" + "".join(", " + c for c in optional)
        + " FROM signals WHERE UPPER(symbol) = UPPER(?) "
        "AND instrument = 'hebel' ORDER BY created_at DESC", (str(symbol),))
    namen = [d[0] for d in cur.description]
    ist_short = str(richtung or "").upper() == "SHORT"
    for werte in cur.fetchall():
        r = dict(zip(namen, werte))
        erzeugt = _zeit(r.get("created_at"))
        if erzeugt is None or erzeugt > auf + KOPPEL_NACHLAUF:
            continue
        if erzeugt < auf - timedelta(days=KOPPEL_TAGE):
            break                       # absteigend sortiert - aelter wird es nur
        aktion = str(r.get("action") or "").upper()
        if aktion not in EROEFFNUNG and not (ist_short and aktion not in
                                             ("HALTEN", "NICHTS_TUN")):
            continue
        if r.get("richtung") and str(r["richtung"]).upper() != (
                "SHORT" if ist_short else "LONG"):
            continue
        # DIE FRIST DES SIGNALS: nach ihr eroeffnet, galt seine Begruendung
        # schon nicht mehr.
        frist = str(r.get("umgeworfen_bis") or "")[:10]
        if frist and auf.date().isoformat() > frist:
            continue
        z = _zonen_absolut({
            "entry_usd_von": r.get("entry_eur_von"),
            "entry_usd_bis": r.get("entry_eur_bis"),
            "stop_loss_usd_von": r.get("stop_loss_eur_von"),
            "stop_loss_usd_bis": r.get("stop_loss_eur_bis"),
            "take_profit_usd_von": r.get("take_profit_eur_von"),
            "take_profit_usd_bis": r.get("take_profit_eur_bis")})
        if z is None or bool(z["ist_short"]) != ist_short:
            continue
        return {"signal_id": r.get("id"), "erzeugt_am": r.get("created_at"),
                "aktion": aktion, "einstieg": z["entry"], "stop": z["stop"],
                "ziel": z["ziel"], "ist_short": bool(z["ist_short"]),
                "umgeworfen_preis_eur": r.get("umgeworfen_preis_eur"),
                "umgeworfen_bis": r.get("umgeworfen_bis"),
                "umgeworfen_durch": r.get("umgeworfen_durch"),
                "outcome_status": r.get("outcome_status"),
                "mfe_r": r.get("outcome_max_realisiertes_crv"),
                "strategie": r.get("strategie") or "einstieg",
                "hebel_signal": r.get("hebel")}
    return None


def fuehre(*, symbol: str, richtung: str, eroeffnet_am, hebel: float | None,
           positionswert_eur: float | None, kreditbetrag_eur: float | None,
           eigenkapital_eur: float | None, positionsmenge: float | None,
           kurs_eur: float | None, jetzt=None, plan: dict | None = None,
           marge: float | None = None, kurs_stand: str | None = None,
           position_id=None) -> dict:
    """Die Fuehrung EINER Position - REIN, ohne DB, Uhr (ausser `jetzt`) oder
    Netz. Alle Betraege in EUR."""
    from agent import ausstiegsrechnung as AR
    from agent.krypto.backward_tracking import (
        OUTCOME_STOP_LOSS, OUTCOME_TAKE_PROFIT, _tagesgebuehr_rel)
    from agent.krypto.hebel_risk_gate import (
        estimate_liquidation_price, max_safe_hebel,
        tage_bis_liquidation_am_stop)

    if marge is None:
        from agent.entscheidungsrechnung import GRENZEN
        marge = GRENZEN["liquidations_marge"]
    jetzt = _zeit(jetzt) or datetime.now(timezone.utc)
    ist_short = str(richtung or "").upper() == "SHORT"
    vz = -1.0 if ist_short else 1.0
    t = {"position_id": position_id, "symbol": str(symbol),
         "richtung": "SHORT" if ist_short else "LONG",
         "kurs_eur": float(kurs_eur) if kurs_eur else None,
         "kurs_stand": kurs_stand, "plan": plan, "bewertung": None,
         "gruende": [], "hinweise": [], "empfehlung": HALTEN}

    auf = _zeit(eroeffnet_am)
    menge = float(positionsmenge or 0.0)
    pw = float(positionswert_eur or 0.0)
    if auf is None or menge <= 0 or pw <= 0:
        # OHNE MENGE KEIN EINSTAND - und ohne Einstand keine Liquidation.
        # Dieselbe Linie wie `_refresh_hebel_position_liquidation_prices`
        # (P-10): lieber keine Zahl als eine falsche.
        t["empfehlung"] = KURS_FEHLT if not kurs_eur else HALTEN
        t["hinweise"].append("Position unvollstaendig rekonstruiert (Menge, "
                             "Positionswert oder Eroeffnung fehlt) - "
                             "Liquidation und Ergebnis nicht berechenbar.")
        return t

    ek = float(eigenkapital_eur) if eigenkapital_eur else None
    kredit = (float(kreditbetrag_eur) if kreditbetrag_eur is not None
              else (pw - ek if ek else None))
    L = (float(hebel) if hebel and float(hebel) > 0
         else (pw / ek if ek else None))
    einstand = pw / menge
    tage = max(0.0, (jetzt - auf).total_seconds() / 86400.0)
    t.update(einstand_eur=einstand, menge=menge, hebel=L,
             positionswert_eur=pw, eigenkapital_eur=ek, kredit_eur=kredit,
             tage=tage, eroeffnet_am=auf.isoformat())

    # ---- FINANZIERUNG - Information, kein Ausloeser (Regel 2) ----------
    if kredit:
        t["finanzierung_bisher_eur"] = kredit * _tagesgebuehr_rel(tage)
        t["finanzierung_je_tag_eur"] = kredit * (
            _tagesgebuehr_rel(tage + 1.0) - _tagesgebuehr_rel(tage))

    # ---- LIQUIDATION mit den ECHTEN Tagen -----------------------------
    liq = None
    if L and L > 1.0:
        liq = estimate_liquidation_price(einstand, L, t["richtung"],
                                         days_held=tage,
                                         sicherheitsmarge_relativ=marge)
    t["liquidation_eur"] = liq

    kurs = t["kurs_eur"]
    if kurs:
        t["ergebnis_brutto_eur"] = vz * (kurs - einstand) * menge
        t["ergebnis_netto_eur"] = (t["ergebnis_brutto_eur"]
                                   - (t.get("finanzierung_bisher_eur") or 0.0))
        if liq:
            t["abstand_liquidation"] = vz * (kurs - liq) / kurs
    else:
        t["empfehlung"] = KURS_FEHLT
        t["gruende"].append("Fuer diese offene Hebelposition liegt kein Kurs "
                            "vor - Liquidationsabstand und Ergebnis sind "
                            "unbekannt. In der Bitpanda-App pruefen.")

    liquidiert = bool(kurs and liq and (kurs >= liq if ist_short
                                        else kurs <= liq))
    if liquidiert:
        t["empfehlung"] = LIQUIDIERT
        t["gruende"].append(
            "Der Kurs hat den geschaetzten Liquidationspreis erreicht. Die "
            "Position ist wahrscheinlich aufgeloest - in der Bitpanda-App "
            "pruefen. Die Schaetzung ist bewusst vorsichtig: sie meldet eher "
            "zu frueh als zu spaet.")

    if not plan:
        t["hinweise"].append(
            "Kein Hebelsignal der Rollen-Kette zugeordnet (dasselbe Symbol, "
            "dieselbe Richtung, bis %s Tage vor der Eroeffnung) - Stop, Ziel "
            "und Widerlegung sind unbekannt. Gefuehrt werden Liquidation und "
            "Finanzierung." % str(KOPPEL_TAGE).replace(".0", ""))
        return t

    # ---- DER PLAN - dieselbe Pruefung wie fuer jedes Signal -----------
    bew = AR.bewerte(
        einstieg=plan["einstieg"], stop_original=plan["stop"],
        kurs_aktuell=kurs, mfe_r=plan.get("mfe_r"),
        ist_short=bool(plan.get("ist_short")),
        umgeworfen_preis=plan.get("umgeworfen_preis_eur"),
        ziel=plan.get("ziel"), umgeworfen_bis=plan.get("umgeworfen_bis"),
        umgeworfen_durch=plan.get("umgeworfen_durch"),
        heute=jetzt.date(), strategie=plan.get("strategie") or "einstieg")
    t["bewertung"] = bew
    stop = float(plan["stop"])
    s = vz * (einstand - stop) / einstand
    t["stop_eur"] = stop
    t["stop_abstand_einstand"] = s

    # ---- RM-11 IM LEBENSZYKLUS -----------------------------------------
    #
    # ⚠️ GEPRUEFT WIRD GEGEN DEN URSPRUENGLICHEN STOP, nicht gegen einen
    # nachgezogenen. Welcher Stop bei der Boerse liegt, weiss das System nicht;
    # der urspruengliche ist der weiteste und damit der, vor den sich die
    # Liquidation zuerst schiebt.
    if liq:
        t["liquidation_vor_stop"] = (liq <= stop) if ist_short else (liq >= stop)
        if s > 0:
            t["tage_bis_liquidation_am_stop"] = tage_bis_liquidation_am_stop(
                s, L, marge, ist_short)
        if t["liquidation_vor_stop"] and s > 0:
            lmax = max_safe_hebel(100.0 * s, marge, ist_short=ist_short,
                                  tage=tage)
            t["hebel_sicher_heute"] = lmax
            t["nachschuss_eur"] = max(0.0, pw / lmax - (ek or pw / L))

    if t["empfehlung"] in (LIQUIDIERT, KURS_FEHLT):
        return t

    bew_empf = str((bew or {}).get("empfehlung") or "")
    status = plan.get("outcome_status")
    if bew_empf.startswith(SCHLIESSEN):
        t["empfehlung"] = SCHLIESSEN
        t["gruende"] += list(bew.get("gruende") or [])
    elif status in (OUTCOME_STOP_LOSS, OUTCOME_TAKE_PROFIT):
        t["empfehlung"] = SCHLIESSEN
        t["gruende"].append(
            "Die Signalverfolgung hat das Signal abgeschlossen (%s) - die "
            "Position ist aber noch offen. Der Plan ist damit zu Ende."
            % ("Stop erreicht" if status == OUTCOME_STOP_LOSS
               else "Ziel erreicht"))
    elif t.get("liquidation_vor_stop"):
        t["empfehlung"] = HEBEL_SENKEN
        tb = t.get("tage_bis_liquidation_am_stop")
        seit = ("schon bei der Eroeffnung" if tb is not None and tb < 0.05
                else "seit etwa Tag %s" % _de(tb or 0.0, 1))
        t["gruende"].append(
            "Die geschaetzte Liquidation liegt %s VOR dem Stop - faellt der "
            "Kurs, loest Bitpanda auf, BEVOR der Stop greift. Die "
            "Finanzierung schiebt sie jeden Tag weiter an den Einstieg." % seit)
    elif bew and bew.get("trailing_aktiv"):
        t["empfehlung"] = STOP_NACHZIEHEN
        t["gruende"] += list(bew.get("gruende") or [])
    else:
        if bew:
            t["gruende"] += list(bew.get("gruende") or [])
            if bew.get("frist_abgelaufen"):
                t["empfehlung"] = HALTEN + " · FRIST ABGELAUFEN"

    tb = t.get("tage_bis_liquidation_am_stop")
    if tb is not None and not t.get("liquidation_vor_stop"):
        t["hinweise"].append(
            "Die Liquidation liegt hinter dem Stop bis etwa Tag %s (heute Tag "
            "%s) - danach schiebt die Finanzierung sie davor."
            % (_de(tb, 1), _de(tage, 1)))
    return t


def _de(wert: float, stellen: int = 2, vorzeichen: bool = False) -> str:
    from agent.schreibweise import de

    return de(wert, stellen, vorzeichen)


def _rang(t: dict) -> tuple:
    empf = str(t.get("empfehlung") or HALTEN).split(" · ")[0]
    stufe = DRINGLICHKEIT.index(empf) if empf in DRINGLICHKEIT else len(DRINGLICHKEIT)
    return (stufe, -(t.get("positionswert_eur") or 0.0))


def lade(conn, symbole=None, jetzt=None, marge: float | None = None) -> list:
    """Alle OFFENEN Hebelpositionen, gefuehrt - dringendste zuerst.

    ⚠️ `conn` wird uebergeben, nie hier geoeffnet (dieselbe Regel wie
    `positionsfuehrung.lade`)."""
    from agent import positionsfuehrung as PF
    from database import db as DBM

    filt = {str(s).upper() for s in (symbole or ())}
    aus = []
    for p in DBM.get_open_hebel_positions(conn):
        if filt and str(p.symbol).upper() not in filt:
            continue
        kurs, stand = PF.kurs_mit_stand(conn, p.symbol)
        plan = None
        try:
            plan = plan_zu(conn, p.symbol, p.richtung, p.eroeffnet_am)
        except Exception as exc:                             # noqa: BLE001
            # OHNE PLAN IST DIE FUEHRUNG AERMER, NICHT FALSCH - die
            # Liquidation braucht ihn nicht. Aber der Ausfall steht im Log.
            logger.warning("Plan zu Hebelposition %s nicht lesbar: %s",
                           p.symbol, exc)
        aus.append(fuehre(
            symbol=p.symbol, richtung=p.richtung,
            eroeffnet_am=p.eroeffnet_am, hebel=p.hebel_effektiv,
            positionswert_eur=p.positionswert_eur,
            kreditbetrag_eur=p.kreditbetrag_eur,
            eigenkapital_eur=p.eigenkapital_eur,
            positionsmenge=p.positionsmenge, kurs_eur=kurs, kurs_stand=stand,
            jetzt=jetzt, plan=plan, marge=marge, position_id=p.id))
    return sorted(aus, key=_rang)


def zeilen(t: dict) -> list:
    """Die Position als Text - absolute Zahlen vor relativen, alles in EUR."""
    from agent.signal_mail import eur, preis

    kopf = "%s - Hebel %sx %s" % (t["symbol"], _de(t.get("hebel") or 0.0, 1),
                                  t["richtung"])
    if t.get("tage") is not None:
        kopf += ", seit %s Tagen" % _de(t["tage"], 1)
    z = [kopf + " · " + str(t.get("empfehlung"))]
    if t.get("einstand_eur") is None:
        return z + ["   " + h for h in t.get("hinweise") or []]
    z.append("   Position     %s EUR · Eigenkapital %s EUR · Kredit %s EUR"
             % (eur(t["positionswert_eur"], 2),
                eur(t["eigenkapital_eur"], 2) if t.get("eigenkapital_eur") else "?",
                eur(t["kredit_eur"], 2) if t.get("kredit_eur") is not None else "?"))
    kurs_txt = ("Kurs %s EUR" % preis(t["kurs_eur"])) if t.get("kurs_eur") else "Kurs unbekannt"
    if t.get("kurs_stand"):
        kurs_txt += " (Stand %s)" % str(t["kurs_stand"])[:16].replace("T", " ")
    z.append("   Einstand     %s EUR · %s" % (preis(t["einstand_eur"]), kurs_txt))
    if t.get("ergebnis_brutto_eur") is not None:
        # `eur()` kennt kein Vorzeichen - es wird davorgesetzt, der Betrag
        # bleibt in der einen Schreibweise (Tausenderpunkt, Dezimalkomma).
        _b, _n = t["ergebnis_brutto_eur"], t["ergebnis_netto_eur"]
        z.append("   Ergebnis     %s%s EUR vor Finanzierung · netto %s%s EUR"
                 % ("+" if _b >= 0 else "-", eur(abs(_b), 2),
                    "+" if _n >= 0 else "-", eur(abs(_n), 2)))
    if t.get("finanzierung_bisher_eur") is not None:
        z.append("   Finanzierung bisher %s EUR · heute %s EUR je Tag "
                 "(Information, kein Ausloeser)"
                 % (eur(t["finanzierung_bisher_eur"], 2),
                    eur(t["finanzierung_je_tag_eur"], 2)))
    if t.get("liquidation_eur"):
        teil = "   Liquidation  etwa %s EUR" % preis(t["liquidation_eur"])
        _ab = t.get("abstand_liquidation")
        # ⚠️ KEIN NEGATIVER ABSTAND IM TEXT - der erste Kettenlauf schrieb
        # "- -3,4 % vom Kurs". Jenseits der Liquidation ist das kein Abstand
        # mehr, sondern ein Ereignis.
        if _ab is not None and _ab >= 0:
            teil += " - %s %% %s dem Kurs" % (
                _de(100.0 * _ab, 1),
                "ueber" if t["richtung"] == "SHORT" else "unter")
        elif _ab is not None:
            teil += " - der Kurs steht bereits %s %% jenseits davon" % _de(
                -100.0 * _ab, 1)
        z.append(teil)
    p = t.get("plan")
    if p:
        z.append("   Plan         Signal %s vom %s: Stop %s EUR · Ziel %s EUR"
                 % (p.get("signal_id"), str(p.get("erzeugt_am") or "")[:10],
                    preis(p["stop"]), preis(p["ziel"])))
        if t.get("liquidation_vor_stop"):
            z.append("   !! Die Liquidation liegt VOR dem Stop")
        if t.get("nachschuss_eur") is not None:
            z.append("   Hebel heute hoechstens %sx - dafuer etwa %s EUR "
                     "Eigenkapital nachschiessen oder entsprechend verkaufen"
                     % (_de(t["hebel_sicher_heute"], 2),
                        eur(t["nachschuss_eur"], 2)))
        stop_neu = (t.get("bewertung") or {}).get("stop_empfohlen")
        if t.get("empfehlung") == STOP_NACHZIEHEN and stop_neu:
            z.append("   Stop nachziehen auf %s EUR" % preis(stop_neu))
    for g in t.get("gruende") or []:
        z.append("   Grund: " + g)
    for h in t.get("hinweise") or []:
        z.append("   Hinweis: " + h)
    return z


def schluessel(t: dict, tag: str) -> str:
    """Wann eine Meldung NEU ist: je Position, Empfehlung und Tag - bei
    STOP NACHZIEHEN zusaetzlich je Marke.

    Der Lauf kommt alle 15 Minuten. Ohne diese Sperre stuende dieselbe
    Warnung 96-mal am Tag im Postfach (83,6 % der Mails waren Wiederholung,
    Befund 29.08.). Mit ihr kommt jeder Zustand einmal je Tag - und eine
    neue Stop-Marke sofort."""
    stop_neu = (t.get("bewertung") or {}).get("stop_empfohlen")
    zusatz = ("%.6g" % stop_neu if t.get("empfehlung") == STOP_NACHZIEHEN
              and stop_neu else "")
    return "hebelfuehrung:%s:%s:%s:%s" % (
        t.get("position_id") or t.get("symbol"), t.get("empfehlung"), zusatz,
        tag)


def neue_meldungen(conn, trades: list, tag: str | None = None) -> list:
    """Die Positionen, deren Zustand heute noch nicht gemeldet wurde."""
    from database import db as DBM

    tag = tag or datetime.now(timezone.utc).date().isoformat()
    return [t for t in trades
            if str(t.get("empfehlung") or "").split(" · ")[0] in MELDEN
            and DBM.letzter_joblauf(conn, schluessel(t, tag)) is None]


def vermerke(conn, trades: list, tag: str | None = None) -> None:
    """Nach dem Versand: diese Zustaende sind fuer heute gemeldet."""
    from database import db as DBM

    tag = tag or datetime.now(timezone.utc).date().isoformat()
    for t in trades:
        DBM.merke_joblauf(conn, schluessel(t, tag))


def sammel_mail(trades: list, zeitpunkt: str | None = None) -> tuple | None:
    """EINE Mail fuer alle meldepflichtigen Hebelpositionen - oder None."""
    posten = sorted([t for t in trades
                     if str(t.get("empfehlung") or "").split(" · ")[0] in MELDEN],
                    key=_rang)
    if not posten:
        return None
    erste = posten[0]
    betreff = ("Hebelfuehrung: %s %s" % (erste["empfehlung"], erste["symbol"])
               + (" (+%d weitere)" % (len(posten) - 1) if len(posten) > 1 else ""))
    text = ["HEBELFUEHRUNG - %d offene Position%s mit Handlungsbedarf"
            % (len(posten), "en" if len(posten) > 1 else "")]
    if zeitpunkt:
        text.append(str(zeitpunkt))
    text += ["",
             "Ausfuehrung manuell ueber die Bitpanda-App - dieses System "
             "handelt nicht.",
             "Die Liquidation ist eine vorsichtige Schaetzung (Bitpanda "
             "veroeffentlicht keine Formel).", ""]
    for t in posten:
        text += zeilen(t) + [""]
    return betreff, "\n".join(text)
