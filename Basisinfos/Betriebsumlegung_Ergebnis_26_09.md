# Die Umlegung auf den Echtbetrieb — und warum „Rangfolge" der falsche Ansatz war

**26.09.2026** · Befunde 2.608, 2.609, 2.610 · `messe_betrieb_umlegung.py`

Nutzerauftrag: *„dann simulation auf unser System — Watchlist mit Hebel
umlegen, Echtbetrieb hier sind es nicht 116 Symbole und zusätzlich den
aktuellen Abdeckungsgrad auf die Bewertungen der Assets (haben alle Assets
die Bewertung die wir benötigen?)."*

---

## ⭐⭐⭐ Die Nutzerkorrektur, die den Befund gerettet hat

Ich hatte die Umlegung zuerst als **Perzentil** gebaut — „nimm das
schärfste 1 % je Stunde". Der Nutzer hat das gekippt:

> *„Warum sprichst du von Rangfolge? Das System muss auch bei nur ‚Einem'
> Asset funktionieren und nicht besser oder schlechter durch die Watchlist
> werden?!?!"*

⚠️⚠️ **Der Einwand ist fachlich zwingend und ich hatte ihn übersehen.**
Ein Perzentil ist eine Aussage über die **Menge**, keine über das **Asset**.
Dieselbe Lage desselben Assets bekommt bei 116 Symbolen ein anderes Urteil
als bei 28 — obwohl sich am Asset nichts geändert hat. Damit hängt jedes
Signal an der Zusammensetzung der Watchlist, und die ist keine Messgröße,
sondern eine Betriebsentscheidung.

⚠️ Das ist genau der Fehler, vor dem die registrierte Regel
**„Die Grundgesamtheit ist keine Stellschraube"** warnt — nur diesmal in
der Anwendung statt in der Messung.

➤ **Die Bewertung ist eine ABSOLUTE Schwelle in ATR.** `ema_abstand_atr`
misst, wie weit der Kurs über seinem 48-Stunden-EMA steht, **in Einheiten
der eigenen Volatilität**. Diese Zahl ist bereits normiert — sie braucht
keinen Vergleich mit anderen Assets, um interpretierbar zu sein.

---

## Der Befund: die absolute Schwelle trägt, und sie ist dosierbar

Gemessen auf den **15 liquiden Watchlist-Symbolen**, 404.642 Anker,
1.746 Tage, Trailing 1,0 ATR, Horizont 72 h:

| Schwelle | Signale/Tag | MFE/MAE | `E[R]` | ±Tagesfehler | Urteil |
|---|---|---|---|---|---|
| 0,30 ATR | 52,1 | 1,25 | +0,0557 | ±0,0183 | ✔ signifikant |
| 0,50 ATR | 25,3 | 1,37 | +0,0842 | ±0,0202 | ✔ signifikant |
| 0,70 ATR | 10,4 | 1,53 | +0,1289 | ±0,0257 | ✔ signifikant |
| 0,90 ATR | 3,6 | 1,65 | +0,1701 | ±0,0325 | ✔ signifikant |
| **1,00 ATR** | **2,0** | **1,75** | **+0,2079** | ±0,0386 | ✔ signifikant |
| 1,20 ATR | 0,54 | 2,04 | +0,2957 | ±0,0645 | ✔ signifikant |

⭐ **Monoton und dosierbar.** Je höher die Schwelle, desto seltener das
Signal und desto größer der Erwartungswert — das ist genau die
Hebelstufung, die der Nutzer gesucht hat: *„GUTE Lagesignale & hohe kurze
Anstiege sind eher selten bzw. können nach unten skalieren (kleinerer
Hebel, das wäre die Abstufung)."*

**Verteilung von `ema_abstand_atr`** (wo die Schwellen liegen):

| Perzentil | 50 % | 90 % | 99 % | Maximum |
|---|---|---|---|---|
| Wert | −0,01 | 0,52 | 0,98 | 1,32 |

