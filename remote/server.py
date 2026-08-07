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
  <div class="row"><span>LLM-Budget heute (Krypto)</span><span id="budget-total">-</span></div>
  <div class="row"><span>&nbsp;&nbsp;davon Hebel</span><span id="budget-hebel">-</span></div>
  <div class="row"><span>&nbsp;&nbsp;davon Marktscan</span><span id="budget-marktscan">-</span></div>
  <div class="row"><span>&nbsp;&nbsp;davon Spot-Rotation</span><span id="budget-spot">-</span></div>
  <div class="row"><span>Multi-Asset heute (Aktien/Rohstoffe/Hedge/ETF, separates Budget)</span><span id="budget-multi-asset">-</span></div>
  <div class="row"><span>Z.ai-Gegenprüfung heute (Konsistenz+Richtung, kein Tagesdeckel)</span><span id="budget-zai-gegenpruefung">-</span></div>
</div>

<div class="card">
  <div class="row"><span>CoinGecko-Kontingent diesen Monat</span><span id="coingecko-quota">-</span></div>
  <div class="row"><span>&nbsp;&nbsp;davon heute</span><span id="coingecko-quota-heute">-</span></div>
  <div class="row"><span class="muted-text">Monatliches Call-Kontingent (2026-07-31, echte 80%-Warnmail von
  CoinGecko ausgeloest) - bei 100% wird laut CoinGecko hart gedeckelt. Warnmails bei 80%/90% (config.yaml
  coingecko_quota.warnschwellen_prozent), je Schwelle nur einmal pro Kalendermonat. Tages-Zeile (2026-08-01) macht
  sichtbar, an welchem Tag der Verbrauch tatsaechlich ansteigt.</span></div>
</div>

</div>

<div class="section-header section-a">
  <span class="section-badge">A</span>
  <span class="section-title">Ausgeführte Empfehlungen</span>
  <span class="section-sub">real, im Handel/Portfolio wirksam</span>
</div>
<div class="section-group group-a">

<div class="card">
  <div class="row"><strong>Provider-Performance (Spot, nach Assetklasse)</strong></div>
  <div class="row"><span class="muted-text">Je LLM-Anbieter: wie viele SEINER Spot-Empfehlungen bereits abschliessend
  entschieden sind (Kurs erreichte Take-Profit oder Stop-Loss) - je Assetklasse getrennt, weil unterschiedliche
  Risikoprofile. Zeigt NUR reale, aufgeloeste Ergebnisse, kein Backtest. Zahl in Klammern: aufgeloest / insgesamt
  gesendet.</span></div>
  <div id="provider-performance-spot"></div>
  <div class="row"><strong>Provider-Performance (Hebel)</strong></div>
  <div class="row"><span class="muted-text">Gleiches Prinzip fuer Hebel-Positionen (zusaetzlich: Liquidation als
  drittes moegliches Ergebnis). Angaben unter 15 aufgeloesten Signalen sind statistisch noch nicht belastbar.</span></div>
  <div id="provider-performance-hebel"></div>
</div>

<div class="card">
  <div class="row"><strong>Konfidenz-Kalibrierung (Spot, nach Assetklasse)</strong></div>
  <div class="row"><span class="muted-text">Vergleicht je Konfidenz-Band (niedrig/mittel/hoch, gleiche Grenzen
  wie der "Konfidenz X%"-Risikofaktor) die durchschnittlich VORHERGESAGTE Konfidenz mit der tatsaechlich
  eingetretenen Trefferquote bereits abgeschlossener Signale - grosse Abweichungen (orange) deuten auf eine
  nicht gut kalibrierte Konfidenzangabe hin.</span></div>
  <div id="konfidenz-kalibrierung-spot"></div>
  <div class="row"><strong>Konfidenz-Kalibrierung (Hebel)</strong></div>
  <div id="konfidenz-kalibrierung-hebel"></div>
</div>

