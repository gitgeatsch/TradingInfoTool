# Bauplan Weg a — Fakt-Teil, Befund-Gedächtnis (A3), Gegenanwalt (A4) (28.10.2026 abends)

**Grundlage:** `Voranalyse_Dashboard_LLM_28_10.md` (§4 Aufgaben, §5 Prinzipien, §1.5a Anbieter gemessen).
**Entscheid:** Nutzer 28.10. abends: *„ok a, Binance-Historie laden ist freigegeben“*.
**Stand:** Vorlage zur Abstimmung. **Nichts am Betrieb geändert.** Gebaut wird erst nach dem Ja zu §8.

---

## 1. Was am Ende da ist

Eine **Asset-Karte** je Asset auf der Statusseite, jeweils für jeden **Bestand** und jedes **REGEL0-Signal des Tages**. Sie besteht aus drei Schichten, und jede Schicht ist gekennzeichnet:

| Schicht | Inhalt | Kennzeichen | Herkunft |
|---|---|---|---|
| **Fakten** | Kurs, Bestand (frei + gestakt), Einstand/Ergebnis zum Schlusskurs, REGEL0 heute, Hebelposition und Abstand, Binance-Ankündigungen (Delisting, Monitoring), Upbit, Verwässerung, Season-Ampel, Makro K1–K9, Termin | **Fakt** mit Stand und Alter | Code, nur lesend, aus den vorhandenen Quellen |
| **Befund-Gedächtnis (A3)** | Welche **gemessenen** Befunde gelten für diese Lage, mit welcher Zahl, und liegt die Lage in ihrem Geltungsbereich | **gemessen** (Befund-ID) | LLM wählt aus der Befund-Karte aus, der Code prüft jede Angabe |
| **Gegenanwalt (A4)** | Höchstens drei Fakten oder Befunde, die **gegen** die Handlung sprechen, oder ausdrücklich „keiner“ | **ungeprüft**, jeder Grund mit Beleg | LLM, der Code prüft jeden Beleg |

⚠️ **Kein Urteilswort, keine Wahrscheinlichkeit des LLM** (P2). Die Karte sagt nicht „kaufen“ oder „nicht kaufen“. Sie sagt, was gilt und was dagegen spricht.

---

## 2. Warum A3 eine eigene Befund-Karte braucht

Das Register hat **1.097 geltende Befunde mit 1,3 Mio. Zeichen** (gezählt am 28.10.). Das passt in keinen Aufruf, und das meiste davon betrifft Messwerkzeuge, nicht den Betrieb.

**Befund-Karte** = eine **Auswahl** aus dem Register, und zwar der Befunde, die eine Handlung im Betrieb betreffen: REGEL0-Einstieg, Hebel, Spot-Einstieg und Spot-Führung. Erwartet sind 30–60 Einträge. **Es entstehen keine neuen Befunde.** Jeder Eintrag verweist auf eine bestehende Kennung und trägt zusätzlich:

| Feld | Beispiel | Wozu |
|---|---|---|
| `kennung` | `E-165-h1c` | Verweis ins Register |
| `strang` | `regel0` / `hebel` / `spot_einstieg` / `spot_fuehrung` | Vorauswahl je Handlung |
| `zahl` | `+1 Pp, an der Nachweisgrenze` | die Zahl, die genannt werden darf |
| `gilt_wenn` | maschinenlesbar, wo möglich (`kern == ja`, `jahr >= 2025`), sonst Text | Geltungsbereich |
| `nicht_wenn` | z. B. „nur Kern“, „nur 2025–26“ | Grenzen ausdrücklich |

Die Befund-Karte steht in `bestand.py` und wird von dort ins Register erzeugt, wie alle Register. Ein Prüfpaket stellt sicher, dass **jede Kennung existiert und gilt** und dass **jede Zahl im Befundtext vorkommt**. Wird ein Befund abgelöst, fällt die Prüfung, und die Karte wird nachgezogen. So kann sie nicht still veralten.

---

## 3. Arbeitsteilung Code — LLM (ehrlich)

