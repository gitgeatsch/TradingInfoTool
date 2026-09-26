# Bestandsaufnahme Hebel — was da ist, was fehlt, was nicht mehr stimmt

**26.09.2026** · Nutzerauftrag: *„Bevor du den Plan zusammensetzt prüfe was
an bestand da ist was fehlt oder veraltet und nicht mehr aktuell ist sonst
wird der Umbau chaotisch."*

Erhoben mit `zeige_modulkarte.py` (nicht per `grep` — genau dafür wurde es
am 27.08. gebaut), dem Befundregister und dem laufenden Code.

---

## ⛔ Zuerst: eine eigene Falschaussage von heute

Ich hatte in der Plananpassung geschrieben, für den Hebel gebe es **keine
Positionsführung**. **Das ist falsch.** Ich hatte nach
`positionsfuehrung.py` gesucht und nicht nach `hebelfuehrung.py`.

> **Nutzerkorrektur 26.09.:** *„der Hebel hat bereits eine Positionsführung
> nur diese ist nicht sauber implementiert da wir immer beim Einstieg und
> dem Hebel als Instrument scheitern"*

✔ **Zutreffend in beiden Teilen** — sie existiert, und sie läuft nie.

---

## A — Was gebaut ist (11 Module)

| Modul | Was es tut | Stand |
|---|---|---|
| `agent/hebelfuehrung.py` | **H-4**: Plan zuordnen, Liquidation, Finanzierung, RM-11, fünf Empfehlungen | 11.09. |
| `agent/hebel_aggregat.py` | **H-5**: Aggregat-Deckel über alle offenen Hebelrisiken | 11.09. |
| `agent/hebel_abgleich.py` | Aktualität des Abgleichs mit Bitpanda | 15.09. |
| `agent/krypto/hebel_risk_gate.py` | RM-1/RM-10/RM-11: Größe, Liquidationspreis | 07. |
| `agent/krypto/hebel_screening.py` | Kandidatensuche, rein rechnerisch | 14.07. |
| `agent/krypto/hebel_pipeline.py` | Trigger → Signal | 07. |
| `agent/krypto/hebel_analyst.py` | LLM-Bewertung | 14.07. |
| `agent/krypto/hebel_backward_tracking.py` | Verfolgung offener Signale | 15.07. |
| `agent/toepfe.py` | getrennte Töpfe Spot/Hebel/Absicherung | 12.08. |
| `agent/krypto/ausstiegsregel.py` | **Trailing ab +1 R** — gemessen | 04.08. |
| `ui/hebel_view.py` | Hebel-Tab | 14.07. |