➤ Die Schwelle 1,00 entspricht grob dem 99. Perzentil — aber sie ist
**nicht** als solches definiert, sondern als absolute Größe. Bei einer
anderen Watchlist verschiebt sich das Perzentil, die Schwelle nicht.

---

## ⛔⛔ Der Median ist NEGATIV — und das ist die eigentliche Hebelfrage

Beim Nachprüfen der Ausreißerfrage (Nutzerhinweis, siehe unten) fiel
etwas auf, das nicht die jungen Assets betrifft, sondern **die ganze
Strategie**:

| Alter | Signale | Mittel | **MEDIAN** | getrimmt (5/95) | ohne Top 5 | Top-1-Anteil |
|---|---|---|---|---|---|---|
| 10–30 Tage | 271 | +0,4182 | **+0,1811** | +0,3176 | +0,3554 | 3,4 % |
| 1–3 Monate | 633 | +0,0320 | −0,2040 | −0,0689 | −0,0029 | ⛔ **27,4 %** |
| 3–12 Monate | 3.737 | +0,0451 | −0,1914 | −0,0533 | +0,0351 | 5,6 % |
| über 1 Jahr | 16.059 | +0,1467 | **−0,1885** | +0,0265 | +0,1423 | 0,9 % |

**Verteilung der Einzeltrades:**

| Alter | R ≤ −0,9 | R < 0 | R > +1 | R > +3 |
|---|---|---|---|---|
| 10–30 Tage | 3,3 % | **43,9 %** | **25,1 %** | 4,4 % |
| 1–3 Monate | 9,3 % | 59,6 % | 13,6 % | 1,6 % |
| 3–12 Monate | 8,6 % | 58,4 % | 13,4 % | 1,3 % |
| über 1 Jahr | 9,0 % | 57,3 % | 18,1 % | 2,5 % |

⚠️⚠️ **Der Erwartungswert +0,1467 R entsteht aus wenigen großen Gewinnern
gegen eine Mehrheit kleiner Verluste.** Getrimmt bleiben +0,0265. Das ist
die typische Trailing-Signatur und kein Fehler — aber es ist
**hebelrelevant**: eine schiefe Verteilung verträgt deutlich weniger
Hebel als ein symmetrischer Erwartungswert derselben Höhe, weil die
Verlustserien lang werden und der geometrische Ertrag unter dem
arithmetischen liegt.

➤ **Vor jeder Festlegung einer Hebelhöhe ist das zu messen** — die
Schiefe, die längste Verlustserie und der geometrische gegen den
arithmetischen Ertrag. Offener Punkt, in „Was NICHT folgt" aufgenommen.

---

## ⭐⭐ Die Historienfrage — sie gehört in die WATCHLIST, nicht in den Hebel

> **Nutzereinordnung 26.09.:** *„Das wäre eher ein Watchlist Thema als
> ein Hebelthema."*

✔ **Richtig, und das ordnet den folgenden Abschnitt neu ein.** Die Frage
*„funktioniert die Bewertung bei einem drei Monate alten Asset"*
entscheidet, **welche Assets überhaupt aufgenommen werden** — also
Beschaffung und Aufnahmebedingung. Der Hebel-Arm beantwortet eine andere
Frage: **wie groß die Position ist, wenn ein Signal vorliegt.**

➤ Die Alterszerlegung ist damit **kein Hebelbefund**, sondern eine
**Aufnahmebedingung für die Watchlist**. Sie steht hier, weil sie beim
Abdeckungsgrad anfiel — sie gehört inhaltlich in den Watchlist-Arm.

### Die Ausreißerfrage — der Nutzerhinweis trifft zu, teilweise

> **Nutzerhinweis 26.09.:** *„junge Assets haben massives Potential nach
> oben (und dann nach unten) — das sind aber Einzelfälle und massive
> Ausreisser in extremen."*

| Gruppe | Urteil |
|---|---|
| **1–3 Monate** | ⛔ **Hinweis bestätigt.** Ein einziges Signal trägt **27,4 %** der Summe; ohne die Top 5 fällt die Gruppe auf −0,0029. Der Wert +0,0320 ist **wertlos** |
| **10–30 Tage** | ⚠️ hält der Prüfung stand: Median **+0,1811** (einzige positive Gruppe), getrimmt +0,3176, ohne Top 5 +0,3554, größtes Signal nur 3,4 %. **Aber 271 Signale** — das belegt wenig |

