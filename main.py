"""Einstiegspunkt: DB init -> Erstimport (falls noetig) -> Scheduler -> UI."""
from __future__ import annotations

import logging
import os
import sys
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path

import config
import database.db as db
import ui.app as app
from api.coingecko import CoinGeckoClient
from api.history import backfill_all
from api.groq import GroqClient
from api.kraken import KrakenClient
from api.kraken_history import backfill_all_ohlc
from importer.excel_import import import_holdings
from scheduler.background import build_scheduler

# U-12-Minimalfix (2026-07-09): bisher NUR Konsole - laeuft die App ohne sichtbares
# Terminal (z.B. als Hintergrundprozess), waren alle Fehler unwiederbringlich
# verloren. Rotierende Datei (max. 5 MB x 3, UTF-8) daneben, damit es auch dann
# eine Log-Datei zum Nachschauen gibt.
LOG_PATH = Path(__file__).resolve().parent / "data" / "tradinginfotool.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(LOG_PATH, maxBytes=5_000_000, backupCount=3, encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def _show_startup_error(title: str, message: str, email_empfaenger: str | None = None) -> None:
    """Betriebssicherheit (2026-07-12): ein unbehandelter Crash VOR der UI landet
    per sys.excepthook nur auf stderr, NICHT durch die logging-Handler oben - laeuft
    die App ohne sichtbares Terminal (z.B. Verknuepfung am 24/7-Notebook), ist das
    sonst komplett unsichtbar. Baut einen minimalen, versteckten Tk-Root nur fuer
    den Dialog, da die eigentliche App-Hauptschleife an dieser Stelle noch nicht laeuft.

    E-Mail-Benachrichtigung (U-8, 2026-07-12): best-effort, wenn `email_empfaenger`
    gesetzt ist - Dialog + Logdatei bleiben so oder so die primaere Absicherung,
    ein E-Mail-Fehlschlag (z.B. kein App-Passwort gesetzt) wird von
    send_notification_email() selbst abgefangen (P-8/P-10)."""
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(title, message)
    root.destroy()

    if email_empfaenger:
        from api.email_notify import send_notification_email

        send_notification_email(f"TradingInfoTool: {title}", message, email_empfaenger)