<div class="card">
  <div class="row"><strong>Richtungstreffer-Quote (Mindestziel/MFE)</strong></div>
  <div class="row"><span class="muted-text">Unabhaengig von der exakten Take-Profit-Zonen-Ausfuehrung - wie oft
  war die Richtung wenigstens ZEITWEISE (Maximum Favorable Excursion) mindestens die Mindestziel-Schwelle wert?
  Zaehlt auch spaeter ueberholte/abgelaufene Signale mit, wenn sie zwischenzeitlich in die richtige Richtung
  liefen. Ø Tage bis Mindestziel nur bei ausreichender Stichprobe (n≥15) empirisch belastbar.</span></div>
  <div class="row"><span class="muted-text"><b>Einordnung 06.08.:</b> MFE ist <b>kein Erfolgsmaß</b>, solange
  der Stop-Abstand variiert - sie belohnt enge Stops systematisch, und genau die liefern gemessen −1,04 R.
  Diese Karte beantwortet <i>"war die Richtung je richtig?"</i>, nicht <i>"war das Signal gut?"</i>. Für die
  zweite Frage ist die Systemgüte (SQN/Expectancy) weiter unten zuständig.</span></div>
  <div id="richtungstreffer-quote"></div>
</div>

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

<div class="card">
  <div class="row"><strong>Z.ai-Richtungs-Erfolgsquote (unabhaengig von Mistral)</strong></div>
  <div class="row"><span class="muted-text">Misst NICHT, ob Z.ai mit Mistral uebereinstimmte (das zeigt das
  Detail-Panel je Signal) - sondern ob Z.ais UNABHAENGIGE Richtungs-Ableitung (Call 2, ohne Mistrals Empfehlung
  als Vorgabe) im Nachhinein mit der tatsaechlichen Kursbewegung uebereinstimmte. Relevant, weil Mistral bei
  Hebel durch die Einstellung "Nur Long" strukturell nie SHORT empfehlen darf - diese Quote zeigt, wie gut Z.ai
  unabhaengig davon liegen wuerde. Gleiche Basis wie die Richtungstreffer-Quote (Maximum Favorable Excursion,
  nicht nur die exakte TP/SL-Zone) - zaehlt auch Signale mit, die spaeter ueberholt/abgelaufen sind aber
  zwischenzeitlich klar in eine Richtung liefen. NEUTRAL-Urteile und Faelle ohne klare Marktbewegung zaehlen
  nicht mit (analog zu HALTEN). Bezieht sich hier NUR auf real ausgefuehrte Empfehlungen - der Veto-Schatten-
  Anteil steht in Gruppe C.</span></div>
  <div id="zai-richtung-performance"></div>
</div>

</div>

<div class="section-header section-c">
  <span class="section-badge">C</span>
  <span class="section-title">Veto-Schatten</span>
  <span class="section-sub">hypothetisch, nie ausgeführt + Gesamt</span>
</div>
<div class="section-group group-c">

<div class="card">
  <div class="row"><strong>Veto-Schatten-Performance</strong></div>
  <div class="row"><span class="muted-text">Das LLM wollte hier tatsaechlich handeln (Kaufen/Verkaufen/Eröffnen),
  wurde aber durch einen deterministischen Risk-Gate-Veto (CRV-Pflicht, Bitpanda/Cash-Veto, Regime-
  Mindestkonfidenz, Nur-Long-Deckel, ...) auf HALTEN zurueckgestuft - der Trade wurde NIE ausgefuehrt. Diese
  Karte zeigt, wie diese rein hypothetischen Vorschlaege sich tatsaechlich entwickelt haetten, damit sie nicht
  spurlos aus der Bewertung verschwinden.</span></div>
  <div id="veto-schatten-performance-spot"></div>
  <div class="row"><strong>&nbsp;&nbsp;davon Hebel</strong></div>
  <div id="veto-schatten-performance-hebel"></div>
</div>

<div class="card">
  <div class="row"><strong>Veto-Schatten-Performance nach Veto-Grund</strong></div>
  <div class="row"><span class="muted-text">Wie oben, aber nach dem Veto-GRUND aufgeschluesselt statt nach
  Provider (2026-07-30, R-5.10-Konfidenzschwellen-Nachtrag) - beantwortet die fuer eine Schwellen-Entscheidung
  eigentliche Frage: schlagen sich Konfidenzschwellen-Vetos (R-5.10) anders als CRV&lt;2.0-Vetos, je
  Assetklasse?</span></div>
  <div class="row"><span class="muted-text"><b>Nachtrag 06.08.:</b> der Grund
  <code>nur_long_historisch</code> beschreibt ein Veto, das es SEIT DEM 05.08. NICHT MEHR GIBT
  (Nur-Long-Umbau: beide Richtungen laufen durch, SHORT wird nur nicht gemailt). Seine Fälle bleiben
  als Historie stehen, es kommen aber keine neuen dazu - eine Trefferquote daraus beschreibt die
  Vergangenheit, nicht das laufende System.</span></div>
  <div id="veto-schatten-performance-nach-grund-spot"></div>
  <div class="row"><strong>&nbsp;&nbsp;davon Hebel</strong></div>
  <div id="veto-schatten-performance-nach-grund-hebel"></div>
