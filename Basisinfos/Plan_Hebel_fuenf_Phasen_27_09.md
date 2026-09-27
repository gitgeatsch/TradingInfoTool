# Der Hebel in fünf Phasen — Planung und Stand

**27.09.2026** · Nutzervorgabe wörtlich, danach der Abgleich

> Dieses Blatt löst `Bauplan_Hebel_27_09.md` als oberste Liste ab. Der
> Bauplan bleibt gültig für die **technischen** Schritte (Dateien,
> Reihenfolge, Fallen), ist aber der Phase 1 untergeordnet.

---

# Die fünf Phasen

| # | Phase | Nutzervorgabe |
|---|---|---|
| **1** | **Grundlage** | *„Messen und die Bewertungen und die fachliche und technische Grundlage zu schaffen — muss sauber über **alle Beiträge** funktionieren (hier sind wir noch immer, Binance, CoinGecko, oder andere Quelle?). Kalibrieren der Hebel, etc."* |
| **2** | **Prüfung an Echtdaten** | *„Prüfung der Messungen anhand von Echtdaten (alle) und **aktuellen Hebelpositionen (Portfolio)** und funktioniert das System am Papier mit historischen Daten (nur Desktop) auf Herz und Nieren — oder müssen wir nachjustieren, da zu wenig oder zu viele Signale entstehen (jetzt kommt **Prüftakt und Cooldown** ins Spiel)"* |
| **3** | **Ablaufkette** | *„Wenn die Basis und das System funktioniert: Hebel über die **gesamte Ablaufkette** prüfen und die **LLM-Bewertung** anpassen, wo erforderlich"* |
| **4** | **Produktion** | *„finaler Umbau und in Produktion für **Einstieg und Hebelbewertung**"* |
| **5** | **Ausbau** | *„nachgelagerte Punkte — Krypto und Hebel final ausbauen mit **Hebelpositionsführung** (Trailing?) und **Ausstieg**"* |

**Wir sind in Phase 1.**

---

# ⛔ Die Trennung, an der ich gescheitert bin

> **Nutzervorgabe 27.09.:** *„DIE BEWERTUNG MUSS NEUTRAL OHNE ERTRAG
> erfolgen — der Ertrag oder Positionsgröße ist NACH der Bewertung
> relevant. Zum Zeitpunkt der Beitragsprüfung ist DAS RISIKO und somit der
> HEBEL zu bewerten. Halte deine Messungen zur Erfolgsmessung mit den
> Betriebsbedingungen auseinander."*

| Ebene | Frage | darf verwenden | darf **nicht** |
|---|---|---|---|
| **A · Bewertung** | Ist diese Lage gut? Welcher Hebel ist bei diesem **Risiko** vertretbar? | Kurs, EMA, ATR, Stopabstand, Zielabstand, RM-11 — alles zum **Entscheidungszeitpunkt** bekannt | ⛔ Ertrag, `q`, CRV aus Ergebnissen, Kelly, Positionsgröße, Kapazität |
| **B · Erfolgsmessung** | Trägt diese Regel? | Erträge, Nullwelt, Weglassprobe, Zeitstabilität | ⛔ zurückfließen in A |
| **C · Betriebsbedingungen** | Was kommt von den Signalen an? | Kapazität, Symbolsperre, Prüftakt, Cooldown, Kontingent, Datenlage | ⛔ als Qualitätsurteil gelesen werden |

⚠️ **Mein Fehler:** Ich habe die **Schwelle** — eine A-Größe — als
**Kelly-Nullstelle** bestimmt. Kelly kommt aus `q` und CRV, also aus
**Erträgen**. Und dann habe ich C (Kapazität, Positionsgröße) in dieselbe
Tabelle gelegt und daraus über A geurteilt.

---

# Der Stand — Befund für Befund, nach Ebenen sortiert

## ✔ Gültig — Ebene B (Erfolgsmessung)

| Befund | |
|---|---|
| **2.606** | EMA-Länge **48 Stunden** ist gemessen; der klassische 50-Tage-EMA ist wertlos (MFE/MAE 1,00) |
| **2.625/2.626** | Die Achse ist **invers** und trägt — 12 von 12 out-of-sample, 115 von 115 Symbolen |
| **2.628** | Geometrie **H24 / Stop 1,00 ATR / Trailing 1,5 / 0,5** |
| **2.629** | Die Kalibriergrenze ergibt sich aus den Kosten; Stop 1,00 ist auch netto optimal |
| **2.633** | Die **Auswahl** trägt 5 von 5 Jahren und in jeder Weglassprobe. ⛔ Die **Stufung** 5/4/3/2 trägt nicht — sie hing an 2025 |
| **2.635** | Auf **Tagesbasis** trägt die Achse **nicht** — keine der sechs EMA-Längen, keine Teillösung |
| **2.636** | Stundendaten machbar: **7-Tage-Fenster** reicht (100 % gleiche Auswahl), Binance am NB erreichbar, Verzögerung bis **6 Stunden** trägt noch |
| **2.637** | **Skalenfaktor 2,0832** für Quellen ohne High/Low — je Symbol (2,6 % Streuung) und über 5 Jahre stabil |

