# -*- coding: utf-8 -*-
"""B1 - DER EINE ORT, AN DEM DIE ROLLEN-KETTE ZUSAMMENGESETZT WIRD.

DIE LUECKE, DIE ER SCHLIESST. Die Gesamtpruefung vom 13.08. hat gezaehlt: alle
15 neuen Module haben NULL Betriebsaufrufer. Zwei hingen nicht einmal
innerhalb der Kette - `toepfe` liefert einen Deckel, den
`entscheidungsrechnung` als Parameter erwartet, und `faktenblock_quellen`
speist die Mail. Es gab niemanden, der sie haette verbinden koennen.

DREI BETRIEBSARTEN, VON ANFANG AN EINGEBAUT - nicht nachtraeglich:

    trocken   KEIN Modellaufruf, KEIN Schreiben, KEINE Mail. Laeuft auf
              aufgezeichneten Antworten. Findet Verdrahtungsfehler, fehlende
              Spalten, Abstuerze - und kostet nichts.
    probe     echte Modellaufrufe, Schreiben in die UEBERGEBENE Verbindung,
              Mail wird GEBAUT aber nicht verschickt.
    scharf    wie probe, und die Mail geht raus.

WARUM DER SCHALTER VON ANFANG AN DA IST. Ein Weg, den man erst nachtraeglich
absichert, ist in der Zwischenzeit ungesichert - und die Zwischenzeit ist
genau die Phase, in der man ihn am meisten braucht. Von den drei Fehlern, die
die Gesamtpruefung fand, haette ein Trockenlauf zwei sofort gezeigt: die Mail
haette "Kein Einstieg geplant" gedruckt, und das Schreiben waere am Vokabular
gescheitert. Dafuer braucht es kein einziges Modell.

DIE VERBINDUNG WIRD UEBERGEBEN, NIE HIER GEOEFFNET. Wer diesen Lauf startet,
entscheidet, auf welche Datenbank er wirkt. Eine Vorgabe waere ein stiller
Zugriff auf die Produktivdatei - und diese Kette SCHREIBT.

WAS ER NICHT TUT: er entscheidet nichts. Jede Bewertung liegt in ihrem Modul;
hier steht nur die Reihenfolge und die Frage, was ein Fehlschlag bedeutet.
"""
from __future__ import annotations

from datetime import datetime, timezone

TROCKEN, PROBE, SCHARF = "trocken", "probe", "scharf"
BETRIEBSARTEN = (TROCKEN, PROBE, SCHARF)


class LaufAbgebrochen(RuntimeError):
    """Der Lauf kann nicht sinnvoll fortgesetzt werden."""


def _tage_bis(datum_text, ab_tag: str | None) -> int | None:
    """Aus dem DATUM des Modells die TAGE der Rechnung.

    GEFUNDEN IM ERSTEN TROCKENLAUF (13.08.), und genau dafuer ist er da: das
    Modell liefert `umgeworfen_bis` als Datum ("2026-09-01"),
    `entscheidungsrechnung.rechne()` erwartet `umgeworfen_tage` als Zahl. Zwei
    Pakete, zwei Einheiten, und niemand dazwischen - bis es diesen Ort gab.

    Ein Datum in der Vergangenheit gibt None statt einer negativen Zahl: eine
    abgelaufene Frist ist keine Haltedauer, sondern ein Fall fuer den
    Ausstieg."""
    from datetime import date

    if not datum_text:
        return None
    try:
        ziel = date.fromisoformat(str(datum_text)[:10])
        start = date.fromisoformat(str(ab_tag)[:10]) if ab_tag else date.today()
    except ValueError:
        return None
    tage = (ziel - start).days
    return tage if tage > 0 else None


def _jetzt() -> str:
    return datetime.now(timezone.utc).isoformat()


