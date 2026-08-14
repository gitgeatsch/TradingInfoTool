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


# Die Klassen, die der Lagebild-Analyst kennt, plus die beiden Bereiche, die
# es nur im Faktenblock gibt. NICHT aus `rolle_analyst.KLASSEN` abgeleitet: dort
# stehen die LEITMAERKTE, ueber die geurteilt wird, hier die Klassen, in denen
# gehandelt wird. Zwei Listen, zwei Bedeutungen - sie sehen nur gleich aus.
KLASSEN = ("krypto", "aktien", "rohstoffe", "themen_etf", "hedge")


def _bereich(assetklasse: str, instrument: str) -> str:
    """Der Faktenblock-Bereich. Nur Krypto ist nach Instrument getrennt.

    `faktenblock.ZUSATZ_JE_BEREICH` fuehrt `krypto_spot` und `krypto_hebel`
    getrennt (Finanzierung und Liquidation gibt es nur beim Hebel), die uebrigen
    Klassen als EINEN Bereich. Diese Funktion bildet genau das ab - statt den
    Namen an zwei Stellen zusammenzusetzen und darauf zu hoffen."""
    return f"krypto_{instrument}" if assetklasse == "krypto" else assetklasse


def _kostenklasse(assetklasse: str) -> str:
    """Krypto rechnet in Prozent, alles andere hat eine Fixgebuehr.

    Der Unterschied ist nicht kosmetisch: die Fixgebuehr macht die Kosten
    POSITIONSGROESSEN-ABHAENGIG. Bei 200 EUR liegt der Breakeven um ueber fuenf
    Prozentpunkte hoeher als bei 1.000 EUR - bei Krypto kuerzt sich der Betrag
    heraus."""
    return "krypto" if assetklasse == "krypto" else "boerse"


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


# Wie viele Symbole am Ankertag eine Kerze haben muessen. 0,6 ist bewusst
# grosszuegig: die Schranke soll den TOTALAUSFALL abfangen, nicht bei jedem
# fehlenden Kleinwert anhalten.
MINDEST_DECKUNG = 0.6

# Wie lange ein Lagebild wiederverwendet wird. Nutzerentscheidung 14.08.:
# drei Stunden, nicht acht - es speist JEDEN Trader-Aufruf in seinem Fenster.
LAGEBILD_HALTBAR_STUNDEN = 3.0


def _ankertag(reihen: dict, mindest_deckung: float = MINDEST_DECKUNG,
              blick_tage: int = 10) -> tuple:
    """Der Tag, auf dem der Lauf ankert - und wie gut er gedeckt ist.

    DER FEHLER, DEN DAS BEHEBT (15.5b). Vorher stand hier schlicht das MAXIMUM
    ueber alle Symbole. Damit setzt EIN einziges Symbol den Anker fuer alle -
    aktualisiert eine Quelle und 44 nicht, faellt der ganze Rest an der
    Faktenstufe heraus, und der Lauf sieht aus wie ein ruhiger Tag statt wie
    ein Datenausfall.

    GEMESSEN AM 13.08. am echten Bestand:

        2026-07-19   20 von 45  (44 %)   <- das Maximum, und der alte Anker
        2026-07-17   29 von 45  (64 %)
        2026-07-13   44 von 45  (98 %)

    IM GESUNDEN BETRIEB AENDERT SICH NICHTS. Sind alle Reihen aktuell, ist der
    juengste Tag zu 100 % gedeckt und wird gewaehlt - genau wie vorher. Die
    Regel greift nur, wenn sie gebraucht wird.

    LIEBER EINEN TAG AELTER ALS EINE HANDVOLL SYMBOLE. Ein Lauf ueber 44 Assets
    auf vorgestrigen Kursen sagt mehr als einer ueber 20 auf gestrigen - und
    vor allem sagt er nicht faelschlich, es sei nichts los gewesen.

    Gibt `(tag, gedeckt, gesamt)` zurueck; `tag` ist None, wenn kein Tag im
    Blickfenster die Schranke erreicht - dann bricht der Aufrufer ab."""
    if not reihen:
        return None, 0, 0
    gesamt = len(reihen)
    kandidaten = sorted({k.date for r in reihen.values()
                         for k in r[-blick_tage:]}, reverse=True)
    bester = (None, 0)
    for tag in kandidaten:
        gedeckt = sum(1 for r in reihen.values()
                      if any(k.date == tag for k in r[-blick_tage:]))
        if gedeckt > bester[1]:
            bester = (tag, gedeckt)
        if gedeckt >= mindest_deckung * gesamt:
            return tag, gedeckt, gesamt
    # NICHTS ERREICHT DIE SCHRANKE - der beste Tag wird trotzdem GENANNT, damit
    # die Fehlermeldung eine Zahl hat statt nur ein "zu wenig".
    return None, bester[1], gesamt


