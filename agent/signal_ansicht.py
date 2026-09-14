# -*- coding: utf-8 -*-
"""Die Detailansicht eines Signals der ROLLEN-KETTE fuer die Oberflaeche.

⚠️⚠️ SCHRITT 32 (14.09.2026), Befund 2.448 und Nutzerentscheidung
*"Neue Gliederung aus DB-Feldern"*.

DER ANLASS: die Reiter Signale und Hebel zeigten jede Zeile in der
Dreiteilung der ALTEN Kette - ,1. MATHEMATISCH BERECHNET / 2.
LLM-BEWERTUNG (Konfidenz) / 3. KONKLUSION'. Seit dem 15.08. schreibt die
alte Kette nichts mehr; jede angezeigte Zeile ist eine der neuen Kette, und
deren Felder (Konfidenz, Top-5-Gruende, Forecast, Halte-Kriterium,
Risikofaktoren) sind nie gefuellt - bei 2.357 Zeilen kein einziges Mal.
Die GUI zeigte also eine Gliederung voller Striche, und die Mail etwas ganz
anderes.

## WAS HIER STEHT - UND WAS NICHT

Die Abschnitte tragen DIESELBEN Titel wie die Mail (`signal_mail`), damit
beide wiedererkennbar sind. Gezeigt wird nur, was mit dem Signal
GESPEICHERT ist:

    AUF EINEN BLICK        Empfehlung, Richtung, Zone, Stop, Ziel, Betrag
    2. DIE RECHNUNG        Zone, Stop, Ziel, Betrag, Hebel, Liquidation,
                           Verlust am Stop
    3. DIE LAGE DES WERTS  die Lagesaetze, die das MODELL gelesen hat
                           (`facts_json`), und das Umfeld
    5. DIE MODELLE         Urteil, Einwand, Widerlegung, Belege,
                           Gegenpruefung, Z1

⚠️ NICHT GESPEICHERT, und deshalb NICHT nachgebaut: die Bewertung
(Trefferquote und Beitraege), die Gebuehrenhuerden, der Faktenblock, der
Marktvergleich, Termine und Lebendigkeit, die Zeile ,Was dagegen spricht'.
Sie entstehen beim Mailbau aus Eingaben, die spaeter nicht mehr vorliegen -
sie hier neu zu rechnen hiesse, einen zweiten Bauweg zu fuehren, der
auseinanderlaeuft (die Kopierfalle). Die Ansicht SAGT das in ihrer zweiten
Zeile, statt es zu verschweigen.

KEINE RECHNUNG. Jede Zahl ist ein gespeichertes Feld; einzige Ausnahme ist
der Stopabstand in Prozent, eine Division zweier gespeicherter Preise.
"""
from __future__ import annotations

import json

# Was diese Ansicht nicht zeigen kann - der Satz steht oben in jeder Ansicht.
NICHT_GESPEICHERT = ("Bewertung (Trefferquote und Beitraege), Gebuehren, "
                     "Faktenblock, Marktvergleich, Termine")
HERKUNFTSZEILE = ("[AUS DER DATENBANK - nicht die versandte Mail. Nicht "
                  "gespeichert und deshalb nur in der Mail: "
                  + NICHT_GESPEICHERT + "]")


def _feld(signal, name, vorgabe=None):
    if isinstance(signal, dict):
        return signal.get(name, vorgabe)
    return getattr(signal, name, vorgabe)


def ist_rollen_signal(signal) -> bool:
    """Stammt die Zeile aus der Rollen-Kette? Am gespeicherten Feld, nicht am
    Datum - eine Zeitgrenze waere eine Behauptung ueber die Zeit."""
    return str(_feld(signal, "quelle_kette") or "") == "rollen"


def ist_hebel_altbestand(signal) -> bool:
    """Eine Hebelzahl OHNE Hebelgeschaeft - Zeilen vor Paket B.

    Befund 2.446-gui: 55 von 56 Hebelzeilen seit dem 11.09. liegen bei
    1,0-1,2x und stammen aus Laeufen VOR dem Rollout. Seit Paket B schreibt
    die Kette unter 2x keinen Hebel mehr, sondern `instrument = spot`. Die
    Unterscheidung steht also im Datensatz selbst: gesetzter Hebel, aber kein
    Hebel-Topf."""
    return (_feld(signal, "hebel") is not None
            and str(_feld(signal, "instrument") or "") != "hebel")


def _preis(wert) -> str:
    from agent.signal_mail import preis
    return preis(float(wert))


def _eur(wert) -> str:
    from agent.signal_mail import eur
    return eur(float(wert))


def _zone(von, bis) -> str | None:
    if von is None:
        return None
    if bis is None or abs(float(bis) - float(von)) < 1e-12:
        return f"{_preis(von)} EUR"
    return f"{_preis(von)} bis {_preis(bis)} EUR"


