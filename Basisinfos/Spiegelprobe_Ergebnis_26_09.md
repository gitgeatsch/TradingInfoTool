# Die Spiegelprobe war falsch konstruiert — geeicht und neu bewertet

**26.09.2026** · Befund **2.603** · Vorabfestlegung 19 ·
`pruefe_spiegelprobe.py` + `messe_kandidaten_spiegel.py`

---

# § 1 Das Ergebnis in drei Sätzen

> ⛔ **Die Spiegelprobe auf `E[R]` ist nachweislich untauglich.** Long- und
> Short-`E[R]` sind auf denselben Ankern **strukturell** gegenläufig — ein
> garantiert richtungsfreies Merkmal liefert dasselbe Muster wie ein reines
> Richtungsmerkmal.
>
> ✔✔ **Die Probe auf dem EREIGNIS trennt** — an einer Simulation geeicht,
> mit **0 % Fehlalarm und 100 % Fundquote**.
>
> ⚠️ **Die registrierte Schwelle 1,30 ist zu lax.** Abgelesen sind **1,717**;
> das 90. Perzentil der Bewegung-Welt liegt bei 1,362 und damit darüber.

---

# § 2 Die Eichung — die Wahrheit ist gesetzt, nicht geschätzt

Auf **echten** Daten gibt es keinen garantiert richtungsfreien Testfall:
große Kryptobewegungen sind häufiger nach oben, also steckt in jedem
Bewegungsmaß Richtung. Gemessen an `|künftige Bewegung|` — garantiert
richtungsfrei konstruiert — ergab sich ein Verhältnis von **2,57**, das nach
jeder Schwelle als „Richtung" durchginge. ➤ **Deshalb die Simulation.**

```
r(t) = drift(gruppe) + sigma(gruppe) * z(t)
    BEWEGUNG-Welt   drift = 0 fuer alle, sigma variiert
    RICHTUNG-Welt   sigma gleich, drift variiert
```

## 2.1 A3 — Dosis-Wirkung

| Größe | Dosis 0,00 | 0,25 | 0,50 | 0,75 | 1,00 | |
|---|---|---|---|---|---|---|
| **V Verhältnis** | 1,151 | 1,424 | 1,644 | 2,113 | **2,667** | ✔ monoton |
| D Differenz | 0,140 | 0,353 | 0,483 | 0,744 | 0,937 | ✔ monoton |
| Q D/S | 0,141 | 0,350 | 0,487 | 0,715 | 0,909 | ✔ monoton |
| **S Summe/2** | 1,026 | 0,982 | 1,000 | 1,026 | 1,044 | **⛔ springt** |

⭐ **Dass `S` nicht monoton ist, ist die Bestätigung, dass die Simulation
hält, was sie soll:** `S` ist der **Bewegungs**anteil und darf mit dem
Richtungsanteil gerade nicht steigen. Das war in Vorabfestlegung 19 § 2.2
**vorhergesagt**.

## 2.2 A1, A2 und A4 — die abgelesene Schwelle

| Größe | BEW 90. Perz | RICH 10. Perz | Schwelle | Fehlalarm | Fundquote |
|---|---|---|---|---|---|
| **V Verhältnis** | **1,362** | 2,071 | **1,717** | **0 %** | **100 %** |
| D Differenz | 0,321 | 0,758 | 0,539 | 0 % | 100 % |
| Q D/S | 0,307 | 0,698 | 0,502 | 0 % | 100 % |
| G Gegenlift | 1,081 | 0,485 | — | ⛔ Verteilungen überlappen | |
| S Summe/2 | 1,095 | 0,957 | — | ⛔ Verteilungen überlappen | |

⚠️ **Die Schwelle ist eine UNTERE Abschätzung** — normalverteilte Renditen
haben keine fetten Ränder und kein Vola-Clustering.

---

# § 3 Die Kandidaten, neu bewertet

**2.878.712 Anker, Sperre aus 2.602 angewandt, Ereignis = ZIEL erreicht**