def fuehre_lauf(*, conn, reihen: dict, symbole: list,
                betriebsart: str = TROCKEN,
                instrument: str = "spot",
                strategie: str = "einstieg",
                datum: str | None = None,
                client=None, modell: str | None = None,
                antworten: dict | None = None,
                config: dict | None = None,
                db: str = "data/tradinginfotool.db",
                versand=None, zai_client=None,
                assetklasse: str = "krypto",
                max_aufrufe: int | None = None) -> dict:
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
                       signal_mail as SM, toepfe as TO, trefferbilanz as TB,
                       wiederholung as WH, zweite_meinung as ZM,
                       betraege as BE)
    from agent.empfehlung_vertrag import EmpfehlungUngueltig
    from agent.handelsauftrag import AuftragUngueltig, pruefe as pruefe_auftrag

    # DER AUFTRAG WIRD EINMAL GEPRUEFT, NICHT JE ASSET (13.08.). Vorher stand
    # hier fest `("spot", "einstieg")` - ein Hebel-Lauf war damit gar nicht
    # moeglich, obwohl Paket 13 alles dafuer gebaut hatte. Die Pruefung gehoert
    # VOR die Schleife: ein unvorgesehenes Paar soll den Lauf abbrechen, nicht
    # vierzigmal dasselbe melden.
    try:
        instrument, strategie = pruefe_auftrag(instrument, strategie)
    except AuftragUngueltig as exc:
        raise LaufAbgebrochen(f'Auftrag ungueltig: {exc}') from exc

    # DIE ASSETKLASSE WIRD EINMAL GEPRUEFT, wie der Auftrag. Ein Tippfehler
    # soll den Lauf abbrechen und nicht vierzigmal in einen unbekannten
    # Faktenblock-Bereich laufen.
    assetklasse = str(assetklasse or "").strip().lower()
    if assetklasse not in KLASSEN:
        raise LaufAbgebrochen(
            f"Assetklasse {assetklasse!r} unbekannt - erlaubt {KLASSEN}")
    ergebnis = {"betriebsart": betriebsart, "signale": [], "mails": [],
                "fehler": [], "assetklasse": assetklasse}
    # EINMAL JE LAUF, nicht je Asset - 45 Symbole waeren sonst 45 Abfragen ueber
    # dieselbe Tabelle. Dass die Bilanz waehrend des Laufs nicht mitwaechst, ist
    # richtig so: alle Assets eines Durchgangs sollen gegen denselben
    # Kenntnisstand bewertet werden, sonst haenge das Urteil an der Reihenfolge.
    try:
        bilanz = TB.zaehle(conn, quelle_kette="rollen")
    except Exception as exc:                                 # noqa: BLE001
        ergebnis["fehler"].append(f"Trefferbilanz nicht lesbar: {exc}")
        bilanz = {}
    ergebnis["bilanz_zellen"] = len(bilanz)
    durchlauf = RG.Durchlauf("rollen")
    ergebnis["durchlauf"] = durchlauf
    aufgezeichnet = antworten or {}

    # ---- ROLLE A: einmal je Lauf, nicht je Asset ----------------------------
    #
    # ERST DIE ABBRUCHGRUENDE, DANN DIE ARBEIT. Die erste Fassung baute die
    # Lagebild-Eingabe VOR der Pruefung auf die Aufzeichnung - bei leeren
    # Kursreihen stuerzte sie dort ab, statt mit einer Begruendung
    # abzubrechen. Ein Absturz sagt nicht, was fehlt.
    if datum:
        tag, gedeckt, gesamt = datum, len(reihen), len(reihen)
    else:
        tag, gedeckt, gesamt = _ankertag(reihen)
    ergebnis["ankertag"] = {"tag": tag, "gedeckt": gedeckt, "gesamt": gesamt}
    if not reihen:
        raise LaufAbgebrochen(
            "keine Kursreihen - ohne sie gibt es weder ein Lagebild noch "
            "einen Ankertag, und ein Lauf ohne Anker vergleicht nichts.")
    if tag is None:
        raise LaufAbgebrochen(
            f"kein Ankertag mit ausreichender Deckung - bestenfalls {gedeckt} "
            f"von {gesamt} Symbolen ({100 * gedeckt / gesamt:.0f} %, noetig "
            f"{100 * MINDEST_DECKUNG:.0f} %). Das ist ein Datenausfall, kein "
            f"ruhiger Tag - ein Lauf darauf saehe aus wie das eine und waere "
            f"das andere.")
    if betriebsart == TROCKEN and aufgezeichnet.get("lagebild") is None:
        raise LaufAbgebrochen(
            "Trockenlauf ohne aufgezeichnetes Lagebild - es gibt nichts zu "
            "pruefen, und ein leerer Durchlauf saehe aus wie ein Erfolg.")

    a_ein = RE.baue_lagebild_eingabe(reihen, tag)

    # DAS LAGEBILD WIEDERVERWENDEN, SOLANGE ES FRISCH IST (14.08.).
    #
    # Rolle A beschreibt den Gesamtmarkt. Im 15-Minuten-Takt waere das 96-mal
    # taeglich dieselbe Frage - fuer eine Aussage, die sich in einer
    # Viertelstunde nicht aendert. Drei Stunden Haltbarkeit machen daraus acht.
    #
    # NUR IM ECHTEN BETRIEB. Der Trockenlauf soll die Verdrahtung pruefen und
    # nicht davon abhaengen, was zufaellig in der Datenbank liegt.
    lagebild = lagebild_id = None
    if betriebsart != TROCKEN:
        gefunden = SA.juengstes_lagebild(conn, LAGEBILD_HALTBAR_STUNDEN)
        if gefunden:
            lagebild_id, lagebild = gefunden
            ergebnis["lagebild_wiederverwendet"] = True

    if lagebild is None:
        # BEIDE ZWEIGE BAUEN DAS LAGEBILD, nicht nur einer. Meine erste Fassung
        # der Wiederverwendung liess die Aufbereitung im `else` stehen - der
        # Trockenlauf hatte danach `lagebild = None` und waere an der naechsten
        # Zeile gestorben. Gefunden beim Nachlesen, nicht vom Testlauf.
        if betriebsart == TROCKEN:
            a_roh = aufgezeichnet.get("lagebild")
            if a_roh is None:
                raise LaufAbgebrochen(
                    "Trockenlauf ohne aufgezeichnetes Lagebild - es gibt nichts "
                    "zu pruefen, und ein leerer Durchlauf saehe aus wie ein "
                    "Erfolg.")
        else:
            a_roh = _frage(client, modell, RA.SYSTEM_PROMPT_ANALYST, a_ein,
                           "agent.rolle_analyst")
        lagebild = RE.stempel_gleichlauf(RA.validiere(a_roh), reihen, tag)
    gleichlauf = lagebild.get("gleichlauf")

    # Z1 auf das Lagebild - ZAEHLEN, nicht verwerfen.
    ergebnis["z1_lagebild"] = Z1.pruefe(lagebild, a_ein.get("fakten", a_ein),
                                        gleichlauf)

    if betriebsart != TROCKEN and lagebild_id is None:
        SA.migriere(conn)
        RG.migriere(conn)
        lagebild_id = SA.schreibe_lagebild(
            conn, datum=tag, antwort=lagebild, fakten=a_ein,
            prompt_stand=getattr(RA, "PROMPT_STAND", "?"), modell=modell or "-")

    # ---- ROLLE BC: je Asset -------------------------------------------------
    #
    # DIE REIHENFOLGE ENTSCHEIDET, WER BEI KNAPPEM BUDGET DRANKOMMT - und der
    # Nutzer hat sie bestimmt: Bestand zuerst. Bei einer Position, die er haelt,
    # steht taeglich eine echte Entscheidung an; bei einem fremden Symbol kann
    # er warten. Ausgeschlossen wird dabei NICHTS (siehe `warteschlange`).
    from agent import warteschlange as WS
    if betriebsart != TROCKEN:
        symbole = WS.sortiere(conn, symbole, instrument)
        ergebnis["reihenfolge"] = WS.erklaere(conn, symbole,
                                              instrument=instrument)

    # DER DECKEL ZAEHLT NUR ECHTE MODELLAUFRUFE, nicht Symbole. Ein Symbol, das
    # am Cooldown scheitert, kostet nichts und darf den Deckel nicht verbrauchen
    # - sonst haette ein gesperrtes Asset dieselbe Wirkung wie ein bezahltes.
    ergebnis["aufrufe"] = 0
    for symbol in symbole:
        if max_aufrufe is not None and ergebnis["aufrufe"] >= max_aufrufe:
            ergebnis.setdefault("budget_gestoppt", []).append(symbol)
            continue
        durchlauf.beginne(symbol)
        try:
            _ein_asset(symbol=symbol, reihen=reihen, tag=tag, lagebild=lagebild,
                       lagebild_id=lagebild_id, gleichlauf=gleichlauf,
                       durchlauf=durchlauf, betriebsart=betriebsart,
                       client=client, modell=modell, conn=conn, db=db,
                       config=config, aufgezeichnet=aufgezeichnet,
                       instrument=instrument, strategie=strategie,
                       ergebnis=ergebnis, versand=versand,
                       assetklasse=assetklasse,
                       module=(AR, ER, FB, FQ, Z1, RT, RE, SA, SM, TO, TB,
                               ZM, BE, WH),
                       zai_client=zai_client, bilanz=bilanz,
                       fehlertypen=(EmpfehlungUngueltig, AuftragUngueltig,
                                    RT.TraderAntwortUngueltig),
                       pruefe_auftrag=pruefe_auftrag)
        except Exception as exc:                       # noqa: BLE001
            # EIN ASSET DARF DEN LAUF NICHT BEENDEN. Was hier abbricht, ist
            # gezaehlt und benannt - stilles Ueberspringen waere derselbe
            # Fehler wie ein Filter, der seine Wirkung verbirgt.
            ergebnis["fehler"].append(f"{symbol}: {type(exc).__name__}: {exc}")
            # DIE STUFE MUSS STIMMEN - JE SYMBOL, nicht global.
            #
            # Die erste Fassung suchte die letzte Stufe, auf der IRGENDEIN
            # Symbol bestanden hatte. Im Watchlist-Probelauf vom 13.08. brach
            # RENDER mit einem Gemini-503 im URTEIL ab und wurde als Verlust
            # der RISIKOSCHICHT gezaehlt - weil andere Symbole dort schon durch
            # waren. Die Tabelle zeigte auf die falsche Stelle, und das ist der
            # einzige Zweck, den sie hat.
            letzte = durchlauf.naechste_stufe(symbol)
            durchlauf.verloren(symbol, letzte, type(exc).__name__)

    if betriebsart != TROCKEN:
        RG.schreibe(conn, durchlauf, _jetzt())
    return ergebnis


