# Vorabfestlegung 30 — lässt sich die Skala von Stufe D angleichen?

**27.09.2026**, vor der Messung · `messe_skalenangleich.py` ·
Frageart **`markt`**

> **Warum:** Dieselbe Schwelle −1,2881 trifft bei Stufe A (echtes OHLC)
> 0,330 % der Anker, bei Stufe D (nur Schlusskurse) **8,515 %** —
> Faktor 25,8. Die ATR-Ersatzgröße ist etwa halb so groß, `W` wird doppelt
> so groß im Betrag. Die Rangkorrelation ist 0,9964: **die Ordnung
> stimmt, nur die Skala nicht.**

---

## Die Frage

> **Trägt Stufe D nach einer Skalenkorrektur bei DERSELBEN Schwelle —
> oder feuert sie dann nur gleich oft?**

⚠️ Das sind zwei verschiedene Fragen. Gleich oft feuern ist trivial
herstellbar; **tragen** ist es nicht.

## ⭐ Woher der Faktor kommt — und woher NICHT

| | |
|---|---|
| **Erlaubt** | aus dem **Verhältnis der ATR-Größen** — eine reine Skaleneigenschaft der Messgröße |
| ⛔ **Verboten** | aus dem **Ertrag** oder aus der Trefferzahl — das wäre Kurvenanpassung, und genau davor warnt 2.616 beim √24-Faktor (*hergeleitet, nicht angepasst*) |

➤ `faktor = median(ATR_A) / median(ATR_D)`, je Symbol bestimmt.

⭐ Der Wert ist grob bekannt: **0,48×** Methodendifferenz aus 2.616/2.618.

## ⚠️ Die Fallen

| # | |
|---|---|
| **1** | ⛔ **Der Faktor darf den Ertrag nicht kennen.** Er wird aus der ATR-Verteilung bestimmt, bevor irgendein Ergebnis gerechnet wird |
| **2** | **Out-of-sample**: Faktor auf der ersten Hälfte bestimmen, auf der zweiten anwenden — und umgekehrt |
| **3** | ⭐ **Ist der Faktor je Symbol stabil?** Ein globaler Faktor funktioniert nur, wenn er nicht je Asset davonläuft. Streuung über die Symbole ausweisen |
| **4** | **Beide Maßstäbe**: bei gleicher Schwelle *und* bei gleichem Auswahlanteil. Der zweite reproduziert 2.616 und ist damit die Kontrolle |
| **5** | **Tagestreue Nullwelt**, 40 Ziehungen |
| **6** | ⚠️ Gemessen auf den Symbolen **mit** OHLC — nur dort lassen sich A und D vergleichen. Für die 16 ohne ist es eine **Übertragung** |
| **7** | Regel 2: Gebühren und Finanzierung bleiben draußen |

## Was vorher als Ergebnis gilt

| Ausgang | Folge |
|---|---|
| D korrigiert trägt bei derselben Schwelle, Faktor je Symbol stabil | ✔ **eine** Schwelle für alle 44 — Weg 2 |
| trägt, aber der Faktor schwankt je Symbol stark | ⚠️ dann Faktor **je Symbol** — mehr Stellschrauben, eigene Entscheidung |
| trägt nicht | ⛔ **nur Binance, 28 Symbole** — Weg 3 |

## Was NICHT beantwortet wird

Ob CoinGecko-Daten für **diese** 16 Symbole dieselbe Qualität haben wie
für die 27 aus 2.618 · Gebühren · der Horizont-Widerspruch
