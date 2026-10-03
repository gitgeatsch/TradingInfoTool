"""Die REGEL0 im Hebel-Tab (Schritt 7, Voranalyse_Schritt7 Par. 17; Nutzer 03.10.2026: *"Ja H-1 bis H-4 wie vorgeschlagen"*).

Reine Funktionen von der Ablage ``data/regel0_signale.db`` zu Anzeigezeilen - die Oberflaeche (ui/hebel_view.py) zeichnet
nur. So prueft die Suite, was angezeigt wird, ohne ein Fenster.

    H-1  die REGEL0-Signale stehen in DERSELBEN Liste wie die alten Hebelsignale (These *REGEL0 24 h*), je Asset das juengste
         Signal; die Filter des Tabs gelten (Hebel-Schalter, 2 Tage). Das Detail ist DERSELBE Text wie die Mail
         (``regel0_mail.signal_mail``) samt Mailstand.
    H-2  ``knopf_hinweis``: solange der alte Hebelweg aus ist (E-46), ist *Jetzt analysieren* gesperrt.
    H-3  ``positions_vermerk``: kam fuer das Asset in den 24 h vor der Eroeffnung einer echten Position ein REGEL0-Signal,
         steht bei ihr *REGEL0, Ausstieg ...* (Bruecke bis O13).

⚠️ LIEST NUR: die Ablage wird mit ``mode=ro`` geoeffnet und nie angelegt (``regel0_ablage.oeffne`` legt an und ergaenzt
Spalten - das ist Sache des Stundenlaufs). Fehlt die Datei, gibt es keine Zeilen.
"""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta, timezone

import agent.regel0_ablage as AB
import agent.regel0_groesse as G
import agent.regel0_mail as RM

THESE = "REGEL0 24 h"
ORDNER_VORGABE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")   # wie regel0_nachlader.DATEN_VORGABE
FENSTER_POSITION_H = 24          # H-3: so lange vor der Eroeffnung zaehlt ein Signal als ihr Anlass


def lese(ordner: str) -> list:
    """Alle Signalzeilen der Ablage als dicts - nur lesend; ohne Datei eine leere Liste."""
    p = os.path.join(ordner, AB.ABLAGE_NAME)
    if not os.path.exists(p):
        return []
    c = sqlite3.connect("file:%s?mode=ro" % p.replace("\\", "/"), uri=True, timeout=10)
    c.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in c.execute("SELECT * FROM signal ORDER BY signalstunde")]
    except sqlite3.Error:
        return []
    finally:
        c.close()


def _ende(txt: str) -> datetime:
    """Schluss der Stunde ``txt`` (UTC) - Einstieg und Ausstieg sind Schlusskurse ihrer Stunde."""
    return RM._t(txt) + timedelta(hours=1)


def _lokal(dt: datetime) -> str:
    return dt.astimezone().strftime("%d.%m. %H:%M")


def stufe(r: dict) -> tuple:
    """-> (Stufe, vorlaeufig?) - die endgueltige, sonst die vorlaeufige."""
    if r.get("stufe") is not None:
        return int(r["stufe"]), False
    if r.get("stufe_vorlaeufig") is not None:
        return int(r["stufe_vorlaeufig"]), True
    return 0, True


def status(r: dict, jetzt: datetime) -> str:
    """Der Stand des Signals in einem Wort - aus den Zeiten der Zeile, nie aus einer Annahme."""
    if r.get("mail_gesperrt_am"):
        return "nicht gemailt (Zuordnung)"
    s, _v = stufe(r)
    if s <= 0:
        return "kein Handel"
    ein, aus = _ende(r["einstieg"]), _ende(r["ausstieg"])
    if jetzt < ein:
        return "Einstieg %s" % _lokal(ein)
    if jetzt < aus:
        return "läuft bis %s" % _lokal(aus)
    if jetzt < aus + timedelta(hours=RM.ERINNERUNG_BIS_H):
        return "Ausstieg fällig"
    return "beendet %s" % _lokal(aus)


def hebel_text(r: dict) -> str:
    s, v = stufe(r)
    if s <= 0:
        return "-"
    return "%dx (vorläufig)" % s if v else "%dx" % s


def name(r: dict) -> str:
    """Der Name, unter dem das Asset im Tab steht: der Bitpanda-Name (= Watchlist), sonst das Binance-Kuerzel."""
    return r.get("bitpanda") or r["symbol"]