> **Was deterministisch geht, macht der Code. Das LLM arbeitet nur dort, wo Text zu lesen oder abzuwägen ist.**

| Aufgabe | Code | LLM |
|---|---|---|
| Fakten sammeln, Alter prüfen | ✔ | – |
| Befund mit **maschinenlesbarem** Geltungsbereich zuordnen | ✔ rechnet selbst | wählt **auch**, und das Ergebnis wird **verglichen** (Übereinstimmung = Prüfmaß) |
| Befund mit Geltungsbereich **als Text** („nur in Epoche …“, „nur bei geballten Signalen“) | – | ✔ |
| Zwei Befunde, die sich für diese Lage widersprechen oder verstärken | – | ✔ |
| Gegengründe aus Fakten **und** Befunden zusammensetzen (A4) | – | ✔ |
| Jede LLM-Angabe prüfen (ID, Zahl, Fakt-Schlüssel, Wert) | ✔ | – |

Weicht das LLM bei einem maschinenlesbaren Befund vom Code ab, **gilt der Code**. Die Abweichung wird protokolliert (LLM ist Prüfung, nicht Entscheider). Nicht belegte Angaben werden **nicht angezeigt**, sondern nur gezählt.

---

## 4. Modell und Kontingent (aus §1.5a, gemessen)

| | |
|---|---|
| Modell | **Gemini, eigener Modelltopf, nicht 3.5-flash-lite** (das ist der Topf des Prüfblocks, Deckel 150) |
| Kandidat | `gemini-3.1-flash-lite`. Der Topf dürfte frei sein, seit die alte Spot-Kette stillgelegt ist (E-164). **Nachweis vor dem Einschalten**: NB-Zähler `gemini:3.1` je Tag ≈ 0 (Kontrolle K-AL-0) |
| Aufrufe | **ein** Aufruf je Asset-Karte (A3 und A4 zusammen, ein JSON-Schema). ~40 Bestände einmal täglich + REGEL0-Signale (meist < 10/Tag) → **≤ 60/Tag** |
| Deckel | 120/Tag in der eigenen Konfiguration, gezählt in der Ablage (wie beim Prüfblock), Pazifik-Tag |
| Ausfall | 3 Fehler in Folge → der Lauf fragt nicht mehr; die Karte zeigt dann die Fakten **ohne** A3/A4, mit Vermerk |
| Groq/OpenRouter | **nicht nötig** für a, deshalb auch kein neuer NB-Schlüssel |

---

## 5. Bauschritte

| # | Schritt | Gerät | Ändert Betrieb? |
|---|---|---|---|
| **B1** | **Befund-Karte** in `bestand.py`, Register-Blatt, Prüfpaket `Befundkarte` | Desktop | nein |
| **B2** | **Fakt-Sammler** `agent/asset_lage.py`: je Asset alle Fakten mit Quelle, Stand, Alter; nur lesend (`mode=ro`), nie `tradinginfotool.db` beschreiben | Desktop, dann NB | nein (liest nur) |
| **B3** | **LLM-Rolle** `agent/asset_lage_llm.py`: Eingabe = Fakten + Befund-Karte des Strangs, Ausgabe JSON-Schema, **Prüfer** (§6), Protokoll in **eigener Datei** `data/asset_lage.db` (V6) | Desktop | nein |
| **B4** | **Job** `asset_lage`: täglich 07:45 (nach `externe_reihen` 06:35 und `season_ampel` 07:30) und nach jedem REGEL0-Lauf mit Signal | NB | ja: neuer Job |
| **B5** | **Statusseite**: Karte „Asset-Lage“; dazu die Mail nach §8 | NB | ja |
| **B6** | Prüfungen nach §6, dann **ein** NB-Bündel (ein Pull, eine Diagnose) | beide | – |

Aufwand: B1–B3 etwa 1–2 Tage, B4–B6 etwa 1 Tag.

---

## 6. Prüfen und Gegenprüfen

