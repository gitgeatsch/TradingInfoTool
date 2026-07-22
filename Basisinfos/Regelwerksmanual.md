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
| RM-3 | Max. Allokation pro Assetklasse | Krypto **100 %**, Aktien/ETF/Rohstoffe je **0 %** | **Stand 2026-07-18 veraltet:** Konfigurationswert selbst unveraendert, aber Aktien/Rohstoffe/Hedge/Themen-ETFs sind seit derselben Runde (Multi-Asset-Batch + Themen-ETF-Pipeline) aktiv im Einsatz - der Cross-Klassen-Deckel selbst wird weiterhin NICHT durchgesetzt (jede Pipeline rechnet nur gegen ihre eigene Assetklassen-Teilmenge, siehe RM-2), das ist die eigentliche offene Luecke, nicht die Frage "im Einsatz oder nicht" |
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

**Nachtrag (2026-07-17): beide RM-4-Werte bestätigt, nicht mehr `[OFFEN]`.** Nach
Rücksprache bleiben 10 %/2.000 € unverändert — bewährte Hausnummer als
Liquiditätspuffer/Overtrading-Bremse, in der Praxis bereits durch einen bewussten
zusätzlichen Cash-Puffer über dem Minimum bestätigt. **Revisit-Bedingung:** sollten
diese Werte in der Praxis einmal ein echtes Problem verursachen (zu eng oder zu
locker), erneut aufgreifen — siehe Memory
`project_portfolio_vollstaendigkeit_cash_staking.md`. Wichtig: RM-4 bleibt bewusst
getrennt vom AZ-4-Cash-Reserve-Ziel (Kap. 4) — RM-4 ist der harte Sicherheits-Floor,
das AZ-4-Ziel eine strategische Zielgröße für eine geplante Nachkaufkampagne.

**Optionaler Live-Abgleich mit Bitpanda (2026-07-10, ERGÄNZT + KORRIGIERT).** Wer
bereits einen Bitpanda-API-Key besitzt (`BITPANDA_API_KEY` in `.env`), kann über
"Datei → Bestände von Bitpanda abgleichen" **alle** Bestände (Krypto **und**
Aktien/ETF/Rohstoffe, da Bitpanda diese im selben Account führt) UND das EUR-Fiat-
Guthaben automatisch von der Börse abrufen (rein lesend — laut Bitpanda-Doku besteht
über API-Keys grundsätzlich keine Order-/Auszahlungsfähigkeit, unabhängig vom
gewählten Scope). Das manuelle Eingabefeld und der bestehende Excel-Import/Export
bleiben **vollständig als Backup** erhalten (bewusst hybrid, da Bitpanda öfter
Ausfälle hat). **Seit 2026-07-16 läuft derselbe Abgleich zusätzlich automatisch
alle 30 Minuten im Hintergrund** (Staking-Verifikation macht das sicher, siehe
Kap. 6) — der manuelle Klick bleibt für sofortige Abgleiche und als seltener
Fallback bestehen. Nach jedem Sync wird automatisch auch `Assets_export.xlsx` aktualisiert (beide Tabs), ohne die
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

**RM-1/RM-2-Obergrenze jetzt konfidenz-skaliert statt flach (2026-07-16).**
Nutzer-Beobachtung: die vorgeschlagene Positionsgröße lag empirisch fast immer
nahe der vollen RM-1/RM-2-Obergrenze, unabhängig von der tatsächlichen
Konfidenz der Empfehlung — wirkte willkürlich. Grund: die Obergrenze war ein
reiner Deckel (nie ein Zielwert), es gab aber keine Vorgabe, INNERHALB der
Obergrenze kleiner zu bleiben. Fix nach gängiger Trading-Praxis
(konviktionsgewichtete Positionsgröße/Bruchteils-Kelly-Logik): die Obergrenze
selbst skaliert jetzt linear mit `confidence_pct` zwischen einem Sockel-Anteil
(Konfidenz genau an der Regime-Mindestschwelle R-5.10, `config.yaml
risiko.konfidenz_positionsgroesse_sockel_anteil`, aktuell **50 %**) und der
vollen Obergrenze (Konfidenz 100 %). Eine Empfehlung genau an der
Mindestschwelle ist der am wenigsten überzeugende noch zulässige Fall und
bekommt entsprechend nur die Hälfte der Obergrenze; erst bei sehr hoher
Konfidenz wird die volle Obergrenze ausgeschöpft. Gilt für **Krypto UND
Aktien** (teilen sich `agent/krypto/risk_gate.py::post_check()`) — Hebel ist
NICHT betroffen, dort berechnet `hebel_risk_gate.py` die Positionsgröße
ohnehin vollständig deterministisch aus Risikobetrag/Stop-Distanz, die KI
schlägt dort nie selbst eine Positionsgröße vor. Zusätzlich bekam der
Analyst-Prompt (`agent/krypto/analyst.py` + `agent/aktien/analyst.py`) einen
Hinweis, die Obergrenze nicht als automatischen Zielwert zu behandeln — das
serverseitige Klemmen bleibt aber die verbindliche, deterministische Grenze,
unabhängig davon, was die KI selbst vorschlägt.

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
| `hebel_screening` (+ Budget-Allocator huckepack) | alle 15 Min | Hebel-Screening (Kap. 7) UND die zentrale Tagesbudget-Verteilung über drei Verbraucher: Hebel-Kandidaten (Tier 1), Marktscan-Kaufkandidaten-Begründung (Tier 2), Spot-Rotation für die am längsten überfälligen Krypto-Assets (Tier 3 — ersetzt seit 2026-07-14/Phase 5 den ehemaligen eigenen `signal_batch`-05:00-Cron) | Binance/Bybit/OKX/Kraken (Screening) + Groq→Mistral→Cerebras→Gemini (je Tier budget-limitiert, Cerebras nur bis 2026-08-17 siehe Kap. 14 Nachtrag) |
| `backward_tracking` | 1× täglich, fix 06:00 Uhr | Prüft vergangene KAUFEN/NACHKAUFEN-Signale gegen die Kurshistorie — Take-Profit oder Stop-Loss erreicht? | keine (nur bereits vorhandene DB-Daten) |
| `bitpanda_holdings` | alle 30 Min (nur mit gesetztem `BITPANDA_API_KEY`) | **Seit 2026-07-16 der komplette Bestandsabgleich** (Krypto + Aktien/ETF/Rohstoffe + EUR-Cash) — ursprünglich (2026-07-11) nur der EUR-Fiat-Cash-Anteil, siehe Nachtrag unten | Bitpanda (Wallets + Transaktionshistorie) |

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
Richtung automatisch (watchlist → aktiv) — die Rückrichtung bei
vollständigem Verkauf ist bewusst KEINE stille Automatik (siehe nächster
Nachtrag), ein Coin bleibt oft absichtlich weiter beobachtet. Isoliert per
try/except — ein Config-Schreibfehler blockiert nie den eigentlichen
Holdings-Sync. Verifiziert gegen eine Kopie der echten `config.yaml`
(BRETT watchlist→aktiv, No-Op bei bereits gesetztem Status, Nachbar-
Einträge unangetastet) — die echte Datei wurde dabei nicht berührt.

**Sicherheits-Nachprüfung (2026-07-16, Nutzer-Wunsch "prüfe ob die Änderung
keine negative Auswirkung hat").** Alle 4 Lesestellen von `.status` im
gesamten Code identifiziert — keine ist veto-/berechnungsrelevant (KI-
Kontext-Fakt, Remote-Status-Zähler, UI-Anzeigespalte). Dieselbe, bereits
etablierte Einschränkung wie bei `add_watchlist_entry()` gilt weiterhin:
die laufende App hält die Watchlist als einmaliges Snapshot beim Start
(`main.py`), eine Änderung wirkt daher erst nach einem Neustart vollständig
(Portfolio/Bestände selbst sind davon NICHT betroffen, die kommen immer
frisch aus der DB). Ein echter kleiner Fund dabei: die Sync-Erfolgsmeldung
erwähnte Status-Hochstufungen bisher gar nicht — ergänzt, inkl.
Neustart-Hinweis.

**Nachtrag: Status-Rückstufung beim Verkauf, Variante 1 umgesetzt
(2026-07-16, Nutzer-Entscheidung nach Rückfrage).** Der bestehende
`BitpandaDecreaseConfirmDialog` (Rückgangs-Bestätigung) bekommt bei einem
Rückgang auf exakt 0 eine zusätzliche, standardmäßig UNGEHAKTE Checkbox
"Watchlist-Status auch auf 'watchlist' zurücksetzen" — bewusst KEINE
automatische Rückstufung wie beim Kauf-Fall, sondern eine bewusste
Nutzer-Entscheidung im selben Moment, in dem der Verkauf ohnehin schon
bestätigt werden muss. Bestätigt der Nutzer sowohl den Rückgang als auch
diese Checkbox, ruft `_on_confirm()` `config.py::update_watchlist_status()`
mit `"watchlist"` auf — eigenes try/except, ein Fehlschlag verhindert nicht
die Bestands-Übernahme selbst. Verifiziert gegen Kopien von `config.yaml`
UND einer In-Memory-DB (beide Richtungen: Checkbox angehakt → Status
zurückgesetzt; nicht angehakt → Status bleibt).

**Wichtiger Nachtrag zur Wechselwirkung mit der Staking-Verifikation
(2026-07-16, noch am selben Tag):** seit der Staking-Verifikation (siehe
unten) läuft ein Rückgang meistens automatisch über `apply_decrease()`
INNERHALB von `sync_from_bitpanda()` — der `BitpandaDecreaseConfirmDialog`
(und damit auch die neue Status-Rückstufungs-Checkbox) erscheint jetzt nur
noch im SELTENEN Fallback-Fall (Transaktions-Abruf fehlgeschlagen). Für den
NORMALEN automatischen Rückgang-auf-0-Fall gibt es aktuell KEINE
Status-Rückstufung (bewusst nicht automatisiert, siehe oben) — ein
vollständig verkaufter Coin behält seinen `status: aktiv`, bis der seltene
Fallback-Dialog erscheint oder der Nutzer manuell editiert. Das ist ein
bekannter, noch nicht abschließend entschiedener Punkt: ob die
Rückstufung auch für den automatischen Pfad nachgezogen werden soll
(z. B. als zusätzliche, informative Meldung statt einer Checkbox), ist
noch offen.

**Nachtrag: Staking-Verifikation + vollautomatischer Bestandsabgleich
(2026-07-16, Nutzer-Frage "Kauf/Verkauf erfolgt nur durch den Nutzer selbst
- wo ist das Risiko?").** Zutreffender Einwand: WER eine Bestandsänderung
auslöst war nie das Risiko (immer der Nutzer, per Trade oder Limit-Order).
Das tatsächliche, rein technische Risiko: Bitpandas Live-Wallet-API kann
einen echten Verkauf nicht von einem Staking-Transfer unterscheiden (beide
erscheinen identisch als Rückgang, siehe `DecreaseCandidate`-Docstring).
Diese Ambiguität war aber bereits an anderer Stelle gelöst -
`importer/bitpanda_avg_cost.py::compute_staked_quantities()` rekonstruiert
aus der Transaktionshistorie (stake/unstake-Tags), wie viel aktuell gestakt
ist, bisher nur beim manuellen "Einstandspreise berechnen"-Button genutzt.

**Fix:** `sync_from_bitpanda()` ruft dieselbe Berechnung jetzt inkrementell
mit auf (EIGENER Cursor, `db.get/set_bitpanda_holdings_last_synced_unix()`
— bewusst NICHT derselbe Schlüssel wie der bestehende
`bitpanda_avg_cost_last_synced_unix`-Cursor, sonst würden sich beide
Features gegenseitig Transaktionen "wegkonsumieren"). Gelingt der
Transaktions-Abruf, lassen sich BEIDE Richtungen sicher automatisch
schreiben: `quantity` kommt direkt vom Live-Wallet-Saldo, `staked_quantity`
unabhängig aus der Transaktionshistorie — keine Interpretation "war das ein
Verkauf?" mehr nötig, egal ob es sich um einen echten Verkauf oder einen
Staking-Transfer handelt. Nur wenn der Transaktions-Abruf selbst fehlschlägt
(z. B. Netzwerkfehler), bleibt der alte, konservative
Bestätigungsdialog als Fallback.

**Konsequenz für den Scheduler:** der bisherige `bitpanda_cash`-Job (nur
EUR-Cash, 30 Min) wurde durch `bitpanda_holdings` ersetzt — ruft direkt die
volle `sync_from_bitpanda()` auf (die den Cash-Anteil intern bereits
mitmacht), kein separater Job mehr nötig. Schlägt die Staking-Verifikation
in einem einzelnen automatischen Lauf fehl, bleiben etwaige Rückgänge
unangewendet (Bestand bleibt auf altem, bekanntem Stand — kein
Datenverlust, nur Staleness) und werden per E-Mail gemeldet (mit demselben
Cooldown-Mechanismus wie Job-Ausfälle, kein Postfach-Spam).

**Verifikation:** 6 synthetische Testfälle (Zuwachs, Rückgang durch Staking
erklärt, Rückgang ohne Stake-Event/echter Verkauf, Netzwerkfehler-Fallback,
Randfall "komplett gestaktes Symbol ohne vorherige Zeile", unabhängiger
Cursor) — dabei einen echten Bug gefunden und behoben: die ursprüngliche
`staked_quantity`-Persistenz prüfte fälschlich gegen `matched_symbols`
(nur "in einer Wallet-Antwort gesehen") statt gegen tatsächlich
geschriebene Zeilen — ein Symbol mit `alt_menge == neu_menge == 0` aber
positivem `staked_quantity` hätte sonst stillschweigend keine Zeile
bekommen und die UPDATE-Anweisung wäre ins Leere gelaufen.

**Offener Punkt:** die Status-Rückstufungs-Checkbox (Nachtrag oben)
erscheint jetzt nur noch im seltenen Fallback-Fall, nicht beim
normalen automatischen Rückgang-auf-0 — ob das nachgezogen werden soll,
ist noch nicht entschieden.

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
| "Bestände von Bitpanda abgleichen" | Datei-Menü | Live-Abgleich **aller Bestände** (Krypto + Aktien/ETF/Rohstoffe) + EUR-Cash direkt von Bitpanda (siehe RM-4-Abschnitt oben) — läuft seit 2026-07-16 bereits automatisch alle 30 Min (siehe `bitpanda_holdings`-Job oben, Staking-Verifikation macht das sicher). Der manuelle Klick bleibt für sofortige Abgleiche UND als Ort, an dem der Bestätigungsdialog erscheint, falls die automatische Staking-Verifikation in einem Lauf mal fehlschlägt (seltener Fallback). |
| "Einstandspreise von Bitpanda berechnen" | Datei-Menü | Echter Anschaffungspreis je Asset aus der Bitpanda-Trade-Historie (siehe Abschnitt 9) — **eigener, unabhängiger Menüpunkt**, nie automatisch (Erstlauf kann ~40s dauern, läuft threaded im Hintergrund) |
| "Bestände neu importieren" / "aus Datei importieren…" / "exportieren…" | Datei-Menü | Excel-Import/-Export (`Basisinfos/Assets.xlsx`) — rein lokal, kein externer Netzwerk-Aufruf |
| Fiat-Cash-Reserve "Speichern" | Portfolio-Tab | Manuelle Eingabe, kein externer Aufruf |

**Grundprinzip (2026-07-16 nachgeschärft):** Groq/Cerebras/Gemini-Aufrufe pro
Einzelsignal bleiben bewusst manuell — jeder Lauf kostet einen echten
KI-Aufruf und soll gezielt ausgelöst werden. Bitpanda-Bestandsabgleich war
ursprünglich ebenfalls aus Vorsicht manuell (ein Rückgang ließ sich nicht
sicher von einem Staking-Transfer unterscheiden) — seit der Staking-
Verifikation (Kap. 6, `bitpanda_holdings`-Job) ist diese Ambiguität
technisch aufgelöst, der volle Abgleich läuft jetzt automatisch. Der
manuelle Klick bleibt als Fallback und für sofortige Abgleiche bestehen.
Kostenlose öffentliche Marktdaten (Preise, Historie) liefen schon immer
automatisch. Der Marktscan ist weiterhin der einzige Fall, der teilweise
automatisch UND optional KI-gestützt läuft (siehe oben).

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

### Nachtrag (2026-07-17): echter Betriebsfehler gefunden — 06:00-Cron zwei Tage in Folge komplett ausgefallen

Beim Versuch, den Datenstand für Schritt 3 (KI-Trimm-Vorschläge) neu zu
prüfen, fiel auf: die zwei ältesten offenen Hebel-ERÖFFNEN-Signale (AIOZ,
CAT, beide vom 07-14) hatten `outcome_geprueft_am = null` — nicht nur
„weiterhin offen", sondern **nie auch nur geprüft**, obwohl die
durchschnittliche Hebel-Haltedauer (~1,1 Tage) längst eine Auflösung
erwarten ließe. Log-Abgleich bestätigte die Ursache: der `backward_
tracking`-Cron (fest auf 6 Uhr) ist an **zwei aufeinanderfolgenden Tagen**
(07-15 und 07-16) komplett ausgefallen — die App lief zu diesem Zeitpunkt
schlicht nicht (letzter Log-Eintrag vor der Lücke: 07-14, 06:00 Uhr).
APScheduler holt einen an einem festen Zeitpunkt verpassten Cron-Termin
**nicht automatisch nach**, wenn der Prozess zu diesem Zeitpunkt gar nicht
läuft — anders als bei den 15-Minuten-Intervall-Jobs, die beim nächsten
Start einfach wieder anlaufen.

**Fix:** neuer Wasserstand `meta.backward_tracking_last_run_date` (ISO-
Datum, `database/db.py::get/set_backward_tracking_last_run_date()`), von
`backward_tracking_job()` bei jedem erfolgreichen Lauf aktualisiert. Neue
Funktion `scheduler/background.py::backward_tracking_catchup_if_missed()`
prüft beim App-Start synchron (kein Netzwerk-Call nötig, reine DB-
Auswertung bereits vorhandener Kursdaten — siehe oben), ob der heutige
Termin bereits erledigt wurde; falls nicht, wird sofort nachgeholt. Kein
Mehrfach-Lauf bei mehreren Neustarts am selben Tag, da der Wasserstand
bereits nach dem ersten (Nachhol-)Lauf aktualisiert ist.

**Einordnung:** dasselbe Resilienz-Prinzip wie bereits bei `refresh_
prices_job`/`refresh_securities_prices_job` (Kap. 12, laufen seit 2026-07-12
sofort nach jedem Neustart) — dort ging es um Intervall-Jobs, hier um einen
**festen Cron-Termin**, der beim Verpassen zusätzlich einen Datums-
Wasserstand braucht, um Mehrfach-Läufe am selben Tag zu vermeiden.
Verifiziert: 4 synthetische Tests (Rundlauf des Wasserstands, Nachhol-Lauf
bei verpasstem Termin, kein Lauf bei bereits erledigtem Termin, korrekte
Persistierung bei echtem `backward_tracking_job()`-Aufruf).

### Nachtrag (2026-07-17): Erfolgsmetrik für Schritt 3 (Regel-Anpassungsvorschläge) festgelegt

**Warum das jetzt schon nötig ist, obwohl die Governance-Frage von Schritt 3
(automatisch vs. Nutzer-Bestätigung) noch offen ist:** ohne eine vorher
festgelegte Metrik lässt sich ein späterer KI- oder Nutzer-Vorschlag
("Regel X mit Wert Y statt Z ist besser kalibriert") nicht objektiv prüfen —
das gilt unabhängig davon, wer am Ende entscheidet. Diese Festlegung ist
deshalb eine reine Dokumentations-Ergänzung, keine Verhaltensänderung.

**Primärmetrik: realisiertes CRV** (bereits vorhanden, siehe Abschnitt
„Die sechs Ergebnis-Felder" oben) — durchschnittlich über alle aufgelösten
Signale einer Regel-Variante, getrennt nach Spot und Hebel (unterschiedliche
Positionsgrößen-Logik, siehe Abschnitt „Provider-Performance-Aggregation").
Begründung: bildet direkt das ursprüngliche Z-2-Versprechen ab (Chance im
Verhältnis zum Risiko) und ist bereits Teil der bestehenden Datenstruktur —
keine neue Berechnung nötig.

**Sekundärmetriken** (zur Einordnung, nicht als alleiniger Maßstab, da CRV
allein z. B. eine niedrige Trefferquote mit wenigen großen Gewinnen
kaschieren könnte):
- **Trefferquote** (Anteil Take-Profit an allen entschiedenen Signalen,
  bereits Teil der Provider-Performance-Karte).
- **Maximaler Drawdown** einer simulierten/realen Sequenz aufeinanderfolgender
  Signale — noch nicht berechnet, wird mit der Backtesting-Engine (siehe
  unten) erstmals verfügbar.

**Mindest-Stichprobe vor jeder Bewertung:** ein einzelner Vorschlag wird erst
ab **30 aufgelösten Fällen** je Regel-Variante überhaupt in Betracht gezogen
(siehe Machbarkeits-Analyse-Notiz, Plandatei `swift-napping-muffin`),
idealerweise geprüft in **zwei nicht-überlappenden Teilzeiträumen** (ein
Muster muss in beiden auftauchen, um nicht auf eine einzelne Marktphase
überzufittet zu sein). Diese Schwelle ist bewusst vorläufig — siehe Kap. 15.

### Nachtrag (2026-07-17): Backtesting-Engine — bestehende Regeln rückwirkend gegen historische Kursdaten simulieren

**Warum:** der größte praktische Engpass für Schritt 3 ist nicht fehlendes
Können, sondern fehlende Zeit — echte KAUFEN/ERÖFFNEN-Signale lösen sich nur
mit der Geschwindigkeit auf, mit der neue Signale entstehen (für Spot eher
Wochen, siehe Abschnitt „Aktueller Stand"). Das Projekt verfügt aber bereits
über eine mehrjährige Kurshistorie (`price_history_ohlc`), die bisher nur für
Charts und Backward-Tracking genutzt wird, nicht aber, um die AKTUELLEN
Regeln testweise gegen die Vergangenheit laufen zu lassen.

**Umfang:** rein analytisch, kein Live-Verhalten wird geändert. Nimmt die
bereits vorhandene, deterministische Regel-Logik (Indikatoren, Regime-
Klassifikation, Risikomanagement-Schwellenwerte) und wendet sie Tag für Tag
auf die gespeicherte Kurshistorie an, als wäre jeder Tag ein neuer Lauf in
der Vergangenheit — erzeugt so synthetische, aber methodisch identische
Signal-Ergebnisse, die genauso wie echte Signale nach CRV/Trefferquote/
Drawdown ausgewertet werden können. Der eigentliche KI-Anteil (Prompt an
Groq/Cerebras/Gemini) ist dabei bewusst AUSSER Betracht — nur der
deterministische Regel-Teil ist rückwirkend reproduzierbar, ein LLM-Aufruf
für einen historischen Tag wäre weder reproduzierbar noch budgetneutral.

**Wo im Code:** `agent/krypto/backtesting.py` (siehe Abschnitt 11 für den
vollständigen Verweis).

**Verifiziert (2026-07-17):** 7 synthetische Tests (Stop-Loss-Priorität bei
Gleichzeitigkeit, CRV-Berechnung, „Ende der Historie" vs. „Haltefrist
abgelaufen", CRV exakt auf `CRV_MINIMUM` skaliert, zu kurze Historie ohne
Crash, Flanken-Trigger verhindert Dutzende korrelierte Trades in einem
einzigen Trend) + echter Lauf gegen die Produktions-DB (BTC/ETH/SOL/LINK,
2025-02 bis 2026-07): 12–21 synthetische Trades je Symbol, Trefferquote
24–33 %, durchschnittliches CRV negativ (−0,03 bis −0,46) in diesem
Zeitfenster. **Einordnung:** kein Widerspruch zur echten Signalqualität —
die vereinfachte Konfluenz-Regel ersetzt bewusst NICHT die mehrfaktorielle
KI-Bewertung (siehe Grenzen oben), das Ergebnis zeigt aber, dass das
gewählte Zeitfenster für eine reine „Konfluenz-bullish + 2:1-CRV"-Heuristik
ungünstig war — ein plausibles, nicht offensichtlich falsches Ergebnis,
kein Hinweis auf einen Fehler in der Engine selbst.

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
- `agent/krypto/backtesting.py` — Backtesting-Engine, deterministische Regeln rückwirkend gegen `price_history_ohlc` (Abschnitt 7, Selbstverifikations-Vision Schritt 3 Vorbereitung)
- `agent/krypto/regime.py::get_last_known_regime_status()`, `agent/krypto/regelwerk_parameter.py`, `ui/regime_view.py` — Regime-Status + Parameter-Übersicht (Abschnitt 13, Remote-Karte + Desktop-Tab „Regime")

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
Jobs (`refresh_prices`, `refresh_securities_prices`, `bitpanda_holdings` — je
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

**Zusätzlicher Fernzugriffsweg (2026-07-16):** Chrome Remote Desktop (Google)
ist eingerichtet — echter Vollzugriff auf den Bildschirm/die Tkinter-
Oberfläche selbst, unabhängig von dieser Steuer-Seite. Für vollen
GUI-Zugriff unterwegs der einfachere Weg; die Tailscale-Steuer-Seite bleibt
sinnvoll für einen schnellen Status-Blick oder falls Remote Desktop selbst
nicht erreichbar ist.

**Regime-Status + Parameter-Übersicht (2026-07-17):** direkter, bewusst
governance-unabhängiger erster Schritt aus der Selbstverifikations-
Machbarkeits-Analyse (siehe Memory `project_selbstverifikation_ki_trimmen`)
— reine Sichtbarkeit bereits vorhandener Werte, keine neue Entscheidungslogik.

- **Regime-Status-Karte:** zeigt den zuletzt bekannten Marktregime-Stand
  (Zustand farbcodiert, Zeitstempel „Stand: …", Begründung, BTC-Trend, Fear
  &amp; Greed, BTC-Dominanz-Trend, Zyklus-Risiko, Liquiditätsregime). **Rein
  passiv** — kein neuer Live-Aufruf von `determine_regime()`, gelesen wird
  ausschließlich der zuletzt PERSISTIERTE Stand aus `signals.regime`/
  `regime_source` (identisch für alle Symbole eines Laufs) + der zuletzt
  gespeicherten `macro_snapshot`-Zeile (`agent/krypto/regime.py::
  get_last_known_regime_status()`). Ein manueller Regime-Override
  (RG-8/RG-9) wird deutlich als „⚠ manuell überschrieben" gekennzeichnet,
  statt mit der automatischen Begründung vermischt zu werden.
- **Datenlücke behoben:** `zyklus_risiko`, `liquiditaets_regime` (+
  Begründungen) und `btc_trend_label` wurden bisher bei jedem Pipeline-Lauf
  frisch berechnet, aber nirgends gespeichert. `agent/krypto/pipeline.py::
  compute_current_regime()` persistiert sie jetzt zusätzlich über den
  bereits bestehenden, try/except-geschützten zweiten `macro_snapshot`-
  Upsert (der bisher nur die Boden-Zielzone nachtrug) — kein neuer
  Netzwerk-Call, reine Persistierungs-Erweiterung. `dominance_trend_label`
  wird bewusst NICHT gespeichert, sondern bei jedem passiven Lesezugriff aus
  der bereits vorhandenen Historie neu berechnet (reine Funktion).
- **Parameter-Übersicht-Karte:** zeigt alle Kap.-15-Kalibrierungsparameter
  mit ihrem aktuell konfigurierten Wert, live aus `config.yaml` gelesen
  (`agent/krypto/regelwerk_parameter.py::build_parameter_overview()`),
  gruppiert nach der a/b/c-Kategorie aus der Machbarkeits-Analyse. Details
  (Begründung + „zuletzt geändert am") **über Mouseover** statt permanent
  sichtbar — Remote-Seite über natives HTML-`title`-Attribut, Desktop-Tab
  über das bestehende `ui/row_tooltip.py`. Begründung/Änderungsdatum sind
  aus den config.yaml-Inline-Kommentaren manuell transkribiert (
  `yaml.safe_load()` liefert keine Kommentare mit) — muss beim inhaltlichen
  Ändern eines Wertes von Hand nachgezogen werden.
- **Desktop-Spiegelung:** neuer Tab „Regime" (`ui/regime_view.py`), inhaltlich
  identisch zur Remote-Karte, nimmt bewusst nur `db_conn_factory` entgegen
  (kein LLM-/API-Client nötig). Nimmt am bestehenden periodischen
  3-Sekunden-Refresh teil (`ui/app.py::_poll_prices()`).

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
(damals `scheduler/background.py::refresh_bitpanda_cash_job`, neue Funktion
`importer/bitpanda_sync.py::sync_fiat_cash_from_bitpanda()`, aus dem bestehenden
manuellen Sync extrahiert) — damit RM-4 nie länger als eine halbe Stunde auf
einem veralteten Cash-Stand rechnet, ohne dass dafür die vollen Bestände
automatisch mitlaufen müssen (damals noch nicht möglich, siehe Kap. 6).
**Überholt (2026-07-16):** dank Staking-Verifikation läuft seither auch der
volle Bestandsabgleich automatisch im selben Takt (`refresh_bitpanda_
holdings_job`) — dieser Cash-only-Job wurde dadurch ersetzt, siehe Kap. 6.
Details/Verifikation: Memory `project-portfolio-vollstaendigkeit-cash-staking`.

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

### Nachtrag (2026-07-17): Mistral als neue zweite Fallback-Stufe, Cerebras-Rückbau vorbereitet

**Auslöser:** Cerebras beendet seinen kostenlosen API-Tier zum **2026-08-17**
(siehe Memory `project_cerebras_free_tier_aenderung_2026-08-17`) — nach dem
$5-Einmalguthaben ist die API ohne echte Bezahlung nutzlos (harter Stopp,
kein Auto-Billing, aber auch keine dauerhafte Lösung). Ausgiebige Recherche
über vier Runden (Cerebras' eigene PayGo-FAQ, NVIDIA NIMs echte Terms of
Service, Groq/Cerebras/Mistral/Gemini-Vertragsvergleich) führte zu:

- **Mistral** übernimmt Cerebras' bisherige Rolle als zweite Fallback-Stufe —
  echt im eigenen Kontingent-Dashboard des Nutzers verifiziert:
  `mistral-small-2506` mit **2.250.000 Tokens/Min, 5 Anfragen/Sek. (≈ 300/Min)**
  — ca. 20x mehr als Geminis Kapazität. Vertraglich zudem günstiger als
  Gemini: keine EWR/CH/UK-Sonderklausel, keine Warnung vor vertraulichen/
  Finanzdaten, Trainings-Nutzung im Free-Tier abwählbar.
- **Gemini** bleibt integriert, rutscht aber bewusst auf die letzte, seltenste
  Fallback-Stufe zurück — von allen vier Anbietern vertraglich die
  ungünstigsten Bedingungen (EWR/CH/UK-Sonderklausel + explizite Warnung vor
  vertraulichen/Finanzdaten + nicht abwählbare Trainings-Nutzung).
- **NVIDIA NIM** wurde anhand der echten Terms of Service (PDF-Primärquelle)
  endgültig abgelehnt — Produktivbetrieb ist ohne kostenpflichtige
  Enterprise-Lizenz vertraglich verboten, kein Grenzfall für ein Hobby-Projekt.
- **Neue Ziel-Reihenfolge:** Groq → Mistral → Cerebras (nur noch bis
  2026-08-17) → Gemini.

**Echter Nebenfund + Bugfix:** Cerebras war bisher an zwei Stellen
UNBEDINGT vorausgesetzt statt optional (anders als Gemini) —
`agent/krypto/budget_allocator.py`s drei `calls`-Listen hängten
`("cerebras", ...)` ohne Existenz-Check an, UND
`scheduler/background.py::hebel_screening_job()` ließ den kompletten
Budget-Allocator nur laufen, `if groq_client is not None and cerebras_client
is not None` — ohne CEREBRAS_API_KEY wäre der gesamte Allocator
stillgelegt worden, nicht nur die Cerebras-Stufe. Beide Stellen jetzt
korrigiert (Cerebras ist jetzt genauso optional wie Gemini/Mistral) — die
Entfernung zum 2026-08-17 ist damit nur noch "Key aus `.env` löschen", kein
weiterer Code-Eingriff nötig.

**Neu:** `api/mistral.py::MistralClient` (identisches `.chat()`-Interface wie
Groq/Cerebras/Gemini). Verdrahtet in `budget_allocator.py`,
`signal_batch.py::run_signal_batch()`, `scheduler/background.py`, `main.py`,
`ui/app.py`/`ui/hebel_view.py`/`ui/signals_view.py`, `remote/server.py`
(API-Status-Karte). Verifiziert: 8 synthetische Tests (Fallback-Reihenfolge,
Cerebras-Optionalität, Gate-Bugfix, `llm_model_label()`-Erkennung,
Tk-Smoke-Test) plus ein echter Live-API-Testaufruf gegen `api.mistral.ai`
(2026-07-17, nachdem der Nutzer den Key in die `.env` eingetragen hat):
einfacher Chat-Call sowie ein Call mit
`response_format={"type": "json_object"}` (exakt das Format aus
`analyst.py:656`) beide erfolgreich — Mistral verhält sich formatkompatibel
zu den anderen drei OpenAI-kompatiblen Anbietern.

### Nachtrag (2026-07-17, gleicher Tag): Korrektur — Cerebras sofort vollständig entfernt statt bis 2026-08-17 auslaufen zu lassen

Der oben dokumentierte Plan ("Cerebras bleibt bis 2026-08-17 als dritte
Stufe aktiv") war der zum damaligen Zeitpunkt abgesegnete Stand. Der Nutzer
hat sich nach Sichtung der Remote-Steuer-Seite (Provider-Performance zeigte
weiterhin echte Cerebras-Calls) explizit umentschieden: Cerebras sollte
bereits jetzt vollständig durch Mistral ersetzt werden, einzige Ausnahme
der `CEREBRAS_API_KEY` in `.env` (Wert unverändert, nur als obsolet für die
Produktion kommentiert).

**Umgesetzt:** `api/cerebras.py` gelöscht; `cerebras_client`-Parameter und
alle Cerebras-Zweige aus `main.py`, `agent/krypto/budget_allocator.py`
(inkl. `cerebras_taegliches_budget`, `AllocationResult`-Felder, alle drei
`calls`-Listen), `scheduler/background.py`, `ui/app.py`/`ui/hebel_view.py`/
`ui/signals_view.py`, `agent/krypto/signal_batch.py`,
`agent/krypto/llm_provider.py::llm_model_label()` und
`remote/server.py::API_HEALTH_GROUPS` entfernt. **Aktive Fallback-Kette
jetzt: Groq → Mistral → Gemini.**

Bewusst NICHT angetastet: historische DB-Einträge mit `"cerebras:..."`-
Provider-Präfix (Provider-Performance-Statistik) sowie
`provider_from_label()` (bleibt generisch, liest Altbestand weiterhin
korrekt). Details siehe Memory
`project_cerebras_free_tier_aenderung_2026-08-17.md`, Abschnitt "KORREKTUR".

### Nachtrag (2026-07-17): Selektiver Desktop↔Notebook-Sync für manuelle Einstandspreise

**Auslöser:** beim Vervollständigen der Einstandspreise für 13 Bitpanda-
"Stocks"-Positionen (Aktien/ETF/Rohstoffe — Kostenbasis lässt sich hier NICHT
automatisch aus Bitpanda-Transaktionen berechnen, da diese Produktklasse im
`/wallets/transactions`-Feed gar nicht auftaucht, live bestätigt) stellte sich
die Frage, wie diese manuellen Werte zuverlässig aufs 24/7-Notebook kommen,
ohne dabei die dortige, laufend selbst erzeugte Produktivdaten-Historie
(`signals`/`hebel_*`/`price_history*`/`macro_snapshot`/`marktscan_candidates`/
`api_health_status`) durch eine volle DB-Kopie zu überschreiben.

**Lösung:** `database/db.py::HOLDINGS_MANUAL_OVERRIDES_PATH`
(`data/holdings_manual_overrides.json`, gitignored wie `Assets.xlsx`) —
enthält ausschließlich `{symbol: avg_buy_price_manual_eur}` für alle Zeilen
mit gesetztem Override.
- `export_holdings_manual_overrides()` schreibt diese Datei automatisch bei
  jedem Aufruf von `set_holding_avg_buy_price_manual()` neu (egal ob über den
  Portfolio-Tab-Dialog oder ein Skript) — kein manueller Export-Schritt.
- `import_holdings_manual_overrides()` liest sie automatisch bei jedem
  `init_db()`-Durchlauf (also bei jedem App-Start) ein und schreibt die
  Werte in die lokale `holdings`-Tabelle zurück — NUR für Symbole, die dort
  bereits eine echte Zeile haben (keine Phantom-Zeilen; die Zeile selbst
  entsteht ausschließlich über den echten Bitpanda-Bestandsabgleich).
  Idempotent, berührt keine andere Tabelle.

**Für den USB-Stick-Sync (siehe Memory `reference_usb_sync_workflow.md`)
bedeutet das:** ab jetzt genügt es, diese eine kleine JSON-Datei mitzunehmen
statt der gesamten `tradinginfotool.db` — sie wird beim nächsten Start auf
dem Zielgerät automatisch angewendet, ohne dort laufende Produktivdaten zu
gefährden. Verifiziert: echter Simulationstest (Kopie der Produktions-DB,
Overrides zurückgesetzt, `init_db()` komplett durchlaufen lassen — Werte
korrekt wiederhergestellt) plus Phantom-Symbol-Schutztest (unbekanntes Symbol
in der JSON legt keine neue `holdings`-Zeile an) plus Regressionstest (frische
leere DB, `init_db()` läuft fehlerfrei durch).

### Nachtrag (2026-07-17): BUGFIX — "Nur Long" griff nicht bei offenen Short-Positionen

**Auslöser:** Nutzer meldete weiterhin unnötige Short-Empfehlungs-E-Mails,
obwohl `hebel_richtung_modus: nur_long` (Einstellungen-Dialog) aktiv war.

**Ursache gefunden (Code-Review, nicht nur Vermutung):** die Einstellung
filterte in `budget_allocator.py` nur `hebel_pending` (frisch entdeckte
Trigger-Kandidaten, seit 2026-07-15 so gebaut). Die zweite, unabhängige
Kandidatenquelle `_offene_positionen_als_kandidaten()` (seit 2026-07-16,
garantiert bestehenden offenen Hebel-Positionen eine regelmäßige KI-
Neubewertung) hatte **keinen** Richtungsfilter — offene SHORT-Positionen
wurden weiterhin unbegrenzt dem LLM vorgelegt, neue Signale erzeugt, und
`scheduler/background.py::_notify_hebel_signal()` prüft die Richtung
seinerseits nicht (nur `action != HALTEN`) — jedes daraus entstehende
Signal wurde gemailt.

**Fix:** derselbe `if hebel_richtung_modus == "nur_long":`-Filter
(`richtung == RICHTUNG_LONG`) jetzt auch auf `_offene_positionen_als_
kandidaten()`-Ergebnisse angewendet, bevor der Cooldown-Filter läuft —
konsistent mit der bereits bestehenden Filterung von `hebel_pending`.

**Verifiziert:** echter End-to-End-Lauf gegen `run_budget_allocator()` mit
einer echten temporären SQLite-DB (zwei offene Positionen: BTC LONG, ETH
SHORT) — im Modus `nur_long` erreicht nur BTC den (gemockten) LLM-Aufruf,
ETH wird korrekt herausgefiltert. Regressionstest: im Modus `beide` erreichen
weiterhin beide Positionen den LLM-Aufruf (keine Verhaltensänderung für den
Standardmodus).

### Nachtrag (2026-07-17): Regelwerk-Überarbeitung nach LINK-Fall — vier Punkte

**Auslöser:** dieselbe LINK-Empfehlungsfolge (ERÖFFNEN 5x LONG während
bereits erkanntem `baer`-Regime, 20 Stunden später fast wortgleiches
HEBEL_SENKEN) warf eine grundsätzlichere Frage auf als der Long/Short-Bugfix
oben: sollte ein 5x-gehebelter Long überhaupt eröffnet werden, WÄHREND das
Regime selbst schon bärisch eingestuft ist? Nutzer-Einschätzung: ein rein
mathematischer Konfidenz-Schwellenwert (R-5.10) reicht dafür nicht aus
("deterministisch dumm"). Vier konkrete Nachbesserungen, alle deterministisch
UND als expliziter Fakt fürs Modell selbst:

**1. Bisher ungenutzte Modell-Wahrscheinlichkeiten jetzt scharf geschaltet:**
das Modell erzeugt bei jedem Signal ohnehin eine Drei-Szenario-Prognose
(`forecast.bull/base/bear.probability_pct`) — bisher nur zur Anzeige, von
keiner Gate-Logik gelesen. Neu: liegt die Gegenszenario-Wahrscheinlichkeit
(Bear bei LONG, Bull bei SHORT) über `gegenszenario_wahrscheinlichkeit_
schwelle_prozent` (Config, Startwert 35%), wird der maximal erlaubte Hebel
zusätzlich auf `gegenszenario_hebel_deckel` (Startwert 3.0) gedeckelt.

**2. Regime-Richtungs-Konflikt (der eigentliche LINK-Auslöser):** eine
Position GEGEN das aktuelle Regime (LONG im `bär`-Regime, SHORT im
`bulle`-Regime) ist eine gehebelte Gegen-Trend-Wette — strukturell riskanter
als beides einzeln. Zwei Ebenen: (a) expliziter Fakt
`regime.richtungs_konflikt_mit_trigger` im Fakten-JSON, das Modell soll das
selbst gegenrechnen (Prompt-Regel 2 entsprechend erweitert); (b)
deterministischer Rückfall-Deckel `regime_konflikt_hebel_deckel` (Startwert
3.0) in `hebel_risk_gate.py::post_check_hebel()`, unabhängig davon ob das
Modell den Konflikt selbst berücksichtigt hat.

**3. `HEBEL_SENKEN` war bisher weder konkret noch ehrlich ausführbar:**
bedeutet praktisch "Eigenkapital nachschießen" (kein Ein-Klick-Vorgang in der
Bitpanda-App), aber (a) es gab nie eine konkrete EUR-Zahl dafür — neue Spalte
`hebel_senkung_eigenkapital_nachschuss_eur`, deterministisch berechnet
(Ziel-Eigenkapital = Positionswert / Ziel-Hebel, Differenz zum aktuellen
Eigenkapital); (b) der Ausführbarkeits-Hinweis war stumm dazu — jetzt
explizit erweitert ("Erfordert manuellen Eigenkapital-Nachschuss von ca. X
EUR … kein Ein-Klick-'Hebel senken'"). **Nebenfund dabei:** `HEBEL_SENKEN`
bekam bisher NIE ein `hebel_final` (war nicht in `_HEBEL_ACTIONS_MIT_HEBEL`
enthalten, dieser Zweig existierte für `HEBEL_SENKEN` schlicht nicht) — ohne
das wäre der konkrete Nachschussbetrag nie berechenbar gewesen. Bewusst OHNE
CRV-Pflicht (eine Risikoreduktion braucht keine Chance-Risiko-
Rechtfertigung), aber MIT denselben Sicherheits-Deckeln wie ERÖFFNEN
(gemeinsamer Helper `_hebel_deckel_kandidaten()`, Refactoring ohne
Verhaltensänderung für die bestehenden drei Aktionen).

**4. Keine Erkennung wiederholter, wirkungsloser Empfehlungen:** die zweite
HEBEL_SENKEN-Empfehlung wusste nichts von der ersten, unwirksam gebliebenen.
Neu: `_build_position_aktuell_facts()` vergleicht den `hebel_effektiv` der
offenen Position mit dem `hebel_final` des letzten Signals für dasselbe
Symbol+dieselbe Richtung (`database/db.py::get_hebel_signal_history()`,
limit=1) — bei unverändertem Hebel UND mindestens 2 Stunden verstrichener
Zeit wird `vorherige_hebel_empfehlung_nicht_umgesetzt` als eigener Fakt
mitgegeben, das Modell soll explizit darauf eingehen statt wortgleich zu
wiederholen (Prompt-Regel 3 entsprechend erweitert).

**Verifiziert:** 7 isolierte Testfälle in `hebel_risk_gate.py` (Regime-
Konflikt LONG/SHORT, Gegenszenario-Deckel, Normalfall unverändert,
HEBEL_SENKEN mit/ohne Konflikt), 5 isolierte Testfälle in
`_build_position_aktuell_facts()` (Wiederholung erkannt/noch zu frisch/
umgesetzt/kein Vorsignal/nur-HALTEN-Vorsignal), sowie ein echter
End-to-End-Lauf durch `generate_hebel_signal()` mit **ETH statt LINK**
(bewusst ein anderes Symbol, um Generik zu belegen — nichts an der neuen
Logik ist LINK-spezifisch): offene ETH-LONG-Position bei 5x, eine 20 Stunden
alte, unwirksame HEBEL_SENKEN-Empfehlung, `bär`-Regime, gemocktes LLM-Signal
mit 45 % Bear-Wahrscheinlichkeit — Ergebnis bestätigt alle vier Punkte
gleichzeitig (Konflikt-Fakt gesetzt, Wiederholungs-Fakt gesetzt, `hebel_final`
korrekt auf 3.0 gedeckelt, Eigenkapital-Nachschuss korrekt auf 66,67 EUR
berechnet). Regressionstest des Long/Short-Bugfixes von weiter oben lief
danach unverändert erfolgreich durch.

---

## 15. Offene / vorläufige Werte — die naheliegendsten Kandidaten für spätere Anpassung

Diese Werte sind laut Spezifikation ausdrücklich **vorläufig** (`[OFFEN]`-markiert) und
noch nicht durch echte Ergebnisse verifiziert — sie sind der wahrscheinlichste
Startpunkt, sobald Backward-Tracking/Outcome-Daten vorliegen:

- RM-2 Core-Allokations-Limit (35 % für BTC/ETH) — nachträglich erhöht, weil die reale
  BTC-Allokation das alte 25%-Limit überschritt; "BTC hat den Lead"-Frage insgesamt
  noch nicht grundsätzlich besprochen.
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
- **KORRIGIERT (2026-07-16), echter Nutzer-Fund an einer offenen LINK-
  Position:** `estimate_liquidation_price()` ignorierte den unbekannten
  Bitpanda-Maintenance-Margin-Puffer komplett — Bitpandas realer
  Liquidationspreis lag ~7% HÖHER (LONG, löst früher aus) als die alte
  Schätzung, also in die unsichere statt die dokumentierte "lieber zu früh
  warnen"-Richtung. Fix: `liquidations_sicherheitsmarge_relativ` (bisher nur
  in `max_safe_hebel()` verwendet) wird jetzt auch in die Liquidationspreis-
  Schätzung selbst eingerechnet, mathematisch aus Eigenkapital/Positionswert-
  Verhältnis hergeleitet (nicht nur genähert) — mit dem empirischen Wert
  reproduziert die Formel den echten Fall fast exakt. Auch geprüft:
  Bitpandas öffentliche API bietet keinerlei Einsicht in offene Stop-Loss-/
  Take-Profit-Limit-Orders (weder eigener Code noch offizielle Doku kennen
  einen solchen Endpunkt) — nur Wallet-Salden und bereits ausgeführte
  Trades sind zugänglich. Volle Details: `docs/hebel_positionsformel.md`.
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
- **ERLEDIGT (2026-07-17), war hier gelistet (2026-07-16):** Hebel hatte
  noch keine "Signal-Historie"-Ansicht analog zum Signale-Tab (Kap. 7) — die
  Überholt-Erkennung schrieb den Status zwar korrekt in
  `hebel_signals.outcome_status`, war im Hebel-Tab aber nirgends sichtbar.
  `ui/hebel_view.py` hat jetzt einen Signal-Historie-Dialog analog zum
  Spot-Pendant.
- **NEU (2026-07-16, Klassifikations-Redesign, siehe Kap. 17):**
  `spot_cooldown_stunden_ausgemustert`/`hebel_cooldown_stunden_ausgemustert`
  (je 120 Std. = 5 Tage) und `hebel_position_cooldown_stunden` (3 Std.) sind
  erste plausible Startwerte für die neuen Cooldown-Stufen, noch nicht gegen
  echten Betrieb kalibriert.

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

---

## 17. Asset-Klassifikation — drei Achsen statt zwei Felder (2026-07-16)

### Ausgangslage und Diagnose

Bis hierhin gab es zwei Felder je Watchlist-Asset: `typ` (core|taktisch|
stablecoin) und `status` (aktiv|watchlist). Auslöser für die Überarbeitung:
der BRETT-Kauf zeigte, dass `status` nach einem echten Kauf veraltet stehen
blieb (erst per Auto-Hochstufung gefixt, siehe Kap. 14/16-Historie), und die
symmetrische Frage beim Verkauf ("sollen wir auch zurückstufen?") führte zur
kritischen Nutzer-Nachfrage: *warum automatisieren wir den ganzen
Bestandsabgleich nicht durchgängig, wo ist das Risiko?*

Bei der Prüfung zeigten sich drei echte Probleme, nicht nur das
Rückstufungs-Symptom:

1. **`status` war ein manuell gepflegtes Duplikat einer Tatsache, die die App
   bereits live kennt.** Ob ein Asset gehalten wird, steht in `holdings`
   (Bestand + gestakte Menge). `status` versuchte, dieselbe Information ein
   zweites Mal manuell zu pflegen — und driftete deshalb strukturell (Kauf-
   UND Verkaufsfall).
2. **Kein Code las `status` risikorelevant.** Alle vier Lesestellen waren
   kosmetisch (LLM-Kontext-Fakt, Remote-Zähler, UI-Spalte) — die einzige
   Stelle, wo "gehalten" tatsächlich zählte (Zwei-Stufen-Cooldown, Kap. 6),
   las `status` schon vorher NICHT, sondern direkt `db.get_all_holdings()`.
3. **`typ` vermischte zwei Achsen in einem Feld.** `core`/`taktisch` ist eine
   Risiko-Rolle (gilt sinnvoll für jede Assetklasse), `stablecoin` ist keine
   Rolle auf derselben Skala, sondern eine Cash-Charakter-Eigenschaft (nie
   core/taktisch).

### Das neue Modell: drei unabhängige Achsen

1. **`rolle`** (`core`|`taktisch`) — rein strategisch, manuell, UNABHÄNGIG
   vom Bestand (ein Asset kann `rolle=core` tragen, bevor es je gekauft
   wurde — bewusster Erstkauf-Kandidat). Bestimmt weiterhin RM-2-Obergrenze,
   Kern-Cooldown-Mitwirkung, LLM-Fakt.
2. **"gehalten"** — KEIN gespeichertes Feld mehr, sondern live aus
   `db.get_all_holdings()` (Spot) UND `db.get_open_hebel_positions()` (Hebel)
   abgeleitet. Kann dadurch nie veralten — es gibt nichts mehr, das beim
   Kauf/Verkauf synchronisiert werden müsste. `config.py::
   update_watchlist_status()` und die zugehörige Checkbox im
   `BitpandaDecreaseConfirmDialog` wurden ersatzlos entfernt (Netto-
   Code-Reduktion statt eines weiteren Sonderfalls).
3. **`beobachtungsstatus`** (`beobachtung`|`ausgemustert`) — manuell, nur
   relevant solange NICHT gehalten. `ausgemustert` bedeutet niedrigste
   Priorität, **kein** Ausschluss ("darf nicht sterben", Nutzer-
   Formulierung) — wirkt nur als dritte, längere Cooldown-Stufe (siehe
   unten). Wird NIE automatisch geschrieben (weder hoch- noch
   heruntergestuft), rein manuell über den neuen GUI-Bearbeiten-Dialog.

Zusätzlich ersetzt `ist_cash_aequivalent: bool` den Sonderfall
`typ==stablecoin` (aktuell nur EURCV) — eine eigene Achse statt eines
dritten Werts auf der Rolle-Skala. Für Cash-Äquivalente trägt `rolle` einen
harmlosen Füllwert (`taktisch`), da jeder rolle-lesende Codepfad Cash-
Äquivalente vorher bereits ausschließt (A-1, `pipeline.py::generate_signal()`
bricht sofort mit HALTEN ab).

### Drei-Stufen-Cooldown (Präzedenz: Kern > Ausgemustert > Taktisch/Beobachtung)

Ein Asset gilt als **Kern** (kürzester Cooldown), wenn `rolle==core` ODER es
aktuell gehalten wird (Spot) ODER eine offene Hebel-Position darauf existiert
— echtes Engagement (Spot oder gehebelt) verdient IMMER die höchste
Priorität, unabhängig von `beobachtungsstatus`. Nur wenn keine Kern-
Bedingung zutrifft UND `beobachtungsstatus==ausgemustert`, gilt die neue,
deutlich längere Ausgemustert-Stufe. Sonst gilt der Standardwert
(Taktisch/Beobachtung).

| Kontext | Kern | Taktisch/Beobachtung (Standard) | Ausgemustert |
|---|---|---|---|
| Spot (`signal_batch.py`) | 10 Std. | 20 Std. | 120 Std. (5 Tage, `[OFFEN]`) |
| Hebel-Trigger (`budget_allocator.py`) | 3,5 Std. (unverändert) | 3,5 Std. (unverändert) | 120 Std. (5 Tage, `[OFFEN]`) |

### Offene Hebel-Positionen — eigene, unabhängige Prioritätsstufe

Nutzer-Anliegen: *"getätigte und aktive Positionen haben hohe Priorität
unabhängig davon, ob es eine Empfehlung gab — nach Wegfall/Verkauf/Stop-Loss
ist wieder die normale Ausgangslage vorhanden."* Geprüft: das galt bisher
NICHT — Tier-1-Kandidaten kamen ausschließlich aus `hebel_screening.py`s
deterministischen Triggern; eine offene Position ohne aktuell feuernden
Trigger wurde nicht regelmäßig neu bewertet.

Fix: `budget_allocator.py::_offene_positionen_als_kandidaten()` liest
`db.get_open_hebel_positions()` direkt und erzeugt daraus synthetische
`HebelTrigger`-Kandidaten mit eigenem, engem Cooldown
(`hebel_position_cooldown_stunden`, 3 Std. — deutlich enger als der
Standard-Trigger-Cooldown, aber budgetverträglich: 15 Min hätte bei nur
einer offenen Position bereits mehr Budget verbraucht als der gesamte
Tagesdeckel). `_dedupe_hebel_kandidaten()` verhindert einen doppelten
LLM-Call, falls eine offene Position zusätzlich einen frischen Trigger hat.
Schließt die Position, verschwindet sie automatisch aus dieser Quelle (keine
gespeicherte Sondermarkierung nötig) und fällt in die normale Trigger-Logik
zurück — genau das gewünschte Verhalten.

### Regel 7/8 (Spot-Analyst) erweitert

Die strikte "ist die langfristige These noch intakt"-Prüfung (bisher nur
`rolle==core`) gilt jetzt auch für taktische Beobachtungs-/Wiedereinstiegs-
Kandidaten (`rolle==taktisch`, nicht gehalten, `beobachtungsstatus==
beobachtung`) — sowohl in `agent/krypto/analyst.py` als auch `agent/aktien/
analyst.py` (identisches Schema). Der LLM-Fakt `asset.status` wurde durch
`asset.wird_aktuell_gehalten` (live abgeleitet) ersetzt.

### "Letzte Bewertung" — kein neues Feld nötig

Ursprünglich als "Notizfeld" angefragt, dann verworfen: die gewünschte
Information (kurz-/mittel-/langfristige Einschätzung je Asset) existiert
bereits strukturiert in jedem Signal (`long_reasoning.technisch/fundamental/
makro`, `top_gruende`), asset-klassen-übergreifend (Spot-Krypto UND Aktien
identisches Schema), automatisch bei jedem echten Analyse-Lauf neu
geschrieben — auch bei stark reduzierter Frequenz (Ausgemustert-Stufe) bleibt
die Einschätzung damit immer aktuell, ohne Drift-Risiko eines manuell
gepflegten Felds. Fehlend war nur die Anzeige-Oberfläche: der Signale-Tab
zeigte das bereits bei Zeilenauswahl an (auch für nicht gehaltene Assets),
neu ist ein Button "Letzte Bewertung anzeigen" im Portfolio-Tab
(`ui/letzte_bewertung.py`, wiederverwendet von beiden Tabs).

### Neuer GUI-Dialog: Asset hinzufügen/bearbeiten

Bisher gab es keinen generischen Weg, ein neues Asset über die GUI
hinzuzufügen — nur das Marktscan-"Übernehmen" (fest `taktisch`/`beobachtung`)
oder manuelles Editieren von `config.yaml`. Neu: "Asset hinzufügen…"/"Asset
bearbeiten…" im Watchlist-Tab (`ui/app.py::AssetAddDialog`/
`AssetEditDialog`). `rolle` ist dabei frei wählbar (core oder taktisch,
keine Einschränkung) — löst das Solana-Beispiel des Nutzers (Rolle=core
festlegen, bevor je gekauft wurde). Vor dem Hinzufügen läuft eine Live-
Validierung gegen CoinGecko (löst die ID auf echte Preisdaten auf?) und
Bitpanda (Symbol/Name gelistet?) — analog zum manuellen BRETT-Check aus
derselben Session, jetzt fest eingebaut. Warnungen blockieren nicht (P-10),
der Nutzer entscheidet nach Kenntnis der Warnung final selbst.

### Auto-Add unbekannter Hebel-Symbole

Geprüfter Nachbar-Fund: eine neu eröffnete Hebel-Position auf einem noch
nicht in der Watchlist geführten Symbol wurde zwar vom Positions-Sync
korrekt in `hebel_positions` gespeichert (rein transaktionsbasiert,
watchlist-unabhängig), aber Screening/Preisversorgung/die neue Positions-
Priorität liefen für dieses Symbol ins Leere, da sie alle auf einen
Watchlist-Eintrag angewiesen sind. Fix:
`importer/bitpanda_margin_positions.py::auto_add_unknown_hebel_symbols()`
ergänzt bei jedem `hebel_screening_job`-Lauf automatisch fehlende Einträge
für offene Positionen (Default `rolle=taktisch`, `beobachtungsstatus=
beobachtung`, Bitpanda-Listing geprüft) — `coingecko_id` bleibt bewusst leer
(keine zuverlässige Symbol→ID-Auflösung verfügbar, analog zu Aktien/ETF/
Rohstoffe), kann später manuell über den neuen Bearbeiten-Dialog ergänzt
werden.

### Migration

`config.yaml`: alle 54 Watchlist-Einträge migriert (`typ:`→`rolle:` mit
Wertübernahme, `stablecoin`→`taktisch`+`ist_cash_aequivalent: true` für
EURCV; `status:`→`beobachtungsstatus:`, alle Einträge einheitlich auf
`beobachtung` — niemand startet als bewusst "ausgemustert", das ist ein
neuer, erst ab jetzt aktiv vergebener Zustand). Reine Text-Transformation
(kein `yaml.dump()`), Backup vorher, `yaml.safe_load()`-Validierung danach.

### Verifikation

Synthetischer Test (6 Gruppen): Drei-Stufen-Cooldown inkl. Kern-Präzedenz
(auch für ein ausgemustertes, aber gehaltenes Asset), Hebel-Trigger-
Ausgemustert-Stufe + Präzedenz, offene-Positionen-Kandidatenquelle +
Dedupe, `config.py`-Roundtrip (`add_watchlist_entry`/
`update_watchlist_rolle`/`update_watchlist_beobachtungsstatus`, inkl.
No-Op-Erkennung bei identischem Wert), Auto-Add unbekannter Hebel-Symbole
inkl. Idempotenz beim zweiten Lauf — alle bestanden. Zusätzlich gegen eine
Kopie der echten Produktions-DB + der echten migrierten `config.yaml`
verifiziert (54 Assets korrekt geladen, 13 core, 1 Cash-Äquivalent,
Spot-Cooldown-Selektion/Kern-Symbol-Berechnung/Remote-Status liefen
fehlerfrei, 0 aktuell offene Hebel-Positionen bestätigt).

---

## 18. GUI-Refresh: Auswahl/Sortierung über Refresh hinweg erhalten + Zeilen-Hover (2026-07-16)

### Ausgangslage und Root Cause

Nutzer-Beobachtung: eine aktive Spaltensortierung "zerstört sich" von selbst,
und eine Zeilenauswahl (z. B. für "Asset bearbeiten…") muss "unter
Zeitdruck" getroffen werden, bevor sie wieder verschwindet. Code-Audit über
alle 5 Treeview-Bereiche bestätigte die Vermutung des Nutzers: der Watchlist-
und der Portfolio-Tab werden von `ui/app.py::_poll_prices()` automatisch
**alle 3 Sekunden** komplett neu aufgebaut (`tree.delete()` + Neueinfügen in
fester Reihenfolge) — dabei gehen zwangsläufig sowohl eine aktive Sortierung
als auch die aktuelle Zeilenauswahl verloren.

**Befund je Bereich vor dem Fix:**

| Tab | Stabile iid | Auswahl erhalten | Sortierung erhalten | Trigger |
|---|---|---|---|---|
| Watchlist | ✗ | ✗ | ✗ | alle 3 Sek. |
| Portfolio | ✗ | ✗ | ✗ | alle 3 Sek. |
| Signale | ✓ | ✗ | ✗ | nur Nutzeraktion |
| Marktscan | ✓ | ✗ | ✗ | nur Nutzeraktion |
| Hebel | ✓ | ✓ (bereits gelöst) | ✗ | nur Nutzeraktion |

`ui/hebel_view.py` hatte das Auswahl-Problem bereits sauber gelöst (Auswahl
vor dem Neuaufbau merken, stabile iid vergeben, danach Auswahl anhand der
iid wiederherstellen) — dieses Muster fehlte nur bei den anderen vier Tabs.

### Fix

1. **`ui/sortable_tree.py::make_sortable()`** gibt jetzt eine
   `reapply_sort()`-Funktion zurück (No-Op, solange nie sortiert wurde) —
   wendet die zuletzt vom Nutzer gewählte Spalte/Richtung nach einem
   Neuaufbau erneut an.
2. **Alle 5 `refresh()`/`_refresh_list()`-Funktionen** (Watchlist, Portfolio,
   Signale, Marktscan, Hebel) merken jetzt die Auswahl vor dem Neuaufbau,
   vergeben eine stabile iid (Symbol bzw. bereits vorhandene stabile ID),
   stellen die Auswahl danach wieder her und rufen `reapply_sort()` auf.
3. Bewusst **keine Checkboxen** eingeführt — mit stabiler Auswahl/Sortierung
   entfällt der ursprüngliche Auslöser ("Zeitdruck"); Checkboxen wären nur
   für einen anderen Anwendungsfall sinnvoll (mehrere Zeilen gleichzeitig
   markieren für Bulk-Aktionen), der aktuell nicht gebraucht wird.

### Neue Mouseover-Funktion: Zeilen-Hover-Tooltips

Bestehende Infrastruktur (`ui/heading_tooltip.py`) deckte bisher nur
Spaltenkopf-Tooltips ab. Neues, analog aufgebautes `ui/row_tooltip.py`
(`add_row_tooltips()`) zeigt Zusatzinfo beim Hover über eine Datenzeile —
der Text wird bewusst LAZY erst beim tatsächlichen Hover berechnet (kein
Vorab-Fetch bei jedem 3-Sekunden-Refresh):

- **Watchlist:** letztes Signal (Aktion, Zeitpunkt, Konfidenz, Kurzbegründung)
  ohne in den Signale-Tab wechseln zu müssen.
- **Portfolio:** volle Einstandspreis-Herkunft (manuell/berechnet/unbekannt),
  Menge ohne bekannten Einstandspreis, Gewinn/Verlust — nutzt einen während
  `refresh()` bereits gefüllten Cache (`_cost_basis_by_symbol`), keine
  zusätzliche Berechnung beim Hover selbst.
- Signale/Marktscan/Hebel bekamen bewusst KEINEN Zeilen-Hover — die zeigen
  bereits ein vollständiges Detail-Panel bei Zeilenauswahl, ein Hover wäre
  dort redundant.

### Verifikation

Tk-Smoke-Test (echter, versteckter Tk-Root, kein `mainloop()`): `make_
sortable()`s `reapply_sort()` erhält eine aktive Sortierung über einen
simulierten Neuaufbau hinweg; `PortfolioView` erhält sowohl Auswahl als
auch Sortierung über `refresh()` hinweg; `SignalsView`/`MarktscanView`
erhalten die Auswahl über `_refresh_list()` hinweg; `HebelView.refresh()`
läuft nach der Sortierungs-Ergänzung weiterhin fehlerfrei. Portfolio-
Hover-Tooltip-Text separat gegen einen bekannten und einen unbekannten
Symbol-Fall geprüft (liefert Text bzw. `None` wie erwartet).

### Nachtrag (2026-07-16): periodischer Refresh für Signale/Marktscan

Nutzer-Beobachtung: die Signale-/Marktscan-Tabelle aktualisierte sich
scheinbar nicht, obwohl im Hintergrund bereits E-Mails zu neuen
Empfehlungen verschickt wurden. Ursache: `ui/app.py::_poll_prices()`
(3-Sekunden-Timer) rief bereits `self._hebel_view.refresh()` mit auf, aber
NICHT `_signals_view`/`_marktscan_view` — beide zeigten neue
Scheduler-Ergebnisse (`budget_allocator`, 15-Min-Takt) erst nach einer
manuellen Aktion im jeweiligen Tab (z. B. Tab-Wechsel oder eigener
Signal-Lauf). **Fix:** `_signals_view._refresh_list()` und
`_marktscan_view._refresh_list()` einfach konsistent mit dem bereits
etablierten Hebel-Muster in denselben 3-Sekunden-Takt aufgenommen — kein
neuer, separater Timer/Tick-Zähler nötig, da der bewusst gebaute
GUI-Refresh-Fix (Auswahl/Sortierung überleben `refresh()`, siehe oben)
genau dafür sorgt, dass ein häufiger Neuaufbau unauffällig bleibt.

### Nachtrag (2026-07-16): rechtes Detail-Panel flackerte bei jedem periodischen Refresh

Nutzer-Fund direkt im Anschluss an den periodischen Refresh (siehe oben):
das rechte Detail-Panel (Signale/Marktscan/Hebel) baute sich bei JEDEM
3-Sekunden-Tick komplett neu auf, auch wenn sich am angezeigten Signal/
Kandidaten nichts geändert hatte — "extrem störend" beim Lesen (Scroll-
Position sprang zurück auf Anfang, jede Textauswahl ging verloren).

**Ursache:** `tree.selection_set(vorher_iid)` (Teil des GUI-Refresh-Fixes
oben) stellt die Auswahl nach jedem Neuaufbau der Liste wieder her — aber
Tkinter feuert `<<TreeviewSelect>>` dabei IMMER, auch wenn exakt dieselbe
Zeile erneut ausgewählt wird. Das löste bei jedem Tick einen kompletten
Re-Render des Detail-Panels aus, unabhängig davon, ob sich die
zugrundeliegenden Daten geändert hatten.

**Fix (`ui/signals_view.py`, `ui/marktscan_view.py`, `ui/hebel_view.py`):**
ein Guard (`self._suppress_select_event`) unterdrückt das durch die
programmatische `selection_set()` ausgelöste `<<TreeviewSelect>>` komplett.
Stattdessen vergleicht der Refresh die frisch geladenen Daten der
ausgewählten Zeile explizit mit dem zuletzt gerenderten Objekt (Dataclass-
Vergleich per `!=`) und rendert das Detail-Panel NUR neu, wenn sich
tatsächlich etwas geändert hat (z. B. eine neue automatische Analyse für
das gerade angezeigte Asset) — ein echter Klick des Nutzers auf eine Zeile
läuft weiterhin unverändert über `_on_select()`.

### Nachtrag (2026-07-16, zweite Runde): Fix griff nach App-Neustart trotzdem nicht — Guard kam zu spät

Nutzer-Fund NACH einem echten App-Neustart mit dem obigen Fix: das
Detail-Panel im Hebel-Tab resettete die Scroll-Position weiterhin bei einem
bereits berechneten Signal (kein Kandidat, dessen Score sich laufend
ändert). Der erste Fix-Ansatz (Guard direkt im `finally`-Block
zurücksetzen) hatte in einem synchronen Test (kein laufender `mainloop()`)
funktioniert, aber in der echten App versagt.

**Ursache (per echtem `mainloop()`-Test bestätigt, siehe
`project_technische_lektionen_uebergreifend`):** Tk feuert `<<TreeviewSelect>>`
NICHT synchron innerhalb von `selection_set()`, sondern hängt das virtuelle
Event hinten an die Tcl-Event-Queue an — es wird erst beim nächsten
Durchlauf des Event-Loops zugestellt. Der Guard wurde aber bereits im
`finally`-Block SOFORT zurückgesetzt, also lange bevor das verzögerte
Event tatsächlich ankam — zu diesem Zeitpunkt war die Unterdrückung schon
wieder deaktiviert, `_on_select()` lief also doch durch. Ein synchroner
Test ohne echten `mainloop()` bekommt das verzögerte Event nie zugestellt
und hätte den Bug nie zeigen können — daher unauffällig in den ersten
Tests.

**Fix:** Guard wird jetzt per `self.after_idle(self._clear_suppress_select_event)`
zurückgesetzt statt sofort im `finally`-Block — `after_idle()` läuft erst,
nachdem alle bereits anstehenden Events (inklusive des verzögerten
`<<TreeviewSelect>>`) abgearbeitet wurden.

**Verifiziert:** neuer Tk-Smoke-Test mit ECHTEM laufenden `mainloop()`
(`root.after(ms, root.quit)` + `root.mainloop()`, damit verzögerte Events
tatsächlich zugestellt werden) für alle drei Tabs — bestätigt kein
Re-Render ohne Datenänderung UND weiterhin korrektes Re-Render bei
tatsächlicher Änderung.

**Verifikation:** synthetischer Test für alle drei Tabs — bestätigt sowohl
"kein Re-Render ohne Datenänderung" als auch "Re-Render, sobald sich die
Daten für die ausgewählte Zeile ändern" (je 2 Fälle, 6 insgesamt).

## 19. Hebel-These: Einmaltrade vs. Swing (2026-07-16)

`agent/krypto/hebel_analyst.py` liefert bei jeder Hebel-Empfehlung ein
Feld `trade_thesis_typ` mit zwei möglichen Werten:

- **`einmal_trade`** — kurzlebige, ereignisgetriebene Gegenbewegung
  (Trigger-Zweig "Kontra", z. B. ein Squeeze nach Übertreibung).
- **`swing_strategie`** — bestätigter, mehrtägiger bis wochenlanger Trend
  (Trigger-Zweig "Trendfolge").

**Wichtig — was dieses Feld NICHT ist:** es ist keine Vorgabe für dein
eigenes Handelsverhalten und ändert NICHTS an der Ausführung. In beiden
Fällen gilt exakt derselbe Ablauf: Position eröffnen, Stop-Loss setzen,
in der Take-Profit-Zone ODER am Stop-Loss wieder aussteigen. Das Feld
beschreibt ausschließlich den von der KI eingeschätzten Zeithorizont der
zugrundeliegenden Marktthese — nicht, wie lange DU die Position halten
sollst. Der Prompt weist die KI explizit an, dieses Feld NICHT anhand
einer angenommenen "typischen Haltedauer" zu schätzen (der Nutzer hält
historisch im Schnitt nur ca. 1 Tag).

Der Feldname ist auch unabhängig von `richtung` (LONG/SHORT) und von der
separaten Bitpanda-Short-Einschränkung (siehe Kap. 6, "Nur Long"-Schalter)
— beides sind unabhängige Achsen, keine Kombination davon ändert die
Ausführungsregel oben.

**Sichtbarkeit in der GUI:** neue Spalte "These" in der Hebel-Liste
(`ui/hebel_view.py`, Werte "Einmaltrade"/"Swing"), mit Mouseover-Erklärung
über `add_heading_tooltips()` (identischer Mechanismus wie bei allen
anderen Spaltenköpfen) — Text der Erklärung entspricht den zwei
Absätzen oben. Bei dieser Gelegenheit einen echten, unabhängig davon
bereits bestehenden Anzeigefehler gefunden und behoben:
`HebelView.refresh()` nutzte `db.get_latest_hebel_signal_per_symbol()`
(nur pro Symbol, nicht pro Richtung) statt der bereits an anderer Stelle
(`hebel_backward_tracking.py`) korrekt verwendeten `..._and_richtung()`-
Variante — dadurch konnte ein älteres, weiterhin relevantes Signal einer
Richtung (z. B. LONG) unsichtbar werden, sobald für dasselbe Symbol die
andere Richtung (SHORT) neuer analysiert wurde. Jetzt konsistent
richtungsbewusst wie überall sonst im Hebel-Code.

## Nachtrag (2026-07-17, gleicher Tag): Spot-Regelwerk-Konsistenzprüfung nach dem Hebel-Fix

**Auslöser:** Nutzer-Wunsch, dieselbe Detailanalyse, die zum 4-Punkte-Hebel-
Fix führte (siehe oben), auf das Spot-Regelwerk (`agent/krypto/risk_gate.py`,
`agent/krypto/analyst.py`, `agent/krypto/pipeline.py` — gilt größtenteils
auch für `agent/aktien/*`, das `risk_gate.py` wiederverwendet) anzuwenden,
explizit als Detailanalyse VOR jeder Implementierung.

**Ergebnis der Analyse (Stand + Meinung, 4 Punkte gegen die Hebel-
Nachbesserung gespiegelt):**

1. **Ungenutzte Forecast-Wahrscheinlichkeiten — echte Lücke, identisch zum
   Hebel-Fall.** `analyst.py` lässt sich bereits `forecast.bull/base/bear.
   probability_pct` liefern, `risk_gate.py::post_check()` hat das nie
   ausgewertet. **Umgesetzt** (siehe unten).
2. **Regime-Richtungs-Konflikt-Deckel — KEINE Lücke, bereits anders
   abgedeckt.** Hebel brauchte das wegen Liquidationsrisiko bei einer
   Position gegen das Regime. Spot/Aktien haben keinen Hebel/keine
   Liquidation — Kaufen im Bär-Regime ist oft die beabsichtigte Strategie
   (AZ-4-Tranchen-Akkumulation). R-5.10s bereits bestehende regime-skalierte
   `min_konfidenz_prozent` (85 % im `baer`, nur 60 % im `bulle`) leistet
   strukturell dasselbe. **Bewusst NICHT umgesetzt** — kein Fix nötig.
3. **HEBEL_SENKEN-Konkretisierung — nicht anwendbar.** Spot/Aktien haben
   keine Hebel-Reduktions-Aktion.
4. **Wiederholte, wirkungslose Empfehlungen — echte, aber geringere Lücke
   als bei Hebel.** Der bestehende "Überholt"-Mechanismus (`backward_
   tracking.py`) erkennt einen ANDEREN Fall (eine offene Empfehlung wird
   durch eine NEUERE Analyse überholt), nicht "VERKAUFEN/TAUSCHEN wiederholt
   empfohlen, Position aber weiterhin gehalten". Geringere Dringlichkeit als
   bei Hebel (kein eskalierendes strukturelles Risiko wie Liquidation, nur
   eine verpasste Gelegenheit). **Umgesetzt** (siehe unten).

**Umsetzung Punkt 1 — Gegenszenario-Deckel (`risk_gate.py::post_check()`):**
bei KAUFEN/NACHKAUFEN wird zusätzlich zur bestehenden Konfidenz-Skalierung
geprüft, ob `forecast.bear.probability_pct` die neue Schwelle
`risiko.gegenszenario_wahrscheinlichkeit_schwelle_prozent` (Startwert 35)
erreicht/überschreitet — falls ja, wird die bereits konfidenz-skalierte
Positionsgrößen-Obergrenze zusätzlich multiplikativ auf
`risiko.gegenszenario_positionsgroesse_deckel_anteil` (Startwert 0.5, d.h.
50 %) reduziert. Bewusst **kein hartes Veto** wie beim Hebel-Pendant
(`risiko.hebel.gegenszenario_hebel_deckel`) — Spot/Aktien tragen kein
Liquidationsrisiko, eine Korrektur der Größe (bestehende Philosophie dieser
Funktion) reicht aus. Wirkt automatisch auch für Aktien-Signale, da
`agent/aktien/pipeline.py` dieselbe `post_check()`-Funktion aufruft.

**Umsetzung Punkt 4 — Wiederholungs-Erkennung (`analyst.py::build_facts()` +
`pipeline.py::generate_signal()`):** neuer Fakt `vorherige_empfehlung` —
`pipeline.py` lädt vor jedem neuen Signal-Lauf das zuletzt gespeicherte
Signal für dasselbe Symbol (`db.get_latest_signal()`) und reicht es an
`build_facts()` durch. War die letzte Aktion VERKAUFEN oder TAUSCHEN
(NICHT KAUFEN/NACHKAUFEN — eine ignorierte Kauf-Empfehlung ist risikoneutral,
keine Warnung wert), UND wird das Asset laut aktuellem Bestand weiterhin
gehalten, UND sind mindestens 4 Stunden vergangen (Grace-Period, bewusst
großzügiger als Hebels 2 Std. — Spot-Signale laufen manuell oder über einen
mehrstündigen Cooldown, kein 15-Min-Trigger-Takt), wird der Fakt gesetzt.
SYSTEM_PROMPT-Regel 21 verlangt vom Modell, den Umstand zu benennen statt
die Begründung wortgleich zu wiederholen. **Bewusst NUR in `agent/krypto/
analyst.py` umgesetzt, NICHT in `agent/aktien/analyst.py`** (eigene, separate
`build_facts()`/SYSTEM_PROMPT-Kopie) — der Nutzer sprach explizit von
"Spot"; Aktien-Analog auf Anfrage nachrüstbar.

**Config (`Basisinfos/config.yaml`, unter `risiko:`, NICHT `risiko.hebel:`):**
```yaml
gegenszenario_wahrscheinlichkeit_schwelle_prozent: 35
gegenszenario_positionsgroesse_deckel_anteil: 0.5
```
Beide Startwerte unkalibriert, identisch zum Hebel-Pendant übernommen — nach
echten Betriebsdaten anzupassen.

**Verifiziert:** 7 synthetische Testfälle (Gegenszenario-Deckel greift bei
hoher/nicht bei niedriger Bear-Wahrscheinlichkeit, Rückwärtskompatibilität
ohne `forecast`-Feld; Wiederholungs-Fakt gesetzt bei VERKAUFEN vor 5 Std. +
Position gehalten, NICHT gesetzt innerhalb der Grace-Period, NICHT gesetzt
wenn Position nicht mehr gehalten wird, NICHT gesetzt bei KAUFEN als letzter
Aktion) plus ein echter Kompatibilitätstest gegen eine Kopie der Produktions-
DB (`db.get_latest_signal()` auf 5 echten Symbolen, reale ISO-Zeitstempel
korrekt geparst, reale `forecast_bear_prob_pct`-Werte 20-30 % liegen
plausibel unter der neuen 35 %-Schwelle).

## Nachtrag (2026-07-17, gleicher Tag): RM-4 (Cash-Reserve) war rueckwaerts- statt vorwaertsgerichtet

**Auslöser:** Nutzer-Wunsch, das Thema Spot-Regelwerk breiter zu denken -
nicht nur Hebel-Punkte auf Spot uebertragen, sondern zusaetzliche,
eigenstaendige Luecken und Eigenheiten des Spot-Markts identifizieren.

**Fund:** RM-4 (`risk_gate.py::pre_check()`) prueft bisher nur, ob die
Cash-Reserve JETZT SCHON unter dem Minimum liegt (`cash_value_usd <
required_reserve_usd`) - anders als RM-1 (berechnet eine maximale
Positionsgroesse aus dem Risikobudget) und RM-2 (deckelt zusaetzlich auf das
verbleibende Allokations-Headroom), die beide VORWAERTSGERICHTET sind. RM-4
rechnete nie durch, ob die konkret vorgeschlagene Positionsgroesse SELBST die
Reserve unter das Minimum druecken wuerde - ein Kauf, der die Reserve von
z. B. 21 % auf 15 % senkt, wurde anstandslos durchgelassen; erst der
NAECHSTE Kaufversuch haette die dann bereits unterschrittene Reserve
gesehen. Verwandter, nicht behobener Nebeneffekt (bewusst zurueckgestellt,
siehe unten): mehrere KAUFEN-Empfehlungen im selben Batch-Lauf
(`signal_batch.py`/Budget-Allocator) werten unabhaengig voneinander gegen
denselben `db.get_all_holdings()`-Snapshot aus - keine "weiss" von den
anderen vorgeschlagenen Kaeufen desselben Laufs.

**Fix (umgesetzt):** analog zu RM-2s Allokations-Headroom wird jetzt ein
Cash-Reserve-Headroom (`cash_value_usd - required_reserve_usd`) berechnet
und per `min()` direkt in `max_position_size_usd` eingerechnet, sobald RM-4
selbst nicht bereits vetoed (im "OK"-Zweig) - ein einzelner Kauf kann die
Reserve dadurch nicht mehr unter das Minimum druecken, unabhaengig davon,
was sonst im Portfolio passiert. Kein neues Feld in `RiskPreCheckResult`
noetig (reine `max_position_size_usd`/`_eur`-Anpassung, wie bei RM-1/RM-2).

**Bewusst zurueckgestellt:** die Batch-Kumulierung (mehrere gleichzeitige
Kaufempfehlungen im selben Lauf, die sich gegenseitig nicht "sehen") -
Nutzer moechte hierzu erst mehr Informationen, bevor entschieden wird
(z. B. wie haeufig Nutzer tatsaechlich mehrere Tages-Empfehlungen gleichzeitig
exekutiert). Deutlich aufwaendiger als Fix 1 (braeuchte einen laufenden
Spend-Akkumulator ueber den gesamten Batch-Lauf), fuer einen eher seltenen
Grenzfall.

**Verifiziert:** 2 synthetische Testfaelle gegen ein handgebautes Portfolio
(BTC-Allokation bewusst unter dem RM-2-Limit gehalten, um RM-4 isoliert zu
pruefen) - (1) knappe Cash-Reserve (21 % bei 20 % Minimum, nur 100 USD
Headroom): Obergrenze korrekt auf ~100 USD gedeckelt, obwohl RM-1 rechnerisch
110.600 USD erlaubt haette; (2) reichlich Cash-Reserve: RM-1/RM-2 bleiben
weiterhin die bindende (kleinere) Grenze, RM-4 greift nicht faelschlich ein.

## Nachtrag (2026-07-18): Konfidenz-Kalibrierung nach dem echten CAT-Fall (fünf Bausteine A-E)

**Auslöser:** Nutzer teilte ein echtes, per E-Mail zugestelltes Spot-KAUFEN-
Signal für "CAT — Simon's Cat" (Konfidenz 80 %, Regime baer) zur eigenen
Experten-Durchsicht. Eigene Bewertung: schwach/kein starker Kauf -
widersprüchliche technische Konfluenz ("EMA-Ordnung bearish, aber MACD/RSI
bullish") wurde von der KI zwar in der Begründung erwähnt, aber NICHT in der
Konfidenz-Zahl (80 %) berücksichtigt; CRV lag nur knapp über der 2.0-
Pflichtgrenze (~2,08), was das binäre CRV-Gate bisher identisch zu einem
CRV von 4,0 behandelte. Nutzer bestätigte diese Einschätzung als deutlich
kritischer/besser als die Systembewertung selbst und beauftragte eine
umfassende Nachbesserung ("heute müssen wir versuchen umfangreiche
Verbesserungen einzuführen") - fünf Bausteine A-E, alle am selben Tag
umgesetzt. Gleichzeitig wurden zwei unabhängige E-Mail-Bugs gefunden und
behoben (siehe eigener Abschnitt oben: wissenschaftliche Notation bei sehr
kleinen Preisen, fehlende Regime-/Risiken-/Halte-Kriterium-Felder).

**A — Technischer-Konflikt-Deckel (`risk_gate.py::post_check()` +
`hebel_risk_gate.py::post_check_hebel()`):** `indicators/calculations.py::
summarize_confluence()` klassifiziert Indikator-Übereinstimmung bereits
deterministisch als `"bullish"|"bearish"|"neutral"|"gemischt"` - der
"gemischt"-Fall (weder bullish noch bearish dominiert) existierte exakt für
den CAT-Fall, wurde aber nirgends im Risiko-Gate ausgewertet. Jetzt: ist
`confluence.overall_bias == "gemischt"`, wird die Positionsgrößen-Obergrenze
(Spot) zusätzlich multiplikativ auf `technischer_konflikt_deckel_anteil`
(Config, Default 0.6) reduziert, bzw. bei Hebel als zusätzlicher Deckel-
Kandidat (`technischer_konflikt_hebel_deckel`, Default 3.0x) in die
bestehende `_hebel_deckel_kandidaten()`/`min()`-Logik eingereiht (Muster aus
dem Hebel-4-Punkte-Fix vom Vortag, siehe oben). Beide Pfade sind rein
deterministisch - unabhängig davon, ob das Modell den Widerspruch selbst
benennt.

**B — CRV-Distanz-abhängige Positionsgrößen-Skalierung ("CRV-Knapp-
Deckel"):** `CRV_MINIMUM = 2.0` war bisher ein binäres Gate (2,01 und 4,0
identisch behandelt). Neu: liegt `crv < CRV_MINIMUM * (1 +
crv_knapp_schwelle_relativ)` (Config, Default 0.2 → Schwelle 2.4), greift
eine weitere multiplikative Reduktion (`crv_knapp_positionsgroesse_
deckel_anteil`, Spot Default 0.6) bzw. ein weiterer Hebel-Deckel-Kandidat
(`crv_knapp_hebel_deckel`, Default 4.0x). Alle vier Spot-Deckel (Konfidenz-
Skalierung, Gegenszenario, Konflikt, CRV-Knapp) sind Geschwister-Blöcke, die
sich multiplikativ verketten (verifiziert: alle vier gleichzeitig aktiv
ergaben korrekt `1000 × 0.5 × 0.5 × 0.6 × 0.6 = 90 USD`); bei Hebel bleibt
es beim bestehenden `min()`-über-alle-Kandidaten-Prinzip (der kleinste
Deckel-Wert bindet, kein Produkt).

**C — bereits durch A+B abgedeckt:** die vom Nutzer gewünschte CRV-Distanz-
abhängige Skalierung ist identisch mit Baustein B (dieselbe Mechanik löst
beide Anliegen), kein separater Code-Pfad nötig.

**D — Gegenargument-Pflichtfeld statt zweitem LLM-Call (`analyst.py`
[Krypto+Aktien] + `hebel_analyst.py`):** Nutzer-Frage, ob eine adversariale
Selbstkritik zwingend zwei getrennte LLM-Calls braucht - Antwort: nein, ein
neues PFLICHT-Schema-Feld `gegenargument` wurde bewusst VOR `confidence_pct`
im JSON-Schema platziert. Da LLM-APIs JSON überwiegend sequenziell links-
nach-rechts erzeugen, "sieht" das Modell sein eigenes, bereits geschriebenes
Gegenargument, wenn es die Konfidenz-Zahl committet - eine kostengünstige
Annäherung an Chain-of-Thought-Selbstkorrektur ohne zweiten Aufruf (relevant
angesichts des knappen ~15-18-Calls/Tag-Groq-Budgets, siehe Memory
project_batch_signal_berechnung.md). Neue SYSTEM_PROMPT-Regel (22 in
`agent/krypto/analyst.py`, 18 in `agent/aktien/analyst.py`, 13 in
`agent/krypto/hebel_analyst.py`) verlangt das STÄRKSTE Gegenargument (nicht
ein Feigenblatt) und verbietet explizit die Kombination "genuin starkes
Gegenargument + Konfidenz > 75 %". `_validate()`/`_validate_hebel()`
erzwingen eine Mindestlänge (15 Zeichen) - ein leeres oder trivial kurzes
Gegenargument macht die gesamte Antwort ungültig (`AnalystResponseInvalid`).
Neues additiv migriertes Feld `gegenargument` (TEXT, nullable) auf `Signal`
und `HebelSignal` (`database/models.py` + `database/db.py::
_migrate_gegenargument_columns()`).

**E — Historische Trefferquote als Kalibrierungs-Fakt
(`backward_tracking.py::compute_win_rate_fact()`):** neue, rein lesende
Funktion aggregiert bereits aufgelöste Signale (`outcome_status` in
`take_profit_erreicht`/`stop_loss_erreicht`/`liquidation_wahrscheinlich`)
getrennt für `signals` ("spot" - Krypto UND Aktien zusammen, gleiche
Vereinfachung wie in `compute_provider_performance()`, Stichprobe zu klein
für eine weitere Aufspaltung) und `hebel_signals` ("hebel"). Gibt `None`
zurück, solange keine Signale aufgelöst sind (aktuell der Fall - reine
Infrastruktur). Unter `_MIN_SAMPLE_FUER_AUSSAGE = 15` Signalen bekommt das
Modell einen expliziten Ehrlichkeits-Hinweis im Fakt selbst
(`hinweis`-Feld), der vor Überschätzung einer kleinen Stichprobe warnt -
bewusst NUR eine grobe Gesamtzahl, kein Per-Asset/Per-Regime-Split. Neuer
Fakt `historische_erfolgsquote` in `build_facts()` (Krypto + Aktien) und
`build_hebel_facts()`, mit neuer SYSTEM_PROMPT-Regel (23/19/14), die das
Modell anweist, die Zahl NUR als schwaches Zusatzindiz zu behandeln.

**Config (`Basisinfos/config.yaml`):**
```yaml
# unter risiko: (Spot/Aktien)
technischer_konflikt_deckel_anteil: 0.6
crv_knapp_schwelle_relativ: 0.2
crv_knapp_positionsgroesse_deckel_anteil: 0.6

# unter risiko.hebel:
technischer_konflikt_hebel_deckel: 3.0
crv_knapp_schwelle_relativ: 0.2
crv_knapp_hebel_deckel: 3.0
```
Alle Startwerte unkalibriert (analog zu den bereits bestehenden Gegenszenario-
Deckeln) - nach echten Betriebsdaten anzupassen.

**Verifiziert:** Import-Smoke-Test aller geänderten Pipelines (keine
Zirkelimporte); synthetische Tests für `compute_win_rate_fact()` (leere DB →
`None`, kleine Stichprobe → Ehrlichkeits-Hinweis, große Stichprobe → kein
Hinweis, Hebel-Liquidation zählt als Fehlschlag); `gegenargument`-Validierung
(gültig akzeptiert, zu kurz/fehlend abgelehnt) für Spot-Krypto UND Hebel;
Konflikt-Deckel + CRV-Knapp-Deckel-Zusammenspiel bei Spot (multiplikativ,
alle vier Deckel gleichzeitig korrekt verkettet) und bei Hebel (`min()`-
Logik, korrekter bindender Grund im Hinweistext); echter Migrations- und
Kompatibilitätstest gegen eine Kopie der Produktions-DB (76 Spot- +
5 Hebel-Signale, neue Spalte vorhanden, `Signal(**dict(row))`/
`HebelSignal(**dict(row))` funktionieren mit `gegenargument=None` für
Alt-Zeilen, `compute_win_rate_fact()` liefert dort korrekt `None`).

**Bewusst zurückgestellt (eigene, dedizierte Session):** der vom Nutzer als
Favorit genannte historische Makro-Konstellationsvergleich (DXY/Aktien-
Blase/Ölpreis/Zinsen gegen historische Perioden mit bekanntem Ausgang) - als
mögliche zusätzliche Kalibrierungs-Basis für Spot/Hebel/andere Assets neben
Bär/Bulle/Regime identifiziert, aber bewusst NICHT im selben Aufwasch
umgesetzt (methodische Komplexität, siehe Memory
project_historischer_makro_konstellationsvergleich_idee.md). Ebenfalls
zurückgestellt: Wiederholungs-Erkennung (Punkt 4 der letzten Runde) für
Aktien nachrüsten - wurde beim Portieren von B+D nach `agent/aktien/
analyst.py` nicht mit angefragt, bleibt als latenter Punkt vorgemerkt.

## Nachtrag (2026-07-18, gleicher Tag): Historischer Makro-Konstellationsvergleich umgesetzt

**Auslöser:** Nutzer wollte das oben zurückgestellte Thema nicht lange
aufschieben ("möchte ich nicht zu lange nach hinten schieben - also asap
angehen") und beauftragte zwei Recherche-Stränge: was lässt sich frei
verfügbar nutzen, was muss selbst gebaut werden - sowie eine eigenständige
Krypto-Bewertung statt der Aktien-Methodik 1:1 zu übertragen.

**Recherche-Ergebnis (Build vs. Buy):** kein kostenloses fertiges Tool macht
"aktuelle Konstellation → historisches Analog → Wahrscheinlichkeit" als
nutzbaren Service. MacroMicro-API wäre das einzige nahe dran, kostet aber
5.000 $/Jahr - für dieses Nur-kostenlose-Werkzeuge-Projekt nicht tragbar.
Also Eigenbau, aber auf Basis bereits vorhandener, bereits integrierter
kostenloser Datenquellen (FRED, yfinance, blockchain.com) statt neuer
Abhängigkeiten - reduziert den Bauaufwand erheblich.

**Datenquellen (alle bereits im Projekt integriert, nur neu genutzt):**
FRED (`api/macro.py::get_fred_history()`) für DXY-Ersatz (`DTWEXBGS`, seit
2006), Fed Funds Rate (`FEDFUNDS`, seit 1954), 10-Jahres-Rendite (`DGS10`,
seit 1962), CPI (`CPIAUCSL`, seit 1913, YoY selbst berechnet), Ölpreis WTI
(`WTISPLC`, monatlich seit 1946 - bewusst länger zurückreichend als das
sonst im Projekt genutzte `DCOILWTICO`, wichtig für die 1970er-
Ölschock-Ära); yfinance (`api/yfinance_history.py::get_full_price_history()`)
für die S&P-500-Vollhistorie (^GSPC, seit 1927); blockchain.com
(`api/onchain.py::get_btc_full_price_history()`) für die BTC-Vollhistorie
seit 2009.

**Bewusst KEIN Shiller-CAPE** (methodisch der etabliertere Bewertungs-Proxy,
aber Yale liefert nur eine fragile Legacy-`.xls`-Datei ohne bestehende
Parser-Infrastruktur - `openpyxl` kann nur `.xlsx`, kein `xlrd`
installiert). Stattdessen: eine neue, selbst berechnete log-linear
Trend-Abweichung des S&P 500 (`indicators/calculations.py::
compute_log_linear_trend_deviation_series()`) - Regression von
log10(Preis) auf LINEARE Zeit (Jahre seit erstem Datenpunkt), bewusst
anders als das bestehende `compute_btc_log_regression_risk()` (log10(Preis)
auf log10(Tage seit Genesis) - ein Power-Law-Adoptionsmodell, das für einen
Aktienindex methodisch nicht passt). Synthetisch mit einer
10%-Jahr-Wachstumskurve gegengeprüft (Regression erkannte die Rate korrekt
wieder).

**Architektur:** neues Modul `agent/krypto/makro_analog.py` mit zwei neuen
DB-Tabellen (`makro_historie_monat` - monatliche Zeitreihe der 6
Konstellations-Dimensionen + SPX-/BTC-Schlusskurse, additiv gemerged wie
`macro_snapshot`; `makro_analog_ergebnis` - gecachtes Tages-Ergebnis als
JSON-Blob). Neuer täglicher Scheduler-Job `makro_analog_job()` (06:30, nach
Backward-Tracking) frischt die Historie auf und berechnet die Top-5
historischen Analoge neu - die teure Berechnung läuft NICHT pro Signal,
`build_facts()`/`build_hebel_facts()` lesen nur das gecachte Ergebnis
(`get_cached_makro_analog_fact()`).

**Ähnlichkeitsmetrik:** Euklidischer Abstand über Z-Score-normalisierte
Dimensionen, fehlend-Werte-tolerant (fehlt eine Dimension bei Kandidat ODER
aktuellem Monat, wird sie für DIESEN Vergleich übersprungen, nicht als 0
angenommen - gleiches Prinzip wie `risk_gate.py::_portfolio_values_usd()`).
**Live-Fund beim ersten echten Testlauf:** ohne Zusatzregel bestand die
Top-5-Liste aus fast identischen, nur wenige Monate auseinanderliegenden
Kandidaten (z. B. Feb/Mär/Mai/Jun/Jul desselben Jahres) - autokorreliertes
Rauschen statt unabhängiger historischer Vergleichspunkte, weil benachbarte
Monate fast immer ähnliche Makro-Werte haben. Fix: derselbe
`mindest_abstand_monate`-Parameter (Default 24) erzwingt jetzt zusätzlich
einen Mindestabstand ZWISCHEN den ausgewählten Analogen untereinander, nicht
nur gegenüber "jetzt". Nach dem Fix lieferte derselbe echte Testlauf fünf
genuin unabhängige Analoge über 20 Jahre verteilt (2006, 2015, 2018, 2022,
2024) mit einer plausibel breiten Streuung der Forward-Renditen (S&P
6-Monats-Vorwärtsrendite der Analoge reichte von −20,9 % bis +9,7 %).

**Krypto-Sonderbehandlung (Nutzer-Entscheidung):** BTC hat nur ~3 volle
Halving-Zyklen mit statistischem Gewicht, und diese 3 Zyklen waren
makro-mäßig selbst nicht vergleichbar (Nahe-Null-Zinsen 2013-2021 vs.
heute) - ein aggregiertes "BTC-Forward-Rendite über die Top-N-Analoge"-Feld
wäre Pseudo-Statistik mit irreführender Präzision. Deshalb liefert
`summarize_analogs_for_facts()` BTC-Forward-Renditen NUR pro einzelnem
Analog (null bei Analogen vor BTCs Existenz), aber KEIN aggregiertes Feld -
das ist STRUKTURELL so (das Feld existiert schlicht nicht im Fakt-Dict),
nicht nur per Prompt-Anweisung unterdrückt (P-10-Philosophie: das Modell
wird nie blind vertraut, die Versuchung wird also gar nicht erst als
fertiger Fakt angeboten). Für den S&P 500 WIRD ein Median-Aggregat über die
Top-N-Analoge geliefert - dort ist die Stichprobentiefe (Jahrzehnte, viele
unabhängige Analoge) deutlich größer und methodisch tragfähiger.

**Prompt-Integration:** neuer Fakt `historischer_makro_vergleich` in allen
drei `build_facts()`/`build_hebel_facts()`-Funktionen (Krypto-Spot, Aktien,
Hebel), mit je einer neuen SYSTEM_PROMPT-Regel (24 in `agent/krypto/
analyst.py`; 20 in `agent/aktien/analyst.py`; 15 in `agent/krypto/
hebel_analyst.py`). Krypto/Hebel-Formulierung verbietet
explizit, `btc_forward_*`-Werte als belastbare Statistik zu behandeln;
Aktien-Formulierung erlaubt die Nutzung von `spx_median_forward_*` als
groben Kalibrierungs-Input, mit Streuungs-Warnhinweis.

**Config (`Basisinfos/config.yaml`, neue Sektion `makro_analog:`):**
```yaml
top_n_analoge: 5
mindest_abstand_monate: 24
mindest_dimensionen: 3
```

**Verifiziert:** synthetischer Regressionstest (10%-Jahr-Wachstumskurve
korrekt zurückgerechnet); Migrations-/CRUD-Test gegen eine Kopie der
Produktions-DB (Merge-Verhalten, Cache-Schreiben/-Lesen); vollständiger
echter End-to-End-Lauf gegen FRED (5 Reihen, ~21 s), yfinance (^GSPC-
Vollhistorie seit 1927) und blockchain.com (BTC seit 2009) - 1.184 Monate
Historie aufgebaut, Analog-Suche + Fakt-Erzeugung geprüft; Diversitäts-Fix
gegen dieselben echten Daten erneut verifiziert (alle 5 Analoge ≥ 24 Monate
auseinander UND ≥ 24 Monate vor "jetzt"); 4 synthetische Edge-Case-Tests
(leere Historie, ein einzelner Monat, konstante Dimension ohne Streuung,
zu wenige überlappende Dimensionen) - alle degradieren graceful (`None`/
leere Liste) statt zu crashen; vollständiger Import-Smoke-Test aller
geänderten Pipelines nach der Verdrahtung.

**Bewusst zurückgestellt:** kein UI-Element für die Analoge selbst (z. B.
ein neuer Tab oder eine Karte im Regime-Tab) - der Fakt fließt direkt in
die LLM-Signale ein, eine separate Visualisierung war nicht Teil des
heutigen Auftrags und kann bei Bedarf nachgerüstet werden.

## Nachtrag (2026-07-18, gleicher Tag): Rohstoff-Pipeline (Phase 2) + Portfolio-Hedge-Logik

**Auslöser:** Nutzer bekräftigte, die Multi-Asset-Roadmap Phase 2-4
(Rohstoffe/ETF/Discovery, siehe Memory project_multi_asset_erweiterbarkeit.md)
als nächstes Großthema angehen zu wollen, und ergänzte explizit die
"Bitpanda-Sonderkonstellation und Absicherung" - da Bitpanda keine echten
Krypto-Short-Positionen anbietet, sollten die bereits gehaltenen inversen/
gehebelten Aktienindex-ETFs (DBPK, 3QSS) als praktischer Kompromiss-Hedge
gegen das GESAMTE Portfolio (nicht nur Aktien) eine eigene Bewertungslogik
bekommen. Nutzer wählte den vollen Durchstich beider Bausteine am selben Tag.

### Baustein 1: Rohstoff-Pipeline (`agent/rohstoff/`)

Neues, eigenständiges Modul (gleiche Architektur-Entscheidung wie bei Aktien -
kein verallgemeinertes Framework). Vier ETCs (OD7N Silber, OD7H Gold, OD7C
Kupfer, OD7L Erdgas, `assetklasse: rohstoffe`). Kein KGV-Äquivalent für
physische Rohstoffe - stattdessen `makro_ueberlagerung` (10J-TIPS-Realrendite
DFII10, Dollar-Index DTWEXBGS, Industrieproduktion INDPRO - alle via FRED)
und `positionierung` (CFTC-COT-Report, "Managed Money"-Netto-Positionierung,
neues Modul `api/cftc_cot.py`, kostenlose Socrata-API, kein Key nötig).

**Datenquellen-Recherche (Build vs. Buy):** kostenlose, echte APIs identifiziert
für COT (`publicreporting.cftc.gov`, Dataset `72hh-3qpy`, live verifiziert für
alle 4 Rohstoffe) und FRED-Realrendite/Dollar/Industrieproduktion. Bewusst
NICHT einbezogen (dokumentierte Lücke, spätere Erweiterung möglich): EIA-
Erdgaslager (bräuchte neuen API-Key, nicht heute testbar), COMEX-/LME-
Lagerbestände (Dateiformat-Risiko, gleiche Kategorie wie das bereits
verworfene Shiller-CAPE), ETF-Gold-/Silber-Bestandsflüsse (CSV-Format
ungeprüft).

**Kritischer Live-Fund bei der Verifikation:** die WisdomTree-ETC-
Börsennotierungen selbst (`asset.yfinance_symbol`) liefern über yfinance
KEINE `.history()`-Daten - nur `fast_info` (aktueller Kurs) funktioniert,
dieselbe Einschränkung, die 2026-07-09 bereits für OD7N/3QSS dokumentiert
wurde (siehe Memory project_multi_asset_yfinance_symbols.md), hier aber
erstmals fest eingebaut vorausgesetzt und dadurch übersehen. **Fix:**
technische Analyse (EMA/MACD/RSI/Bollinger/ATR/Fibonacci/S&R) wird stattdessen
aus dem liquiden, kontinuierlichen Futures-Kontrakt abgeleitet, den das ETC
nachbildet (GC=F/SI=F/HG=F/NG=F, 25+ Jahre Historie, live verifiziert).

**Zweiter, direkt daraus folgender Fund:** Futures- und ETC-Kurs liegen auf
VÖLLIG unterschiedlichen absoluten Preisskalen (z. B. Gold-Future ~4.000
USD/Unze vs. das Bruchteils-ETC bei ~18-20 USD) - ohne Korrektur wären
EMA/Bollinger/ATR/Support-Resistance/Fibonacci-Level absolute Preis-Level auf
der FALSCHEN Skala, eine daraus abgeleitete Stop-Loss-Zone wäre um
Größenordnungen falsch. **Fix:** `_rescale_ohlc_zum_etc_kurs()` skaliert die
GESAMTE Futures-Historie mit einem einzigen, heute gültigen Faktor (ETC-Kurs
/ letzter Futures-Kurs) auf die ETC-Größenordnung, bevor sie in
`build_technical_snapshot()` geht - technische Muster (Trendrichtung,
Support/Resistance-Abstände in Prozent) bleiben dabei unverändert, nur die
absolute Preisachse verschiebt sich. Live verifiziert: ATR/Preis-Verhältnis
nach der Korrektur für alle 4 ETCs plausibel im Bereich 0,018-0,045 (vorher
absurd, z. B. Gold-ATR von ~40 USD auf einen ~18-USD-Kurs angewendet).

**Dritter Fund (Robustheits-Lücke, ebenfalls behoben):** `price_usd` wird für
diese EUR-notierten ETCs erst nachträglich aus `price_eur * eur_usd_fx_rate`
abgeleitet und kann fehlen, wenn beim letzten Preisabruf kein aktueller FX-Kurs
vorlag - ohne explizites Gate hätte das Fehlen von `price_usd` die Skalierung
still auf die (falsche) Futures-Skala zurückfallen lassen. Neuer Gate-Check
VOR der Skalierung: fehlt `price_usd`, wird das Signal als `gate_passed=False`
mit klarem Grund abgelehnt statt eine falsch skalierte Analyse zu erzeugen.

**Verifiziert:** Live-Test aller 4 ETCs gegen echtes FRED/CFTC/yfinance
(Fakten-Generierung + Skalierungs-Korrektheit), ein echter End-to-End-Lauf mit
echtem Groq-Call (OD7H/Gold: HALTEN, 60 % Konfidenz, korrekt begründet mit
gemischter Konfluenz + belastenden Makro-Faktoren + COT-Positionierung).

### Baustein 2: Portfolio-Hedge-Logik (`agent/hedge/`)

Bewusst ANDERS architektiert als Aktien/Rohstoff: KEINE
Einzeltitel-Technikanalyse (3QSS hat wie die Rohstoff-ETCs keine
yfinance-Historie, UND ein Hedge-Instrument sollte ohnehin nicht nach eigener
technischer Stärke bewertet werden, sondern danach, wie viel ungesichertes
PORTFOLIO-Risiko es gerade abdeckt). KEIN `risk_gate.pre_check()`/
`post_check()` (RM-1/2/4/5 + CRV-Pflicht sind für profitorientierte
Directional-Wetten gebaut, nicht für eine Absicherungs-Position) - eigener,
einfacherer Deckel.

**Kernmechanik:** `_compute_portfolio_exposure()` berechnet die ungesicherte
Long-Exposure (Portfolio-Wert ohne Hedge-Instrumente und ohne
Cash-Äquivalente) sowie die aktuelle Hedge-Abdeckung (Summe über ALLE
gehaltenen Hedge-Instrumente, je mit ihrem Hebelfaktor multipliziert - 1 USD
in einem 3x-Short-ETF deckt effektiv 3 USD Long-Exposure ab). Ein
konfigurierbares Ziel-Maximum (`hedge.max_abdeckung_anteil`, Default 1.0 =
100 %) begrenzt deterministisch, wie viel zusätzliche Hedge-Position
vorgeschlagen werden darf.

**Live-Fund während der Verifikation:** `_portfolio_values_usd()` lässt ein
Symbol ohne bekannten Preis (P-10) einfach aus der Wertesumme weg - ein
ANDERES, tatsächlich gehaltenes Hedge-Instrument mit fehlendem `price_usd`
hätte die Gesamt-Abdeckung dadurch STILLSCHWEIGEND unterschätzt (0 statt des
echten Werts), was einen KAUFEN/NACHKAUFEN-Vorschlag zu einer unbemerkten
Übersicherung hätte führen können. **Fix:** `fehlende_preise`-Erkennung +
explizite Warnung im Fakt (`berechnung_unsicher_fehlende_preise`) + das
verbleibende Hedge-Budget wird in diesem Fall vorsorglich auf 0 gedeckelt
(VERKAUFEN/HALTEN bleiben davon unberührt, nur ein Hedge-AUFBAU wird
blockiert). Live gegen das echte Portfolio verifiziert: mit vollständigen
Preisen korrekt 1.768 USD Gesamt-Abdeckung (1.739 DBPK × 0,163 × 2 + 218
3QSS × 1,836 × 3 = 12,7 % der 13.936 USD Long-Exposure), ohne einen der
beiden Preise korrekt auf 0 USD Budget gedeckelt mit klarer Warnung.

**Volatility-Decay-Warnung:** neue SYSTEM_PROMPT-Regel verlangt, gehebelte/
inverse ETFs NIE als Buy-and-Hold-Position zu behandeln (tägliches
Rebalancing erzeugt bei Seitwärtsbewegung strukturellen Wertverlust,
unabhängig von der Richtung des zugrunde liegenden Index) - explizit in
`key_risks`/`long_reasoning.risiko` zu benennen.

**Verifiziert:** Facts-Generierung + Exposure-Berechnung gegen echtes
Portfolio (mit und ohne fehlende Preise), ein echter End-to-End-Lauf mit
echtem Mistral-Call (DBPK: HALTEN, 60 % Konfidenz, korrekt begründet mit
12,7 % bestehender Abdeckung + inaktivem Aktien-Bärenmarkt-Indikator +
Decay-Erwägung).

**Config (`Basisinfos/config.yaml`):**
```yaml
hedge:
  max_abdeckung_anteil: 1.0
```

**UI-Wiring:** `ui/signals_view.py` verzweigt jetzt nach `assetklasse ==
"rohstoffe"` (→ `agent/rohstoff/pipeline.py`) bzw. Symbol-Zugehörigkeit zu
`agent.hedge.pipeline.SYMBOL_ZU_HEBEL_FAKTOR` (→ `agent/hedge/pipeline.py`),
zusätzlich zur bestehenden Aktien-/Krypto-Verzweigung.

**Bewusst zurückgestellt:** Themen-ETFs (Phase 3) und Discovery (Phase 4) der
Multi-Asset-Roadmap - eigene, spätere Themen. EIA-Erdgaslager/COMEX-Lagerbestände/
ETF-Bestandsflüsse als Rohstoff-Datenquellen-Erweiterung (siehe oben).

## Nachtrag (2026-07-18, gleicher Tag): Bugfix Bitpanda-Listing-Spalte fuer Aktien/Rohstoffe/Hedge

Nutzer-Fund: die Watchlist zeigte fuer alle Nicht-Krypto-Assets (Aktien, ETFs,
Rohstoffe/ETCs) in der "Bitpanda"-Spalte hartkodiert "-", statt eines echten
✓/✗-Status. Ursache war eine seit 2026-07-09 bestehende, seit dem
2026-07-16-Ausbau ueberholte Annahme in `ui/app.py::_refresh_watchlist_from_db()`:
"Bitpanda-Listing-Check ergibt fuer Nicht-Krypto keinen Sinn". Das stimmte zum
Zeitpunkt des urspruenglichen Kommentars (reines Krypto-Multi-Asset-Tracking),
war aber seit `api/bitpanda.py::get_listed_non_crypto_assets()` (2026-07-16,
schliesst die Aktien-Pipeline-Luecke) nicht mehr aktuell: `agent/aktien/pipeline.py`
und `agent/rohstoff/pipeline.py` berechnen den echten Listing-Status seither
laengst fuer den Bitpanda-Veto (`risk_gate.py::pre_check()`) - er wurde nur nie
in der allgemeinen Watchlist-UI angezeigt.

**Fix:** `ui/app.py` laedt jetzt zusaetzlich zum bestehenden Krypto-Katalog
(`self._bitpanda_assets`) den Nicht-Krypto-Katalog
(`self._bitpanda_non_crypto_assets`, ueber `get_listed_non_crypto_assets()`,
gleiches P-10-Fehlschlag-Verhalten: `None` bei Abrufsfehler statt falschem
Wert). Die Zeilen-Render-Logik waehlt den passenden Katalog nach
`asset.assetklasse` und nutzt fuer beide denselben `bitpanda_is_listed()`-
Vergleich - keine getrennte Logik mehr fuer Krypto vs. Nicht-Krypto. Deckt
damit einheitlich Aktien (`stock`), Rohstoff-ETCs (`etc`) UND die
Hedge-ETFs DBPK/3QSS (`etf`, `NON_CRYPTO_ASSET_GROUPS` in `api/bitpanda.py`) ab.

**Verifiziert:** Logik-Smoke-Test (Krypto BTC/ETH, Aktie PLTR, Rohstoff-ETC
OD7H, Hedge-ETF DBPK, unbekanntes Symbol, sowie Katalog-Fehlschlag-Fall) -
alle 7 Faelle korrekt.

## Nachtrag (2026-07-18, gleicher Tag): VIX-Frühindikator als beschreibender Fakt

Direkt im Anschluss an die Bitpanda-Listing-Bugfix-Bestandsaufnahme fragte der
Nutzer explizit nach dem "nachlaufenden M2"-Konzept und ob wir bereits für
den Aktien-Bärenmarkt aufgestellt sind. Antwort: das bestehende
`equities_baermarkt_aktiv`-Flag ist ein reiner **Drawdown-Schwellenwert**
(S&P 500/Nasdaq ≥20 % unter 5-Jahres-Hoch, siehe AZ-4 Baustein 2) - NACHLAUFEND.
VIX (CBOE Volatility Index) ist dagegen ein **VORLAUFENDES** Optionsmarkt-
Stimmungssignal, im Code bisher komplett ungenutzt (kein einziger Treffer).
Nutzer bestätigte nach Bestandsaufnahme: erst die kleine Rohstoff-Lücke
(aktien_baermarkt-Fakt, siehe oben) schließen, dann VIX "mit korrekter
Implementierung" ergänzen - bewusst NUR als beschreibender LLM-Fakt (KEIN
deterministischer Deckel), analog `liquiditaets_regime`/`equities_baermarkt`.

**Datenquelle:** `api/yfinance_history.py::get_vix_reading()` - nutzt
denselben Timeout-geschützten `get_full_price_history("^VIX")` wie
`get_equities_bear_market_status()`, EIGENER try/except in
`_fetch_boden_zielzone_context()` (P-10: ein VIX-Ausfall darf die
Aktien-Bärenmarkt-Fakten nicht mit sich reißen und umgekehrt - zwei
unabhängige yfinance-Ticker-Abrufe).

**Bänder (branchenübliche CBOE-Praktiker-Konvention, KEIN projekteigener
Schwellenwert wie bei den equities_baermarkt-[OFFEN]-Werten):** <20 "ruhig",
20-30 "erhöht", 30-40 "gestresst", >40 "krise" - `agent/krypto/regime.py::
VIX_BANDS`/`_vix_label()`.

**Caching:** täglich über `macro_snapshot.vix_wert` (neue additive Spalte,
gleiches COALESCE-Upsert-Muster wie alle anderen Boden-Zielzone-Felder,
`database/db.py::_MACRO_SNAPSHOT_NEW_COLUMNS`).

**Konsum:** neuer `regime.vix.{wert,label}`-Fakt in ALLEN VIER Analysten
(Krypto/Aktien/Rohstoff/Hedge) - dasselbe Synergie-Muster wie beim
Bitpanda-Listing-Fix: EIN Berechnungsort (`compute_current_regime()`) statt
vier Einzellösungen. Rohstoff-spezifisch: "gestresst"/"krise" verstärkt bei
Gold/Silber die Safe-Haven-Logik, bei Kupfer/Erdgas eher neutral. Hedge-
spezifisch: zusätzliches (schwächeres als `aktien_baermarkt.aktiv`) Signal
FÜR mehr Absicherung, da VIX früher ausschlagen kann als der Drawdown.

**Verifiziert:** `_vix_label()` gegen alle 4 Bandgrenzen (8 Testfälle) +
echter Live-Abruf gegen `^VIX` (18,77 → "ruhig") + DB-Migrationstest gegen
Kopie der Produktions-DB (Spalte fehlte vorher, Upsert/Reread danach korrekt)
+ echter End-to-End-Lauf von `compute_current_regime()` gegen die migrierte
DB-Kopie (liefert echten VIX-Wert + korrektes Label im vollständigen
Regime-Objekt, inkl. BTC-Regime "baer" parallel korrekt berechnet).

**Bewusst NICHT umgesetzt:** kein deterministischer Deckel (Nutzer-
Entscheidung), keine Anzeige in `ui/regime_view.py`/Remote-Status-Karte
(bestehendes `equities_baermarkt` ist dort ebenfalls nicht enthalten -
konsistent, kein Präzedenzbruch) - beides mögliche spätere Ausbaustufen.

**Nebenfund behoben (selbes Datum):** `agent/rohstoff/analyst.py::build_facts()`
gab `aktien_baermarkt`/`equities_baermarkt` (aus `compute_current_regime()`)
nicht als LLM-Fakt weiter, obwohl Krypto-, Aktien- und Hedge-Analyst das tun.
Ergänzt: `regime.aktien_baermarkt.{aktiv,begruendung}` im Facts-Dict + neue
SYSTEM_PROMPT-Regel-8-Ergänzung (Gold/Silber tendenziell Safe-Haven-Nachfrage
bei Aktien-Bärenmarkt, Kupfer/Erdgas eher neutral/leicht belastend wegen
schwächerer Industriekonjunktur) - Gewichtung je `asset.symbol`, analog Fakt 9.
Syntax- und Feld-Smoke-Test bestanden (`equities_baermarkt_aktiv`/
`_begruendung` existieren exakt so auf `RegimeResult`, keine Kollision mit
`_FREMDE_KONTAMINATIONS_BEGRIFFE`).

## Nachtrag (2026-07-18, gleicher Tag): Detailanalyse Bärenmarkt-Schwellenwerte + VIX als zweiter Boden-Zielzone-Trigger

Nutzer bat um eine Detailanalyse der vier `[OFFEN]`-Parameter in
`boden_zielzone` (`reifegrad_daempfer_staerke`, `equities_baermarkt_
schwelle_prozent`, `equities_baermarkt_lookback_jahre`,
`equities_overlay_shift_std`) statt einer schnellen Einschätzung, mit einem
wichtigen Korrektur-Einwand: die Standard-Bärenmarkt-Definition (20% Drawdown)
gilt für Aktienindizes, NICHT für BTC — dort sind 50-70%+ historisch die
Norm. Das führte zu einer echten, datengestützten Analyse statt einer
Bauchgefühl-Antwort.

**Echte historische BTC-Zyklus-Böden nachgerechnet** (yfinance BTC-USD seit
2014, laufendes ATH + Drawdown, Phasenerkennung zwischen neuen ATHs):
2015-01-14 (-61%), 2018-12-15 (-83%), 2022-11-21 (-77%) — normale
Bullenmarkt-Korrekturen liegen dagegen bei 15-35% und sind deutlich häufiger,
sollten nicht mit echten Zyklus-Bärenmärkten verwechselt werden.

**Wichtiger Fund:** diese 3 Daten sind EXAKT dieselben, die bereits in
`indicators/calculations.py::BTC_CYCLE_BOTTOM_DEVIATIONS_STD = (-1.16,
-0.78, -1.26)` (Kommentar: "2015-01-14, 2018-12-15, 2022-11-21") verwendet
werden — die BTC-eigene Boden-Zielzone ist also bereits sauber gegen die
echten historischen Böden kalibriert, nur als Log-Regressions-Abweichung
(Std.), nicht als rohe %-Zahl. Das war beim ersten Analyse-Durchgang
übersehen worden.

**Trefferquoten-Analyse:** geprüft, ob `equities_baermarkt_aktiv` (S&P500/
Nasdaq, 20%/5J) an den 3 echten BTC-Böden aktiv gewesen wäre:

| BTC-Boden | S&P500-DD (5J) | Nasdaq-DD (5J) | VIX (Tag) | VIX-Max ±10 Tage |
|---|---|---|---|---|
| 2015-01-14 | -3,2% | -3,0% | 21,5 | 22,4 |
| 2018-12-15 | -11,3% | -14,8% | 21,6 | **36,1** |
| 2022-11-21 | -17,3% | -30,6% | 22,4 | 24,5 |

Ergebnis: **1 von 3** (nur 2022, über Nasdaq). `lookback_jahre`-Änderungen
hätten daran nichts geändert (die Tiefe lag unter 20%, nicht das Zeitfenster
war das Problem) — `schwelle_prozent` selbst ist Marktkonvention, keine
projekteigene Erfindung, daher nicht weiter kalibrierbar.

**VIX als zweiter, unabhängiger ODER-Trigger:** nach erneuter Prüfung (erste
Einschätzung "das wäre dieselbe Overfitting-Falle wie MVRV" war zu pauschal
- Unterschied: VIX-Bänder 20/30/40 sind branchenübliche CBOE-Konventionen,
NICHT aus diesen 3 Punkten gefittet) umgesetzt: `_boden_zielzone()` in
`agent/krypto/regime.py` löst den Overlay jetzt bei
`equities_baermarkt_aktiv ODER vix_label in (gestresst, krise)` aus, nutzt
denselben `overlay_shift_std` (kein zweiter, unbelegbarer Parameter).
2018 wäre damit zeitversetzt erfasst worden (VIX-Peak 36,1 wenige Tage um
den Boden) → **realistische Verbesserung von 1/3 auf ~2/3**, 2015 bleibt
weiterhin unerreicht (VIX nur ~21,5, "erhöht" statt "gestresst"). Bei n=3
bewusst mit Vorsicht zu interpretieren, aber ein echter, nicht erfundener
Fortschritt.

**Bewusst NICHT geändert:** `equities_baermarkt_aktiv` als eigenständiger
Fakt (von Krypto-, Aktien-, Rohstoff- und Hedge-Analyst konsumiert) bleibt
unverändert eng definiert ("Aktienindex im Drawdown") - der neue VIX-Pfad
wirkt NUR innerhalb des Boden-Zielzone-Overlays, nicht auf diesen Fakt.
`reifegrad_daempfer_staerke`/`equities_overlay_shift_std` bleiben
unveränderte Schätzwerte - bei n=3 Vergleichspunkten wäre jede weitere
Kalibrierung Overfitting, `config.yaml`-Kommentare entsprechend ehrlich
umformuliert (kein `[OFFEN]` mehr, sondern "bewusst nicht weiter
kalibrierbar" mit Begründung).

**Verifiziert:** 6 synthetische Testfälle (nur Aktien/nur VIX gestresst/nur
VIX krise/beide/keins/beide unbekannt) - alle korrekt; echter End-to-End-Lauf
von `compute_current_regime()` gegen Kopie der Produktions-DB (aktueller VIX
18,77 "ruhig" + `equities_baermarkt_aktiv=False` → Overlay korrekt NICHT
ausgelöst, keine Regression gegenüber dem bisherigen Verhalten).


## Nachtrag (2026-07-18, gleicher Tag): Multi-Asset-Batch - automatische Signal-Erzeugung fuer Aktien/Rohstoffe/Hedge

Nutzer-Fund: das letzte VST-Signal war 3 Tage alt, kein Kaufsignal
erhalten. Bestandsaufnahme (echte Notebook-Diagnose via
extract_notebook_diagnose.py, siehe Memory project_multi_asset_batch)
zeigte: die Krypto-Pipeline lief normal weiter, aber VST/PLTR/OD7N-L/DBPK/
3QSS hatten seit Erstellung der Rohstoff/Hedge-Pipelines KEINEN einzigen
automatischen Bewertungsversuch - agent/krypto/budget_allocator.py
enthaelt keine Referenz auf aktien/assetklasse, diese 8 Assets waren
ausschliesslich ueber den manuellen "Signal berechnen"-Klick erreichbar.

**Bewusst NICHT in den bestehenden 15-Min-Krypto-Allocator integriert**
(Nutzer-Auftrag "Job bauen, aber vorher genau durchdenken"):
- Die strikte Tier-1>2>3-Kaskade (Hebel>Marktscan>Spot,
  budget_allocator.py::_verteile_budget()) wuerde ein Tier 4 an
  geschaeftigen Tagen nie erreichen - genau das Problem, das geloest
  werden soll.
- Aktien/Rohstoffe/Hedge bewegen sich strukturell langsamer
  (Boersenzeiten/Wochenenden, 5-Tage-OHLC-Staleness-Schwelle vs. Kryptos
  2 Tage) - der 15-Min-Takt waere verschwendet.
- Kein Regressionsrisiko fuer den gut getesteten, kritischen Krypto-Pfad.

**Neues Modul agent/multi_asset_batch.py::run_multi_asset_batch()** -
eigenstaendige, kleinere Variante desselben Fallback-Musters wie
budget_allocator.py::_mit_fallback_chain()/_mit_conn() (Groq -> Mistral
-> Gemini, eigene Connection je Call), bewusst NICHT die private
Closure aus budget_allocator.py wiederverwendet (Entkopplung von einem
kritischen, bereits gut funktionierenden Pfad). Nutzt dasselbe geteilte
Tagesbudget (count_real_llm_calls_today_by_provider() zaehlt bereits
assetklassen-uebergreifend ueber die signals-Tabelle) - kein separates
Kontingent noetig.

**Cooldown bewusst nur 2-stufig** (kein drittes "ausgemustert"-Level wie
bei Krypto, alle 8 Assets sind beobachtungsstatus: beobachtung):
"gehalten" live aus der holdings-Tabelle abgeleitet (identisches Muster
wie signal_batch.py), cooldown_stunden_gehalten: 24 /
cooldown_stunden_beobachtet: 72 (config.yaml multi_asset_batch) -
deutlich traeger als Kryptos 10h/20h, passend zur langsameren
Marktdynamik.

**Neuer Job** scheduler/background.py::multi_asset_batch_job(),
ursprünglich registriert mit MULTI_ASSET_BATCH_INTERVAL_HOURS = 12
(reines Intervall + next_run_time=jetzt bei jedem Neustart) - der
Job-Takt gab nur Redundanz bei einem verpassten Lauf, der eigentliche
Rhythmus lief ueber die Cooldown-Werte. Eigener Lock
(multi_asset_batch_lock), P-8-Gate (nur aktiv mit groq_client). Neue
_notify_multi_asset_signal() (E-Mail bei handlungsrelevanten Signalen,
NIE bei HALTEN) - wiederverwendet dieselben Formatierungs-Helfer wie
Spot/Hebel (_formatiere_top_gruende/_formatiere_key_risks/
_formatiere_halte_kriterium/_formatiere_positionsgroesse_und_tranchen),
keine Duplikation.

**Nachtrag (2026-07-20): Quotrix-Handelsfenster-Fix.** Bitpandas Aktien/
ETFs/ETCs laufen seit 2026 ueber die Quotrix-Boerse (Duesseldorf), mit
echten, begrenzten Handelszeiten (Mo-Fr 07:30-23:00 CET), NICHT 24/7 wie
Krypto (siehe Memory project_bitpanda_exchange - erst bei der Recherche
zur Eigentumsstruktur/Real-Securities-Frage entdeckt). Das alte reine
Intervall mit next_run_time=jetzt bei jedem Neustart konnte zu jeder
Uhrzeit (auch nachts) ein Signal mit Kurszonen erzeugen, die auf einem
Stunden/Tage alten Schlusskurs basierten UND vom Nutzer erst zum
naechsten Handelsstart ueberhaupt umsetzbar waren. Jetzt fester Cron
(MULTI_ASSET_BATCH_CRON_HOURS = "9,19", nur Mo-Fr) statt Intervall, kein
next_run_time-Sofortstart mehr - ein Neustart wartet bewusst bis zum
naechsten reguleaeren Takt.

**Nachtrag (2026-07-20): OI-Abdeckungs-Warnung respektiert jetzt den
Hebel-Pruefung-Toggle.** Echter Nutzer-Fund: CANTON wurde ueber den
Hebel-Pruefung-Toggle abgeschaltet (siehe Kap. "SOL-Tranchen + Hebel-
Pruefung-Toggle"), meldete aber ueber die persistente OI-Abdeckungs-
Warnung (siehe Kap. "Persistente OI-Abdeckungs-Warnung") weiterhin per
E-Mail "seit 9 aufeinanderfolgenden Laeufen keine OI-Daten" - obwohl
laengst keine neuen Laeufe mehr fuer dieses Symbol stattfanden. Ursache:
`oi_abdeckung_status.konsekutive_fehlschlaege` wird ausschliesslich beim
tatsaechlichen Screening-Lauf aktualisiert - ein per Toggle
abgeschaltetes Symbol friert einfach beim letzten Stand ein, der aber
weiterhin >= Schwelle blieb und nach jedem Cooldown-Ablauf erneut eine
(inhaltlich falsche) Warnmail ausloeste.
db.py::get_symbole_mit_ueberschrittener_oi_schwelle() prueft jetzt per
LEFT JOIN gegen asset_hebel_settings zusaetzlich den Toggle-Status
(COALESCE-Default 1/erlaubt, wenn keine Zeile existiert) - abgeschaltete
Symbole werden von der Warnung ausgenommen, unabhaengig vom eingefrorenen
Zaehlerstand.

**Verifiziert:** _kandidaten() liefert exakt die erwarteten 8 Assets
(VST/PLTR/OD7N/OD7H/OD7C/OD7L/DBPK/3QSS), korrekt auf ihre Pipeline
gemappt. _ist_faellig() gegen 5 synthetische Cooldown-Faelle (gehalten/
beobachtet, jeweils knapp unter/ueber der Schwelle, kein Vorsignal). Echter
End-to-End-Lauf gegen Kopie der Produktions-DB: VST-Preis live aktualisiert
(vorher gate_passed=False, "Preis veraltet" korrekt erkannt), danach
echter Groq-Call erfolgreich (gate_passed=True, gegenargument befuellt,
provider_je_symbol={"VST": "groq"}), Cooldown blockierte einen sofortigen
zweiten Lauf korrekt. Kompletter Job-Wrapper (multi_asset_batch_job())
inkl. Lock/E-Mail-Pfad fehlerfrei durchgelaufen (kein Versand bei HALTEN,
wie erwartet).


## Nachtrag (2026-07-18, gleicher Tag): Multi-Asset-Vollstaendigkeitspruefung -
## Themen-ETF-Pipeline + 6 Konsistenz-Fixes

**Ausloeser:** Nutzer-Nachfrage "welche Assetklassen haben wir jetzt konkret
und wie sind diese unterteilt" fuehrte zur Live-Watchlist-Abfrage (55 Assets:
42 Krypto, 7 etf, 4 Rohstoffe, 2 Aktien) und dabei zum Fund, dass 5 der 7
"etf"-Assets (VVMX/X136/EXH3/CEBS/ISOC - Themen-/Sektor-ETFs: Seltene Erden/
Bioenergie/Food&Bev/Kupferminen/Agribusiness) seit ihrer Ersterfassung in
config.yaml OHNE JEDE Pipeline dastanden - weder im neuen Multi-Asset-Batch
(nur aktien/rohstoffe/Hedge-Symbole beruecksichtigt) noch sauber im manuellen
UI-Klick (fielen dort auf die Krypto-Pipeline durch, die weder CoinGecko-ID
noch Kraken-Symbol fuer sie kennt).

Nutzer-Auftrag danach: "wir sollten das multiasset Thema jetzt vollinhaltlich
abschliessen" - vollstaendiger Audit ueber API-Monitoring/Regelwerksuebersicht/
Marktscan/Feature-Paritaet/Doku-Aktualitaet ueber alle 4 Nicht-Krypto-Pipelines
(Aktien/Rohstoffe/Hedge + die neue Themen-ETF-Pipeline). Ergab 7 konkrete
Befunde, alle in dieser Runde abgearbeitet:

### 1. Themen-ETF-Pipeline (agent/themen_etf/)

Neues, eigenstaendiges Modul (gleiche Architektur-Entscheidung wie bei Aktien/
Rohstoffen - siehe Spezifikation.md "Zielarchitektur fuer Multi-Asset-
Erweiterbarkeit"), mirror von agent/rohstoff/. Entfernt gegenueber Rohstoff:
makro_ueberlagerung (kein sauberer Treiber-Bezug) + positionierung
(CFTC-COT existiert nur fuer Rohstoff-Futures). Neu: sektor_rotation - relative
Staerke des ETFs gegenueber einem breiten Markt-Benchmark (SPY) ueber 30/90
Handelstage, berechnet aus bereits vorhandener OHLC-Historie (KEIN neuer
externer Datenanbieter - Ersatz fuer das fehlende KGV/COT-Aequivalent).

**Live-Fund bei der Verifikation:** anders als die duenn gehandelten
WisdomTree-Rohstoff-ETCs haben die meisten UCITS-Themen-ETFs eine echte,
direkt handelbare yfinance-Historie (VVMX/EXH3/CEBS live bestaetigt, 778-4707
Handelstage) - KEIN Futures-Proxy-Workaround noetig. X136 (Boerse Berlin-
Notierung) liefert dagegen 0 Punkte ("Period 'max' is invalid"), ISOC hat
eine seit 2025-09-10 eingefrorene Historie (>10 Monate) - fuer beide greift
bewusst NUR das bestehende Staleness-Gate (gate_passed=False, sauber
degradiert), KEIN Ersatz-Ticker gesucht (P-10: sauber degradieren statt eine
fragile Ersatzloesung erzwingen; kann spaeter nachgeruestet werden, falls
gewuenscht).

Verdrahtet in ui/signals_view.py (_themen_etf_watchlist, _run_pipeline()-
Branch, _asset_by_symbol()/_refresh_list()-Listen ergaenzt - waren zunaechst
uebersehen und haetten die 5 Themen-ETFs sonst weiterhin unsichtbar in der
Signale-Tab-Liste gelassen) UND in agent/multi_asset_batch.py
(_kandidaten()/_pipeline_fuer() - Multi-Asset-Batch deckt jetzt 13 statt 8
Assets ab).

### 2. API-Monitoring-Luecke

api/cftc_cot.py trackt korrekt via @track_api_health("cftc_cot"), tauchte
aber in remote/server.py::API_HEALTH_GROUPS in KEINER der drei Gruppen auf -
die API-Status-Karte zeigte CFTC-Gesundheit also nie an, obwohl die Daten in
der DB vorhanden waren. Ergaenzt zu api-health-makro.

### 3. Regelwerksuebersicht-Luecke

agent/krypto/regelwerk_parameter.py (Parameter-Uebersicht-Tab/-Karte) war
komplett Krypto-fokussiert - enthielt keinen einzigen Hedge- oder Multi-Asset-
Batch-Parameter. Ergaenzt: hedge.max_abdeckung_anteil,
multi_asset_batch.cooldown_stunden_gehalten/beobachtet, sowie (siehe Punkt 6)
die beiden neuen Hedge-Bull-Deckel-Parameter.

### 4. Wiederholungs-Erkennung: nur Krypto hatte sie

Die "letzte VERKAUFEN/TAUSCHEN-Empfehlung wurde nicht umgesetzt"-Erkennung
(urspruenglich 2026-07-17 nur in agent/krypto/analyst.py eingebaut) nach
agent/krypto/wiederholungs_erkennung.py ausgelagert (build_wiederholung_fact(),
5 synthetische Testfaelle verifiziert) und fuer Aktien/Rohstoffe/Hedge/
Themen-ETF nachgeruestet (_WIEDERHOLUNG_RELEVANTE_AKTIONEN = ("VERKAUFEN",)
statt Kryptos ("VERKAUFEN", "TAUSCHEN"), da diese 4 Klassen kein TAUSCHEN
kennen). Jede Pipeline laedt jetzt letztes_signal vor dem build_facts()-Call
und reicht es durch, jeder SYSTEM_PROMPT bekam die entsprechende Regel ergaenzt.

### 5. Historische Trefferquote: stillschweigend gepoolt

compute_win_rate_fact(conn, "spot") pool­te FRUEHER ALLE Zeilen aus der
signals-Tabelle ungefiltert - urspruenglich eine bewusste, dokumentierte
Krypto+Aktien-Vereinfachung ("Stichprobe zu klein fuer weitere Aufspaltung"),
aber seit Rohstoff/Hedge/Themen-ETF ebenfalls in dieselbe Tabelle schreiben,
OHNE dass das je neu entschieden wurde - eine Rohstoff-Trefferquote haette
z.B. stillschweigend Krypto-Momentum-Ergebnisse mit eingerechnet.
compute_win_rate_fact() um einen optionalen erlaubte_symbole-Parameter
erweitert (5 synthetische Testfaelle: Krypto+Aktien-Pool/Rohstoff-Pool/
Hedge-Pool/leerer Themen-ETF-Pool/ungefiltert - alle bestaetigt exakt).
Krypto+Aktien bleiben BEWUSST gepoolt (die urspruengliche Begruendung gilt
weiterhin), Rohstoffe/Hedge/Themen-ETF bekommen je einen EIGENEN Pool (anfangs
meist None, bis genug eigene Signale ausgewertet sind - ehrlicher als eine
geliehene fremde Zahl).

### 6. Hedge-Gegenszenario-Frage (SPIEGELVERKEHRT, nicht 1:1 uebernommen)

Kritischer Punkt bei der Konsistenzpruefung: der bestehende Gegenszenario-
Deckel (risk_gate.py::post_check(), wirkt automatisch fuer Krypto/Aktien/
Rohstoffe, die post_check() teilen) kappt die Positionsgroesse bei hoher
forecast.bear.probability_pct - richtig fuer eine normale Long-Position (das
IST das Risiko-Szenario). Fuer ein inverses Hedge-Instrument (DBPK/3QSS) waere
ein 1:1 uebernommener Bear-Deckel FUNKTIONAL FALSCHHERUM gewesen: die Position
GEWINNT bei fallenden Kursen, ihr eigentliches Risiko-Szenario ist eine hohe
forecast.bull.probability_pct (Volatility-Decay bei anhaltendem Aufwaertstrend
ohne Absicherungsnutzen, siehe SYSTEM_PROMPT Regel 4). Neu implementiert:
_post_check_hedge() um einen SPIEGELVERKEHRTEN "Bull-Wahrscheinlichkeits-
Deckel" erweitert (hedge.bull_wahrscheinlichkeit_schwelle_prozent: 35,
hedge.bull_wahrscheinlichkeit_deckel_anteil: 0.5 - identische Werte wie das
Spot/Aktien-Pendant, aber eigene Config-Keys unter hedge:). 4 synthetische
Testfaelle verifiziert: hohe Bull-WK bei KAUFEN -> gekappt; niedrige Bull-WK ->
unveraendert; VERKAUFEN -> Deckel greift nicht; hohe BEAR- statt Bull-WK bei
KAUFEN -> KEIN Deckel (bestaetigt die Spiegelung ist korrekt, kein versehentlich
uebernommener Bear-Deckel).

### 7. RM-3-Tabelle war stale

Zeile behauptete weiterhin "Aktien/ETF/Rohstoffe je 0%, nur Krypto im Einsatz"
- seit den Pipelines vom 15./18.07. schlicht falsch. Korrigiert: der
KONFIGURATIONSWERT ist unveraendert 0%, aber die eigentliche offene Luecke ist,
dass der Cross-Klassen-Deckel selbst nirgends durchgesetzt wird (jede Pipeline
rechnet nur gegen ihre eigene Assetklassen-Teilmenge).

**Verifiziert:** _kandidaten()/_pipeline_fuer() liefern exakt 13 Assets,
korrekt gemappt (Live-Check gegen echte Watchlist). Echter End-to-End-Lauf
gegen Kopie der Produktions-DB (nach Migration + frischen Preis-Snapshots fuer
alle 5 Themen-ETFs): VVMX - vollstaendiger echter Groq-Call, HALTEN, 42%
Konfidenz, sektor_rotation-Fakt korrekt in der Begruendung genutzt ("negative
Sektor-Rotation gegenueber dem breiten Markt (SPY)"), alle 15 inhaltlichen
Pflichtfelder befuellt (Top-5-Gruende/Key-Risks/Forecast/Halte-Kriterium/
Gegenargument - Entry/Stop/Take-Profit bei HALTEN leer, identisches Verhalten
wie bei bestehenden Aktien-HALTEN-Signalen, kein Regressionsfund). X136 -
sauberer Gate-Fehlschlag ("keine historischen Daten vorhanden"), kein Absturz.
Kompletter run_multi_asset_batch()-Lauf gegen alle 13 Kandidaten: korrekte
Kandidaten-Erkennung, Cooldown-Pruefung, Gate-Handling (mehrere Assets mit
nicht-aktualisierten Preisen korrekt als gate_passed=False verarbeitet, kein
Budget verbraucht), 3 echte Groq-Calls liefen tatsaechlich (429-Rate-Limit
durch die vorangegangenen Testaufrufe in derselben Sitzung erwartungsgemaess
sauber als "fehlgeschlagen" behandelt, kein Crash - P-10 funktioniert wie
vorgesehen).


### 8. Nachtrag zum Nachtrag: Watchlist-/Portfolio-Asset-Verwaltung geprueft

Nutzer-Hinweis "vergiss auch nicht die Asset-Verwaltung in der Watchlist und
im Portfolio - manuelle Eingabe und automatische Befuellung" fuehrte zu einem
gezielten Audit von AssetAddDialog (ui/app.py), Bitpanda-Sync
(importer/bitpanda_sync.py) und Portfolio-Tab (ui/portfolio.py). Ergebnis:
Portfolio-Tab und Bitpanda-Sync sind bereits vollstaendig assetklassen-neutral
(keine Aenderung noetig). EIN echter Fund: das "etf"-Dropdown im
AssetAddDialog deckt sowohl Themen-ETFs als auch Hedge-Instrumente ab, die
NUR per Symbol-Zugehoerigkeit zu SYMBOL_ZU_HEBEL_FAKTOR unterschieden werden
(kein eigenes UI-Feld dafuer) - ein neu hinzugefuegtes Hedge-Instrument waere
ohne Warnung als Themen-ETF behandelt worden, bis ein Entwickler es zusaetzlich
im Code eintraegt (hebel_faktor/Referenzindex sind hartkodiert, nicht per UI
abbildbar). Fix: `_validate_new_asset()` warnt jetzt (P-10, nicht blockierend)
bei jedem neuen etf-Symbol, das nicht in SYMBOL_ZU_HEBEL_FAKTOR steht, mit
konkretem Hinweis auf den noetigen Code-Schritt. Synthetisch verifiziert (Nicht-
Hedge-Symbol -> Warnung, echtes Hedge-Symbol DBPK -> keine Warnung).

Nebenbefund (bewusst NICHT geaendert, vorbestehendes und symmetrisches
Verhalten ueber alle Assetklassen): ein automatisches Hinzufuegen unbekannter
Bitpanda-Symbole zur Watchlist existiert nur fuer offene Hebel-/Margin-
Positionen (auto_add_unknown_hebel_symbols(), importer/bitpanda_margin_
positions.py). Neue Spot-/Nicht-Krypto-Bestaende fuer noch nicht in der
Watchlist gefuehrte Symbole werden NICHT automatisch angelegt, sondern per
result.unmatched_bitpanda_symbols im Sync-Ergebnis-Dialog angezeigt (ui/app.py,
zwei Stellen) - der Nutzer fuegt sie bei Bedarf manuell ueber AssetAddDialog
hinzu. Gilt gleichermassen fuer Krypto und Nicht-Krypto, keine Themen-ETF-
spezifische Luecke.


## Nachtrag (2026-07-18, gleicher Tag): LLM-Tagesbudget-Konsistenzpruefung +
## E-Mail-Versand-Audit

**Ausloeser:** Nutzer bemerkte auf der Remote-Status-Seite ein verdaechtiges
Bild (Groq "Fehler", "cerebras (2)" in der Hebel-Provider-Performance-Karte,
angezeigtes LLM-Budget) und bat um eine Pruefung des E-Mail-Versands sowie
des LLM-Tagesbudgets speziell im Zusammenspiel mit den neuen Multi-Asset-
LLM-Verbrauchern.

**"cerebras (2)" in der Provider-Performance:** korrekte historische
Anzeige, kein Bug - diese 2 Hebel-Signale wurden vor der vollstaendigen
Cerebras-Entfernung erzeugt und sind seither aufgeloest (siehe
project_cerebras_free_tier_aenderung_2026-08-17.md). Kein Code aendert das
mehr, es ist reine Vergangenheitsdaten-Anzeige.

**Groq "Fehler (vor 20 Min)":** ebenfalls kein Bug - echter 429-Rate-Limit
durch die vorangegangenen Verifikations-Testlaeufe dieser Session (mehrere
echte Groq-Calls kurz hintereinander waehrend der Themen-ETF-Verifikation).
Selbstheilend.

**Echter Fund: `count_real_signals_today()` war fuer das Krypto-Tagesbudget
verfaelscht.** Diese Funktion zaehlt Zeilen in der `signals`-Tabelle seit
Mitternacht UTC, OHNE Assetklassen-Filter. Sie wird an 3 Stellen fuer
Krypto-spezifische Tagesbudget-Entscheidungen verwendet (das Krypto-Budget-
System - Hebel/Marktscan/Spot, `taegliches_budget_gesamt: 15` - kalibriert
auf Groqs reale Token-Kapazitaet fuer Krypto allein):

1. `agent/krypto/signal_batch.py::run_signal_batch()` - der manuelle "Batch
   berechnen"-Button berechnete sein verbleibendes Tagesbudget als
   `daily_budget - bereits_heute`. Seit der automatische Multi-Asset-Batch
   (Aktien/Rohstoffe/Hedge/Themen-ETF, alle 12h) in dieselbe `signals`-
   Tabelle schreibt, schrumpfte das verbleibende KRYPTO-Budget
   stillschweigend um jede Multi-Asset-Signal-Erzeugung - eine echte
   Funktionsbeeintraechtigung, nicht nur eine Anzeige-Ungenauigkeit.
2. `remote/status.py::_get_budget_heute()` - die "LLM-Budget heute"-Karte
   (die im Screenshot zu sehende Karte) zeigte ein verzerrtes Verhaeltnis
   zum 15er-Deckel.
3. `ui/marktscan_view.py::_run_writeup()` - dieselbe Verzerrung in der
   Budget-Warnung des manuellen Marktscan-Buttons.

**Fix:** `database/db.py::count_real_signals_today()` um einen optionalen
`erlaubte_symbole`-Parameter erweitert (identisches Muster wie bereits heute
bei `compute_win_rate_fact()`). Alle 3 Aufrufstellen filtern jetzt auf
Krypto-Symbole. `remote/status.py` weist den Multi-Asset-Verbrauch
zusaetzlich als eigene, sichtbare Zeile (`multi_asset_heute`) aus statt ihn
unsichtbar zu verschlucken - neue Karten-Zeile in `remote/server.py`.

Synthetisch verifiziert (4 Faelle: ungefiltert/Krypto-only/leeres Set/
unbekanntes Symbol). Echter Nachweis-Lauf gegen eine Kopie der Produktions-
DB mit realistischem Mischszenario (8 echte Krypto- + 6 Multi-Asset-Signale
am selben Tag): ALTE Zaehlweise haette 14/15 (93%) angezeigt - faelschlich
fast erschoepft; NEUE Zaehlweise zeigt korrekt 8/15 (53%) Krypto-Verbrauch,
6 separat als Multi-Asset ausgewiesen.

**E-Mail-Versand-Audit (bereits sauber, keine Aenderung noetig):**
`_notify_spot_signal()`/`_notify_hebel_signal()`/`_notify_multi_asset_signal()`
decken alle 6 Signal-erzeugenden Pfade ab (Krypto Spot, Hebel, Aktien,
Rohstoffe, Hedge, Themen-ETF). Marktscan-Tier-2-LLM-Writeups (reine
Text-Anreicherung eines bereits per Score entdeckten Kandidaten, kein
eigenstaendiges Signal-Objekt) senden bewusst keine zweite E-Mail - der
Kandidat wurde bereits ueber `_notify_marktscan_kaufkandidaten()` beim
eigentlichen Scan gemeldet, kein Duplikat noetig. Manuelle "Signal
berechnen"-Klicks (alle Assetklassen) senden bewusst NIE eine E-Mail - nur
automatische Jobs, konsistent ueber die gesamte App.


## Nachtrag (2026-07-18, gleicher Tag): SOL in AZ-4-Tranchen + neuer
## Hebel-Prüfung-Toggle

**Auslöser:** Nutzer-Wunsch, Solana in die bisher BTC/ETH-exklusive AZ-4-
Tranchen-Funktion aufzunehmen (mit Verifikationsauftrag), plus ein neuer
per-Asset-Schalter, ob ein Krypto-Asset überhaupt fürs automatische
Hebel-Screening berücksichtigt werden soll.

### 1. SOL in AZ-4-Tranchen

Zwei getrennte BTC/ETH-Hardcodierungen identifiziert: `tranchen_erlaubt`
(gestaffelte Kauf-/Verkaufszonen fürs eigene Signal - einfach erweiterbar)
und `cash_reserve_ziel` (AZ-4 Baustein 3, ein *portfolioweites* Ziel, das
BTC+ETH fest zu zwei Gewichten kombiniert - eine echte 3-Wege-Erweiterung
wäre ein groesserer Umbau der Gewichtungsformel). Bewusst NUR
`tranchen_erlaubt` um SOL erweitert (`agent/krypto/pipeline.py`,
`database/db.py::_DCA_ERLAUBT_DEFAULT_SYMBOLS`, alle 5 Text-/Spalten-Stellen
in `ui/app.py`) - `cash_reserve_ziel` bleibt unverändert BTC/ETH-exklusiv.

**Verifikation:** 5 synthetische `_validate()`-Testfälle (gültige Tranchen,
Summe≠100, doppelter Rang, von>bis, null) - alle bestätigt korrekt. Echter
End-to-End-Lauf gegen Kopie der Produktions-DB mit erzwungenem Bär-Regime
(`dataclasses.replace()` auf ein echtes `RegimeResult`): SOL/BTC/ETH liefen
alle drei fehlerfrei durch `generate_signal()`. Zusätzlich ein Fake-LLM-
Client mit einer kanonischen Antwort inkl. echtem 3-Tranchen-Vorschlag durch
die komplette Pipeline geschickt - `tranchen_json` korrekt serialisiert,
`entry_usd_von/bis` blieb korrekt die Gesamtspanne (nicht die Tranchen-
Einzelzonen), aus der DB neu geladen identisch mit dem Original-Objekt -
genau der Pfad, den `ui/signals_view.py` beim Anzeigen nimmt.

**Nebenfund bei der Verifikation (kein Code-Bug, reines Testartefakt):**
die Desktop-DB-Kopie hatte für SOL eine veraltete `price_history` (CoinGecko-
Tabelle, separat von der Kraken-`price_history_ohlc`-Tabelle) - beide Tabellen
speisen die Staleness-Pruefung in `_load_closes_and_ohlc()` unabhaengig
voneinander. Kein Fix noetig, nur ein frischer Preis-/Historie-Abruf im
Testaufbau.

### 2. Neuer Hebel-Prüfung-Toggle

Per-Asset-Schalter (analog zum bestehenden AZ-4-Tranchen-Toggle-Muster,
`asset_dca_settings`): neue Tabelle `asset_hebel_settings` +
`get/set_hebel_pruefung_erlaubt()` in `database/db.py`. Default **true**
für ALLE Krypto-Assets (bewusst anders als der Tranchen-Toggle, dessen
Default nur für BTC/ETH/SOL an ist) - kein Verhaltenswechsel für bestehende
Nutzer ohne explizites Abschalten.

Greift in `agent/krypto/hebel_screening.py::run_hebel_screening()` VOR dem
teuren OI-Abruf (Binance/Bybit/OKX) - ein abgeschaltetes Asset bekommt weder
neue Trigger noch einen LLM-Call noch einen neuen Kandidaten im Hebel-Tab.
Bewusst NICHT verdrahtet in `agent/krypto/budget_allocator.py::
_offene_positionen_als_kandidaten()` - bereits offene Hebel-Positionen
bleiben unabhängig vom Toggle weiter risikoüberwacht (Nutzer-Bestätigung im
Vorgespräch).

Neue Spalte "Hebel-Prüfung" im Watchlist-Tab (`ui/app.py`, gilt für alle
Krypto-Assets, nicht nur eine feste Liste), neuer Toolbar-Button "Hebel-
Prüfung umschalten" mit Guard-Klausel (nur Krypto ohne Stablecoins).

**Verifikation:** Tk-Smoke-Test gegen Kopie der Produktions-DB (leichtgewichtig
über `TradingInfoToolApp.__new__()` statt der vollen `__init__` mit allen 5
Tabs, um unnötige Netzwerk-Aufrufe zu vermeiden) - Spalte korrekt vorhanden,
Toggle-Klick flippt den Wert korrekt in der DB UND in der Anzeige, Guard-
Klausel für ein Nicht-Krypto-Asset (VST) löst korrekt nur den Info-Dialog
aus, OHNE einen DB-Write auszulösen.

## Nachtrag (2026-07-18, gleicher Tag): LLM-Budget-Neukalibrierung nach
## Mistral-Einführung + Zeitpunkt/Anbieter-Anzeige + LLM-Anfrage in der Historie

**Auslöser:** Nutzer-Beobachtung ("wir kämpfen um jede Abfrage") anhand der
Remote-Status-Seite: Groq wirkte ausgelastet, Gemini praktisch ungenutzt (27h
seit letztem Call), das Tagesbudget zeigte weiterhin "15" an, obwohl seit der
Mistral-Integration (2026-07-17) eine dritte, deutlich größere Kapazitätsstufe
existiert. Zusätzlich zwei Wünsche: Zeitpunkt/Anbieter der LLM-Abfrage im
Info-Fenster und in der E-Mail sichtbar machen, und die zugehörige LLM-Anfrage
in der Signal-Historie einsehbar machen.

### 1. Budget-Neukalibrierung (`taegliches_budget_gesamt`, B)

Klargestellt: `B` ist **kein** literaler Tages-Deckel für LLM-Calls, sondern
steuert nur, wie viele Kandidaten pro 15-Minuten-Tick überhaupt einen
LLM-Versuch bekommen (`agent/krypto/budget_allocator.py::_verteile_budget()`,
siehe `docs/budget_queue_design.md`) - jeder ausgewählte Kandidat durchläuft
danach individuell die Groq→Mistral→Gemini-Kaskade. `B` war 1:1 auf Groqs
eigene Tageskapazität kalibriert (~15-18 Calls, siehe
`signale_batch.taegliches_budget`), bevor Mistral existierte, und wurde seither
nie angepasst. Die echte Schutzgrenze ist Mistrals eigenes Tagesbudget
(`mistral_taegliches_budget`, unverändert 150) - unabhängig von `B`.

**Berechnung (Nutzer-Vorgabe "berechne zuerst die Auswirkungen"):** anhand der
live über `config.get_watchlist()` abgefragten Watchlist (41 nicht-cash-
äquivalente Krypto-Assets, davon 13 `rolle=="core"`) wurde der theoretische
maximale Spot-Rotation-Bedarf je Cooldown-Regime berechnet
(`asset_anzahl × 24 / cooldown_stunden`). Ergebnis: selbst beim ALTEN Cooldown
(10h Kern/20h taktisch) lag der Bedarf bei ~65/Tag, weit über dem alten
`B=15` - die Drosselung war real, kein reines Anzeige-Problem. Beim neuen,
gelockerten Cooldown (8h/15h, siehe Punkt 2) liegt der Bedarf bei
13×24/8 + 28×24/15 ≈ 39 + 45 = 84/Tag.

Neu kalibriert: `taegliches_budget_gesamt: 90` (deckt die vollen 84/Tag plus
Puffer für Hebel-/Marktscan-Aktivität, bleibt deutlich unter Mistrals 150er-
Deckel - echte Ausreißertage laufen kontrolliert in Gemini als dritte Stufe).
`spot_rotation_reserve` proportional mitskaliert (5→30, Verhältnis F/B ≈ 33%
wie ursprünglich 2026-07-13 festgelegt) - Spot-Rotation behält denselben
relativen Mindestanteil auch an sehr Hebel-/Marktscan-aktiven Tagen.

### 2. Cooldown-Lockerung (Nutzer entschied sich für die moderate Empfehlung)

`spot_cooldown_stunden_kern` (rolle=core ODER gehalten ODER offene Hebel-
Position): 10h → 8h. `spot_cooldown_stunden` (rein taktische Watchlist-Assets
ohne Position): 20h → 15h. Beide waren ursprünglich als Bremse gegen die
knappe Groq-Kapazität gesetzt (2026-07-15/16) - jetzt, wo Mistrals große
Fallback-Kapazität den Groq-Engpass abfedert, ist die Bremse weniger nötig.

**Verifikation:** 4 synthetische `_verteile_budget()`-Testszenarien (ruhiger
Tag, normaler Tag, Crash-Tag mit vielen Hebel-Triggern, "nur Spot volle
Berechnung") - alle bestätigt korrekt: der volle gelockerte Spot-Bedarf
(84/Tag) läuft jetzt ohne Drosselung durch `B=90`, Crash-Tag-Priorität
(Hebel > Marktscan > Spot) und Spot-Rotations-Mindestreserve (`F=30`)
funktionieren weiterhin wie vorgesehen.

### 3. Zeitpunkt + Anbieter in Detail-Panel und E-Mail

`ui/hebel_view.py` zeigte bereits Anbieter+Zeitpunkt im Detail-Panel
(`meta_label`); `ui/signals_view.py` zeigte nur den Zeitpunkt, ohne Anbieter -
um `Anbieter: {signal.groq_model}` ergänzt (deckt Spot UND Aktien/Rohstoffe/
Hedge/Themen-ETF ab, da alle dieselbe `SignalsView`-Klasse und `Signal`-
Dataclass nutzen). Alle drei E-Mail-Funktionen in `scheduler/background.py`
(`_notify_spot_signal`, `_notify_hebel_signal`, `_notify_multi_asset_signal`)
zeigten bisher WEDER Zeitpunkt noch Anbieter - je eine Zeile
`Berechnet: <Datum Uhrzeit> · Anbieter: <provider:modell>` ergänzt.

### 4. LLM-Anfrage/Antwort in der Signal-Historie

Neue Spalte "Anbieter" in beiden History-Dialogen (`SignalHistoryDialog` in
`ui/signals_view.py`, `HebelSignalHistoryDialog` in `ui/hebel_view.py`).
Doppelklick auf eine Historien-Zeile öffnet einen neuen Detail-Dialog
(`LlmAbfrageDialog` bzw. `HebelLlmAbfrageDialog`) mit den an die KI gesendeten
Fakten (`facts_json`, JSON-formatiert) und der Roh-Antwort (`groq_raw_response`
bzw. `groq_raw_response` bei `HebelSignal`) - beide Felder waren bereits in der
DB gespeichert, reine UI-Sichtbarmachung ohne neuen Netzwerk-Call oder neue
Datenerfassung.

**Verifikation:** Tk-Smoke-Test gegen Kopie der Produktions-DB - Anbieter-
Spalte korrekt befüllt (z. B. `gemini:gemini-3.1-flash-lite`,
`groq:llama-3.3-70b-versatile`), simulierter Doppelklick öffnet den
Detail-Dialog korrekt für ein echtes Spot-Signal (BTC, 20 Historien-Einträge)
und ein echtes Hebel-Signal (CAT LONG), `facts_json`/Roh-Antwort werden
lesbar formatiert angezeigt (mehrere Tausend Zeichen, korrekt eingerückt).

## Nachtrag (2026-07-18, gleicher Tag): Cash-Veto-Warnsystem - RM-4-Block
## sichtbar machen statt stillschweigend zu HALTEN downzugraden

**Auslöser:** Nutzer-Auftrag "prüfe bitte - wichtig Anzeige und Info, wenn
über einen der Cash-Parameter ein Block oder die weitere Verarbeitung
verhindert werden - Detailanalyse durchführen". Ergebnis der Analyse: RM-4
(Cash-Reserve-Minimum, `risk_gate.py::pre_check()`) ist der einzige echte
Cash-Block (Spot/Aktien/Rohstoffe/Themen-ETF - nicht Hebel/Hedge). Vier
konkrete Lücken gefunden, alle auf Nutzer-Wunsch ("ja alles umsetzen")
behoben.

### 1. Der wichtigste Fund: `risk_veto` erfasste den häufigeren Fall gar nicht

Der bestehende `risk_veto`/`risk_veto_reason`-Mechanismus in `post_check()`
feuert NUR, wenn das Modell die `risiko_check.kauf_erlaubt`-Regel MISSACHTET
und trotzdem KAUFEN/NACHKAUFEN vorschlägt (deterministischer Backstop). Ein
regelkonformes Modell, das bei `kauf_erlaubt == false` bereits von sich aus
HALTEN sagt (der häufigere Fall, da genau das per Prompt-Regel verlangt
wird), löste bisher GAR KEIN sichtbares Signal aus - der Cash-Block blieb
komplett unsichtbar, obwohl das System dadurch faktisch beeinträchtigt war.

**Fix:** Neues, unabhängiges Feld `RiskPreCheckResult.cash_veto`/
`cash_veto_reason` in `risk_gate.py` - wird IMMER gesetzt, wenn RM-4 bei
dieser Bewertung aktiv war, unabhängig vom tatsächlichen Modellverhalten.
`post_check()` reicht `_cash_veto`/`_cash_veto_reason` jetzt IMMER durch
(nicht nur bei einer tatsächlichen Aktions-Überschreibung). Persistiert auf
`Signal.cash_veto`/`cash_veto_reason` (additive Migration, nur `signals`-
Tabelle, da RM-4 hebel-/hedge-unabhängig ist) - an allen 4 Pipelines
verdrahtet (Krypto, Aktien, Rohstoffe, Themen-ETF, alle nutzen dieselbe
`risk_gate.pre_check()`/`post_check()`).

### 2. WARNUNG-E-Mail statt Stille (Nutzer-Vorgabe: "System beeinträchtigt")

Ein cash-blockiertes Signal endet als HALTEN - HALTEN löst normalerweise NIE
eine E-Mail aus (bewusstes Design gegen Postfach-Spam). Für `cash_veto`
wurde das bewusst durchbrochen: neue `_notify_cash_veto_warning()` in
`scheduler/background.py`, aufgerufen aus `_notify_spot_signal()` und
`_notify_multi_asset_signal()` VOR deren HALTEN-Guard. Betreff
`WARNUNG - Cash-Veto (<Symbol>)`, Body erklärt explizit, dass das System
aktuell durch eine zu geringe Cash-Reserve beeinträchtigt ist und das für
ALLE Spot-/Aktien-/Rohstoff-/Themen-ETF-Bewertungen gilt, nicht nur das
eine Asset.

**Cooldown bewusst EIN globaler Zeitstempel, nicht pro Asset/Job**
(`config.yaml benachrichtigung.email.cash_veto_warnung_cooldown_minuten`,
Default 360 Min/6h) - RM-4 ist ein PORTFOLIOWEITER Zustand: ohne Cooldown
würde jedes während der Unterschreitung bewertete Asset eine eigene Mail
auslösen (potenziell ein Dutzend am Tag). Gleiches Muster wie
`_notify_job_failure()`, nur mit einem einzelnen statt einem pro-Job-
Zeitstempel.

### 3. Detail-Panel-Warnung unabhängig vom bestehenden Risiko-Veto

`ui/signals_view.py`: neue Zeile `⚠ WARNUNG - Cash-Veto (System
beeinträchtigt): <Grund>` im `gate_label`, geprüft über `signal.cash_veto`
(NICHT über `signal.risk_veto`) - erscheint also auch dann, wenn das Modell
sich schon regelkonform verhalten hat (der unter Punkt 1 beschriebene,
häufigere Fall).

### 4. Zwei kleinere Detailfunde ebenfalls behoben

- EURCV-Kurs fehlt → Fiat-Guthaben zählte bisher schon nicht in die
  Cash-Reserve mit, der Grund dafür landete aber nur in einer nirgends
  verwendeten `checks`-Liste. Jetzt als Zusatzsatz direkt an
  `cash_veto_reason` angehängt, sobald es tatsächlich zu einem Veto kam.
- `db.get_cash_reserve_fiat_eur()`: ein korrupter DB-Wert (`ValueError`)
  fiel bisher still auf 0.0 zurück, ohne jede Spur. Jetzt `logger.warning()`
  mit dem kaputten Rohwert.

**Verifikation:** 4 synthetische `pre_check()`/`post_check()`-Szenarien
gegen eine In-Memory-DB + echte `config.yaml`-Werte (kein Cash → Veto,
inkl. des bisher unsichtbaren "Modell sagt selbst korrekt HALTEN"-Falls;
genug Cash → kein Veto; EURCV fehlt → Veto mit Zusatzhinweis; korrupter
DB-Wert → geloggt) - alle bestätigt korrekt. Migration + Signal-Roundtrip
gegen echte Kopie der Produktions-DB (ALTER TABLE, alte Zeilen laden
korrekt mit `cash_veto=False`). Tk-Smoke-Test für die neue Detail-Panel-
Zeile (erscheint bei `cash_veto=True`, verschwindet bei `False`, keine
Verwechslung mit der bestehenden Risiko-Veto-Zeile). Cooldown-Logik der
Warnmail synthetisch getestet (erste Warnung geht raus, zweite wird
unterdrückt, nach simuliertem Cooldown-Ablauf geht die dritte wieder raus).

## Nachtrag (2026-07-18, gleicher Tag): Groq-Tageserschöpfung erkennen - kein
## unnötiger Erschöpfungs-Versuch mehr pro Kandidat

**Auslöser:** Nutzer-Beobachtung: "mir kommt vor, dass trotz Erschöpfung
immer zuerst Groq abgefragt wird". Bestätigt durch Code-Prüfung: anders als
Mistral/Gemini (echter, aus der DB gelesener Tageszähler, siehe
`_mit_fallback_chain()`) hatte Groq **kein** eigenes Tagesbudget - Kommentar
im Code war explizit: "Groqs reales Tageslimit wirkt extern über echte
429s". Das bedeutete: sobald Groqs echtes tägliches Token-Limit erreicht
war, wurde **jeder weitere Kandidat** - in diesem UND allen folgenden
15-Minuten-Läufen desselben Tages - trotzdem zuerst erfolglos gegen Groq
versucht, bevor Mistral übernahm. Kein verlorenes Mistral/Gemini-
Kontingent (der Fallback funktionierte pro Call korrekt), aber unnötige
Latenz: ein garantiert scheiternder HTTP-Call pro Kandidat, den ganzen
Resttag über.

**Warum es diesen Zähler bisher nicht gab:** Groqs echte Tagesgrenze ist
token-basiert, nicht anfrage-basiert - anders als bei Mistral/Gemini gibt
es keine feste Zahl, die man lokal vorab prüfen könnte. Die ursprüngliche
Design-Entscheidung war, das der echten API zu überlassen statt zu raten.

**Fix:** neuer In-Memory-Zustand in `agent/krypto/budget_allocator.py`
(gleiches Muster wie `scheduler/background.py::_consecutive_failures`) -
`_groq_failure_date`/`_groq_failure_count`/`_groq_exhausted_date`. Ab
`groq_exhaustion_schwelle_fehlschlaege` (neuer Config-Wert, Default 2)
aufeinanderfolgenden Groq-Fehlschlägen **am selben Kalendertag (UTC)** wird
Groq in `_mit_fallback_chain()` für den Rest des Tages direkt übersprungen
(kein Call-Versuch mehr) - Kandidaten gehen sofort an Mistral/Gemini.
Schwelle 2 statt 1, damit ein einzelner transienter Netzwerk-Ausrutscher
nicht sofort fälschlich als Tageserschöpfung gewertet wird. Reset erfolgt
implizit über den Kalendertag-Vergleich (kein expliziter Reset-Code nötig)
- passt zur echten Ursache (ein TAGES-Limit). In-Memory statt DB-persistiert
(wie bei `_consecutive_failures`) - überlebt keinen Prozess-Neustart,
bewusst akzeptabel (selten, im schlimmsten Fall wird Groq danach einfach
frisch neu probiert). Ein Datenqualitäts-Gate-Skip (`gate_passed=False`,
kein echter LLM-Call) zählt bewusst NICHT als Erfolg oder Fehlschlag - der
Erfolgs-/Fehlschlag-Zähler wird nur bei einem tatsächlich stattgefundenen
Groq-Call aktualisiert.

Neues `AllocationResult.groq_erschoepft_erkannt`-Feld (Analogie zu
`mistral_budget_erschoepft`/`gemini_budget_erschoepft`) für Logging/
Nachvollziehbarkeit, in der bestehenden Budget-Allocator-Log-Zeile in
`scheduler/background.py` ergänzt.

**Verifikation:** synthetische Tests der Schwellenwert-Logik (1 Fehlschlag
→ noch nicht erschöpft, 2. Fehlschlag → erschöpft, Erfolg setzt nur den
Zähler zurück, nicht das Tages-Flag; simulierter Tageswechsel → alter
Zählerstand wird verworfen, ein einzelner Fehlschlag am neuen Tag erschöpft
noch nicht). Echter End-to-End-Test über zwei komplette
`run_budget_allocator()`-Läufe gegen eine echte (Datei-)DB mit 5 Spot-
Kandidaten und einem Fake-Groq-Client, der immer fehlschlägt: im ersten
Lauf wird Groq genau 2x versucht (dann Schwelle erreicht), alle 5
Kandidaten laufen über Mistral; im zweiten Lauf (simuliert den nächsten
15-Minuten-Takt am selben Tag) wird Groq kein einziges Mal mehr versucht.

## Nachtrag (2026-07-19): erste Notebook-Nacht-Analyse - Misfire-Fehlalarm,
## klare OI-Fehlermeldungen, persistente OI-Abdeckungs-Warnung pro Symbol

**Auslöser:** erster kompletter Notebook-Nachtlauf mit dem neuen Release.
Der Nutzer schickte einen Screenshot mit mehreren "Job fehlgeschlagen"-
E-Mails kurz nach Mitternacht und bat um eine Detailanalyse. Dafür wurde
zunächst `extract_notebook_diagnose.py` um einen Log-Ausschnitt-Export,
eine Job-Fehlschlag-Historie und eine Groq-Erschöpfungs-Ereignisliste
erweitert (siehe eigener Abschnitt weiter unten) und gegen die echten
Notebook-Logs ausgeführt. Ergebnis: drei unabhängige Funde.

### 1. Falscher Alarm: APScheduler-Misfire bei Sofort-Start-Jobs

Der 00:32-E-Mail-Cluster war **kein Absturz** - alle 7 Jobs, die beim
Scheduler-Start sofort laufen sollen (`next_run_time=datetime.now()`,
u. a. `refresh_prices`, `hebel_screening`, `multi_asset_batch`), liefen
tatsächlich korrekt durch. APScheduler meldet aber standardmäßig nach nur
1 Sekunde (`misfire_grace_time`-Default) ein `EVENT_JOB_MISSED`, wenn der
Scheduler zwischen `add_job()`-Aufruf und tatsächlichem Start etwas
beschäftigt ist (mehrere synchrone `add_job()`-Calls + Vorbereitungsarbeit
beim Start brauchten hier ca. 1,1 Sekunden) - und
`_log_job_event()`s Misfire-Zweig verschickt dafür unbedingt eine
"fehlgeschlagen"-E-Mail, obwohl der Job danach ganz normal lief.

**Fix:** neue Konstante `_IMMEDIATE_START_MISFIRE_GRACE_SECONDS = 300` in
`scheduler/background.py`, als `misfire_grace_time=` an alle 7 betroffenen
`scheduler.add_job(...)`-Aufrufe ergänzt. 5 Minuten statt 1 Sekunde Toleranz
- reicht für jede realistische Scheduler-Startverzögerung, ohne einen
echten, dauerhaft blockierten Job zu verschleiern (der würde nach 5 Minuten
immer noch als Misfire gemeldet).

### 2. Wiederkehrender Fund: fünf Symbole ohne Open-Interest-Daten

Dieselbe Log-Analyse zeigte ein **echtes, wiederkehrendes** (nicht
einmaliges) Muster: KAS, KAIA, FLOKI, TURBO und CANTON scheiterten beim
15-Minuten-Hebel-Screening regelmäßig bei **allen drei** OI-Börsen
(Binance/Bybit/OKX) mit einem nichtssagenden `IndexError: list index out
of range`. Ursache: Bybit/OKX antworten bei einem auf der jeweiligen Börse
nicht gelisteten Symbol mit HTTP 200 und einer **leeren** Liste statt einem
Fehlerstatus - `liste[0]` warf dafür nur den rohen IndexError statt einer
erklärenden Meldung. War vorher schon abgefangen (P-10-Isolation, kein
Crash), aber ohne erkennbaren Grund im Log.

**Fix:** neue `NoOpenInterestDataError`-Exception + `_erstes_element()`-
Hilfsfunktion in `api/derivatives.py`, ersetzt die drei rohen
`liste[0]`-Zugriffe (Bybit-OI, OKX-OI, Binance-Long-Short-Ratio). Ändert
NICHTS am Fehlerverhalten selbst (weiterhin pro Börse einzeln
abgefangen), macht die Ursache im Log aber sofort erkennbar.

### 3. Nutzer-Vorschlag: sichtbare Warnung bei dauerhaft fehlender OI-Abdeckung

Der Nutzer fragte, ob ein solcher wiederholter Fehlschlag nicht auch ein
"relativ eindeutiges Zeichen" sei, dass die Hebel-Prüfung für so ein Symbol
u. U. problematisch sei, und ob das für eine gewisse Zeit in GUI/E-Mail
sichtbar gemacht werden sollte, gerade weil es sich um ein dauerhaftes (nicht
nur vorübergehendes) Problem handeln könnte.

**Bewertung:** zugestimmt, mit einer bewussten Einschränkung - **kein
automatisches Abschalten** der Hebel-Prüfung. Ein fehlender OI-Wert ist ein
Kontextverlust (das Hebel-Signal wird ohne Positionierungs-Kontext
bewertet), kein Grund, die Prüfung selbst zu unterbinden - die Entscheidung
soll beim Nutzer über den bestehenden Hebel-Prüfung-Toggle bleiben, nicht
beim System automatisch getroffen werden.

**Fix, drei Teile:**

- **Neue Tabelle** `oi_abdeckung_status` (`database/db.py`) - ein Zustand
  je SYMBOL (nicht je Börse wie bei `api_health_status`), weil erst das
  gleichzeitige Scheitern bei ALLEN drei Börsen als ein Fehlschlag zählt
  (siehe `fetch_and_store_oi_snapshot()`-Rückgabewert, jetzt `bool`).
  4 neue Funktionen: `record_oi_abdeckung_ergebnis()` (Erfolg setzt den
  Zähler zurück, Fehlschlag erhöht ihn), `get_oi_abdeckung_status()` (für
  die GUI), `get_symbole_mit_ueberschrittener_oi_schwelle()` (Schwelle +
  Cooldown-Filter, gleiches Prinzip wie beim Cash-Veto),
  `set_oi_abdeckung_gemeldet()`. DB-persistiert statt in-memory wie bei der
  Groq-Erschöpfung oben - bewusst, weil dieser Zustand laut Nutzer-
  Einschätzung potenziell DAUERHAFT ist und einen Neustart überleben soll,
  nicht nur eine kurze Störung wie Groq.
- **E-Mail-Warnung** (`scheduler/background.py::_notify_oi_abdeckung_
  warnung()` + `_pruefe_oi_abdeckung_warnung()`, aufgerufen direkt nach
  jedem `run_hebel_screening()`-Lauf) - neue Config-Werte
  `oi_abdeckung_schwelle_fehlschlaege` (Default 8, also gut 2 Stunden
  durchgängiger Fehlschlag bei 15-Minuten-Takt) und `oi_abdeckung_warnung_
  cooldown_stunden` (Default 24) unter `hebel_screening:`. Erklärt in der
  Mail explizit: keine automatische Abschaltung, Hinweis auf den manuellen
  Toggle. Die Meldung wird nur bei TATSÄCHLICH verschicktem Mail-Erfolg als
  "gemeldet" markiert (nicht schon beim bloßen Versuch) - sonst würde eine
  deaktivierte E-Mail-Benachrichtigung oder ein Versandfehler den Cooldown
  fälschlich anlaufen lassen und eine später (wieder) aktivierte Warnung
  bis zu 24 Stunden lang unterdrücken, obwohl nie etwas verschickt wurde
  (im ersten Entwurf ein echter Bug, beim Testen gefunden und behoben).
- **GUI-Markierung** (`ui/app.py`, Watchlist-Tab) - ein `⚠`-Zeichen direkt
  in der bestehenden Hebel-Prüfung-Spalte, wenn `konsekutive_fehlschlaege
  >= oi_abdeckung_schwelle_fehlschlaege`, mit erklärendem Spalten-Tooltip.
  Kein neuer Schalter, keine automatische Aktion - reine Sichtbarmachung.

**Verifikation:** 8 synthetische DB-Tests für die neue Tabelle/Funktionen
(Erfolg setzt zurück, Schwelle wird erkannt, Symbol darunter wird NICHT
gemeldet, Cooldown unterdrückt eine zweite Meldung, Cooldown=0 hebt das
sofort wieder auf, Erholung setzt den Zähler zurück). End-to-End-Test von
`_pruefe_oi_abdeckung_warnung()` mit gemocktem E-Mail-Versand (genau 1 Mail
für das Symbol über der Schwelle, keine für das Symbol darunter, Cooldown
verhindert eine zweite Mail, deaktivierte E-Mail verschickt nichts UND
markiert nichts als gemeldet - deckte den oben beschriebenen Bug auf, der
noch vor der Verifikation behoben wurde). Tk-Smoke-Test der Watchlist-
Spalte (Warnzeichen erscheint für das Symbol über der Schwelle, fehlt beim
Symbol darunter). Migrationstest gegen eine echte Kopie der Produktions-DB
(`init_db()` legt die neue Tabelle sauber an, bestehende `cash_veto`-Spalten
weiterhin vorhanden). Regressionstest der `NoOpenInterestDataError`/
`_erstes_element()`-Fixes sowie aller 7 `misfire_grace_time`-Ergänzungen.

### Erweiterung: `extract_notebook_diagnose.py` konsolidiert Log-Analyse

Im Zuge dieser Analyse wurde außerdem ein zweites, nicht im Repo verwaltetes
Export-Skript entdeckt (6-Datei-Format, offenbar direkt auf dem Notebook
entstanden und nie zurücksynchronisiert). Statt es zu pflegen, wurde
`extract_notebook_diagnose.py` (das bereits bestehende, repo-versionierte
Skript) erweitert: optionales Log-Zeitfenster (Standard 72 Stunden,
CLI-Parameter), Log-Zeilen-Auszug inkl. mehrzeiliger Tracebacks,
extrahierte Job-Fehlschlag-Historie, extrahierte Groq-Erschöpfungs-
Ereignisse, sowie eine regelbasierte Auffälligkeiten-Liste (u. a.
`risk_veto=True` bei einer Nicht-HALTEN-Aktion) - deckt jetzt sowohl
DB-Snapshot als auch Log-Historie in einem einzigen Export ab. Siehe
Memory `reference_notebook_analyseordner_standard`.

### Nachtrag: zwei weitere yfinance-"nur fast_info"-Ticker in die Unterdrückungsliste aufgenommen

Dieselbe Log-Analyse zeigte 826 yfinance-ERROR-Zeilen ("possibly delisted;
no price data found") über das 72-Stunden-Fenster. Fünf der betroffenen
Ticker (OD7N/3QSS/OD7L/OD7H/OD7C) waren bereits seit 2026-07-16 als bekannte,
unkritische "nur fast_info"-Fälle in `api/yfinance_client.py::
YFINANCE_HISTORY_UNRELIABLE_TICKERS` erfasst und wurden per Logging-Filter
in `main.py` unterdrückt. Zwei weitere Ticker - X136.BE und IS0C.DE (X136/
ISOC) - zeigten das identische Muster (je 272 ERROR-Zeilen über 72 Std.,
`fast_info` lieferte dabei durchgehend gültige Kurse, "Wertpapier-Preis-
Refresh: 13 Assets aktualisiert" bei jedem Lauf), waren aber NICHT in der
Liste enthalten und erzeugten dadurch unnötiges Log-Rauschen.

**Fix:** beide Ticker zur `YFINANCE_HISTORY_UNRELIABLE_TICKERS`-Menge
ergänzt (jetzt 7 statt 5 Einträge). Kein funktionaler Fehler, reine
Log-Hygiene - `fast_info` war in allen Fällen erfolgreich, nur `.history()`
schlägt intern erwartungsgemäß fehl (dünn gehandelte ISIN-/Berlin-Börsen-
Instrumente, siehe ursprüngliche Data-Quality-Caveats vom 2026-07-09).

**Verifikation:** Filter synthetisch gegen die echten Log-Zeilen getestet -
X136.BE/IS0C.DE/OD7C.SG werden jetzt unterdrückt, ein unbekanntes Symbol
(Kontrollfall) bleibt weiterhin sichtbar (P-10-Prinzip unverändert: nur
bestätigte Fälle werden unterdrückt, kein pauschales Wegfiltern).

## Nachtrag (2026-07-19): Liquidationspreis-Sicherheitsmarge neu kalibriert

**Auslöser:** Nutzer-Beobachtung beim gemeinsamen Durchsehen zweier echter
Hebel-Empfehlungs-E-Mails (VIRTUAL/AVAX): "den Liquidationspreis müssen wir
auf ein realistisches Niveau bringen, ist u.U. zu restriktiv." Der bisherige
Config-Wert `liquidations_sicherheitsmarge_relativ: 0.175` (17,5%) war seit
seiner Einführung explizit als `[OFFEN]` markiert - laut Kommentar nur ein
"Mittelwert einer 15-20%-Spanne", **keine echte Quelle**, nicht kalibriert.

**Vorgehen:** zwei unabhängige Kalibrierungsquellen kombiniert.

1. **Bitpandas offizielle Doku** (Bitpanda Helpdesk, "Amplify your trading
   with Bitpanda Leverage"): Liquidation greift, wenn Margin Level =
   Positionswert / (Kreditbetrag + Tagesgebühren) unter ~105-110% fällt.
   Mathematisch übersetzt in unsere Formel (sicherheitsmarge_relativ =
   1 - 1/Schwelle) ergibt das einen theoretisch plausiblen Bereich von
   **4,76% bis 9,09%**.
2. **4 echte, aus der Bitpanda-Transaktionshistorie rekonstruierte
   Liquidationsfälle** (LINK id=5, TAO id=77, TAO id=87, SUI id=54, alle aus
   `importer/bitpanda_margin_positions.py`, Status `wahrscheinlich_
   liquidiert`) gegen die echte tägliche OHLC-Kurshistorie der App geprüft.
   Bei 2 Fällen (TAO id=87, SUI id=54) verlief der Kurs am Schließungstag
   ruhig statt in einem Crash-Docht, was eine präzise Rückrechnung erlaubte:
   implizierte Marge **6,75% (SUI)** bzw. **8,4% (TAO)** - beide innerhalb
   des Bitpanda-Bereichs. Die beiden anderen Fälle (LINK, TAO id=77) hatten
   Crash-Dochte weit unterhalb der berechneten Zone, was nicht widerspricht,
   aber keine präzise Eingrenzung erlaubt. Zusammen mit dem bereits am
   2026-07-16 live verifizierten LINK-Fall (~6,5%, siehe oben) ergeben sich
   **drei präzise Datenpunkte im Bereich 6,5%-8,4%**, alle konsistent mit der
   offiziellen Bitpanda-Spanne.

**Fix:** `liquidations_sicherheitsmarge_relativ` von 0,175 auf **0,09 (9%)**
gesetzt - knapp über dem höchsten real beobachteten Wert (8,4%), damit
bewusst weiterhin ein kleiner Sicherheitspuffer, aber keine ~2x-Übertreibung
mehr. Wirkt an zwei Stellen gleichzeitig (Nutzer-Vorgabe: "Anpassung soll
generell passieren, auch bei den Signalen und Empfehlungen"):
- `estimate_liquidation_price()` - der angezeigte "Geschätzte
  Liquidationspreis" in App/E-Mail liegt jetzt näher an der Realität.
- `max_safe_hebel()` (RM-11) - der Deckel für den bei neuen Positionen
  empfohlenen Hebel erlaubt jetzt etwas mehr (bei 15% Stop-Loss-Distanz z. B.
  6,07x statt vorher 5,50x maximal sicherer Hebel).

**Verifikation:** Reproduktion des LINK-Live-Falls (Entry 7,42 €, Hebel 5x)
mit dem neuen Wert ergibt 6,52 € gegen den echten Bitpanda-Wert 6,3515 € -
Abweichung nur noch +2,7% (vorher +13,3% mit 17,5%), UND weiterhin in der
sicheren Richtung (zeigt Liquidation nicht später an als real). `config.yaml`
lädt den neuen Wert korrekt, Syntax-/YAML-Validität beider geänderten
Dateien bestätigt.

## Nachtrag (2026-07-19): Retail-Konsens-Deckel + Risikofaktoren-Liste + 3-Abschnitte-Neustrukturierung (E-Mail/App, alle Assetklassen)

**Auslöser:** gemeinsame Durchsicht zweier echter Hebel-Empfehlungs-E-Mails
(VIRTUAL, AVAX) deckte zwei Inkonsistenzen auf:

1. **AVAX-Signal** begründete eine LONG-Empfehlung u. a. mit "Retail-Bias
   extrem long (65,9% Long-Konten), was für eine Gegenbewegung spricht" -
   eine antizyklische Beobachtung, die logisch GEGEN LONG spricht (eine
   bereits stark in eine Richtung positionierte Crowd wird bei einer
   Gegenbewegung zuerst liquidiert/ausgestoppt), aber trotzdem zur Stützung
   von LONG verwendet wurde.
2. Beide Signale hatten `trade_thesis_typ: swing_strategie` ("bestätigter,
   noch nicht ausgereizter Trend") UND gleichzeitig einen erkannten
   Regime-Konflikt (Position widerspricht dem Regime) - ein innerer
   Widerspruch in der eigenen Klassifikation.

Der Nutzer bat außerdem darum, E-Mail und App-Detailansicht für **alle**
Assetklassen einheitlich in drei Abschnitte zu gliedern: 1. was ist
mathematisch berechnet, 2. was sagt die LLM-Bewertung, 3. eine ausführliche
Konklusion mit positiven/neutralen/negativen Risikofaktoren.

### 1. Retail-Konsens-Deckel (neu, Hebel) + Prompt-Fix (Hebel UND Spot)

Ursachenanalyse: `build_hebel_facts()`/`build_facts()` liefern dem Modell nur
Rohzahlen (Long-Konten-Anteil, zwei Extrem-Flags) - **keine** Regel im
SYSTEM_PROMPT erklärte bisher, wie ein extremer Retail-Konsens richtungsmäßig
zu interpretieren ist. `agent/krypto/anticyclic.py`s einzige gerichtete Logik
ist an den Spezialfall "möglicher Flush nach Kursabsturz" gekoppelt, keine
allgemeingültige Übersetzung.

**Fix, zwei Ebenen (wie überall in diesem System - nie blind auf
Prompt-Befolgung vertrauen):**
- **Prompt-Regel** (`hebel_analyst.py` Regel 8, `analyst.py` Regel 15):
  extremer Retail-Konten-Anteil in eine Richtung ist ein Kontraindikator
  GEGEN diese Richtung - ein `top_gruende`-Eintrag mit `kategorie:
  antizyklisch`, der auf Retail-Konsens verweist, darf NIEMALS dieselbe
  Richtung wie die eigene Empfehlung stützen.
- **Neuer deterministischer Hebel-Deckel** `retail_konsens_hebel_deckel`
  (config.yaml, 3.0): `hebel_risk_gate.py::retail_konsens_risiko()` - True,
  wenn `retail_long_bias_extreme` UND `richtung == LONG` (bzw. symmetrisch
  `long_account_pct <= 35%` UND `richtung == SHORT`, gleiche 65%-Schwelle wie
  `anticyclic.py::LONG_BIAS_EXTREME_THRESHOLD_PCT`). Als fünfter Kandidat in
  `_hebel_deckel_kandidaten()` ergänzt.
- **These-Regime-Widerspruch** (neu, reine Sichtbarmachung, KEIN Deckel - es
  gibt keine saubere numerische Dimension dafür): `hebel_risk_gate.py::
  these_regime_widerspruch()` - True, wenn `trade_thesis_typ == swing_
  strategie` UND gleichzeitig ein Regime-Konflikt vorliegt.
- `regime_konflikt_hebel()` als eigene Funktion extrahiert (vorher inline in
  `_hebel_deckel_kandidaten()`), damit Deckel-Logik UND Risikofaktoren-Liste
  auf exakt derselben Bedingung basieren.

### 2. Neue Risikofaktoren-Liste (Kern von Abschnitt 3)

`agent/krypto/hebel_risk_gate.py::compute_risikofaktoren_hebel()` und
`agent/krypto/risk_gate.py::compute_risikofaktoren()` (Spot/Aktien/Rohstoffe/
Themen-ETF-Pendant) fassen alle bereits vorhandenen Deckel-/Veto-Checks
deterministisch in eine kompakte 🟢positiv/⚪neutral/🔴negativ-Liste
zusammen - bewusst NICHT vom LLM generiert (genau das war beim AVAX-Fund das
Problem). Geprüfte Faktoren: Regime-Konflikt, These-Regime-Widerspruch
(nur Hebel), Gegenszenario-Wahrscheinlichkeit, technische Konfluenz, CRV-Höhe,
Retail-Konsens-Risiko, Konfidenz-Niveau, sowie Cash-Veto/Risiko-Veto als
Kurzschluss-Fälle (Spot). Jeder Check liefert sowohl den negativen ALS AUCH
den positiven Gegenfall (z. B. "Regime-Ausrichtung: positiv", wenn KEIN
Konflikt vorliegt) - keine reine Fehlerliste, sondern eine vollständige
Bilanz.

Neues Feld `risikofaktoren_json` (JSON-serialisierte Liste von `{name,
bewertung, begruendung}`) auf `Signal` UND `HebelSignal` (additive Migration,
beide Tabellen), deterministisch am Ende von `post_check()`/
`post_check_hebel()` berechnet und in der Pipeline persistiert (`hebel_
pipeline.py` und alle 4 Spot-family-Pipelines).

### 3. 3-Abschnitte-Neustrukturierung (E-Mail + App, alle Assetklassen)

`scheduler/background.py`: alle drei E-Mail-Builder (`_notify_spot_signal()`,
`_notify_hebel_signal()`, `_notify_multi_asset_signal()`) sowie `ui/hebel_
view.py`/`ui/signals_view.py`s Detail-Panels zeigen jetzt einheitlich:

- **1. MATHEMATISCH BERECHNET** - bei Hebel: Hebel final, Liquidationspreis,
  Eigenkapitalbedarf/-Nachschuss, Ausführbarkeit. Bei Spot/Aktien/Rohstoffe/
  Themen-ETF: Boden-Zielzone, Cash-Reserve-Ziel (beide AZ-4-Bausteine,
  vollständig deterministisch).
- **2. LLM-BEWERTUNG (Konfidenz X%)** - Kurz-/Langbegründung, Top-Gründe,
  **Gegenargument (NEU - existierte seit 2026-07-18 als Pflichtfeld, fehlte
  aber bisher komplett in E-Mail UND App)**, Entry/SL/TP-Zonen, Positions-
  größe/Tranchen, Halte-Kriterium, wichtigste Risiken, **Forecast-Szenarien
  (NEU, waren bisher nur in der DB sichtbar)**.
- **3. KONKLUSION (RISIKOFAKTOREN)** - die neue deterministische Liste.

Neue gemeinsame Formatierungs-Helper: `scheduler/background.py::
_formatiere_gegenargument()`/`_formatiere_forecast()`/`_formatiere_
risikofaktoren()` (E-Mail-Textformat) und `ui/formatting.py::format_
risikofaktoren_lines()` (App-Textformat, von beiden Detail-Panels
wiederverwendet).

**Verifikation:** 9 synthetische Testgruppen (Pure-Funktionen isoliert,
`compute_risikofaktoren_hebel()` reproduziert den echten AVAX-Fall korrekt
mit 3 negativen Flags, sauberer Gegenfall überwiegend positiv, Kurzschluss-
Fälle bei `hebel_erlaubt=False`/`cash_veto=True`, `post_check_hebel()`
End-to-End bestätigt Deckel-Wert UND Risikofaktoren-Liste gleichzeitig
korrekt). Tk-Smoke-Test beider Detail-Panels (alle 3 Abschnitte + Gegen-
argument + Risikofaktoren korrekt gerendert, inkl. Sortierung negativ vor
positiv). E-Mail-Formatierungstest (Gegenargument/Forecast/Risikofaktoren-
Text, leerer Fall ohne Exception). DB-Roundtrip-Test gegen echte
Produktions-DB-Kopie für beide Tabellen. Gesamt-Import-Check aller 15
geänderten Module fehlerfrei, `retail_konsens_hebel_deckel` lädt korrekt aus
`config.yaml`.

## Nachtrag (2026-07-19, gleicher Tag): "Info-Leichen" - automatischer Verfall
unanalysierter Hebel-Kandidaten

**Auslöser:** Nutzer bemerkte im Hebel-Tab eine lange Liste von Kandidaten
("Kandidat (wartet auf Analyse)") mit Zeitstempeln bis zu 3 Tage zurück und
fragte, ob sich diese von selbst ausschleichen. Antwort nach Codeprüfung:
**nein** - `hebel_triggers` bekommt bei jedem 15-Min-Screening-Tick nur dann
eine neue Zeile, wenn der Score-Schwellenwert erneut erreicht wird
(`agent/krypto/hebel_screening.py::run_hebel_screening()`). Sinkt der Score
später wieder (Marktbedingung nicht mehr gegeben), bleibt die alte
`status='neu'`-Zeile trotzdem als "neuester Kandidat" bestehen -
`update_hebel_trigger_status()` wird nur beim tatsächlichen LLM-Verbrauch
aufgerufen (`agent/krypto/hebel_pipeline.py`), es gab weder eine
Alters-Ablaufgrenze noch (anders als beim Marktscan-Tab) einen manuellen
"Ablehnen"-Button.

**Funktional relevant, nicht nur optisch:** `db.get_pending_hebel_candidates()`
sortiert nach `score_gesamt DESC`, nicht nach Aktualität - sowohl die
Hebel-Tab-Anzeige als auch der Budget-Allocator (`agent/krypto/
budget_allocator.py`) übernehmen diese Reihenfolge unverändert. Ein alter,
hoch bewerteter, aber längst überholter Kandidat konnte damit einen
frischen, niedriger bewerteten Kandidaten dauerhaft um das knappe
LLM-Budget verdrängen.

**Fix (Nutzerentscheidung: automatischer Verfall nach X Stunden, kein
manueller Button):** neue Funktion `database/db.py::
expire_stale_hebel_candidates(conn, verfall_stunden)` setzt Trigger mit
`status='neu'` und `screened_at` älter als die Schwelle auf
`status='verfallen'` (einfaches UPDATE, kein neuer Tabellen-Status-Enum
nötig, da `hebel_triggers.status` kein CHECK-Constraint hat). Aufgerufen am
Ende jedes Screening-Laufs (`run_hebel_screening()`, nach dem Insert aller
neuen Trigger), mit Log-Zeile bei tatsächlichem Verfall. Neuer Config-Wert
`hebel_screening.hebel_kandidat_verfall_stunden` (48h) - lang genug, um eine
einzelne budgetknappe Tagesphase zu überstehen, kurz genug, um wochenlanges
Anwachsen zu verhindern. Da sowohl die UI-Anzeige als auch der Allocator
`get_pending_hebel_candidates()` nutzen (WHERE `status='neu'`), verschwinden
verfallene Kandidaten automatisch aus beiden Stellen, ohne dass an der
Abfrage selbst etwas geändert werden musste.

**Verifiziert:** synthetischer In-Memory-Test (3 Kandidaten - alt/status=neu,
frisch/status=neu, alt/status=llm_generiert; nach Verfall bleibt nur der
frische als pending, der bereits verarbeitete bleibt unangetastet,
zweiter Aufruf ist idempotent/findet nichts mehr). DB-Roundtrip gegen eine
Kopie der echten Produktions-DB (1 echter Kandidat, FLOKI vom 14.07., korrekt
als verfallen erkannt und aus der Pending-Liste entfernt) - dabei auffällig:
die lokale Desktop-DB enthält deutlich weniger Kandidaten als der vom
Nutzer gezeigte Notebook-Screenshot, konsistent mit der bekannten
Desktop/Notebook-DB-Trennung (getrennte lokale Datenbanken, siehe Kapitel
zum USB-Sync-Workflow).

## Nachtrag (2026-07-19, gleicher Tag): Konsistenz-Ausweitung des Verfall-Fixes
auf Marktscan-Kandidaten

Nutzer bat explizit darum, den gerade gebauten Hebel-Verfall-Fix auf andere
Bereiche zu prüfen, damit das System konsistent bleibt. Codeweite Suche nach
allen "Kandidat-wartet-auf-Analyse"-Warteschlangen (Muster: `status='neu'`,
Selektion via Self-Join auf neuesten Eintrag) ergab genau eine weitere
Stelle mit derselben Struktur-Schwäche: `marktscan_candidates`
(`db.get_pending_marktscan_kaufkandidaten()`, ebenfalls
`score_gesamt DESC` statt aktualitätssortiert). Multi-Asset-Batch (Aktien/
Rohstoffe/Themen-ETF) und Hedge sind **strukturell nicht betroffen** - sie
iterieren pro Lauf direkt über die aktuelle Watchlist mit Cooldown-Logik
(`agent/multi_asset_batch.py::_kandidaten()`), es gibt dort keine separate
Scoring-Warteschlange, die veralten könnte.

**Fix (identisches Muster wie Hebel):** neue `database/db.py::
expire_stale_marktscan_candidates(conn, verfall_stunden)`, scoped auf
`einstufung='kaufkandidat' AND status='neu' AND groq_generiert_am IS NULL`
(exakt die Bedingungen von `get_pending_marktscan_kaufkandidaten()`). Neuer
Config-Wert `budget_allocator.marktscan_kandidat_verfall_stunden` (48h).
**Ein Unterschied zum Hebel-Fix:** der Aufruf sitzt NICHT in der Discovery-
Funktion (`agent/krypto/marktscan.py::run_scan()`, läuft nur 2x/Tag um
04:00/16:00), sondern in `agent/krypto/budget_allocator.py::
run_budget_allocator()` direkt vor dem Abruf der Pending-Kandidaten - der
Allocator läuft alle 15 Min (huckepack auf `hebel_screening_job`), damit
bleibt die Warteliste deutlich zeitnaher aktuell als bei einer Kopplung an
den seltenen Scan-Takt. Ergänzt (ersetzt nicht) den bereits bestehenden
manuellen "Ablehnen"-Button im Marktscan-Tab (`status=
'nutzer_verworfen'`) - der deckt nur Kandidaten ab, die der Nutzer aktiv
sieht und beurteilt, der automatische Verfall greift zusätzlich für alle
anderen. `ui/marktscan_view.py::STATUS_LABELS` um `"verfallen": "verfallen
(zu alt)"` ergänzt, damit der neue Status in der allgemeinen
Kandidatenliste lesbar dargestellt wird (die Pending-Abfrage selbst filtert
ihn bereits automatisch heraus).

**Verifiziert:** synthetischer In-Memory-Test (4 Kandidaten - alt/
kaufkandidat/neu, frisch/kaufkandidat/neu, alt/bereits mit
`groq_generiert_am` versehen, alt/andere Einstufung "beobachten"; nach
Verfall bleibt nur der frische pending, die anderen drei bleiben
unangetastet weil außerhalb der Verfall-Bedingung, zweiter Aufruf
idempotent). Import-Check aller geänderten Module fehlerfrei.

## Nachtrag (2026-07-19, gleicher Tag): echter KAITO-Fund - Geschwisterzeilen
beim Übernehmen/Verwerfen nicht mitaufgelöst

**Auslöser:** Nutzer hatte zum ersten Mal einen Marktscan-Kandidaten über
"In Watchlist übernehmen" real in die Watchlist aufgenommen (KAITO), die App
neu gestartet und danach im Marktscan-Tab immer noch eine KAITO-Zeile mit
Status "neu" gesehen - obwohl der Coin bereits übernommen war.

**Root Cause (zwei zusammenhängende Stellen):**
1. `marktscan_candidates` hat `UNIQUE(coingecko_id, scan_run_id)` - jeder
   neue Scan-Lauf, der denselben Coin erneut findet, legt eine EIGENE Zeile
   an. Klickt der Nutzer "In Watchlist übernehmen" auf EINER dieser Zeilen,
   setzte `ui/marktscan_view.py` bisher nur den Status GENAU dieser einen
   Zeile (`db.update_marktscan_candidate_status(conn, candidate.id, ...)`) -
   andere, bereits vorher ODER danach entdeckte Zeilen desselben Coins
   blieben unverändert `status='neu'` und wirkten wie eine "nie aktualisierte"
   Info-Leiche.
2. Zusätzlich fand sich beim Nachvollziehen ein zweiter, eigenständiger Bug:
   `db.get_latest_marktscan_status_by_coingecko_id()` (der Cross-Lauf-
   Duplikat-Check in `_duplicate_should_skip()`) sortiert nach
   `discovered_at DESC` - also nach ENTDECKUNGSZEITPUNKT, nicht danach,
   welche Zeile die tatsächliche Nutzer-ENTSCHEIDUNG trägt. Im KAITO-Fall
   war die spätere, nie angeklickte Zeile (14 Uhr) chronologisch "neuer" als
   die tatsächlich übernommene (2 Uhr) - die Funktion hätte fälschlich
   `'neu'` statt `'nutzer_behalten_manuell_uebernommen'` zurückgegeben, was
   künftige Scans theoretisch wieder hätte verwirren können (in diesem
   konkreten Fall zusätzlich durch den bereits vorhandenen
   Watchlist-Mitgliedschafts-Check in `_duplicate_should_skip()` abgefangen,
   aber nicht robust).

**Fix:** neue `database/db.py::resolve_marktscan_candidate_siblings(conn,
coingecko_id, status)` - setzt ALLE noch `status='neu'`-Zeilen desselben
`coingecko_id` auf den neuen Status. Aufgerufen direkt nach dem bestehenden
Einzelzeilen-Update in BEIDEN Handlern (`_on_adopt_to_watchlist_clicked()`
und `_on_reject_clicked()` in `ui/marktscan_view.py`). Löst damit auch
Punkt 2 auf, ohne die Sortierlogik selbst anfassen zu müssen: sobald alle
Zeilen eines entschiedenen Coins konsistent denselben Status tragen, ist es
irrelevant, welche davon `get_latest_marktscan_status_by_coingecko_id()`
zurückgibt. Nebenbei `_on_reject_clicked()` um ein fehlendes
`self._refresh_list()` ergänzt (war vorher nicht vorhanden, `_on_adopt_
to_watchlist_clicked()` hatte es bereits) - sonst wären die aufgelösten
Geschwisterzeilen zwar in der DB korrekt, aber nicht sofort sichtbar
gewesen.

**Verifiziert:** synthetischer Test reproduziert den echten KAITO-Fall 1:1
(zwei Zeilen desselben `coingecko_id`, früh entdeckte übernommen, spät
entdeckte bleibt `status='neu'`) - bestätigt zunächst den Bug
(`get_latest_marktscan_status_by_coingecko_id()` liefert fälschlich `'neu'`),
dann den Fix (nach `resolve_marktscan_candidate_siblings()` liefert dieselbe
Abfrage korrekt `'nutzer_behalten_manuell_uebernommen'`, die zweite Zeile
trägt jetzt denselben Status, zweiter Aufruf idempotent). Import-Check
fehlerfrei.

## Nachtrag (2026-07-19, gleicher Tag): Watchlist-Tab-Konsistenzprüfung -
fehlende coingecko_id verschwendet dauerhaft Spot-Budget

**Auslöser:** Nutzer bat explizit darum, die Watchlist-Tab-Konsistenz
ebenfalls zu prüfen (nach den Info-Leichen-Funden bei Hebel/Marktscan).
Codeprüfung ergab keine Duplikat-/Entfernungs-Lücke (`add_watchlist_entry()`
prüft bereits zentral auf doppelte Symbole, alle drei Aufrufer -
Marktscan-Übernehmen, manueller "Asset hinzufügen"-Dialog, Hebel-Auto-Add -
nutzen dieselbe Funktion; ein "Watchlist entfernen"-Feature existiert
bewusst nicht, die Datei ist explizit handgepflegt). Stattdessen ein
eigenständiger, bisher unbemerkter struktureller Bug gefunden.

**Root Cause:** ein per `importer/bitpanda_margin_positions.py::
auto_add_unknown_hebel_symbols()` automatisch ergänztes Krypto-Asset (offene
Hebel-Position auf einem noch unbekannten Symbol) bekommt bewusst KEINE
`coingecko_id` (keine zuverlässige automatische Symbol→ID-Auflösung, siehe
Docstring dort). `agent/krypto/signal_batch.py::
select_assets_due_for_signal()` filterte bisher nur nach `assetklasse ==
"krypto"`, nicht zusätzlich auf eine gesetzte `coingecko_id`. Ohne ID liefert
`agent/krypto/pipeline.py::generate_signal()` strukturell IMMER sofort ein
Fixed-HALTEN (`gate_reason='keine historischen Daten vorhanden'`), OHNE
`groq_raw_response` zu setzen - `db.get_latest_real_signal_per_symbol()`
(WHERE `groq_raw_response IS NOT NULL`) sieht das Asset dadurch für immer als
"nie berechnet". Da `select_assets_due_for_signal()` "nie berechnet zuerst"
sortiert, wäre so ein Asset bei JEDEM 15-Min-Budget-Allocator-Lauf dauerhaft
an Position 1 der Prioritätsliste gelandet und hätte einen echten
Spot-Budget-Slot verschwendet - unbegrenzt, ohne jede sichtbare Warnung.
Aktuell 0 betroffene Symbole in der lokalen Watchlist (noch nicht
zugeschlagen), aber strukturell jederzeit möglich, sobald eine Hebel-Position
auf einem neuen, unbekannten Symbol eröffnet wird.

**Fix (zwei Ebenen, gleiches Muster wie beim Info-Leichen-Fix):**
1. `select_assets_due_for_signal()` filtert jetzt zusätzlich auf
   `a.coingecko_id` (truthy) - das Asset wird gar nicht erst als Kandidat
   ausgewählt, verschwendet also keinen Slot mehr.
2. `ui/app.py::_refresh_watchlist_from_db()` markiert ein betroffenes Asset
   sichtbar in der Status-Spalte ("⚠ keine CoinGecko-ID", neuer Tag
   `coingecko_id_fehlt`, `theme.danger_color()` wie beim bestehenden
   `bitpanda_fehlt`-Muster) UND in der Spalten-Kopfzeilen-Tooltip - der
   Nutzer sieht so weiterhin, WARUM Spot-Analyse für dieses Symbol inaktiv
   ist, und kann die ID über den bestehenden "Asset hinzufügen/bearbeiten"-
   Dialog nachtragen. `ui/signals_view.py`s identisches Filtermuster (manuelle
   "Signal berechnen"-Auswahl) bewusst NICHT geändert - ein manueller Klick
   liefert dort bereits eine klare, sofortige Fehlermeldung, kein
   wiederkehrender stiller Ressourcenverbrauch wie beim automatischen
   Allocator.

**Verifiziert:** synthetischer Test von `select_assets_due_for_signal()`
(Asset ohne `coingecko_id` wird korrekt ausgeschlossen, Asset mit ID bleibt
Kandidat). Tk-Smoke-Test der Watchlist-Tab-Zeile (Asset ohne ID zeigt korrekt
"⚠ keine CoinGecko-ID" + gesetztes Tag, unbetroffenes Asset bleibt
unverändert). Echte Watchlist-Prüfung: aktuell 0 betroffene Symbole.

## Nachtrag (2026-07-19, gleicher Tag): CoinGecko-Symbolsuche im
"Asset hinzufügen/bearbeiten"-Dialog

**Auslöser:** Nutzer fragte direkt nach der obigen Warn-Markierung, warum die
`coingecko_id` nicht einfach automatisch aus dem Symbol ergänzt werden kann.
Live gegen die echte CoinGecko-API geprüft, um die Antwort auf Fakten statt
Vermutung zu stützen: das Symbol (z. B. "SOL") ist bei CoinGecko NICHT
eindeutig - `coingecko_id` ist der interne eindeutige Schlüssel, das Symbol
nur der Ticker. Konkret geteilt: **12 verschiedene IDs** tragen den Ticker
"SOL" (das echte Solana plus 11 gebrückte/gewrappte Varianten über andere
Chains - Base, Near, Eclipse, Neon, Osmosis, Binance). Insgesamt sind 2.116
von 13.704 Symbolen bei CoinGecko mehrdeutig. Eine stille automatische
Zuordnung (z. B. "erstes Ergebnis nehmen") hätte das Risiko, dauerhaft die
FALSCHE Coin-Historie zu laden, ohne dass es auffällt. Marktkapitalisierung
disambiguiert aber zuverlässig (bei SOL: echtes Solana Rang 7 / ~44 Mrd. $,
die Wrapped-Varianten ohne Rang und nur Bruchteile davon) - deshalb Suche
mit Nutzer-Bestätigung statt automatischer Auswahl.

**Umgesetzt (drei Ebenen):**
1. Neue `api/coingecko.py::CoinGeckoClient.search_coins(query)` - nutzt
   CoinGeckos `/search`-Endpunkt (liefert `market_cap_rank` bereits mit, kein
   zusätzlicher `/coins/markets`-Call nötig), sortiert exakte Symbol-Treffer
   zuerst nach Rang aufsteigend (kein Rang zuletzt), danach die übrigen
   Namens-Treffer in CoinGeckos eigener Relevanz-Reihenfolge.
2. Neuer `ui/app.py::CoinSearchDialog` - zeigt die Treffer in einer Tabelle
   (Symbol/Name/ID/Rang), Nutzer wählt per Doppelklick oder Button, KEINE
   automatische Vorauswahl auch bei nur einem Treffer.
3. Neuer "Suchen …"-Button neben dem CoinGecko-ID-Feld in `AssetAddDialog`
   UND `AssetEditDialog` - **wichtiger Nebenbefund dabei:** `AssetEditDialog`
   bot das Feld bisher überhaupt nicht an (Docstring: "Symbol/Name/
   CoingeckoID etc. bleiben hier unverändert"), es gab also für ein bereits
   BESTEHENDES Asset (z. B. genau die im vorherigen Nachtrag beschriebenen
   automatisch ergänzten Hebel-Symbole) gar keinen GUI-Weg, die ID
   nachzutragen - nur beim Erst-Anlegen über `AssetAddDialog`. Jetzt
   ergänzt, sichtbar nur für `assetklasse=krypto`, mit derselben
   Warn-Markierung wie im Watchlist-Tab, falls die ID noch fehlt. Neue
   `config.py::update_watchlist_coingecko_id()` - eigenständige
   Implementierung statt Erweiterung von `_update_watchlist_field()` (die
   kann nur bereits VORHANDENE Feldzeilen aktualisieren, keine neuen
   einfügen - `add_watchlist_entry()` lässt die Zeile bei `coingecko_id=None`
   komplett weg). Fügt die Zeile bei Bedarf direkt nach `beobachtungsstatus:`
   ein (identische Position wie beim Erst-Anlegen), sonst wird die
   vorhandene Zeile aktualisiert - gleiches Backup+Validierungs+Rollback-
   Muster wie alle anderen `config.yaml`-Schreibfunktionen.

**Verifiziert:** live gegen die echte CoinGecko-API (Symbolmehrdeutigkeit
quantifiziert, `search_coins()` liefert für "SOL" korrekt "solana" als
ersten exakten Treffer). Synthetischer Test von
`update_watchlist_coingecko_id()` gegen eine Konfigurationskopie (Einfügen
einer neuen Zeile, Aktualisieren einer vorhandenen, Idempotenz bei
gleichem Wert, unbekanntes Symbol - alle 4 Fälle korrekt). Tk-Smoke-Test
der kompletten Kette: `CoinSearchDialog` direkt, `AssetAddDialog` mit
Suchen-Button, `AssetEditDialog` für ein Krypto-Asset ohne ID (Feld+Warnung
sichtbar, Suche+Auswahl übernimmt korrekt) und für ein Nicht-Krypto-Asset
(Feld bleibt korrekt unsichtbar) - sowie ein echter End-to-End-Test des
kompletten Speicherpfads gegen eine Konfigurationskopie (`_on_submit()`
persistiert die gewählte ID tatsächlich in `config.yaml`).

## Nachtrag (2026-07-19, gleicher Tag): automatische coingecko_id-Aufloesung
per Bitpanda-Namensabgleich - Dialog kommt gleich bei der Aufnahme

**Auslöser:** Nutzer stellte zwei zusammenhängende Fragen zur gerade gebauten
CoinGecko-Symbolsuche: (1) ob der Suchdialog nicht direkt bei der Aufnahme
in die Watchlist erscheinen sollte statt einen manuellen "Suchen"-Klick zu
verlangen, (2) ob der bereits vorhandene CoinGecko-Scan-mit-Bitpanda-Prüfung-
Ablauf (Marktscan-Discovery) das Symbol nicht schon eindeutig machen sollte,
bevor überhaupt eine manuelle Auswahl nötig wird. Live geprüft: Bitpandas
kuratierter Katalog listet nie zwei verschiedene Coins unter demselben
Ticker - der Bitpanda-Name für SOL ("Solana") matcht exakt GENAU EINEN von
25 CoinGecko-Suchtreffern für "SOL". Diese Kreuzreferenz löst die
Mehrdeutigkeit in der überwiegenden Mehrheit der Fälle automatisch auf,
ohne dass der Nutzer manuell auswählen muss - eine echte Mehrdeutigkeit
(kein oder mehr als ein Namenstreffer) bleibt dabei eine ECHTE Inkonsistenz
zwischen Bitpanda- und CoinGecko-Katalog, kein Fall für automatisches Raten.

**Umgesetzt (drei Ebenen):**
1. `api/bitpanda.py::find_listed_asset()` - wie `is_listed()`, gibt aber das
   tatsächlich gefundene `BitpandaAsset`-Objekt zurück statt nur eines Bool
   (fürs Namensfeld gebraucht). `is_listed()` selbst ruft die neue Funktion
   nur noch auf (reiner Refactor, verhaltensidentisch, Regressionstest
   bestätigt).
2. `api/coingecko.py::resolve_coingecko_id_by_name(results, expected_name)`
   - reine Funktion, filtert `search_coins()`-Treffer auf Namensgleichheit,
   gibt nur bei GENAU EINEM Treffer die ID zurück, sonst `None`.
3. Neue gemeinsame `ui/app.py::_try_auto_resolve_coingecko_id(symbol,
   coingecko_client)` - kombiniert beide Bausteine (Bitpanda-Listing prüfen
   + Namensabgleich), genutzt von:
   - **`AssetAddDialog._on_submit()`**: bei leerem CoinGecko-ID-Feld und
     `assetklasse=krypto` wird zuerst still automatisch aufgelöst; schlägt
     das fehl (nicht bei Bitpanda gelistet ODER echte Mehrdeutigkeit), öffnet
     sich der `CoinSearchDialog` jetzt AUTOMATISCH (`self.wait_window()`,
     blockiert bis zur Nutzer-Auswahl/zum Abbrechen) - genau der vom Nutzer
     gewünschte "kommt gleich bei der Aufnahme"-Ablauf, kein manueller Klick
     mehr nötig im Regelfall.
   - **`AssetEditDialog.__init__()`**: still (KEIN Dialog-Popup) versucht,
     sobald ein Krypto-Asset ohne ID geöffnet wird - deckt genau den Fall ab,
     der die ganze Erweiterung ausgelöst hat (automatisch aus einer Hebel-
     Position ergänzte Symbole). Kein Popup beim blossen Öffnen, da der
     Nutzer den Dialog auch nur für rolle/beobachtungsstatus öffnen könnte -
     die Warn-Markierung verschwindet automatisch, wenn die stille Auflösung
     erfolgreich war.
   - **`importer/bitpanda_margin_positions.py::
     auto_add_unknown_hebel_symbols()`**: neuer optionaler `coingecko_client`-
     Parameter (aus `scheduler/background.py::hebel_screening_job()` bereits
     im Scope durchgereicht) - versucht dieselbe Auflösung, BEVOR der
     Watchlist-Eintrag geschrieben wird. Der Nutzer-Punkt "in dieser Schleife
     sollte das Symbol schon eindeutig sein" trifft damit jetzt genau zu -
     das Bitpanda-Listing wird an dieser Stelle ohnehin schon geprüft
     (`find_listed_asset()`), der Namensabgleich kostet nur einen
     zusätzlichen `search_coins()`-Call. `coingecko_client=None` erhält das
     alte Verhalten (ID bleibt leer) für Aufrufer ohne Netzwerkzugriff.

**Verifiziert:** Regressionstest von `is_listed()` nach dem Refactor
(identisches Verhalten). Synthetischer Test von
`resolve_coingecko_id_by_name()` (eindeutig/mehrdeutig/kein Treffer).
Synthetischer Test von `auto_add_unknown_hebel_symbols()` mit drei Fällen
(automatische Auflösung erfolgreich, `coingecko_client=None` behält altes
Verhalten, mehrdeutiger Namenstreffer fällt korrekt auf leer zurück statt
abzustürzen) gegen eine Konfigurationskopie. Tk-Smoke-Test des kompletten
`AssetAddDialog`-Submit-Flows (automatische Auflösung UND automatisch
geöffneter `CoinSearchDialog` bei Mehrdeutigkeit, jeweils bis zum
tatsächlichen Schreiben in `config.yaml` durchgetestet) sowie von
`AssetEditDialog` (stille Auflösung beim Öffnen, Warn-Markierung
verschwindet korrekt bei erfolgreicher Auflösung).

## Nachtrag (2026-07-19, gleicher Tag): Konsistenzprüfung über ALLE
Assetklassen - echter Absturz-Fund bei Aktien ohne yfinance-Symbol

**Auslöser:** Nutzer bat explizit darum, die coingecko_id-Konsistenzprüfung
nicht nur für Krypto/Hebel, sondern für alle Bereiche durchzuführen ("prüfe
das gegenüber allen Bereichen nicht nur Hebel, Spot, etc."). Systematisch
alle vier Multi-Asset-Pipelines (Aktien/Rohstoffe/Hedge/Themen-ETF) auf das
Krypto-Muster (fehlende externe ID → strukturell nie erfolgreiche
Analyse) geprüft.

**Echter, eigenständiger Fund - Absturz statt nur Budget-Verschwendung:**
`agent/aktien/pipeline.py::_ensure_ohlc_backfilled()` rief
`get_full_ohlc_history(asset.yfinance_symbol, ...)` bisher OHNE Guard auf -
im Gegensatz zum strukturell identischen `agent/themen_etf/pipeline.py`,
das den Guard (`if not asset.yfinance_symbol: ... return`) bereits hatte.
Live bestätigt: `yf.Ticker(None)` wirft `AttributeError: 'NoneType' object
has no attribute 'upper'`. Ein manuell hinzugefügtes Aktien-Asset ohne
yfinance-Symbol (im "Asset hinzufügen"-Dialog als "optional" markiert)
hätte damit sowohl im automatischen Multi-Asset-Batch als auch beim
manuellen "Signal berechnen"-Klick einen rohen, unbehandelten Absturz
ausgelöst statt einer sauberen HALTEN-Meldung.

**Geprüft und für strukturell unbetroffen befunden:**
- `agent/rohstoff/pipeline.py`: nutzt einen hartkodierten Futures-Ticker
  (`SYMBOL_ZU_FUTURES_TICKER`), unabhängig vom Watchlist-Feld - ein neues
  Rohstoff-Asset bräuchte ohnehin eine Code-Änderung, kein GUI-Feld dafür.
- `agent/hedge/pipeline.py`: braucht überhaupt keine OHLC-Historie (arbeitet
  nur mit Live-Preisen + Portfolio-Exposure).
- **Auto-Add-Mechanismus:** `config.py::add_watchlist_entry()` wird
  automatisch nur an GENAU EINER Stelle aufgerufen
  (`auto_add_unknown_hebel_symbols()`) - kein analoges automatisches
  Hinzufügen für Aktien/Rohstoffe/ETF, die kommen nur über den manuellen
  "Asset hinzufügen"-Dialog rein.

**Fix (drei Ebenen, gleiches Muster wie beim Krypto-Fund):**
1. `agent/aktien/pipeline.py::_ensure_ohlc_backfilled()` bekommt denselben
   Guard wie `themen_etf/pipeline.py` - fällt jetzt sauber in den bereits
   vorhandenen `len(closes)==0`-Pfad (Fixed-HALTEN mit klarem
   `gate_reason`) statt abzustürzen.
2. `agent/multi_asset_batch.py::_kandidaten()` schließt Aktien- UND
   Themen-ETF-Assets ohne `yfinance_symbol` jetzt aus der automatischen
   Kandidatenauswahl aus (analog zu `signal_batch.py`s coingecko_id-Filter)
   - Rohstoffe/Hedge bleiben unberührt (siehe oben).
3. `ui/app.py::_refresh_watchlist_from_db()` markiert betroffene Aktien-/
   Themen-ETF-Assets jetzt ebenfalls sichtbar ("⚠ kein yfinance-Symbol").
   Das bisherige Tag `coingecko_id_fehlt` wurde dafür in `externe_id_fehlt`
   umbenannt (deckt jetzt beide Fälle ab, gleiche rote Hervorhebung).

**Verifiziert:** synthetischer Regressionstest des Absturz-Fixes (Guard
verhindert die `AttributeError`, `_load_ohlc()` bleibt korrekt leer).
Synthetischer Test von `_kandidaten()` mit 6 Fällen (Aktie mit/ohne ID,
Themen-ETF mit/ohne ID, Rohstoff ohne ID bleibt Kandidat, Hedge-Instrument
ohne ID bleibt Kandidat). Tk-Smoke-Test der erweiterten Watchlist-Tab-
Warnung (Aktie/ETF ohne ID markiert, Hedge-Instrument korrekt unmarkiert).

## Nachtrag (2026-07-19, gleicher Tag): Backtracking-Aussagekraft-Audit - Überholt-Erkennung neutralisierte die eigene Ergebnisstatistik

**Auslöser:** Nutzer bat vor der Governance-Diskussion (Selbstverifikations-
Vision Schritt 3, siehe Kap. 7) darum, sicherzustellen, dass Backward-
Tracking "sauber funktioniert und auch kurzfristig eine gewisse
Aussagekraft hat" - erst wenn das gewährleistet ist, soll die Governance-
Frage angegangen werden.

**Echter, gravierender Fund:** Live gegen den frischesten Notebook-
Datenexport geprüft (`notebook_diagnose.json`, 2026-07-19), da die lokale
Desktop-DB seit dem NB-Umzug veraltet ist. Ergebnis: von 9 trackbaren Spot-
Signalen (KAUFEN/NACHKAUFEN) wurden **alle 9 (100%)** als "überholt"
markiert, bevor der Kurs jemals gegen Take-Profit/Stop-Loss geprüft werden
konnte (nach durchschnittlich ~29 Std., Spanne 18-56 Std.) - **kein
einziges** reales Ergebnis liegt vor. Bei Hebel wurden 21 von 35 ERÖFFNEN-
Signalen (60%) nach durchschnittlich **11,7 Std.** (Spanne 4,2-22,7 Std.)
überholt; nur 2 von 35 kamen je zu einem echten Ergebnis (beide Stop-Loss,
beide aus der inzwischen entfernten Cerebras-Ära - die aktuelle Kette
Groq/Mistral/Gemini hat bislang null ausgewertete Ergebnisse).

**Root Cause:** `_is_superseded()` (Kap. „Info-Leichen"-Nachtrag oben,
2026-07-16 eingeführt gegen doppelte/widersprüchliche Anzeigen) markierte
ein offenes KAUFEN/ERÖFFNEN als überholt, sobald **irgendein** neueres
reales Signal für dasselbe Symbol vorlag - unabhängig von dessen Aktion.
Da HALTEN die weit überwiegende Aktion ist (>95%) und gehaltene/offene
Positionen sehr häufig neu bewertet werden (`hebel_position_cooldown_
stunden`: 3 Std., `spot_cooldown_stunden_kern`: 8 Std.), wurde praktisch
jede offene Kauf-These durch eine bloße HALTEN-Bestätigung "überholt" -
lange bevor ein realistischer mehrtägiger Kursverlauf Take-Profit/Stop-Loss
überhaupt erreichen konnte. Die Funktion, die Doppel-Anzeigen verhindern
sollte, hielt dadurch strukturell die Ergebnisstatistik leer, die
Governance Schritt 3 als Grundlage braucht.

**Fix 1 - Überholt-Erkennung eingeschränkt:** `_is_superseded()` (Spot UND
Hebel) überholt eine offene These jetzt nur noch bei einer echten neuen
Aktion (erneutes KAUFEN/NACHKAUFEN/ERÖFFNEN = redundant, oder VERKAUFEN/
TAUSCHEN/SCHLIESSEN/HEBEL_SENKEN = widersprechend) - eine reine HALTEN-
Bestätigung widerspricht der offenen These nicht und überholt sie nicht
mehr. Die ursprüngliche Absicht (Duplikate/Widersprüche ausblenden) bleibt
dadurch unverändert erhalten.

**Fix 2 - inhaltsbasierte Ablaufzeit statt fixer 90-Tage-Frist:** Nutzer-
Vorgabe: "der zeitliche Faktor sollte durch den Inhalt bzw. Angabe - wann
soll ein Zielwert erreicht werden - besser abschätzbar sein". Statt eine
neue Datenstruktur zu erfinden, wird das bereits bestehende, vom Modell
zuverlässig gefüllte `halte_kriterium` genutzt (Regel 17 in
`analyst.py`/`hebel_analyst.py`, bereits vollständig als eigene
Spalten in `signals`/`hebel_signals` persistiert): `ziel_datum` hat
Vorrang, wenn gesetzt (in der Praxis fast nie - live geprüft: 0 von 9
Fällen), sonst der grobe `bucket` (kurz/mittel/lang, in der Praxis
**zuverlässig** gefüllt - live geprüft: 9 von 9 Fällen). Neue Config-Werte
`backward_tracking.abgelaufen_nach_tagen_bucket` (kurz: 14, mittel: 45,
lang: 120 Tage) + `abgelaufen_nach_tagen_fallback` (90 Tage, für ältere
Signale ohne halte_kriterium) ersetzen den alten einzelnen
`abgelaufen_nach_tagen`-Wert. Die konkreten Tageswerte sind selbst
`[OFFEN]`/vorläufig (siehe Kap. 15), erste plausible Startwerte analog dem
bisherigen 90-Tage-Vorschlag.

**Fix (drei Dateien, identisches Muster fuer Spot und Hebel):**
1. `agent/krypto/backward_tracking.py`: `_is_superseded()` + `_is_expired()`
   wie beschrieben geändert, `DEFAULT_ABGELAUFEN_TAGE_BUCKET`/
   `DEFAULT_ABGELAUFEN_TAGE_FALLBACK` ersetzen `DEFAULT_ABGELAUFEN_NACH_
   TAGEN`.
2. `agent/krypto/hebel_backward_tracking.py`: identischer Fix (mirror-
   Muster), importiert die neuen Konstanten von oben.
3. `Basisinfos/config.yaml`: `backward_tracking`-Sektion umgestellt.

**Verifiziert:** 14 synthetische Tests (HALTEN überholt nicht mehr/andere
Aktionen weiterhin doch, für Spot UND Hebel; bucket-Mapping kurz/mittel/
lang; ziel_datum-Override in beide Richtungen; Fallback bei fehlendem
bucket; ungültiges ziel_datum fällt korrekt auf bucket zurück). Echter Lauf
gegen eine Kopie der Produktions-DB: von 51 vorher unverarbeiteten Spot-
Signalen bleiben danach korrekt nur die 2 tatsächlich noch unentschiedenen
trackbaren Signale offen (vorher wären sie durch die alte Regel fälschlich
überholt worden, da fuer beide zwischenzeitlich nur HALTEN-Bestätigungen
vorlagen), alle anderen korrekt `nicht_anwendbar`.

## Nachtrag (2026-07-19, gleicher Tag): 29× "Auto-Add unbekannter
Hebel-Symbole fehlgeschlagen" im Notebook-Export - Bug war bereits gefixt,
keine neue Ursache

**Auftrag:** vollen Traceback zu 29 Vorkommen von "Auto-Add unbekannter
Hebel-Symbole fehlgeschlagen" im `notebook_diagnose.json`-Export finden,
Root Cause klären, fixen.

**Ergebnis: kein neuer Fix nötig - der Export zeigt einen bereits
abgeschlossenen Vorfall.** Vollständiger Traceback aus `log_auszug`
extrahiert (72h-Fenster, `job_fehlschlaege` listet nur die Kurzmeldung ohne
Traceback): 28 der 29 Vorkommen sind exakt der `AttributeError: 'str'
object has no attribute 'get'`-Bug aus `get_listed_assets(bitpanda_api_key)`
statt `get_listed_assets()` - **derselbe Bug, der bereits am selben Tag
(2026-07-16, Commit `fe970ef`) live anhand eines FRÜHEREN
Notebook-Diagnose-Exports gefunden und gefixt wurde** (siehe
Commit-Nachricht: "Live in den Notebook-Logs gefunden
(Notebook_Analysedaten-Export)"). Alle 28 Vorkommen liegen zeitlich
zwischen 2026-07-16 13:10:02 und 2026-07-17 02:52:35 - der Fix wurde um
15:33 Uhr desselben Tages committet, das Notebook lief bis zum nächsten
USB-Sync aber noch mit dem alten Code weiter (siehe
[[reference_usb_sync_workflow]]). Aktueller Code
(`scheduler/background.py`, `importer/bitpanda_margin_positions.py`,
`api/bitpanda.py`) wurde geprüft und ruft an allen vier Stellen bereits
korrekt `get_listed_assets()` ohne Positionsargument auf - keine Änderung
nötig, per Signatur-Check bestätigt.

Das **29. Vorkommen** (2026-07-17 02:52:35, letztes in der Reihe) ist ein
eigenständiger `requests.exceptions.ReadTimeout` gegen
`api.bitpanda.com` (15s-Timeout in `_fetch_all_bitpanda_assets()`,
paginierter Abruf des gesamten Asset-Katalogs) - eine normale transiente
Netzwerkstörung, kein Code-Fehler, kein Wiederholungsmuster (kein weiteres
Vorkommen im restlichen 72h-Fenster bis 2026-07-19 06:03). Konsistent mit
dem bestehenden Muster anderer transienter API-Fehler in diesem Projekt
(z. B. FRED-Timeouts), die ebenfalls ohne Sonderbehandlung beim nächsten
15-Min-Tick automatisch erneut versucht werden - `hebel_screening_job`
fängt den Fehler ohnehin lokal ab (eigener `try/except` um den Auto-Add-
Aufruf), sodass weder der restliche Job-Lauf noch die U-8-Job-Ausfall-
E-Mail-Benachrichtigung betroffen sind.

**Wichtige Korrektur der Auftragsbeschreibung:** der im Auftrag genannte
"letzter Treffer 2026-07-19 06:03:30" bezieht sich nicht auf diese
Fehlermeldung - der tatsächlich letzte "Auto-Add..."-Eintrag im Export
liegt auf 2026-07-17 02:52:35. Der spätere Zeitstempel gehört zu einer
andersartigen, unabhängigen Meldung ("FRED-Abruf für bok_diskontsatz
fehlgeschlagen"). Lektion: bei mehrdeutigen/verwechselbaren Log-Zeitstempel-
Angaben im Auftrag den vollen `job_fehlschlaege`/`log_auszug`-Datensatz
selbst nachprüfen statt die genannten Eckwerte ungeprüft zu übernehmen.

**Verifiziert:** vollständige Traceback-Extraktion aller 29 Vorkommen aus
`log_auszug` (Python-Skript, Gruppierung per Zeitstempel-Regex), Diff der
Exception-Endzeilen (2 eindeutige Cluster: `AttributeError` × 28,
`ReadTimeout` × 1). Aktueller Code an allen 4 `get_listed_assets()`-
Aufrufstellen per `grep` + Signatur-Introspektion (`inspect.signature()`)
gegengeprüft - keine Regression.

## Nachtrag (2026-07-19, gleicher Tag): zwei neue Datenquellen - FRED-CPI-Kalender + SEC-EDGAR-Insider-Trading

**Auslöser:** direkter Nachfolger der Backtracking-Aussagekraft-Audit-Runde:
Nutzer wollte generell, "nicht nur Krypto", zusätzliche Marktdaten-Quellen
zur Aufwertung der LLM-Abfragen recherchiert haben - mit dem expliziten
Hinweis, dass X (Twitter) und YouTube bereits als problematisch bekannt sind
(API-Kosten bzw. ToS-Risiko) und deshalb nicht erneut vertieft werden
müssen. Ein spezialisierter Recherche-Agent lieferte eine priorisierte
Top-5-Liste kostenloser, offizieller Quellen; Nutzer entschied sich, mit
FRED-Release-Kalender + SEC-EDGAR-Insider-Trading zu beginnen.

### FRED-CPI-Veröffentlichungskalender (analog zum bestehenden FOMC-Kalender)

Live gegen die echte FRED-API verifiziert (`/fred/series/release`,
`/fred/release/dates`): CPI hat `release_id=10`. Bewusst NUR CPI
aufgenommen, nicht alle bereits genutzten `FRED_SERIES` - H.15 (Fed Funds,
`release_id=18`) wird taeglich veröffentlicht und wäre als "bevorstehendes
Ereignis" nie aussagekräftig (immer "morgen"), M2/ISM-Ersatz haben keinen so
ausgeprägten Markt-Reaktions-Charakter wie der monatliche CPI-Print. Live
auch bestätigt: FRED veröffentlicht den JEWEILS NÄCHSTEN Termin nicht immer
im Voraus (kurz nach einem CPI-Print am 2026-07-14 lieferte die API noch
keinen Eintrag für den nächsten Termin) - kein Fehler, `get_next_fred_release()`
liefert dann korrekt `None` statt zu raten (P-10).

**Umgesetzt:** `api/macro.py::get_next_fred_release()`/`get_upcoming_fred_releases()`
(neu, `FRED_RELEASE_IDS`-Konstante). `agent/krypto/pipeline.py::
fetch_market_context()` bekommt einen neuen optionalen `fred_api_key`-
Parameter und füllt `naechste_cpi_veroeffentlichung` analog zu
`upcoming_fomc` (gleiches Footprint wie der bestehende FOMC-Kalender:
Spot/Hebel/Marktscan - NICHT Aktien/Rohstoffe/Hedge/Themen-ETF, die nutzen
`fetch_market_context()` bisher nicht). Drei Aufrufstellen entsprechend
angepasst (`agent/krypto/pipeline.py::generate_signal()`,
`agent/krypto/hebel_pipeline.py::generate_hebel_signal()`,
`agent/krypto/marktscan.py::generate_candidate_writeup()` inkl. dessen
beiden Callern `budget_allocator.py`/`ui/marktscan_view.py`). Neue Regel 13-
Erweiterung in `agent/krypto/analyst.py` (analog zur bestehenden FOMC-Regel:
CPI-Print innerhalb von 5 Tagen wird als möglicher kurzfristiger
Volatilitäts-Faktor in `key_risks` erwähnt), reines Fakten-Feld in
`agent/krypto/hebel_analyst.py` (kein eigener Regeltext, wie beim FOMC-
Pendant dort auch).

**Verifiziert:** live gegen die echte FRED-API (Endpunkt-Verhalten,
inkl. des "noch kein Termin bekannt"-Falls). Synthetischer Test der
Facts-Zusammenbau-Logik (gesetzter Fakt/None/fehlender Key). Echter
End-to-End-Lauf von `fetch_market_context()` mit und ohne Key - kein Fehler.

### SEC-EDGAR-Insider-Trading (Form 4, nur Aktien-Pipeline)

Live gegen die echte SEC-EDGAR-API verifiziert (CIK-Auflösung für VST/PLTR,
echte Form-4-Rohdaten-XML-Struktur): `submissions/CIK##########.json`
liefert die Filing-Liste inkl. `primaryDocument`-Pfad wie
"xslF345X06/wk-form4_XXXX.xml" - das ist die XSLT-GERENDERTE HTML-Ansicht,
NICHT die Rohdaten. Die eigentliche Roh-XML mit den strukturierten
Transaktionsdaten liegt im selben Verzeichnis OHNE das "xslF345X06/"-
Präfix (für beide Testfälle bestätigt) - reiner String-Präfix-Strip, kein
zusätzlicher Index-Abruf nötig. Nur Transaktionscode P (offener Markt-Kauf)
und S (offener Markt-Verkauf) gelten als echtes Insider-Conviction-Signal -
A (Zuteilung/Grant), M (Optionsausübung), F (Steuerabzug) etc. sind
administrativ/vergütungsbedingt und werden bewusst herausgefiltert (P-10:
keine Fehlinterpretation als Kauf-/Verkaufssignal).

**Umgesetzt:** neue `api/sec_edgar.py` (kein API-Key nötig, nur ein
Pflicht-User-Agent-Header laut SEC-Vorgabe) -
`get_cik_for_ticker()` (in-memory gecacht, die ~800KB-Gesamtliste wird
nur einmal pro App-Lauf geladen), `get_recent_insider_transactions()`
(max. 5 Filings, 90-Tage-Fenster), `summarize_insider_activity()`
(Aggregation zu Kauf-/Verkaufszahlen + -Volumen, reine Lesefunktion, keine
Bewertung). `agent/aktien/analyst.py::build_facts()` bekommt neuen
`insider_trading`-Parameter, neue Regel 22 (niedrig gewichteter
Zusatzkontext, explizite Warnung vor Überinterpretation einzelner
Transaktionen - Insider-Verkäufe sind oft routinemäßig/steuerlich bedingt).
`agent/aktien/pipeline.py::generate_signal()` ruft den Abruf mit
`asset.yfinance_symbol` (nicht `asset.symbol` - SEC braucht den echten
Börsen-Ticker) in einem eigenen try/except auf, degradiert bei Fehlschlag
auf `None` (P-10). `remote/server.py::API_HEALTH_GROUPS` um `sec_edgar`
ergänzt.

**Verifiziert:** live gegen die echte SEC-EDGAR-API fuer VST und PLTR
(reale Insider-Transaktionen korrekt geparst, inkl. Edge-Case unbekannter
Ticker -> leere Liste statt Fehler). JSON-Serialisierbarkeit geprüft.
**Echter End-to-End-Signal-Lauf fuer VST gegen eine Kopie der (migrierten)
Produktions-DB, inklusive echter LLM-Antwort (Mistral):** das Modell hat
den neuen Fakt tatsächlich in seiner Begründung verwendet ("Die
Insideraktivitäten sind negativ") - nicht nur strukturell verdrahtet,
sondern nachweislich wirksam. Ein erster Versuch mit Groq schlug wegen
bereits ausgeschöpftem Tageskontingent fehl (429), kein Code-Fehler.

**Bewusst nicht umgesetzt (Nutzer-Vorgabe: "Fang mit FRED-Kalender + SEC
EDGAR an"):** die weiteren drei Top-5-Empfehlungen (EIA-Energiedaten,
Finnhub Recommendation-Trends/Earnings-Kalender, FINRA Equity Short
Interest) bleiben als nächste Kandidaten vorgemerkt, sobald gewünscht.

## Nachtrag (2026-07-19, gleicher Tag): EIA-Erdgas-Lagerbestand + Finnhub-Analysten-Trend

**Auslöser:** direkter Nachfolger obigen Nachtrags - Nutzer bat "Fang mit EIA
und Finnhub an".

**Wichtiger Unterschied zu FRED/SEC-EDGAR (Ehrlichkeits-Hinweis, P-10):**
beide neuen Quellen brauchen einen kostenlosen, aber PERSÖNLICHEN API-Key
(E-Mail-Registrierung), den ich nicht selbst anlegen kann/darf (Accounts
erstellen ist eine Nutzer-Aktion). Anders als bei FRED/SEC-EDGAR konnte die
tatsächliche DATEN-Struktur der Antworten deshalb noch NICHT live gegen
eine echte Antwort verifiziert werden - nur die Endpunkt-ROUTEN selbst
wurden live bestätigt (EIA: 403 `API_KEY_MISSING` statt 404, Finnhub: 401
"Please use an API key" statt 404, d.h. beide URLs/Parameter-Strukturen
existieren tatsächlich). Die konkreten Feld-/Series-Namen basieren auf der
offiziellen Dokumentation der beiden Anbieter, sind aber bis zur ersten
echten Antwort als "wahrscheinlich korrekt, noch nicht bestätigt"
einzustufen - explizit als TODO im jeweiligen Modul-Docstring vermerkt.
Key-Setup wie gewohnt: `.env.example` + leere Platzhalterzeile in der
echten `.env` vorbereitet (`EIA_API_KEY`/`FINNHUB_API_KEY`), Nutzer trägt
den Wert selbst ein (siehe Memory `feedback_key_setup_workflow`).

### EIA-Erdgas-Lagerbestand (nur Rohstoff-Pipeline, nur OD7L)

Schließt die im Rohstoff-Disclaimer bereits dokumentierte Lücke ("EIA-
Erdgas-Speicher NOCH NICHT einbezogen", siehe Nachtrag "Rohstoff-Pipeline
Phase 2"). Neue `api/eia.py::get_natural_gas_storage_history()` (Weekly
Natural Gas Storage Report, Lower 48, Series-ID `NW2_EPG0_SWO_R48_BCF` -
siehe Vorbehalt oben) liefert die letzten 8 Wochenwerte inkl. Woche-zu-
Woche-Änderung (Build/Draw). Bewusst KEIN 5-Jahres-Saisonvergleich in
dieser Runde (würde eine laengere historische Datenbasis + eigene
Berechnungslogik brauchen) - stattdessen wird dem Modell der 8-Wochen-
Verlauf mitgegeben und in der neuen Regel 21 (`agent/rohstoff/analyst.py`)
explizit angewiesen, den Verlaufstrend statt eines Einzelwerts zu nutzen
und die fehlende Saisonalitäts-Einordnung als Einschränkung zu
berücksichtigen. `agent/rohstoff/pipeline.py::_fetch_lagerbestaende()` nur
für `asset.symbol == "OD7L"` aktiv (kein Erdgas-Äquivalent für Gold/
Silber/Kupfer), Disclaimer-Text in `build_facts()` entsprechend
aktualisiert.

### Finnhub-Analysten-Trend (nur Aktien-Pipeline)

Bewusst NUR `recommendation-trends` umgesetzt, NICHT der ebenfalls
empfohlene Earnings-Kalender - wäre redundant mit dem bereits vorhandenen
`fundamentaldaten.naechstes_earnings_datum` (aus yfinance); zwei
potenziell abweichende Terminquellen im selben Prompt wären mehr
Verwirrung als Mehrwert (P-10). Neue `api/finnhub.py::
get_recommendation_trends()`/`summarize_recommendation_trend()` liefert
die Analysten-Empfehlungsverteilung (strong_buy/buy/hold/sell/strong_sell)
des aktuellsten UND des Vormonats - ergänzt den bereits vorhandenen
`fundamentaldaten.analysten_konsens` (reiner Momentanwert aus yfinance) um
eine RICHTUNGSKOMPONENTE ("wird der Konsens optimistischer oder
pessimistischer?"). Neue Regel 23 in `agent/aktien/analyst.py` (niedrig
gewichtet, analog zu den bestehenden Analysten-Fakten).

**Umgesetzt:** `api/eia.py`, `api/finnhub.py` (neu). `agent/rohstoff/
pipeline.py`/`agent/rohstoff/analyst.py` (Lagerbestände, Regel 21).
`agent/aktien/pipeline.py`/`agent/aktien/analyst.py` (Analysten-Trend,
Regel 23). `.env.example` + `.env`: zwei neue Platzhalter mit
Registrierungs-Anleitung. `remote/server.py::API_HEALTH_GROUPS` um `eia`/
`finnhub` ergänzt.

**Verifiziert:** 14 synthetische Tests (EIA-Wochenwerte-Parsing inkl.
Delta-Berechnung, Rohstoff-Symbol-Filter, Finnhub-Trend-Sortierung +
Zusammenfassung inkl. Ein-Monats-Edge-Case, JSON-Serialisierbarkeit).
Modul-Imports fehlerfrei. Endpunkt-Routen live gegen die echten Server
bestätigt (siehe Vorbehalt oben).

## Nachtrag (2026-07-19, gleicher Tag, Folge): EIA + Finnhub live mit echten Nutzer-Keys verifiziert

Nutzer hat beide kostenlosen Keys angelegt und in `.env` eingetragen. Damit
konnte die zuvor offene Lücke geschlossen werden - nicht mehr nur die
Endpunkt-Route, sondern die tatsächliche Datenform der Antworten.

**EIA:** `get_natural_gas_storage_history()` liefert 8 echte Wochenwerte
(2026-05-22 bis 2026-07-10), Lower-48-Bestand steigt saisonal korrekt von
2.483 auf 3.024 Bcf (Build in jeder Woche, konsistent mit der
US-Sommer-Füllsaison). Series-ID, Feldnamen und Delta-Berechnung bestätigt
korrekt - kein Ratefehler in der ursprünglichen Implementierung.
`agent/rohstoff/pipeline.py::_fetch_lagerbestaende("OD7L", ...)` direkt
gegen die echte API getestet, liefert das erwartete Fakten-Dict inkl.
8-Wochen-Verlauf; für andere Rohstoff-Symbole weiterhin korrekt `None`.

**Finnhub:** `get_recommendation_trends()` liefert für VST und PLTR je 4
Monatswerte mit den erwarteten Feldern (period/strongBuy/buy/hold/sell/
strongSell). Konsens plausibel unterschiedlich zwischen beiden Aktien (VST
fast ausschließlich Buy/Strong-Buy, PLTR mit spürbarem Hold-Anteil) -
Datenform bestätigt korrekt, `summarize_recommendation_trend()` bildet die
Monat-zu-Monat-Richtungskomponente wie vorgesehen.

**Rechtliche Einordnung (auf Nutzerfrage hin geprüft):** EIA-Daten sind
U.S.-Government-Public-Domain (eia.gov/about/copyrights_reuse.php) - jede
Nutzung erlaubt, keine Einschränkung, Attribution nur optional empfohlen.
Finnhubs Free-Tier ist vertraglich klar auf "Non-Professional/persönliche,
nicht-kommerzielle Nutzung" beschränkt (finnhub.io/terms-of-service) und
verbietet Weitergabe der Daten/Ergebnisse an Dritte - beides passt exakt
zum tatsächlichen Nutzungsmuster von TradingInfoTool (privates
Single-User-Tool, Daten fließen nur in lokale LLM-Prompts, keine
Weiterverteilung). Bei der Finnhub-Registrierung ist die Kontoart aktiv als
"Non-Professional/Personal" zu wählen - keine reine Formsache, sondern
deckt sich inhaltlich mit der echten Nutzung.

Modul-Docstrings in `api/eia.py`/`api/finnhub.py` von "wahrscheinlich
korrekt, noch nicht bestätigt" auf "live verifiziert" aktualisiert. Damit
sind alle vier vom Nutzer gewählten neuen Datenquellen (FRED, SEC-EDGAR,
EIA, Finnhub) vollständig umgesetzt UND live verifiziert - nur FINRA Equity
Short Interest bleibt als letzter, noch nicht angegangener Kandidat aus der
ursprünglichen Auswahl offen.

## Nachtrag (2026-07-19, gleicher Tag, Folge 2): FINRA Equity Short Interest (Aktien-Pipeline)

**Auslöser:** Nutzer bat "jetzt FINRA Short Interest angehen" - der letzte
der vier ursprünglich gewählten Datenquellen-Kandidaten.

**Wichtiger Fund:** anders als EIA/Finnhub braucht FINRAs Consolidated-
Short-Interest-Endpunkt (`api.finra.org/data/group/otcMarket/name/
ConsolidatedShortInterest`) KEINEN API-Key - live bestätigt oeffentlich
zugänglich (dieselbe Backend-API, die FINRAs eigene Daten-Browse-
Oberfläche nutzt). Für VST/PLTR (beide NYSE) echte, plausible Historie
zurückbekommen (VST: 205 Datenpunkte seit 2017, PLTR: 138 seit 2019).
Ein Sortierversuch über den Partition-Key `settlementDate` scheitert ohne
zusätzlichen Datums-Filter (API-Einschränkung) - stattdessen wird die
komplette Historie mit einem großzügigen `limit` geholt und clientseitig
sortiert/zugeschnitten. Bei unbekanntem Symbol liefert die API HTTP 204
mit leerem Body (kein valides JSON) statt einer leeren Liste - live mit
einem Fantasiesymbol bestätigt, expliziter Check in
`get_short_interest_history()`.

**Umgesetzt:** neue `api/finra.py` - `get_short_interest_history(symbol,
n_periods=6)` (letzte 6 zweiwöchentliche Meldeperioden, aufsteigend),
`summarize_short_interest()` (aktuelle vs. vorherige Periode, analog zum
Finnhub-Muster). Nur Aktien-Pipeline (`agent/aktien/pipeline.py`,
`asset.yfinance_symbol` wie bei SEC-EDGAR/Finnhub), neue Regel 24 in
`agent/aktien/analyst.py`: niedrig gewichteter Zusatzkontext, explizit
AMBIVALENT markiert (steigende Short-Position + hohes `days_to_cover`
kann sowohl anhaltenden Abwärtsdruck als auch ein Short-Squeeze-Setup
bedeuten, je nach technischem Kontext) - Erwähnung nur bei auffälligem
`days_to_cover` (>3-4 Tage) oder starker Periodenänderung (>15-20%).
Meldelag (1-3 Wochen, zweiwöchentliche FINRA-Meldung) explizit als "kein
Echtzeit-Signal" vermerkt. `remote/server.py::API_HEALTH_GROUPS` um
`finra` ergänzt. Kein `.env`-Eintrag nötig (kein Key).

**Verifiziert:** synthetische Tests für `summarize_short_interest()`
(leer/1-Eintrag/2-Eintraege), Pipeline-Block-Simulation mit echtem
API-Aufruf für VST (JSON-serialisierbar), Live-Test für VST/PLTR (echte
Werte, z. B. VST 2026-06-30: 15.917.274 Short-Aktien, 3,45 Tage
Eindeckungsdauer, +3,61% ggü. Vorperiode) sowie für ein Fantasiesymbol
(leere Liste, kein Crash trotz HTTP-204-Sonderfall). `build_facts()`-
Signatur-Check bestätigt korrekte Parameter-Durchreichung. Damit sind
JETZT ALLE FÜNF ursprünglich recherchierten Datenquellen-Kandidaten
(FRED, SEC-EDGAR, EIA, Finnhub, FINRA) vollständig umgesetzt und live
verifiziert - keine offenen Kandidaten aus dieser Recherche-Runde mehr.

## Nachtrag (2026-07-19, gleicher Tag, Folge 3): Aktien/ETF-Screener + Bitpanda-Sonderthema

**Auslöser:** Nutzer fragte nach dem Stand von "Marktscan-analogen" Mechanismen
für Aktien/Rohstoffe/ETF. Antwort: es gab bisher KEINE automatische Neu-
Kandidaten-Entdeckung für diese drei Klassen (nur die 11 manuell in
`config.yaml` gepflegten Symbole werden per `agent/multi_asset_batch.py`
regelmäßig neu bewertet, siehe Cooldown-Werte 24h/72h dort) - die
Bewertung bestehender Positionen lief also schon automatisch, nur die
Kandidaten-Suche fehlte. Nutzer bat: "bau einen einfachen Aktien/ETF-
Screener über eine kostenlose Quelle und berücksichtige auch hier das
Sonderthema - was ist bei Bitpanda davon gelistet und was nicht."

**Wichtiger Fund VOR der Implementierung (direkt relevant für die Bitpanda-
Frage):** ein Live-Check aller 9 aktuell gehaltenen Rohstoff-/Themen-ETF-
Positionen (OD7N/OD7H/OD7C/OD7L/VVMX/X136/EXH3/CEBS/ISOC) gegen
`api.bitpanda.is_listed()` ergab: KEINE davon ist bei Bitpanda gelistet -
nur die beiden Aktien (VST/PLTR) sind es. Bitpanda führt zwar eigene ETF/
ETC-"Themenkörbe" (z.B. "COPPERMINE", "NATGAS", 209 Einträge insgesamt),
das sind aber ANDERE, Bitpanda-eigene Produkte - keine echten UCITS-ETFs/
WisdomTree-ETCs wie in der Watchlist. Der Nutzer hält diese 9 Positionen
also nachweislich über einen anderen Broker (die Bestände selbst sind
über den bestehenden Excel-Import erfasst, nicht über Live-Bitpanda-Sync).
Diese Erkenntnis hat die Architektur direkt geprägt (siehe unten).

**Datenquelle (kostenlos, kein neuer API-Key):** `yfinance` (bereits im
Projekt für OHLC/Fundamentaldaten genutzt) Version 1.5.1 hat ein
eingebautes `yf.screen()`-Feature (Yahoo-Finance-Screener-Backend, live
verifiziert: `most_actives`/`day_gainers`/`growth_technology_stocks`/
`undervalued_growth_stocks`/`small_cap_gainers` liefern je 30-325 Treffer
mit >90 Feldern pro Symbol).

**Bewusst ASYMMETRISCHE Architektur** (`agent/aktien/screener.py`, neu),
direkt begründet durch den Bitpanda-Fund oben:
- **Aktien:** `scan_aktien_candidates()` durchsucht 3 Yahoo-Finance-Screens
  (Momentum + Growth + Value gemischt), filtert Mikro-Caps (<500 Mio. $
  Marktkap.) und Illiquides (<500k Tagesvolumen) heraus, dedupliziert,
  schließt bereits gelistete Watchlist-Symbole aus und markiert pro
  Kandidat `bitpanda_gelistet` via `is_listed()`.
- **ETF/ETC:** `scan_etf_candidates()` enumeriert NICHT über yfinance,
  sondern DIREKT Bitpandas eigenen ETF/ETC-Katalog (`get_listed_non_crypto_
  assets()`, Gruppen `etf`+`etc`) - das IST das bei Bitpanda tatsächlich
  kaufbare Angebot, während eine echte UCITS-ETF-Discovery über yfinance
  an Bitpandas Sortiment vorbeigegangen wäre (siehe Fund oben). Kein
  `yfinance_symbol` ableitbar (Bitpandas Symbole wie "COPPERMINE" sind
  eigene Produktnamen, keine Börsenticker) - degradiert sauber auf "keine
  technische Historie" (bereits bestehender Fix, Ticket #319).

**Bewusst EINFACH gehalten** (Nutzer-Wunsch): kein vierstufiges Scoring wie
beim Krypto-Marktscan (`agent/krypto/marktscan.py`), keine DB-Persistenz,
kein automatischer LLM-Call - ein manueller "Jetzt scannen"-Klick liefert
eine frische Kandidatenliste, "In Watchlist übernehmen" nutzt exakt
dasselbe bereits etablierte Muster wie Marktscan (`config.py::
add_watchlist_entry()`, Backup + Validierung + Rollback). Die eigentliche
Bewertung übernommener Kandidaten läuft danach ganz regulär über den
bereits bestehenden `multi_asset_batch_job` - kein Doppelbau.

**Umgesetzt:** `agent/aktien/screener.py` (neu, `ScreenerCandidate`-
Dataclass, `scan_aktien_candidates()`, `scan_etf_candidates()`), `ui/
screener_view.py` (neu, Treeview + Scan-Button + Übernehmen-Button, Muster
identisch zu `ui/marktscan_view.py`, aber ohne Score-Spalte/Detail-Panel).
`ui/app.py`: neuer Tab "Screener" zwischen Marktscan und Hebel.

**Verifiziert:** synthetische Tests (`_bereits_in_watchlist()` Groß-/
Kleinschreibung), echter Live-Lauf gegen beide Quellen (144 Aktien-
Kandidaten aus 3 Screens, 209 ETF/ETC-Kandidaten aus Bitpandas Katalog,
u.a. NVDA/TSM/AVGO mit korrektem Bitpanda-Listing-Flag), Tk-Smoke-Test
der `ScreenerView` isoliert UND als Teil der vollständigen `App`
(gegen eine Kopie der Produktions-DB, alle 7 Tabs inkl. "Screener"
korrekt registriert). `config.add_watchlist_entry()` selbst wurde NICHT
erneut gegen die echte `config.yaml` getestet (bereits durch die
bestehende Marktscan-Nutzung etabliert/verifiziert, Signatur-Kompatibilität
per Code-Review bestätigt) - kein ungewolltes Schreiben in die reale Datei
während der Verifikation.

## Nachtrag (2026-07-19, gleicher Tag, Folge 4): Schwerpunkt-Feld + Diversifikations-Übersicht

**Auslöser:** Nutzer bat um eine "konkrete Einordnung der Assets - z.B.
Inhalt und Zweck damit wir dies z.B. bei der Diversifikation - Gold,
Silber, Kupfer, seltene Erden, Güter, Energie korrekt einordnen können"
und wollte diese Schwerpunkte selbst in der Oberfläche pflegen können.

**Umgesetzt:** neues, optionales Freitext-Feld `schwerpunkt` auf
`WatchlistAsset` (`config.py`) - bewusst freier Text statt fester
Enum-Liste, da die sinnvollen Kategorien vom konkreten Portfolio abhängen
und nicht im Code vorgegeben werden sollen. Neue Funktion
`update_watchlist_schwerpunkt()` (gleiches Backup+Validierung+Rollback-
Muster wie `update_watchlist_coingecko_id()`), ABER mit einer bewussten
Abweichung: Einfügeposition ist das ENDE des Eintrags-Blocks statt einer
festen Position - `schwerpunkt` ist das zuletzt hinzugekommene optionale
Feld und soll bestehende Einträge mit bereits vorhandenen optionalen
Feldern (coingecko_id/assetklasse/yfinance_symbol/ist_cash_aequivalent)
nicht durcheinanderbringen. `add_watchlist_entry()` um den Parameter
erweitert (Neuanlage).

**GUI:** `AssetAddDialog`/`AssetEditDialog` (`ui/app.py`) um ein
"Schwerpunkt"-Textfeld erweitert (analog zum bestehenden coingecko_id-
Muster im Edit-Dialog). Watchlist-Tab-Treeview um eine neue Spalte
"Schwerpunkt" ergänzt.

**Diversifikations-Übersicht (`ui/portfolio.py`):** neue kompakte Tabelle
unterhalb der Bestandsliste, gruppiert den aktuellen Portfoliowert (inkl.
gestakter Anteile) nach `schwerpunkt` und zeigt EUR-Wert + Anteil-%.
Assets ohne gesetzten Schwerpunkt fallen in einen Sammel-Eintrag "ohne
Schwerpunkt", Fiat-Cash in "Cash/Sonstiges" - die Prozentwerte summieren
sich dadurch sauber auf denselben `Gesamtwert:` wie in der bestehenden
Anzeige. Bewusst als Tabelle statt Pie-Chart (kein bestehendes
Chart-Vorbild für Verteilungsdarstellungen, `ui/charts.py` deckt nur
Kursverlaufs-Liniencharts eines einzelnen Assets ab).

**Direkt befüllt** für alle 13 bestehenden Nicht-Krypto-Watchlist-
Einträge (Aktien/Rohstoffe/Themen-ETF) über die neue Funktion gegen die
echte `config.yaml`: VST → Energieversorger, PLTR → Software/KI-
Datenanalyse, OD7N → Silber, OD7H → Gold, OD7C → Kupfer, OD7L → Erdgas/
Energie, VVMX → Seltene Erden & strategische Metalle, X136 → Bioenergie,
EXH3 → Nahrungsmittel & Getränke, CEBS → Kupferminen (Aktien), ISOC →
Agrarwirtschaft, DBPK/3QSS → Absicherung (S&P 500/Nasdaq 100 Short).
Krypto-Einträge bewusst NICHT befüllt (außerhalb des ursprünglichen
Anfrage-Kontexts, kann der Nutzer bei Bedarf selbst über die GUI
nachtragen).

**Verifiziert:** synthetische Tests für `update_watchlist_schwerpunkt()`
(neue Zeile einfügen/bestehende Zeile ändern/unveränderter Wert -> kein
Schreibvorgang/unbekanntes Symbol) - dabei ZUERST versehentlich gegen die
echte `config.yaml` statt einer Kopie gelaufen (Testskript-Fehler, keine
Datenverlust, siehe git diff danach leer), sofort per Backup-Restore
korrigiert, danach sauber gegen eine echte Kopie wiederholt. Tk-Smoke-Test
`PortfolioView` gegen eine Kopie der Produktions-DB (Diversifikations-
Tabelle vor UND nach dem Befüllen der 13 Schwerpunkte geprüft - 13
korrekte Kategorien + "ohne Schwerpunkt"/"Cash/Sonstiges"-Sammeltöpfe),
voller `TradingInfoToolApp`-Smoke-Test (Watchlist-Tab zeigt die neue
Spalte korrekt), `AssetEditDialog`/`AssetAddDialog`-Instanziierungstest.
`git diff Basisinfos/config.yaml` vor dem Commit geprüft - ausschließlich
13 neue `schwerpunkt:`-Zeilen, keine sonstigen Änderungen.

## Nachtrag (2026-07-19, gleicher Tag, Folge 5): Kategorie-Taxonomie ERSETZT das Freitext-Schwerpunkt-Feld (Release 1)

**Auslöser - Nutzer-Korrektur:** der Freitext-`schwerpunkt` aus Folge 4 war
ein Missverständnis. Nutzer-Originalzitat: *"du hast mich falsch verstanden
- nicht ich will etwas manuell befüllen sondern schritt für schritt -
unabhängig von Krypto - 1. brauche eine Grundmenge an existierenden
Hauptgruppen - z.B. ETF Gruppen - dann unterkategorien z.B. Energie, KI,
Software etc, aus denen kann ich dann für den Marktscan und die
Diversifikation Schwerpunkte selbst gestalten u.U. gestützt durch
Vorschläge der KI [...] Das kann über einen Bereich komfortabel über die
GUI und automatischen Prozessen gesteuert werden."* Kernpunkt: Freitext
kann von automatischen Prozessen (Marktscan-Bias, KI-Vorschläge,
Gruppierung) strukturell nicht zuverlässig ausgewertet werden - es braucht
einen kontrollierten Vokabular-Baum. Auf Nachfrage (AskUserQuestion)
präzisierte der Nutzer zwei weitere Anforderungen: (a) wo verfügbar,
Detailinformationen zur Asset-Zusammensetzung zeigen (z.B. "wie setzt sich
ein ETF zusammen"), (b) bei mehreren ähnlichen Bitpanda-Produkten die
"Besseren" filtern helfen - explizite Motivation: *"damit die Investition
besser funktioniert und wir nicht wieder Produkte im Portfolio haben welche
gleich wieder delisted werden oder sind."* Auf die Frage nach der
Taxonomie-Quelle entschied der Nutzer: *"Erst Bitpanda-Katalog systematisch
auswerten"* statt einer vom Assistenten vorgeschlagenen Liste.

**Umfang dieser Runde (Release 1):** die Taxonomie-Infrastruktur komplett
(Kategorien-Datei, Datenmodell, GUI-Migration, Bestandsmigration,
Kompositions-/Qualitätsmodul, Screener-Integration, Diversifikations-
Umbau). Die aktive Schwerpunkt-Steuerung selbst (Prioritäten setzen, KI-
Vorschläge, Marktscan-Bias) ist bewusst als "Release 2" zurückgestellt -
noch nicht umgesetzt, siehe Ausblick am Ende dieses Nachtrags.

### Zwei echte Bitpanda-API-Bugs gefunden und behoben (betrifft die GESAMTE App, nicht nur dieses Feature)

Bei der Herleitung der Taxonomie aus dem echten `/v3/assets`-Katalog
(`api/bitpanda.py::_fetch_all_bitpanda_assets()`) fiel auf, dass
wiederholte Aufrufe im selben Moment gegen denselben Datensatz
unterschiedliche Ergebnisanzahlen lieferten (209/187/228/213 ETF/ETC/
Metal-Einträge beobachtet) - das betraf JEDEN bisherigen Aufrufer der
Funktion (Bitpanda-Listing-Prüfung in allen Signal-Pipelines, Screener,
Watchlist-Konsistenzprüfung), nicht nur die neue Taxonomie-Arbeit.

- **Bugfix 1 (Duplikate über Seitengrenzen):** derselbe Symbol-Eintrag
  tauchte teils auf mehreren Paginierungsseiten gleichzeitig auf (bis zu 53
  Duplikate bei `total_count=3238` gemessen). Erster Fix: Deduplizierung
  per Symbol beim Sammeln - reichte allein NICHT aus (siehe Bugfix 2/3).
- **Bugfix 2 (verworfen, aber dokumentiert):** die Vermutung, das
  ursprüngliche Abbruchkriterium `page_number * page_size >= total_count`
  sei die Ursache (da `total_count` selbst instabil ist), führte zu einem
  Ersatz-Abbruchkriterium `len(page_data) < page_size`. Live-Test zeigte:
  das machte es NICHT robuster, sondern schlimmer (163/173/211 Einträge
  über 6 Wiederholungen, teils fehlte real ZINC/SXR8/WTI komplett) - auch
  NICHT-letzte Seiten kamen serverseitig manchmal unvollständig zurück.
- **Bugfix 3 (tatsächliche Lösung):** das Problem war die MEHRSEITIGE
  Paginierung selbst - der Datensatz verschiebt sich offenbar leicht
  zwischen einzelnen Roundtrips (Ursache serverseitig unbekannt). Live
  bestätigt: ein EINZELNER Request mit `page_size=10000` (deutlich über dem
  aktuellen `total_count=3238`) liefert den kompletten Datensatz in einer
  Antwort - 6/6 Wiederholungen exakt stabil (3238 Einträge, 3185 eindeutige
  Symbole, alle 211 realen ETF/ETC/Metal-Symbole). Die Dedup-Notwendigkeit
  aus Bugfix 1 bleibt (der Datensatz selbst enthält echte Symbol-Kollisionen,
  ca. 53 Stück, keine Paginierungs-Artefakte) - die `while`-Schleife bleibt
  nur noch als Sicherheitsnetz für ein zukünftiges Wachstum über 10.000
  Einträge hinaus im Code, wird im Normalfall aber nie ein zweites Mal
  durchlaufen. **Lektion:** bei unzuverlässigen Paginierungs-APIs mit
  überschaubarer Gesamtgröße ist "alles in einer Anfrage mit großzügigem
  `page_size`" robuster als Mehrseiten-Konsistenz-Reparaturen.

### `Basisinfos/kategorien.yaml` (neu)

10 Hauptgruppen, 72 Unterkategorien, systematisch aus dem (nach obigen
Bugfixes) stabilen Bitpanda-ETF/ETC/Edelmetall-Katalog hergeleitet:
Edelmetalle (Gold/Silber/Platin&Palladium/Diversifiziert), Industriemetalle,
Energie, Agrarrohstoffe & Nahrungsmittel, Technologie & KI, Absicherung,
Aktien - Regionen & Länder, Aktien - Sektoren, Anleihen & Geldmarkt,
Sonstige. Jede Unterkategorie trägt eine `bitpanda_symbole`-Liste zur
automatischen Vor-Klassifikation neuer Kandidaten. Vollständigkeits-Check
bestätigt: alle 211 realen Symbole sind genau einer Unterkategorie
zugeordnet, keine Waisen, keine erfundenen Symbole (per Live-Test gegen den
echten, jetzt stabilen Katalog reproduzierbar). Eigene Watchlist-Assets
(auch nicht bei Bitpanda gelistete) speichern ihre Hauptgruppe/
Unterkategorie direkt am Asset, unabhängig von dieser Datei - die Datei ist
nur die Vorschlagsquelle für neue Kandidaten.

### `config.py`: strukturelle Migration

`WatchlistAsset.schwerpunkt` (Freitext, Folge 4) ersetzt durch
`hauptgruppe`/`unterkategorie` (beide `str | None`, IDs aus
`kategorien.yaml`). Neue Lookup-Funktionen: `get_kategorien()` (gecached),
`find_kategorie_fuer_bitpanda_symbol()`, `get_hauptgruppe_name()`,
`get_kategorie_name()`. `update_watchlist_kategorie(symbol, hauptgruppe,
unterkategorie)` ersetzt `update_watchlist_schwerpunkt()` - schreibt beide
Felder ATOMAR (beide oder keins), validiert beide IDs gegen
`kategorien.yaml` VOR jedem Schreibvorgang (Fail-Fast, nie ein ungültiger
Halbzustand in `config.yaml`). Alle 13 bestehenden Nicht-Krypto-Assets
wurden auf die neue Struktur migriert, die alten `schwerpunkt:`-Zeilen
entfernt (`git diff` bestätigt: nur die erwarteten Zeilenänderungen).

### GUI-Migration (`ui/app.py`)

Freitext-Feld in `AssetAddDialog`/`AssetEditDialog` ersetzt durch
kaskadierende Hauptgruppe→Unterkategorie-Comboboxen
(`_build_kategorie_selector()`). Watchlist-Tab-Spalte zeigt jetzt
`config.get_kategorie_name(...)`. Diversifikations-Tabelle
(`ui/portfolio.py`) gruppiert entsprechend nach Hauptgruppe um (Fix eines
dabei live gefundenen `AttributeError` durch die Feldumbenennung).

### Asset-Qualitäts-/Kompositionsmodul (`api/asset_quality.py`, neu) - "wie setzt sich zusammen"

`get_asset_quality(yfinance_symbol)` liefert über `yfinance`s
`Ticker.info`/`Ticker.funds_data` Top-10-Holdings, Sektorgewichtung, AUM
(`totalAssets`) und Kostenquote (`netExpenseRatio`) für Assets mit echtem
Börsenticker - live verifiziert (VVMX.DE/EXH3.DE/VST/PLTR). Neuer
Watchlist-Toolbar-Button "Zusammensetzung anzeigen…" öffnet
`AssetQualityDialog`. **Bewusste, dokumentierte Grenze (P-10):** Bitpandas
EIGENE synthetische ETF/ETC-Themenkörbe (z.B. "COPPERMINE") haben KEINEN
echten Börsenticker und damit strukturell KEINE öffentliche AUM/
Kostenquote - für diese Kandidaten bleibt `get_asset_quality()` `None`, ein
"besseres Produkt"-Vergleich ist dort nicht möglich. Die AUM-basierte
Delisting-Risiko-Einschätzung (kleine Fonds werden häufiger geschlossen)
funktioniert NUR für echte Fonds mit Ticker.

### Screener-Integration (`agent/aktien/screener.py`, `ui/screener_view.py`)

`ScreenerCandidate` um `hauptgruppe`/`unterkategorie` erweitert.
`scan_etf_candidates()` taggt jeden Bitpanda-Katalog-Kandidaten automatisch
per `config.find_kategorie_fuer_bitpanda_symbol()` (204 von 204 aktuellen
Kandidaten live erfolgreich zugeordnet - alle 211 Katalog-Symbole sind ja
per Definition in der Taxonomie erfasst). Neue "Kategorie"-Spalte im
Screener-Tab. Bei "In Watchlist übernehmen" wird die erkannte Kategorie
gleich mit übernommen, damit der Nutzer sie nicht nochmal manuell setzen
muss. **Kein Qualitätsvergleich für diese Kandidaten** (siehe Grenze oben,
dokumentiert im Modul-Docstring mit Querverweis auf `asset_quality.py`) -
`scan_aktien_candidates()` (Einzelaktien) bewusst NICHT um Kategorie-Tagging
erweitert, da die Taxonomie nur ETF/ETC/Edelmetall-Gruppen abbildet, keine
Einzeltitel.

### Verifikation

Synthetisch: `kategorien.yaml`-Vollständigkeit (211=211, 0 Waisen, 0
erfunden) über 10 Wiederholungen NACH Bugfix 3 stabil (VORHER, mit den
verworfenen Fixes, war das nicht der Fall - siehe Bugfix-Historie oben).
Echt: `_fetch_all_bitpanda_assets()`/`get_listed_assets()`/
`get_listed_non_crypto_assets()` je 5-10x wiederholt gegen die echte API,
alle stabil (822 Krypto/2363 Nicht-Krypto/3185 eindeutige Symbole gesamt).
`get_asset_quality()` live gegen mehrere echte Ticker + einen erfundenen
Ticker (korrektes `None`). Voller `TradingInfoToolApp`-Smoke-Test:
`PortfolioView.refresh()`, `ScreenerView`-Aufbau, `AssetAddDialog`/
`AssetEditDialog`-Instanziierung mit echten Produktionsdaten - keine
Exceptions. `git status`/`git diff` vor dem Commit geprüft.

### Ausblick: Release 2 (noch NICHT umgesetzt, separate Runde)

Schwerpunkte/Thesen-Verwaltung (GUI zum Setzen von Prioritäten/
Zielgewichtungen pro Kategorie mit Begründung+Datum), ein periodischer
KI-Vorschläge-Job (Muster wie `makro_analog.py`, schlägt Kategorie-
Schwerpunkte basierend auf bestehenden Makro-Fakten vor, Nutzer
akzeptiert/verwirft), sowie Marktscan-/Screener-Bias (Kandidaten aus
priorisierten Kategorien höher gewichten) - alle drei bewusst
zurückgestellt, bis die Taxonomie-Infrastruktur (dieser Nachtrag) im
laufenden Betrieb bestätigt ist.

## Nachtrag (2026-07-19, gleicher Tag, Folge 6): Release 2 (Schwerpunkte/Thesen-Verwaltung) - Konzeptionsrunde

**Status dieses Nachtrags:** reine Konzeption/Entscheidungsfindung, kein
Code zum Zeitpunkt dieses Eintrags. Vollständige Ausarbeitung liegt in
`Basisinfos/Kategorie_Basisinformationen_Release2.md`/`.docx` - dieser
Eintrag hält nur die wichtigsten Entscheidungen und Funde fest, damit sie
auch ohne die separate Datei nachvollziehbar bleiben. **Umsetzung folgte
noch am selben Tag, siehe Nachtrag Folge 7 weiter unten** - die
Konzeptionsrunde und die Implementierungsrunde fielen beide auf den
2026-07-19/2026-07-20-Übergang.

**Datenmodell einer "These":** `hauptgruppe`/`unterkategorie` (beide Ebenen
erlaubt, GUI zeigt bei Hauptgruppen-These transparent die darunter
konsolidierten Unterkategorien), `richtung` (Übergewichten/Neutral/Meiden),
`staerke`, `begruendung` (Freitext), `pruef_mechanismus` (strukturiert,
siehe unten), `gesetzt_am`, `review_am`, `status`, `quelle`
(manuell/KI-Vorschlag). Neue DB-Tabelle, nicht `config.yaml`.

**#334 (Marktscan-/Screener-Bias) zweistufig entschieden - wichtigster
Punkt dieser Runde:**
- Stufe 1 (Teil der ersten Umsetzungsrunde): NUR Hervorhebung/Sortierung,
  KEINE Scoring-Gewichtung. Grund: eine aktive These spiegelt die
  subjektive, aktuelle Einschätzung des Nutzers - würde sie das Scoring
  gewichten, entstünde bei trendgetriebenen Themen (Beispiel Technologie &
  KI) eine prozyklische Verstärkung ("KI ist im Trend" → System zeigt mehr
  KI-Aktien → verstärkt die Wahrnehmung, obwohl das Thema evtl. bereits
  überhitzt ist) - direkter Widerspruch zur bestehenden antizyklischen
  Risikogate-Philosophie im Projekt (Retail-Konsens-Deckel, siehe Nachtrag
  vom 2026-07-19 weiter oben).
- Zusatz, Teil der ersten Runde: neuer Fakt `these_abgleich` je Signal -
  prüft die These NICHT gegen ihre eigene Beliebtheit, sondern gegen
  unabhängige, bereits im Projekt vorhandene objektive Daten (M2-/
  Liquiditätsregime für Edelmetalle, CFTC-COT-Positionierung für
  Industriemetalle/Energie, Zinskurve für Finanzsektor-Aktien,
  Dollar-Index für Emerging Markets). Kann eine hypebasierte These sogar
  als "objektiv nicht gestützt" kennzeichnen - das eingebaute Gegenmittel
  zum Bubble-/Trend-Chasing-Risiko.
- Stufe 2 (später, vorsichtig): echte Scoring-Gewichtung nur für
  strukturelle/langsame Kategorien (Edelmetalle, Industriemetalle, Energie,
  Anleihen), nie für Technologie & KI.

**Acht Kandidaten-Thesen mit Mechanik durchgearbeitet** (Energie,
Edelmetalle, Industriemetalle/Kupfer, Erneuerbare & Clean Energy, Anleihen/
TIPS, Aktien-Sektoren/Finanzen, Aktien-Regionen/Emerging Markets,
Absicherung) - für jede die zugrundeliegende ökonomische Mechanik ("wann
funktioniert das grundsätzlich") plus echter Live-Datenabgleich (yfinance,
CFTC COT, FRED M2/Fed Funds, EIA), nicht nur Trainingswissen. Bewusst als
Mechanik-Erklärung + aktuelle Datenlage kommuniziert, NICHT als
Kaufempfehlung (siehe Modul-Docstring-Stil im restlichen Projekt).

**Echter Fund dabei (Dollar-Index-Trend):** für die Emerging-Markets-These
zeigte eine Momentaufnahme des Dollar-Index (100,69) zunächst nichts
Eindeutiges - erst der 12-Monats-Verlauf (yfinance, monatliche Kerzen)
zeigte einen klaren Aufwärtstrend seit Jahresbeginn 2026 (96,99 im Januar
auf Höchststand 101,19 im Juni) - das ist ein Gegenwind für eine
EM-Übergewichtungs-These, kein Rückenwind, obwohl die Fed erkennbar lockert.
Lektion: ein einzelner aktueller Wert reicht bei makroökonomischen
Indikatoren oft nicht, der Trend über mehrere Monate ist aussagekräftiger.

**Lücken-Prüfung (auf Nutzer-Wunsch, sieben Funde, Details in der
Basisinformationen-Datei):**
1. CFTC-COT deckt kein Rohöl ab (`COT_MARKET_NAMES` in `api/cftc_cot.py`
   hat nur Gold/Silber/Kupfer/Erdgas) - Energie-These fehlt damit die
   Positionierungs-Perspektive für WTI/Brent.
2. Dollar-Index und Zinskurve (10J vs. kurzfristig) sind NICHT als eigene,
   `@track_api_health`-überwachte Datenquellen im Projekt vorhanden - für
   heutige Zwecke ad-hoc direkt über yfinance abgefragt, für einen
   verlässlichen `these_abgleich`-Fakt müssten das richtige, abgesicherte
   Funktionen werden.
3. Absicherung/Hedge passt nicht sauber ins Standard-Datenmodell (Feld
   `richtung` ergibt bei einer Versicherungs-Logik wenig Sinn) - eigene
   GUI-Darstellung (Aktiv/Inaktiv) vermutlich nötig.
4. Krypto ist komplett außen vor (`kategorien.yaml` deckt bewusst keine
   Kryptowerte ab) - der `these_abgleich`-Fakt erscheint deshalb nie bei
   Krypto-Signalen, muss in GUI/Doku klar kommuniziert werden.
5. Kein automatisches Verhalten bei Ablauf von `review_am` definiert.
6. Keine Verbindung zur Diversifikations-Tabelle (Portfolio-Tab) vorgesehen.
7. Synergie mit dem Screener (`scan_etf_candidates()` taggt Kandidaten
   schon heute mit Hauptgruppe/Unterkategorie, Release 1) noch nicht
   genutzt - Kandidaten aus Kategorien mit aktiver, aber in der Watchlist
   noch nicht vertretener These könnten hervorgehoben werden.

**Weitere Entscheidungen:** Granularität beide Ebenen erlaubt; 3-6
gleichzeitig aktive Thesen als weiche Richtgröße, kein Hard-Limit;
KI-Vorschläge-Job (#333) täglich wie `makro_analog_job` (06:30 Uhr),
Rhythmus-Optimierung vorgemerkt für später.

**Nachtrag zum Nachtrag, gleicher Tag - drei weitere Punkte auf
Nutzer-Wunsch ergänzt:**
- **Haltedauer/Zeithorizont:** die Prüf-Mechanismen haben unterschiedliche
  natürliche Zeithorizonte (COT wöchentlich → kürzer, M2/Zinskurve/
  Dollar-Index-Trend brauchen Monate → länger) - der `review_am`-Vorschlag
  in der GUI orientiert sich daran (z. B. 4 Wochen bei COT-gestützten
  Thesen, 3 Monate bei M2-gestützten). Ein zusätzlicher Mismatch-Check
  zwischen dem Zeithorizont der These und der Haltedauer-Empfehlung des
  konkreten Signals (`holding_duration`/`halte_kriterium_bucket`) war hier
  angedacht, ist aber bei der Umsetzung (Folge 7) bewusst NICHT eingebaut
  worden: dieses Feld entsteht erst als LLM-OUTPUT, ein Vorab-Abgleich vor
  dem LLM-Aufruf ist strukturell nicht möglich - das wäre ein Post-Check
  nach der Antwort (analog `risk_gate.py::post_check()`), siehe
  `agent/kategorie_thesen.py::build_these_abgleich_fact()`-Docstring für den
  dokumentierten, offenen Nachrüstpunkt.
- **Gehaltene Assets erhalten Priorität:** innerhalb einer Kategorie mit
  aktiver These werden in der Stufe-1-Hervorhebung zuerst bereits gehaltene
  Assets (`wird_aktuell_gehalten`) angezeigt, dann neue Watchlist-/
  Screener-Kandidaten, dann alles Übrige - unterschiedliche Dringlichkeit
  (echte Entscheidung vs. "einen Blick wert").
- **Transparenz-Prinzip, ausdrücklicher Nutzer-Wunsch, gilt durchgängig:**
  jede automatische Wirkung einer These (Sortierung, Hervorhebung,
  Review-Datum-Vorschlag, `these_abgleich`-Text) muss ihre konkrete
  Begründung sichtbar mitliefern, minimaler Interpretationsaufwand für den
  Nutzer - keine stille Umsortierung, kein Badge ohne Klartext-Erklärung.

**Nächster Schritt:** die sieben Lücken-Punkte (plus die drei
Ergänzungen oben) sind kleinere Ausbau-Entscheidungen, kein Blocker für den
Start der Umsetzung von #332 - Implementierung kann beginnen, offene
Punkte während der Umsetzung nach und nach klären.

## Nachtrag (2026-07-20, Folge 7): Release 2 (Schwerpunkte/Thesen-Verwaltung) - Umsetzung #332/#343

Direkte Fortsetzung von Folge 6 (Nutzer-Anweisung "starten wir hier") - die
komplette Backend- + GUI-Infrastruktur für #332 sowie die Stufe-1-
Hervorhebung aus #343 wurden implementiert und verifiziert. #333
(KI-Vorschläge-Job) und die eigentliche Stufe 2 von #334 (Scoring-Gewichtung
für strukturelle Kategorien) sind bewusst NICHT Teil dieser Runde, siehe
Folge 6.

**Backend:**
- `database/models.py::These`-Dataclass + `database/db.py`: `thesen`-Tabelle
  (2 Indizes) + volles CRUD (`create_these`/`update_these`/
  `set_these_status`/`get_these`/`get_aktive_thesen`/`get_alle_thesen`/
  `get_aktive_these_fuer_kategorie()` - Unterkategorie-spezifische These hat
  Vorrang vor einer Hauptgruppen-weiten, identische Priorität überall wo
  Thesen nachgeschlagen werden).
- `config.py::PRUEF_MECHANISMUS_MAPPING`/`get_pruef_mechanismus()` - welcher
  objektive Check (m2_liquiditaet/cot_positionierung/zinskurve/dollar_index/
  baerenmarkt_overlay) für welche Hauptgruppe/Unterkategorie gilt, inkl.
  `review_tage_vorschlag` + `review_begruendung` fürs Transparenz-Prinzip.
- Lücke 1 (CFTC-COT ohne Rohöl) geschlossen: `api/cftc_cot.py::
  COT_MARKET_NAMES` um `rohoel_wti`/`rohoel_brent` erweitert (echte
  Marktnamen live über die CFTC-API mit `LIKE`-Filtern ermittelt, nicht
  geraten).
- Lücke 2 (Dollar-Index/Zinskurve ohne überwachte Datenquelle) geschlossen:
  `api/macro.py::get_zinskurve()`/`get_dollar_index_trend()`, beide
  `@track_api_health("yfinance")` (kein neuer API_HEALTH_GROUPS-Eintrag
  nötig, teilen sich den bestehenden yfinance-Block).
  `get_dollar_index_trend()` liefert IMMER den 12-Monats-Verlauf, nie nur
  eine Momentaufnahme (siehe der echte DXY-Fund in Folge 6).
- `agent/kategorie_thesen.py` (neu): `these_abgleich`-Berechnungsmodul.
  `compute_these_abgleich()` + 4 `_abgleich_*()`-Funktionen (M2/COT/
  Zinskurve/Dollar-Index) plus `_abgleich_baerenmarkt_overlay()`, die ehrlich
  `"nicht_pruefbar"` zurückgibt (P-10, Absicherung-Check bleibt bewusst
  Lücke 3/unimplementiert, siehe Folge 6). `build_these_abgleich_fact()` als
  gemeinsamer, in allen 4 Nicht-Krypto-Pipelines (Aktien/Rohstoffe/Hedge/
  Themen-ETF) wiederverwendeter Fact-Baustein (Muster wie
  `agent.krypto.wiederholungs_erkennung.build_wiederholung_fact()`) - je ein
  neuer SYSTEM_PROMPT-Regel-Eintrag in den 4 Analysten, der die KI anweist,
  den Abgleich zu kommentieren, aber NIE die Action über das hinaus zu
  schieben, was die übrigen Fakten hergeben (Stufe-1-Prinzip: Hervorhebung,
  kein Scoring-Einfluss).
- `index_aktive_thesen()`/`lookup_these()` (selbes Modul) - In-Memory-Index
  für wiederholte Lookups über viele Assets/Kandidaten (Watchlist-Tab,
  Screener), vermeidet einen SQL-Query pro Zeile, identische
  Prioritäts-Logik wie `get_aktive_these_fuer_kategorie()`.

**GUI Task #342 - neuer Tab "Schwerpunkte":** `ui/thesen_view.py` (neu).
Liste aller Thesen (Kategorie/Richtung/Stärke/Prüf-Mechanismus/Status/
Termine) + Add/Edit-Dialog. Eigener, lokaler Kategorie-Selector (nicht der
aus `ui.app` wiederverwendet - eine These kann sich auf eine GANZE
Hauptgruppe beziehen, zeigt dabei live alle darunter konsolidierten
Unterkategorien, Nutzer-Entscheidung #1 aus Folge 6). Absicherung-Sonderfall
sauber gelöst: Richtung-Feld zeigt bei `hauptgruppe=absicherung` automatisch
Aktiv/Inaktiv statt Übergewichten/Neutral/Meiden (schließt Lücke 3 aus
Folge 6 GUI-seitig). Transparenz-Prinzip live umgesetzt: der
`review_am`-Vorschlag erscheint direkt neben dem Feld mit konkretem Datum
UND Begründungstext (z. B. "Vorschlag: 2026-08-17 (heute + 28 Tage) -
CFTC-COT-Berichte erscheinen wöchentlich..."), nie eine stille Vorbelegung.
Statuswechsel (aktiv → erledigt/verworfen) über eigene Listen-Buttons, nicht
im Dialog (eine neue These startet immer aktiv/manuell).

**GUI Task #343 - Stufe-1-Hervorhebung, schließt Lücken 6+7 aus Folge 6:**
alle drei Stellen nutzen dieselben Marker (▲ Übergewichten/Aktiv, ▼ Meiden,
● Neutral/Inaktiv) mit denselben drei Farb-Tags (`these_positiv`/
`these_negativ`/`these_neutral`) und demselben Prinzip: sichtbarer Marker +
Zeilen-Tooltip mit der konkreten These-Begründung, NIE eine stille
Umsortierung (Transparenz-Prinzip).
- **Watchlist-Tab** (`ui/app.py`): Sortier-Priorität nur bei der initialen
  Einsortierung (Gruppe 0 = gehalten + aktive These, 1 = nicht gehalten +
  aktive These, 2 = Rest, jeweils alphabetisch), greift NICHT in eine
  manuelle Spaltensortierung ein (Nutzer-Entscheidung "gehaltene Assets
  sollten Priorität erhalten" aus Folge 6). Marker an die
  Schwerpunkt-Spalte angehängt, Zeilen-Tooltip erweitert (zeigt aktive
  These VOR dem letzten Signal, falls beides vorhanden).
- **Diversifikations-Tabelle** (`ui/portfolio.py`): Marker je
  Hauptgruppen-Zeile, wenn irgendeine aktive These (Hauptgruppen-weit ODER
  eine ihrer Unterkategorien) zutrifft - bei mehreren Treffern bestimmt die
  "stärkste" Richtung den Marker (Übergewichten/Aktiv vor Meiden vor
  Neutral), der Tooltip listet trotzdem ALLE Treffer einzeln auf. Bewusst
  KEIN Eingriff in die bestehende Wert-Sortierung (größte Position bleibt
  oben - das ist die eigentlich nützliche Ordnung für diese Tabelle), nur
  der Marker.
- **Screener-Tab** (`ui/screener_view.py`): Sortier-Priorität (Treffer vor
  Nicht-Treffer, sonst Scan-Reihenfolge unverändert) - ohne
  gehalten-Priorität, Screener-Kandidaten sind per Definition noch nicht in
  der Watchlist. Neu: `add_row_tooltips()` für diesen Tab (gab es vorher
  nicht).

**Verifikation:** drei synthetische Tk-Smoke-Test-Skripte gegen Kopien der
Produktions-DB (nie die echte DB) - `ThesenView` (Liste/Filter/Add-Dialog
inkl. Absicherung-Sonderfall/Edit-Dialog-Vorbelegung/Statuswechsel, alle
Assertions bestanden), Watchlist-Sortier-/Marker-Logik (isoliert
nachgebaut, exakt dieselbe `index_aktive_thesen()`/`lookup_these()`-Funktion
wie im echten Code), Portfolio-Diversifikation + Screener (beide mit echten
Tk-Widgets, `PortfolioView`/`ScreenerView` direkt instanziiert, Marker/Tags/
Tooltips/Sortierreihenfolge geprüft). Zusätzlich ein kombinierter
Import-Regressionstest über alle geänderten/neuen Module (`ui.app`,
`ui.portfolio`, `ui.screener_view`, `ui.thesen_view`, `agent.
kategorie_thesen`, alle 4 Nicht-Krypto-Pipelines, `main`) - keine Fehler.

**Verbleibend offen (bewusst nicht Teil dieser Runde):**
- #333: täglicher KI-Vorschläge-Job für neue Thesen-Kandidaten.
- #334, Stufe 2: echte Scoring-Gewichtung für strukturelle Kategorien
  (Edelmetalle, Industriemetalle, Energie, Anleihen) - erst nach einer
  Beobachtungsphase mit Stufe 1.
- Lücke 5 aus Folge 6: kein automatisches Verhalten, wenn `review_am` in der
  Vergangenheit liegt (weder Benachrichtigung noch visuelle Markierung) -
  bisher rein manuell im Schwerpunkte-Tab einsehbar.
- Der in Folge 6 angedachte Haltedauer-Mismatch-Check (These-Zeithorizont
  gegen die Haltedauer-Empfehlung eines konkreten Signals) bleibt aus dem
  oben genannten strukturellen Grund unimplementiert (`agent/
  kategorie_thesen.py::build_these_abgleich_fact()`-Docstring).
- Absicherung/Hedge-`these_abgleich` bleibt `"nicht_pruefbar"` (Lücke 3 aus
  Folge 6, Bärenmarkt-Overlay-Indikator ist noch keine eigenständig
  aufrufbare Funktion).

## Nachtrag (2026-07-20, Folge 8): Screener-Auto-Scan + Mouseover-Tooltips fuer Tabs/Aktionen

Nutzer-Feedback nach dem ersten Test der Folge-7-Neuerungen: der Screener-Tab
war leer, weil er ausschliesslich manuell scannt, und die neuen Elemente
(Schwerpunkte-Tab, Screener-Auto-Scan) hatten keine erklaerenden Tooltips.
Zwei kleine, in sich abgeschlossene Nachbesserungen.

**Screener-Auto-Scan** (Nutzer-Wunsch "Auto-Screen beim Start bzw.
regelmaessige Updates", Nutzer-Bestaetigung "60 Minuten passt"): bewusst ein
GUI-lokaler, selbstverlaengernder `self.after()`-Timer in
`ui/screener_view.py` (Muster wie `ui/app.py::_poll_prices()`), KEIN neuer
Scheduler-Job - der Screener persistiert bewusst nichts in die DB (siehe
Folge-Ur-Docstring "keine DB-Persistenz"), ein Scheduler-Job haette dafuer
eine neue Tabelle gebraucht, nur damit die GUI sie wieder ausliest. Erster
Scan kurz nach dem Tab-Aufbau, danach alle `Basisinfos/config.yaml::
screener.auto_scan_intervall_minuten` (Default 60) Minuten erneut - der
Folge-Timer wird IMMER ab dem letzten tatsaechlichen Scan neu geplant
(egal ob manuell oder automatisch ausgeloest), mit Schutz gegen doppelte
Timer-Ketten (`after_cancel()` vor jedem Neuplanen) und gegen
ueberlappende Scans (Guard: ein Aufruf waehrend `scan_button` disabled
ist, wird ignoriert). 60 Minuten bewusst zurueckhaltend gewaehlt: Yahoo-
Finance-`day_gainers` ist zwar echt intraday-dynamisch, aber Bitpandas
ETF/ETC-Katalog aendert sich kaum, und das Notebook hatte bereits einen
echten yfinance-Haenger (siehe Memory
`project_multi_asset_yfinance_symbols`).

**Mouseover-Tooltips fuer Tabs/Aktionen** (Nutzer-Wunsch: "fuer die
Primaerseiten - Tabs und Aktionen - eine konkrete Kurzbeschreibung bei
Mouseover was diese bewirken/nutzung und optional [...] was sie nicht
koennen"): neues Modul `ui/widget_tooltip.py` - Ergaenzung zu den
bestehenden `ui/heading_tooltip.py` (Treeview-Spaltenkoepfe) und
`ui/row_tooltip.py` (Treeview-Zeilen), die beide NICHT auf normale Widgets
oder Notebook-Tab-Kopfzeilen anwendbar sind. Zwei neue Funktionen:
`add_widget_tooltip(widget, text)` (statischer Tooltip fuer z.B. einen
Button) und `add_notebook_tab_tooltips(notebook, {index: text})` (ueber
`notebook.identify()`/`notebook.index("@x,y")`). Bewusst eingegrenzter
Scope fuer diese Runde: NUR die beiden Tabs, deren Verhalten sich neu
geaendert hat (Schwerpunkte: neuer Tab; Screener: neuer Auto-Scan) -
Tab-Kopf-Tooltip fuer beide (`ui/app.py`) + Aktions-Tooltip fuer jeden
Button/jede Checkbox im Schwerpunkte-Toolbar (`ui/thesen_view.py`) und im
Screener-Toolbar (`ui/screener_view.py`), jeweils inkl. explizitem Hinweis
auf fehlenden Automatismus wo relevant (z.B. "Uebernimmt NICHTS
automatisch in die Watchlist"). Die uebrigen, bereits laenger bestehenden
Tabs (Watchlist/Portfolio/Signale/Marktscan/Hebel/Regime) sind bewusst NICHT
Teil dieser Runde - koennten im selben Muster nachgeruestet werden, falls
gewuenscht.

**Lesbarkeits-Check der neuen Marker-Farben (▲/▼/●, `these_positiv`/
`these_negativ`/`these_neutral`):** WCAG-Kontrastverhaeltnis berechnet
gegen Standard- UND Zebra-Streifen-Hintergrund, beide Modi. Echter,
bereits VORHANDENER Befund (nicht durch diese Runde neu verursacht - die
drei Marker-Tags nutzen die laengst etablierten `theme.success_color()`/
`danger_color()`/`info_color()`, dieselben Farben wie z.B. `pl_positive`/
`pl_negative` im Portfolio-Tab): im Light Mode liegen alle drei knapp an
oder leicht unter der WCAG-AA-Schwelle (4,5:1) auf dem Zebra-Streifen
(4,26-4,82:1); im Dark Mode ist der Kontrast auf normalem Hintergrund gut
(5,2-6,0:1), faellt aber auf dem dunklen Zebra-Streifen (`#404040`) auf
3,2-3,7:1 - unter der AA-Schwelle fuer normalen Text. Da dies ein
projektweites, bereits lange bestehendes Theme-Farbthema betrifft (nicht
nur die neuen Marker) und eine Korrektur alle Stellen mit `pl_positive`/
`pl_negative`/`bitpanda_fehlt`/etc. gleichermassen beeinflussen wuerde,
wurde dem Nutzer der Befund zunaechst nur gemeldet statt am Theme-System
vorbeizukorrigieren.

**Nachtrag zum Nachtrag, gleicher Tag - Nutzer bestaetigte den Fix nach
einem echten Screenshot** (Screener-Tab, Dark Mode: die "AGRICULTURE"/
"SOFTS"-Zeilen kaum lesbar grau auf dunkelgrauem Zebra-Streifen): bewusst
NICHT die Text-Farben selbst geaendert (haette die etablierte Bedeutung
von success/danger/warn/swap/info ueberall im Projekt angefasst), sondern
NUR `theme.py::_LIGHT["zebra_odd"]`/`_DARK["zebra_odd"]` selbst justiert -
ein einziger, zentraler Wert, den `restripe_treeview()` ohnehin bei jedem
Aufruf dynamisch nachschlaegt (`_palette()["zebra_odd"]`), also automatisch
ueberall wirksam ohne weitere Codeaenderung. Dark Mode: `#404040` ->
`#2d2d2d` (bewusst der bereits etablierte `entry_bg`-Ton wiederverwendet,
keine neue, ungetestete Farbe) - success/danger/info/muted/warn/swap jetzt
bei 4,0-6,5:1 (vorher 3,0-4,9:1), die meisten ueber der AA-Schwelle, der
Rest deutlich naeher dran. Light Mode: `#ebebeb` -> `#f2f2f2` (naeher an
`bg`) - success/danger/info jetzt bei 4,5-5,1:1 (vorher 4,3-4,8:1), alle
drei jetzt ueber der Schwelle.

**Verifikation:** synthetischer Tk-Test gegen eine DB-Kopie (kein echter
Produktivstart) mit gemockten `scan_aktien_candidates()`/
`scan_etf_candidates()`/`get_listed_non_crypto_assets()` (kein echter
Netzwerkzugriff im Test) - Auto-Scan-Ausloesung beim Tab-Aufbau, korrekt
geladenes Intervall aus `config.yaml`, Folge-Timer-Planung nach
Scan-Abschluss, Doppel-Scan-Guard, doppelter `_schedule_next_auto_scan()`-
Aufruf ohne Fehler, sowie die Tooltip-Bindung an allen neuen Widgets (2
Screener-Buttons, 4 Schwerpunkte-Buttons + 1 Checkbox, Notebook-Tab-Helper)
- alle 9 Testfaelle bestanden. Kombinierter Import-Regressionstest von
`ui.app` weiterhin fehlerfrei.

## Nachtrag (2026-07-20): `key_risks` bei Hebel-Signalen wurde bei
gleichem Regime/gleicher Aktion praktisch wortgleich wiederholt

**Auslöser:** Nutzer verglich zwei echte Hebel-ERÖFFNEN-E-Mails (ONDO,
KAIA) und bemerkte, dass die "Risiken:"-Liste vor dem Halte-Kriterium bei
beiden fast wortidentisch war ("Liquidationsrisiko bei schnellen
Kursbewegungen", "laufende Finanzierungsgebühr bei längerer Haltedauer",
"Gegen-Trend-Position ... Bärenregime").

**Root Cause:** anders als bei den Top-5-Gründen (Regel 8, verweist
explizit auf konkrete Indikatorwerte) gab Regel 9 dem Modell fuer
`key_risks` bisher fast woertlich die Zielformulierung als Beispiel vor
("Liquidationsrisiko bei schnellen Kursbewegungen, laufende
Finanzierungsgebühr bei längerer Haltedauer") - das Modell übernahm diese
Beispielsätze praktisch unveraendert statt sie nur als Kategorie-Vorgabe
zu behandeln. Der dritte, ebenfalls wiederkehrende Punkt stammt aus einer
strukturell identischen Formulierung in der Regime-Konflikt-Anweisung
(Regel 2, `regime.richtungs_konflikt_mit_trigger`).

**Fix (Nutzer-Entscheidung: Textbausteine behalten, aber um Zahlen
ergaenzen - minimal-invasiv statt Neuformulierung):** beide Prompt-Stellen
in `agent/krypto/hebel_analyst.py` fordern jetzt explizit, die
Beispielformulierungen mit den KONKRETEN Werten dieses Signals zu
ergaenzen - bei `key_risks` der eigene `hebel_vorschlag`-Wert (je hoeher,
desto groesser das Liquidationsrisiko bei gleicher Kursbewegung) sowie die
aktuelle `funding_rate_aktuell` aus den Fakten; beim Regime-Konflikt-Punkt
das konkrete `regime.regime` und die eigene Gegenszenario-Wahrscheinlichkeit
aus `forecast`. Eine reine Wortwiederholung ohne Zahlen ist damit explizit
als nicht ausreichend markiert.

**Bewusst NICHT angefasst:** die deterministische Risikofaktoren-Liste
("3. KONKLUSION", farbige Punkte) ist von diesem Fund nicht betroffen -
die wird NICHT vom LLM generiert (siehe `hebel_risk_gate.py::
compute_risikofaktoren_hebel()`-Docstring), sondern rein regelbasiert
berechnet.

**Verifikation:** reine Prompt-Textaenderung, keine Schema-/Code-Logik-
Aenderung - per Syntax-/Import-Check sowie manueller Sichtpruefung des
zusammengesetzten `SYSTEM_PROMPT`-Strings verifiziert. Kein echter
LLM-Testaufruf in dieser Runde (Wirkung zeigt sich erst am naechsten
echten Hebel-ERÖFFNEN-Signal auf dem Notebook).

## Nachtrag (2026-07-20): Risikofaktoren-Legende + drei kleine Bugfixes
aus der Notebook-Nachtanalyse

**Risikofaktoren-Legende:** Nutzer-Fund per Screenshot - das weisse
Neutral-Emoji (`_RISIKOFAKTOR_SYMBOL["neutral"]`) wird in manchen
E-Mail-Clients (Gmail-Web) blass-lila statt eindeutig grau gerendert, was
zu einer falschen Vermutung ueber die Farblogik fuehrte (tatsaechlich:
gruen = unterstuetzt die Empfehlung, rot = Warnsignal/Risiko). Neue
`RISIKOFAKTOREN_LEGENDE`-Konstante (`ui/formatting.py` fuer App-Kontext,
eigene Kopie in `scheduler/background.py` fuer E-Mail-Kontext, gleiches
Muster wie `_formatiere_risikofaktoren()`) direkt ueber der Liste in
Detail-Panel UND allen drei E-Mail-Vorlagen (Spot/Hebel/Multi-Asset).

**Drei kleine Bugfixes**, alle aus derselben Notebook-Diagnose-Auswertung:

1. `api/history.py::backfill_history()` - Guard fuer fehlende
   `coingecko_id` (verursachte taeglich einen sinnlosen
   `.../coins/None/market_chart`-404, im API-Health-Log sichtbar).
2. `api/yfinance_history.py::get_full_ohlc_history()` - bekannte "nur
   fast_info"-Ticker (`YFINANCE_HISTORY_UNRELIABLE_TICKERS`, z.B.
   X136.BE/IS0C.DE) wurden im taeglichen OHLC-Job bisher nicht
   beruecksichtigt (nur im 15-Min-Live-Preis-Pfad) - yfinance wirft dort
   hart "Period 'max' is invalid, must be one of: 1d, 5d" statt nur zu
   loggen. Jetzt zentraler Skip vor dem Call.
3. `api/onchain.py` - neue `MissingOnChainMetricError` statt rohem
   `TypeError: float() argument ... not 'NoneType'`, wenn CoinMetrics fuer
   den neuesten Tag eine einzelne Metrik noch nicht nachgetragen hat
   (bekannter Anbieter-Lag). Muster identisch zu
   `api/derivatives.py::NoOpenInterestDataError`.

Alle drei per synthetischem Test verifiziert (kein echter API-Call noetig,
da jeweils reines Verhalten bei fehlenden/fehlerhaften Rohdaten getestet).

## Nachtrag (2026-07-20): Risikofaktoren-Symbole von farbigen Emoji auf Form-Marker umgestellt

Fortsetzung des obigen Legende-Fixes - Nutzer schickte einen Screenshot des
LIVE laufenden Detail-Panels am Notebook (12:30 Uhr, Hebel-Tab): die
farbigen Kreis-Emoji (🟢/🔴) rendern in Tkinters Standardfont unter Windows
NICHT farblich unterscheidbar - beide fallen auf denselben Ersatzglyph
("⊘") zurueck, nur das weisse Neutral-Emoji (⚪) blieb als "○" sichtbar
unterscheidbar. Damit beschrieb die gerade erst hinzugefuegte
`RISIKOFAKTOREN_LEGENDE` eine Farbunterscheidung, die auf dem Bildschirm gar
nicht existierte - Ursache: `_set_detail_text()` (`ui/hebel_view.py`,
`ui/signals_view.py`) ist ein reiner `tk.Text.insert()`-Aufruf ohne jedes
`tag_configure(foreground=...)`, die Farbwirkung haengt komplett vom
(nicht vorhandenen) Emoji-Farb-Support des Fonts ab.

**Fix:** `_RISIKOFAKTOR_SYMBOL` in `ui/formatting.py` UND der parallelen
Kopie in `scheduler/background.py` von `{"positiv": "🟢", "neutral": "⚪",
"negativ": "🔴"}` auf `{"positiv": "▲", "neutral": "●", "negativ": "▼"}`
umgestellt - dieselben Form-Marker (unterschiedliche Glyphen, nicht nur
unterschiedliche Farbe), die bereits fuer die These-Marker im Schwerpunkte-
Tab etabliert sind (`ui/app.py`/`portfolio.py`/`screener_view.py`, gleiche
Semantik: ▲ positiv/unterstuetzend, ▼ negativ/Warnung, ● neutral). Form
statt Farbe macht die Unterscheidung robust sowohl gegen Tkinter-
Emoji-Rendering (App) als auch gegen E-Mail-Client-Eigenheiten (bereits der
Ausloeser des vorherigen Legende-Fixes). `RISIKOFAKTOREN_LEGENDE`-Text in
beiden Dateien entsprechend angepasst. Bewusst KEINE echten Tk-Farb-Tags
zusaetzlich eingefuehrt (haette eine Restrukturierung von `_set_detail_text()`
auf zeilenweises Einfuegen mit Tags erfordert) - die Form-Marker loesen das
gemeldete Problem bereits vollstaendig und bleiben minimal-invasiv.

Verifikation: synthetischer Test der Beispielszenerie aus dem Nutzer-
Screenshot (Regime-Konflikt=negativ, Retail-Konsens-Risiko=positiv) gegen
beide Formatierungsfunktionen, Tk-Smoke-Test bestaetigt, dass `tk.Text`
die drei Zeichen (U+25B2/U+25CF/U+25BC) unveraendert speichert/liefert.

## Nachtrag (2026-07-20): Dark-Mode-Comboboxen kaum lesbar (TCombobox-Styling-Luecke)

Nutzer-Screenshot vom "These bearbeiten"-Dialog (Schwerpunkte-Tab, live am
Notebook): alle vier readonly-Comboboxen (Hauptgruppe, Unterkategorie,
Richtung, Staerke) erschienen hell/kaum lesbar - sahen aus wie deaktivierte
Felder, obwohl `state="readonly"` (der Standard-Zustand fuer feste
Auswahllisten im gesamten Projekt) korrekt und normal editierbar ist.

Root Cause: `ui/theme.py::apply_dark_mode()` konfigurierte `TCombobox` nur
generisch mit `background`/`foreground`, setzte aber nie `fieldbackground`
(die eigentliche Textfeld-Flaeche im 'clam'-Theme, getrennt von
`background`) und keinen `style.map()` fuer den `readonly`-Zustand -
'clam' fiel dadurch im geschlossenen Zustand auf seine eingebaute helle
Systemfarbe zurueck. Zusaetzlich ist das aufklappende Popdown einer
ttk.Combobox intern ein klassisches Tk-Listbox-Widget, das `ttk.Style`
gar nicht erreicht und eigene `option_add()`-Zeilen braucht.

**Fix:** `style.configure("TCombobox", fieldbackground=..., arrowcolor=...)`
+ `style.map("TCombobox", fieldbackground=[("readonly", ...), ("disabled",
...)], foreground=[("readonly", ...), ("disabled", ...)], ...)` sowie vier
neue `root.option_add("*TCombobox*Listbox...")`-Zeilen fuer das Popdown.
Betrifft alle Comboboxen im Dark Mode projektweit (nicht nur den
Schwerpunkte-Tab) - reiner Style-Fix in der zentralen Theme-Datei, keine
Aenderung an einzelnen Dialogen noetig.

Verifikation: `ttk.Style.lookup("TCombobox", "fieldbackground"/"foreground",
state=["readonly"])` nach `apply_dark_mode()` liefert die erwarteten
Dark-Palette-Werte (vorher lieferte die Style-Lookup keinen expliziten
Override, `clam` nutzte seine Vorgabe); Tk-Smoke-Test baut den echten
`TheseDialog` fehlerfrei unter Dark Mode auf. Light Mode unveraendert (ruft
`apply_dark_mode()` gar nicht auf).

## Nachtrag (2026-07-20): Bitpanda-Gelistet-Override fuer Aktien/ETF/Rohstoffe

**Ausloeser:** Nutzer bemerkte im Signale-Detail-Panel und im laufenden
Notebook, dass mehrere gehaltene Rohstoff-/Themen-ETF-Positionen (CEBS,
EXH3, ISOC, VVMX, X136, OD7C/H/L/N, DBPK, 3QSS) durchgaengig als "nicht bei
Bitpanda gelistet" markiert wurden, obwohl er sie real haelt und handeln
kann - belegt mit zwei echten Bitpanda-Screenshots (DBPK = "S&P 500 2X
Inverse", ISOC = "iShares Agribusiness"), beide mit aktiven Kaufen/
Verkaufen/Tauschen-Buttons und real gehaltenen Anteilen.

**Root Cause (live verifiziert):** `api/bitpanda.py`s `/v3/assets`-
Endpunkt fand fuer keines der genannten Symbole einen Treffer - weder per
Symbol- noch per Namensvergleich (Volltextsuche nach "Copper Miners"/
"Food & Beverage"/"Agribusiness" ueber den kompletten Katalog, 3185
Eintraege inkl. 177 "etf" + 30 "etc", ergab null Treffer). Der Endpunkt ist
fuer Bitpandas "Bitpanda Stocks"-Fractional-ETF/ETC-Produktlinie offenbar
keine vollstaendige Quelle - PLTR/VST (echte Aktien) werden dagegen korrekt
gefunden. Reine Datenquellen-Luecke, kein Logikfehler in `is_listed()`.

**Konkreter Schaden:** `pre_check()` setzt `kauf_erlaubt = len(veto_reasons)
== 0`, `bitpanda_gelistet is False` landet in `veto_reasons`. In
`post_check()` erzwingt das bei jedem KAUFEN/NACHKAUFEN-Vorschlag
automatisch `risk_veto=True` -> `action="HALTEN"` (siehe RM-Bitpanda,
Kap. 3/Abschnitt 100/101 in diesem Manual). Fuer die betroffenen Assets
konnte die App also strukturell NIE einen (Nach-)Kauf empfehlen, unabhaengig
von der eigentlichen Analyse. VERKAUFEN/TAUSCHEN sind nicht betroffen (der
Veto greift nur bei `_BUY_ACTIONS`).

**Fix: manueller Override statt Abschaltung der Pruefung.** Neue Tabelle
`asset_bitpanda_override` (`database/db.py`, analog `asset_hebel_settings`)
+ `get_bitpanda_gelistet_override()`/`set_bitpanda_gelistet_override()`.
Default (keine Zeile): kein Override, der Live-Check gilt unveraendert -
keine Verhaltensaenderung fuer alle anderen Assets, insbesondere echtes
Krypto (CANTON/CC-Fall bleibt korrekt erfasst). Alle 4 Spot-family-
Pipelines (`agent/krypto/pipeline.py`, `agent/aktien/pipeline.py`,
`agent/rohstoff/pipeline.py`, `agent/themen_etf/pipeline.py`) pruefen den
Override direkt nach dem Live-Check: `if not bitpanda_gelistet and
db.get_bitpanda_gelistet_override(conn, asset.symbol): bitpanda_gelistet
= True`. Neuer Button "Bitpanda-Override umschalten" im Watchlist-Tab
(gleiches Auswahl-Toggle-Muster wie "Hebel-Pruefung umschalten", aber fuer
JEDE Assetklasse verfuegbar, nicht nur Krypto). Die Bitpanda-Spalte zeigt
bei aktivem Override "✓ (M)" statt "✗" - macht den effektiven Wert, den die
Pipelines tatsaechlich verwenden, transparent sichtbar.

**Nutzer-Vorgabe:** fuer zukuenftige Assets soll der Override manuell in
der App setzbar sein, nicht nur fuer die aktuell elf identifizierten
Symbole - deshalb ein generischer Toggle statt einer Hardcoded-Ausnahme-
liste im Code. Der Nutzer aktiviert den Override selbst am Notebook fuer
die von ihm bestaetigten Symbole (Desktop darf keine Produktivdaten
schreiben, siehe `feedback_desktop_kein_produktivstart`).

Verifikation: synthetischer Test von `get_/set_bitpanda_gelistet_override()`
(Default False, Toggle, ON-CONFLICT-Update ohne Fehler); Tk-Smoke-Test der
kompletten `TradingInfoToolApp` (In-Memory-DB, synthetisches CEBS-Asset) -
Watchlist-Spalte zeigt vor Override "✗", nach Klick auf den neuen Button
"✓ (M)", nach erneutem Klick wieder "✗", `get_bitpanda_gelistet_override()`
spiegelt den DB-Zustand exakt; Import-Check aller 4 Pipelines + `ui/app.py`
fehlerfrei.

## Nachtrag (2026-07-20): Bitpanda-Katalog-Dedup verwarf Krypto-Token bei Ticker-Kollision mit Aktien

**Ausloeser:** Nutzer bemerkte im Watchlist-Screenshot, dass mehrere Krypto-
Assets (SUI, W/Wormhole, BIO/Bio Protocol, CAT/Simon's Cat) - darunter SUI
als `core`-Position - ploetzlich rot/"nicht bei Bitpanda gelistet" zeigten,
obwohl es sich um bekannte, real gehandelte Token handelt.

**Root Cause (live bestaetigt):** `api/bitpanda.py::_fetch_all_bitpanda_assets()`
dedupliziert seit dem 2026-07-19-Bugfix ("erstes Vorkommen gewinnt") per
`symbol` UEBER ALLE Anlageklassen hinweg. Der Rohdatensatz enthaelt aber
echte Ticker-Kollisionen ZWISCHEN unterschiedlichen Klassen: Krypto-Token
"SUI" koexistiert mit der Aktie "Sun Communities" (REIT), "BIO" mit
"Bio-Rad Laboratories", "W" mit "Wayfair", "CAT" mit "Caterpillar" - live
im Rohdatensatz (vor Dedup) bestaetigt: beide Eintraege sind vorhanden.
Da die Aktien-Eintraege im Rohdatensatz vor den Krypto-Eintraegen auftraten,
"gewann" jeweils die Aktie den Dedup-Slot, der echte Krypto-Token wurde
schon VOR der gruppenspezifischen Filterung (`get_listed_assets()`) still-
schweigend verworfen. Der urspruengliche Bugfix vom 19.07. hatte diese ca.
53 "echten Symbol-Duplikate" bereits im eigenen Docstring korrekt als
"vermutlich verschiedene interne Assets mit kollidierendem Ticker"
identifiziert - aber trotzdem pauschal dedupliziert, ohne die Assetklassen-
uebergreifende Konsequenz zu bedenken.

**Fix:** Dedup-Schluessel von `symbol` auf `(symbol, group)` geaendert -
entfernt weiterhin echte Innerhalb-derselben-Gruppe-Duplikate (der
urspruengliche Zweck), behaelt aber Eintraege aus unterschiedlichen Gruppen
mit zufaellig gleichem Ticker als eigenstaendige Assets. Betrifft nur
`api/bitpanda.py`, keine Aenderung an Aufrufern noetig (`is_listed()`
bekommt ohnehin schon gruppen-gefilterte Listen).

**Vollstaendigkeits-Check:** alle 56 Watchlist-Symbole gegen den echten
Katalog geprueft - genau die 4 vom Nutzer gefundenen Symbole betroffen,
keine weiteren Kollisionen. Verifikation: Live-Check bestaetigt SUI/BIO/W/
CAT jetzt korrekt als gelistetes Krypto-Asset; Regressionstest bestaetigt
PLTR/VST (Aktien) weiterhin korrekt, die vier Kollisions-Symbole bleiben
auf der Aktien-Seite ebenfalls korrekt vorhanden (Sun Communities/Bio-Rad/
Wayfair/Caterpillar), CANTON/CC-Namens-Fallback weiterhin funktionsfaehig;
Tk-Smoke-Test der Watchlist-Spalte zeigt SUI/W jetzt "✓" statt "✗".

## Nachtrag (2026-07-20): Groq als Primär-LLM abgeloest - Mistral vor Groq + DB-persistente Erschoepfungs-Erkennung

**Ausloeser:** Nutzer bewertete Groq nach Auswertung der heutigen echten
LLM-Aufrufe als Primär-LLM "relativ unbrauchbar" - reale Zahlen bestaetigten
das: nur 9 von 79 echten Calls (~11%) liefen ueber Groq, `api_health` zeigte
echte `429 Too Many Requests`-Fehler. Zusaetzlich bestand seit dem
2026-07-18-Fund (siehe Nachtrag "Groq-Erschoepfungs-Erkennung") eine offene
Schwaeche: die In-Memory-Erschoepfungssperre wurde bei jedem App-Neustart
zurueckgesetzt - in der aktiven Entwicklungsphase (Notebook startet bei
jedem Git-Pull neu, ~8x/Tag beobachtet) lief Groq dadurch wiederholt binnen
Minuten erneut in dieselben 429-Fehlschlaege, bevor die Sperre erneut
greifen konnte.

**Fix 1 - Reihenfolge umgedreht:** `agent/krypto/budget_allocator.py` versucht
fuer jeden Kandidaten (Hebel/Marktscan/Spot) jetzt zuerst Mistral (falls
`mistral_client` gesetzt), erst bei dessen Fehlschlag Groq, dann Gemini.
Mistrals echt verifizierte Kapazitaet (2.250.000 TPM/300 RPM, siehe Nachtrag
Mistral-Integration) macht es zur zuverlaessigeren ersten Stufe; Groq bleibt
als kostenlose zweite Stufe erhalten (schlaegt gelegentlich noch erfolgreich
an), Gemini bleibt bewusst am Ende der Kette (ungueenstigste
Vertragsbedingungen, siehe Modul-Docstring).

**Fix 2 - DB-persistente Erschoepfungs-Erkennung:** neue Tabelle
`groq_exhaustion_status` (Einzeilen-Tabelle, `datum`/`fehlschlaege`/
`erschoepft`) in `database/db.py`, mit `is_groq_exhausted_today(conn)`/
`record_groq_failure(conn, schwelle)`/`record_groq_success(conn)` - ersetzen
1:1 die bisherigen modul-globalen In-Memory-Variablen (gleiche
Kalendertag-Semantik: N Fehlschlaege in Folge am selben Kalendertag ->
erschoepft, Erfolg setzt zurueck), ueberleben aber jetzt einen App-Neustart,
da der Zustand direkt aus der DB gelesen/geschrieben wird statt aus einer
Prozess-Variable. `_mit_fallback_chain()` in `budget_allocator.py` ruft
diese drei Funktionen ueber eine kurzlebige `conn_factory()`-Verbindung auf
(gleiches Muster wie der bestehende `_mit_conn()`-Helfer fuer die LLM-Calls
selbst).

**Verifikation:** synthetischer Test bestaetigt DB-Persistenz (Erschoepfung
ueberlebt einen simulierten "Neustart", d.h. eine neue Connection auf
dieselbe DB-Datei, Erfolg setzt korrekt zurueck) sowie die neue
Fallback-Reihenfolge in `run_budget_allocator()` gegen eine echte
In-Memory-SQLite-Kopie mit Fake-Clients: (1) Mistral erfolgreich -> Groq
wird gar nicht erst aufgerufen, (2) Mistral schlaegt fehl -> Fallback auf
Groq greift korrekt, (3) Groq DB-seitig als erschoepft markiert -> wird bei
einem Mistral-Fehlschlag korrekt uebersprungen (kein Aufruf, `result.
groq_erschoepft_erkannt=True`). Import-/Syntax-Check von
`agent/krypto/budget_allocator.py` und `scheduler/background.py` bestaetigt
keine verwaisten Referenzen mehr auf die entfernten In-Memory-Funktionen.

**Offen (bewusst nicht Teil dieser Runde):** `agent/multi_asset_batch.py`
(separater Cron fuer Aktien/Rohstoffe/Themen-ETF) hat weiterhin keinerlei
Groq-Erschoepfungs-Bewusstsein (kein Skip-Check, keine Erfolg-/Fehlschlag-
Aufzeichnung), obwohl es denselben Groq-Rate-Limit-Pool teilt - eine
natuerliche Erweiterung fuer Konsistenz, aber nicht Teil dieses expliziten
Nutzer-Auftrags ("ja mach beides" bezog sich nur auf die zwei oben
genannten Punkte).

## Nachtrag (2026-07-20): Provider-Performance-Karte nach Assetklasse aufgeschluesselt (Krypto/Aktien/Rohstoffe/ETF getrennt statt gepoolter "Spot"-Topf)

**Ausloeser:** Nutzer fragte nach dem Status von Backward-Tracking bei
Nicht-Krypto-Assetklassen anhand eines Remote-Status-Screenshots ("Provider-
Performance (Spot): noch keine Daten"). Antwort: Backward-Tracking selbst
lief fuer Aktien/Rohstoffe/Hedge/Themen-ETF bereits automatisch mit (alle 4
Spot-family-Pipelines schreiben ueber `db.insert_signal()` in dieselbe
`signals`-Tabelle, `run_backward_tracking()` liest diese Tabelle OHNE
Assetklassen-Filter) - das war kein Luecken-Fund. Die eigentliche Luecke:
`compute_provider_performance()` poolte ALLE Spot-Assetklassen (Krypto,
Aktien, Rohstoffe, Hedge, Themen-ETF) unter einem einzigen "spot"-
Schluessel in der Anzeige-Karte, wodurch nicht sichtbar war, ob eine
spaetere Win-Rate von Krypto oder z.B. Rohstoffen kommt - derselbe
Pooling-Fehler, der fuer den internen Win-Rate-Prompt-Fakt
(`compute_win_rate_fact()`) schon am 2026-07-18 behoben worden war, aber
fuer diese Anzeige-Karte nie nachgezogen wurde.

**Fix:** `agent/krypto/backward_tracking.py::compute_provider_performance()`
bekommt einen neuen optionalen Parameter `watchlist` (Default `None` = altes
Verhalten, ein gepoolter "spot"-Schluessel - erhaelt `extract_notebook_
diagnose.py` unveraendert funktionsfaehig, das ohne Watchlist aufruft). Ist
`watchlist` gesetzt, wird jedes aufgeloeste Spot-Signal ueber sein Symbol
der `asset.assetklasse` (krypto/aktien/rohstoffe/etf) zugeordnet statt
pauschal "spot" - bewusst FEINER als `compute_win_rate_fact()`s Pooling
(das Krypto+Aktien fuer die Prompt-Kalibrierung bewusst zusammenlegt),
weil diese Anzeige-Karte dem Nutzer Sichtbarkeit PRO Assetklasse geben
soll, nicht ein Modell kalibrieren. `remote/status.py::_get_provider_
performance()` reicht die Watchlist jetzt durch. `remote/server.py`
rendert die Spot-Seite ueber eine neue Funktion `renderSpotProviderPerformanceByAssetklasse()`
mit fester Reihenfolge/Beschriftung (Krypto/Aktien/Rohstoffe/ETF -
Themen-ETF und Hedge teilen sich die Watchlist-Assetklasse "etf" und
werden hier bewusst nicht weiter unterschieden), damit auch eine noch
leere Assetklasse sichtbar "noch keine Daten" zeigt statt stillschweigend
zu fehlen. Die Hebel-Karte bleibt unveraendert (Hebel ist ohnehin
krypto-exklusiv).

**Verifikation:** synthetischer Test mit 4 synthetischen, ueber den echten
Schreibpfad (`db.insert_signal()` + `db.update_signal_outcome()`) erzeugten
Signalen (je eins pro Assetklasse, je ein anderer Provider) bestaetigt:
(1) mit `watchlist` werden Krypto/Aktien/Rohstoffe/ETF korrekt getrennt
ausgewiesen, kein gepoolter "spot"-Schluessel mehr vorhanden; (2) ohne
`watchlist` (Legacy-Aufruf wie in `extract_notebook_diagnose.py`) bleiben
alle Spot-Signale weiterhin unter einem gemeinsamen "spot"-Schluessel
gepoolt, exakt wie vor der Aenderung. Syntax-Check aller 3 geaenderten
Dateien bestanden.

## Nachtrag (2026-07-20): Z.ai (Zhipu AI) testweise als vierte, unverifizierte Fallback-Stufe VOR Mistral eingehaengt

**Ausloeser:** Direkte Fortsetzung der Groq-Alternative-Recherche (siehe
[[project_groq_alternative_recherche_2026-07-20]] und
[[reference_llm_provider_recherche_uebersicht]]) - Z.ai/Zhipu GLM-4.5-Flash
wurde als echtes, dauerhaftes Free-Tier-Modell identifiziert (kein Trial-
Guthaben, OpenAI-kompatibler Endpunkt, gute Vertragsbedingungen fuer API-
Kunden: keine Speicherung, keine Trainings-Nutzung). Einzige offene Luecke:
die exakten Rate-Limits sind oeffentlich nicht dokumentiert (nur ein
Concurrency-Limit von 2 im Nutzer-Dashboard sichtbar, keine RPM/TPM/RPD-
Zahl). Nutzer-Entscheidung, trotzdem sofort produktiv zu testen: "kein
Grund nicht auf ein bestimmtes hoeheres Limit zu gehen, wenn diese Quelle
blockiert wird passiert auch nichts fuer diese eine Nacht".

**Umgesetzt:**
- `api/zai.py` (neu) - `ZaiClient`, identisches `.chat()`-Interface wie
  Groq/Mistral/Gemini (OpenAI-kompatibel, `https://api.z.ai/api/paas/v4/
  chat/completions`, Modell `glm-4.5-flash`). Bewusst KEIN konservativer
  Rate-Limiter wie bei Mistral (`RATE_LIMIT_PER_MINUTE = 120` ist nur ein
  grobes Sicherheitsnetz, keine Kapazitaetsschaetzung) - Nutzer-Vorgabe.
- `agent/krypto/budget_allocator.py`: neuer optionaler Parameter
  `zai_client`, eigener Tagesbudget-Zaehler (`zai_taegliches_budget`,
  Default 300 in `config.yaml`), neue `AllocationResult`-Felder
  (`zai_calls_verbraucht`/`zai_budget_erschoepft`). Alle 3 Tiers (Hebel/
  Marktscan/Spot) versuchen jetzt Z.ai VOR Mistral/Groq - testweise, NICHT
  final, siehe Modul-Docstring.
- `main.py`: `ZAI_API_KEY` gelesen, `ZaiClient` konstruiert (P-8-optional),
  an `build_scheduler()`/`app.run_app()` durchgereicht.
- `scheduler/background.py`: `hebel_screening_job()`/`build_scheduler()`
  reichen `zai_client` durch.
- UI-Wiring: `ui/app.py`, `ui/hebel_view.py`, `ui/signals_view.py` - neuer
  `zai_client`-Parameter, `_any_llm_client_available()` erweitert, die
  manuellen Einzel-Klick-Fallback-Tupel (Hebel-Tab + Signale-Tab, alle
  Assetklassen) versuchen Z.ai ebenfalls zuerst.
- `agent/krypto/llm_provider.py`: neuer `zai`-Zweig in `llm_model_label()`.
- `remote/server.py`: `"zai"` zu `API_HEALTH_GROUPS["api-health-llm"]`
  ergaenzt.
- `.env.example`/`.env`: `ZAI_API_KEY`-Platzhalter mit vollem
  Recherche-Kontext als Kommentar (gleiches Muster wie Mistral).

**Bewusst NICHT Teil dieser Runde:** `agent/multi_asset_batch.py` (Aktien/
Rohstoffe/Themen-ETF-Cron) - gleiche Scope-Entscheidung wie beim Groq-
Erschoepfungs-Fix, Z.ai bleibt vorerst auf die Krypto-Kette beschraenkt.

**Verifikation:** (1) echter Testaufruf gegen die echte Z.ai-API - einfacher
Chat-Call UND JSON-Mode (`response_format={"type": "json_object"}`) beide
erfolgreich, bestaetigt volle OpenAI-Kompatibilitaet. (2) Import-/Syntax-
Check aller 9 geaenderten Dateien fehlerfrei. (3) Synthetischer Test der
kompletten Fallback-Kette mit Fake-Clients gegen eine echte In-Memory-
SQLite-Kopie: Z.ai erfolgreich -> Mistral/Groq werden nicht gerufen; Z.ai
schlaegt fehl -> Fallback auf Mistral korrekt; Z.ai-Tagesbudget erschoepft
-> wird korrekt uebersprungen, Kette faellt auf Mistral zurueck.

**Offen:** Reihenfolge ist testweise, nicht final - sobald genug echte
Betriebsdaten (api_health-429-Rate, Provider-Performance) vorliegen, wird
neu entschieden, ob Z.ai vor Groq bleibt, dahinter wandert, oder bei
schlechten Ergebnissen wieder entfernt wird.

## Nachtrag (2026-07-20, spaet abends): Z.ai auf letzte Fallback-Stufe zurueckgestuft + Budget-Neukalibrierung

**Ausloeser:** Erste echte Testnacht mit Z.ai an erster Stelle (siehe
Nachtrag oben) lieferte sofort 2/2 `Read timed out`-Fehlschlaege
(hebel:NEAR:LONG, hebel:SUI:LONG, je nach ~80-100s) auf dem Notebook.
Root-Cause-Diagnose ueber mehrere Schritte:
1. Notebook-Log gruendlich durchsucht (`zai-Call für ... fehlgeschlagen`-
   Zeilen gefunden) - kein Haenger, sondern echte `ReadTimeout`-Exceptions.
2. Live-Test vom Desktop aus mit trivialem Prompt ("Antworte nur mit OK"):
   3/3 Erfolge in 4.6-10.2s - Z.ai grundsaetzlich erreichbar und schnell.
3. Live-Test vom Desktop mit REALISTISCHER Payload (echter `SYSTEM_PROMPT`
   aus `hebel_analyst.py`, 11.761 Zeichen + synthetisches Facts-JSON,
   JSON-Mode wie in der echten Pipeline): Timeout nach exakt 60.4s -
   reproduziert unabhaengig vom Notebook, also ein echtes Kapazitaets-
   problem der Payload-Groesse, kein Notebook-Netzwerk-/Hardware-Problem.
4. Vergleichstest beider echter Free-Tier-Modelle mit 150s-Timeout:
   GLM-4.5-Flash antwortete nach 109.2s korrekt und vollstaendig (valides
   JSON gemaess Schema) - GLM-4.7-Flash lieferte auch nach vollen 150s
   keine Antwort (Concurrency-Limit 1 statt 2, damit endgueltig verworfen).

**Fazit:** GLM-4.5-Flash ist nicht kaputt/unerreichbar, sondern schlicht zu
langsam fuer eine FRUEHE Fallback-Stufe (~110s realistische Antwortzeit,
der bisherige 60s-Timeout war strukturell zu knapp). Als erste Stufe wuerde
das jeden einzelnen Kandidaten um bis zu 2 Minuten verzoegern, bevor der
Fallback ueberhaupt greift - direkt gegensaetzlich zum parallel
dokumentierten Delta-Thema (siehe [[project_delta_berechnung_llm_abfrage_timing]]).

**Umgesetzt:**
- `agent/krypto/budget_allocator.py`: alle 3 Tiers (Hebel/Marktscan/Spot)
  neu geordnet auf Mistral -> Groq -> Gemini -> Z.ai (Z.ai jetzt echte
  letzte Stufe statt erste).
- `api/zai.py`: neue Konstante `REQUEST_TIMEOUT_SECONDS = 150` (vorher
  hart codiert 60s) - als letzte Stufe faellt die laengere Wartezeit kaum
  ins Gewicht, da nur genutzt wenn Mistral/Groq/Gemini alle drei
  fehlschlagen.
- Docstrings/Log-Zeilen in `main.py`, `budget_allocator.py`, `api/zai.py`,
  `config.yaml` auf die neue Reihenfolge korrigiert (vorher ueberall
  "testweise VOR Mistral").
- **Budget-Neukalibrierung** (Nutzer-Vorgabe: "flachere Budgetkurve,
  Glaettung, vernuenftige Last auf die ersten Quellen, dann sehen wir wo
  wir liegen" - Ziel: reale Kapazitaetsgrenzen von Mistral/Groq/Gemini
  ueber echte Nutzung sichtbar machen, UND beobachtete "1h-Leerlaufphasen"
  reduzieren, bei denen das Tagesbudget B schon frueh erschoepft war und
  fuer den Rest des Tages kein neuer Kandidat mehr einen LLM-Versuch
  bekam):
  - `mistral_taegliches_budget`: 150 -> 400 (weiterhin klar unter der
    echt verifizierten ~300/Min-Kapazitaet).
  - `gemini_taegliches_budget`: 200 -> 500 (weiterhin unter der
    recherchierten ~1.000-1.500/Tag-Kapazitaet).
  - `taegliches_budget_gesamt` (B): 90 -> 180 - deutlich mehr Puffer
    ueber dem rein rechnerischen Spot-Rotation-Bedarf (84/Tag bei 8h/15h-
    Cooldown), bleibt aber weiterhin unter Mistrals neuem 400er-Deckel,
    damit echte Ausreissertage kontrolliert in Gemini/Zai ueberlaufen
    statt den ganzen Tag ungebremst durchzuschlagen.
  - `spot_rotation_reserve` (F): 30 -> 60 (Verhaeltnis F/B ≈ 33%
    beibehalten).
  - Groq hat weiterhin keinen Tages-Deckel (nur echte 429-
    Erschoepfungserkennung) - laeuft also bereits "unter Last".

**Verifikation:** Reihenfolge-Aenderung per `grep` in allen 3 Tiers
bestaetigt (Mistral->Groq->Gemini->Zai). Syntax-Check aller 4 geaenderten
Python-/YAML-Dateien fehlerfrei. `_verteile_budget()` mit einem
synthetischen Ausreissertag getestet (20 Hebel + 15 Marktscan + 84 faellige
Spot-Kandidaten = 119 gesamt): mit dem alten B=90 waeren Spot-Kandidaten
auf 55 gekappt worden, mit B=180 bekommen alle 119 einen LLM-Versuch.

**Offen:** Erst nach einem echten Notebook-Neustart (config.yaml wird nur
einmal pro Prozess gelesen) wirksam. Weiterhin zu beobachten: ob die neuen,
grosszuegigeren Budgets zu mehr echten 429-Fehlern bei Mistral/Gemini
fuehren (dann waere die reale Kapazitaetsgrenze gefunden), und ob die
"1h-Leerlaufphasen" durch B=180 tatsaechlich seltener werden.

## Nachtrag (2026-07-21, Vormittag): Erste Nacht-Auswertung + BUGFIX Zeitzonen-Anzeige in Signal-E-Mails + zweiter Zai-Datenpunkt

**Nacht-Auswertung (frischer `extract_notebook_diagnose.py`-Export, ca.
9,5 Std. nach dem Neustart, Fokus letzte 6 Std.):** Die Umstellung wirkt
wie gedacht. Letzter `zai-Call`-Fehlschlag im gesamten Log war um 21:57 Uhr
- noch mit dem ALTEN Code (Timeout=60, Zai zuerst). Danach: kein einziger
Zai-Versuch mehr trotz durchgehender Aktivitaet, weil Zai jetzt hinten
steht und Mistral seither JEDEN Kandidaten sofort erfolgreich bedient
(alle stichprobenartig geprueften Hebel-/Spot-Signale der letzten 6 Std.
zeigen `llm_model: mistral:mistral-small-2506`, keine Mistral-Fehlschlaege,
kein 429, Tageszaehler von 3 - nach UTC-Mitternachts-Reset - auf 25 bis
06:18 Uhr, deutlich unter dem neuen 400er-Deckel). Groq/Gemini: 0 Calls,
nicht wegen Erschoepfung sondern weil Mistral nie fehlschlaegt. Keine
1h-Leerlaufphasen mehr sichtbar - alle `Budget-Allocator:`-Zusammenfassungs-
zeilen liegen durchgehend ~15 Minuten auseinander.

**BUGFIX - Zeitzonen-Anzeige in Signal-E-Mails (Nutzer-Fund):** eine
Hebel-E-Mail (KAIA ERÖFFNEN) zeigte `"Berechnet: 2026-07-21 01:17"` im
Mail-Body, waehrend der Gmail-Header den Empfang um `03:18 Uhr` (lokale
Zeit) auswies - wirkte wie eine 2-Stunden-Verzoegerung zwischen Berechnung
und Versand. Tatsaechlich war `signal.created_at` in der DB korrekt als
UTC gespeichert (`01:17:44+00:00` = `03:17:44` lokal, CEST = UTC+2) - der
Mail-Text zeigte aber den rohen UTC-String OHNE Umrechnung
(`signal.created_at[:16].replace("T", " ")`, an 3 Stellen in
`scheduler/background.py` identisch). Kein echtes Latenzproblem, reiner
Anzeige-Bug. **Fix:** neue Funktion `_formatiere_zeitpunkt_lokal()`
(`datetime.fromisoformat(...).astimezone().strftime(...)`, konvertiert auf
die lokale Systemzeitzone) ersetzt alle 3 Vorkommen. Wichtig: dieser Fund
betrifft NICHT die andere, echte Beobachtung vom Vorabend (Marktscan-
Discovery 16:00 Uhr vs. Signal 19:30 Uhr, siehe
[[project_delta_berechnung_llm_abfrage_timing]]) - das ist ein separater,
weiterhin ungeloester Mechanismus (Warteschlange im Budget-Allocator),
kein Zeitzonen-Darstellungsfehler.

**Zweiter Zai-Realdaten-Punkt (Desktop-Live-Test, gleiche realistische
Payload wie am Vorabend):** GLM-4.5-Flash, das am Vorabend noch nach
109,2s erfolgreich geantwortet hatte, schaffte es diesmal NICHT innerhalb
von 150s (`ReadTimeout` nach 150,8s). GLM-4.7-Flash ebenfalls Timeout nach
150,6s. Die Antwortzeiten sind also nicht stabiler/schneller geworden,
eher volatiler - bestaetigt die Entscheidung, Zai nur noch als letzte,
selten erreichte Stufe zu fuehren.

**Verifikation:** `_formatiere_zeitpunkt_lokal()` funktional getestet
(UTC `2026-07-21T01:17:44...+00:00` -> lokal `2026-07-21 03:17`, `None` ->
`"-"`, kaputter String -> Fallback auf alte Slicing-Logik). Syntax-Check
von `scheduler/background.py` fehlerfrei.

## Nachtrag (2026-07-21): Groq-Alternative-Recherche Runde 3+4 abgeschlossen - 32 Kandidaten insgesamt verworfen, Suche vorerst beendet

Ausgeloest durch Zais enttaeuschende erste Nacht, vom Nutzer bewusst NICHT
nach dem ersten Fehlschlag abgebrochen ("Runde nicht vorbei, nur durch
Fehlschlag unterbrochen"), spaeter fortgesetzt bis zu einem selbst gesetzten
Budget ("noch ca. 5 Kandidaten, dann Schluss fuer heute"). Runde 3 (7
Kandidaten: Vercel AI Gateway, OpenCode Zen, OVHcloud AI Endpoints,
SambaNova-Re-Check, Moonshot/Kimi, MiniMax, SiliconFlow) und Runde 4 (10
Kandidaten: xAI-Re-Check, Scaleway, AI21 Labs, Fireworks AI, Nebius AI
Studio, StepFun, 01.AI/Yi, Poe API, Reka AI, Baidu Qianfan/ERNIE) - alle
Details in Memory [[project_groq_alternative_recherche_2026-07-20]].

**Bemerkenswertester Fund: Nebius AI Studio** (Nebius B.V., Amsterdam,
Nasdaq-gelistet) - qualitativ die besten Vertragsbedingungen der gesamten
Recherche: automatische Rate-Limit-Skalierung basierend auf echter Nutzung
statt Bezahlung (Dokumentation: "wenn Nutzung in einem 15-Min-Fenster
>=80% des Limits erreicht, steigt das Limit um 20%"), GDPR-nativ, ToS
woertlich "Nebius will not use Customer Content to train Nebius Models".
Scheiterte trotzdem am selben harten Ausschlusskriterium wie fast alle
anderen Kandidaten dieser beiden Runden: eine Kreditkarte ist fuer den
Signup zwingend ("$0 authorization to verify the card"). Nutzer hat den
Schritt bewusst abgebrochen, keine Kartendaten eingegeben.

**Durchgaengiges Muster ueber beide Runden:** praktisch jeder gepruefte
Kandidat gehoert zu einer von drei Kategorien - (1) reiner Einmal-Trial
statt dauerhaftem Free-Tier (Scaleway, AI21, Fireworks, StepFun, Reka,
Moonshot), (2) Kreditkarte/Zahlungsmethode zwingend fuer brauchbare Limits
(Vercel, OVHcloud, SiliconFlow, Nebius), oder (3) struktureller Zugangs-
Ausschluss (Baidu: chinesische Mobilfunknummer noetig, wie schon Alibaba/
Qwen in Runde 2).

**Status:** Kette bleibt Mistral -> Groq -> Gemini -> Z.ai. Suche fuer
diese Session auf Nutzer-Wunsch beendet. Revisit-Bedingung siehe Memory:
entweder ein Anbieter mit echtem Dauer-Free-Tier ohne Kreditkarte/China-
Telefon/Umsatzschwelle taucht auf, oder Nebius bietet irgendwann einen
Signup-Pfad ohne Kreditkarten-Pflicht an.

## Nachtrag (2026-07-21, Nachmittag): Zai-Root-Cause endgueltig geklaert - Kontextlaengen-Drosselung >8K Token

Nutzer entdeckte auf der Z.ai-"Rate Limits"-Dashboardseite einen bisher
uebersehenen Erklaerungstext: "To ensure stable access to GLM-4-Flash
during the free trial, requests with context lengths over 8K will be
throttled to 1% of the standard concurrency limit." Das erklaert die seit
zwei Tagen beobachteten Zai-Probleme (2/2 Timeouts erste Nacht, 109,2s-
Erfolg vs. 150s-Doppel-Timeout am naechsten Vormittag) potenziell vollstaendig
- keine allgemeine Modell-Langsamkeit, sondern eine gezielte Drosselung ab
einer bestimmten Kontextgroesse.

**Gezielter Vergleichstest** (`test_zai_context_length_hypothesis.py`,
identischer echter `SYSTEM_PROMPT` aus `hebel_analyst.py`, einmal mit
kleinem, einmal mit auf >8K Token aufgeblaehtem Facts-Payload, glm-4.5-flash,
150s Timeout) bestaetigt die These eindeutig:
- Klein (echte 3.910 Prompt-Tokens laut API-`usage`-Feld, unter 8K): Erfolg
  nach 105,9s (2.184 Zeichen Antwort, 3.387 Completion-Tokens) - deckt sich
  mit dem 109,2s-Erfolgswert vom Vorabend.
- Gross (>8K Token): kompletter `ReadTimeout` nach den vollen 150s, keine
  Antwort.

**Praktische Einordnung:** Unser Hebel-`SYSTEM_PROMPT` allein ist bereits
~11.761 Zeichen (~3.360 Token geschaetzt), der Spot-`SYSTEM_PROMPT` sogar
~18.119 Zeichen (~5.177 Token geschaetzt) - bei echten (nicht synthetischen)
Facts-Payloads mit vollem Kontext (Historie, Risikofaktoren, Makro-Analog-
Vergleich) rutscht man damit speziell bei Spot- und bei umfangreicheren
Hebel-Signalen plausibel regelmaessig ueber die 8K-Grenze.

**Entscheidung:** keine Code-Aenderung. Ein Zai-spezifischer gekuerzter
Prompt wuerde den Aufwand nicht rechtfertigen, da Zai ohnehin nur die
seltenste letzte Rueckfallstufe ist (Mistral bedient real praktisch die
gesamte Last). Root-Cause-Recherche hiermit abgeschlossen.

**Nebenbefund - Dashboard-Anomalie "Last used: Not used" geklaert:** Der
API-Key ("TIT") zeigte durchgehend "Last used: Not used", obwohl mehrfach
echte, erfolgreich abgeschlossene Testcalls liefen (inkl. des obigen
Kleinpayload-Calls mit echten `usage`-Daten in der Antwort). Komplette
Dashboard-Seitenleiste durchgeprueft (Account, Rate Limits, GLM Coding
Plan/My Plan/Usage, API Keys, Billing) plus oberer "API"-Navigationspunkt -
"My Plan"/"Usage" gehoeren nachweislich zu einem anderen Produkt (GLM Coding
Plan, IDE-Abo, "You don't have any subscription"), "Billing" zeigt nur
$0-Bilanz. Auch nach dem definitiv erfolgreichen Testcall weiterhin "Not
used" - damit endgueltig als kosmetische Z.ai-Dashboard-Einschraenkung
eingeordnet (vermutlich rein Billing-Event-basierte Anzeige, die fuer
kostenlose Flash-Modell-Calls ohne Zahlungsereignis nie aktualisiert wird),
OHNE Auswirkung auf unser eigenes (DB-basiertes) Budget-Tracking.
Investigation abgeschlossen.

**Nachtrag - Isolationstest bestaetigt zweite, unabhaengige Bremse:
Generierungsgeschwindigkeit selbst.** Nutzer hinterfragte zurecht, warum
selbst der erfolgreiche Kleinpayload-Call (unter 8K) noch 105,9s brauchte.
Gezielter Isolationstest (`test_zai_speed_isolation.py`, identischer Prompt
~3.866 Token, aber `max_tokens=20` erzwungen statt voller Antwort): Erfolg
nach nur 5,1s. Damit klar getrennt: Prompt-Verarbeitung/Warteschlange ist
schnell (~5s fuer ~3.900 Token Input), die reine Text-Generierung ist der
Flaschenhals (~34-35 Tokens/Sekunde). Das heisst: selbst ein perfekt unter
8K gehaltener Prompt waere bei uns real weiterhin ~100s+ langsam, weil
unser Signal-Schema lange strukturierte JSON-Antworten verlangt - die
Langsamkeit ist NICHT nur kontextlaengenabhaengig, sondern eine zweite,
unabhaengige Bremse der Generierungsgeschwindigkeit auf dem kostenlosen
Tier. Bestaetigt die Entscheidung (Zai bleibt letzte, selten gebrauchte
Rueckfallstufe) noch eindeutiger - Prompt-Kuerzung allein wuerde das
Problem nicht loesen.

**Bestaetigung durch offizielle Z.ai-FAQ** (docs.z.ai/help/faq), Frage "Why
hasn't my account balance changed after I used the API?": "The billing
history reflect daily consumption records, and therefore display the
billing status from the previous day (n-1). Current day consumption will
not be immediately visible in the billing details" (zusaetzlich: "there is
currently a processing delay in our billing system"). Offizielle
Bestaetigung einer generellen n-1-Verzoegerung im gesamten Billing-/
Nutzungssystem - unser Key wurde erst 2026-07-20 abends angelegt, "Not
used" ist damit die dokumentierte Verzoegerung, kein Fehler.

## Nachtrag (2026-07-21): Marktscan-Dedup-Bug behoben - "immer dieselben Coins" (APE/EIGEN)

Im Rahmen der Budget-Allocator-Neuplanung (siehe Plan-Datei
swift-napping-muffin.md) fiel beim historischen Backtest auf, dass ueber
12 Tage/24 Scan-Laeufe nur 8 verschiedene Coins je als `kaufkandidat`
auftauchten. Nutzer-Skepsis ("immer dieselben Ergebnisse sehe ich eher
negativ als positiv") war berechtigt und deckte einen echten, eigenstaendigen
Bug auf - getrennt vom SLA-/Warteschlangen-Thema.

**Root Cause:** `agent/krypto/marktscan.py::_duplicate_should_skip()` prueft
bisher nur, ob ein Coin bereits auf der echten Watchlist ist oder final
entschieden wurde (`nutzer_verworfen`/`nutzer_behalten_manuell_
uebernommen`). Ein Coin mit Status `neu` (unbearbeitete Kaufkandidat-Zeile)
oder `verfallen` wurde NICHT uebersprungen - da jeder der zwei taeglichen
Scan-Laeufe eine komplett neue Zeile anlegt (eigene `scan_run_id`,
`UNIQUE(coingecko_id, scan_run_id)`), wurde derselbe, laengst entdeckte
Coin bei jedem Lauf erneut dupliziert. Historischer Beleg aus der lokalen
DB: APE und EIGEN bekamen am 2026-07-09 acht frische 'neu'-Zeilen innerhalb
weniger Stunden, bevor der Nutzer reagierte - dieselben zwei Coins
dominierten zwei Wochen spaeter noch immer die Stichprobe.

**Einordnung:** Zwei getrennte Effekte. (1) Beabsichtigt/gesund: die
Kaufkandidat-Schwelle (Score >=70) ist bewusst eng - von 468 historischen
Rohkandidaten-Zeilen erreichten nur 3,8% je "kaufkandidat", 84 verschiedene
Coins wurden aber roh entdeckt (Filter A filtert 86% vorher raus, siehe
`apply_stufe_a_filters()`). (2) Echter Bug obendrauf: das fehlende Dedup
liess denselben Coin immer wieder dieselben knappen Plaetze belegen, statt
echten neuen Tages-Kandidaten eine faire Chance zu geben.

**Fix:**
- `database/db.py`: `has_pending_marktscan_kaufkandidat()` (existenzielle
  Pruefung: gibt es IRGENDWO in der Historie eine unbearbeitete
  Kaufkandidat-Zeile fuer diesen Coin?) + `get_letzter_marktscan_verfall_am()`
  (juengster Verfallszeitpunkt fuer die Abklingzeit-Pruefung).
- `_duplicate_should_skip()` erweitert: ueberspringt jetzt zusaetzlich (a)
  Coins mit bereits unbearbeiteter Kaufkandidat-Zeile (unabhaengig von
  einer Zeitschwelle - die bestehende Zeile wartet einfach in Ruhe weiter)
  und (b) kuerzlich (< `verfallen_abklingzeit_stunden`) verfallene Coins
  (verhindert sofortiges Wiederauftauchen, gibt der Marktlage aber nach
  einer Abklingzeit eine neue Chance).
- `config.yaml::marktscan.verfallen_abklingzeit_stunden` (neu, Default 24h).

**Verifikation:** 5 synthetische Testfaelle (unbearbeiteter Kaufkandidat,
kuerzlich verfallen, lange verfallen, nutzer_verworfen, nie gesehener Coin)
- alle bestanden. Smoke-Test gegen die lokale Desktop-DB reproduziert den
echten APE-Fall (`has_pending_marktscan_kaufkandidat` liefert korrekt
`True`).

## Nachtrag (2026-07-21): Budget-Allocator neu gedacht - SLA-Reservierung statt Score-Ranking (Abschnitt 2+3 umgesetzt)

Umsetzung der in `docs/budget_queue_design.md` (Nachtrag) revidierten
Design-Entscheidung, nach vollstaendiger Genehmigung des Plans
(swift-napping-muffin.md) inkl. historischem Backtest VOR jeder Code-
Aenderung (siehe eigener Nachtrag oben zu "Wahre Wartezeit-Erkennung").

**Kernaenderung:** `agent/krypto/budget_allocator.py::_priorisiere_nach_
wartezeit()` teilt jede Kandidatenliste (Hebel-Trigger, Marktscan-
Kaufkandidaten - beide bereits DB-seitig `score_gesamt DESC` sortiert) in
"ueberfaellig" (wahre Wartezeit seit Erstkandidatur >= effektiver SLA-
Schwelle) und "normal". Ueberfaellige werden IMMER zuerst eingereiht (FIFO
untereinander, nach Wartezeit absteigend), Normale behalten die
bestehende Score-Reihenfolge. Der bestehende `[:tier_n]`-Deckel aus
`_verteile_budget()` bleibt unveraendert - echte Garantie statt Soft-Boost,
wie vom Nutzer gefordert.

**Portfolio-Bezug** (`database/db.py::get_portfolio_prioritaets_bonus_
je_symbol()`): die effektive SLA-Schwelle wird pro Symbol reduziert, wenn
es bereits gehalten wird (Spot ODER offene Hebel-Position, 12h Bonus) oder
`WatchlistAsset.rolle=='core'` ist (6h Bonus - deckt den Fall "noch nie
gehalten, aber bewusster Erstkauf-Kandidat" ab). Bewusst NICHT These-
basiert - Krypto ist von der Kategorie-Taxonomie ausgeschlossen (siehe
Marktscan-Dedup-Nachtrag oben).

**Neue config.yaml-Schluessel:** `budget_allocator.hebel_kandidat_sla_
stunden` (6), `marktscan_kandidat_sla_stunden` (30), `bonus_gehalten_
stunden` (12), `bonus_kern_rolle_stunden` (6), `marktscan_kandidat_
luecken_toleranz_stunden` (20), `marktscan_wartezeit_lookback_tage_cap`
(14); `hebel_screening.hebel_kandidat_luecken_toleranz_stunden` (1.5),
`hebel_wartezeit_lookback_tage_cap` (14).

**Verfall-Backstop korrigiert:** `expire_stale_hebel_candidates()`/
`expire_stale_marktscan_candidates()` pruefen jetzt die wahre Kandidatur-
Dauer statt des Alters der (immer frischen) einzelnen Zeile - der 48h-
Verfall wirkt damit erstmals tatsaechlich als Backstop (siehe eigener
Nachtrag oben).

**Verifikation:** Unit-Test `_priorisiere_nach_wartezeit()` (Ueberfaellige
zuerst, Normale behalten Reihenfolge, keine Kandidaten verloren). Info-
Leichen-Regressionstest (Paar mit 60h durchgehender Requalifizierung, 241
Zeilen) - verfaellt jetzt korrekt, waere mit der alten Logik nie verfallen.
End-to-End-Trockenlauf gegen die echte Desktop-DB-Kopie (alle LLM-/
Netzwerk-Clients=None, garantiert kein echter Call) - kompletter Durchlauf
ohne Exception, neue Log-Zeile zeigt korrekt "ueberfaellig=1" fuer den
einzigen vorhandenen Hebel-Kandidaten (FLOKI SHORT).

**Methodik dieser Runde (als Vorgehens-Standard fuer kuenftige aehnliche
Faelle festgehalten):**

1. **Harte Garantie statt Soft-Boost bei systemischen Verzoegerungs-/
   Fairness-Problemen.** Ein "Prioritaet nach Wartezeit leicht erhoehen"-
   Vorschlag wurde vom Nutzer explizit verworfen, weil er das Problem nur
   abschwaecht, nicht strukturell begrenzt (weiterhin von noch hoeher
   gescorten/frischeren Kandidaten verdraengbar). Stattdessen: die
   Kandidatenliste strukturell in "ueberfaellig" (immer zuerst, FIFO
   untereinander) und "normal" (unveraenderte Reihenfolge) teilen - das
   ist eine echte Obergrenze, kein Wahrscheinlichkeits-Vorteil. Gilt als
   Leitplanke fuer jede kuenftige Priorisierungs-/Scheduling-Aenderung in
   diesem Projekt: bei einer echten Deadline-/Fairness-Anforderung ein
   strukturelles Zwei-Klassen-Modell pruefen, bevor ein Score-Zuschlag
   vorgeschlagen wird.
2. **Historischer Backtest gegen echte Produktionsdaten ist ein
   verpflichtendes Gate VOR jeder Aenderung an produktivem Entscheidungs-
   code** (Budget-Allocator, Risk-Gate, Scoring o.ae.) - nicht optional
   und nicht nachtraeglich. Erst nach Ruecksprache zu den Backtest-
   Ergebnissen wurde ueberhaupt mit der eigentlichen Code-Aenderung
   begonnen (siehe Ablauf im Plan `swift-napping-muffin.md`).
3. **Eine einzige Quelle der Wahrheit fuer Backtest und Live-Betrieb**:
   die neuen Wartezeit-Funktionen (`get_hebel_wartezeit_stunden_je_paar()`/
   `get_marktscan_wartezeit_stunden_je_coin()`) bekamen einen optionalen
   `as_of`-Parameter, damit der Backtest exakt dieselbe Produktionslogik
   mit einem Zeitpunkt aus der Vergangenheit aufruft - kein separat
   gepflegter Simulations-Nachbau derselben Regel, der unbemerkt
   auseinanderlaufen koennte.
4. **Nutzer-Skepsis gegenueber einer "harmlosen" Erklaerung ernst nehmen
   und tiefer graben, statt sie als Datensparsamkeit abzutun.** Die
   Beobachtung "immer dieselben Coins (APE/EIGEN)" wurde zunaechst als
   plausible Folge duenner Marktscan-Historie eingeordnet - der Nutzer
   wies das explizit als "eher negativ als positiv" zurueck und verlangte
   eine echte Mechanik-Pruefung. Das deckte den zweiten, unabhaengigen
   Dedup-Bug auf (siehe eigener Nachtrag oben). Bestaetigt/erweitert
   [[feedback_thorough_diagnosis_before_conclusion]]: gilt auch, wenn die
   erste Erklaerung technisch plausibel klingt, aber der Nutzer aus
   Erfahrung/Beobachtung widerspricht.

## Nachtrag (2026-07-21): Abschnitt 4 - Wartezeit-Transparenz in UI + E-Mail

Letzter Baustein des Plans (`swift-napping-muffin.md`): der Nutzer soll die
neue SLA-Logik nicht nur an weniger Verzoegerung erkennen, sondern die
wahre Wartezeit auch direkt einsehen koennen - konsistent mit dem bereits
etablierten Anzeige-Prinzip (`_formatiere_zeitpunkt_lokal()`): reine
Anzeige, nie ein neuer LLM-Fakt.

- `ui/hebel_view.py`/`ui/marktscan_view.py`: Mouseover-Tooltip (nicht neue
  Spalte, `ui/row_tooltip.py`-Muster wie in `regime_view.py`/`thesen_view.py`)
  auf noch unbearbeiteten Kandidaten-Zeilen, live berechnet bei jedem
  `refresh()`/`_refresh_list()` ueber `get_hebel_wartezeit_stunden_je_paar()`/
  `get_marktscan_wartezeit_stunden_je_coin()` - kein neues DB-Feld.
- `scheduler/background.py::_notify_hebel_signal()`: neuer optionaler
  `conn_factory`-Parameter, Zeile "· Wartezeit seit Erstkandidatur: Xh"
  neben "Berechnet: ... · Anbieter: ...". **Bewusst NICHT** in
  `_notify_spot_signal()` ergaenzt (Abweichung von der urspruenglichen
  Plan-Formulierung, nach Code-Pruefung korrigiert): Tier 3 (Spot-Rotation)
  hat keine Kandidatur-Historie wie Hebel/Marktscan (keine wiederholt
  eingefuegten "ist_kandidat"-Zeilen, nur Cooldown-Intervalle) - eine
  Wartezeit-seit-Erstkandidatur ist dort konzeptionell nicht definiert.
  Marktscan-Kaufkandidaten (Tier 2) erzeugen ohnehin kein Signal-Objekt
  (nur eine Kurzbegruendung/"Writeup", siehe `budget_allocator.py`s
  `marktscan:`-Zweig) und werden daher schon bisher gar nicht per E-Mail
  benachrichtigt - unveraendert, kein Teil dieser Aenderung.

**Verifikation:** Tk-Smoke-Test beider Views gegen eine echte DB-Kopie
(FLOKI/SHORT-Tooltip zeigt korrekt 177,8h, identisch zum direkt per
`db.py`-Funktion berechneten Wert) + synthetischer E-Mail-Test
(`_notify_hebel_signal()` mit echtem CAT/SHORT-Wartezeitwert, Zeile
erscheint korrekt im Mail-Body).

**Nebenbefund waehrend der Verifikation:** der End-to-End-Trockenlauf aus
Abschnitt 2+3 (`test_budget_allocator_dry_run.py`) hatte `db.DB_PATH` nie
auf eine Kopie umgebogen und dadurch versehentlich einen echten
Gate-Fail-HALTEN-Datensatz (FLOKI/SHORT, "Preis veraltet oder nicht
vorhanden", kein LLM-Call/keine Kosten) in die echte lokale Desktop-DB
geschrieben - dasselbe Muster wie bei den Desktop-Produktivstart-Vorfaellen
zuvor, diesmal durch ein Test-Skript statt die App selbst. Nutzer
entschied sich fuer Bereinigung, Zeile wurde nach Bestaetigung geloescht.
Lehre: Verifikationsskripte gegen Produktivdaten IMMER `db.DB_PATH` explizit
auf eine Kopie umbiegen, nie den Default-Pfad implizit verwenden.

## Nachtrag (2026-07-21): Historische-Trefferquote-Risikofaktor + Provider-Performance-Karte verstaendlicher

Echter Anlass: erstes BTC-LONG-Hebel-Signal, dessen Gegenargument die
historische Erfolgsquote (0%) nannte, aber den mitgelieferten
Stichprobengroessen-Hinweis (nur 5 aufgeloeste Hebel-Signale bisher, alle 5
Stop-Loss) NICHT erwaehnte - obwohl `hebel_analyst.py`s SYSTEM_PROMPT Regel
14 das Modell explizit dazu anweist. Genau das gleiche Prinzip wie beim
AVAX-Fund (Modell-Interpretationsfehler nicht dem Modell ueberlassen):

- `hebel_risk_gate.py::compute_risikofaktoren_hebel()`: neuer Parameter
  `historische_erfolgsquote` (+ `min_sample_fuer_aussage`, Default 15,
  identisch zu `backward_tracking.py::_MIN_SAMPLE_FUER_AUSSAGE`). Bei
  `anzahl_ausgewertete_signale < 15` erscheint IMMER ein neutraler
  Risikofaktor "Historische Trefferquote X% (n=Y)" mit explizitem
  Stichproben-Hinweis - unabhaengig davon, ob das LLM es im freien
  Gegenargument-Text erwaehnt. Bei ausreichender Stichprobe wird die Quote
  stattdessen als positiv/neutral/negativ bewertet (Schwellen 30%/60%).
  `post_check_hebel()` reicht den bereits in `hebel_pipeline.py` berechneten
  `historische_erfolgsquote`-Fakt einfach durch (keine zweite DB-Abfrage).
- Verifiziert per 3 synthetischen Faellen: kleine Stichprobe (n=5, neutral +
  Hinweistext), grosse Stichprobe mit schlechter Quote (n=20/20%, negativ),
  kein Fakt vorhanden (kein Risikofaktor-Eintrag).

**Provider-Performance-Karte auf der Remote-Seite** (`remote/server.py`):
Nutzer-Fund - "keine Daten" ohne Begruendung war nicht nachvollziehbar. Fix:
- Erklaerender Untertitel unter beiden Karten-Ueberschriften (Spot/Hebel),
  was die Kennzahl bedeutet (nur ECHTE, bereits aufgeloeste Signale, kein
  Backtest) und warum sie je Assetklasse/Tier getrennt ist.
- Leerer Zustand nennt jetzt den Grund ("noch keine abgeschlossenen Signale
  ... kann Tage bis Wochen dauern") statt nur "noch keine Daten" zu meiden.
- Jede Provider-Zeile mit `anzahl_resolved < 15` bekommt denselben
  Stichproben-Hinweis wie oben ("noch nicht belastbar") direkt neben der
  Zahl - dieselbe Schwelle wie im neuen Hebel-Risikofaktor, konsistent
  sichtbar an beiden Stellen.

## Nachtrag (2026-07-22): Retail-Konsens + CRV/Stop-Loss - "Fakt zuerst, Wertung danach"

Ausloeser: Nutzer wertete alle 9 ERÖFFNEN-Empfehlungen einer Nacht (7
Symbole, LONG, Regime baer) im Detail aus und fand zwei echte, wiederholt
auftretende Probleme - beide vom selben Muster ("eine abgeleitete
Kennzahl/binaere Phrase versteckt den eigentlich relevanten Rohwert").

**1. Retail-Konsens-Risiko (5 von 7 Signalen mit Wert betroffen, ~71%):**
Die alte Version pruefte nur "ist die Mehrheit EXTREM (>65%)?" und
beschriftete JEDEN Nicht-Extremfall pauschal als "positiv"/"steht NICHT im
Konsens" - auch bei 51-64% long UND einer LONG-Empfehlung, was tatsaechlich
DIESELBE Richtung wie die (nicht-extreme) Mehrheit ist. Fix in
`hebel_risk_gate.py::compute_risikofaktoren_hebel()`: der Text nennt jetzt
IMMER explizit den Prozentsatz und ob die empfohlene Richtung mit der
Mehrheit uebereinstimmt oder nicht ("Fakt zuerst") - die Bewertung wird
danach in drei Stufen abgeleitet: negativ (extreme gleiche Richtung,
unveraendert), **neutral (NEU - moderate gleiche Richtung, weder klarer
Kontraindikator noch antizyklischer Pluspunkt)**, positiv (nur noch bei
echter Gegenrichtung zur Mehrheit).

**2. CRV kann durch einen unrealistisch engen Stop-Loss aufgeblaeht werden:**
Ein echtes BTC-Signal (21:35 derselben Nacht) hatte einen Stop-Loss nur
1,12% vom Entry entfernt - bei 3x Hebel reicht normales Kursrauschen (kein
Krisenereignis) zum Ausloesen - wurde aber wegen der dadurch aufgeblaehten
CRV (16,41) als "deutlich ueber Minimum, positiv" bewertet. Zum Vergleich:
XLM hatte eine aehnlich hohe CRV (4,20) bei einem soliden 7,72%-Stop - die
reine CRV-Zahl unterscheidet diese sehr unterschiedlichen Risikoprofile
nicht. Fix:
- CRV-Risikofaktor-Text nennt jetzt immer den Stop-Loss-Abstand in % mit.
- Neuer eigener Risikofaktor "Enger Stop-Loss (X%)" (negativ), wenn der
  Abstand unter `risiko.hebel.sl_abstand_eng_schwelle_relativ` (NEU, 2%)
  liegt - unabhaengig von einer gleichzeitig hohen CRV.
- `post_check_hebel()` berechnet `sl_abstand_relativ` aus den bereits
  vorhandenen `entry_mid`/`stop_von`-Werten (keine neue Berechnung, nur
  zusaetzlich exportiert).

**Verifikation:** synthetischer Test reproduziert alle 9 echten Nacht-Werte
(Retail-Konsens 51-70%, CRV/SL-Kombinationen BTC/XLM) sowie einen echten
End-to-End-Aufruf von `post_check_hebel()` mit einem BTC-aehnlichen
Szenario - alle Ergebnisse decken sich mit der Handanalyse.

## Nachtrag (2026-07-22): Ueberholt-Erkennung repariert - Mindestbeobachtung + Zonen-Reaffirmation (Hebel+Spot)

Ausloeser: Nutzer-Frage nach der ersten inhaltlichen BTC-Signal-Review "so
wie ich es verstehe funktioniert das aktuelle System auf Glueck bzw.
Zufall?" - konkret ausgeloest durch die Beobachtung "es kommen genuegend
LONG-Signale rein, aber es gibt kaum echte Ergebnisse (Take-Profit/
Stop-Loss)".

**Root Cause:** Die Ueberholt-Erkennung (siehe Abschnitt 7, Punkt 6 oben,
2026-07-16/07-19) markierte ein offenes Signal sofort als ueberholt, sobald
IRGENDEINE neuere Nicht-HALTEN-Aktion fuer denselben Schluessel existierte -
unabhaengig vom Alter und unabhaengig davon, ob die neue These inhaltlich
ueberhaupt etwas anderes sagte (z. B. ein erneutes ERÖFFNEN mit praktisch
identischen Entry-/Stop-/Take-Profit-Zonen). Da das SLA-reservierte
Screening (Nachtrag 2026-07-21 oben) Hebel-Kandidaten alle ~3,5-7h und Spot
alle 8-15h neu bewertet - weit unter der Zeit, die eine 10-30% entfernte
Zielzone realistischerweise braucht -, verschwand die grosse Mehrheit der
Signale spurlos als "ueberholt", bevor der Kurs eine faire Chance hatte.
Die "historische Trefferquote" (n=5 fuer Hebel) war dadurch nicht nur
klein, sondern strukturell survivorship-verzerrt.

**Fix - zwei zusaetzliche Gates vor einer Ueberholung** (nur fuer den
"gleiche Richtung/erneute These"-Fall - eine echte Gegenrichtung bei Spot,
VERKAUFEN/TAUSCHEN nach KAUFEN, ueberholt weiterhin SOFORT, unveraendert
seit 2026-07-16):
1. **Mindestbeobachtung:** ein Signal darf erst ueberholt werden, nachdem
   seit seiner Erstellung mindestens eine Mindestzeit vergangen ist -
   abgeleitet aus `halte_kriterium_bucket` (`backward_tracking.
   mindestbeobachtung_tage_bucket`: kurz=2/mittel=5/lang=10 Tage, deutlich
   unter den bestehenden Abgelaufen-Schwellen 14/45/120). Bei Hebel
   zusaetzlich ein praeziserer Override ueber `trade_thesis_typ`:
   `einmal_trade` (kurzlebige Squeeze-Gegenbewegung) nutzt eine kuerzere
   Stunden-Schwelle (`hebel_mindestbeobachtung_stunden_einmal_trade`, 18h)
   statt der Tage-Bucket-Logik.
2. **Zonen-Reaffirmation:** liegen Entry-/Stop-Loss-/Take-Profit-
   Mittelwert des neuen Signals alle innerhalb einer relativen Toleranz
   (`zonen_reaffirmation_toleranz_relativ`, 3%) um die Werte des offenen
   Signals, gilt das als reine Bestaetigung derselben These, keine neue
   Information - keine Ueberholung. Konservativ: fehlt einer der drei
   Werte bei einem der beiden Signale, gilt das NICHT als Reaffirmation.

Beide Gates muessen die Ueberholung ERLAUBEN (Mindestbeobachtung erreicht
UND keine Zonen-Reaffirmation), sonst bleibt das Signal offen. Implementiert
in `agent/krypto/backward_tracking.py`/`hebel_backward_tracking.py::
_is_superseded()`, neue Config-Schluessel unter `backward_tracking:`.

**Backtest VOR Live-Umstellung** (gleicher Standard wie beim
Budget-Allocator-SLA-Fix, Nachtrag 2026-07-21 oben): neues Skript
`backtest_ueberholt_erkennung.py` spielte die beiden neuen Gates gegen ALLE
historisch echt "ueberholten" Hebel-/Spot-Signale nach (Rohdaten aus
`extract_notebook_diagnose.py`, neu ergaenzte Preishistorie-Sektion) -
Ergebnis: **24 von 27 (89%) historisch ueberholten Hebel-Signalen waeren
gerettet worden** (weiter offen geblieben statt zu verschwinden), darunter
mind. 1 Take-Profit- und 3 Stop-Loss-Treffer, die die historische
Trefferquote von n=5 auf n=9 erweitert haetten. Bei Spot (nur 2 historische
Faelle) blieb die echte Gegenrichtung (KAS) korrekt sofort ueberholt, der
zweite Fall (CAT) wurde gerettet. Ein besonders anschauliches Beispiel:
VIRTUAL LONG lief vom 16.07. bis 21.07. (5 Tage) als praktisch dieselbe
These durchgehend weiter, wurde aber unter der alten Regel 8-mal
hintereinander als "ueberholt" markiert.

**Verifikation:** synthetischer Test gegen die ECHTEN Produktivfunktionen
(nicht nur die Backtest-Kopien) reproduziert die zentralen Faelle (BTC-
artig gerettet, VIRTUAL-artig weiterhin ueberholt, KAS `einmal_trade`-
Override, Spot-Gegenrichtung, HALTEN-Regression) sowie ein echter
End-to-End-Lauf von `run_backward_tracking()`/`run_hebel_backward_
tracking()` gegen eine Kopie der Desktop-DB.

## Nachtrag (2026-07-22): Zwei weitere echte Funde aus einem LINK-Hebel-Signal (Antizyklisch-Regelverstoss + Funding-Rate-Rohfloat)

Ausloeser: Nutzer teilte einen echten LINK LONG ERÖFFNEN-Vorschlag (16:09
Uhr, Mistral) zur fachlichen Begutachtung. Zwei zusaetzliche, unabhaengige
Funde neben der eigentlichen inhaltlichen Bewertung (fuenf ▼-Warnsignale
gegen nur ein ▲, u.a. Bear-Forecast 50% > Bull-Forecast 25% trotz LONG-
Empfehlung, Regime-Konflikt, niedrige Konfidenz 50%):

**1. Antizyklisch-Regelverstoss trotz bestehender Regel (Regel 8,
`hebel_analyst.py`):** Top-Grund #5 des Signals lautete "Long-Konten-Anteil
von 63,5% zeigt eine moderate Positionierung, was Raum für eine Erholung
lässt" - als Stuetze fuer die eigene LONG-Empfehlung formuliert, obwohl
63,5% bereits eine (nicht-extreme) Mehrheit IN DERSELBEN Richtung ist. Die
bestehende Regel 8 verbietet das explizit fuer EXTREME Retail-Mehrheiten -
ein frueheres Signal desselben Tages (02:49 Uhr, HALTEN) formulierte
denselben Fakt korrekt neutral ("zeigt keine extreme Positionierung"),
zeigt also, dass die Regel grundsaetzlich befolgt werden KANN, nur nicht
zuverlaessig wird. Fix: Regel 8 um ein konkretes Gegenbeispiel ergaenzt,
das explizit auch den MODERATEN (nicht-extremen), gleichgerichteten Fall
verbietet - "noch nicht extrem, also ist noch Luft nach oben" als
derselbe Fehler nur anders formuliert benannt. Reine Prompt-Verschaerfung
(kein deterministischer Filter moeglich/sinnvoll fuer freien Fliesstext,
anders als bei den folgenden zwei Punkten) - die bereits bestehende
deterministische Retail-Konsens-Bewertung in Abschnitt 3 bleibt die
verlaessliche Quelle, unabhaengig davon, was das LLM im freien Text
formuliert.

**2. Funding-Rate als unformatierter Rohfloat im Risiken-Text:** "Laufende
Finanzierungsgebühr bei längerer Haltedauer, aktuell bei
2.624963888888792e-06." - der rohe Python-Float wurde unformatiert an das
LLM gereicht (`hebel_analyst.py`, `funding_rate_aktuell`) und von diesem
gemaess Regel 9 unveraendert in den Text kopiert. Fix in zwei Teilen:
- `hebel_analyst.py`: der LLM-Fakt heisst jetzt
  `funding_rate_aktuell_prozent_pro_stunde` und ist bereits als gerundeter
  Prozentwert formatiert (z.B. `0.00026` statt `2.624963888888792e-06`) -
  Regel 9 verlangt zusaetzlich explizit die Einheit "% pro Stunde" im Text.
- **Nutzer-Nachfrage:** macht eine reine Prozentzahl ohne Kontext ueberhaupt
  Sinn, oder waere ein EUR/Zeiteinheit-Betrag sinnvoller? Antwort: beides,
  nach demselben "Fakt zuerst, Wertung danach"-Prinzip wie Retail-Konsens/
  CRV - die Rate selbst MIT Zeiteinheit (Kraken veroeffentlicht Funding
  stuendlich, `rates[-24:]` in `hebel_screening.py` = 24h-Durchschnitt der
  Stundenrate) als Fakt, plus ein neuer deterministischer Risikofaktor
  "Funding-Kosten" (`hebel_risk_gate.py::compute_risikofaktoren_hebel()`)
  mit einem konkreten USD/Tag-Betrag bei der TATSAECHLICHEN Positionsgroesse
  (`positionsgroesse_usd * funding_rate_stunde * 24`, aus der bereits
  vorhandenen Positionsgroessen-Berechnung in `post_check_hebel()`) - klar
  benannt als Momentaufnahme ("schwankt mit dem Satz, keine feste
  Kostenzusage"), nicht als LLM-Rechnung (LLMs sind kein verlaesslicher
  Taschenrechner). Neue Schwelle
  `risiko.hebel.funding_rate_hoch_schwelle_relativ_stunde` (0.0001, identisch
  zum bereits kalibrierten `hebel_screening.kontra.funding_rate_extrem_
  schwelle`, aber als eigener Schluessel fuer ein unabhaengiges Konzept)
  faerbt den Faktor ab dieser Rate "negativ" statt "neutral".

**Verifikation:** synthetischer Test bestaetigt: (a) niemals mehr
wissenschaftliche Notation im Text, (b) korrekte USD/Tag-Berechnung fuer
den echten Screenshot-Wert (≈0,13 USD/Tag bei einer Beispiel-Positionsgroesse),
(c) Schwellenwert-Verhalten (neutral/negativ), (d) kein Faktor ohne
vorhandenen Fakt, (e) echter End-to-End-Lauf von `post_check_hebel()` mit
einem LINK-aehnlichen Szenario, (f) Regressionstest der vorherigen Retail-
Konsens-/CRV-Fixes weiterhin gruen.

## Nachtrag (2026-07-22): Alt-Coin-Marktphase fehlte im Hebel-Regelwerk (echter VIRTUAL-Fund)

Ausloeser: ein weiteres echtes Signal (VIRTUAL LONG ERÖFFNEN, Mistral,
15:40 Uhr) zur fachlichen Begutachtung. Gegenargument des LLM nannte
korrekt "Regime (baer_flucht)" als staerksten Einwand - Nachforschung
ergab: `baer_flucht` ist KEIN Wert des einfachen Baer/Bulle-Regimes
(`regime.regime`), sondern ein separates Label der BTC-Dominanz-Matrix
(`agent/krypto/regime.py::BTC_MATRIX`), das explizit dokumentiert "Alt-
Ausbrueche meist Fallen - erhoehte Vorsicht bei Alt-Kaufsignalen". VIRTUAL
ist ein Alt-Coin, also genau der Fall, fuer den diese Warnung gedacht ist.

**Fund:** Die Spot-Pipeline (`analyst.py` Regel 8) kennt diese Regel
bereits seit laengerem UND uebergibt sowohl das Label (`btc_matrix`) als
auch die erklaerende Beschreibung (`btc_matrix_hinweis`) als Fakt. Die
Hebel-Pipeline (`hebel_analyst.py`) uebergab bisher NUR das nackte Label
ohne Erklaerung und hatte KEINE SYSTEM_PROMPT-Regel dazu - das LLM hat den
Zusammenhang diesmal aus eigenem Wissen richtig hergestellt, aber ohne
System-Vorgabe (gleiches Muster wie beim Antizyklisch-Regel-8-Fund: "hat
diesmal zufaellig richtig geraten" ist keine verlaessliche Grundlage,
gerade fuer die risikoreichere Hebel-Pipeline).

**Fix:**
- `hebel_analyst.py`: `asset.rolle` und `btc_matrix_hinweis` (=
  `regime_result.btc_matrix_beschreibung`) neu ins Fakten-JSON aufgenommen
  (identische Feldnamen wie bei Spot). Neue Regel 16 im SYSTEM_PROMPT,
  wortgleich zum Spot-Muster: bei `asset.rolle != "core"` (nicht BTC/ETH)
  UND `richtung == LONG` soll bei `btc_season`/`baer_flucht` erhoehte
  Skepsis gegenueber Alt-Kaufsignalen gelten, bei `altseason` normal/hoeher
  gewichtet werden.
- `hebel_risk_gate.py`: neuer deterministischer Risikofaktor "Alt-Coin-
  Marktphase" (`compute_risikofaktoren_hebel()`) - erscheint nur bei
  `richtung == LONG`, `ist_core_asset == False` und
  `btc_matrix_state in ("btc_season", "baer_flucht")`. Text wird bewusst
  1:1 aus `btc_matrix_hinweis` uebernommen (bereits ein vollstaendiger,
  verstaendlicher Satz aus `regime.py::BTC_MATRIX`) statt neu formuliert -
  eine Quelle der Wahrheit, kein driftender Zweittext, und direkt die vom
  Nutzer gewuenschte "sinnvolle Beschreibung fuer den User" ohne
  zusaetzliche Uebersetzungsarbeit.
- `hebel_pipeline.py`: `asset.rolle` an `post_check_hebel()` durchgereicht;
  `btc_matrix_state`/`btc_matrix_beschreibung` werden dort direkt aus dem
  bereits vorhandenen `regime_result` gelesen (kein zusaetzlicher
  Parameter noetig).

**Verifikation:** synthetischer Test bestaetigt: (a) Faktor erscheint fuer
Alt-Coin+LONG+`baer_flucht`/`btc_season` mit korrektem, unveraendertem
Hinweistext, (b) kein Faktor fuer BTC/ETH (`asset.rolle == "core"`), (c)
kein Faktor fuer SHORT (Regel betrifft nur Alt-Kaufsignale), (d) kein
Faktor bei `altseason`/`unklar_defensiv`/fehlendem Zustand, (e) echter
End-to-End-Lauf von `post_check_hebel()` mit einem VIRTUAL-aehnlichen
Szenario, (f) Regressionstest der Funding-Kosten-/Retail-Konsens-/CRV-Fixes
weiterhin gruen.

## Nachtrag (2026-07-22): Abschnitt 3 (Konklusion) verschmolz in Outlook zu einem Fliesstext

Nutzer-Fund (Screenshot derselben VIRTUAL-E-Mail): die Legende
"(▲ unterstützt die Empfehlung · ● neutral · ▼ Warnsignal/Risiko)" und der
erste Risikofaktor erschienen in Outlook Web als EIN zusammenhaengender
Fliesstext statt als zwei Zeilen - Outlook zeigte dabei den Hinweis "Wir
haben zusätzliche Zeilenumbrüche aus dieser Nachricht entfernt". Root
Cause: `scheduler/background.py::_formatiere_risikofaktoren()` trennte
Risikofaktoren-Zeilen bisher nur mit einfachem `\n`, und auch der Uebergang
Legende -> erster Faktor nutzte nur ein einfaches `\n` - Outlook Web
entfernt offenbar genau solche einzelnen Zeilenumbrueche beim Anzeigen
(vermutlich ein Reflow-Mechanismus, der einzelne "\n" als reinen
Wortumbruch interpretiert). Alle ANDEREN Abschnitte der E-Mail trennen
Bloecke bereits durchgehend mit `\n\n` (echte Leerzeile) und rendern
deshalb zuverlaessig als eigene Absaetze - genau dieses Muster fehlte hier.

**Fix:** `_formatiere_risikofaktoren()` verbindet die einzelnen
Risikofaktor-Zeilen jetzt mit `"\n\n"` statt `"\n"`, und alle drei
Aufrufstellen (Spot-, Hebel-, Multi-Asset-E-Mail) trennen die Legende vom
ersten Faktor ebenfalls mit `"\n\n"` statt `"\n"` - konsistent mit dem
bereits etablierten Absatz-Trenn-Muster der uebrigen E-Mail-Abschnitte.
Rein die E-Mail-Formatierung betroffen - `ui/formatting.py::
format_risikofaktoren_lines()` fuer die App-Anzeige (Tkinter, keine
Reflow-Problematik) blieb unveraendert.

**Verifikation:** synthetischer Test bestaetigt echte Leerzeilen zwischen
allen Risikofaktor-Zeilen sowie zwischen Legende und erstem Faktor;
bestehender Regressionstest der Risikofaktor-Symbole weiterhin gruen.

## Nachtrag (2026-07-22): Zwei Hedge-Funde - Bitpanda-Override im E-Mail-Gate + Batch-Budget-Bewusstsein

Ausloeser: echte Hedge-Signale (DBPK/3QSS, beide NACHKAUFEN im selben Lauf
07:01) aus dem Signale-Tab. Nutzer fragte, warum keine E-Mail dafuer
ankam, und bat um eine fachliche Bewertung der beiden Empfehlungen.

**Fund 1: Bitpanda-Override wurde vom E-Mail-Gate ignoriert.** Erste
(falsche) Vermutung: DBPK/3QSS seien schlicht nicht bei Bitpanda gelistet -
vom Nutzer korrigiert unter Verweis auf einen bereits bestehenden
Mechanismus. Tatsaechlicher Stand (siehe `asset_bitpanda_override`-
Tabellendocstring, 2026-07-20, Commit `1ae800c`): der oeffentliche
`/v3/assets`-Endpunkt deckt Bitpandas "Bitpanda Stocks"-Fractional-ETF/ETC-
Produktlinie nachweislich NICHT vollstaendig ab - echte Bitpanda-App-
Screenshots hatten das damals bewiesen (DBPK/ISOC dort real gehalten,
aktive Kaufen/Verkaufen-Buttons). Deshalb existiert der manuelle
"Bitpanda-Override umschalten"-Button im Watchlist-Tab. Alle 4 Spot-
family-Pipelines (`agent/krypto|aktien|rohstoff|themen_etf/pipeline.py`)
fragen `db.get_bitpanda_gelistet_override()` bereits nach einem negativen
Live-Check ab - `scheduler/background.py::_ist_email_relevantes_asset()`
(das E-Mail-Gate) war die einzige Stelle, die den Override noch NICHT
respektierte, obwohl fuer DBPK/3QSS bereits ein bestaetigter Override-
Eintrag existierte.

**Fix 1:** `_ist_email_relevantes_asset()` bekommt einen optionalen
`conn_factory`-Parameter (Standard `None`, rueckwaertskompatibel) - nach
einem negativen Live-Check wird jetzt zusaetzlich der Override abgefragt,
identisches Muster wie die 4 Pipelines. `conn_factory` wird an allen 3
Aufrufstellen (`_notify_spot_signal()`, `_notify_hebel_signal()` [hatte es
bereits fuer die Wartezeit-Anzeige], `_notify_multi_asset_signal()`)
durchgereicht - beide Jobs (`hebel_screening_job()`, `multi_asset_batch_
job()`) haben `conn_factory` bereits im Scope.

**Fund 2: zwei Hedge-Instrumente im selben Batch-Lauf kannten sich
nicht.** `agent/hedge/pipeline.py::_compute_portfolio_exposure()` liest
`verbleibendes_hedge_budget_usd` unabhaengig aus dem tatsaechlichen
DB-Bestand - da nichts real ausgefuehrt wird (rein advisory), sehen zwei im
selben Lauf verarbeitete Hedge-Kandidaten (hier: 3QSS dann DBPK)
denselben, noch unveraenderten Ausgangsbestand. Setzt der Nutzer beide
Vorschlaege manuell um, kann die tatsaechliche Gesamt-Abdeckung ueber
`ziel_hedge_abdeckung_max_prozent` hinausschiessen, ohne dass eine der
beiden Empfehlungen davon wissen konnte.

**Fix 2 (Nutzer-Entscheidung: strukturelle Loesung statt reinem Hinweis):**
- `_compute_portfolio_exposure()` bekommt einen neuen Parameter
  `bereits_vorgeschlagen_effektiv_usd` (Standard 0.0, kein
  Verhaltensunterschied bei Einzelaufruf) - wird zusaetzlich von der
  aktuellen Hedge-Abdeckung abgezogen, BEVOR das verbleibende Budget durch
  den `hebel_faktor` DIESES Instruments geteilt wird. Der `hinweis`-Text
  erklaert den Abzug explizit, wenn er greift.
- `generate_signal()` reicht den (keyword-only) Parameter
  `bereits_vorgeschlagen_effektiv_usd` durch.
- `agent/multi_asset_batch.py::run_multi_asset_batch()`: neuer lokaler
  Akkumulator `hedge_effektiv_vorgeschlagen_usd` (nur fuer Hedge-Symbole
  relevant, bleibt bei 0.0 fuer Aktien/Rohstoffe/Themen-ETF - kein
  zusaetzliches kwarg fuer diese Pipelines, kein Regressionsrisiko). Nach
  jedem erfolgreichen KAUFEN/NACHKAUFEN-Signal eines Hedge-Instruments wird
  `position_size_usd * hebel_faktor` (leverage-adjustiert) zum Akkumulator
  addiert, bevor der naechste Hedge-Kandidat im selben Lauf verarbeitet
  wird - macht den Deckel ueber den ganzen Batch hinweg real konsistent.

**Verifikation:** synthetischer Test bestaetigt (a) E-Mail-Gate respektiert
den Override jetzt (mit `conn_factory`), bleibt ohne `conn_factory`
rueckwaertskompatibel beim alten (strengeren) Verhalten; (b)
`_compute_portfolio_exposure()` reduziert das verbleibende Budget korrekt
um den uebergebenen Wert, deckelt nie unter 0; (c) echter Integrationstest
von `run_multi_asset_batch()` mit zwei gestubbten Hedge-Signalen bestaetigt,
dass das ZWEITE Instrument im Lauf tatsaechlich die vom ERSTEN vorgeschlagene,
leverage-adjustierte Summe als Ausgangswert erhaelt.

**Fachliche Bewertung der beiden echten Signale (zur Nutzer-Frage):** beide
Empfehlungen entsprechen dem Hedge-Regelwerk (`agent/hedge/analyst.py`) -
korrekte `exposure/makro/risiko/timing`-Kategorien (Regel 10, NICHT die
Spot-Taxonomie), Decay-Warnung explizit genannt (Regel 4), rein
exposure-/regimebasierte Begruendung (Regel 3), `aktien_baermarkt.aktiv`
korrekt als noch nicht aktiv benannt, aber `regime=='baer'` allein reicht
laut der ODER-Verknuepfung in Regel 3. Die fehlenden strukturierten
Risikofaktoren ("Keine strukturierten Risikofaktoren verfügbar") in
Abschnitt 3 sind KEIN Bug, sondern bewusste Architektur (Hedge durchlaeuft
laut Modul-Docstring absichtlich NICHT `risk_gate.pre_check()/post_check()`
- CRV-Pflicht etc. passen nicht auf eine Absicherungsposition).