⚠️ Der Befund „jung trägt" steht damit **nur** für 10–30 Tage und auch
dort auf dünner Menge. Für 1–3 Monate ist er **zurückgezogen**.

Nutzerfrage: *„Das System sollte auch bei einem Asset funktionieren, das
vor drei Monaten auf den Markt eingeführt wurde und aktuelle Daten hat —
warum sollte hier die Historie relevant sein?"*

### Was die Bewertung technisch braucht (davon unberührt)

| Bestandteil | Bedarf | Begründung |
|---|---|---|
| EMA über 48 h | 240 Stunden | 5× die Periode, bis das Einschwingen unter 1e-5 fällt |
| ATR über 24 h | 24 Stunden | in den 240 enthalten |
| **Summe** | **240 Stunden = 10 Tage** | |

⭐ **Ein Asset mit drei Monaten Historie hat 2.160 Stunden — das
Neunfache des Nötigen.** Die lange Historie ist für die **MESSUNG**
erforderlich (um den Befund statistisch abzusichern), nicht für die
**ANWENDUNG**.

⚠️ Ich hatte „hat keine Kurse in der Messbasis" mit „hat zu wenig
Historie" verwechselt. Das sind zwei verschiedene Dinge, und nur das
erste war wahr.

### Gemessen: `E[R]` nach Alter seit dem ersten Kurs

Schwelle 1,0 ATR, Trailing 1,0 ATR, H = 72 h:

| Alter seit Listung | Anker | Signale | `E[R]` | ±Fehler | Urteil |
|---|---|---|---|---|---|
| **10–30 Tage** | 55.680 | 271 | **+0,4182** | ±0,1218 | ✔ über Band · **signifikant** |
| 1–3 Monate | 167.040 | 633 | +0,0320 | ±0,0634 | ✔ über Band · n.s. |
| 3–6 Monate | 250.560 | 1.164 | +0,0521 | ±0,0452 | ✔ über Band · n.s. |
| 6–12 Monate | 514.208 | 2.573 | +0,0419 | ±0,0345 | ✔ über Band · n.s. |
| über 1 Jahr | 2.220.506 | 16.059 | +0,1467 | ±0,0250 | ✔ über Band · **signifikant** |

✔✔ **Kein Fenster liegt im Nullband.** Die Bewertung funktioniert auf
Assets, die seit 10 Tagen Kurse haben.

⚠️⚠️ **Zwei Einschränkungen, die dazugehören:**

| # | |
|---|---|
| **1** | 271 Signale sind wenig, das Band ist breit (±0,1218). **„Trägt auch jung" ist belegt, „trägt jung BESSER" nicht** — der Unterschied zu +0,1467 ist vom Fehler gedeckt |
| **2** | Die mittleren drei Gruppen sind **nicht signifikant**. Sie liegen über dem Band, aber der Tagesfehler deckt sie — sie belegen nichts für sich allein |

⚠️ Und ein Überlebenseffekt bleibt: gemessen wurden nur Assets, die es
bis in die Messbasis geschafft haben. Ein Coin, der nach sechs Wochen
verschwand, ist nicht dabei.

---

## ⛔ Die Abdeckungslücke — und dass sie KEIN Historienproblem ist

`asset_hebel_settings` hat **43 freigegebene Symbole**:

| Stufe | Anzahl | Anteil |
|---|---|---|
| freigegeben | 43 | 100 % |
| davon mit Stundenkursen | 28 | **65 %** |
| davon über 100.000 USD/Stunde | **15** | **35 %** |

**Die 15 liquiden:** BTC, ETH, SOL, BNB, SUI, NEAR, LINK, AVAX, XLM,
TAO, ONDO, INJ, APT, VIRTUAL, RENDER

### Die 15 ohne Stundenkurse — nach Ursache

