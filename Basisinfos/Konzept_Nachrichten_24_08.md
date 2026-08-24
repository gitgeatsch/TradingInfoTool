# Nachrichten (Weg D) — Plan und Konzept

*Nutzervorgabe 24.08.2026: „mach weiter mit den nachrichten" und, unmittelbar
danach: **„bevor wir mit den nachrichten starten brauchen wir einen
detaillierten Plan und Konzept."** Dieses Dokument ist dieser Plan. Es wird
**nichts gebaut**, bevor die Entscheidungen in §9 getroffen sind.*

> ## ⚠️ Zwei Korrekturen an meinem ersten Entwurf
>
> Der erste Entwurf dieses Dokuments (vor der Bestandsaufnahme) enthielt zwei
> Fehler. Sie stehen hier, weil beide lehrreich sind:
>
> **1. Ich behauptete, der Desktop habe keinen Netzzugang.** Das war falsch.
> `curl` lieferte in meiner Werkzeugumgebung `000`, und daraus habe ich auf den
> Rechner geschlossen. Tatsächlich war nur mein Bash-Werkzeug gesandboxt —
> Python erreicht CoinGecko problemlos (`200`). **Ein Werkzeug-Artefakt für
> eine Tatsache über die Welt gehalten** — genau der Fehlertyp, den wir heute
> den ganzen Tag in den Prüfungen behoben haben.
>
> **2. Ich habe mit der QUELLE angefangen.** Der Umbauplan sagt in Kapitel 63.5
> ausdrücklich das Gegenteil, und er hat recht — siehe §3.

---

## 1. Der wichtigste Fund: der teuerste Schritt ist gar nicht der erste

**Die Bestandsaufnahme hat eine Lücke gefunden, die ohne jede neue Quelle
schließbar ist.**

Der Anlass-Kalender (`agent/anlass_kalender.py`, gebaut am 20.08.) liefert
FOMC-Termine, CPI-Veröffentlichungen und Optionsverfall. Er steht in jeder
Mail. **Aber:**

| | |
|---|---|
| Modellaufruf (Rolle BC) | `agent/rollen_lauf.py:1065` |
| Aufruf des Anlass-Kalenders | `agent/rollen_lauf.py:1550`, im Abschnitt `--- Die Mail ---` (ab :1485) |

> ⚠️ **Der Kalender läuft NACH dem Urteil. Das Modell entscheidet, ohne zu
> wissen, dass in vier Tagen ein Optionsverfall ansteht.** Die Information geht
> ausschließlich in den Mailtext — kein `facts_json`, keine Tabelle, kein
> Prompt.

**Dasselbe gilt für `agent/cycles.py`** (Präsidentschaftszyklus): gebaut,
nirgends verdrahtet — der Modulkopf sagt es selbst.

**Das ist die Kategorie „bereits deterministisch berechnet, es fehlt nur die
Weitergabe"** — dieselbe Kategorie, die bei Kosten und Ausstiegsregel am 05.08.
als „aussichtsreichste" eingestuft wurde. Sie kostet **keine neue Quelle, kein
Kontingent, keine Sammelzeit** und ist **sofort gepaart messbar**.

⚠️ **Und der Kalender ist bis heute nie gegen den Zufall gemessen worden.**
`agent/wahrscheinlichkeit.py:135-139` führt ihn mit `zustand="nie", punkte=0.0`
und der wörtlichen Begründung *„Anzeige, nie gegen den Zufall gemessen"*. Nach
der Projektregel „gebaut heißt nicht geprüft" trägt er heute **null**.

---

## 2. Was es sonst gibt — und was ausdrücklich fehlt

### Gebaut

| Modul | Quelle | erreicht das LLM? |
|---|---|---|
| `anlass_kalender._fomc()` | statische Liste, `cycles.py` | **nein** |
| `anlass_kalender._cpi()` | FRED (braucht `FRED_API_KEY`) | **nein** |
| `anlass_kalender._verfall()` | Deribit, **nur BTC/ETH** | **nein** |
| `marktlage.beschreibe_stimmung()` | Fear & Greed, 3.111 Tage | ✔ **ja** — aber das ist Stimmung, keine Nachricht |
| `api/finnhub.py` | Analysten-Konsens | ✔ ja, **nur Aktien-Prompt** |

