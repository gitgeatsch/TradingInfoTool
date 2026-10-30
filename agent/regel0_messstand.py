"""REGEL0-Messstand im Betrieb - laufende Ergebnismessung der Signale (O21 Stufe 1, 17.10.2026; Schritt7 §23.64).

Nutzer 17.10.: *"ja A1 bis A6 bauen, finde die Zeile fuer den Messstand sollte sofort vorhanden sein"*.

DIE MESSUNG (wie die Referenz, R-R11 bitgleich 10.732/10.732 in p61 Teil 0):
    Einstieg   Schluss der EINSTIEGSstunde (Signal + 1 h; in der Referenz die Spalte ``stunde``)
    Ausgang    24-h-Ertrag = Schluss Einstieg + 24 h / Schluss Einstieg - 1 · t_u / t_d = erste Stunde mit Hoch >= +5 % bzw. Tief
               <= -5 % (``E2.ergebnisse``, 72 h) · A24 = +5 % zuerst binnen 24 h, B24 = -5 % zuerst · Q = A24 - B24 (Trefferbilanz)
    Kurse      DIESELBEN Stundenkurse wie die Rechnung (stundenkurse.db, dann stundenkurse_alle.db - die erste Datei gewinnt);
               ohne lueckenlose Kurse ''ohne_kurse'', nie still
    fertig     24-h-Teil, sobald die Stunde Einstieg + 24 abgeschlossen ist; t_u/t_d endgueltig nach 72 h

⚠️⚠️ WAS DER MESSSTAND KANN UND WAS NICHT (p61 Teil 1, Gegenprobe G2): Alle Einstiege eines Tages sehen denselben Markt - ein Tag
zaehlt wie EINE Beobachtung. Das 95-%-Intervall des Mittels ist nach 90 Tagen etwa +-1,2 Pp, nach einem Jahr +-0,6 Pp breit; der Befund nutzt 99 % (NIVEAU).
    kann     zeigen, ob der Betrieb IM BAND DER MESSUNG laeuft (grobe Brueche: Daten, Zuordnung, ein Regime, das die Regel umkehrt)
    kann NICHT  entscheiden, ob der Vorteil je Handel die Kosten (0,48 % je Tageshandel) schlaegt - dafuer braucht es Jahre
Darum steht neben jeder Zahl die Spanne und die Zahl der TAGE, und der Befund ''im Band'' erst ab ``MIN_TAGE`` Tagen.

Schreibt NUR die REGEL0-Ablage (Tabelle ``ausgang``); liest die Stundenkurse und - fuer die echten Trades - das Hebel-Buch der
Produktion nur. Keine Mail (Information ohne Handlung); die Zeile ``zeile()`` geht als Fakt in die REGEL0-Signalmail.
"""
from __future__ import annotations

import logging
import os
import sqlite3
from datetime import datetime, timedelta, timezone

import numpy as np

logger = logging.getLogger(__name__)

KURSE = ("stundenkurse.db", "stundenkurse_alle.db")
HMAX = 72
START = "2026-10-03 00:00"               # Betriebsbeginn REGEL0 (S7-4, 03.10.2026)
FENSTER_T = 90                           # rollierender Messstand
MIN_TAGE = 10                            # darunter kein Befund 'im Band' (zu wenige Beobachtungen fuer ein Intervall)
# ⚠️ NIVEAU 99 % statt 95 % (Selbsttest o21_gegenprobe, 17.10.): Tage mit grossen Marktbewegungen machen die Tagesmittel dickschwaenzig -
# mit 95 % meldete der Befund bei einem Betrieb GENAU wie die Messung zu oft eine Abweichung (10 T 12,5 %, 30 T 9,2 %, 180 T 5,7 %);
# mit 99 % 5,2 / 3,3 / 1,4 % - nie ueber dem Sollwert 5 %. Angezeigt wird dasselbe Band, damit Zahl und Befund zusammenpassen
NIVEAU = 0.99
# Referenz: Messung kern48jbz bestand 2025-01..2026-08 (p61 Teil 1): 8.408 Einstiege an 497 Tagen
REF_MITTEL, REF_Q, REF_HALB = 0.00545, 0.071, 0.0049
KOSTEN = 0.0048
FMT = "%Y-%m-%d %H:%M"


def _ro(p: str) -> sqlite3.Connection:
    return sqlite3.connect("file:%s?mode=ro" % p.replace("\\", "/"), uri=True, timeout=10)


def _t(s: str) -> datetime:
    return datetime.strptime(str(s)[:16], FMT)


