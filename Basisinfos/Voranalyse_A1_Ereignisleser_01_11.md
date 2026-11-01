# Voranalyse A1 — der Ereignis-Leser (G9, Fütterung §3 und §6 Schritt 4, 01.11.2026)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte.

**Auftrag (Nutzer 01.11.):** *„ja, starte mit der Voranalyse A1 – prüfen, gegenprüfen und doku“*.
**Gehört zu:** [`Voranalyse_Dashboard_LLM_28_10.md`](Voranalyse_Dashboard_LLM_28_10.md) (A1 §140: *„Welches Ereignis meldet diese
Nachricht … zu welchem Asset, welcher Typ, welche Schwere?“*, Prüfung gegen ~200 handgeprüfte Meldungen, V4) ·
[`Fuetterung_Satzform_31_10.md`](Fuetterung_Satzform_31_10.md) §3 (Ereignisse kommen **nur** über A1, Zeilenform) ·
[`Voranalyse_Zustaende_Modul_01_11.md`](Voranalyse_Zustaende_Modul_01_11.md) (Ebene 1, S8 im Takt offen).
**Stand:** Vorlage zur Abstimmung. **Nichts gebaut, nichts geladen, Betrieb unberührt.** Gemessen nur lesend auf den drei Archiven;
dazu **ein Probelauf** gpt-oss-120b (Groq) auf 2 × 2 × 25 öffentlichen Nachrichtentiteln. Skripte und Ausgaben: `Rechenkern_02_10/a1_voranalyse_regeln.py` → `.txt`, `a1_voranalyse_llm_probe.py` → `…_standard.csv`, `…_low.csv` (Variante mit `reasoning_effort: low`).

---

## 0. Worum es geht

A1 macht aus **Meldungen** (Börsen-Ankündigungen, Nachrichten) **Ereignisse**: Zeit · Asset oder Bereich · Typ · Schwere · Beleg —
als **Fakt**, nie als Urteil (Ü2). Die Sichten bekommen nie Rohmeldungen (Fütterung §3). A1 ist laut Dashboard-Voranalyse der
**einzige Weg zu neuer Information**: Ausnahmen erkennen, bevor sie eine Position treffen (A2 baut darauf).

---

## 1. Quellen und Abdeckung

| Quelle | Bestand (Desktop) | Rückspiel 01.12.2025 – 16.10.2026 | live am NB |
|---|---|---|---|
| **Binance-Ankündigungen** | `data/_a1/binance_ankuendigungen_alle.db`: **6.276** Meldungen 01/2023 – 28.10.2026, sechs Kataloge (48 Listing, 49 News, 93 Aktionen, 128 Airdrops, 157 Netz/Wallet, 161 Delisting); Text bei 4.097 (Katalog 93 nur Titel) | vollständig | ✔ `binance_ankuendigungen` — aber **nur Kataloge 161 und 49** (`KATALOGE`) |
| **Upbit-Ankündigungen** | `data/_c2/ankuendigungen.db`: **785** Meldungen 2017 – 08.10.2026, nur Titel | vollständig | ✔ `spot_upbit` |
| **Nachrichten** (9 Feeds) | `data/_lc/nachrichten.db` (Wayback): **39.929**, im Wesentlichen ab 01/2025 | **25.193**, Median **67 je Tag**; an **14 von 320** Tagen keine einzige Meldung (Archivlücken) | ✘ **kein Job am NB** (`sichten_quellen.feeds_laufend` nur Desktop) |

---

## 2. Befunde — geprüft und gegengeprüft

