# Regelwerk: Bewertung von Einstieg und Hebel

**27.09.2026** · gehört zu `Plan_Hebel_fuenf_Phasen_27_09.md`, Phase 1
Faktenteil: `python hebel_neubau.py`

> **Nutzerauftrag:** *„Regelwerk zuerst — du bist komplett ohne Plan."*
> Und: *„Was ist mit turnover und funding, diese waren bereits gesetzt
> oder? Du hast recherchiert und noch immer keine Ahnung zum Einstieg und
> den Merkmalen."*

---

# ⛔ Der Fehler, der dieses Blatt nötig macht

Am 27.09. habe ich **sieben Kursmerkmale** gemessen — `ema_abstand_atr`,
`momentum_kurz`, `rsi`, `rsi_umkehr`, `rsi_aenderung`, `ema_lage`,
`ema_steigung`, `trendstruktur`, `bandenge`, `vola`.

**Die drei einzigen registrierten Träger des Systems habe ich nicht ein
einziges Mal geladen:**

| | Form | Zustand | Basis |
|---|---|---|---|
| **`funding`** | Regler | ✔ trägt | H20 · 2.369 Kalendertage · 290 Symbole · 6,3 Jahre |
| **`turnover`** | Regler | ✔ trägt | H20 · 2.636 Kalendertage · Richtung +0,00512 (stärkster der drei) |
| **`oi_aenderung`** | Schalter | ✔ trägt | H20 · 1.702 Kalendertage · 117 Symbole · 126.491 Anker |

⚠️ **Mein eigener Riegel hat sie mir aus dem Blick genommen.** `hebel_neubau.SPOT_QUELLEN`
sperrt `funding_fuenftel` und `turnover_fuenftel` — die **alten Beitragsstufen**.
E-3 gibt die **Rohgrößen ausdrücklich frei**. Ich habe die Sperre auf die
Rohgrößen ausgedehnt, ohne es zu merken.

---

# 1. Der Ablauf zum Prüfzeitpunkt

**Nutzervorgabe 27.09.:** *„1. Hebel-Einstieg zulässig? … 2. Hebelbewertung:
ist auch das Risiko gering und die Chance hoch."* Und: *„dann weiter in der
Kette wie heute."*

```
T1  Prüfzeitpunkt
    ├─ BEWERTUNG 1  Einstieg zulässig?     gut | sehr gut | nein
    ├─ BEWERTUNG 2  Hebelhöhe               2× | 3× | 5×
    └─ weiter in der Kette wie heute  ──►  Mail

T2  nach der Eröffnung — eine neue Hebelposition existiert
    └─ Stop · Trailing · Ausstieg            (Phase 5)
```

⚠️ **Beide Bewertungen sind neutral:** kein Kapital, keine Positionsgröße,
kein Ergebniswert, **keine Geometrie**.

---

# 2. Die zwei Bewertungen — und sie messen Verschiedenes

> **Das ist der Kern, und er hat mir bis heute gefehlt: Einstieg misst
> gegen die CHANCE, Hebel gegen das RISIKO. Zwei Zielgrößen, zwei
> Messungen — ein Merkmal kann in der einen tragen und in der anderen
> nicht.**

| | **BEWERTUNG 1 · Einstieg** | **BEWERTUNG 2 · Hebelhöhe** |
|---|---|---|
| **Frage** | Kommt eine Bewegung nach oben? | Wie weit geht es gegen mich, bevor es für mich geht? |
| **Zielgröße** | **Ereignis**: +X % in Y h — regelfrei | **MAE in ATR** — maximaler Rückgang |
| **Bezug** | das eigene Asset (**Lift**) | das eigene Asset |
| **Nullpunkt** | **Lift = 1** | eigener Durchschnitts-MAE |
| **Ergebnis** | nein / gut / sehr gut | 2× · 3× · 5× |
| **Richtung** | geringes Risiko → **höhere** Stufe | |

## ⚠️ Die Karenzbedingung für Bewertung 1

**Nutzerdefinition:** *„OPTIMUM ist, wir kennen die Lage VOR der Bewegung.
Die Bewertung eines bereits gestiegenen Assets ist weder das Ziel noch ein
Optimum — dazu brauche ich kein System."*

➤ **Ein Merkmal qualifiziert sich für Bewertung 1 nur, wenn sein Lift eine
Karenz von mindestens 3 Stunden überlebt.** Ohne diese Bedingung misst man
die Fortsetzung einer laufenden Bewegung.

---

# 3. Wo welcher Beitrag zählt — der Stand, ehrlich

