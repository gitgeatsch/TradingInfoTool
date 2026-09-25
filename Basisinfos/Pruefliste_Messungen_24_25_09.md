# Prüfliste — alle Messungen vom 24./25.09. gegen den Messstandard

**Nutzerauftrag 25.09.2026:** *„gehe alle bisherigen prüfungen auf fehler
oder nicht einhaltung der messtandards durch - wir können uns keine Fehler
leisten"*

---

# § 1 Der Standard, gegen den geprüft wird

```
messnorm.standardzeile():
  Bezug = nullpunkt · Nullwelten = 90. Perzentil über 40 Ziehungen
  Trennschärfe gegen denselben Bezug · gepflanzte Stärken bis 0,40 R
  Positivkontrolle 5 Ziehungen

FRAGEARTEN:   beitrag → SELEKTIERTE Menge (F-212)
              zaehlung → beliebig, aber BENANNT
ZIELGRÖSSE:   (hebel, einstieg) → barriere
HORIZONT:     (hebel, einstieg) → 3
```

---

# § 2 ⛔⛔⛔ Der schwerwiegendste Befund: alle neuen Werkzeuge sind Altbestand

| Werkzeug | `messnorm`-Verweise |
|---|---|
| `messe_hebel_dimension.py` | **0** |
| `messe_basisrate_vorhersagbar.py` | **0** |
| `messe_zusammenspiel_beitraege.py` | **0** |
| `messe_gleichstand_stundenbasis.py` | **0** |
| `messe_scharfe_bewegungen.py` | **0** |

**CLAUDE.md:** *„181 von 315 Messwerkzeugen sind Altbestand — **ein Befund
aus dieser Gruppe gilt nur mit Vorbehalt**."*

➤ **Damit stehen 2.583, 2.585, 2.586 und 2.587 unter diesem Vorbehalt.**

⚠️ Die Norm**werte** habe ich teils eingehalten (200 Nullwelten statt 40,
90. Perzentil) — aber **nicht aus `messnorm` gelesen**, sondern eigene
Konstanten gesetzt. Läuft die Norm weg, laufen meine Werkzeuge nicht mit.
Genau dafür gibt es `messnorm`.

---

# § 3 ⛔ Das Register wurde nicht gelesen

**Meine Kandidaten K2, K4, K5 sind seit dem 06.09. registriert:**

| mein Name | registriert als | Zustand |
|---|---|---|
| K5 `konten_verh` | **`long_bias`** | ✖ trägt nicht — 0 von 3 Mengen |
| K4 top minus retail | **`top_bias`** | ✖ trägt nicht — 0 von 2 Mengen |
| K2 `taker_verh` | **`taker_bias`** | ✖ trägt nicht — 0 von 3 Mengen |

**CLAUDE.md:** *„`REGISTER_Kandidaten.md` — hier VOR jeder neuen Messung
nachsehen."*

⚠️⚠️ **Und R-R11 ist damit verletzt:** *„Ein registrierter Befund darf nur
von einer Messung umgestoßen werden, die ihn ZUERST reproduziert."* Ich
habe neu gemessen, ohne den 06.09.-Befund zu reproduzieren.

## 3.1 ⚠️ Was das relativiert — aber nicht aufhebt

Die alten Urteile stehen auf **H20 · `bewegung_r` · Tagesbasis**, meine
Messung auf **6–72 h · `ergebnis_r` · Stundenbasis**. Das sind
**verschiedene Fragen**, kein direkter Widerspruch.

⚠️ **Aber genau das hätte VOR der Messung gesagt werden müssen**, nicht
danach. Und das Register nennt für `long_bias` eine zweite Belastung, die
ich nicht geprüft habe: *„NICHT unabhängig vom `rsi`"* (N-17b, 05.09.).
Meine Entflechtung prüfte K4 gegen K5 — **nicht gegen `rsi`.**

---

# § 4 Die einzelnen Messungen