def _reihe(ordner: str, symbol: str, ab: datetime, bis: datetime) -> dict:
    """{stunde: (high, low, close)} aus den REGEL0-Kursdateien - die erste Datei gewinnt (wie regel0_llm._reihe_stunden)."""
    aus: dict = {}
    for name in KURSE:
        p = os.path.join(ordner, name)
        if not os.path.exists(p):
            continue
        c = _ro(p)
        try:
            for st, h, lo, cl in c.execute("SELECT stunde, high, low, close FROM stundenkurse WHERE symbol=? AND stunde >= ? AND stunde <= ?",
                                           (symbol, ab.strftime(FMT), bis.strftime(FMT))):
                aus.setdefault(st, (h, lo, cl))
        except sqlite3.Error:
            pass
        finally:
            c.close()
    return aus


def ausgang(ordner: str, symbol: str, einstieg: str, jetzt: datetime) -> dict:
    """Der Ausgang EINES Signals. -> {'status': ok|offen|ohne_kurse, 'e24', 'a24', 'b24', 'q', 't_u', 't_d', 'mfe24', 'endgueltig'}"""
    import messe_e2_beitraege as E2
    e = _t(einstieg)
    if jetzt < e + timedelta(hours=25):                       # Stunde Einstieg + 24 ist erst um +25 h abgeschlossen
        return {"status": "offen"}
    bis = min(e + timedelta(hours=HMAX), jetzt - timedelta(hours=1))
    k = _reihe(ordner, symbol, e, bis)
    n = int((bis - e).total_seconds() // 3600) + 1
    zeilen = [k.get((e + timedelta(hours=s)).strftime(FMT)) for s in range(n)]
    if any(z is None or z[2] is None for z in zeilen[:25]) or not zeilen[0][2]:
        return {"status": "ohne_kurse"}
    m = next((i for i, z in enumerate(zeilen) if z is None or z[2] is None), len(zeilen))   # lueckenloser Teil
    h = np.array([z[0] for z in zeilen[:m]], float)
    lo = np.array([z[1] for z in zeilen[:m]], float)
    cc = np.array([z[2] for z in zeilen[:m]], float)
    t, mfe, _v = E2.ergebnisse(h, lo, cc, HMAX, (("u5", 1.05, True), ("d5", 0.95, False)))
    tu, td = int(t["u5"][0]), int(t["d5"][0])
    # E2.ergebnisse klemmt das Fenster an das Reihenende: ein Treffer zaehlt nur, wenn seine Stunde schon in der Reihe liegt
    tu = tu if tu < m else 999
    td = td if td < m else 999
    a24 = int(tu <= 24 and tu < td)
    b24 = int(td <= 24 and td <= tu)
    return {"status": "ok", "e24": float(cc[24] / cc[0] - 1.0), "a24": a24, "b24": b24, "q": a24 - b24, "t_u": tu, "t_d": td,
            "mfe24": float(max(h[1:25]) / cc[0] - 1.0), "endgueltig": int(m > HMAX)}


def _tabelle(c: sqlite3.Connection) -> None:
    c.execute("CREATE TABLE IF NOT EXISTS ausgang (symbol TEXT, signalstunde TEXT, einstieg TEXT, status TEXT, e24 REAL, a24 INTEGER, "
              "b24 INTEGER, q INTEGER, t_u INTEGER, t_d INTEGER, mfe24 REAL, endgueltig INTEGER, berechnet_am TEXT, "
              "PRIMARY KEY (symbol, signalstunde))")


def lauf(ordner: str, jetzt: datetime | None = None) -> dict:
    """A1: misst alle Signale ab START, deren Ausgang fehlt, offen ist oder nicht endgueltig. Schreibt nur ``ausgang``."""
    from agent import regel0_ablage as AB
    jetzt = jetzt or datetime.now(timezone.utc).replace(tzinfo=None)
    jt = jetzt.strftime("%Y-%m-%d %H:%M:%S")
    erg = {"neu": 0, "ok": 0, "offen": 0, "ohne_kurse": 0, "endgueltig": 0}
    c = AB.oeffne(ordner)
    try:
        _tabelle(c)
        da = {(r[0], r[1]): (r[2], r[3]) for r in c.execute("SELECT symbol, signalstunde, status, endgueltig FROM ausgang")}
        sig = c.execute("SELECT symbol, signalstunde, einstieg FROM signal WHERE signalstunde >= ? ORDER BY signalstunde", (START,)).fetchall()
        for sym, sh, ein in sig:
            alt = da.get((sym, sh))
            if alt and alt[0] == "ok" and alt[1]:
                continue
            a = ausgang(ordner, sym, ein, jetzt)
            erg[a["status"]] += 1
            if a["status"] == "offen":
                continue
            if a["status"] == "ok" and a["endgueltig"]:
                erg["endgueltig"] += 1
            erg["neu"] += int(alt is None)
            c.execute("INSERT OR REPLACE INTO ausgang VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (sym, sh, ein, a["status"], a.get("e24"), a.get("a24"), a.get("b24"), a.get("q"), a.get("t_u"), a.get("t_d"),
                       a.get("mfe24"), a.get("endgueltig"), jt))
        c.commit()
    finally:
        c.close()
    return erg


