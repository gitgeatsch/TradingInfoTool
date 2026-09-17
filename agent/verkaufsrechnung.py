# -*- coding: utf-8 -*-
"""Die Verkaufsseite - was tun mit dem, was schon da ist (14.08.2026).

DER FUND, DER DIESES MODUL AUSGELOEST HAT. Im ersten Echtbetrieb fielen 45
Urteile. Elf davon waren Verkaufsseite - und keines hat den Nutzer erreicht:

    HALTEN       24    keine Mail   (richtig)
    REDUZIEREN    9    keine Mail   FALSCH
    KAUFEN        8    Mail
    VERKAUFEN     2    keine Mail   FALSCH
    NACHKAUFEN    2    Mail

Der Grund stand in einer einzigen Zeile: `AKTIONEN_MIT_EINSTIEG` kennt drei
Woerter, und alles andere fiel in `_schreibe_nein()` - gebucht als "reines
LLM-Halten", ohne Mail. **Verkaufen wurde mit Nichtstun in einen Topf
geworfen.**

Bei einem Bestand, der ueber 60 % im Minus steht, ist das die dringendere
Nachricht - nicht der neunte Kaufvorschlag.

DREI KLASSEN STATT ZWEI. Das ist die eigentliche Korrektur:

    Einstieg    KAUFEN, NACHKAUFEN, EROEFFNEN      -> Einstiegsrechnung, Mail
    Ausstieg    REDUZIEREN, VERKAUFEN, SCHLIESSEN  -> DIESES MODUL, Mail
    Nichts      HALTEN, NICHTS_TUN                 -> Schattenbuchung, keine Mail

WARUM NICHT `ausstiegsrechnung.py` - das gibt es doch schon. Es verlangt
`einstieg` UND `stop_original` und rechnet in R. Das passt fuer eine Position,
die aus einem EIGENEN Signal entstanden ist; fuer den echten Spot-Bestand passt
es nicht, denn der hat nach Nutzerangabe **keinen Stop**:

    *"es gibt einen Spot bestand und Hebel bestand"* - und beim Spot ist die
    Positionsgroesse die einzige Risikosteuerung, nicht der Stop.

Ohne Stop gibt es kein R, ohne R keine der drei Aussagen von
`ausstiegsrechnung`. Sie hier zu erzwingen hiesse, eine Zahl zu erfinden, damit
eine Formel rechnet. Dieses Modul rechnet stattdessen mit dem, was wirklich
vorliegt: Menge, Einstandspreis, aktueller Kurs.

WAS ES NICHT TUT: es entscheidet nicht, OB verkauft wird. Das Urteil kommt vom
Modell; hier wird nur ausgerechnet, was es in Stueck und Euro bedeutet.
"""
from __future__ import annotations

# Die Aktionen, die eine BESTEHENDE Position betreffen. Bewusst als Liste des
# Erlaubten, nicht als Ausschluss - genau der Fehler, der am 13.08. schon
# einmal zuschlug (der CRV-Faktor traf `absicherung` mit, weil er ueber
# `!= "hebel"` definiert war).
AKTIONEN_MIT_AUSSTIEG = ("REDUZIEREN", "VERKAUFEN", "SCHLIESSEN",
                         "TEILVERKAUF")

# DIE DRITTE KLASSE: die Position bleibt, ihr HEBEL aendert sich (O-31,
# 15.08.2026).
#
# GEFUNDEN IM TROCKENLAUF ueber beide Instrumente, und der Fund war groesser
# als erwartet. Gesucht war `HEBEL_ERHOEHEN`, das durch beide Listen fiel und
# als "nichts" gebucht wurde - obwohl es Kapital bindet.
#
# DABEI KAM HERAUS, DASS `HEBEL_SENKEN` FALSCH EINSORTIERT WAR. Es stand in der
# Ausstiegsliste und bekam damit den Satz:
#
#     "Verkaufen  0,206667 Stueck - ein Drittel der Position"
#
# Das ist keine fehlende Anweisung, sondern eine FALSCHE. Den Hebel zu senken
# heisst, geliehenes Kapital zurueckzuzahlen - die Stueckzahl bleibt, das
# Risiko sinkt. Wer diesem Satz folgt, verkauft ein Drittel seiner Position und
# hat den Hebel danach immer noch.
#
# BEIDE AENDERN NICHT DIE MENGE, sondern den Kredit:
#
#     HEBEL_ERHOEHEN   mehr Kredit  -> groesseres Risiko, gleiche Stueckzahl
#     HEBEL_SENKEN     Kredit zurueck -> kleineres Risiko, gleiche Stueckzahl
#
# Und beide setzen eine OFFENE POSITION voraus. Ohne sie gibt es keinen Hebel,
# den man aendern koennte - dann ist das Urteil ein Messpunkt, kein Auftrag,
# genau wie ein VERKAUFEN ohne Bestand.
AKTIONEN_MIT_ANPASSUNG = ("HEBEL_ERHÖHEN", "HEBEL_SENKEN")

