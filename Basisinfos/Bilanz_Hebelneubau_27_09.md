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
| „die Achse trägt" (2.626) | trägt nur **relativ zum Tag** — ✔ inzwischen **widerlegt**, siehe Abschnitt 2a |
| „die Stufung trägt" (2.632) | Weglassprobe **kippt** sie |
| „die Schwelle ist −1,65" (2.640) | aus **Ertrag** abgeleitet, abgelöst |
| „das Depot verliert" (2.639) | falsche **Positionsgröße** (20–50 % statt 1,2–7,8 %) |
| „MFE/MAE ist besser" | **E[R]** ordnet 138 % schärfer |

⛔ **Die Prüfungen sind keine Entdeckungen.** Weglassprobe,
Zeitstabilität, Mehrfachtesten, tagestreue Nullwelt stehen alle im
Regelwerk. Ich habe sie als **Nacharbeit** behandelt statt als
**Voraussetzung der Meldung** — deshalb kommt nicht ein Detail um die
Ecke, sondern die Grundlage.

## ➤ Die Maßnahme: keine Meldung ohne diese **sechs**

| # | vor **jeder** Meldung eines Befundes |
|---|---|
| **1** | **Nullwelt** — tagestreu, nicht gepoolt |
| **2** | **Zeitstabilität** je Kalenderjahr |
| **3** | **Weglassprobe** — ohne je ein Jahr |
| **4** | **Mehrfachtesten** — Band für *alle* getesteten Zellen, nicht je Zelle |
| **5** | **Ebene** — ist es Bewertung (A), Erfolgsmessung (B) oder Betrieb (C)? |
| **6** | ⭐ **Je Asset** — trägt es *innerhalb* der Symbole, oder sortiert es nur Symbole? |

⚠️ Und: **kein Befund wird eingetragen, bevor alle sechs durch sind.**
Bewacht vom Suite-Paket `Hebelneubau`, gültig ab 2.647.

### ⭐ Die sechste kam vom Nutzer, mitten im Lauf

> *„nicht den Markt alleine messen, sondern die Bewertung muss auf das
> Asset gehen"* — 27.09.2026

⛔ **Was sie verhindert:** „+1,2568 % gegen Markt +0,0150 %" ist ein
**gepoolter** Vergleich. Treten die scharfen Lagen bevorzugt in wenigen
volatilen Symbolen auf, misst diese Zahl die **Symbolauswahl** — und ein
Beitrag, der nur Symbole sortiert, verstößt beim Hebel gegen **Regel 3**
(kein Asset-Rang). Der gepoolte Vergleich allein hätte das nie gezeigt.

➤ **Der Beleg ist ein anderer Bezug, keine andere Zahl:** jeder Anker
gegen den Durchschnitt **seines eigenen Symbols**.

⚠️ Sie stand längst im Memory
(`feedback_nicht_den_markt_messen_sondern_beitraege_je_asset`) — sie war
nur nicht bewacht.

---

# 2a. ✔✔✔ Die Grundlage hält — und sie hält **je Asset** (2.647)

**Nutzereinwand:** *„gestern Abend hast du mir geschworen, die Standards
einzuhalten, und die Messung war grün, alle danach auch — wenn du falsch
beginnst, sind die Messungen danach auch wertlos."*

**Berechtigt.** 2.626 ist die Grundlage, auf der 2.628 bis 2.646 stehen,
und sie hatte nur **tagestreu** gemessen. Nachgemessen mit allen sechs
Prüfungen — `messe_grundlage_je_asset.py`:

| Schwelle in `ema_abstand_atr` | Anker | Ertrag | gegen Markt |
|---|---|---|---|
| alle Anker (Markt) | 3.186.954 | **+0,0150 %** | — |
| W ≤ −1,0 | 46.713 | +0,4346 % | **29×** |
| W ≤ −1,2881 | 10.532 | +1,2568 % | **84×** |
| W ≤ −1,5 | 3.372 | +2,2942 % | 153× |
| W ≤ −1,65 | 1.531 | +3,4260 % | **228×** |
| W ≤ −1,8 | 691 | +4,3234 % | 288× |

