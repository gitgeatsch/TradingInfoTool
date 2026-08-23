# Option — eine Claude-Anbindung: wie das technisch geht, und welche Form zu diesem Projekt passt

*Nutzerauftrag 23.08.: „Die Option als Erweiterung und auch als Lösung für
bestimmte und wichtige Probleme **in Evidenz halten**. Deinem Vorschlag zu
Stufe 0 stimme ich zu. Da ich nicht sagen kann, wie man deine Funktionalität
sinnvoll technisch und fachlich integriert, brauche ich Vorschläge von dir und
eine Diskussion, wie man eine solche Verbindung macht — es gibt ja auch
autonome und funktionierende Agents, ohne dass die Software läuft, in der wir
gerade schreiben. Wie wird das in der Praxis gehandhabt?"*

> **Dieses Dokument ist eine Option, kein Bauauftrag.** Es hält fest, welche
> Formen es gibt, welche zu den Regeln dieses Projekts passt und was vorher
> entschieden sein muss.

---

## 1. Die Antwort auf „wie machen das andere?"

**Das Chatfenster ist nur ein Client.** Darunter liegt eine gewöhnliche
HTTP-Schnittstelle. Ein autonomer Agent ist derselbe Aufruf, nur von einem
Skript statt von einem Menschen ausgelöst. Es gibt im Wesentlichen vier Formen:

| Form | was passiert | wer holt die Daten |
|---|---|---|
| **F1 — reiner Modellaufruf** | Text rein, Text raus. Genau wie `api/gemini.py`, `api/groq.py`, `api/zai.py` heute | **wir**, vorher |
| **F2 — Werkzeugnutzung** *(tool use / function calling)* | Das Modell bekommt eine Liste **unserer** Funktionen als Schema. Es antwortet nicht mit Text, sondern mit *„rufe `hole_tvl('TAO')` auf"*. **Unser Code führt aus**, gibt das Ergebnis zurück, Schleife bis fertig | **unser Code**, auf Anforderung |
| **F3 — Agent-SDK, kopflos** | Eine fertige Agentenschleife mit eigenen Werkzeugen (Dateien, Shell, Suche), gestartet aus einem Skript oder per Zeitplan. **Das ist die Form, in der diese Sitzung läuft** — ohne Mensch daneben ist es ein autonomer Agent | **der Agent selbst** |
| **F4 — Stapelverarbeitung** | Viele Aufrufe gesammelt, verzögert, günstiger | wie F1/F2 |

⚠️ **Der entscheidende Unterschied zwischen F2 und F3 ist nicht die Technik,
sondern wer die Kontrolle über die Datenwege hat.**

---

## 2. ⚠️ Warum F2 und nicht F3 — und das folgt aus den eigenen Regeln

**F3 wäre bequemer und ist die falsche Wahl für dieses Projekt.** Drei Gründe,
alle aus bestehenden Projektregeln:

| Regel | was sie hier bedeutet |
|---|---|
| *„Immer an der Quelle prüfen"* · *„zwei Kopien laufen auseinander"* | Ein Agent mit eigenem Netzzugang baut einen **zweiten Datenweg** neben `api/coingecko.py`, `api/macro.py`, `lebendigkeit`. Zwei Wege zur selben Zahl laufen auseinander, und der Unterschied sieht später aus wie ein Befund |
| *„Datenstand und Abrufstand trennen"* | Bei F2 geht jeder Abruf durch **unsere** Module — mit Zeitstempel, Kontingentzählung, Fehlerzeile. Bei F3 wissen wir nicht, was er wann gesehen hat |
| *Alles wird gemessen* | ⚠️ Eine Antwort, die auf einer nicht gespeicherten Websuche beruht, ist **nicht wiederholbar** und damit **nicht messbar**. Dasselbe Modell dreht bei bitgleicher Eingabe rund 12 % der Fälle (gemessen an nemotron) — ohne gespeicherte Eingabe ist keine spätere Auswertung möglich |

> **Empfehlung: F2.** Das Modell darf **fragen**, aber **unser Code holt**.
> Damit bleibt jede Zahl auf dem Weg, den das Projekt schon kennt.

---

## 3. ⚠️ Die wichtigste Bauregel: der Agent liefert einen FAKT, keine Entscheidung

**Das ist der Punkt, an dem so etwas üblicherweise schiefgeht.** Die
naheliegende Bauweise wäre: Agent fragen, was er von TAO hält, Antwort ins
Signal. **Das wäre ein zweiter Entscheider neben der Rollen-Kette** — und die
Kette hätte keine Möglichkeit, ihn zu prüfen.

**Stattdessen dieselbe Bauform, die `lebendigkeit` und der `vorfilter`-Schatten
schon haben:**

```
    sammeln  ->  SPEICHERN (Quelle, Abrufstand, Text)  ->  später bewerten
                                                       ->  erst dann entscheiden
```