def _ein_asset(*, symbol, reihen, tag, lagebild, lagebild_id, gleichlauf,
               durchlauf, betriebsart, client, modell, conn, db, config,
               instrument, strategie,
               aufgezeichnet, ergebnis, versand, module, fehlertypen,
               pruefe_auftrag, zai_client=None, bilanz=None,
               assetklasse="krypto") -> None:
    """Ein Asset durch alle Stufen. Wirft, wenn es nicht weitergeht."""
    AR, ER, FB, FQ, Z1, RT, RE, SA, SM, TO, TB, ZM, BE, WH = module

    # --- Stufe: Auftrag --- (schon vor der Schleife geprueft)
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

    # --- Cooldown: VOR dem Modellaufruf ---------------------------------
    #
    # HIER UND NIRGENDWO SPAETER. Die erste Fassung stand NACH dem
    # Trader-Aufruf - sie verhinderte die Mail, nicht die Kosten. Das Geld war
    # ausgegeben, wenn sie griff, und der Lauf machte bei jedem 15-Minuten-Takt
    # einen vollen Durchgang: 4.800 Trader-Aufrufe am Tag gegen ein
    # Gemini-Budget von 500.
    #
    # An dieser Stelle kostet dieselbe Pruefung nichts und spart alles:
    # 41 Symbole bei 15 h Cooldown ergeben 66 Aufrufe am Tag statt 3.936.
    #
    # DER GRUND, WARUM ES DEN COOLDOWN GIBT, ist die eigene Messung dieses
    # Projekts: fuenf Symbole trugen 102 % des Minus, und die Ursache war die
    # WIEDERHOLUNG. Die alte Kette fuehrt dafuer acht Einstellungen; die
    # Rollen-Kette las bis zum 13.08. keine davon.
    #
    # GEBUCHT WIRD DER VERLUST AUF DER URTEILSSTUFE - dort, wo das Symbol
    # gerade stand. Es hat Auftrag, Fakten und Lagebild bestanden und ist nie
    # zu einem Urteil gekommen; der Trichter bleibt damit monoton. Dass es der
    # Cooldown war und kein schlechtes Urteil, steht im Grund.
    if betriebsart != TROCKEN:
        sperre = WH.gesperrt_bis(conn, symbol, instrument, config=config)
        if sperre:
            durchlauf.verloren(symbol, "urteil", f"Cooldown bis {sperre[:16]}")
            return

    # --- Stufe: Urteil ---
    bc_ein["marktlage_beurteilung"] = {"lage": lagebild["lage"],
                                       "gleichlauf": gleichlauf}
    if betriebsart == "trocken":
        bc_roh = (aufgezeichnet.get("befund") or {}).get(symbol)
        if bc_roh is None:
            durchlauf.verloren(symbol, "urteil", "keine aufgezeichnete Antwort")
            return
    else:
        ergebnis["aufrufe"] = ergebnis.get("aufrufe", 0) + 1
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
        # DAS NEIN WIRD MITGESCHRIEBEN - und zwar AUFLOESBAR (14.08.).
        #
        # NUTZERSORGE, die das ausgeloest hat: *"es werden laufend Signale
        # erzeugt deren Qualitaet nie oder in Monaten bewertet werden koennen"*
        # und *"die Signale sind Wuerfel mit Bonusinfo"*.
        #
        # Beide Fragen brauchen BEIDE Arme. Ob das JA des Modells den
        # Kosten-Breakeven schlaegt, misst man an den Einstiegen; ob das NEIN
        # besser ist als der Zufall, nur an den Nein-Faellen. Die Urteile
        # fallen ohnehin - sie wurden bisher nur weggeworfen.
        #
        # KOSTET KEINEN EINZIGEN ZUSAETZLICHEN AUFRUF und halbiert die Zeit bis
        # zu einer Antwort auf die Zufallsfrage.
        #
        # MIT GERECHNETEN ZONEN, sonst ist es wertlos: `backward_tracking.
        # _hat_selbst_halten_these()` verlangt Einstieg, Stop UND Ziel - ohne
        # sie bliebe die Zeile fuer immer unaufgeloest und waere genau das,
        # wovor der Nutzer warnt. Die Zonen sind hier eine GEGENRECHNUNG, keine
        # Empfehlung: sie sagen, was passiert waere.
        if betriebsart != TROCKEN:
            _schreibe_nein(symbol=symbol, befund=befund, kurs_e=kurs_e,
                           atr_e=atr_e, tag=tag, reihe=reihe, idx=idx,
                           lagebild_id=lagebild_id, instrument=instrument,
                           strategie=strategie, conn=conn, db=db,
                           config=config, modell=modell, ergebnis=ergebnis,
                           module=module)
        return
    durchlauf.bestanden(symbol, "aktion")


    # --- Stufe: Geometrie + Risikoschicht ---
    # HIER HAENGT `toepfe` ENDLICH DRAN. Bis zum 13.08. war das Modul gebaut
    # und von nichts aufgerufen; `entscheidungsrechnung` bekam den Deckel als
    # Parameter, den niemand fuellte.
    # DER BESTAND DES TOPFES, nicht die Null. Bis zum 13.08. stand hier fest
    # `belegt_eur=0.0` - der Topf meldete sich bei JEDEM Signal als vollstaendig
    # frei, und der Deckel konnte nie greifen. Im Live-Lauf bekamen drei
    # Hebel-Signale je 500 EUR aus einem 500-EUR-Topf.
    # RM-4: was nach der Reserve ueberhaupt noch einsetzbar ist. Im
    # Trockenlauf None - er hat keine Verbindung zu einer echten Lage.
    cash_frei = TO.cash_frei_eur(conn, config) if betriebsart != TROCKEN else None
    frei = TO.frei_eur(instrument, config=config,
                       belegt_eur=(TO.belegt_eur(conn, instrument)
                                   if betriebsart != TROCKEN else 0.0))
    # DIE BETRAEGE KOMMEN AUS `betraege`, NICHT AUS DIESER ZEILE. Vorher standen
    # hier 75.0 und 500.0 - Zahlen, die niemand hergeleitet hatte und die jedes
    # Signal gleich gross machten.
    try:
        rechnung = ER.rechne(kurs=kurs_e, atr=atr_e,
                             risiko_eur=BE.risiko_eur(instrument, strategie, config),
                             instrument=instrument,
                             betrag_wunsch_eur=BE.einsatz_eur(instrument, strategie, config),
                             topf_frei_eur=frei, cash_frei_eur=cash_frei,
                             umgeworfen_preis_eur=befund.get("umgeworfen_preis_eur"),
                             # DIE RICHTUNG KOMMT VOM MODELL (Paket 13) und
                             # dreht Stop, Ziel und Liquidation. Bei Spot gibt
                             # es sie nicht - dort ist LONG die einzige Lage.
                             ist_short=(befund.get("richtung") == "SHORT"),
                             umgeworfen_tage=_tage_bis(
                                 befund.get("umgeworfen_bis"), tag))
    except ER.RechnungBlockiert as exc:
        durchlauf.verloren(symbol, "geometrie", str(exc)[:40])
        return
    durchlauf.bestanden(symbol, "geometrie")
    durchlauf.bestanden(symbol, "risikoschicht")

    # --- Stufe: Entscheider - ZAEHLT, verwirft nicht ---
    #
    # DIE FAMILIEN WERDEN HIER GEBRAUCHT, nicht erst in der Mail: sie sind seit
    # 15.1 der Konstellationsschluessel. Deshalb steht die Berechnung jetzt vor
    # dem Entscheider statt darunter - dieselben Werte, eine Stelle.
    kern = FB.werte_aus_reihe([k.high for k in reihe], [k.low for k in reihe],
                              [k.close for k in reihe],
                              [getattr(k, "volume", 0) or 0 for k in reihe],
                              i=idx, tag_vollstaendig=(idx < len(reihe) - 1))
    # DIE KOSTENKLASSE MUSS MIT (17.3). Vorher lief das auf die Vorgabe
    # "krypto" hinaus - bei der ersten Aktie haette der Entscheider mit
    # Krypto-Gebuehren (1,5 % je Seite) statt Boersengebuehren (1 EUR fix
    # + 0,25 % Spread) gerechnet, und der Breakeven waere grob falsch
    # gewesen, ohne dass irgendetwas meldet.
    kosten_r = TB.kosten_r_aus_stop(
        kurs_e, rechnung["stop_eur"], klasse=_kostenklasse(assetklasse),
        position_eur=rechnung["betrag_eur"])
    # DIE EIGENE BILANZ, NICHT EIN LEERES DICT. Bis zum 13.08. stand hier
    # `TB.bewerte({}, ...)` - der Entscheider las eine leere Tabelle und fiel
    # damit IMMER auf die Basisrate zurueck, auch wenn Faelle vorlagen. Zusammen
    # mit dem fehlenden Schreiben (Schritt 1) waren das zwei Luecken in Reihe:
    # nichts wurde gezaehlt, und das Nichts wurde auch nicht gelesen.
    bewertung = TB.bewerte(bilanz or {}, TB.merkmale(
        vola_perzentil=TB._prozent((kern or {}).get("schwankung_perzentil")),
        spanne_perzentil=TB._prozent((kern or {}).get("momentum_perzentil")),
        gleichlauf=TB._band_grob((kern or {}).get("volumen_perzentil"))),
        kosten_r=kosten_r or 0.0, crv=rechnung["crv"])
    if not bewertung["traegt"]:
        durchlauf.verloren(symbol, "entscheider", "traegt sich nicht")
    else:
        durchlauf.bestanden(symbol, "entscheider")

    # --- Die Mail ---
    # UND HIER `faktenblock_quellen` - das zweite Modul ohne Aufrufer.
    zusatz, _fehlt = FQ.abbilden(bc_ein.get("fakten_roh"),
                                 bereich=_bereich(assetklasse, instrument),
                                 position_eur=rechnung["betrag_eur"],
                                 hebel=rechnung.get("hebel"))
    block = FB.baue(_bereich(assetklasse, instrument), kern_werte=kern,
                    zusatz_werte=zusatz, symbol=symbol) if kern else []
    # DIE MAIL ALS BAUPLAN, NICHT ALS FERTIGER TEXT. Die Zeilen der zweiten
    # Meinung entstehen erst, wenn Z.ai geantwortet hat - und darauf wartet
    # die Kette bis zu vier Minuten. Sie danach in einen fertigen String
    # hineinzuflicken hiesse, die Reihenfolge der Abschnitte an zwei Orten zu
    # pflegen; ein Bauplan kennt sie an einem.
    def baue(zweite_zeilen: list) -> tuple:
        return SM.baue_mail(
            symbol=symbol, name=symbol, kurs_eur=kurs_e, instrument=instrument,
            strategie=strategie, rechnung=rechnung, urteil=befund,
            faktenblock=block, modell=modell, zeitpunkt=tag,
            einordnung=TB.satz(bewertung, einstieg=kurs_e,
                               stop=rechnung["stop_eur"],
                               einsatz_eur=rechnung["betrag_eur"])
            + Z1.satz(z1) + list(zweite_zeilen))

    betreff, text = baue([])
    eintrag = {"symbol": symbol, "betreff": betreff, "text": text}
    ergebnis["mails"].append(eintrag)

    # --- Schreiben ----------------------------------------------------------
    #
    # HIER ENTSTEHT DIE SIGNALZEILE - bis zum 13.08. entstand sie NIE. Die
    # Felder wurden gebaut und in `ergebnis` gelegt, geschrieben hat sie
    # niemand. Folge: `trefferbilanz.zaehle()` selektiert
    # `WHERE quelle_kette = 'rollen'` und lieferte dauerhaft {} - der
    # Entscheider rechnete nicht "mit wenig Daten", sondern mit null, und die
    # 34 % waren nie eine geschrumpfte Schaetzung, sondern der unberuehrte
    # Mittelwert.
    if betriebsart == TROCKEN:
        return
    felder = SA.felder_aus_entscheidung(
        befund, fakten=bc_ein, lagebild_id=lagebild_id,
        prompt_stand=getattr(RT, "PROMPT_STAND", "?"), modell=modell,
        eur_je_usd=RE.fx_eur_je_usd(symbol, reihe, idx, db),
        # DIE RECHNUNG MIT - sie traegt den Hebelfaktor, den das Modell nicht
        # nennt und nicht nennen soll.
        rechnung=rechnung,
        # DIE DREI GEMESSENEN FAMILIEN - dieselben Werte, die oben schon in den
        # Faktenblock der Mail gingen. Sie sind das einzige Material fuer den
        # Konstellationsschluessel, das NICHT die Entscheidung wiederholt.
        familien=kern)
    signal_id = SA.schreibe_signal(conn, felder, symbol=symbol)
    eintrag["signal_id"] = signal_id
    ergebnis["signale"].append({"symbol": symbol, "id": signal_id,
                                "felder": felder})

    # --- Zweite Meinung, dann versenden -------------------------------------
    #
    # DIE REIHENFOLGE IST DER GANZE PUNKT: schreiben -> Z.ai -> warten ->
    # Mail bauen -> versenden. Ginge die Mail vorher raus, kehrte der Fund vom
    # 28.07. zurueck - die BTC-SHORT-Mail ohne Gegenpruefungszeilen, obwohl das
    # Urteil zum Versandzeitpunkt vorlag.
    #
    # AUCH IN `probe`, nicht erst in `scharf`. Eine Wartemechanik, die nur im
    # scharfen Betrieb laeuft, ist genau dort zum ersten Mal erprobt, wo ein
    # Fehler eine echte Mail kostet.
    zweite = ZM.hole(faktentext=bc_ein, urteil=befund, zai_client=zai_client)
    if zweite:
        ZM.schreibe(conn, signal_id, zweite)
        eintrag["zweite_meinung"] = zweite
        eintrag["betreff"], eintrag["text"] = baue(ZM.zeilen(zweite))
    if betriebsart == SCHARF and versand is not None:
        versand(eintrag["betreff"], eintrag["text"])


