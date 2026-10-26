"""Spot B1 - Mitnahme x3 je L-Position (P14, 11.10.2026; Voranalyse_Spot_Neubau_04_10.md §31, §39.5-§39.7, §41).

Nutzer 11.10.: *"Ja, B1 jetzt bauen, pruefen und gegenpruefen"*.

DIE REGEL (wie gemessen, nichts neu gewaehlt - ``fb_messung.l_regel`` Stufe "Z1 x3", Uebertragbarkeit §39.6 TRAEGT auf dem ganzen
Bestand: 7.819 Positionen, 7,1 % ausgeloest, Korb +4,87 Pp, je Ausloesung Median +97 Pp):

    Kreis      jeder Krypto-Bestand (frei + gestakt > 0) ausser Kern BTC/ETH/SOL und Stablecoins (E-90)
    Fenster    365 Tage ab Starttag; Startkurs = Dollar-Tagesschluss am Starttag (Altbestand: Tag der Inbetriebnahme, A1 a)
    Ausloesung erster Tagesschluss NACH dem Start >= 3 x Startkurs; verkauft wird die HAELFTE am FOLGETAG. Liegt der Treffer auf dem
               letzten Fenstertag, gibt es keinen Folgetag im Fenster - dann keine Mitnahme (genau wie die Messung)
    danach     der Rest laeuft bis zum Fensterende; ohne Ausloesung beginnt am Fensterende ein neues Fenster mit neuem Startkurs

DATEN: ``price_history_ohlc`` der Produktion (Dollar-Tagesschluss, ``refresh_ohlc``), NUR LESEND - fuer alle gehaltenen Coins, auch die
ausserhalb des Binance-Universums (gegengeprueft 11.10.). ABLAGE: ``data/spot_betrieb.db`` (eigene Datei, nicht die Produktion).

KEIN Einstieg, keine Bewertung des Coins, kein Abbau (B4), keine Umschichtung des Erloeses (B-6, nicht gemessen). An Tagen ohne
Ausloesung keine Mail (E-91). Kosten (D6) nur als Information, nie in der Ausloesung (Regel 2).
"""
from __future__ import annotations

import os
import sqlite3
from datetime import date, datetime, timedelta, timezone

from agent.kernwerte import KERN  # noqa: E402  K-4 (26.10.2026): EINE Liste fuer alle Spot-Pfade
FAKTOR = 3.0
FENSTER_T = 365
MAIL_HOECHSTENS_T = 3          # ausgeloest vor mehr Tagen (Ausfall) -> nur Protokoll "verpasst", keine Mail (wie REGEL0 N-1)
SPRUNG = 2.0                   # Tagesschluss >= 2 x Vortag am Ausloesetag -> "zu pruefen" (Token-Umstellung?), keine Mail
KOSTEN_JE_SEITE = {"H": 0.36, "M": 0.88, "S": 3.20}    # D6: Bitpanda je Seite in %, Klasse nach Marktwert-Rang (Spot §32.1)
ABLAGE = "spot_betrieb.db"
BELEG = ("Gemessen ab 2024 auf dem ganzen Bestandskreis (7.819 Positionen): Die Mitnahme schlägt Halten, je Auslösung im Median "
         "um +97 Prozentpunkte, in 89 % der Fälle besser (Spot §39.6)")


# ══ die Regel - EINE Funktion, dieselbe wie in der Messung (Gegenprobe Teil 0) ═════════════════════════════════════════════
# Nutzer 17.10.2026: *"ja zu deinem Vorschlag zum Verkauf"* - der Nutzer tauscht oft in den Stablecoin EURCV statt in Fiat zu verkaufen
EURCV_SATZ = "Ob in Euro (Fiat) oder in den Stablecoin EURCV, ist deine Wahl – gemessen ist der Ausstieg aus dem Coin."


