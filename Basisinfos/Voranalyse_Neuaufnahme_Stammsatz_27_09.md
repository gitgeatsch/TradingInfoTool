# Voranalyse: Neuaufnahme eines Assets über alle Datenquellen — der Stammsatz

**27.09.2026** · Fortsetzung von `Voranalyse_Stammsatz_26_09.md` (Entwurf
`asset_stamm`, Befunde 2.612 bis 2.615) · **nichts gebaut, zur Abstimmung**

> **Nutzervorgabe:** *„wenn ich ein neues Asset aus BP aufnehme, muss das über
> alle Datenquellen korrekt umgesetzt werden, und hier haben wir das Symbol-
> und ID-Problem … Das ist auch ein Grund, warum einige Symbole aktuell nicht
> gefunden werden — auch Canton sollte eigentlich gefunden werden.“*

---

## 1 · Was heute neu belegt ist (27.09., an der Quelle geprüft)

| Fund | Beleg |
|---|---|
| **Canton wird gefunden — unter `CC`**, nicht unter „CANTON“ | Binance-Terminmarkt `CCUSDT`, Bybit `CCUSDT`, OKX `CC-USDT-SWAP`; unter CANTON nirgends etwas. Der Bitpanda-Katalog führt es seit jeher als `CC` (2.615), `BITPANDA_SYMBOL_OVERRIDES` seit 09.07. |
| **Faktor im Terminmarkt-Namen**: 15 Binance-Terminmärkte tragen `1000`, `1000000` oder `1M` | `1000FLOKI`, `1000CAT`, `1000PEPE`, `1000BONK`, `1000SHIB`, `1MBABYDOGE`, `1000000MOG` … — der Kurs ist das 1.000- bzw. 1.000.000-fache |
| **Unsere eigenen Tabellen widersprechen sich** | Hebelliste `CAT`, Stundenkurse `1000CAT`; `FLOKI` fehlt in Stundenkursen **und** Terminmarkt-Historie, obwohl Binance Spot und Terminmarkt es führen |
| **Die Lücke liegt bei den Ladern, nicht bei den Quellen** | Abdeckungsmatrix 27.09.: Stundenkurse 29 von 43 Hebelsymbolen, aber Binance-Terminmarkt live 38 von 43, irgendein Terminmarkt 39 von 43; gar nichts bei 3 (CANTON, SUPRA, VSN) — CANTON davon nur scheinbar, weil unter `CC` gesucht werden muss; XNO nur Spot |
| **Mehrdeutigkeit ist real** (2.615) | 1.625 von 12.402 Katalog-Symbolen mehrfach; 11 der 48 gehaltenen/Hebel-Assets mehrdeutig (ETH, LINK, SEI, SUI …) — ein Ticker allein beweist nichts |

## 2 · Was der Entwurf vom 26.09. schon richtig macht

- **`asset_id` aus `bitpanda_katalog` als Schlüssel** — stabil, eindeutig, am Notebook vorhanden (14.054 Einträge).
- **Nur Belegtes übernehmen, Lücken bleiben `NULL`** — kein Raten.
- **Binance-Paare gegen beide `exchangeInfo` auflösen** (Spot und Terminmarkt).
- **Suite-Prüfung: jedes gehaltene Asset hat einen vollständigen Stammsatz.**
- **Lader erst danach umstellen** — sonst ändert sich still die Grundgesamtheit (2.487).

## 3 · Was ergänzt werden muss

| # | Ergänzung | warum |
|---|---|---|
| **S1** | **Kürzel und Faktor je Quelle**: `binance_futures` = `1000CATUSDT` **und** `faktor_futures` = 1000; ebenso Bybit, OKX | ohne Faktor ist jeder Kurs- oder Volumenvergleich um das 1.000-fache falsch |
| **S2** | **Zuordnung per KURSABGLEICH bestätigen**, nicht per Namensgleichheit: ein Kandidat gilt erst, wenn sein Kurs (durch den Faktor geteilt) dem Bitpanda-Kurs über die letzten Tage folgt (Median-Abweichung unter einer Schwelle, z. B. 2 Prozent) | das einzige Kriterium, das Mehrdeutigkeit (ETH = Ethereum oder *Eurotech*) und falsche Treffer sicher erkennt — ein Fakt, keine Namensregel |
| **S3** | **Bybit und OKX** als eigene Spalten (Terminmarkt), nicht nur Binance | 39 statt 38 von 43; Rückfall, wenn Binance ein Asset nicht führt |
| **S4** | **Eine Neuaufnahme ist ein Ablauf, kein Eintrag**: Katalog → Kandidaten je Quelle → Kursabgleich → Stammsatz schreiben → Prüfung „vollständig und bestätigt“ → erst dann Watchlist | heute wird ein Asset über den Ticker aufgenommen und fällt dort, wo er nicht passt, still heraus |
| **S5** | **Lader lesen den Stammsatz** (Stundenkurse, Terminmarkt, Funding, Richtungsdaten, Betrieb) — **eine** Zuordnung für Messung und Betrieb | heute leitet jeder Lader seine Liste anders ab (aus dem Terminmarkt, aus Spot-Paaren, aus Tickern) |
| **S6** | **Handübersteuerung mit Begründung** (`asset_stamm_override`: Quelle, Kürzel, Faktor, Grund, Datum) | für Fälle, die der Kursabgleich nicht entscheiden kann — sichtbar, nie still |