## ⭐⭐ Und die Assetprüfung — das eigentliche Ergebnis

| Bezug | Lift |
|---|---|
| gegen den **Markt** (gepoolt) | +1,2418 Pp |
| gegen das **eigene Symbol** | **+1,2301 Pp** |

➤ **99,1 % bleiben übrig.** 111 von 115 Symbolen haben genug Treffer,
**84,7 %** von ihnen zeigen einen positiven Lift, und die Auswahl
konzentriert sich nur zu **17,5 %** auf die zehn häufigsten Symbole
(Gleichverteilung wäre 9 %).

⛔ **Damit ist ausgeschlossen, dass die Achse Symbole statt Lagen
sortiert** — der Verstoß gegen Regel 3, den der gepoolte Vergleich nicht
hätte zeigen können.

## Die übrigen vier Prüfungen

| | |
|---|---|
| **Nullwelt** + **Mehrfachtesten** | Bestes-von-fünf-Band −1,2570, **alle fünf** Schwellen darüber |
| **Zeitstabilität** | **5 von 5** Kalenderjahren über den Markt desselben Jahres |
| **Weglassprobe** | **7 von 7**, auch ohne 2025 (+1,0270 gegen +0,0537) |
| **Ebene** | B — Erfolgsmessung, kein Rückfluss in die Bewertung |

## ⚠️ Zwei Fehler in dieser Messung — beide **vor** der Meldung gefunden

| | |
|---|---|
| **Jahr aus dem Index statt aus dem Datum** | `G // (24·365)`. Die Reihe beginnt am **01.12.2021**, also lief „Jahr 2022" von Dez 2021 bis Nov 2022 — und bei einem Teillauf verschob sich die Grenze nochmals. Genau daher wich der Probelauf (12 Symbole) vom vollen ab: **5 von 5 gegen 4 von 5**. Nicht in den Daten, sondern in der **Beschriftung** |
| **Ein Jahr mit 3 Ankern zählte als bestanden** | ergab „6 von 6". Seither Mindestmengen: **100 Anker** je Jahr, **20 Symbole** je Assetzeile — darunter wird *ausgewiesen*, nicht gezählt |

⭐ Der erste Fehler ist die registrierte Regel *„kleine Läufe täuschen"* —
diesmal nicht als Zufall, sondern als **Skriptfehler**, den erst der
Größenunterschied sichtbar machte.

## ⛔ Zwei eigene Zweifel waren unbegründet

| ich hatte gemeldet | was stimmt |
|---|---|
| „als absoluter Auslöser ist die Achse **kontraindiziert**" | **Falsch.** Das beruhte auf `crv_erwartet = MFE/MAE` — und **MFE/MAE ist nicht der Ertrag**. Die Auswahl hat ein schlechteres MFE/MAE-Verhältnis und **trotzdem** den 84-fachen Ertrag, weil das Trailing die Bewegung einsammelt. Beide Messungen stimmen; ich habe die eine als Urteil über die andere gelesen |
| „2.642 ignoriert die Reihenfolge" | nachgemessen: sie ändert **1,0 %** der Anker (2.644) |

➤ **Was daraus für die Kette folgt:** Gefallen sind vier Befunde
*oberhalb* der Grundlage (2.630, 2.632, 2.639, 2.640) — alle an derselben
Ursache. Die Messungen *darunter* stehen auf einer Achse, die **absolut
und symbolneutral** trägt.

---

# 2. Die Befundlage — 24 gelten, 4 sind gefallen

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
| **Die Achse** | invers (2.625), trägt 5 von 5 Jahren und in jeder Weglassprobe (2.626/2.633) — ⭐ und **absolut sowie je Asset** (2.647) |
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
