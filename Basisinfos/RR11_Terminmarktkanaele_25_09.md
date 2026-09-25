# R-R11 — die Terminmarkt-Kanäle reproduziert

**25.09.2026.** Nutzerauftrag: *„R-R11 und rsi zuerst"* · *„du musst jetzt
bei der hebelmessung genau arbeiten - hole dir die informationen aus den
zentraldokumenten und Standards"*

**Werkzeug:** `n78_terminmarkt_kanaele.py` — **unverändert**, das Original
vom 07.09. Es ist normgerecht (`messnorm` + `messnorm_auswahl.pruefe_auswahl`
+ `zulaessige_mengen`), kein Neubau.

---

# § 1 Warum diese Reproduktion nötig war

Am 25.09. habe ich drei Kandidaten auf der Stundenbasis gemessen, **ohne
vorher ins Kandidatenregister zu sehen**. Zwei davon waren seit dem 06.09.
registriert:

| mein Name | registriert als |
|---|---|
| K5 `konten_verh` | **`long_bias`** — trägt nicht |
| K2 `taker_verh` | **`taker_bias`** — trägt nicht |
| K4 top minus retail | ⚠️ **nicht registriert** (`top_bias` ist der **rohe** Wert) |

**R-R11:** *„Ein registrierter Befund darf nur von einer Messung umgestoßen
werden, die ihn ZUERST reproduziert."*

---

# § 2 ✔ Die Basis reproduziert exakt

| Kandidat | Symbole | Tage | zulässige Mengen | Register sagt |
|---|---|---|---|---|
| `long_bias` | **122** | 1.715 | 20 %, 50 %, frei → **3** | 3 ✔ |
| `top_bias` | **122** | 1.415 | 50 %, frei → **2** | 2 ✔ |
| `taker_bias` | **122** | 1.605 | 20 %, 50 %, frei → **3** | 3 ✔ |

Register: *„H20 · 122 Symbole · rund 1.400 bis 1.736 Tage"* — **getroffen**.

---

# § 3 Die Urteile

| Kandidat | Menge | Wirkung | Band | Urteil |
|---|---|---|---|---|
| **`long_bias`** | 20 % | +0,0445 | [−0,0029 … +0,0868] | trägt nicht |
| | 50 % | +0,0132 | [−0,0079 … +0,0313] | trägt nicht |
| | frei | −0,0001 | [−0,0298 … +0,0301] | trägt nicht |
| **`top_bias`** | 50 % | +0,0001 | [−0,0221 … +0,0212] | trägt nicht |
| | frei | −0,0197 | [−0,0569 … +0,0129] | nicht trennbar |
| **`taker_bias`** | 20 % | +0,0292 | [−0,0022 … +0,0608] | trägt nicht |
| | **50 %** | **+0,0177** | **[+0,0038 … +0,0342]** | ⚠️ **TRÄGT** |
| | frei | +0,0002 | [−0,0098 … +0,0095] | trägt nicht |

## 3.1 ✔ Die Kontrollen halten

| | |
|---|---|
| **Referenz `oi_aenderung`** | trägt auf **3 von 3** (+0,0469 / +0,0213 / +0,0125) — **der Aufbau stimmt** |
| **`zufall`** | trägt auf **keiner** der 4 Mengen |

⚠️ Ohne die Referenz wäre ein Nullbefund nicht von einem kaputten Aufbau zu
unterscheiden. Sie ist der Grund, warum diesem Lauf zu trauen ist.

---

# § 4 ⚠️ Die eine Abweichung — `taker_bias`

| | |
|---|---|
| **Register** (06.09.) | *„trägt auf KEINER der 3 zulässigen Mengen"* |
| **Heute** | trägt auf **1 von 3** (50 %: +0,0177 [+0,0038 … +0,0342]) |

➤ **Das Gesamturteil bleibt trotzdem „trägt nicht"** — und zwar aus der
Regel, die das Werkzeug selbst nennt:

> *„Ein Kandidat, der nur auf EINER von mehreren zulässigen Mengen trägt,
> ist nicht robust — das ist die Lehre aus N-73."*

⚠️ **Aber die Abweichung ist real und gehört benannt.** Mögliche Ursachen,
ungeprüft: mehr Tage seit dem 07.09., oder das Register fasst zusammen, wo
der Lauf differenziert. **Eine Vermutung ist hier keine Erklärung.**

---

# § 5 ⭐ Die Zahl, die meine eigene Messung korrigiert

```
long_bias gegen top_bias: +0.947   (N-17b: +0,955)  - REPRODUZIERT
```

**Ich hatte zwischen meinem K4 und K5 eine Korrelation von −0,046 gemessen**
und daraus geschlossen, sie seien „weitgehend unabhängig".

➤ **Beides stimmt — weil es verschiedene Größen sind:**

| | |
|---|---|
| `top_bias` | **roh** = `top_konten_verh` → korreliert mit `long_bias` zu **+0,95** |
| mein K4 | **Differenz** = `top_konten_verh − konten_verh` → korreliert zu **−0,05** |

⚠️ **Meine Entflechtung prüfte also nicht, was das Register meint.** Dass K4
bedingt fiel, bleibt richtig — aber die Aussage „die beiden sind
unabhängig" war auf die falsche Größe bezogen.

---

# § 6 ⚠️ Was die Redundanztabelle sagt — und was sie NICHT prüft

| Kandidat | funding | turnover | oi_aenderung |
|---|---|---|---|
| `long_bias` | +0,117 | +0,129 | **+0,004** |
| `top_bias` | +0,160 | +0,119 | +0,013 |
| `taker_bias` | +0,013 | +0,050 | +0,011 |

✔ `long_bias` ist von `oi_aenderung` **unabhängig** (+0,004) — obwohl beide
aus derselben Quelle stammen.

⛔ **Die `rsi`-Redundanz aus N-17b (05.09.) ist hier NICHT geprüft.** Das
Werkzeug misst gegen funding, turnover und oi_aenderung — nicht gegen `rsi`.
**Die zweite Belastung von `long_bias` bleibt damit offen.**

---

# § 7 Das Ergebnis

| | |
|---|---|
| ✔ **R-R11 GEHALTEN** | Basis exakt, `long_bias` 0/3, `top_bias` 0/2 — beide reproduziert |
| ✔ **Kontrollen sauber** | Referenz trägt 3/3, `zufall` 0/4 |
| ✔ **Spearman 0,947 reproduziert** | gegen 0,955 aus N-17b |
| ⚠️ **Eine Abweichung** | `taker_bias` 1/3 statt 0/3 — Gesamturteil unverändert, Ursache ungeklärt |
| ⛔ **Offen** | die `rsi`-Redundanz |

➤ **Damit ist die Vorbedingung erfüllt**, um die Kandidaten auf der
HEBEL-Frage zu messen — der Spur, die das Register selbst als offen
ausweist: *„gegen `bewegung_r` gefallen, also gegen die SPOT-Frage. Die
HEBEL-Frage ist `barriere` — dagegen ist er NIE gemessen."*
