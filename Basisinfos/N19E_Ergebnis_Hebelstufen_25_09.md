# N19-E — die Hebelstufen: das Ergebnis

**25.09.2026.** Vorabfestlegung 13 · Werkzeug `n19e_hebelstufen.py`
(10 `messnorm`-Verweise — **Neubestand**, keine eigenen Konstanten).

**N19-E war eine Nutzerentscheidung vom 06.09.2026, die nie umgesetzt
wurde.** Sie ist jetzt gemessen.

---

# § 1 ⭐⭐⭐ Das Ergebnis: `funding` liefert eine Stufenleiter

**Menge `frei`, Zielgröße `barriere`, Horizont 3, 2.401 Tage, 299 Symbole.**

| Fünftel | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| **q** | **0,3510** | 0,3499 | 0,3470 | 0,3427 | **0,3389** |
| **Punkte** | +0,509 | +0,401 | +0,111 | −0,318 | −0,703 |

| Prüfung | Ergebnis |
|---|---|
| **B5 Monotonie** | ✔ **fallend über alle fünf Fünftel** |
| **Nullpunkt** (40 Ziehungen, 90. Perzentil) | Spanne **0,0121** gegen **0,0040** → **Faktor 3,0** ✔ |
| **out-of-sample** | r = **+0,575** ✔ die Ordnung hält |
| **Kelly-Nullstelle 0,3333** | ✔ **alle fünf** Fünftel darüber |
| **Negativkontrolle `zufall`** | ✔ auf **allen vier** Mengen im Rauschen |

➤ **Alle Bedingungen der Entscheidungsregel (§ 5 der Vorabfestlegung)
erfüllt.**

## 1.1 Die Wirkung auf den Hebel

| Fünftel | q | Kelly | r | Hebel roh |
|---|---|---|---|---|
| 0 | 0,3510 | +0,0265 | 0,0125 ← **r_max** | 7,50x |
| 1 | 0,3499 | +0,0249 | 0,0124 | |
| 2 | 0,3470 | +0,0205 | 0,0103 | |
| 3 | 0,3427 | +0,0141 | 0,0070 | |
| 4 | 0,3389 | +0,0084 | 0,0050 ← **r_min** | 3,00x |

**Spreizung Faktor 2,5.** Nach dem Deckel `hebel_grenze: 5.0` bleibt
**3,0x bis 5,0x**, monoton abgestuft.

⚠️⚠️ **Zwei Einschränkungen, die dazugehören:**

| | |
|---|---|
| **Die Klammer bestimmt mit** | Fünftel 0 erreicht `r_max`, Fünftel 4 liegt mit Kelly/2 = 0,0042 **unter** `r_min` und wird auf 0,005 **angehoben**. Frei steuert die Bewertung nur die drei mittleren Stufen |
| **Immer ein Hebel, nie null** | alle q liegen über der Nullstelle (0,3389–0,3510 gegen 0,3333) |

---

# § 2 `oi_aenderung`: eine SPERRE, kein Regler — und sie ist gebaut

| Menge | Spanne | Nullpunkt (90 %) | monoton | out-of-sample | Fünftel über Nullstelle |
|---|---|---|---|---|---|
| 20 % | 0,0153 | 0,0135 ✔ | nein | r +0,082 ✗ | 0,1,2,3 |
| 50 % | 0,0144 | 0,0058 ✔ | nein | r +0,724 ✔ | nur 0 |
| frei | 0,0090 | 0,0037 ✔ | nein | r +0,810 ✔ | ⛔ **keines** |

➤ **Über dem Nullpunkt auf allen Mengen, aber nicht monoton** — und das
oberste Fünftel ist durchgängig das schlechteste (Punkte −1,13 / −0,78 /
−0,60).

**Nach der Entscheidungsregel: Schalter statt Regler.** ⭐ **Und genau so
ist er bereits gebaut** — N14, die OI-Sperre an Trichterstufe 12.

⚠️ **N19-E bestätigt damit die bestehende Bauform**, statt eine neue zu
verlangen.

⛔ **Aber als Hebelquelle taugt er nicht:** auf `frei` liegt **kein**
Fünftel über der Kelly-Nullstelle.

