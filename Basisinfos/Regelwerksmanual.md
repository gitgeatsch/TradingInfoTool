# TradingInfoTool — Regelwerksmanual (für den Nutzer)

**Zweck dieses Dokuments:** Der Agent folgt einem festen, nummerierten Regelwerk (nicht
freiem Ermessen). Dieses Manual erklärt jede aktive Regel in normaler Sprache, mit dem
aktuell eingestellten Wert und der Begründung dahinter. Es ist die gemeinsame Grundlage
für künftige Entscheidungen: wenn die KI aufgrund vergangener Signal-Ergebnisse eine
Regel-Anpassung vorschlägt (z. B. "RM-1 von 2% auf 1,5% senken, weil..."), kannst du
mit diesem Dokument nachvollziehen, was sich dadurch tatsächlich ändert — und bewusst
zustimmen oder ablehnen, statt blind zu vertrauen.

**Wie du dieses Dokument liest:**
- **Status "AKTIV"** = die Regel wird im Code tatsächlich durchgesetzt (nicht nur als
  Idee dokumentiert).
- **Status "OFFEN"** = die Regel ist geplant/entschieden, aber noch nicht im Code
  umgesetzt — gilt aktuell also NICHT.
- **Status "DEAKTIVIERT"** = bewusst ausgeschaltet (z. B. Hebel-Handel).
- Werte in **Fettschrift** sind die aktuell in `Basisinfos/config.yaml` eingestellten
  Zahlen — genau diese Zahlen wären Ziel einer künftigen KI-gestützten Anpassung.
- Technische Quelle: `Basisinfos/Spezifikation.md` (vollständige, entwicklerorientierte
  Fassung inkl. Entscheidungshistorie). Dieses Manual ist die destillierte,
  entscheidungsorientierte Kurzform davon.

---

## 1. Die vier Grundsätze (Z-1 bis Z-4)

Diese vier stehen über allen anderen Regeln — jede andere Regel muss sich daran messen.

| ID | Grundsatz | Bedeutung |
|----|-----------|-----------|
| Z-1 | Kapitalerhalt vor Gewinn | Im Zweifel gewinnt immer "Verlust vermeiden" gegen "mehr Gewinn machen". |
| Z-2 | Mindest-Chance-Risiko-Verhältnis | Jedes KAUFEN-Signal braucht ein Verhältnis von **mindestens 2,0** — der mögliche Gewinn bis zum Take-Profit muss mindestens doppelt so groß sein wie der mögliche Verlust bis zum Stop-Loss. Konservativ gerechnet (schlechtester Fall der Kurszone). **AKTIV**, hart erzwungen — ein Vorschlag, der das nicht schafft, wird automatisch auf HALTEN korrigiert. |
| Z-3 | Drawdown-Notbremse | Bei zu großem Gesamt-Portfolio-Verlust automatisch in den Kapitalschutz-Modus wechseln. **OFFEN** — fehlt noch eine Portfolio-Wert-Historie als Grundlage. |
| Z-4 | Nachvollziehbarkeit | Jede Empfehlung braucht Begründung + Datenbasis + Konfidenz-Angabe. **AKTIV** (Top-5-Gründe, Kurszonen, Halte-Kriterium). |

---

## 2. Risikomanagement — wie viel wird pro Trade riskiert (RM-1 bis RM-11)

| ID | Regel | Aktueller Wert | Status |
|----|-------|----------------|--------|
| RM-1 | Risiko pro Trade — wie viel des Portfolios darf bis zum Stop-Loss maximal verloren gehen | **2 %** | AKTIV, seit heute (2026-07-10) hart durchgesetzt: schlägt die KI eine größere Position vor, wird sie automatisch auf diesen Wert gekürzt |
| RM-2 | Max. Allokation pro Einzelwert | **25 %** (taktische Assets) / **35 %** (Kernwerte BTC/ETH) | AKTIV, siehe RM-1 (gleicher Clamp-Mechanismus) |
| RM-3 | Max. Allokation pro Assetklasse | Krypto **100 %**, Aktien/ETF/Rohstoffe je **0 %** | Konfiguriert, aber noch nicht aktiv genutzt (nur Krypto im Einsatz) |
| RM-4 | Cash-Reserve-Minimum | **Größerer Wert aus 10 %** des Portfolios **oder 2000 €** Festbetrag | AKTIV, seit heute (2026-07-10) Hybrid-Formel — Unterschreitung blockiert weitere Käufe |
| RM-5 | Pflicht-Stop-Loss | jede Position braucht einen | AKTIV, unantastbar (kein Override erlaubt) |
| RM-6 | Trailing-Stop | erlaubt | Als Option vorhanden, keine automatische Durchsetzung |
| RM-7 | Drawdown-Notbremse | — | **OFFEN**, siehe Z-3 |
| RM-8/RM-9 | Risiko-Score je Asset (aus Volatilität, Liquidität, BTC-Korrelation, Projektreife) → höheres Risiko = kleinere erlaubte Position | — | **OFFEN**, noch nicht gebaut |
| RM-10/RM-11 | Hebel: nur Long, max. **3x**, Liquidationspreis muss ausgewiesen werden | konfiguriert | **DEAKTIVIERT** (Strategie S-6 aus) — eigenes, noch zu führendes Thema |

