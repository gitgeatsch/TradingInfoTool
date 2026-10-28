# Voranalyse Dashboard mit Fakten und LLM-Bewertung — Bestandsaufnahme und Expertenkonzept (28.10.2026)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte.

**Auftrag (Nutzer 28.10.):**
- *„das Dashboard mit Fakten und LLM Bewertungen brauchen wir ohnehin … mir fehlt die Intelligenz in der Bewertung, mit statischen mathematischen Berechnungen kommen wir nicht weiter.“*
- *„bereite alles für die Bestandsaufnahme vor und wie wir die LLM mit unseren Mitteln optimal nutzen können, du in der Rolle des Experten“*

**Stellung im Plan:** Das ist Konzept `Konzept_Lagegerechte_Handlung_27_10.md` §7 (Dashboard) und F3. Das Ergebnis H-1 (E-165-h1b/-h1c, *trägt nicht*) steht im Register. **Betrieb unverändert.** Dieses Blatt ist eine Voranalyse; gebaut wird erst nach der Abstimmung (§8).

Kennzeichnung der externen Angaben: **[B]** belegt auf der Primärquelle, **[S]** nur Sekundärquellen, **[U]** unsicher. Die Recherche lief am 28.10.; vor einem Bau wird jede verwendete Quelle **am NB** nachgewiesen (Regel *Datenquellen-Inventar + Abdeckung je Bedarf*).

---

## 1. Bestandsaufnahme — was das System heute hat

### 1.1 Statusseite (NB, `remote/server.py`)

- **Technik:** Flask, Port 8765, über Tailscale, Token-Pflicht (server.py:1265–1275). Gestartet als Thread aus main.py (:404–418), nur wenn `REMOTE_ACCESS_TOKEN` gesetzt ist.
- **Daten:** `/api/status` aus `remote/status.py::build_status`. Teure Teile werden 900 s zwischengespeichert, die Seite fragt alle 5 s ab.
- **Blöcke heute:**
  - Makro-Umfeld (K1–K9, „Fakt, kein Signal“), Gesamtmarkt (Lagebild L1–L7), Krypto-Markt (Season-Ampel, Einstiegskandidaten)
  - System, Notbremse und Kontrollen, Hebel/REGEL0, Betrieb/Jobs, Schalter/Bestand
  - Kontingente, API-Status, Parameter, Multi-Asset (ruht), letzte Fehler
- ⇒ **Der Rahmen für das Dashboard steht.** Es fehlt die **Asset-Sicht**: je Asset und Bestand ein Prüffall mit Schichten, Ereignissen und Einordnung (Konzept §7).

### 1.2 LLM im Betrieb

| Rolle | Stand | Was sie bekommt / tut | Modell, Budget |
|---|---|---|---|
| REGEL0 **Trader** | **an**, im Mailblock markiert „trennt nicht“ | Kerzen und Lage zur Signalstunde, anonym → *stützt / neutral / spricht dagegen* | gemini-3.5-flash-lite, 5 Stimmen, Temperatur 0; 150 Aufrufe/Tag (regel0_llm.yaml) |
| REGEL0 **Markt** | an, nur Auskunft | Umfeld aus Leitmärkten, Makro und Stimmung | wie oben |
| REGEL0 **Entscheider** | aus (E-82) | – | – |
| Alte Kette (Rolle A, BC, Gate, Z1, Z.ai) | **stillgelegt** (`ALTE_KETTE_STILLGELEGT`, E-164) | – | Topfkette Gemini → OpenRouter :free → Groq |
| Szenario-Module, Kategorie-Synthese, Kanarienvogel, `local_model` | nicht verdrahtet bzw. pausiert | – | – |

**Schlüssel am Desktop** (nur gesetzt ja/nein): Gemini (2 Schlüssel), Groq, OpenRouter, Z.ai, Mistral (seit 07.08. Fehler 402), Anthropic, Cerebras, xAI. Ob die NB-`.env` gleich ist, ist **offen**.

### 1.3 Fakten, die nicht aus Kursen stammen