| # | Befund | gemessen | Folge |
|---|---|---|---|
| **A1-1** | **Regeln tragen bei den Börsen.** Ein Entwurf mit 17 Typ-Mustern ordnet Binance-Titel zu **82 %** (5.168 von 6.276), Upbit zu **83 %** (649 von 785) | Rest Binance 1.108 (davon erkennbare Muster: *„Removal of Margin Trading Pairs“*, *„Completes Integration … Opens Deposits“*), Upbit 136 (*„상장“*, *„거래 지원 종료“* mit Leerzeichen, *„유의 종목 해제“*) | Börsen **regelbasiert**, Regeln beim Bau nachschärfen; LLM nur für den Rest |
| **A1-2** | ✔ **Gleichheit mit dem Betrieb.** Für die drei Arten, die in die REGEL0-Mail gehen, findet der Entwurf **dieselben** Meldungen wie `binance_ankuendigungen.art` | Futures-Delisting **59/59**, Monitoring **19/19**, Token-Delisting **32/32** — dazu **2** echte, die die Betriebsregel nicht kennt (*„Will Delist Non-MiCA Compliant Stablecoin …“*, *„Will Delist UTK and Support Rebranding …“*) | A1 ist für diese Arten eine **Obermenge** des Betriebs; Prüfpaket hält die Gleichheit fest |
| **A1-3** | ⚠ **Die Betriebsregel `art()` etikettiert falsch** — ohne Wirkung auf die Mail | **550** Futures-Neuzulassungen (*„USDⓈ-Margined“*, Katalog 48) und 45 Aktionen (93) gelten als `margin`; **27** Paar-Entfernungen 01–10/2023 (alter Titel *„Notice of Removal of Trading Pairs“* ohne „Spot“) als `sonstiges` — **auch in der E-1-Ablage** (dort 221 Entfernungen, 78 ohne „Spot“) | `margin` und `paar_entfernt` gehen nicht in die Mail (`ARTEN_MAIL`) → Betrieb unberührt. **Vermerk zu E-1:** *paar_entfernt ohne Effekt* stand auf einer Menge ohne diese 27 — kein Widerruf (R-R11), aber Geltungsbereich |
| **A1-4** | **Nachrichten nennen selten ein Watchlist-Asset** | im Titel: mit BTC/ETH/SOL 13,5 %, **ohne Kern höchstens 4,8 %** (überzählt: das Kürzel **„S“** trifft jeden Buchstaben); **17** Watchlist-Coins kommen in **keinem** Titel vor (u. a. AKT, IMX, RENDER, SEI, VIRTUAL) | Ereignisse **je Asset** kommen vor allem von den **Börsen**; Nachrichten tragen die **Lage** (Regulierung, ETF, Makro → S1–S3, S7-Bereich). Asset-Zuordnung braucht eine **Alias-Tabelle** für mehrdeutige Kürzel (S, CAT …) |
| **A1-5** | **`bekannt_ab` der Nachrichten** — das Archiv ist später als die Veröffentlichung | Wayback-Aufnahme nach Veröffentlichung, Median **5–11 h** je Feed; einzelne negative Abstände (Veröffentlichungszeit **nach** der Aufnahme) | Regel: `bekannt_ab` = **min(Aufnahme, Veröffentlichung + 1 h)** — live würden die Feeds stündlich gelesen (Ü8); nie früher als belegt |
| **A1-6** | **LLM-Probelauf** gpt-oss-120b, 2 × 25 Titel je Lauf | Form **50/50** gültig (JSON je Meldung). Token je Titel: **≈ 137** (Standard-Denkstufe, davon ~70 % Nachdenken), **≈ 93** mit `reasoning_effort: low`. **Aber:** zwischen beiden Läufen gleicher Typ nur **35/50**, gleiches *Ereignis ja/nein* 43/50. Sichtbare Fehler: Stablecoin-Start als *token_freigabe*, Grayscale-S-1 als *listing* | die Typen brauchen **Definitionen** im Prompt; **ob** das LLM trägt, entscheidet erst die handgeprüfte Stichprobe (§5) — nicht dieser Probelauf |
| **A1-7** | **Budget** (Groq frei: ~200.000 Token/Tag) | alle 25.193 Nachrichten: **2,3–3,5 Mio. Token = 12–17 Tage** Kontingent. **Vorfilter** auf Risiko-Stichwörter (hack, exploit, depeg, delist, halt, lawsuit, SEC, unlock …): **3.721 Titel (14,8 %) ≈ 0,35 Mio. Token ≈ 2 Tage** | Frage §6. Die **Vollständigkeit** (Recall) des Vorfilters ist **nicht** gemessen — sie kommt aus der Stichprobe |
| **A1-8** | **Schwere ist kein Urteil** | E-1: Token-/Futures-Delisting, Monitoring *„24 h −1,0 bis −1,5 %, nach der Vorabregel nicht getragen“*; C2: Upbit-KRW-Listing *„7 T −10 Pp gegen BTC“* | `schwere` = **die gemessene Wirkung aus dem Register mit Befundnummer**, sonst *„ungemessen“*. So bleibt es ein Fakt (Regel 4) |
| **A1-9** | **Kontamination** | gpt-oss-120b, Wissensstand vor 2025 (Memory: *LLM-Kontamination*) | Einordnen ist keine Prognose; für 2025/26 kennt das Modell den Ausgang nicht ✔ |
| **A1-10** | **Live am NB fehlt** | Nachrichten: kein Job; Binance nur 161/49 | gehört zu **G8** (ein Bündel), nicht hierher |

---

## 3. Was A1 liefert

**Typkatalog** (mit Definition im Prompt, A1-6): Delisting (Token / Futures / Margin / Paar) · Monitoring an/aus · Listing (Spot /
Futures / Alpha) · Verschoben · Depeg/Aussetzung · Hack/Exploit · Regulierung/Klage · ETF/Fonds · Makro/Zentralbank ·
Unternehmen (Kauf, Insolvenz) · Netz-Upgrade/Migration · Token-Freigabe (**nur** Unlock/Vesting) · Airdrop · Aktion/Werbung ·
Produkt · Marktbericht/Meinung (*kein Ereignis*).