**Unantastbar (RG-6):** Weder Nutzer noch KI dürfen RM-1, RM-5 oder Z-3 per Override
abschalten — das sind die harten Leitplanken, die auch eine künftige KI-gestützte
Anpassung nicht in Frage stellen darf, ohne dass du das bewusst und explizit änderst.

**RM-4 zählt jetzt auch echtes Fiat-Geld (2026-07-10).** Bis dahin kannte die App nur
Stablecoin-Bestände (EURCV) als "Cash" — echtes EUR-Guthaben auf der Börse (z. B.
Bitpanda) war ihr komplett unbekannt, weder als Reserve noch im Portfolio-Gesamtwert.
Jetzt gibt es dafür ein manuelles Eingabefeld im Portfolio-Tab ("Fiat-Guthaben auf
Börse"), das du gelegentlich aktuell hältst — kein Börsen-API-Zugriff nötig (P-7 bleibt
gewahrt). **Korrektur (2026-07-10):** Bitpanda führt auch Aktien/ETF/Rohstoffe im
selben Account — der Live-Abgleich deckt seitdem alle Assetklassen ab, nicht nur
Krypto (siehe unten). Zusätzlich wurde die Formel von reinem Prozentsatz auf
**Hybrid** umgestellt:
erforderlich ist das *Größere* aus 10 % des Portfolios und einem festen Mindestbetrag
(aktuell 2000 €, `cash_reserve_min_fixed_eur` in `config.yaml`) — reiner Prozentsatz
hätte bei kleinen Portfolios einen zu dünnen Puffer erlaubt, ein reiner Festbetrag hätte
bei wachsendem Portfolio nicht mitskaliert.

**Optionaler Live-Abgleich mit Bitpanda (2026-07-10, ERGÄNZT + KORRIGIERT).** Wer
bereits einen Bitpanda-API-Key besitzt (`BITPANDA_API_KEY` in `.env`), kann über
"Datei → Bestände von Bitpanda abgleichen" **alle** Bestände (Krypto **und**
Aktien/ETF/Rohstoffe, da Bitpanda diese im selben Account führt) UND das EUR-Fiat-
Guthaben automatisch von der Börse abrufen (rein lesend — laut Bitpanda-Doku besteht
über API-Keys grundsätzlich keine Order-/Auszahlungsfähigkeit, unabhängig vom
gewählten Scope). Das manuelle Eingabefeld und der bestehende Excel-Import/Export
bleiben **vollständig als Backup** erhalten (bewusst hybrid, da Bitpanda öfter
Ausfälle hat) — der Sync ist rein manuell ausgelöst, kein Hintergrund-Job. Nach jedem
Sync wird automatisch auch `Assets_export.xlsx` aktualisiert (beide Tabs), ohne die
handgepflegte Original-`Assets.xlsx` anzutasten. Erkennt der Abgleich, dass sich ein
Bestand passend zu einem noch offenen Signal geändert hat, wird das als Vorschlag
angezeigt (nie automatisch bestätigt).

**Wichtige Einschränkung, live entdeckt (2026-07-10): gestakte Bestände sind über
diese API nicht sichtbar.** Drei Endpunkte live geprüft (`/wallets`, `/asset-wallets`,
`/wallets/transactions`) — keiner liefert einen Staking-Wert; gestakte Anteile
erscheinen fälschlich als 0 oder reduziert. **Deshalb gilt seit demselben Tag:
Zuwächse werden weiterhin automatisch übernommen, Rückgänge NIE automatisch** —
sie erscheinen als eigener Bestätigungsdialog, den du explizit pro Symbol bestätigen
musst. So bleibt der Sync auch bei dieser API-Lücke sicher, ohne echte Bestände
versehentlich zu überschreiben.

---

## 3. Regime-Steuerung — wie sich die Regeln je nach Marktlage anpassen (RG-1 bis RG-11)

Grundidee: Die *Struktur* der Bewertung bleibt gleich, aber vier Stellschrauben ändern
sich automatisch je nach Marktphase (**Krise-extrem → Bär → Seitwärts → Bulle →
Euphorie-extrem**):