| Gruppe | Symbole | Ursache | Lösbar? |
|---|---|---|---|
| **1** | ASTER, FLOKI, HYPE, PLUME, XNO | bei Binance **Spot** handelbar — nur nie geholt | ✔ **sofort** |
| **2** | AKT, BRETT, GRIFFAIN, KAS | bei Binance **Futures** (stehen im Terminmarkt!), aber der Lader prüft **Spot** | ✔ **Konstruktionsfehler** |
| **3** | AIOZ, CANTON, CAT, MON, SUPRA, VSN | gar nicht bei Binance | ⚠️ andere Quelle nötig |

⚠️⚠️ **Gruppe 2 ist ein Fehler im Lader.** `hole_stundenkurse.py` leitet
seine Symbolliste aus dem **Terminmarkt** ab (Binance Futures), prüft die
Handelbarkeit dann aber gegen `api.binance.com` — die **Spot**-Börse.
Symbole, die es nur als Perpetual gibt, fallen dadurch heraus, obwohl
ihre Kurse über `fapi.binance.com` verfügbar wären.

➤ **9 von 15 wären beschaffbar** — die Abdeckung stiege von 65 % auf
**86 %**.

### ⭐⭐ Die Lücke trifft nicht nur die Watchlist — sie trifft offene Positionen

Die Prüfsuite meldet am selben Tag drei rote Zeilen im Paket
`Neuaufnahme`:

```
FEHL  ⚠️⚠️ jede GEHALTENE Position hat eine Messreihe
      ASTER ist GEHALTEN, hat aber keine Messreihe (rolle=taktisch)
      CANTON ist GEHALTEN, hat aber keine Messreihe (rolle=core)
      MON ist GEHALTEN, hat aber keine Messreihe (rolle=taktisch)
FEHL  ⚠️⚠️ kein KERNWERT ohne jeden Beitrag
      KERNWERTE ohne jeden Beitrag: CANTON
```

⚠️⚠️ **ASTER, CANTON und MON sind genau drei der 15.** Das sind keine
Watchlist-Kandidaten, sondern **offene Positionen** — die Kette kann sie
weder nachkaufen noch verkaufen. CANTON fällt als `core` ein zweites Mal
auf.

➤ **ASTER liegt in Gruppe 1** und wäre sofort beschaffbar. Damit ist die
Beschaffungslücke kein reines Watchlist-Thema, sondern betrifft
laufendes Kapital.

✔ **Keines der 15 fehlt wegen zu kurzer Historie.** Die Lücke ist
vollständig ein **Beschaffungsproblem**.

---

---

## ⛔⛔⛔ Die eigentliche Ursache: vier Symbolwelten ohne Brücke

> **Nutzerbefund 26.09.:** *„Es müssen Bitpanda Symbole mit den
> Datenquellen — binance, Coingecko etc sauber zusammengeführt werden
> sonst können wir auch keine neuen Assets ohne probleme aufnehmen."*

⚠️⚠️ **Und dieser Befund korrigiert meine eigene Diagnose oben.** Ich
hatte „hat keine Stundenkurse" als „hat keine Daten" gelesen. Richtig
ist: **13 der 15 haben Tagesdaten**, teils über 1.900 Punkte. Sie fehlen
nicht — sie liegen in der **falschen Auflösung** und unter einer anderen
Symbolwelt.

### Die vier Welten

| # | Welt | Schlüssel | Zuordnung |
|---|---|---|---|
| **1** | **Bitpanda** | `ASTER`, `CANTON`, `VSN` | der Bestand — `holdings`, `asset_hebel_settings` |
| **2** | **CoinGecko** | `aster-2`, `canton-network`, `vision-3` | ✔ 74 %, aber über **drei Tabellen verstreut**, kein Stammsatz |
| **3** | **Binance Spot** | `ASTERUSDT` | ⛔ **keine Zuordnung** — nur Namensgleichheit |
| **4** | **Binance Futures** | Terminmarkt | ⛔ **keine Zuordnung** |