</div>

<div class="card">
  <div class="row"><strong>Systemgüte (SQN / Expectancy)</strong></div>
  <div class="row"><span class="muted-text">Die Zielgröße des Systems, nicht nur eine Trefferquote
  (2026-08-02, Herleitung in Basisinfos/Zielgroessen_und_Erfolgsmasse.md). <b>Expectancy</b> in R =
  mittlerer Gewinn je riskierter Einheit, muss über 0 liegen. <b>SQN</b> = Mittelwert ÷ Streuung × √n
  (Van Tharp): unter 1,5 kaum handelbar, 1,5-2 durchschnittlich, ab 2 gut - bestraft also Schwankung,
  nicht nur einen schwachen Durchschnitt. Die <b>Auflösungsquote</b> steht bewusst daneben: Gruppen mit
  weiten Stops werden kaum aufgelöst, ihre Quoten sind entsprechend selektiert.</span></div>
    <div class="row"><span class="muted-text"><b>Signalbeitrag</b> (2026-08-03) ist die wichtigere Zahl, solange nur eine Marktphase beobachtet ist: Expectancy minus dem, was ein reiner Zufallseinstieg mit denselben Stop- und Zielabständen im selben Zeitraum gebracht hätte. Gemessen am 03.08. verliert dieser Zufallseinstieg 0,11 bis 0,26 R - ein negativer SQN heißt also nicht zwingend, dass das System nicht funktioniert, sondern kann schlicht die Marktphase sein. Positiver Signalbeitrag = die Signale tragen etwas bei, was der Zufall nicht hergibt.</span></div>
  <div id="systemguete"></div>
</div>

<div class="card">
  <h2>Stop nachziehen &mdash; offene Signale mit ungesichertem Gewinn</h2>
  <div class="row"><span class="muted-text">Advisory-only: gerechnet und gemeldet, nicht ausgef&uuml;hrt. Grundlage (2026-08-04): 50&nbsp;% der Signale standen einmal bei +1R, nur 17,6&nbsp;% kamen am Ziel an &ndash; Positionen geben Gewinne zur&uuml;ck. Ein Trailing-Stop ab +1R hob den Erwartungswert von &minus;0,176 auf &minus;0,084&nbsp;R (495 echte Signale, symbolgeblocktes Intervall [+0,051; +0,131], h&auml;lt im Split-Sample und &uuml;ber alle drei Marktphasen). Das ist <b>kein</b> Breakeven-Lock &ndash; der wurde am 01.08. gemessen und verworfen, er kostet 63&nbsp;% der Gewinner.</span></div>
  <div id="ausstieg-empfehlungen"></div>
</div>

<div class="card">
  <div class="row"><strong>Selbst gewähltes HALTEN - Schatten-Performance</strong></div>
  <div class="row"><span class="muted-text">Das LLM hat sich HIER von sich aus (kein Gate/Veto)
  gegen einen Trade entschieden, aber trotzdem eine hypothetische Zone angegeben (2026-07-31,
  Regel 28/33) - zeigt, ob die eigene Zurueckhaltung im Nachhinein richtig war. Getrennt von der
  Veto-Schatten-Karte oben, da dort das Gate entschieden hat, hier das LLM selbst.</span></div>
  <div id="selbst-halten-performance-spot"></div>
  <div class="row"><strong>&nbsp;&nbsp;davon Hebel</strong></div>
  <div id="selbst-halten-performance-hebel"></div>
</div>

<div class="card">
  <div class="row"><strong>Selbst gewähltes HALTEN nach Grund</strong></div>
  <div id="selbst-halten-performance-nach-grund-spot"></div>
  <div class="row"><strong>&nbsp;&nbsp;davon Hebel</strong></div>
  <div id="selbst-halten-performance-nach-grund-hebel"></div>
</div>

<div class="card">
  <div class="row"><strong>Z.ai-Richtungs-Erfolgsquote (Veto-Schatten)</strong></div>
  <div class="row"><span class="muted-text">Wie die Z.ai-Karte in Gruppe B, aber NUR fuer die vetoten
  Vorschlaege oben - gerade hier ist Z.ais unabhaengiges Urteil interessant, weil es auf einen Fall angewendet
  wird, den das primaere Regelwerk selbst blockiert hat.</span></div>
  <div id="zai-richtung-performance-schatten"></div>