| Quelle | Inhalt | Historie | Zeitpunkt des Bekanntwerdens (PIT)? |
|---|---|---|---|
| `binance_ankuendigungen.py` | Delisting, Monitoring-Kennzeichen | nur am NB, Umfang offen | **ja** (`release_ms`) |
| `spot_upbit.py` | Upbit-KRW-Listings | nur am NB | **ja** |
| `termin_fakt.py` | FOMC, CPI, NFP | live | entfällt |
| `makro_lage.py` | K1–K9, F&G, DVOL | **keine**: `makro_lage.json` wird bei jedem Lauf überschrieben | nein |
| `verwaesserung.py` / Umlaufmenge | Umlaufmenge heute gegen vor 90 Tagen | 2025-09-21 bis 2026-09 | Stichtag ja, die Menge selbst nachgeladen |
| On-Chain, TVL, Funding, OI, Terminmarkt | Reihen | 2013 bzw. 2018 bzw. 2019 bis 2026 | **nein** (nachgeladen, Revisionen gewinnen) |
| **Nachrichtenarchiv** `data/_lc/nachrichten.db` | **39.929 Meldungen aus 9 RSS-Feeds** über das Wayback-Archiv (Schritt7 §23.72) | Cointelegraph ab 2019, die übrigen ab 12/2024 bzw. 2025, bis 17.10.2026 | **ja**: Veröffentlichungszeit und Aufnahmezeit im Archiv |

⚠️ Das Dashboard soll jede Einschätzung und jeden Fakt mit Zeitstempel **protokollieren**. Heute fehlt das für Makro und externe Reihen, und ohne Protokoll ist später nichts nachprüfbar.

### 1.4 Externe kostenfreie Ereignisquellen (Recherche 28.10.)

| Quelle | frei? | Historie | PIT | Tauglich für |
|---|---|---|---|---|
| **Binance-Ankündigungen** (Webseiten-Endpunkt, inoffiziell) | ja [S] | Jahre zurück [S] | ja, Millisekunden [B] | Listing, Delisting, Monitoring für alle Binance-Werte |
| **Wayback-CDX auf RSS** | ja [B] | 2025–26 schon geladen | Obergrenze „war bekannt“ | Nachrichten der großen Medien (haben wir) |
| **GDELT GKG-Rohdateien** | ja [S] | 2015 [S] | 15-Minuten-Pakete [U] | Breite Nachrichtenlage, Ton; kleine Werte dünn. Laden nur mit Ja (Download) |
| GDELT DOC-API | ja [B] | **nur 3 Monate** Artikellisten [B] | ja | nur live |
| **GitHub Releases/Commits** | ja [U] | ganze Repo-Historie | ja | Entwicklungsereignisse; Zuordnung Coin → Repo selbst pflegen |
| **Reddit über Arctic Shift** | ja [S] | 2005 [S] | ja | Gemeinschaftsstimmung je Coin; keine Verfügbarkeitszusage |
| SEC EDGAR | ja [S] | 2001 | Annahmezeit [U] | ETF-Anträge, Klagen (nur US) |
| CryptoPanic | **nein**, Free-Plan seit 04/2026 weg [S] | – | – | scheidet aus |
| CoinGecko /news | **nur bezahlt** seit 03/2026 [B] | – | – | scheidet aus |
| DefiLlama Hacks/Raises/Unlocks, Tokenomist | **nur Pro** [B] | – | – | scheidet aus (Unlocks ggf. über die Git-Historie der offenen Adapter [U]) |
| Google Trends | keine freie API [B] | – | nicht PIT | scheidet aus |
| Farside ETF | Web frei, keine API | ab 01/2024 | nicht PIT | gemessen: nicht auflösbar (E-158-etf) |

### 1.5 Kostenfreie LLM-Zugänge (Recherche 28.10.)