# Was ein REDUZIEREN bedeutet, wenn das Modell keine Menge nennt.
#
# EIN DRITTEL IST GESETZT, NICHT GEMESSEN, und das steht hier, damit niemand es
# fuer einen Befund haelt. Die Begruendung ist die Umkehrung der Tranche: wer in
# Stufen einsteigt, steigt in Stufen aus. Sobald es eigene Ausstiegsdaten gibt,
# gehoert diese Zahl gemessen.
TEIL_ANTEIL = 1.0 / 3.0

# Unter diesem Gegenwert lohnt kein Teilverkauf - die Gebuehren fressen ihn.
# Bei Krypto sind 1,5 % je Seite bei 20 EUR gerade 60 Cent, aber der Rest der
# Position wird dadurch nicht handhabbarer.
MINDEST_GEGENWERT_EUR = 25.0


def ist_ausstieg(aktion: str | None) -> bool:
    """Wird bei diesem Urteil etwas VERKAUFT?"""
    return str(aktion or "").strip().upper() in AKTIONEN_MIT_AUSSTIEG


def ist_anpassung(aktion: str | None) -> bool:
    """Bleibt die Position und aendert sich nur ihr Hebel?"""
    return str(aktion or "").strip().upper() in AKTIONEN_MIT_ANPASSUNG


def betrifft_bestand(aktion: str | None) -> bool:
    """Braucht dieses Urteil ueberhaupt eine bestehende Position?

    Die eine Frage, die der Lauf stellen muss - beide Klassen setzen einen
    Bestand voraus, und ohne ihn ist das Urteil ein Messpunkt."""
    return ist_ausstieg(aktion) or ist_anpassung(aktion)


def anpassung(*, aktion: str, menge: float, kurs_eur: float,
              hebel_jetzt: float | None = None) -> dict | None:
    """Eine Hebelaenderung - `None`, wenn keine Position offen ist.

    KEINE MENGE, KEIN GEGENWERT. Das ist der ganze Unterschied zum Verkauf und
    der Grund, warum diese Funktion getrennt steht: was sich aendert, ist der
    Kredit, nicht der Bestand. Eine Zahl in Stueck waere hier eine
    Falschaussage."""
    menge = float(menge or 0.0)
    if menge <= 0 or not kurs_eur or kurs_eur <= 0:
        return None
    a = str(aktion or "").strip().upper()
    return {"aktion": a, "richtung": "hoch" if a == "HEBEL_ERHÖHEN" else "runter",
            "menge": menge, "wert_gesamt_eur": menge * float(kurs_eur),
            "hebel_jetzt": float(hebel_jetzt) if hebel_jetzt else None}


def saetze_anpassung(e: dict) -> list[str]:
    """Die Hebelaenderung fuer die Mail."""
    from agent.signal_mail import eur

    hoch = e["richtung"] == "hoch"
    z = [f"Hebel {'ERHOEHEN' if hoch else 'SENKEN'}"
         + (f" - aktuell {e['hebel_jetzt']:.1f}x".replace(".", ",")
            if e.get("hebel_jetzt") else ""),
         f"Die Position bleibt bestehen ({eur(e['wert_gesamt_eur'], 2)} EUR) - "
         + ("es wird zusaetzliches Kapital geliehen."
            if hoch else "ein Teil des geliehenen Kapitals wird zurueckgezahlt."),
         "Die Stueckzahl aendert sich dabei NICHT."]
    if hoch:
        z.append("!! Mehr Hebel heisst naeher an der Liquidation. Vor der "
                 "Ausfuehrung den Liquidationspreis pruefen.")
    return z


def rechne(*, aktion: str, menge: float, kurs_eur: float,
           einstand_eur: float | None = None,
           gestakt: float | None = None) -> dict | None:
    """Was das Urteil in Stueck und Euro bedeutet.

    `None`, wenn nichts zu verkaufen ist. Das ist der Normalfall bei einem
    Symbol, das der Nutzer gar nicht haelt - und dort ist ein VERKAUFEN kein
    Auftrag, sondern eine Aussage ueber die Qualitaet des Urteils. Der Aufrufer
    bucht es dann als Schatten, so wie ein HALTEN.

    DER GESTAKTE TEIL WIRD ABGEZOGEN. Er laesst sich nicht ohne Weiteres
    verkaufen, und eine Empfehlung ueber eine Menge, an die man nicht
    herankommt, ist keine."""
    menge = float(menge or 0.0)
    frei = max(0.0, menge - float(gestakt or 0.0))
    if frei <= 0 or not kurs_eur or kurs_eur <= 0:
        return None

    a = str(aktion or "").strip().upper()
    # ⚠️ S6c HAT HIER BEWUSST NICHTS GEAENDERT. REDUZIEREN faellt in den
    # `else`-Zweig und bekommt TEIL_ANTEIL - genau richtig, es IST der
    # Teilverkauf. Eine Ergaenzung in der oberen Liste waere ein Fehler.
    anteil = 1.0 if a in ("VERKAUFEN", "SCHLIESSEN") else TEIL_ANTEIL
    verkaufsmenge = frei * anteil
    gegenwert = verkaufsmenge * float(kurs_eur)

    aus = {
        "aktion": a,
        "menge_gesamt": menge,
        "menge_frei": frei,
        "menge_verkauf": verkaufsmenge,
        "anteil": anteil,
        "gegenwert_eur": gegenwert,
        "wert_gesamt_eur": frei * float(kurs_eur),
        "zu_klein": gegenwert < MINDEST_GEGENWERT_EUR,
    }
    if gestakt:
        aus["gestakt"] = float(gestakt)

    # DAS ERGEBNIS DER POSITION, wenn wir es kennen. Es steht in der Mail,
    # weil es die Frage beantwortet, die der Nutzer zuerst stellt - und NICHT,
    # weil es die Entscheidung begruenden soll. Ein Verlust ist kein Grund zu
    # halten und kein Grund zu verkaufen; er ist die Ausgangslage.
    if einstand_eur and einstand_eur > 0:
        aus["einstand_eur"] = float(einstand_eur)
        aus["ergebnis_eur"] = (float(kurs_eur) - float(einstand_eur)) * frei
        aus["ergebnis_prozent"] = 100.0 * (float(kurs_eur) / float(einstand_eur) - 1.0)
        aus["realisiert_eur"] = ((float(kurs_eur) - float(einstand_eur))
                                 * verkaufsmenge)
    return aus