### Nicht vorhanden — verifiziert

**Es gibt keinen Nachrichten-Client.** Kein `agent/nachrichten.py`, kein RSS,
keine Tabelle, keine Zeitreihe. Alle vier Analyst-Prompts enthalten im
Gegenteil die Anweisung *„Erfinde keine … Nachrichten oder Ereignisse"* und
melden `"sentiment_einbezogen": False`.

### ⚠️ Die FOMC-Liste läuft aus

`FOMC_MEETING_DATES_2026` endet am **09.12.2026**. Ab Januar 2027 liefert sie
nichts — **und das sieht in der Mail aus wie „keine Sitzung", nicht wie „Liste
abgelaufen".** Eine automatische Warnung gibt es nicht. Das ist unabhängig von
diesem Vorhaben zu beheben.

---

## 3. ⚠️ Die Reihenfolge — Form vor Quelle, nicht umgekehrt

**Der Umbauplan hat diese Frage bereits entschieden** (Kapitel 63.5, wörtlich):

> ⚠️ **„Eine Schlagzeile ist von Natur aus ein Etikett."** *„Unternehmen
> übertrifft Erwartungen"* **ist** ein fertiges Urteil — genau das, was am
> selben Abend als Regime aus Rolle G geflogen ist (R-T2, R-T3, R-T12).
>
> Sie in eine beschreibende Form zu übersetzen ist selbst eine Modellleistung.
> **Wir würden einen ungemessenen LLM-Schritt VOR das LLM setzen** — und damit
> die Fehlerquelle einbauen, gegen die die ganze Faktenschicht geschrieben ist.

Und die vorgeschriebene Reihenfolge:

| | |
|---|---|
| **1** | die **Übersetzung** festlegen: Ereignisart, zeitlicher Abstand, Betroffenheit — **ohne Wertung** |
| **2** | eine kostenlose Quelle für die tatsächliche Watchlist finden |
| **3** | gepaart messen, wie jede andere Änderung |

> **„Erst die Form, dann die Quelle, dann die Wirkung. Wer bei der Quelle
> anfängt, baut ein Etikett ein."**

**Mein erster Entwurf begann mit der Quellenprüfung. Das war der Fehler, vor
dem dieses Kapitel warnt.**

---

## 4. Das zweite Messproblem: Look-ahead-Bias

*Dieser Punkt kommt zusätzlich hinzu und wird im Umbauplan noch nicht
behandelt.*

Selbst mit Form und Quelle bleibt: **ein historischer Backtest funktioniert
hier nicht.**

> Das LLM wurde auf Daten trainiert, die die Nachricht **und ihre Folgen**
> enthalten. Fragt man es, wie es eine Meldung vom März 2025 bewertet hätte,
> kann es auf Wissen darüber zurückgreifen, was danach geschah.

Das ist in der Literatur als Look-ahead-Bias bei LLM-Sentiment untersucht und
bestätigt. **Und es trifft dieses Projekt doppelt**, weil ein fremdes,
kostenfreies Modell urteilt, dessen Trainingsstand wir weder kennen noch
kontrollieren — und der sich bei Modellwechseln verschiebt (Provider-Drift ist
belegt: Mistral, 31.07.).

| Umgehungsversuch | warum er nicht trägt |
|---|---|
| „nur nach dem Trainingsstichtag" | Stichtag bei freien Providern nicht verlässlich bekannt |
| „Datum verschweigen" | der Inhalt verrät den Zeitpunkt |
| „nur die Schlagzeile" | ändert nichts am Vorwissen über genau diese Schlagzeile |

**Konsequenz: Vorwärtssammlung.** Dasselbe Muster wie Kapitel 93 C
(`lebendigkeit.py`), das seit 19.08. sammelt und ab 18.09. auswertbar ist.
⚠️ **Der Sammelbeginn bestimmt den Auswertungstermin** — jeder Tag Verzögerung
verschiebt ihn.

