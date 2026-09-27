# Vorabfestlegung 29 — was kostet ein veralteter Merkmalswert?

**27.09.2026**, vor der Messung · `messe_altersabschlag.py` ·
Frageart **`markt`**

> **Warum sie gebraucht wird:** Das CoinGecko-Kontingent erlaubt die 16
> Symbole ohne Binance-Daten **nicht stündlich** (17.370 gegen 10.000
> Anfragen/Monat). Ab einem 4-Stunden-Takt passt es. Die Frage ist, was
> dieser Takt kostet — und die soll **gemessen**, nicht gesetzt werden.

---

## Die Frage

> **Wie stark verschlechtert sich die Auswahl, wenn der Merkmalswert
> N Stunden alt ist?**

## Der Aufbau

| | |
|---|---|
| Anker | **unverändert** — gehandelt wird zum Zeitpunkt `t` |
| Merkmal | aus `t − N` statt aus `t` |
| Ertrag | ab `t`, Geometrie H24 / Stop 1,00 / Trailing 1,5 / 0,5 |
| Verzögerungen | **0, 1, 2, 4, 6, 12, 24** Stunden |

⭐ Das ist genau der Betriebsfall: **man handelt jetzt, aber mit
Information von vorhin.**

## Zwei Maßstäbe, weil sie Verschiedenes sagen

| Maßstab | beantwortet |
|---|---|
| **Auswahlüberlappung** mit N=0 | wie viele derselben Werte werden gewählt |
| **Ertrag gegen die tagestreue Nullwelt** | ob die *veraltete* Auswahl **noch trägt** |

⚠️ Die Überlappung allein genügt nicht: eine zur Hälfte andere Auswahl
kann genauso gut sein. Umgekehrt kann eine fast identische Auswahl
trotzdem den entscheidenden Teil verlieren.

## ⚠️ Die Fallen

| # | |
|---|---|
| **1** | **Gleicher Auswahlanteil** bei jeder Verzögerung — sonst vergleicht man die Härte |
| **2** | **Tagestreue Nullwelt** je Verzögerung |
| **3** | **P5**: sieben Verzögerungen sind sieben Ziehungen |
| **4** | ⚠️ Gemessen wird auf den **28 Symbolen mit Binance-Stundendaten** — betroffen sind aber die **16 anderen**. Die Wirkung einer Verzögerung ist eine Eigenschaft der **Achse**, nicht des Symbols; das ist vertretbar, aber es ist eine **Übertragung** und gehört ausgewiesen |
| **5** | Der Ertrag wird ab `t` gemessen, **nicht** ab `t − N` — sonst misst man einen anderen Trade |
| **6** | Regel 2: Gebühren und Finanzierung bleiben draußen |

## Was vorher als Ergebnis gilt

| Ausgang | Folge |
|---|---|
| 4 Stunden trägt noch über dem Mehrfach-Band | ✔ alle 44, CoinGecko im 4-Stunden-Takt |
| nur 1–2 Stunden tragen | ⛔ die 16 gehen mit CoinGecko nicht — Binance zuerst, Rest später |
| auch 0 Stunden trägt hier nicht | ⚠️ dann stimmt am Aufbau etwas nicht (N=0 ist die bekannte Referenz) — **das ist die eingebaute Selbstprobe** |

## Was NICHT beantwortet wird

Gebühren (Regel 2) · der Horizont-Widerspruch · ob CoinGecko-Daten für
**diese** 16 Symbole dieselbe Qualität haben wie für die 27 aus 2.618
