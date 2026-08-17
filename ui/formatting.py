"""Gemeinsame Zahlenformatierung fuer Preis-/Wertanzeigen (nie wissenschaftliche Notation).
Staleness-Erkennung (P-10) lebt in staleness.py (Domaenenlogik, auch vom Agent
gebraucht) - hier nur re-exportiert, damit bestehende Imports unveraendert bleiben."""
from __future__ import annotations

from datetime import datetime, timezone

from staleness import format_price_age, is_history_stale, is_price_stale

__all__ = [
    "format_money", "format_price_age", "is_history_stale", "is_price_stale",
    "format_risikofaktoren_lines", "RISIKOFAKTOREN_LEGENDE",
    "format_fazit_lines", "format_zai_gegenpruefung_lines",
    "classify_detail_line", "render_detail_html", "format_zeitpunkt_lokal",
]


# Aktionen, fuer die ueberhaupt Risikofaktoren berechnet werden - identisch zu
# agent/krypto/risk_gate.py::_BUY_ACTIONS. Bewusst hier gespiegelt statt
# importiert: ui/ soll nicht von agent/ abhaengen.
_RISIKOFAKTOREN_KAUF_AKTIONEN = ("KAUFEN", "NACHKAUFEN")
_HEDGE_SYMBOLE_FUER_HINWEIS = ("3QSS", "DBPK")


def risikofaktoren_hinweis(signal, faktoren_text: str) -> str:
    """Was steht in Abschnitt 3, wenn keine Risikofaktoren vorliegen?

    ANLASS (Nutzer-Beobachtung 2026-08-06): "es werden keine strukturierten
    Risikofaktoren mehr uebermittelt". Nachgemessen an 276 Signalen seit dem
    04.08. - es ist KEIN Datenverlust und keine Regression, sondern die
    Meldung war irrefuehrend. Drei verschiedene Sachverhalte trugen denselben
    Satz "Keine strukturierten Risikofaktoren verfuegbar", und "verfuegbar"
    liest sich wie "die Daten fehlen":

      1. HALTEN/VERKAUFEN (239 von 276). compute_risikofaktoren() steigt bei
         allem ausser KAUFEN/NACHKAUFEN frueh aus - die Faktorenliste ist als
         Pruefung einer KAUFIDEE gebaut. Ohne Kaufidee gibt es nichts zu
         pruefen; das ist kein Mangel, sondern die Definition.
      2. Hedge-Instrumente (8 von 276). agent/hedge/pipeline.py nutzt einen
         eigenen _post_check_hedge() und ruft compute_risikofaktoren() gar
         nicht auf - fuer ein Absicherungs-Overlay sind die Faktoren auch
         inhaltlich andere (siehe ist_hedge_instrument()-Docstring). Das ist
         eine echte, offene Luecke - und sie gehoert benannt, nicht als
         "nicht verfuegbar" getarnt.
      3. Alles andere - dann fehlen die Daten tatsaechlich.

    Der Unterschied ist nicht kosmetisch: Fall 1 heisst "alles in Ordnung,
    nichts zu berichten", Fall 3 heisst "hier ist etwas kaputt". Ein Satz fuer
    beide macht den einen unlesbar und den anderen unsichtbar.
    """
    if faktoren_text:
        return faktoren_text
    symbol = getattr(signal, "symbol", None)
    if symbol in _HEDGE_SYMBOLE_FUER_HINWEIS:
        return ("Fuer Absicherungs-Instrumente werden derzeit keine Risikofaktoren "
                "berechnet - offener Punkt, kein Datenfehler.")
    aktion = getattr(signal, "original_action", None) or getattr(signal, "action", None)
    if aktion and aktion not in _RISIKOFAKTOREN_KAUF_AKTIONEN:
        return (f"Keine Risikofaktoren - die Konklusion prueft eine KAUFIDEE, und die "
                f"Empfehlung lautet {aktion}. Kein Veto ausgeloest, nichts zu berichten.")
    return "Keine strukturierten Risikofaktoren verfügbar."


