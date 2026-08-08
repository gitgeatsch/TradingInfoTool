"""Ein 504 beim Preisabruf darf die Erfolgsmessung nicht mehr toeten.

DER VORFALL (2026-08-09, Nutzer-Meldung): CoinGecko lieferte ein
"504 Gateway Timeout" auf einen `simple/price`-Aufruf mit 28 IDs. Der Aufruf
holt gebuendelt die Preise fuer ALLE offenen Messungen - die Exception lief bis
scheduler/background.py durch und beendete die gesamte Erfolgsmessung.

WARUM DER FIX AN DER AUFRUFSTELLE SITZT UND NICHT IM CLIENT: api/zai.py haelt
als bewusste Entscheidung fest, dass Timeout/5xx/Verbindungsfehler NICHT
wiederholt werden - "P-8 (kein Hard-Fail, Aufrufer faengt die Exception ab)".
Diese Annahme traf hier nicht zu. Repariert wurde deshalb die Annahme.

GEPRUEFT WIRD BEIDES: dass der Lauf ueberlebt UND dass der Ausfall sichtbar
bleibt. Ein fail-soft, das niemand sieht, ist von "es gab nichts zu pruefen"
nicht zu unterscheiden.

Laeuft gegen eine frische Test-DB, nie gegen die Produktiv-DB.
"""
import pathlib
import sys
import tempfile

SCRATCH = pathlib.Path(tempfile.gettempdir()) / "tit_marktscan_failsoft.db"
if SCRATCH.exists():
    SCRATCH.unlink()

import database.db as db  # noqa: E402

db.DB_PATH = SCRATCH
_c = db.get_connection()
db.init_db(_c)
_c.close()

import agent.krypto.marktscan_backward_tracking as M  # noqa: E402

fehler = []


def pruefe(bedingung, text, info=""):
    if bedingung:
        print(f"  OK   {text}  {info}")
    else:
        print(f"  FEHL {text}  {info}")
        fehler.append(text)


class _Kandidat:
    """Nur die Felder, die `pruefe_messung()` tatsaechlich anfasst - ermittelt
    durch Auslesen der Zugriffe, nicht geraten."""

    def __init__(self, cg_id, symbol, kandidat_id):
        from datetime import datetime, timedelta, timezone
        self.coingecko_id = cg_id
        self.symbol = symbol
        self.id = kandidat_id
        self.price_usd = 1.0
        self.mindestziel_usd = 2.0        # wird im Test nie erreicht (Preis 1,0)
        self.mindestziel_zeitraum_tage_geschaetzt = 5
        self.groq_kurzbegruendung = "x"
        self.einstufung = "kauf"
        self.outcome_status = None
        self.outcome_gestartet_am = (
            datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        self.signale_momentum_json = "{}"


class _CoingeckoKaputt:
    """Verhaelt sich wie der echte Client bei einem 504: raise_for_status()
    wirft eine HTTPError-artige Exception."""

    def __init__(self):
        self.aufrufe = 0

    def get_simple_prices(self, ids, vs_currencies=("usd", "eur")):
        self.aufrufe += 1
        raise RuntimeError("504 Server Error: Gateway Timeout for url: "
                           "https://api.coingecko.com/api/v3/simple/price")


class _CoingeckoOk:
    def __init__(self):
        self.aufrufe = 0

    def get_simple_prices(self, ids, vs_currencies=("usd", "eur")):
        self.aufrufe += 1
        return {i: {"usd": 1.0} for i in ids}


CONFIG = {"marktscan": {"erfolgsmessung": {
    "mindestziel_zeitraum_tage_cap": 30, "schnellerfolg_anteil_max": 0.5}}}

OFFENE = [_Kandidat("bitcoin", "BTC", 1), _Kandidat("ethereum", "ETH", 2)]

# Die Kandidatensuche fuer NEUE Messungen ist hier nicht Gegenstand - sie wird
# stillgelegt, damit der Test genau eine Frage stellt.
alt_offene = db.get_offene_marktscan_messungen
alt_kandidaten = db.get_marktscan_kandidaten_fuer_erfolgsmessung \
    if hasattr(db, "get_marktscan_kandidaten_fuer_erfolgsmessung") else None
db.get_offene_marktscan_messungen = lambda conn: OFFENE
alt_starte = M.starte_messung
M.starte_messung = lambda *a, **kw: None

print("A) DER LAUF UEBERLEBT EINEN 504")
kaputt = _CoingeckoKaputt()
try:
    ergebnis = M.run_marktscan_backward_tracking(
        db.get_connection, kaputt, None, None, [], None, CONFIG)
    pruefe(True, "A1 kein Absturz", "vorher beendete die Exception den ganzen Job")
except Exception as exc:  # noqa: BLE001
    pruefe(False, "A1 kein Absturz", f"{type(exc).__name__}: {exc}")
    ergebnis = {}

pruefe(kaputt.aufrufe == 1, "A2 der Preisabruf wurde genau einmal versucht",
       f"{kaputt.aufrufe}x - kein stiller Retry-Sturm")
pruefe(ergebnis.get("geprueft") == 0, "A3 nichts geprueft",
       "die offenen Messungen bleiben offen (P-10, kein Datenverlust)")

print("\nB) DER AUSFALL BLEIBT SICHTBAR")
grund = ergebnis.get("preis_abruf_fehler")
pruefe(grund is not None, "B1 der Grund steht im Ergebnis",
       "fail-soft darf nicht fail-silent werden")
pruefe(grund is not None and "504" in grund, "B2 mit der echten Fehlermeldung",
       str(grund)[:60])

print("\nC) OHNE FEHLER AENDERT SICH NICHTS")
gut = _CoingeckoOk()
ergebnis2 = M.run_marktscan_backward_tracking(
    db.get_connection, gut, None, None, [], None, CONFIG)
pruefe(ergebnis2.get("preis_abruf_fehler") is None,
       "C1 kein Fehlergrund bei erfolgreichem Abruf")
pruefe(gut.aufrufe == 1, "C2 Preisabruf normal ausgefuehrt")

db.get_offene_marktscan_messungen = alt_offene
M.starte_messung = alt_starte
try:
    SCRATCH.unlink()
except Exception:
    pass

print("\n" + ("ALLE TESTS BESTANDEN" if not fehler else f"{len(fehler)} FEHLER: {fehler}"))
sys.exit(1 if fehler else 0)
