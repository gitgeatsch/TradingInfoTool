# Arbeitsplan — die LAGE des Hebels, in zwei Schritten

**25.09.2026.** Nutzervorgabe, wörtlich:

> *„1. ZUERST alle schiefen Beiträge aus der ALTEN (spot)Hebel sauber und
> korrekt messen und Einordnen und Lösungen suchen. 2. Kommen wir mit den
> vorherigen Beiträgen und KOMBINATIONEN nicht weiter DANN suchen wir
> weitere (neue) Beiträge."*

⚠️ **Und die Kritik dazu:** *„du wirfst die Bewertungen in einen Topf"* —
richtig. Ich hatte alle zwölf registrierten Kandidaten gleich behandelt,
obwohl drei davon einen völlig anderen Status haben.

---

# § 1 Die Fragestellung, sauber

**Warum prüfen wir die Lage?** Regel 3: *„beim HEBEL kein Asset-Rang — der
Hebel kommt aus der Wahrscheinlichkeit DIESES Trades."* Die Lage ist der
Zustand, aus dem diese Wahrscheinlichkeit folgt.

**Wie entsteht sie?** Am Code (`wahrscheinlichkeit.rechne`):

```
q = basisrate + Summe(punkte über ALLE geltenden Beiträge)
                ↑
                DAS ist die Lage — eine SUMME, kein Einzelmerkmal
q → Kelly → r → Hebel
```

⚠️⚠️ **Deshalb ist ein Einzelmerkmal noch keine Lagebewertung.** Mein
`funding`-Befund (2.588) ist ein Baustein, nicht die Lage.

---

# § 2 ⭐ SCHRITT 1 — die drei TRAGENDEN sauber einordnen

**Das sind die Beiträge des alten (Spot-)Hebels.** Sie tragen auf
`bewegung_r`/H20 und sind live. Auf der Hebel-Frage (`barriere`/H3) stehen
sie so:

| Kandidat | Form | auf `barriere` | ⚠️ WORAN es scheitert |
|---|---|---|---|
| **`funding`** | regler | Stufen monoton, Spanne **0,0121** | ⛔ **unter der Auflösung 0,0133** — Grauzone |
| **`turnover`** | regler | +0,0073 | ⛔ **unter der Nachweisgrenze** 0,0094–0,0180 |
| **`oi_aenderung`** | schalter | über Nullpunkt, nicht monoton | ⛔ **kein Fünftel über der Kelly-Nullstelle** |

## 2.1 ⚠️ „Kein Beitrag fällt ohne Lösungssuche" — je Kandidat

### `funding` — die Lösung liegt in der FORM, nicht in mehr Daten