| Weg | Modell | freies Limit | Wissensstand | für |
|---|---|---|---|---|
| **Groq** | gpt-oss-120b, gpt-oss-20b, llama-3.3-70b | 1.000 Anfragen und 200.000 Token je Tag [B] | gpt-oss 06/2024 [B] (gemessen eher 09/2023 [S]); Llama 12/2023 [B] | **Rückspiel 2025–26** (sauber) |
| **Cloudflare Workers AI** | gpt-oss-120b, llama-3.3-70b | 10.000 Neurons/Tag [B], nach eigener Rechnung ~200.000 Token Eingabe [U] | wie oben | zweiter sauberer Weg |
| **Gemini API** | Flash-Lite / Flash (im Betrieb 3.x) | ~500 je Modell/Tag (Projektzähler, geteilt mit NB) | 2025 bekannt → **kontaminiert** für 2025 | **Live-Aufgaben** (kein Rückspiel) |
| Ollama lokal | gpt-oss-20b (~16 GB RAM), Llama 8B | unbegrenzt | 2023/24 | nur, wenn die NB-Hardware reicht (**offen**) |
| OpenRouter :free | wechselnd | 50/Tag [B] | je Modell | Reserve |
| Cerebras, Mistral, GitHub Models | – | Cerebras: nur Testguthaben mit Zahlungsmittel [B]; Mistral: 402; GitHub Models: eingestellt 30.07.2026 [B] | – | **scheiden aus** |

#### 1.5a Nachtrag 28.10. abends — was WIR je Anbieter gemessen haben (Nutzer: *„dies musst du in der Doku oder Memory erheben“*)

⚠️ Die Tabelle oben ist **Recherche**. Maßgeblich ist, was das Projekt selbst gemessen hat — Quellen: Code `api/*.py`, `Basisinfos/regel0_llm.yaml`, Schritt7 §23.73–§23.75, `p66_horizont*.txt`, Memory. **[M]** gemessen · **[F]** Fehlerkörper des Anbieters · **[D]** Dashboard des Nutzers · **[R]** Recherche.

| Anbieter | Modelle bei uns | Grenzen | Tempo | Fehlerbilder | Wissenshorizont (19.10.) | Rolle heute |
|---|---|---|---|---|---|---|
| **Gemini** | 3.5-flash-lite (Prüfblock), 3.1-flash-lite (alte Spot-Kette) | **500/Tag je Projekt UND je Modell** [F, 09.08.] — jedes Modell ein eigener Topf, der Topf hängt am **Schlüssel**. Der Desktop hat mit `GEMINI_API_KEY_2` einen **eigenen** Topf (N4, Deckel 480/Tag); nur Läufe mit Schlüssel 1 zehren am NB-Topf; ~15/min [M]; Prüfblock-Deckel 150/Tag | Median 5,5 s; Trader 5 Stimmen Ø 27 s, max 52 s [M] | 503 bei ~8 % (13.08.), 429 bei verbranntem Tagestopf | 3.5 kennt Kurse bis **~Okt. 2025** → kontaminiert für 2025 [M] | **Betrieb** (Prüfblock „trennt nicht“) |
| **Groq** | gpt-oss-120b, qwen3.8-27b (Messung); `llama-3.3-70b` im Code | **200.000 Token/Tag** [M, 19.10. bei 199.847 erreicht]; danach ~1 Abfrage je 10–11 min | L-C2: 497 Abfragen in ~2 Tagen, **0 Ausfälle** [M] | 413 (26.07., alte Nutzlast); `llama-3.3-70b` lieferte 19.10. keine Antwort und fehlt in der Modellliste — **`api/groq.DEFAULT_MODEL` ist veraltet** | gpt-oss-120b **sauber** (~Mitte 2024); qwen3.8 kontaminiert (~Aug. 2025) [M] | **Messarm** für saubere Rückspiele |
| **OpenRouter :free** | nemotron-3-super-120b, gpt-oss-20b, gemma-4-31b | **1.000/Tag** (10 $ Einmalkauf 08.08. hebt 50 → 1.000; die „50“ oben gilt ohne Kauf), 20/min [R] | nemotron 21–48 s, gpt-oss-20b 125 s [M] | 429 bei gemma, 404 bei entfernten Modellen | nicht gemessen | Reserve |
| **Mistral** | mistral-small-2506 (Code), ministral-8b-2512 (Messung) | — | — | **402 seit 07.08.**; am 19.10. antwortete aber ministral-8b — ob 402 für alle Modelle gilt, ist **ungeklärt** | ministral-8b sauber, aber schwach [M] | ausgeschieden (Rest ungeklärt) |
| **Z.ai** | glm-4.5-flash | Gleichzeitigkeit 2; >8K Kontext auf 1 % gedrosselt [D] | ~105–110 s, ~35 Token/s [M] | Zeitüberschreitungen, 429 am NB (28.07.) | nicht gemessen | stillgelegt (alte Kette) |
| **Cerebras** | — | — | — | 402, nicht kostenfrei (19.10.) | — | ausgeschieden |
| **Cloudflare** | — | 10.000 Neurons/Tag [R] | — | — | — | **nie angebunden, kein Schlüssel** |
| **Lokal (Ollama)** | Platzhalter `api/local_model.py` | — | — | — | — | **scheidet aus**: NB = i5-4300U (2 Kerne), **8 GB RAM** (`project_dev_setup`), gpt-oss-20b braucht ~16 GB. Damit sind **V3 erledigt** und alle Aufgaben auf den freien Diensten |