def format_money(value: float | None) -> str:
    if value is None:
        return "-"
    if abs(value) >= 1:
        return f"{value:,.2f}"
    return f"{value:,.8f}"


def format_zeitpunkt_lokal(iso_timestamp: str | None) -> str:
    """BUGFIX (2026-07-21, Nutzer-Fund): "Berechnet: ..." in den Signal-E-Mails
    zeigte den rohen UTC-Zeitstempel aus der DB (`signal.created_at`) OHNE
    Umrechnung auf lokale Zeit, waehrend der E-Mail-Client (Gmail) den
    Empfangszeitpunkt ganz normal lokal anzeigt - das erweckte den falschen
    Eindruck einer ~2-Stunden-Verzoegerung zwischen Berechnung und Versand
    (CEST = UTC+2), obwohl beide Zeitpunkte nur Sekunden auseinanderlagen.
    `astimezone()` ohne Argument konvertiert auf die lokale Systemzeitzone.

    2026-07-26 (echter Folge-Fund, Nutzer-Screenshot GUI vs. E-Mail): der
    Fix von 2026-07-21 lebte nur in scheduler/background.py und wurde nie
    fuer die App-GUI verwendet - `ui/hebel_view.py`/`ui/signals_view.py`/
    `ui/app.py`/`ui/regime_view.py`/`ui/letzte_bewertung.py` zeigten
    `created_at[:16].replace("T", " ")` weiterhin roh, wodurch GENAU dieselbe
    optische 2-Stunden-Luecke wieder auftrat - nur diesmal zwischen GUI-Liste
    und E-Mail statt zwischen Berechnung und Versand. Deshalb hierher in das
    gemeinsame, Tk-freie Modul verschoben (aus scheduler/background.py, dort
    nur noch re-exportiert), damit GUI und E-Mail dieselbe EINE Funktion
    verwenden und nicht wieder auseinanderlaufen koennen."""
    if not iso_timestamp:
        return "-"
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone().strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return iso_timestamp[:16].replace("T", " ")


_RISIKOFAKTOR_SYMBOL = {"positiv": "▲", "neutral": "●", "negativ": "▼"}

# 2026-07-20: urspruenglich farbige Kreis-Emoji (🟢/⚪/🔴) - Nutzer-Screenshot
# vom echten Notebook-App-Detail-Panel zeigte, dass Tkinters Standardfont
# (Windows) fuer 🟢/🔴 (ausserhalb der Basic Multilingual Plane) auf denselben
# Ersatzglyph zurueckfaellt, wodurch die Farbunterscheidung im laufenden
# Betrieb komplett verloren ging (nur ⚪ blieb sichtbar unterscheidbar). Wechsel
# auf die bereits im Projekt etablierten Form-Marker ▲/●/▼ (siehe
# ui/app.py/portfolio.py/screener_view.py: These-Marker, gleiche Semantik
# positiv/neutral/negativ) - Form statt Farbe macht die Unterscheidung robust
# gegen Emoji-Rendering, sowohl in der App als auch im reinen Text der E-Mail.
RISIKOFAKTOREN_LEGENDE = "(▲ unterstützt die Empfehlung · ● neutral · ▼ Warnsignal/Risiko)"


