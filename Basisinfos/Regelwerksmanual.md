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
| RM-4 | Cash-Reserve-Minimum | **10 %** | AKTIV — Unterschreitung blockiert weitere Käufe |
| RM-5 | Pflicht-Stop-Loss | jede Position braucht einen | AKTIV, unantastbar (kein Override erlaubt) |
| RM-6 | Trailing-Stop | erlaubt | Als Option vorhanden, keine automatische Durchsetzung |
| RM-7 | Drawdown-Notbremse | — | **OFFEN**, siehe Z-3 |
| RM-8/RM-9 | Risiko-Score je Asset (aus Volatilität, Liquidität, BTC-Korrelation, Projektreife) → höheres Risiko = kleinere erlaubte Position | — | **OFFEN**, noch nicht gebaut |
| RM-10/RM-11 | Hebel: nur Long, max. **3x**, Liquidationspreis muss ausgewiesen werden | konfiguriert | **DEAKTIVIERT** (Strategie S-6 aus) — eigenes, noch zu führendes Thema |

**Unantastbar (RG-6):** Weder Nutzer noch KI dürfen RM-1, RM-5 oder Z-3 per Override
abschalten — das sind die harten Leitplanken, die auch eine künftige KI-gestützte
Anpassung nicht in Frage stellen darf, ohne dass du das bewusst und explizit änderst.

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

## 6. Strategie-Katalog (S-1 bis S-6)

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

## 7. Wo diese Regeln im Code stehen (für Nachvollziehbarkeit)

- `Basisinfos/config.yaml` — alle einstellbaren Zahlen (Abschnitte `risiko`, `regime`, `antizyklisch`, `strategien`)
- `agent/krypto/risk_gate.py` — harte Durchsetzung von RM-1/2/4/5, Z-2 (CRV), Positionsgrößen-Clamp, Bitpanda-Veto
- `agent/krypto/regime.py` — RG-1 bis RG-3 (Regime-Bestimmung)
- `agent/krypto/anticyclic.py` — vereinfachte AZ-1-Heuristik
- `agent/krypto/analyst.py` — SYSTEM_PROMPT (alle Regeln, die der KI als Anweisung mitgegeben werden) + Schema-Validierung
- `agent/krypto/pipeline.py` — Reihenfolge R-5.0 bis R-5.11 (Orchestrierung)

---

## 8. Offene / vorläufige Werte — die naheliegendsten Kandidaten für spätere Anpassung

Diese Werte sind laut Spezifikation ausdrücklich **vorläufig** (`[OFFEN]`-markiert) und
noch nicht durch echte Ergebnisse verifiziert — sie sind der wahrscheinlichste
Startpunkt, sobald Backward-Tracking/Outcome-Daten vorliegen:

- RM-2 Core-Allokations-Limit (35 % für BTC/ETH) — nachträglich erhöht, weil die reale
  BTC-Allokation das alte 25%-Limit überschritt; "BTC hat den Lead"-Frage insgesamt
  noch nicht grundsätzlich besprochen.
- RM-4 Cash-Reserve-Minimum (10 %)
- Small-Cap-Budget je Regime (0/4/8/12/15 %)
- Mindest-Konfidenz je Regime (85/75/65/60/60 %)
- Die vier Gewichte je Regime (Technik/Fundamental/Momentum/Makro)
- RG-4 Makro-Multiplikator (`risikoappetit_faktor`, aktuell fix auf 1,0)
- RM-10 max. Hebel (3x, aktuell ohnehin deaktiviert)