# ══ A2: der Messstand ═══════════════════════════════════════════════════════════════════════════════════════════════════════
def _kennzahl(rows: list) -> dict:
    """rows: [(tag, e24, q)] -> n, Tage, Mittel, Q, Halbbreite auf NIVEAU (cluster-robust ueber Tage; p61 G2: = Bootstrap bei 95 %).

    ⚠️ Mit wenigen Tagen ist die Formel zu eng (12 Tage: 1,46 gegen Bootstrap 1,75 Pp, Pruefstand 17.10.) - darum die Korrektur fuer
    kleine Gruppenzahl: t-Quantil mit T-1 Freiheitsgraden und Faktor sqrt(T/(T-1)). Bei 497 Tagen aendert sie fast nichts."""
    if not rows:
        return {"n": 0, "tage": 0}
    e = np.array([r[1] for r in rows], float)
    q = np.array([r[2] for r in rows], float)
    tage = np.array([r[0] for r in rows])
    m = float(e.mean())
    _, inv = np.unique(tage, return_inverse=True)
    s = np.bincount(inv, weights=e)
    k = np.bincount(inv)
    T = len(k)
    if T > 1:
        from scipy.stats import t as _t_vert
        halb = float(_t_vert.ppf(0.5 + NIVEAU / 2, T - 1) * np.sqrt(T / (T - 1)) * np.sqrt(((s - m * k) ** 2).sum()) / len(e))
    else:
        halb = float("nan")
    return {"n": len(e), "tage": int(len(k)), "mittel": m, "q": float(q.mean()), "halb": halb,
            "a24": float((q == 1).mean()), "b24": float((q == -1).mean())}


def _befund(k: dict) -> str:
    if not k.get("n"):
        return "noch keine Ausgänge"
    if k["tage"] < MIN_TAGE:
        return "zu wenige Tage für ein Urteil (%d, ab %d)" % (k["tage"], MIN_TAGE)
    lo, hi = k["mittel"] - k["halb"], k["mittel"] + k["halb"]
    if lo <= REF_MITTEL <= hi:
        return "im Band der Messung"
    return "UNTER der Messung" if hi < REF_MITTEL else "über der Messung"


def stand(ordner: str, jetzt: datetime | None = None) -> dict:
    """A2 (+A4): Messstand seit START und rollierend FENSTER_T Tage, je Gruppe; dazu der LLM-Pruefblock gegen den Ausgang.

    M1 (17.10.2026, Nutzer: *"wir hatten keine 471 Signale - sollten wir nicht die eMail-Signale rechnen?"*): zwei Sichten -
    ``gemailt`` (``mail_signal_am`` gesetzt = was beim Nutzer ankam) und ``alle`` (die ganze Datenbasis = Pruefung der REGEL);
    die Stufen je Sicht getrennt (``gruppen_gemailt``, ``gruppen``)."""
    from agent import regel0_ablage as AB
    p = os.path.join(ordner, AB.ABLAGE_NAME)
    jetzt = jetzt or datetime.now(timezone.utc).replace(tzinfo=None)
    aus = {"vorhanden": False}
    if not os.path.exists(p):
        return aus
    c = _ro(p)
    try:
        if not c.execute("SELECT 1 FROM sqlite_master WHERE name='ausgang'").fetchone():
            return aus
        rows = c.execute("SELECT a.signalstunde, a.e24, a.q, s.hebel_schalter, s.stufe, s.zusatz, s.mail_signal_am FROM ausgang a JOIN signal s "
                         "ON s.symbol = a.symbol AND s.signalstunde = a.signalstunde WHERE a.status='ok' ORDER BY a.signalstunde").fetchall()
        ohne = c.execute("SELECT COUNT(*) FROM ausgang WHERE status='ohne_kurse'").fetchone()[0]
        offen = c.execute("SELECT COUNT(*) FROM signal s WHERE s.signalstunde >= ? AND NOT EXISTS (SELECT 1 FROM ausgang a WHERE "
                          "a.symbol = s.symbol AND a.signalstunde = s.signalstunde)", (START,)).fetchone()[0]
        llm = []
        if c.execute("SELECT 1 FROM sqlite_master WHERE name='pruefung'").fetchone():
            llm = c.execute("SELECT p.urteil, a.signalstunde, a.e24, a.q FROM pruefung p JOIN ausgang a ON a.symbol = p.symbol AND "
                            "a.signalstunde = p.signalstunde WHERE p.rolle='trader' AND a.status='ok' AND p.urteil IS NOT NULL").fetchall()
        zuletzt = c.execute("SELECT MAX(berechnet_am) FROM ausgang").fetchone()[0]
    finally:
        c.close()
    grenze = (jetzt - timedelta(days=FENSTER_T)).strftime(FMT)
    z = [(r[0][:10], r[1], r[2]) for r in rows]
    gesamt = _kennzahl(z)
    gemailt = _kennzahl([x for x, r in zip(z, rows) if r[6]])
    stufen = (("Stufe 5", lambda r: r[4] == 5), ("Stufe 3", lambda r: r[4] == 3), ("Stufe 2", lambda r: r[4] == 2))
    aus.update(vorhanden=True, seit=rows[0][0][:10] if rows else None, zuletzt=zuletzt, ohne_kurse=ohne, offen=offen,
               gesamt=gesamt, befund=_befund(gesamt), gemailt=gemailt, befund_gemailt=_befund(gemailt),
               fenster=_kennzahl([x for x, r in zip(z, rows) if r[0] >= grenze]),
               gruppen={name: _kennzahl([x for x, r in zip(z, rows) if f(r)]) for name, f in (
                   ("gemailt", lambda r: bool(r[6])), ("nicht gemailt", lambda r: not r[6])) + stufen + (
                   ("Zusatz-Assets", lambda r: r[5] == 1),)},
               gruppen_gemailt={name: _kennzahl([x for x, r in zip(z, rows) if r[6] and f(r)]) for name, f in stufen},
               llm={u: _kennzahl([(r[1][:10], r[2], r[3]) for r in llm if r[0] == u]) for u in sorted({r[0] for r in llm})},
               referenz={"mittel": REF_MITTEL, "q": REF_Q, "halb": REF_HALB, "quelle": "Messung 2025-01..2026-08 (bestand, 497 Tage)"})
    return aus