def gesperrt_durch_staking(*, aktion: str, menge: float, kurs_eur: float,
                           gestakt: float | None = None,
                           einstand_eur: float | None = None) -> dict | None:
    """Die DRITTE Klasse: es gibt die Position, sie ist nur nicht frei.

    ⚠️⚠️ WARUM ES DIESE FUNKTION GIBT (Schritt 48a, 12.09.2026). `rechne()`
    gibt `None` zurueck, sobald `frei = menge - gestakt` auf null faellt - und
    das ist RICHTIG: eine Empfehlung ueber eine Menge, an die man nicht
    herankommt, ist keine. Der Aufrufer machte daraus aber SCHWEIGEN, und
    zwar fuer beide Faelle:

        ohne Bestand         es gibt nichts zu verkaufen   -> Schweigen ist richtig
        vollstaendig gestakt es GIBT die Position          -> Schweigen verschweigt
                                                              eine Handlung

    Der Unterschied steht seit dem 17.08. im Wortlaut in `rollen_lauf`
    (*"ZWEI SEHR VERSCHIEDENE GRUENDE, EIN WORT"*) - gezogen wurde die
    Konsequenz nie. GEMESSEN an sieben Tagen: ALLE 25 stummen Faelle lauteten
    "vollstaendig gestakt", KEIN einziger "ohne Bestand". Der Nutzer kann
    entstaken; er erfuhr nur nichts davon.

    ⚠️ WAS DIESE FUNKTION NICHT TUT: sie erzeugt KEINEN Verkaufsauftrag. Die
    Menge ist nicht verfuegbar, und daran aendert ein Hinweis nichts. Sie
    liefert genau das, was fehlt - die Information, dass eine Sperre zwischen
    dem Urteil und der Handlung steht.

    `None`, wenn nichts gesperrt ist: kein Bestand, kein Staking, oder es
    bleibt freie Menge uebrig (dann hat `rechne()` einen Auftrag geliefert).
    """
    menge = float(menge or 0.0)
    g = float(gestakt or 0.0)
    if menge <= 0 or g <= 0 or not kurs_eur or kurs_eur <= 0:
        return None
    # ⚠️ NUR DIE VOLLSTAENDIGE SPERRE. Bleibt etwas frei, gibt es einen
    # richtigen Auftrag - dann steht das Staking dort schon als `gestakt`.
    if menge - g > 1e-12:
        return None

    aus = {
        "aktion": str(aktion or "").strip().upper(),
        "menge_gesamt": menge,
        "gestakt": g,
        "wert_gesamt_eur": menge * float(kurs_eur),
        "gesperrt": "staking",
    }
    if einstand_eur and einstand_eur > 0:
        aus["einstand_eur"] = float(einstand_eur)
        aus["ergebnis_prozent"] = 100.0 * (float(kurs_eur)
                                           / float(einstand_eur) - 1.0)
    return aus


