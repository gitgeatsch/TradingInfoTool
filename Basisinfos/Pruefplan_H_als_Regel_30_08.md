# Prüfplan: H als Regel — jede bekannte Fehlerquelle einzeln (30.08.2026)

**Nutzerauftrag:** *„es ist eine der wichtigsten Messungen, die wir
durchführen — gehe vorher alle bisherigen Fehler bei Messungen durch, die wir
bereits hatten, und Fehlerprüfungen als Maßnahme, damit das Ergebnis
tatsächlich stimmt."*

**Warum diese Messung zählt:** H ist der **einzige** Beitrag, der heute im
System wirkt — und die eine Prüfung, die R-R8 (B3) für alle anderen zur
Pflicht macht, fehlt bei ihm. Alle H-Zahlen sind Merkmalsvergleiche.

---

## Die Checkliste — 15 Fehlerquellen, jede mit Maßnahme

| # | Fehler, den wir hatten | Wo er auftrat | Maßnahme in dieser Messung |
|---|---|---|---|
| **1** | ⚠️ **Merkmal statt Regel gemessen** | Funding: +0,132 gegen +0,024 R — **Faktor 5,5** | ✔ **das IST der Zweck** — drei Zahlen: wie viele Fälle · waren die besser · was bleibt netto |
| **2** | **Das blinde Maß** — „Ziel vor Stop" fällt per Konstruktion auf 1/(1+CRV) | Zielbild, seit 23.08. | ✔ gemessen wird die **Bewegung in R**, nicht die Trefferquote |
| **3** | Kontrolle aus fremdem Zeitfenster | V-0: +0,704 Punkte geschenkt | ✔ Zufallsanker aus **demselben Kalendertag** |
| **4** | ⚠️ **Nicht quotengleich verglichen** | Schwellenkalibrierung: +0,21 gegen Zufallsmaximum +0,34 | ✔ **quotengleiche** Zufallsauswahl — H trifft nur 3,3 %, der Selektionseffekt ist dort besonders groß |
| **5** | Symbole als unabhängig gezählt | V-0: 20 Symbole, 7 gemeinsame Tage | ✔ Bootstrap über **Blöcke**, nicht über Anker |
| **6** | Blocklänge kürzer als der Horizont | MC/TVL H60: Artefakt | ✔ Block **250 Tage** > Horizont 20 |
| **7** | Mittelwert bei Schiefe 2,68 | K-2: ein Anker trug 187 % | ✔ durchgehend **Median** |
| **8** | ⚠️ **Datenbrüche** (Token-Umstellungen) | LUNA Faktor 177.400 | ✔ Anker mit Sprung > Faktor 5 im Vorwärtsfenster **entfernt** |
| **9** | Positivkontrolle frisst den eigenen Effekt | zweimal falsch gebaut | ✔ **künstliches Merkmal** bekannter Güte |
| **10** | Suchpreis nicht bezahlt | K-1: 105 Zellen | ✔ **eine** vorab benannte Regel, keine Variantensuche |
| **11** | Nur die erste Historienhälfte trägt | dreimal an einem Tag | ✔ **beide Hälften** getrennt ausgewiesen |
| **12** | Survivorship | Turnover: 71 % gegen 90 % | ✔ Endstand der H-Symbole gegen den Rest |
| **13** | Messung auf der kleinen Basis | 32 von 54 Werkzeugen | ✔ **523 Reihen** aus `messdaten.db` |
| **14** | Bytecode-Cache verfälscht | 30.08. | ✔ `__pycache__` vor dem Lauf gelöscht |
| **15** | ⚠️ **Struktureinbruch 2024** | Bewegung in R: +0,14 → −0,63 | ✔ **je Zeitabschnitt** getrennt |

---

## Was vorab festgelegt ist — vor der ersten Zahl

**Die Regel, die geprüft wird:**

> **„Nimm nur Einstiege, bei denen H zutrifft."**

⚠️ Das ist eine **extreme** Sperrquote: H trifft auf rund 3,3 % der Ankertage
zu. Die Regel sperrt also ~97 %. Deshalb wird **zusätzlich** die mildere
Lesart gerechnet:

> **„Bevorzuge H"** — H-Anker gegen quotengleiche Zufallsanker desselben Tages.

**Die Urteilsregel:**

| | |
|---|---|
| **trägt** | Netto positiv, Bootstrap-Intervall ohne Null, **beide Hälften** gleiches Vorzeichen |
| **trägt nicht** | sonst — **und** die Positivkontrolle zeigt, dass ein Effekt dieser Größe gefunden worden wäre |
| **unentscheidbar** | Netto ≤ 0, aber die Positivkontrolle fällt ebenfalls |

⚠️ **Und die Konsequenz ist vorab benannt:** Trägt H als Regel nicht, wird der
Beitrag auf `zustand="null"` gesetzt — **nicht auf einen kleineren Wert**. Ein
Zwischenwert wäre genau das Nachjustieren, das der Nutzer zu Recht
zurückgewiesen hat.
