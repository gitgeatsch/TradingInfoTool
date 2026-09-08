# REGISTER — DIE WERKZEUGE (Altbestand gegen Neubestand)

*Erzeugt aus `bestand.py` durch **Scan**, nicht gepflegt — 281 Eintraege von Hand zu fuehren waere dieselbe Falle noch einmal.*

⚠️ **Getrennt wird nach METHODIKSTAND, nicht nach Datum.** 178 von 384 Dateien wurden in 14 Tagen angefasst, die meisten nur vom N-19-Fix (Krypto-Filter, 44 Skripte). Das Datum sagt nichts darueber, ob ein Werkzeug der Norm genuegt.

| Stufe | Anzahl | Anteil | Bedeutung |
|---|---|---|---|
| **NORM** | 21 | 7 % | ruft `messnorm` - der aktuelle Stand, Trennschaerfe Pflicht |
| **TAGESKLAMMER** | 27 | 9 % | Tagesklammer und Band, aber keine Trennschaerfe-Pflicht |
| **BLOCK** | 81 | 27 % | eigener Blockbootstrap, ausserhalb der Norm |
| **ALTBESTAND** | 174 | 57 % | weder Norm noch Tagesklammer - Befunde nur mit Vorbehalt |

> ⚠️ **174 von 303 Werkzeugen (57 %) sind Altbestand.** Ein Befund aus dieser Gruppe gilt nur mit Vorbehalt — er hat weder Tagesklammer noch Trennschaerfe.

## Die Regel fuer neue Arbeit

    NEUE Messung        ruft `messnorm` oder `messnorm_rand`
    BESTEHENDE Messung  bleibt, wird aber nicht als Beleg fuer
                        einen NEUEN Befund herangezogen, ohne
                        vorher unter die Norm gestellt zu werden
                        (R-R11: erst reproduzieren)

## NORM (21)

    messe_alle_kandidaten.py, messnorm_auswahl.py, messnorm_rand.py, pruefe_audit_06_07_09.py
    pruefe_datengrundlage.py, pruefe_messbasis_wechsel.py, pruefe_n1_mehrfachmischung.py, pruefe_n1_rangtest.py
    pruefe_n1_schichtung_gegen_partner.py, pruefe_n1_vorbedingungen.py, pruefe_n5_haelften_saaten.py, pruefe_n5_mengenkontrolle.py
    pruefe_n5_modi.py, pruefe_nullschwelle.py, pruefe_o4_stufenband.py, pruefe_pakete.py
    pruefe_schichtentest_spiegelung.py, schritt3_gegenpruefung.py, schritt3_trennschaerfe.py, schritt4a_gegenpruefung.py
    schritt4a_matched.py

## TAGESKLAMMER (27)

    messe_ausstiegsbeitrag.py, messe_beitragssumme.py, messe_bewertungskennzahl.py, messe_form_kurz_gegen_lang.py
    messe_funding_niveau.py, messe_h_als_regel.py, messe_kandidaten_als_regel.py, messe_kandidaten_kombination.py
    messe_momentum_12_1.py, messe_regel_wirksamkeit.py, messe_schwelle_quotengleich.py, messe_sperre_kombi_h20.py
    messe_umkehr_je_turnover.py, messe_volumenanteil.py, messnorm.py, pruefe_funding_befund.py
    pruefe_funding_marktphase.py, pruefe_funding_survivorship.py, pruefe_funding_wirksamkeit.py, pruefe_mctvl_befund.py
    pruefe_momentum_trennschaerfe.py, pruefe_n31_tagesklammer.py, pruefe_regel_trennschaerfe.py, pruefe_schwelle_gegenpruefung.py
    pruefe_turnover_befund.py, pruefe_turnover_und_kombination.py, rechne_sperren_zusammen.py

