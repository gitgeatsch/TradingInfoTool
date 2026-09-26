# Vorabfestlegung 26 — die stetige Hebelkurve

**26.09.2026**, vor der Messung · `messe_hebelkurve_stetig.py` ·
Frageart **`markt`**

> **Nutzereinwand, der sie ausgelöst hat:** *„hier ist es etwas stufenartig
> und nicht regelmäßig — Warum nicht −1,3?"* und *„eigentlich sollte das
> System entscheiden ob −1,0 jetzt besser ist und den Hebel so anwenden,
> also ich habe mir das so vorgestellt, dass eben das Risiko mit der
> Qualität steigt, also der Hebel"*

---

## Was an der Bandmessung falsch war

Die Bandmessung vom selben Tag hat die **Ordnung belegt** — 5 von 5
Jahren fallend, 54 von 63 Symbolen, 4 von 4 Blöcken. Das gilt.

⛔ **Aber die Bandgrenzen waren gesetzt, nicht gemessen.** −2,0 / −1,5 /
−1,2 / −1,0 sind vier Stellschrauben, die ich in die Rechnung eingeführt
habe. Auf die Frage *„warum nicht −1,3"* gibt es keine Antwort, die nicht
willkürlich ist.

⚠️ Das ist derselbe Fehlertyp wie bei der Grundgesamtheit: **eine Wahl,
die wie ein Befund aussieht.** Und das Regelwerk verlangt umgekehrt, dass
die Form aus der Sache folgt, nicht aus meiner Tabelleneinteilung
(`feedback_formwahl_immer_begruenden`).

## Die Frage

> **Wie hoch ist der Hebel bei gegebener Lagequalität — als stetige
> Funktion, ohne Bandgrenzen?**

## Die Konstruktion — sie steht bereits vollständig im Code

| Schritt | woher |
|---|---|
| **1** | `q(W)` und `CRV(W)` **stetig** schätzen — gleitendes Fenster über den nach `W` sortierten Ankern, kein Gitter, keine Klassen |
| **2** | `kelly(W) = (q·(1+CRV) − 1)/CRV` — steht seit langem in `agent/betraege.py:365` |
| **3** | `hebel(W, ATR) = (kelly(W)/2) · N / s` mit `s` = Stopweite (1,00 ATR) und `N` = Zahl gleichzeitiger Positionen. **Herleitung:** Kelly ist der Kontoanteil, der bei Stop verloren geht; `f·Konto = s·Position` ⇒ `Position/Konto = f/s`; bei `N` Positionen zu je `1/N` Margin ist der Hebel das `N`-fache |
| **4** | Deckel: **RM-11** (`max_safe_hebel(s·100, 0,09)`) und die Nutzer-Zielzone **2–5×** |

⭐ **Die Mindestschwelle wird damit GERECHNET, nicht gewählt**: sie liegt
dort, wo `hebel(W)` unter 2× fällt. Dieselbe Frage, aber ohne
Stellschraube — und sie beantwortet *„warum nicht −1,3"* von selbst.

## ⚠️ Die Fallen

| # | |
|---|---|
| **1** | **Ein gleitendes Fenster glättet auch Rauschen zu einer schönen Kurve.** Gegenmittel: dieselbe Kurve auf einer tagestreuen **Nullwelt** schätzen — sie muss flach sein |
| **2** | **Monotonie ist eine Behauptung, keine Voraussetzung.** Erst die rohe Kurve zeigen, dann prüfen, ob sie monoton ist. Keine Isotonie erzwingen, bevor die Rohform gesehen ist |
| **3** | **Out-of-sample**: Kurve auf der ersten Hälfte schätzen, auf der zweiten anwenden. Wenn der vorhergesagte Hebel dort nicht mit dem realisierten Ertrag korreliert, ist die Kurve Anpassung |
| **4** | ⭐ **`s` ist nicht konstant** — 1,00 ATR variiert je Asset und Zeit. Der Hebel ist deshalb eine Funktion von **(W, ATR)**, nicht von `W` allein. Das ist konsistent mit 2.627 (*die Hebelhöhe folgt dem Risiko*) |
| **5** | **Regel 2**: Finanzierung und Gebühren bleiben aus `q` und `CRV` draußen |
| **6** | **Regel 3**: die Kurve kennt kein Asset — sie liest nur `W` und `ATR` |

## Was vorher als Ergebnis gilt

| Ausgang | Folge |
|---|---|
| `kelly(W)` fällt **monoton** und ist out-of-sample bestätigt | ✔ die Kurve **ist** die Kalibrierung; die Schwelle ist ihre 2×-Nullstelle |
| Monoton, aber out-of-sample flach | ⚠️ die Ordnung trägt, die **Höhe** nicht — dann fester Hebel über der Schwelle |
| Nicht monoton | ⛔ zurück zu Bändern — dann aber mit begründeten Grenzen |

## Was NICHT beantwortet wird

Gebühren in der Bewertung (Regel 2) · Gaps und Slippage · Short ·
wie viele Positionen `N` gleichzeitig laufen (Nutzerentscheidung)
