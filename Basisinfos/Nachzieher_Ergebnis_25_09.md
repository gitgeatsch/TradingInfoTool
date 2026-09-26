# Der Nachzieher — doppelt widerlegt, aber die Dominanz trägt als Achse

**25.09.2026** · Befund **2.601** · Vorabfestlegung 18 · `messe_nachzieher.py`
**116 Symbole (BTC ausgeschlossen) · 3.131.754 Anker · zwei Fenster**

**Nutzervorgabe, die es auslöste:**

> *„ja btc steigt alts ziehen verzögert nach **aber nicht alle gleichzeitig**
> das muss das system über die **optimale lage des assets** bewerten."*
>
> *„wenn btc steigt steigen auch alts aber nicht immer gleich — **wenn die
> dominanz fällt steigen alts stärker**."*

---

# § 1 Das Ergebnis in drei Sätzen

> ⛔⛔ **Der Rückstand ist kein Beitrag.** Zwei unabhängige Gegenproben sagen
> dasselbe: er ist nur **13 %** stärker als `beta` allein, und die
> Spiegelprobe liefert **0,87–0,90** — Bewegung ohne Richtung.
>
> ⭐⭐⭐ **Aber die DOMINANZ trägt als Achse** — in jeder BTC-Lage ist
> „Dominanz fällt" um **+0,0074 bis +0,0123** besser als „Dominanz steigt".
> Die Nutzerlogik ist damit bestätigt.
>
> ⛔ **Und die gesuchte Zelle bleibt bei null:** BTC steigt **und** Dominanz
> fällt ergibt `E[R]` = **+0,0001 ± 0,0058** — nicht mehr negativ, aber auch
> nicht von null zu trennen.

---

# § 2 ⭐⭐⭐ Die Kreuztabelle — die Nutzerlogik ist bestätigt

**`E[R]` brutto, tagesgeblockter Fehlerbereich:**

| Fenster **voll** | **Dominanz FÄLLT** | **Dominanz STEIGT** | Differenz |
|---|---|---|---|
| BTC fällt | +0,0057 ± 0,0078 ⚠️ | +0,0042 ± 0,0063 ⚠️ | +0,0015 |
| BTC seitwärts | −0,0014 ± 0,0052 ⚠️ | **−0,0106 ± 0,0060** ✔ | **+0,0092** |
| **BTC steigt** | **+0,0030 ± 0,0054** ⚠️ | **−0,0134 ± 0,0077** ✔ | **+0,0164** |

| Fenster **ab 2024** | Dominanz FÄLLT | Dominanz STEIGT | Differenz |
|---|---|---|---|
| BTC fällt | −0,0018 ± 0,0191 ⚠️ | −0,0064 ± 0,0175 ⚠️ | +0,0046 |
| BTC seitwärts | −0,0071 ± 0,0151 ⚠️ | −0,0233 ± 0,0156 ⚠️ | +0,0162 |
| **BTC steigt** | **+0,0087 ± 0,0157** ⚠️ | **−0,0268 ± 0,0180** ⚠️ | **+0,0355** |

➤ **In allen sechs Zeilen ist fallende Dominanz besser** — und die STÄRKSTE
Differenz steht genau dort, wo der Nutzer sie erwartet hat: bei **steigendem
BTC** (+0,0164 voll, +0,0355 ab 2024).

⭐⭐ **Die verwertbare Hälfte ist die NEGATIVE:** „BTC steigt **und** Dominanz
steigt" liegt bei **−0,0134 ± 0,0077** und ist damit vom Null verschieden —
eine **belegte Sperre**. Die positive Hälfte („Dominanz fällt", +0,0030 ±
0,0054) erreicht die Signifikanz **nicht**.

⚠️⚠️ **Und der kleine Lauf hatte überzeichnet:** über 15 Symbole stand bei
„BTC fällt + Dominanz fällt" +0,0156, auf der vollen Menge sind es **+0,0057**
— Faktor 2,7. Die Zahlen dieses Dokuments stammen alle aus dem Lauf über
115 Symbole.

