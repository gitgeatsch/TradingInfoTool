# Vorabfestlegung 4 — tragen die unteren vier Fünftel eine Ordnung?

**23.09.2026, geschrieben VOR der Messung.** Nutzerhaltung, die sie
auslöst: *„entweder ich verstehe den Schalter nicht oder wir wenden den
Beitrag falsch an."*

---

## § 1 Der Anlass — zwei Code-Funde, nicht zwei Vermutungen

### Fund 1: die registrierte Wirkung IST eine Schalterwirkung

`messe_regel_wirksamkeit.py` — das Werkzeug, aus dem die Registrierung
stammt — misst **eine Sperre**, nicht fünf Stufen:

```python
GRENZE = 0.80          # 20 % werden gesperrt - wie bei Funding
frei = (r < GRENZE) if oben_sperren else ...
```

und im Kopf steht die Richtung, vorab festgelegt:

> `funding` — hohes Funding = überhitzt → **OBEN sperren**
> (Kontrolle: der bereits belegte Fall, muss **+0,024 R** reproduzieren)

➔ **Die +0,0246 R, auf denen `funding` registriert ist, sind der Ertrag
einer Sperre des obersten Fünftels.** Ein Schalter. Fünf Stufen sind nie
gemessen worden.

### Fund 2: die Live-Tabelle ist eine UMRECHNUNG, keine Messung

`rechne_funding_beitrag.py` nimmt die fünf Fünftel-Mediane und rechnet sie
in Punkte um. Kein Band, keine Trennschärfe, keine Kontrolle. Der Kopf
sagt es selbst:

> ⚠️ **IN-SAMPLE.** Diese Zahlen stammen aus derselben Messung, die den
> Befund ergeben hat.

Und dasselbe Werkzeug trägt eine **eigene Vorabfestlegung**:

> **nutzbar** — die Stufen sind **MONOTON** über die Fünftel
> **nicht nutzbar** — sonst; dann bekommt die Zelle **KEINEN** Beitrag

**Reproduziert am 23.09.** (2.399 Kalendertage, H20):

| Fünftel | Bewegung | geschrumpfte Punkte | live |
|---|---|---|---|
| 0 | −0,0639 R | +0,76 | +0,82 |
| **1** | **−0,0262 R** ◀ das beste | **+1,39** | **+1,30** |
| 2 | −0,0962 R | +0,22 | +0,12 |
| 3 | −0,1476 R | −0,64 | −0,54 |
| 4 | −0,2127 R | −1,72 | −1,70 |

➔ **Nicht monoton** (0 → 1 steigt). Nach der eigenen Regel des Werkzeugs
ist diese Tabelle **nicht nutzbar** — und sie läuft seit dem 30.08. live.

⚠️ R-R11 erfüllt: die Live-Tabelle ist reproduziert, die Abweichung liegt
bei ≤ 0,09 Punkten (andere Tagesmenge: 2.399 statt 2.369).

---

## § 2 Die Frage, präzise

**Die unteren vier Fünftel unterscheiden sich in der Live-Tabelle um bis
zu 1,85 Punkte** (+1,39 gegen −0,64). Fünftel 4 dagegen ist in beiden
Formen praktisch gleich.

> **Tragen diese Unterschiede zwischen den unteren vier Fünfteln eine
> Ordnung — oder sind sie Rauschen, das als Signal ausgegeben wird?**

Das ist die ganze Differenz zwischen Regler und Schalter. Alles andere an
den beiden Formen ist identisch.

### Die zwei Tabellen im Vergleich

| | 0 | 1 | 2 | 3 | 4 | Mittel |
|---|---|---|---|---|---|---|
| **HEUTE** (Regler) | +0,82 | +1,30 | +0,12 | −0,54 | **−1,70** | ≈ 0 |
| **SCHALTER** | +0,43 | +0,43 | +0,43 | +0,43 | **−1,72** | ≈ 0 |

⚠️⚠️ **Beide sind mengenneutral konstruiert:** gleiches Mittel, nahezu
identisches Fünftel 4. Damit misst der Vergleich die **Ordnung**, nicht
die **Härte** — die Falle aus `feedback_zwei_regeln_vergleichen_auswahlanteil_angleichen`.

Der Schalterwert +0,43 ist hergeleitet, nicht gewählt: Fünftel 4 liegt
−0,1292 R unter dem Mittel der **übrigen vier** (−0,0835 R); × 1/(1+CRV)
× 100 = −4,31 Punkte roh, geschrumpft −2,15, zentriert auf Mittel null
ergibt (+0,43 ×4, −1,72).

---

## § 3 Die Messung

| | |
|---|---|
| **Menge** | ⚠️ die **SELEKTIERTE** — 20 %, `messe_beitrag_auf_auswahl._auswahl_maske` |
| **warum** | die stehende Vorbedingung in `wahrscheinlichkeit.py:404`. F-212: die Beiträge wirken auf **1,5 %** der Anker; auf der freien Menge gemessene Gegenbefunde (N-56, N-58) sind genau daran gescheitert |
| **Horizont** | H20 |
| **Zielgröße** | `bewegung_r` der Durchgelassenen |
| **Auswahl** | die besten **50 %** nach Punktsumme (funding + turnover) — **je Form gleich viele**, damit der Auswahlanteil identisch ist |
| **Klammer** | Kalendertag (R-R8 B2) |
| **Band** | Blockbootstrap, Blocklänge `messnorm._block(20)` = 60 |
| **Entscheidung** | auf der **gepaarten** Differenz je Tag — nicht auf zwei Mittelwerten (Lehre aus 2.545 und 2.553) |
| **B6** | beide Historienhälften einzeln |
| **Positivkontrolle** | eine echte Ordnung über die unteren vier wird **gepflanzt**; findet die Anlage sie nicht, ist ein Nullergebnis nicht deutbar |