| | |
|---|---|
| **Woran** | auf Menge `frei` monoton, aber Spanne **unter** der Auflösung. Auf **50 %** liegt die Spanne mit **0,0164 über** der Auflösung — dort aber **nicht monoton** |
| ➤ **Lösungsspur** | ⭐ **als SCHALTER prüfen statt als Regler.** Wenn die Monotonie nicht trägt, aber die Trennung schon, ist eine Zweiteilung (bestes Fünftel gegen Rest) die stärkere Bauform — dieselbe Lehre wie bei `funding` auf Spot (23.09.: *„die unbedingte Sperre des obersten Rangfünftels ist die richtige Bauform"*) |
| **Warum das plausibel ist** | eine Zweiteilung braucht nur **eine** Trennung über der Auflösung, nicht fünf monotone Stufen. Die Datenlage muss dafür nicht besser werden |

### `turnover` — die Lösung ist die DATENLAGE

| | |
|---|---|
| **Woran** | nur **66 Symbole** (gegen 122 bzw. 299 bei den anderen), nur zwei zulässige Mengen |
| ➤ **Lösungsspur** | die Abdeckung prüfen: `umschlag_frei` ist seit 22.09. die Live-Größe. **Wieviele Symbole hat sie, und wächst sie?** Bleibt es bei 66, ist der Kandidat auf `barriere` nicht entscheidbar — das ist eine Datenlage, kein Urteil |

### `oi_aenderung` — eingeordnet, keine Lösung nötig

| | |
|---|---|
| **Woran** | auf `frei` liegt **kein** Fünftel über der Kelly-Nullstelle — als Quelle der Hebel**höhe** taugt er nicht |
| ✔ **Aber das ist kein Mangel** | er ist als **Schalter** registriert und als OI-Sperre (Stufe 12) gebaut. Die Messung **bestätigt** die Bauform |
| ➤ **Seine Rolle** | er **filtert** die Lage, er bemisst sie nicht |

---

# § 3 ⭐ SCHRITT 1b — die KOMBINATION der drei

⚠️⚠️ **Nie gemessen — für keine Zielgröße, weder Spot noch Hebel.**

Das Nutzermodell steht seit dem 20.08.: *„Ein Wert hat fast keine positive
Auswirkung, aber die richtige Kombination bildet dann den Trichter der
Optimierung."*

| | |
|---|---|
| **Werkzeug** | `messe_kandidaten_kombination.py` (N-17b) — existiert, prüft eine **vorab benannte** UND-Kombination gegen jede Einzelgröße |
| **Vorbedingung** | die Redundanz. Gemessen: `funding × turnover` +0,129 · `funding × oi_aenderung` ~0 · **unabhängig genug** |
| **Was zu prüfen ist** | trägt `funding × turnover` oder `funding` ohne das gesperrte OI-Fünftel mehr als `funding` allein? |

⚠️ **Erst wenn auch das nichts bringt**, kommt Schritt 2.

---

# § 4 SCHRITT 2 — die neun anderen, und zwar ERST DANN

**Diese neun sind auf `bewegung_r`/H20 gefallen und auf `barriere`
ungemessen:**

| geprüft (25.09., alle gefallen) | **ungemessen auf `barriere`** |
|---|---|
| `oi_je_umsatz` · `long_bias` · `top_bias` · `taker_bias` | ⛔ `rsi` · `momentum` · `momentum_kurz` · `funding_extrem` · `amihud` |

⚠️ **Die Erwartung ist gedämpft** — alle sind auf `bewegung_r` gefallen, und
die vier bereits geprüften tragen auf `barriere` auch nicht. Aber das
Register führt die Spur ausdrücklich als offen: *„die HEBEL-Frage ist
`barriere` — dagegen ist er NIE gemessen."*

⛔ **Sie kommen NICHT vor Schritt 1.** Neue Kandidaten zu suchen, während die
tragenden schief liegen, wäre genau die Verwechslung, die der Nutzer
benannt hat.

---

# § 5 Die Reihenfolge, verbindlich

```
1a  funding als SCHALTER prüfen        (Form, nicht Daten)
1b  turnover: Datenlage klären          (66 Symbole - wächst sie?)
1c  oi_aenderung: ✔ eingeordnet, nichts zu tun
1d  die KOMBINATION der drei            (nie gemessen)
────────────────────────────────────────────────────────────
2   erst dann: die fünf ungemessenen auf barriere
3   erst dann: neue Beiträge suchen
```

⚠️ **Und der Fallback bleibt daneben liegen**, nicht davor: fester Hebel
(z. B. 3x), Bewertung nur für das Ob — dafür braucht `q` nur zu ordnen, und
die Ordnung ist belegt (Spearman +0,947 horizontstabil).

---

# § 6 Was dieser Plan NICHT anfasst

- **Die Klammer** — geklärt, sie bleibt (2.589: `r_min`/`r_max` sind der
  Schutz gegen ein `q` auf schwankender Basisrate).
- ⚠️ **Offen daneben:** `r_min = 0,005` **hebt** die schlechteste Lage auf
  3,00x **an**. Bei `r_min = 0` bekäme sie **keinen** Hebel. Eigene Frage.
- **Spot** — liegt, nur als Vergleich.
- **Die Kette** — nach der Bewertung.