</div>

<div class="card">
  <div class="row"><strong>Gesamt-Signalqualitaet (unabhaengig vom Risk-Gate)</strong></div>
  <div class="row"><span class="muted-text">Real ausgefuehrte Empfehlungen (Gruppe A) PLUS Veto-Schatten
  zusammengefasst - beantwortet "wie gut waere das Modell insgesamt gelegen, wenn man das Risk-Gate ausblendet?".
  Nur eine Anzeige-Zusammenfuehrung, keine eigene Datenquelle - Real und Schatten bleiben in der Datenbank
  getrennt gespeichert.</span></div>
  <div id="gesamt-signalqualitaet-spot"></div>
  <div class="row"><strong>&nbsp;&nbsp;davon Hebel</strong></div>
  <div id="gesamt-signalqualitaet-hebel"></div>
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

<div class="card" id="richtungsverteilung-card" style="display:none">
  <div class="row"><strong>Richtungsverteilung LONG / SHORT</strong></div>
  <div class="row"><span class="muted-text">Seit dem Nur-Long-Umbau am 05.08. laufen BEIDE Richtungen
  normal durch die Pipeline. SHORT wird nur nicht gemailt und im Hebel-Tab standardmäßig ausgeblendet -
  gemessen wird es weiterhin. Diese Karte war bisher die einzige Sicht auf das, was das System tatsächlich
  vorschlägt, und fehlte auf der Seite (nachgezogen 06.08.).</span></div>
  <div id="richtungsverteilung-body"></div>
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