**Das gilt NICHT für Schritt N1** (§5): Termine sind im Voraus bekannt und
rückwirkend rekonstruierbar. **Deshalb ist N1 sofort messbar und alles andere
nicht.**

---

## 5. Der Stufenplan

### N1 — Den vorhandenen Kalender an das Modell verdrahten

**Kein neuer Anbieter, keine Sammelzeit, sofort messbar.**

| | |
|---|---|
| **Was** | `anlass_kalender.saetze()` vor den Modellaufruf ziehen und in den Faktensatz geben |
| **Form** | beschreibend nach `R-T`: Ereignisart, Abstand in Tagen, Quelle — **ohne Wertung**. Der Satz *„⚠️ UNGÜNSTIG FÜR EINEN EINSTIEG"* aus der Mail darf **nicht** mitwandern: das ist ein Etikett |
| **Messung** | gepaart, A/B, wie jede Prompt-Änderung. Drei-Arm-Design mit Rauschboden |
| **Kosten** | keine neue Quelle. Prompt wächst um wenige Zeilen |
| ⚠️ **Vorsicht** | der Prompt wurde am 10.08. bewusst von 34.611 auf 3.183 Zeichen gekürzt. **Obergrenze festlegen** |

> **Damit wird zugleich die offene Frage beantwortet, ob der Kalender
> überhaupt etwas trägt** — heute steht er mit „null Punkte, nie gemessen" da.
> Trägt er nicht, ist das ein Ergebnis über die *Kategorie* Termine, bevor Geld
> und Monate in Nachrichten fließen.

### N2 — Die Übersetzung festlegen *(Papier, kein Code)*

**Vor jeder Quelle.** Zu bestimmen ist, welche **beschreibenden** Merkmale eine
Meldung bekommt:

| Merkmal | Beispiel | ⚠️ verboten |
|---|---|---|
| Ereignisart | `netzwerk_umstellung`, `zwischenfall`, `boersenzugang`, `token_freigabe` | `gute_nachricht` |
| zeitlicher Abstand | „vor 6 Stunden" | „frisch" |
| Betroffenheit | „nennt ETH im Titel" | „betrifft ETH stark" |
| Quelle + Reichweite | „CoinDesk" | „seriöse Quelle" |

**Ergebnis von N2 ist eine feste Liste von Ereignisarten** — geschlossen, nicht
frei. Nur so ist die Zuordnung prüfbar und der Etikett-Fehler ausgeschlossen.

⚠️ **Offen und in N2 zu entscheiden:** wie die Zuordnung erfolgt. Eine
Stichwortliste ist deterministisch und prüfbar, aber grob. Ein Modellaufruf ist
feiner, kostet Kontingent **und ist genau der „ungemessene LLM-Schritt vor dem
LLM"** aus 63.5. **Meine Empfehlung: Stichwortliste**, mit ausgewiesener
Fehlerquote.

### N3 — Quelle und Bestand

Erst jetzt. Eine Tabelle `nachricht_beobachtung` (so bereits vorgeschlagen in
`Option_Claude_Agent_Anbindung_23_08.md` §6), die sammelt:

Quelle · Zeitstempel der Meldung · **Zeitstempel unseres Abrufs** · Titel ·
Ereignisart (aus N2) · betroffene Symbole · Link

⚠️ **Beide Zeitstempel getrennt** — Lehre „Datenstand ≠ Abrufstand" (17.08.):
der Anbieter darf alt sein, wir nie.

### N4 — Messen

Gegen das **Potential** (barrierenfrei, brutto, fester Horizont), **nicht**
gegen „Ziel vor Stop". Mit **Positivkontrolle** — ohne sie heißt „nichts
gefunden" nur „nicht hingesehen" (Lehre 93 B).

---

## 6. Quellenprüfung — heute durchgeführt

*Vom Desktop, mit Python. Kein Notebook beteiligt.*

