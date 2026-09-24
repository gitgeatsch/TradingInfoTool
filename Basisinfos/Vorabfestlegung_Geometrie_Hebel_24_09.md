# Vorabfestlegung 9 — die Hebelerzeugung (N19-E über die Horizontachse)

**24.09.2026, geschrieben VOR der Messung.** Phase 2 aus
`Bauplan_Hebel_einpflanzen_24_09.md`.

**Nutzeraufträge, alle vier:**
1. *„versuche zuerst die fachlich korrekte Hypothese für die Hebelerzeugung
   anzuwenden (dynamisch, optimales Chancen-Risiko-Verhältnis)"*
2. *„Bewertungen müssen neutral sein — ohne Wirtschaftlichkeit (erst in der
   Mail); der Hebel sollte aufgrund der **Lage der Bewertungen** zur
   Hebelgröße entstehen"*
3. *„hole dir alle relevanten Infos zum Hebel"*
4. ⚠️ *„seit gestern wissen wir, dass der Hebel falsch **dimensioniert** ist
   und die Beiträge anzupassen sind — einige Punkte könnten veraltet sein"*

> ⛔⛔ **ZWEI EIGENE FASSUNGEN VERWORFEN.** Die erste wollte die Geometrie
> nach **Netto**wachstum optimieren — Verstoß gegen Regel 2 (Auftrag 2).
> Die zweite wollte die Kalibrierung von `q` als **neue** Frage stellen —
> sie ist längst diagnostiziert (Auftrag 3+4). **Beides war unnötig, weil
> die Antwort im eigenen Register steht.**

---

# § 1 ⭐⭐⭐ DIE URSACHE IST BEKANNT — und sie heißt Zielgrößenbruch

**Aus dem Stand vom 24.09. (2.557–2.567), wörtlich:**

> **`q` IST die Barrieren-Trefferquote. Die Beiträge sind aber auf
> `bewegung_r` gemessen und 1:1 übersetzt.**

Die Umrechnung `d(quote) = d(Potential)/(1+CRV)` ist algebraisch exakt —
**die Annahme steckt im Eingang.** Nachgemessen:

| | vorhergesagt | tatsächlich | Faktor |
|---|---|---|---|
| `funding` | 5,744 Pkt | **1,715** | **0,30** |
| `turnover` | 8,643 Pkt | **3,000** | **0,35** |
| `vola` | 7,968 Pkt | 7,185 | 0,90 ✔ |

➤ **Die registrierten Stufen sind 1,47× / 1,85× zu groß** — Überhang
zusammen **~3,4 Punkte**. Genau das ist der am 23.09. unabhängig gemessene
Versatz von **−3,5 bis −4,0 Pp** (2.561, 2.562): *dieselbe Zahl, zwei Wege,
achtzehn Tage auseinander.*

⚠️⚠️ **Das ist die „falsche Dimensionierung" aus Auftrag 4** — und sie ist
kein Verdacht, sondern zweifach belegt.

## 1.1 ⛔ Die Entscheidung dazu steht seit dem 06.09. und wurde nie umgesetzt

> **N19-E (Nutzerentscheidung):** *„die Stufen neu kalibrieren — direkt
> gegen die gemessene Barrieren-Quote, nicht über die Umrechnung."*

**Diese Vorabfestlegung setzt genau das um** — und erweitert es um die
Achse, die seit dem 24.09. bekannt ist: **den Horizont.**

---

# § 2 Die Hypothese

> ## **H-N19E: Die Beitragsstufen für den Hebel werden DIREKT gegen die Barrieren-Quote gemessen — über die Horizontachse — statt aus einer R-Messung übersetzt.**

**Warum das die fachlich korrekte Fassung von Auftrag 1 und 2 ist:**