| Merkmal | Bewertung 1 (Chance) | Bewertung 2 (Risiko) | Beleg |
|---|---|---|---|
| **`funding`** | ⬜ **ungemessen** | ⬜ **ungemessen** | trägt auf H20/`bewegung_r`; auf `barriere` Grauzone |
| **`turnover`** | ⬜ **ungemessen** | ⬜ **ungemessen** | trägt; auf `barriere` untermächtig (66 Symbole) |
| **`oi_aenderung`** | ⬜ **ungemessen** | ⬜ **ungemessen** | trägt als Schalter; auf `barriere` Sperre |
| **`ema_abstand_atr`** | ⛔ **nein** | ✔✔ **belegt** | 2.642: d 0,521 auf MAE gegen 0,267 auf MFE · 2.648: sagt Abstürze 9,8-fach voraus |
| **`momentum_kurz`** | ⛔ **Fortsetzung** | ⬜ ungemessen | 2.648: Lift 6,93 — bricht bei 3 h Karenz auf 0,31 ein |
| **`rsi`** | ⛔ **Fortsetzung** | ⬜ ungemessen | 2.648: Lift 4,67 — bricht auf 0,43 ein |
| **`vola`** | ⛔ **nur Bewegung** | ⭐ **Spur** | Spiegelprobe 1,31 · Register: *„gehört in die Geometrie- und Horizontwahl, und über `hebel = verlustanteil / stop_rel` fällt daraus der Hebel"* |
| **`bandenge`** | ⛔ **misst nichts** | ⛔ | Lift 0,84–1,22 gegen Band 2,77 |
| `rsi_umkehr` · `ema_lage` · `ema_steigung` · `trendstruktur` | ⛔ | ⬜ | 2.645 |
| `amihud` · `funding_extrem` · `oi_je_umsatz` · `long_bias` · `top_bias` · `taker_bias` | ⛔ | ⬜ | Register: tragen nicht |

## ➤ Was diese Tabelle sagt

| | |
|---|---|
| **Bewertung 2 hat einen Träger** | `ema_abstand_atr`, belegt — und eine Spur (`vola`) |
| ⛔ **Bewertung 1 hat keinen** | und die drei registrierten Träger sind dort **nie gemessen worden** |

⚠️ **Das ist keine Sackgasse, sondern eine Lücke.** `funding`, `turnover`
und `oi_aenderung` sind auf **H20 gegen `bewegung_r`** gemessen — der
Spot-Lage. Auf der Frage *„kommt ein Anstieg von +15 % in 6 Stunden, und
zwar mit Karenz"* sind sie **ungeprüft**.

---

# 4. Die Anordnung — Beitragssystem, kein Blocksystem

**Nutzervorgabe (E-4):** *„der HEBEL ist ein Beitragssystem und KEIN
Blocksystem."*

```
BEWERTUNG 1        Σ Beiträge auf die CHANCE   →  Schwelle  →  gut | sehr gut
BEWERTUNG 2        Σ Beiträge auf das RISIKO   →  Stufe     →  2× | 3× | 5×
```

⚠️ **Was aus dem alten Gerüst übernommen wird — und was nicht:**

| ✔ übernommen | ⛔ tot |
|---|---|
| **Registrierung**: ein Beitrag = ein Eintrag mit Wert, Zustand, Quelle, Begründung | `Basisrate = 1/(1+CRV)` — Geometrie **und** Kelly-Nullstelle |
| **Fünf Zustände** + `luecke`: traegt / enthalten / null / noch_nicht / nie | `Breakeven` mit Gebühren — Regel 2 |
| **Additive Verrechnung** — durch 2.302 **belegt** (turnover unabhängig von funding) | **Stufen je Fünftel** — Querschnittsrang (2.649) |
| | `Quote` als Ergebnis — setzt Barrieren voraus |

➤ **Die Stufengrundlage wechselt von *Fünftel* auf *absolute Schwelle in
eigenen Einheiten*.** `funding` und `turnover` müssen dafür neu gestuft
werden — die registrierten Stufen `(+0.82, +1.30, …)` hängen am Fünftel und
gelten nicht.

---

# 5. Was als Nächstes zu messen ist — in dieser Reihenfolge

| # | Messung | warum zuerst |
|---|---|---|
| **1** | **`funding`, `turnover`, `oi_aenderung` auf Bewertung 1**, mit Karenz, auf Assetebene, absolute Schwellen | Es sind die einzigen registrierten Träger. Sie sind auf dieser Frage **ungemessen**. Ohne sie ist Bewertung 1 leer |
| **2** | dieselben drei auf **Bewertung 2** (MAE) | Bewertung 2 hat bisher **einen** Träger; ein zweiter unabhängiger würde die Stufung tragfähig machen |
| **3** | **`vola` in der Hebelhöhe** statt in der Bewertung | Register nennt es ausdrücklich als Spur: *„über `hebel = verlustanteil / stop_rel` fällt daraus der Hebel"* |

⚠️ **Und was NICHT mehr gemessen wird:** weitere Kursmerkmale aus der
EMA/RSI/ATR-Familie. Drei unabhängige Messungen (2.578, 2.645, 2.650) sagen
dasselbe — dort ist nichts.

---

# 6. Die Prüfpflicht

Jeder Befund ab 2.647 belegt **sechs** Prüfungen, bewacht von
`pruefe_pakete.py --paket Hebelneubau`:

**Nullwelt** (tagestreu) · **Zeitstabilität** (Kalenderjahre) ·
**Weglassprobe** · **Mehrfachtesten** (Bestes-von-N) · **Ebene** (A/B/C) ·
**je Asset**

Für Bewertung 1 kommt die **Karenzbedingung** dazu (Abschnitt 2).
