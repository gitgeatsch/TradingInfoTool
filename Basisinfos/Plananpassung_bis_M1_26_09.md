# Plananpassung bis M1 — der Weg vom Messen zum Betrieb

**26.09.2026** · Nutzerauftrag: *„wenn du der Meinung bist wir haben genug
informationen sollten wir eine saubere Plananpassung bis zum Ende von M1
vornehmen"*

---

## Warum eine Anpassung nötig ist — gemessen, nicht eingeschätzt

| | |
|---|---|
| Commits seit 25.09. | **21** |
| Befunde 2.597–2.619 | **23** |
| `ema_abstand_atr` in `agent/` oder `scheduler/` | ⛔ **nirgends** |
| `hebel_positions` | **0 Zeilen** |

**Zwei Tage Messung, null Zeilen im laufenden Code.** Die gesamte neue
Bewertung existiert ausschließlich in Messwerkzeugen.

⭐ **Der Auftrag vom 25.09. ist erfüllt** — *„Wir bauen den Hebel-Arm
vollständig neu"*: absolute Schwelle statt Perzentil, `E[R]` +0,2079, in
allen fünf Jahren belegt, Gegenprüfungen bestanden, Fallback gemessen,
BTC geklärt. **Was jetzt fehlt, ist kein Wissen, sondern Verdrahtung.**

---

## Der Hebel-Lebenszyklus — Nutzergliederung 26.09.

> *„HEBEL: 1. Einstieg 2. Hebelhöhe 3. LLM Bewertung 4. Positionsführung
> wenn Trade eröffnet (Trailing der Position?) 5. Ausstieg"*

| # | Stufe | Stand | Was fehlt |
|---|---|---|---|
| **1** | **Einstieg** | ✔✔ **gemessen** (2.608): absolute Schwelle 1,0 ATR, `E[R]` +0,2079, 2,0 Signale/Tag | ⛔ **nicht verdrahtet** |
| **2** | **Hebelhöhe** | ⛔⛔ **gesperrt** (2.609): Median −0,1885, Verteilung schief | Schiefe, längste Verlustserie, geometrischer Ertrag — **eine Messung** |
| **3** | **LLM-Bewertung** | offen (Kriterium 4, Phase 8) | ⚠️ gilt: *LLM ist Prüfung, nicht Entscheider* |
| **4** | **Positionsführung** | ⛔⛔⛔ **existiert für den Hebel NICHT** | siehe unten — **das ist der Fund** |
| **5** | **Ausstieg** | teilweise: `ausstiegsrechnung.py` läuft, aber für **Spot** | Hebel-Ausstieg ungeprüft |

### ⛔⛔⛔ Der Fund: Stufe 4 gehört IN M1, nicht danach

`agent/positionsfuehrung.py` existiert und trägt eine **gemessene Regel
(+0,092 R)** — aber ihr Modulkopf sagt:

