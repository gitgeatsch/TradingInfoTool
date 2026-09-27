# Vorabfestlegung 28 — trägt die Achse auf TAGESBASIS?

**27.09.2026**, vor der Messung · `messe_tagesbasis.py` ·
Frageart **`markt`**

> **Warum sie gebraucht wird** (Voranalyse Schritt 1): Die gemessene
> Achse `ema_abstand_atr` beruht auf **stündlichen** Ankern mit
> EMA über **48 Stunden**. Der Betrieb hat ausschließlich **Tagesdaten** —
> keine einzige stündliche Kursreihe in 31 Tabellen. Ohne diese Klärung
> ist Schritt 1 nicht baubar: man würde ein Merkmal registrieren, das im
> Betrieb nicht berechenbar ist.

---

## ⚠️ Was 2.616 NICHT beantwortet hat

2.616 sieht aus, als wäre die Auflösungsfrage geklärt. Im Quelltext von
`messe_aufloesung_und_fallback.py` steht aber:

| Zeile | | Folge |
|---|---|---|
| `:217` | `e = ema(cc, 48)` | die EMA läuft auf **stündlichen** Schlusskursen |
| `:130-134` | ATR *„zurück auf Stunden, kausal versetzt"* | das Raster bleibt **stündlich** |
| `:222` | `VORLAUF = 240` | 240 **Stunden**, Anker = jede Stunde |

➤ Gröber wurden nur die **Kerzen**, nicht die **Anker** und nicht die
**EMA**. Die Frage ist offen.

## Die Frage

> **Trägt die Achse, wenn das Merkmal aus TAGESDATEN kommt und es nur
> EINEN Anker pro Tag gibt?**

## ⭐ Der Aufbau zerlegt die zwei Ursachen

Zwischen der gestrigen Messung und dem Betriebsfall liegen **zwei**
Unterschiede. Ein einzelner Vergleich könnte sie nicht trennen:

| Arm | Merkmal aus | Anker | misst |
|---|---|---|---|
| **1** | Stunden (EMA48h) | **jede Stunde** | die Referenz — 2.626/2.632 |
| **2** | Stunden (EMA48h) | **1 pro Tag** | was die **Ankerreduktion** kostet |
| **3** | **Tagen** (Tages-EMA, Tages-ATR) | **1 pro Tag** | was die **Auflösung** zusätzlich kostet — **der Betriebsfall** |

➤ Differenz 1→2 ist die Ankerzahl, 2→3 ist die Auflösung.

## ⭐ Die Zielgröße bleibt stündlich — und das ist kein Widerspruch

Der **Ertrag** wird weiter aus den Stundenkursen gerechnet (Trailing
1,5 R / 0,5 R, Stop 1,00 ATR, H24). Das ist die **Wahrheit** darüber, was
tatsächlich passiert wäre — sie ändert sich nicht dadurch, dass der
Betrieb sie nicht sieht.

⭐ Genau so lief 2.618: *Bewertung aus CoinGecko, Ertrag auf Binance.*
Nur die **Bewertung** muss aus dem kommen, was der Betrieb hat.

## Die EMA-Länge auf Tagesbasis

**2.606** hat gemessen: **48 Stunden ist das Optimum**, und beim
klassischen 50-Tage-EMA (1.200 h) fällt MFE/MAE auf **1,00** — völlig
symmetrisch, also wertlos. 48 h sind **2 Tage**.

⚠️ Eine Tages-EMA über 2 Punkte ist nicht dasselbe wie eine Stunden-EMA
über 48. Deshalb werden mehrere Längen geprüft: **2, 3, 5, 8, 13, 21**
Tage.

## ⚠️ Die Fallen

| # | |
|---|---|
| **1** | **Kausalität**: das Tagesmerkmal darf nur **abgeschlossene** Tage nutzen. Der Anker sitzt auf Stunde 0; die Tageskerze von gestern ist die jüngste erlaubte. Ein Off-by-one macht die Messung wertlos und sieht dabei gut aus |
| **2** | **Mehrfachtesten (P5)**: sechs EMA-Längen sind sechs Ziehungen. Bestes-von-sechs-Band |
| **3** | **Gleicher Auswahlanteil** über alle Arme — sonst vergleicht man die **Härte** statt der **Ordnung** (registrierte Regel) |
| **4** | **Tagestreue Nullwelt** je Arm |
| **5** | ⚠️ Bei einem Anker pro Tag ist die Ankermenge **24-mal kleiner**. Ein schwächeres Ergebnis kann allein daher kommen — deshalb Arm 2 als Zwischenstufe |
| **6** | **Dieselbe Ankermenge** in Arm 2 und 3, damit nur das Merkmal sich unterscheidet |
| **7** | Regel 2: Gebühren und Finanzierung bleiben draußen |

## Was vorher als Ergebnis gilt

| Ausgang | Folge |
|---|---|
| Arm 3 trägt über dem Mehrfach-Band | ✔ **Schritt 1 ist klein** — Tages-EMA und Tages-ATR in `marktrang.py`, fertig |
| Arm 3 im Band, Arm 2 trägt | ⛔ die **Auflösung** ist das Problem ➤ Stundendaten in den Betrieb holen |
| Arm 2 schon im Band | ⛔ die **Ankerzahl** ist das Problem ➤ ebenfalls Stundendaten, und die Signalzahlen aus 2.633 gelten nicht für den Betrieb |

## Was NICHT beantwortet wird

Gebühren (Regel 2) · Gaps und Slippage · der Horizont-Widerspruch
(H24 gegen 3 Tage gegen 0,30 Tage real) · wie die Schwelle in
Fünftel-Stufen übersetzt wird