def _abschnitt(titel: str, zeilen: list[str], herkunft: str | None = None) -> list[str]:
    from agent.signal_mail import _abschnitt as _mail_abschnitt
    return _mail_abschnitt(titel, zeilen, herkunft)


def zeilen(signal) -> list[str]:
    """Die Ansicht als Zeilen - fuer `ui.detail_panel.render_detail_text`."""
    from agent.signal_mail import (AKTIONEN_MIT_EINSTIEG, BELEG_LEGENDE,
                                   BELEG_ZEICHEN, HERKUNFT, RICHTUNG_TEXT)
    from agent.schreibweise import de

    aktion = str(_feld(signal, "action") or "?")
    ri = str(_feld(signal, "richtung") or "").upper()
    hebel = _feld(signal, "hebel")
    instrument = str(_feld(signal, "instrument") or "")
    ein_von_eur, ein_bis_eur = _feld(signal, "entry_eur_von"), _feld(signal, "entry_eur_bis")
    stop_eur = _feld(signal, "stop_loss_eur_von")
    ziel_von_eur, ziel_bis_eur = (_feld(signal, "take_profit_eur_von"),
                          _feld(signal, "take_profit_eur_bis"))
    betrag_eur = _feld(signal, "position_size_eur")

    stop_rel = None
    try:
        _mitte = (float(ein_von_eur) + float(ein_bis_eur if ein_bis_eur is not None else ein_von_eur)) / 2
        if stop_eur is not None and _mitte > 0:
            stop_rel = abs(float(stop_eur) - _mitte) / _mitte
    except (TypeError, ValueError):
        stop_rel = None
    # ⚠️ DAS VORZEICHEN FOLGT DER RICHTUNG - dieselbe Regel wie in der Mail
    # (2.446-richtung): beim SHORT liegt der Stop UEBER dem Kurs.
    stop_text = None
    if stop_eur is not None:
        stop_text = f"{_preis(stop_eur)} EUR" + (
            f"  ({'+' if ri == 'SHORT' else '-'}{de(100 * stop_rel, 1)} %)"
            if stop_rel is not None else "")

    aus = [HERKUNFTSZEILE, ""]

    # ---- AUF EINEN BLICK -------------------------------------------------
    blick = [f"Empfehlung      {aktion} - Urteil des Modells (Abschnitt 5)"]
    # ⚠️ EINE NEIN-BUCHUNG IST KEINE EMPFEHLUNG. Die Kette schreibt auch
    # Urteile, die an einer spaeteren Stufe haengenbleiben (`gate_passed = 0`)
    # - als Messung. Ohne diese Zeile laese sich ,NACHKAUFEN' wie eine
    # verschickte Empfehlung.
    if not _feld(signal, "gate_passed"):
        blick.append("                ⚠️ NEIN-BUCHUNG - dieses Urteil ging NICHT als "
                     "Empfehlung hinaus, es wird nur gemessen")
    if ri in RICHTUNG_TEXT:
        blick.append("Richtung        " + RICHTUNG_TEXT[ri])
    mit_einstieg = aktion in AKTIONEN_MIT_EINSTIEG
    if mit_einstieg and _zone(ein_von_eur, ein_bis_eur):
        blick.append("Einstiegszone   " + _zone(ein_von_eur, ein_bis_eur))
    if mit_einstieg and stop_text:
        blick.append("Stop            " + stop_text)
    if mit_einstieg and _zone(ziel_von_eur, ziel_bis_eur):
        blick.append("Take-Profit     " + _zone(ziel_von_eur, ziel_bis_eur))
    if mit_einstieg and betrag_eur is not None:
        blick.append(f"Betrag          {_eur(betrag_eur)} EUR - "
                     + (f"Hebel {de(float(hebel), 1)}x"
                        if hebel is not None and instrument == "hebel"
                        else "kein Hebel"))
    blick.append("Topf / Auftrag  "
                 + (instrument or "?") + " / " + str(_feld(signal, "strategie") or "?"))
    aus += _abschnitt("AUF EINEN BLICK", blick)

    # ---- 1. DIE BEWERTUNG ------------------------------------------------
    aus += _abschnitt("1. DIE BEWERTUNG", [
        "Nicht gespeichert - Trefferquote, Beitraege und Gebuehrenhuerden "
        "stehen nur in der versandten Mail."])

    # ---- 2. DIE RECHNUNG -------------------------------------------------
    rechnung = []
    if mit_einstieg:
        if _zone(ein_von_eur, ein_bis_eur):
            rechnung.append("Einstiegszone   " + _zone(ein_von_eur, ein_bis_eur))
        if stop_text:
            rechnung.append("Stop            " + stop_text)
        if _zone(ziel_von_eur, ziel_bis_eur):
            rechnung.append("Take-Profit     " + _zone(ziel_von_eur, ziel_bis_eur))
        if betrag_eur is not None:
            rechnung.append(f"Betrag          {_eur(betrag_eur)} EUR")
        if hebel is not None and instrument == "hebel":
            liq_eur = _feld(signal, "liquidation_etwa_eur")
            rechnung.append(f"Hebel           {de(float(hebel), 1)}x"
                            + (f"  (Liquidation etwa {_preis(liq_eur)} EUR)"
                               if liq_eur is not None else ""))
        elif ist_hebel_altbestand(signal):
            # 2.446-gui: Hebelzahl ohne Hebelgeschaeft - benannt statt gezeigt.
            rechnung.append(f"Hebel           {de(float(hebel), 1)}x gerechnet, "
                            f"aber Topf {instrument or '?'} - Zeile vor Paket B "
                            f"(seit 12.09. wird unter 2x Spot)")
        verlust_eur = _feld(signal, "verlust_am_stop_eur")
        if verlust_eur is not None:
            rechnung.append(f"Am Stop verlieren Sie {_eur(verlust_eur)} EUR.")
    else:
        rechnung.append(f"Kein Einstieg geplant - die Empfehlung lautet {aktion}.")
    aus += _abschnitt("2. DIE RECHNUNG", rechnung, HERKUNFT["rechnung"])

    # ---- 3. DIE LAGE DES WERTS -------------------------------------------
    try:
        fakten = json.loads(_feld(signal, "facts_json") or "{}")
    except (TypeError, ValueError):
        fakten = {}
    lage = [str(z) for z in (fakten.get("stand") or []) if str(z).strip()]
    termin = [str(z) for z in (fakten.get("terminmarkt") or []) if str(z).strip()]
    if termin:
        lage += ([""] if lage else []) + ["Terminmarkt:"] + [f"  {z}" for z in termin]
    umfeld = (fakten.get("marktlage_beurteilung") or {}).get("lage")
    if umfeld:
        lage += ([""] if lage else []) + ["Umfeld:", f"  {umfeld}"]
    if lage:
        aus += _abschnitt("3. DIE LAGE DES WERTS",
                          ["(die Saetze, die das Modell gelesen hat)"] + lage,
                          HERKUNFT["wert"])

    # ---- 5. DIE MODELLE - DAS URTEIL -------------------------------------
    urteil = [f"Aktion: {aktion}"]
    if _feld(signal, "short_reasoning"):
        urteil += ["", str(_feld(signal, "short_reasoning"))]
    if _feld(signal, "gegenargument"):
        urteil += ["", f"Was dagegen spricht: {_feld(signal, 'gegenargument')}"]
    if _feld(signal, "umgeworfen_durch"):
        urteil += ["", f"Die Entscheidung {aktion} waere widerlegt durch: "
                       f"{_feld(signal, 'umgeworfen_durch')}"]
    try:
        belege = json.loads(_feld(signal, "belege_json") or "[]")
    except (TypeError, ValueError):
        belege = []
    if belege:
        n = _feld(signal, "unabhaengige_faktoren")
        urteil += ["", (f"Belege ({len(belege)}, davon {n} unabhaengige Faktoren):"
                        if n else f"Belege ({len(belege)}):"), BELEG_LEGENDE]
        for b in belege:
            urteil.append(f"  {BELEG_ZEICHEN.get(b.get('richtung'), '?')} "
                          f"{b.get('fakt', '')} [{b.get('gewicht', '?')}]")
    if _feld(signal, "zai_gegenpruefung_urteil"):
        # ⚠️ ,ja' HEISST ,ES GIBT EINEN EINWAND' (`zweite_meinung.
        # einwand_liegt_vor`) - das rohe Wort liest sich wie Zustimmung.
        from agent.zweite_meinung import einwand_liegt_vor
        _ew = einwand_liegt_vor(_feld(signal, "zai_gegenpruefung_urteil"))
        urteil += ["", "Gegenpruefung (zweites Modell): "
                   + {True: "EINWAND", False: "kein Einwand"}.get(_ew, "unklar")
                   + (f" - {_feld(signal, 'zai_gegenpruefung_kurzbegruendung')}"
                      if _feld(signal, "zai_gegenpruefung_kurzbegruendung") else "")]
    if _feld(signal, "z1_verletzt"):
        urteil += ["", "⚠️ Treuepruefung Z1 hat angeschlagen - das Modell "
                       "nannte Zahlen, die nicht in seinen Fakten standen."]
    aus += _abschnitt("5. DIE MODELLE - DAS URTEIL", urteil, HERKUNFT["urteil"])
    return aus


def metazeile(signal) -> str:
    """Die Zeile ueber dem Detailtext - OHNE Konfidenz (die neue Kette hat
    keine, 2.390-gui: sie stand als ,Konfidenz: -' da)."""
    from ui.formatting import format_zeitpunkt_lokal

    return (f"Rollen-Kette · Modell: {_feld(signal, 'modell') or '-'} · "
            f"Promptstand: {_feld(signal, 'prompt_stand') or '-'} · "
            f"Berechnet: {format_zeitpunkt_lokal(_feld(signal, 'created_at'))}")