def verkaufstag(x) -> int | None:
    """``x``: Tagesschluesse der Tage 1..n NACH dem Start, geteilt durch den Startkurs (wie ``fb_messung``). -> Index des
    Verkaufstags (Folgetag des ersten Schlusses >= 3), oder None. Treffer am letzten Tag des Fensters -> None."""
    for k, v in enumerate(x):
        if v is not None and v == v and v >= FAKTOR:
            return k + 1 if k + 1 < len(x) else None
    return None


# ══ Ablage ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def oeffne(ordner: str) -> sqlite3.Connection:
    c = sqlite3.connect(os.path.join(ordner, ABLAGE), timeout=10)
    c.execute("CREATE TABLE IF NOT EXISTS fenster (symbol TEXT, start TEXT, startkurs_usd REAL, ende TEXT, ausloese_tag TEXT, "
              "ausloese_kurs REAL, verkauf_tag TEXT, mail_am TEXT, status TEXT, geschlossen_am TEXT, grund TEXT, PRIMARY KEY (symbol, start))")
    c.execute("CREATE TABLE IF NOT EXISTS protokoll (am TEXT, symbol TEXT, art TEXT, text TEXT)")
    c.commit()
    return c


def _ro(pfad: str) -> sqlite3.Connection:
    return sqlite3.connect("file:%s?mode=ro" % pfad.replace("\\", "/"), uri=True, timeout=10)


# ══ Eingaben (nur lesend) ═══════════════════════════════════════════════════════════════════════════════════════════════════
def kreis(conn_prod, watchlist: list) -> dict:
    """{Symbol: Menge frei + gestakt} der L-Bestaende - abgeleitet, nicht aufgezaehlt: Krypto der Watchlist ohne Stablecoins, ohne Kern."""
    krypto = {a.symbol for a in watchlist if getattr(a, "assetklasse", None) == "krypto" and not getattr(a, "ist_cash_aequivalent", False)}
    aus = {}
    for s, q, st in conn_prod.execute("SELECT symbol, quantity, staked_quantity FROM holdings"):
        m = float(q or 0) + float(st or 0)
        if m > 0 and s in krypto and s not in KERN:
            aus[s] = m
    return aus


def schluesse(conn_prod, symbol: str) -> list:
    """[(Tag, Dollar-Schluss)] aufsteigend aus price_history_ohlc - nur ECHTE Kurse: Zeilen mit quelle 'rekonstruiert' (aus einer
    Referenzreihe abgeleitet, agent/rekonstruktion.py) loesen keine Mitnahme aus (11.10.: betrifft heute nur OD7-Produkte, keine Kryptos)."""
    return [(d[:10], float(c)) for d, c in conn_prod.execute(
        "SELECT date, close FROM price_history_ohlc WHERE symbol=? AND currency='USD' AND close IS NOT NULL "
        "AND COALESCE(quelle, '') != 'rekonstruiert' ORDER BY date", (symbol,))]


def _tag(s: str) -> date:
    return date.fromisoformat(s[:10])