def format_risikofaktoren_lines(risikofaktoren_json: str | None) -> list[str]:
    """2026-07-19 (E-Mail-/App-Neustrukturierung in 3 Abschnitte - Mathematisch
    berechnet / LLM-Bewertung / Konklusion, echter AVAX-Hebel-Fund). Gemeinsame
    Anzeigelogik fuer ui/hebel_view.py + ui/signals_view.py, spiegelt
    scheduler/background.py::_formatiere_risikofaktoren() (dort eigene Kopie
    fuer den E-Mail-Textkontext - bewusst getrennt, unterschiedliche
    Ziel-Formate). Sortiert negativ vor neutral vor positiv, damit die
    wichtigsten Warnungen zuerst erscheinen.

    Regelwerk-Audit Stufe 3, Punkt 3 (2026-07-29): Eintraege mit `ist_kontext`
    (aktuell nur Regime-Konflikt/-Ausrichtung, siehe hebel_risk_gate.py::
    Risikofaktor-Docstring) erscheinen VOR den gezaehlten Warnungen als eigene
    Kontext-Zeile ohne ▲/▼/●-Symbol - sie sind in einem anhaltenden Regime fuer
    praktisch jedes Signal derselben Richtung vorhanden und sollen nicht als
    gleichwertige zusaetzliche Warnung neben echten Einzelfall-Faktoren
    erscheinen. Rueckwaertskompatibel: fehlt das Feld (aeltere gespeicherte
    Signale), verhaelt es sich wie `False` - identisches Verhalten wie vorher."""
    import json

    if not risikofaktoren_json:
        return []
    try:
        faktoren = json.loads(risikofaktoren_json)
    except (ValueError, TypeError):
        return []
    if not faktoren:
        return []

    kontext_zeilen = [
        f"--- {f.get('name', '')}: {f.get('begruendung', '')} ---"
        for f in faktoren if f.get("ist_kontext", False)
    ]

    gruppen: dict[str, list[dict]] = {"negativ": [], "neutral": [], "positiv": []}
    for f in faktoren:
        if f.get("ist_kontext", False):
            continue
        gruppen.setdefault(f.get("bewertung", "neutral"), []).append(f)

    zeilen = list(kontext_zeilen)
    for bewertung in ("negativ", "neutral", "positiv"):
        for f in gruppen.get(bewertung, []):
            symbol = _RISIKOFAKTOR_SYMBOL.get(bewertung, "●")
            zeilen.append(f"{symbol} {f.get('name', '')}: {f.get('begruendung', '')}")
    return zeilen


_FAZIT_SYMBOL = {"ja": "▲", "mit_vorbehalt": "●", "nein": "▼"}
# 2026-07-26 (Nutzer-Wunsch "nur das Wort Fazit unterstreichen, nicht der
# ganze Text"): eigene Konstante statt eines Literals im f-String, damit
# _split_fazit_label() unten denselben exakten Text zum Suchen verwendet.
_FAZIT_LABEL = "Fazit:"


def format_fazit_lines(
    fazit_folgen: str | None, fazit_kurzfazit: str | None, fazit_konsistenz_hinweis: str | None,
) -> list[str]:
    """Signal-Fazit (2026-07-25, abschliessendes LLM-Synthese-Verdikt, siehe
    Signal.fazit_folgen-Docstring und Memory feedback_llm_synthese_kein_
    deterministischer_override.md) - gemeinsame Anzeigelogik fuer
    ui/hebel_view.py + ui/signals_view.py, direkt nach der Risikofaktoren-
    Liste (Abschnitt 3). Wiederverwendet BEWUSST dieselben ▲/●/▼-Symbole wie
    format_risikofaktoren_lines() (ja=gruen/unterstuetzend, mit_vorbehalt=
    neutral, nein=rot/warnend) - dadurch greift classify_detail_line() unten
    automatisch, ohne eigene Tag-Definition. Leere Liste, wenn kein Fazit
    vorliegt (aeltere Signale vor diesem Feature)."""
    if not fazit_folgen:
        return []
    symbol = _FAZIT_SYMBOL.get(fazit_folgen, "●")
    zeilen = [f"{symbol} {_FAZIT_LABEL} {fazit_folgen.replace('_', ' ')} - {fazit_kurzfazit or ''}"]
    if fazit_konsistenz_hinweis:
        zeilen.append(f"⚠ {fazit_konsistenz_hinweis}")
    return zeilen


_ZAI_KONSISTENZ_SYMBOL = {"konsistent": "▲", "widerspruch": "▼"}
_ZAI_UEBEREINSTIMMUNG_SYMBOL = {"ja": "▲", "nein": "▼"}
_ZAI_KONSISTENZ_LABEL = "Z.ai-Gegenprüfung der Begründung:"
_ZAI_RICHTUNG_LABEL = "Z.ai eigene Richtungseinschätzung:"