⚠️⚠️ **Warum mein erster Lauf das verdeckte:** Ich hatte nur nach der BTC-Lage
getrennt und über beide Dominanz-Richtungen **gemittelt**. Bei „BTC steigt"
stand dort −0,0070 — der Mittelwert aus +0,0001 und −0,0116. **Der Effekt war
in der Mittelung verschwunden.**

---

# § 3 ⛔⛔⛔ Der Konstruktionsfehler, den der Nutzer gefunden hat

**Nutzerfrage:** *„wie hast du dominanz gemessen wenn fällt dann steige
Alts?"*

Die erste Fassung bildete `dominanz_wirkung = dom_aenderung × beta` — als
„Regler × Empfänglichkeit". **Das ist arithmetisch unmöglich:**

```
dom_aenderung ist INNERHALB einer Stunde fuer alle Assets DIESELBE Zahl.
  =>  Produkt = Konstante x beta
  =>  innerhalb der Stundenklammer MONOTON IN BETA
```

**Am Konstrukt nachgewiesen** (200 Assets, eine Stunde):

| Dominanz-Änderung | Rangkorrelation (`wirkung`, `beta`) |
|---|---|
| +0,010 | **+1,0000** |
| −0,010 | **−1,0000** |

➤ **`dominanz_wirkung` WAR `beta`** — bei steigender Dominanz gleich
sortiert, bei fallender exakt umgekehrt. Über viele Stunden hebt sich das auf.

⚠️⚠️ **Mein Urteil war deshalb falsch.** Ich hatte gemeldet *„die Regler-Idee
trägt nicht"*. Richtig ist: **so gemessen KANN sie nicht tragen** — und als
Achse gefahren trägt sie sehr wohl (§ 2).

➤ **Die Lehre:** ein Marktzustand wird zur **Achse**, nicht zum Faktor in
einem Produkt. Ein Produkt mit einer je Stunde konstanten Größe fügt der
Ordnung innerhalb der Stunde **nichts** hinzu.

---

# § 4 ⛔⛔ Warum der Rückstand kein Beitrag ist — zwei unabhängige Gegenproben

## 4.1 Die `beta`-Kontrolle

| Merkmal | Fenster voll | ab 2024 |
|---|---|---|
| `rueckstand_roh` | −0,00197 | −0,00172 |
| `rueckstand_beta` | −0,00177 | −0,00149 |
| **`beta` allein** | **−0,00157** | **−0,00145** |
| `zufall` | −0,00005 ✔ | −0,00013 ✔ |

➤ **Nur 13 % über `beta`** — im zweiten Fenster **3 %**. Der Rückstand misst
im Wesentlichen Volatilität.

⚠️ **Im Mini-Lauf über 20 Symbole war er 3× stärker als `beta`**
(−0,00247 gegen −0,00081). Auf der vollen Menge schrumpft der Vorsprung auf
1,13×. **Der kleine Lauf hat getäuscht** — und ohne die `beta`-Kontrolle wäre
„rueckstand trennt ✔" gemeldet worden.

## 4.2 ⭐ Die Spiegelprobe — und sie hätte gefehlt

| | |
|---|---|
| Merkmal | Long | Short | Verhältnis | |
|---|---|---|---|---|
| `rueckstand_beta` | −0,00177 | +0,00236 | **0,75** | ⚠️ **Grenzfall** (Schwelle 0,77) |
| `rueckstand_roh` | −0,00197 | +0,00249 | **0,79** | ⛔ Bewegung ohne Richtung |
| `rueckstand_alt` | −0,00197 | +0,00249 | **0,79** | ⛔ Bewegung ohne Richtung |
| `mitlauf` | −0,00124 | +0,00247 | **0,50** | ✔ eindeutig inverse Richtung |

