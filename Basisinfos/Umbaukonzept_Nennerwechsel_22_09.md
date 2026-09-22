# Umbaukonzept — Nennerwechsel `turnover` (22.09.2026)

> **Nutzervorgabe:** *„beim Umbau und austausch von Turnover zu
> Umlaufmenge sauber trennen damit nichts passiert, berücksichtige den
> Fingerprint, etc. gleiche den Code sauber mit der Doku ab und teste und
> simuliere damit alles passt"*

⚠️ **Nichts hiervon ist gebaut.** Dies ist die Trennungsanalyse vor der
Abstimmung. Jede Zeile unten ist **am Code belegt**, nicht angenommen.

**Entschieden:** E1 (Näherung als Messverfahren) und E2 (Nennerwechsel)
— Nutzerentscheidung 22.09. **Nicht** dabei: der Hebel (E4).

---

## 0. Was überhaupt getauscht wird

| | heute | nachher |
|---|---|---|
| Beitrag | `turnover_fuenftel` | **derselbe** — kein dritter Beitrag |
| Zähler | Binance-24h-Stückvolumen | **unverändert** |
| **Nenner** | `SplyCur` = Gesamtausgabe, 66 Symbole | **freier Umlauf** = Marktkap./Preis, 366 |
| Codefeld | `turnover_fuenftel` | **bleibt** (2.512: Umbenennen bricht Verträge) |

---

## 1. Die sechs Trennstellen

### T1 — Die Größe selbst ✔ steht bereits

`marktrang.UMSCHLAG_GROESSEN` führt beide, `umschlag_name(datei)` leitet
die Größe **aus der Datei ab** und liefert für eine unbekannte Quelle
`unbekannt`. Eine stille Verwechslung ist damit schon ausgeschlossen.

**Zu tun:** `betriebsweg` für `umschlag_frei` füllen (heute `None`).

### T2 — ⛔ DER FINGERABDRUCK IST BLIND FÜR DEN NENNER

```python
# potential.beitragslage()
teile.append("%s:%s" % (b.merkmal or b.name, "/".join(...b.stufen)))
```

> **Der Fingerabdruck bildet die STUFEN ab, nicht die QUELLE.**
> Ein Nennerwechsel bei gleichen Stufen käme durch die R-R9-Prüfung
> **unbemerkt** durch — `kalibrierung_gilt()` meldete „passt", obwohl der
> Beitrag etwas völlig anderes misst.