def format_zai_gegenpruefung_lines(
    zai_gegenpruefung_urteil: str | None,
    zai_gegenpruefung_kurzbegruendung: str | None,
    zai_eigene_richtung: str | None,
    zai_uebereinstimmung: str | None,
    zai_richtung_kurzbegruendung: str | None,
    war_re_evaluierung_faellig: bool = False,
) -> list[str]:
    """Z.ai-Gegenpruefung (2026-07-26, siehe agent/krypto/gegenpruefung.py) -
    ZWEI unabhaengige Zeilen, analog format_fazit_lines(): dieselben ▲/▼-
    Symbole (kein ●, `urteil`/`uebereinstimmung` kennen nur zwei Werte), damit
    classify_detail_line() automatisch greift (risk_positiv/risk_negativ -
    bewusst NICHT die fazit_*-Tags, siehe Nutzer-Entscheidung 2026-07-26:
    farbig wie Risikofaktoren, aber NICHT fett wie das Fazit selbst, um die
    Abstufung Abschnitts-Header > Fazit > Risikofaktoren/Z.ai zu erhalten).
    Explizites Label unterscheidet klar von "Fazit:" - prueft die eigene
    Begruendung des Primaer-Modells (Abschnitt 2), NICHT dessen Fazit
    (Abschnitt 3). Jede Zeile erscheint nur, wenn das jeweilige Feld gesetzt
    ist (kein Rauschen bei aelteren Signalen oder fehlgeschlagenem Z.ai-Call).

    war_re_evaluierung_faellig (2026-08-01, Spot-Verkaufs-Luecke Schritt 4,
    nur Signal - HebelSignal hat kein solches Feld, Default False laesst den
    Hebel-Aufruf unveraendert): HALTEN-Signale liefern nie ein
    zai_uebereinstimmung, weil richtung_aus_action() dafuer None zurueckgibt
    (siehe agent/krypto/gegenpruefung.py) - das macht "unklar" fuer die
    ueberwiegende Mehrheit aller HALTEN-Faelle zu reinem Rauschen. Fuer die
    kleine Teilmenge, bei der das eigene halte_kriterium/Regel 17 bereits
    erreicht war (Re-Evaluierung faellig), ist Z.ais unabhaengige Richtungs-
    einschaetzung aber besonders lesenswert - daher ein eigenes, informativeres
    Label statt des generischen "unklar"."""
    zeilen = []
    if zai_gegenpruefung_urteil:
        symbol = _ZAI_KONSISTENZ_SYMBOL.get(zai_gegenpruefung_urteil, "●")
        zeilen.append(
            f"{symbol} {_ZAI_KONSISTENZ_LABEL} {zai_gegenpruefung_urteil} - "
            f"{zai_gegenpruefung_kurzbegruendung or ''}"
        )
    if zai_eigene_richtung:
        symbol = _ZAI_UEBEREINSTIMMUNG_SYMBOL.get(zai_uebereinstimmung, "●")
        if zai_uebereinstimmung == "ja":
            abgleich_text = "stimmt überein"
        elif zai_uebereinstimmung == "nein":
            abgleich_text = "weicht ab"
        elif war_re_evaluierung_faellig:
            abgleich_text = "Re-Evaluierung fällig - unabhängige Einschätzung beachten"
        else:
            abgleich_text = "unklar"
        zeilen.append(
            f"{symbol} {_ZAI_RICHTUNG_LABEL} {zai_eigene_richtung} ({abgleich_text}) - "
            f"{zai_richtung_kurzbegruendung or ''}"
        )
    return zeilen


# 2026-07-23: gemeinsame Zeilen-Klassifikation fuer Signal-Detail-Textbloecke
# (Hebel/Spot-Familie/Marktscan) - wird sowohl von ui/detail_panel.py (tk.Text-
# Tags im App-Detail-Panel) als auch von scheduler/background.py/
# api/email_notify.py (HTML-Hervorhebung in der Benachrichtigungs-E-Mail)
# genutzt. Bewusst hier in formatting.py (Tk-frei) statt in ui/detail_panel.py
# (importiert tkinter) - der Scheduler/E-Mail-Pfad soll kein Tkinter brauchen.
_SUBHEADER_MAX_LEN = 70
_RISK_TAG_BY_SYMBOL = {"▲": "risk_positiv", "●": "risk_neutral", "▼": "risk_negativ"}
# 2026-07-25 (Nutzer-Wunsch "Fazit-Label deutlicher"): eigene, farblich
# identische Tag-Variante nur fuer die Fazit-Zeile (erkennbar am "Fazit:"-
# Praefix direkt nach dem Symbol) - Fett+Unterstrichen in App UND E-Mail,
# OHNE die Farbsemantik/Optik der normalen Risikofaktoren-Zeilen anzutasten.
_FAZIT_TAG_BY_SYMBOL = {"▲": "fazit_positiv", "●": "fazit_neutral", "▼": "fazit_negativ"}