**Schlüssel am NB** (V2): Gemini ist belegt (Prüfblock-Urteile in den NB-Mails, K-LLM-1). Für Groq und OpenRouter ist es **nicht dokumentiert**. Für den Bau ist das kein Hindernis, weil A3/A4 auf Gemini laufen (§9 im Bauplan). A1 läuft als Messung am **Desktop**.

**Was daraus für die Aufgaben folgt:**
- **Live (A3, A4, A6) auf Gemini, auf einem EIGENEN Modelltopf** — nicht 3.5-flash-lite (Prüfblock). `regel0_llm.yaml` vermerkt *„3.1 ist durch die Spot-Kette ausgelastet“*; die Spot-Kette gehört zur alten Kette, die seit E-164 stillgelegt ist. Der 3.1-Topf sollte damit frei sein. Das ist **nachzuweisen** (NB-Zähler `gemini:3.1` je Tag) und nicht anzunehmen.
- **Rückspiel und Klassifikation zur Messung (A1, später A2) auf Groq gpt-oss-120b.** Der Engpass sind die **200.000 Token/Tag**, nicht die Anfragen: bei ~300 Token je Meldung sind das ~600 Meldungen/Tag. Deshalb ordnen **Regeln zuerst** ein (Binance-Titel sind formelhaft, E-1 tut das schon), und das LLM bekommt nur den Rest und die Prüfstichprobe.
- **Gemini nie für ein Rückspiel 2025**, aus demselben Grund wie bisher (Kontamination).

---

## 2. Was schon geprüft ist — die Lage ehrlich

`Bilanz_LLM_Komponente_21_10.md` fasst **elf geprüfte Wege** zusammen (N4, N5, Entscheider, A2, Binance-Ereignisse, Nachrichten L-C/L-C2 …). Der gemeinsame Befund:

> **Information ist der Engpass, nicht das Modell.** Über dieselben Zahlen wie die Regel kann ein LLM die Regel nicht schlagen, und Nachrichten erreichen die kleinen Werte kaum.

Dazu kommen die statistischen „klugen“ Wege: Kombinationsmodelle (K1, 2.677/2.678/2.680: nicht mehr als rsi allein) und alle Einstiegsinventare (E-155: mit freien Daten erschöpft). Das „Wie“ trägt beim **Risiko** (K6), nicht beim Ertrag (H-1).

**Was das heißt — und was nicht:**
- Es heißt **nicht**, dass ein LLM wertlos ist.
- Es heißt: Gestellt war bisher **eine einzige Aufgabe**: *„sag aus Zahlen die nächsten 24 h voraus, besser als die Regel“*. Genau diese Aufgabe kann es nicht lösen.
- Die Nutzervorgabe vom 18.10. trifft den Kern: *„die LLM-Komponente sollte selbst neu dimensioniert sein oder werden, damit diese trägt“*.

