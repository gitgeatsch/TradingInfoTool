# Bilanz des Hebelneubaus — Stand 27.09.2026 abends

**Nutzerauftrag:** bilanzieren, bevor der nächste Zweig aufgemacht wird.

---

# 1. ⚠️ Zuerst das Arbeitsmuster, weil es die Bilanz erklärt

> **Nutzerkritik:** *„wie oft soll ich dich bitten, die Messungen zu
> prüfen — und immer wieder müssen wir bereits fertige Bereiche
> aufmachen … dann kommst du nicht mit einem Fehler um die Ecke, sondern
> das ganze System kippt."*

**Sie trifft. Fünfmal an einem Tag habe ich gemeldet, bevor ich fertig
geprüft hatte:**

| gemeldet | was die Prüfung **danach** ergab |
|---|---|
| „die Achse trägt" (2.626) | trägt nur **relativ zum Tag** |
| „die Stufung trägt" (2.632) | Weglassprobe **kippt** sie |
| „die Schwelle ist −1,65" (2.640) | aus **Ertrag** abgeleitet, abgelöst |
| „das Depot verliert" (2.639) | falsche **Positionsgröße** (20–50 % statt 1,2–7,8 %) |
| „MFE/MAE ist besser" | **E[R]** ordnet 138 % schärfer |

⛔ **Die Prüfungen sind keine Entdeckungen.** Weglassprobe,
Zeitstabilität, Mehrfachtesten, tagestreue Nullwelt stehen alle im
Regelwerk. Ich habe sie als **Nacharbeit** behandelt statt als
**Voraussetzung der Meldung** — deshalb kommt nicht ein Detail um die
Ecke, sondern die Grundlage.

## ➤ Die Maßnahme: keine Meldung ohne diese fünf

| # | vor **jeder** Meldung eines Befundes |
|---|---|
| **1** | **Nullwelt** — tagestreu, nicht gepoolt |
| **2** | **Zeitstabilität** je Kalenderjahr |
| **3** | **Weglassprobe** — ohne je ein Jahr |
| **4** | **Mehrfachtesten** — Band für *alle* getesteten Zellen, nicht je Zelle |
| **5** | **Ebene** — ist es Bewertung (A), Erfolgsmessung (B) oder Betrieb (C)? |

⚠️ Und: **kein Befund wird eingetragen, bevor alle fünf durch sind.**

---

# 2. Die Befundlage — 23 gelten, 4 sind gefallen

## ⛔ Gefallen (alle vier am selben Tag)

| | warum |
|---|---|
| **2.630** Hebelkurve | Hebelhöhe aus **Kelly** — Ertrag in der Bewertung |
| **2.632** vier Hebelstufen | Weglassprobe: ohne 2025 bleibt **nichts** |
| **2.639** Depot verliert | Positionsgröße 20–50 % statt der echten 1,2–7,8 % |
| **2.640** Betriebsschwelle | Schwelle aus der **Kelly-Nullstelle** |

## ✔ Was belastbar steht

| Bereich | Befund |
|---|---|
| **Die Achse** | invers (2.625), trägt 5 von 5 Jahren und in jeder Weglassprobe (2.626/2.633) |
| **Ihre Rolle** | ⭐ **Risikosperre** — d 0,521 auf MAE gegen 0,267 auf MFE (2.642/2.643) |
| **Die Geometrie** | H24 / Stop 1,00 ATR / Trailing 1,5 / 0,5 (2.628), netto-optimal (2.629) |
| **Die Zielgröße** | `E[R]`, ordnet 138 % schärfer als MFE/MAE (2.644) |
| **Der Horizont** | **24 Stunden**, gemessen (2.642), Standard nachgezogen (2.646) |
| **Die Daten** | Tagesbasis trägt **nicht** (2.635); Stundendaten machbar, 7-Tage-Fenster (2.636); Quellen ohne OHLC angleichbar, Faktor 2,0832 (2.637) |
| **Der Betriebsfall** | nur **Streckenanfänge**, Trennschärfe bleibt (2.638) |
| **Der Ist-Zustand** | Kelly im Code **exakt 0,0** — der Hebel kann heute gar nicht entstehen (2.634) |

---

# 3. ⛔ Der Kern: Rolle A trägt nicht

| Prüfung | Ergebnis |
|---|---|
| einzeln | kein Merkmal von null zu trennen — Effekt **10–60× kleiner** als der Tagesfehler |
| Kombination, Einzelband | 20 Treffer bei 64 Versuchen (erwartet 6,4) |
| Kombination, **Band(32)** | ⛔ die stärkste fällt; Einzelband **1,9× zu lax** |
| Zeitstabilität | ⛔ keine in mehr als **3 von 5** Jahren positiv |

⭐ **Was bleibt:** 20 von 64 ist keine Zufallszahl — **Signal ist da**,
aber nicht in einzelnen Zellen isolierbar und nicht über null.

## Die sieben geprüften Merkmale sind **eine Familie**

`rsi_aenderung` · `rsi_umkehr` · `ema_lage` · `ema_steigung` ·
`ema_abstand_atr` · `bandenge` · `trendstruktur`

**Alle aus EMA, RSI und ATR** — also aus demselben Kursverlauf, nur
anders verrechnet. 2.594 hat das schon gemessen: *„Trendstruktur
korreliert mit dem 24h-Rang zu +0,6675 — teilweise neue Information,
aber dieselbe Familie."*

➤ **Eine Verfeinerung derselben Familie schließt die Lücke nicht.**

---

# 4. Die Lücke, beziffert

| | |
|---|---|
| `E[R]` heute, ganze Menge | **−0,00136** (H6) bis **−0,00628** (H24) |
| bestes Einzelmerkmal | +0,00037 — im Rauschen |
| Tagesfehler | ±0,00294 bis ±0,00393 |
| **was fehlt** | **+0,00136** bis null — und der Tagesfehler ist **doppelt so groß** |

⚠️ **Das ist keine Frage der Messgenauigkeit, sondern der
Größenordnung.** Selbst ein Merkmal, das doppelt so stark wäre wie alles
je Gemessene, bliebe im Rauschen.

⭐ Dieselbe Rechnung stand schon in **2.578** (24.09.): *„Faktor 4 bis 21
zu wenig … es ist keine Frage der Messgenauigkeit, sondern der
Größenordnung."* Drei Tage später ist sie bestätigt, mit sieben neuen
Merkmalen.

---

# 5. ➤ Was daraus folgt — die Grundsatzfrage

**Nicht der Neubau ist gescheitert, sondern eine Annahme darin:** dass
sich aus dem *Kursverlauf allein* eine Lage finden lässt, die `E[R]`
über null hebt.

| | |
|---|---|
| ✔ **Die Achse ordnet** — als **Risikofilter**, belastbar über fünf Jahre |
| ✔ **Die Geometrie steht** — H24, Stop 1,00 ATR, Trailing 1,5/0,5 |
| ⛔ **Die Richtung fehlt** — und sie ist aus EMA/RSI/ATR nicht zu holen |
| ⚠️ **Ungeprüft**: Terminmarkt-**Rohgrößen** (seit E-3 freigegeben) — `oi_aenderung`, `taker_verh`, `konten_verh`, `volumenschub`. Im A-Lauf liefen sie **mit** und trugen einzeln ebenfalls nicht |

⚠️ **Auch die Terminmarktgrößen sind gemessen und negativ** — sie standen
in derselben Tabelle. Damit ist die naheliegendste verbleibende Quelle
bereits geprüft.
