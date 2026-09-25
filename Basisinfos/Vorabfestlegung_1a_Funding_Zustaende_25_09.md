# Vorabfestlegung 14 — 1a: `funding` als ökonomische Zustände auf `barriere`

**25.09.2026, geschrieben VOR der Messung.** Arbeitsplan § 2, Schritt 1a.

---

# § 1 ⭐ Die FORMWAHL — begründet, wie verlangt

**Nutzervorgabe 25.09.:** *„sag mir ab jetzt immer WARUM als Schalter — eine
Begründung um dies für mich klar zu stellen."*

## 1.1 Warum NICHT Rangfünftel

**Gemessen am 25.09.** (reproduziert 2.551, das 32,5 % nannte):

| Bindungsanteil je Kalendertag | |
|---|---|
| Median | **31,4 %** |
| 75. Perzentil | 53,4 % |
| 90. Perzentil | **73,2 %** |
| Mittel | **35,4 %** |

➤ **An einem Viertel der Tage sind über die Hälfte der Funding-Werte
identisch.** Die Fünftel-Zuordnung ist dort willkürlich — und das ist eine
plausible Erklärung dafür, dass die Spanne (0,0121) unter der Auflösung
(0,0133) liegt.

⚠️ **Solange ein Drittel der Ränge zufällig vergeben wird, ist jede
Formdiskussion darüber verfrüht.**

## 1.2 Warum NICHT Schalter

**Das war der vierte Anlauf am 23.09. (2.554)** und endete mit:

> *„pflanzt man genau die behauptete Ordnung ein (Spanne 0,1104 R), findet
> die Anlage sie auf KEINER Quelle."*

⚠️ Und der Kernfund dort: *„Die registrierte Wirkung IST eine
Schalterwirkung"* — `messe_regel_wirksamkeit.py` misst `GRENZE = 0.80`.
**Fünf Stufen sind auf Spot nie gemessen worden.**

## 1.3 ⭐ Warum ZUSTÄNDE

| | |
|---|---|
| **Die Grenzen kommen aus der SACHE** | negativ (< 0) · normal (0 … Standardrate) · hoch (> Standardrate) |
| ⭐ **Drei Probleme entfallen gemeinsam** | Bindungen, Monotoniefrage und Tagesbesetzung sind **alle** Folgen der Rangbildung |

## 1.4 ⭐⭐ Warum JETZT — der wichtigste Teil

Die Zustände sind am 23.09. gemessen worden und an **B6** gescheitert
(2.553): `normal − hoch` = +0,2331 R [+0,0392 … +0,4623], aber 1. Hälfte
+0,3623, 2. Hälfte +0,1198 mit Null im Band.

➤ **Das war auf `bewegung_r`. Auf `barriere` sind sie UNGEMESSEN.**

⚠️ **Und dort ist die Form nachweislich besser:** auf `bewegung_r` ist
`funding` nicht monoton (Buckel bei Fünftel 1, reproduziert), auf `barriere`
**monoton fallend** über alle fünf.

---

# § 2 ⭐⭐⭐ Die ASYMMETRIE-Anforderung — Nutzervorgabe als Kriterium

**Nutzervorgabe 25.09., wörtlich:**

> *„auch ein ‚negativer' Beitrag hat wert — somit sehr hohes Funding schlecht
> für hebel wäre eine Festlegung. [...] Aber wir brauchen auch ‚positive'
> Beiträge nicht nur Sperren. ALSO muss es ‚Lagen' geben welche einen Hebel
> RECHTFERTIGEN und andere die diesen nicht zulassen bzw. schlecht sind."*

## 2.1 Wie diese Anforderung messbar wird

`q = basisrate + punkte/100` mit `basisrate = 1/(1+CRV) = 0,3333`. Und
`Kelly > 0` genau dann, wenn `q > 0,3333`.

| | |
|---|---|
| **rechtfertigt Hebel** | Zustandspunkte **> 0** → `q` über der Kelly-Nullstelle |
| **lässt keinen zu** | Zustandspunkte **< 0** → `Kelly ≤ 0`, kein Hebel |

➤ **Die Asymmetrie ist erfüllt, wenn mindestens ein Zustand positive und
mindestens einer negative Punkte bekommt.** Das ist ein **Kriterium**, nicht
nur eine Beobachtung.

⚠️⚠️ **Und es ist ein echtes Risiko:** bei den Rangfünfteln war es erfüllt
(Fünftel 0–2 positiv, 3–4 negativ). Bei **drei** Zuständen könnte es
kippen — wenn etwa alle drei über oder alle unter dem Mittel liegen.

## 2.2 ⚠️ Ein Fund, der dazugehört

**Die Formel ist um 1,26 Punkte zu pessimistisch.** Gemessen (25.09.):