def zeitpunkt(r: dict) -> str:
    """ISO-Zeit (UTC), zu der das Signal feststand: Schluss der Signalstunde."""
    return _ende(r["signalstunde"]).isoformat()


def ist_aktiv(r: dict, jetzt: datetime) -> bool:
    """Noch nicht vorbei: vor dem Ausstieg oder Ausstieg gerade faellig."""
    return status(r, jetzt).startswith(("Einstieg", "läuft", "Ausstieg fällig"))


def juengste_je_asset(rows: list) -> dict:
    """{Name: juengste Signalzeile} - die Liste des Tabs hat je (Asset, Richtung) EINE Zeile, und die REGEL0 ist nur LONG."""
    aus = {}
    for r in rows:
        n = name(r)
        if n not in aus or r["signalstunde"] > aus[n]["signalstunde"]:
            aus[n] = r
    return aus


def sichtbar(r: dict, jetzt: datetime, schalter: dict, offen: set, nur_2_tage: bool, tage: int = 2) -> bool:
    """Dieselben Filter wie fuer die alten Zeilen: Schalter aus und keine offene Position -> weg; 2 Tage -> nur Juengeres
    (ein laufendes Signal bleibt, solange es laeuft)."""
    n = name(r)
    if (n, "LONG") in offen:
        return True
    if not r.get("bitpanda") or not schalter.get(n, False):     # O18: keine Zeile = aus; ohne Bitpanda-Namen kein Handel
        return False
    if nur_2_tage and not ist_aktiv(r, jetzt):
        return _ende(r["signalstunde"]) >= jetzt - timedelta(days=tage)
    return True


def listenzeile(r: dict, jetzt: datetime) -> tuple:
    """Die Werte der Liste: (Symbol, Richtung, Status, Hebel, These, Zeitpunkt-ISO)."""
    return (name(r), "LONG", status(r, jetzt), hebel_text(r), THESE, zeitpunkt(r))


def _offen_bei_mail(rows: list, r: dict) -> int:
    """Wie viele andere gemailte Signale liefen, als dieses gemailt wurde - dieselbe Zaehlung wie in ``versende``."""
    jt = r.get("mail_signal_am") or r["einstieg"]
    n = 0
    for x in rows:
        if x is r or (x["symbol"], x["signalstunde"]) == (r["symbol"], r["signalstunde"]):
            continue
        if x.get("mail_signal_am") and x["mail_signal_am"] <= jt and stufe(x)[0] > 0 and x["ausstieg"] > jt:
            n += 1
    return n


def mailstand(r: dict) -> list:
    z = ["", "MAILSTAND"]
    if r.get("mail_gesperrt_am"):
        z.append("  Signalmail: NICHT verschickt (%s UTC) - Zuordnung zweifelhaft" % r["mail_gesperrt_am"])
    elif r.get("mail_signal_am"):
        z.append("  Signalmail: verschickt %s UTC mit %sx" % (r["mail_signal_am"], r.get("mail_signal_stufe")))
    elif not r.get("hebel_schalter"):
        z.append("  Signalmail: keine - Hebel-Schalter war bei der Rechnung aus")
    elif stufe(r)[0] <= 0:
        z.append("  Signalmail: keine - kein Handel (keine Stufe unter der Liquidationsgrenze)")
    else:
        z.append("  Signalmail: noch nicht verschickt (der Stundenjob versucht es zur naechsten Stunde)")
    if r.get("mail_korrektur_am"):
        z.append("  Korrektur:  verschickt %s UTC (endgueltig %sx)" % (r["mail_korrektur_am"], r.get("stufe")))
    if r.get("mail_erinnerung_am"):
        z.append("  Erinnerung: verschickt %s UTC" % r["mail_erinnerung_am"])
    if r.get("abgleich"):
        z.append("  Abgleich:   %s" % r["abgleich"])
    z.append("  Regelversion %s · gerechnet %s UTC%s" % (r.get("version") or "-", r.get("erfasst_am") or "-",
                                                      " · endgueltig %s UTC" % r["endgueltig_am"] if r.get("endgueltig_am") else ""))
    return z


