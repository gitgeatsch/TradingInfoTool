"""Gegenpruefung SN-2: echter build_scheduler auf einer Wegwerf-DB, Uhr gestellt.
Kein Start des Schedulers (start() wird nie gerufen) - es werden nur die geplanten
naechsten Laeufe gelesen."""
import os, sys, sqlite3, tempfile, datetime as D
sys.path.insert(0, r"D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool")
os.chdir(r"D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool")
import database.db as db
tmp = tempfile.mkdtemp()
db.DB_PATH = os.path.join(tmp, "wegwerf.db")
_c0 = sqlite3.connect(db.DB_PATH); _c0.row_factory = sqlite3.Row; db.init_db(_c0); _c0.close()
import scheduler.background as BG

def fabrik():
    c = sqlite3.connect(db.DB_PATH); c.row_factory = sqlite3.Row; return c

JOBS = ("refresh_aktien_ohlc", "backward_tracking", "portfolio_wert", "ausstiegs_empfehlungen")
def lauf(uhr, gestern=True):
    c = fabrik()
    c.execute("CREATE TABLE IF NOT EXISTS job_laeufe (job_id TEXT PRIMARY KEY, zuletzt_am TEXT NOT NULL)")
    c.execute("DELETE FROM job_laeufe")
    if gestern:
        for j in JOBS:
            c.execute("INSERT INTO job_laeufe VALUES (?,?)", (j, (uhr - D.timedelta(days=1)).isoformat()))
    c.commit(); c.close()
    class Uhr(D.datetime):
        @classmethod
        def now(cls, tz=None):
            return uhr if tz is None else uhr.replace(tzinfo=D.datetime.now().astimezone().tzinfo).astimezone(tz)
    alt = BG.datetime; BG.datetime = Uhr
    try:
        s = BG.build_scheduler(None, None, fabrik, lambda: [])
    finally:
        BG.datetime = alt
    erg = {}
    for j in JOBS:
        job = s.get_job(j)
        nr = getattr(job, "next_run_time", None) or job.trigger.get_next_fire_time(None, uhr.astimezone())
        erg[j] = nr.replace(tzinfo=None) if nr else None
    return erg

ok = True
for uhr, soll_nach in [(D.datetime(2026, 10, 3, 6, 22), {"refresh_aktien_ohlc", "backward_tracking"}),
                       (D.datetime(2026, 10, 3, 7, 30), set(JOBS)),
                       (D.datetime(2026, 10, 3, 4, 0), set())]:
    e = lauf(uhr)
    nachgeholt = {j for j, t in e.items() if t is not None and t - uhr < D.timedelta(minutes=5)}
    gut = nachgeholt == soll_nach
    ok &= gut
    print(("OK  " if gut else "FEHL"), "Start", uhr.strftime("%H:%M"), "nachgeholt:", sorted(nachgeholt),
          "| naechste Laeufe:", {j: t.strftime("%d. %H:%M:%S") for j, t in e.items()})
print("SCHLUSS:", "bestanden" if ok else "NICHT bestanden")

# GEGENPROBE: das alte Verhalten (Uhrzeit ignoriert) muss hier auffallen
_neu = BG.nachholen_jetzt
BG.nachholen_jetzt = lambda z, j, h, m: _neu(z, j, 0, 0)
e = lauf(D.datetime(2026, 10, 3, 6, 22))
BG.nachholen_jetzt = _neu
alt_nach = {j for j, t in e.items() if t - D.datetime(2026, 10, 3, 6, 22) < D.timedelta(minutes=5)}
print("GEGENPROBE altes Verhalten, Start 06:22 -> nachgeholt", sorted(alt_nach),
      "| Ausstieg", e["ausstiegs_empfehlungen"].strftime("%H:%M:%S"), "->",
      "faellt auf" if "ausstiegs_empfehlungen" in alt_nach else "FAELLT NICHT AUF")