def _pp(x: float) -> str:
    return ("%+.2f %%" % (100 * x)).replace(".", ",")


def _spanne(k: dict) -> str:
    return ("%s bis %s" % (_pp(k["mittel"] - k["halb"]), _pp(k["mittel"] + k["halb"]))) if k.get("halb") == k.get("halb") else "–"


def zeile(st: dict | None = None, ordner: str | None = None) -> str:
    """Die EINE Zeile fuer Mail, Statusseite und Teilexport - ZUERST die gemailten Signale (M1), dann alle als Pruefung der Regel; mit
    Spanne und Tagen, damit sie nicht genauer wirkt, als sie ist."""
    if st is None:
        from agent import regel0_nachlader as NL
        st = stand(ordner or NL.DATEN_VORGABE)
    g = (st or {}).get("gesamt") or {}
    if not g.get("n"):
        return "noch keine abgeschlossenen 24-h-Ausgänge"
    m = st.get("gemailt") or {}
    seit = _t(st["seit"] + " 00:00").strftime("%d.%m.")
    deine = ("deine gemailten Signale seit %s: %d an %d Tagen, 24-h-Ertrag im Mittel %s (Spanne 99 %%: %s) – %s" % (
        seit, m["n"], m["tage"], _pp(m["mittel"]), _spanne(m), st.get("befund_gemailt"))) if m.get("n") else \
        "deine gemailten Signale: noch keine mit 24-h-Ausgang"
    alle = "alle REGEL0-Signale (Prüfung der Regel): %d an %d Tagen, im Mittel %s (Spanne 99 %%: %s), Messung %s – %s" % (
        g["n"], g["tage"], _pp(g["mittel"]), _spanne(g), _pp(REF_MITTEL), st.get("befund"))
    return "%s · %s. Ein Tag zählt wie eine Beobachtung; ob der Vorteil die Kosten (0,48 %%) schlägt, ist so erst nach Jahren entscheidbar" % (
        deine, alle)