def saetze(e: dict) -> list[str]:
    """Die Rechnung in der Form, in der sie in die E-Mail gehoert.

    ABSOLUTE ZAHLEN VOR RELATIVEN - dieselbe Regel wie beim Einstieg
    (Nutzervorgabe 12.08.): erst wieviel Stueck und wieviel Euro, dann der
    Prozentsatz."""
    from agent.signal_mail import eur, preis

    m = e["menge_verkauf"]
    # Mengen sind keine Kurse: bei 12.000 Stueck sind Nachkommastellen Unsinn,
    # bei 0,004 BTC sind sie die ganze Information.
    menge_txt = (f"{m:,.0f}".translate(str.maketrans(",.", ".,"))
                 if m >= 100 else f"{m:,.6f}".translate(str.maketrans(",.", ".,")))
    z = []
    if e["anteil"] >= 1.0:
        z.append(f"Verkaufen        die GANZE Position - {menge_txt} Stueck "
                 f"zu etwa {preis(e['gegenwert_eur'] / e['menge_verkauf'])} EUR")
    else:
        z.append(f"Verkaufen        {menge_txt} Stueck - ein Drittel der "
                 f"Position (gesetzt, nicht gemessen)")
    z.append(f"Gegenwert        {eur(e['gegenwert_eur'], 2)} EUR "
             f"von {eur(e['wert_gesamt_eur'], 2)} EUR Gesamtwert")
    if e.get("gestakt"):
        z.append(f"                 (der gestakte Teil ist abgezogen - "
                 f"er ist nicht frei verfuegbar)")
    if "ergebnis_prozent" in e:
        vz = "+" if e["ergebnis_eur"] >= 0 else ""
        z.append(f"Stand            {vz}{eur(e['ergebnis_eur'], 2)} EUR "
                 f"({vz}{eur(e['ergebnis_prozent'], 1)} %) auf die freie Menge")
        vzr = "+" if e["realisiert_eur"] >= 0 else ""
        z.append(f"Davon realisiert {vzr}{eur(e['realisiert_eur'], 2)} EUR "
                 f"bei diesem Verkauf")
    if e.get("zu_klein"):
        z.append(f"!! Der Gegenwert liegt unter {eur(MINDEST_GEGENWERT_EUR, 0)} "
                 f"EUR - die Gebuehren stehen in keinem Verhaeltnis. Entweder "
                 f"ganz oder gar nicht.")
    return z


def _rang(p: dict) -> tuple:
    """Wonach die Sammelmail sortiert. NICHT nach Gegenwert.

    KORREKTUR 14.08. NACH DEM NACHLESEN. Meine erste Fassung sortierte nach
    Euro. Die dokumentierte Regel sortiert nach DRINGLICHKEIT
    (`backward_tracking`, Zeile 4930):

        "Dringlichstes zuerst: SCHLIESSEN, dann STOP NACHZIEHEN, dann der Rest
         - NICHT nach Buchgewinn. Der groesste ungesicherte Gewinn ist nicht
         automatisch der dringendste Fall."

    Dieselbe Logik gilt hier. Ein VERKAUFEN ueber eine kleine Position ist
    dringender als ein REDUZIEREN ueber eine grosse: das eine sagt "raus", das
    andere "weniger davon". Der Gegenwert entscheidet nur noch INNERHALB
    derselben Dringlichkeit."""
    v = p["verkauf"]
    # 0 = die deterministische Fuehrung sagt ebenfalls "schliessen" - das ist
    #     der einzige Fall, in dem sich beide Ebenen einig sind
    # 1 = ganze Position raus
    # 2 = Teilverkauf
    # EINE HEBELAENDERUNG HAT KEINEN `anteil` - sie verkauft nichts. Sie steht
    # hinter den Verkaeufen, weil sie die Position nicht aufloest: wer beides
    # in einer Mail hat, muss zuerst wissen, was rausgeht.
    if "anteil" not in v:
        return (3, -float(v.get("wert_gesamt_eur") or 0.0))
    stufe = 1 if v["anteil"] >= 1.0 else 2
    if str((p.get("fuehrung") or {}).get("empfehlung", "")).startswith("SCHLIESSEN"):
        stufe = 0
    return (stufe, -v["gegenwert_eur"])