def fuehre_lauf(*, conn, reihen: dict, symbole: list,
                betriebsart: str = TROCKEN,
                datum: str | None = None,
                client=None, modell: str | None = None,
                antworten: dict | None = None,
                config: dict | None = None,
                db: str = "data/tradinginfotool.db",
                versand=None) -> dict:
    """Ein vollstaendiger Durchgang ueber alle Symbole.

    `antworten` ist die Aufzeichnung fuer den Trockenlauf:
    `{"lagebild": {...}, "befund": {symbol: {...}}}`. Fehlt sie dort, wird das
    Symbol als Fehlschlag der Stufe gezaehlt - NICHT uebersprungen. Ein
    Trockenlauf, der stillschweigend weniger prueft, als er behauptet, ist
    schlimmer als keiner.

    Gibt `{"durchlauf": ..., "signale": [...], "mails": [...], "z1": {...}}`
    zurueck."""
    if betriebsart not in BETRIEBSARTEN:
        raise LaufAbgebrochen(f"unbekannte Betriebsart {betriebsart!r} - "
                              f"erlaubt {BETRIEBSARTEN}")
    if betriebsart != TROCKEN and client is None:
        raise LaufAbgebrochen(
            f"Betriebsart {betriebsart!r} braucht einen Modell-Client. Ohne ihn "
            f"waere es ein Trockenlauf, der sich als echter ausgibt.")
    if conn is None:
        raise LaufAbgebrochen(
            "ohne Verbindung kein Lauf - sie wird uebergeben, nie hier "
            "geoeffnet: diese Kette schreibt.")

    from agent import (ausstiegsrechnung as AR, entscheidungsrechnung as ER,
                       faktenblock as FB, faktenblock_quellen as FQ,
                       gegenpruefer_rollen as Z1, rolle_analyst as RA,
                       rolle_trader as RT, rollen_eingabe as RE,
                       rollen_gate as RG, signal_abbildung as SA,
                       signal_mail as SM, toepfe as TO, trefferbilanz as TB)
    from agent.empfehlung_vertrag import EmpfehlungUngueltig
    from agent.handelsauftrag import AuftragUngueltig, pruefe as pruefe_auftrag

    ergebnis = {"betriebsart": betriebsart, "signale": [], "mails": [],
                "fehler": []}
    durchlauf = RG.Durchlauf("rollen")
    ergebnis["durchlauf"] = durchlauf
    aufgezeichnet = antworten or {}

    # ---- ROLLE A: einmal je Lauf, nicht je Asset ----------------------------
    #
    # ERST DIE ABBRUCHGRUENDE, DANN DIE ARBEIT. Die erste Fassung baute die
    # Lagebild-Eingabe VOR der Pruefung auf die Aufzeichnung - bei leeren
    # Kursreihen stuerzte sie dort ab, statt mit einer Begruendung
    # abzubrechen. Ein Absturz sagt nicht, was fehlt.
    tag = datum or max((k.date for r in reihen.values() for k in r[-1:]),
                       default=None)
    if not reihen or tag is None:
        raise LaufAbgebrochen(
            "keine Kursreihen - ohne sie gibt es weder ein Lagebild noch "
            "einen Ankertag, und ein Lauf ohne Anker vergleicht nichts.")
    if betriebsart == TROCKEN and aufgezeichnet.get("lagebild") is None:
        raise LaufAbgebrochen(
            "Trockenlauf ohne aufgezeichnetes Lagebild - es gibt nichts zu "
            "pruefen, und ein leerer Durchlauf saehe aus wie ein Erfolg.")

    a_ein = RE.baue_lagebild_eingabe(reihen, tag)
    if betriebsart == TROCKEN:
        a_roh = aufgezeichnet.get("lagebild")
        if a_roh is None:
            raise LaufAbgebrochen(
                "Trockenlauf ohne aufgezeichnetes Lagebild - es gibt nichts zu "
                "pruefen, und ein leerer Durchlauf saehe aus wie ein Erfolg.")
    else:
        a_roh = _frage(client, modell, RA.SYSTEM_PROMPT_ANALYST, a_ein,
                       "agent.rolle_analyst")
    lagebild = RE.stempel_gleichlauf(RA.validiere(a_roh), reihen, tag)
    gleichlauf = lagebild.get("gleichlauf")

    # Z1 auf das Lagebild - ZAEHLEN, nicht verwerfen.
    ergebnis["z1_lagebild"] = Z1.pruefe(lagebild, a_ein.get("fakten", a_ein),
                                        gleichlauf)

    lagebild_id = None
    if betriebsart != TROCKEN:
        SA.migriere(conn)
        RG.migriere(conn)
        lagebild_id = SA.schreibe_lagebild(
            conn, datum=tag, antwort=lagebild, fakten=a_ein,
            prompt_stand=getattr(RA, "PROMPT_STAND", "?"), modell=modell or "-")

    # ---- ROLLE BC: je Asset -------------------------------------------------
    for symbol in symbole:
        durchlauf.beginne(symbol)
        try:
            _ein_asset(symbol=symbol, reihen=reihen, tag=tag, lagebild=lagebild,
                       lagebild_id=lagebild_id, gleichlauf=gleichlauf,
                       durchlauf=durchlauf, betriebsart=betriebsart,
                       client=client, modell=modell, conn=conn, db=db,
                       config=config, aufgezeichnet=aufgezeichnet,
                       ergebnis=ergebnis, versand=versand,
                       module=(AR, ER, FB, FQ, Z1, RT, RE, SA, SM, TO, TB),
                       fehlertypen=(EmpfehlungUngueltig, AuftragUngueltig,
                                    RT.TraderAntwortUngueltig),
                       pruefe_auftrag=pruefe_auftrag)
        except Exception as exc:                       # noqa: BLE001
            # EIN ASSET DARF DEN LAUF NICHT BEENDEN. Was hier abbricht, ist
            # gezaehlt und benannt - stilles Ueberspringen waere derselbe
            # Fehler wie ein Filter, der seine Wirkung verbirgt.
            ergebnis["fehler"].append(f"{symbol}: {type(exc).__name__}: {exc}")
            # DIE STUFE MUSS STIMMEN. Der erste Trockenlauf zaehlte einen
            # Fehler aus der GEOMETRIE als Urteilsverlust - die Tabelle haette
            # auf die falsche Stelle gezeigt, und genau dafuer gibt es sie.
            letzte = next((st for st, _ in reversed(RG.STUFEN)
                           if durchlauf.bestanden_je_stufe.get(st)), "auftrag")
            durchlauf.verloren(symbol, letzte, type(exc).__name__)

    if betriebsart != TROCKEN:
        RG.schreibe(conn, durchlauf, _jetzt())
    return ergebnis


