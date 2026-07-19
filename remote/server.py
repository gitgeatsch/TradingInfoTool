"""Remote-Steuer-Seite (2026-07-11, ueber Tailscale erreichbar, siehe
Basisinfos/Regelwerksmanual.md Kap. 12/13 und Basisinfos/Tailscale-Setup-
Anleitung.md). Eingebettet in main.py als Hintergrund-Thread (kein separater
Prozess) - teilt sich Clients/Connection-Factory/Watchlist mit der bereits
laufenden Tkinter-App, keine Multi-Prozess-DB-Koordination noetig.

Flask statt FastAPI: keine der Job-Funktionen ist async, hier reichen wenige
simple Routen + eine mobile HTML-Seite. Der eingebaute Dev-Server (threaded)
ist fuer einen einzelnen Nutzer im privaten Tailscale-VPN ausreichend, kein
Produktions-WSGI-Server noetig."""
from __future__ import annotations

import hmac
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, Response, jsonify, request

import database.db as db
import scheduler.background as background
from api.yfinance_client import YFinanceClient
from remote.status import build_status

DEFAULT_PORT = 8765

# Neustart-Bruecke zum separaten Watchdog-Prozess (2026-07-14, siehe
# monitor/watchdog.py::_monitor_loop()) - main.py kann sich nicht selbst neu
# starten (Neustart eines haengenden Tk-Mainloops von innen ist nicht
# moeglich), deshalb nur eine Flag-Datei schreiben, die der ohnehin alle 5 Sek.
# pollende Watchdog aufgreift und ausfuehrt. Kein neuer Port/keine neue Auth -
# nutzt den bestehenden Token-Check dieser Seite.
RESTART_FLAG_PATH = Path(__file__).resolve().parent.parent / "data" / "watchdog_restart_requested.txt"

logger = logging.getLogger(__name__)

