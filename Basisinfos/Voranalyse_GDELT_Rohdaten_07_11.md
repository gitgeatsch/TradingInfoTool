# Voranalyse GDELT-Rohdaten — Probetag (07.11.2026)

> Zurück zum laufenden Plan: [`Gesamtplan.md`](Gesamtplan.md)

Nutzer 07.11.: *„Probetag laden - wenn dieser auch nichts bringt können wir uns offensichtlich den langen und mühsamen weg sparen und
sind wieder an einem Scheideweg.“*

## 1. Warum

Die NB-Probe (K-GD-1) zeigt: Die Abfrage-Schnittstelle `api.gdeltproject.org` sperrt auch nach 6 h Pause schon den **ersten** Abruf.
K1 (Abdeckung) ist nicht mehr erreichbar. GDELT stellt dieselben Rohdaten als Dateien bereit: GKG 2.1, alle 15 Minuten, auf
`data.gdeltproject.org`, ohne Abfrage. Der Ton je Artikel steht darin (Feld `V1.5TONE`, erster Wert). Die Abfrage-Schnittstelle
rechnet ihren Tageston aus genau diesen Artikeln, sucht aber im **Volltext**, den die Rohdaten nicht enthalten.

## 2. Was der Probetag prüft — VOR dem Laden festgelegt

**Tag:** 03.11.2026, 00:00–23:45 UTC, 96 Dateien. Das ist der einzige Tag, für den die NB-Probe alle **vier** API-Werte hat.

**Treffer je Ton.** Ein Artikel zählt, wenn das Stichwort in Titel (`<PAGE_TITLE>`), Adresse, Namen, Organisationen oder Themen steht.
Die Abfrage-Schnittstelle sucht im Volltext, deshalb ist das nur eine Annäherung:

| Ton | API-Abfrage | Treffer im Rohsatz |
|---|---|---|
| krypto | `(bitcoin OR cryptocurrency)` | `bitcoin` oder `cryptocurrenc` · Thema mit `BITCOIN`/`CRYPTO` |
| fed | `"federal reserve"` | `federal reserve` / `federal-reserve` |
| aktien | `"stock market"` | `stock market` / `stock-market` · Thema `ECON_STOCKMARKET` |
| konflikt | `(war OR sanctions OR tariffs)` | Wort `war`, `sanction…`, `tariff…` · Thema mit `ARMEDCONFLICT`/`SANCTION`/`TARIFF` |

**Kriterien:**

| | Kriterium | Grund |
|---|---|---|
| **R1 Machbarkeit** | Tagesmenge komprimiert ≤ 500 MB **und** Auswertung ≤ 15 min am Desktop | Das NB muss das täglich laden und rechnen |
| **R2 Treffer** | je Ton ≥ 100 Artikel am Tag | darunter ist ein Tagesmittel zu verrauscht |
| **R3 Nähe** | \|Ton roh − Ton API\| ≤ 1,0 bei mindestens 3 von 4 Tönen | Die API-Werte schwanken von Tag zu Tag um etwa 0,5–1,5. Liegt der eigene Wert weiter weg, misst er etwas anderes |

**Urteil, vorab:**
- **alle drei erfüllt** → der Weg ist machbar. Nächster Schritt wäre ein 14-Tage-Abgleich (eigene Frage): Folgt die eigene Reihe der API
  über die Tage?
- **R1 verfehlt** → **Weg tot.** Auch das Rückspiel müsste aus diesen Dateien gerechnet werden: 335 Tage für G7, über 2.000 Tage für den
  Befund aus Stufe 0c.
- **R1 erfüllt, R3 verfehlt** → Eine eigene Reihe wäre möglich, sie ist aber **nicht** die gemessene. Der Befund aus Stufe 0c
  („Aktienmarkt-Ton trägt“) gälte dafür nicht, und das ganze Rückspiel müsste neu gerechnet und neu gemessen werden → **praktisch tot**.
- Ein Tag sagt **nichts** darüber, ob der Ton etwas trägt. Er sagt nur, ob der Weg gangbar ist.

**Abgrenzung zur NB-Probe:** Geladen werden statische Dateien von `data.gdeltproject.org`, nicht die Abfrage-Schnittstelle. K1 ist
ohnehin entschieden. K2 holt der Desktop erst nach dem 16.11.

**Ablage:** `data/_gdelt_roh/2026-11-03/` (nicht im Repository). Gelöscht wird erst, wenn der Nutzer es sagt.
Werkzeug: `Rechenkern_02_10/gdelt_rohdaten_probetag.py` → `gdelt_rohdaten_probetag.txt`.

## 3. Ergebnis (07.11.2026, `gdelt_rohdaten_probetag.txt`)

96 von 96 Dateien, **487 MB**, Ladezeit 218 s, 113.571 Artikel, Auswertung **15 s**, 0 kaputte Zeilen.

| Ton | Artikel | Ton roh | Ton API | Abstand | nur Textstellen (Artikel / Ton) |
|---|---|---|---|---|---|
| krypto | 620 | −3,12 | −3,78 | 0,66 | 89 / −2,19 |
| fed | 347 | −0,75 | −0,40 | 0,35 | 347 / −0,75 |
| aktien | 6.862 | +0,24 | +0,68 | 0,44 | 288 / +1,00 |
| konflikt | 14.038 | −2,16 | −1,98 | 0,18 | 2.272 / −1,91 |

R1 erfüllt (knapp: 487 von 500 MB) · R2 4/4 · R3 4/4 → **Urteil nach Vorabfestlegung: GANGBAR.**

**Was das heißt und was nicht:**
- Der Weg ist **technisch machbar**: Das NB könnte täglich etwa 0,5 GB laden und in unter einer Minute rechnen, ohne Sperre.
- Ein Tag zeigt nur, dass die Werte in der **richtigen Gegend** liegen. Ob die eigene Reihe der API **über die Tage folgt**, zeigt erst der
  14-Tage-Abgleich (≈ 7 GB). Erst damit ließe sich die API-Historie (Rückspiel) behalten und live aus den Rohdaten rechnen. Ohne ihn
  müsste das Rückspiel neu gerechnet werden: 163 GB für G7, rund 1 TB für 2021–2026.
- Ob der Ton überhaupt **etwas trägt**, zeigt dieser Tag **nicht**. S1 und S3 tragen nicht (G7 Stufe 2, 07.11.). Gebraucht wird der Ton
  nur, wenn S2, S7 oder das finale LLM (Stufe 3) tragen.
- **Ablage:** `data/_gdelt_roh/2026-11-03/` (487 MB). Bleibt liegen, bis der Nutzer über das Löschen entscheidet.