def classify_detail_line(line: str) -> str | None:
    """Erkennt bekannte Zeilenmuster in den Signal-Detail-Textbloecken rein per
    Text-Pattern (keine Aenderung an den Zeilen-Bau-Funktionen selbst noetig):
    Abschnitts-Kopfzeilen ("--- N. ... ---"), Unter-Kopfzeilen, Warnungen (⚠),
    Risikofaktor-Marker (▲/●/▼), die Fazit-Zeile (gleiche Symbole, eigener
    Tag - siehe _FAZIT_TAG_BY_SYMBOL) und die zugehoerige Legendenzeile. Gibt
    None zurueck, wenn die Zeile keinem bekannten Muster entspricht (normaler
    Fliesstext/eingerueckte Detailzeilen)."""
    stripped = line.strip()
    if not stripped:
        return None
    if stripped[0] in "⚠":
        return "warning"
    if stripped[0] in _RISK_TAG_BY_SYMBOL:
        rest = stripped[1:].strip()
        if rest.startswith(_FAZIT_LABEL):
            return _FAZIT_TAG_BY_SYMBOL[stripped[0]]
        return _RISK_TAG_BY_SYMBOL[stripped[0]]
    if stripped.startswith("(") and stripped.endswith(")") and "Warnsignal" in stripped:
        return "legend"
    if stripped.startswith("--- ") and stripped.endswith(" ---"):
        return "section_header"
    # DIE HERKUNFTSZEILE DER NEUEN MAIL (17.08.2026). Sie steht eingerueckt
    # in eckigen Klammern unter jedem Abschnittskopf - "[GEMESSEN - Kurse
    # und Fremdquellen]". Ohne diese Regel faellt sie in den Zweig
    # darunter und bleibt schwarzer Fliesstext; sie ist aber Beiwerk zum
    # Kopf, kein Inhalt, und gehoert damit in dieselbe Klasse wie die
    # Legende: kursiv und grau.
    if stripped.startswith("[") and stripped.endswith("]"):
        return "legend"
    if line.startswith(" "):
        return None  # eingerueckte Detailzeilen nie als Kopfzeile behandeln
    core = stripped.split("(", 1)[0].strip()  # z.B. "STUFE-B-SCORES (0-100 je Kategorie)" -> "STUFE-B-SCORES"
    if core and core.isupper() and 1 <= len(core.split()) <= 6:
        return "sub_header"
    if stripped.endswith(":") and len(stripped) <= _SUBHEADER_MAX_LEN:
        return "sub_header"
    return None