## 4 · Ablauf einer Neuaufnahme — der Vorschlag

```
Nutzer nimmt Asset in Bitpanda auf
   │
   ├─ 1  asset_id, Name, Gruppe, ISIN aus bitpanda_katalog (nie der Ticker allein)
   ├─ 2  Kandidaten je Quelle: Binance Spot, Binance Terminmarkt (auch 1000…/1M…),
   │     Bybit, OKX, CoinGecko (Symbol UND Name)
   ├─ 3  Kursabgleich je Kandidat gegen den Bitpanda-Kurs (Faktor beachtet)
   ├─ 4  Stammsatz schreiben — bestätigt / unbestätigt / keine Quelle
   ├─ 5  Prüfung: vollständig und bestätigt? sonst Meldung mit Grund
   └─ 6  erst dann: Watchlist, Hebelliste, Lader
```

## 5 · Risiken

| Risiko | Gegenmaßnahme |
|---|---|
| **Grundgesamtheit ändert sich**, wenn die Lader umgestellt werden — Messung und Betrieb laufen auseinander (2.487) | Umstellung von Messbasis **und** Betrieb im selben Schritt; vorher `messe_grundgesamtheit.py` |
| **Katalog nur am Notebook** (2.615) | für den Desktop aus der Produktionssicherung lesen (nur lesend) — keine zweite Pflege |
| **Kursabgleich braucht einen Bitpanda-Kurs** | den gibt es für gehaltene und gelistete Assets im Betrieb; für die Messbasis reicht der Abgleich zwischen den Börsen untereinander |
| Faktor falsch → Werte 1.000-fach daneben | Faktor nur aus dem Kürzel ableiten **und** per Kursabgleich bestätigen |

## 6 · Einplanung — wo es hingehört

| | |
|---|---|
| **Abhängigkeit** | Die **Hebel-Datenbasis** (Binance-Terminmarkt für 88 bis 91 Prozent der Hebelsymbole) braucht diese Zuordnung — ohne sie findet sie FLOKI, CANTON und die 1000er nicht |
| **Nicht abhängig** | Die laufende **Richtungsmessung** (116 Symbole der Stundenkurse) — sie braucht den Stammsatz nicht |
| **Reihenfolge, Vorschlag** | 1. Richtungsmessung abschließen · 2. **Stammsatz** (S1 bis S6) · 3. Hebel-Datenbasis auf den Stammsatz · 4. Betrieb |
| **Im Gesamtplan** | als eigener Schritt, sobald der Gesamtplan nachgezogen wird (Nutzer: erst, wenn das System verstanden ist) |
| ⛔ **Betriebsumstellung — Bedingung (Nutzer 27.09.)** | *„erst dann, wenn alles sauber gemessen, Datenquellen und Basis für die Produktion steht … es muss die ganze Ablaufkette geprüft und angepasst werden inkl. LLMs und Rollen (siehe Hauptplan).“* ➤ Schritt 4 oben ist also **kein** Ladertausch, sondern die Phasen 2 bis 4 des Hebel-Plans: Prüfung an Echtdaten, Ablaufkette samt LLM-Rollen, dann Produktion |

## 7 · Entscheidungen für den Nutzer

✔ **ENTSCHIEDEN 27.09.2026: N1 bis N3 wie empfohlen** (Nutzer: *„ja, N1 bis
N3 wie empfohlen“*). Stammsatz **nach** der Richtungsmessung, Zuordnung **per
Kursabgleich**, Ablage **in der Produktionsdatenbank am Notebook**.

| # | Frage | Empfehlung |
|---|---|---|
| **N1** | Stammsatz vor oder nach der Richtungsmessung bauen? | **danach** — die Messung braucht ihn nicht; trägt die Richtung nicht, ändert sich der Umfang der Hebel-Datenbasis |
| **N2** | Zuordnung per Kursabgleich bestätigen (S2)? | **ja** — das einzige Kriterium, das Mehrdeutigkeit sicher erkennt |
| **N3** | Wo liegt der Stammsatz? | **in der Produktionsdatenbank am Notebook** (dort liegt der Katalog); der Desktop liest ihn aus der Sicherung |

## Was NICHT folgt

- **Nichts gebaut.** Keine Änderung an Ladern oder Betrieb.
- CANTON ist damit **auffindbar**, aber noch **nicht** in der Messbasis: bei Binance nur am Terminmarkt und erst seit Mitte 2026 (2.613) — für eine Messung zu kurz, für den Betrieb brauchbar.