def pruefung_zeilen(ordner: str, r: dict) -> list:
    """E-52: der Pruefblock der LLM-Rollen zu diesem Signal, wie in der Mail - nur gelesen; ohne Eintrag eine leere Liste."""
    p = os.path.join(ordner, AB.ABLAGE_NAME)
    if not os.path.exists(p):
        return []
    c = sqlite3.connect("file:%s?mode=ro" % p.replace("\\", "/"), uri=True, timeout=10)
    try:
        if not c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='pruefung'").fetchone():
            return []
        rows = c.execute("SELECT rolle, fassung, ergebnis, fehler FROM pruefung WHERE symbol=? AND signalstunde=? ORDER BY am",
                         (r["symbol"], r["signalstunde"])).fetchall()
    except sqlite3.Error:
        return []
    finally:
        c.close()
    if not rows:
        return []
    import json
    import agent.regel0_llm as LLM
    erg = {}
    for rolle, _f, e, fehler in rows:
        erg[rolle] = json.loads(e) if e else {"fehlt": fehler or "?"}
    return [""] + LLM.mail_zeilen(erg, dict(LLM.lade(), fassung=rows[-1][1]))


def detail(r: dict, rows: list, jetzt: datetime, werte: dict | None = None, pruefzeilen: list | None = None) -> tuple:
    """-> (Titel, Metazeile, Text). Der Text ist DERSELBE wie in der Signalmail (eine Quelle), dazu Pruefblock und Mailstand."""
    werte = werte if werte is not None else G.lade()
    s, v = stufe(r)
    titel = "%s LONG: REGEL0 · %s" % (name(r), status(r, jetzt))
    meta = "REGEL0.1 · Signalstunde %s UTC · Einstieg %s · Ausstieg %s (Ortszeit)" % (
        r["signalstunde"], _lokal(_ende(r["einstieg"])), _lokal(_ende(r["ausstieg"])))
    if s > 0:
        _b, text = RM.signal_mail(r, s, v, G.rechne(s, _offen_bei_mail(rows, r), werte), werte, jetzt)
        zeilen = text.split("\n")
    else:
        zeilen = ["REGEL0.1 - SIGNAL OHNE HANDEL", "",
                  "Fuer %s lag zur Signalstunde keine Hebelstufe unter der Liquidationsgrenze 2 %% (24 h)." % name(r),
                  "Geschaetzte Liquidationsgefahr: 2x %s · 3x %s · 5x %s" % (RM._pct(r.get("p2")), RM._pct(r.get("p3")), RM._pct(r.get("p5")))]
    return titel, meta, "\n".join(zeilen + list(pruefzeilen or []) + mailstand(r))


def positions_vermerk(symbol: str, richtung: str, eroeffnet_am: str | None, rows: list) -> str:
    """H-3: 'REGEL0, Ausstieg dd.mm. HH:MM', wenn in den 24 h VOR der Eroeffnung ein REGEL0-Signal fuer das Asset feststand."""
    if str(richtung or "").upper() != "LONG" or not eroeffnet_am:
        return ""
    try:
        auf = datetime.fromisoformat(str(eroeffnet_am).replace("Z", "+00:00"))
    except ValueError:
        return ""
    if auf.tzinfo is None:
        auf = auf.replace(tzinfo=timezone.utc)
    best = None
    for r in rows:
        if name(r) != symbol or stufe(r)[0] <= 0:
            continue
        fest = _ende(r["signalstunde"])
        if fest <= auf <= fest + timedelta(hours=FENSTER_POSITION_H):
            if best is None or r["signalstunde"] > best["signalstunde"]:
                best = r
    return "REGEL0, Ausstieg %s" % _lokal(_ende(best["ausstieg"])) if best else ""


def knopf_hinweis(werte: dict | None = None) -> str | None:
    """H-2: None = der Knopf *Jetzt analysieren* darf den alten Hebelweg starten. Unlesbar -> gesperrt (fail-closed)."""
    try:
        aus = G.alter_hebelweg_aus(werte)
    except Exception:                                        # noqa: BLE001
        return "Gesperrt: Schalter alter_hebelweg_aus nicht lesbar"
    if aus:
        return ("Gesperrt: alter Hebelweg aus (REGEL0, E-46) - neue Hebel-Einstiege kommen nur aus der REGEL0. "
                "Der Knopf wuerde den alten Weg von Hand anstossen.")
    return None
