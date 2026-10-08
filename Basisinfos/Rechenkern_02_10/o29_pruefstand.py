"""Pruefstand O29 (Schritt7 §23.28) am SEITENEFFEKT - Wegwerf-Ablage, Versand abgefangen, Standard-DB unberuehrt.

    python Basisinfos/Rechenkern_02_10/o29_pruefstand.py

  A1 Schalter AUS (Vorgabe): kein Abruf, keine Tabellen, keine Mailzeile
  A2 Schalter AN, Meldungen aus dem E-1-Archiv als aufgezeichnete Antworten (kein Netz): Token-Delisting -> Satz mit Ankuendigung und
     Wirksamkeit, Monitoring -> Satz 'seit', Margin/Paar -> KEINE Zeile; Titel und Link in der Technik
  A3 Abruf scheitert -> Lauf mit Fehler abgelegt, die Mail geht OHNE Zeile, sonst vollstaendig
  A4 Vorwaertsprotokoll: jedes Signal bekommt einen Eintrag (auch 'keins')
  A5 der Job am DESKTOP (Messbasis, nicht Betriebsgeraet) tut nichts, auch mit Schalter an - kein Netz, kein Schreiben
  A6 Live-Probe: ein echter Abruf (1 Seite je Katalog) in die Wegwerf-Ablage
  A7 Standard-DB und Messbasen unberuehrt
"""
import os
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
os.chdir(PROJ)
sys.path.insert(0, PROJ)
import agent.binance_ankuendigungen as BA     # noqa: E402
import agent.regel0_ablage as AB              # noqa: E402
import agent.regel0_mail as RM                # noqa: E402

E1 = os.path.join(PROJ, "data", "_e1", "binance_ankuendigungen.db")
ERG = []


def ok(name, b, info=""):
    ERG.append(bool(b))
    print("%s  %s  %s" % ("OK  " if b else "FEHL", name, info), flush=True)


class Antwort:
    def __init__(self, d):
        self._d = d

    def json(self):
        return self._d


class Archiv:
    """Antworten aus dem E-1-Archiv - dieselbe Form wie die Binance-Website (list/detail)."""
    def __init__(self, codes=None, kaputt=False):
        c = sqlite3.connect("file:%s?mode=ro" % E1.replace("\\", "/"), uri=True)
        q = "SELECT code, katalog, titel, release_ms, text FROM meldung" + (" WHERE code IN (%s)" % ",".join("?" * len(codes)) if codes else "")
        self.m = c.execute(q, list(codes or [])).fetchall()
        c.close()
        self.kaputt = kaputt

    def get(self, url, params=None, headers=None, timeout=None):
        if self.kaputt:
            raise ConnectionError("Platzhalter: kein Netz")
        if url == BA.LISTE:
            if params["pageNo"] > 1:
                return Antwort({"data": {"catalogs": [{"articles": []}]}})
            arts = [{"code": x[0], "title": x[2], "releaseDate": x[3]} for x in self.m if x[1] == params["catalogId"]]
            return Antwort({"data": {"catalogs": [{"articles": arts}]}})
        code = params["articleCode"]
        txt = next(x[4] for x in self.m if x[0] == code)
        import json
        return Antwort({"data": {"body": json.dumps({"node": "root", "child": [{"node": "text", "text": txt or ""}]})}})


def signal(d, sym, st, schalter=1):
    c = AB.oeffne(d)
    w = {"symbol": sym, "signalstunde": st, "einstieg": st, "ausstieg": st, "vh": 0.042, "stufe_vorlaeufig": 3, "stufe": 3, "p2": 0.001,
         "p3": 0.007, "p5": 0.1, "hebel_schalter": schalter, "bitpanda": sym, "zusatz": 0, "btc": 0, "version": "REGEL0.1",
         "erfasst_am": st, "kurs": 1.0, "kurs_markt": "spot"}
    c.execute("INSERT OR REPLACE INTO signal (%s) VALUES (%s)" % (",".join(w), ",".join("?" * len(w))), list(w.values()))
    c.commit(); c.close()


