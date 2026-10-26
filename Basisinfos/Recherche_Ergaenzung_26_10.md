# Recherche-Ergänzung: Elliott-Wellen, Chart + Makro, weitere Ansätze (26.10.2026)

Nutzer 26.10.: *„danach prüfe noch einmal auf recherchebasis welche Möglichkeiten noch bestehen und wir nicht berücksichtigt haben: Eliot Wellen Methode, Kombinationen chart und Makro, sonstiges“*

**Abgrenzung:** Die Recherche R-A vom 22.10. (`Recherche_Neue_Ansaetze_22_10.md`, E-129) hat schon bewertet:
- Carry; Trendfolge (TSMOM);
- Faktoren, Kalender, Paarhandel, Liquiditätsgabe;
- Token-Freigaben, Volatilitätssteuerung, Allokation.

Diese Ergänzung sucht nur, was dort **fehlte**, und gleicht jeden Fund mit R-A und unseren Messungen ab.

**Vorgehen:**
- Eine Recherche im Web, als Auftrag mit der vollständigen Liste dessen, was bei uns gemessen ist.
- **Gegenprüfung durch mich:** die Datenquellen selbst abgefragt (je eine Abfrage, nichts geladen) und eine tragende Literaturaussage an der Quelle nachgelesen.
- **[B]** = begutachtet bzw. offene Methode; **[I]** = Industrie oder Blog, ohne Test außerhalb der Stichprobe.

## 1. Ergebnis

| Ansatz | Beleglage | nach 2023 | freie Daten (selbst geprüft) | Abgleich | **Urteil** |
|---|---|---|---|---|---|
| **Elliott-Wellen / Fibonacci** | kein objektiver Test außerhalb der Stichprobe; automatische Fibonacci-Zonen ohne Unterschied zu anderen Zonen [B]; Retracements ohne ausgezeichnete Niveaus [B] | – | Kurse ✔ | objektiv kodierbar nur als Zickzack-/Swing-Regel ⇒ **gemessen** (Kursmerkmale, Spot §19/§35) | ✘ **nein** |
| **Chart-Signal nur in einem Makro-Regime** | keine Studie für Krypto 2020–26; Hudson/Urquhart (≈ 15.000 Regeln, Data-Snooping-Korrektur): **Bitcoin außerhalb der Stichprobe ohne Vorhersagekraft** [B, von mir an der Quelle nachgelesen] | – | ✔ | Regime hat bei uns ~70 Wechsel (E-151); eine Bedingung erhöht die Mehrfachtest-Last | ✘ **nein** (Makro bleibt Gewicht/Fakt, E-131) |
| **Volatility-Targeting** als Größenregel | Sharpe-Gewinn bei Risiko-Assets, kleinere Ränder in allen Klassen [B]; Bitcoin Sharpe ↑ [B, nur Zusammenfassung]; R-A: außerhalb der Stichprobe nicht besser, aber Bremse [B] | wenig | eigene Kurse ✔ | **Lücke im Betrieb**: Hebel nach ATR, Positionswert fest 1.500 € (Voranalyse Reife/Vola §2) | ✔ **ja** — Messplan **V-1** liegt vor |
| **ETF-Flüsse** (BTC/ETH, mit Verzögerung ≥ 1 T) | gleichzeitig stark [B]; verzögert nur vorläufig, r ≈ 0,30 bei 1 T [I] | ✔ ab 01/2024 | **Farside ✔ frei** (Webseite, Status 200, Tabelle seit 2024, keine Sperre; keine offizielle Schnittstelle) | **neu**, bei uns nie gemessen | ◐ **vielleicht**: erst Machbarkeit (Auflösung) |
| **Deribit DVOL** (implizite Vola BTC/ETH) | Rendite-Prognose nicht belegt; Varianzprämie regimeabhängig [B] | ✔ | **öffentliche API ✔** (1.000 Tage je Abfrage, weiter mit `continuation`) | neu; passt nur als **Risikogröße** (V-1-Variante für BTC/ETH) | ◐ nur als Variante in V-1 |
| TSMOM mit Vola-Skalierung 1–7 T | stark bis 2018 [B]; nach der Futures-Einführung verschwunden [B] | unklar | ✔ | R-A: TSMOM 1,41 → 0,41; Momentum bei uns gemessen | ✘ |
| Intraday-Momentum, Wochentag, Stunde, Sessions | bis 2022 teils belegt [B/I], nicht dauerhaft [B] | nicht gezeigt | ✔ | R-A: Kalender verschwunden; **Regel 1** (*der Takt ist nie Signalgeber*); Kosten bei Stunden-Haltedauer | ✘ |
| USDT-Mints | 2017/18 [B]; Gegenstudie: keine Rendite, nur Umsatz [B] | – | ✔ | Stablecoins gemessen (Spot §16, §45 U1) | ✘ |
| CME-Gaps, Halving-Zyklus | ohne seriöse Methode [I]; Halving nichts nach FDR [B] | – | – | Regel 1 (Takt) | ✘ |
| ETH/BTC-Paar, Kointegration | nach Kosten schwach oder negativ [B] | – | ✔ | R-A verworfen; ohne Short bleibt nur Rotation = Querschnittsauswahl (gemessen) | ✘ |
| **Token-Unlocks** | ~90 % negativer Druck ab ~30 T vorher [I, Keyrock] | ✔ | ✘ **DefiLlama `/emissions` 402 (kostenpflichtig, heute geprüft)**; Tokenomist kostenpflichtig | R-A verworfen (Daten nicht frei); die Verwässerung steht schon als Fakt aus der Mengenänderung in den Mails (P22/P22c) | ✘ nach Projektregel |
| Lead-Lag BTC → Altcoins | Vorlauf 16–118 **Sekunden** [B] | ✔ | ✔ | für Bitpanda zu schnell | ✘ |
| Liquidations-Kaskaden | kein Vorlaufsignal über Ereignisse [B] | ✔ | Historie nicht frei | – | ✘ |