def mailteil(ordner: str | None = None) -> dict:
    """Fuer die REGEL0-Signalmail (Muster ``termin``/``makro``): {'ein': Zeile, 'zusatz': [(Label, Text)], 'technik': [(k, v)]}.
    B1 (17.10.2026, Nutzer: *"EUR-Ergebnis auch in die Mail"*): die echten Hebel-Trades als zweite Zeile - Wert zum Schlusskurs."""
    from agent import regel0_nachlader as NL
    ordner = ordner or NL.DATEN_VORGABE
    aus = {"ein": zeile(ordner=ordner), "zusatz": [],
           "technik": [("Messstand im Betrieb", "Fakt, nicht Teil der Regel (O21) · gemessen wie die Referenz (Einstiegsstunde, 24 h, ±5 %); "
                                                "Spanne über Tage (Schritt7 §23.64)")]}
    try:
        p = os.path.join(ordner, "tradinginfotool.db")
        if os.path.exists(p):
            c = _ro(p)
            try:
                txt = trades_zeile(c, ordner)
            finally:
                c.close()
            if txt:
                aus["zusatz"].append(("Deine Hebel-Trades", txt))
                aus["technik"].append(("Hebel-Ergebnis", "Wert zum Schlusskurs aus den Bitpanda-Buchungen (Eigenkapital = EUR-Kauf − Kredit; "
                                                         "Rückfluss = Rest-Coin × Verkaufskurs); keine steuerliche Einordnung (Schritt7 §23.66)"))
    except Exception as exc:                                  # noqa: BLE001
        logger.warning("Messstand: Hebel-Trades nicht lesbar: %s: %s", type(exc).__name__, exc)
    return aus


# ══ Punkt 2 (18.10.2026, Schritt7 §23.68): Haltedauer als gemessener FAKT fuer die Positionsfuehrung (E1-E3) ════════════════
HALTEDAUER_FAKT = ("Gemessen auf den REGEL0-Einstiegen 2025–26 (Schritt7 §23.68): länger als 24 h halten kostete im Mittel 0,3–0,4 % je "
                   "weiteren Tag (nach Gebühr und Finanzierung, auf den Positionswert); 2024 (Aufwärtsjahr) war es umgekehrt – ob "
                   "längeres Halten lohnt, hängt am Marktumfeld, und das ist vorab nicht erkennbar")
# Tief binnen 24 h / binnen 7 Tagen (Anteil der Einstiege, 2025-26, vier Mengen) - die Liquidationsnaehe je Hebelstufe
LIQ_NAEHE = {5: ("−20 %", "0,4–0,6 %", "12–13 %"), 3: ("−33 %", "0,2–0,4 %", "2–4 %")}
REGEL_H = 24


def liq_satz(stufe) -> str | None:
    """'bei 5x liegt die Liquidation etwa bei -20 %: binnen 24 h erreichten das 0,4-0,6 %, binnen 7 Tagen 12-13 % der Einstiege'."""
    try:
        s = int(stufe)
    except (TypeError, ValueError):
        return None
    if s not in LIQ_NAEHE:
        return None
    g, k, l_ = LIQ_NAEHE[s]
    return "bei %dx liegt die Liquidation etwa bei %s: binnen 24 h erreichten das %s der Einstiege, binnen 7 Tagen %s" % (s, g, k, l_)


def zuordnung(ordner: str, symbol: str, eroeffnet) -> dict | None:
    """Das REGEL0-Signal zu einer echten Position: dasselbe Asset, Eroeffnung 1-26 h nach der Signalstunde (wie ``trades``). Nur lesend."""
    from agent import regel0_ablage as AB
    p = os.path.join(ordner, AB.ABLAGE_NAME)
    if not os.path.exists(p) or eroeffnet is None:
        return None
    auf = datetime.fromisoformat(str(eroeffnet).replace("Z", "")[:19]).replace(tzinfo=None) if not isinstance(eroeffnet, datetime) \
        else eroeffnet.replace(tzinfo=None)
    c = _ro(p)
    try:
        rows = c.execute("SELECT COALESCE(bitpanda, symbol), signalstunde, einstieg, stufe, mail_signal_am FROM signal WHERE "
                         "UPPER(COALESCE(bitpanda, symbol)) = ? AND signalstunde >= ? AND signalstunde <= ? ORDER BY signalstunde",
                         (str(symbol).upper(), (auf - timedelta(hours=27)).strftime(FMT), auf.strftime(FMT))).fetchall()
    finally:
        c.close()
    rows = [r for r in rows if 1 <= (auf - _t(r[1])).total_seconds() / 3600 <= 26]     # dieselbe Regel wie ``trades`` (sekundengenau)
    if not rows:
        return None
    r = rows[-1]
    return {"signalstunde": r[1], "einstieg": r[2], "stufe": r[3], "gemailt": bool(r[4])}


