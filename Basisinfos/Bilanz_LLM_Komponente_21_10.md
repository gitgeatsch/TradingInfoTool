# Bilanz der LLM-Komponente (Stand 21.10.2026)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte.

**Wozu:** Nutzer 21.10.: *„Die LLM-Komponente sollte hier einen Mehrwert und Nutzen liefern – was wir offenbar nicht schaffen … Wenn sich das als Deadend herausstellt, brauchen wir das System so nicht weiterverfolgen. Halte alle Ergebnisse und Messungen fest.“*

Dieses Blatt fasst **jeden** geprüften Weg zusammen: was gefragt war, wie gemessen wurde, was herauskam und warum. Die Einzelheiten stehen in den genannten Abschnitten von `Voranalyse_Schritt7_Betrieb_02_10.md` (Schritt7) und in den Entscheidungen E-n.

## 1. Was die LLM-Komponente leisten sollte

- **Ziel (E-78, Nutzer):** *besser als die Regel*. Minimum: *gleich oder etwas besser als Bestätigung/Gegenmeinung*.
- **Rolle:** Prüfung, kein Entscheider. Der LLM ändert kein Signal, er urteilt darüber.
- **Betrieb heute:** Ein Trader-Prüfblock steht in jeder REGEL0-Signalmail, Modell gemini-3.5-flash-lite (5 Stimmen), markiert *„gemessen: trennt nicht“*. Der Entscheider ist seit 0.1e aus.

## 2. Alle geprüften Wege

| # | Weg | Frage | Ergebnis | Beleg |
|---|---|---|---|---|
| 1 | Sofortfassung 0.1 (Rollen Markt, Trader, Entscheider) | Trennen die Urteile? | Trader 9/10 *dagegen* (kannte die Wette des Plans nicht); nach 0.1b mit Wette weiter konstant | Schritt7 §20.12, E-50 bis E-52 |
| 2 | 0.1c / 0.1d Entscheider | Bringt ein Gesamturteil Neues? | Markt sagte zu 85 % *stützt*, der Entscheider erbte die Konstanz; mit nur dem Trader **Echo 39/40** → Entscheider aus | E-53, E-82 |
| 3 | **N4** (Fassung 0.1e, Rückspiel) | Trennt der Trader im Rückspiel? | **STOP-ANPASSEN** am Zwischenentscheid (07.10.) | Schritt7 §23.12 |
| 4 | A2 Teil 2 | Trennt irgendeine der 12 Eingangszahlen **innerhalb** der REGEL0-Signale? | **keine** → „besser als die Regel“ über Zahlen nicht erreichbar | Schritt7 §23.18 |
| 5 | **N5** (Fassung 0.2 mit der Lage zur Signalstunde) | wie N4 | **STOP-ANPASSEN** (10.10.); wo der LLM *dagegen* sagte, lief es **besser** (2025 −2,60 Pp, 2026 −3,95 Pp) | Schritt7 §23.51 |
| 6 | Ursachenanalyse | Warum trennt er nicht? | Sechs Ursachen: Lehrbuch-Trendlogik statt Wette; Pessimismus (*dagegen* 43–52 %); **die Eingangszahlen tragen selbst kaum (|ρ| ≤ 0,15) und wechseln mit dem Regime**; Rauschen (5/5 einig nur 34–45 %); kleines Modell; Messmenge ≠ Betrieb | Schritt7 §23.52 |
| 7 | W3 Regime als Gewicht | Hilft das Regime (BTC 7 T) als Eingang? | **nein**, das Vorzeichen wechselt 2025/2026 | Schritt7 §23.62, E-117 |
| 8 | E-1 Binance-Ankündigungen | Trägt ein strukturiertes Ereignis (Delisting, Monitoring)? | nach der Vorabregel **nicht** (2 von 4 Mengen); linkes Ende sichtbar, aber zu selten. Braucht keinen LLM | Schritt7 §23.23 |
| 9 | O21 Stufe 2 (Schatten) | Was kann ein Vorwärtsvergleich entscheiden? | nur große Effekte (Filter ≥ 0,25–0,5 Pp, sonst ≥ 0,5–1 Pp in 1–2 Jahren) → zurückgestellt | Schritt7 §23.70 |
| 10 | **L-C** Asset-Nachrichten als Risikoprüfer | Werden die Assets des linken Endes in Nachrichten genannt? | **nein**: Tief-Fälle zu 94 % außerhalb der Top 50, nur 7–9 % mit Meldung, 43 von 112 Assets nie genannt | Schritt7 §23.71, §23.72 |
| 11 | **L-C2** Marktnachrichten des Vortags | Kündigen sie die 16 Absturztage an? | **trägt nicht** (gpt-oss-120b, 497 Tage, Lift 0,88 [0,19–1,71], Zufall gleich gut in 71 %; vor dem Crash 10.10.2025 *niedrig*) | Schritt7 §23.73 bis §23.75 |

