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
| RM-10/RM-11 | Hebel: Long **und** Short (Short nur beratend, Bitpanda kann es noch nicht ausführen), max. **10x** (2026-07-14 kalibriert), eigenes Risiko-pro-Trade von **1 %** (statt 2 % bei Spot), Liquidationspreis als Schätzung ausgewiesen | Formel/Regelwerk + komplette Umsetzung (Screening/Risiko-Formeln/Positions-Rekonstruktion/KI-Empfehlung/Budget-Allocator/UI-Tab) fertig | **AKTIV, automatisch im 15-Min-Takt + im "Hebel"-Tab sichtbar** — volles Design in Kap. 14, `docs/hebel_positionsformel.md` |

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

**Gestakte Bestände fließen seit 2026-07-11 auch in RM-1/RM-2/RM-4 selbst ein**
(nicht nur in die Anzeige) — mit einer konservativen Ausnahme für ETH, dessen
Un-/Restaking bisher nicht instant war. Volle Details in Kap. 14.

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

**AZ-4 seit 2026-07-12 strukturiert umsetzbar (gestaffelte Kauf-/Verkaufszonen).**
Bisher war "gestaffelt kaufen" nur eine lose Absicht ohne Schema-Unterstützung — Groq
konnte höchstens EINE Kauf-/Verkaufszone (`entry`) vorschlagen. Jetzt kann Groq
zusätzlich das optionale Feld `tranchen` füllen: 2-5 Preiszonen mit Prozentanteil der
Gesamtposition (Summe 100 %), aufsteigend von der nächsten/höchsten zur tiefsten Zone,
optional mit einer Trigger-Bedingung als Freitext (z. B. "Bodenbestätigung laut
Regime-/Risiko-Modell"). Gilt symmetrisch für Käufe UND Verkäufe.

**Voraussetzungen, alle drei müssen gleichzeitig erfüllt sein:**
1. Regime ist `baer`, `krise_extrem` **oder** `seitwaerts` (bewusst weiter gefasst als
   nur die Extremfälle — Akkumulation beginnt oft schon vor der offiziellen
   Bär-Bestätigung; Bulle/Euphorie-extrem sind ausgeschlossen, weil tiefere
   Tranchen-Zonen dort meist unausgefüllt bleiben und Kapital unnötig binden).
2. Asset ist BTC oder ETH (aktuell keine anderen Assets vorgesehen).
3. Ein per-Asset-Schalter im Watchlist-Tab ("Tranchen-Vorschläge umschalten
   (BTC/ETH)") steht auf "An" — Default: an für BTC/ETH.

**Bewusst reine Zusatz-Information, kein neues Veto und keine echte Order-Anbindung:**
- Die eine `position_size` bleibt die geklemmte Gesamtgröße (RM-1/RM-2 unverändert) —
  jede Tranche ist nur ein Prozentanteil davon, kein eigener Absolutbetrag von Groq.
- Ein fehlerhafter Tranchen-Vorschlag (Summe ≠ 100 %, kaputte Zone) wird verworfen,
  löst aber **keinen** Validierungsfehler des Gesamtsignals aus.
- **Keine Order-Ausführung oder -Verfolgung möglich** — live geprüft (2026-07-12):
  weder `/fiatwallets`, `/wallets`, `/wallets/transactions` noch `/trades` zeigen
  offene Orders der persönlichen Bitpanda-API. Ein Order-Ausführungs-API existiert nur
  als separates B2B-Partnerprodukt, für Privatkunden nicht zugänglich. Wer eine
  Tranche tatsächlich umsetzen will, muss sie selbst als echte Bitpanda-Order anlegen
  (Fusion empfohlen — sperrt den Betrag korrekt in `/fiatwallets`, siehe Kap. 14).
- Die Z-2-CRV-Prüfung (Mindest-Chance-Risiko-Verhältnis) rechnet bei aktiven Tranchen
  weiterhin über die `entry`-Gesamtspanne — wird dadurch zu einem **geblendeten
  Gesamtwert** über alle Tranchen, keine scharfe Einzeltrade-Kennzahl mehr.
- Kein Ausführungs-Tracking je einzelner Tranche (die bestehende
  Umsetzungs-Rückmeldung/Backward-Tracking bleibt signal-weit) — ohnehin nicht
  sinnvoll umsetzbar ohne Order-API.

### AZ-4 Baustein 2: Boden-Zielzone für BTC/ETH (2026-07-12)

Zweite Bausteinstufe der Bärenmarkt-Akkumulations-Roadmap (Baustein 1 =
AZ-4-Tranchen oben, Baustein 3 = Cash-Reserve-Ziel, noch offen). Liefert eine
**Wahrscheinlichkeits-Zone** (kein hartes Kursziel), wo ein Zyklus-Tief für BTC
bzw. ETH realistisch liegen könnte — als zusätzlicher Kontext für den Nutzer UND
als Groq-Fakt (fließt in die Begründung/den Tranchen-Vorschlag ein, ohne selbst
ein Veto oder eine Regel durchzusetzen).

**Methodik:** eine einfache Log-Log-lineare Regression über die gesamte
verfügbare Preishistorie (dasselbe bestehende Modell wie beim BTC-Zyklus-Risiko,
Kap. 5) liefert eine Trendlinie. Das historische Abweichungs-Band vergangener
echter Zyklus-Tiefs (live nachgerechnet, 2026-07-12, ohne Lookahead) wird auf die
aktuelle Trendlinie projiziert:
- **BTC** (Datenquelle: blockchain.com, seit 2009): −1,16 / −0,78 / −1,26
  Standardabweichungen an den Tiefs vom 2015-01-14 / 2018-12-15 / 2022-11-21.
- **ETH** (Datenquelle: yfinance `ETH-USD`, seit 2017-11 — kein BTC-Äquivalent
  verfügbar: CoinGecko-Free-Tier auf 365 Tage limitiert, Kraken nur ~720 Tage):
  −2,04 / −0,41 Standardabweichungen an den Tiefs vom 2018-12-15 / 2022-11-21.
  **Nur 2 Vergleichspunkte, weit gestreut — deutlich unsichere Datengrundlage.**
  Jede Anzeige/jeder Groq-Fakt zur ETH-Zone trägt deshalb einen sichtbaren
  Niedrig-Konfidenz-Hinweis.
- 2020-03-13 (COVID-Crash) bewusst aus beiden Bändern ausgeschlossen — ein
  Liquiditätsschock, kein echtes mehrjähriges Zyklus-Tief.

**Zwei Korrektur-Komponenten** (config.yaml `boden_zielzone:`, beide bewusst
transparent getrennt statt zu einem Faktor verschmolzen):
1. **Reifegrad-Dämpfer** (`reifegrad_daempfer_staerke`, Start 0,15): zieht beide
   Bandkanten Richtung Trendlinie — mit wachsender Marktkapitalisierung werden
   Korrekturen historisch tendenziell milder, ein starres Band aus früheren,
   kleineren Zyklen wäre sonst zu tief angesetzt.
2. **Aktien-Bärenmarkt-Overlay** (Nutzer-Punkt: gemeinsamer Liquiditätsentzug
   kann BTC/ETH zusätzlich tiefer drücken): sind S&P 500 **oder** Nasdaq
   (`equities_baermarkt_verknuepfung: entweder`, feste Nutzer-Entscheidung) mehr
   als `equities_baermarkt_schwelle_prozent` (Start 20 %) vom
   `equities_baermarkt_lookback_jahre`-Hoch (Start 5 Jahre) entfernt, wird die
   untere Bandkante um `equities_overlay_shift_std` (Start 0,2) zusätzlich
   vertieft. Wirkt dem Reifegrad-Dämpfer entgegen, bewusst getrennt sichtbar.

**Live-Beispiel (2026-07-12, echte Daten):** BTC-Zone 63.029–83.601 $, ETH-Zone
986–2.729 $ (mit Niedrig-Konfidenz-Hinweis), Aktien-Bärenmarkt aktuell nicht
aktiv (S&P −0,5 %, Nasdaq −3,0 % vom Hoch — beide unter der 20-%-Schwelle).

**Persistenz:** täglicher Snapshot in `macro_snapshot` (dieselbe Tabelle wie
BTC-Dominanz/Fear&Greed/FRED — day-keyed, signal-unabhängig), damit die
Verschiebung der Zone über Zeit nachvollziehbar bleibt. ETH- und
Aktien-Index-Daten werden dabei **höchstens 1×/Tag** live abgerufen
(Tages-Cache) — jeder manuelle "Signal berechnen"-Klick und jeder der beiden
täglichen Marktscan-Läufe würde sonst zusätzliche Netzwerk-Calls auslösen. Die
eigentliche Zonen-Berechnung läuft trotzdem bei jedem Aufruf frisch (reine
Arithmetik, kein Netzwerk), damit eine config.yaml-Änderung sofort greift. BTC
selbst bleibt wie das bestehende Zyklus-Risiko **immer** frisch berechnet (kein
Cache nötig, kein zusätzlicher Netzwerk-Call gegenüber vorher).

**Bewusst reine Zusatz-Information**, wie die AZ-4-Tranchen oben: kein neues
Veto, keine Positionsgrößen-Beeinflussung, kein Automatismus. Bei einem
Fetch-Fehlschlag (ETH-Historie oder Aktien-Indizes nicht erreichbar) degradiert
nur der jeweilige Fakt auf `None`/nicht angezeigt (P-10) — die restliche
Signal-Pipeline läuft unbeeinträchtigt weiter.

### AZ-4 Baustein 3: Cash-Reserve-Ziel für BTC/ETH (2026-07-12)

Letzter Baustein der Bärenmarkt-Akkumulations-Roadmap. Ursprüngliche
Nutzer-Sorge: "zu geringe Reserve verhindert u. U. Nachkäufe". Antwort bisher
nur eine grobe Schätzung ("verdoppeln") — jetzt ein konkreter **Zielwert**
(kein neues hartes Veto, RM-4 bleibt der bestehende Minimum-Floor), wie viel
Cash-Reserve für die geplante Nachkauf-Kampagne über BTC/ETH sinnvoll wäre.

**Methodik, referenziert zwei verbreitete Praktiken aus dem
Risikomanagement** (bewusst als Konvention eingeordnet, nicht als
Marktgesetz):
- **"Buying in Thirds":** 3 Runden als Basis — balanciert zwischen
  All-in-Risiko (1 Kauf) und Überkomplexität (5+ kleine Käufe).
- **Value Averaging** (Michael Edleson, 1988): bei größerem Rücksetzer wird
  bewusst überproportional mehr Kapital eingesetzt, nicht gleichmäßig
  verteilt. Umgesetzt als **20 % / 30 % / 50 %**-Gewichtung über die drei
  Runden (Nutzer-Entscheidung 2026-07-12, `config.yaml
  cash_reserve_ziel.rundengewichte`).

**Rechnerische Präzisierung** (notwendig — sonst kürzt sich die Gewichtung
rechnerisch weg): naiver Gesamtbedarf je Asset = 3 × heutige
RM-1-Risiko-Obergrenze (jede Runde unabhängig wie ein normaler Trade heute
bemessen), **hart gedeckelt durch die RM-2-Allokationsgrenze** (strukturelles
Limit, das nie überschritten werden kann — RM-1 allein würde sonst beliebig
oft "neu bemessen" und die Allokationsgrenze ignorieren). Die 20/30/50-Gewichte
verteilen erst diesen bereits gedeckelten Gesamtbetrag auf die drei Runden.
Cash-Reserve-Ziel (gesamt) = RM-4-Minimum + BTC-Ziel + ETH-Ziel.

**Live-Beispiel (2026-07-12, echte Daten):** BTC-Ziel 4.014 $ (RM-2-Headroom
deckelte den naiven Bedarf von 3×6.137=18.411 $ auf 4.014 $ — das
RM-2-Allokationslimit war der bindende Faktor), ETH-Ziel 5.678 $, RM-4-Minimum
2.282 $ → Gesamt-Ziel 11.975 $.

**Grenzfälle, ehrlich behandelt (P-10):** ist die RM-2-Allokation für ein
Asset bereits ausgeschöpft, wird dessen Ziel-Anteil `0` (kein Spielraum mehr,
statt eines irreführenden positiven Werts). Ist RM-1 nicht berechenbar (kein
Stop-Loss ableitbar, z. B. fehlende ATR-Daten), wird der Wert `None` statt
geraten — degradiert nur diesen einen Fakt, blockiert nicht die Pipeline.

**Bewusst KEIN UI-Feld für die Rundengewichte** — Konsistenz mit allen
anderen Risikoparametern (RM-1/RM-2/RM-4/Regime-Gewichte), die ausschließlich
in `config.yaml` leben; ein UI-Editor wäre Mehraufwand für einen selten
geänderten Wert. Nur berechnet, wenn das aktuell bewertete Asset selbst
BTC/ETH ist (kein Mehraufwand für Alt-Coin-Signale) UND das Regime
`baer`/`krise_extrem`/`seitwaerts` ist — bewusst OHNE den per-Asset-AZ-4-
Toggle (Cash-Reserve-Ziel ist ein portfolioweiter Informationswert, keine
Tranchen-Einstellung). Signal-gebunden gespeichert (`signals`-Tabelle, wie
`tranchen_json`), nicht macro_snapshot-artig wie die Boden-Zielzone.

**Damit ist die komplette 3-Bausteine-Roadmap (Tranchen-Struktur →
Boden-Zielzone → Cash-Reserve-Ziel) abgeschlossen.**

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
| `marktscan` | 2× täglich, fix 04:00 + 16:00 Uhr | Kompletter Marktscan-Lauf (Stufe A-D, Kap. 13) — rein deterministisch, **kein** Groq-Aufruf mehr direkt in diesem Job (seit Phase 5, siehe unten) | CoinGecko + Kraken |
| `hebel_screening` (+ Budget-Allocator huckepack) | alle 15 Min | Hebel-Screening (Kap. 7) UND die zentrale Tagesbudget-Verteilung über drei Verbraucher: Hebel-Kandidaten (Tier 1), Marktscan-Kaufkandidaten-Begründung (Tier 2), Spot-Rotation für die am längsten überfälligen Krypto-Assets (Tier 3 — ersetzt seit 2026-07-14/Phase 5 den ehemaligen eigenen `signal_batch`-05:00-Cron) | Binance/Bybit/OKX/Kraken (Screening) + Groq→Cerebras→Gemini (je Tier budget-limitiert) |
| `backward_tracking` | 1× täglich, fix 06:00 Uhr | Prüft vergangene KAUFEN/NACHKAUFEN-Signale gegen die Kurshistorie — Take-Profit oder Stop-Loss erreicht? | keine (nur bereits vorhandene DB-Daten) |
| `bitpanda_cash` | alle 30 Min (nur mit gesetztem `BITPANDA_API_KEY`) | Nur der EUR-Fiat-Cash-Stand für RM-4 — **nicht** die vollen Bestände | Bitpanda (`/fiatwallets`) |

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

**Automatischer Fiat-Cash-Sync (2026-07-11, ERGÄNZT).** Ausgelöst durch die Frage
"was ist ein sinnvoller Cash-Betrag für Agent/Regelwerk" — Ergebnis: RM-4 bekam
über `/fiatwallets` schon immer den korrekten, um offene Fusion-Order-Sperren
bereinigten Betrag, das eigentliche Problem war nur die **Aktualität**: der Wert
zog erst bei manuellem "Bestände von Bitpanda abgleichen"-Klick nach. Seit heute
läuft dafür ein eigener, schlanker Job alle 30 Minuten (nur EUR-Fiat-Cash, NICHT
die vollen Bestände — die haben einen interaktiven Rückgangs-Bestätigungsdialog,
der aus einem Hintergrund-Thread nicht sauber aufrufbar ist). Läuft sofort nach
dem App-Start ein erstes Mal, danach im 30-Minuten-Takt. Ohne `BITPANDA_API_KEY`
bleibt der Job wie gehabt deaktiviert (P-8) — dann gilt weiterhin nur der manuelle
Sync bzw. die Eingabe im Portfolio-Tab.

**Batch-Signal-Berechnung (2026-07-13, NEU).** Ausgelöst durch die Beobachtung,
dass der Signale-Tab fast überall "-" zeigte — Signal-Berechnung ist bewusst
manuell (jeder Lauf kostet einen echten Groq-Aufruf), aber bei 54 Watchlist-
Assets (35 aktiv + 19 watchlist-Status) unpraktisch, wenn niemand 54× einzeln
klicken kann, gerade im 24/7-Betrieb ohne Handy-App.

**Gemessen statt geschätzt:** Groq Free-Tier erlaubt zwar 1.000 Requests/Tag,
aber nur **100.000 Tokens/Tag** — und eine echte Signal-Berechnung in dieser
App verbraucht ~5.600-6.000 Tokens (System-Prompt ~12.072 Zeichen/~3.450
Tokens, Fakten-JSON ~5.100-6.500 Zeichen, Antwort ~2.560 Zeichen — real gegen
den Code gemessen, nicht geschätzt). Das Token-Limit ist die bindende Grenze:
**reales Maximum ~15-18 Berechnungen/Tag**, nicht 1.000. Alle 54 Assets an
einem Tag ist damit unmöglich.

**Lösung: zweistufig wie Marktscan.** Eine günstige Auswahl (reine Staleness-
Sortierung — am längsten ohne echte Analyse zuerst, kein Groq-Aufruf) läuft
über alle Krypto-Assets (Aktien/ETF/Rohstoffe ausgeschlossen — die Pipeline
ist Krypto-only, siehe Spezifikation Kap. 11), die teure Groq-Analyse nur für
eine budget-begrenzte Teilmenge (`config.yaml signale_batch.taegliches_budget`,
Default 15). Stablecoins ebenfalls ausgeschlossen (A-1: bekommen strukturell
nie ein echtes Signal, würden sonst wegen "nie berechnet" dauerhaft ganz oben
stehen). Bewusst KEIN Gate auf die 7-Tage-Schwelle bei der Auswahl selbst —
das würde bei einer eingeschwungenen Rotation zeitweise Leerlauf und dann
einen Stau erzeugen, siehe `agent/krypto/signal_batch.py`-Docstring.

**Geteiltes Tagesbudget ohne eigene Zähltabelle:** sowohl der tägliche
Scheduler-Job als auch der manuelle "Fällige Signale jetzt berechnen"-Button
(Signale-Tab) als auch der bestehende Einzel-Klick-Button zählen automatisch
gegen dasselbe Budget, da alle drei in dieselbe `signals`-Tabelle schreiben
(`groq_raw_response IS NOT NULL AND created_at >= heute`). Lock-geschützt
(`signal_batch_lock`, wie bei `marktscan_lock`) gegen einen gleichzeitigen
Doppel-Lauf von Scheduler und manuellem Klick.

**E-Mail nur bei echtem Anlass:** anders als der Job-Ausfall-Cooldown gibt es
hier keinen Cooldown, sondern ein Inhalts-Gate — eine E-Mail geht nur raus,
wenn mindestens ein Ergebnis NICHT HALTEN ist (`config.yaml
signale_batch.benachrichtigung_email`). Ein reiner HALTEN-Batch (der
Normalfall) verschickt keine tägliche Spam-Mail.

**Wichtiger Korrektheits-Fund beim Bauen:** `signals.gate_passed=True` reicht
NICHT als "hat eine echte Groq-Analyse bekommen" — der
`AnalystResponseInvalid`-Fallback-Pfad (kaputtes/unvollständiges JSON nach
Retries) setzt `gate_passed=True`, aber `groq_raw_response` bleibt `None`.
Korrektes Kriterium: `groq_raw_response IS NOT NULL`.

**Nachtrag: echter Spot-Cooldown-Fix (2026-07-15, nach einem echten
3-Provider-Erschöpfungs-Vorfall am Notebook, Details in Memory
`project_llm_budget_ueberlast_2026-07-15`).** Die Verteilungsformel oben
(Tier 1/2/3) hatte für Hebel (Tier 1) und Marktscan (Tier 2) schon immer
einen echten Cooldown (`budget_allocator.cooldown_stunden`, 3,5 Std.) — Tier
3 (Spot-Rotation) dagegen **keinen**: `select_assets_due_for_signal()` hat
nur nach "am längsten nicht analysiert zuerst" sortiert, ohne jeden
Mindestabstand. Bei ~40 aktiven Krypto-Assets und einem 15-Minuten-Takt
bedeutete das: eine komplette Rotation dauerte nur ~40 Minuten statt eines
Tages — real bestätigt mit 234 Spot-Signalen an einem einzigen Tag für nur
40 distinkte Symbole. Fix: `select_assets_due_for_signal()` bekam einen
echten `cooldown_stunden`-Parameter (Default `SPOT_COOLDOWN_STUNDEN = 20`,
`config.yaml budget_allocator.spot_cooldown_stunden`) — ein Asset mit einer
echten Analyse innerhalb des Cooldown-Fensters wird jetzt ausgeschlossen,
bevor sortiert/gekappt wird. Gilt automatisch auch für den manuellen
"Fällige Signale jetzt berechnen"-Button (dieselbe Funktion), nicht nur für
den Budget-Allocator.

**Nachtrag: GUI-Schalter "Nur Long" für Hebel-Kandidaten (2026-07-15,
Nutzer-Wunsch).** Von 14 tatsächlichen Hebel-"ERÖFFNEN"-Empfehlungen im
gesamten bisherigen Datensatz waren 13 SHORT, nur 1 LONG — Bitpanda kann
Hebel-Short aber gar nicht ausführen, jede SHORT-Analyse war damit
faktisch verschwendetes LLM-Budget. Neues Menü "Hebel" → "Nur Long
analysieren" (`ui/settings.py::hebel_richtung_modus`, LIVE wirksam, kein
Neustart nötig) filtert SHORT-Kandidaten schon **vor** dem Cooldown-Check
und dem LLM-Aufruf heraus (`agent/krypto/budget_allocator.py::
run_budget_allocator()`) — ein direkter Hebel auf die tatsächliche
Aufrufzahl, keine nachträgliche Anzeige-Filterung.

**Nachtrag: Zwei-Stufen-Cooldown für Spot-Rotation (2026-07-16, Nutzer-
Wunsch nach Gewichtungs-Analyse).** Der einheitliche Spot-Cooldown (siehe
oben, 20 Std.) behandelte gehaltene Kernpositionen (`typ: core`, RM-2) und
reine taktische Watchlist-Kandidaten ohne Position gleich — obwohl bei
gehaltenen Positionen echtes Geld an einer Neubewertung hängt. Neuer
`cooldown_stunden_kern`-Parameter (Default 10 Std., `config.yaml
budget_allocator.spot_cooldown_stunden_kern`) in
`select_assets_due_for_signal()`: ein Asset gilt als "Kern", wenn
`asset.typ == "core"` ODER es aktuell gehalten wird (Bestand + gestakte
Menge > 0, live per `db.get_all_holdings()` geprüft) — bekommt dann ~2×/Tag
statt ~1×/Tag eine Neubewertung. Reale Watchlist (2026-07-16): 13 core
(100 % davon gehalten) + 8 weitere gehaltene taktische Assets = 21
"Kern"-Symbole, 19 rein taktische Watchlist-Symbole ohne Position bleiben
bei 20 Std. Moderater Mehrverbrauch (~13-21 zusätzliche Calls/Tag), kein
Rückfall in die alte Burst-Problematik.

**Nachtrag: Vollständigkeits-Audit der Empfehlungs-E-Mails (2026-07-16,
Nutzer-Wunsch "prüfe ob alle relevanten Informationen enthalten sind").**
Bestätigter Fund: `_notify_spot_signal()`/`_notify_hebel_signal()`
(`scheduler/background.py`) enthielten Positionsgröße
(`position_size_usd/eur/note`) und AZ-4-Tranchen (`tranchen_json`,
Anteile je Kauf-Stufe) NICHT im E-Mail-Text — obwohl beides im Signale-Tab
schon immer vollständig angezeigt wurde. Ebenso fehlte bei Hebel-
Empfehlungen der `eigenkapitalbedarf_usd` (im Hebel-Tab längst sichtbar).
Beide E-Mails um die fehlenden Felder ergänzt (neue Hilfsfunktion
`_formatiere_positionsgroesse_und_tranchen()`, gleiche Rundung/Darstellung
wie im Signale-Tab). Der Bitpanda-Ausführbarkeits-Hinweis
(`ausfuehrbarkeit_hinweis`, siehe unten) war dagegen bereits vollständig in
der Hebel-E-Mail enthalten — keine Lücke dort.

**Nachtrag: automatische Status-Hochstufung watchlist → aktiv (2026-07-16,
Nutzer-Wunsch nach dem BRETT-Fund).** `config.yaml`s `status`-Feld
(aktiv/watchlist) wurde bisher NIE automatisch nachgezogen — ein Kauf über
Bitpanda ließ die Bestandsmenge korrekt synchronisieren, aber der Watchlist-
Status blieb auf "watchlist" stehen, bis jemand die Datei manuell editierte.
Neue Funktion `config.py::update_watchlist_status()` (identisches Backup+
Validierungs-Muster wie `add_watchlist_entry()` — reine Text-Ersetzung NUR
der betroffenen Zeile, Backup vorher, `yaml.safe_load()`-Validierung danach,
automatische Wiederherstellung bei Fehlschlag) wird jetzt vom
`importer/bitpanda_sync.py`-Zuwachs-Zweig aufgerufen, sobald ein Symbol mit
Status "watchlist" einen echten Bestands-Zuwachs bekommt — für Krypto UND
Non-Krypto gleichermaßen (derselbe Sync-Pfad). Bewusst NUR diese eine
Richtung (watchlist → aktiv); die Rückrichtung bei vollständigem Verkauf
wird NICHT automatisch ausgelöst (ein Coin bleibt oft absichtlich weiter
beobachtet). Isoliert per try/except — ein Config-Schreibfehler blockiert
nie den eigentlichen Holdings-Sync. Verifiziert gegen eine Kopie der echten
`config.yaml` (BRETT watchlist→aktiv, No-Op bei bereits gesetztem Status,
Nachbar-Einträge unangetastet) — die echte Datei wurde dabei nicht berührt.

**Audit-Ergebnis: Hebel-"Swing" (`trade_thesis_typ: swing_strategie`) und
Bitpanda-Einschränkung (2026-07-16, Nutzer-Nachfrage).** `richtung`
(LONG/SHORT) und `trade_thesis_typ` (`einmal_trade` = kurzfristige,
ereignisgetriebene Squeeze-Chance vs. `swing_strategie` = bestätigter,
mehrtägiger bis wochenlanger Trend) sind zwei UNABHÄNGIGE Felder im
Hebel-Schema (`agent/krypto/hebel_analyst.py`) — Swing war nie bewusst
long-only konzipiert, der SYSTEM_PROMPT deckt "Long UND Short" für beide
Thesentypen gleich ab. Reale Daten bestätigen aber eine starke
Konzentration: von 13 realen SHORT-"ERÖFFNEN"-Empfehlungen waren 12
`swing_strategie` (nur 1 `einmal_trade`) — SHORT-Empfehlungen sind also
fast ausschließlich mehrtägige Trendfolge-Swings, keine kurzen
Squeeze-Spielereien. Die Bitpanda-Einschränkung selbst ist bereits
vollständig und **deterministisch** (nicht von der KI entschieden)
abgedeckt: `agent/krypto/hebel_risk_gate.py` setzt
`ausführbarkeit_hinweis` = "Aktuell nicht über Bitpanda ausführbar..." für
JEDE SHORT-Empfehlung, unabhängig vom Thesentyp — sichtbar im Hebel-Tab UND
(nach obigem Fix) in der E-Mail. **Kein Code-Fund/keine Lücke** — die
Entscheidung "Swing/SHORT trotzdem informativ zeigen (Marktlese-Wert) vs.
komplett unterdrücken" ist bereits als Nutzer-Wahl über den "Nur
Long"-Schalter (siehe oben) verfügbar, keine zusätzliche Swing-spezifische
Restriktion nötig.

### Manuell (GUI-Aktionen, nur bei Klick)

| Aktion | Wo | Was |
|--------|-----|-----|
| "Jetzt aktualisieren" | Toolbar (oben) | Sofortiger Krypto-Preis-Refresh (CoinGecko) + Bitpanda-Listing-Check |
| "Signal berechnen" | Signale-Tab | Die **gesamte** Agent-Pipeline (R-5.0 bis R-5.11, Abschnitt 5) für **ein** Asset — inkl. echtem Groq-Aufruf. Bewusst **nie automatisch/geplant** — jeder Signal-Lauf kostet einen KI-Aufruf und soll bewusst ausgelöst werden. |
| "Signal-Historie" | Signale-Tab | Zeigt alle bisherigen Signale des ausgewählten Assets inkl. Backward-Tracking-Ergebnis (Take-Profit/Stop-Loss/Offen/Abgelaufen) — reine Anzeige, kein externer Aufruf. |
| "Fällige Signale jetzt berechnen" (2026-07-13, NEU) | Signale-Tab | Berechnet die am längsten überfälligen Krypto-Assets sofort statt beim nächsten 05:00-Scheduler-Lauf, respektiert dasselbe geteilte Tagesbudget (siehe oben) — kein separater Klick pro Asset nötig. |
| "Jetzt scannen" | Marktscan-Tab | Derselbe Marktscan-Lauf wie der 04:00/16:00-Scheduler-Job, nur sofort statt zur festen Uhrzeit |
| "Bestände von Bitpanda abgleichen" | Datei-Menü | Live-Abgleich **aller Bestände** (Krypto + Aktien/ETF/Rohstoffe) + EUR-Cash direkt von Bitpanda (siehe RM-4-Abschnitt oben) — **nie automatisch**, da ein echter, authentifizierter API-Key UND ggf. der interaktive Rückgangs-Bestätigungsdialog beteiligt sind. Der reine EUR-Cash-Anteil läuft seit 2026-07-11 zusätzlich automatisch (siehe oben). |
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
5. Bleibt ein Signal an keinem Tag entschieden, wird VOR der reinen
   Zeitablauf-Prüfung zusätzlich geprüft, ob es bereits **überholt** ist
   (siehe Punkt 6) — erst wenn auch das nicht zutrifft, bleibt es **offen**,
   außer es ist bereits älter als `backward_tracking.abgelaufen_nach_tagen`
   (`config.yaml`, aktuell **90 Tage**, vorläufiger Wert) — dann wird es als
   **„Abgelaufen (unentschieden)"** markiert und nicht weiter täglich neu
   geprüft.
6. **Überholt-Erkennung (2026-07-16, Nutzer-Wunsch: "redundante bzw.
   gegensätzliche Empfehlungen müssen rausfallen").** Backward-Tracking war
   bis dahin rein rückblickend/statistisch (Schritt 2 der
   Selbstverifikations-Vision) — es gab keinen Mechanismus, der eine noch
   offene, aber durch eine neuere Analyse längst überholte Empfehlung aktiv
   markiert. Jetzt: bevor ein offenes Signal zeitbasiert abläuft (90 Tage),
   prüft derselbe tägliche Lauf zusätzlich, ob für dasselbe Symbol (bei
   Hebel zusätzlich dieselbe Richtung LONG/SHORT) bereits eine **neuere**
   echte Analyse existiert — unabhängig davon, ob diese zustimmt
   (redundant, z. B. erneut KAUFEN) oder widerspricht (gegensätzlich, z. B.
   jetzt VERKAUFEN/HALTEN). Ist das der Fall, wird das ältere Signal sofort
   als **„Überholt (neuere Analyse vorhanden)"** markiert, unabhängig vom
   90-Tage-Fenster. Rein deterministischer Datumsvergleich gegen
   `db.get_latest_real_signal_per_symbol()` (Spot) bzw.
   `db.get_latest_hebel_signal_per_symbol_and_richtung()` (Hebel, neu) —
   **kein LLM-Call**, erhöht das Tagesbudget nicht. Bewusst **ohne**
   automatische Benachrichtigung (Nutzer-Vorgabe "mit oder ohne
   Benachrichtigung") — sichtbar über den bestehenden
   "Signal-Historie"-Button (Spot). Für Hebel gibt es aktuell noch keine
   entsprechende History-Ansicht im Hebel-Tab (offener Punkt, siehe Kap. 15).

**Die sechs Ergebnis-Felder je Signal:**

| Feld | Bedeutung |
|------|-----------|
| **Ergebnis-Status** | Einer von: Offen · Take-Profit erreicht · Stop-Loss erreicht · Abgelaufen (unentschieden) · Überholt (neuere Analyse vorhanden) · Nicht anwendbar |
| **Zuletzt geprüft am** | Zeitstempel des letzten Prüflaufs |
| **Entschieden am** | Datum, an dem die Zone erreicht wurde (leer, solange offen) |
| **Realisiertes CRV** | Nur bei entschiedenem Ergebnis: `(erzielter Kurs − Entry-Mitte) / (Entry-Mitte − Stop-Loss-Zone-Untergrenze)` — dieselbe konservative Formel wie die ursprünglich vorhergesagte CRV (Abschnitt 2, Z-2), nur mit dem tatsächlich erreichten Kurs statt der Zonen-Grenze. Positiv bei Take-Profit, negativ bei Stop-Loss. |
| **Datenquelle** | `real` (echtes OHLC) oder `proxy` (nur Tagesschlusskurs) |

**Wo du das siehst:** neuer Button **"Signal-Historie"** im Signale-Tab, direkt
neben "Signal berechnen" — zeigt alle bisherigen Signale des ausgewählten
Assets mit Datum, Aktion, Konfidenz und Ergebnis-Status, farblich markiert
(grün = Take-Profit, rot = Stop-Loss, neutral = offen, grau = abgelaufen
ODER überholt).
Macht eine bereits vorhandene, aber bis dahin nie genutzte Datenbank-Abfrage
erstmals sichtbar.

**Aktueller Stand (2026-07-10):** Bisher gibt es **kein einziges echtes
KAUFEN/NACHKAUFEN-Signal** in der Datenbank — alle bisherigen Signale sind
HALTEN. Backward-Tracking ist also einsatzbereit, aber noch ohne echte
Auswertungsgrundlage. Schritt 3 der Vision (KI-gestützte Regel-
Anpassungsvorschläge) braucht erst eine gewisse Anzahl echter, aufgelöster
Kauf-Signale, bevor er sinnvoll ansetzen kann.

### Erweiterung: Hebel-Backward-Tracking + Provider-Performance-Vergleich (2026-07-15)

Ausgangsfrage: sollen Groq/Cerebras/Gemini nach echter Trefferquote statt nur
nach roher Kapazität geordnet werden? Ein Qualitätsvergleich per Hand (siehe
Gemini-Memory) zeigte bereits qualitative Unterschiede, aber ohne Langzeit-
Historie lässt sich die Reihenfolge nicht belastbar optimieren — die
Infrastruktur wird deshalb jetzt gebaut, damit sie ab sofort automatisch
Daten sammelt, auch wenn heute noch fast keine vorliegen.

**Neu: `agent/krypto/hebel_backward_tracking.py`** — mirror des obigen
Mechanismus, aber für `hebel_signals` (ERÖFFNEN/NACHKAUFEN statt KAUFEN/
NACHKAUFEN), **richtungsabhängig** (LONG/SHORT kehren die Vergleichsrichtung
für Take-Profit/Stop-Loss um). Zusätzlicher vierter Ergebnis-Status
**„Liquidation wahrscheinlich"** — der Liquidationspreis liegt näher am Kurs
als der Stop-Loss (Sicherheitsmarge 15-20 %, siehe Abschnitt „Margin-/
Hebel-Trading"), wird deshalb bei einer Tages-Kerze, die mehrere Zonen
gleichzeitig trifft, **zuerst** geprüft — noch konservativer als die
bestehende „Stop-Loss gewinnt bei Gleichzeitigkeit"-Regel. Läuft im selben
täglichen Job wie oben (`backward_tracking`), keine zusätzliche Konfiguration
nötig.

**Neu: Provider-Performance-Aggregation** (`compute_provider_performance()`)
— gruppiert alle bereits aufgelösten Signale (Spot UND Hebel, getrennt
gehalten wegen unterschiedlicher Risikoprofile: 2 % vs. 1 % Positionsgröße)
nach Anbieter (Groq/Cerebras/Gemini) und zeigt je Anbieter Trefferzahl,
Win-Rate und durchschnittliches realisiertes CRV. Sichtbar als neue Karte
„Provider-Performance" auf der Remote-Steuer-Seite (Abschnitt 13).

**Wichtiger Datenstand (2026-07-15):** aktuell liegen praktisch keine
aufgelösten Signale vor (Spot: 2 offene, 0 aufgelöst; Hebel: 2 offene,
0 aufgelöst) — die Karte zeigt deshalb vorerst „noch keine Daten". Das ist
erwartetes Verhalten, kein Fehler — reine Infrastruktur, die erst über die
kommenden Wochen echte Vergleichswerte ansammelt.

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
| S-2 | DCA | regelmäßige Käufe unabhängig vom Preis (kalenderbasiert) | aktiv |
| S-3 | Swing-Trading | Ein-/Ausstieg an Support/Resistance und Fibonacci | aktiv |
| S-4 | Trendfolge | Einstieg bei bestätigtem Trend, Trailing-Stop | aktiv |
| S-5 | Kapitalschutz | defensiv, hohe Cash-Quote, automatisch bei Drawdown | aktiv |
| S-6 | Hebel-Long | nur Long, strikt nach Risiko-Regeln | **deaktiviert** |

**Terminologie-Klarstellung (2026-07-12):** die gestaffelten Kauf-/Verkaufszonen
("mehrere Tranchen an unterschiedlichen Preiszonen") gehören fachlich zu **AZ-4**
("gestaffelt, nie all-in", siehe Kap. 4), **nicht** zu S-2 — S-2/DCA ist per
Definition kalenderbasiert ("regelmäßig", unabhängig vom Preis), während die
Tranchen-Funktion preiszonen-basiertes Scaling-in/Laddering ist. Der vormals hier
offene Punkt "keine echte Mehrfach-Tranchen-Unterstützung" ist damit über AZ-4
gelöst, siehe Kap. 4.

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
- `remote/server.py`, `remote/status.py` — Remote-Steuer-Seite (Abschnitt 13)
- `importer/bitpanda_avg_cost.py::compute_staked_quantities()` — aktuell gestakte Mengen (Abschnitt 14)
- `api/yfinance_client.py` — EUR-Umrechnung für USD-only-Aktien wie PLTR/VST (Abschnitt 14)
- `indicators/calculations.py::compute_btc_log_regression_risk()`/`compute_eth_log_regression_risk()`, `agent/krypto/regime.py::_boden_zielzone()`, `api/yfinance_history.py` — AZ-4 Baustein 2, Boden-Zielzone (Abschnitt 4)
- `agent/krypto/risk_gate.py::compute_cash_reserve_ziel()`, `agent/krypto/pipeline.py::_compute_cash_reserve_ziel_context()` — AZ-4 Baustein 3, Cash-Reserve-Ziel (Abschnitt 4)

---

## 12. Betriebssicherheit — Systemstart, Fehlerbehandlung, wie du informiert wirst

**Zweck (2026-07-11, Nutzer-Wunsch):** vollständige, ehrliche Bestandsaufnahme —
was passiert beim Start automatisch, was brauchst du manuell, wie stabil sind
Scheduler und Agent wirklich, und auf welchem Weg erfährst du von einem Problem.
Wichtig für den geplanten 24/7-Betrieb am Notebook, wo du nicht ständig danebensitzt.

### Was beim Start passiert

| Schritt | Wann | Bei einem Fehler |
|---|---|---|
| Logging-Setup (Konsole + Logdatei) | immer | — |
| `.env`/`config.yaml` laden | immer | **Behoben (2026-07-12):** Try/Except → `logger.exception()` (landet garantiert in der Logdatei) + sichtbarer Fehlerdialog + sauberer Prozess-Abbruch (`sys.exit(1)`), statt eines stillen Absturzes |
| Datenbank initialisieren (`db.init_db`) | immer | **Behoben (2026-07-12):** gleiches Muster wie oben — Log + Dialog + `sys.exit(1)` |
| Bestände aus `Assets.xlsx` importieren | **nur beim allerersten Start** | **Behoben (2026-07-12), aber bewusst NICHT fatal:** Log + Dialog, die App startet trotzdem mit leeren Beständen weiter (Bestände lassen sich jederzeit über "Datei → Bestände aus Datei importieren…" nachholen) |
| Kurs-/OHLC-Historie erstbefüllen (CoinGecko/Kraken) | **nur beim allerersten Start** | Robust — jeder Asset-Abruf einzeln abgesichert, degradiert statt abzustürzen |
| Scheduler starten, Fenster öffnen | immer | — |

**Alle drei vormals ungeschützten Schritte sind jetzt abgesichert (2026-07-12,
`main.py::_show_startup_error()`).** Ein minimaler, versteckter Tk-Root zeigt
einen Fehlerdialog auch dann, wenn die eigentliche App-Hauptschleife noch gar
nicht läuft — wichtig, weil ein unbehandelter Python-Absturz sonst nur über
`sys.excepthook` auf `stderr` landet, **nicht** durch die `logging`-Handler
(die Logdatei bliebe sonst leer, egal wie gut sie eingerichtet ist). Config-
und DB-Fehler sind bewusst fatal (App kann ohne beides nicht sinnvoll
weiterlaufen), der Erstimport-Fehler bewusst nicht (fehlende Bestände sind
jederzeit nachholbar). Live gegen drei simulierte Fehlerfälle verifiziert
(fehlende `config.yaml`, beschädigte DB, fehlgeschlagener Erstimport) — in
allen drei Fällen landete der volle Traceback garantiert in der Logdatei.

### Was tun bei einem Fehler — Schritt für Schritt

Diese Anleitung ist für den Fall gedacht, dass die App nicht wie erwartet
hochfährt oder sich merkwürdig verhält — besonders relevant am 24/7-Notebook,
wo niemand direkt danebensitzt. Für jedes Szenario: woran du es erkennst, und
was du konkret manuell tun musst.

**1. App startet gar nicht, kein Fenster erscheint, dafür ein Fehlerdialog
("TradingInfoTool - Start fehlgeschlagen")**

Das ist ein **fataler** Config- oder Datenbank-Fehler (siehe Tabelle oben).
Die App hat sich bewusst sauber beendet, statt mit kaputtem Zustand
weiterzulaufen.
- Dialogtext lesen — er nennt bereits, ob es an `Basisinfos/config.yaml` oder
  an der Datenbank liegt, plus die eigentliche Python-Fehlermeldung.
- **Bei Config-Fehler:** `Basisinfos/config.yaml` öffnen (Texteditor genügt)
  und auf offensichtliche Syntaxfehler prüfen (fehlende Doppelpunkte,
  falsche Einrückung — YAML ist einrückungsempfindlich). Am einfachsten:
  letzte funktionierende Version aus dem Git-Verlauf vergleichen
  (`git log -- Basisinfos/config.yaml`, dann `git diff <commit> --
  Basisinfos/config.yaml`).
- **Bei DB-Fehler:** meist eine beschädigte/nicht lesbare
  `data/tradinginfotool.db`. **Nicht selbst reparieren versuchen** — stattdessen
  die Datei umbenennen (z. B. `tradinginfotool.db.defekt`) und die App erneut
  starten. Sie legt beim nächsten Start automatisch eine neue, leere Datenbank
  an (`db.init_db()`); Bestände lässt sich danach über "Datei → Bestände aus
  Datei importieren…" neu einspielen (historische Signale/Kursverlauf sind
  dann allerdings weg — falls die alte Datei noch gebraucht wird, vor dem
  Umbenennen eine Kopie sichern).
- Nach der Korrektur: App neu starten. Kommt derselbe Dialog wieder, Logdatei
  prüfen (siehe Punkt 4) für den vollen Traceback.

**2. App startet, aber ein Dialog "Erstimport fehlgeschlagen" erscheint**

Nur beim allerersten Start relevant (leere Datenbank). **Nicht fatal** — die
App läuft danach normal weiter, nur ohne importierte Bestände.
- Meist liegt es daran, dass `Basisinfos/Assets.xlsx` fehlt, das falsche
  Format hat, oder gerade in Excel geöffnet ist (Datei dann gesperrt).
  Excel schließen bzw. die Datei an den richtigen Ort legen.
- Import manuell nachholen: Menü "Datei → Bestände aus Datei importieren…" —
  identischer Code wie beim automatischen Erstimport, kein Unterschied im
  Ergebnis.

**3. Ein einzelner Scheduler-Job hängt (z. B. "Preise aktualisieren" läuft
seit über 10 Minuten, obwohl das normal Sekunden dauert)**

Am einfachsten über die Remote-Steuer-Seite (Abschnitt 13) zu erkennen ("läuft
seit X Min") und zu beheben — funktioniert aber auch ohne Remote-Zugriff:
- **Mit Remote-Zugriff (Handy/Tailscale):** Seite öffnen, "Zurücksetzen"-Button
  nutzen. Wichtig: das gibt nur die interne Sperre frei, ein neuer Versuch wird
  danach möglich — der ursprünglich hängende Vorgang im Hintergrund wird dadurch
  nicht zwangsläufig beendet.
- **Ohne Remote-Zugriff, direkt am Notebook:** App komplett beenden (Fenster
  schließen oder über den Task-Manager den `python`-Prozess beenden) und neu
  starten. Der Scheduler baut beim Start alle Sperren neu auf — ein Neustart
  behebt einen hängenden Job also immer zuverlässig, auch ohne den
  "Zurücksetzen"-Button.
- Einzelne Jobs schlagen normalerweise nicht dauerhaft fehl, sondern laufen im
  nächsten Takt automatisch wieder an (siehe "Scheduler-Jobs" unten) — ein
  manueller Eingriff ist nur bei einem echten Hänger nötig, nicht bei einem
  einzelnen fehlgeschlagenen Lauf.

**4. Logdatei finden und lesen**

Weg für alle Fälle, die keinen sichtbaren Dialog auslösen (z. B. ein
fehlgeschlagener einzelner Scheduler-Job):
- Pfad: `data/tradinginfotool.log` im Installationsordner (rotierend, max.
  3 × 5 MB — bei Bedarf existieren `tradinginfotool.log.1`, `.2`, `.3` mit
  älteren Einträgen).
- Mit einem normalen Texteditor öffnen (Editor, Notepad++, VS Code). Suche
  nach `ERROR` oder `Traceback`, um Fehler schnell zu finden — jede Zeile hat
  Zeitstempel + Modulname, um sie zeitlich einzuordnen.
- Seit 2026-07-11 zeigt die Remote-Steuer-Seite (Abschnitt 13) zusätzlich die
  letzten Fehlerzeilen direkt an, ohne die Datei selbst öffnen zu müssen.

**5. App war lange offline (Notebook aus, Update, Reise) — was beim nächsten
Start zu erwarten ist**

Siehe die eigene Auswertung dazu direkt im Anschluss ("Verhalten nach
längerer Downtime").

### Verhalten nach längerer Downtime (2026-07-12, Nutzer-Frage, geprüft)

**Frage:** Funktioniert/aktualisiert sich die App beim nächsten Start korrekt,
wenn sie längere Zeit nicht gelaufen ist?

**Kurz:** Ja — inklusive der Kurs-/OHLC-Historie, seit dem staleness-bewussten
Sofort-Trigger (siehe unten, ebenfalls 2026-07-12 umgesetzt).

Kein Job "merkt sich" eine verpasste Downtime im Sinne eines Nachhol-Zählers —
APScheduler nutzt einen reinen In-Memory-Job-Store, der beim Neustart verworfen
wird. Jeder Job verhält sich beim nächsten Start so, als wäre er neu:

| Job | Verhalten beim nächsten Start, unabhängig von der Downtime-Dauer |
|---|---|
| Kryptopreise, Aktien/ETF/Rohstoff-Preise | **Behoben (2026-07-12):** sofortiger erster Lauf direkt nach dem Start (`next_run_time=jetzt`), kein Warten mehr auf ein volles Intervall |
| Bitpanda-Cash-Sync | War bereits seit 2026-07-11 sofort (`next_run_time=jetzt`) |
| Kurs-/OHLC-Historie (für Indikatoren wie EMA-200) | **Behoben (2026-07-12), staleness-bewusst:** kein bedingungsloser Sofort-Lauf bei jedem Neustart, sondern nur, wenn die Daten tatsächlich veraltet sind (`_history_data_is_stale()`/`_ohlc_data_is_stale()`, `scheduler/background.py`) — prüft beim Scheduler-Aufbau je Asset das letzte Datum gegen `HISTORY_STALE_THRESHOLD_DAYS` (2 Tage). War die App z. B. eine Woche offline, läuft der Refresh sofort; nach einem kurzen Neustart (Daten noch frisch) wartet er wie gehabt bis zum nächsten 24-Std.-Takt |
| Marktscan, Backward-Tracking | Feste Cron-Uhrzeiten (04:00/16:00 bzw. 06:00) — kein Nachhol-Mechanismus nötig, der nächste reguläre Termin reicht, kein API-Kontingent-Risiko |

**Warum kein bedingungsloses "sofort" wie bei den Preisen:** anders als der
günstige Einzel-Preisabruf wäre ein bedingungsloser sofortiger Historie-/OHLC-
Lauf bei *jedem* Neustart (auch nach einem kurzen Absturz oder einem gewollten
Neustart nach 5 Minuten) ein vollständiger Asset-Refresh — unnötiger Verbrauch
von CoinGecko-/Kraken-API-Kontingent ohne echten Nutzen. Der staleness-bewusste
Trigger löst das: er prüft vor dem Scheduler-Start je Asset (mit
CoinGecko-ID bzw. Kraken-Listing) das letzte gespeicherte Datum und löst nur
dann sofort aus, wenn mindestens ein Asset tatsächlich veraltet ist — schlägt
der Check selbst fehl (z. B. DB-Problem), ist der sichere Default kein
Sofort-Lauf (P-10). Live gegen drei Szenarien verifiziert (frische Daten,
5 Tage alte Daten, leere Datenbank) — dabei auch eine Falle in APScheduler
selbst gefunden: `next_run_time=None` bedeutet NICHT "normal aus dem
Trigger berechnen", sondern legt den Job dauerhaft ohne nächsten Lauf an (er
würde nie mehr laufen) — das kwarg muss bei "nicht veraltet" deshalb komplett
weggelassen werden, nicht auf `None` gesetzt werden.

**In der Zwischenzeit erkennbar:** die Watchlist/Portfolio-Ansicht markiert
veraltete Preise/Historie ohnehin farblich (⚠, siehe "Wie du aktuell von einem
Problem erfährst" unten) — die Staleness-Anzeige selbst funktioniert nach
jeder Downtime-Länge korrekt, sie zeigt nur an, dass es bis zu 24 Std. dauern
kann, bis die Warnung von selbst verschwindet.

Ein einmaliger Ersteinrichtungs-Sonderfall bleibt unverändert bestehen: die
Kurs-/OHLC-**Erstbefüllung** (`is_history_first_run()`/`is_ohlc_first_run()`)
läuft nur exakt einmal im Leben der Datenbank, unabhängig von jeder späteren
Downtime — das ist beabsichtigt (danach übernehmen die 24-Std.-Jobs), betrifft
also nicht das oben beschriebene Downtime-Verhalten.

### Scheduler-Jobs — wie stabil sie wirklich sind

Jeder der sechs automatischen Jobs (Abschnitt 6) hat sein **eigenes**
Try/Except (`logger.exception(...)`, Verbindung wird im `finally` geschlossen) —
**kein** Job bleibt bei einem Fehler "hängen", jeder läuft beim nächsten Takt
automatisch wieder an, egal wie oft er vorher fehlgeschlagen ist. Zusätzlich gibt
es einen globalen Fehler-Listener (`EVENT_JOB_ERROR`/`EVENT_JOB_MISSED`) als
zweite Verteidigungslinie, falls doch etwas bis zum Scheduler selbst durchschlägt.
**Job-Ausfall-Backoff — ERLEDIGT (2026-07-12).** Die drei häufig getakteten
Jobs (`refresh_prices`, `refresh_securities_prices`, `bitpanda_cash` — je
15/15/30 Min. Normal-Takt) verdoppeln ab dem zweiten Fehlschlag in Folge das
Intervall bis zum nächsten Versuch (`_record_job_failure_for_backoff()` in
`scheduler/background.py`, verschiebt `next_run_time` per
`scheduler.modify_job()`), gedeckelt auf 4 Std. Ein erfolgreicher Lauf setzt
den Zähler zurück (`_record_job_success_for_backoff()`) — APScheduler's
`IntervalTrigger` rechnet den Normal-Takt danach automatisch ab dem
tatsächlichen letzten Lauf weiter, kein manueller Reset des nächsten
Laufzeitpunkts nötig (live gegen eine echte `BackgroundScheduler`-Instanz
verifiziert). Die beiden 24-Std.-Jobs (Historie/OHLC) und die
Cron-getakteten Jobs (Marktscan/Backward-Tracking) bewusst OHNE Backoff — ihr
Normal-Takt ist bereits so groß, dass ein zusätzliches Backoff keinen
nennenswerten Nutzen hätte.

### Wie du aktuell von einem Problem erfährst

- **Logdatei** (`data/tradinginfotool.log`, rotierend, 5 MB × 3) ist der einzige
  vollständige Weg — aktuell **kein Menüpunkt**, der sie dir öffnet, du müsstest
  den Installationsordner kennen.
- **Indirekt, verzögert:** Watchlist/Portfolio/Charts markieren Zeilen farblich
  als "veraltet" (⚠), wenn Preise seit 30 Minuten bzw. Historie seit 2 Tagen nicht
  aktualisiert wurde — aber nur für genau diese beiden Datenarten, nicht für
  Marktscan- oder Backward-Tracking-Fehlschläge.
- **Bei manuellen Aktionen** (Bitpanda-Sync, Einstandspreise berechnen, Signal
  berechnen) siehst du Fehler direkt in der Oberfläche (Popup bzw. Status-Zeile).
  Ausnahme: "Bestände neu importieren"/"aus Datei importieren" haben **kein**
  Try/Except — ein Fehler landet nur auf der Konsole, ohne Popup und ohne
  Logeintrag.
- **E-Mail-Benachrichtigung — ERLEDIGT (U-8, 2026-07-12).** Siehe eigener
  Abschnitt unten für Details.

### E-Mail-Benachrichtigung (U-8, 2026-07-12)

**Zweck:** die App läuft künftig auf dem 24/7-Notebook ohne ständige
Beaufsichtigung — bisher war der einzige Weg, von einem Problem zu erfahren,
aktiv in die Logdatei oder auf die Remote-Steuer-Seite (Abschnitt 13) zu
schauen. E-Mail schließt diese Lücke passiv: die App meldet sich selbst.

**Technisch:** neues Modul `api/email_notify.py`, `smtplib` +
`email.mime.text` (Python-Standardbibliothek, keine neue Abhängigkeit).
Gmail bewusst fest verdrahtet (`smtp.gmail.com:587`, STARTTLS) statt
konfigurierbarem SMTP-Host — die konzeptionelle Vorentscheidung (2026-07-11)
war ein eigener, separat angelegter **"Robot"-Gmail-Account** mit
App-Passwort, nicht der Hauptaccount des Nutzers: das App-Passwort ist ein
dauerhafter, programmatischer Zugriffsschlüssel zur gesamten Mailbox, der
auf dem 24/7-Notebook liegt — ein separates Konto begrenzt den Schaden im
Fall eines Leaks auf diesen einen Kanal. `GMAIL_ABSENDER_ADRESSE`/
`GMAIL_APP_PASSWORT` in `.env` (P-8: fehlen beide, bleibt die Funktion
komplett deaktiviert, kein Fehler, nur ein Info-Log — Kernfunktionen dürfen
nie von einem optionalen Benachrichtigungs-Kanal abhängen).

**Zwei Auslöser-Pfade, bewusst beide verdrahtet:** beim Durcharbeiten des
Scheduler-Codes zeigte sich, dass der bereits bestehende
`EVENT_JOB_ERROR`/`EVENT_JOB_MISSED`-Listener (`_log_job_event()`) nur bei
unbehandelten Bugs im Job-Wrapper selbst feuert. Der weitaus häufigere
Realfall — eine externe API (Groq/CoinGecko/Bitpanda) ist über Stunden nicht
erreichbar — wird von jedem der sieben `*_job()` bereits INTERN in seinem
eigenen `except Exception:`-Block abgefangen und geloggt, ohne den Listener
je zu erreichen. Eine E-Mail nur am Listener aufzuhängen hätte also genau
den Fall verpasst, um den es eigentlich geht. Deshalb ruft sowohl
`_log_job_event()` als auch jede der sieben Job-Funktionen denselben
gemeinsamen Helper `_notify_job_failure(job_id, fehler_text)` auf.

**Cooldown gegen Postfach-Spam:** `_notify_job_failure()` merkt sich pro
`job_id` den Zeitpunkt der letzten gesendeten Mail
(`_last_failure_email_sent`-Dict) und unterdrückt weitere Mails innerhalb von
`config.yaml benachrichtigung.email.job_ausfall_cooldown_minuten` (Start: 60)
— ein mehrstündiger oder mehrtägiger Ausfall erzeugt so höchstens eine Mail
pro Stunde statt eine pro fehlgeschlagenem Lauf.

**Start-Fehler:** an den zwei echten fatalen Stellen verdrahtet
(Watchlist-Laden, `db.init_db()` — siehe "Betriebssicherheit" oben), NICHT
beim allerersten Config-Lade-Fehler (Empfänger-Adresse kommt selbst aus
`config.yaml`, an der Stelle noch unbekannt) und NICHT beim nicht-fatalen
Erstimport-Fehler (einmaliges Ereignis, typischerweise während der Nutzer
ohnehin am Rechner sitzt). Dialog + Logdatei bleiben in jedem Fall die
primäre Absicherung — die E-Mail ist ein zusätzlicher, best-effort Kanal
obendrauf, ein Versandfehler (z. B. fehlendes App-Passwort) wird von
`send_notification_email()` selbst abgefangen und blockiert nichts (P-10).

Auch keine "Ausfall-Streak"-Zählung (z. B. erst nach 3x in Folge alarmieren)
— der Cooldown allein gilt als ausreichender Spam-Schutz für Job-Ausfälle.

### Marktscan-Kaufkandidaten-Mails (MS-1b, 2026-07-12)

Direkter Folgeschritt zu U-8, nutzt dieselbe E-Mail-Infrastruktur
(`api/email_notify.py`) wieder: findet ein Marktscan-Lauf (`marktscan_job()`,
2x täglich, 04:00/16:00) mindestens einen echten Kaufkandidaten
(`einstufung == "kaufkandidat"`), verschickt `_notify_marktscan_kaufkandidaten()`
in `scheduler/background.py` **eine gebündelte E-Mail** mit allen
Kaufkandidaten des Laufs (Symbol, Score, Tier, Einstufungs-Begründung, plus
KI-Kurzbegründung falls `marktscan.groq_automatisch_kaufkandidaten` aktiv
ist und Groq bereits automatisch dazu befragt wurde) — kein separater Mail
pro Kandidat. Schalter: `config.yaml marktscan.benachrichtigung_email`
(zusätzlich zum globalen `benachrichtigung.email.aktiv`).

**Bewusst OHNE Cooldown**, anders als bei Job-Ausfällen: ein wiederholt
gemeldeter Kaufkandidat ist keine Spam-Situation, sondern eine weiterhin
gültige Kauf-Chance — der Scan läuft ohnehin nur 2x täglich, und bereits vom
Nutzer entschiedene Kandidaten (verworfen/übernommen) tauchen wegen der
bestehenden Duplikat-Prüfung (`marktscan.py::_duplicate_should_skip()`)
gar nicht erst erneut auf. Eigener try/except um den gesamten
E-Mail-Versand (P-10) — ein Fehler beim Mailen darf einen erfolgreich
abgeschlossenen Marktscan-Lauf nicht nachträglich als "fehlgeschlagen"
markieren.

### Empfehlungs-E-Mails bei Spot-/Hebel-Signalen (2026-07-14)

**Zweck:** U-8 war ursprünglich als "Desktop-Benachrichtigungen bei neuen
Signalen" gedacht (Spezifikation), umgesetzt wurde zunächst bewusst nur der
schmalere Job-Ausfall-/Marktscan-Kandidaten-Teil — die eigentlichen
Kauf-/Verkauf-Empfehlungen selbst lösten bislang **keine** E-Mail aus. Da der
Nutzer selten am Notebook ist und die tatsächliche Umsetzung ohnehin manuell
über die Bitpanda-App erfolgt (P-7, Advisory-only), schließt dies die Lücke:
jede **handlungsrelevante** Spot- oder Hebel-Empfehlung löst jetzt eine
eigene E-Mail aus.

**Handlungsrelevant heißt:** alle Aktionen außer HALTEN (Spot:
KAUFEN/VERKAUFEN/TAUSCHEN/NACHKAUFEN; Hebel: ERÖFFNEN/NACHKAUFEN/
HEBEL_ERHÖHEN/HEBEL_SENKEN/TEILVERKAUF/SCHLIESSEN). HALTEN — der weitaus
häufigste Fall — löst bewusst **nie** eine Mail aus, sonst würde die
Mailflut kontraproduktiv.

**Nur automatische Läufe, keine manuellen Klicks:** die E-Mail wird direkt
im Budget-Allocator-Pfad (`hebel_screening_job()`, 15-Min-Takt) ausgelöst,
NICHT wenn du selbst im Signale-/Hebel-Tab manuell "Signal berechnen"/"Jetzt
analysieren" klickst — dann siehst du das Ergebnis ja bereits live vor dir,
eine zusätzliche Mail wäre redundant. Gleiches Prinzip wie bei MS-1b (auch
dort löst nur der automatische `marktscan_job()`-Lauf eine Mail aus, nicht
der manuelle "Kaufkandidaten aktualisieren"-Button).

**Bitpanda-Listing-Filter (Schalter im Menü "Benachrichtigungen"):**
"E-Mail-Empfehlungen nur für Bitpanda-gelistete Assets", Standard AN — da
die Ausführung ohnehin nur über die Bitpanda-App erfolgt, wäre eine
Empfehlung für ein dort nicht gelistetes Asset nicht direkt umsetzbar.
Anders als Dark Mode **sofort wirksam ohne Neustart** (in
`data/settings.json`, wird erst beim tatsächlichen Mailversand gelesen).
Schlägt der Bitpanda-Listing-Abruf fehl, wird bewusst NICHT blockiert
(P-10: lieber eine Mail zu viel als eine verlorene Empfehlung).

**Schalter:** `config.yaml benachrichtigung.email.empfehlungen_aktiv`
(zusätzlich zum globalen `benachrichtigung.email.aktiv`, gleiches Muster
wie `marktscan.benachrichtigung_email` bei MS-1b).

**Bewusst zurückgestellt:** eine gebündelte Tages-/Wochen-Zusammenfassung
mit Performance-Rückblick (Backward-Tracking, `agent/krypto/
backward_tracking.py`) wäre reizvoll, aber die Datenlage ist aktuell noch
zu dünn für eine aussagekräftige Auswertung (Stand 2026-07-14: von 30
Signalen haben 25 den Status "nicht_anwendbar", 0 haben tatsächlich
Take-Profit/Stop-Loss erreicht) — wird revisitiert, sobald mehr echte
Outcome-Daten vorliegen. Außerdem gilt Backward-Tracking bisher NUR für
Spot-Signale, nicht für Hebel.

### Cerebras-Stunden-Rate-Limit + manueller Signale-Fallback (2026-07-14)

**Realer Vorfall am Notebook:** an einem Tag mit ungewöhnlich hoher Auslastung
(komplette Hebel-Roadmap live entwickelt+getestet, plus normaler 15-Min-Takt)
fiel Groqs Tageskontingent nachmittags komplett aus (jeder Call schlug fehl —
erwartetes Verhalten, `taegliches_budget_gesamt: 15` ist ja an Groqs realer
Kapazität ausgerichtet). Dadurch musste **Cerebras faktisch die gesamte
restliche Tageslast tragen statt nur gelegentlichen Überlauf** — und geriet
dabei selbst in echte 429-Fehler, obwohl das Tageskontingent (~166 Calls/Tag)
bei Weitem nicht ausgeschöpft war.

**Ursache gefunden:** der Cerebras-Rate-Limiter (`api/cerebras.py`) schützte
bisher nur vor dem 5-Anfragen/Minute-Limit, nicht vor dem separaten,
ebenfalls per API-Headern bestätigten 150-Anfragen/Stunde-Limit. Bei
nachhaltig ~4 Anfragen/Min (unser eigener Minuten-Puffer) kommt man auf
240/Std. — weit über der echten Stunden-Grenze. Solange Cerebras nur
gelegentlich einspringt, fällt das nie auf; sobald es aber (wie an diesem
Tag) zur Hauptlast wird, greift die Lücke.

**Fix:** `CerebrasClient._respect_rate_limit()` hat jetzt **zwei** parallele
Sliding-Windows (Minute UND Stunde, `RATE_LIMIT_PER_HOUR = 140`, Puffer unter
dem echten 150/Std.-Limit) — analog zum bestehenden Minuten-Fenster. Gilt
automatisch für alle Aufrufer (Budget-Allocator, Hebel-Tab-Button, Marktscan-
Writeups), da alle dieselbe `CerebrasClient`-Instanz aus `main.py` teilen.

**Zweiter, dabei gefundener Fund:** sowohl der manuelle "Signal berechnen"-
Button als auch der Batch-Button ("Fällige Signale jetzt berechnen") im
Signale-Tab hatten — anders als der Hebel-Tab's "Jetzt analysieren"-Button
und der automatische Budget-Allocator — **gar keinen Cerebras-Fallback**,
ein Rest aus der Zeit vor Cerebras (Phase 4). Ein manueller Klick brach
dadurch hart mit dem rohen Groq-429-Fehler ab, selbst wenn Cerebras noch
Kapazität gehabt hätte. Beide jetzt nachgezogen (`ui/signals_view.py::
_run_pipeline()` und `agent/krypto/signal_batch.py::run_signal_batch()`,
identisches Groq-dann-Cerebras-Muster wie im Hebel-Tab — beim Batch **pro
Asset einzeln entschieden**, kein gemeinsamer "Groq ist heute tot"-
Kurzschluss für den ganzen Lauf). Damit haben jetzt alle drei manuellen
KI-Auslöser (Einzel-Klick, Batch, Hebel) sowie der automatische Allocator
denselben Fallback — volle Konsistenz.

**Wichtig zu wissen:** wenn bei einem Kandidaten sowohl Groq als auch
Cerebras scheitern, wird in diesem Zyklus einfach nichts geschrieben (auch
kein HALTEN-Platzhalter) — kein dauerhafter Datenverlust, der Kandidat gilt
weiterhin als "fällig" und wird beim nächsten 15-Min-Zyklus automatisch
erneut versucht. Die Konsequenz ist Verzögerung, nicht Verlust.

### Gemini als dritte Fallback-Stufe + echte Tages-Zähler (2026-07-14)

**Qualitätsvergleich Groq/Cerebras/Gemini** (zwei echte Testrunden gegen
dieselben Assets) ergab: Gemini liefert am vollständigsten (immer Entry/
Stop/Take-Zonen, auch bei HALTEN), hat aber einen echten Halluzinations-Fund
(ETH-spezifischer Text tauchte in einer SEI-Analyse auf). Cerebras war 2/2
mal aggressiver als der Konsens der anderen beiden. Ohne Backward-Tracking-
Historie lässt sich die Reihenfolge nicht weiter optimieren — Gemini wird
deshalb als **dritte, letzte Stufe** ergänzt: **Groq → Cerebras → Gemini**,
nach Reife/Vertrauen sortiert, nicht nach roher Kapazität (Gemini hätte mit
Abstand die größte Kapazität, ist aber am wenigsten erprobt).

**Halluzinations-Absicherung:** eine neue Prüfung
(`agent/krypto/analyst.py::_pruefe_kreuzkontamination()`, identisch in
`hebel_analyst.py`) erkennt, wenn eine Antwort für ein Nicht-BTC/ETH-Asset
den Begriff "Boden-Zielzone" erwähnt — dieses Feature wird im Facts-JSON
NUR für BTC/ETH überhaupt mitgeschickt, jede Erwähnung bei einem anderen
Symbol ist also garantiert erfunden. Löst automatisch denselben Retry aus
wie kaputtes JSON (Korrektur-Hinweis ans Modell). Bewusst nur dieser eine,
konkret beobachtete Begriff — ein breiterer "andere Symbole erwähnt"-Filter
hätte legitime Vergleiche ("ähnlich wie bei BTC") fälschlich abgewiesen.

**Echter Tages-Zähler-Fix (Kern-Prinzip: "eine KI darf nicht durch einen
eigenen Buchführungsfehler sterben"):** Cerebras' bisheriger "Tagesbudget"-
Zähler war eine lokale Variable, die bei **jedem** 15-Min-Lauf auf 0
zurückgesetzt wurde — da ein einzelner Lauf maximal `taegliches_budget_
gesamt` (~15) Kandidaten verarbeitet, konnte die 60er-Grenze nie erreicht
werden, die Tagesobergrenze wirkte also nie wirklich. Neue Funktion
`database/db.py::count_real_llm_calls_today_by_provider()` zählt jetzt
**echt** über alle drei Tiers (Hebel/Spot/Marktscan-Tabellen) hinweg, seit
Mitternacht UTC — dafür bekam `marktscan_candidates` eine neue `llm_model`-
Spalte (fehlte bisher als einzige der drei Tabellen). Gilt jetzt genauso für
Gemini (`gemini_taegliches_budget: 200`, config.yaml) wie für Cerebras.

**Integration:** wie beim Cerebras-Fix an allen vier Stellen ergänzt (Budget-
Allocator automatisch, Hebel-Tab-Button, Signale-Einzel-Button, Signale-
Batch-Button) — volle Konsistenz. `GEMINI_API_KEY` optional (P-8), ohne Key
bleibt die Kette bei Groq→Cerebras wie zuvor.

### Agent-Pipeline ("Signal berechnen") im Detail

Zwei unterschiedliche Fehlerklassen: **(a) Groq liefert ungültiges/kaputtes JSON**
— sauberer, automatischer Fallback auf HALTEN mit erklärendem Grund, kein Absturz,
Signal wird trotzdem gespeichert. **(b) Echter Netzwerkausfall von Groq selbst**
(Server down, Timeout) — **kein** Fallback, der rohe Fehlertext erscheint in der
Status-Zeile, es wird nichts gespeichert. Ausfälle aller anderen Datenquellen
innerhalb der Pipeline (CoinGecko/Kraken/FRED/Bitpanda-Listing) sind dagegen
durchgehend nach dem P-10-Prinzip abgesichert — ein Ausfall degradiert nur den
jeweiligen Fakt auf `null`, ohne die Pipeline abzubrechen.

### Watchdog + Tray-Monitor (2026-07-13) — sichtbarer Status, einfacher Start/Stop

**Auslöser:** Am 24/7-Notebook war die GUI über Nacht verschwunden, während
Scheduler und Agent im Hintergrund unbeeindruckt weiterliefen — **kein
einziger Fehler** stand in `data/tradinginfotool.log`. Da `main.py`s
`finally: bg_scheduler.shutdown(...)` direkt nach `app.mainloop()` läuft, hätte
ein echter Absturz auch den Scheduler mit heruntergefahren. Die wahrscheinlichere
Erklärung: der Tk-Mainloop ist eingefroren/unsichtbar geworden (Display-Sleep,
Tcl-Hänger o. ä.), und eventuelle Fehlerausgaben landeten im Leeren, weil beim
Start per Verknüpfung keine Konsole angehängt ist (Tkinters Standard-Callback-
Exception-Handling schreibt nur nach `stderr`).

**Bewusst KEIN Windows-Service mit Auto-Restart** (Nutzer-Entscheidung): ein
kaputter Auto-Restart-Loop wäre selbst ein stilles Fehlerbild, der Mensch soll
in der Schleife bleiben. Stattdessen: ein separater **Watchdog-Prozess**
(`monitor/watchdog.py`), der `main.py` als Kindprozess startet und unabhängig
davon überwacht — ein Tray-Icon im selben Prozess wie ein hängender Tk-Mainloop
wäre im schlimmsten Fall selbst mitbetroffen.

**Funktionsweise:**
- `ui/app.py::_poll_prices()` (bestehender 3-Sekunden-Tick) schreibt bei jedem
  Durchlauf einen Zeitstempel nach `data/gui_heartbeat.txt` — feuert nur, wenn
  der Tk-Event-Loop tatsächlich pumpt, beweist also "Fenster reagiert" statt
  nur "Prozess existiert".
- `TradingInfoToolApp.report_callback_exception()` routet Tk-Callback-
  Exceptions zusätzlich durch `logging` (landet in `tradinginfotool.log`).
- Der Watchdog startet `main.py` per `subprocess.Popen(..., stdout=crash_log,
  stderr=crash_log)` — alle bisher unsichtbaren Ausgaben landen jetzt in
  `data/watchdog_crash.log` (append, einfache 2-MB-Größenbremse statt echter
  Rotation).
- **Tray-Icon-Farben:** grau = startet gerade (erste 60s nach Spawn) /
  🟢 grün = läuft normal / 🟡 gelb = Heartbeat seit >30s veraltet (möglicher
  Hänger, Prozess aber noch da) / 🔴 rot = Prozess beendet.
- **Tray-Menü (Rechtsklick):** "Fenster anzeigen" (holt das bestehende
  Tk-Fenster per Windows-API in den Vordergrund, OHNE `main.py` neu zu
  starten — passt zum Fall "Fenster nur unsichtbar/minimiert/verschoben",
  fällt auf einen echten Neustart zurück, falls kein Fenster-Handle mehr
  gefunden wird), "Status-Details" (öffnet die bestehende Remote-Steuer-Seite,
  Abschnitt 13, lokal auf `127.0.0.1:8765`), "Neu starten" (beendet + startet
  `main.py` komplett neu, für einen echten Absturz/Hänger), "Beenden"
  (beendet `main.py` und den Watchdog selbst).
- **Stop-Mechanismus bewusst einfach gehalten:** `terminate()` (kein
  Graceful-Shutdown-Signal) — vertretbar, da die App durchgängig
  Connection-per-Call statt langlebiger DB-Transaktionen nutzt.
- Einfache PID-Datei (`data/watchdog.pid`) verhindert einen versehentlichen
  zweiten Start (zwei `main.py`-Instanzen würden sich um dieselbe SQLite-Datei
  und Port 8765 streiten).

**Einmaliges Setup pro Gerät** (nicht Teil des USB-Syncs, da der
Windows-Desktop-Ordner nicht mitgenommen wird):
```
powershell -ExecutionPolicy Bypass -File monitor\create_shortcut.ps1
```
Legt zwei identische Verknüpfungen `TradingInfoTool.lnk` an — auf dem
Windows-Desktop UND im Start-Menü (startet jeweils `pythonw.exe
monitor\watchdog.py`, kein Konsolenfenster). Die Start-Menü-Verknüpfung lässt
sich per Rechtsklick → "An Taskleiste anheften" dauerhaft in der Taskleiste
verankern (native Windows-Funktion, kein zusätzlicher Code nötig).

**Bekannte Grenze (bewusst so belassen für v1):** kein automatischer
Neustart bei einem echten Hänger/Absturz — der Nutzer muss den gelben/roten
Tray-Status selbst bemerken und "Neu starten" klicken. Ein möglicher
Folgeschritt wäre ein lokaler `/api/shutdown`-Endpoint auf der bestehenden
Remote-Seite für ein saubereres Stop-Signal statt `terminate()`.

### Empfehlung für den nächsten Schritt

Die drei ungeschützten Start-Schritte sind seit 2026-07-12 abgesichert (siehe
oben), ebenso der sofortige erste Preis-Lauf und der staleness-bewusste
Sofort-Trigger für die Kurs-/OHLC-Historie-Jobs nach jedem Neustart (siehe
"Verhalten nach längerer Downtime"). E-Mail-Benachrichtigung bei Start-Fehlern
und Job-Ausfällen (U-8) sowie bei Marktscan-Kaufkandidaten (MS-1b) ist seit
2026-07-12 erledigt, ebenso der Job-Ausfall-Backoff (siehe "Scheduler-Jobs"
oben) — damit ist die komplette Betriebssicherheits-Liste aus diesem Kapitel
abgearbeitet. Die aggregierte Status-Übersicht selbst ist inzwischen Teil der
Remote-Steuer-Seite geworden (Abschnitt 13). Neu hinzugekommen (2026-07-13):
Watchdog + Tray-Monitor für einfachen Start/Stop/Status vom Windows-Desktop
aus (siehe oben) — der eigentliche Live-Test am 24/7-Notebook steht noch aus.

### Bugfix: yfinance-Kursabrufe blockierten Prozess-Ende + Scheduler-Start (2026-07-15)

Beim echten Notebook-Test hing die App beim Start dauerhaft im gelben
("stale") Tray-Status. Ursache: `api/yfinance_client.py` und
`api/yfinance_history.py` schützten haltlose Yahoo-Finance-Aufrufe bisher je
mit einem eigenen `concurrent.futures.ThreadPoolExecutor(max_workers=1)` +
`shutdown(wait=False)`. Zwei echte Probleme dabei:

1. **Prozess-Ende blockiert:** `ThreadPoolExecutor`-Worker sind nicht
   daemonisch, und Python registriert global (unabhängig vom `shutdown()` der
   einzelnen Instanz) einen `atexit`-Hook, der beim Interpreter-Ende ALLE
   jemals erzeugten Executor-Threads joint — ein einzelner hängender
   Yahoo-Finance-Call blockierte dadurch das komplette Prozess-Beenden/
   Neustarten. Real reproduziert: alter Code hing trotz `shutdown(wait=False)`
   und abgelaufenem Timeout exakt so lange wie der simulierte Hänger.
2. **Scheduler-Start wirkte hängengeblieben:** die Wertpapier-Preise wurden
   sequenziell abgerufen, jedes Symbol mit eigenem bis zu 15s-Timeout — bei
   mehreren gleichzeitig unerreichbaren Symbolen (z. B. Yahoo Finance vom
   Notebook-Netzwerk aus nicht erreichbar) summierte sich das auf N × 15s.

**Fix:** neue Funktion `run_with_daemon_timeout()` (`api/yfinance_client.py`)
nutzt einen echten `threading.Thread(daemon=True)` statt eines Executors —
Daemon-Threads werden beim Interpreter-Exit nicht gejoint, sondern abrupt
beendet. `fetch_price_snapshots()` ruft zusätzlich alle Assets PARALLEL ab
(ein Daemon-Thread je Asset) mit einer GEMEINSAMEN Gesamt-Deadline statt
einer Summe von Einzel-Timeouts — Gesamtlaufzeit bleibt dadurch bei ca. 15s,
unabhängig von der Anzahl betroffener Assets. `api/yfinance_history.py`
(identisches Muster dort dupliziert) nutzt jetzt denselben
`run_with_daemon_timeout()`-Helper.

---

## 13. Remote-Steuer-Seite — Status + Aktionen von unterwegs über Tailscale

**Zweck (2026-07-11, direkter Anschluss an Abschnitt 12):** löst zwei der dort
genannten Lücken — kein Weg, unterwegs auf Probleme zu reagieren, und Fehler
nur über die schwer auffindbare Logdatei sichtbar. Voraussetzung: Tailscale
(privates Mesh-VPN, siehe `Basisinfos/Tailscale-Setup-Anleitung.md`) zwischen
Notebook und Handy eingerichtet.

**Was die Seite zeigt/kann:** Portfolio-Gesamtwert, Anzahl veralteter Preise,
letzter Marktscan (Kandidaten/Treffer), das gemeinsame LLM-Tagesbudget
(Hebel/Marktscan/Spot-Rotation, siehe Abschnitt 14 „Hebel-Trading“ →
Budget-Allocator) mit Aufteilung je Verbraucher, die letzten Fehlerzeilen aus
dem Log — plus drei Aktions-Buttons: **„Preise aktualisieren“** (Krypto +
Aktien/ETF/Rohstoffe zusammen), **„Marktscan jetzt starten“** und **„App neu
starten (erzwingen)“**. Backward-Tracking bleibt bewusst ohne eigenen Button
(selten zeitkritisch), ein Bitpanda-Sync-Button wäre durch den echten
authentifizierten API-Call sensibler — beides kann später nach demselben
Muster ergänzt werden.

**Neustart-Bruecke zum Watchdog (2026-07-14):** `main.py` kann sich nicht
selbst neu starten — ein hängender Tk-Mainloop kann sich nicht selbst
beenden. Der Neustart-Button auf der Remote-Seite schreibt deshalb nur eine
Flag-Datei (`data/watchdog_restart_requested.txt`), die der separate
Watchdog-Prozess (Abschnitt 12) in seinem ohnehin laufenden 5-Sekunden-Takt
aufgreift und ausführt — kein neuer Netzwerk-Port, keine neue Auth (nutzt den
bestehenden Zugriffs-Token dieser Seite). Der Button fragt vorher per
Bestätigungsdialog nach, da ein Neustart eine gerade laufende Analyse/
Marktscan mitten drin abbricht. **Bekannte Grenze:** ist der Watchdog-Prozess
selbst tot (nicht nur `main.py`), greift auch diese Brücke nicht — dann hilft
nur physischer Zugriff oder ein Notebook-Neustart.

**API-Status-Karte (2026-07-15):** nach den echten Vorfällen (Groq-429-
Erschöpfung, Cerebras-Ausfälle, yfinance-Hänger am Notebook) zeigt eine neue
Karte für **alle 19 externen Quellen** (LLM-Anbieter, Markt-/Preisdaten,
Makro/On-Chain/Derivate), ob der jeweils letzte echte Aufruf erfolgreich war
oder fehlschlug — inkl. Zeitpunkt. Rein **passiv**: es wird nichts zusätzlich
angefragt (kein zusätzliches Kontingent-Risiko bei den LLM-Anbietern), nur
aufgezeichnet, was die App ohnehin schon tut. Umgesetzt über einen Decorator
(`database/api_health.py::track_api_health()`), der an der jeweils schmalsten
bestehenden Funnel-Stelle jeder Quelle angebracht ist (z. B. `GroqClient.
chat()`, `CoinGeckoClient._get()`) — verändert nie Rückgabewert oder
Exception-Typ des eigentlichen Aufrufs. Eine Quelle, die noch nie aufgerufen
wurde, erscheint als „unbekannt" statt als Fehler.

**Technisch:** eingebettet in `main.py` als Hintergrund-Thread (`remote/server.py`,
Flask) — kein separater Prozess, läuft im selben Prozess wie die Tkinter-App
und der Scheduler, nutzt dieselben bereits vorhandenen Verbindungen. Ohne einen
gesetzten `REMOTE_ACCESS_TOKEN` (`.env`) bleibt die Seite komplett deaktiviert,
kein lauschender Port (P-8).

**Absicherung, zwei Schichten:** (1) nur innerhalb des Tailscale-Netzes
erreichbar, (2) zusätzlich ein geheimer Zugriffs-Token wie ein API-Key. Ein
Klick auf einen Aktions-Button startet den jeweiligen Job im Hintergrund und
antwortet sofort — die Seite fragt danach alle paar Sekunden den Status ab,
bis der Job fertig ist (kein langes Warten auf eine einzelne Antwort, wichtig
bei wackliger Mobilfunkverbindung).

**Doppelte Läufe ausgeschlossen:** jeder Job (Preise/Marktscan) hat eine
eigene Sperre, geteilt zwischen dem normalen automatischen Takt (Abschnitt 6)
und der Remote-Seite — ein manueller Klick kann einen bereits laufenden Job
also nie doppelt anstoßen.

**Not-Reset bei einem hängenden Job:** läuft ein Job ungewöhnlich lange (die
Seite zeigt „läuft seit X Min“), blendet sie einen „Zurücksetzen“-Button ein.
**Wichtig zu wissen:** das gibt nur die interne Sperre frei, damit ein neuer
Versuch möglich ist — es beendet nicht zwingend den ursprünglich hängenden
Hintergrund-Vorgang selbst. Bewusst als Not-Funktion gekennzeichnet, nicht für
den Alltag gedacht.

**Dabei gefundener und behobener Fehler:** `api/yfinance_client.py` (Kursquelle
für Aktien/ETF/Rohstoffe) hatte als einzige Netzwerk-Quelle im Projekt keinen
kontrollierten Timeout — ein hängender Yahoo-Finance-Aufruf hätte die neue
Sperre dauerhaft blockiert. Jetzt mit einem harten 15-Sekunden-Timeout
versehen, unabhängig von der Steuer-Seite ein eigenständiger Zuverlässigkeits-
Gewinn.

**Erreichbar unter:** `http://notebook.<dein-tailnet>.ts.net:8765/?token=DEIN_TOKEN`
(Details/Ersteinrichtung siehe `Basisinfos/Tailscale-Setup-Anleitung.md`).

---

## 14. Portfolio-Vollständigkeit — Cash-Sperren, Staking, Margin-Trading

**Zweck (2026-07-11, Nutzer-Fund):** eine Nachfrage zur Cash-Reserve-Anzeige
deckte auf, dass der von der App gesehene Portfoliowert deutlich kleiner war als
der tatsächliche (Bitpanda selbst zeigte 15.694,69 €, die App kam nur auf
9.934,31 € — eine Lücke von ca. 5.760 €, rund 37 % des echten Vermögens). Diese
Sektion hält fest, was die Lücke verursacht hat, was schon behoben ist, und was
bewusst offen bleibt.

### Gefundene Ursachen, im Detail geprüft

| Ursache | Betrag (Live-Test) | Status |
|---|---|---|
| In offener Bitpanda-Fusion-Limit-Order gebunden ("Committed Balance") | ~188 € | Erkannt + dokumentiert; RM-4 rechnete schon immer korrekt (siehe unten), Aktualität jetzt zusätzlich per automatischem Sync abgesichert |
| Aktuell gestakte Krypto-Bestände (ETH, SOL, AVAX, SUI, TAO, HYPE, NEAR, SEI, BNB) | ~2.435 € | **Behoben** — Anzeige (Portfolio-Tab, Remote-Seite) UND `risk_gate.py` (ETH-Ausnahme, siehe unten) |
| PLTR/VST: yfinance liefert nur USD, keine EUR-Umrechnung | ~660 € | **Behoben** |
| Historische, aktuell nicht offene Margin-/Hebel-Trading-Aktivität (Krypto) | — | Kein Handlungsbedarf (aktuell keine offene Position, Nutzer bestätigt) |
| Zwei offene Margin-Positionen in anderen Assetklassen | — | Bewusst außerhalb des Tool-Scopes |

### Committed Balance (offene Fusion-Orders)

Bitpanda sperrt den für eine offene Limit-Order benötigten Betrag sofort aus dem
Wallet-Guthaben (offiziell dokumentiert in den Bitpanda-Fusion-Terms als
"Committed Balance") — unsere `/fiatwallets`-Abfrage liefert bereits den
**bereinigten, wirklich freien** Betrag, das ist für RM-4 (Cash-Reserve-Minimum)
die korrekte, sicherheitsseitig richtige Zahl. Das Problem war nur, dass die
App nicht erkennen ließ, ob dieser Wert *aktuell* ist. **Behoben (2026-07-11):**
`database/db.py::get/set_cash_reserve_synced_at()` + neues Label im Portfolio-Tab
("Bitpanda-Sync: vor X Min") — bewusst OHNE Stale-Färbung wie bei Preisen, da ein
manueller Sync normalerweise stundenlang zurückliegt, ohne dass etwas falsch ist.

**Klargestellt (2026-07-11): keine Schätzung des gesperrten Betrags nötig.** Eine
ursprünglich angedachte Herleitung aus der Transaktionshistorie (Cash-Delta minus
sichtbare Trades/Transfers) erübrigt sich — `/fiatwallets` liefert den gesperrten
Betrag serverseitig bereits korrekt heraus, das war für RM-4 nie das Problem.
**Stattdessen umgesetzt: automatischer Sync alle 30 Minuten**
(`scheduler/background.py::refresh_bitpanda_cash_job`, neue Funktion
`importer/bitpanda_sync.py::sync_fiat_cash_from_bitpanda()`, aus dem bestehenden
manuellen Sync extrahiert) — damit RM-4 nie länger als eine halbe Stunde auf
einem veralteten Cash-Stand rechnet, ohne dass dafür die vollen Bestände
automatisch mitlaufen müssen (siehe Kap. 6). Details/Verifikation: Memory
`project-portfolio-vollstaendigkeit-cash-staking`.

### Staking-Sichtbarkeit

Gestakte Bestände sind über die normalen Bitpanda-Wallet-Endpunkte strukturell
unsichtbar (bereits länger bekannt, siehe `[[project-bitpanda-exchange]]`) — neu
ist, dass sich das jetzt **automatisch aus der Transaktionshistorie berechnen**
lässt, ohne eine eigene Order-API zu brauchen: jeder "stake"-Transfer bucht die
Menge aus der normalen Wallet ab, jeder "unstake"-Transfer wieder zu — der
verbleibende, noch nicht zurückgeholte Rest ist die aktuell gestakte Menge.

**Umgesetzt (2026-07-11):** `importer/bitpanda_avg_cost.py::compute_staked_quantities()`
läuft automatisch bei jedem "Einstandspreise berechnen"-Sync mit (kein
zusätzlicher API-Aufruf, nutzt dieselben bereits geladenen Transaktionen), neue
Spalte `holdings.staked_quantity`. Portfolio-Tab und Remote-Steuer-Seite zeigen
den gestakten Anteil jetzt separat ausgewiesen im Gesamtwert.

**Jetzt auch in `risk_gate.py` berücksichtigt (2026-07-11, eigene Planungs-
Session).** Die zunächst bewusst zurückgestellte Einbindung (RG-6-unantastbare
Datei) wurde nachgeholt: `_portfolio_values_usd()` zählt `staked_quantity`
seitdem additiv zu `quantity` — sowohl in die Gesamtwert-Basis (RM-1/RM-2) als
auch, für Stablecoins, automatisch in die Cash-Reserve (RM-4), da der
bestehende Stablecoin-Filter dieselbe erweiterte Zahl liest. **Eine
Ausnahme:** ETH ist laut Nutzer-Erfahrung der einzige Bitpanda-Staking-Fall,
bei dem Un-/Restaking bisher nicht instant möglich war (alle anderen bisher
gestakten Assets waren es) — ETH-Staking bleibt deshalb konservativ (Z-1) von
der Risikoberechnung ausgeschlossen (`STAKING_ILLIQUID_SYMBOLS`-Konstante in
`risk_gate.py`), mit einer sichtbaren Hinweiszeile im Check-Protokoll. Live
gegen die echte DB verifiziert: Gesamtwert-Basis stieg um ~1.949 USD (die
gestakten Nicht-ETH-Bestände), die ~832 USD gestaktes ETH blieben korrekt
außen vor.

### Margin-/Hebel-Trading — Rahmenbedingungen jetzt vollständig entschieden (2026-07-14)

**Status: komplett fertig.** Alle sechs Phasen (Screening, Risiko-/
Liquidationsformeln, Positions-Rekonstruktion, Cerebras-Anbindung +
KI-Empfehlung, Budget-Allocator, UI-Tab) sind gebaut und gegen echte Daten
verifiziert. Hebel-Empfehlungen laufen vollautomatisch im 15-Min-Takt, mit
demselben Tagesbudget wie Marktscan und deine Spot-Signal-Rotation, UND sind
jetzt im neuen "Hebel"-Tab in der App selbst sichtbar. Volle technische
Herleitung in `docs/hebel_positionsformel.md`, hier die für dich relevante
Zusammenfassung.

**RM-10 korrigiert:** stand bisher als "nur Long, kein Short" — das war aber
nur ein Bitpanda-Fakt (Bitpanda kann aktuell kein Short ausführen), keine
bewusste Risiko-Entscheidung gegen Short. **Short bleibt Teil der Empfehlungs-
Logik** (rein beratend wie überall sonst — der Agent führt nie selbst aus),
du bekommst also auch Short-Empfehlungen angezeigt, kannst sie aktuell nur
nicht über Bitpanda direkt umsetzen.

**Echte Bitpanda-Margin-Historie ausgewertet** (rein lesend, dieselbe API wie
beim Bestände-Abgleich): 185 vollständig geschlossene Positionen (22.09.2025
bis 07.05.2026) chronologisch rekonstruiert (Korrektur 2026-07-14: die
ursprünglich hier notierte Zahl 311 war ein Bug im ersten Auswertungs-Skript
— 126 Phantom-Einträge ohne echten Wert wurden mitgezählt; beim Bau des
richtigen, wiederverwendbaren Codes aufgefallen und korrigiert):
- Genutzter Hebel real: klare Bitpanda-Stufen 2x/3x/5x/10x, Ø 6,44x je
  Einzelkauf — **`max_hebel` deshalb von 3x auf 10x angehoben**, der alte
  Wert war niedriger als deine eigene bisherige Praxis
- Ø Haltedauer nur 1,1 Tage (Min 0, Max 16,7) — laut dir Marktreaktion, keine
  bewusste Kurzfrist-Strategie
- **4 wahrscheinliche Liquidationen erkannt**, obwohl Bitpandas API das nicht
  extra kennzeichnet — über eine Gebühren-Auffälligkeit gefunden (die
  betroffenen Closes zeigten ca. 1 Prozentpunkt mehr Gebühr als normal, exakt
  Bitpandas dokumentierte Zwangsliquidations-Gebühr). Bewusst **keine
  Testposition mit echtem Geld** eröffnet, um das weiter zu prüfen — die
  vorhandenen Daten waren überzeugend genug.

**Liquidationspreis-Formel (Schätzung, nie Bitpandas exakter Wert):**
Bitpanda veröffentlicht die genaue Formel nicht — unsere Schätzung ist bewusst
konservativ (zeigt Liquidation eher zu früh als zu spät an):
```
Long:  Liquidationspreis ≈ Entry × (1 − 1/Hebel + Tage_gehalten × 0,0018)
Short: Liquidationspreis ≈ Entry × (1 + 1/Hebel − Tage_gehalten × 0,0018)
```
Die 0,18 %/Tag-Finanzierungsgebühr lässt den Wert mit der Zeit näher rücken,
auch ohne Kursbewegung — gegen die echte Historie geprüft, passt gut (nur
0,08 Prozentpunkte Abweichung im Schnitt).

**Positionsgröße bei Hebel — eigener, niedrigerer Risikowert:** Bei Spot
riskierst du 2 % pro Trade (RM-1). Bei Hebel setzen wir das bewusst auf
**1 %** herunter — Gründe: Kurs kann in schnellen Bewegungen über den
Stop-Loss hinweg direkt Richtung Liquidation springen (Slippage), dazu
kommt die laufende Gebühr, und die 4 echten Liquidationen zeigen, dass das
kein theoretisches Risiko ist. Der gewählte Hebel wird zusätzlich so
gedeckelt, dass zwischen Stop-Loss und geschätztem Liquidationspreis immer
ein Sicherheitsabstand bleibt (15-20 %) — ein weiter Stop-Loss erlaubt also
automatisch nur einen niedrigeren Hebel.

**Automatische Positions-Verfolgung (statt manueller Bestätigung) — gebaut:**
Sobald eine Hebel-Position wirklich offen ist, erkennt die App das
**automatisch** aus deinen echten Bitpanda-Transaktionen (`importer/
bitpanda_margin_positions.py`, alle 15 Min huckepack auf dem Hebel-
Screening-Takt) — keine manuelle "ich hab's umgesetzt"-Bestätigung wie bei
Spot-Signalen nötig. Grund: bei "den fragilsten, zeitkritischsten Positionen"
(deine eigene Einordnung) ist eine vergessene manuelle Bestätigung besonders
riskant. Der geschätzte Liquidationspreis wird bei jedem Tick mit den echten
verstrichenen Tagen neu berechnet. Aktuell hast du keine offene Hebel-
Position — dieser Pfad ist gebaut und mit einer künstlichen Testposition
durchgespielt, aber noch nicht an einer echten offenen Position beobachtet.

**Zusätzliche Sicherheitsregel aus AZ-7:** in einem Extrem-Krise-Regime wird
Hebel komplett deaktiviert, unabhängig von der reinen Rechnung; ansonsten
tendiert die Empfehlung zum unteren Ende des sicher berechneten Hebel-
Korridors statt zum Maximum.

**KI-Empfehlung selbst (Cerebras + Analyst) — gebaut:** aus einem
Screening-Kandidaten wird jetzt eine vollständige Empfehlung mit Begründung,
Kurszonen, Hebel-Vorschlag und Halte-Kriterium (gleicher Aufbau wie bei
Spot-Signalen, plus Hebel-spezifische Felder wie "Einmal-Trade vs.
Swing-Strategie"). Läuft über Cerebras (zweite, kostenlose KI-Ebene neben
Groq) statt über dein bestehendes Groq-Tagesbudget, damit die Hebel-
Empfehlungen die knappe Spot-/Marktscan-Kapazität nicht verdrängen. Dein
gewählter Hebel-Vorschlag wird - wie überall im System - nie blind
übernommen: die Sicherheitsregeln oben (Liquidations-Sicherheitsmarge,
Extrem-Krise-Deaktivierung) werden danach nochmal deterministisch erzwungen.
Echt gegen die Produktions-DB getestet: für AIOZ (ein automatisch erkannter
Short-Kandidat) kam eine vollständige, plausible Empfehlung heraus (Short-
Eröffnung, 5-facher Hebel, Kurszonen samt Liquidationspreis-Schätzung).

**Budget-Allocator — gebaut:** entscheidet jetzt automatisch, wann welcher
Kandidat (Hebel/Marktscan/Spot-Rotation) eine echte KI-Analyse bekommt,
verteilt über euer gemeinsames Tagesbudget (siehe
`docs/budget_queue_design.md`) - läuft huckepack auf dem 15-Min-Hebel-
Screening-Takt. Der fixe tägliche 05:00-Uhr-Job für Spot-Signale ist damit
entfallen (der Allocator übernimmt Spot-Rotation jetzt viel häufiger mit),
der manuelle "Fällige Signale jetzt berechnen"-Button bleibt trotzdem
bestehen. Wichtiger Fund dabei: Cerebras (deine zweite, kostenlose KI-Ebene)
hat ein echtes, deutlich größeres Tageslimit als bisher angenommen (~166
statt Groqs ~15-18 Analysen/Tag) - Hebel-/Marktscan-/Spot-Empfehlungen
können dadurch bei Bedarf automatisch auf Cerebras ausweichen, ohne dein
Groq-Kontingent zu belasten.

**Neuer "Hebel"-Tab in der App — gebaut:** zeigt die zuletzt berechnete
Empfehlung je Symbol (gleicher Aufbau wie der Signale-Tab), noch nicht
analysierte Screening-Kandidaten (optisch abgesetzt, mit einem "Jetzt
analysieren"-Button für den sofortigen manuellen Einzel-Wunsch), sowie ein
kompaktes Panel mit deinen aktuell offenen Hebel-Positionen. Damit ist die
komplette Hebel-Roadmap (alle 6 Phasen) abgeschlossen.

---

## 15. Offene / vorläufige Werte — die naheliegendsten Kandidaten für spätere Anpassung

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
- RM-10 max. Hebel (10x, 2026-07-14 gegen echte Bitpanda-Historie kalibriert,
  aktuell ohnehin deaktiviert) — Liquidations-Sicherheitsmarge (15-20 %, Mitte
  0,175 als Startwert) und die Hebel-Trigger-Schwellenwerte selbst (OI-Änderung
  ±3 %, Kursänderung ±2 %, Long-Anteil 75 %/25 %) sind noch unbestätigte
  Platzhalter, siehe `docs/hebel_positionsformel.md`
- **NEU (2026-07-11):** die ETH-Ausnahme in `risk_gate.py`
  (`STAKING_ILLIQUID_SYMBOLS`, siehe Kap. 14) beruht auf einer einzelnen
  Nutzer-Erfahrung, nicht auf einer systematischen Prüfung aller Bitpanda-
  Staking-Produkte — bei künftigen neuen gestakten Assets prüfen, ob die Liste
  erweitert werden muss.
- **ERLEDIGT, war hier gelistet (2026-07-11):** eine Schätzung des in offenen
  Fusion-Orders gebundenen Cash-Betrags erwies sich als unnötig — `/fiatwallets`
  liefert den korrekten, bereinigten Betrag bereits serverseitig; gelöst wurde
  stattdessen die Aktualität per automatischem 30-Minuten-Sync (Kap. 6/14).
- **ERLEDIGT, Design UND Code (2026-07-14):** RM-10/RM-11 (Hebel) Positions-
  Rekonstruktion aus den `margin_trading.*`-Transaktions-Tags (Kap. 14) —
  Logik gegen 185 echte historische Positionen (korrigierte Zahl, siehe dort)
  erfolgreich getestet, läuft automatisch alle 15 Min. Aktuell keine offene
  Position zum Live-Beobachten.
- **NEU (2026-07-12):** Boden-Zielzone (Abschnitt 4, `config.yaml
  boden_zielzone:`) — `reifegrad_daempfer_staerke` (0,15), `equities_baermarkt_
  schwelle_prozent` (20), `equities_baermarkt_lookback_jahre` (5),
  `equities_overlay_shift_std` (0,2) sind erste plausible Startwerte, noch nicht
  gegen echte Ergebnisse validiert. `equities_baermarkt_verknuepfung: entweder`
  ist dagegen eine bewusste, feste Nutzer-Entscheidung (kein `[OFFEN]`).
- **NEU (2026-07-15):** `budget_allocator.spot_cooldown_stunden` (20 Std.,
  Kap. 6) — erster plausibler Startwert für den neuen Spot-Rotation-Cooldown
  (< 24 Std., damit die tägliche Rotation nicht durch feste Tick-Zeiten
  driftet), noch nicht gegen mehrere Tage echten Betrieb verifiziert.
- **NEU (2026-07-16):** `budget_allocator.spot_cooldown_stunden_kern` (10
  Std., Kap. 6) — erster plausibler Wert für die kürzere Kern-Cooldown-Stufe
  (core/gehaltene Assets), ebenfalls noch nicht über mehrere Tage echten
  Betrieb verifiziert.
- **NEU (2026-07-16):** Hebel hat noch keine "Signal-Historie"-Ansicht
  analog zum Signale-Tab (Kap. 7) — die neue Überholt-Erkennung schreibt den
  Status zwar korrekt in `hebel_signals.outcome_status`, ist aber im
  Hebel-Tab aktuell nirgends sichtbar (nur über eine direkte DB-Abfrage).

---

## 16. Multi-Asset-Erweiterung — Aktien-Agent-Pipeline Phase 1 (2026-07-15)

**Hintergrund:** Non-Krypto-Assets (Aktien/ETFs/Rohstoffe) hatten bisher nur
Kursanzeige — kein Regime, kein Risiko-Gate, keine KI-Empfehlung. Nach der
Non-Krypto-Margin-Recherche (RM-10/11 lässt sich für Aktien/ETFs technisch
NICHT rekonstruieren, siehe Kap. 14 — Bitpanda-API bietet dafür keine
Transaktionshistorie an) hat der Nutzer stattdessen entschieden, das größere
Thema anzugehen: eine echte Agent-Pipeline auch für diese Assetklassen, mit
Marktscan-Äquivalent als Fernziel.

**Architektur-Entscheidung (bereits 2026-07-09 in der Spezifikation getroffen,
jetzt erstmals umgesetzt):** eigene Agent-Logik pro Assetklasse
(`agent/aktien/`, künftig `agent/etfs/`, `agent/rohstoffe/`) statt einer
verallgemeinerten Engine — vermeidet sowohl eine aufgeblähte If/Else-Kaskade
als auch einen verwässerten kleinsten gemeinsamen Nenner. Eine gemeinsame
Datenbank (`signals`-Tabelle wird direkt mitgenutzt, kein neues Schema nötig).

**Was Phase 1 umfasst (Einzelaktien PLTR/VST):**
- Neues Modul `agent/aktien/` (Analyst + Pipeline), mirror von
  `agent/krypto/`, aber mit eigenem Prompt/Schema — OHNE Bitpanda-Veto,
  TAUSCHEN-Aktion, BTC-Matrix, On-Chain-Zyklus-Risiko oder
  Funding-Rate/Open-Interest (kein Aktien-Äquivalent). Vier statt fünf
  Aktionen (kein TAUSCHEN — Aktienverkauf ist immer steuerlich relevant,
  anders als der österreichische Krypto-zu-Krypto-Tausch).
- **Wiederverwendet direkt, kein Duplikat:** `agent/krypto/risk_gate.py`
  (RM-1/RM-2/RM-4/RM-5-Mathematik ist bereits assetklassen-neutral; der
  Bitpanda-Veto war anfangs auf `assetklasse == "krypto"` beschränkt — als
  echte Lücke erkannt und am 2026-07-16 behoben, siehe Nachtrag unten),
  `agent/krypto/pipeline.py::compute_current_regime()` (liefert
  Liquiditäts-Regime + Aktien-Bärenmarkt-Overlay als Nebenprodukt der
  ohnehin nötigen BTC-Regime-Berechnung), `indicators/calculations.py`
  (bereits generisch).
- **Neu: Fundamentaldaten** (KGV, Forward-KGV, Gewinn-/Umsatzwachstum,
  Dividendenrendite, Analysten-Konsens + Kursziel, Marktkapitalisierung,
  Sektor, nächstes Earnings-Datum) über die bereits vorhandene `yfinance`-
  Abhängigkeit (`Ticker.info`/`.calendar`, bisher ungenutzt) — komplett neue
  Datenkategorie. Eigene Bewertungs-/Bubble-Risiko-Regel: **wichtige
  Nachbesserung nach dem ersten Testlauf** (Nutzer-Nachfrage "welche Regeln
  fehlen noch?") — die Regel verglich anfangs nur das trailing-KGV, ohne
  Wachstumsdaten mitzuschicken, wodurch ein echter Testlauf PLTRs hohes KGV
  fälschlich als "ohne erkennbares Wachstum" bewertete, obwohl real ein
  Gewinnwachstum von +325 %/Umsatzwachstum von +85 % vorlag. Jetzt vergleicht
  die Regel trailing- GEGEN forward-KGV UND die Wachstumsraten, bevor ein
  Bewertungsrisiko ausgesprochen wird — zweiter Testlauf bestätigt eine
  deutlich fundiertere Einordnung ("dank starkem Gewinnwachstum attraktives
  Bewertungsprofil", zusätzlich weiterhin der Blasen-Hinweis bei fehlender
  Wachstumsbestätigung). Analysten-Konsens/Kursziel fließen nur als
  niedrig gewichtete Drittmeinung ein (inkl. deterministisch vorberechnetem
  Kursziel-Potenzial in Prozent), nie als eigene Empfehlung.
- **Neu: echte OHLC-Historie** statt nur Schlusskurs — `price_history_ohlc`
  war bereits nach Symbol (nicht Coingecko-ID) geschlüsselt, also strukturell
  schon assetklassen-neutral, bisher nur von Kraken befüllt. Wird jetzt bei
  Bedarf automatisch aus derselben yfinance-Antwort befüllt, die ohnehin
  für den Schlusskurs abgerufen wird (kein zusätzlicher Netzwerk-Call).
- **Eigener, großzügigerer Staleness-Schwellenwert** für die Kurshistorie
  (5 Tage statt der Krypto-üblichen 2) — Aktienmärkte schließen an
  Wochenenden/Feiertagen, der Krypto-Schwellenwert (24/7-Handel) hätte an
  jedem Montag fälschlich "veraltet" ausgelöst.
- **Manueller Button, bewusst kein Scheduler-Automatismus** in Phase 1 (wie
  beim ursprünglichen Krypto-Aufbau) — im Signale-Tab erscheinen Aktien
  jetzt zusätzlich zu Krypto-Assets in derselben Liste, "Signal berechnen"
  verzweigt automatisch zur richtigen Pipeline.

**Live verifiziert (2026-07-15):** echter End-to-End-Lauf für PLTR und VST
gegen die Produktions-DB, inkl. echtem LLM-Call (Groq 429 korrekt auf
Cerebras abgefangen) — beide Signale korrekt mit Regime-Konfidenz-Veto
(R-5.10) auf HALTEN korrigiert, CRV-Zonen plausibel, Bewertungs- und
Earnings-Nähe-Hinweise korrekt erkannt.

**Nachtrag: zwei Lücken aus dem Asset-Verwaltungs-Audit behoben (2026-07-16).**
Der Nutzer bat um eine Prüfung, ob sich in der Asset-Verwaltung über alle
Klassen Lücken angesammelt haben, seit sich Rahmenbedingungen (Cooldowns,
Gewichtung) geändert haben. Zwei echte Fundstellen, beide sofort behoben:

1. **Kein automatischer OHLC-Refresh für Aktien.** Der tägliche Backward-
   Tracking-Job (Kap. 7) läuft automatisch über ALLE `signals`-Zeilen ohne
   Assetklassen-Filter — aber Phase 1 aktualisierte `price_history_ohlc`
   nur bei manuellem Signal-Klick (`_ensure_ohlc_backfilled()`, 5-Tage-
   Schwelle). Ein offenes PLTR/VST-KAUFEN-Signal wäre also zunehmend gegen
   veraltete Kurse geprüft worden. Fix: neuer Scheduler-Job
   `refresh_aktien_ohlc_job` (alle 24 Std., wie der Kraken-OHLC-Refresh),
   `api/yfinance_history.py::backfill_all_aktien_ohlc()`. Live gegen eine
   Kopie der Produktions-DB verifiziert: VST 2455→2456, PLTR 1452→1453
   OHLC-Punkte.
2. **Fehlender Bitpanda-Check bei Aktien.** `risk_gate.py::pre_check()`
   prüfte den Bitpanda-Veto bisher nur für `assetklasse == "krypto"` — die
   Aktien-Pipeline reichte `bitpanda_gelistet=None` hartkodiert durch, der
   Veto konnte nie auslösen. Aktuell unkritisch (alle 13 Non-Krypto-
   Einträge sind bereits bestätigt gehaltene Positionen), würde aber zum
   echten Problem sobald Phase 4 (Discovery) neue, ungeprüfte Kandidaten
   vorschlägt. Fix: neue `api/bitpanda.py::get_listed_non_crypto_assets()`
   (derselbe öffentliche `/v3/assets`-Feed wie beim Krypto-Check, live
   verifiziert: PLTR/VST als Gruppe `stock` gefunden), `pre_check()`s
   Bitpanda-Bedingung ist jetzt assetklassen-neutral. Live verifiziert
   (echte DB-Kopie, echter Bitpanda-Call): `bitpanda_gelistet=False` löst
   jetzt korrekt einen Veto aus (`kauf_erlaubt=False`), `True` lässt den
   Kauf zu, `None` wird wie zuvor übersprungen (P-10).

**Roadmap (konzeptionell, noch nicht umgesetzt):**

| Phase | Umfang | Kern-Unterschied |
|---|---|---|
| 1 (erledigt) | Einzelaktien (PLTR/VST) | Fundamentaldaten/Bewertung/Bubble-Risiko |
| 2 | Rohstoff-ETCs (Gold/Silber/Kupfer/Erdgas) | Kein KGV, sondern Angebot/Nachfrage + Zyklen/Knappheit; festes kleines Universum, keine Discovery nötig |
| 3 | Themen-ETFs (Food&Bev/Agribusiness/Bioenergy/Rare Earth/Copper Miners) | Sektor-Rotation/Themen-Zyklen |
| 4 | Discovery/Marktscan-Äquivalent | Neue Aktien/ETFs vorschlagen — braucht zuerst eine freie Screener-Datenquelle (kein CoinGecko-Äquivalent bekannt); Bitpanda-Check jetzt bereit dafür |