def stumme_bestaende(conn, mindesttage: int | None = None,
                     assetklasse: str = "krypto") -> list:
    """Gehaltene Positionen, die die Kette NICHT bewerten kann.

    ⚠️⚠️ WARUM ES DIESE FUNKTION GIBT (Schritt 51, 13.09.2026). Drei
    gehaltene Werte - ASTER, MON, CANTON - haben eine Kursreihe, die
    kuerzer ist als die Mindestlaenge. Die Kette ist zu ihnen deshalb
    STUMM: kein Nachkauf, kein Verkauf, keine Begruendung. Gesucht
    wurde in `agent/` und `ui/` - es gab dafuer keine einzige Zeile.
    Der Nutzer erfuhr von der Luecke nur, wenn er die Pruefsuite las.

    ⚠️ DIE QUELLE IST `holdings`, NICHT DIE SYMBOLE DES LAUFS - wer die
    nimmt, sieht genau die Werte nicht, um die es geht.

    ⚠️⚠️ RICHTIGSTELLUNG 14.09. (Review): hier stand, CANTON stehe ,nicht
    in der Watchlist'. Das stimmt nicht (config.yaml fuehrt es), und der
    Code UEBERSPRINGT jeden Bestand ohne Watchlist-Eintrag (`_w is None`,
    weiter unten) - er braucht die Assetklasse aus der Watchlist. Ein
    gehaltener Wert AUSSERHALB der Watchlist bleibt also weiterhin still:
    das ist Planpunkt A2 / Befund 2.450-neu, nicht hier geloest.

    ⚠️ DIE GRENZE KOMMT AUS `lade_messreihen.MIN_KERZEN`, importiert
    statt abgeschrieben - es ist dieselbe Grenze, an der eine Reihe beim
    Laden verworfen wird, und zwei Kopien liefen frueher oder spaeter
    auseinander.

    ⚠️⚠️ UND NUR KRYPTO. Das Kriterium ist die USD-Kursreihe in
    `price_history_ohlc` - Aktien, ETFs und Rohstoffe stehen dort gar
    nicht, sie werden ueber yfinance gefuehrt. Die erste Fassung ohne
    Klassenfilter meldete 12 von 28 Bestaenden, davon acht falsch.

    ⚠️ CASH-AEQUIVALENTE FALLEN HERAUS. EURCV braucht einen PREIS
    fuer die Cash-Quote, aber keine Bewertung (`ist_cash_aequivalent`).

    ⚠️ KEINE SYMBOLLISTE IM CODE. Gefiltert wird ueber
    EIGENSCHAFTEN, nicht ueber Namen - eine Ausnahmeliste waere die
    naechste Stelle, die niemand pflegt.

    Rueckgabe je Wert: symbol, tage, grenze, fehlend, menge, gestakt.
    """
    try:
        from lade_messreihen import MIN_KERZEN as _MIN
    except Exception:                                        # noqa: BLE001
        _MIN = 400
    grenze = int(mindesttage or _MIN)
    try:
        import config as _cfg
        _wl = {str(getattr(a, "symbol", "") or "").upper(): a
               for a in _cfg.get_watchlist()}
    except Exception:                                        # noqa: BLE001
        _wl = {}
    # ⚠⚠ NUR FUER KLASSEN MIT USD-KURSREIHE. Aktien, ETFs und
    # Rohstoffe stehen nicht in `price_history_ohlc` - dort waere die
    # Zahl 0 fuer JEDEN Wert und die Meldung reines Rauschen.
    if str(assetklasse or "").lower() != "krypto":
        return []
    aus = []
    try:
        zeilen = conn.execute(
            "SELECT symbol, quantity, staked_quantity FROM holdings "
            "WHERE quantity > 0").fetchall()
    except Exception:                                        # noqa: BLE001
        return []
    for r in zeilen:
        sym = str((r["symbol"] if hasattr(r, "keys") else r[0]) or "").upper()
        if not sym:
            continue
        _w = _wl.get(sym)
        if _w is None:
            continue
        # ⚠️ KLASSENREIN: die Sammelmail geht JE Assetklasse raus -
        # Kryptowerte im Aktienlauf zu nennen waere derselbe Fehler wie
        # der Aktienbestand in der Krypto-Mail (siehe rollen_lauf).
        if (str(getattr(_w, "assetklasse", "") or "").lower()
                != str(assetklasse or "").lower()):
            continue
        if getattr(_w, "ist_cash_aequivalent", False):
            continue
        try:
            tage = conn.execute(
                "SELECT COUNT(DISTINCT date) FROM price_history_ohlc "
                "WHERE UPPER(symbol)=? AND currency='USD'", (sym,)
            ).fetchone()[0] or 0
        except Exception:                                    # noqa: BLE001
            continue
        if tage >= grenze:
            continue
        aus.append({
            "symbol": sym,
            "tage": int(tage),
            "grenze": grenze,
            "fehlend": grenze - int(tage),
            "menge": (r["quantity"] if hasattr(r, "keys") else r[1]) or 0.0,
            "gestakt": (r["staked_quantity"] if hasattr(r, "keys") else r[2]) or 0.0,
        })
    # ⚠️ DER KUERZESTE ZUERST - er ist am laengsten stumm.
    return sorted(aus, key=lambda x: x["tage"])