## 3. Querschnittsbefunde

- **Information ist der Engpass, nicht das Modell.** Über dieselben Zahlen wie die Regel kann ein LLM die Regel nicht schlagen (Ursache 3, A2). Nachrichten erreichen die kleinen Werte nicht, und die Abstürze kommen durch Ereignisse innerhalb der 24 h.
- **Der LLM neigt zur Warnung:** Trader *dagegen* 43–52 % (N5); L-C2 *hoch* an 28 % der Tage bei 3,2 % Absturztagen.
- **Kontamination (§23.73):** gemini-3.5-flash-lite kennt Kurse bis etwa Oktober 2025, qwen3.8 bis etwa August 2025.
  - ⇒ **Vorbehalt für N4/N5:** Rückspiele auf 2025 mit Gemini konnten den Ausgang kennen. Das Ergebnis „trennt nicht“ bleibt, ist aber kein sauberer Test.
  - Sauber für 2025–26 sind gpt-oss-120b und ministral-8b.
  - Probe mit **Positivkontrolle** und **erzwungener** Schätzung: Ein Modell, das „unbekannt“ sagen darf, wirkt sauberer, als es ist.
- **Kostenfreie Grenzen:** Gemini 500/Tag (geteilt mit dem NB), Groq 200.000 Tokens/Tag. Cerebras und die Unlocks bei DefiLlama sind nicht kostenfrei.

## 4. Was nicht geprüft ist (und warum)

- **Entscheider-Neubau (O22):** Er braucht eigene Information über *diesen* Handel. Keine der geprüften Quellen liefert sie.
- **Stärkeres Modell (L-E):** Für die geprüften Fragen begrenzt die Information, nicht die Modellstärke. Für ein Rückspiel kommen nur Modelle mit Wissen vor 2025 infrage, und das stärkste davon (gpt-oss-120b) hat L-C2 geprüft.
- **LLM als Erklärer in der Mail** (Fakten verständlich zusammenfassen): Das ist kein Mehrwert in der Trefferquote und war nie das Ziel.

## 5. Stand und Folge

- **Nach allen geprüften Wegen liefert die LLM-Komponente keinen messbaren Mehrwert** für die REGEL0 (Hebel). Ein weiterer Weg mit Aussicht ist aus den freien Daten nicht erkennbar.
- **Betrieb unverändert:** Der Prüfblock steht in der Mail, markiert *„trennt nicht“*. Ob er bleibt, aus der Mail kommt oder das System so nicht weiterverfolgt wird, entscheidet der Nutzer.
- **Verwertbar bleiben:**
  - das kostenfreie Nachrichtenarchiv 2025–26 (`data/_lc/nachrichten.db`, 39.926 Meldungen);
  - die Kontaminationsprobe als Standard vor jedem LLM-Rückspiel;
  - der Nebenbefund *Signalflut* (43 % des linken Endes an 10 Tagen mit ~30 Signalen), ohne LLM auf der Messbasis messbar.
- **Nächster Schritt (Nutzer 21.10.):** Recherche **Grid-Trading** mit oder ohne LLM, Start mit BTC und einem Altcoin.
