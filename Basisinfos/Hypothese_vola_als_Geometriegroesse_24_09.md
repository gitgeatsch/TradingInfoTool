# Hypothese — `vola` ist keine Richtung, sondern die Geometriegröße

**24.09.2026.** Nutzeridee: *„vola wäre ein geeigneter Kandidat — allein
u. U. nicht ok, aber prüfe ob und wie fachlich vola **mit den anderen
Beiträgen kombiniert** als Beitrag in Frage kommt. Mach zuvor eine
Hypothese."* Und: *„recherchiere intern und extern, was wurde bereits
gemessen, was davon nicht korrekt nach unseren Standards, mit welchem
Beitrag korreliert vola."*

---

# § 1 Die interne Recherche — `vola` ist der best­gemessene Kandidat

| Messung | Ergebnis |
|---|---|
| **Wirkung** | +0,0100 (H20) · +0,0033 (H5 voll) — trägt auf allen drei Läufen |
| **Form** | **einzige belegte Dreiteilung**, beide Hälften, 2/2 Nachbarn getrennt (N23-E1) |
| **Umrechnung** | ✔ **einzige geprüfte**: Faktor 0,82–0,90, Korrelation **+0,990**, alle Vorzeichen richtig (N19) |
| **Abdeckung** | **516 von 516** Symbolen — die einzige Größe, die überall wirkt (N12) |
| ⛔ **Richtung** | **keine.** Richtungsrein −0,00041 [−0,00287 … +0,00194], 2/5, Drittel ohne Ordnung (N-52) |

## ⚠️⚠️ Aber kein Nullbefund — der Registereintrag sagt es selbst

> *„+3,1 Punkte auf die **Auflösungsquote** sind der größte saubere Effekt
> des Tages. `vola` gehört in die **GEOMETRIE- und HORIZONTWAHL** — und
> über `hebel = verlustanteil / stop_rel` fällt daraus der Hebel. Das ist
> die als fehlend geführte **Horizont-Achse**."*

Der Mechanismus ist benannt: **ruhige Assets lösen ihre Barrieren
überhaupt auf** (+0,03088), statt flach auszulaufen — und ein flacher
Auslauf zählt als 0, genau wie ein Stop.

---

# § 2 Womit `vola` korreliert — gemessen, nicht geschätzt

**N1-Rangtest, 39 Mischungen (06.09.):**

| | erklärt von `vola` | |
|---|---|---|
| `funding` | **3 %** (p = 0,325) | ➤ praktisch **unabhängig** |
| `turnover` | **18 %** (Rang 1 von 40, p = 0,025) | ➤ schwach, aber belegt |

**Und die Schichtung (N1-C / N1-D):**

| | |
|---|---|
| `vola` **in** `funding` | +0,00309 ✔ trägt |
| `vola` **in** `turnover` | +0,00281 ⚠️ nicht trennbar |
| **`turnover` in `vola`** | **+0,02217** ✔ — **wird stärker** |

➤ **Die Interaktion ist gerichtet:** `turnover` trägt *innerhalb* der
`vola`-Schichtung deutlich stärker als sonst. Umgekehrt nicht.

⚠️ **Gegenbefund, der dazugehört:** V9 (10.09.) — *„unabhängig von
funding, aber **geschichtet nicht mehr trennbar**"* (echter Nullbefund,
0,05 R). Die Schichtung nach `funding` bringt nichts.

---

# § 3 ⛔ Was nach heutigem Standard NICHT korrekt vermessen ist

| | |
|---|---|
| **`vola ODER turnover`** | ⚠️ **VOR dem Messstandard** (06.09.). Wert +0,00777, mengenkontrolliert **+26 % bis +34 %** über der besten Einzelgröße, beide Hälften, drei Saaten — **aber unter anderen Regeln entstanden** |
| **N1-V2 am Randmaß** | Richtungseffekt −0,00345 gefunden; *„durch N-52 nicht widerlegt (andere Zielgröße), steht aber unter Verdacht, weil das Randmaß sich den Schiefe-Kanal mit `bewegung_r` teilt"*. **Richtungsreine Nachmessung am Rand steht aus** |
| **N-73 / Kriterium 2** | `vola` trägt nur in **1 von 3** Beitragsmengen — *„der wackligste Kandidat"* |

