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
import agent.regel0_chart as CH
import agent.regel0_groesse as G

NICHT_AELTER_H = 3        # ein Signal, dessen Einstieg laenger als so viele Stunden vorbei ist, wird nicht mehr gemailt
ABGLEICH_GRENZE = 0.05    # S7-5b: Bitpanda gegen Binance zum selben Moment - gemessen 03.10.: gleiche Coins -0,1 %, Kollisionen +25 bis +428 %
NL = chr(10)
ERINNERUNG_BIS_H = 6      # eine Erinnerung, deren Ausstieg laenger vorbei ist, entfaellt (z. B. nach langem Stillstand)
# N-1 (E-57): eine Signalmail entfaellt erst, wenn der gemessene Einstieg (Schluss der Einstiegsstunde) LAENGER als dies vorbei ist.
# Die Grenze folgt aus dem Takt, sie ist keine Wahl: ein regulaerer Lauf (vorlaeufig 0 -> endgueltig > 0, D1/E-46, oder eine aufgefangene
# Stunde) mailt hoechstens etwa 10 min nach dem Einstieg; ein nach einem Ausfall nachgeholtes Signal liegt mindestens 1 h dahinter.
VERPASST_NACH = timedelta(hours=1)


def _t(txt: str) -> datetime:
    return datetime.strptime(txt, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)


def _zeit(dt: datetime) -> str:
    """'03.10. 14:00 UTC (16:00 Ortszeit)' - die Ortszeit aus der Uhr des Geraets."""
    return "%s UTC (%s Ortszeit)" % (dt.strftime("%d.%m. %H:%M"), dt.astimezone().strftime("%H:%M"))


def _pct(x) -> str:
    return "-" if x is None else ("%.1f %%" % (100.0 * x)).replace(".", ",")


def _testwoche(werte: dict, jetzt: datetime) -> str:
    """Vermerk TESTWOCHE oder "". S-2 (E-57, 04.10.2026): sie endet NUR mit ``testwoche_freigegeben: true`` (Nutzer-Ja) -
    nach dem geplanten Tag bleibt der Vermerk stehen, mit *Freigabe ausstehend*. Leeres ``testwoche_bis`` = keine Testwoche."""
    bis = werte.get("testwoche_bis") or ""
    if not bis or werte.get("testwoche_freigegeben"):
        return ""
    return bis if jetzt.strftime("%Y-%m-%d") <= bis else "%s - Freigabe ausstehend" % bis


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
    """-> ({Bitpanda-Symbol: USD}, {Binance-Paar: Kurs}, {Bitpanda-Symbol: EUR}) - oeffentliche Ticker, zum selben Moment.
    Wirft bei Netzfehlern. Der EUR-Kurs (04.10.2026) ist der Kurs, zu dem bei Bitpanda gehandelt wird."""
    import requests
    bp = requests.get("https://api.bitpanda.com/v1/ticker", timeout=20).json()
    bpu = {k: float(v["USD"]) for k, v in bp.items() if isinstance(v, dict) and v.get("USD")}
    bpe = {k: float(v["EUR"]) for k, v in bp.items() if isinstance(v, dict) and v.get("EUR")}
    bn = {x["symbol"]: float(x["price"]) for x in requests.get("https://api.binance.com/api/v3/ticker/price", timeout=20).json()}
    for x in requests.get("https://fapi.binance.com/fapi/v1/ticker/price", timeout=20).json():
        bn.setdefault(x["symbol"], float(x["price"]))
    return bpu, bn, bpe


def abgleich(r: dict, bpu: dict | None, bn: dict | None) -> tuple:
    """-> (ok, text): gehoert der Binance-Kurs zum Bitpanda-Coin? Fehlt ein Kurs, ist das KEIN Fehler, sondern *nicht gegengeprueft*."""
    if bpu is None or bn is None:
        return True, "Kurs nicht gegengeprueft (Ticker nicht erreichbar)"
    b, n = bpu.get(r.get("bitpanda") or ""), bn.get(r.get("paar") or "")
    if not b or not n:
        return True, "Kurs nicht gegengeprueft (%s)" % ("kein Bitpanda-Kurs" if not b else "kein Binance-Kurs %s" % r.get("paar"))
    d = n / (b * float(r.get("faktor") or 1.0)) - 1.0
    # ⚠️ 04.10.2026: hier stand `txt.replace(".", ",", 0)` - die 0 ersetzt NICHTS, die Mail zeigte *261.168 USD*, *+0.0 %*
    txt = "Bitpanda %s USD, Binance %s %s (Abweichung %s %%)" % (CH._zahl(b), r.get("paar"), CH._zahl(n),
                                                             ("%+.1f" % (100 * d)).replace(".", ","))
    return abs(d) <= ABGLEICH_GRENZE, txt