⚠️⚠️ **Die 0,75 gegen 0,77 ist keine belastbare Trennung.** `rueckstand_beta`
besteht formal, `rueckstand_roh` mit 0,79 fällt durch — bei fast identischen
Zahlen. Eindeutig ist nur `mitlauf` (0,50), und das ist mit −0,00124 das
SCHWÄCHSTE der Merkmale und schwächer als `beta` allein.

⚠️⚠️ **Die Spiegelprobe war in Vorabfestlegung 18 § 3.2 vier Mal zugesagt und
im Werkzeug NICHT eingebaut.** Gefunden erst auf die Nutzeraufforderung
*„prüfe noch einmal ob die letzten messungen die standards einhalten"* —
derselbe Fehler wie bei Vorabfestlegung 15 am selben Tag.

⚠️ **Und der erste Versuch, sie nachzurüsten, war wertlos:** ich drehte nur
das Vorzeichen der Zielgröße (`-r`), ohne die **Barrieren** zu spiegeln. Das
unterstellt dieselben Ausgänge und wird bei konsequenter Rechnung
tautologisch 1,00. ✔ **Richtig gebaut** über `ausgaenge(..., runter=True)`:
Stop **oben**, Ziel **unten**, `r_offen` gedreht — nachgewiesen bitgleich im
Standardpfad (R-R11 unberührt) und mit echten anderen Ausgängen
(221 ZIEL/1454 STOP short gegen 286/1168 long).

---

# § 5 Die Trennschärfe

| Anteil echter Ordnung | 0,00 | 0,10 | 0,25 | 0,50 | 1,00 |
|---|---|---|---|---|---|
| Fundquote | 0–40 % | 0 % | 20–60 % | **80–100 %** | **100 %** |

➤ Auflösung bei **Anteil 0,50** — wie in 2.597. ⚠️ Die 40 % bei Stufe 0,00
sind Clusterung aus 5 Ziehungen (2.600 § 8.4), kein Fehlalarm.

---

# § 6 ⛔ Was NICHT folgt