def haltedauer_text(ordner: str, symbol: str, eroeffnet, jetzt: datetime | None = None) -> str | None:
    """E3: 'seit 198 h offen (Regel 24 h) · REGEL0-Signal 10.10. 05:00' oder '... · eigene Entscheidung (kein REGEL0-Signal davor)'."""
    if eroeffnet is None:
        return None
    if isinstance(jetzt, str):                       # 30.10.2026: hebelfuehrung.lade nimmt `jetzt` auch als ISO-Text an (TypeError im Log)
        jetzt = datetime.fromisoformat(jetzt.strip().replace("Z", "+00:00"))
    if jetzt is not None and jetzt.tzinfo:
        jetzt = jetzt.astimezone(timezone.utc)
    jetzt = (jetzt or datetime.now(timezone.utc)).replace(tzinfo=None)
    auf = datetime.fromisoformat(str(eroeffnet).replace("Z", "")[:19]).replace(tzinfo=None) if not isinstance(eroeffnet, datetime) \
        else eroeffnet.astimezone(timezone.utc).replace(tzinfo=None) if eroeffnet.tzinfo else eroeffnet
    h = (jetzt - auf).total_seconds() / 3600
    s = zuordnung(ordner, symbol, auf)
    kopf = "seit %.0f h offen" % h
    if s:
        return "%s (Regel %d h%s) · REGEL0-Signal %s" % (kopf, REGEL_H, ", überschritten" if h > REGEL_H else "", _t(s["signalstunde"]).strftime("%d.%m. %H:%M"))
    return "%s · eigene Entscheidung (kein REGEL0-Signal in den 26 h davor)" % kopf


# ══ A3 + B1: echte Trades, Ergebnis in EUR ═════════════════════════════════════════════════════════════════════════════════
EUR_FIAT = "b88b8466-efe3-11eb-b56f-0691764446a7"   # Bitpanda-Waehrung EUR (Fiat) in /v1/operations


def buch(conn_prod) -> list:
    """B1 (Schritt7 §23.66, s1b_voranalyse - dieselbe Rechnung, Gegenprobe 37/37 auf den Cent): Lebenszyklen je Symbol aus
    ``hebel_buch_vorgang.roh`` mit Eigenkapital, Rueckfluss, Gebuehr und Ergebnis zum Schlusskurs. Die Wachen P1-P4 laufen mit;
    ein Zyklus mit Verstoss traegt ``pruefung`` (Liste) und KEIN Ergebnis - nie eine falsche Zahl."""
    import json as _json
    import importer.hebel_buch as HB
    kat = dict(conn_prod.execute("SELECT asset_id, symbol FROM bitpanda_katalog").fetchall())
    ops = conn_prod.execute("SELECT zeit, typ, asset_id, zugang, abgang, kredit_aenderung, roh FROM %s ORDER BY zeit, operation_id"
                            % HB.TABELLE).fetchall()
    f = lambda x: float(x or 0)                                   # noqa: E731
    stand_, aus = {}, []
    for zeit, typ, aid, zu, ab, kd, roh in ops:
        s = kat.get(aid)
        if not s or "short" in typ or not roh:
            continue
        tx = _json.loads(roh).get("transactions") or []
        t = datetime.fromisoformat(zeit.replace("Z", "")[:19])
        b = stand_.get(s)
        if typ == "margin_trading_open_long":
            eur_kauf = sum(f(x["asset_amount"]["value"]) for x in tx if x.get("currency_id") == EUR_FIAT and x.get("flow") == "OUTGOING"
                           and x.get("transaction_type") == "buy")
            kredit = sum(f(x["asset_amount"]["value"]) for x in tx if x.get("wallet_owner") == "margin-trading-credit" and x.get("flow") == "OUTGOING")
            verk = sum(f(x["asset_amount"]["value"]) for x in tx if x.get("transaction_type") == "sell" and x.get("flow") == "OUTGOING"
                       and x.get("wallet_owner") == "shared-default")
            if b is None or b["menge"] <= HB.TOL:
                b = stand_[s] = {"symbol": s, "auf": t, "zu": None, "menge": 0.0, "ek": 0.0, "ek_summe": 0.0, "kredit": 0.0, "tilgung": 0.0,
                                 "rueck": 0.0, "kosten": 0.0, "ergebnis": 0.0, "liquidiert": False, "pruefung": [], "rest_coin": 0.0,
                                 "letzte_auf": t}
            if abs(eur_kauf - verk) > 0.005 or abs(kredit - f(kd)) > 0.005:
                b["pruefung"].append("P3 %s" % zeit[:16])
            b["menge"] += f(zu)
            b["ek"] += eur_kauf - kredit
            b["ek_summe"] += eur_kauf - kredit
            b["kredit"] += kredit
            b["letzte_auf"] = t
            continue
        if b is None or b["menge"] <= HB.TOL:
            continue
        fee = sum(f(x["asset_amount"]["value"]) for x in tx if x.get("transaction_type") == "fee" and x.get("asset_id") == aid)
        verk = sum(f(x["asset_amount"]["value"]) for x in tx if x.get("transaction_type") == "sell" and x.get("asset_id") == aid)
        rate = next((f(x["trade"]["rate"]) for x in tx if x.get("transaction_type") == "sell" and x.get("asset_id") == aid and x.get("trade")), 0.0)
        eur_ein = sum(f(x["asset_amount"]["value"]) for x in tx if x.get("currency_id") == EUR_FIAT and x.get("flow") == "INCOMING"
                      and x.get("transaction_type") == "sell")
        tilg = sum(f(x["asset_amount"]["value"]) for x in tx if x.get("wallet_owner") == "margin-trading-credit" and x.get("flow") == "INCOMING")
        uebertrag = sum(f(x["asset_amount"]["value"]) for x in tx if x.get("asset_id") == aid and x.get("wallet_owner") == "shared-default"
                        and x.get("flow") == "INCOMING" and x.get("transaction_type") == "transfer")
        if abs(f(ab) - (verk + fee + uebertrag)) > 1e-8:
            b["pruefung"].append("P1 %s" % zeit[:16])
        if abs(verk * rate - eur_ein) > 0.011:
            b["pruefung"].append("P4 %s" % zeit[:16])
        anteil = min(f(ab) / b["menge"], 1.0)
        ek_anteil = b["ek"] * anteil
        rueck = uebertrag * rate + (eur_ein - tilg)
        b["rueck"] += rueck
        b["kosten"] += fee * rate
        b["ergebnis"] += rueck - ek_anteil
        b["ek"] -= ek_anteil
        b["tilgung"] += tilg
        b["rest_coin"] += uebertrag
        b["menge"] = max(b["menge"] - f(ab), 0.0)
        b["liquidiert"] |= typ == "margin_trading_liquidation_long"
        if b["menge"] <= HB.TOL:
            b["zu"] = t
            if abs(b["tilgung"] - b["kredit"]) > 0.01:
                b["pruefung"].append("P2")
            aus.append(b)
            del stand_[s]
    return aus + list(stand_.values())