## BLOCK (81)

    messe_abstand_zum_zufall.py, messe_akkumulation_az4.py, messe_akkumulationsmass.py, messe_alle_groessen_neu.py
    messe_allocator_gegen_zufall.py, messe_alltagsmarkt.py, messe_asset_anteil_und_relativform.py, messe_ausstieg.py
    messe_auswahl_kriterium.py, messe_beitrag_auf_auswahl.py, messe_bewertung_kalibrierung.py, messe_datenqualitaet.py
    messe_drift_wiederholung.py, messe_einordnung_wirkung.py, messe_form_und_nullpunktkurve.py, messe_fremdgroesse.py
    messe_fuenftel_mit_tagesklammer.py, messe_g_trefferbilanz.py, messe_h_als_filter.py, messe_h_als_marktmerkmal.py
    messe_h_anteil_vorlauf.py, messe_h_je_asset.py, messe_h_produktionsgeometrie.py, messe_halte_kriterium.py
    messe_horizont_aus_stop.py, messe_kalibrierung_je_datenlage.py, messe_kandidaten_je_horizont.py, messe_kettennaht_eingriffe.py
    messe_konfidenz_kalibrierung_neu.py, messe_planungshorizont.py, messe_querschnitt_umkehr.py, messe_rand_je_schicht.py
    messe_rangschichtung.py, messe_rangverfall.py, messe_rascher_anstieg.py, messe_regimephasen_llm.py
    messe_sentiment_je_horizont.py, messe_short_und_einbruch.py, messe_stop_abstand_baender.py, messe_stopquelle.py
    messe_stufen_aus_quote.py, messe_tagewahl_je_eigenschaft.py, messe_top_fakten.py, messe_umbau_wirkung.py
    messe_zeitschranke.py, messe_zellen_ausgang.py, messe_zielregel.py, pruefe_alltagsmarkt.py
    pruefe_amihud_handelbarkeit.py, pruefe_analogie_gross.py, pruefe_auswahl_produktion.py, pruefe_auswahl_schaedlich.py
    pruefe_beitragszahl_sickert.py, pruefe_filter_am_befund.py, pruefe_filter_trennschaerfe.py, pruefe_funding_je_reihe.py
    pruefe_gefallen_randpotential.py, pruefe_h_tageseffekt.py, pruefe_horizont_dimensionierung.py, pruefe_kandidaten_abdeckung_stabilitaet.py
    pruefe_kandidaten_untereinander.py, pruefe_konsistenz_06_09.py, pruefe_n8_gegenpruefung.py, pruefe_ohne_widerstand.py
    pruefe_persistenz_und_nullpunkt.py, pruefe_rangzugehoerigkeit.py, pruefe_regel_je_marktphase.py, pruefe_steigung_invarianz.py
    pruefe_strukturstop.py, pruefe_stufen_gegen_quote.py, pruefe_stufen_stabilitaet.py, pruefe_trailing_je_instrument.py
    pruefe_turnover_weglassen.py, pruefe_veraenderungsformen_unabhaengig.py, pruefe_vola_unabhaengig.py, pruefe_vola_zeitpunkt_oder_asset.py
    pruefe_zielregel_befund.py, pruefe_zielregel_robust.py, pruefe_zielweite.py, rechne_nullpunkte_feiner.py
    simuliere_staffelung.py