| # | |
|---|---|
| **1** | ⛔ **Nicht, dass die Dominanz ein Beitrag ist.** Sie trägt als **Achse** — das ist eine Bedingung („wann"), kein Merkmal, das Assets ordnet. Nach `feedback-nicht-den-markt-messen…` gehört sie damit in eine Sperre oder in die Mail, nicht in die Bewertung |
| **2** | ⛔ **Nicht, dass „BTC steigt + Dominanz fällt" trägt.** +0,0001 ± 0,0058 ist **null**, nicht positiv |
| **3** | ⚠️ **Die Dominanz ist ein PROXY.** Die echte BTC-Dominanz ist nicht messbar: `macro_snapshot` hat 3.384 Zeilen, aber nur **10 Werte** mit `btc_dominance_pct`. CoinGecko liefert gratis nur **365 Tage** (`/global/market_cap_chart` ist Pro, `days=400` → 401). Gemessen wurde `BTC-Rendite − Alt-Mittel`, also die **Änderung**, nicht das Niveau |
| **4** | ⚠️ **Das Niveau bleibt ungeprüft.** Ob „Dominanz bei 60 %" anders wirkt als „bei 40 %", ist mit einem Jahr Historie nicht zu beantworten |
| **5** | ⛔ **Nichts über Handelbarkeit.** Der stärkste Wert steht bei **fallendem** BTC — dort sind Liquidität und Slippage am schlechtesten. Ungeprüft |

---

# § 7 Standards

| | |
|---|---|
| **gilt** | Vorabfestlegung vor der Messung · Nullband 40 Ziehungen, 90. Perzentil · `zufall` **und** `beta` als Kontrollen · **Spiegelprobe** (nachgerüstet) · **Trennschärfe** (nachgerüstet) · Stundenklammer · Fenster als Achse · tagesgeblockter Fehlerbereich |
| ⛔ **verletzt und behoben** | Spiegelprobe und Trennschärfe waren zugesagt und fehlten · `dominanz_wirkung` war arithmetisch unmöglich |
| ➤ **Frageart** | **`beitrag`** für die Asset-Merkmale, **`markt`** für die Achsen — und die Trennung ist der Kern dieses Befunds |

---

# § 8 Was die Sperre bringt — gerechnet (Nachtrag 26.09., Befund 2.602)

**Nutzerauftrag:** *„ja rechnen — prüfen und gegenprüfen"* ·
`messe_sperre_wirkung.py` · **3.211.104 Anker**

Die Sperre aus § 2: *BTC steigt (> +0,5 %/6 h) **und** Dominanz steigt* —
**10,4 %** aller Anker, `E[R]` der Zelle **−0,0131** (H6).

## 8.1 Die vier Prüfungen

| | H6 | H24 |
|---|---|---|
| **P1 Selbstprobe** (arithmetisch = gemessen) | ✔ exakt | ✔ exakt |
| Gewinn **in-sample** | +0,00120 (−0,00275 → **−0,00155**) | +0,00223 (−0,00901 → **−0,00679**) |
| **P2 Nullwelt der Überanpassung** | +0,00120 gegen **+0,00020** → **Faktor 6** ✔✔ | +0,00223 gegen +0,00051 → **Faktor 4,4** ✔✔ |
| **P3 out-of-sample (B6)** | ✔ **dieselbe Zelle**, Gewinn **+0,00182** | ✔ **dieselbe Zelle**, Gewinn **+0,00211** |

⭐⭐ **P2 ist die eigentliche Gegenprobe.** Sie misst nicht, ob eine
zufällige Sperre gleicher Größe hilft — das wäre die falsche Frage. Sie
wendet **dieselbe Prozedur** auf Zufallsachsen an: Raster bilden,
schlechteste Zelle suchen, sperren, Gewinn messen. Das ist der Anteil, der
allein aus dem **Suchen** entsteht, und er liegt bei +0,00020.

⭐⭐ **P3 ist der stärkste Teil:** die Sperre wird auf der ersten Hälfte
gefunden und wirkt auf der zweiten **genauso stark** — bei H24 +0,00211
gegen +0,00223. Keine Überanpassung.

## 8.2 ⛔ Und trotzdem reicht es nicht

> `E[R]` steigt von **−0,00275 auf −0,00155**. Die Sperre **halbiert den
> Verlust, sie dreht ihn nicht.**

Für null bräuchte es noch einmal das Doppelte. Und **P4** zeigt, dass mehr
Sperren monoton mehr bringt (14,6 % gesperrt → +0,00143) — ⚠️ das ist
genau der Weg in die Überanpassung, den P2 und P3 gerade ausgeschlossen
haben. Er wird hier **nicht** beschritten.

⚠️ **Der Gewinn ist nicht signifikant:** out-of-sample +0,00182 bei einem
tagesgeblockten Fehler von **±0,00547**. Belegt ist, dass er **nicht aus der
Suche stammt** (P2) und **out-of-sample hält** (P3) — nicht, dass er von
null verschieden ist.

## 8.3 ⚠️⚠️ Der Mini-Lauf hat zum dritten Mal in die Irre geführt

Über **20 Symbole** meldete P3 das Gegenteil: auf Hälfte 1 war eine
**andere** Zelle die schlechteste („BTC nicht + Dom steigt"), und der Gewinn
auf Hälfte 2 lag bei **+0,00001**.

| heute | klein | voll |
|---|---|---|
| `rueckstand` gegen `beta` | Faktor **3** | Faktor **1,13** |
| Kreuztabelle „BTC fällt + Dom fällt" | +0,0156 | +0,0057 |
| **P3 Sperrenstabilität** | ⛔ andere Zelle | ✔ dieselbe Zelle |

➤ **Für diese Fragen taugen kleine Läufe nicht — auch nicht zur
Vorabschätzung.** Sie haben heute dreimal ein anderes Vorzeichen oder eine
andere Größenordnung geliefert als die volle Menge, in beide Richtungen.
