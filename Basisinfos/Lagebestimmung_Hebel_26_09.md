# Lagebestimmung Hebel-Arm — Stand 26.09.2026

**Zwei Tage, acht registrierte Befunde (2.597 bis 2.604), rund 30 Messungen
über 3,2 Mio Anker.** Dieses Blatt gliedert auf, was gemessen ist, was
davon gilt, und was daraus folgt.

---

# § 1 Die Bilanz in drei Sätzen

> ✔✔ **Die Messanlage ist so scharf wie nie.** Vier Werkzeugfehler wurden
> gefunden und behoben, die Spiegelprobe ist erstmals an einer Simulation
> geeicht, und jede Aussage hat eine Nullwelt, die die eigene Suche enthält.
>
> ⛔⛔ **Ein positiver Beitrag wurde nicht gefunden.** Kein Merkmal hebt
> `E[R]` über null — und zwar keines von 22 geprüften, in keiner Zelle, in
> keiner Kombination.
>
> ⭐ **Der strukturelle Grund ist jetzt benannt:** ein Barrierensystem hat
> Erwartungswert null und **verschiebt Risiko, statt es zu verdienen**. Die
> Kante muss von außen kommen — aus einer Information über den künftigen
> Kurs. Alle geprüften Informationen liefern sie nicht.

---

# § 2 Die Eigenschaften — was jedes Merkmal kann

**Legende:** *ordnet* = Fünftel trennen über dem Nullband ·
*Richtung* = Spiegelprobe auf dem Ereignis ≥ 1,717 (2.603) ·
*trägt* = `E[R]` im **vorhergesagten** Fünftel über null, belegt (2.604)

## 2.1 Preis-Merkmale

| Merkmal | ordnet | Richtung | trägt `E[R]` | Bemerkung |
|---|---|---|---|---|
| `momentum_kurz` | ✔ | ✔ 2,222 | ⛔ −0,00318 | der älteste Kandidat (2.594) |
| `rsi` | ✔ | ✔ 2,165 | ⛔ −0,00124 | bester der neun, trotzdem negativ |
| `ema_lage` | ✔ | ✔ 2,347 | ⛔ −0,00333 | ⚠️ im **besten** Fünftel +0,00037 → Auslese |
| `ema_abstand_atr` | ✔ | ✔ 2,515 | ⛔ −0,00196 | „überdehnt"-Maß |
| `ema_steigung` | ✔ | ✔ 1,788 | ⛔ −0,00280 | |
| `trendstruktur` | ✔ | ✔ 1,768 | ⚠️ **+0,00032** | einziger positiver Wert, **nicht belegt** (±0,00294) |
| `bandenge` | ✔ | ✔ 2,276 | ⛔ −0,00216 | Squeeze |
| `vola` | ✔ | ✔ 2,536 | ⛔ −0,00288 | höchster Richtungslift |
| `rsi_umkehr` | ✔ | ⛔ 1,348 | — | „tief und steigend" — **keine** Richtung |

## 2.2 Terminmarkt-Merkmale

| Merkmal | ordnet | Richtung | trägt | Bemerkung |
|---|---|---|---|---|
| `oi_aenderung` | ✔ | ⛔ 1,409 | — | Gegenlift **1,010** → Bewegung |
| `funding` | ✔ | ⛔ 1,284 | — | bestätigt 2.594 auf anderer Geometrie |
| `taker_verh`, `konten_verh`, `top_konten_verh` | ✔ | ⛔ | — | alle Fünftel negativ |
| `volumenschub` | ✔ | ⛔ | — | |

## 2.3 Abgeleitete und Markt-Merkmale

| Merkmal | Status |
|---|---|
| `rueckstand_beta` (Nachzieher) | ✔ Richtung 2,105, aber im Fünftel **0** → **Momentum, nicht Nachziehen**. Trägt nicht (−0,00375). Und nur 13 % stärker als `beta` allein |
| `dominanz_aenderung` | ⭐ trägt **als Achse**, nicht als Beitrag. „BTC steigt ∧ Dominanz steigt" = **−0,0134 ± 0,0077**, belegte **Sperre** |
| `btc_trend`, `breite`, `markt_momentum`, `markt_vola` | ⛔ Marktzustände — nicht vorab ordenbar (2.599) |
| **Kontrollen** `zufall`, `beta` | ✔ verhalten sich wie erwartet, die Anlage ist nicht schief |

---

# § 3 Die Hypothesen — was geprüft ist