_WTAG = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")


def _wann(dt: datetime, jetzt: datetime) -> str:
    """O25 (04.10.2026): Ortszeit zuerst und in Worten - 'heute 14:00', 'morgen 14:00', sonst 'Di 06.10. 14:00'."""
    o, j = dt.astimezone(), jetzt.astimezone()
    tage = (o.date() - j.date()).days
    tag = {0: "heute", 1: "morgen", -1: "gestern"}.get(tage, "%s %s" % (_WTAG[o.weekday()], o.strftime("%d.%m.")))
    return "%s %s" % (tag, o.strftime("%H:%M"))


def _prozent(x: float) -> str:
    return ("%+.1f %%" % (100.0 * x)).replace(".", ",")


def _signal_teile(r: dict, stufe: int, vorlaeufig: bool, groesse, werte: dict, jetzt: datetime, pruefung=None, spot=None) -> dict:
    """O25 (Nutzer 04.10.2026: *nicht die bisherige Form uebernehmen*; M-a bis M-f): EINE Gliederung fuer Text und HTML.

    Reihenfolge M-a: (1) was zu tun ist - (2) Chart - (3) Einschaetzung - (4) Begruendung der Rollen - (5) Technik.
    M-b alles in EUR (Bitpanda), M-c Ortszeit zuerst, M-e Fachbegriffe nur in der Technik, M-f Hinweis auf die alte Spot-Kette.
    ``pruefung``: {"kurz": [(Rolle, Text)], "lang": [Zeilen]} (regel0_llm.mail_teile) oder eine Zeilenliste (alte Form) oder
    {"fehler": Grund}. ``spot``: ein Satz ueber eine Spot-Mail zum selben Asset (oder None)."""
    tw = _testwoche(werte, jetzt)
    ein = _t(r["einstieg"]) + timedelta(hours=1)          # Schlusskurs der Einstiegsstunde
    aus = _t(r["ausstieg"]) + timedelta(hours=1)
    sig = _t(r["signalstunde"])
    name = r.get("bitpanda") or r["symbol"]
    betreff = "%sREGEL0 Hebel LONG %s %dx - Einstieg %s" % ("[TESTWOCHE] " if tw else "", name, stufe,
                                                            ein.astimezone().strftime("%d.%m. %H:%M"))
    p_st = r.get("p%d" % stufe)
    tun = [("Einstieg", "%s - zum Schlusskurs der Stunde %s-%s Uhr" % (
                _wann(ein, jetzt), (ein - timedelta(hours=1)).astimezone().strftime("%H:%M"), ein.astimezone().strftime("%H:%M")))]
    if jetzt > ein:
        # D1-Weg (die Stufe stand erst mit der Einstiegsstunde fest) oder eine aufgefangene Stunde: die Mail kommt nach dem Einstieg
        tun.append(("", "⚠ dieser Einstieg ist seit %d min vorbei - gemessen ist er; ein späterer Einstieg weicht davon ab"
                    % int((jetzt - ein).total_seconds() // 60)))
    if r.get("kurs_eur"):
        tun.append(("Kurs jetzt", "%s EUR (Bitpanda, beim Versand dieser Mail)" % CH._zahl(r["kurs_eur"])))
    else:
        tun.append(("Kurs jetzt", "nicht verfuegbar (Bitpanda-Ticker nicht erreichbar) - bitte in Bitpanda nachsehen"))
    tun.append(("Hebel", "%dx  %s" % (stufe, ("VORLÄUFIG - endgültig, sobald die Einstiegsstunde abgeschlossen ist (%s); weicht "
                                             "die Stufe ab, kommt eine Korrektur" % _wann(ein, jetzt)) if vorlaeufig else "(endgültig)")))
    tun.append(("Einsatz", "%s EUR  →  Position %s EUR" % (("{:,.0f}".format(groesse.einsatz_eur)).replace(",", "."),
                                                          ("{:,.0f}".format(groesse.positionswert_eur)).replace(",", "."))))
    if groesse.vermerk:
        tun.append(("", groesse.vermerk))
    tun.append(("Ausstieg", "%s - nach 24 Stunden, ohne Stop und ohne Ziel" % _wann(aus, jetzt)))
    if r.get("kurs_eur") and stufe > 0:
        lq = r["kurs_eur"] * CH.liq_schwelle(stufe, CH.MARGE, 0)
        tun.append(("Liquidation", "bei etwa %s EUR (%s) - Gefahr binnen 24 h %s (Grenze 2 %%)" % (
            CH._zahl(lq), _prozent(lq / r["kurs_eur"] - 1.0), _pct(p_st))))
    else:
        tun.append(("Liquidation", "Gefahr binnen 24 h %s (Grenze 2 %%) - Kurs in EUR nicht verfuegbar" % _pct(p_st)))
    tun.append(("Bitpanda", "Hebelstufen prüfen: wird %dx nicht angeboten, die nächst kleinere nehmen" % stufe))

    detail, hinweise = [], []
    ein_z = [("Regel", "Gegenbewegung nach einem Rückgang erwartet - Signalstärke %s (gehandelt ab 0,035)" % (
        ("%.3f" % r["vh"]).replace(".", ",") if r.get("vh") is not None else "-"))]
    lang = []
    if isinstance(pruefung, dict) and "fehler" in pruefung:
        ein_z.append(("Rollen", "PRUEFUNG DURCH DIE ROLLEN: nicht verfuegbar (%s)" % pruefung["fehler"]))
    elif isinstance(pruefung, dict):
        ein_z += list(pruefung.get("kurz") or [])
        lang = list(pruefung.get("lang") or [])
        detail, hinweise = list(pruefung.get("detail") or []), list(pruefung.get("hinweise") or [])
    elif pruefung:
        lang = list(pruefung)
    if spot:
        ein_z.append(("Achtung", spot))
    ein_z.append(("Gefahr je Stufe", "2x %s · 3x %s · 5x %s binnen 24 h (Grenze 2 %%)" % (
        _pct(r.get("p2")), _pct(r.get("p3")), _pct(r.get("p5")))))

    technik = [("Asset", "%s%s" % (name, "" if name == r["symbol"] else " (Binance %s)" % r["symbol"])),
               ("Signal", "Stunde ab %s, abgeschlossen %s" % (_zeit(sig), _zeit(sig + timedelta(hours=1)))),
               ("Einstieg", "%s (so ist die REGEL0 gemessen - wer früher oder später einsteigt, handelt etwas anderes)" % _zeit(ein)),
               ("Ausstieg", _zeit(aus))]
    if r.get("kurs"):
        technik.append(("Kurs Signal", "%s USD (Binance %s, Messgrundlage der REGEL0)" % (
            CH._zahl(r["kurs"]), "Futures" if r.get("kurs_markt") == "futures" else "Spot")))
    vm = _vermerke(r)
    if r.get("abgleich"):
        vm.append("Zuordnung: " + r["abgleich"])
    technik += [("Vermerk", x) for x in vm]
    technik += [("Regel", "REGEL0.1 (rsi-Ersteintritt, v-dach %s, Schwelle +0,035, Ruhe 48 h; Hebel aus dem ATR-Modell, Grenze 2 %%)" % (
                    ("%+.4f" % r["vh"]).replace(".", ",") if r.get("vh") is not None else "-")),
                ("Einsatz", "Startwerte in regel0_betrieb.yaml; die Hebelstufen je Asset bei Bitpanda sind noch nicht als Daten hinterlegt (D2)")]
    kopf = "REGEL0.1 - HEBEL-SIGNAL LONG · %s%s" % (name, ("   ·   TESTWOCHE bis %s" % tw) if tw else "")
    return {"betreff": betreff, "kopf": kopf, "tun": tun, "ein": ein_z, "lang": lang, "detail": detail, "hinweise": hinweise,
            "technik": technik,
            "fuss": "Das ist eine Auskunft deines Systems, kein Auftrag - du entscheidest."}


def _als_text(t: dict) -> str:
    import textwrap

    def blk(titel, paare):
        z = ["", titel]
        for k, v in paare:
            z += textwrap.wrap(v, 96, initial_indent="  %-16s" % k, subsequent_indent=" " * 18) or ["  %-16s" % k]
        return z
    z = [t["kopf"]]
    z += blk("1  WAS ZU TUN IST", t["tun"])
    z += ["", "2  CHART  (in der HTML-Ansicht der Mail)"]
    z += blk("3  EINSCHÄTZUNG", t["ein"])
    if t["lang"]:
        z += ["", "4  BEGRÜNDUNG DER ROLLEN"] + ["  " + x if x else "" for x in t["lang"]]
    z += blk("5  TECHNIK", t["technik"])
    z += ["", t["fuss"]]
    return NL.join(z)


def _als_html(t: dict, bilder: int = 0) -> str:
    """O25 M-d: echtes HTML statt eines einzigen <pre> - Abschnitte, Tabellen, bricht am Handy um. ``{{BILD:0}}`` setzt der Versand."""
    from html import escape as e
    sans = "font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;"

    def tab(paare, klein=False):
        zs = "".join("<tr><td style='padding:3px 10px 3px 0;vertical-align:top;color:#555;white-space:nowrap;%s'>%s</td>"
                     "<td style='padding:3px 0;vertical-align:top;%s'>%s</td></tr>" % (
                         "font-size:12px;" if klein else "", e(k), "font-size:12px;" if klein else "", e(v)) for k, v in paare)
        return "<table style='border-collapse:collapse;width:100%%;%s'>%s</table>" % (sans, zs)

    def h(text, farbe="#1f4e79"):
        return "<div style='%sfont-weight:bold;font-size:15px;color:%s;margin:18px 0 6px;border-bottom:2px solid %s'>%s</div>" % (
            sans, farbe, farbe, e(text))
    teile = ["<div style='max-width:680px;%s color:#1a1a1a'>" % sans,
             "<div style='font-weight:bold;font-size:17px;margin-bottom:4px'>%s</div>" % e(t["kopf"]),
             h("1 · Was zu tun ist", "#1e8449"), tab(t["tun"]),
             h("2 · Chart"), "".join("{{BILD:%d}}" % i for i in range(bilder)) or "<div style='color:#888'>(kein Chart verfügbar)</div>",
             h("3 · Einschätzung"), tab(t["ein"])]
    if t.get("detail"):
        teile.append(h("4 · Begründung der Rollen"))
        for titel, urteil, begr, gegen in t["detail"]:
            teile.append("<div style='margin:6px 0 10px'><b>%s</b> · %s%s%s</div>" % (
                e(titel), e(urteil), ("<br>" + e(begr)) if begr else "",
                ("<br><span style='color:#555'><i>Gegengrund:</i> %s</span>" % e(gegen)) if gegen else ""))
        teile += ["<div style='font-size:12px;color:#666'>%s</div>" % e(x) for x in t.get("hinweise") or []]
    elif t["lang"]:
        teile += [h("4 · Begründung der Rollen"),
                  "<pre style='font-family:monospace;font-size:12px;white-space:pre-wrap;overflow-wrap:anywhere;margin:0'>%s</pre>"
                  % e(NL.join(t["lang"]))]
    teile += [h("5 · Technik", "#7f8c8d"), tab(t["technik"], klein=True),
              "<div style='margin-top:14px;color:#555;font-size:12px'>%s</div>" % e(t["fuss"]), "</div>"]
    return "".join(teile)


def signal_mail(r: dict, stufe: int, vorlaeufig: bool, groesse, werte: dict, jetzt: datetime, pruefung=None, spot=None) -> tuple:
    """-> (Betreff, Text). Der Text ist auch das Detail im Hebel-Tab (eine Quelle). Aufbau O25: ``_signal_teile``."""
    t = _signal_teile(r, stufe, vorlaeufig, groesse, werte, jetzt, pruefung, spot)
    return t["betreff"], _als_text(t)


def signal_html(r: dict, stufe: int, vorlaeufig: bool, groesse, werte: dict, jetzt: datetime, pruefung=None, spot=None,
                bilder: int = 0) -> str:
    """Die HTML-Fassung derselben Gliederung (O25 M-d)."""
    return _als_html(_signal_teile(r, stufe, vorlaeufig, groesse, werte, jetzt, pruefung, spot), bilder)


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
    text = "\n".join(["REGEL0.1 - KORREKTUR zum Signal %s (Einstieg %s)" % (name, _wann(ein, jetzt)), "", kern, "",
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
                      "%s, Hebel %dx, Einstieg %s" % (name, stufe, _wann(_t(r["einstieg"]) + timedelta(hours=1), jetzt)),
                      "Die 24 Stunden sind um: Ausstieg zum Schlusskurs %s." % _wann(aus, jetzt), "",
                      "Zeiten in UTC: Einstieg %s, Ausstieg %s." % (_zeit(_t(r["einstieg"]) + timedelta(hours=1)), _zeit(aus)),
                      "Die Fuehrung offener Positionen kommt spaeter (O13)."])
    return betreff, text


def versende(ordner_ablage: str, senden, jetzt: datetime | None = None, werte: dict | None = None, kurse=None, melden=None,
             bild=None, pruefung=None, position=None, spot=None, senden_html=None) -> dict:
    """Prueft die Ablage und verschickt faellige Mails. ``senden(betreff, text) -> bool``. Vermerkt nur echte Versaende.

    S7-5b: vor jeder SIGNALmail der Preisabgleich (``kurse() -> (bitpanda_usd, binance)``, Vorgabe die oeffentlichen Ticker).
    Weicht der Kurs mehr als 5 % ab, gehoert der Binance-Kurs zu einem ANDEREN Coin: keine Mail, Vermerk in der Ablage,
    ``melden(text)`` einmal je Signal. Ist der Ticker nicht erreichbar, geht die Mail mit Vermerk raus (F-2).

    E-50 N-f (03.10.2026): ``bild(r) -> PNG | None`` haengt das Chart an die SIGNALmail (``senden(betreff, text, bilder)``).
    ``pruefung(r) -> [Zeilen]`` haengt den Block der LLM-Rollen an (E-52). Beides darf scheitern, ohne die Mail aufzuhalten (P-8).

    04.10.2026: ``position() -> befund`` (siehe ``position_stand``) - die ERINNERUNG geht nur bei offener Position; ohne
    ``position`` bleibt es beim alten Verhalten (jede Erinnerung).

    O25 (04.10.2026): ``pruefung(r)`` darf ``{"kurz", "lang"}`` liefern (Einschaetzung und Begruendung getrennt), ``spot(r)`` einen
    Satz ueber eine Spot-Mail zum selben Asset (M-f), ``senden_html(betreff, text, html, bilder) -> bool`` verschickt die
    HTML-Fassung (M-d). Ohne ``senden_html`` bleibt der alte Weg ``senden``. Jede dieser Zutaten darf scheitern (P-8)."""
    jetzt = jetzt or datetime.now(timezone.utc)
    werte = werte if werte is not None else G.lade()
    jt = jetzt.strftime("%Y-%m-%d %H:%M")
    grenze_alt = (jetzt - timedelta(hours=NICHT_AELTER_H)).strftime("%Y-%m-%d %H:%M")
    grenze_erin = (jetzt - timedelta(hours=ERINNERUNG_BIS_H + 1)).strftime("%Y-%m-%d %H:%M")
    zaehl = dict(signal=0, korrektur=0, erinnerung=0, fehlgeschlagen=0, gesperrt=0, entfallen=0, verpasst=0)
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
        # 0  VERPASST (N-1, E-57): jedes ungemailte Signal der letzten 24 h, dessen gemessener Einstieg laenger als VERPASST_NACH
        #    vorbei ist, bekommt den Vermerk - auch die nach einem Ausfall nachgeholten, die das Fenster unten (NICHT_AELTER_H) nie
        #    sieht. Sonst stuenden sie als *ohne Mail* da, als waere etwas schiefgegangen.
        _v = c.execute("UPDATE signal SET mail_verpasst_am=? WHERE hebel_schalter=1 AND mail_signal_am IS NULL AND mail_gesperrt_am IS NULL "
                       "AND mail_verpasst_am IS NULL AND COALESCE(stufe, stufe_vorlaeufig) > 0 AND einstieg < ? AND einstieg >= ?",
                       (jt, (jetzt - timedelta(hours=1) - VERPASST_NACH).strftime("%Y-%m-%d %H:%M"),
                        (jetzt - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M"))).rowcount
        # ⚠️ IMMER committen (08.10.2026, Schritt7 §23.25): sqlite3 oeffnet schon mit dem UPDATE eine Schreibtransaktion, auch wenn es
        # 0 Zeilen trifft. Ohne commit hielt diese Verbindung die Ablage gesperrt; der Pruefblock (eigene Verbindung) wartete 30 s und
        # scheiterte mit 'database is locked' - die Mail ging ohne Pruefung raus, keine pruefung-Zeile (BEAMX 07.10., L1 rot).
        c.commit()
        if _v:
            zaehl["verpasst"] += _v
        # 1  SIGNAL: Schalter an, Stufe > 0, noch nicht gemailt, Einstieg nicht laenger als NICHT_AELTER_H vorbei
        for r in c.execute("SELECT * FROM signal WHERE hebel_schalter=1 AND mail_signal_am IS NULL AND mail_gesperrt_am IS NULL "
                           "AND mail_verpasst_am IS NULL "
                           "AND COALESCE(stufe, stufe_vorlaeufig) > 0 AND einstieg >= ? ORDER BY signalstunde", (grenze_alt,)).fetchall():
            r = dict(r)
            # N-1 (E-57): ist der Einstiegszeitpunkt (Schluss der Einstiegsstunde) schon vorbei - nach einem Ausfall nachgeholt -,
            # geht KEINE Signalmail: gemessen ist dieser Einstieg, ein spaeterer ist ein anderer Handel. Vermerk als Fakt.
            if jetzt >= _t(r["einstieg"]) + timedelta(hours=1) + VERPASST_NACH:
                c.execute("UPDATE signal SET mail_verpasst_am=? WHERE symbol=? AND signalstunde=?", (jt, r["symbol"], r["signalstunde"]))
                c.commit(); zaehl["verpasst"] += 1
                continue
            _v = _live()
            ok, txt = abgleich(r, _v[0], _v[1])
            r["abgleich"] = txt
            # 04.10.2026: EUR-Kurs und EUR je USD dieses Assets aus DEMSELBEN Bitpanda-Abruf - fuer Mailtext und Chart
            _e = (_v[2] if len(_v) > 2 and _v[2] else {}).get(r.get("bitpanda") or "")
            _u = (_v[0] or {}).get(r.get("bitpanda") or "")
            if _e:
                r["kurs_eur"] = _e
                if _u:
                    r["eur_je_usd"] = _e / _u
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
            _pr = None
            if pruefung is not None:
                try:
                    _pr = pruefung(r) or None
                except Exception as exc:                        # noqa: BLE001
                    _pr = {"fehler": type(exc).__name__}
                    # 08.10.2026: der Grund gehoert ins Protokoll - am 07.10. war der Ausfall dort unsichtbar (§23.25)
                    __import__("logging").getLogger(__name__).warning("REGEL0-Pruefblock %s %s gescheitert: %s: %s", r.get("symbol"),
                                                                      r.get("signalstunde"), type(exc).__name__, exc)
            _sp = None
            if spot is not None:
                try:
                    _sp = spot(r)
                except Exception:                               # noqa: BLE001
                    _sp = None
            b, t = signal_mail(r, stufe, r["stufe"] is None, g, werte, jetzt, _pr, _sp)
            bilder = None
            if bild is not None:
                try:
                    _png = bild(r)
                except Exception:                               # noqa: BLE001
                    _png = None
                if _png:
                    bilder = [{"png": _png, "alt": "REGEL0 %s" % (r.get("bitpanda") or r["symbol"]),
                               "filename": "regel0_%s_%s.png" % (r["symbol"], r["signalstunde"][:13].replace(" ", "_").replace(":", ""))}]
            if senden_html is not None:
                try:
                    _h = signal_html(r, stufe, r["stufe"] is None, g, werte, jetzt, _pr, _sp, len(bilder or []))
                except Exception:                               # noqa: BLE001
                    _h = None
                _ok = senden_html(b, t, _h, bilder)
            else:
                _ok = senden(b, t, bilder) if bilder else senden(b, t)
            if _ok:
                c.execute("UPDATE signal SET mail_signal_am=?, mail_signal_stufe=?, abgleich=? WHERE symbol=? AND signalstunde=?",
                          (jt, stufe, txt, r["symbol"], r["signalstunde"]))
                c.commit(); zaehl["signal"] += 1
            else:
                zaehl["fehlgeschlagen"] += 1
        # 2  KORREKTUR: die endgueltige Stufe weicht von der gemailten ab
        for r in c.execute("SELECT * FROM signal WHERE mail_signal_am IS NOT NULL AND stufe IS NOT NULL AND mail_korrektur_am IS NULL "
                           "AND korrektur_verpasst_am IS NULL AND stufe != mail_signal_stufe").fetchall():
            r = dict(r)
            # N-1: kam die endgueltige Stufe erst nach einem Ausfall, ist der Einstieg laengst vorbei - keine Korrekturmail, Vermerk
            if jetzt >= _t(r["einstieg"]) + timedelta(hours=1) + VERPASST_NACH:
                c.execute("UPDATE signal SET korrektur_verpasst_am=? WHERE symbol=? AND signalstunde=?", (jt, r["symbol"], r["signalstunde"]))
                c.commit(); zaehl["verpasst"] += 1
                continue
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
