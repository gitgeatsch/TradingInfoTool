# Horizontstabilität — das Ergebnis, und warum H3 richtig ist

**25.09.2026.** Nutzerhypothese: *„Die Bewertung sollte auch die
Horizontachse bei der Hebelentstehung berücksichtigen (bei Einstieg musst du
das als Experte bewerten ob das erforderlich ist)?"*

**Werkzeug:** `n19e_horizontstabilitaet.py` · Kandidat `funding`, Menge
`frei`, Zielgröße `barriere`, 299 Symbole, 2.401 Tage.

⚠️ **Nutzerauflage eingehalten:** *„Finanzierungsfrage ist bei der Bewertung
NICHT relevant"* — Regel 2. Die 0,18 %/Tag gehen **nicht** ein.

---

# § 1 Die Messung

| H | q0 | q1 | q2 | q3 | q4 | Spanne | monoton |
|---|---|---|---|---|---|---|---|
| **1** | 0,3389 | 0,3381 | 0,3380 | 0,3365 | 0,3348 | 0,0041 | ✔ fallend |
| **2** | 0,3448 | 0,3438 | 0,3429 | 0,3391 | 0,3367 | 0,0081 | ✔ fallend |
| **3** | 0,3510 | 0,3499 | 0,3470 | 0,3427 | 0,3389 | 0,0121 | ✔ fallend |
| **5** | 0,3629 | 0,3615 | 0,3574 | 0,3489 | 0,3443 | 0,0186 | ✔ fallend |
| 10 | 0,3945 | 0,3958 | 0,3800 | 0,3680 | 0,3633 | 0,0313 | ⚠️ nicht |
| 20 | 0,4736 | 0,4801 | 0,4515 | 0,4308 | 0,4122 | 0,0614 | ⚠️ nicht |

**Die Ordnung:** Spearman **+0,947** über 15 Paare, gegen Nullpunkt
**+0,194** (40 Welten, gemischte Zuordnung) → **Faktor 4,9**.

✔ **DIE ORDNUNG IST HORIZONTSTABIL.**

---

# § 2 ⭐⭐⭐ Und daraus folgt: H3 ist das Optimum

**Gegengeprüft gegen `betraege.hebelrechnung` — bitgleich:**

| H | r Fünftel 0 | r Fünftel 4 | **Hebel 0** | **Hebel 4** | Spreizung |
|---|---|---|---|---|---|
| 1 | 0,00500 | 0,00500 | 3,00x | 3,00x | **1,00x** |
| 2 | 0,00860 | 0,00500 | — | — | 1,72x |
| **3** | **0,01250** | **0,00500** | ⭐ **5,00x** | ⭐ **3,00x** | ⭐ **2,50x** |
| 5 | 0,01250 | 0,00822 | 5,00x | 4,93x | 1,52x |
| 10 | 0,01250 | 0,01250 | 5,00x | 5,00x | 1,00x |
| 20 | 0,01250 | 0,01250 | 5,00x | 5,00x | 1,00x |

> **Im tatsächlichen Hebel gibt es nur bei H3 eine echte Abstufung.**

| | |
|---|---|
| **unter H3** | beide Fünftel liegen bei `r_min` — keine Trennung |
| **bei H3** | Fünftel 0 erreicht `r_max`, Fünftel 4 `r_min` — das Fenster spannt sich voll auf |
| **über H3** | beide am Deckel — die Trennung verschwindet wieder |

✔ **`messnorm.HORIZONT_JE_LAGE[(hebel, einstieg)] = 3` ist damit nicht
willkürlich, sondern das Spreizungsoptimum.**

## 2.1 ⚠️⚠️ Aber es ist ein Artefakt der KLAMMER, nicht des Marktes

Bei H20 liegt `q0` bei **0,4736** und Kelly bei **+0,2104** — das
**Sechzehnfache** von `r_max`. Die Bewertung hätte dort viel mehr zu sagen;
`r_max = 0,0125` schneidet es ab.

| | |
|---|---|
| `r_min` = 0,005 · `r_max` = 0,0125 | aus **Paket B, 11.09.** — eine **Nutzerentscheidung**, keine Messung |
| ➤ **Sie bestimmt, welcher Horizont optimal ist** | bei weiterer Klammer wäre ein längerer Horizont besser |

⚠️ **Das gehört dem Nutzer vorgelegt, nicht von mir entschieden.**

---

# § 3 Die Antwort auf die Hypothese

| Frage | Antwort |
|---|---|
| **Ist die Ordnung horizontstabil?** | ✔ **Ja** — Spearman +0,947 gegen Nullpunkt +0,194 |
| **Braucht der EINSTIEG die Horizontachse?** | ⛔ **Nein.** Ein Asset ist auf 1 und auf 20 Tagen gleich gut eingeordnet. Der Einstieg fragt „welches Asset", und diese Antwort ändert sich nicht |
| **Braucht die HEBELHÖHE sie?** | ⭐ **Ja, massiv** — `q0` steigt von 0,3389 (H1) auf 0,4736 (H20) |
| **Wo liegt das Optimum?** | **H3** — gesetzt durch die Klammer, nicht durch den Markt |

➤ ⭐ **Die Hypothese ist bestätigt, aber ihre praktische Folge ist: es gibt
nichts zu bauen.** Der Horizont wirkt nur auf die Höhe, und die Klammer
sorgt dafür, dass H3 bereits der beste Punkt ist.

---

# § 4 ⚠️ Der Zielkonflikt, der offen bleibt

| | Spreizung | Trennschärfe |
|---|---|---|
| **H3** | ⭐ **2,50x** | ⛔ Spanne 0,0121 gegen Auflösung 0,0133 — **Grauzone** |
| **H5** | 1,52x | ✔ Spanne 0,0186 — **gesichert** |

**Der Horizont mit der besten Hebelspreizung ist nicht der mit dem
sichersten Befund.** ⚠️ Entwurfsfrage, keine Messung.

---

# § 5 Was geprüft und gegengeprüft ist

| | |
|---|---|
| **Nullpunkt** | ✔ 40 Welten, gemischte Zuordnung (aus `messnorm`) |
| **Kelly-Rechnung** | ✔ **bitgleich** mit `betraege.hebelrechnung` in 8 von 8 Fällen |
| **Der Buckel aus dem Probelauf** | ✔ **erklärt** — Stichprobeneffekt: bei 80 Symbolen Buckel, bei 299 monoton |
| **Monotonie** | ✔ H1 bis H5 fallend, H10/H20 nicht |

## 5.1 ⚠️ Was NICHT geprüft ist

| | |
|---|---|
| **Trennschärfe je Horizont** | nur für H3 gemessen (aus N19-E). Für H1, H2, H5, H10, H20 **offen** |
| **Die Prüfgröße `\|q0 − q4\|`** | unterschätzt bei Buckelform. Bei H10/H20 ist es nicht monoton, dort ist die Spanne also **zu klein ausgewiesen**. `max − min` wäre richtig — nach dem Sehen zu ändern wäre unzulässig |
| **Andere Kandidaten** | nur `funding`. `oi_aenderung` ist als Sperre gebaut, nicht als Regler |

---

# § 6 ⚠️ Eine eigene Korrektur, die dazugehört

Ich hatte vorgeschlagen, den optimalen Horizont über **`q(H)` minus
Finanzierung(H)** zu bestimmen. **Das war ein Verstoß gegen Regel 2**
(*„Gebühren gehören nicht in die Bewertung"*) — vom Nutzer korrigiert.

➤ **Und die Messung zeigt, dass es auch unnötig war:** die Klammer setzt
das Optimum, nicht die Kosten.
