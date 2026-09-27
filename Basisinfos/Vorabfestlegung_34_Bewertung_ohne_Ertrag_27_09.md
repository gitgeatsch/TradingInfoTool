# Vorabfestlegung 34 — die Bewertung ohne Ertrag (Weg C)

**27.09.2026** · Phase 1b · `messe_bewertung_c.py` · Frageart **`markt`**

> **Nutzerentscheidung:** Weg **C** — *„welche der drei ist die beste
> Lösung, nicht die einfachste"*. C trennt zwei Fragen, die beide
> beantwortet werden müssen.

---

# Warum C und nicht A oder B

| | warum es allein nicht reicht |
|---|---|
| **A** nur Stopwahrscheinlichkeit | eine Lage mit **niedrigem Risiko und null Chance** bekäme hohen Hebel und ein Signal. Niedriges Risiko allein ist kein Handelsgrund |
| **B** nur erwartetes CRV | ein Verhältnis ist maßstabsfrei: **CRV 2 bei MFE 0,2/MAE 0,1 ATR** ist etwas anderes als **CRV 2 bei MFE 4,0/MAE 2,0** — zwanzigfaches absolutes Risiko bei gleichem Verhältnis |
| **C** beides | ⭐ nicht zwei Regler an derselben Frage, sondern **zwei verschiedene Fragen** |

| Frage | Größe | Nutzervorgabe |
|---|---|---|
| **Kommt ein Signal?** | `crv_erwartet(W)` — das **Potential** | *„wenn ein Asset ein bestimmtes Potential erreicht"* |
| **Wie hoch der Hebel?** | steigt mit `crv_erwartet`, begrenzt durch **absolutes** `mae_erwartet` | *„je besser das Chance-Risiko-Verhältnis, desto höher … der Hebel"* |
| **Harte Grenze** | **RM-11** | unverändert |

---

# ⭐ Die Stelle im Code — der Eingriff ist chirurgisch

`agent/betraege.py:360-399` rechnet heute:

```
kelly = (q·(1+CRV) − 1)/CRV          ← q und CRV aus ERTRÄGEN
halb  = kelly / 2
r     = clamp(halb, r_min, r_max)    ← HIER geht die Lagequalität ein
risiko  = r · Kapital
nominal = risiko / stop_rel
hebel   = min(nominal/nenner, hebel_sicher)     ← RM-11
ist_hebel = hebel ≥ hebel_ab (2,0)
```

➤ **Ersetzt wird genau eine Zeile:** `r` kommt künftig aus
`crv_erwartet(W)` statt aus Kelly. **Alles dahinter bleibt** — Risiko,
Nominale, RM-11, die 2×-Grenze.

⚠️ Und der Abbruch `if kelly <= 0` braucht ein regelfreies Gegenstück.

---

# Die Konstruktion

## Was kalibriert wird — aus der Historie, regelfrei

| | |
|---|---|
| `mae_erwartet(W)` | Lage → erwarteter Rückgang in **ATR** |
| `mfe_erwartet(W)` | Lage → erwarteter Anstieg in **ATR** |
| `crv_erwartet(W)` | `mfe_erwartet(W) / \|mae_erwartet(W)\|` |
| `p_stop(W, weite)` | aus der **MAE-Verteilung**: wie oft reißt `weite × ATR`? |

⚠️ **Alle vier ohne Stop, ohne Trailing, ohne Ertrag** (2.642).

## Wie daraus `r` wird — und warum diese Form

| | |
|---|---|
| **Nullpunkt** | `crv_erwartet = 1` heißt Chance **gleich** Risiko — darunter lohnt es nicht. Das ist ein **hergeleiteter** Nullpunkt, keine gesetzte Zahl |
| **Form** | `r` steigt mit `(crv_erwartet − 1)`, geklammert auf `[r_min, r_max]` = **[0,5 %, 1,25 %]** aus `config.yaml` |
| **Obergrenze** | ⚠️ bei **welchem** `crv_erwartet` ist `r_max` erreicht? Das ist **zu messen**, nicht zu setzen — aus der Verteilung von `crv_erwartet` über die Lagen |
| **Begrenzung** | `p_stop(W)` deckelt zusätzlich: eine Lage mit hoher Stopwahrscheinlichkeit bekommt weniger `r`, auch bei gutem Verhältnis |

⭐ **Die Formwahl wird in der Messung geprüft**, nicht angenommen: linear
in `(crv−1)` gegen proportional gegen gestuft. Registrierte Regel
*„Formwahl immer begründen — warum diese, warum nicht die anderen"*.

---

# ⚠️ Die Fallen

| # | |
|---|---|
| **1** | ⛔ **Kein Ertrag, kein Kelly, kein `q`, kein CRV aus Ergebnissen** (2.641) |
| **2** | ⚠️⚠️ **`crv_erwartet` ist NICHT das CRV der Handelsregel.** Das eine ist eine Markterwartung in ATR, das andere das Verhältnis von Ziel- zu Stopabstand (`GRENZEN["crv"] = 2,0`). **Sie dürfen im Code nie denselben Bezeichner tragen** — sonst ist der nächste Fehler vorprogrammiert |
| **3** | ⚠️ **Der mittlere MAE ist nicht die Stopwahrscheinlichkeit.** Für `p_stop` wird die **Verteilung** gebraucht, nicht der Mittelwert |
| **4** | ⚠️ **Die Stopweite 1,00 ATR stammt aus 2.628 und wurde nach ERTRAG optimiert.** Sie ist hier ein **Parameter**, keine Wahrheit — `p_stop` wird über mehrere Weiten gerechnet und die Abhängigkeit ausgewiesen |
| **5** | **Streckenanfänge** (2.638), nicht jeder Anker — das ist der Betriebsfall |
| **6** | **Out-of-sample** auf **beiden** Funktionen, und **Weglassprobe je Jahr** — sie haben heute zwei Befunde gekippt |
| **7** | ⭐ **Die 2×-Grenze und `r_min`/`r_max` sind Nutzervorgaben**, keine Messergebnisse. Sie werden als solche gekennzeichnet |
| **8** | ⚠️ **Selbstprobe**: bei zufälliger Lage muss `crv_erwartet` gegen den Marktdurchschnitt laufen. Tut es das nicht, ist die Kalibrierung falsch |
| **9** | Regel 2: Gebühren und Finanzierung bleiben draußen |

---

# Was vorher als Ergebnis gilt

| Ausgang | Folge |
|---|---|
| `crv_erwartet` ordnet monoton, out-of-sample und zeitstabil | ✔ das ist die Bewertungsgröße; `r` folgt daraus |
| ordnet, aber nicht zeitstabil | ⚠️ wie 2.633 — dann kein Punkt, sondern ein Bereich |
| `crv_erwartet` liegt überall nahe 1 | ⛔ dann trägt die Lage kein Potential, und der Hebel ist nicht zu rechtfertigen |
| `p_stop` hängt kaum von `W` ab | ⚠️ dann ist die Begrenzung wirkungslos und C fällt auf B zurück |

# Was NICHT beantwortet wird

Positionsgröße, Kapazität, Takt, Cooldown *(Phase 2)* · die übrigen
Beiträge *(1c)* · die Quellenfrage *(1d)* · die Stopweite selbst
*(Parameter, nicht Gegenstand)*