⭐ **`hebelfuehrung.py` ist vollständiger, als ich angenommen hatte** — sie
hat Liquidationsabstand, tägliche Finanzierung, RM-11 im Lebenszyklus und
hält Regel 2 sauber ein (*„Die Finanzierung ist Information, kein
Auslöser"*).

✔ **Keines dieser Module steht auf der Tot-Liste** (`--tot`).

---

## B — Was gebaut ist und trotzdem nicht läuft

| | Zeilen | Warum |
|---|---|---|
| `hebel_positions` | **0** | es wird nie eine Position eröffnet |
| `hebel_signals` | 5 | steht seit dem 10.08. still |
| `hebel_triggers` | 49 | Kandidaten entstehen, werden aber nicht zu Signalen |
| `hebelfuehrung` | — | läuft über `hebel_positions` — **ohne Position kein Aufruf** |

➤ **Die gesamte Führungskette ist funktionsfähig und arbeitslos.** Der
Engpass ist der **Einstieg**, genau wie vom Nutzer benannt.

⚠️ `asset_hebel_settings` hat 43 freigegebene Symbole, davon **15 liquide
und bewertbar** (2.611).

---

## C — Was fehlt

| # | | |
|---|---|---|
| **1** | **Die neue Bewertung ist nicht verdrahtet** | `ema_abstand_atr` kommt in `agent/` und `scheduler/` **nirgends** vor |
| **2** | **Die Hebelhöhe ist gesperrt** | 2.609: Median −0,1885, Verteilung schief |
| **3** | **Deckung zwischen Messung und Führung** | siehe D-1 |

---

## D — Was nicht mehr stimmt

### ⛔⛔ D-1 — Zwei Trailing-Regeln, die sich um einen Parameter unterscheiden

| | Stop wird nachgezogen | Abstand | gemessen an |
|---|---|---|---|
| **laufend** (`ausstiegsregel.py`) | ab **MFE ≥ 1 R** | 1 R | 495 echten Signalen, EW −0,176 → **−0,084 R** |
| **meine Messung** (2.607/2.608) | **sofort** | 1,0 ATR | 3,18 Mio Ankern, `E[R]` **+0,2079** |

⭐ Bei Trailing-Weite 1,0 ATR ist **1 R = 1 ATR** — die Abstände sind
identisch. Der Unterschied ist **allein `ausloese_r`**: 1,0 gegen 0.

⚠️ **Beide Erwartungswerte der laufenden Regel sind negativ.** Sie
verbessert die Führung, macht das Ergebnis aber nicht positiv. Meine
+0,2079 kommen aus der **Selektion**. Die beiden greifen an verschiedenen
Stellen an und schließen sich **nicht** aus.

⚠️⚠️ **Der Vorbehalt im Modulkopf ist jetzt prüfbar:** *„alle Zahlen
stammen aus EINER Marktphase (Bärenregime). In einer Aufwärtsphase könnte
ein Trailing-Stop Gewinner zu früh beenden."* Mit fünf Jahren Messbasis ist
das messbar.

### ⛔⛔ D-2 — Vier Zahlen für die Haltedauer

| Quelle | Wert | Wofür sie benutzt wird |
|---|---|---|
| `docs/hebel_positionsformel.md` | **Ø 1,1 Tage** | Kalibrierung des **15-Minuten-Takts** |
| Befund über 188 echte geschlossene Positionen | **Median 0,30 Tage** | — |
| „Betrieb rechnet" (Befundregister) | **3,4 Tage** | Finanzierungsrechnung |
| meine Messung 2.607/2.608 | **H = 72 h = 3 Tage** | die Zielgröße |

⚠️⚠️ Mittelwert 1,1 und Median 0,30 widersprechen sich nicht (schiefe
Verteilung) — aber **drei verschiedene Werte gehen in drei verschiedene
Rechnungen**, und mein Messhorizont ist ein vierter. **Das gehört
vereinheitlicht, bevor verdrahtet wird**, sonst rechnet jede Stelle mit
einer anderen Annahme.

### ⚠️ D-3 — Die Zielzone 2–5× ist tautologisch

Befundregister: *„`hebel_ab` 2,0 und `hebel_grenze` 5,0 **erzwingen** sie.
Dass die Werte dort liegen, ist keine Aussage."* — M1-Kriterium 2 nennt sie
trotzdem.

---

## E — Prüftakt und Cooldown

> **Nutzerhinweis 26.09.:** *„vergiss nicht den Punkt — Prüftakt und
> Cooldown, diese werden u.U. auch noch einmal wichtig vor einem
> Produktivgang."*

| | Wert | Herkunft |
|---|---|---|
| **Prüftakt Hebel-Screening** | **15 Minuten** | `HEBEL_SCREENING_INTERVAL_MINUTES`, kalibriert auf Ø 1,1 Tage |
| **Cooldown** Kern/Taktisch | **3,5 h** | `cooldown_stunden`, F-214 — *kein Bug*, bestätigte 3–4-h-Spanne |
| **Cooldown** ausgemustert | 120 h | `hebel_cooldown_stunden_ausgemustert` |

⛔⛔ **Zwei registrierte Befunde, die hier zusammenstoßen:**

| | |
|---|---|
| **2.461-sperre** | **Keine Sperrlänge trägt** — jede liegt unter dem Nullpunkt ihrer eigenen Nullwelt. Kosten: 43 % der Anker bei einem Tag, 87 % bei zwanzig |
| **„N hinein, 0 heraus"** | **Takt und Cooldown sperren 69 %**, die Bewertung fast nichts |
| **Wiederholungssperre** | **stärkster Filter der Kette: 94,1 %** |

⚠️⚠️ **Die Rechnung, die daraus folgt und die noch niemand gemacht hat:**
Die Bewertung liefert **2,0 Signale/Tag** (2.608) — das ist **vor** Takt und
Cooldown. Sperren diese wie gemessen 69 %, bleiben **0,6 Signale/Tag**.
⚠️ Die 3,5 h liegen zudem **unter der Tagesauflösung** der Messung
(2.461-sperre-auflösung) — sie sind **ungemessen**.

➤ **Das ist ein eigener Punkt vor dem Produktivgang**, und der Nutzer hat
recht, ihn jetzt zu nennen: eine Bewertung, die 69 % ihrer Signale an einer
Sperre verliert, die **nachweislich nichts trägt**, ist kein tragfähiger
Betrieb.

---

## Was daraus für den Umbau folgt

| # | |
|---|---|
| **1** | ⭐ **Es wird weniger gebaut als gedacht.** Führung, Risiko-Gate, Aggregat-Deckel, Ausstieg — alles da. Es fehlt der **Einstieg** und seine Verdrahtung |
| **2** | **D-1 ist eine Messung auf einer Parameterachse** (`ausloese_r`), kein Neubau |
| **3** | **D-2 muss vor der Verdrahtung entschieden werden** — eine Haltedauer, nicht vier |
| **4** | **E gehört vor den Produktivgang**, nicht danach |

## Was NICHT folgt

| # | |
|---|---|
| **1** | ⛔ Nichts gebaut, nichts geändert — reine Bestandsaufnahme |
| **2** | Ob `hebel_analyst` erreichbar ist, widersprechen sich Modulkarte und Suite (2.343) — **ungeklärt** |
| **3** | Die **Hebelhöhe** bleibt gesperrt (2.609) |
| **4** | Nichts über **Short** |