⚠️⚠️ **Dass Namensgleichheit nicht genügt, beweisen die IDs selbst.**
CoinGecko musste `aster-2` und `vision-3` durchnummerieren, weil es
**mehrere Coins mit demselben Ticker** gibt. Dieselbe Mehrdeutigkeit
besteht bei Binance — und dort wird sie über den blanken Symbolnamen
aufgelöst, also **gar nicht**.

`asset_hebel_settings` hat genau zwei Spalten: `symbol`,
`hebel_pruefung_erlaubt`. **Kein Stammsatz, keine Quellen-IDs.**

### Die Lage über alle 57 relevanten Symbole

(gehalten mit `quantity > 0` oder in der Hebel-Watchlist)

| | Anzahl | Anteil |
|---|---|---|
| CoinGecko-ID hinterlegt | 42 | 74 % |
| Tageskurse (`price_history_ohlc`) | 47 | 82 % |
| **Stundenkurse — was der Hebel braucht** | **28** | **49 %** |

⛔ **Ohne jede Kursquelle:** 3QSS, CANTON, DBPK, EURCV, OD7C, OD7H,
OD7L, OD7N, VSN, X136

### Zwei Einzelfälle, die das Muster zeigen

| Symbol | Lage |
|---|---|
| **CANTON** | gehalten, als `core` geführt, CoinGecko-ID `canton-network` **ist hinterlegt** — und trotzdem **null Kursdaten in jeder Quelle**. ➤ Die Brücke existiert und wird nicht befahren |
| **XNO** | 1.665 Tageskurse vorhanden, aber **keine CoinGecko-ID** im Cache. ➤ Es kam über einen anderen Weg herein, und welcher, steht nirgends |

### Was daraus folgt

➤ **Ein Stammsatz je Asset mit den IDs aller Quellen ist die
Voraussetzung für jede Neuaufnahme.** Solange er fehlt, entscheidet
Namensgleichheit darüber, ob ein Asset Daten bekommt — und sie
entscheidet **still**: kein Fehler, kein Log, das Symbol fällt einfach
aus der Ladeliste.

⛔ **Nicht behoben, nur gemessen.** Der Umbau ist ein eigenes Paket und
braucht eine Voranalyse.

---

## Was daraus folgt

| # | |
|---|---|
| **1** | Die Bewertung ist eine **absolute Schwelle in ATR**, kein Perzentil. Sie funktioniert bei einem Asset genauso wie bei 116 |
| **2** | Sie braucht **10 Tage Historie**, nicht Jahre |
| **3** | Die Abdeckungslücke ist **Beschaffung**, nicht Datenlage — und 9 von 15 sind lösbar |
| **4** | Die Schwelle ist die **Hebelstufung**: 0,3 ATR → klein und häufig, 1,2 ATR → groß und selten |

## Was NICHT folgt

| # | |
|---|---|
| **1** | **Gebühren und Finanzierung** bleiben nach Regel 2 draußen. Ob +0,2079 R sie trägt, ist ungeprüft |
| **2** | Die **Ausführbarkeit** ist ungeprüft — Slippage bei 2 Signalen/Tag auf 15 Symbolen |
| **3** | Die **Hebelhöhe in Zahlen** ist nicht gemessen — die Schwelle liefert eine Ordnung, keine Kelly-Größe. ⛔⛔ Und sie darf **nicht** aus `E[R]` allein folgen: der **Median ist negativ**, die Verteilung schief. Zu messen sind Schiefe, längste Verlustserie und der **geometrische** gegen den arithmetischen Ertrag |
| **4** | Der Einstieg ist **nicht verdrahtet** — es gibt kein Signal im Betrieb |
| **5** | „Jung trägt besser" ist **nicht** belegt — nur „jung trägt auch", und das **nur für 10–30 Tage**. Die Gruppe 1–3 Monate ist **zurückgezogen** (ein Signal trägt 27,4 % der Summe) |
| **6** | Die Alterszerlegung ist ein **Watchlist-Thema**, kein Hebelbefund — sie sagt, welche Assets aufgenommen werden können, nicht wie groß die Position wird |
| **7** | ⛔ **Short ruht** — alles hier ist LONG |
