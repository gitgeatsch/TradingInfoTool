# Vorabfestlegung 8 — B0: trägt `oi_aenderung` auch **ohne** Fünftel 4?

**24.09.2026, geschrieben VOR der Messung.** Pflichtschritt B0 aus
`Umbauplan_Hebel_eigene_Bewertung_24_09.md`, Blocker A (Befund 2.574).

---

# § 1 Die Frage

> **2.573 hat `oi_aenderung` über alle fünf Fünftel gemessen (+0,0069).
> Trichterstufe 6 sperrt das oberste Fünftel — es erreicht die Bewertung
> nie. Trägt der Beitrag auch auf den Fünfteln 0–3?**

Der Code, um den es geht (`agent/rollen_lauf.py:1608`):

```python
elif _oi_f >= 4:
    durchlauf.verloren(symbol, "terminmarkt", "OI-Aufbau im hoechsten Fuenftel ...")
    return
```

⚠️ Die Sperre greift für `strategie == "einstieg"` **ohne Bestand** — also
genau die Lage `hebel × einstieg`.

---

# § 2 ⚠️⚠️ Die Sperre ist eine Eigenschaft des ANKERS, nicht des Kandidaten

**Das entscheidet die Bauform.** Stufe 6 wirft den Anker aus der **ganzen
Kette** — unabhängig davon, welcher Beitrag gerade bewertet wird.

➤ Die gesperrten `(Tag, Symbol)` werden **einmal** aus der
`oi_aenderung`-Welt bestimmt und dann aus **allen fünf** Kandidatenwelten
entfernt — auch aus `zufall`.

⛔ **Falsch wäre**, nur die `oi_aenderung`-Welt zu kürzen. Dann liefe die
Kontrolle auf einer anderen Menge als der Kandidat, und der Vergleich wäre
keiner.

---

# § 3 Die Planung

| | |
|---|---|
| **Werkzeug** | `k1c_hebel_barriere.py` — **dasselbe wie 2.573**, keine Nachbildung |
| **Änderung** | genau eine: Schalter `--ohne-oberstes-fuenftel` |
| **Vorgabe** | **aus**, damit ein Aufruf ohne Argument 2.573 bitgleich reproduziert (R-R11) |
| **Sonst unverändert** | `--horizont 3`, `--ab 2023-01-01`, `--menge auto`, Saat 20260909 |
| **Fünftel** | oberste 20 % der Tagesverteilung von `oi_aenderung` — dieselbe Definition wie `marktrang.oi_fuenftel` |

## 3.1 Was mitläuft

1. **R-R11 zuerst:** derselbe Lauf **ohne** den Schalter muss 2.573
   reproduzieren. Ohne das wird nichts umgestoßen.
2. **Wie viele Anker fallen weg** — erwartet rund 20 %, gemessen wird es.
3. **Die Kontrolle `zufall`** muss auf der gekürzten Menge sauber bleiben.
4. **Die Trennschärfe** — auf einer um ein Fünftel kleineren Menge kann
   sie steigen, und dann ist ein Nullbefund eine **Datendecke**, kein
   Ergebnis.

---

# § 4 Die Entscheidungsregel — vor der Messung

| Ergebnis auf den Fünfteln 0–3 | Entscheidung |
|---|---|
| **R-R11 fällt** | ⛔ **Stopp.** Dann ist der Schalter das Problem, nicht die Menge |
| **`oi_aenderung` trägt**, Kontrolle sauber | ✔ **Blocker A ist entschärft** — der Umbau geht weiter mit Schritt B. ⚠️ Die Stufen werden dann auf **dieser** Menge kalibriert, nicht auf der vollen |
| **Trägt nicht**, Kontrolle sauber, Trennschärfe reicht | ⛔ **Der Umbau entfällt.** Die Wirkung von 2.573 kam aus dem gesperrten Fünftel. 2.573 bleibt richtig — es gilt dann für eine Menge, die die Kette nicht sieht |
| **Trägt nicht, Trennschärfe reicht nicht** | ⚠️ **nichts entschieden** — Datendecke. Dann ist zu prüfen, ob die Sperre selbst gemessen ist |
| **Kontrolle `zufall` trägt** | ⛔ **Lauf ungültig** |

⚠️⚠️ **Wird nicht nachverhandelt.** Zeile 3 ist ein reguläres Ergebnis,
kein Scheitern — sie war im Umbauplan als *wahrscheinlichste
Abbruchursache* benannt, **bevor** gemessen wurde.

## 4.1 Die Vorhersage, vor dem Lauf (Methodik 2.80)