| Quelle | Ergebnis | Bewertung |
|---|---|---|
| **CoinDesk RSS** | **200**, 30 KB, 31 Einträge, `pubDate` **mit Uhrzeit** (`Mon, 24 Aug 2026 17:30:10 +0000`) | ✔ brauchbar |
| **Cointelegraph RSS** | **200**, 45 KB | ✔ brauchbar |
| **DefiLlama `/protocols`** | **200**, 8,6 MB | ✔ frei (wird bereits genutzt) |
| **DefiLlama `/emissions`** (Token-Freigaben) | ⚠️ **402 Payment Required** | ✘ **kostenpflichtig** |
| **CoinGecko `/news`** | ⚠️ **401 Unauthorized** | ✘ braucht Schlüssel |

**Damit ist die Lage klar und deckt sich mit dem, was der Umbauplan schon
2026-08 festhielt:**

> „Unlocks und Listings stehen in keiner freien, vollständigen API — dasselbe
> Problem wie bei den On-Chain-Daten, nur schlimmer."

| Ereignisart | freie Quelle? |
|---|---|
| **Zwischenfälle** (Hacks, Ausfälle) | ✔ über RSS erreichbar |
| **Netzwerk-Umstellungen** | ✔ über RSS erreichbar |
| **Börsenzugänge** (Listings) | teilweise über RSS |
| ⚠️ **Token-Freigaben** | ✘ **keine freie strukturierte Quelle gefunden** |

⚠️ **Und der Zeitstempel ist der entscheidende Befund**: RSS liefert ihn
sekundengenau. Ohne ihn wäre die ganze Vorwärtsmessung wertlos.

---

## 7. Die drei ungelösten Seiten — aus dem eigenen Plan

*`Umbauplan_Gesamtsystem_12_08.md:11946-11958`, warum Stufe 93 D
zurückgestellt wurde. Sie gelten unverändert:*

| | |
|---|---|
| **Quelle** | keine freie, vollständige API — bestätigt durch §6 |
| ⚠️ **Vollständigkeit** | *„ein Kalender mit Lücken ist gefährlicher als keiner: fehlt ein Anlass, sieht die Lage ruhig aus"* |
| **Deckelproblem** | *„ein Anlass, der zur Bedingung wird, ist ein Gate — und ein lückenhaftes Gate sperrt zufällig"* |

**Die Vollständigkeitsfrage ist der härteste Einwand gegen das ganze Vorhaben**
und lässt sich nicht wegbauen — nur **benennen**. Deshalb: wie beim
Anlass-Kalender muss jede Ausgabe sagen, **was sie nicht abdeckt.**

---

## 8. ⚠️ Der Prioritätswiderspruch — vom Nutzer zu klären

**Vier Projektdokumente widersprechen sich darüber, wie dringend das ist:**

| Dokument | Rang |
|---|---|
| `Zwischenstand` 8d | **Rang 2** — und seit S2 erledigt ist der **oberste offene** |
| `Umbauplan` 41.6 | **„jetzt: hoch"** |
| `Was_vor_Schritt_1_23_08.md` | Rang 4 |
| `Befundkarte.md` | **Schritt 7 — letzter Rang**, wörtlich `NIE BEARBEITET` |

**Das ist kein Formfehler, sondern eine offene Entscheidung.** Solange sie
nicht getroffen ist, lässt sich „mach weiter mit den Nachrichten" nicht
eindeutig ausführen.

---

## 9. Die Entscheidungen, die vor dem Bau zu treffen sind

| # | Frage | Meine Empfehlung |
|---|---|---|
| **E1** | **Mit N1 beginnen** (vorhandenen Kalender verdrahten) oder direkt Nachrichten sammeln? | ⚠️ **Klar N1.** Es kostet keine neue Quelle, keine Sammelzeit, ist sofort gepaart messbar — und beantwortet, ob die Kategorie „Termine" überhaupt trägt, bevor Monate in Nachrichten fließen. **Der billigste Erkenntnisgewinn im ganzen Vorhaben** |
| **E2** | **Zuordnung per Stichwortliste oder Modellaufruf?** | **Stichwortliste.** Ein Modellaufruf wäre der „ungemessene LLM-Schritt vor dem LLM" aus 63.5 — und kostet Kontingent |
| **E3** | **Token-Freigaben trotz fehlender freier Quelle verfolgen?** | **Nein, zurückstellen.** Die einzige gefundene Quelle ist kostenpflichtig; das verstößt gegen „nur kostenfrei". Mit Zwischenfällen und Netzwerk-Umstellungen beginnen |
| **E4** | **Sammelbeginn sofort** (auch ohne fertige Messung), damit die Uhr läuft? | **Ja, sobald N2 steht.** Der Sammelbeginn bestimmt den Auswertungstermin — jeder Tag Verzögerung verschiebt ihn. Aber **nicht vor N2**, sonst sammeln wir Etiketten |
| **E5** | **Der Prioritätswiderspruch aus §8** | Ihre Entscheidung — ich kann sie nicht aus den Dokumenten ableiten, weil sie sich widersprechen |

