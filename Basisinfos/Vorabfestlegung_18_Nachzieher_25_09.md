# Vorabfestlegung 18 — Der Nachzieher: welches Asset hat noch nicht reagiert?

**25.09.2026**, vor der Messung geschrieben · Werkzeug
`messe_nachzieher.py` · Frageart **`beitrag`**

**Nutzervorgabe, wörtlich:**

> *„ja btc steigt alts ziehen verzögert nach **aber nicht alle gleichzeitig**
> das muss das system über die **optimale lage des assets** bewerten."*
>
> *„du sollst nicht das system oder den Markt messen sondern wir müssen
> **Beiträge finden die für einzelne Assets genutzt werden**."*

---

# § 1 Die Fragestellung

> **Wenn BTC sich bewegt hat: ordnet der RÜCKSTAND eines Assets, was danach
> passiert?**

⭐ **Der entscheidende Unterschied zu Schritt 3 (2.599):** dort war das
Merkmal ein **Marktzustand** — zu jeder Stunde für alle 116 Assets derselbe
Wert. Hier ist es eine Größe, die sich **je Asset unterscheidet**.

| | 2.599 (gescheitert) | hier |
|---|---|---|
| Merkmal | „steigt BTC?" | **„ist DIESES Asset zurück?"** |
| je Stunde | ein Wert für alle | **116 verschiedene Werte** |
| Frage | Niveau | **Querschnitt** |
| Stundenklammer | unmöglich | ✔ **möglich** |
| effektive Stichprobe | 6–10 Regimewechsel | **Asset-Stunden** |

## 1.1 H0 und H1

| | |
|---|---|
| **H0** | Der Rückstand eines Assets gegenüber BTC ordnet `E[R]` nicht über dem Nullband |
| **H1** | Er ordnet — und zwar **mit Richtung**: das zurückgebliebene Asset holt auf |

⚠️⚠️ **H1 hat eine Gegenhypothese, die genauso plausibel ist:** ein Asset,
das *nicht* mitzieht, ist vielleicht **schwach** und bleibt schwach. Dann
ordnet der Rückstand **umgekehrt**. ➤ Beide Vorzeichen sind verwertbar —
Aufholen als Einstieg, Schwäche als Sperre. **Deshalb wird zweiseitig
geprüft.**

## 1.2 ⭐ Die Vorhersage, damit ein Treffer nachprüfbar ist

**Erwartet:** `rueckstand_beta` ordnet stärker als `rueckstand_roh`, weil ein
Asset mit Beta 2 bei +5 % BTC eben +10 % *sollte* — ein roher Vergleich hält
es fälschlich für zurückgeblieben.

⚠️ **Trifft das nicht zu, ist Vorsicht geboten:** dann misst `rueckstand_roh`
womöglich nur **Beta** (also Volatilität), und das wäre nach 2.594 kein
Richtungsbefund, sondern Bewegung.

---

# § 2 Die Merkmale — alle je Asset, alle streng kausal

| Merkmal | Bildung zur Stunde t | Frage |
|---|---|---|
| `rueckstand_roh` | BTC-Rendite über 6 h **minus** Asset-Rendite über 6 h | wie weit ist es zurück? |
| `rueckstand_beta` | `beta × BTC-Rendite − Asset-Rendite`, β aus 30 Tagen bis t | zurück **gemessen am eigenen Anspruch** |
| `mitlauf` | Korrelation Asset/BTC über 7 Tage bis t | läuft es überhaupt mit? |
| `beta` | Steigung Asset~BTC über 30 Tage bis t | ⚠️ **Kontrolle**: ist es nur Volatilität? |
| `zufall` | Zufallszahl je Anker | **Kontrolle** |

⭐ **`beta` als Merkmal ist die eingebaute Gegenprobe.** Trägt `rueckstand`
nicht stärker als `beta` allein, dann misst der Rückstand nur, wie wild ein
Asset schwankt — das wäre kein Beitrag, sondern 2.594 noch einmal.

⚠️ **BTC selbst wird aus der Messmenge ausgeschlossen.** Sein Rückstand gegen
sich selbst ist per Konstruktion null.

---

# § 3 Die Messform

| | |
|---|---|
| **Geometrie** | k = 1,0 × ATR, geklammert — der lageneutrale Arm aus 2.597 |
| **Zielgröße** | `E[R]` **brutto UND netto** (netto = minus Drift, siehe 2.597 § 5.3) |
| **Klammer** | **Stundenklammer** — die Fünftel werden *innerhalb* jeder Stunde gebildet |
| **Nullwelt** | Zufallsfünftel innerhalb der Stunde, 40 Ziehungen, 90. Perzentil |
| **Zellen** | CRV 1,5 / 2,0 × H 6 / 24 |
| **Fenster** | voll **und** ab 2024 — als Achse (Nutzerhinweis zur Übertreibung) |

## 3.1 ⚠️ Warum die Stundenklammer hier richtig ist

Die Frage lautet *„welches Asset ist jetzt besser"* — das ist die
**Querschnittsfrage**, und dafür ist die Klammer der registrierte Standard.
⚠️ Sie beantwortet **nicht** die Niveaufrage. `E[R]` brutto wird trotzdem
ausgewiesen, damit die Lücke sichtbar bleibt statt vergessen zu werden.

## 3.2 ⭐ Die Spiegelprobe

Nach `feedback-spiegelprobe-richtung-gegen-bewegung` wird **dasselbe Ereignis
nach unten** mitgemessen. Ordnet der Rückstand in beide Richtungen gleich
stark, ist es **Bewegung ohne Richtung** — dann kein Beitrag.

---

# § 4 Welche Standards gelten

| | |
|---|---|
| **gilt** | Bezug = Nullpunkt · 40 Ziehungen, 90. Perzentil · Stundenklammer · `zufall` **und** `beta` als Kontrollen · Spiegelprobe · Trennschärfe · Fenster als Achse · zweiseitige Prüfung |
| **angepasst** | Stunden- statt Tagesklammer · gepflanzte Stärken als Anteil echter Ordnung (wie 2.597) |
| **gilt nicht** | `HORIZONT_JE_LAGE` = 3 Tage · Produktionsgeometrie · **F-212 selektierte Menge** (keine stündliche Kette, also keine Trichterstufe 12) |
| ➤ **Frageart** | **`beitrag`** — und diesmal zu Recht: das Merkmal unterscheidet Assets |

---

# § 5 Was diese Messung NICHT beantworten kann

| # | |
|---|---|
| **1** | ⛔ **Nicht die Niveaufrage.** Ein Querschnittsbeitrag sagt, *welches* Asset besser ist, nicht *ob* gehandelt werden soll. `E[R]` brutto war in 0 von 60 Zellen positiv (2.597) — das bleibt offen |
| **2** | ⛔ **Nicht die Handelbarkeit.** Ein Vorlauf von Stunden nützt nichts, wenn die Ausführung ihn frisst. Nicht gemessen |
| **3** | ⚠️ **Nicht die Arbitrage-Frage.** Ein bekannter Effekt kann verschwunden sein — die Fensterachse zeigt es, beweist es aber nicht |
| **4** | ⛔ **Nichts über Short** — ruht, aber die Spiegelprobe liefert die Zahlen dafür mit |
| **5** | ⚠️ **BTC als einziger Leitwert.** Ob ETH oder ein Marktindex besser führen, ist nicht Teil dieser Messung |