**Erwartung: der Beitrag trägt schwächer, aber er trägt.** Begründung: ein
Fünftelbeitrag hängt typischerweise am Extrem, aber `oi_aenderung` war in
2.573 auf `--menge auto` = 50 % gemessen — also ohnehin nicht nur auf dem
obersten Fünftel. Ein vollständiger Zusammenbruch wäre überraschend.

**Gegenthese:** die Wirkung verschwindet — dann war Stufe 6 bereits die
richtige Anwendung dieses Merkmals, und ein zweiter Zugriff als Beitrag
wäre Doppelzählung gewesen.

⚠️ **Beide Ausgänge sind brauchbar.** Der zweite beantwortet nebenbei die
offene Frage aus 2.481, ob Stufe 6 die richtige Bauform ist.

---

# § 5 Was B0 **nicht** entscheidet

- **Nicht**, ob die Sperre in Stufe 6 selbst gemessen richtig ist.
- **Nicht**, ob der Hebel wirtschaftlich wäre — `barriere` bleibt blind
  für *„wieviel ist zu holen"*.
- **Nicht** die Stufenlage. Das ist Schritt B.

---

# ERGEBNIS — 24.09.2026

## ✔✔ R-R11 zuerst: bitgleich reproduziert

Ohne den Schalter kommen Ziffer für Ziffer die Zahlen von 2.573:
funding +0,0002 (78 Blöcke) · turnover +0,0040 (58) · **oi_aenderung
+0,0069 [+0,0031 … +0,0108], 1.140 Tage, 76 Blöcke, TRÄGT** · schnitt
+0,0066 (51) · zufall −0,0034 (81).

## ➤➤➤ Das Ergebnis ohne Fünftel 4

Gesperrt: **28.191 Anker an 1.734 Tagen.**

| Kandidat | mit Fünftel 4 (2.573) | **ohne** Fünftel 4 (B0) |
|---|---|---|
| `funding` | +0,0002 | −0,0005 |
| `turnover` | +0,0040 | +0,0021 |
| **`oi_aenderung`** | **+0,0069 [+0,0031…+0,0108] TRÄGT** | **−0,0002 [−0,0032…+0,0030] trägt nicht** |
| `schnitt` | +0,0066 | +0,0003 |
| **`zufall`** | −0,0034 ✔ sauber | −0,0036 ✔ **sauber** |

Menge bleibt tragfähig: gelöst 51,7 → 51,5 % · Tage 1.140 → 1.060 ·
Blöcke 76 → 70. **Die Sperre nimmt Anker, kaum Tage.**

## ⛔ Entscheidung nach § 4

> **Der Umbau entfällt.** Die Wirkung von 2.573 kam aus dem Fünftel, das
> die Kette nie sieht.

⚠️ **2.573 bleibt richtig** — es gilt für eine Menge, die es im Betrieb
nicht gibt. Das ist kein Widerruf, sondern eine Eingrenzung.

## ⚠️⚠️ Zwei Vorbehalte, die dazugehören

1. **Die Trennschärfe des B0-Laufs liegt bei 0,0101 R**, die alte Wirkung
   bei 0,0069 — *formal* könnte die Anlage einen Effekt dieser Größe auf
   dieser Menge nicht sicher finden. Dagegen steht das **Band**, das oben
   bei +0,0030 endet, also deutlich unter +0,0069. Band und Trennschärfe
   sind **zwei Skalen**; beides wird ausgewiesen.
2. **Ein gepaarter Test ist nicht möglich.** Die Läufe messen auf
   verschiedenen Restmengen, es gibt keinen unbeteiligten Arm — dieselbe
   Lage wie bei N-67 (2.538). Ein Band um die Differenz wäre *„eine Zahl
   ohne Gegenstand"*. Genau deshalb stand die Entscheidungsregel vorab auf
   den Einzelläufen.

## ➤➤ Der Nebenbefund — und er ist der interessantere

**Es fallen alle vier.** Nicht nur `oi_aenderung`.

> **Das oberste OI-Fünftel ist der Ort, an dem in dieser Messung die
> Wirkung sitzt — für jeden Kandidaten. Und genau diese Menge sperrt die
> Kette weg.**

⚠️ Das ist **kein** Widerspruch zu 2.481 (die Sperre trägt +0,0145 R):
dort ist die **Trefferquote** niedriger, hier **trennen die Merkmale**
stärker. Beides kann gleichzeitig wahr sein.

⚠️⚠️ Es ist aber eine **offene Frage an Stufe 6**, und sie ist jetzt zum
ersten Mal gestellt: die Bewertung wird auf der Menge angewandt, auf der
sie am wenigsten zu sagen hat.

Befund **2.576-b0-fuenftel4-war-die-wirkung**.