| Auftrag | erfüllt durch |
|---|---|
| *„dynamisch, optimales Chance-Risiko-Verhältnis"* | `q → kelly → r → Hebel` ist der Mechanismus (`betraege.hebelrechnung`, seit 11.09.). Er ist **gebaut**; was fehlt, ist eine **gültige Eingabe** |
| *„aus der Lage der Bewertungen"* | die Stufen **sind** die Lage: Fünftel je Merkmal → `q` → `r`. Gemessen wird, wie hoch sie auf der **richtigen** Zielgröße wirklich sind |
| *„Bewertungen neutral, ohne Wirtschaftlichkeit"* | ✔ `barriere` ist **gebührenfrei** (Regel 2). Die Finanzierung erscheint nur in der Mail (§ 5) |
| *„kein Asset-Rang"* (Regel 3) | ✔ `q` ist die Wahrscheinlichkeit **dieses Trades** aus seiner Merkmalslage |

## 2.1 ⚠️⚠️ Die ehrliche Erwartung, die im Register schon steht

> **„Die Korrektur macht die Lage SCHLECHTER.** Gestutzte Stufen heißen
> ~3,4 Punkte niedrigere Quote, also **noch weiter** unter der
> Kelly-Nullstelle. **Richtig ist sie trotzdem."**

⚠️ **Das ist vorab festgehalten, damit das Ergebnis nicht als Überraschung
gedeutet wird.** Eine Messung, die das System schlechter aussehen lässt und
trotzdem richtig ist, ist kein Rückschlag — sie ist die Korrektur einer
Überschätzung, die sonst bei der Freigabe scharf geworden wäre.

## 2.2 ⭐ WAS „SCHLECHTER" KONKRET HEISST — durchgerechnet, nicht behauptet

**Nutzerfrage:** *„dein ‚Schlechter' macht mir Angst — wie und wo ist dann
die Bewertung schlechter?"*

Mit den gemessenen Faktoren (funding 0,30 · turnover 0,35) über alle
**25** Merkmalslagen gerechnet:

| | heute | nach N19-E |
|---|---|---|
| **Spreizung** (beste minus schlechteste Lage) | 0,2514 | **0,0835** — Faktor 0,33 |
| **Rangkorrelation** der 25 Lagen | — | **+0,9938** |
| Lagen mit unverändertem Rang | — | **15 von 25**, größte Verschiebung **2 Plätze** |
| **Top-3 Lagen** | — | ✔ **identisch** |
| über der Schwelle 0,060 | 3 von 25 | 0 von 25 ⛔ |
| ⭐ nach **R-R9** (Schwelle **0,0254**) | 3 von 25 | ✔ **3 von 25 — die Menge bleibt** |

> ✔ **Das System erkennt exakt dieselben Lagen als gut und lässt exakt
> dieselbe Menge durch. Nur die Zahl daneben war zu groß.**

➤ **„Schlechter" ist deshalb das falsche Wort und wird zurückgenommen.**
Richtig: **die Skala war überhöht, die Ordnung stimmt.**

⚠️ **Wo es wirklich schlechter wird: beim HEBEL.** Kelly hängt an der
**absoluten** Höhe von `q`, nicht an der Ordnung — dort war die
Überschätzung real. ✔ **Heute kostet sie nichts:** aus der Quote entsteht
0,16×, also kein Hebel.

⚠️⚠️ **R-R9 ist damit keine Nacharbeit, sondern Teil der Korrektur.** Ohne
die neue Schwelle fielen alle 25 Lagen durch — das wäre ein Artefakt der
Skala, kein Urteil über die Assets.

## 2.3 ⚠️⚠️ DIE FORM IST NICHT GESETZT — Sperre oder Regler wird MITGEMESSEN

**Nutzerhinweis:** *„du sprichst immer von Sperren, das sollte man
überdenken — es gibt Lagen, ich glaube Funding war es, wo extreme oder hohe
Werte schädlich sind, da passt es auch."*

✔ **Der Hinweis trifft, und das Register gibt ihm recht.** Für `funding` ist
die Form bereits **gemessen entschieden** (23.09.):

> *„DIE UNBEDINGTE SPERRE DES OBERSTEN RANGFÜNFTELS IST DIE RICHTIGE
> BAUFORM"* — +0,0234 R, B6 erfüllt, R-R11 reproduziert

➤ **Die Wirkung sitzt dort am Extrem, nicht im Verlauf.** Eine Sperre
bildet das ab, fünf Stufen verwässern es.

⚠️ **Deshalb wird die Form NICHT unterstellt, sondern gemessen:**

