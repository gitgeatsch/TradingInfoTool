"""P22 Verwaesserung als FAKT in Mail und Statusseite (15.10.2026; Voranalyse_Spot_Neubau_04_10.md §53, §54).

Nutzer 15.10.: *"Ja, P22 bauen, pruefen und gegenpruefen"* · *"haette gerne immer die Verwaesserung auch beim Kauf"* · *"die GUI nutze
ich nur zur Wartung ... der Rest kommt alles per eMail"*.

WAS ES IST: die Umlaufmenge (Free Float, CoinGecko, ``umlaufmenge_cg.db``) heute gegen vor 90 Tagen, log und als Prozent, und ihr
Fuenftel in der B4-Klasse (H/M/S nach Marktwert, dasselbe Universum wie B4). Fuenftel 5 = staerkste, 1 = geringste Verwaesserung.

WAS ES NICHT IST: kein Ausloeser, keine eigene Mail, keine Begruendung einer Handlung (Regel 4), kein Gewicht in B4 (die B4-Regel bleibt
bitgleich). Es steht als Faktenzeile in Mails, die ohnehin eine Handlung tragen (B4, B1, B3, REGEL0-Signal = "beim Kauf"), und auf der
Statusseite.

GEMESSEN (§54.1, Betriebsform = B4-Universum und B4-Klassen, 01-06/2026): geringstes Fuenftel +5,8 log-Pp in 90 T gegen die Klasse
(p 0,015), staerkstes -3,8 (p 0,055, nicht belegt); EIN Jahr, EIN Regime. Deshalb steht der Satz MESSLAGE dabei.

DATEN: die Rechnung am Monatsstichtag schreibt ``verw_universum`` (alle Coins des B4-Universums) in ``data/spot_betrieb.db``.
Fuer Mails zwischen den Stichtagen wird der Wert HEUTE aus der Mengenreihe gelesen und an den Fuenftelgrenzen der Klasse vom letzten
Stichtag eingeordnet. Lesegrenze wie B4 (``spot_abbau._asof``: der Wert darf hoechstens 7 T alt sein). NUR LESEND auf der Mengenreihe.
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import date, datetime, timezone

import numpy as np
import pandas as pd

TAGE = 90
MIN_ZELLE = 10                    # wie B4: ein Fuenftel nur in Klassen mit >= 10 Coins mit Wert
MESSLAGE = ("Verwässerung = wie stark die Umlaufmenge in 90 Tagen gewachsen ist (Freigaben, Ausgabe). Fakt, nicht Teil der Regel. "
            "Gemessen 01–06/2026: das geringste Fünftel lag 90 Tage später +5,8 Prozentpunkte über seiner Klasse (belegt), das "
            "stärkste −3,8 (nicht belegt) – ein Jahr, ein Marktregime")
WORT = {5: "stärkstes Fünftel", 4: "4. Fünftel", 3: "Mitte", 2: "2. Fünftel", 1: "geringstes Fünftel"}


def _ablage(ordner: str) -> str:
    from agent import spot_mitnahme as SM
    return os.path.join(ordner, SM.ABLAGE)


def schema(c: sqlite3.Connection) -> None:
    c.execute("CREATE TABLE IF NOT EXISTS verw_universum (stichtag TEXT, symbol TEXT, klasse TEXT, verw90 REAL, fuenftel INTEGER, "
              "PRIMARY KEY (stichtag, symbol))")
    c.execute("CREATE TABLE IF NOT EXISTS verw_grenzen (stichtag TEXT, klasse TEXT, grenzen TEXT, n INTEGER, PRIMARY KEY (stichtag, klasse))")


def wert(reihe: pd.Series | None, t) -> float | None:
    """log(Umlauf t / Umlauf t-90) mit der B4-Lesegrenze; None, wenn einer der beiden Werte fehlt."""
    if reihe is None:
        return None
    from agent import spot_abbau as SA
    t = pd.Timestamp(t)
    a, b = SA._asof(reihe, t), SA._asof(reihe, t - pd.Timedelta(days=TAGE))
    if not a or not b:
        return None
    return float(np.log(a / b))


def fuenftel_je_klasse(z: pd.DataFrame) -> tuple:
    """``z``: DataFrame mit ``sym``, ``kl``, ``v`` (log-Wachstum oder NaN). -> (Series Fuenftel je sym, {Klasse: (Grenzen, n)}).
    Grenzen = die 20/40/60/80-Perzentile der Klasse; dieselbe Einteilung wie die Messung (Rang in der Zelle, p > 0,8 = Fuenftel 5)."""
    q = pd.Series(np.nan, index=z.sym.values)
    grenzen = {}
    for k, g in z.groupby("kl"):
        g = g[g.v.notna()]
        if len(g) < MIN_ZELLE:
            continue
        p = g.v.rank(pct=True)
        q[g.sym.values] = np.clip(np.ceil(p.values * 5), 1, 5)
        grenzen[k] = ([float(x) for x in np.quantile(g.v.values, [0.2, 0.4, 0.6, 0.8])], int(len(g)))
    return q, grenzen


def speichere(c: sqlite3.Connection, stichtag: str, z: pd.DataFrame, reihen: dict) -> int:
    """Am B4-Stichtag: Verwaesserung fuer das ganze Universum ``z`` (sym, kl) - schreibt nur verw_universum / verw_grenzen."""
    schema(c)
    z = z[["sym", "kl"]].copy()
    z["v"] = [wert(reihen.get(s), stichtag) for s in z.sym]
    z["v"] = z.v.astype(float)
    q, grenzen = fuenftel_je_klasse(z)
    c.execute("DELETE FROM verw_universum WHERE stichtag=?", (stichtag,))
    c.executemany("INSERT INTO verw_universum VALUES (?,?,?,?,?)",
                  [(stichtag, s, k, None if v != v else float(v), None if q[s] != q[s] else int(q[s])) for s, k, v in zip(z.sym, z.kl, z.v)])
    c.execute("DELETE FROM verw_grenzen WHERE stichtag=?", (stichtag,))
    c.executemany("INSERT INTO verw_grenzen VALUES (?,?,?,?)", [(stichtag, k, json.dumps(g), n) for k, (g, n) in grenzen.items()])
    return int(z.v.notna().sum())


def _einordnen(v: float, grenzen: list) -> int:
    return int(1 + sum(v > g for g in grenzen))


def _binance(symbol: str) -> str:
    from agent import spot_abbau as SA
    try:
        return SA._zuordnung().get(symbol, (symbol, 1.0))[0]
    except Exception:                                            # noqa: BLE001
        return symbol


def fakt(ordner: str, symbol: str, heute: date | None = None, reihen: dict | None = None) -> dict | None:
    """Die Verwaesserung eines Coins als Fakt: {'heute', 'fuenftel', 'klasse', 'stichtag', 'v_stichtag', 'q_stichtag', 'text'} oder
    {'text': Grund} wenn nichts da ist. ``symbol`` = Bestand- oder Binance-Symbol (Zuordnung wie B4). Scheitert nie."""
    try:
        heute = heute or datetime.now(timezone.utc).date()
        b = _binance(symbol)
        if reihen is None:
            from agent import spot_abbau as SA
            reihen = SA._umlauf(ordner)
        r = reihen.get(b) if reihen else None
        v = wert(r, heute)
        aus = {"symbol": symbol, "reihe": b, "hat_reihe": r is not None, "heute": v, "fuenftel": None, "klasse": None, "stichtag": None,
               "v_stichtag": None, "q_stichtag": None}
        p = _ablage(ordner)
        if os.path.exists(p):
            from agent import spot_mitnahme as SM
            c = SM._ro(p)
            try:
                if c.execute("SELECT 1 FROM sqlite_master WHERE name='verw_universum'").fetchone():
                    zeile = c.execute("SELECT stichtag, klasse, verw90, fuenftel FROM verw_universum WHERE symbol=? ORDER BY stichtag DESC LIMIT 1",
                                      (b,)).fetchone()
                    if zeile:
                        aus.update(stichtag=zeile[0], klasse=zeile[1], v_stichtag=zeile[2], q_stichtag=zeile[3])
                        g = c.execute("SELECT grenzen FROM verw_grenzen WHERE stichtag=? AND klasse=?", (zeile[0], zeile[1])).fetchone()
                        if g and v is not None:
                            aus["fuenftel"] = _einordnen(v, json.loads(g[0]))
            finally:
                c.close()
        aus["text"] = text(aus)
        return aus
    except Exception as exc:                                     # noqa: BLE001
        return {"symbol": symbol, "text": "Verwässerung nicht lesbar (%s)" % type(exc).__name__}


def _pct(v: float) -> str:
    return ("%+.1f %%" % (100 * np.expm1(v))).replace(".", ",")


def text(f: dict) -> str:
    """Eine Zeile fuer die Mail."""
    if f.get("heute") is None and f.get("v_stichtag") is None:
        if not f.get("hat_reihe"):
            return "Verwässerung 90 T: für %s gibt es keine Mengenreihe (CoinGecko-Umlauf nicht erfasst)" % f.get("reihe")
        return "Verwässerung 90 T: noch keine 90 Tage Mengenhistorie"
    if f.get("heute") is not None:
        t = "Umlaufmenge %s in 90 Tagen" % _pct(f["heute"])
        if f.get("fuenftel"):
            t += " (%s der Klasse %s, Grenzen vom Stichtag %s)" % (WORT[f["fuenftel"]], f["klasse"], _de(f["stichtag"]))
        elif f.get("klasse") is None:
            t += " (nicht im B4-Universum – ohne Einordnung)"
        return t
    return "Umlaufmenge %s in 90 Tagen am Stichtag %s (%s der Klasse %s; heute kein frischer Wert)" % (
        _pct(f["v_stichtag"]), _de(f["stichtag"]), WORT.get(f["q_stichtag"], "ohne Fünftel"), f["klasse"])


def _de(s: str) -> str:
    return date.fromisoformat(str(s)[:10]).strftime("%d.%m.%Y")


def mailteil(ordner: str, symbol: str, heute: date | None = None) -> dict:
    """Fuer die REGEL0-Signalmail (Muster ``ankuendigung``): {'ein': Zeile, 'technik': [(k, v)]}."""
    f = fakt(ordner, symbol, heute)
    return {"ein": f["text"], "technik": [("Verwässerung", "Fakt, nicht Teil der Regel (P22) · " + MESSLAGE)]}


def stand_bestand(ordner: str, bestand_reihen: dict) -> list:
    """Statusseite: Bestandscoins im staerksten Fuenftel am letzten Stichtag. ``bestand_reihen``: {Bestandsymbol: Binance-Symbol}.
    -> [(Symbol, Prozent-Text, Klasse, Stichtag)]."""
    p = _ablage(ordner)
    if not os.path.exists(p):
        return []
    from agent import spot_mitnahme as SM
    c = SM._ro(p)
    try:
        if not c.execute("SELECT 1 FROM sqlite_master WHERE name='verw_universum'").fetchone():
            return []
        t = c.execute("SELECT MAX(stichtag) FROM verw_universum").fetchone()[0]
        if not t:
            return []
        w = {r[0]: r[1:] for r in c.execute("SELECT symbol, klasse, verw90, fuenftel FROM verw_universum WHERE stichtag=?", (t,))}
    finally:
        c.close()
    aus = []
    for s, b in sorted(bestand_reihen.items()):
        x = w.get(b)
        if x and x[2] == 5 and x[1] is not None:
            aus.append((x[1], s, _pct(x[1]), x[0], t))
    return [r[1:] for r in sorted(aus, reverse=True)]


def text_stichtag(v: float | None, q: int | None) -> str:
    """Kurzform fuer die B4-Mail (Fakten am Stichtag)."""
    if v is None:
        return "Verwässerung 90 T: keine Mengenreihe oder noch keine 90 Tage Historie"
    return "Verwässerung 90 T %s%s" % (_pct(v), (" (%s)" % WORT[q]) if q else "")