| Merkmal | Lift hoch | Lift runter | Verhältnis | Urteil | Fünftel |
|---|---|---|---|---|---|
| `vola` | 1,183 | 0,467 | **2,536** | ✔✔ RICHTUNG | 4 |
| `ema_abstand_atr` | 1,796 | 0,714 | 2,515 | ✔✔ RICHTUNG | 4 |
| `ema_lage` | 1,751 | 0,746 | 2,347 | ✔✔ RICHTUNG | 4 |
| `bandenge` | 1,288 | 0,566 | 2,276 | ✔✔ RICHTUNG | 4 |
| `momentum_kurz` | 1,669 | 0,751 | 2,222 | ✔✔ RICHTUNG | 4 |
| `rsi` | 1,848 | 0,854 | 2,165 | ✔✔ RICHTUNG | 4 |
| **`rueckstand_beta`** | 1,881 | 0,894 | 2,105 | ✔✔ RICHTUNG | **0** |
| `ema_steigung` | 1,079 | 0,603 | 1,788 | ✔✔ RICHTUNG | 4 |
| `trendstruktur` | 1,198 | 0,678 | 1,768 | ✔✔ RICHTUNG | 4 |
| `oi_aenderung` | 1,424 | **1,010** | 1,409 | ⛔ Bewegung | 4 |
| `rsi_umkehr` | 1,345 | **0,998** | 1,348 | ⛔ Bewegung | 0 |
| `funding` | 1,094 | 0,852 | 1,284 | ⛔ Bewegung | 0 |
| **`zufall`** | 1,017 | 0,998 | **1,019** | ✔ Kontrolle hält | 2 |

## 3.1 ⭐ Was sich dadurch ändert

| | |
|---|---|
| ⛔ **2.601 war falsch** | `rueckstand_beta` hat **Richtung** (2,105), nicht „Bewegung ohne Richtung". ⚠️ Aber im Fünftel **0** — dort, wo das Asset BTC **voraus** ist. Also **Momentum, nicht Nachziehen**: die Idee war richtig gemessen, mit umgekehrtem Vorzeichen |
| ⛔ **A-Faktoren neu** | `trendstruktur` und `ema_abstand_atr` haben **Richtung**, nicht Bewegung |
| ✔ **2.594 bestätigt** | `funding` bleibt Bewegung (1,284), `oi_aenderung` ebenfalls (1,409) — unabhängig auf einer **anderen** Geometrie reproduziert |
| ⛔ **`rsi_umkehr` fällt** | 1,348 mit Gegenlift **0,998** — der neue Faktor trägt keine Richtung |

## 3.2 ⚠️⚠️ Was die Spiegelprobe NICHT sagt

> **„Hat Richtung" ist nicht „trägt `E[R]`".**

Ein hoher Lift auf *Ziel erreicht* ist mit häufigeren Stops vereinbar. Alle
neun Merkmale mit Richtung können trotzdem ein negatives `E[R]` haben — und
nach 2.597 haben sie das auch. **Die Niveaufrage bleibt offen.**

---

# § 4 Was korrigiert wird — und was ausdrücklich nicht

**Nutzervorgabe:** *„korrigiere die Doku aber nur dort wo es sicher ist."*

| | |
|---|---|
| ✔ **sicher, wird korrigiert** | die Spiegelproben-Urteile aus 2.601 und den A-Faktoren — die Probe war nachweislich falsch konstruiert |
| ✔ **sicher, wird ergänzt** | die Schwelle 1,717 als abgelesener Wert |
| ⛔ **NICHT angefasst: 2.594** | dort wurde auf **Ereignissen** gemessen, also richtig. Mit 1,717 nachgerechnet bleiben alle drei Urteile bestehen; nur `vola` wandert von „teilweise Richtung" zu klar Richtung |
| ⛔ **NICHT angefasst: 2.601 zweiter Teil** | `rueckstand` trägt nur **13 %** über `beta` — das war die `beta`-Kontrolle und von der Spiegelprobe unberührt |
| ⛔ **NICHT angefasst: 2.602** | die Sperre steht auf P2/P3 (Suchnullwelt und B6), nicht auf der Spiegelprobe |
| ⚠️ **offen gelassen** | ob die neun Richtungsmerkmale `E[R]` heben. Das ist die Niveaufrage und hier **nicht** gemessen |