## 2. Was daraus folgt

- **Elliott-Wellen und Chart-plus-Makro tragen nach der Literatur nicht.** Sie wären bei uns auch nicht neu: Objektiv kodiert sind sie Kurs- bzw. Regimemerkmale, und die sind gemessen.
- **Neu und frei prüfbar sind zwei Dinge:**
  1. die **Größe nach Schwankung** (V-1). Sie ist eine Bremse und kein Signal, schließt aber eine echte Lücke im Betrieb;
  2. **ETF-Flüsse mit Verzögerung** für BTC/ETH. Das ist der einzige neue Kandidat mit Vorhersage-Anspruch; belegt ist er nur vorläufig [I].
- **DVOL** gehört höchstens als Variante in V-1 (implizite statt historischer Schwankung, nur BTC/ETH).

## 3. Vorschlag zur ETF-Fluss-Frage (zur Abstimmung)

- **Stufe 0 Machbarkeit wie p91**, ohne Ergebnis:
  - Farside-Tabelle einmal laden (Download mit deinem Ja, eine Webseite, < 1 MB).
  - Zustand = Nettofluss der Vortage (Summe 1/3/5 T, am Tag t erst nach US-Börsenschluss bekannt, deshalb Wirkung ab t+1).
  - Zählen: Zahl der Wechsel zwischen Zufluss- und Abflussstrecken.
  - Selbsttest: Fehlalarm und Auflösung für Ertrag 1/7 T BTC, auf einer Strecken-Nullwelt.
- **Ehrliche Erwartung:** Flüsse sind träge und laufen dem Kurs **nach**. Wahrscheinlich ist es wieder eine Regimefrage mit wenigen Strecken; dann ist sie nicht entscheidbar wie L2-a.

## 4. Quellen (Auswahl, von der Recherche geliefert; † selbst nachgelesen)

- † Hudson/Urquhart, *Technical trading and cryptocurrencies*, Annals of OR: https://hull-repository.worktribe.com/OutputFile/2639834 · https://link.springer.com/article/10.1007/s10479-019-03357-1
- Fibonacci automatisch (ESWA 2021), Retracement-Verteilung arXiv 1605.03559: https://arxiv.org/pdf/1605.03559
- Liu/Tsyvinski, Risks and Returns of Cryptocurrency (RFS 2021): https://papers.ssrn.com/abstract=3226806
- Shen/Urquhart/Wang, Bitcoin intraday time-series momentum: https://research.birmingham.ac.uk/en/publications/bitcoin-intraday-time-series-momentum/
- Baur u. a., Time-of-day/day-of-week effects: https://research-repository.uwa.edu.au/en/publications/bitcoin-time-of-day-day-of-week-and-month-of-year-effects-in-retu/
- FalconX ETF-Flüsse (vorläufig): https://falconx.io/newsroom/what-can-spot-etf-flows-tell-us-about-the-trajectory-of-bitcoin-prices-a-preliminary-statistical-investigation
- † Deribit DVOL API: https://docs.deribit.com/api-reference/market-data/public-get_volatility_index_data
- Keyrock Token-Unlocks [I]: https://keyrock.com/from-locked-to-liquidity-what-16000-token-unlocks-teach-us/
- Halving FDR arXiv 2607.26188: https://arxiv.org/pdf/2607.26188
- Liquidationskaskaden arXiv 2607.27070: https://ideas.repec.org/p/arx/papers/2607.27070.html