## ALTBESTAND (174)

    messe_abgleich_alt_neu.py, messe_akkumulation.py, messe_akkumulation_phasen.py, messe_alter_vs_zeit.py
    messe_anlass.py, messe_anreicherung.py, messe_auswahl.py, messe_auswahl_historie.py
    messe_b2_unabhaengigkeit.py, messe_basislinie.py, messe_basislinie_aufloesung.py, messe_begruendungen.py
    messe_betragsdeckel.py, messe_bodenabstand.py, messe_degradierung.py, messe_dimensionierung.py
    messe_dosis.py, messe_dosis_sauber.py, messe_drift.py, messe_drift_absolut.py
    messe_drift_zerlegt.py, messe_dritter_faktor.py, messe_eigenschaft_beitrag.py, messe_entwickleraktivitaet.py
    messe_faktorzahl.py, messe_fensterlaenge_selbstjustierung.py, messe_filterschaden.py, messe_geometrie.py
    messe_h3_totzone_und_kombination.py, messe_h_je_zeitabschnitt.py, messe_h_lagenregel.py, messe_h_neu.py
    messe_halten_ursache.py, messe_halten_ursache2.py, messe_halten_ursache3.py, messe_kandidaten_redundanz.py
    messe_kat_alter.py, messe_kategorie_und_horizont.py, messe_klassen.py, messe_kollinearitaet.py
    messe_kombi_gegen_f165_bar.py, messe_konjunktion.py, messe_konjunktion_positivkontrolle.py, messe_konstellationen.py
    messe_kostenhebel.py, messe_lage_beitrag.py, messe_liquiditaet.py, messe_llm1_positionsbias.py
    messe_llm_gegen_regel.py, messe_marken.py, messe_marktphasen.py, messe_n7_kette.py
    messe_n7_kette_korrigiert.py, messe_namensanker.py, messe_phase_invers.py, messe_prompt_nebeneffekte.py
    messe_prompt_verbesserungen.py, messe_regime_empfindlichkeit.py, messe_regimeflag_sauber.py, messe_regimewechsel_trockenlauf.py
    messe_reifeband.py, messe_reihung_x_h.py, messe_schnittabstand_beitrag.py, messe_schwelle_h2_kalibrierung.py
    messe_schwelle_kalibrierung.py, messe_signalbilanz.py, messe_spiegel.py, messe_struktur_bereinigt.py
    messe_strukturstop.py, messe_summe_gegen_mittel.py, messe_szenario_stufe1.py, messe_tagewahl_je_symbol.py
    messe_trichter_treffer.py, messe_ueberleben.py, messe_umschlag_kontext.py, messe_verkaufsseite.py
    messe_wann.py, messe_zai_ohne_regime.py, messe_zeitteilung.py, messe_zerlegung.py
    pruefe_abdeckung.py, pruefe_abdeckung_watchlist.py, pruefe_aktionsvokabular.py, pruefe_analogie.py
    pruefe_assetdaten.py, pruefe_assetklassen_datenlage.py, pruefe_assetklassen_trennung.py, pruefe_aufruf_signaturen.py
    pruefe_ausrollbarkeit.py, pruefe_ausrollen.py, pruefe_ausschuss_suche.py, pruefe_auswertbarkeit.py
    pruefe_beitragsabdeckung.py, pruefe_belege_gegen_fakten.py, pruefe_bruchschwelle.py, pruefe_btc_abflachung.py
    pruefe_coingecko_stand.py, pruefe_coinmetrics_umfang.py, pruefe_cooldown_nachgestellt.py, pruefe_cooldown_wirkung.py
    pruefe_crv_positionsgroesse.py, pruefe_datenqualitaet.py, pruefe_defillama_historie.py, pruefe_einstiegsnachweis.py
    pruefe_export_standard.py, pruefe_export_vollcheck.py, pruefe_fakten_bezugsgroessen.py, pruefe_fakten_rollout.py
    pruefe_funding_historie.py, pruefe_funding_monoton.py, pruefe_fx_ableitung.py, pruefe_gegenpruefung_trefferquote.py
    pruefe_gemini_verhalten.py, pruefe_h_kette_von_grund_auf.py, pruefe_h_original_reproduziert.py, pruefe_instrument_verzweigungen.py
    pruefe_kalibrierung_trocken.py, pruefe_kette_horizonte.py, pruefe_kette_je_asset.py, pruefe_konjunktion_befund.py
    pruefe_llm_stabilitaet.py, pruefe_makro_bestand.py, pruefe_marktlage.py, pruefe_marktrang.py
    pruefe_massstab_unterschied.py, pruefe_messwerkzeug_bodenabstand.py, pruefe_messwerkzeug_h3.py, pruefe_messwerkzeug_h_neu.py
    pruefe_messwerkzeug_h_produktion.py, pruefe_n8_live_abdeckung.py, pruefe_n8_schwelle_je_datenlage.py, pruefe_n8_schwellenarithmetik.py
    pruefe_nachweis_grundmenge.py, pruefe_nachweis_robustheit.py, pruefe_nb_betrieb.py, pruefe_nb_details.py
    pruefe_nb_nach_umschaltung.py, pruefe_neuaufnahme.py, pruefe_nichtkurs_bestand.py, pruefe_outcome_plausibilitaet.py
    pruefe_pfad_bewerter.py, pruefe_phase1.py, pruefe_phasenindex.py, pruefe_positionierung_kanal.py
    pruefe_produktion_nb.py, pruefe_prompt_matrix.py, pruefe_quellen2.py, pruefe_quellen_optionen.py
    pruefe_regime_glaettung.py, pruefe_regimephasen_vorflug.py, pruefe_rollenkette.py, pruefe_s6a_rollen.py
    pruefe_short_ursache.py, pruefe_sperrquote_wirkung.py, pruefe_sprung_bei_crv4.py, pruefe_szenario_stufe0.py
    pruefe_trader_merkmale.py, pruefe_tvl_abdeckung.py, pruefe_u1_wirkung.py, pruefe_waehrungen.py
    pruefe_wahrscheinlichkeit_bitgleich.py, pruefe_watchlist.py, pruefe_zahlen_in_prompts.py, rechne_einordnung_vorschau.py
    rechne_funding_beitrag.py, rechne_kandidaten_beitrag.py, rechne_oi_beitrag.py, rechne_redundanz_je_asset.py
    rechne_takt_je_asset.py, rechne_turnover_beitrag.py, simuliere_bremse.py, simuliere_h_varianten.py
    simuliere_kette.py, simuliere_rollout_gegen_nb.py