---

# § 3 ⚠️ Was noch fehlt — offen benannt

| | |
|---|---|
| **Trennschärfe** | ⛔ **nicht gemessen.** Vorabfestlegung § 4 verlangt gepflanzte Stärken bis 0,40 R. Erst der Nullpunkt zeigte, dass überhaupt etwas über dem Rauschen liegt — die Frage „ab welcher Stärke findet die Anlage etwas" ist damit noch offen |
| **Nur `frei` ist monoton** | auf 50 % liegt `funding` ebenfalls über dem Nullpunkt (0,0164 gegen 0,0060) und hält out-of-sample (r +0,584), ist aber **nicht monoton**. Auf 10 % und 20 % liegt er **im Rauschen** |
| ⭐ **Ebene 3: die Merkmalsauflösung** | `oi_aenderung` liegt **stündlich** vor (`terminmarkt_historie.stunde`), wird hier aber **täglich** aggregiert. `funding` gibt es nur täglich (`funding_historie.datum`). **Ob die feinere Auflösung mehr bringt, ist ungemessen** |

## 3.1 ⚠️ Tages- oder Stundenwerte — die drei Ebenen getrennt

**Nutzerfrage 25.09.:** *„berücksichtige auch ob du mit tages oder
stundenwerte rechnest — du hast festgestellt dass kaum ein Unterschied
besteht"*

| Ebene | Tag gegen Stunde | belegt durch |
|---|---|---|
| **1 Barrieren-Auflösung** | ⭐ **+0,0003 — vernachlässigbar** | 2.583: 0,63 % mehrdeutig, Auflösung 207/195 = 50/50 |
| **2 Horizont** | ⛔ **riesig** | H3: 52,6 % entschieden · 6 h: nur **2,9 %** |
| **3 Merkmalsauflösung** | ⚠️ **ungemessen** | `oi_aenderung` stündlich verfügbar, täglich verwendet |

➤ **Die Nutzererinnerung trifft Ebene 1 und ist dort richtig** — deshalb
ist die Tagesbasis für N19-E korrekt, belegt statt bequem.

---

# § 4 Was das für den Plan heißt

| | |
|---|---|
| ⭐ **Der Hebel hat eine Bewertungsgrundlage** | `funding` auf `barriere`/H3, monoton, out-of-sample stabil, über dem Nullpunkt |
| ✔ **Die Kapselung kann gelockert werden** | `funding` bekommt `instrumente=("spot","hebel")` — mit **eigenen** Stufen je Instrument |
| ⛔ **Die Spot-Stufen werden NICHT übernommen** | Spot +0,82 … −1,70 gegen Hebel +0,51 … −0,70 — Faktor 2,4 |
| ⚠️ **`turnover` bleibt bei Spot** | auf `barriere` untermächtig (+0,0073 gegen Nachweisgrenze 0,0094–0,0180, nur 66 Symbole) |
| ⚠️ **`oi_aenderung` bleibt Sperre** | keine Hebelquelle, aber die bestehende Bauform ist bestätigt |

## 4.1 ⚠️ Die Plan-Vorgabe des Nutzers, festgehalten

> *„Wenn ein Asset geprüft wird, soll entweder ein Spot oder Hebel nach der
> Bewertung in der Ablaufkette verarbeitet werden, das erfordert aber erst
> NACH dem Hebel eine Neubewertung von SPOT."*

➤ **Reihenfolge: Hebel fertig → dann Spot neu → dann die parallele
Auswahl.** Die Entweder-Oder-Entscheidung kommt zuletzt, nicht zuerst.

---

# § 5 ⚠️ Eigene Fehler in diesem Durchgang

| | gefunden durch |
|---|---|
| **Nullpunkt, `zufall` und Trennschärfe fehlten** im ersten Lauf — obwohl die eigene Vorabfestlegung sie verlangt | eigene Gegenprüfung, **vor** dem Urteil |
| Nullpunkt und Kontrolle nachgezogen | ✔ erst damit ist die Spanne einzuordnen |
| Trennschärfe **weiterhin offen** | benannt, nicht vergessen |