| Prüfung | Soll | Wie |
|---|---|---|
| **Faktentreue A3** | **100 %** angezeigter Angaben belegt | Prüfer: ID in der Karte, Zahl gleich, genannter Fakt-Schlüssel vorhanden und Wert gleich |
| **Selbsttest Prüfer** | 100 % erkannt | gepflanzte Fehler (falsche ID, falsche Zahl, erfundener Fakt, falscher Wert), je Art ≥ 1.000 Fälle |
| **Übereinstimmung A3 mit dem Code** | ausgewiesen, kein Soll vorab | bei maschinenlesbarem Geltungsbereich: Anteil gleicher Zuordnung |
| **A4 reflexhaft?** | Anteil „keiner“ und Anteil Gegengründe je Karte ausgewiesen | gezählt im Protokoll; Vergleich mit N5 (Pessimismus 43–52 %) |
| **Prüfstand** | Mail und Karte mit echter Konfiguration | gegen die **Kopie** im Austauschordner, Wegwerfpfad, Seiteneffekt nachgewiesen = 0 |
| **NB-Kontrollen** | K-AL-0 (3.1-Topf frei), K-AL-1 (Job läuft, Karte gefüllt, Deckel eingehalten) | `nb_kontrollen.yaml` |

⚠️ **Was diese Prüfungen NICHT zeigen:** dass A4 Verluste vermeidet. Das wäre eine Wertmessung. Möglich ist sie als Rückspiel auf REGEL0-Signale 2025–26 mit **gpt-oss-120b** (sauber), aber nur mit Fakten, die einen Zeitpunkt des Bekanntwerdens haben (Ankündigungen, Verwässerung, Termine; Makro hat keinen, §1.3). Das ist ein **eigener Messplan nach dem Bau**, kein Teil von a.

---

## 7. Parallel: A1 mit der Binance-Historie (V1)

- **Download läuft** seit 28.10. abends: `Basisinfos/Rechenkern_02_10/a1_lade_binance.py` → `data/_a1/binance_ankuendigungen_alle.db`. Es sind 6 Kataloge ab 2023 (Listing, News, Delisting, Wartung, Airdrop mit Text; Aktionen nur mit Titel). Erwartet sind ~9.000 Meldungen, fortsetzbar, gedrosselt. Die E-1-Ablage bleibt unberührt.
- **Danach:** eigene Voranalyse A1 mit Regeln zuerst, LLM nur für den Rest. Begründung: Groq gpt-oss-120b schafft ~600 Meldungen/Tag (200.000 Token, §1.5a). Dazu die Prüfstichprobe (~200) und die Frage, welche Ereignisart überhaupt häufig genug ist, um sie zu messen.

---

## 8. Zur Abstimmung — eine Frage

**Was passiert in der REGEL0-Signalmail?** Dort steht heute der Trader-Prüfblock, gemessen *„trennt nicht“*.

| | Weg | Folge | Einschätzung |
|---|---|---|---|
| **1** | **A3/A4 ersetzen den Trader-Block in der Mail.** Der Trader läuft im Schatten weiter (berechnet und gespeichert, nicht gemailt) | Die Mail zeigt, was gemessen gilt und was dagegen spricht. Der Trader bleibt als Vergleichsarm erhalten, es geht keine Grundfunktion verloren | **Empfehlung.** Ein gemessen nicht trennender Block in jeder Mail ist Rauschen (*jede Mail eine Handlung*). In die Mail gehen nur maschinell belegte Angaben |
| 2 | A3/A4 **zusätzlich** zum Trader-Block | längere Mail, zwei LLM-Blöcke | widerspricht der Mailregel; der Trader bleibt Rauschen |
| 3 | Mail **unverändert**, A3/A4 zwei Wochen nur auf der Statusseite, dann neu entscheiden | vorsichtiger, aber die Intelligenz ist dort, wo du sie unterwegs nicht siehst | nur sinnvoll, wenn du der Faktentreue erst im Protokoll trauen willst |

Bestände ohne Handlung bekommen **keine Mail**, nur die Karte (*jede Mail eine Handlung*). Gilt für alle drei Wege.