**Was das leistet:**

- Der Beitrag ist **später messbar** — gegen Ergebnisse, wie jeder andere Fakt.
- Er kann die Formregeln **nicht umgehen** (R-T1…R-T12 gelten für den Text).
- Fällt er aus, **fehlt eine Zeile — nie ein Signal**. Das ist die Regel aus
  `anlass_kalender`, und sie hat sich bewährt.

⚠️ **Und er wird zuerst als Schatten geführt**, wie H seit dem 22.08.: rechnet
mit, steht in Mail und Datenbank, **entscheidet nichts**. Erst wenn er die
Zufallslinie messbar schlägt, darf er wirken.

---

## 4. Wo das im Code andockt — konkret

| # | was | analog zu |
|---|---|---|
| **B1** | `api/claude.py` — Anbieter neben Gemini/Groq/Z.ai, gleiche Schnittstelle wie `llm_basis` | `api/zai.py` |
| **B2** | `agent/nachrichten.py` — **Stufe 0**: Sammlung aus freien Quellen, schreibt `nachricht_beobachtung` (Symbol, Quelle, Abrufstand, Text). **Kein Modell.** | `agent/lebendigkeit.py` |
| **B3** | Die Werkzeugliste für F2: bestehende Funktionen als Schema — `lebendigkeit.sammle_tvl`, `coingecko`, `trichter.spanne`, `vorfilter.bewerte`, `drift.rang` | — |
| **B4** | Aufrufstelle: `rollen_lauf._ein_asset`, **hinter der letzten Abbruchstelle** | `anlass_kalender.saetze()` |
| **B5** | Kostenzähler mit **hartem Tagesdeckel** | `api_call_kontingent` (existiert) |

⚠️ **B5 ist nicht optional.** Ein Agent, der selbst entscheidet, wie oft er
nachfragt, hat keine natürliche Obergrenze. Der Deckel gehört in den Code, nicht
in die Absicht.

---

## 5. ⚠️ Was vor jedem Bau entschieden sein muss

| # | Frage | Stand |
|---|---|---|
| **E1** | **Kosten.** Ein Claude-Aufruf ist kostenpflichtig — das ändert die stehende Regel *„nur kostenfreie LLMs"* | ⚠️ **Nutzerentscheidung, offen** |
| **E2** | **Wieviel?** Vor jedem Einsatz gilt die eigene Regel *„vor jedem Messlauf Limits, Kontingent, Dauer"*. Der Tokenbedarf ist **an einem Trockenlauf zu messen**, bevor ein Cent fließt | messbar, noch nicht gemessen |
| **E3** | **Schlüssel auf dem Notebook** — dieselben Regeln wie `.env`, nie geräteübergreifend | Regel existiert |
| **E4** | **Wo?** Selektiv auf den *k* Finalisten je Umlauf, nicht auf 41 Symbolen | folgt aus der Rangauswahl (A1) |

---

## 6. Stufe 0 — was ohne jede Entscheidung und ohne einen Cent gebaut werden kann

**Nachrichten werden heute nirgends gesammelt.** Im ganzen Projekt gibt es kein
Nachrichtenmodul; `api/finnhub.py` liefert nur Analystentrends.

> ⚠️ **Damit gibt es nichts einzuordnen — weder für mich noch für ein freies
> Modell.** Die Lücke ist nicht die Bewertung, sondern der **Bestand**.

**Stufe 0 ist deshalb Sammlung, nicht Bewertung:**

| | was | Kosten |
|---|---|---|
| 0.1 | `nachricht_beobachtung` — Tabelle mit Symbol, Quelle, Abrufstand, Text | 0 |
| 0.2 | Sammlung aus freien Quellen, mit Fehlerzeile bei Ausfall | 0 |
| 0.3 | Anzeige im Faktenblock (für den Nutzer), **nicht** im Faktentext (fürs Modell) | 0 |

⚠️ **Erst wenn eine Reihe steht, ist die Frage überhaupt stellbar** — genau wie
bei TVL, wo die 30 Beobachtungen den Termin 18.09. bestimmen. **Ein Agent kann
keine Vergangenheit erzeugen.**

---

## 7. Der Satz, der die Sache einordnet

Alles, was in diesem Projekt an belastbaren Zahlen steht — der Trichter, die
quotengleiche Kontrolle, die Querschnittsmessung — ist **außerhalb** der
Produktion entstanden und läuft dort jetzt **kostenlos**.

> **Das beste Verhältnis hat nicht ein Agent in der Schleife, sondern einer,
> der die Schleife baut.** Eine Anbindung lohnt genau dort, wo etwas *laufend*
> gebraucht wird, das deterministisch nicht geht — und das ist bisher
> **genau eine** Sache: **Nachrichten lesen und einordnen.**