---

## § 4 Die Entscheidungsregel — vor der Messung

| Ergebnis `HEUTE minus SCHALTER` | Deutung | Entscheidung |
|---|---|---|
| Band **über** null, **beide** Hälften | die Abstufung trägt | ✔ **Regler bleibt.** 2.552 geschlossen, die Live-Tabelle ist gerechtfertigt |
| Band **unter** null, **beide** Hälften | die Abstufung **schadet** | ⛔ **Umbau auf SCHALTER**, danach Schwelle nach R-R9 neu kalibrieren |
| Band **mit** null, Positivkontrolle ✔ | die Abstufung trägt **nichts** | ➤ **Nutzerentscheidung.** Messgleichstand; für den Schalter spricht allein die Sparsamkeit (eine unbelegte Behauptung weniger), gegen ihn, dass kein Gewinn belegt ist |
| Band mit null, Positivkontrolle ✖ | die Anlage ist zu grob | ⛔ **nichts entschieden** — kein Umbau, der Punkt bleibt offen |
| Hälften **widersprechen** sich | B6 verletzt | ⛔ **nichts ändern** (wie 2.553) |

⚠️⚠️ **Diese Festlegung wird nicht nachverhandelt.** Der dritte Fall ist
ausdrücklich **keine** Messentscheidung und wird auch nicht als eine
ausgegeben.

⚠️ **Was diese Messung NICHT beantwortet:** ob `funding` überhaupt trägt.
Das ist registriert (+0,0246 R) und am 06.09. auf der selektierten Menge
reproduziert (F-212: +0,0274). Hier steht **nur die Form** zur Frage.

---

# ERGEBNIS — 23.09.2026

## ⛔ Nichts entschieden — und *warum* ist der eigentliche Befund

### Der Vergleich: Gleichstand auf beiden Quellen

| Quelle | `HEUTE minus SCHALTER` | Tage |
|---|---|---|
| `gesamt` | +0,00776 R [−0,04555 … +0,06605] | 1.006 |
| **`frei`** (die Live-Größe) | −0,00499 R [−0,02916 … +0,01703] | 2.015 |

Beide Historienhälften ebenfalls mit Null im Band, **kein** Widerspruch.

⚠️ **Die Formen sind dabei nicht folgenlos:** sie wählen an **19,5 %** der
Durchlässe verschiedene Werte aus; nur 18,4 % der Tage haben eine völlig
gleiche Auswahl. Der Gleichstand kommt also nicht daher, dass beide
dasselbe täten.

### ⛔⛔ Aber der Gleichstand sagt nichts

Pflanzt man **genau die Ordnung ein, die die Live-Tabelle behauptet** —
in R: +0,0237 / +0,0525 / −0,0183 / −0,0579, Spanne **0,1104 R** —, dann
findet die Anlage sie **nicht**:

| Quelle | eingepflanzt und gemessen | |
|---|---|---|
| `gesamt` | +0,02200 R [−0,03079 … +0,08015] | ✖ |
| `frei` | +0,00910 R [−0,01541 … +0,03169] | ✖ |

> **Die behauptete Abstufung liegt unter der Nachweisgrenze.** Sie lässt
> sich mit dieser Datenlage weder bestätigen noch widerlegen — auch dann
> nicht, wenn man sie künstlich einpflanzt.

## ➤ Was daraus folgt

**Die Formfrage ist keine Messfrage mehr.** Sie kann nur noch nach
**Sparsamkeit** entschieden werden: eine unbelegte Behauptung weniger
gegen einen unveränderten Status quo.

⚠️ Genau das lag am **06.09.** schon einmal vor — **N23-E1**, ausdrücklich
als *Nutzerentscheidung* gekennzeichnet: *„Die fünfstufige Bauform ist für
**keine** Größe belegt."* Umgesetzt wurde es nie.

## ⛔ Eigener Werkzeugfehler, vor dem Ergebnis gefunden

Die erste Fassung brach die Positivkontrolle bei *„3 von 5 gepflanzten
Stärken gefunden"* ab und meldete auf `frei` einen **Messgleichstand**.

Diese Grenze ist **willkürlich**. Sie belegt, dass die Anlage
*irgendeinen* Effekt findet — nicht **den**, um den es geht:

| | |
|---|---|
| Auflösung der Anlage | 0,10 R Leiterstärke = **0,30 R** Spanne |
| behauptete Ordnung | **0,11 R** Spanne |
| Abstand | **Faktor 2,7 zu grob** |

Die Kontrolle prüft jetzt die **behauptete** Ordnung. Damit kippt das
Urteil von „Gleichstand" auf „nichts entschieden" — und das ist die
ehrliche Lage.

## Was **nicht** folgt

**Nicht, dass `funding` nicht trägt.** Der Beitrag ist registriert
(+0,0246 R) und am 06.09. auf der selektierten Menge reproduziert
(F-212: +0,0274). Zur Frage stand allein die **Form**.

Befund **2.554-funding-form-unter-nachweisgrenze**.