---

## 3. Expertensicht — wo Intelligenz in der Bewertung herkommen kann

Ein erfahrener Trader schlägt einen Rechner nicht, weil er besser **rechnet**. Er schlägt ihn mit drei Dingen:

| | Was der Trader tut | Was unser System heute tut | Wer es können könnte |
|---|---|---|---|
| **I1** | **liest, was nicht in den Kursen steht**: Delisting, Hack, Migration, Klage, Freigabe, Partnerschaft | kennt nur Delisting/Monitoring (Binance) und Upbit-Listing | **LLM als Leser** (Text → Ereignis) |
| **I2** | **erinnert sich**, wie ähnliche Lagen ausgingen, und weiß, wann seine Erfahrung **nicht** gilt | hat ~2.700 gemessene Befunde mit Geltungsbereich, aber nur im Register | **LLM als Gedächtnis** über die eigenen Befunde |
| **I3** | **wägt im Zusammenhang** ab: was dafür spricht, was dagegen, was ihn umstimmen würde | gibt Zeilen einzeln aus | **LLM als Abwäger** mit Quelle je Satz |

Die Messung wird damit nicht überflüssig. Sie **wechselt die Rolle**: Sie prüft künftig, ob ein **Urteil** stimmt (Faktentreue, Trefferquote beim Erkennen), und erst danach, ob es Geld bringt.

> **Leitsatz:** Das LLM erzeugt Information, die Messung bestimmt ihren Wert. Was trägt, wird Bewertung; was nicht trägt, bleibt Fakt oder Einschätzung, und so steht es auch da.

---

## 4. Die sechs Aufgaben, die ein LLM mit unseren Mitteln gut kann

| # | Aufgabe | Frage an das LLM | Prüfbar wie (Stunden, nicht Jahre) | Modell | Bedarf |
|---|---|---|---|---|---|
| **A1** | **Ereignis-Leser** | *Welches Ereignis meldet diese Nachricht oder Ankündigung, zu welchem Asset, welcher Typ (Delisting, Hack, Migration, Freigabe, Klage, Listing, Partnerschaft …), welche Schwere?* | **Klassifikation** gegen eine handgeprüfte Stichprobe (~200 Meldungen): Treffsicherheit und Vollständigkeit. Das ist keine Prognose, also gibt es kein Kontaminationsproblem für die Prüfung | gpt-oss-120b (Groq) | Nachrichtenarchiv (vorhanden), Binance-Historie (laden, Ja nötig) |
| **A2** | **Risiko-Wächter** (linkes Ende) | *Gibt es für dieses Asset in den letzten 72 h ein Ereignis, das eine Position gefährdet?* | **Erkennungsquote** gegen eine Liste bekannter Ausnahmefälle 2025–26 (Delisting, Hack, Depeg) mit einem sauberen Modell; danach **Ereignisstudie** auf der Messbasis (Messnorm, Selbsttest) | gpt-oss-120b | A1 als Unterbau |
| **A3** | **Befund-Gedächtnis** | *Welche gemessenen Befunde betreffen diese Lage, mit welcher Zahl, und liegt die heutige Lage in ihrem Geltungsbereich?* | **Faktentreue maschinell**: Jede genannte Zahl und jede Befund-ID wird gegen das Register geprüft, Soll 100 %. Eine Prognose findet nicht statt | Gemini (live) | Register (`bestand.py`) ist vorhanden |
| **A4** | **Gegenanwalt** je Prüffall | *Welche Fakten sprechen gegen diese Handlung?* (Konzept §7) | Faktentreue wie A3; zusätzlich wird gezählt, wie oft er nichts findet, damit er nicht reflexhaft warnt (N5: Pessimismus 43–52 %) | Gemini | Fakt-Teil des Dashboards |
| **A5** | **Lagebild je Asset** (Abwägung) | *Fasse Fakten, Ereignisse und Befunde zu einer Einschätzung mit Gründen dafür und dagegen und „was mich umstimmen würde“ zusammen* | als **„Einschätzung, ungeprüft“** gekennzeichnet; jede wird mit Zeitstempel protokolliert. Ein Rückspiel ist erst möglich, wenn A1/A2 Ereignisse liefern, die in den Zahlen nicht stecken, dann mit gpt-oss-120b auf 2025–26 | Gemini live, gpt-oss für Rückspiel | A1–A4 |
| **A6** | **Erklärer für dich** | *Was hat sich seit gestern geändert, und was davon verlangt eine Handlung?* | Nutzen für dich, nicht Trefferquote (Regel *jede Mail eine Handlung*) | Gemini | Protokoll |

