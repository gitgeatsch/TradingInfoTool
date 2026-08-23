# Gesamtplan — Granularität je Asset: was wo gemessen wird, und in welcher Reihenfolge

*Nutzerfrage 23.08.: „kannst du mir deinen Gesamtplan je Asset und Granularität
vorlegen? Vor allem in unserem Hauptbereich Krypto fehlt mir durch die
unterschiedlichen und komplexen Zusammenhänge — mit Spot, Akkumulation, Hebel
etc. — noch, ob und wie wir mit der Abgrenzung BTC als eigene virtuelle Klasse
in Krypto sowie Highcaps, Midcaps, Smallcaps umgehen. Soll das einfließen oder
erst später — was sagt der Experte?"*

> **Alles hier ist gemessen oder am Code gelesen.** Wo ich als Fachexperte
> eine Empfehlung abgebe, steht **Empfehlung** davor.

---

## 0. Die kurze Antwort auf die BTC-/Caps-Frage

| | |
|---|---|
| **Fließt es ein?** | **Ja — aber als Schichtung, nicht als Klasse, und erst auf Stufe 3** |
| **Warum nicht jetzt** | ⚠️ **Der Vorsprung ist keine Eigenschaft des Symbols.** Gemessen: Rangkorrelation zwischen aufeinanderfolgenden Fenstern **+0,019** — es gibt nichts zu ranggeordnen |
| **Was BTC sofort wird** | **Bezugsgröße**, nicht Klasse — für Krypto ist er der Maßstab, gegen den relativ gemessen wird |
| **Der eine echte Befund dazu** | BTC hat den **kleinsten** Vorsprung aller Krypto-Gruppen (+0,052 gegen +0,153 mittel) — er verhält sich wie ein Aktienindex, nicht wie sein Markt |

---

## 1. Der Messbefund, der den Plan bestimmt

`messe_tagewahl_je_symbol.py`, 41 Symbole, Jahresfenster, Vorsprung gegen den
**quotengleichen** Zufall:

| Gruppe | Symbole | Fenster | UNTER_SMA | RUECKGANG |
|---|---:|---:|---|---|
| **mittel** (1–10 Mrd) | 8 | 29 | **+0,1531** (90 % pos.) | **+0,1027** (79 %) |
| **gross** (≥ 10 Mrd) | 3 | 20 | +0,1123 (90 %) | +0,1140 (86 %) |
| **klein** (< 1 Mrd) | 21 | 43 | +0,0819 (86 %) | +0,0314 (60 %) |
| **btc** | 1 | 7 | **+0,0517** (86 %) | +0,0306 (83 %) |
| etf | 4 | 22 | +0,0142 (91 %) | +0,0275 (**100 %**) |
| aktien | 2 | 8 | +0,0266 (75 %) | +0,0310 (62 %) |

**Drei Dinge stehen fest:**

1. ✔ **Der Befund hält auch bei Jahresfenstern.** Er war keine Eigenschaft der
   Zweijahresfenster — das ist eine bestandene Robustheitsprobe, keine
   Wiederholung.
2. ⚠️ **Er ist NICHT symbolspezifisch.** Spearman zwischen Fenster *t* und
   *t+1*: **+0,019** (UNTER_SMA, 93 Paare) und **−0,147** (RUECKGANG, 79
   Paare). Das gleiche Vorzeichen tritt in 81 % der Paare auf — ein reiner
   Basisratenwurf ergäbe **76 %**. **Die Höhe des Vorsprungs im nächsten
   Fenster ist nicht vorhersagbar.**
3. ⚠️ **Die Kapitalisierungsstufen unterscheiden sich — aber verzerrt.** Die
   Kapitalisierung ist die **von heute**, und die kleinen Werte, die gestorben
   sind, fehlen. **`klein +0,0819` ist eine Obergrenze, kein Messwert.**

> **Daraus folgt der Kern des Plans: Der Vorteil gehört der REGEL, nicht dem
> WERT.** Er sagt *wie* gekauft wird, nicht *was*. Eine Auswahl unter Symbolen
> lässt sich darauf **heute nicht** gründen.

---

## 2. Die sechs Granularitätsebenen — mit Belegstand je Ebene

