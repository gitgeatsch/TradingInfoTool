# Voranalyse A — Positionsführung als erste Optimierung der REGEL0 (ENTWURF 01.10.2026, zur Abstimmung)

**Auftrag:** Nutzer 30.09. (E-33): *„A und B sind Optionen, die ohnehin sinnvoll sind"*, und 01.10.: *„wie können wir in der Zwischenzeit
weitermachen bzw. parallel du eigenständig Punkte abarbeiten kannst"*. ⚠️ **Das ist nur ein Entwurf.** Es wird nichts gemessen und nichts gebaut,
bevor du Ja sagst.
**Vorher:** REGEL0 festgeschrieben (E-36), Erfolgsmessung 24 h ohne Ziel und ohne Stop. 2.690: Ein festes Ziel kappt die Gewinner. 2.693/2.694: Die Wucht
bringt +5,9 % Hoch binnen 24 h, das bis zum Ausstieg wieder verloren geht. 2.700: Auf deiner Liste ist die REGEL0 schon positiv.

> **Urteil in einer Zeile:** Wir lassen den **Einstieg unverändert** (REGEL0) und messen nur den **Ausstieg**, einen nachgezogenen
> Stop in eigener ATR. Die Frage: Holt er einen Teil des Hochs, das heute nach 24 h wieder weg ist?

---

## 0. Ziel, Stand, Test oder Betrieb

| | |
|---|---|
| **Ziel** | den **Vorteil je Handel** erhöhen, ohne das Signal anzufassen. Das greift S3 an (Rohvorteil unter den Kosten auf allen Assets) |
| **Stand** | Die REGEL0 hält 24 h ohne Stop. In der Wahl 2024 (2.690) war *ohne Ziel* besser als +3 %/+5 %, aber ein **Stop** wurde nie gemessen (bewusst, K6a: *der Stop gehört zur Positionsführung*) |
| **Test oder Betrieb** | Test, Ebene B (Erfolgsmessung). Die **Bewertung bleibt neutral** und unberührt, die Positionsführung ist Phase 5 (Nutzer 30.09.) |

---

## 1. Die Messung — Vorschlag

| | |
|---|---|
| Einstiege | **REGEL0**, fest: `kern48j_einstiege_<m>.csv` |
| Hebelstufe | REGEL0: ATR-Modell, Grenze 2 %. ⚠️ Die Liquidationsgefahr hängt an der **Haltedauer** H, und das Modell gibt es für H = 24 / 72 / 120 h |
| **Achse Stop** | nachgezogener Stop: Abstand **k × ATR** unter dem höchsten Markpreis-Hoch seit dem Einstieg, mit k ∈ {1,0; 1,5; 2,0; 3,0} |
| **Achse Haltedauer** | höchstens H ∈ {24, 72} h, dann Zeitausstieg |
| Referenzzelle | *ohne Stop, 24 h* = REGEL0. Sie muss **bitgleich** zur Referenz sein (R-R11) |
| Reihenfolge in einer Stunde | Liquidation vor Stop vor neuem Hoch, also vorsichtig: Ein neues Hoch derselben Stunde hebt den Stop erst ab der nächsten |
| Kosten | wie REGEL0. Der Stop-Ausstieg kostet dieselbe Gebühr, die Finanzierung läuft bis zum Ausstieg |
| **Wahl** | auf **2024** per Regel: größtes Kontowachstum, bei Gleichstand (< 1 % Endwert) die **einfachere** Zelle (ohne Stop vor mit Stop, dann größeres k, dann kürzeres H) |
| **Bestätigung** | einmal 2025–26 in 4 Mengen, Kriterien S1–S5 wie 2.690/2.694, dazu *besser als REGEL0* in ≥ 3/4 Mengen |
| Auskunft | dieselbe gewählte Zelle auf deiner **Hebel-Liste** (2.700) |

9 Zellen (4 × 2 + Referenz) auf 2024. Das ist wenig Mehrfachtesten, und die Bestätigung erfolgt einmal.

---

## 2. Prüfung und Gegenprüfung

| | |
|---|---|
| R-R11 | Die Referenzzelle trifft die REGEL0 (Hebelkonto, Rohvorteil, Handel) |
| Nullwelt | zeitverschobene Einstiege mit derselben Stop-Regel. Der Stop allein darf im Zufall nicht tragen |
| Zeitstabilität | 2025 und 2026 getrennt, Juli–Dezember 2025 |
| Spiegel | der Stop verändert die Verteilung. Ausgewiesen werden Gewinn- und Verlusthandel getrennt |
| Vorgriff | Der Stop nutzt nur Hochs **nach** dem Einstieg, stündlich |

---

## 3. ⚠️ Betriebsprüfung (E-35) — schon jetzt zu klären

| # | Frage | warum |
|---|---|---|
| A-B1 | Kann Bitpanda einen **nachgezogenen Stop** für Hebelpositionen, oder muss das System ihn stündlich nachführen? | Ohne das ist die Regel im Betrieb nicht ausführbar. Das ist eine **Nutzerfrage** |
| A-B2 | Stündliche Markpreise am Notebook live | Das ist dieselbe Datenanbindung wie für die REGEL0 (Schritt 7) |

---

## 4. Zur Abstimmung (später)

| # | Vorschlag |
|---|---|
| **A1** | Stop in ATR mit k ∈ {1,0; 1,5; 2,0; 3,0} × H ∈ {24, 72}, Referenz REGEL0 |
| **A2** | Wahl 2024 per Regel, einmal bestätigt, ≥ 3/4 Mengen und besser als REGEL0 |
| **A3** | Die Antwort zu A-B1 (Bitpanda) von dir, bevor A in den Betrieb geht |