**Warum diese Reihenfolge der Erwartung:**
- **A3 und A4** sind sofort sicher nützlich. Sie bringen die Erfahrung des Systems, also die gemessenen Befunde, in die Bewertung, und ihre Prüfung ist maschinell und streng.
- **A1 und A2** sind der **einzige Weg zu neuer Information** und damit zu einem echten Vorteil. Am wahrscheinlichsten liegt er beim **Risiko**: Ausnahmen erkennen, bevor sie eine Position treffen. Das passt zu K6 („trägt beim Risiko“) und zum linken Ende aus E-1 (sichtbar, aber zu selten für die Vorab-Regel).
- **A5** ist das, was du „Intelligenz in der Bewertung“ nennst. Es ist aber nur so gut wie A1–A4 darunter. Ohne neue Information wäre es N5 noch einmal.

---

## 5. Bauprinzipien — so wird das LLM optimal genutzt

| # | Prinzip | aus welcher Lehre |
|---|---|---|
| P1 | **Eine klare Frage je Rolle**, die Wette der Handlung ist bekannt; nie *„stützt der Markt das?“* | E-82 (Echo/Mitte), N5 Ursache 1 |
| P2 | **Strukturierte Ausgabe** (JSON-Schema), jede Aussage mit **Quelle** (Fakt-ID, Befund-ID, Meldungs-Link) | Konzept §7, `llm_schema.py` als Vorlage |
| P3 | **Das LLM nennt keine eigene Wahrscheinlichkeit.** Zahlen kommen nur aus der Messung (A3) | Prüffrage *Bewertung oder Fakt?* |
| P4 | **Modell je Aufgabe:** Live-Aufgaben nehmen das stärkste freie Modell, Rückspiele nur Modelle mit Wissen vor 2025 (gpt-oss-120b) samt **Positivkontrolle** | Kontamination §23.73 |
| P5 | **Kennzeichnung je Zeile:** Fakt · gemessen trägt · Einschätzung ungeprüft | Konzept §7 |
| P6 | **Protokoll mit Zeitstempel** für jede Einschätzung und jeden Fakt; damit wird später gemessen | Lücke §1.3 |
| P7 | **Kontingent rechnen, bevor gebaut wird:** ~40 Assets × 1 Lagebild/Tag ≈ 40 Aufrufe; Ereignis-Leser ≈ 60 Meldungen/Tag in Bündeln ≈ 3–5 Aufrufe. Das passt in Gemini 500/Tag und Groq 1.000/Tag | Bilanz §3 |
| P8 | **Keine Rolle ändert ein Signal**, solange ihre Prüfung nicht trägt | E-125, *LLM ist Prüfung, nicht Entscheider* |
| P9 | **Mehrere Stimmen nur, wo Rauschen gemessen ist**, sonst eine Stimme mit Temperatur 0 | N5 Ursache 4 |

**Was ich als Experte NICHT empfehle:**
- noch ein LLM-Urteil über dieselben Zahlen (elf Wege, Bilanz §2);
- ein stärkeres Modell allein (L-E: die Information begrenzt, nicht das Modell);
- bezahlte Quellen (Projektregel);
- eine Lösung, die erst nach einem Jahr Vorwärtsbetrieb zeigt, ob sie trägt (Nutzer 18.10.).