| | |
|---|---|
| Kelly-Nullstelle (Formel) | 0,3333 |
| **echte Basisrate** auf `barriere`/H3, Menge frei | **0,3459** |

➤ Die Formel sperrt damit Lagen, die tatsächlich über break-even liegen.

✔ **Konservativ ist hier richtig** — die Nullstelle fragt *„besser als
break-even"*, und das ist der richtige Bezug; die echte Basisrate zu nehmen
würde *„besser als der Durchschnitt"* fragen, eine andere Frage.

⚠️ **Aber der Puffer ist ein Nebeneffekt, kein Entwurf.** Er gehört
benannt, nicht als Absicht ausgegeben.

---

# § 3 Was gemessen wird

| | |
|---|---|
| **Kandidat** | `funding`, drei Zustände |
| **Grenzen** | negativ (< 0) · normal (0 … Standardrate) · hoch (> Standardrate) |
| ⚠️ **Nicht AN der Standardrate schneiden** | 2.553: *„meine frühere Dreiteilung schnitt AN der Standardrate und isolierte den Massepunkt statt eines Zustands. Ihr Negativergebnis zählt nicht"* |
| **Zielgröße** | `barriere` (aus `messnorm.ZIELGROESSE_JE_LAGE`) |
| **Horizont** | **3** (aus `messnorm.HORIZONT_JE_LAGE`) |
| **Lage** | `hebel × einstieg`, `simuliert=True` |
| **Menge** | `beitrag` → selektiert, über `zulaessige_mengen()` |

## 3.1 Die Norm

| | |
|---|---|
| **Nullpunkt** | 90. Perzentil über 40 Ziehungen — **aus `messnorm`**, keine eigene Konstante |
| **Trennschärfe** | gepflanzt in **neutralisierte** Menge, Stärken bis 0,40 R |
| **Negativkontrolle** | `zufall` |
| **B6** | ⭐ **Ausschlusskriterium, nicht Beiwerk** — daran ist der 23.09. gescheitert |
| **gepaart** | die Abstände **gepaart** rechnen, nicht über ungepaarte Mittelwerte (2.554: genau dieser Fehler meldete „widerlegt", während der gepaarte Abstand das Gegenteil sagte) |
| **Belegung** | je Zustand die Anteile ausweisen — 22,6 / 30,2 / 47,3 % am 23.09. |

---

# § 4 ⭐ Die Entscheidungsregel — VOR der Messung

| Ergebnis | Entscheidung |
|---|---|
| ✔ **Ein Zustand positiv, einer negativ, B6 hält, Kontrolle sauber, über Nullpunkt** | ⭐ **Die Zustände werden die Hebelform.** Danach R-R9 (Schwelle je Lage) |
| ⛔ **Alle drei Zustände gleichgerichtet** | **Asymmetrie-Anforderung verletzt** — die Form taugt nicht, auch wenn sie trennt |
| ⛔ **B6 verletzt** | wie am 23.09.: **kein Umbau**. Ein Effekt in einer Hälfte ist keiner |
| ⛔ **unter dem Nullpunkt** | die Zustände trennen nicht besser als die Ränge — dann bleibt es bei 2.588 (Grauzone) |
| ⚠️ **Trennschärfe reicht nicht** | nichts entschieden, Datendecke |
| ⛔ **`zufall` trägt** | Lauf ungültig |

⚠️⚠️ **Wird nicht nachverhandelt.**

---

# § 5 Die Vorhersage

**Erwartung: `hoch` negativ, `normal` positiv, `negativ` unentschieden — und
B6 wird knapp.**

**Begründung:** Der 23.09. fand auf `bewegung_r` genau das — *„die halbe
Lehrmeinung trägt: hohes Funding ist belegt schlechter. Für ‚niedrig ist
gut' gibt es KEINE Stütze. Die erwartete U-Form ist in Wahrheit eine
Schräge nach unten am oberen Rand."* Auf `barriere` erwarte ich dasselbe
Muster, **schwächer** (die Wirkungen sind dort rund 4× kleiner).

⚠️ **Wenn nur `hoch` trägt und `normal`/`negativ` sich nicht unterscheiden,
ist die Asymmetrie-Anforderung trotzdem erfüllt** — `hoch` negativ, die
übrigen positiv. Das wäre der wahrscheinlichste brauchbare Ausgang.

---

# § 6 Was diese Messung **nicht** entscheidet

- **Nicht** die Kombination mit `turnover`/`oi_aenderung` (Schritt 1d).
- **Nicht** die fünf ungemessenen Kandidaten (Schritt 2).
- **Nicht** `r_min` (offene Frage: hebt die schlechteste Lage auf 3,00x an).
- **Nicht** die Klammer (geklärt, 2.589).
