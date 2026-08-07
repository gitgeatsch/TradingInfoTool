"""Prueft Themen-Bruecken und Asset-Steckbrief (07.08.2026).

BEIDE kommen aus einer Nutzer-Vorgabe, und beide haben eine gemeinsame Regel:
**Luecken sind erlaubt.** Nicht jede Kategorie hat eine Bruecke, nicht jedes
Symbol einen vollstaendigen Steckbrief - fehlende Angaben fallen weg statt
geraten zu werden. Ein erfundener Steckbrief waere schlechter als ein knapper.

THEMEN-BRUECKEN: die Hauptgruppen sind nach INSTRUMENTENTYP geschnitten, ein
Thema laeuft quer dazu. "Kupfer ist interessant" betrifft das Material
(industriemetalle:kupfer) UND die Minenbetreiber (aktien_sektoren:grundstoffe).
Der Nutzer entscheidet dann, ob er die riskantere Aktie oder den breiteren ETF
nimmt - eine automatische Bewertung ist ausdruecklich NICHT gewollt.

STECKBRIEF: "welches Asset und was macht das Asset - vor allem bei ETF
relevant". Ohne neue Datenquelle: Name + Bitpanda-`group` (Instrumententyp) +
Kategorie ergeben zusammen die Antwort.
"""
import config

fehler = []
def pruefe(name, ok, info=""):
    print(("  OK   " if ok else "  FEHL ") + name + ("  " + info if info else ""))
    if not ok:
        fehler.append(name)

print("A) THEMEN-BRUECKEN")
bruecken = config.themen_bruecken()
pruefe("A1 Bruecken geladen", len(bruecken) >= 5, f"{len(bruecken)} Stueck")

kupfer_verwandt = config.verwandte_kategorien("industriemetalle", "kupfer")
pruefe("A2 Kupfer-Material findet die Miner",
       ("aktien_sektoren", "grundstoffe") in kupfer_verwandt, str(kupfer_verwandt))

grundstoffe = config.verwandte_kategorien("aktien_sektoren", "grundstoffe")
pruefe("A3 Rueckrichtung funktioniert",
       ("industriemetalle", "kupfer") in grundstoffe, str(grundstoffe))

pruefe("A4 sich selbst nie in der Liste",
       ("industriemetalle", "kupfer") not in kupfer_verwandt)

pruefe("A5 ohne Bruecke leere Liste (kein Fehler)",
       config.verwandte_kategorien("anleihen_geldmarkt") == [])
pruefe("A6 unbekannte Kategorie ohne Absturz",
       config.verwandte_kategorien("gibtesnicht", "auchnicht") == [])
pruefe("A7 None ohne Absturz", config.verwandte_kategorien(None) == [])

# Eine Bruecke, die eine GANZE Hauptgruppe nennt, muss jede Unterkategorie treffen
edel = config.verwandte_kategorien("edelmetalle", "gold")
pruefe("A8 Hauptgruppen-Bruecke greift fuer jede Unterkategorie",
       ("aktien_sektoren", "grundstoffe") in edel, str(edel))

pruefe("A9 Thema wird benannt",
       config.bruecken_name_fuer("industriemetalle", "kupfer") == "Kupfer")
pruefe("A10 ohne Bruecke kein Thema",
       config.bruecken_name_fuer("anleihen_geldmarkt") is None)

print("\nB) ASSET-STECKBRIEF")
etf = config.asset_steckbrief("COPPERMINE", "Copper Miners", "etf",
                              "industriemetalle", "kupfer", True)
pruefe("B1 ETF: Typ und Streuung erkennbar",
       "ETF" in etf and "Korb" in etf, etf)
pruefe("B2 ETF: Themenfeld genannt", "Kupfer" in etf)

aktie = config.asset_steckbrief("PLTR", "Palantir", "stock",
                                "technologie_ki", "ki", True)
pruefe("B3 Aktie wird als Einzelaktie erkannt", "Einzelaktie" in aktie, aktie)

etc = config.asset_steckbrief("OD7C", "WisdomTree Copper", "etc",
                              "industriemetalle", "kupfer", True)
pruefe("B4 ETC vom ETF unterschieden",
       "ETC" in etc and "Zertifikat" in etc, etc)

nicht_handelbar = config.asset_steckbrief("ABCDE", "Irgendwas", "etf", None, None, False)
pruefe("B5 nicht handelbar wird benannt",
       "NICHT handelbar" in nicht_handelbar, nicht_handelbar)

leer = config.asset_steckbrief("XYZ")
pruefe("B6 ohne jede Zusatzangabe nur das Symbol", leer == "XYZ", leer)

luecke = config.asset_steckbrief("NEUXY", "Neues Produkt", "etf", None, None, None)
pruefe("B7 Luecke: Kategorie fehlt, Rest bleibt",
       "ETF" in luecke and "Thema" not in luecke, luecke)
pruefe("B8 nichts wird geraten", "Kupfer" not in luecke and "None" not in luecke)

unbekannter_typ = config.asset_steckbrief("ZZZ", "Test", "voellig_neu", None, None, True)
pruefe("B9 unbekannter Instrumententyp faellt weg statt zu raten",
       "voellig_neu" not in unbekannter_typ, unbekannter_typ)

print("\nC) ZUSAMMENSPIEL - der Fall aus der Nutzer-Frage")
# "Kupfer interessant" -> was bekomme ich zu sehen?
print(f"    Material: {config.asset_steckbrief('OD7C','WisdomTree Copper','etc','industriemetalle','kupfer',True)}")
for h, u in config.verwandte_kategorien("industriemetalle", "kupfer"):
    print(f"    verwandt: {config._kategorie_klartext(h, u)}")
pruefe("C1 Material und Miner erscheinen zusammen",
       len(config.verwandte_kategorien("industriemetalle", "kupfer")) >= 1)

print("\n" + ("ALLE TESTS BESTANDEN" if not fehler else f"FEHLER: {fehler}"))