def trades(conn_prod, ordner: str, seit: str = START) -> list:
    """Je Lebenszyklus ab ``seit``: das REGEL0-Signal desselben Assets (Eroeffnung 1-26 h nach der Signalstunde) oder 'eigene
    Entscheidung', Verzug zum gemessenen Einstieg, Haltedauer gegen die Regel 24 h - und (B1) Eigenkapital, Wert zum Schlusskurs,
    Gebuehr, Ergebnis in EUR. ⚠️ Kein 'realisiert': beim Schliessen verkauft Bitpanda nur den Kreditanteil in EUR (zur Tilgung, sofort
    wieder EURCV), der Rest liegt als Coin im Spot-Wallet - die steuerliche Einordnung ist nicht Teil der Rechnung."""
    from agent import regel0_ablage as AB
    import importer.hebel_buch as HB
    if conn_prod is None or not conn_prod.execute("SELECT 1 FROM sqlite_master WHERE name=?", (HB.TABELLE,)).fetchone():
        return []
    p = os.path.join(ordner, AB.ABLAGE_NAME)
    sig = []
    if os.path.exists(p):
        c = _ro(p)
        try:
            sig = c.execute("SELECT COALESCE(bitpanda, symbol), signalstunde, einstieg, stufe, hebel_schalter FROM signal WHERE signalstunde >= ?",
                            (START,)).fetchall()
        finally:
            c.close()
    jetzt = datetime.now(timezone.utc).replace(tzinfo=None)
    aus = []
    for z in buch(conn_prod):
        auf, zu = z["auf"], z["zu"]
        if auf.strftime(FMT) < seit:
            continue
        kand = [s for s in sig if str(s[0]).upper() == z["symbol"].upper() and 1 <= (auf - _t(s[1])).total_seconds() / 3600 <= 26]
        s = kand[-1] if kand else None
        ok = not z["pruefung"]
        aus.append({"symbol": z["symbol"], "auf": auf.strftime(FMT), "zu": zu.strftime(FMT) if zu else None,
                    "status": "liquidiert" if z["liquidiert"] else ("geschlossen" if zu else "offen"),
                    "dauer_h": ((zu or jetzt) - auf).total_seconds() / 3600,
                    "signal": s[1] if s else None, "stufe": s[3] if s else None, "schalter": s[4] if s else None,
                    "verzug_h": ((auf - _t(s[2])).total_seconds() / 3600) if s else None,
                    "eigenkapital": z["ek_summe"], "rueckfluss": z["rueck"] if ok else None, "kosten": z["kosten"] if ok else None,
                    "ergebnis": z["ergebnis"] if ok else None, "ek_offen": z["ek"] if not zu else 0.0, "rest_coin": z["rest_coin"],
                    "pruefung": z["pruefung"]})
    return aus