| Regime | Small-Cap-Budget | Gewicht Technik | Gewicht Fundamental | Gewicht Momentum | Gewicht Makro | Mindest-Konfidenz |
|--------|-------------------|-----------------|----------------------|--------------------|-----------------|---------------------|
| Krise-extrem | 0 % | 0,15 | 0,45 | 0,15 | 0,25 | **85 %** |
| Bär | 4 % | 0,24 | 0,40 | 0,16 | 0,20 | **75 %** |
| Seitwärts | 8 % | 0,34 | 0,34 | 0,17 | 0,15 | **65 %** |
| Bulle | 12 % | 0,43 | 0,25 | 0,17 | 0,15 | **60 %** |
| Euphorie-extrem | 15 % | 0,38 | 0,15 | 0,22 | 0,25 | **60 %** (+ verschärfte Gewinnsicherung) |

Alle Werte sind laut Spezifikation **vorläufig** — genau das macht sie zu einem
naheliegenden ersten Ziel für datenbasierte Anpassungsvorschläge (z. B. "Mindest-
Konfidenz im Bär war mit 75% zu konservativ/zu locker, weil...").

**Override-Reihenfolge (RG-9), von stark nach schwach:** harte Limits (RM-1/RM-5/Z-3) >
manueller Override (aber nur "offensiver" mit deiner Bestätigung) > KI-Override
(defensiver werden darf die KI jederzeit autonom, offensiver nur mit Nachweis) >
regelbasierte Basis. Kurz: **vorsichtiger werden geht immer sofort, mutiger werden
braucht immer eine Bremse** (RG-5) — dieselbe Asymmetrie sollte auch für künftige
KI-Regelvorschläge gelten.

---

## 4. Antizyklische Kauf-Disziplin (AZ-1 bis AZ-8)

Der eigentliche Mehrwert des Agenten: er soll den typischen Fehler von Privatanlegern
vermeiden (im Absturz verkaufen, im Tief nicht kaufen).

| ID | Regel | Kurz |
|----|-------|------|
| AZ-1 | Flush vs. Zusammenbruch unterscheiden | schneller, nachrichtenloser Kurssturz (Flush) ist meist eine Kaufgelegenheit — ein Zusammenbruch mit echten schlechten Nachrichten nicht |
| AZ-2 | Bestätigungs-Gate | vor dem Kauf erst Stabilisierung abwarten ("die Bestätigung kaufen, nicht das fallende Messer") |
| AZ-3 | Abgestuft | kleine Sondierungs-Tranche nur bei BTC/ETH vor voller Bestätigung, größere Positionen erst danach |
| AZ-4 | Gestaffelt, nie all-in | in Tranchen kaufen, damit ein tieferer Absturz zur Chance statt zum Ruin wird |
| AZ-5 | Fundamental-Gate | nur nachkaufen, wenn die Substanz des Assets intakt ist |
| AZ-6 | Ausstieg bei gescheiterter These | läuft der Kauf zu lange gegen die Erwartung, wird das Nachkaufen gestoppt statt stur weitergemacht |
| AZ-7 | Hebel nur nach Bestätigung | im Extrem-Krise-Regime komplett aus |
| AZ-8 | Ehrliche Grenzen | strukturell vs. zyklisch lässt sich in Echtzeit nicht sicher unterscheiden — Schutz kommt aus den anderen AZ-Regeln, nicht aus Vorhersage |

**Aktueller Umsetzungsstand:** nur eine vereinfachte Heuristik (Funding-Rate-Extremwert
+ Kurs-Rückgangsgeschwindigkeit + Open-Interest/Long-Short-Ratio als Kontext-Hinweis an
die KI) — nicht die volle AZ-1-Klassifikation, da eine unabhängige Nachrichtenquelle
fehlt. Liefert Kontext, trifft aber keinen eigenen Veto-Entscheid.

---

## 5. Entscheidungs-Reihenfolge bei jedem Signal (R-5.0 bis R-5.11)

So läuft jede einzelne Bewertung ab, in genau dieser Reihenfolge:

1. **R-5.0 Datenqualitäts-Gate** — sind Preis/Historie aktuell genug? Wenn nein: Abbruch, "HALTEN — Datenlage unsicher".
2. **R-5.1 Marktregime bestimmen** — Bulle/Bär/Seitwärts über BTC-Trend, BTC-Dominanz, Fear & Greed.
3. **R-5.2 Makro-Kontext** — Zinsen, globale Liquidität, Zyklus-Risiko.
4. **R-5.3 Technische Analyse** — Trend, Indikatoren, Fibonacci, Support/Resistance.
5. **R-5.4 Sentiment** — niedrig gewichtet, aktuell noch nicht angebunden.
6. **R-5.5 Risikoprüfung als Veto-Stufe** — scheitert hier etwas (RM-1/2/4/5, Bitpanda-Listung), gibt es keinen Kauf, egal wie gut alles andere aussieht.
7. **R-5.6 Signal + Konfidenz** — vollständige, strukturierte Empfehlung.
8. **R-5.7 Haltedauer-Empfehlung** mit Zielpreis/-datum/Bedingung.
9. **R-5.8 Forecast als Szenario** (Bull/Base/Bear mit Wahrscheinlichkeiten statt einer einzelnen Zahl).
10. **R-5.9 Steuerliche Optimierung** — Tauschen statt Verkaufen wird bevorzugt, wo steuerlich gleichwertig (Krypto-zu-Krypto ist in Österreich bis zur Auszahlung in Fiat steuerneutral).
11. **R-5.10 Regime-Profil anwenden** — die Tabelle aus Abschnitt 3 fließt hier ein.
12. **R-5.11 Antizyklische Disziplin** — siehe Abschnitt 4.

**Wichtig:** Schritt 6 (Risikoprüfung) ist eine echte Veto-Stufe — sie kann jeden noch
so überzeugenden Kauf-Vorschlag stoppen. Das ist bewusst so gebaut, damit die KI (die
bei Schritt 7 die eigentliche Formulierung übernimmt) niemals das letzte Wort über
Risiko-Grenzen hat.

---

## 6. Datenabfragen — was wann wie automatisch vs. manuell passiert

Zwei getrennte Wege: ein **Hintergrund-Scheduler** (läuft automatisch, solange die
App offen ist) und **manuelle GUI-Aktionen** (nur bei Klick). Beide schreiben in
dieselbe Datenbank — der Unterschied ist nur, ob du selbst klicken musst.

### Automatisch (Scheduler, `scheduler/background.py::build_scheduler()`)

| Job | Takt | Was | Quelle |
|-----|------|-----|--------|
| `refresh_prices` | alle 15 Min | Live-Preise für alle Krypto-Assets | CoinGecko |
| `refresh_securities_prices` | alle 15 Min | Live-Preise für Aktien/ETF/Rohstoffe | yfinance |
| `refresh_history` | alle 24 Std. | Tages-Historie (für Indikatoren wie EMA-200) | CoinGecko |
| `refresh_ohlc` | alle 24 Std. | Echtes OHLC (für ATR/Swing-Highs-Lows) | Kraken |
| `marktscan` | 2× täglich, fix 04:00 + 16:00 Uhr | Kompletter Marktscan-Lauf (Stufe A-D, Kap. 13) | CoinGecko + Kraken, optional Groq |
| `backward_tracking` | 1× täglich, fix 06:00 Uhr | Prüft vergangene KAUFEN/NACHKAUFEN-Signale gegen die Kurshistorie — Take-Profit oder Stop-Loss erreicht? | keine (nur bereits vorhandene DB-Daten) |

**Der Marktscan-Job nutzt Groq nur, wenn du das explizit erlaubst:** Standardmäßig
(`config.yaml marktscan.groq_automatisch_kaufkandidaten: false`) generiert der
automatische Lauf nur die deterministischen Kennzahlen (Stufe A-C), aber keine
KI-Begründungstexte — die holst du dir manuell im Marktscan-Tab. Setzt du das Flag
auf `true`, ruft der Scheduler Groq automatisch für jeden neu erkannten
"Kaufkandidat" auf (Stufe D), um zusätzlich eine kurze Begründung zu erzeugen.

**15-Minuten-Takt bewusst gewählt** (nicht kürzer): CoinGecko Free-Tier hat ein
Monats-Kontingent — ein 5-Minuten-Takt hätte zusammen mit dem täglichen
Historie-Refresh das Limit überschritten (siehe Spezifikation Kap. 16).

**Backward-Tracking (2026-07-10, ERGÄNZT — Selbstverifikations-Vision Schritt 2).**
Jeden Morgen um 6 Uhr prüft die App automatisch, ob vergangene KAUFEN/NACHKAUFEN-
Signale ihre Take-Profit- oder Stop-Loss-Zone erreicht haben — anhand bereits
vorhandener Kursdaten, kein zusätzlicher Netzwerk-Aufruf. Das Ergebnis siehst du
über den neuen Button "Signal-Historie" im Signale-Tab. Das ist die Datengrundlage
für Schritt 3 der Vision (KI-gestützte Regel-Anpassungsvorschläge) — ohne
gespeicherte Ist-Ergebnisse kann später nichts verglichen werden.

### Manuell (GUI-Aktionen, nur bei Klick)

| Aktion | Wo | Was |
|--------|-----|-----|
| "Jetzt aktualisieren" | Toolbar (oben) | Sofortiger Krypto-Preis-Refresh (CoinGecko) + Bitpanda-Listing-Check |
| "Signal berechnen" | Signale-Tab | Die **gesamte** Agent-Pipeline (R-5.0 bis R-5.11, Abschnitt 5) für **ein** Asset — inkl. echtem Groq-Aufruf. Bewusst **nie automatisch/geplant** — jeder Signal-Lauf kostet einen KI-Aufruf und soll bewusst ausgelöst werden. |
| "Signal-Historie" | Signale-Tab | Zeigt alle bisherigen Signale des ausgewählten Assets inkl. Backward-Tracking-Ergebnis (Take-Profit/Stop-Loss/Offen/Abgelaufen) — reine Anzeige, kein externer Aufruf. |
| "Jetzt scannen" | Marktscan-Tab | Derselbe Marktscan-Lauf wie der 04:00/16:00-Scheduler-Job, nur sofort statt zur festen Uhrzeit |
| "Bestände von Bitpanda abgleichen" | Datei-Menü | Live-Abgleich aller Bestände (Krypto + Aktien/ETF/Rohstoffe) + EUR-Cash direkt von Bitpanda (siehe RM-4-Abschnitt oben) — **nie automatisch**, da ein echter, authentifizierter API-Key beteiligt ist |
| "Einstandspreise von Bitpanda berechnen" | Datei-Menü | Echter Anschaffungspreis je Asset aus der Bitpanda-Trade-Historie (siehe Abschnitt 9) — **eigener, unabhängiger Menüpunkt**, nie automatisch (Erstlauf kann ~40s dauern, läuft threaded im Hintergrund) |
| "Bestände neu importieren" / "aus Datei importieren…" / "exportieren…" | Datei-Menü | Excel-Import/-Export (`Basisinfos/Assets.xlsx`) — rein lokal, kein externer Netzwerk-Aufruf |
| Fiat-Cash-Reserve "Speichern" | Portfolio-Tab | Manuelle Eingabe, kein externer Aufruf |

**Grundprinzip:** alles, was **Geld kostet oder einen persönlichen API-Key
voraussetzt** (Groq pro Einzelsignal, Bitpanda-Sync), ist bewusst manuell — alles,
was **kostenlose öffentliche Marktdaten** sind (Preise, Historie), läuft automatisch
im Hintergrund. Der Marktscan ist der einzige Fall, der teilweise automatisch UND
optional KI-gestützt läuft (siehe oben).

---

## 7. Backward-Tracking im Detail — wie Signal-Ergebnisse geprüft werden

**Zweck:** Schritt 2 der Selbstverifikations-Vision (Schritt 1 war dieses Manual
selbst). Der Agent soll über Zeit lernen können, ob seine eigenen KAUFEN/
NACHKAUFEN-Empfehlungen tatsächlich zutrafen — ohne diese Ist-Ergebnisse kann
später (Schritt 3) keine KI-gestützte Regel-Anpassung sinnvoll vorgeschlagen
werden. Rein beobachtend: der tägliche Job liest nur bereits vorhandene
Kursdaten und trägt ein Ergebnis nach — er ändert nie eine Empfehlung, ein Veto
oder eine Position (P-7 Advisory-only).

**Was wird geprüft:** Ausschließlich **KAUFEN**- und **NACHKAUFEN**-Signale mit
gültiger Entry-/Stop-Loss-/Take-Profit-Zone. HALTEN, VERKAUFEN und TAUSCHEN
haben keine vergleichbare Take-Profit/Stop-Loss-Logik und werden sofort als
„Nicht anwendbar" markiert, ohne dass jemals Kursdaten dafür geprüft werden.

**Ablauf, Schritt für Schritt** (`agent/krypto/backward_tracking.py`):

1. Jeden Morgen um 6 Uhr (Scheduler-Job `backward_tracking`, siehe Abschnitt 6)
   werden alle Signale gesucht, deren Ergebnis noch **offen** ist (also weder
   Take-Profit noch Stop-Loss noch „abgelaufen" noch „nicht anwendbar").
2. Für jedes Signal wird die Kurshistorie **ab dem Erstellungsdatum** des
   Signals geholt — bevorzugt aus `price_history_ohlc` (echtes Tages-High/Low,
   nur für Krypto-Assets mit Kraken-Listing verfügbar), sonst als Rückfallebene
   aus `price_history` (nur der tägliche Schlusskurs). Welche Quelle verwendet
   wurde, wird transparent im Feld **Datenquelle** festgehalten (`real` vs.
   `proxy`) — ein Ergebnis auf Basis von echtem Intraday-High/Low ist
   verlässlicher als eines, das nur auf dem Tagesschlusskurs beruht.
3. Die Tage werden **chronologisch, ältester zuerst**, durchgegangen. Für jeden
   Tag wird geprüft: Hat der Tages-Höchstwert (bzw. bei „proxy" der
   Schlusskurs) die Take-Profit-Zone erreicht? Hat der Tages-Tiefstwert (bzw.
   Schlusskurs) die Stop-Loss-Zone erreicht?
4. **Konservative Regel bei Gleichzeitigkeit:** Trifft ein einzelner Tag
   sowohl die Stop-Loss- als auch die Take-Profit-Zone (nur bei echten
   OHLC-Daten überhaupt feststellbar), gewinnt **immer Stop-Loss** — dieselbe
   Logik wie Z-1 (Kapitalerhalt vor Gewinn) und dieselbe Vorsicht wie bei der
   CRV-Berechnung (Abschnitt 2): ohne Kenntnis der tatsächlichen
   Innertages-Reihenfolge wird nie zugunsten des optimistischeren Ausgangs
   angenommen.
5. Wird an keinem Tag eine Zone erreicht, bleibt das Signal **offen** — außer
   es ist bereits älter als `backward_tracking.abgelaufen_nach_tagen`
   (`config.yaml`, aktuell **90 Tage**, vorläufiger Wert) — dann wird es als
   **„Abgelaufen (unentschieden)"** markiert und nicht weiter täglich neu
   geprüft.

**Die fünf neuen Ergebnis-Felder je Signal:**

| Feld | Bedeutung |
|------|-----------|
| **Ergebnis-Status** | Einer von: Offen · Take-Profit erreicht · Stop-Loss erreicht · Abgelaufen (unentschieden) · Nicht anwendbar |
| **Zuletzt geprüft am** | Zeitstempel des letzten Prüflaufs |
| **Entschieden am** | Datum, an dem die Zone erreicht wurde (leer, solange offen) |
| **Realisiertes CRV** | Nur bei entschiedenem Ergebnis: `(erzielter Kurs − Entry-Mitte) / (Entry-Mitte − Stop-Loss-Zone-Untergrenze)` — dieselbe konservative Formel wie die ursprünglich vorhergesagte CRV (Abschnitt 2, Z-2), nur mit dem tatsächlich erreichten Kurs statt der Zonen-Grenze. Positiv bei Take-Profit, negativ bei Stop-Loss. |
| **Datenquelle** | `real` (echtes OHLC) oder `proxy` (nur Tagesschlusskurs) |

**Wo du das siehst:** neuer Button **"Signal-Historie"** im Signale-Tab, direkt
neben "Signal berechnen" — zeigt alle bisherigen Signale des ausgewählten
Assets mit Datum, Aktion, Konfidenz und Ergebnis-Status, farblich markiert
(grün = Take-Profit, rot = Stop-Loss, neutral = offen, grau = abgelaufen).
Macht eine bereits vorhandene, aber bis dahin nie genutzte Datenbank-Abfrage
erstmals sichtbar.

**Aktueller Stand (2026-07-10):** Bisher gibt es **kein einziges echtes
KAUFEN/NACHKAUFEN-Signal** in der Datenbank — alle bisherigen Signale sind
HALTEN. Backward-Tracking ist also einsatzbereit, aber noch ohne echte
Auswertungsgrundlage. Schritt 3 der Vision (KI-gestützte Regel-
Anpassungsvorschläge) braucht erst eine gewisse Anzahl echter, aufgelöster
Kauf-Signale, bevor er sinnvoll ansetzen kann.

---

## 8. Lokale KI-Ebene (P-8) — Architektur vorbereitet, noch nicht aktiv

**Hintergrund:** P-8 verlangt seit Projektbeginn, dass der Agent perspektivisch
auch **ohne** externen KI-Zugang funktionieren können soll. Groq ist bereits
vollständig optional (kein `GROQ_API_KEY` → Signale-Tab bleibt nutzbar, nur die
Berechnung ist deaktiviert) — aber es gab bisher **keine echte lokale
Alternative**, nur eine nie umgesetzte Absichtserklärung. Das ist jetzt
richtiggestellt: entweder etwas ist gebaut, oder es steht offen als geplant da.

**Was heute (2026-07-10) tatsächlich gemacht wurde — ein Architektur-Seam, kein
lauffähiges lokales Modell:**
- Neuer Konfig-Schalter `config.yaml agent.ai_provider` (`groq` oder `lokal`).
- Neue Datei `api/local_model.py` mit `LocalModelClient` — hat exakt dieselbe
  Schnittstelle wie der bestehende `GroqClient` (`.chat(messages, model,
  temperature, response_format)`). Die eigentliche Signal-Pipeline
  (`agent/krypto/analyst.py::call_groq_for_signal()`) ruft ohnehin nur diese
  Methode auf — sie war also bereits vorher "egal welches Modell", nur nie so
  dokumentiert. Ein künftiges echtes lokales Modell ersetzt später nur diese
  eine Klasse, der Rest der Pipeline ändert sich nicht.
- Aktuell wirft `LocalModelClient.chat()` bewusst einen klaren Fehler
  (`NotImplementedError`), falls `ai_provider: lokal` gesetzt wird — kein
  stilles Scheitern.

**Modell-/Runtime-Entscheidung getroffen, aber bewusst nicht installiert:**
**llama.cpp (über `llama-cpp-python`) + ein Phi-4-mini-Modell im GGUF-Format +
GBNF-Grammar-Constraint** — nicht Microsofts eigener „ONNX Runtime GenAI"-Pfad.
Grund: unser Signal-Schema ist sehr streng (genau 5 rangierte Gründe, feste
Kategorien, Kurszonen mit `von <= bis`, bedingte Pflichtfelder im
Halte-Kriterium) — selbst Groq (ein 70-Milliarden-Parameter-Modell) braucht
dafür gelegentlich einen zweiten Versuch. Ein kleines lokales Modell (3-4
Milliarden Parameter) bräuchte vermutlich noch öfter einen Retry, wenn es sich
nur auf trainiertes Verhalten verlässt. GBNF-Grammar-Constraint erzwingt
gültiges JSON bereits beim Erzeugen jedes einzelnen Wortes — eine strukturelle
Garantie, kein bloß antrainiertes Verhalten.

**Warum die eigentliche Installation bewusst zurückgestellt bleibt:** ein
int4-quantisiertes Modell dieser Größe bräuchte schätzungsweise 2,5-3,5 GB RAM
allein für die Modell-Gewichte. Auf der aktuellen 24/7-Notebook-Hardware (8 GB
RAM) würde das den bisher komfortablen Speicherpuffer spürbar einengen — und
ein Zuverlässigkeitstest auf beengter
Hardware würde ohnehin ein zu pessimistisches Bild liefern. **Empfehlung:**
diesen Schritt erst nach einem Hardware-Upgrade tatsächlich umsetzen, dann mit
realistischen Testbedingungen.

---

## 9. Einstandspreis / Gewinn-Verlust — echter Marktpreis aus Bitpanda-Trades

**Zweck (2026-07-11, Nutzer-Wunsch):** bisher zeigte die App nirgends, ob eine
Position im Gewinn oder Verlust steht — nur den aktuellen Marktwert (Menge ×
Kurs). Auslöser war eine konkrete Beobachtung des Nutzers: Bitpandas eigene
Anzeige "durchschnittlicher Kaufpreis" verwechselt den echten Marktpreis mit der
**steuerlichen** Bemessungsgrundlage — bei Krypto-zu-Krypto-Swaps (in Österreich
keine steuerliche Realisierung) wird der ursprüngliche EUR-Anschaffungswert der
gesamten Swap-Kette übertragen, nicht der tatsächliche Preis des neu erhaltenen
Assets. Konkretes Beispiel: Bitpanda zeigte für eine BTC-Position einen
"Kaufpreis" von 157.586 € an — einen Wert, den BTC nie hatte.

**Bewusste Eingrenzung:** Diese Funktion bildet ausschließlich den **echten
Marktpreis** zum Kaufzeitpunkt ab — **keine** steuerliche Kostenbasis-Verfolgung
über Swap-Ketten. Das bleibt bei Bitpanda selbst (dort steuerlich korrekt
geführt) und ist für dieses Tool nicht relevant.

**Datenquelle:** `GET /v1/wallets/transactions` (Bitpanda, authentifiziert) liefert
für jede `buy`/`sell`-Transaktion den echten Marktpreis zum Zeitpunkt
(`trade.price`, EUR-denominiert) — auch für die Empfangs-/Verkaufsseite eines
Swaps, da beide Seiten zu echten Marktpreisen "gehandelt" werden. Interne
Bewegungen (Transfer/Staking/Gebühren) haben keinen Preis und werden ignoriert.

**Berechnung — gleitender Durchschnitt:** alle bepreisten Buy/Sell-Trades eines
Assets werden chronologisch verarbeitet — ein Kauf blendet in den bestehenden
Durchschnittspreis ein, ein Verkauf reduziert nur die Menge (der Durchschnitt der
verbleibenden Stücke bleibt unverändert).

**Ehrlichkeits-Regel (P-10):** nicht jede gehaltene Einheit stammt aus einem
bepreisten Trade — Staking-Gutschriften oder externe Einzahlungen haben keinen
Marktpreis. Diese Menge wird **nie stillschweigend mitgepreist**, sondern in der
Portfolio-Anzeige explizit als "⚠ unbepreist" ausgewiesen.

**Manueller Override:** für Bestände ohne (vollständige) Bitpanda-Handelshistorie
(Alt-Bestände, Excel-Import) kann im Portfolio-Tab per Doppelklick auf eine Zeile
ein manueller Einstandspreis eingetragen werden — hat dann **kompletten Vorrang**
vor dem automatisch berechneten Wert, sowohl in der Anzeige als auch im
KI-Kontext.

**App-Start- und Trigger-Verhalten:** kein automatischer Trigger beim App-Start
(gleiches Prinzip wie der Bestandsabgleich — braucht einen optionalen API-Key,
ist bewusst nutzergetrieben). Der Erstlauf holt die komplette Transaktionshistorie
(kann je nach Kontogröße bis zu einer Minute dauern, läuft threaded im
Hintergrund). Jeder weitere Lauf ist **inkrementell**: da Bitpanda Transaktionen
neueste-zuerst liefert, bricht die Abfrage früh ab, sobald bereits bekannte
Transaktionen erscheinen — nur echt neue Trades werden geladen und in den
bestehenden Durchschnitt eingeblendet.

**KI-Integration:** der effektive Einstandspreis und der daraus resultierende
Gewinn/Verlust in % fließen als niedrig gewichteter Kontext-Fakt in die
Signal-Pipeline ein (`haltung.einstandspreis_eur`/`gewinn_verlust_pct`, SYSTEM_PROMPT-
Regel 19) — relevant für die Halten/Verkaufen-Abwägung, aber **keine harte Regel**
und kein Ersatz für die Stop-Loss-/CRV-Pflicht (Z-2).

---

## 10. Strategie-Katalog (S-1 bis S-6)

Pro Asset wählbar, der Agent schlägt die zur Marktlage passende Strategie vor.

| ID | Name | Kern | Status |
|----|------|------|--------|
| S-1 | HODL / Core | langfristig halten, an starken Leveln nachkaufen | aktiv |
| S-2 | DCA | regelmäßige Käufe unabhängig vom Preis | aktiv, aber noch **keine echte Mehrfach-Tranchen-Unterstützung im Signal-Schema** (offener Punkt) |
| S-3 | Swing-Trading | Ein-/Ausstieg an Support/Resistance und Fibonacci | aktiv |
| S-4 | Trendfolge | Einstieg bei bestätigtem Trend, Trailing-Stop | aktiv |
| S-5 | Kapitalschutz | defensiv, hohe Cash-Quote, automatisch bei Drawdown | aktiv |
| S-6 | Hebel-Long | nur Long, strikt nach Risiko-Regeln | **deaktiviert** |

---

## 11. Wo diese Regeln im Code stehen (für Nachvollziehbarkeit)

- `Basisinfos/config.yaml` — alle einstellbaren Zahlen (Abschnitte `risiko`, `regime`, `antizyklisch`, `strategien`)
- `agent/krypto/risk_gate.py` — harte Durchsetzung von RM-1/2/4/5, Z-2 (CRV), Positionsgrößen-Clamp, Bitpanda-Veto
- `agent/krypto/regime.py` — RG-1 bis RG-3 (Regime-Bestimmung)
- `agent/krypto/anticyclic.py` — vereinfachte AZ-1-Heuristik
- `agent/krypto/analyst.py` — SYSTEM_PROMPT (alle Regeln, die der KI als Anweisung mitgegeben werden) + Schema-Validierung
- `agent/krypto/pipeline.py` — Reihenfolge R-5.0 bis R-5.11 (Orchestrierung)
- `scheduler/background.py` — alle automatischen Jobs (Abschnitt 6)
- `importer/bitpanda_sync.py`, `importer/excel_import.py` — manuelle Bestands-Abgleiche (Abschnitt 6)
- `agent/krypto/backward_tracking.py` — Signal-Ergebnis-Prüfung (Abschnitt 7, Selbstverifikations-Vision Schritt 2)
- `api/local_model.py` — lokale KI-Ebene, Architektur-Seam (Abschnitt 8, noch nicht aktiv)
- `importer/bitpanda_avg_cost.py`, `api/bitpanda.py::get_wallet_transactions()` — Einstandspreis aus Bitpanda-Trades (Abschnitt 9)

---

## 12. Offene / vorläufige Werte — die naheliegendsten Kandidaten für spätere Anpassung

Diese Werte sind laut Spezifikation ausdrücklich **vorläufig** (`[OFFEN]`-markiert) und
noch nicht durch echte Ergebnisse verifiziert — sie sind der wahrscheinlichste
Startpunkt, sobald Backward-Tracking/Outcome-Daten vorliegen:

- RM-2 Core-Allokations-Limit (35 % für BTC/ETH) — nachträglich erhöht, weil die reale
  BTC-Allokation das alte 25%-Limit überschritt; "BTC hat den Lead"-Frage insgesamt
  noch nicht grundsätzlich besprochen.
- RM-4 Cash-Reserve-Minimum (10 % **und** der neue Festbetrag 2000 €, beide vorläufig)
- Small-Cap-Budget je Regime (0/4/8/12/15 %)
- Mindest-Konfidenz je Regime (85/75/65/60/60 %)
- Die vier Gewichte je Regime (Technik/Fundamental/Momentum/Makro)
- RG-4 Makro-Multiplikator (`risikoappetit_faktor`, aktuell fix auf 1,0)
- RM-10 max. Hebel (3x, aktuell ohnehin deaktiviert)