| # | Ebene | Beispiel | Belegstand | Verwendung |
|---|---|---|---|---|
| **G1** | **Anlageklasse** | krypto · aktien · etf · rohstoffe · absicherung | ✔ **gemessen**: Trichterfaktor 0,79 / 0,91 / 1,18, stabil über zwölffachen Horizont; Tagewahl in allen drei positiv | **harte Trennung** — eigene Faktoren, eigene Kosten |
| **G2** | **Vorteilsquelle** | Rückkehr zum Mittel · Drift · Information · Struktur | ✔ **eine gemessen** (Rückkehr zum Mittel, 23.08.); Drift gemessen und zu klein für die Kosten | **die Entscheidung** — bestimmt Kriterien und Erfolgsmaß |
| **G3** | **Instrument** | spot · hebel · absicherung | ✔ **Ergebnis der Geometrie** (`verlustanteil / stop_rel`), keine Kategorie | folgt aus G2 + Risiko |
| **G4** | **Marktphase** | steigend · fallend | ✔ gemessen, **kippt die Rangfolge vollständig** (91 % ↔ 21 %) | ⚠️ **nur Schichtung** — das Etikett ist beschreibend, vorab nicht bekannt |
| **G5** | **Kapitalisierungsstufe** | btc · gross · mittel · klein | ⚠️ **gemessen, aber stichtags- und überlebensverzerrt** | **später**, als Schichtung |
| **G6** | **Einzelsymbol** | SUI, ALGO, … | ⚠️ **nicht ranggeeignet** (Spearman +0,02) | **heute nicht** |

> **Empfehlung: G1 und G2 tragen den Bau. G4 und G5 sind Schichtungen für die
> Auswertung. G6 bleibt draußen, bis eine Größe gefunden ist, die bleibt.**

---

## 3. Je Anlageklasse — was heute geht und was fehlt

| Klasse | Symbole | Historie | was misst | ⚠️ was fehlt |
|---|---:|---|---|---|
| **krypto** | 41 | **9 Jahre** (seit 19.08. nachgeladen) | alles: Tagewahl, H, Trichter, Drift, Marken, Terminmarkt | Hebel ist faktisch abgeschaltet (Median 1,10); Marktscan nutzt das Potentialmaß noch nicht |
| **etf** | 4 | bis 2008 | Tagewahl **stabilster Befund** (RUECKGANG 100 % positiv) | ⚠️ nur 4 Werte — kein eigenes Regelwerk begründbar |
| **aktien** | **2** | bis 2016 | wenig | ⚠️ **n = 2 ist keine Klasse.** Der Aktienmarkt hat die längste Historie und die dichteste Literatur — und wir nutzen zwei Titel |
| **rohstoffe** | 3 | über interne Futures bis 2000 | Trichter | keine eigene Vorteilsquelle geprüft |
| **absicherung** | — | — | folgt dem Portfolio | hier ist kein Einstiegsvorteil zu suchen — das ist der Zweck |

> **Empfehlung, und sie ist billig:** die **Aktien- und ETF-Liste verbreitern**,
> bevor dort Regeln gebaut werden. Kein Modellaufruf, kein Kontingent — nur
> Kursreihen. ⚠️ Ihr eigener Punkt trifft genau hier: *„der Aktienmarkt
> existiert schon lange und es gibt mehr als genug verfügbare Information"* —
> **die Information ist da, unsere Stichprobe ist es nicht.**

---

## 4. Krypto im Einzelnen — Spot, Akkumulation, Hebel

**Die Verwirrung kommt daher, dass drei verschiedene Achsen einen Namen teilen.
Sortiert:**

| Achse | Werte | wer entscheidet | Beleg |
|---|---|---|---|
| **Vorteilsquelle** (G2) | Rückkehr zum Mittel · Drift | ⚠️ **heute niemand** — wird nie zugewiesen | Rückkehr zum Mittel gemessen 23.08. |
| **Ausführungsform** | einstieg · akkumulation · swing | `handelsauftrag`, in Produktion fest auf `einstieg` | Reparaturliste D1 |
| **Instrument** | spot · hebel | fällt aus der Rechnung an | `verlustanteil / stop_rel` |

⚠️ **Und sie hängen zusammen, aber nicht eins zu eins:**

- **Rückkehr zum Mittel** passt zur **Akkumulation** (kein einzelner Zeitpunkt,
  kein Stop) — und genau dort ist der Vorsprung gemessen.