---

# § 4 Die externe Recherche — die Praxis trennt genau so

Die Literatur zum **Volatility Targeting** trennt beides ausdrücklich:

> *„Position sizing tells you how much capital is actually at risk. **These
> are two separate decisions**, and most newcomers treat them as one. **The
> trend signal itself is deliberately not the focus.**"*

Und die Mechanik ist Standard in Managed Futures: Positionsgröße =
`Kapital × Zielvolatilität / realisierte Volatilität`; volatilere Märkte
bekommen **kleinere** Positionen. Die Turtles skalierten in Einheiten von
`N` — einem geglätteten 20-Tage-ATR, also genau der Größe, die hier `vola`
heißt.

➤ **Intern und extern stimmen überein:** Volatilität steuert die **Größe**,
nicht die **Richtung**.

---

# § 5 ➤ Die Hypothese

> **H-vola:** `vola` ist kein Richtungsbeitrag und darf keiner sein. Es ist
> die **Geometriegröße**: es sagt vorher, **ob ein Trade überhaupt
> aufgelöst wird**, und steuert darüber Stop-Weite, Horizont — und damit
> den Hebel.
>
> **In Kandidat D** (*`q` entscheidet über das OB, die Geometrie über das
> WIEVIEL*) ist `vola` die fehlende Geometriegröße.

## Warum das die Prüfsteine erfüllt

| | |
|---|---|
| **P1** kein Entfernen | ✔ es skaliert, es sperrt nicht |
| **P2** stetig | ✔ Dreiteilung belegt, Umrechnung geprüft |
| **P3** kein Asset-Vorurteil | ✔ keine Richtungsaussage — das ist hier gerade der Vorteil |
| **P4** Bewertung statt Fakt | ⚠️ **hier sitzt die Gefahr.** „Dieses Asset schwankt stark" ist ein **Fakt**. Zur Bewertung wird es erst über die gemessene **Auflösungswahrscheinlichkeit** — und die ist eine Aussage über das, was kommt |
| **P5** eigene Zielgröße | ✔ auf `barriere` gemessen, Umrechnung dort geprüft (0,90) |

## ⚠️⚠️ Was die Hypothese NICHT behauptet

- **Nicht**, dass `vola` die Trefferquote hebt. Das ist widerlegt (N-52).
- **Nicht**, dass die Kombination `vola ODER turnover` gilt — sie ist vor
  dem Messstandard gemessen und müsste **neu** geprüft werden.
- **Nicht**, dass damit der Hebel gerechtfertigt wäre. Eine Geometriegröße
  sagt, **wie viel** man setzen darf, wenn man setzt — **nicht**, ob sich
  das Setzen lohnt. Das bleibt an `q`, und `q` trägt es nicht (2.568).

---

# § 6 Was zu messen wäre — und in welcher Reihenfolge

| # | | warum |
|---|---|---|
| **1** | Trägt `turnover` **in** der `vola`-Schichtung auf dem **heutigen Standard** stärker? (N1-D war 06.09.) | die Interaktion ist der stärkste interne Hinweis (+0,02217) |
| **2** | `vola ODER turnover` **normgerecht** nachmessen | +26–34 % Vorsprung, aber vor dem Standard |
| **3** | Richtungsreine Nachmessung **am Randmaß** | steht als offener R-R11-Punkt |

⚠️ **Punkt 1 zuerst**, weil er die Nutzerfrage direkt beantwortet — „wie
kommt `vola` **kombiniert** in Frage" — und weil er die kleinste Messung
ist.
