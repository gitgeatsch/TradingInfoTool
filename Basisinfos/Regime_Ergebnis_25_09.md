# Ist der Marktzustand vorab erkennbar? — Nein

**25.09.2026** · Schritt 3 des Hebel-Neubaus · Befund **2.599** ·
Vorabfestlegung 17 · `messe_regime_rollierend.py`

**116 Symbole · 3.237.922 Anker · zwei Fenster · nur lesend**

---

# § 1 Das Ergebnis

> ⛔ **H0 ist nicht widerlegt.** Kein zum Zeitpunkt t verfügbarer
> Marktzustand ordnet `E[R]` brutto verlässlich über dem Nullband — auch
> `btc_trend` nicht.
>
> ⚠️⚠️ **Was damit NICHT widerlegt ist:** dass BTC den Markt treibt. Die
> Mitläufer-Struktur ist real und erklärt weiterhin, warum die Drift breit
> ist (2.598) und die Symbolauswahl nicht greift. Widerlegt ist nur, dass
> man aus dem BTC-Zustand **vorab** ableiten kann, ob sich ein Trade lohnt.

---

# § 2 Die Zahlen — Verhältnis Spanne / Nullband, kausale Fassung

| Fenster | Zelle | `btc_trend` | höchste **Kontrolle** | |
|---|---|---|---|---|
| **voll** (2021-12 →) | H24 | **1,09** | 1,04 | knapp vorn |
| **voll** | H6 | **1,02** | **1,43** | ⛔ Zufall schlägt es um 40 % |
| **ab 2024** | H24 | **1,26** | 1,14 | knapp vorn |
| **ab 2024** | H6 | **1,35** | **1,44** | ⛔ Zufall vorn |

**Die übrigen fünf Merkmale**, alle Fenster, alle Zellen: `breite` 0,69 ·
`btc_momentum` 0,56–0,80 · `markt_vola` 0,60 · `btc_vola` 0,63 ·
`markt_momentum` 0,36 — **durchweg unter 1**, also im Nullband.

⭐ **Das Muster ist in beiden Fenstern identisch:** H24 knapp vorn, H6
dahinter. Kein konsistenter Nachweis.

## 2.1 ⚠️ Was ehrlich dazugehört

`btc_trend` ist in **allen vier** Zellen das höchste oder zweithöchste echte
Merkmal, während die anderen fünf nie über 0,80 kommen. **Das ist ein
Hinweis.** Er ist kein Befund, weil eine reine Zufallsreihe ihn in zwei von
vier Zellen schlägt.

⭐ Und die Fensterachse hat geliefert, wozu sie gebaut war: die Werte sind im
kurzen Fenster **höher** (1,26/1,35 gegen 1,09/1,02) — **aber die Kontrollen
auch**. Das war vorhergesagt: weniger Regimewechsel → breiteres Band.

---

# § 3 ⭐⭐⭐ Warum es nicht messbar ist — eine prinzipielle Grenze

| | |
|---|---|
| Anker | 3.237.922 |
| Stunden | 42.207 |
| **echte Regimewechsel in 4,75 Jahren** | **schätzungsweise 6 bis 10** |

⚠️⚠️ **Die effektive Stichprobe ist die Zahl der Regimewechsel, nicht die
Zahl der Anker.** Mit zehn Beobachtungen lässt sich nur ein riesiger Effekt
nachweisen.

➤ **Mehr Rechenzeit ändert daran nichts. Nur mehr Jahre würden es — und die
gibt es nicht.** Das ist der Unterschied zu allen bisherigen Nullbefunden
des Projekts: dort war die Messform oder die Zielgröße das Problem, hier ist
es die Datenmenge, und zwar unbehebbar.

---

# § 4 Der Weg dorthin — drei Fehlversuche, jeder mit einer Lehre

## 4.1 ⛔ Erster Versuch: das Zeitfenster gab den Effekt vor

`btc_trend` meldete in **allen vier** Zellen „ordnet und TRÄGT", mit
`E[R]` bis **+0,066**. Es war ein **Verfügbarkeitsartefakt**: BTC lag in der
Messbasis erst ab **2023-09** vor, 26.872 von 42.207 Stunden — das Fenster
enthielt 2026 (positiv) und **nicht 2022** (`E[R]` −0,0430).

⭐ **Verraten hat es sich durch eine Unmöglichkeit:** die **kausale** Fassung
war *stärker* als die Rückschau (Faktor 0,64). Das kann nicht sein, wenn
beide dasselbe messen — die Rückschau kennt die Zukunft.