✔ Das Feld dafür existiert: `Beitrag.quelle` (*„woher die Zahl stammt"*).
Es wird nur nicht in den Fingerabdruck aufgenommen.

**Zu tun:** `beitragslage()` nimmt eine **Nennerkennung** mit auf.
⚠️ Nicht die ganze `quelle`-Zeichenkette — die enthält Tageszahlen und
Wirkungswerte und würde bei jeder Doku-Änderung den Fingerabdruck
brechen. Sondern die **Größe** aus `UMSCHLAG_GROESSEN`.

⚠️ **Die Änderung bricht `kalibrierung_gilt()` sofort** — das ist
gewollt und muss im **selben Schritt** mit `KALIBRIERT_FUER` nachgezogen
werden. `pruefe_pakete.py` prüft es (Z. 17315).

### T3 — ⛔ DIE NENNERSPERRE IST AN DIE ALTE QUELLE GEBUNDEN

`marktrang.NENNER_WIDERLEGT` sperrt **XVG** und **KNC**. Der Grund steht
dort im Klartext:

| Symbol | Begründung | wer liegt falsch |
|---|---|---|
| **XVG** | SplyCur 1,6522e12 gegen freien Umlauf 1,6522e10, CoinMarketCap 16.521.951.235 | **die Betriebsquelle** (SplyCur), Faktor 100 zu hoch |
| **KNC** | SplyCur 1,1264e7 gegen freien Umlauf 2,0923e8, CoinMarketCap 209.230.859 | **die Betriebsquelle** |

> ⚠️⚠️ **Bei beiden ist der FREIE UMLAUF der richtige Wert.** Nach dem
> Wechsel würde die Sperre **zwei gesunde Symbole entfernen** — und der
> gemessene Preis (3,26 % der Symbol-Tage verschieben sich um ein
> Fünftel) fiele grundlos an.

**Zu tun:** `NENNER_WIDERLEGT` wird **je Quelle** geführt, nicht global.
⚠️ Nicht löschen — sonst fehlt die Sperre bei einem Rückwechsel.

### T4 — Die Messbasis und der Scheduler

`marktrang.MESSBASIS["turnover"]` zeigt auf
`data/onchain_historie.db` / `SELECT DISTINCT symbol FROM splycur`.
Und `scheduler/background.py` fragt **genau diese Symbole** ab:

```python
_symbole = sorted(_MR.messbasis("turnover"))
```

➤ **Wer nur den Leser umstellt, bekommt keine einzige zusätzliche
Menge.** Leser und Schreiber gehören in denselben Schritt.

⚠️⚠️ **Und damit wechselt die GRUNDGESAMTHEIT** (66 → 366 Symbole im
Rang). CLAUDE.md: *„Wer sie ändert, misst die Wirkung."* →
`messe_grundgesamtheit.py`, vier Sekunden. **Vor** dem Rollout, nicht
danach.

### T5 — Die Schwelle

| | |
|---|---|
| heute | 0,080, `KALIBRIERT_FUER` auf den alten Stufen |
| nachher | **0,060** (gerechnet, 2.521) + neuer Fingerabdruck |
| Regel | **im selben Schritt** — R-R9 |
| Ort | `Basisinfos/config.yaml` → `bewertung: potential_schwelle_r` **und** `potential.KALIBRIERT_AM` |

### T6 — Der Bündelfaktor ⚠️ NICHT anfassen

Er sitzt im Abruf (`hole_umlaufmenge_cg.vervielfacher` → `zerlege`) und
ist **angewandt** (2.522). Eine zweite Anwendung in `marktrang` machte
die Menge 1.000-fach zu klein. **Genau einmal, und das ist bereits der
Fall.**

**Zu tun:** nur der Herkunftsnachweis — `_quelle` bekommt ein Feld
`buendelfaktor`, und der Leser bricht ab, wenn es fehlt.

---

## 2. Code gegen Doku — der Abgleich

| Ort | sagt heute | nach dem Umbau |
|---|---|---|
| `CLAUDE.md` | — (nennt turnover nicht direkt) | prüfen, ob die Messbasis-Tabelle stimmt |
| `agent/potential.py` | `KALIBRIERT_FUER` alte Stufen; Kommentarblock „gerechnet, aber nicht gesetzt" | beides nachziehen |
| `agent/marktrang.py` Kopf | beschreibt `SplyCur` als Betriebsquelle | umschreiben |
| `agent/datenfrische.py` | Quelle `coinmetrics_splycur`, Frist 21 Tage; `messmenge.ABDECKUNG[turnover]` | neue Quelle **und** neue Frist |
| `UMSCHLAG_GROESSEN` | `umschlag_frei`: `live: False`, `codefeld: None`, `stufen_registriert: False` | alle drei umdrehen |
| Register | erzeugt aus `bestand.py` | läuft automatisch mit |

⚠️ **`UMSCHLAG_GROESSEN` ist der Abgleichpunkt** — es behauptet den
Zustand, und `pruefe_pakete.py` kann ihn gegen den Code prüfen. Wer dort
`live: True` schreibt, ohne den Betriebsweg zu bauen, fällt auf.

---

## 3. Testen und simulieren

| # | Prüfung | Kriterium |
|---|---|---|
| **P1** | **Bitgleichheit vorher/nachher bei UNVERÄNDERTER Quelle** | jeder alte Aufruf liefert dasselbe — sonst ist der Umbau nicht additiv |
| **P2** | **Seiteneffekt-Nachweis je Riegel** (Mutation) | Riegel abschalten → Prüfung muss rot werden. Ein Riegel, der nie greift, ist keiner |
| **P3** | ✔ **Grundgesamtheit gemessen (22.09., 2.525)** | `phase4_c_fuenftelwechsel_nenner.py` — ⚠️ nicht `messe_grundgesamtheit.py`, die misst `schnitt`. **59 %** der gemeinsamen Symbol-Tage wechseln das Fünftel auf der 20-%-Menge, **53.113 bekommen erstmals eines**. Die Größe allein macht 65,5 % (richtungsneutral), die **Menge kippt die Richtung** auf 4,35:1 nach unten |
| **P4** | **Betriebssimulation an echten Signalen** | wie 2.517: Werte mit/ohne, Durchlass, Hebel — gegen die NB-Sicherung |
| **P5** | **R-R9 grün** | `kalibrierung_gilt()` muss nach dem Schritt `True` sein |
| **P6** | **Volle Suite** | 3.052 Prüfungen, nur die drei bekannten Datenstands-Zeilen rot |
| **P7** | **Betrieb** | Pull + Neustart + Export nach ~30 Min |

⚠️ **P1 und P2 sind die wichtigen.** P1 stellt sicher, dass nichts
kaputtgeht, was heute läuft; P2, dass die neuen Schutzmaßnahmen nicht
bloß dastehen — *„der alte in Paket 15 stand da und griff nie."*

---

## 4. Reihenfolge

```
S1  Fingerabdruck um den Nenner erweitern (T2)     ← ohne Wirkung, aber Voraussetzung
S2  NENNER_WIDERLEGT je Quelle (T3)                ← ohne Wirkung
S3  Herkunftsmarke + Riegel fuer den Buendelfaktor (T6)
S4  Betriebsweg + Scheduler umstellen (T1, T4)     ← HIER wirkt es
S5  Grundgesamtheit messen (P3)          <- ERLEDIGT 22.09., 2.525
S6  Schwelle 0,060 + KALIBRIERT_FUER (T5)          ← im SELBEN Commit wie S4
S7  Doku-Abgleich (Abschnitt 2)
S8  Simulation + Suite + Betrieb (P4, P6, P7)
```

⚠️ **S1 bis S3 sind wirkungslos und deshalb sicher** — sie können vor
der Umstellung gebaut und geprüft werden. **S4 und S6 gehören zusammen**:
ein Nennerwechsel ohne Neukalibrierung ist nach R-R9 unvollständig.

---

## Belege

2.522-buendelfaktor-schon-drin · 2.521-schwelle-neu · 2.520-trefferquote-selektiert ·
2.519-* · 2.517-* · 2.515-* · 2.512-benennung-umschlag · 2.501-buendelpaare ·
2.500 · 2.453-turnover · R-R8, R-R9, R-R11 ·
`Basisinfos/Voranalyse_Umschlag_Nutzung_22_09.md`