---

## 10. Was dagegen spricht — vollständig

| # | Einwand | Gewicht |
|---|---|---|
| **1** | ⚠️ **Vollständigkeit ist nicht herstellbar** (§7). Ein lückenhafter Ereigniskanal lässt eine Lage ruhig aussehen, die es nicht ist | **schwer** |
| **2** | **Look-ahead-Bias** verhindert jeden schnellen Nachweis (§4) — Ergebnisse frühestens nach Monaten | **schwer** |
| **3** | **Nachrichten sind das am stärksten beforschte Feld.** Was frei zugänglich ist, ist mit hoher Wahrscheinlichkeit eingepreist, bevor unser 15-Minuten-Takt es sieht | **schwer** |
| **4** | ⚠️ **A1 verengt die Fallzahl** (Zielkonflikt vom 24.08.) — weniger Beurteilungen heißt **längere** Sammeldauer. Beide Vorhaben ziehen gegeneinander | **mittel–schwer** |
| **5** | **Sentiment war schon einmal empirisch widerlegt** (Kap. 12.7, BTC 3.087 Tage): stützt Momentum, nicht Stimmung | mittel |
| **6** | **Provider-Drift** trifft die Bewertung über die Zeit | mittel |

> **Ehrliche Gesamteinschätzung:** Von den drei verbliebenen Wegen ist dieser
> der **teuerste in Zeit** und der mit der **schwächsten Vorabvermutung**.
> **Kosten (Weg 3) ist rechnerisch näher an einem Ergebnis.**
>
> ⚠️ **Aber N1 ist davon ausgenommen:** die Verdrahtung des vorhandenen
> Kalenders ist billig, schnell und sofort messbar — sie lohnt sich unabhängig
> davon, wie über den Rest entschieden wird.

---

## 11. Wenn gebaut wird — Pflichten aus der eigenen Methodik

- **Dauerprüfungen in `pruefe_pakete.py`** für jede neue Tabelle/Spalte
- **Wer eine Spalte anlegt, muss eine Zeile daraus LESEN** (2.61)
- **`finde_freie_namen.py`** vor dem Funktionstest (2.63)
- **Isolation:** Tests gegen eine **eigene Kopie**, nie gegen die laufende
  Produktion (2.66 / 2.71 / 2.72)
- **NB-Export mitziehen** — sonst meldet der Drift-Wächter `nicht_erwaehnt`
- **Zentraldokumente:** `Regelwerksmanual.md` (neue Regel), `Umbauplan`
  (Kapitel 148), `Fakten_Entscheidungsmappe.md` (neuer Fakt), `Zwischenstand` 8c
- ⚠️ **`anlass_kalender` gepaart messen** — er trägt heute „null Punkte, nie
  gemessen"; N1 muss diesen Zustand beenden, nicht fortschreiben

---

## 12. Was dieses Konzept NICHT löst

| | |
|---|---|
| **Die Sammeldauer** | erst nach N2/N3 rechenbar — Meldungsrate je Symbol unbekannt |
| **Token-Freigaben** | keine freie Quelle gefunden (§6) |
| **Die Vollständigkeitsfrage** | grundsätzlich nicht lösbar, nur benennbar |
| **Der Prioritätswiderspruch** | §8 — Nutzerentscheidung |
| **Die FOMC-Liste ab 2027** | eigenständiger Betriebsmangel, unabhängig zu beheben |