| Form | was geprüft wird |
|---|---|
| **Regler** (fünf Stufen) | ist der Verlauf über die Fünftel **monoton** (B5)? |
| **Schalter** (Sperre des Extrems) | trägt die unbedingte Sperre des obersten (oder untersten) Fünftels **mehr** als der Regler? |

⚠️⚠️ **Und die Entscheidung folgt der stehenden Regel:** ein
Zustandsschalter lohnt **nur bei UMKEHR** — nicht, wenn ein Zustand die
Wirkung bloß abschwächt. Diese Arithmetik gehört **in diese
Vorabfestlegung**, nicht in die Auswertung.

## 2.4 ⭐ Beide Vorzeichen zählen — ein negativer Beitrag ist ein Ergebnis

**Nutzerfrage:** *„wo liegen positive oder negative Beiträge?"*

`funding` trägt heute schon negative Stufen (**−0,54**, **−1,70**),
`turnover` ebenfalls (**−0,11**, **−3,06**).

➤ **Ein negativer Beitrag ist genauso wertvoll wie ein positiver:** er sagt
*„in dieser Lage KEIN Hebel"*. Die Messung weist beide Vorzeichen je
Fünftel aus — und die **Sperrform** ist nichts anderes als ein sehr großer
negativer Beitrag am Extrem.

---

# § 3 ⚠️ Was aus dem Register NICHT mehr offen ist — nicht erneut messen

| | |
|---|---|
| ⛔ **Kein ungehobener Asset-Beitrag** | 3 tragen, 9 nicht, 4 offen — und alle vier sind **Rahmen**größen oder Aktien (2.566) |
| ⛔ `vola` als Richtung | trägt keine — einziger mit geprüfter Umrechnung (N24) |
| ⛔ **CRV erhöhen** | rechtfertigt **keinen** Hebel: bei CRV 5 wäre er überall maximal, käme also aus der **Zielregel** statt aus einer Asset-Aussage (Regel 4). Zurückgenommen, 2.565 |
| ✔ **CRV global** | die Merkmalslage ändert die Geometrie nicht (Cochran Q, beide Mengen homogen) — **2.564 gilt** |
| ⛔ **Nachrichten** | System-Info fürs LLM, wirkt auf den Prompt, nicht auf `q` |
| ⛔ Grundbefund 10.08. | *„kein Verfahren schlägt die Basisrate"* |

➤ **Deshalb wird hier KEIN neuer Kandidat gesucht.** Gemessen wird die
**Höhe** der vorhandenen Stufen auf der richtigen Zielgröße.

---

# § 4 Der Messaufbau

| | |
|---|---|
| **Frageart** | `beitrag` → **selektierte Menge** (F-212) |
| ⭐ **Abgrenzung** | **NUR KRYPTO** (Nutzervorgabe). `klassen=("krypto",)` tragen die Beiträge ohnehin; die Messmenge wird zusätzlich explizit auf Krypto beschränkt und die Zahl ausgewiesen |
| **Lage** | `hebel × einstieg` → Zielgröße **`barriere`** |
| **Achse** | ⭐ **Horizont 2/3/5/10/20** — die Stufenhöhe kann horizontabhängig sein, und das ist nie geprüft |
| **Was gemessen wird** | je Merkmal und je Fünftel die **tatsächliche Verschiebung der Barrieren-Trefferquote**, in Prozentpunkten — das sind die neuen Stufen |
| **Menge** | ⚠️ **ohne das oberste OI-Fünftel** — Trichterstufe 6 sperrt es (2.576), es erreicht die Bewertung nie |
| **Kontrolle** | `zufall` — dort müssen alle Stufen null sein |
| **Positivkontrolle** | nach Norm, 5 Ziehungen |
| **Statistik** | Blockbootstrap, `messnorm._block(H)`, Band je Stufe |

## 4.1 Was mitläuft

1. **R-R11:** die alte Umrechnung wird nachgerechnet und der Faktor
   (0,30 / 0,35) reproduziert, bevor die Stufen ersetzt werden.
2. **Monotonie über die Fünftel** (B5) und **beide Historienhälften** (B6).
3. **Die Belegung je Fünftel** — eine Stufe aus zwölf Ankern ist keine.
4. ⚠️ **Der Anteil unaufgelöster Anker** je Horizont. Bei `barriere` mit
   `ungeloest=None` fallen sie heraus; steigt der Anteil bei kurzem
   Horizont stark, gilt jede Stufe nur für *„Anker, die auflösen"*.