# Reine mobile Seite, kein Templates-Verzeichnis noetig fuer eine einzige Seite.
# Der Token wird NICHT serverseitig eingebettet (kein Jinja-Rendering noetig) -
# das Frontend liest ihn selbst aus der URL (location.search), damit ein
# einmal gesetztes Handy-Bookmark (mit ?token=...) dauerhaft funktioniert.
_INDEX_HTML = """<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TradingInfoTool - Fernsteuerung</title>
<style>
  body { font-family: -apple-system, Roboto, Arial, sans-serif; margin: 0; padding: 16px;
         background: #101418; color: #e8e8e8; }
  h1 { font-size: 1.2rem; margin: 0 0 16px; }
  .card { background: #1b2128; border-radius: 10px; padding: 14px; margin-bottom: 12px; }
  .row { display: flex; justify-content: space-between; padding: 4px 0; font-size: 0.92rem; }
  .stale { color: #e0a030; }
  .ok { color: #4caf50; }
  .err { color: #e0605a; }
  .regime-krise_extrem { color: #e0605a; }
  .regime-baer { color: #e0a030; }
  .regime-seitwaerts { color: #999; }
  .regime-bulle { color: #4caf50; }
  .regime-euphorie_extrem { color: #7a6ee0; }
  .muted-text { color: #999; font-size: 0.82rem; }
  .kategorie-header { color: #7a8290; font-size: 0.78rem; text-transform: uppercase; margin-top: 8px; }
  button { width: 100%; padding: 14px; margin-top: 8px; font-size: 1rem; border: none;
           border-radius: 8px; background: #2e5fa3; color: white; }
  button:disabled { background: #3a4048; color: #888; }
  button.danger { background: #7a2e2e; }
  #status-text { font-size: 0.85rem; color: #999; margin-top: 4px; }
  .error-line { font-size: 0.78rem; color: #e0605a; word-break: break-word; margin: 2px 0; }
</style>
</head>
<body>
<h1>TradingInfoTool - Fernsteuerung</h1>

<div class="card">
  <div class="row"><span>Portfolio-Wert</span><span id="portfolio-value">-</span></div>
  <div class="row"><span>Preise veraltet</span><span id="stale-count">-</span></div>
  <div class="row"><span>Letzter Marktscan</span><span id="marktscan-info">-</span></div>
</div>

<div class="card">
  <div class="row"><span>LLM-Budget heute (Krypto)</span><span id="budget-total">-</span></div>
  <div class="row"><span>&nbsp;&nbsp;davon Hebel</span><span id="budget-hebel">-</span></div>
  <div class="row"><span>&nbsp;&nbsp;davon Marktscan</span><span id="budget-marktscan">-</span></div>
  <div class="row"><span>&nbsp;&nbsp;davon Spot-Rotation</span><span id="budget-spot">-</span></div>
  <div class="row"><span>Multi-Asset heute (Aktien/Rohstoffe/Hedge/ETF, separates Budget)</span><span id="budget-multi-asset">-</span></div>
</div>

<div class="card">
  <div class="row"><strong>Provider-Performance (Spot)</strong></div>
  <div id="provider-performance-spot"></div>
  <div class="row"><strong>Provider-Performance (Hebel)</strong></div>
  <div id="provider-performance-hebel"></div>
</div>

<div class="card">
  <div class="row"><strong>API-Status: LLM-Anbieter</strong></div>
  <div id="api-health-llm"></div>
  <div class="row"><strong>API-Status: Markt-/Preisdaten</strong></div>
  <div id="api-health-markt"></div>
  <div class="row"><strong>API-Status: Makro/On-Chain/Derivate</strong></div>
  <div id="api-health-makro"></div>
</div>

<div class="card" id="regime-status-card" style="display:none">
  <div class="row"><strong>Regime-Status</strong></div>
  <div id="regime-status-body"></div>
</div>

<div class="card" id="parameter-overview-card" style="display:none">
  <div class="row"><strong>Parameter-Übersicht</strong></div>
  <div id="parameter-overview-body"></div>
</div>

<div class="card">
  <button id="btn-prices" onclick="triggerAction('refresh-prices')">Preise aktualisieren</button>
  <div id="status-prices" class="row"></div>
  <button id="btn-marktscan" onclick="triggerAction('marktscan')">Marktscan jetzt starten</button>
  <div id="status-marktscan" class="row"></div>
</div>

<div class="card">
  <button class="danger" onclick="restartApp()">App neu starten (erzwingen)</button>
  <div id="status-restart" class="row"></div>
</div>

<div class="card" id="errors-card" style="display:none">
  <div class="row"><strong>Letzte Fehler</strong></div>
  <div id="errors-list"></div>
</div>

<div id="status-text">wird geladen ...</div>

<script>
const params = new URLSearchParams(location.search);
const TOKEN = params.get("token") || "";
// Grober Schwellenwert (Minuten), ab dem ein Job als "ungewoehnlich lange
// laufend" gilt und der Not-Reset-Button eingeblendet wird - kein exaktes
// Limit, nur eine Heuristik (siehe Regelwerksmanual Kap. 13).
const RESET_THRESHOLD_MINUTES = { refresh_prices: 1, refresh_securities: 1, marktscan: 3 };
const ACTION_JOBS = { "refresh-prices": ["refresh_prices", "refresh_securities"], "marktscan": ["marktscan"] };

function apiFetch(path, method) {
  return fetch(path, { method: method || "GET", headers: { "X-Access-Token": TOKEN } });
}

async function triggerAction(action) {
  const resp = await apiFetch("/api/" + action, "POST");
  if (resp.status === 409) {
    document.getElementById("status-text").textContent = "Läuft bereits - bitte warten.";
  } else if (!resp.ok) {
    document.getElementById("status-text").textContent = "Fehler beim Starten (" + resp.status + ").";
  }
  refreshStatus();
}

async function resetLock(job) {
  await apiFetch("/api/reset-lock?job=" + encodeURIComponent(job), "POST");
  refreshStatus();
}

async function restartApp() {
  if (!confirm("App wirklich neu starten? Eine gerade laufende Analyse/Marktscan wird dabei abgebrochen.")) {
    return;
  }
  const statusDiv = document.getElementById("status-restart");
  await apiFetch("/api/restart-app", "POST");
  statusDiv.textContent = "Neustart angefordert - Watchdog uebernimmt in wenigen Sekunden.";
}

function fmtMoney(value) {
  if (value === null || value === undefined) return "-";
  return value.toLocaleString("de-AT", { maximumFractionDigits: 2 }) + " EUR";
}

function renderProviderPerformance(tierData) {
  const providers = Object.keys(tierData);
  if (providers.length === 0) {
    return '<div class="row"><span>noch keine Daten</span></div>';
  }
  return providers.map(function(p) {
    const d = tierData[p];
    const winRate = d.win_rate !== null && d.win_rate !== undefined
      ? Math.round(d.win_rate * 100) + "%" : "-";
    const crv = d.avg_realisiertes_crv !== null && d.avg_realisiertes_crv !== undefined
      ? d.avg_realisiertes_crv.toFixed(2) : "-";
    return '<div class="row"><span>' + p + ' (' + d.anzahl_resolved + ')</span>' +
      '<span>Win-Rate ' + winRate + ', &oslash; CRV ' + crv + '</span></div>';
  }).join("");
}

const API_HEALTH_GROUPS = {
  "api-health-llm": ["groq", "mistral", "gemini"],
  "api-health-markt": ["coingecko", "kraken", "bitpanda", "yfinance"],
  "api-health-makro": [
    "fear_greed", "fred", "ecb", "china_pboc_lpr", "china_m2", "japan_boj",
    "coinmetrics", "defillama", "blockchain_com", "binance", "bybit", "okx",
    "cftc_cot", "sec_edgar",
  ],
};

function fmtRelativeTime(iso) {
  if (!iso) return "nie";
  const diffMinutes = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (diffMinutes < 60) return "vor " + diffMinutes + " Min";
  const diffHours = Math.round(diffMinutes / 60);
  if (diffHours < 48) return "vor " + diffHours + " Std.";
  return "vor " + Math.round(diffHours / 24) + " Tagen";
}

function renderApiHealthGroup(sourceKeys, apiHealth) {
  return sourceKeys.map(function(key) {
    const entry = apiHealth[key];
    let statusClass = "";
    let statusText = "unbekannt";
    if (entry) {
      if (entry.status === "ok") {
        statusClass = "ok";
        statusText = "OK (" + fmtRelativeTime(entry.last_success_at) + ")";
      } else if (entry.status === "fehler") {
        statusClass = "err";
        statusText = "Fehler (" + fmtRelativeTime(entry.last_error_at) + ")";
      }
    }
    return '<div class="row"><span>' + key + '</span><span class="' + statusClass + '">' +
      statusText + '</span></div>';
  }).join("");
}

const REGIME_LABELS = {
  krise_extrem: "Krise (extrem)", baer: "Bär", seitwaerts: "Seitwärts",
  bulle: "Bulle", euphorie_extrem: "Euphorie (extrem)",
};

function fmtDateTime(iso) {
  if (!iso) return "-";
  return new Date(iso).toLocaleString("de-AT", { dateStyle: "medium", timeStyle: "short" });
}

function renderRegimeStatus(r) {
  const label = REGIME_LABELS[r.regime] || r.regime;
  const cls = "regime-" + r.regime;
  let html = '<div class="row"><span>Stand</span><span>' + fmtDateTime(r.created_at) + '</span></div>';
  html += '<div class="row"><span>Regime</span><span class="' + cls + '"><strong>' + label + '</strong></span></div>';
  if (r.regime_source === "manuell") {
    html += '<div class="row"><span class="muted-text">⚠ manuell überschrieben</span></div>';
  } else if (r.regime_reason) {
    html += '<div class="row"><span class="muted-text">' + r.regime_reason + '</span></div>';
  }
  const zeilen = [
    ["BTC-Trend", r.btc_trend_label],
    ["Fear &amp; Greed", r.fear_greed_label ? r.fear_greed_label + " (" + r.fear_greed_value + ")" : null],
    ["BTC-Dominanz-Trend", r.dominance_trend_label],
    ["Zyklus-Risiko", r.zyklus_risiko !== null && r.zyklus_risiko !== undefined
      ? r.zyklus_risiko.toFixed(2) + (r.zyklus_risiko_begruendung ? " - " + r.zyklus_risiko_begruendung : "") : null],
    ["Liquiditätsregime", r.liquiditaets_regime
      ? r.liquiditaets_regime + (r.liquiditaets_regime_begruendung ? " - " + r.liquiditaets_regime_begruendung : "") : null],
  ];
  for (const [titel, wert] of zeilen) {
    if (wert === null || wert === undefined) continue;
    html += '<div class="row"><span>' + titel + '</span><span>' + wert + '</span></div>';
  }
  return html;
}

function renderParameterOverview(rows) {
  if (!rows || rows.length === 0) return "";
  let html = '<table style="width:100%; border-collapse: collapse; font-size: 0.85rem;">';
  let letzteKategorie = null;
  for (const p of rows) {
    if (p.kategorie !== letzteKategorie) {
      html += '<tr><td colspan="2" class="kategorie-header">' + p.kategorie + '</td></tr>';
      letzteKategorie = p.kategorie;
    }
    const tooltip = (p.begruendung || "") +
      " (zuletzt geändert: " + (p.geaendert_am || "kein Datum vermerkt") + ")";
    html += '<tr title="' + tooltip.replace(/"/g, "&quot;") + '">' +
      '<td style="padding:3px 4px 3px 0">' + p.bezeichnung + '</td>' +
      '<td style="padding:3px 0; text-align:right">' + p.wert + '</td></tr>';
  }
  html += "</table>";
  return html;
}

async function refreshStatus() {
  let data;
  try {
    const resp = await apiFetch("/api/status");
    if (!resp.ok) throw new Error("HTTP " + resp.status);
    data = await resp.json();
  } catch (e) {
    document.getElementById("status-text").textContent = "Keine Verbindung zum Server.";
    return;
  }

  let portfolioText = fmtMoney(data.portfolio_value_eur);
  if (data.cash_reserve_eur > 0) {
    portfolioText += " (davon " + fmtMoney(data.cash_reserve_eur) + " Cash)";
  }
  document.getElementById("portfolio-value").textContent = portfolioText;
  const staleCount = data.prices.filter(p => p.stale).length;
  document.getElementById("stale-count").textContent = staleCount + " / " + data.prices.length;
  document.getElementById("stale-count").className = staleCount > 0 ? "stale" : "ok";

  if (data.marktscan_last) {
    document.getElementById("marktscan-info").textContent =
      data.marktscan_last.kandidaten + " Kandidaten, " + data.marktscan_last.treffer + " Treffer";
  }

  if (data.budget_heute) {
    const b = data.budget_heute;
    document.getElementById("budget-total").textContent = b.verbraucht_gesamt + " / " + b.gesamt;
    document.getElementById("budget-hebel").textContent = b.hebel;
    document.getElementById("budget-marktscan").textContent = b.marktscan;
    document.getElementById("budget-spot").textContent = b.spot;
    document.getElementById("budget-multi-asset").textContent = b.multi_asset_heute;
  }

  if (data.provider_performance) {
    document.getElementById("provider-performance-spot").innerHTML =
      renderProviderPerformance(data.provider_performance.spot || {});
    document.getElementById("provider-performance-hebel").innerHTML =
      renderProviderPerformance(data.provider_performance.hebel || {});
  }

  if (data.api_health) {
    for (const [elementId, sourceKeys] of Object.entries(API_HEALTH_GROUPS)) {
      document.getElementById(elementId).innerHTML = renderApiHealthGroup(sourceKeys, data.api_health);
    }
  }

  if (data.regime_status) {
    document.getElementById("regime-status-card").style.display = "block";
    document.getElementById("regime-status-body").innerHTML = renderRegimeStatus(data.regime_status);
  }

  if (data.parameter_overview && data.parameter_overview.length > 0) {
    document.getElementById("parameter-overview-card").style.display = "block";
    document.getElementById("parameter-overview-body").innerHTML = renderParameterOverview(data.parameter_overview);
  }

  for (const [action, jobs] of Object.entries(ACTION_JOBS)) {
    const btn = document.getElementById("btn-" + action.replace("refresh-prices", "prices"));
    const runningJob = jobs.find(j => data.jobs_running[j]);
    const statusDiv = document.getElementById("status-" + action.replace("refresh-prices", "prices"));
    if (runningJob) {
      btn.disabled = true;
      const minutes = data.jobs_running_seit_minuten[runningJob];
      const minutesText = minutes !== null ? minutes.toFixed(1) : "?";
      statusDiv.textContent = "läuft seit " + minutesText + " Min ...";
      const threshold = RESET_THRESHOLD_MINUTES[runningJob] || 3;
      if (minutes !== null && minutes > threshold) {
        statusDiv.innerHTML += ' <button class="danger" style="width:auto;padding:4px 10px" ' +
          'onclick="resetLock(\\'' + runningJob + '\\')">Zurücksetzen (Not-Funktion)</button>';
      }
    } else {
      btn.disabled = false;
      statusDiv.textContent = "";
    }
  }

  const errorsCard = document.getElementById("errors-card");
  const errorsList = document.getElementById("errors-list");
  if (data.recent_errors && data.recent_errors.length > 0) {
    errorsCard.style.display = "block";
    errorsList.innerHTML = data.recent_errors.map(
      line => '<div class="error-line">' + line.replace(/</g, "&lt;") + "</div>"
    ).join("");
  } else {
    errorsCard.style.display = "none";
  }

  document.getElementById("status-text").textContent = "zuletzt aktualisiert: " + new Date().toLocaleTimeString("de-AT");
}

refreshStatus();
setInterval(refreshStatus, 2000);
</script>
</body>
</html>
"""


