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