def _eur(x: float) -> str:
    return ("%+.2f €" % x).replace(".", ",") if x is not None else "–"


def trade_text(t: dict) -> str:
    d = "%.0f h%s" % (t["dauer_h"], "" if t["status"] != "offen" else " bisher")
    kopf = ("%s %s → %s · %s · REGEL0-Signal %s (Stufe %s), eröffnet %.1f h nach dem gemessenen Einstieg · Haltedauer %s (Regel 24 h)" % (
        t["symbol"], t["auf"], t["zu"] or "offen", t["status"], t["signal"], t["stufe"], t["verzug_h"], d)) if t["signal"] else \
        "%s %s → %s · %s · ohne REGEL0-Signal in den 26 h davor (eigene Entscheidung) · Haltedauer %s" % (
            t["symbol"], t["auf"], t["zu"] or "offen", t["status"], d)
    if "eigenkapital" not in t:
        return kopf
    if t.get("pruefung"):
        return kopf + " · Ergebnis NICHT berechnet (Buchung passt nicht: %s)" % ", ".join(t["pruefung"])
    if t["status"] == "offen":
        return kopf + " · Eigenkapital %s € · aus Teilschließungen zum Schlusskurs %s · offen noch %s € Eigenkapital" % (
            ("%.2f" % t["eigenkapital"]).replace(".", ","), _eur(t["ergebnis"]), ("%.2f" % t["ek_offen"]).replace(".", ","))
    return kopf + " · Eigenkapital %s € · Wert zum Schlusskurs %s € · Ergebnis %s (%s auf das Eigenkapital) · Gebühr %s €" % (
        ("%.2f" % t["eigenkapital"]).replace(".", ","), ("%.2f" % t["rueckfluss"]).replace(".", ","), _eur(t["ergebnis"]),
        _pp(t["ergebnis"] / t["eigenkapital"]) if t["eigenkapital"] else "–", ("%.2f" % t["kosten"]).replace(".", ","))


def trade_summen(conn_prod, ordner: str) -> dict:
    """Summen seit START (REGEL0-Betrieb) und seit Beginn des Buchs: Zahl, Eigenkapital, Ergebnis zum Schlusskurs, Gebuehr."""
    def s_(lst):
        ok = [t for t in lst if t["ergebnis"] is not None]
        return {"n": len(lst), "offen": sum(1 for t in lst if t["status"] == "offen"), "nicht_berechnet": len(lst) - len(ok),
                "eigenkapital": sum(t["eigenkapital"] for t in ok), "ergebnis": sum(t["ergebnis"] for t in ok),
                "kosten": sum(t["kosten"] for t in ok)}
    return {"seit_start": s_(trades(conn_prod, ordner)), "seit_beginn": s_(trades(conn_prod, ordner, seit="2000-01-01 00:00"))}


def trades_zeile(conn_prod, ordner: str) -> str | None:
    """B1: die Zeile 'Deine Hebel-Trades' fuer die Signalmail - Summe seit START, dazu der juengste geschlossene Trade."""
    tr = trades(conn_prod, ordner)
    if not tr:
        return None
    s = trade_summen(conn_prod, ordner)["seit_start"]
    zu = [t for t in tr if t["zu"] and t["ergebnis"] is not None]
    letzter = max(zu, key=lambda t: t["zu"]) if zu else None
    # Nutzer 17.10. (Bild: EURCV "Gesamtverlust -50,64 %"): das Eigenkapital geht bei der Eroeffnung als EURCV hinaus, beim Schliessen
    # kommt nur der Rest als COIN zurueck - darum zeigt Bitpanda das Minus beim Stablecoin. Wert zum Schlusskurs, keine steuerliche Aussage
    return ("seit %s: %d Trades (%d offen) · Ergebnis zum Schlusskurs %s auf %s € Eigenkapital · Gebühren %s €%s · ⚠ Wert zum Schlusskurs: "
            "beim Schließen verkauft Bitpanda nur den Kreditanteil, der Rest bleibt als Coin im Spot-Wallet; das Eigenkapital ging als "
            "EURCV hinaus – darum steht das Minus in der Bitpanda-Ansicht beim EURCV") % (
        _t(START).strftime("%d.%m."), s["n"], s["offen"], _eur(s["ergebnis"]), ("%.2f" % s["eigenkapital"]).replace(".", ","),
        ("%.2f" % s["kosten"]).replace(".", ","),
        (" · zuletzt %s %s (%.0f h%s)" % (letzter["symbol"], _eur(letzter["ergebnis"]), letzter["dauer_h"],
                                          ", ohne REGEL0-Signal" if not letzter["signal"] else ", Regel 24 h")) if letzter else "")