⚠️ Damit war eine **registrierte Regel verletzt** (gemeinsames Zeitfenster je
Klasse). Und der Fehler steckte doppelt: bei `np.roll` wandern die NaN mit,
also lief die Nullwelt auf einer **anderen** Teilmenge als die Messung.

## 4.2 ⛔ Zweiter Versuch: die gepoolte Quote verdeckte alles

Nach der Behebung meldete das Werkzeug *„NULLWELT GEEICHT"*, weil die
gepoolte Fehlalarmquote (17,5 %) mit dem Sollwert 10 % vereinbar war.

⚠️ **Das war die falsche Frage.** Je Merkmal aufgeschlüsselt:
`btc_trend` 75 %, **`zufall_2` 50 %**, drei echte Merkmale 0 %. Die gepoolte
Zahl verdeckte beide Extreme.

## 4.3 ⛔ Dritter Versuch: Quoten aus zwei Beobachtungen

Danach verglich das Werkzeug Trefferquoten je Merkmal — aber bei zwei Zellen
sind das **zwei Tests**. `btc_trend` 2/2 = 100 %, und eine Kontrollreihe
ebenfalls 100 %.

➤ **Eine Quote aus zwei Beobachtungen ist bedeutungslos.** Die Messgröße ist
die **Spanne selbst** (wie weit über dem Band), nicht wie oft. Erst damit
wurde das Ergebnis lesbar — und eindeutig.

---

# § 5 ✔✔ Was an dieser Messung belastbar ist

| | |
|---|---|
| **BTC-Daten** | 44.415 Stunden ab 2021-09, **lückenlos** (vorher 26.872 ab 2023-09) |
| **Fundament** | **5 von 5** Gegenprüfungen (`pruefe_leitwert_und_regimeform.py`) |
| **Nullwelt** | zyklische Verschiebung ≥ 90 Tage · Restkorrelation **0,017** (bei 1 Tag: 0,967 — die Probe kann fehlschlagen) |
| **Eichung** | **9 von 10** Kontrollreihen treffen nie |
| **Kausalität** | am Seiteneffekt nachgewiesen: Zukunft verändert → Wert bei t unberührt |
| **Fensterachse** | beide Zuschnitte gemessen, statt einen zu wählen |

⭐ **Nur deshalb ist das negative Ergebnis etwas wert.** Der erste Versuch war
ein Fehlalarm; dieser ist ein Befund.

---

# § 6 ⛔ Was NICHT folgt

| # | |
|---|---|
| **1** | ⛔ **Nicht, dass BTC den Markt nicht treibt.** Das bleibt plausibel und durch 2.598 gestützt — nur nicht *vorab verwertbar* |
| **2** | ⛔ **Nicht, dass es keinen Regimefilter gibt.** Geprüft sind sechs Merkmale aus Kursdaten. Makro-Quellen (Fear & Greed, BTC-Dominanz, Zinsen) sind **ungeprüft** — ⚠️ aber sie haben dasselbe Stichprobenproblem |
| **3** | ⚠️ **`btc_trend` ist nicht ausgeschlossen**, sondern **unentschieden**. In H24 liegt es in beiden Fenstern vorn. Für eine Entscheidung bräuchte es ~40 Kontrollreihen und mehr Zellen — bei unveränderter Stichprobengrenze |
| **4** | ⛔ **Nichts über Short** — ruht weiter |
| **5** | ⚠️ **Nichts über Nicht-Krypto.** Gemessen auf 116 Kryptowerten |

---

# § 7 Standards

| | |
|---|---|
| **gilt** | Vorabfestlegung **vor** der Messung (H0/H1 und die Vorhersage) · Bezug = Nullpunkt · 40 Ziehungen, 90. Perzentil · **10 Kontrollreihen** · Rückschau gegen kausal · Dosis-Wirkung (Versatzleiter 1/7/30/90/180 Tage) |
| **angepasst** | Nullwelt = **zyklische Verschiebung** statt Permutation · **gepoolt** statt geklammert (marktweite Merkmale sind je Stunde konstant) · `zufall` **autokorreliert** statt weiß |
| ⚠️ **verletzt und behoben** | **gemeinsames Zeitfenster je Klasse** (§ 4.1) — die Verletzung erzeugte den Fehlalarm |
| ➤ **Frageart** | **`markt`**, Menge = Messuniversum |