**Zeile** (Fütterung §3): `Zeit (UTC) · Asset oder Bereich · Typ · Schwere (gemessen/ungemessen, mit Befund) · neu seit · Beleg
(Quelle, Link) · Ereignis`. Aktion, Produkt, Marktbericht und Meinung werden **abgelegt, aber nicht** an die Sichten gegeben.

**Sicht-Zuordnung:** Asset-Ereignisse → S7 (je Asset) · Depeg, Börse, Krypto-Regulierung → S1 · Makro/Zentralbank → S2 ·
Aktien/Kredit → S3 · Asien → S5 (später). Ein Ereignis löst das Neugutachten seiner Sicht aus (Takt §5) — damit ist auch **S8**
geklärt: ein Termin wird zum Ereignis, wenn er **stattfindet**.

---

## 4. Bauplan (nach Ja)

| Teil | was |
|---|---|
| `agent/ereignisse.py` | **ein** Rechenweg live und Rückspiel (Ü8): Regeltabelle je Quelle (Binance, Upbit) · LLM-Teil für Nachrichten in Stapeln zu 25, `temperature 0`, Typ-Definitionen im Prompt · Asset-Zuordnung gegen die Watchlist mit **Alias-Tabelle** · `schwere` aus dem Register · `bekannt_ab` nach A1-5 |
| Ablage | `sichten.db`, Tabelle `ereignis` (quelle, meldung, zeit, bekannt_ab, typ, assets, bereich, sicht, schwere, beleg, methode *regel/llm*, modell) — nie die Produktion |
| `agent/zustaende.py` | liest die Ereignisse am Stichtag (`bekannt_ab ≤ T`) und hängt sie an die Sicht |
| nicht | Betrieb, NB, Mail — `binance_ankuendigungen.art` bleibt, wie sie ist (E-1-Gleichheit) |

---

## 5. Prüfen und gegenprüfen

| # | Prüfung |
|---|---|
| **P1** | **Handgeprüfte Stichprobe, 200 Meldungen, geschichtet**: Binance-Regel 50 · Binance-Rest 30 · Upbit 30 · Nachrichten 90 (davon 45 Vorfilter-Treffer, 45 Nicht-Treffer). **Ich bereite vor** (Meldung, Vorschlag Typ/Asset/Ereignis ja/nein), **du prüfst stichprobenartig gegen** (V4) |
| **P2** | daran gemessen, mit Band (Wilson 95 %): Typ richtig · *Ereignis ja/nein* richtig · Asset richtig — **je Quelle und Methode** getrennt; für den Vorfilter die **Vollständigkeit** (wie viele echte Ereignisse fallen durch) |
| **P3** | Regeln = Betrieb an den drei Mail-Arten (59/19/32, A1-2) — als Prüfpaket |
| **P4** | LLM-Stabilität: derselbe Stapel zweimal → gleiche Antwort (Temperatur 0); Abweichungen ausgewiesen |
| **P5** | kein Vorgriff: ein Ereignis erscheint am Stichtag erst ab `bekannt_ab`; Nachweis wie N3 bei den Zuständen (gekürzte Ablage) |
| **P6** | Prüfpaket `Ereignisse` (ohne Netz): Regeln je Typ an Mustertiteln, Alias-Kürzel, Schwere nur aus dem Register, nie Produktion |

---

## 6. Zur Abstimmung — eine Frage

**Wie viele Nachrichten liest das LLM im Rückspiel?** (A1-7)

| | Weg | Folge |
|---|---|---|
| **a** | **Vorfilter + LLM nur auf Treffer** (14,8 %, ≈ 2 Tage Kontingent). Die Stichprobe misst, wie viele echte Ereignisse der Vorfilter verliert; **ist das mehr als die Stichprobe als vernachlässigbar ausweist, geht es auf b** | schnell, prüfbar; Risiko-Ereignisse (das Ziel von A1/A2) liegen genau im Filter |
| b | **alle Nachrichten per LLM** (`low`, ≈ 12 Tage Kontingent) | vollständig, aber fast zwei Wochen Laufzeit, bevor G7 messen kann |
| c | **Nachrichten nicht in A1** — nur Börsen-Ankündigungen; Nachrichtenlage nur als GDELT-Ton | sofort; aber Regulierung, ETF, Hacks außerhalb der Börsen fehlen |

**Empfehlung a** — mit der Regel, dass die Messung (nicht eine Wahl) über den Wechsel auf b entscheidet. A1-1 bis A1-10, der
Typkatalog, die Zeilenform und P1–P6 sind fachlich begründet und hier nicht zur Wahl gestellt — Einwände willkommen.