5. ⭐ **Wo landet `q` danach** — über/unter der Kelly-Nullstelle 0,3333, je
   Lage. Das ist die Zahl, an der die Nutzervorgabe (2–5×) hängt.

---

# § 5 Die Wirtschaftlichkeit bleibt DRAUSSEN — gehört aber ausgewiesen

Die Finanzierung (0,18 %/Tag, 2.493) in Stopeinheiten: `0,0018 × H / s`

| Stop | H3 | **H20** |
|---|---|---|
| **5 %** | 0,108 | **0,720 R** |
| 8 % | 0,068 | 0,450 R |
| 20 % | 0,027 | 0,180 R |

⚠️⚠️ **Arithmetik, kein Messergebnis — und NICHT Teil der Bewertung**
(Nutzervorgabe 2). Sie gehört in die **Mail**.

**Zwei Folgerungen für später:** der Horizont geht **linear** ein (H20
kostet 6,7× so viel wie H3), und ein **enger** Stop ist beim Hebel
**teuer** (Kosten skalieren mit `1/s`). ➤ Hinweise für eine spätere
Geometriefrage, nicht für diese Messung.

---

# § 6 Die Entscheidungsregel — VOR der Messung

| Ergebnis | Entscheidung |
|---|---|
| **R-R11 fällt** | ⛔ Stopp — das Werkzeug ist das Problem |
| **Stufen belegt, monoton, beide Hälften** — und `q` kommt in mindestens einer Lage **über 0,3333** | ✔ **Der Hebel ist begründbar.** Stufen ersetzen (N19-E), danach **R-R9** (Schwelle neu), dann Betriebsprüfung |
| **Stufen belegt, aber `q` bleibt überall unter 0,3333** | ⛔ **Die Nutzervorgabe ist mit diesen Daten nicht erfüllbar.** Die Stufen werden **trotzdem** ersetzt — eine Überschätzung bleibt nicht stehen, nur weil die Korrektur unbequem ist |
| **Keine Stufe belegt**, Trennschärfe reicht | ⛔ dito, und schärfer: auf `barriere` trägt keine Merkmalslage |
| **Ein anderer Horizont trägt deutlich besser** | ⭐ **eigener Befund** — dann ist `HORIZONT_JE_LAGE` zu korrigieren, mit dieser Messung als Begründung |
| **Die SCHALTERform trägt mehr als der Regler** | ⭐ dann wird der Beitrag als **Sperre** gebaut, nicht als Stufen — ⚠️ nur bei **Umkehr**, nicht bei blosser Abschwächung |
| **Trennschärfe reicht nicht** | ⚠️ nichts entschieden — Datendecke |
| **Kontrolle `zufall` trägt** | ⛔ Lauf ungültig |

⚠️⚠️ **Wird nicht nachverhandelt.** Zeile 3 ist das **erwartete** Ergebnis
(§ 2.1) und kein Scheitern.

## 6.1 Die Vorhersage, vor dem Lauf (Methodik 2.80)

**Erwartung: die Stufen schrumpfen um Faktor ~0,3, und `q` bleibt überall
unter der Nullstelle.** Begründung: der Faktor ist zweifach gemessen
(0,30 / 0,35), der Überhang beträgt ~3,4 Punkte, und B0 hat auf
`barriere`/H3 keine tragende Wirkung gefunden.

**Gegenthese:** auf einem **anderen** Horizont als H3 sind die Stufen
größer — die Horizontachse wurde bei den Beiträgen **nie** durchgemessen.

---

# § 7 Was diese Messung **nicht** entscheidet

- **Nicht** die Geometrie (Stop, CRV, Horizont als Vorgabe) — § 5.
- **Nicht**, ob ein **neuer** Beitrag existiert — § 3, abgeschlossen.
- **Nicht** die Zielzone 2–5×. Sie ist eine **Vorgabe**, kein Messergebnis.
- **Nicht**, ob M1 ohne Hebel definierbar ist — Frage an den Meilenstein.