# ══ ein Lauf ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def lauf(conn_prod, ordner: str, watchlist: list, heute: date | None = None) -> dict:
    """Fortschreiben aller Fenster bis zum letzten ABGESCHLOSSENEN Tag (gestern, UTC). Schreibt nur in die Ablage.
    -> {'kreis': n, 'angelegt': [...], 'ausgeloest': [...], 'faellig': [Mailfaelle], 'protokoll': [...]}"""
    heute = heute or datetime.now(timezone.utc).date()
    letzter = heute - timedelta(days=1)
    jt = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    c = oeffne(ordner)
    erg = {"kreis": 0, "angelegt": [], "ausgeloest": [], "faellig": [], "protokoll": [], "neu_fenster": [], "geschlossen": []}

    def prot(sym, art, text, nur_bei_wechsel=False):
        # "kein Kurs" nur beim WECHSEL (sonst je Tag eine Zeile Rauschen - Pruefstand 11.10.: 410 Zeilen fuer einen Coin)
        if nur_bei_wechsel:
            r = c.execute("SELECT art FROM protokoll WHERE symbol=? ORDER BY rowid DESC LIMIT 1", (sym,)).fetchone()
            if r and r[0] == art:
                return
        c.execute("INSERT INTO protokoll VALUES (?,?,?,?)", (jt, sym, art, text))
        erg["protokoll"].append((sym, art, text))

    try:
        bestand = kreis(conn_prod, watchlist)
        erg["kreis"] = len(bestand)
        offen = {s: dict(zip(("symbol", "start", "startkurs_usd", "ende", "ausloese_tag", "ausloese_kurs", "verkauf_tag", "mail_am", "status"), r))
                 for r in c.execute("SELECT symbol, start, startkurs_usd, ende, ausloese_tag, ausloese_kurs, verkauf_tag, mail_am, status "
                                    "FROM fenster WHERE geschlossen_am IS NULL") for s in [r[0]]}
        # Bestand weg (verkauft): Fenster schliessen
        for s in sorted(set(offen) - set(bestand)):
            c.execute("UPDATE fenster SET geschlossen_am=?, grund='Bestand weg' WHERE symbol=? AND start=?", (letzter.isoformat(), s, offen[s]["start"]))
            prot(s, "geschlossen", "Bestand nicht mehr da (verkauft?) - Fenster ab %s geschlossen" % offen[s]["start"])
            erg["geschlossen"].append(s)
        for s in sorted(bestand):
            reihe = [(d, k) for d, k in schluesse(conn_prod, s) if _tag(d) <= letzter]
            if not reihe:
                prot(s, "kein Kurs", "kein Dollar-Tagesschluss in price_history_ohlc - kein Fenster", nur_bei_wechsel=True)
                continue
            f = offen.get(s)
            if f is None:
                d0, k0 = reihe[-1]
                if (letzter - _tag(d0)).days > 3:
                    prot(s, "kein Kurs", "letzter Tagesschluss %s aelter als 3 T - Fenster spaeter" % d0, nur_bei_wechsel=True)
                    continue
                f = {"symbol": s, "start": d0, "startkurs_usd": k0, "ende": (_tag(d0) + timedelta(days=FENSTER_T)).isoformat(),
                     "ausloese_tag": None, "ausloese_kurs": None, "verkauf_tag": None, "mail_am": None, "status": "laeuft"}
                c.execute("INSERT INTO fenster (symbol, start, startkurs_usd, ende, status) VALUES (?,?,?,?,?)", (s, d0, k0, f["ende"], "laeuft"))
                prot(s, "angelegt", "Fenster ab %s, Startkurs %.6g USD%s" % (d0, k0, "" if d0 == letzter.isoformat() else " (letzter Tagesschluss)"))
                erg["angelegt"].append(s)
            # Fensterende ueberschritten -> schliessen, neues Fenster ab dem Ende
            while _tag(f["ende"]) < letzter:
                c.execute("UPDATE fenster SET geschlossen_am=?, grund=? WHERE symbol=? AND start=?",
                          (f["ende"], "Fensterende" + (" nach Mitnahme" if f["ausloese_tag"] else " ohne Ausloesung"), s, f["start"]))
                vor = [(d, k) for d, k in reihe if _tag(d) <= _tag(f["ende"])]
                if not vor:
                    break
                d0, k0 = vor[-1]
                neu_ende = (_tag(d0) + timedelta(days=FENSTER_T)).isoformat()
                f = {"symbol": s, "start": d0, "startkurs_usd": k0, "ende": neu_ende, "ausloese_tag": None, "ausloese_kurs": None,
                     "verkauf_tag": None, "mail_am": None, "status": "laeuft"}
                c.execute("INSERT OR IGNORE INTO fenster (symbol, start, startkurs_usd, ende, status) VALUES (?,?,?,?,?)", (s, d0, k0, neu_ende, "laeuft"))
                prot(s, "neues Fenster", "ab %s, Startkurs %.6g USD" % (d0, k0))
                erg["neu_fenster"].append(s)
            if f["ausloese_tag"]:
                continue                                   # einmal je Fenster; der Rest laeuft bis zum Ende
            # die Regel: Tage NACH dem Start bis zum Fensterende (bzw. bis gestern) - verkaufstag() wie in der Messung
            nach = [(d, k) for d, k in reihe if _tag(f["start"]) < _tag(d) <= _tag(f["ende"])]
            fenster_voll = _tag(f["ende"]) <= letzter
            x = [k / f["startkurs_usd"] for _d, k in nach]
            # EINE Regel mit der Messung: verkaufstag(). Laeuft das Fenster noch, steht der Folgetag noch aus - ein Platzhalter
            # haelt die Bedeutung gleich (Treffer gestern -> Verkauf heute, liegt im Fenster); bei vollem Fenster gilt der letzte
            # Fenstertag ohne Folgetag wie in der Messung als KEINE Mitnahme.
            j = verkaufstag(x if fenster_voll else x + [float("nan")])
            if j is None:
                continue
            d_aus, k_aus = nach[j - 1]
            vortag = next((k for d, k in reversed(reihe) if _tag(d) < _tag(d_aus)), None)
            alter = (letzter - _tag(d_aus)).days
            if vortag and k_aus >= SPRUNG * vortag:
                status, art = "zu pruefen", "zu pruefen"
            elif alter > MAIL_HOECHSTENS_T:
                status, art = "verpasst", "verpasst"
            else:
                status, art = "faellig", "ausgeloest"
            c.execute("UPDATE fenster SET ausloese_tag=?, ausloese_kurs=?, verkauf_tag=?, status=? WHERE symbol=? AND start=?",
                      (d_aus, k_aus, (_tag(d_aus) + timedelta(days=1)).isoformat(), status, s, f["start"]))
            prot(s, art, "Tagesschluss %s %.6g USD = %.2f x Startkurs %.6g (Start %s)%s" % (
                d_aus, k_aus, k_aus / f["startkurs_usd"], f["startkurs_usd"], f["start"],
                " - Sprung >= %.0f x zum Vortag, nicht gemailt" % SPRUNG if status == "zu pruefen" else
                (" - %d T alt, nicht gemailt" % alter if status == "verpasst" else "")))
            erg["ausgeloest"].append(s)
        # faellige Mails (auch aus frueheren Laeufen, solange noch nicht gemailt und nicht zu alt)
        for r in c.execute("SELECT symbol, start, startkurs_usd, ende, ausloese_tag, ausloese_kurs FROM fenster WHERE status='faellig' "
                           "AND mail_am IS NULL AND geschlossen_am IS NULL"):
            if (letzter - _tag(r[4])).days <= MAIL_HOECHSTENS_T and r[0] in bestand:
                erg["faellig"].append({"symbol": r[0], "start": r[1], "startkurs_usd": r[2], "ende": r[3], "ausloese_tag": r[4],
                                       "ausloese_kurs": r[5], "menge": bestand[r[0]]})
        c.commit()
    finally:
        c.close()
    return erg


