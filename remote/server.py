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

  /* Kapitel-Header (2026-08-01): farblich klar abgesetzte Zwischenabschnitte statt
     einheitlichem Grau-in-Grau - je Bereich (System/Budget, Gruppe A/B/C) eine
     eigene Akzentfarbe fuer Badge + Rahmen der zugehoerigen Karten. */
  .section-header { display: flex; align-items: baseline; gap: 10px; margin: 26px 0 10px;
                     padding-bottom: 8px; border-bottom: 2px solid #2a323c; }
  .section-header:first-of-type { margin-top: 0; }
  .section-badge { display: inline-block; flex: none; font-size: 0.7rem; font-weight: 700;
                    letter-spacing: 0.04em; padding: 3px 10px; border-radius: 999px;
                    background: #3a4048; color: #0d1117; }
  .section-title { font-size: 1rem; color: #eef2f7; font-weight: 600; }
  .section-sub { font-size: 0.78rem; color: #8a93a0; }
  .section-group { border-left: 3px solid #2a323c; padding-left: 11px; margin-left: -14px; }
  .section-system { border-bottom-color: #5b8fd6; }
  .section-system .section-badge { background: #5b8fd6; }
  .group-system { border-left-color: #5b8fd6; }
  .section-a { border-bottom-color: #4caf50; }
  .section-a .section-badge { background: #4caf50; }
  .group-a { border-left-color: #4caf50; }
  .section-b { border-bottom-color: #b18cf0; }
  .section-b .section-badge { background: #b18cf0; }
  .group-b { border-left-color: #b18cf0; }
  .section-c { border-bottom-color: #e0a030; }
  .section-c .section-badge { background: #e0a030; }
  .group-c { border-left-color: #e0a030; }
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

<div class="section-header section-system">
  <span class="section-badge">System</span>
  <span class="section-title">Status &amp; Budget</span>
  <span class="section-sub">Portfolio, LLM-Kontingente, CoinGecko-Quote</span>
</div>
<div class="section-group group-system">

<div class="card">
  <div class="row"><span>Portfolio-Wert</span><span id="portfolio-value">-</span></div>
  <div class="row"><span>Preise veraltet</span><span id="stale-count">-</span></div>
  <div class="row"><span>Letzter Marktscan</span><span id="marktscan-info">-</span></div>
</div>

<div class="card">
  <div class="row"><span><b>LLM-Kontingent heute (Rollen-Kette)</b></span><span id="rollen-rest">-</span></div>
  <div class="row"><span>&nbsp;&nbsp;Gemini 3.1 (erster Topf)</span><span id="topf-gemini31">-</span></div>
  <div class="row"><span>&nbsp;&nbsp;Gemini 3.5 (Rückfall)</span><span id="topf-gemini35">-</span></div>
  <div class="row"><span>&nbsp;&nbsp;OpenRouter</span><span id="topf-openrouter">-</span></div>
  <div class="row"><span>&nbsp;&nbsp;Groq (Token-Grenze, nicht Anfragen)</span><span id="topf-groq">-</span></div>
  <div class="row"><span>Urteile der Rollen-Kette heute</span><span id="rollen-signale">-</span></div>
  <div class="row"><span>&nbsp;&nbsp;davon Hebel / mit Handlung</span><span id="rollen-aufteilung">-</span></div>
  <div class="row"><span>Z.ai-Gegenprüfung heute (kein Tagesdeckel)</span><span id="budget-zai-gegenpruefung">-</span></div>
</div>

<div class="card">
  <div class="row"><span>ALTE KETTE (seit dem Schnitt ohne Aufrufer)</span><span id="budget-total">-</span></div>
  <div class="row"><span>&nbsp;&nbsp;Hebel / Marktscan / Spot-Rotation</span><span id="budget-alt-drei">-</span></div>
  <div class="row"><span>&nbsp;&nbsp;Multi-Asset</span><span id="budget-multi-asset">-</span></div>
</div>

<div class="card">
  <div class="row"><span>CoinGecko-Kontingent diesen Monat</span><span id="coingecko-quota">-</span></div>
  <div class="row"><span>&nbsp;&nbsp;davon heute</span><span id="coingecko-quota-heute">-</span></div>
  <div class="row"><span class="muted-text">Monatliches Call-Kontingent (2026-07-31, echte 80%-Warnmail von
  CoinGecko ausgeloest) - bei 100% wird laut CoinGecko hart gedeckelt. Warnmails bei 80%/90% (config.yaml
  coingecko_quota.warnschwellen_prozent), je Schwelle nur einmal pro Kalendermonat. Tages-Zeile (2026-08-01) macht
  sichtbar, an welchem Tag der Verbrauch tatsaechlich ansteigt.</span></div>
</div>

<div class="card">
  <div class="row"><span>Gemini-Tageskontingent je Modell</span><span id="llm-kontingent-tag">-</span></div>
  <div id="llm-kontingent"></div>
  <div class="row"><span class="muted-text">500 Aufrufe pro Tag, pro Projekt, pro MODELL - am 2026-08-09 aus
  Googles eigenem Fehlerkoerper gemessen (GenerateRequestsPerDayPerProjectPerModel-FreeTier), nicht recherchiert.
  Das Kontingent haengt am API-SCHLUESSEL, nicht am Geraet: Laeufe am Desktop nehmen der Produktion am Notebook
  direkt Budget weg - genau so stand die Produktion am 09.08. einen Tag lang still, ohne dass es irgendwo
  sichtbar war. Der Tag laeuft auf Googles Grenze (Mitternacht Pazifik, also 09:00 MESZ), nicht auf UTC.
  Jedes Modell hat einen eigenen Topf.</span></div>
</div>

</div>

<div class="section-header section-a">
  <span class="section-badge">A</span>
  <span class="section-title">Ausgeführte Empfehlungen</span>
  <span class="section-sub">real, im Handel/Portfolio wirksam</span>
</div>
<div class="section-group group-a">







<div class="card">
  <div class="row"><strong>Marktscan-Erfolgsquote (Kaufkandidaten/"heiße" Watchlist)</strong></div>
  <div class="row"><span class="muted-text">Anteil der abgeschlossenen Erfolgsmessungen (CRV-Mindestziel
  erreicht, siehe Regelwerksmanual "Marktscan-Erfolgsmessung"), die tatsaechlich erfolgreich waren. "Offen"
  laufende Messungen zaehlen nicht mit. Ø Tage bis Erfolg nur bei ausreichender Stichprobe (n≥15) empirisch
  belastbar.</span></div>
  <div id="marktscan-erfolgsquote"></div>
</div>

</div>

<div class="section-header section-b">
  <span class="section-badge">B</span>
  <span class="section-title">Unabhängige Zweitmeinung</span>
  <span class="section-sub">Z.ai-Gegenprüfung</span>
</div>
<div class="section-group group-b">



</div>

<div class="section-header section-c">
  <span class="section-badge">C</span>
  <span class="section-title">Veto-Schatten</span>
  <span class="section-sub">hypothetisch, nie ausgeführt + Gesamt</span>
</div>
<div class="section-group group-c">







<div class="card">
  <h2>Stop nachziehen &mdash; offene Signale mit ungesichertem Gewinn</h2>
  <div class="row"><span class="muted-text">Advisory-only: gerechnet und gemeldet, nicht ausgef&uuml;hrt. Grundlage (2026-08-04): 50&nbsp;% der Signale standen einmal bei +1R, nur 17,6&nbsp;% kamen am Ziel an &ndash; Positionen geben Gewinne zur&uuml;ck. Ein Trailing-Stop ab +1R hob den Erwartungswert von &minus;0,176 auf &minus;0,084&nbsp;R (495 echte Signale, symbolgeblocktes Intervall [+0,051; +0,131], h&auml;lt im Split-Sample und &uuml;ber alle drei Marktphasen). Das ist <b>kein</b> Breakeven-Lock &ndash; der wurde am 01.08. gemessen und verworfen, er kostet 63&nbsp;% der Gewinner.</span></div>
  <div id="ausstieg-empfehlungen"></div>
</div>









</div>

<div class="card">
  <div class="row"><strong>API-Status: LLM-Anbieter</strong></div>
  <div id="api-health-llm"></div>
  <div class="row"><strong>API-Status: Markt-/Preisdaten</strong></div>
  <div id="api-health-markt"></div>
  <div class="row"><strong>API-Status: Makro/On-Chain/Derivate</strong></div>
  <div id="api-health-makro"></div>
</div>



<div class="card" id="themenfeld-erfolg-card" style="display:none">
  <div class="row"><strong>Themenfelder — traf die Richtung?</strong></div>
  <div class="row"><span class="muted-text">Gemessen wird <b>nicht</b> die Systemgüte je Hauptgruppe:
  von 101 aufgelösten Signalen (Stand 07.08.) gehört <b>keines</b> zu einem Themenfeld — die Tabelle wäre
  leer und sähe trotzdem aus wie ein Instrument. Eine These ist auch keine Trade-Folge, sondern eine
  Richtungsaussage auf einen Korb. Verglichen wird deshalb die gleichgewichtete Korbrendite der Kategorie
  seit dem Setzen der These gegen die aller übrigen Themen-Assets. Die Absicherung fehlt hier bewusst —
  sie wird über die Dämpfung gemessen, nicht über Überrendite.</span></div>
  <div id="themenfeld-erfolg-body"></div>
</div>

<div class="card" id="wartende-themen-card" style="display:none">
  <div class="row"><strong>Themen in Beobachtung — wann wird was reif?</strong></div>
  <div class="row"><span class="muted-text">Ein Themen-Vorschlag zählt erst, wenn sein Prüf-Mechanismus
  lange genug in dieselbe Richtung zeigt (7 Tage Bärenmarkt-Overlay, 14 COT/M2, 30 Zinskurve/Dollar-Index/
  Bellwether). Bis dahin steht er auf „beobachtung“ — und genau das war bisher unsichtbar: die
  Statusverteilung sagt <b>nichts</b> über den Vorlauf. Die entscheidende Zahl ist, wie viele Kandidaten am
  <b>selben Tag</b> reif werden. Seit dem 07.08. <b>sperrt die Richtgröße nicht mehr</b> — die
  Spezifikation sagt „weich in der GUI angezeigt, kein Hard-Limit im Code“, implementiert war das
  Gegenteil. Zurückgestellt wird ein Vorschlag nur noch, wenn sein Themenfeld gar kein handelbares
  Asset hat.</span></div>
  <div id="wartende-themen-body"></div>
</div>

<div class="card" id="hedge-card" style="display:none">
  <div class="row"><strong>Absicherung — hat sie gewirkt?</strong></div>
  <div class="row"><span class="muted-text">Ein Hedge, der Geld verliert während das Portfolio steigt,
  hat <b>funktioniert</b> — er ist eine Versicherungsprämie. Nach Systemgüte oder Expectancy gemessen wäre
  das Ergebnis konstruktionsbedingt negativ und ohne Aussage. Gemessen wird deshalb derselbe Bestand
  einmal mit und einmal ohne Absicherung.</span></div>
  <div id="hedge-body"></div>
</div>

<div class="card" id="z3-card" style="display:none">
  <div class="row"><strong>Drawdown-Notbremse Z-3</strong></div>
  <div id="z3-body"></div>
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

// Mindeststichprobe fuer eine belastbare Aussage - identisch zu
// agent/krypto/backward_tracking.py::_MIN_SAMPLE_FUER_AUSSAGE, hier nur zur
// Anzeige eines Hinweises, keine eigene Schwellenwert-Logik.
const PROVIDER_PERF_MIN_SAMPLE = 15;

// Fortschritts-Hinweis, sobald mind. 1 offenes (noch nicht aufgeloestes)
// trackbares Signal existiert - 2026-07-24, Nutzer-Fund: die reine
// "0 abgeschlossen"-Meldung liess nicht erkennen, ob ueberhaupt Fortschritt
// passiert (laufende offene Positionen) oder das Tracking stillsteht.
function renderOffeneSignaleHinweis(offenInfo) {
  if (!offenInfo || !offenInfo.anzahl) return '';
  const alterText = offenInfo.aeltestes_erstellt_am
    ? ' (aeltestes seit ' + fmtRelativeTime(offenInfo.aeltestes_erstellt_am) + ')' : '';
  return '<div class="row"><span class="muted-text">' + offenInfo.anzahl +
    ' offene' + (offenInfo.anzahl === 1 ? 's' : '') + ' Signal' + (offenInfo.anzahl === 1 ? '' : 'e') +
    ' in Beobachtung' + alterText + '</span></div>';
}


// Assetklassen-Aufschluesselung (2026-07-20): compute_provider_performance()
// poolt Spot-Signale seit dem Watchlist-Wiring nicht mehr unter einem
// einzigen "spot"-Schluessel, sondern nach asset.assetklasse - siehe
// Docstring in agent/krypto/backward_tracking.py. Feste Reihenfolge/Labels
// hier, damit auch eine (noch) leere Assetklasse sichtbar bleibt statt
// stillschweigend zu fehlen.
const SPOT_ASSETKLASSEN = [
  // "hedge" ist seit 07.08. ein EIGENER Tier (siehe backward_tracking.
  // _assetklasse_index()). Ohne Eintrag hier faellt er stillschweigend aus der
  // Anzeige - genau die Sorte Luecke, die am 06.08. schon einmal auftrat.
  ["krypto", "Krypto"], ["aktien", "Aktien"], ["rohstoffe", "Rohstoffe"],
  ["etf", "ETF (Themen)"], ["hedge", "Hedge (Absicherung)"],
];


// Konfidenz-Kalibrierungskurve (2026-07-26, Punkt 3 des Regime-Persistenz-
// Folge-Vorschlags - siehe agent/krypto/backward_tracking.py::
// compute_konfidenz_kalibrierung()). Bucket-Grenzen/Reihenfolge fest, damit
// ein (noch) leeres Band sichtbar bleibt statt stillschweigend zu fehlen -
// gleiches Prinzip wie SPOT_ASSETKLASSEN oben.
//
// R-1 (14.08.2026): NUR ALTE KETTE. Die Rollen-Kette erhebt keine Konfidenz
// mehr (E3, 12.08.). Die Daten tragen dafuer `_nur_alte_kette` und `_hinweis`
// - wer diese Karte rendert, zeigt den Hinweis mit an. Ohne ihn liest sich
// eine leere Karte wie ein Defekt; sie ist nur nicht mehr zustaendig.
function konfidenzHinweis(d) {
  if (!d || !d._hinweis) return "";
  return '<div class="row"><span class="muted-text">' + d._hinweis +
    "</span></div>";
}
const KONFIDENZ_BUCKET_ORDER = [
  ["niedrig", "Niedrig (<55%)"], ["mittel", "Mittel (55-70%)"], ["hoch", "Hoch (≥70%)"],
];
// Rein optische Hervorhebung grosser Abweichungen (nicht: neuer Deckel/neue
// Regel) - 15 Prozentpunkte ist keine backtestete Schwelle, nur ein grober
// Blickfang fuer "hier lohnt ein genauerer Blick".
const KONFIDENZ_DIFFERENZ_AUFFAELLIG_PP = 15;



// Richtungstreffer-Quote (2026-07-27, Mindestziel/MFE-Tracking - siehe
// agent/krypto/backward_tracking.py::compute_richtungstreffer_quote()).
function renderRichtungstrefferQuoteTier(label, tierData) {
  if (!tierData) {
    return '<div class="row"><span class="muted-text">' + label +
      ': noch keine ausgewerteten Signale.</span></div>';
  }
  const zeitHinweis = tierData.avg_tage_bis_mindestziel !== null && tierData.avg_tage_bis_mindestziel !== undefined
    ? '&Oslash; ' + tierData.avg_tage_bis_mindestziel.toFixed(1) + ' Tage bis Mindestziel (n=' +
      tierData.avg_tage_bis_mindestziel_stichprobe_n + ')'
    : 'Ø Tage bis Mindestziel noch nicht belastbar (n=' + tierData.avg_tage_bis_mindestziel_stichprobe_n + ', Ziel n≥15)';
  return '<div class="row"><span>' + label + ' (n=' + tierData.anzahl_ausgewertet + ')</span>' +
    '<span>' + tierData.richtungstreffer + '/' + tierData.anzahl_ausgewertet + ' = ' +
    tierData.richtungstreffer_quote_pct.toFixed(1) + '%</span></div>' +
    '<div class="row"><span class="muted-text">' + zeitHinweis + '</span></div>';
}


// Marktscan-Erfolgsquote (2026-07-30, siehe agent/krypto/
// marktscan_backward_tracking.py::compute_marktscan_erfolgsquote()).
function renderMarktscanErfolgsquote(data) {
  if (!data) {
    return '<div class="row"><span class="muted-text">Noch keine abgeschlossenen Erfolgsmessungen.</span></div>';
  }
  const zeitHinweis = data.avg_tage_bis_erfolg !== null && data.avg_tage_bis_erfolg !== undefined
    ? '&Oslash; ' + data.avg_tage_bis_erfolg.toFixed(1) + ' Tage bis Erfolg (n=' +
      data.avg_tage_bis_erfolg_stichprobe_n + ')'
    : 'Ø Tage bis Erfolg noch nicht belastbar (n=' + data.avg_tage_bis_erfolg_stichprobe_n + ', Ziel n≥15)';
  return '<div class="row"><span>Erfolgsquote (n=' + data.anzahl_ausgewertet + ')</span>' +
    '<span>' + data.erfolge + '/' + data.anzahl_ausgewertet + ' = ' +
    data.erfolgsquote_pct.toFixed(1) + '%</span></div>' +
    '<div class="row"><span class="muted-text">' + zeitHinweis + '</span></div>' +
    '<div class="row"><span class="muted-text">' + data.offen + ' Messung(en) noch offen</span></div>';
}

// Z.ai-Richtungs-Erfolgsquote (2026-07-27, siehe agent/krypto/backward_tracking.py::
// compute_zai_richtung_performance()) - feste Tier-Reihenfolge wie SPOT_ASSETKLASSEN,
// damit ein (noch) leeres Tier sichtbar bleibt statt stillschweigend zu fehlen.
const ZAI_RICHTUNG_TIERS = [
  ["hebel", "Hebel"], ["krypto", "Krypto (Spot)"], ["aktien", "Aktien"],
  ["rohstoffe", "Rohstoffe"], ["etf", "ETF (Themen)"],
  ["hedge", "Hedge (Absicherung)"],
];

function renderZaiRichtungPerformanceTier(label, tierData) {
  if (!tierData) {
    return '<div class="row"><span class="muted-text">' + label +
      ': noch keine bewertbaren Z.ai-Richtungs-Calls.</span></div>';
  }
  const nebenHinweise = [];
  if (tierData.neutral > 0) nebenHinweise.push(tierData.neutral + 'x NEUTRAL');
  if (tierData.keine_klare_marktbewegung > 0) nebenHinweise.push(tierData.keine_klare_marktbewegung + 'x keine klare Marktbewegung');
  const nebenHinweisText = nebenHinweise.length
    ? ' <span class="muted-text">(+' + nebenHinweise.join(', ') + ', nicht mitgezaehlt)</span>' : '';
  if (tierData.anzahl_bewertet === 0) {
    return '<div class="row"><span class="muted-text">' + label +
      ': noch keine bewertbaren Z.ai-Richtungs-Calls' + nebenHinweisText + '.</span></div>';
  }
  // 2026-07-31, Screenshot-Review-Fund: anders als renderProviderPerformance()
  // fehlte hier der Hinweis auf kleine Stichproben - gleiche Schwelle
  // (PROVIDER_PERF_MIN_SAMPLE) nachgeruestet, damit n=1 nicht wie eine
  // belastbare Quote aussieht.
  const kleineStichprobe = tierData.anzahl_bewertet < PROVIDER_PERF_MIN_SAMPLE
    ? ' <span class="muted-text">(n&lt;' + PROVIDER_PERF_MIN_SAMPLE + ', noch nicht belastbar)</span>' : '';
  return '<div class="row"><span>' + label + ' (n=' + tierData.anzahl_bewertet + ')' + nebenHinweisText + kleineStichprobe + '</span>' +
    '<span>' + tierData.treffer + '/' + tierData.anzahl_bewertet + ' = ' +
    tierData.trefferquote_pct.toFixed(1) + '%</span></div>';
}


const API_HEALTH_GROUPS = {
  // MIT ROLLE, UND IN DER REIHENFOLGE DER KETTE (2026-08-10).
  //
  // Hier stand ["mistral", "gemini", "zai"] - OpenRouter fehlte vollstaendig,
  // obwohl er seit dem 08.08. ZWEITE Stufe der Signal-Kette ist und am 10.08.
  // saemtliche 21 Signale erzeugt hat, weil Geminis Tagesbudget leer war. Der
  // einzige Anbieter, der gerade arbeitet, war auf der Statusseite unsichtbar.
  //
  // Die Rolle steht dabei, weil der blosse Name die falsche Frage beantwortet:
  // "mistral: Fehler" sieht dramatisch aus, ist aber die dritte Stufe, die seit
  // dem 402 ohnehin gesperrt ist - waehrend ein Ausfall der ersten Stufe die
  // Produktion trifft. Ohne Rolle sind beide Zeilen gleich laut.
  "api-health-llm": [
    {key: "gemini", rolle: "Kette 1"},
    {key: "openrouter", rolle: "Kette 2"},
    {key: "mistral", rolle: "Kette 3"},
    {key: "zai", rolle: "Gegenprüfung"},
  ],
  "api-health-markt": ["coingecko", "kraken", "bitpanda", "yfinance"],
  "api-health-makro": [
    "fear_greed", "fred", "ecb", "china_pboc_lpr", "china_m2", "japan_boj",
    "coinmetrics", "defillama", "blockchain_com", "binance", "bybit", "okx",
    "cftc_cot", "sec_edgar", "eia", "finnhub", "finra", "deribit",
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
  return sourceKeys.map(function(eintrag) {
    // Zwei Formen zugelassen: schlichter Name (Markt-/Makro-Gruppen) oder
    // {key, rolle} (LLM-Gruppe, seit 2026-08-10).
    const key = (typeof eintrag === "string") ? eintrag : eintrag.key;
    const rolle = (typeof eintrag === "string") ? null : eintrag.rolle;
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
      } else if (entry.status === "budget_leer") {
        // WEDER GRUEN NOCH ROT (2026-08-10). Der Anbieter ist gesund, liefert
        // aber bis Mitternacht Pazifik (09:00 MESZ) nichts mehr. Gruen waere
        // gelogen - wer nachsieht, weil Signale ausbleiben, braucht genau
        // diese Zeile. Rot waere auch gelogen und hat am 09.08. die Diagnose
        // zwei Tage in die falsche Richtung geschickt.
        statusClass = "stale";
        statusText = "Tagesbudget leer, Reset 09:00 (" +
          fmtRelativeTime(entry.last_error_at) + ")";
      }
    }
    const beschriftung = rolle
      ? key + ' <span class="muted-text">(' + rolle + ')</span>'
      : key;
    return '<div class="row"><span>' + beschriftung + '</span><span class="' + statusClass + '">' +
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


function renderThemenfeldErfolg(t) {
  if (!t.thesen || t.thesen.length === 0) {
    return '<div class="row"><span class="muted-text">Keine aktive These.</span></div>';
  }
  let x = '<div class="row"><span>Thesen gesamt</span><span>' + t.anzahl_thesen + "</span></div>";
  x += '<div class="row"><span>davon messbar</span><span>' + t.anzahl_messbar + "</span></div>";
  if (t.anzahl_mit_urteil > 0) {
    x += '<div class="row"><span>Richtung getroffen</span><strong' +
      (t.treffer >= t.fehlschlaege ? ' class="ok"' : ' class="err"') + ">" +
      t.treffer + " von " + t.anzahl_mit_urteil + "</strong></div>";
  }
  x += '<div class="row"><span class="muted-text">&nbsp;</span></div>';
  for (const e of t.thesen) {
    const name = e.kategorie_anzeige || e.hauptgruppe;
    if (!e.messbar) {
      x += '<div class="row"><span>' + name + ' <span class="muted-text">(' +
        (e.richtung_anzeige || e.richtung) +
        ')</span></span><span class="muted-text">nicht messbar</span></div>';
      x += '<div class="row"><span class="muted-text">↳ ' + (e.grund || "") + "</span></div>";
      continue;
    }
    // "unentschieden" ist ein String, Treffer/Fehlschlag sind Boolesche - der
    // Unterschied muss sichtbar bleiben, sonst liest sich Zufall wie Koennen.
    let urteil, klasse;
    if (e.treffer === true) { urteil = "getroffen"; klasse = ' class="ok"'; }
    else if (e.treffer === false) { urteil = "daneben"; klasse = ' class="err"'; }
    else if (e.treffer === "unentschieden") { urteil = "unentschieden"; klasse = ""; }
    else { urteil = "kein Urteil (neutral)"; klasse = ""; }
    const pp = (e.ueberrendite_prozentpunkte >= 0 ? "+" : "") +
      e.ueberrendite_prozentpunkte.toFixed(1) + " pp";
    x += '<div class="row"><span>' + name + ' <span class="muted-text">(' +
      (e.richtung_anzeige || e.richtung) +
      ", " + e.tage_aktiv + " Tage, getragen von " +
      (e.getragen_von || []).join(", ") + ')</span></span><strong' + klasse + ">" +
      pp + " · " + urteil + "</strong></div>";
    const w = e.wirkungskette || {};
    x += '<div class="row"><span class="muted-text">↳ ' + w.assets_mit_kursreihe + " von " +
      w.assets_gesamt + " Assets mit Kursreihe, " + w.signale_gesamt + " Signale (" +
      w.signale_aufgeloest + " aufgelöst)</span></div>";
  }
  return x;
}

function renderWartendeThemen(w) {
  if (!w.vorschlaege || w.vorschlaege.length === 0) {
    const l = w.richtgroessen_lage || {};
    return '<div class="row"><span class="muted-text">Kein Themen-Vorschlag in Beobachtung. ' +
      l.aktive_thesen + " aktive Thesen, Richtgröße " + l.minimum + "–" + l.maximum +
      " — " + (l.hinweis || "") + "</span></div>";
  }
  let x = '<div class="row"><span>in Beobachtung</span><span>' + w.anzahl_wartend + "</span></div>";
  x += '<div class="row"><span>bereits reif</span><span>' + w.anzahl_reif + "</span></div>";
  // Die Richtgroesse SPERRT seit 07.08. nicht mehr - sie wird berichtet.
  // Deshalb hier "Lage", nicht "freie Plätze": das alte Wort hätte ein Budget
  // suggeriert, das es nicht mehr gibt.
  const lage = w.richtgroessen_lage || {};
  const lageKlasse = lage.lage === "unter" ? ' class="err"' : "";
  x += '<div class="row"><span>aktive Thesen</span><strong' + lageKlasse + ">" +
    lage.aktive_thesen + " (Richtgröße " + lage.minimum + "–" + lage.maximum + ")</strong></div>";
  x += '<div class="row"><span class="muted-text">' + (lage.hinweis || "") +
    " — verteilt auf " + lage.hauptgruppen_abgedeckt + " Hauptgruppen, " +
    lage.davon_neutral + " davon neutral.</span></div>";
  if (w.engpass_am) {
    // Die Zahl, die den Engpass ankuendigt - rot NUR wenn sie das Budget
    // wirklich uebersteigt, sonst ist sie eine harmlose Terminmeldung.
    // Keine Rotfaerbung mehr: seit dem Wegfall des Deckels ist ein
    // gemeinsamer Reifetag eine Terminmeldung, kein Engpass.
    x += '<div class="row"><span>am ' + w.engpass_am + " gleichzeitig reif</span><strong>" +
      w.engpass_anzahl + "</strong></div>";
  }
  x += '<div class="row"><span class="muted-text">&nbsp;</span></div>';
  for (const v of w.vorschlaege) {
    const name = v.kategorie_anzeige || (v.hauptgruppe || "");
    const stern = v.ist_schwerpunkt ? "★ " : "";
    const keineAssets = !v.handelbare_assets || v.handelbare_assets.length === 0;
    const rest = keineAssets
      ? '<strong class="err">kein handelbares Asset</strong>'
      : (v.ist_reif
          ? '<strong class="ok">reif</strong>'
          : "noch " + v.tage_bis_reif + " T. → " + v.reif_am);
    x += '<div class="row"><span>' + stern + name + ' <span class="muted-text">(' +
      (v.richtung_anzeige || v.vorgeschlagene_richtung || "—") + " · " +
      (v.mechanismus_anzeige || "") + " · " + v.tage_beobachtet + "/" + v.schwelle_tage +
      ' Tage)</span></span><span>' + rest + "</span></div>";
  }
  return x;
}

function renderHedge(h) {
  const pct = (v) => (v === null || v === undefined) ? "—" : v.toFixed(2) + " %";
  const pp = (v) => (v === null || v === undefined) ? "—" : (v >= 0 ? "+" : "") + v.toFixed(2) + " pp";
  if (!h.messbar) {
    return '<div class="row"><span class="muted-text">Nicht messbar: ' +
      (h.grund || "unbekannt") + "</span></div>";
  }
  let x = '<div class="row"><span>Rückschlag OHNE Absicherung</span><span>' +
    pct(h.rueckschlag_ohne_hedge_prozent) + "</span></div>";
  x += '<div class="row"><span>Rückschlag MIT Absicherung</span><span>' +
    pct(h.rueckschlag_mit_hedge_prozent) + "</span></div>";
  const gut = (h.daempfung_prozentpunkte || 0) > 0;
  x += '<div class="row"><span>Dämpfung</span><strong' + (gut ? ' class="ok"' : '') + ">" +
    pp(h.daempfung_prozentpunkte) + "</strong></div>";
  x += '<div class="row"><span>gezahlte Prämie (Renditeunterschied)</span><span>' +
    pp(h.praemie_prozent) + "</span></div>";
  x += '<div class="row"><span class="muted-text">' + (h.tage || 0) + " Tage · " +
    (h.hedge_symbole_bewertet || []).join(", ") + "</span></div>";
  if (h.teilweise_ohne_kurse) x += '<div class="row"><span class="err">ohne Kursreihe: ' +
    h.teilweise_ohne_kurse.join(", ") + "</span></div>";
  return x;
}

function renderZ3(z) {
  // Zwei Zahlen fuer dasselbe Portfolio: die Seite rechnet aus Snapshot-Preisen,
  // Z-3 aus der Kursreihe. Weichen sie ab, stimmt eine der Quellen nicht - am
  // 06.08. lag genau darin ein Fehler von ueber 50.000 EUR, den niemand sah,
  // weil die beiden Werte nie nebeneinander standen.
  const eur = (v) => (v === null || v === undefined) ? "—" :
    v.toLocaleString("de-DE", {minimumFractionDigits: 2, maximumFractionDigits: 2}) + " €";
  const pct = (v) => (v === null || v === undefined) ? "—" : v.toFixed(1) + " %";
  const ausgeloest = z.ausgeloest === true;
  let h = '<div class="row"><span>Rückschlag aktuell</span><strong' +
    (ausgeloest ? ' class="err"' : '') + '>' + pct(z.aktuell_prozent) +
    " (Schwelle " + pct(z.schwelle_prozent) + ")</strong></div>";
  h += '<div class="row"><span>größter Rückschlag im Fenster</span><span>' +
    pct(z.max_prozent) + (z.hoch_am ? " (" + z.hoch_am + " → " + (z.tief_am || "?") + ")" : "") +
    "</span></div>";
  if (ausgeloest) h += '<div class="row"><strong class="err">AUSGELÖST</strong></div>';
  if (z.datenbasis_duenn) h += '<div class="row"><span>Datenbasis</span><span>dünn (' +
    (z.tage_historie || 0) + " Tage)</span></div>";

  h += '<div class="row" style="margin-top:8px"><strong>Gegenprobe der Datenbasis</strong></div>';
  h += '<div class="row"><span>Wert laut Kursreihe' +
    (z.reihen_tag ? " (" + z.reihen_tag + ")" : "") + "</span><span>" + eur(z.reihen_wert_eur) + "</span></div>";
  h += '<div class="row"><span>Wert laut Snapshot-Preisen</span><span>' + eur(z.snapshot_wert_eur) + "</span></div>";
  const abw = z.abweichung_prozent;
  const warn = (abw !== null && abw !== undefined && abw > 5);
  h += '<div class="row"><span>Abweichung</span><strong' + (warn ? ' class="err"' : '') +
    ">" + pct(abw) + "</strong></div>";
  if (z.symbole_ohne_kurs) h += '<div class="row"><span>Symbole ohne Kurs</span><strong' +
    (z.symbole_ohne_kurs > 0 ? ' class="err"' : '') + ">" + z.symbole_ohne_kurs + "</strong></div>";
  if (warn) h += '<div class="row" class="err" style="font-size:0.9em">' +
    "Beide Zahlen beschreiben dasselbe Portfolio — weichen sie ab, ist eine der " +
    "beiden Datenquellen fehlerhaft und Z-3 rechnet auf der falschen.</div>";
  return h;
}

function renderRegimeStatus(r) {
  const label = REGIME_LABELS[r.regime] || r.regime;
  const cls = "regime-" + r.regime;
  let html = '<div class="row"><span>Stand</span><span>' + fmtDateTime(r.created_at) + '</span></div>';
  html += '<div class="row"><span>Regime</span><span class="' + cls + '"><strong>' + label + '</strong></span></div>';
  if (r.regime_reason) {
    const praefix = r.regime_source === "manuell" ? "⚠ " : "";
    html += '<div class="row"><span class="muted-text">' + praefix + r.regime_reason + '</span></div>';
  } else if (r.regime_source === "manuell") {
    html += '<div class="row"><span class="muted-text">⚠ manuell überschrieben</span></div>';
  }
  if (r.regime_persistenz_tage) {
    html += '<div class="row"><span class="muted-text">Regime seit ' + r.regime_persistenz_tage
      + ' Tag(en) regelbasiert bestätigt.</span></div>';
  }
  // REGIME-GLAETTUNG (2026-08-06). Bis heute zeigte diese Karte nur das harte
  // Label ("baer"/"bulle") - waehrend die Mindestkonfidenz seit der Glaettung am
  // STETIGEN Score haengt. Die Anzeige beschrieb damit ein Verfahren, das so
  // nicht mehr laeuft. Genau der Fall, den der Nutzer am 06.08. vermutet hat:
  // "hier haben wir jetzt ein anderes Konzept im Einsatz".
  if (r.regime_score_stetig !== null && r.regime_score_stetig !== undefined) {
    html += '<div class="row"><span>Regime-Score (stetig, 0 = klar bärisch)</span><span><strong>' +
      r.regime_score_stetig.toFixed(2) + "</strong></span></div>";
  }
  if (r.regime_min_konfidenz_stetig !== null && r.regime_min_konfidenz_stetig !== undefined) {
    html += '<div class="row"><span>daraus Mindestkonfidenz</span><span><strong>' +
      r.regime_min_konfidenz_stetig.toFixed(1) + " %</strong></span></div>";
  }
  if (r.btc_abstand_ema50_prozent !== null && r.btc_abstand_ema50_prozent !== undefined) {
    html += '<div class="row"><span>BTC zur EMA50</span><span>' +
      (r.btc_abstand_ema50_prozent >= 0 ? "+" : "") +
      r.btc_abstand_ema50_prozent.toFixed(2) + " %" +
      (r.btc_ema50_einordnung ? " (" + r.btc_ema50_einordnung + ")" : "") + "</span></div>";
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
  if (r.regime_konflikt_gesamt) {
    html += '<div class="row"><span>Regime-Konflikt-Übersicht</span><span>' + r.regime_konflikt_anzahl
      + ' von ' + r.regime_konflikt_gesamt + ' aktiven Kandidaten</span></div>';
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
    // DIE ALTE KARTE ZAEHLTE UEBER `groq_raw_response IS NOT NULL` - eine
    // Spalte, die nur die alte Kette schrieb. Seit dem Schnitt stand dort 0,
    // waehrend die Kette lief; auf derselben Karte meldete Z.ai zehn Aufrufe.
    // Zwei Zahlen, die einander widersprachen.
    const rb = data.rollen_budget || {};
    const toepfe = rb.toepfe || [];
    const zeig = (id, i) => {
      const el = document.getElementById(id);
      if (!el) return;
      const t = toepfe[i];
      el.textContent = t ? (t.verbraucht + " / " + t.grenze) : "-";
    };
    zeig("topf-gemini31", 0); zeig("topf-gemini35", 1);
    zeig("topf-openrouter", 2); zeig("topf-groq", 3);
    // DER ERSTE TOPF MIT REST IST DIE GRENZE, nicht die Summe (15.08.2026).
    // Hier stand `rest_gesamt` als "N Aufrufe frei" - 1.874 ueber alle vier
    // Toepfe. Arithmetisch richtig, als Aussage falsch: die Toepfe sind eine
    // Rueckfallkette, und hinter jedem steht ein anderes Modell.
    document.getElementById("rollen-rest").textContent =
      (rb.rest_aktiv === undefined ? "-"
       : rb.rest_aktiv + " frei in " + (rb.topf_aktiv || "?")
         + " · Kette gesamt " + (rb.rest_gesamt ?? "?"));
    document.getElementById("rollen-signale").textContent = rb.signale_heute ?? "-";
    document.getElementById("rollen-aufteilung").textContent =
      (rb.davon_hebel ?? 0) + " / " + (rb.davon_handlung ?? 0);
    // Die alte Kette bleibt sichtbar, aber als das, was sie ist: ohne
    // Aufrufer. Sie wegzulassen hiesse, eine Zahl verschwinden zu lassen,
    // ohne dass jemand sieht, dass sie verschwunden ist.
    document.getElementById("budget-total").textContent = b.verbraucht_gesamt + " / " + b.gesamt;
    document.getElementById("budget-alt-drei").textContent =
      b.hebel + " / " + b.marktscan + " / " + b.spot;
    document.getElementById("budget-multi-asset").textContent = b.multi_asset_heute;
    document.getElementById("budget-zai-gegenpruefung").textContent = b.zai_gegenpruefung_heute;
  }

  if (data.coingecko_quota) {
    const q = data.coingecko_quota;
    const el = document.getElementById("coingecko-quota");
    el.textContent = q.anzahl.toLocaleString() + " / " + q.limit.toLocaleString() + " (" + q.prozent + "%)";
    el.className = q.prozent >= 80 ? "stale" : "ok";
    document.getElementById("coingecko-quota-heute").textContent = (q.anzahl_heute ?? 0).toLocaleString();
  }

  if (data.llm_kontingent) {
    const k = data.llm_kontingent;
    document.getElementById("llm-kontingent-tag").textContent = k.tag_pazifik + " (Pazifik)";
    // Ampel bei 80 %: darunter ist Spielraum, darueber wird es fuer die
    // Produktion eng - die Reihenfolge kommt schon sortiert aus der DB.
    document.getElementById("llm-kontingent").innerHTML = (k.modelle || []).map(m =>
      '<div class="row"><span>&nbsp;&nbsp;' + m.modell + '</span><span class="' +
      (m.prozent >= 80 ? "stale" : "ok") + '">' + m.anzahl.toLocaleString() + " / " +
      m.limit.toLocaleString() + " (" + m.prozent + "%)</span></div>").join("");
  }




  document.getElementById("marktscan-erfolgsquote").innerHTML =
    renderMarktscanErfolgsquote(data.marktscan_erfolgsquote);


  // Gruppe C: Veto-Schatten + Gesamt (2026-07-28) - gleiche Render-Funktionen
  // wie Gruppe A/B, nur gegen die veto_schatten_*/gesamt_signalqualitaet-Felder.

  // R-5.10-Konfidenzschwellen-Nachtrag (2026-07-30) - gleiche Render-Funktionen
  // wie oben, nur gegen die nach Veto-Grund statt Provider gruppierten Daten.

  // Selbst-gewaehltes-HALTEN-Schatten-Tracking (2026-07-31) - Gegenfall zum
  // Veto-Schatten oben: kein Gate/Veto, das LLM hat sich selbst gegen einen
  // Trade entschieden. Gleiche Render-Funktionen, identisches Datenformat.
  if (data.ausstiegs_empfehlungen) {
    var ae = data.ausstiegs_empfehlungen;
    var liste = ae.empfehlungen || [];
    var html = "";
    if (!ae.parameter || ae.parameter.aktiv === false) {
      html = '<div class="row"><span class="muted-text">'
           + "über config abgeschaltet (risiko.ausstieg_trailing_*)</span></div>";
    } else if (!liste.length) {
      html = '<div class="row"><span class="muted-text">'
           + "kein offenes Signal über der Auslöseschwelle von "
           + ae.parameter.ausloese_r.toFixed(1) + " R (" + (ae.geprueft || 0)
           + " geprüft)</span></div>";
    } else {
      html = liste.map(function (e) {
        // Der gesicherte Betrag ist die eigentliche Botschaft: so viel steht
        // fest, wenn der Stop nachgezogen wird und der Kurs dreht.
        var sichert = (e.sichert_r >= 0 ? "+" : "") + e.sichert_r.toFixed(2);
        return '<div class="row"><span>' + e.symbol
             + ' <span class="muted-text">(' + e.tier + ", " + e.richtung
             + ", seit " + e.seit + ")</span></span>"
             + '<span>MFE ' + e.mfe_r.toFixed(2) + " R &rarr; Stop auf "
             + Number(e.stop_empfohlen).toPrecision(6)
             + ' <span class="ok">sichert ' + sichert + " R</span></span></div>";
      }).join("");
      html += '<div class="row"><span class="muted-text">'
            + liste.length + " von " + (ae.geprueft || 0)
            + " offenen Signalen über der Schwelle ("
            + ae.parameter.ausloese_r.toFixed(1) + " R Auslösung, "
            + ae.parameter.abstand_r.toFixed(1) + " R Abstand)</span></div>";
    }
    document.getElementById("ausstieg-empfehlungen").innerHTML = html;
  }



  if (data.api_health) {
    for (const [elementId, sourceKeys] of Object.entries(API_HEALTH_GROUPS)) {
      document.getElementById(elementId).innerHTML = renderApiHealthGroup(sourceKeys, data.api_health);
    }
  }


  if (data.themenfeld_erfolg) {
    document.getElementById("themenfeld-erfolg-card").style.display = "block";
    document.getElementById("themenfeld-erfolg-body").innerHTML =
      renderThemenfeldErfolg(data.themenfeld_erfolg);
  }

  if (data.wartende_themen) {
    document.getElementById("wartende-themen-card").style.display = "block";
    document.getElementById("wartende-themen-body").innerHTML =
      renderWartendeThemen(data.wartende_themen);
  }

  if (data.hedge_wirksamkeit) {
    document.getElementById("hedge-card").style.display = "block";
    document.getElementById("hedge-body").innerHTML = renderHedge(data.hedge_wirksamkeit);
  }

  if (data.z3_und_bewertung) {
    document.getElementById("z3-card").style.display = "block";
    document.getElementById("z3-body").innerHTML = renderZ3(data.z3_und_bewertung);
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
// FUENF SEKUNDEN STATT ZWEI (14.08.2026).
//
// Im Log des Nutzers riss der Statusaufbau zwanzigmal in drei Minuten die
// Warnschwelle: 1,24 bis 2,71 s bei einem Takt von 2,0 s. Ab da ueberlappen
// die Anfragen, und jede verzoegert die naechste weiter.
//
// DIE URSACHE IST NICHT DIE SEITE. Am Desktop dauert ein Aufbau kalt 0,42 s
// und warm 0,03 s - der Zwischenspeicher wirkt. Die Spitzen fielen GENAU in
// das Fenster, in dem die Rollen-Kette lief (14:21:07 Hebel-Screening,
// 14:21:13 Rollen-Kette): dieselbe Datenbank, dieselbe CPU eines i5-4300U von
// 2013. Es ist Konkurrenz um die Maschine, kein Defekt der Karte.
//
// DESHALB DER TAKT UND NICHT NOCH EIN CACHE. Gegen Konkurrenz hilft kein
// Zwischenspeicher - der Aufbau ist ja bereits schnell. Was hilft, ist,
// seltener zu fragen. Fuenf Sekunden geben auch dem langsamsten gemessenen
// Aufbau (2,71 s) noch das Doppelte an Luft, und eine Fernsteuerung, die man
// beim Beobachten eines Laufs benutzt, braucht keine Zwei-Sekunden-Aufloesung.
setInterval(refreshStatus, 5000);
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
    watchlist_provider,
    fred_api_key,
    access_token: str,
    log_path: Path,
) -> Flask:
    # Werkzeug (Flasks Dev-Server) loggt sonst jede Request-Zeile inkl. voller
    # URL an den Root-Logger - ohne diese Zeile wuerde der Token bei jedem
    # GET / (Query-Param, siehe Modul-Docstring in remote/server.py) im
    # Klartext in data/tradinginfotool.log landen.
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    # Restart-Fix (2026-07-23, siehe Memory project_watchlist_live_reload_fix):
    # `watchlist_provider` (config.get_watchlist selbst, siehe main.py) statt
    # einer beim Server-Start eingefrorenen Liste - jede Route ruft sie bei
    # jedem Request frisch auf, damit ein neuer Watchlist-Eintrag (z.B. per
    # "In Watchlist uebernehmen") auch hier ohne App-Neustart sichtbar wird.

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
            status = build_status(conn, watchlist_provider(), log_path)
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
            background.refresh_prices_job(coingecko_client, conn_factory, watchlist_provider)
            background.refresh_securities_prices_job(YFinanceClient(), conn_factory, watchlist_provider)

        threading.Thread(target=_run, daemon=True).start()
        return jsonify({"started": True}), 202

    @app.route("/api/marktscan", methods=["POST"])
    def api_marktscan():
        if background.marktscan_lock.locked():
            return jsonify({"error": "already_running"}), 409

        threading.Thread(
            target=background.marktscan_job,
            args=(coingecko_client, kraken_client, conn_factory, watchlist_provider, fred_api_key),
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