| # | Messung | Frageart | Verstöße |
|---|---|---|---|
| **1** | `messe_scharfe_bewegungen` | `zaehlung` | ✔ Menge benannt · ⚠️ Altbestand |
| **2** | `messe_gleichstand_stundenbasis` (2.583) | `zaehlung` | ✔ zwei Gegenprüfungen · ⚠️ Altbestand |
| **3** | `messe_basisrate_vorhersagbar` (2.585) | `markt` | ⛔ **95. statt 90. Perzentil** · ⛔ **keine Trennschärfe** · ⛔ keine Positivkontrolle · ⚠️ Altbestand |
| **4** | `messe_zusammenspiel_beitraege` | `zaehlung` | ⛔ **Urteil ohne Nullpunkt** („Faktor 2 zu groß") · ⚠️ Altbestand |
| **5** | `messe_bewertung_kalibrierung` | `beitrag` | ✔ selektierte Menge als Schalter · ✔ 3 Kontrollen · ✔ R-R11 |
| **6** | `messe_hebel_dimension` (2.586) | `beitrag` | ⛔ **freie statt selektierte Menge** · ⛔ **keine Trennschärfe** · ⛔ keine Positivkontrolle · ⛔ **Register nicht gelesen** · ⚠️ Zielgröße abweichend · ⚠️ Altbestand |
| **7** | `messe_hebel_nachpruefung` | `beitrag` | ✔ selektiert · ✔ Trennschärfe (nach Korrektur) · ✔ Monotonie · ✔ beide Hälften · ⛔ keine Positivkontrolle |

## 4.1 ⛔ Die durchgängige Lücke: die POSITIVKONTROLLE

Der Standard verlangt **5 Ziehungen Positivkontrolle**. In **keiner** meiner
Messungen läuft sie.

⚠️ Teilweise ersetzt die Trennschärfe sie (gepflanzte Stärken **sind** eine
Positivkontrolle) — aber nur in Messung 7, und erst nach der Korrektur.

## 4.2 ⚠️ Abweichungen, die begründet sind

| | |
|---|---|
| **Zielgröße `ergebnis_r` statt `barriere`** | begründet in Vorabfestlegung 10 § 2 und durch 2.582 belegt: `barriere` wirft bei 6 h **97 %** der Fälle weg. ✔ Die Norm sieht das vor (*„wer bewusst eine andere misst, ruft `messnorm.pruefe` und begründet es"*) — ⛔ **aber ich habe `messnorm.pruefe` nicht gerufen** |
| **Horizont als Achse statt 3** | begründet in Vorabfestlegung 10 § 3; die Achse 6–72 h enthält die 3 Tage |
| **200 statt 40 Nullwelten** | strenger, nicht laxer |

---

# § 5 ⚠️ Was das für die Befunde bedeutet

| Befund | Lage |
|---|---|
| **2.583** Gleichstandsregel unschuldig | ✔ **hält** — eine Zählung mit zwei Gegenprüfungen, kein Urteil über einen Beitrag |
| **2.585** Basisrate nicht vorhersagbar | ⚠️ **Vorbehalt** — Perzentil abweichend, keine Trennschärfe. Der Kern (Streuung Faktor 3,13 über dem Nullpunkt) ist davon kaum berührt, die Vorhersage-Nullbefunde schon |
| **2.586** K5 gefallen | ⚠️ **Vorbehalt** — aber er sagt „trägt nicht", und die Fehler waren alle in Richtung **zu optimistisch**. Ein Nullbefund wird davon nicht falsch |
| **2.587** Querschnitt zu dünn | ✔ **hält** — reine Zählung (18 Symbole im Median) |

➤ ⭐ **Die Richtung rettet zwei davon:** meine Fehler machten die Messung
**optimistischer** (freie Menge, fehlende Trennschärfe). Ein Befund, der
trotzdem „trägt nicht" sagt, wird dadurch nicht schwächer.

⚠️ **Umgekehrt gilt das nicht für 2.585** — dort ist der Nullbefund die
Aussage, und fehlende Trennschärfe heißt: *„zu wenig gesehen"* ist nicht
ausgeschlossen.

---

# § 6 Was zu tun ist — nach Dringlichkeit

| # | | |
|---|---|---|
| **1** | ⛔ **R-R11 nachholen**: den 06.09.-Befund zu `long_bias` reproduzieren, bevor irgendetwas Neues gilt | blockierend |
| **2** | ⛔ **`rsi`-Redundanz prüfen** — das Register nennt sie für `long_bias`, meine Entflechtung hat sie übersehen | blockierend |
| **3** | ⛔ **Positivkontrolle** in die Werkzeuge | vor dem nächsten Befund |
| **4** | ⛔ **Die Werkzeuge an `messnorm` binden** statt eigene Konstanten | vor dem nächsten Befund |
| **5** | ⚠️ **2.585 nachziehen**: 90. Perzentil, Trennschärfe | vor Verwendung |
| **6** | ⚠️ **`messe_zusammenspiel_beitraege`**: Nullpunkt nachrüsten oder das Urteil zurücknehmen | vor Verwendung |

⚠️⚠️ **Punkt 1 und 2 stehen vor allem anderen** — auch vor P-1. Ohne sie
ist jeder weitere Befund auf derselben Spur wertlos.
