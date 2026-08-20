# -*- coding: utf-8 -*-
"""Wo steht dieser Wert in der Rangliste? (Umbauplan 93 B, Punkt 3, 20.08.2026)

DIE TATSACHE DARF IN DIE MAIL, DIE BEHAUPTUNG NICHT.

Der Rangplatz nach der Entwicklung der letzten 250 Handelstage ist eine
Aussage ueber die VERGANGENHEIT - nachrechenbar, unstrittig, und der Nutzer
sieht sie ohnehin im Chart. Sie zu verschweigen waere die "Einschraenkung,
damit es weniger wird", die dieses Projekt sich verboten hat.

Was NICHT dazugehoert, ist der Satz "deshalb kaufen". Genau der ist gemessen
worden, und das Ergebnis steht mit in der Mail:

⚠️ GEMESSEN, UND DAS ERGEBNIS IST ERNUECHTERND (messe_drift.py, 40 Reihen,
3.290 Termine, Newey-West, Schwelle aus 40 Placebo-Laeufen):

    Rueckblick 250 / Horizont  5   +1,01 % Abstand bestes zu schlechtestem
                                   Fuenftel, t = 3,20 bei Schwelle 3,11
    Rueckblick 250 / Horizont 20   +3,85 %, t = 2,54
    Rueckblick 250 / Horizont 60  +10,10 %, t = 1,58

Nur EIN Feld von 27 haelt die Schwelle, und ausgerechnet das kuerzeste:
+1,01 % Abstand heisst rund +0,5 % fuer das beste Fuenftel gegenueber dem
Markt. DIE HANDELSKOSTEN BETRAGEN 3 %. Der Vorteil ist gemessen und
gleichzeitig zu klein, um ihn zu bezahlen.

DREI EINSCHRAENKUNGEN, DIE DAZUGEHOEREN:

  1. Ohne den letzten Monat im Rueckblick faellt der Wert von t = 3,20 auf
     1,68. Klassisches Momentum sollte das AUSHALTEN - es spricht dafuer,
     dass der Vorteil an der juengsten Bewegung haengt.
  2. Das Signal lebt in der nachgeladenen Historie (t = 3,21 vor 07/2024,
     1,57 danach). Diese Zeit ist auswahlverzerrt: die Reihen enthalten nur
     Werte, die es heute noch gibt.
  3. Beide Haelften der Symbolliste zeigen dasselbe Vorzeichen (+0,56 % und
     +0,57 %), keine ist fuer sich signifikant. Der Effekt haengt nicht an
     wenigen Werten - er ist nur klein.

DESHALB STEHT HIER EIN RANGPLATZ UND KEINE EMPFEHLUNG.
"""
from __future__ import annotations

# Der Rueckblick, fuer den ueberhaupt etwas gemessen wurde. Ein anderer waere
# eine Zahl ohne Befund daneben.
RUECKBLICK_TAGE = 250

# Was die Messung ergeben hat - hier, damit die Mail nicht raet.
GEMESSEN = {"abstand_5t": 0.0101, "t": 3.20, "schwelle": 3.11,
            "felder": 27, "kosten": 0.03, "stand": "2026-08-20"}


def _gleiche_klasse(symbol: str) -> set:
    """Nur Werte DERSELBEN Anlageklasse - sonst ist es keine Rangliste.

    ⚠️ ERSTE FASSUNG RANGIERTE GEGEN ALLES (gefunden 20.08.2026 beim ersten
    Probelauf): "Platz 15 von 47 Kryptowerten", waehrend die Datenbank nur 41
    Kryptoreihen kennt - Aktien und ETF standen mit in der Liste. Ein
    Rangplatz gegen einen ETF sagt ueber einen Coin nichts."""
    try:
        import config as C
        wl = {x.symbol.upper(): str(getattr(x, "assetklasse", "") or "").lower()
              for x in C.get_watchlist()}
    except Exception:                                        # noqa: BLE001
        return set()
    meine = wl.get(str(symbol).upper())
    return {s for s, k in wl.items() if k and k == meine} if meine else set()


def rang(reihen: dict, symbol: str, rueckblick: int = RUECKBLICK_TAGE,
         mindest_symbole: int = 10) -> dict | None:
    """Platz dieses Symbols nach der Entwicklung ueber `rueckblick` Tage.

    ⚠️ NUR GEGEN WERTE MIT GENUG HISTORIE. Wer erst seit hundert Tagen dabei
    ist, hat keine Jahresentwicklung - ihn mit null zu fuehren waere eine
    erfundene Zahl und wuerde ihn ans Ende der Liste setzen.

    Gibt None zurueck, wenn es keine Rangliste gibt. KEINE Notzahl."""
    erlaubt = _gleiche_klasse(symbol)
    if not erlaubt:
        return None
    entwicklung = {}
    for sym, kerzen in (reihen or {}).items():
        if sym.upper() not in erlaubt or len(kerzen) <= rueckblick:
            continue
        try:
            frueher = float(kerzen[-1 - rueckblick].close)
            jetzt = float(kerzen[-1].close)
        except (AttributeError, IndexError, TypeError, ValueError):
            continue
        if frueher > 0 and jetzt > 0:
            entwicklung[sym] = jetzt / frueher - 1.0
    if symbol not in entwicklung or len(entwicklung) < mindest_symbole:
        return None
    sortiert = sorted(entwicklung, key=lambda s: entwicklung[s], reverse=True)
    return {"platz": sortiert.index(symbol) + 1, "von": len(sortiert),
            "entwicklung": entwicklung[symbol],
            "rueckblick": rueckblick}


def saetze(reihen: dict, symbol: str, assetklasse: str = "") -> list[str]:
    """Die Zeilen fuer die Mail: Tatsache, Einordnung, gemessener Wert.

    ⚠️ KEIN URTEIL UND KEIN GATE. Diese Zeilen sperren nichts."""
    from agent.schreibweise import de

    if str(assetklasse or "").strip().lower() != "krypto":
        return []
    r = rang(reihen, str(symbol).upper())
    if not r:
        return []
    # Das obere und untere Fuenftel benennen - "Platz 7 von 40" allein
    # zwingt den Leser zum Kopfrechnen.
    anteil = r["platz"] / r["von"]
    lage = ("im besten Fuenftel" if anteil <= 0.2 else
            "im schlechtesten Fuenftel" if anteil > 0.8 else
            "im Mittelfeld")
    aus = [f"Rangplatz nach {de(r['rueckblick'], 0)}-Tage-Entwicklung "
           f"(Tatsache, keine Prognose):",
           f"   Platz {de(r['platz'], 0)} von {de(r['von'], 0)} "
           f"Kryptowerten, {lage} "
           f"({de(100 * r['entwicklung'], 1)} % in diesem Zeitraum)."]
    # ⚠️ UND SOFORT DANEBEN, WAS DAS WERT IST.
    aus.append(
        f"   Was das bringt, ist GEMESSEN: der Abstand zwischen bestem und "
        f"schlechtestem Fuenftel betraegt "
        f"{de(100 * GEMESSEN['abstand_5t'], 1)} % auf fuenf Handelstage - "
        f"ein Feld von {de(GEMESSEN['felder'], 0)} haelt die Schwelle.")
    aus.append(
        f"⚠️ KEIN HANDELBARER VORTEIL: das beste Fuenftel liegt damit rund "
        f"{de(100 * GEMESSEN['abstand_5t'] / 2, 1)} % ueber dem Markt, die "
        f"Handelskosten betragen {de(100 * GEMESSEN['kosten'], 0)} %. "
        f"Der Rangplatz ist eine Beobachtung, kein Kaufgrund.")
    return aus