def _schreibe_nein(*, symbol, befund, kurs_e, atr_e, tag, reihe, idx,
                   lagebild_id, instrument, strategie, conn, db, config,
                   modell, ergebnis, module) -> None:
    """Ein NICHTS_TUN als auflösbare Zeile - der Kontrollarm der Messung.

    `ist_reines_llm_halten = 1` ist der Schluessel: `backward_tracking` sucht
    genau danach (Zeile 1192) und loest solche Zeilen ueber das
    Selbst-HALTEN-Schatten-Tracking auf. Die Maschine existiert seit dem
    31.07. - sie bekam nur nie Futter aus der neuen Kette.

    STILL BEI EINEM FEHLSCHLAG. Diese Zeile ist eine Messung, kein Signal - sie
    darf den Lauf unter keinen Umstaenden aufhalten. Wer hier abbricht, verliert
    ein Urteil, das ohnehin schon bezahlt ist."""
    AR, ER, FB, FQ, Z1, RT, RE, SA, SM, TO, TB, ZM, BE, WH = module
    try:
        rechnung = ER.rechne(
            kurs=kurs_e, atr=atr_e,
            risiko_eur=BE.risiko_eur(instrument, strategie, config),
            instrument=instrument,
            betrag_wunsch_eur=BE.einsatz_eur(instrument, strategie, config),
            umgeworfen_preis_eur=befund.get("umgeworfen_preis_eur"),
            ist_short=(befund.get("richtung") == "SHORT"),
            umgeworfen_tage=_tage_bis(befund.get("umgeworfen_bis"), tag))
        kern = FB.werte_aus_reihe(
            [k.high for k in reihe], [k.low for k in reihe],
            [k.close for k in reihe],
            [getattr(k, "volume", 0) or 0 for k in reihe],
            i=idx, tag_vollstaendig=(idx < len(reihe) - 1))
        felder = SA.felder_aus_entscheidung(
            befund, fakten={"asset": symbol}, lagebild_id=lagebild_id,
            prompt_stand=getattr(RT, "PROMPT_STAND", "?"),
            eur_je_usd=RE.fx_eur_je_usd(symbol, reihe, idx, db),
            familien=kern, rechnung=rechnung, modell=modell)
        # DIE ZONEN AUS DER GEGENRECHNUNG. `felder_aus_entscheidung` nimmt sie
        # aus der ANTWORT, und ein NICHTS_TUN nennt keine - deshalb hier aus der
        # Rechnung nachgetragen, in genau den Spalten, die das Tracking liest.
        for feld, wert in (("entry_eur_von", rechnung.get("einstieg_eur")),
                           ("stop_loss_eur_von", rechnung.get("stop_eur")),
                           ("take_profit_eur_von", rechnung.get("ziel_eur"))):
            if wert is not None:
                felder[feld] = wert
        fx = felder.get("fx_eur_je_usd")
        if fx:
            for eur, usd in (("entry_eur_von", "entry_usd_von"),
                             ("stop_loss_eur_von", "stop_loss_usd_von"),
                             ("take_profit_eur_von", "take_profit_usd_von")):
                if felder.get(eur) is not None:
                    felder[usd] = round(float(felder[eur]) / float(fx), 8)
        felder["ist_reines_llm_halten"] = 1
        felder["gate_passed"] = 0        # es ist kein Signal, es ist eine Messung
        kennung = SA.schreibe_signal(conn, felder, symbol=symbol)
        ergebnis.setdefault("nein_gemessen", []).append(
            {"symbol": symbol, "id": kennung})
    except Exception as exc:                                 # noqa: BLE001
        ergebnis.setdefault("nein_fehler", []).append(f"{symbol}: {exc}")