- **Drift** passt zum **Einstieg mit Stop** — und dort ist er **zu klein für
  die Kosten** (+1,01 % gegen 3 %).
- **Hebel** ist mit Akkumulation ausgeschlossen (`ERLAUBTE_PAARE`), weil die
  Finanzierung jeden Tag kostet.

> ⚠️ **Damit steht die unbequeme Folgerung im Raum:** die einzige gemessene
> Vorteilsquelle liegt auf der Ausführungsform, die **die Kette heute nicht
> trägt** (Machbarkeitsprüfung S-1), und **schließt den Hebel aus**.

---

## 5. Die Reihenfolge — vier Stufen

### Stufe 1 — die Grundlage tragfähig machen *(kein Modellaufruf)*

| | was | warum |
|---|---|---|
| 1.1 | **Kette für `akkumulation`** (S-1) | sonst bekommt die einzige gemessene Vorteilsquelle still einen ATR-Stop |
| 1.2 | **Feld `vorteilsquelle` speichern** (S-2) | ohne Speicherung kein Messen je Quelle |
| 1.3 | **Aktien-/ETF-Liste verbreitern** | zwei Titel sind keine Klasse |

### Stufe 2 — die Quelle in die Kette *(hier beginnt S1)*

| | was |
|---|---|
| 2.1 | Rolle BC bekommt die **Vorteilsquelle als Auftrag**, wie heute Instrument und Strategie |
| 2.2 | Die Kriterien je Quelle in den Faktensatz — **Bedingung, keine Wertung** (R-T3) |
| 2.3 | Erfolgsmaß je Quelle **getrennt**: Rückkehr zum Mittel misst den Durchschnittspreis, Drift die Zielerreichung |

### Stufe 3 — Schichtung, hier kommen BTC und die Caps

| | was | Vorbedingung |
|---|---|---|
| 3.1 | **BTC als Bezugsgröße** für Krypto (relativer Kurs, relative Stärke) | sofort möglich |
| 3.2 | Auswertung **geschichtet** nach Kapitalisierungsstufe | ⚠️ braucht **historische** Kapitalisierung, nicht die von heute |
| 3.3 | Auswertung geschichtet nach Marktphase | läuft bereits |

### Stufe 4 — Auswahl *(nur wenn Stufe 3 etwas Bleibendes findet)*

⚠️ **Diese Stufe ist heute nicht begründbar.** Der gemessene Vorsprung ist
nicht symbolspezifisch. Eine Rangauswahl braucht eine Größe mit
Beständigkeit — die ist noch nicht gefunden.

---

## 6. ⚠️ Was ich als Fachexperte ausdrücklich NICHT empfehle

| | warum |
|---|---|
| **BTC jetzt als eigene Assetklasse führen** | Er unterscheidet sich messbar (+0,052 gegen +0,153) — aber **n = 1 Symbol, 7 Fenster**. Eine eigene Klasse bedeutet eigene Faktoren, eigene Kosten, eigene Regeln. Das ist zu viel Bau für einen Unterschied, der auch Rauschen sein kann |
| **Cap-Stufen jetzt in die Entscheidung** | Die Zahlen sind stichtags- und überlebensverzerrt. Wer heute nach `klein` filtert, filtert nach den Kleinen, **die überlebt haben** |
| **Nach Symbolen ranggeordnet auswählen** | gemessen widerlegt: Spearman +0,019 |
| **Vier Ebenen gleichzeitig eröffnen** | Der eigene Suchpreis: 300 Zellen = **+20,5 Punkte** Hürde, eine vorab benannte = **+10,2**. G1 × G2 × G4 × G5 sind schon 120 Zellen |

---

## 7. Vorgemerkt, eigenes Thema

*Nutzerhinweis 23.08.: „das Potential sollte auch beim Krypto-Marktscan zum
Einsatz kommen, aber das ist ein eigenes Thema."*

**Aufgenommen.** Der Marktscan (`agent/krypto/marktscan.py`,
`marktscan_candidates` mit 468 Zeilen) wählt heute nach anderen Merkmalen aus.
Das Potentialmaß ist dort anwendbar, weil es **keinen Stop und kein Ziel
braucht** — genau das, was ein Scan über unbekannte Werte nicht hat.
**Nicht in dieser Reihe, aber nicht vergessen.**