def sammel_mail(alle: list, modell: str | None = None,
                zeitpunkt: str | None = None,
                positionen: list | None = None,
                gesperrt: list | None = None,
                stumm: list | None = None,
                gruppe: str | None = None) -> tuple | None:
    """EINE Mail fuer alle Ausstiege eines Laufs. `None`, wenn keiner anfiel.

    NUTZEREINWAND 14.08., NOCH WAEHREND DIESER UMBAU LIEF: *"45 Signale sind
    durchgekommen - 9 Spot, Rest irgendwas z.B. Verkaufen - das ist zu viel."*

    Er hat recht, und meine erste Fassung hat es SCHLIMMER gemacht: elf
    Einzelmails fuer die Verkaufsseite waeren zu den zehn Kaufmails
    dazugekommen. Einundzwanzig Mails aus einem Lauf - und die Verkaufsseite
    ist genau die, die man nicht uebersehen darf.

    DAS PROJEKT KENNT DIE ANTWORT SCHON. `ausstiegsrechnung.sammel_mail()`
    schreibt sie seit dem 13.08. auf:

        "Wer fuer eine nie eroeffnete Position geweckt wird, hoert nach der
         dritten Mail auf hinzusehen."

    Deshalb hier dieselbe Form: ein Ueberblick fuer den ganzen Lauf, nach
    Gegenwert sortiert - was am meisten Geld bewegt, steht oben. Die
    Einstiegsmails bleiben einzeln; sie sind seltener und tragen eine
    vollstaendige Planung, die sich nicht buendeln laesst.

    WARUM NICHT `ausstiegsrechnung.sammel_mail` DIREKT: die rechnet in R und
    verlangt Einstieg und Originalstop. Der Spot-Bestand hat keinen Stop -
    siehe Modulkopf.
    """
    from agent.signal_mail import eur, preis

    # ⚠️ AUCH OHNE EINEN EINZIGEN AUFTRAG (Schritt 48a): wenn alle Urteile an
    # der Staking-Sperre haengen, ist genau DAS die Nachricht. Vorher fiel
    # der ganze Lauf hier auf `None` und der Nutzer erfuhr nichts.
    # ⚠️ `stumm` ALLEIN LOEST KEINE MAIL AUS. Eine Mail, die nur
    # sagt ,zu drei Werten kann ich nichts sagen', kaeme taeglich und
    # ohne Anlass - das ist genau der Andrang, gegen den die
    # Sammelmail gebaut wurde. Sie faehrt mit, wenn ohnehin eine geht.
    if not alle and not gesperrt:
        return None
    posten = sorted(alle, key=_rang)
    # NUR VERKAEUFE ZAEHLEN IN DIE SUMME. Eine Hebelaenderung bewegt kein Geld
    # aus der Position heraus - sie in den Gegenwert einzurechnen wuerde eine
    # Zahl erzeugen, die niemand irgendwo wiederfindet.
    verkaeufe = [p for p in posten if "anteil" in p["verkauf"]]
    anpassungen = [p for p in posten if "anteil" not in p["verkauf"]]
    summe = sum(p["verkauf"]["gegenwert_eur"] for p in verkaeufe)
    ganz = sum(1 for p in verkaeufe if p["verkauf"]["anteil"] >= 1.0)

    teile = []
    if verkaeufe:
        teile.append(f"{len(verkaeufe)} Positionen zum Verkauf vorgeschlagen - "
                     f"{eur(summe, 2)} EUR Gegenwert")
    if anpassungen:
        teile.append(f"{len(anpassungen)} Hebelaenderung"
                     + ("en" if len(anpassungen) > 1 else "")
                     + " - die Position bleibt bestehen")
    kopf = teile
    if zeitpunkt or modell:
        kopf.append(" · ".join(x for x in (zeitpunkt,
                                           f"Modell {modell}" if modell else None)
                               if x))
    # ⚠️ DER SATZ GILT DEN AUFTRAEGEN. Bei einem Lauf, in dem ALLES an der
    # Staking-Sperre haengt, gibt es nichts auszufuehren - dann waere
    # "Ausfuehrung manuell" eine Anweisung ins Leere (Schritt 48a).
    if alle:
        kopf += ["",
                 "DIES IST KEINE GEWINNMITNAHME. Das Modell haelt diese Positionen",
                 "fuer schwaecher als die Alternative - mehr sagt es nicht.",
                 "Ausfuehrung manuell ueber die Bitpanda-App.", ""]
    else:
        kopf += ["",
                 "KEIN AUSFUEHRBARER AUFTRAG in diesem Lauf - alle Urteile",
                 "haengen an der Staking-Sperre. Siehe unten.", ""]

    if gesperrt:
        kopf.insert(0, "%d Position%s mit Urteil, aber GESPERRT durch Staking"
                    % (len(gesperrt), "en" if len(gesperrt) > 1 else ""))
    # ⚠️ BEREICH OHNE GEMESSENE BEWERTUNG (17.09.2026, Schritt 59 Phase
    # 0.7/0.10, Nutzerentscheidung D4): Aktien-, Rohstoff-, Themen-ETF- und
    # Absicherungs-Verkaufsvorschlaege waren von Krypto nicht zu unterscheiden.
    from agent import assetklassen as _AKV
    _bereich_nv = (_AKV.anzeigename(gruppe)
                   if gruppe and _AKV.nicht_vermessen(gruppe) else None)
    if _bereich_nv:
        kopf.insert(0, "Bereich %s – ohne gemessene Bewertung" % _bereich_nv)
    zeilen = list(kopf)
    if alle:
        zeilen += ["--- WAS ZU TUN IST ---"]
    for p in posten:
        v = p["verkauf"]
        if "anteil" not in v:
            # HEBELAENDERUNG - keine Menge, kein Gegenwert. Sie in die
            # Verkaufsspalten zu pressen waere genau die Falschaussage, wegen
            # der diese Klasse getrennt wurde.
            richtung = "HOCH" if v["richtung"] == "hoch" else "RUNTER"
            zeile = (f"{p['symbol']:<10} {'HEBEL ' + richtung:<11} "
                     f"{'Position bleibt':<12} "
                     f"{eur(v['wert_gesamt_eur'], 2):>10} EUR")
            if v.get("hebel_jetzt"):
                zeile += f"   aktuell {v['hebel_jetzt']:.1f}x".replace(".", ",")
            zeilen.append(zeile)
            continue
        art = "GANZ" if v["anteil"] >= 1.0 else "ein Drittel"
        zeile = f"{p['symbol']:<10} {v['aktion']:<11} {art:<12} " \
                f"{eur(v['gegenwert_eur'], 2):>10} EUR"
        if "ergebnis_prozent" in v:
            vz = "+" if v["ergebnis_prozent"] >= 0 else ""
            zeile += f"   Stand {vz}{eur(v['ergebnis_prozent'], 1)} %"
        if v.get("zu_klein"):
            zeile += "   !! zu klein fuer einen Teilverkauf"
        zeilen.append(zeile)
        # DIE ZWEITE EBENE IN DERSELBEN ZEILE - der eigentliche Grund fuer
        # diesen Umbau. Fuer BTC liefen am 14.08. zwei Ausstiegswege parallel:
        # die deterministische Fuehrung (Trailing, taeglich 7:15) und dieses
        # Modellurteil aus dem 15-Minuten-Lauf. Der Nutzer haette zwei Mails
        # mit zwei Aussagen zum selben Symbol bekommen und keine Angabe,
        # welche gilt.
        #
        # SIE WIDERSPRECHEN EINANDER NICHT - sie beantworten verschiedene
        # Fragen ("gibt die Position Gewinn zurueck" gegen "traegt die These
        # noch"). Genau deshalb muessen sie nebeneinander stehen: getrennt
        # gelesen sehen sie aus wie zwei Meinungen, zusammen sind sie zwei
        # Befunde.
        f = p.get("fuehrung") or {}
        if f:
            teil = [f"Fuehrung: {f['empfehlung']}"] if f.get("empfehlung") else []
            if f.get("mfe_r") is not None:
                teil.append(f"hoechster Stand {f['mfe_r']:+.2f} R".replace(".", ","))
            if f.get("stop_neu") is not None:
                teil.append(f"Stop nachziehen auf {preis(f['stop_neu'])}")
            if teil:
                zeilen.append("           " + " · ".join(teil))

    # ---- SCHRITT 48a: WAS GESPERRT IST (12.09.2026) ---------------------
    #
    # ⚠️ EIGENER ABSCHNITT, NICHT IN DER AUFTRAGSLISTE. Hier steht kein
    # Auftrag - die Menge ist nicht verfuegbar. Sie zwischen die
    # ausfuehrbaren Zeilen zu mischen waere genau die Falschaussage, wegen
    # der schon die Hebelaenderungen getrennt wurden.
    #
    # GEMESSEN, warum es diesen Abschnitt gibt: in sieben Tagen fielen 25
    # Urteile still an dieser Sperre - 22 REDUZIEREN, 3 VERKAUFEN, und der
    # Nutzer erfuhr von keinem einzigen.
    if gesperrt:
        zeilen += ["", "--- GESPERRT: DIE MENGE IST GESTAKT ---",
                   "Hier gibt es ein Urteil, aber keinen ausfuehrbaren "
                   "Auftrag.",
                   "Die Position besteht - sie ist nur nicht frei "
                   "verkaeuflich.",
                   "Wer handeln will, muss zuerst entstaken "
                   "(Bitpanda-App).", ""]
        # ⚠️ NUTZERANGABE 12.09.2026, KEINE MESSUNG: *"bis auf ETH ist ein
        # Unstaken der Assets grundsaetzlich kurzfristig moeglich"*. Meine
        # erste Fassung schrieb pauschal "das dauert" - das haette die Sperre
        # groesser aussehen lassen, als sie ist, und genau davon haengt ab,
        # ob der Nutzer ueberhaupt handelt. Die Angabe steht als Angabe da,
        # nicht als gemessene Frist.
        if any(str(g.get("symbol") or "").upper() == "ETH" for g in gesperrt):
            zeilen += ["Nach Ihrer Angabe ist Entstaken kurzfristig moeglich "
                       "- ausser bei ETH.", ""]
        else:
            zeilen += ["Nach Ihrer Angabe ist Entstaken hier kurzfristig "
                       "moeglich.", ""]
        for g in sorted(gesperrt,
                        key=lambda x: -(x["gesperrt"].get("wert_gesamt_eur") or 0)):
            v = g["gesperrt"]
            zeile = (f"{g['symbol']:<10} {v['aktion']:<11} "
                     f"{'gestakt':<12} "
                     f"{eur(v['wert_gesamt_eur'], 2):>10} EUR")
            if "ergebnis_prozent" in v:
                vz = "+" if v["ergebnis_prozent"] >= 0 else ""
                zeile += f"   Stand {vz}{eur(v['ergebnis_prozent'], 1)} %"
            zeilen.append(zeile)
        zeilen += ["",
                   "⚠️ Das ist KEINE Handlungsempfehlung, sondern eine "
                   "Information:",
                   "   ob sich das Entstaken lohnt, sagt diese Zeile nicht.", ""]

    # ---- ⚠️⚠️ STUMM: GEHALTEN, ABER NICHT BEWERTBAR (Schritt 51) -------
    #
    # Nutzerentscheidung 13.09.2026: *"ja Mailzeile fuer alle drei"* -
    # also fuer jede gehaltene Position ohne ausreichende Kursreihe.
    #
    # ⚠️ WARUM EIN EIGENER ABSCHNITT: hier gibt es NICHT EINMAL ein
    # Urteil. Bei `gesperrt` existiert eines und ist nur nicht
    # ausfuehrbar; hier fehlt die Grundlage. Beides zu mischen waere
    # dieselbe Falschaussage, wegen der die Sperre schon getrennt wurde.
    if stumm:
        zeilen += ["", "--- STUMM: GEHALTEN, ABER NICHT BEWERTBAR ---",
                   "Zu diesen Positionen sagt die Kette NICHTS - weder "
                   "halten noch verkaufen.",
                   "Der Grund ist die Datenlage, nicht das Urteil: die "
                   "Kursreihe ist zu kurz.", ""]
        for x in stumm:
            zeile = (f"{x['symbol']:<10} {x['tage']:>4} von "
                     f"{x['grenze']} Tagen   es fehlen "
                     f"{x['fehlend']:>3}")
            if x.get("gestakt"):
                zeile += "   (gestakt)"
            zeilen.append(zeile)
        zeilen += ["",
                   "⚠️ Das ist KEIN Mangel der Kette und keine Nachlaessigkeit:",
                   "   es sind junge Werte, ihre Reihe IST vollstaendig.",
                   "   Keine Quelle macht sie laenger - nur Zeit.", ""]

    # ---- SCHRITT 7: DIE POSITIONSFUEHRUNG (01.09.2026) ------------------
    #
    # ⚠️ `agent/positionsfuehrung.py` war seit dem 27.08. gebaut und stand
    # in der Toten-Liste der Modulkarte - kein Betriebsaufrufer. Damit war
    # die Nutzerfestlegung vom 26.08. nie erfuellt:
    #
    #     *„eine Position bleibt eine Position - hier sollte auch der
    #      Verlust sichtbar sein und somit ein Break-even"*
    #
    # DIE LUECKE, DIE SIE SCHLIESST. Am NB-Stand vom 26.08.: 266 offene
    # Signale auf 44 Symbole, 37 Symbole MEHRFACH gefuehrt, 222
    # ueberzaehlige Fuehrungen (83 %). BIO stand 21x, BTC 17x. Vierzehn
    # Symbole trugen am selben Tag verschiedene Handlungen - HYPE gleich-
    # zeitig NACHKAUFEN und REDUZIEREN. Das ist kein Meinungsstreit des
    # Modells, sondern eine Buchhaltungsfrage: die Ausstiegspruefung laeuft
    # ueber SIGNALE, der Nutzer haelt aber EINE Position mit EINEM Einstand.
    #
    # ⚠️ SIE STEHT NEBEN DEN VORSCHLAEGEN, NICHT AN IHRER STELLE. Die
    # Vorschlaege sagen, was zu TUN ist; die Fuehrung sagt, was man HAT.
    # Dieselbe Begruendung wie bei der zweiten Ebene oben ("getrennt
    # gelesen sehen sie aus wie zwei Meinungen, zusammen sind sie zwei
    # Befunde").
    #
    # ⚠️ UND SIE ERFINDET KEIN R. Eine Spot-Position hat nach Nutzerangabe
    # keinen Stop, also kein R und keinen sinnvollen MFE. Was sie hat, ist
    # ein Einstand - und daraus Gewinn/Verlust in Euro und Prozent. Genau
    # das steht hier und nichts darueber hinaus (N-11).
    if positionen:
        zeilen += ["", "--- WAS SIE HALTEN (eine Zeile je Position) ---"]
        for _pz in positionen:
            zeilen += list(_pz)

    if posten:
        zeilen += ["", "--- WARUM ---"]
        for p in posten:
            zeilen.append(f"{p['symbol']}: "
                          f"{p.get('begruendung') or '(keine Begruendung)'}")

    kern = []
    if verkaeufe:
        kern.append(f"{len(verkaeufe)} Verkaufsvorschlaege ({eur(summe, 0)} EUR"
                    + (f", davon {ganz} ganz" if ganz else "") + ")")
    if anpassungen:
        kern.append(f"{len(anpassungen)}x Hebel aendern")
    # ⚠️ DIE GESPERRTEN GEHOEREN IN DEN BETREFF (Schritt 48a). Ohne sie hiess
    # die Mail bei einem reinen Sperrlauf "TradingInfoTool: " - ein leerer
    # Betreff ist schlimmer als keine Mail, er wird ungelesen weggeklickt.
    if gesperrt:
        kern.append("%dx gestakt - Urteil ohne Auftrag" % len(gesperrt))
    if stumm:
        kern.append("%dx stumm - zu kurze Kursreihe" % len(stumm))
    betreff = "TradingInfoTool: " + ", ".join(kern)
    if _bereich_nv:
        betreff += " · %s" % _bereich_nv
    return betreff, "\n".join(zeilen)