## ✔ Gültig — Ebene C (Betriebsbedingungen)

| Befund | |
|---|---|
| **2.634** | ⛔ **Der Hebel kann heute gar nicht entstehen**: kein Beitrag gilt für `instrument="hebel"`, Kelly im Code ist exakt **0,0**. Das ist der Ist-Zustand, kein Urteil |
| **2.638** | Der Betrieb kauft nur **Streckenanfänge** (29,1 % der Anker). Die **Trennschärfe bleibt** (+2,78 gegen +2,83), der absolute Ertrag fällt |
| **2.623** | **Z-2** (`crv_minimum` 2,0) ist tautologisch und gehört entfernt |
| **2.621** | Längste **Verlustserie 198–199** über alle Stopweiten — nicht wegkalibrierbar |
| *aus 2.640* | ⚠️ Ohne High/Low zerfällt die Reihe in **mehr, kürzere Strecken** (2,32 gegen 2,92 Anker) und feuert **2,29×** so oft. Mengenfrage, keine Ordnungsfrage |

## ⛔ Zurückzuziehen — Ebene A aus Ertrag abgeleitet

| Befund | warum |
|---|---|
| **2.630** | Hebelkurve und Hebelhöhe aus **Kelly** — war schon durch 2.632/2.633 korrigiert, ich habe den Fehler dann wiederholt |
| **2.632** | Schwelle **−1,2881** als Kelly-Nullstelle |
| **2.640** | Schwellen **−1,65 / −2,20** ebenso. ⚠️ Der **Quellenvergleich** darin bleibt gültig (Ebene C) |
| **2.639** | ⛔ **Doppelt falsch**: Positionsgröße 20–50 % statt der echten 1,2–7,8 % (`r_min` 0,5 %, `r_max` 1,25 %), **und** die Frage gehört gar nicht in die Bewertung |

---

# Was Phase 1 noch verlangt

| # | offen | |
|---|---|---|
| **0** | ✔✔ **1a ERLEDIGT (2.642)** — der Horizont ist kein Eingang, sondern ein **Messfenster**. Gemessen regelfrei in ATR: die Achse ist ein **Risiko-Filter** (d 0,521 auf MAE) und kein Ertragsfilter (d 0,267 auf MFE), stabil in 5 von 5 Jahren. ⛔ *Kurz* trifft nicht zu — die Auswahl braucht 10,5 % **laenger** bis zum Hoechstpunkt. ⭐ Die Bruecke zum Hebel steht damit **ohne Ertrag**: 0,75 statt 1,08 ATR Rueckgang heisst niedrigere Stopwahrscheinlichkeit, also mehr Hebel | *erledigt* |
| **1** | ⭐ **Die Bewertungsebene neu aufsetzen** — Chance-Risiko-Verhältnis aus Stop- und Zielabstand, ohne jede Ertragsgröße. Daraus die Schwelle **und** der Hebel | *nächster Schritt* |
| **2** | ⚠️ **„muss sauber über ALLE Beiträge funktionieren"** — bisher ist nur `ema_abstand_atr` betrachtet. Die übrigen sieben Beiträge in `wahrscheinlichkeit.py` stehen auf `null`/`nie` oder `instrumente=("spot",)` | ungeklärt |
| **3** | **Die Quellenfrage**: Binance (28), CoinGecko (16) — oder eine dritte Quelle? | Nutzerentscheidung |
| **4** | **Den Hebel kalibrieren** — aus dem Risiko, nicht aus der Statistik (2.627) | offen |
| **5** | ⚠️ **Der Horizont widerspricht sich dreifach**: gemessen H24, Messnorm 3 Tage, real Median 0,30 Tage | offen seit 26.09. |
| **6** | **Stundendaten in den Betrieb** — technische Grundlage, ohne sie trägt nichts (2.635) | geplant, nicht gebaut |

## Was NICHT in Phase 1 gehört

Positionsgröße · Kapazität · Prüftakt und Cooldown *(Phase 2)* ·
LLM-Bewertung *(Phase 3)* · Positionsführung und Ausstieg *(Phase 5)*

⚠️ Genau diese Punkte habe ich in Phase 1 hineingezogen. Sie stehen hier,
damit das nicht noch einmal passiert.
