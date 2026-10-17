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
    """A2 (+A4): Messstand seit START und rollierend FENSTER_T Tage, je Gruppe; dazu der LLM-Pruefblock gegen den Ausgang."""
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
        rows = c.execute("SELECT a.signalstunde, a.e24, a.q, s.hebel_schalter, s.stufe, s.zusatz FROM ausgang a JOIN signal s "
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
    aus.update(vorhanden=True, seit=rows[0][0][:10] if rows else None, zuletzt=zuletzt, ohne_kurse=ohne, offen=offen,
               gesamt=gesamt, befund=_befund(gesamt),
               fenster=_kennzahl([x for x, r in zip(z, rows) if r[0] >= grenze]),
               gruppen={name: _kennzahl([x for x, r in zip(z, rows) if f(r)]) for name, f in (
                   ("Hebel-Schalter an", lambda r: r[3] == 1), ("Schalter aus", lambda r: r[3] != 1), ("Stufe 5", lambda r: r[4] == 5),
                   ("Stufe 3", lambda r: r[4] == 3), ("Stufe 2", lambda r: r[4] == 2), ("Zusatz-Assets", lambda r: r[5] == 1))},
               llm={u: _kennzahl([(r[1][:10], r[2], r[3]) for r in llm if r[0] == u]) for u in sorted({r[0] for r in llm})},
               referenz={"mittel": REF_MITTEL, "q": REF_Q, "halb": REF_HALB, "quelle": "Messung 2025-01..2026-08 (bestand, 497 Tage)"})
    return aus


def _pp(x: float) -> str:
    return ("%+.2f %%" % (100 * x)).replace(".", ",")


def zeile(st: dict | None = None, ordner: str | None = None) -> str:
    """Die EINE Zeile fuer Mail, Statusseite und Teilexport - mit Spanne und Tagen, damit sie nicht genauer wirkt, als sie ist."""
    if st is None:
        from agent import regel0_nachlader as NL
        st = stand(ordner or NL.DATEN_VORGABE)
    g = (st or {}).get("gesamt") or {}
    if not g.get("n"):
        return "Messstand im Betrieb: noch keine abgeschlossenen 24-h-Ausgänge"
    sp = ("%s bis %s" % (_pp(g["mittel"] - g["halb"]), _pp(g["mittel"] + g["halb"]))) if g["halb"] == g["halb"] else "–"
    an = (st.get("gruppen") or {}).get("Hebel-Schalter an") or {}
    return ("seit %s %d Signale an %d Tagen: 24-h-Ertrag im Mittel %s (Spanne 99 %%: %s), Messung %s – %s%s. Ein Tag zählt wie eine "
            "Beobachtung; ob der Vorteil die Kosten (0,48 %%) schlägt, ist so erst nach Jahren entscheidbar") % (
        _t(st["seit"] + " 00:00").strftime("%d.%m."), g["n"], g["tage"], _pp(g["mittel"]), sp, _pp(REF_MITTEL), st.get("befund"),
        (" · Schalter an: %d an %d Tagen, %s" % (an["n"], an["tage"], _pp(an["mittel"]))) if an.get("n") else "")


def mailteil(ordner: str | None = None) -> dict:
    """Fuer die REGEL0-Signalmail (Muster ``termin``/``makro``): {'ein': Zeile, 'technik': [(k, v)]}."""
    return {"ein": zeile(ordner=ordner), "technik": [("Messstand im Betrieb", "Fakt, nicht Teil der Regel (O21) · gemessen wie die Referenz "
                                                                  "(Einstiegsstunde, 24 h, ±5 %); Spanne über Tage (Schritt7 §23.64)")]}


# ══ A3: echte Trades ═══════════════════════════════════════════════════════════════════════════════════════════════════════
def trades(conn_prod, ordner: str) -> list:
    """Je Lebenszyklus aus dem Hebel-Buch ab START: das REGEL0-Signal desselben Assets (Eroeffnung 1-26 h nach der Signalstunde)
    oder 'eigene Entscheidung', Verzug zum gemessenen Einstieg, Haltedauer gegen die Regel 24 h. FAKT - kein Ergebnis in EUR
    (Bitpanda bucht Eigenkapital, Kredit, Teilverkauf und Uebertrag getrennt; Stufe 1b)."""
    from agent import regel0_ablage as AB
    import importer.hebel_buch as HB
    p = os.path.join(ordner, AB.ABLAGE_NAME)
    if conn_prod is None or not os.path.exists(p):
        return []
    if not conn_prod.execute("SELECT 1 FROM sqlite_master WHERE name=?", (HB.TABELLE,)).fetchone():
        return []
    zy = [z for z in HB.lebenszyklen(conn_prod) if str(z["auf"])[:16].replace("T", " ") >= START]
    c = _ro(p)
    try:
        sig = c.execute("SELECT COALESCE(bitpanda, symbol), signalstunde, einstieg, stufe, hebel_schalter FROM signal WHERE signalstunde >= ?",
                        (START,)).fetchall()
    finally:
        c.close()
    aus = []
    for z in zy:
        auf = datetime.fromisoformat(str(z["auf"]).replace("Z", "")[:19])
        zu = datetime.fromisoformat(str(z["zu"]).replace("Z", "")[:19]) if z.get("zu") else None
        kand = [s for s in sig if str(s[0]).upper() == z["symbol"].upper() and 1 <= (auf - _t(s[1])).total_seconds() / 3600 <= 26]
        s = kand[-1] if kand else None
        aus.append({"symbol": z["symbol"], "auf": auf.strftime(FMT), "zu": zu.strftime(FMT) if zu else None,
                    "status": "liquidiert" if z.get("liquidiert") else ("geschlossen" if zu else "offen"),
                    "dauer_h": ((zu or datetime.now(timezone.utc).replace(tzinfo=None)) - auf).total_seconds() / 3600,
                    "signal": s[1] if s else None, "stufe": s[3] if s else None, "schalter": s[4] if s else None,
                    "verzug_h": ((auf - _t(s[2])).total_seconds() / 3600) if s else None})
    return aus


def trade_text(t: dict) -> str:
    d = "%.0f h%s" % (t["dauer_h"], "" if t["status"] != "offen" else " bisher")
    if t["signal"]:
        return "%s %s → %s · %s · REGEL0-Signal %s (Stufe %s), eröffnet %.1f h nach dem gemessenen Einstieg · Haltedauer %s (Regel 24 h)" % (
            t["symbol"], t["auf"], t["zu"] or "offen", t["status"], t["signal"], t["stufe"], t["verzug_h"], d)
    return "%s %s → %s · %s · ohne REGEL0-Signal in den 26 h davor (eigene Entscheidung) · Haltedauer %s" % (
        t["symbol"], t["auf"], t["zu"] or "offen", t["status"], d)