> *„Eine Spot-Position hat nach Nutzerangabe KEINEN Stop (‚aktuell auch
> ohne StopLoss'). Sie hat deshalb auch kein R und keinen sinnvollen
> Positions-MFE."*

**Ein Hebel-Trade hat zwingend einen Stop** — die Liquidation erzwingt ihn.
Für den Hebel gibt es **keine** Positionsführung; `hebel_positions` hat
**0 Zeilen**.

⚠️⚠️ **Und deshalb ist Stufe 4 keine Erweiterung, sondern eine
Voraussetzung:**

```
E[R] = +0,2079   gemessen MIT Trailing 1,0 ATR
```

Führt der Betrieb die Position anders — fester Stop, Ziel, MFE-Regel wie
bei Spot — **gilt diese Zahl nicht**. Einstieg und Führung sind nicht
trennbar; der Erwartungswert hängt an beiden.

➤ Das ist der registrierte Befund **2.591 „Messgeometrie ist nicht
Betrieb"**, und er wiederholt sich hier.

---

## Der Plan bis M1

| # | Schritt | Art | Kriterium |
|---|---|---|---|
| **A** | **Hebelhöhe klären** — Schiefe, längste Verlustserie, geometrischer gegen arithmetischen Ertrag (2.609) | Messung, **1 Lauf** | 2 |
| **B** | **Positionsführung für den Hebel** — Trailing 1,0 ATR als Betriebsregel, deckungsgleich mit der Messung | **Bau + Nachweis am Seiteneffekt** | 2 |
| **C** | **Verdrahten**: Bewertung → Signal → Mail, auf den 15 liquiden Symbolen | **Bau** | 5 |
| **D** | **Hebel-Ausstieg** gegen die bestehende `ausstiegsrechnung` prüfen | Prüfung | 2 |
| **E** | **Durchgängigkeit am Papier** | Prüfung | **5** |
| **F** | **Rudimentäre Wirksamkeit** beobachten | Beobachtung | **7** |

⚠️ **A vor B vor C** ist zwingend: ohne Hebelhöhe keine Positionsgröße,
ohne Führungsregel gilt der Erwartungswert nicht, und ohne beides ist die
Verdrahtung eine leere Hülle.

⚠️⚠️ **Zu B gehört ein Nachweis am Seiteneffekt**, nicht am Test — die
registrierte Regel *„Ein Test deckt die FUNKTION ab, nicht den PFAD"*
(`potential.rechne` reichte `instrument` 14 Tage lang nicht weiter, der
Test war grün).

### Was in M1 NICHT mehr angefasst wird

| | Begründung |
|---|---|
| **Stufe 3 (LLM)** | Kriterium 4, Phase 8 — und laut stehender Vorgabe ohnehin *Prüfung, nicht Entscheider*. Ohne Verdrahtung gibt es nichts zu prüfen |
| **Stammsatz** | ⭐ **gleich nach M1** (Nutzerentscheidung 26.09.: *„da es gesamt relevant ist"*) — er bringt **Breite** (15 → ~24 Symbole), nicht **Tiefe** |
| **Kriterium 1 (Spot)** | Haken entzogen (Nutzerbefund 25.09.). Nach dem Hebel |
| **Kriterium 3 (Akkumulation)** | Maß gemessen, Weg liefert null Signale. Nach dem Hebel |

⚠️ **Eine Ausnahme beim Stammsatz:** **ASTER, CANTON und MON sind offene
Positionen ohne Messreihe** — gebundenes Kapital ohne Bewertungsgrundlage
(2.611/2.615). Das ist ein eigenes, kleines Thema und hängt nicht am
Stammsatz.

---

## Die Reihenfolge danach

> **Nutzervorgabe 26.09.:** *„Wenn wir das bei Hebel erreicht haben sind
> Spot und Akkumulation an der Reihe."*

| Rang | | |
|---|---|---|
| **1** | **M1 — Hebel vollständig** | Stufen 1, 2, 4, 5 + Verdrahtung |
| **2** | **Stammsatz** | gesamt relevant, danach greift jede Erweiterung |
| **3** | **Stufe 3 — LLM** | erst wenn es etwas zu prüfen gibt |
| **4** | **Spot** | Kriterium 1, Haken neu zu verdienen |
| **5** | **Akkumulation** | Kriterium 3, der Weg ist umzubauen |

---

## Was NICHT folgt

| # | |
|---|---|
| **1** | ⛔ **M1 ist nicht nah.** Vier der sieben Kriterien sind offen (1, 4, 5, 7), und zwei davon brauchen erst die Verdrahtung |
| **2** | Die **Hebelhöhe** ist gesperrt, bis A gemessen ist — kein Trade ohne Größe |
| **3** | Der gemessene Erwartungswert ist **brutto**: Gebühren und Finanzierung bleiben nach Regel 2 draußen |
| **4** | Warum das **höchste ATR-Fünftel** nicht trägt, ist offen (2.617) |
| **5** | Nichts über **Short** |