| # | Hypothese | Ergebnis | Befund |
|---|---|---|---|
| **H1** | Die **Lage** ist ordenbar | ✔✔ **bestätigt** — Lift ~1,9, neun Merkmale mit Richtung | 2.594, 2.603 |
| **H2** | Die Lage **trägt einen Hebel** | ⛔⛔ **widerlegt** — `E[R]` in 0 von 60 Zellen positiv | 2.595, 2.597, **2.604** |
| **H3** | Der Nullpunkt von `E[R]` ist **null** | ⛔ **widerlegt** — es ist die **Drift** | 2.597 |
| **H4** | Das **Regime** ist wichtiger als die Lage | ✔✔ **bestätigt** — Faktor **12** | 2.598 |
| **H5** | Das Regime ist **vorab erkennbar** | ⛔ **H0 nicht widerlegt** — Grenze ist die Zahl der Regimewechsel (6–10), nicht die Rechenzeit | 2.599 |
| **H6** | **Symbolauswahl** hilft | ⛔⛔ **widerlegt** — kausal *schlechter*, monoton mit der Dosis | 2.598 |
| **H7** | Alts **ziehen nach** (Nachzieher) | ⛔ **widerlegt** — ist Beta, und das Vorzeichen ist umgekehrt | 2.601, 2.603 |
| **H8** | **Dominanz** wirkt als Regler | ⚠️ **halb bestätigt** — als **Achse** ja, als **Beitrag** nein | 2.601 |
| **H9** | Eine **Sperre** hebt `E[R]` | ✔ **bestätigt, reicht nicht** — halbiert den Verlust (−0,00275 → −0,00155), dreht ihn nicht | 2.602 |
| **H10** | „Hat Richtung" ⇒ „trägt `E[R]`" | ⛔⛔ **widerlegt** — das Fünftel mit dem höchsten Richtungslift ist **nicht** das mit dem besten `E[R]` | **2.604** |

⭐ **H10 ist der Ertrag der letzten Messung** und erklärt alle vorherigen
Fehlschläge: Ein Merkmal kann mehr Ziele treffen **und** mehr Stops
kassieren. Richtung und Ertrag sind zwei Größen.

---

# § 4 Was die Messanlage dazugelernt hat

| # | Werkzeugfehler | gefunden durch |
|---|---|---|
| 1 | **Spiegelprobe auf `E[R]`** — Long und Short sind dort strukturell gegenläufig | Selbstprobe an bekannter Wahrheit |
| 2 | **Schwelle 1,30** war nicht geeicht — abgelesen sind **1,717** | Simulation |
| 3 | **`Marktzustand × beta`** ist in der Stundenklammer dasselbe wie `beta` (Rangkorrelation ±1,0000) | ⭐ **Nutzerfrage** |
| 4 | **Bestes Fünftel** statt vorhergesagtes = Auslese | Auswahl-Nullwelt |
| 5 | Kleine Läufe täuschen — **dreimal** anderes Vorzeichen als die volle Menge | Vergleich |
| 6 | **Letzte Stundenkerze** blieb dauerhaft offen (Datenfehler, korrigiert) | Gegenprüfung des Leitwerts |

⚠️ **Vier der sechs wurden durch Gegenprüfungen oder Nutzerfragen gefunden,
nicht durch die Messung selbst.**

---

# § 5 Lagebestimmung — was folgt

## 5.1 Der strukturelle Befund

```
E[R]_alle  =  Drift                      (Optional Stopping, 2.597)
Barriere   =  Versicherung, keine Kante  (2.598 § 4)
```

➤ **Ein Barrierensystem kann per Konstruktion keinen Erwartungswert
erzeugen.** Es verschiebt Risiko: in fallenden Jahren schneidet der Stop ab
(+0,0187), in steigenden deckelt das Ziel (−0,0091). Die Kante muss von
**außen** kommen — aus einer Information über den künftigen Kurs.

## 5.2 Was geprüft ist und nichts hergibt

**22 Merkmale** aus vier Familien: Preis und seine Ableitungen · Terminmarkt
(OI, Funding, Taker, Konten) · Volumen · Marktzustände (BTC, Dominanz,
Breite). Dazu **Kombinationen**, **Sperren** und zwei **Fenster**.

## 5.3 ⭐ Die drei Wege, die offen sind

| Weg | Was dafür spricht | Was dagegen |
|---|---|---|
| **A Neue Datenquellen** — Orderbuchtiefe, Liquidationen, Social/News | Die geprüften Familien sind **ausgeschöpft**; was fehlt, ist Information, die im Kurs noch nicht steckt | Beschaffung, Historie, Kosten. Liquidationsdaten gibt es bei Binance nur kurz zurück |
| **B Andere Geometrie** — kein Barrierensystem, sondern Halten mit Trailing oder Zeitausstieg | Die Barriere ist nachweislich eine Versicherung; ein anderer Ausstieg hat einen anderen Erwartungswert | 2.597/2.598 gelten nur für Barrieren — alles müsste neu gemessen werden |
| **C Den Hebel zurückstellen** | Zwei Tage, 22 Merkmale, kein positiver Beitrag. Die Akkumulation ist ungeprüft und hat mit `schnitt` bereits einen tragenden Beitrag | ⚠️ Nutzervorgabe: *„Wir haben NICHTS ohne den Hebel"* |

## 5.4 ⚠️ Was ich nicht empfehle

| | |
|---|---|
| ⛔ **Mehr Merkmale derselben Familie** | Neun Preis-Ableitungen wurden geprüft, alle mit Richtung, keine mit Ertrag. Die zehnte wird daran nichts ändern |
| ⛔ **Mehr Sperren** | P4 in 2.602 zeigt: der Gewinn steigt monoton mit der Sperrgröße — das ist der Weg in die Überanpassung, den P2/P3 gerade ausgeschlossen haben |
| ⛔ **Feinere Fünftel oder mehr Zellen** | Das Problem ist nicht die Auflösung. `E[R]` ist in **allen** Zuschnitten negativ |