def mail_fuer(d, sym, st, an=True):
    signal(d, sym, st)
    jetzt = datetime.strptime(st, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    jetzt = jetzt.replace(minute=10) if jetzt.minute == 0 else jetzt
    from datetime import timedelta
    post = []
    RM.versende(d, lambda b, t, *a, **k: post.append(t) or True, jetzt=jetzt + timedelta(hours=1),
                kurse=lambda: ({sym: 1.0}, {sym + "USDT": 1.0}, {sym: 0.9}),
                ankuendigung=(lambda r: BA.mailteile_aus_ablage(d, r)) if an else None)
    return post[0] if post else ""


def main():
    vorher = {p: os.path.getmtime(p) for p in (os.path.join(PROJ, "data", f) for f in ("tradinginfotool.db", "stundenkurse.db",
                                                                                        "stundenkurse_alle.db")) if os.path.exists(p)}
    c = sqlite3.connect("file:%s?mode=ro" % E1.replace("\\", "/"), uri=True)
    hft = c.execute("SELECT code FROM meldung WHERE titel LIKE 'Binance Will Delist ACX, HFT%'").fetchone()[0]
    stx = c.execute("SELECT code FROM meldung WHERE titel LIKE '%Monitoring Tag to Include ACX, LSK & STX%'").fetchone()[0]
    qnt = [r[0] for r in c.execute("SELECT DISTINCT m.code FROM meldung m JOIN ereignis e ON e.code=m.code WHERE e.symbol='QNT'")]
    c.close()
    codes = [hft, stx] + qnt
    orig = BA.aktiv
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        # A1
        BA.aktiv = lambda: False
        e = BA.lauf(d, os.path.join(PROJ, "data"), http=Archiv(kaputt=True))
        cc = AB.oeffne(d); tab = {r[0] for r in cc.execute("SELECT name FROM sqlite_master WHERE type='table'")}; cc.close()
        t = mail_fuer(d, "HFT", "2026-08-20 10:00")
        ok("A1 Schalter AUS: kein Abruf, keine Tabellen, keine Mailzeile", e == {"aktiv": False} and "ankuendigung" not in tab and "Binance hat" not in t)
        # A2
        BA.aktiv = lambda: True
        e = BA.lauf(d, os.path.join(PROJ, "data"), http=Archiv(codes))
        t_hft = mail_fuer(d, "HFT", "2026-08-21 10:00")
        t_stx = mail_fuer(d, "STX", "2026-08-14 12:00")
        t_qnt = mail_fuer(d, "QNT", "2026-10-04 08:00")
        ok("A2 Abruf aus dem Archiv: Meldungen und Zuordnungen abgelegt", e.get("neu", 0) >= 3 and e.get("zuordnungen", 0) >= 2 and not e.get("fehler"), str(e))
        ok("A2 Token-Delisting: Satz mit Ankuendigung und Wirksamkeit, Titel und Link in der Technik",
           "Binance hat am" in t_hft and "einzustellen" in t_hft and "17.08." in t_hft and "binance.com/en/support/announcement/" in t_hft,
           [z for z in t_hft.splitlines() if "Binance" in z][:2])
        ok("A2 Monitoring: Satz 'seit 24.07.'", "Monitoring-Kennzeichen" in t_stx and "seit 24.07." in t_stx, [z for z in t_stx.splitlines() if "Monitoring" in z][:1])
        ok("A2 nur Margin/Paar (QNT): KEINE Zeile", "Binance hat" not in t_qnt and "Monitoring-Kennzeichen" not in t_qnt and "Binance-Meldung" not in t_qnt)
        # A4
        cc = AB.oeffne(d)
        n_s = cc.execute("SELECT COUNT(*) FROM signal").fetchone()[0]
        n_p = cc.execute("SELECT COUNT(*) FROM signal_ereignis").fetchone()[0]
        n_k = cc.execute("SELECT COUNT(*) FROM signal_ereignis WHERE arten='keins'").fetchone()[0]
        cc.close()
        BA.lauf(d, os.path.join(PROJ, "data"), http=Archiv(codes))
        cc = AB.oeffne(d); n_p2 = cc.execute("SELECT COUNT(*) FROM signal_ereignis").fetchone()[0]; cc.close()
        ok("A4 Vorwaertsprotokoll: jedes Signal hat einen Eintrag (auch 'keins')", n_p2 == cc_n(d) and n_k >= 0, "Signale %d · Eintraege %d" % (cc_n(d), n_p2))
        # A3
        e3 = BA.lauf(d, os.path.join(PROJ, "data"), http=Archiv(kaputt=True))
        t3 = mail_fuer(d, "ICX", "2026-09-01 10:00")
        cc = AB.oeffne(d); f = cc.execute("SELECT ok, fehler FROM ankuendigung_lauf ORDER BY am DESC LIMIT 1").fetchone(); cc.close()
        ok("A3 Abruf scheitert: Lauf mit Fehler abgelegt, Mail geht trotzdem (ohne neue Zeile)", e3.get("fehler") and f[0] == 0 and "REGEL0.1" in t3,
           str(f))
        # A6
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d6:
        BA.aktiv = lambda: True
        try:
            cc = BA.oeffne(d6)
            e6 = BA.hole(cc, os.path.join(PROJ, "data"), seiten=1)
            n6 = cc.execute("SELECT COUNT(*) FROM ankuendigung").fetchone()[0]
            cc.close()
            ok("A6 Live-Probe: echter Abruf, je Katalog eine Seite", n6 >= 50, "%s · Meldungen %d" % (e6, n6))
        except Exception as exc:                                 # noqa: BLE001
            ok("A6 Live-Probe: echter Abruf, je Katalog eine Seite", False, "%s: %s" % (type(exc).__name__, exc))
    # A5
    BA.aktiv = lambda: True
    import scheduler.background as SB
    import logging
    meld = []
    h = logging.Handler(); h.emit = lambda rec: meld.append(rec.getMessage())
    SB.logger.addHandler(h); SB.logger.setLevel(logging.INFO)
    abl = os.path.join(PROJ, "data", "regel0_signale.db")
    m_vor = os.path.getmtime(abl) if os.path.exists(abl) else None
    SB.binance_ankuendigungen_job()
    SB.logger.removeHandler(h)
    ok("A5 Job am Desktop tut nichts (nicht Betriebsgeraet), auch mit Schalter an", any("uebersprungen" in x for x in meld)
       and (os.path.getmtime(abl) if os.path.exists(abl) else None) == m_vor, meld[-1:] if meld else "-")
    BA.aktiv = orig
    nachher = {p: os.path.getmtime(p) for p in vorher}
    ok("A7 Standard-DB und Messbasen unberuehrt", nachher == vorher)
    print("\n%d von %d bestanden" % (sum(ERG), len(ERG)))


def cc_n(d):
    c = AB.oeffne(d)
    n = c.execute("SELECT COUNT(*) FROM signal").fetchone()[0]
    c.close()
    return n


if __name__ == "__main__":
    main()