def _frage(client, modell, system_prompt, eingabe, modulname):
    """Der Modellaufruf - in der Form, die die Clients wirklich haben.

    MEINE ERSTE FASSUNG WAR ERFUNDEN: sie rief
    `client.chat(modell=..., system=..., nachricht=...)`. Kein Client dieses
    Projekts hat diese Schnittstelle - sie nehmen eine NACHRICHTENLISTE und
    geben Text zurueck. Der Trockenlauf konnte das nicht finden, weil er
    `_frage()` nie aufruft; es waere erst beim ersten echten Aufruf
    hochgekommen, mit verbrauchtem Kontingent.

    Die Form ist woertlich die von `pruefe_rollenkette.frage()`, die seit dem
    12.08. gegen echte Antworten laeuft. Eine eigene Variante daneben waere
    die naechste Stelle zum Auseinanderlaufen.

    JSON WIRD AUS DEM TEXT GESCHNITTEN, nicht erwartet: Modelle setzen
    gelegentlich einen Satz davor. Fehlt eine Struktur ganz, ist das ein
    Fehler und keine leere Antwort.
    """
    import json

    from agent import llm_schema

    fmt = llm_schema.response_format_fuer(client, modulname)
    roh = client.chat(
        [{"role": "system", "content": system_prompt},
         {"role": "user", "content": json.dumps(eingabe, ensure_ascii=False)}],
        **({"model": modell} if modell else {}), response_format=fmt,
        temperature=0.2)
    text = roh if isinstance(roh, str) else str(roh)
    anfang, ende = text.find("{"), text.rfind("}")
    if anfang < 0 or ende < anfang:
        raise LaufAbgebrochen(
            f"keine JSON-Struktur in der Antwort von {modulname}: {text[:180]}")
    return json.loads(text[anfang:ende + 1])