def _ein_asset(*, symbol, reihen, tag, lagebild, lagebild_id, gleichlauf,
               durchlauf, betriebsart, client, modell, conn, db, config,
               aufgezeichnet, ergebnis, versand, module, fehlertypen,
               pruefe_auftrag) -> None:
    """Ein Asset durch alle Stufen. Wirft, wenn es nicht weitergeht."""
    AR, ER, FB, FQ, Z1, RT, RE, SA, SM, TO, TB = module

    # --- Stufe: Auftrag ---
    instrument, strategie = pruefe_auftrag("spot", "einstieg")
    durchlauf.bestanden(symbol, "auftrag")

    # --- Stufe: Fakten ---
    reihe = reihen.get(symbol)
    if not reihe:
        durchlauf.verloren(symbol, "fakten", "keine Kursreihe")
        return
    idx = len(reihe) - 1
    if tag:
        treffer = next((i for i, k in enumerate(reihe) if k.date >= tag), None)
        if treffer is None:
            durchlauf.verloren(symbol, "fakten", f"keine Daten ab {tag}")
            return
        idx = treffer
    # TROCKEN HEISST AUCH: KEIN NETZ. `baue_fall()` holt sonst die
    # Finanzierungsrate von der Boerse - und JEDER externe Aufruf bucht seinen
    # Gesundheitsstand in `api_health_status`. Der erste Trockenlauf hat damit
    # in die Produktivdatenbank geschrieben, obwohl er nichts schreiben
    # sollte. Gefunden von der eigenen Pruefung, nicht vermutet.
    #
    # `mit_finanzierung=False` steht dafuer schon im Modul bereit - es war als
    # Vergleichsarm fuer gepaarte Messungen gebaut und passt hier genau: der
    # Trockenlauf soll die VERDRAHTUNG pruefen, nicht die Boerse.
    _, bc_ein = RE.baue_fall(symbol=symbol, reihe=reihe, index=idx,
                             reihen=reihen, db=db,
                             mit_finanzierung=(betriebsart != "trocken"))
    atr_e = RE.atr_eur(symbol, reihe, idx, db)
    kurs_e = RE.kurs_eur(symbol, reihe, idx, db)
    durchlauf.bestanden(symbol, "fakten")
    durchlauf.bestanden(symbol, "lagebild")

    # --- Stufe: Urteil ---
    bc_ein["marktlage_beurteilung"] = {"lage": lagebild["lage"],
                                       "gleichlauf": gleichlauf}
    if betriebsart == "trocken":
        bc_roh = (aufgezeichnet.get("befund") or {}).get(symbol)
        if bc_roh is None:
            durchlauf.verloren(symbol, "urteil", "keine aufgezeichnete Antwort")
            return
    else:
        bc_roh = _frage(client, modell, RT.prompt_fuer(instrument, strategie),
                        bc_ein, "agent.rolle_trader")
    try:
        befund = RT.validiere(bc_roh, symbol, atr=atr_e, instrument=instrument,
                              strategie=strategie)
    except fehlertypen as exc:
        durchlauf.verloren(symbol, "urteil", type(exc).__name__)
        ergebnis["fehler"].append(f"{symbol}: {exc}")
        return
    z1 = Z1.pruefe_und_zaehle(befund, bc_ein, symbol=symbol,
                              durchlauf=durchlauf, stufe="urteil",
                              gleichlauf_wert=gleichlauf)
    durchlauf.faktorzahl(befund.get("unabhaengige_faktoren"))

    # --- Stufe: Aktion ---
    aktion = befund.get("aktion")
    if aktion not in SM.AKTIONEN_MIT_EINSTIEG:
        durchlauf.verloren(symbol, "aktion", aktion or "?")
        return
    durchlauf.bestanden(symbol, "aktion")

    # --- Stufe: Geometrie + Risikoschicht ---
    # HIER HAENGT `toepfe` ENDLICH DRAN. Bis zum 13.08. war das Modul gebaut
    # und von nichts aufgerufen; `entscheidungsrechnung` bekam den Deckel als
    # Parameter, den niemand fuellte.
    frei = TO.frei_eur(instrument, belegt_eur=0.0, config=config)
    try:
        rechnung = ER.rechne(kurs=kurs_e, atr=atr_e, risiko_eur=75.0,
                             instrument=instrument, betrag_wunsch_eur=500.0,
                             topf_frei_eur=frei,
                             umgeworfen_preis_eur=befund.get("umgeworfen_preis_eur"),
                             umgeworfen_tage=_tage_bis(
                                 befund.get("umgeworfen_bis"), tag))
    except ER.RechnungBlockiert as exc:
        durchlauf.verloren(symbol, "geometrie", str(exc)[:40])
        return
    durchlauf.bestanden(symbol, "geometrie")
    durchlauf.bestanden(symbol, "risikoschicht")

    # --- Stufe: Entscheider - ZAEHLT, verwirft nicht ---
    kosten_r = TB.kosten_r_aus_stop(kurs_e, rechnung["stop_eur"])
    bewertung = TB.bewerte({}, TB.merkmale(
        unabhaengige_faktoren=befund.get("unabhaengige_faktoren")),
        kosten_r=kosten_r or 0.0, crv=rechnung["crv"])
    if not bewertung["traegt"]:
        durchlauf.verloren(symbol, "entscheider", "traegt sich nicht")
    else:
        durchlauf.bestanden(symbol, "entscheider")

    # --- Die Mail ---
    kern = FB.werte_aus_reihe([k.high for k in reihe], [k.low for k in reihe],
                              [k.close for k in reihe],
                              [getattr(k, "volume", 0) or 0 for k in reihe],
                              i=idx, tag_vollstaendig=(idx < len(reihe) - 1))
    # UND HIER `faktenblock_quellen` - das zweite Modul ohne Aufrufer.
    zusatz, _fehlt = FQ.abbilden(bc_ein.get("fakten_roh"),
                                 bereich=f"krypto_{instrument}",
                                 position_eur=rechnung["betrag_eur"],
                                 hebel=rechnung.get("hebel"))
    block = FB.baue(f"krypto_{instrument}", kern_werte=kern,
                    zusatz_werte=zusatz, symbol=symbol) if kern else []
    betreff, text = SM.baue_mail(
        symbol=symbol, name=symbol, kurs_eur=kurs_e, instrument=instrument,
        strategie=strategie, rechnung=rechnung, urteil=befund,
        faktenblock=block, modell=modell, zeitpunkt=tag,
        einordnung=TB.satz(bewertung, einstieg=kurs_e,
                           stop=rechnung["stop_eur"],
                           einsatz_eur=rechnung["betrag_eur"])
        + Z1.satz(z1))
    ergebnis["mails"].append({"symbol": symbol, "betreff": betreff, "text": text})

    # --- Schreiben und Versenden ---
    if betriebsart != "trocken":
        felder = SA.felder_aus_entscheidung(
            befund, fakten=bc_ein, lagebild_id=lagebild_id,
            prompt_stand=getattr(RT, "PROMPT_STAND", "?"),
            eur_je_usd=RE.fx_eur_je_usd(symbol, reihe, idx, db))
        ergebnis["signale"].append({"symbol": symbol, "felder": felder})
    if betriebsart == "scharf" and versand is not None:
        versand(betreff, text)


def _frage(client, modell, system_prompt, eingabe, modulname):
    """Der Modellaufruf. Absichtlich duenn - die Kette soll nicht wissen,
    welcher Anbieter dahintersteht."""
    import json

    from agent.llm_schema import als_response_format

    antwort = client.chat(
        modell=modell, system=system_prompt,
        nachricht=json.dumps(eingabe, ensure_ascii=False),
        response_format=als_response_format(modulname))
    return antwort if isinstance(antwort, dict) else json.loads(antwort)
