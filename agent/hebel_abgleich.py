# -*- coding: utf-8 -*-
"""WIE AKTUELL IST DER HEBEL-ABGLEICH MIT BITPANDA? (15.09.2026)

⚠️⚠️ ANLASS - Befund 2.453-hebelpos und Nutzerentscheidung 7d (14.09.).
Alle 15 Minuten liest `sync_hebel_positions` die Bitpanda-Transaktionen und
schreibt `hebel_positions`. Darauf stehen die HEBELFUEHRUNG (Schliessen,
Hebel senken, Stop nachziehen) und der AGGREGAT-DECKEL (alle Hebelrisiken
zusammen hoechstens 3 % des Kapitals). Faellt der Abgleich aus, stand bis
hierher nur eine WARNING im Log - je Lauf, ohne Mail.

Am Notebook-Log 12.09. bis 15.09. gezaehlt: 212 Abgleiche im Median alle 15,0
Minuten, zwei Ausfaelle (Bitpanda 503), jeder EINZELN und im naechsten Lauf
nachgeholt. Ein anhaltender Ausfall bliebe dagegen unbemerkt: eine
geschlossene Position bekaeme weiter Empfehlungen, eine neue keine, und der
Deckel zaehlte falsch.

⚠️ DER VORHANDENE STEMPEL TAUGT NICHT. `hebel_position_last_synced_unix` ist
die Zeit der letzten TRANSAKTION - ohne Handel steht er still (am 14.09. auf
dem 11.09.). Deshalb ein eigener Stempel `hebel_positions_synced_at`: wann
lief der Abgleich zuletzt ERFOLGREICH. Dasselbe Prinzip wie
`bitpanda_holdings_synced_at` (2.453-bestand).

DIE GRENZE (Nutzerentscheidung 15.09.): 1 STUNDE = vier verpasste Laeufe in
Folge. Ein einzelner 503 loest damit nie aus; beim Hebel zaehlen aber
Stunden, nicht Tage - die 6 Stunden des Terminmarkts waeren hier zu lang.

GEZAEHLT AB DEM APP-START, wie beim Terminmarkt: eine App, die aus war, ist
kein Abgleichsausfall. ⚠️ Das heisst auch: laeuft die App NICHT, kommt keine
Mail - das kann dieses Modul nicht leisten.

EINE MAIL JE AUSFALL. Keine Wiederholung, keine Entwarnung (Muster
`terminmarkt_sammlung`, Nutzerentscheidung B vom 14.09.).
"""
from __future__ import annotations

from datetime import datetime, timezone

MELDEGRENZE_STUNDEN = 1.0
STEMPEL = "hebel_positions_synced_at"