# Feste Light-Mode-Farben fuer die E-Mail-HTML-Variante (2026-07-23) - E-Mails
# haben kein Dark-Mode-Konzept wie die App (siehe ui/theme.py); die Farben hier
# sind bewusst als Literale fixiert, nicht von ui.theme abgeleitet, damit die
# E-Mail unabhaengig vom aktuellen App-Theme immer gleich (und immer lesbar)
# aussieht - siehe auch die color-scheme-Meta-Tags in api/email_notify.py, die
# Gmails automatische Dark-Mode-Invertierung fuer die ganze Mail unterdruecken.
# 2026-07-25, Nutzer-Fund: der neutrale Grauton (risk_neutral/fazit_neutral/
# legend) war mit #666666 in der echten Gmail-Darstellung teils schwer lesbar
# - auf #4a4a4a nachgedunkelt (Kontrast zu Weiss steigt von ~5,7:1 auf ~8,4:1).
_HTML_STYLE_BY_TAG = {
    "section_header": "font-weight:bold;font-size:1.05em;color:#0056b3;",
    "sub_header": "font-weight:bold;color:#000000;",
    "warning": "font-weight:bold;color:#c0392b;",
    "risk_positiv": "color:#1a7f37;",
    "risk_neutral": "color:#4a4a4a;",
    "risk_negativ": "color:#c0392b;",
    # 2026-07-26 (Nutzer-Wunsch "nur das Wort Fazit unterstreichen, nicht der
    # ganze Text"): Unterstreichung NICHT mehr hier - nur noch fett+farbig
    # fuer den Rest der Zeile, das Wort "Fazit:" selbst bekommt zusaetzlich
    # _FAZIT_LABEL_STYLE_BY_TAG (siehe render_detail_html()/_split_fazit_label()).
    "fazit_positiv": "font-weight:bold;color:#1a7f37;",
    "fazit_neutral": "font-weight:bold;color:#4a4a4a;",
    "fazit_negativ": "font-weight:bold;color:#c0392b;",
    "legend": "color:#4a4a4a;font-style:italic;",
}

# Nur fuer das "Fazit:"-Label-Praefix (siehe _split_fazit_label()) - dieselbe
# Farbe wie der jeweilige Basis-Tag oben, zusaetzlich unterstrichen.
_FAZIT_LABEL_STYLE_BY_TAG = {
    "fazit_positiv": "font-weight:bold;text-decoration:underline;color:#1a7f37;",
    "fazit_neutral": "font-weight:bold;text-decoration:underline;color:#4a4a4a;",
    "fazit_negativ": "font-weight:bold;text-decoration:underline;color:#c0392b;",
}


def _split_fazit_label(line: str) -> tuple[str, str] | None:
    """Trennt eine Fazit-Zeile in Label-Praefix ('<Symbol> Fazit:') und den
    Rest - fuer die Teil-Unterstreichung (nur das Wort 'Fazit' unterstrichen,
    nicht der ganze Text, Nutzer-Wunsch 2026-07-26). None, wenn "Fazit:" aus
    irgendeinem Grund nicht in der Zeile vorkommt (sollte bei einer als
    fazit_*-getaggten Zeile nicht passieren, defensiv trotzdem abgesichert)."""
    idx = line.find(_FAZIT_LABEL)
    if idx == -1:
        return None
    ende = idx + len(_FAZIT_LABEL)
    return line[:ende], line[ende:]


def _html_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_detail_html(text: str) -> str:
    """HTML-Pendant zu ui/detail_panel.py::render_detail_text() - baut aus
    demselben Zeilen-Text ein <pre>-basiertes HTML-Fragment mit Inline-Styles
    fuer dieselben Zeilenmuster (Abschnitts-Kopfzeilen fett+Akzentfarbe,
    Risikofaktor-Zeilen farbig etc.), damit die E-Mail dieselbe visuelle
    Hervorhebung zeigt wie das App-Detail-Panel. Fazit-Zeilen werden in ZWEI
    Spans gesplittet (siehe _split_fazit_label()), damit nur das Wort
    "Fazit:" unterstrichen ist, nicht der gesamte Text."""
    teile = ["<pre style=\"font-family: monospace; color:#1a1a1a; margin:0;\">"]
    for line in text.split("\n"):
        tag = classify_detail_line(line)
        split = _split_fazit_label(line) if tag in _FAZIT_LABEL_STYLE_BY_TAG else None
        if split:
            prefix, rest = split
            teile.append(f"<span style=\"{_FAZIT_LABEL_STYLE_BY_TAG[tag]}\">{_html_escape(prefix)}</span>")
            teile.append(f"<span style=\"{_HTML_STYLE_BY_TAG[tag]}\">{_html_escape(rest)}</span>")
        else:
            escaped = _html_escape(line)
            style = _HTML_STYLE_BY_TAG.get(tag)
            teile.append(f"<span style=\"{style}\">{escaped}</span>" if style else escaped)
        teile.append("\n")
    teile.append("</pre>")
    return "".join(teile)
