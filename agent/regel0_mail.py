"""Mails der REGEL0 (Schritt 7, S7-4, E-46; Nutzer 03.10.2026: *"Ja D1 bis D4 wie vorgeschlagen"*).

Drei Mails, alle aus der Ablage ``data/regel0_signale.db`` (agent/regel0_ablage.py):

    SIGNAL       je neuem Signal mit eingeschaltetem Hebel-Schalter und Stufe > 0 - Asset, Einstieg und Ausstieg (wie gemessen),
                 Hebelstufe, Einsatz (regel0_betrieb.yaml), Vermerke. Die Stufe ist zuerst VORLAEUFIG (ATR der Signalstunde, D1)
    KORREKTUR    nur wenn die ENDGUELTIGE Stufe (eine Stunde spaeter) von der gemailten abweicht (B-9: rund 1,6 %)
    ERINNERUNG   wenn die 24 h um sind: Ausstieg faellig (E-43 Punkt 2) - seit 04.10.2026 NUR bei einer OFFENEN Hebelposition
                 in diesem Asset (Nutzer: *Ausstiegsmails von nicht offenen Hebelpositionen* sofort aendern). Ist der Positionsstand
                 unbekannt (Bitpanda-Abgleich veraltet oder nie gelaufen), geht sie MIT Vermerk raus - lieber eine Mail zu viel als
                 eine fehlende Ausstiegsmeldung bei echtem Geld

D2: die Stufen, die Bitpanda je Asset anbietet, sind noch nicht als Daten da - die Mail sagt das. D3: kein LLM-Kommentar in
dieser Fassung. D4: bis ``testwoche_bis`` (regel0_betrieb.yaml) tragen Betreff und Text den Vermerk TESTWOCHE.

⚠️ Eine Mail gilt erst als versandt, wenn der Versand True meldet - sonst wird sie in der naechsten Stunde wieder versucht.
⚠️ Kein Netz und keine Produktion hier: das Senden kommt von aussen (der Stundenjob gibt ``_sende_hinweismail`` mit).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import agent.regel0_ablage as AB
import agent.regel0_groesse as G

NICHT_AELTER_H = 3        # ein Signal, dessen Einstieg laenger als so viele Stunden vorbei ist, wird nicht mehr gemailt
ABGLEICH_GRENZE = 0.05    # S7-5b: Bitpanda gegen Binance zum selben Moment - gemessen 03.10.: gleiche Coins -0,1 %, Kollisionen +25 bis +428 %
NL = chr(10)
ERINNERUNG_BIS_H = 6      # eine Erinnerung, deren Ausstieg laenger vorbei ist, entfaellt (z. B. nach langem Stillstand)


def _t(txt: str) -> datetime:
    return datetime.strptime(txt, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)


def _zeit(dt: datetime) -> str:
    """'03.10. 14:00 UTC (16:00 Ortszeit)' - die Ortszeit aus der Uhr des Geraets."""
    return "%s UTC (%s Ortszeit)" % (dt.strftime("%d.%m. %H:%M"), dt.astimezone().strftime("%H:%M"))


def _pct(x) -> str:
    return "-" if x is None else ("%.1f %%" % (100.0 * x)).replace(".", ",")


def _testwoche(werte: dict, jetzt: datetime) -> str:
    bis = werte.get("testwoche_bis") or ""
    return bis if (bis and jetzt.strftime("%Y-%m-%d") <= bis) else ""


def _vermerke(r: dict) -> list:
    v = []
    if r.get("kurs_markt") == "futures":
        v.append("Kurs aus Futures (Binance fuehrt dieses Asset nicht als Spot)")
    if r.get("zusatz"):
        v.append("bewertet, nicht trainiert (Asset ausserhalb der Messbasis, E-40)")
    if r.get("btc"):
        v.append("BTC: nicht nachgewiesen (rund 30 Signale je Jahr), unschaedlich (E-37)")
    return v


def kurse_live() -> tuple:
    """-> ({Bitpanda-Symbol: USD}, {Binance-Paar: Kurs}) - oeffentliche Ticker, zum selben Moment. Wirft bei Netzfehlern."""
    import requests
    bp = requests.get("https://api.bitpanda.com/v1/ticker", timeout=20).json()
    bpu = {k: float(v["USD"]) for k, v in bp.items() if isinstance(v, dict) and v.get("USD")}
    bn = {x["symbol"]: float(x["price"]) for x in requests.get("https://api.binance.com/api/v3/ticker/price", timeout=20).json()}
    for x in requests.get("https://fapi.binance.com/fapi/v1/ticker/price", timeout=20).json():
        bn.setdefault(x["symbol"], float(x["price"]))
    return bpu, bn


def abgleich(r: dict, bpu: dict | None, bn: dict | None) -> tuple:
    """-> (ok, text): gehoert der Binance-Kurs zum Bitpanda-Coin? Fehlt ein Kurs, ist das KEIN Fehler, sondern *nicht gegengeprueft*."""
    if bpu is None or bn is None:
        return True, "Kurs nicht gegengeprueft (Ticker nicht erreichbar)"
    b, n = bpu.get(r.get("bitpanda") or ""), bn.get(r.get("paar") or "")
    if not b or not n:
        return True, "Kurs nicht gegengeprueft (%s)" % ("kein Bitpanda-Kurs" if not b else "kein Binance-Kurs %s" % r.get("paar"))
    d = n / (b * float(r.get("faktor") or 1.0)) - 1.0
    txt = "Bitpanda %.6g USD, Binance %s %.6g (Abweichung %+.1f %%)" % (b, r.get("paar"), n, 100 * d)
    return abs(d) <= ABGLEICH_GRENZE, txt.replace(".", ",", 0)


def signal_mail(r: dict, stufe: int, vorlaeufig: bool, groesse, werte: dict, jetzt: datetime) -> tuple:
    tw = _testwoche(werte, jetzt)
    ein = _t(r["einstieg"]) + timedelta(hours=1)          # Schlusskurs der Einstiegsstunde
    aus = _t(r["ausstieg"]) + timedelta(hours=1)
    sig = _t(r["signalstunde"])
    betreff = "%sREGEL0 Hebel LONG %s %dx - Einstieg %s" % ("[TESTWOCHE] " if tw else "", r["bitpanda"] or r["symbol"], stufe,
                                                            ein.astimezone().strftime("%d.%m. %H:%M"))
    z = ["REGEL0.1 - HEBEL-SIGNAL LONG%s" % ("   ·   TESTWOCHE bis %s" % tw if tw else ""), "",
         "Asset:      %s%s" % (r["bitpanda"] or r["symbol"], "" if (r["bitpanda"] or r["symbol"]) == r["symbol"] else " (Binance %s)" % r["symbol"]),
         "Signal:     Stunde ab %s, abgeschlossen um %s" % (_zeit(sig), _zeit(sig + timedelta(hours=1))),
         "",
         "EINSTIEG    zum Schlusskurs der Folgestunde: %s" % _zeit(ein),
         "            (so ist die REGEL0 gemessen - wer frueher oder spaeter einsteigt, handelt etwas anderes)",
         "AUSSTIEG    24 Stunden danach: %s - ohne Stop, ohne Ziel (REGEL0)" % _zeit(aus),
         "",
         "HEBEL       %dx%s" % (stufe, "  (VORLAEUFIG aus der ATR der Signalstunde - die endgueltige Stufe steht eine Stunde spaeter fest;"
                                     " weicht sie ab, kommt eine kurze Korrektur)" if vorlaeufig else "  (endgueltig)"),
         "            geschaetzte Liquidationsgefahr binnen 24 h: 2x %s · 3x %s · 5x %s (Grenze 2 %%)" % (
             _pct(r.get("p2")), _pct(r.get("p3")), _pct(r.get("p5"))),
         "            ⚠️ Pruefe, welche Hebelstufen Bitpanda fuer dieses Asset anbietet - die Stufen je Asset sind noch nicht als Daten"
         " hinterlegt (D2). Bietet Bitpanda weniger an, die naechst kleinere nehmen.",
         "EINSATZ     %s EUR  (Positionswert %s EUR / %dx, Startwerte in regel0_betrieb.yaml)" % (
             ("%.0f" % groesse.einsatz_eur), ("%.0f" % groesse.positionswert_eur), stufe)]
    if groesse.vermerk:
        z.append("            %s" % groesse.vermerk)
    if r.get("kurs"):
        z.append("Kurs zur Signalstunde: %s USDT (Binance %s, nur Orientierung - Bitpanda handelt in EUR)" % (
            ("%.6g" % r["kurs"]), "Futures" if r.get("kurs_markt") == "futures" else "Spot"))
    vm = _vermerke(r)
    if r.get("abgleich"):
        vm.append("Zuordnung: " + r["abgleich"])
    if vm:
        z += ["", "Vermerke:"] + ["  - " + x for x in vm]
    z += ["", "Regel: REGEL0.1 (rsi-Ersteintritt, v-dach %s, Schwelle +0,035, Ruhe 48 h; Hebel aus dem ATR-Modell, Grenze 2 %%)" % (
              ("%+.4f" % r["vh"]).replace(".", ",") if r.get("vh") is not None else "-"),
          "Das ist eine Auskunft deines Systems, kein Auftrag - du entscheidest."]
    return betreff, "\n".join(z)


def korrektur_mail(r: dict, alt: int, neu: int, werte: dict, jetzt: datetime) -> tuple:
    tw = _testwoche(werte, jetzt)
    ein = _t(r["einstieg"]) + timedelta(hours=1)
    name = r["bitpanda"] or r["symbol"]
    if neu > 0:
        g = G.rechne(neu, 0, werte)
        kern = "Endgueltige Hebelstufe %dx statt %dx - Einsatz dann %.0f EUR (Positionswert %.0f EUR)." % (neu, alt, g.einsatz_eur, g.positionswert_eur)
    else:
        kern = "Endgueltig KEIN HANDEL: mit der ATR der Einstiegsstunde liegt keine Stufe unter der Liquidationsgrenze 2 %."
    betreff = "%sREGEL0 KORREKTUR %s: %s" % ("[TESTWOCHE] " if tw else "", name, ("%dx statt %dx" % (neu, alt)) if neu > 0 else "kein Handel")
    text = "\n".join(["REGEL0.1 - KORREKTUR zum Signal %s (Einstieg %s)" % (name, _zeit(ein)), "", kern, "",
                      "Grund: die vorlaeufige Stufe kam aus der ATR der Signalstunde, die endgueltige aus der ATR der Einstiegsstunde"
                      " - so wie die REGEL0 gemessen ist (B-9)."])
    return betreff, text


def position_stand(r: dict, befund: dict | None) -> tuple:
    """-> (offen, vermerk) fuer die ERINNERUNG: True (offene LONG-Position in diesem Asset), False (Abgleich frisch, keine
    offene Position - die Erinnerung entfaellt), None (unbekannt - sie geht mit Vermerk raus).

    ``befund``: {"stand": datetime|None, "veraltet": bool, "stunden": float|None, "positionen": [(symbol, richtung, eroeffnet_am)]}
    - Positionen mit status 'offen' aus ``hebel_positions``, Stand aus dem Bitpanda-Abgleich (agent/hebel_abgleich.py).
    ⚠️ Bekannte Grenze (2.679): der Importer wertet eine Teilschliessung als Vollschluss - dann gilt die Restposition als zu."""
    if not befund:
        return None, "Positionsstand nicht lesbar - Erinnerung vorsichtshalber verschickt"
    if befund.get("stand") is None:
        return None, "Positionsstand unbekannt (Bitpanda-Abgleich noch nie erfolgreich) - Erinnerung vorsichtshalber verschickt"
    if befund.get("veraltet"):
        return None, ("Positionsstand unbekannt (Bitpanda-Abgleich seit %.1f h nicht erfolgreich) - Erinnerung vorsichtshalber verschickt"
                      % (befund.get("stunden") or 0.0))
    name = (r.get("bitpanda") or r.get("symbol") or "").upper()
    pos = [p for p in (befund.get("positionen") or []) if str(p[0]).upper() == name and str(p[1] or "LONG").upper() == "LONG"]
    if not pos:
        return False, "keine offene Hebelposition %s LONG bei Bitpanda (Abgleich %s UTC)" % (
            name, befund["stand"].astimezone(timezone.utc).strftime("%d.%m. %H:%M"))
    return True, "offene Hebelposition %s LONG seit %s" % (name, ", ".join(str(p[2])[:16].replace("T", " ") for p in pos))


def erinnerung_mail(r: dict, stufe: int, werte: dict, jetzt: datetime) -> tuple:
    tw = _testwoche(werte, jetzt)
    aus = _t(r["ausstieg"]) + timedelta(hours=1)
    name = r["bitpanda"] or r["symbol"]
    betreff = "%sREGEL0 AUSSTIEG faellig: %s %dx" % ("[TESTWOCHE] " if tw else "", name, stufe)
    text = "\n".join(["REGEL0.1 - AUSSTIEG FAELLIG", "",
                      "%s, Hebel %dx, Einstieg %s" % (name, stufe, _zeit(_t(r["einstieg"]) + timedelta(hours=1))),
                      "Die 24 Stunden sind um: Ausstieg zum Schlusskurs %s." % _zeit(aus), "",
                      "Die Fuehrung offener Positionen kommt spaeter (O13)."])
    return betreff, text


def versende(ordner_ablage: str, senden, jetzt: datetime | None = None, werte: dict | None = None, kurse=None, melden=None,
             bild=None, pruefung=None, position=None) -> dict:
    """Prueft die Ablage und verschickt faellige Mails. ``senden(betreff, text) -> bool``. Vermerkt nur echte Versaende.

    S7-5b: vor jeder SIGNALmail der Preisabgleich (``kurse() -> (bitpanda_usd, binance)``, Vorgabe die oeffentlichen Ticker).
    Weicht der Kurs mehr als 5 % ab, gehoert der Binance-Kurs zu einem ANDEREN Coin: keine Mail, Vermerk in der Ablage,
    ``melden(text)`` einmal je Signal. Ist der Ticker nicht erreichbar, geht die Mail mit Vermerk raus (F-2).

    E-50 N-f (03.10.2026): ``bild(r) -> PNG | None`` haengt das Chart an die SIGNALmail (``senden(betreff, text, bilder)``).
    ``pruefung(r) -> [Zeilen]`` haengt den Block der LLM-Rollen an (E-52). Beides darf scheitern, ohne die Mail aufzuhalten (P-8).

    04.10.2026: ``position() -> befund`` (siehe ``position_stand``) - die ERINNERUNG geht nur bei offener Position; ohne
    ``position`` bleibt es beim alten Verhalten (jede Erinnerung)."""
    jetzt = jetzt or datetime.now(timezone.utc)
    werte = werte if werte is not None else G.lade()
    jt = jetzt.strftime("%Y-%m-%d %H:%M")
    grenze_alt = (jetzt - timedelta(hours=NICHT_AELTER_H)).strftime("%Y-%m-%d %H:%M")
    grenze_erin = (jetzt - timedelta(hours=ERINNERUNG_BIS_H + 1)).strftime("%Y-%m-%d %H:%M")
    zaehl = dict(signal=0, korrektur=0, erinnerung=0, fehlgeschlagen=0, gesperrt=0, entfallen=0)
    _kurse = {}

    def _live():
        if "v" not in _kurse:
            try:
                _kurse["v"] = (kurse or kurse_live)()
            except Exception:                                   # noqa: BLE001
                _kurse["v"] = (None, None)
        return _kurse["v"]
    c = AB.oeffne(ordner_ablage)
    c.row_factory = __import__("sqlite3").Row
    try:
        # 1  SIGNAL: Schalter an, Stufe > 0, noch nicht gemailt, Einstieg nicht laenger als NICHT_AELTER_H vorbei
        for r in c.execute("SELECT * FROM signal WHERE hebel_schalter=1 AND mail_signal_am IS NULL AND mail_gesperrt_am IS NULL "
                           "AND COALESCE(stufe, stufe_vorlaeufig) > 0 AND einstieg >= ? ORDER BY signalstunde", (grenze_alt,)).fetchall():
            r = dict(r)
            ok, txt = abgleich(r, *_live())
            r["abgleich"] = txt
            if not ok:
                c.execute("UPDATE signal SET mail_gesperrt_am=?, abgleich=? WHERE symbol=? AND signalstunde=?", (jt, txt, r["symbol"], r["signalstunde"]))
                c.commit(); zaehl["gesperrt"] += 1
                if melden:
                    melden("REGEL0-Signal %s (Binance %s) NICHT gemailt - Zuordnung zweifelhaft: %s. Pruefen: Basisinfos/symbol_zuordnung.csv "
                           "(gesperrt, wenn Bitpanda einen anderen Coin unter dem Kuerzel fuehrt)" % (r.get("bitpanda"), r["symbol"], txt))
                continue
            stufe = int(r["stufe"] if r["stufe"] is not None else r["stufe_vorlaeufig"])
            offen = c.execute("SELECT COUNT(*) FROM signal WHERE mail_signal_am IS NOT NULL AND COALESCE(stufe, mail_signal_stufe) > 0 "
                              "AND ausstieg > ? AND NOT (symbol=? AND signalstunde=?)", (jt, r["symbol"], r["signalstunde"])).fetchone()[0]
            g = G.rechne(stufe, int(offen), werte)
            b, t = signal_mail(r, stufe, r["stufe"] is None, g, werte, jetzt)
            if pruefung is not None:
                try:
                    _z = pruefung(r) or []
                except Exception as exc:                        # noqa: BLE001
                    _z = ["PRUEFUNG DURCH DIE ROLLEN: nicht verfuegbar (%s)" % type(exc).__name__]
                if _z:
                    t = t + NL + NL + NL.join(_z)
            bilder = None
            if bild is not None:
                try:
                    _png = bild(r)
                except Exception:                               # noqa: BLE001
                    _png = None
                if _png:
                    bilder = [{"png": _png, "alt": "REGEL0 %s" % (r.get("bitpanda") or r["symbol"]),
                               "filename": "regel0_%s_%s.png" % (r["symbol"], r["signalstunde"][:13].replace(" ", "_").replace(":", ""))}]
            if (senden(b, t, bilder) if bilder else senden(b, t)):
                c.execute("UPDATE signal SET mail_signal_am=?, mail_signal_stufe=?, abgleich=? WHERE symbol=? AND signalstunde=?",
                          (jt, stufe, txt, r["symbol"], r["signalstunde"]))
                c.commit(); zaehl["signal"] += 1
            else:
                zaehl["fehlgeschlagen"] += 1
        # 2  KORREKTUR: die endgueltige Stufe weicht von der gemailten ab
        for r in c.execute("SELECT * FROM signal WHERE mail_signal_am IS NOT NULL AND stufe IS NOT NULL AND mail_korrektur_am IS NULL "
                           "AND stufe != mail_signal_stufe").fetchall():
            r = dict(r)
            b, t = korrektur_mail(r, int(r["mail_signal_stufe"]), int(r["stufe"]), werte, jetzt)
            if senden(b, t):
                c.execute("UPDATE signal SET mail_korrektur_am=? WHERE symbol=? AND signalstunde=?", (jt, r["symbol"], r["signalstunde"]))
                c.commit(); zaehl["korrektur"] += 1
            else:
                zaehl["fehlgeschlagen"] += 1
        # 3  ERINNERUNG: 24 h um (Schluss der Ausstiegsstunde erreicht), Handel nicht auf 0 korrigiert
        _bef = {}
        for r in c.execute("SELECT * FROM signal WHERE mail_signal_am IS NOT NULL AND mail_erinnerung_am IS NULL "
                           "AND erinnerung_entfallen_am IS NULL "
                           "AND COALESCE(stufe, mail_signal_stufe) > 0 AND ausstieg <= ? AND ausstieg >= ?",
                           ((jetzt - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"), grenze_erin)).fetchall():
            r = dict(r)
            b, t = erinnerung_mail(r, int(r["stufe"] if r["stufe"] is not None else r["mail_signal_stufe"]), werte, jetzt)
            if position is not None:
                if "v" not in _bef:                              # EIN Positionsstand je Lauf
                    try:
                        _bef["v"] = position()
                    except Exception:                           # noqa: BLE001
                        _bef["v"] = None
                offen, vm = position_stand(r, _bef["v"])
                if offen is False:
                    c.execute("UPDATE signal SET erinnerung_entfallen_am=?, erinnerung_grund=? WHERE symbol=? AND signalstunde=?",
                              (jt, vm, r["symbol"], r["signalstunde"]))
                    c.commit(); zaehl["entfallen"] += 1
                    continue
                t = t + NL + NL + "Position: " + vm
            if senden(b, t):
                c.execute("UPDATE signal SET mail_erinnerung_am=? WHERE symbol=? AND signalstunde=?", (jt, r["symbol"], r["signalstunde"]))
                c.commit(); zaehl["erinnerung"] += 1
            else:
                zaehl["fehlgeschlagen"] += 1
    finally:
        c.close()
    return zaehl