def _zeit(wert) -> datetime | None:
    if not wert:
        return None
    try:
        t = datetime.fromisoformat(str(wert).replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def _stunden(von: datetime, bis: datetime) -> float:
    return max(0.0, (bis - von).total_seconds() / 3600.0)


def _stand_text(t: datetime | None) -> str:
    if t is None:
        return "noch nie"
    return t.astimezone().strftime("%d.%m. %H:%M")


def stempel_setzen(conn, jetzt: datetime | None = None) -> None:
    """Am Ende eines ERFOLGREICHEN Abgleichs - nie nach einem Fehlschlag."""
    from database import db as DBM

    DBM.set_hebel_positions_synced_at(
        conn, (jetzt or datetime.now(timezone.utc)).isoformat())


def stand(conn) -> datetime | None:
    from database import db as DBM

    return _zeit(DBM.get_hebel_positions_synced_at(conn))


def frische(conn, jetzt: datetime | None = None,
            app_start: datetime | None = None) -> dict:
    """Wie alt ist der letzte erfolgreiche Abgleich - und ist das ein Ausfall?

        veraltet   seit >= 1 Stunde kein erfolgreicher Abgleich, gezaehlt ab
                   dem spaeteren von letztem Erfolg und App-Start
        stand      der letzte Erfolg (None: noch nie)
        stunden    Alter des letzten Erfolgs (None: noch nie)
        offen      die Symbole, die laut LETZTEM Stand offen sind"""
    from database import db as DBM

    jetzt = jetzt or datetime.now(timezone.utc)
    t = stand(conn)
    bezug = max([x for x in (t, app_start) if x is not None], default=None)
    alter_bezug = _stunden(bezug, jetzt) if bezug is not None else None
    try:
        offen = sorted({p.symbol for p in DBM.get_open_hebel_positions(conn)})
    except Exception:                                        # noqa: BLE001
        offen = []
    return {"veraltet": alter_bezug is not None and alter_bezug >= MELDEGRENZE_STUNDEN,
            "stand": t,
            "stunden": None if t is None else _stunden(t, jetzt),
            "offen": offen}


class Meldezustand:
    """Ist DIESER Ausfall schon gemeldet? Im Speicher - nach einem Neustart
    zaehlt der Ausfall ohnehin neu ab dem App-Start."""

    def __init__(self):
        self.gemeldet = False


def meldung(befund: dict, zustand: Meldezustand,
            letzter_fehler: str | None = None):
    """(betreff, text) oder None. Der Aufrufer merkt den Versand erst nach
    ERFOLGREICHEM Versand vor (`vormerken`) - scheitert er, versucht es der
    naechste Lauf wieder.

    ⚠️ ERHOLT SICH DER ABGLEICH, WIRD DER ZUSTAND SOFORT ZURUECKGESETZT - auch
    ohne Mail. Sonst wuerde der naechste Ausfall verschwiegen."""
    if not befund.get("veraltet"):
        zustand.gemeldet = False
        return None
    if zustand.gemeldet:
        return None
    from geheimnisse import maskiere

    offen = befund.get("offen") or []
    n = len(offen)
    h = befund.get("stunden")
    seit = _stand_text(befund.get("stand"))
    betreff = ("TradingInfoTool: Hebel-Abgleich mit Bitpanda seit %s ausgefallen - %s"
               % (seit if befund.get("stand") else "dem App-Start",
                  ("%d offene Hebelposition%s nicht aktuell" % (n, "en" if n != 1 else ""))
                  if n else "keine offene Hebelposition bekannt"))
    zeilen = [
        "Der Abgleich der Hebelpositionen mit Bitpanda laeuft alle 15 Minuten. "
        "Zuletzt erfolgreich: %s%s." % (
            seit, (" (vor %s Stunden)" % ("%.1f" % h).replace(".", ",")) if h is not None else ""),
        "",
        "OFFEN LAUT LETZTEM STAND: " + (", ".join(offen) if offen else "keine"),
        "",
        "WAS DAS BEDEUTET: Die Hebelfuehrung und der Aggregat-Deckel rechnen mit "
        "diesem Stand. Eine inzwischen geschlossene Position bekaeme weiter "
        "Empfehlungen, eine neu eroeffnete keine - und der Deckel zaehlt sie nicht.",
        "",
        "WAS ZU TUN IST: Offene Hebelpositionen in der Bitpanda-App selbst "
        "pruefen. Im Log nach ,Hebel-Positions-Abgleich uebersprungen' suchen.",
    ]
    if letzter_fehler:
        zeilen += ["", "LETZTER FEHLER: " + maskiere(str(letzter_fehler))[:300]]
    zeilen += ["", "Zu diesem Ausfall kommt keine weitere Mail. Sobald ein "
                   "Abgleich wieder gelingt, gilt er als beendet."]
    return betreff, "\n".join(zeilen)


def vormerken(zustand: Meldezustand) -> None:
    zustand.gemeldet = True


def positionsstand_zeile(befund: dict) -> str | None:
    """Die Zeile fuer die Hebelfuehrungs-Mail - nur, wenn der Stand veraltet ist.

    Ein FAKT in der Mail, kein Ausloeser (Regel 4): die Empfehlungen bleiben,
    der Leser erfaehrt, auf welchem Stand sie stehen.

    ⚠️ OHNE JEDEN ERFOLGREICHEN ABGLEICH KEINE ZEILE: dann ist kein
    Bitpanda-Schluessel gesetzt (der Abgleich laeuft absichtlich nicht, P-8)
    oder er ist seit dem Einspielen noch nie gelungen - den zweiten Fall meldet
    die Hinweismail des Jobs."""
    if not befund.get("veraltet") or befund.get("stand") is None:
        return None
    return ("⚠ POSITIONSSTAND VOM %s - der Abgleich mit Bitpanda ist veraltet; "
            "offene und geschlossene Positionen koennen abweichen."
            % _stand_text(befund.get("stand")))
