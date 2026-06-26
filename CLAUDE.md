# TradingInfoTool — Projektkontext für Claude

## Projektbeschreibung
Desktop-Anwendung (Windows) die als KI-Trading-Agent fungiert. Die App analysiert Kryptowährungsmärkte, sendet Kauf-/Verkaufsignale und verwaltet ein Portfolio. Der KI-Agent agiert wie ein erfahrener Trading-Experte.

## Eigentümer
- Name: Gernot Spiessmaier
- GitHub: https://github.com/gitgeatsch/TradingInfoTool
- E-Mail: gernotspiessmaier@gmail.com

## Tech-Stack
- **Sprache:** Python
- **UI:** tkinter (Desktop-App, Windows)
- **Datenbank:** SQLite (wird automatisch beim Start erstellt und verwaltet)
- **Marktdaten:** CoinGecko API (kostenlos, kein API-Key nötig)
- **KI-Agent:** Claude API (claude-sonnet-4-6 oder neuer)
- **Charts:** matplotlib
- **Scheduler:** APScheduler (Hintergrund-Datenabfragen)

## Anforderungen

### KI-Agent
- Fungiert als autonomer Trading-Experte
- Sendet Kauf- und Verkaufsignale mit Begründung
- Basisanalyse: Technische Chart-Analyse
- Erweiterte Analyse: Makroökonomische Faktoren + historische Indikatoren
- Indikatoren: RSI, MACD, Bollinger Bands, EMA, Fear & Greed Index, BTC-Dominanz

### Daten
- Aktuelle Preise & Marktdaten (CoinGecko)
- Historische Kursdaten für Chart-Analyse
- Top Coins Übersicht
- Makroökonomische Daten (Zinsen, Fear & Greed, BTC-Dominanz)

### Portfolio-Tracking
- Eigene Bestände eintragen
- Wert und P&L verfolgen
- Signale dem Portfolio zuordnen

### UI
- Desktop-App (Windows, tkinter)
- Charts mit technischen Indikatoren
- Signal-Anzeige (Kauf/Verkauf mit Begründung)
- Portfolio-Übersicht
- Desktop-Benachrichtigungen bei neuen Signalen

## Projektstruktur (geplant)
```
TradingInfoTool/
├── main.py               # Einstiegspunkt, startet UI
├── database/
│   ├── db.py             # SQLite Verwaltung, automatische Initialisierung
│   └── models.py         # Datenmodelle
├── api/
│   ├── coingecko.py      # CoinGecko API Anbindung
│   └── macro.py          # Makroökonomische Daten
├── agent/
│   ├── analyst.py        # KI-Agent (Claude API)
│   └── signals.py        # Signal-Generierung und -Verwaltung
├── ui/
│   ├── app.py            # Haupt-UI
│   ├── charts.py         # Chart-Komponente
│   ├── portfolio.py      # Portfolio-Ansicht
│   └── signals_view.py   # Signal-Anzeige
├── scheduler/
│   └── background.py     # Hintergrund-Tasks (Daten abrufen, Analyse)
├── requirements.txt
├── .gitignore
└── CLAUDE.md
```

## Entwicklungsphasen
- [ ] Phase 1: Grundgerüst (Projektstruktur, SQLite, CoinGecko, Basis-UI)
- [ ] Phase 2: Marktdaten & Charts (Indikatoren, Visualisierung)
- [ ] Phase 3: KI-Agent (Claude API, Signalgenerierung, Makro)
- [ ] Phase 4: Portfolio & Benachrichtigungen

## Wichtige Hinweise
- CoinGecko Free Tier: max. 30 Requests/Minute, kein API-Key nötig
- Claude API Key wird in einer lokalen .env Datei gespeichert (niemals committen)
- SQLite Datenbankdatei liegt lokal, wird nicht auf GitHub gepusht
- GitHub Token: muss noch ersetzt werden (wurde im Chat sichtbar geteilt)