function renderProviderPerformance(tierData, offenInfo, sendeData) {
  const sendeD = sendeData || {};
  // Provider-Sendezaehler-Fix (2026-07-28, Nutzer-Frage "wie oft hat Gemini
  // ueberhaupt welche Signale gesendet?"): ein Provider mit Sendungen aber
  // noch KEINEM aufgeloesten Signal war bisher komplett unsichtbar (nur
  // tierData durchsucht) - jetzt Vereinigung beider Schluesselmengen, damit
  // z.B. Gemini (selten eingesetzt) sichtbar bleibt, auch ohne Resolved-Wert.
  const providers = Array.from(new Set(Object.keys(tierData).concat(Object.keys(sendeD))));
  if (providers.length === 0) {
    // 2026-07-21, Nutzer-Fund: "noch keine Daten" ohne Begruendung war nicht
    // nachvollziehbar - erklaeren WARUM (keine aufgeloesten Signale, nicht:
    // Feature kaputt/kein Tracking) statt nur den leeren Zustand zu melden.
    return '<div class="row"><span class="muted-text">Noch keine abgeschlossenen Signale in dieser Kategorie ' +
      '(Kurs hat bei keinem bisherigen Signal Take-Profit oder Stop-Loss erreicht) - kann je nach Marktlage ' +
      'Tage bis Wochen dauern.</span></div>' + renderOffeneSignaleHinweis(offenInfo);
  }
  return providers.map(function(p) {
    const d = tierData[p];
    const gesendet = sendeD[p];
    const gesendetText = gesendet !== undefined ? ' / ' + gesendet + ' gesendet' : '';
    if (!d) {
      return '<div class="row"><span>' + p + ' (0' + gesendetText + ')</span>' +
        '<span class="muted-text">noch kein Signal aufgeloest</span></div>';
    }
    const winRate = d.win_rate !== null && d.win_rate !== undefined
      ? Math.round(d.win_rate * 100) + "%" : "-";
    const crv = d.avg_realisiertes_crv !== null && d.avg_realisiertes_crv !== undefined
      ? d.avg_realisiertes_crv.toFixed(2) : "-";
    const kleineStichprobe = d.anzahl_resolved < PROVIDER_PERF_MIN_SAMPLE
      ? ' <span class="muted-text">(n&lt;' + PROVIDER_PERF_MIN_SAMPLE + ', noch nicht belastbar)</span>' : '';
    return '<div class="row"><span>' + p + ' (' + d.anzahl_resolved + gesendetText + ')' + kleineStichprobe + '</span>' +
      '<span>Win-Rate ' + winRate + ', &oslash; CRV ' + crv + '</span></div>';
  }).join("") + renderOffeneSignaleHinweis(offenInfo);
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

function renderSpotProviderPerformanceByAssetklasse(perfData, offeneData, sendeData) {
  return SPOT_ASSETKLASSEN.map(function([key, label]) {
    return '<div class="row"><span class="muted-text">' + label + '</span></div>' +
      renderProviderPerformance(perfData[key] || {}, (offeneData || {})[key], (sendeData || {})[key]);
  }).join("");
}

// Konfidenz-Kalibrierungskurve (2026-07-26, Punkt 3 des Regime-Persistenz-
// Folge-Vorschlags - siehe agent/krypto/backward_tracking.py::
// compute_konfidenz_kalibrierung()). Bucket-Grenzen/Reihenfolge fest, damit
// ein (noch) leeres Band sichtbar bleibt statt stillschweigend zu fehlen -
// gleiches Prinzip wie SPOT_ASSETKLASSEN oben.
const KONFIDENZ_BUCKET_ORDER = [
  ["niedrig", "Niedrig (<55%)"], ["mittel", "Mittel (55-70%)"], ["hoch", "Hoch (≥70%)"],
];
// Rein optische Hervorhebung grosser Abweichungen (nicht: neuer Deckel/neue
// Regel) - 15 Prozentpunkte ist keine backtestete Schwelle, nur ein grober
// Blickfang fuer "hier lohnt ein genauerer Blick".
const KONFIDENZ_DIFFERENZ_AUFFAELLIG_PP = 15;

function renderKonfidenzKalibrierungTier(tierData) {
  if (!tierData || Object.keys(tierData).length === 0) {
    return '<div class="row"><span class="muted-text">Noch keine abgeschlossenen Signale mit Konfidenzwert ' +
      'in dieser Kategorie.</span></div>';
  }
  return KONFIDENZ_BUCKET_ORDER.map(function([key, label]) {
    const b = tierData[key];
    if (!b) return "";
    const stichprobeHinweis = !b.ausreichend_stichprobe
      ? ' <span class="muted-text">(n=' + b.anzahl + ', noch nicht belastbar)</span>'
      : ' <span class="muted-text">(n=' + b.anzahl + ')</span>';
    const auffaellig = Math.abs(b.differenz_prozentpunkte) >= KONFIDENZ_DIFFERENZ_AUFFAELLIG_PP;
    return '<div class="row"><span>' + label + stichprobeHinweis + '</span>' +
      '<span class="' + (auffaellig ? "stale" : "") + '">vorhergesagt &oslash; ' +
      b.avg_vorhergesagte_konfidenz_pct.toFixed(1) + '% / tatsächlich ' +
      b.tatsaechliche_trefferquote_pct.toFixed(1) + '%</span></div>';
  }).join("");
}

function renderKonfidenzKalibrierungByAssetklasse(kalibData) {
  return SPOT_ASSETKLASSEN.map(function([key, label]) {
    return '<div class="row"><span class="muted-text">' + label + '</span></div>' +
      renderKonfidenzKalibrierungTier(kalibData[key] || {});
  }).join("");
}

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

function renderRichtungstrefferQuote(data) {
  if (!data) return "";
  return renderRichtungstrefferQuoteTier("Spot", data.spot) +
    renderRichtungstrefferQuoteTier("Hebel", data.hebel);
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

function renderZaiRichtungPerformance(data) {
  if (!data) return "";
  return ZAI_RICHTUNG_TIERS.map(function([key, label]) {
    return renderZaiRichtungPerformanceTier(label, data[key]);
  }).join("");
}

const API_HEALTH_GROUPS = {
  "api-health-llm": ["mistral", "gemini", "zai"],
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

function renderRichtungsverteilung(r) {
  const pct = (v) => (v === null || v === undefined) ? "—" : v.toFixed(1) + " %";
  let h = '<div class="row"><span>Zeitraum</span><span>ab ' + (r.ab_datum || "?") + "</span></div>";
  h += '<div class="row"><span>SHORT-Anteil an allen Signalen</span><strong>' +
    pct(r.short_anteil_pct) + "</strong></div>";
  for (const [richtung, v] of Object.entries(r.richtungen || {})) {
    h += '<div class="row" style="margin-top:6px"><strong>' + richtung + "</strong></div>";
    h += '<div class="row"><span>Signale / davon ERÖFFNEN</span><span>' +
      v.signale + " / " + v.eroeffnen + "</span></div>";
    h += '<div class="row"><span>aufgelöst / davon Ziel erreicht</span><span>' +
      v.aufgeloest + " / " + v.take_profit + "</span></div>";
    // Trefferquote NUR zeigen, wenn sie belastbar ist. Eine Prozentzahl aus
    // drei Fällen sieht genauso aus wie eine aus dreihundert - und wird auch so
    // gelesen. Lieber die Fallzahl zeigen als eine Zahl, die Sicherheit
    // vortäuscht (Methodik: unter 30 aufgelösten Fällen kein Ergebnis).
    if (v.belastbar) {
      h += '<div class="row"><span>Trefferquote / Erwartungswert</span><span>' +
        pct(v.trefferquote_pct) + " / " +
        (v.erwartungswert_r === null || v.erwartungswert_r === undefined
          ? "—" : v.erwartungswert_r.toFixed(2) + " R") + "</span></div>";
    } else {
      h += '<div class="row"><span class="muted-text">noch nicht belastbar (' +
        v.aufgeloest + " von 30 aufgelösten Fällen)</span></div>";
    }
  }
  return h;
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
    document.getElementById("budget-total").textContent = b.verbraucht_gesamt + " / " + b.gesamt;
    document.getElementById("budget-hebel").textContent = b.hebel;
    document.getElementById("budget-marktscan").textContent = b.marktscan;
    document.getElementById("budget-spot").textContent = b.spot;
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

  if (data.provider_performance) {
    const offen = data.offene_signale || {};
    const sende = data.provider_sendezaehler || {};
    document.getElementById("provider-performance-spot").innerHTML =
      renderSpotProviderPerformanceByAssetklasse(data.provider_performance, offen, sende);
    document.getElementById("provider-performance-hebel").innerHTML =
      renderProviderPerformance(data.provider_performance.hebel || {}, offen.hebel, sende.hebel);
  }

  if (data.konfidenz_kalibrierung) {
    document.getElementById("konfidenz-kalibrierung-spot").innerHTML =
      renderKonfidenzKalibrierungByAssetklasse(data.konfidenz_kalibrierung);
    document.getElementById("konfidenz-kalibrierung-hebel").innerHTML =
      renderKonfidenzKalibrierungTier(data.konfidenz_kalibrierung.hebel || {});
  }

  if (data.richtungstreffer_quote) {
    document.getElementById("richtungstreffer-quote").innerHTML =
      renderRichtungstrefferQuote(data.richtungstreffer_quote);
  }

  document.getElementById("marktscan-erfolgsquote").innerHTML =
    renderMarktscanErfolgsquote(data.marktscan_erfolgsquote);

  if (data.zai_richtung_performance) {
    document.getElementById("zai-richtung-performance").innerHTML =
      renderZaiRichtungPerformance(data.zai_richtung_performance);
  }

  // Gruppe C: Veto-Schatten + Gesamt (2026-07-28) - gleiche Render-Funktionen
  // wie Gruppe A/B, nur gegen die veto_schatten_*/gesamt_signalqualitaet-Felder.
  if (data.veto_schatten_performance) {
    document.getElementById("veto-schatten-performance-spot").innerHTML =
      renderSpotProviderPerformanceByAssetklasse(data.veto_schatten_performance, {}, {});
    document.getElementById("veto-schatten-performance-hebel").innerHTML =
      renderProviderPerformance(data.veto_schatten_performance.hebel || {}, null, null);
  }

  // R-5.10-Konfidenzschwellen-Nachtrag (2026-07-30) - gleiche Render-Funktionen
  // wie oben, nur gegen die nach Veto-Grund statt Provider gruppierten Daten.
  if (data.veto_schatten_performance_nach_grund) {
    document.getElementById("veto-schatten-performance-nach-grund-spot").innerHTML =
      renderSpotProviderPerformanceByAssetklasse(data.veto_schatten_performance_nach_grund, {}, {});
    document.getElementById("veto-schatten-performance-nach-grund-hebel").innerHTML =
      renderProviderPerformance(data.veto_schatten_performance_nach_grund.hebel || {}, null, null);
  }

  // Selbst-gewaehltes-HALTEN-Schatten-Tracking (2026-07-31) - Gegenfall zum
  // Veto-Schatten oben: kein Gate/Veto, das LLM hat sich selbst gegen einen
  // Trade entschieden. Gleiche Render-Funktionen, identisches Datenformat.
  if (data.systemguete) {
    document.getElementById("systemguete").innerHTML =
      Object.keys(data.systemguete).sort().map(function (tier) {
        return ["real", "schatten"].map(function (art) {
          var k = data.systemguete[tier][art];
          if (!k || !k.anzahl_bewertet) { return ""; }
          var ew = k.expectancy_r === null ? "-" : (k.expectancy_r >= 0 ? "+" : "") + k.expectancy_r.toFixed(3);
          // Bootstrap-Intervall direkt an den Punktwert (2026-08-03): "-0,299 R"
          // liest sich exakt, beruht aber auf wenigen Trades. Das Intervall
          // zeigt, wie weit der wahre Wert streuen kann.
          if (k.expectancy_ci_unten !== null && k.expectancy_ci_unten !== undefined) {
            ew += ' <span class="muted-text">[' + k.expectancy_ci_unten.toFixed(2) +
                  " bis " + k.expectancy_ci_oben.toFixed(2) + "]</span>";
          }
          var sqn = k.sqn === null ? "-" : k.sqn.toFixed(2) + " (" + k.sqn_einordnung + ")";
          var pf = k.profit_factor === null ? "-" : k.profit_factor.toFixed(2);
          var auf = k.aufloesungsquote === null ? "-" : (k.aufloesungsquote * 100).toFixed(0) + "%";
          var warn = k.sqn_belastbar ? "" : ' <span class="muted-text">[n&lt;30]</span>';
          // Zweite Zeile: Signalbeitrag gegen die mechanische Basislinie
          // (2026-08-03). Ohne diesen Bezugspunkt liest sich ein negativer SQN
          // als kaputtes System, obwohl der Zufallseinstieg im selben Zeitraum
          // noch mehr verliert - Begruendung in basislinie_erwartungswert().
          // Erst ab anzahl_bewertet >= 30 (dieselbe Schwelle wie sqn_belastbar):
          // ein Signalbeitrag aus 8 Trades gegen eine Basislinie aus tausenden
          // Ziehungen suggeriert eine Genauigkeit, die er nicht hat - krypto/real
          // stand am 03.08. mit n=8 bei "-1,069 R" auf dieser Karte.
          var zusatz = "";
          if (k.signalbeitrag_r !== null && k.signalbeitrag_r !== undefined
              && k.sqn_belastbar) {
            var sb = (k.signalbeitrag_r >= 0 ? "+" : "") + k.signalbeitrag_r.toFixed(3);
            var blw = (k.basislinie_erwartungswert_r >= 0 ? "+" : "") +
                      k.basislinie_erwartungswert_r.toFixed(3);
            var chance = "";
            if (k.anteil_positiv !== null && k.anteil_positiv !== undefined) {
              chance = " | " + (k.anteil_positiv * 100).toFixed(0) +
                       "% der Bootstrap-Ziehungen positiv";
            }
            // Zeitraum mit ausweisen: derselbe Parametersatz liefert je nach
            // Fenster entgegengesetzte Vorzeichen, ohne die Angabe ist der
            // Wert nicht nachvollziehbar.
            var zeitraum = "";
            if (k.basislinie_ab_datum && k.basislinie_bis_datum) {
              zeitraum = ", " + k.basislinie_ab_datum + ".." + k.basislinie_bis_datum;
            }
            zusatz = '<div class="row"><span class="muted-text">&nbsp;&nbsp;&nbsp;&nbsp;' +
              "Zufallseinstieg, gleiche Parameter (Stop " +
              (k.basislinie_stop_rel * 100).toFixed(1) + "%, CRV " +
              k.basislinie_crv.toFixed(2) + ", n=" + k.basislinie_anzahl +
              zeitraum + "): " +
              blw + " R" + chance + '</span><span class="' +
              (k.signalbeitrag_r >= 0 ? "ok" : "warn") +
              '">Signalbeitrag ' + sb + " R</span></div>";
          }
          // Mark-to-Market getrennt ausweisen (2026-08-03): seit Population A
          // bekommen noch laufende Trades einen R-Wert zum Schlusskurs. Ohne
          // die Angabe liest sich "n=111" als 111 abgeschlossene Trades,
          // obwohl 25 davon noch offene Positionen sind.
          var mtm = "";
          if (k.anzahl_mark_to_market) {
            mtm = ", davon " + k.anzahl_mark_to_market + " zum Schlusskurs bewertet";
          }
          // Dritte Zeile: Handelskosten (2026-08-04, Phase 0.2). Der EW oben
          // ist BRUTTO - er entsteht aus Zonen, also aus reiner
          // Preisbewegung. Ohne diese Zeile liest sich "EW -0,104 R" als die
          // Luecke zum Break-even, obwohl Finanzierung und Schliessungsgebuehr
          // noch fehlen. Herleitung in backward_tracking.py::kosten_in_r().
          var kostenzeile = "";
          if (k.kosten_r !== null && k.kosten_r !== undefined) {
            var netto = k.expectancy_r_netto === null || k.expectancy_r_netto === undefined
              ? "-" : (k.expectancy_r_netto >= 0 ? "+" : "") + k.expectancy_r_netto.toFixed(3);
            var annahme = k.kosten_hebel
              ? "Hebel " + k.kosten_hebel.toFixed(1) + ", "
              : "";
            if (k.kosten_median_haltedauer_tage !== null
                && k.kosten_median_haltedauer_tage !== undefined) {
              annahme += k.kosten_median_haltedauer_tage.toFixed(1) + " Tage gehalten";
            }
            // Unbelegte Saetze deutlich kennzeichnen: fuer Spot ist der Satz
            // eine Annahme, weil die Gebuehr dort im Spread steckt und aus den
            // eigenen Buchungen nicht messbar ist. Eine Zahl ohne diesen
            // Hinweis wuerde wie ein Messwert gelesen.
            var beleg = k.kosten_belegt
              ? ""
              : ' <span class="warn">[Satz nicht belegt]</span>';
            kostenzeile = '<div class="row"><span class="muted-text">' +
              "&nbsp;&nbsp;&nbsp;&nbsp;Handelskosten (" + annahme + "): -" +
              k.kosten_r.toFixed(3) + " R" + beleg +
              // Einfache Anfuehrungszeichen um dieses Fragment: der Block
              // liegt in einem NICHT-rohen dreifach gequoteten Python-String.
              // Ein rueckwaerts escaptes doppeltes Anfuehrungszeichen wuerde
              // dort von Python aufgeloest und das JavaScript zerstoeren -
              // genau so ist diese Zeile beim ersten Anlauf gebrochen.
              '</span><span class="' +
              (k.expectancy_r_netto >= 0 ? "ok" : "warn") +
              '">EW netto ' + netto + " R</span></div>";
          }
          return '<div class="row"><span>' + tier + " / " + art +
            ' <span class="muted-text">(n=' + k.anzahl_bewertet + mtm + ", " +
            k.anzahl_offen + " offen, Auflösung " + auf + ")</span></span>" +
            "<span>EW " + ew + " R (brutto), SQN " + sqn + ", PF " + pf + warn +
            "</span></div>" + kostenzeile + zusatz;
        }).join("");
      }).join("") || '<div class="row"><span class="muted-text">noch keine bewerteten Trades</span></div>';
  }
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
  if (data.selbst_gewaehltes_halten_performance) {
    document.getElementById("selbst-halten-performance-spot").innerHTML =
      renderSpotProviderPerformanceByAssetklasse(data.selbst_gewaehltes_halten_performance, {}, {});
    document.getElementById("selbst-halten-performance-hebel").innerHTML =
      renderProviderPerformance(data.selbst_gewaehltes_halten_performance.hebel || {}, null, null);
  }
  if (data.selbst_gewaehltes_halten_performance_nach_grund) {
    document.getElementById("selbst-halten-performance-nach-grund-spot").innerHTML =
      renderSpotProviderPerformanceByAssetklasse(data.selbst_gewaehltes_halten_performance_nach_grund, {}, {});
    document.getElementById("selbst-halten-performance-nach-grund-hebel").innerHTML =
      renderProviderPerformance(data.selbst_gewaehltes_halten_performance_nach_grund.hebel || {}, null, null);
  }

  if (data.zai_richtung_performance_schatten) {
    document.getElementById("zai-richtung-performance-schatten").innerHTML =
      renderZaiRichtungPerformance(data.zai_richtung_performance_schatten);
  }

  if (data.gesamt_signalqualitaet) {
    document.getElementById("gesamt-signalqualitaet-spot").innerHTML =
      renderSpotProviderPerformanceByAssetklasse(data.gesamt_signalqualitaet, {}, {});
    document.getElementById("gesamt-signalqualitaet-hebel").innerHTML =
      renderProviderPerformance(data.gesamt_signalqualitaet.hebel || {}, null, null);
  }

  if (data.api_health) {
    for (const [elementId, sourceKeys] of Object.entries(API_HEALTH_GROUPS)) {
      document.getElementById(elementId).innerHTML = renderApiHealthGroup(sourceKeys, data.api_health);
    }
  }

  if (data.richtungsverteilung) {
    document.getElementById("richtungsverteilung-card").style.display = "block";
    document.getElementById("richtungsverteilung-body").innerHTML =
      renderRichtungsverteilung(data.richtungsverteilung);
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