---

## 6. Ehrliche Erwartung

- **Sicher:** Das Dashboard mit A3/A4/A6 macht die Bewertung **verständiger**. Es zeigt je Asset, was gemessen gilt, was dagegen spricht und was sich geändert hat, mit Quelle. Das ist sofort Nutzen, auch ohne Ertragsbeweis.
- **Möglich:** A1/A2 finden Ausnahmen, die Kurse nicht zeigen. Dann wäre der Vorteil eine **vermiedene** Verlustposition, kein zusätzlicher Gewinner.
- **Unwahrscheinlich, aber nicht ausgeschlossen:** A5 trennt auf 2025–26 Gewinner von Verlierern. Das prüfen wir erst, wenn A1/A2 tragen.
- **Grenze bleibt:** Kleine Werte stehen selten in den Nachrichten (L-C: 43 von 112 Assets nie genannt). Für sie kommen Ereignisse vor allem aus Binance, Upbit und GitHub.

---

## 7. Vorarbeiten und offene Punkte

| # | Punkt | wer / wann |
|---|---|---|
| V1 | **Binance-Ankündigungshistorie** 2023–26 einmalig sichern (inoffizieller Endpunkt, gedrosselt) | ✔ **Ja 28.10.**, läuft: `Rechenkern_02_10/a1_lade_binance.py` → `data/_a1/` (6 Kataloge, ~9.000 Meldungen, fortsetzbar) |
| V2 | NB-`.env`: welche LLM-Schlüssel sind dort gesetzt? Groq vorhanden? | Gemini belegt; Groq/OpenRouter am NB **nicht nötig** für a (§1.5a) |
| V3 | NB-Hardware: reicht RAM für Ollama gpt-oss-20b? (sonst nur Groq/Cloudflare) | ✔ **erledigt**: 8 GB, 2 Kerne → kein lokales LLM (Nutzer 28.10.) |
| V4 | Handgeprüfte Stichprobe für A1 (~200 Meldungen): von mir vorbereitet, **von dir stichprobenartig gegengeprüft** | nach Ja |
| V5 | GDELT GKG und Arctic Shift erst, wenn A1 auf den vorhandenen Feeds trägt (Download nur mit Ja) | später |
| V6 | Protokolltabelle für Dashboard-Einschätzungen in eigener Datei, **nicht** in `tradinginfotool.db` | beim Bau |

---

## 8. Zur Abstimmung (heute Abend) — eine Frage

**Womit beginnen wir?**

| | Weg | Was du danach siehst | Aufwand | Einschätzung |
|---|---|---|---|---|
| **a** | **Fakt-Teil + Befund-Gedächtnis (A3) + Gegenanwalt (A4)** auf der Statusseite, je Asset und Bestand; parallel die Voranalyse für A1 mit V1 | Asset-Sicht mit „was gilt gemessen, was spricht dagegen“ | ~Tage | **Empfehlung**: sofort sichtbar mehr Verstand in der Bewertung, streng prüfbar, ohne Kontamination; A1 bekommt Zeit für die Daten |
| b | **Ereignis-Leser zuerst (A1 → A2)**, das Dashboard danach | zunächst nur Messergebnisse | ~1–2 Wochen | der einzige Weg zu neuer Information, aber lange nichts zu sehen |
| c | **Lagebild (A5) gleich mit**, auf den heutigen Fakten | volle Einschätzung je Asset | ~Tage | wirkt am „intelligentesten“, ist aber ohne neue Information N5 noch einmal, nur hübscher |

Nach deinem Entscheid folgen Messplan bzw. Bauplan als eigene Vorlage. Betrieb und Mails bleiben bis dahin unverändert.

✔ **Entschieden 28.10. abends: a** (Nutzer: *„ok a, Binance-Historie laden ist freigegeben“*). Bauplan: `Bauplan_Dashboard_A3_A4_28_10.md`.