def main() -> None:
    config.load_env()
    coingecko_api_key = os.environ.get("COINGECKO_API_KEY")
    if coingecko_api_key:
        logger.info("CoinGecko API-Key gefunden (100 Req/Min statt 30).")
    else:
        logger.info("Kein CoinGecko API-Key gesetzt - anonymer Zugriff (30 Req/Min).")

    # KI-Ebene: config.yaml agent.ai_provider waehlt zwischen "groq" (aktiv) und
    # "lokal" (Architektur-Seam vorbereitet, siehe api/local_model.py - noch nicht
    # implementiert, wirft bei tatsaechlicher Nutzung bewusst NotImplementedError
    # statt still zu scheitern, P-10).
    try:
        ai_provider = config.load_config().get("agent", {}).get("ai_provider", "groq")
    except Exception as exc:
        logger.exception("config.yaml konnte nicht geladen werden")
        _show_startup_error(
            "TradingInfoTool - Start fehlgeschlagen",
            f"Basisinfos/config.yaml konnte nicht geladen werden:\n\n{exc}\n\n"
            "Details in der Logdatei (data/tradinginfotool.log).",
        )
        sys.exit(1)

    # E-Mail-Benachrichtigung (U-8, 2026-07-12): erst HIER ermittelbar, da
    # config.yaml gerade erst erfolgreich geladen wurde - der Config-Lade-Fehler
    # oben bleibt bewusst OHNE E-Mail-Versuch (Empfaenger-Adresse an der Stelle
    # noch unbekannt). Nur bei den beiden folgenden echten fatalen Stellen
    # verdrahtet, nicht beim nicht-fatalen Erstimport-Fehler weiter unten.
    email_cfg = config.load_config().get("benachrichtigung", {}).get("email", {})
    email_empfaenger = email_cfg.get("empfaenger") if email_cfg.get("aktiv", False) else None

    groq_api_key = os.environ.get("GROQ_API_KEY")
    if ai_provider == "lokal":
        from api.local_model import LocalModelClient

        groq_client = LocalModelClient()
        logger.info("KI-Ebene: lokal (config.yaml agent.ai_provider) - Architektur-Seam, noch nicht implementiert.")
    elif groq_api_key:
        groq_client = GroqClient(api_key=groq_api_key)
        logger.info("Groq API-Key gefunden - Signal-Pipeline (Phase 3) verfügbar.")
    else:
        # P-8: Kernfunktionen duerfen nie zwingend von einem KI-Key abhaengen - ohne
        # GROQ_API_KEY bleibt der Signale-Tab nutzbar, nur die Berechnung ist deaktiviert
        # (siehe ui/signals_view.py).
        groq_client = None
        logger.info("Kein GROQ_API_KEY gesetzt - Signalberechnung (Phase 3) deaktiviert.")

    fred_api_key = os.environ.get("FRED_API_KEY")
    if fred_api_key:
        logger.info("FRED API-Key gefunden - Leitzinsen/CPI/M2/ISM-Ersatz im Makro-Kontext verfügbar.")
    else:
        # Ebenfalls optional (P-8) - ohne Key bleiben nur BTC-Dominanz/Fear&Greed/PBoC
        # im Makro-Kontext (agent/krypto/pipeline.py degradiert sauber, kein Absturz).
        logger.info("Kein FRED_API_KEY gesetzt - Fed/EZB/M2/CPI/ISM-Ersatz/BoJ/BoK bleiben leer.")

    bitpanda_api_key = os.environ.get("BITPANDA_API_KEY")
    if bitpanda_api_key:
        logger.info("Bitpanda API-Key gefunden - Bestands-/Cash-Reserve-Abgleich verfügbar.")
    else:
        # P-8: manuelle Excel-Import/Export- und Fiat-Cash-Eingabe (Portfolio-Tab)
        # bleiben ohne Key voll nutzbar, nur der Live-Abgleich ist deaktiviert.
        logger.info("Kein BITPANDA_API_KEY gesetzt - Bestandsabgleich mit Bitpanda deaktiviert.")

    try:
        watchlist = config.get_watchlist()
    except Exception as exc:
        logger.exception("Watchlist konnte nicht aus config.yaml geladen werden")
        _show_startup_error(
            "TradingInfoTool - Start fehlgeschlagen",
            f"Watchlist konnte nicht aus Basisinfos/config.yaml geladen werden:\n\n{exc}\n\n"
            "Details in der Logdatei (data/tradinginfotool.log).",
            email_empfaenger=email_empfaenger,
        )
        sys.exit(1)

    try:
        conn = db.get_connection()
        db.init_db(conn)
    except Exception as exc:
        logger.exception("Datenbank konnte nicht initialisiert werden")
        _show_startup_error(
            "TradingInfoTool - Start fehlgeschlagen",
            f"Datenbank konnte nicht initialisiert werden:\n\n{exc}\n\n"
            "Details in der Logdatei (data/tradinginfotool.log).",
            email_empfaenger=email_empfaenger,
        )
        sys.exit(1)

    if db.is_first_run(conn):
        try:
            result = import_holdings(conn)
            logger.info("Erstimport: %d Bestände importiert.", result.imported_count)
            for warning in result.warnings:
                logger.warning(warning)
        except Exception as exc:
            # NICHT fatal (anders als Config/DB oben) - die App kann mit leeren
            # Bestaenden starten, der Nutzer kann jederzeit ueber "Datei -> Bestaende
            # aus Datei importieren..." nachholen (identischer Codepfad).
            logger.exception("Erstimport aus Assets.xlsx fehlgeschlagen")
            _show_startup_error(
                "TradingInfoTool - Erstimport fehlgeschlagen",
                f"Bestände aus Basisinfos/Assets.xlsx konnten nicht importiert werden:"
                f"\n\n{exc}\n\nDie App startet trotzdem mit leeren Beständen - du kannst "
                "sie später über \"Datei → Bestände aus Datei importieren…\" nachholen.",
            )

    coingecko_client = CoinGeckoClient(api_key=coingecko_api_key)

    if db.is_history_first_run(conn):
        results = backfill_all(coingecko_client, conn, watchlist)
        degraded = [r for r in results if r.degraded]
        logger.info(
            "Historie-Erstbefüllung: %d/%d Assets, %d degradiert",
            len(results) - len(degraded),
            len(results),
            len(degraded),
        )
        for r in degraded:
            logger.warning("Historie für %s unvollständig: %s", r.coingecko_id, r.reason)
        db.mark_history_backfilled(conn)

    kraken_client = KrakenClient()

    if db.is_ohlc_first_run(conn):
        ohlc_results = backfill_all_ohlc(kraken_client, conn, watchlist)
        ohlc_skipped = [r for r in ohlc_results if r.skipped]
        ohlc_degraded = [r for r in ohlc_results if r.degraded]
        logger.info(
            "Kraken-OHLC-Erstbefüllung: %d/%d Assets, %d ohne Kraken-Listing, %d degradiert",
            len(ohlc_results) - len(ohlc_skipped) - len(ohlc_degraded),
            len(ohlc_results),
            len(ohlc_skipped),
            len(ohlc_degraded),
        )
        for r in ohlc_degraded:
            logger.warning("Kraken-OHLC für %s unvollständig: %s", r.symbol, r.reason)
        db.mark_ohlc_backfilled(conn)

    conn.close()

    bg_scheduler = build_scheduler(
        coingecko_client=coingecko_client,
        kraken_client=kraken_client,
        db_conn_factory=db.get_connection,
        watchlist_provider=lambda: watchlist,
        groq_client=groq_client,
        fred_api_key=fred_api_key,
        bitpanda_api_key=bitpanda_api_key,
    )
    bg_scheduler.start()

    # Remote-Steuer-Seite (2026-07-11, ueber Tailscale erreichbar, siehe
    # Basisinfos/Regelwerksmanual.md Kap. 12/13) - P-8: ohne Token bleibt sie
    # komplett deaktiviert, kein lauschender Port. Eingebettet als Hintergrund-
    # Thread im selben Prozess (kein separater Prozess noetig, siehe remote/server.py
    # Modul-Docstring) - nutzt dieselben bereits instanziierten Clients wieder.
    remote_access_token = os.environ.get("REMOTE_ACCESS_TOKEN")
    if remote_access_token:
        from remote.server import create_app, run_remote_server

        remote_app = create_app(
            coingecko_client=coingecko_client,
            kraken_client=kraken_client,
            groq_client=groq_client,
            conn_factory=db.get_connection,
            watchlist=watchlist,
            fred_api_key=fred_api_key,
            access_token=remote_access_token,
            log_path=LOG_PATH,
        )
        threading.Thread(target=run_remote_server, args=(remote_app,), daemon=True).start()
        logger.info("Remote-Steuer-Seite gestartet (Port %d, nur ueber Tailscale/lokales Netz erreichbar).", 8765)
    else:
        logger.info("Kein REMOTE_ACCESS_TOKEN gesetzt - Remote-Steuer-Seite deaktiviert (P-8).")

    try:
        app.run_app(
            db_conn_factory=db.get_connection,
            watchlist=watchlist,
            coingecko_client=coingecko_client,
            kraken_client=kraken_client,
            groq_client=groq_client,
            fred_api_key=fred_api_key,
            bitpanda_api_key=bitpanda_api_key,
        )
    finally:
        bg_scheduler.shutdown(wait=False)


if __name__ == "__main__":
    main()