def vermerke_mail(ordner: str, symbol: str, start: str) -> None:
    c = oeffne(ordner)
    try:
        c.execute("UPDATE fenster SET mail_am=?, status='gemailt' WHERE symbol=? AND start=?",
                  (datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"), symbol, start))
        c.execute("INSERT INTO protokoll VALUES (?,?,?,?)", (datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"), symbol, "gemailt", "Mitnahme-Mail"))
        c.commit()
    finally:
        c.close()


# ══ die Mail (E-91: Coin · was tun · bis wann · warum) ══════════════════════════════════════════════════════════════════════
def mail(fall: dict, btc_faktor: float | None = None, ausserhalb_binance: bool = False, gestakt: float | None = None,
         verw_text: str | None = None, makro_text: str | None = None, ampel_text: str | None = None) -> tuple:
    s = fall["symbol"]
    x = fall["ausloese_kurs"] / fall["startkurs_usd"]
    haelfte = fall["menge"] / 2.0
    b = "Spot: Hälfte von %s verkaufen oder in EURCV tauschen" % s   # Nutzer 17.10.: tauscht oft in EURCV statt in Fiat
    z = ["1  WAS ZU TUN IST",
         "  %s: die HÄLFTE verkaufen oder in EURCV tauschen – heute (%s Stück von %s)." % (s, _menge(haelfte), _menge(fall["menge"])),
         "  %s" % EURCV_SATZ,
         "  Den Rest weiter halten; das laufende Fenster endet am %s." % _de(fall["ende"])]
    if gestakt:
        z.append("  Davon gestakt: %s Stück – bei Bitpanda wie Spot verkauf- und tauschbar." % _menge(gestakt))
    z += ["", "2  WARUM",
          "  Der Kurs hat sich seit dem Start am %s verdreifacht: Tagesschluss %s USD am %s = %s × Startkurs %s USD." % (
              _de(fall["start"]), _zahl(fall["ausloese_kurs"]), _de(fall["ausloese_tag"]), ("%.2f" % x).replace(".", ","),
              _zahl(fall["startkurs_usd"])),
          "  " + BELEG + "."]
    if ausserhalb_binance:
        z.append("  Hinweis: Die Regel ist auf Coins des Binance-Universums gemessen; %s liegt außerhalb – angewandt, nicht auf ihm gemessen." % s)
    z += ["", "3  KONTEXT (keine Handlung)"]
    if btc_faktor is not None:
        z.append("  Gegen BTC seit dem Start: %+.0f %%." % (100 * (x / btc_faktor - 1)))
    z.append("  Kosten bei Bitpanda je Seite nach Klasse: H %s %% · M %s %% · S %s %% (nur Information, nicht Teil der Regel)." % tuple(
        ("%.2f" % KOSTEN_JE_SEITE[k]).replace(".", ",") for k in ("H", "M", "S")))
    z.append("  Der Erlös: Wohin er geht, ist nicht gemessen – in der Messung lag er still (Dollar).")
    if verw_text:                                                # P22 (15.10.2026): Verwaesserung als Fakt, nicht Teil der Regel
        from agent import verwaesserung as _VW
        z.append("  " + verw_text + ".")
        z.append("  (" + _VW.MESSLAGE + ".)")
    if makro_text:                                               # O54 (15.10.2026): Makro-Lage als Fakt, Gewichtung beim Nutzer
        z.append("  Makro " + makro_text + ".")
    if ampel_text:                                               # P19 (17.10.2026): Season-Ampel als Fakt, loest nichts aus
        z.append("  Season-Ampel " + ampel_text + ".")
    z += ["", "4  TECHNIK", "  Spot B1 Mitnahme ×3 · Fenster %s bis %s · Dollar-Tagesschluss (price_history_ohlc) · Verkauf am Folgetag wie gemessen." % (
        fall["start"], fall["ende"])]
    return b, "\n".join(z)


def _menge(m: float) -> str:
    return ("%.8f" % m).rstrip("0").rstrip(".").replace(".", ",")


def _zahl(x: float) -> str:
    return ("%.6g" % x).replace(".", ",")


def _de(s: str) -> str:
    return _tag(s).strftime("%d.%m.%Y")


# ══ Lesen fuer Statusseite und Teilexport ═══════════════════════════════════════════════════════════════════════════════════
def stand(ordner: str) -> dict:
    p = os.path.join(ordner, ABLAGE)
    if not os.path.exists(p):
        return {"ablage": False}
    c = _ro(p)
    try:
        offen = c.execute("SELECT COUNT(*), SUM(ausloese_tag IS NOT NULL) FROM fenster WHERE geschlossen_am IS NULL").fetchone()
        je = [tuple(r) for r in c.execute("SELECT status, COUNT(*) FROM fenster GROUP BY status ORDER BY 2 DESC")]
        letzte = [tuple(r) for r in c.execute("SELECT am, symbol, art, text FROM protokoll ORDER BY rowid DESC LIMIT 6")]
        naechste = [tuple(r) for r in c.execute("SELECT symbol, start, ende FROM fenster WHERE geschlossen_am IS NULL ORDER BY ende LIMIT 3")]
        return {"ablage": True, "offen": offen[0] or 0, "ausgeloest_offen": offen[1] or 0, "je_status": je, "letzte": letzte, "naechste_enden": naechste}
    finally:
        c.close()
