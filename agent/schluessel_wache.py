# -*- coding: utf-8 -*-
"""SCHLUESSELUEBERWACHUNG FUER DIE BITPANDA-ZUGAENGE (Schritt 61 Stufe 1.7).

⚠️ WARUM. Bis 16.09.2026 sah ein ungueltiger Schluessel aus wie ein Netzausfall:
der Bestandsabgleich meldete ,Job fehlgeschlagen' ohne Handlung, ein
abgelehnter Fusion-Schluessel stand nur als WARNING im Log, ein fehlender
Schluessel beim Start nur als INFO. Bestand, Cash und Hebelpositionen froren
dabei still ein. Nutzerentscheidungen G1-G6 vom 16.09.:

    G1  eigener Zustand ,Schluessel abgelehnt' - Beweis ist die 401-Antwort der
        NEUEN Schnittstelle (eindeutiger Text). Ein 401 der ALTEN Schnittstelle
        zaehlt nicht allein: dort heisst 401 auch ,Pfad unbekannt'
        (`api/bitpanda.py`, /trades-Docstring). Fusion hat einen eigenen Zustand.
    G2  eigene Mail mit Wirkung und Handlung - sofort, dann hoechstens einmal
        am Tag; gelingt der Zugang wieder, eine kurze Entwarnung
    G3  fehlender Schluessel beim Start -> eine Mail je Start
    G4  Erinnerung 30, 7 und 1 Tag vor dem Ablauf (Fusion 15.09.2027; der
        Hauptschluessel hat laut Nutzer keinen Ablauf)
    G5  Backoff der Jobs bleibt unveraendert
    G6  nur die Bitpanda-Schluessel

⚠️⚠️ KEINE GEHEIMNISSE (Nutzervorgabe 16.09.). Mails, Log und Datenbank nennen
nur den NAMEN der Umgebungsvariable, nie einen Wert oder einen Teil davon, und
keinen Fehlertext der Gegenseite. Die Zustaende liegen in `meta` (Zeitpunkte
und Tage, sonst nichts).
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone

logger = logging.getLogger(__name__)

SCHLUESSEL = {
    "bitpanda": {
        "name": "Bitpanda-Hauptschluessel",
        "variable": "BITPANDA_API_KEY",
        "wo": "im Bitpanda-Konto bei den API-Schluesseln",
        "wirkung": (
            "Bestand und Cash werden nicht mehr mit Bitpanda abgeglichen - das System "
            "rechnet mit dem letzten guten Stand weiter. Kaeufe, Verkaeufe und "
            "Staking seitdem sieht es nicht. Auch die Hebelpositionen werden nicht "
            "mehr abgeglichen."),
    },
    "fusion": {
        "name": "Bitpanda-Fusion-Schluessel",
        "variable": "FUSION_API_KEY",
        "wo": "in Bitpanda Fusion bei den API-Schluesseln",
        "wirkung": (
            "Die Kaufmails nennen beim gebundenen Cash keine Anzahl und keine "
            "aelteste Order mehr. Der gebundene Betrag selbst stimmt weiter - er "
            "kommt aus dem Hauptzugang."),
    },
}

# G4: bekannte Ablaufdaten. In `config.yaml` unter `bitpanda.schluessel_ablauf`
# ueberschreibbar (z.B. `fusion: 2028-09-15` nach einem neuen Schluessel).
SCHLUESSEL_ABLAUF_VORGABE = {"fusion": "2027-09-15"}
ABLAUF_STUFEN_TAGE = (30, 7, 1)

_START_GEMELDET = False


def _meta(conn, schluessel: str) -> str | None:
    from database import db
    try:
        return db.get_meta_wert(conn, schluessel)
    except Exception:                                        # noqa: BLE001
        return None


def _setze(conn, schluessel: str, wert: str) -> None:
    from database import db
    db.set_meta_wert(conn, schluessel, wert)


def _sende(betreff: str, text: str) -> bool:
    """Standardversand ueber die Mail-Einstellungen - fail-soft."""
    try:
        import config as config_module
        from api.email_notify import send_notification_email
        email_cfg = ((config_module.load_config().get("benachrichtigung") or {}).get("email") or {})
        if not email_cfg.get("aktiv", False) or not email_cfg.get("empfaenger"):
            return False
        return bool(send_notification_email(betreff, text, email_cfg["empfaenger"]))
    except Exception:                                        # noqa: BLE001
        logger.exception("Schluesselmail nicht verschickt: %s", betreff)
        return False


def _handlung(k: str, abschluss: str = "") -> str:
    s = SCHLUESSEL[k]
    return ("WAS ZU TUN IST:\n"
            "  1. %s einen neuen Schluessel anlegen - nur mit Leserechten, ohne "
            "Handels- oder Auszahlungsrechte.\n"
            "  2. Am Notebook in der Datei .env die Zeile %s= mit dem neuen Schluessel "
            "ersetzen.\n"
            "  3. Die App neu starten - der Schluessel wird nur beim Start gelesen.\n"
            "  4. Die .env per USB auf den Desktop uebertragen.%s"
            % (s["wo"], s["variable"], abschluss))


def _jetzt(jetzt):
    return jetzt or datetime.now(timezone.utc)


def _zeit(iso: str | None) -> str:
    if not iso:
        return "unbekannt"
    try:
        z = datetime.fromisoformat(iso)
        return z.astimezone().strftime("%d.%m.%Y %H:%M")
    except ValueError:
        return str(iso)[:16]


def abgelehnt_seit(conn, k: str) -> str | None:
    return _meta(conn, "schluessel_%s_abgelehnt_seit" % k) or None


def abgelehnt(conn, k: str, jetzt: datetime | None = None, senden=None) -> bool:
    """G1/G2: der Zugang wurde abgelehnt. Mail sofort, dann hoechstens einmal je
    Kalendertag. True, wenn eine Mail verschickt wurde."""
    senden = senden or _sende
    jetzt = _jetzt(jetzt)
    seit = abgelehnt_seit(conn, k)
    if not seit:
        seit = jetzt.isoformat()
        _setze(conn, "schluessel_%s_abgelehnt_seit" % k, seit)
        logger.error("%s abgelehnt (%s) - eigene Mail mit Handlung folgt",
                     SCHLUESSEL[k]["name"], SCHLUESSEL[k]["variable"])
    tag = jetzt.date().isoformat()
    if _meta(conn, "schluessel_%s_gemeldet_tag" % k) == tag:
        return False
    s = SCHLUESSEL[k]
    betreff = "TradingInfoTool: %s abgelehnt - Handlung noetig" % s["name"]
    text = "\n".join([
        "Bitpanda lehnt den %s (%s) ab - seit %s." % (s["name"], s["variable"], _zeit(seit)),
        "",
        "WAS DAS BEDEUTET: " + s["wirkung"],
        "",
        _handlung(k),
        "",
        "Solange der Zugang abgelehnt wird, kommt diese Mail einmal am Tag. Sobald er "
        "wieder funktioniert, kommt eine kurze Entwarnung.",
    ])
    if senden(betreff, text):
        _setze(conn, "schluessel_%s_gemeldet_tag" % k, tag)
        return True
    return False


def wieder_in_ordnung(conn, k: str, jetzt: datetime | None = None, senden=None) -> bool:
    """G2: der Zugang funktioniert wieder - Zustand loeschen, Entwarnung schicken.
    Ohne vorherige Ablehnung passiert nichts."""
    seit = abgelehnt_seit(conn, k)
    if not seit:
        return False
    senden = senden or _sende
    _setze(conn, "schluessel_%s_abgelehnt_seit" % k, "")
    _setze(conn, "schluessel_%s_gemeldet_tag" % k, "")
    s = SCHLUESSEL[k]
    logger.info("%s wieder angenommen (abgelehnt seit %s)", s["name"], _zeit(seit))
    return bool(senden("TradingInfoTool: %s wieder in Ordnung" % s["name"],
                       "Bitpanda nimmt den %s (%s) wieder an. Abgelehnt war er seit %s.\n\n"
                       "Der naechste Abgleich holt den aktuellen Stand nach - nichts weiter zu tun."
                       % (s["name"], s["variable"], _zeit(seit))))


def fehlende_beim_start(umgebung: dict, senden=None) -> list[str]:
    """G3: eine Mail je Start fuer jeden fehlenden Schluessel. Gibt die Kennungen
    der fehlenden zurueck."""
    global _START_GEMELDET
    fehlend = [k for k, s in SCHLUESSEL.items() if not (umgebung.get(s["variable"]) or "").strip()]
    if not fehlend or _START_GEMELDET:
        return fehlend
    senden = senden or _sende
    teile = []
    for k in fehlend:
        s = SCHLUESSEL[k]
        teile += ["%s (%s) FEHLT." % (s["name"], s["variable"]),
                  "WAS DAS BEDEUTET: " + s["wirkung"], "", _handlung(k), ""]
    betreff = "TradingInfoTool: beim Start fehlt %s" % ", ".join(SCHLUESSEL[k]["variable"] for k in fehlend)
    teile.append("Diese Mail kommt einmal je Start der App.")
    if senden(betreff, "\n".join(teile)):
        _START_GEMELDET = True
    return fehlend


def ablaufdaten(config: dict | None = None) -> dict:
    aus = dict(SCHLUESSEL_ABLAUF_VORGABE)
    try:
        eigene = (((config or {}).get("bitpanda") or {}).get("schluessel_ablauf") or {})
        for k, v in eigene.items():
            if k in SCHLUESSEL:
                aus[k] = str(v) if v else None
    except AttributeError:
        pass
    return {k: v for k, v in aus.items() if v}


def pruefe_ablauf(conn, config: dict | None = None, heute: date | None = None, senden=None) -> list[str]:
    """G4: Erinnerung 30, 7 und 1 Tag vor dem Ablauf, dazu einmal am Ablauftag
    oder danach. Jede Stufe genau einmal je Ablaufdatum. Gibt die Kennungen
    zurueck, fuer die jetzt gemailt wurde."""
    senden = senden or _sende
    heute = heute or datetime.now(timezone.utc).date()
    gemailt = []
    for k, datum in ablaufdaten(config).items():
        try:
            ablauf = date.fromisoformat(str(datum)[:10])
        except ValueError:
            logger.warning("Ablaufdatum fuer %s nicht lesbar: %r", SCHLUESSEL[k]["variable"], datum)
            continue
        tage = (ablauf - heute).days
        if tage > ABLAUF_STUFEN_TAGE[0]:
            continue
        stufe = "abgelaufen" if tage <= 0 else str(min(s for s in ABLAUF_STUFEN_TAGE if tage <= s))
        marke = "%s|%s" % (ablauf.isoformat(), stufe)
        if _meta(conn, "schluessel_%s_ablauf_gemeldet" % k) == marke:
            continue
        s = SCHLUESSEL[k]
        if tage <= 0:
            betreff = "TradingInfoTool: %s ist am %s abgelaufen" % (s["name"], ablauf.strftime("%d.%m.%Y"))
            kopf = "Der %s (%s) ist am %s abgelaufen." % (s["name"], s["variable"], ablauf.strftime("%d.%m.%Y"))
        else:
            betreff = "TradingInfoTool: %s laeuft in %d Tag%s ab" % (s["name"], tage, "en" if tage != 1 else "")
            kopf = ("Der %s (%s) laeuft am %s ab - in %d Tag%s."
                    % (s["name"], s["variable"], ablauf.strftime("%d.%m.%Y"), tage, "en" if tage != 1 else ""))
        text = "\n".join([
            kopf, "", "WAS DANN FEHLT: " + s["wirkung"], "",
            _handlung(k, "\n  5. Das neue Ablaufdatum in Basisinfos/config.yaml unter "
                         "bitpanda: schluessel_ablauf: %s: JJJJ-MM-TT eintragen." % k),
            "", "Erinnerungen kommen 30, 7 und 1 Tag vorher und am Ablauftag."])
        if senden(betreff, text):
            _setze(conn, "schluessel_%s_ablauf_gemeldet" % k, marke)
            gemailt.append(k)
    return gemailt


def hinweis_zeile(conn, k: str = "bitpanda") -> str | None:
    """Eine Zeile fuer andere Mails (Hebel-Abgleich, Datenfrische): die bekannte
    Ursache nennen, statt einen zweiten Ausfall zu vermuten."""
    seit = abgelehnt_seit(conn, k)
    if not seit:
        return None
    s = SCHLUESSEL[k]
    return ("URSACHE BEKANNT: der %s (%s) wird seit %s abgelehnt - siehe die eigene Mail "
            "mit der Handlung." % (s["name"], s["variable"], _zeit(seit)))