def create_app(
    *,
    coingecko_client,
    kraken_client,
    groq_client,
    conn_factory,
    watchlist,
    fred_api_key,
    access_token: str,
    log_path: Path,
) -> Flask:
    # Werkzeug (Flasks Dev-Server) loggt sonst jede Request-Zeile inkl. voller
    # URL an den Root-Logger - ohne diese Zeile wuerde der Token bei jedem
    # GET / (Query-Param, siehe Modul-Docstring in remote/server.py) im
    # Klartext in data/tradinginfotool.log landen.
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    app = Flask(__name__)

    def _token_from_request() -> str | None:
        header_token = request.headers.get("X-Access-Token")
        if header_token:
            return header_token
        return request.args.get("token")

    @app.before_request
    def _check_token():
        supplied = _token_from_request() or ""
        if not hmac.compare_digest(supplied, access_token):
            return jsonify({"error": "unauthorized"}), 401

    @app.route("/", methods=["GET"])
    def index():
        return Response(_INDEX_HTML, mimetype="text/html")

    @app.route("/api/status", methods=["GET"])
    def api_status():
        conn = conn_factory()
        try:
            status = build_status(conn, watchlist, log_path)
        finally:
            conn.close()
        return jsonify(status.to_dict())

    @app.route("/api/refresh-prices", methods=["POST"])
    def api_refresh_prices():
        """Startet Krypto- UND Wertpapier-Preis-Refresh zusammen (ein Button
        fuer "Preise", siehe Plan) - jeweils in einem eigenen Daemon-Thread, die
        Job-Funktionen selbst schuetzen sich per Lock vor doppelten Laeufen
        (siehe scheduler/background.py). Der Vorab-Check hier ist nur fuer
        sofortiges Nutzer-Feedback (409), die eigentliche Garantie liegt in den
        Jobs selbst."""
        if background.refresh_prices_lock.locked() or background.refresh_securities_lock.locked():
            return jsonify({"error": "already_running"}), 409

        def _run():
            background.refresh_prices_job(coingecko_client, conn_factory, watchlist)
            background.refresh_securities_prices_job(YFinanceClient(), conn_factory, watchlist)

        threading.Thread(target=_run, daemon=True).start()
        return jsonify({"started": True}), 202

    @app.route("/api/marktscan", methods=["POST"])
    def api_marktscan():
        if background.marktscan_lock.locked():
            return jsonify({"error": "already_running"}), 409

        threading.Thread(
            target=background.marktscan_job,
            args=(coingecko_client, kraken_client, conn_factory, watchlist, fred_api_key),
            daemon=True,
        ).start()
        return jsonify({"started": True}), 202

    @app.route("/api/reset-lock", methods=["POST"])
    def api_reset_lock():
        """Not-Reset (siehe Regelwerksmanual Kap. 13) - setzt NUR den Lock
        zurueck, keine echte Prozess-Kontrolle ueber einen haengenden
        Hintergrund-Thread (siehe force_release_lock()-Docstring)."""
        job_name = request.args.get("job") or (request.get_json(silent=True) or {}).get("job")
        if not job_name:
            return jsonify({"error": "missing_job"}), 400
        released = background.force_release_lock(job_name)
        return jsonify({"released": released})

    @app.route("/api/restart-app", methods=["POST"])
    def api_restart_app():
        """Schreibt nur die Flag-Datei fuer den Watchdog (siehe RESTART_FLAG_PATH
        oben) - main.py fuehrt den Neustart NICHT selbst aus. Atomarer Write wie
        beim GUI-Heartbeat (tmp-Datei + os.replace), damit der Watchdog nie einen
        halb geschriebenen Inhalt liest."""
        try:
            tmp_path = RESTART_FLAG_PATH.with_suffix(".tmp")
            tmp_path.write_text(datetime.now(timezone.utc).isoformat(), encoding="utf-8")
            os.replace(tmp_path, RESTART_FLAG_PATH)
        except OSError:
            logger.exception("Neustart-Flag-Datei konnte nicht geschrieben werden")
            return jsonify({"error": "flag_write_failed"}), 500
        return jsonify({"requested": True}), 202

    return app


def run_remote_server(app: Flask, host: str = "0.0.0.0", port: int = DEFAULT_PORT) -> None:
    """Thread-Target-Funktion (main.py startet das per threading.Thread,
    daemon=True). use_reloader=False/debug=False bewusst explizit gesetzt -
    Flasks Reloader forkt sonst einen zweiten Subprozess, was mit dem
    Embedded-Thread-Modell kollidieren wuerde."""
    app.run(host=host, port=port, threaded=True, use_reloader=False, debug=False)
