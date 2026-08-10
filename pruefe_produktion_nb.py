"""Rauchtest fuer die Produktion auf dem Notebook - nach dem Deployment.

WOZU. Am 09.08. stand die Produktion einen ganzen Tag still, weil Messlaeufe am
Desktop Geminis Tagesbudget aufgebraucht hatten - das Kontingent haengt am
API-SCHLUESSEL, nicht am Geraet. Es gab keine Stelle, an der man das haette
sehen koennen, und die Kette wich nicht aus.

Dieser Test prueft genau das, und zwar unter der ECHTEN Bedingung: solange
Geminis Tag leer ist (bis Mitternacht Pazifik, 09:00 MESZ), laesst sich das
Ausweichen ueberhaupt erst beweisen. Danach ist das Budget frisch und der Fall
nicht mehr herstellbar, ohne 500 Aufrufe zu verbrennen.

WAS ER KOSTET: hoechstens ein Gemini-Aufruf (der scheitern SOLL) und ein
OpenRouter-Aufruf. Kein Signal wird erzeugt, nichts wird geschrieben ausser
dem Aufrufzaehler.

    python pruefe_produktion_nb.py
    python pruefe_produktion_nb.py --ohne-aufrufe    # nur Struktur, 0 Aufrufe
"""
from __future__ import annotations

import argparse
import os
import sys

_ok, _fehler, _warnung = 0, [], []


def pruefe(name, bedingung, detail=""):
    global _ok
    if bedingung:
        _ok += 1
        print(f"  [ok]     {name}" + (f"   {detail}" if detail else ""))
    else:
        _fehler.append(name)
        print(f"  [FEHLER] {name}   {detail}")


def hinweis(text):
    _warnung.append(text)
    print(f"  [hinweis] {text}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ohne-aufrufe", action="store_true",
                   help="keine echten LLM-Aufrufe - nur Struktur und Schema")
    args = p.parse_args()

    print("=" * 72)
    print("PRODUKTIONS-RAUCHTEST (Notebook)")
    print("=" * 72)

    print("\nA  Der neue Code ist ueberhaupt da")
    try:
        from api.gemini import (TAGESBUDGET_JE_MODELL, GeminiClient,
                                TageskontingentErschoepft, _kontingent_tag)
        pruefe("A1 api.gemini traegt den Tageswaechter", True,
               f"Budget {TAGESBUDGET_JE_MODELL}, Tag {_kontingent_tag()}")
    except ImportError as exc:
        pruefe("A1 api.gemini traegt den Tageswaechter", False, str(exc))
        print("\nABBRUCH: der Code ist nicht aktuell. 'git pull' fehlt.")
        return 1
    try:
        from agent.krypto.budget_allocator import (_ist_kontingent_leer,
                                                   _TageskontingentErschoepft)
        pruefe("A2 der Allocator unterscheidet Budget von Stoerung",
               _TageskontingentErschoepft is TageskontingentErschoepft)
    except ImportError as exc:
        pruefe("A2 der Allocator unterscheidet Budget von Stoerung", False,
               str(exc))
        return 1

    print("\nB  Die Datenbank kann mitzaehlen")
    import database.db as db
    conn = db.get_connection()
    try:
        tabellen = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name LIKE 'api_call_kontingent%'")}
        pruefe("B1 die Zaehlertabellen existieren",
               {"api_call_kontingent", "api_call_kontingent_taeglich"} <= tabellen,
               str(sorted(tabellen)) or "keine")
        if not tabellen:
            hinweis("init_db() legt sie an - die App einmal starten.")

        print("\nC  Was der Zaehler heute sieht")
        import remote.status as st
        karte = st._get_llm_kontingent(conn)
        if karte is None:
            hinweis("noch kein Gemini-Aufruf heute gebucht - die Karte auf der "
                    "Statusseite bleibt bis zum ersten Aufruf leer. Das ist "
                    "richtig so und keine Stoerung.")
            _ok_karte = True
        else:
            _ok_karte = all(m["limit"] == TAGESBUDGET_JE_MODELL
                            for m in karte["modelle"])
            for m in karte["modelle"]:
                print(f"      {m['modell']}: {m['anzahl']}/{m['limit']} "
                      f"({m['prozent']} %)")
        pruefe("C1 die Statusseiten-Karte baut sich fehlerfrei", _ok_karte,
               f"Tag {karte['tag_pazifik']}" if karte else "leer")

        # WICHTIG: der Zaehler kennt nur, was DIESES Geraet gebucht hat. Steht
        # er auf 0 und Google weist trotzdem ab, ist das kein Widerspruch -
        # es heisst, das Budget ging woanders drauf. Genau der Fall vom 09.08.
        print("\nD  Meldet der Anbieter selbst, was der Zaehler nicht weiss?")
        if args.ohne_aufrufe:
            hinweis("uebersprungen (--ohne-aufrufe)")
        else:
            import config as config_module
            config_module.load_env()
            if not os.environ.get("GEMINI_API_KEY"):
                pruefe("D1 GEMINI_API_KEY vorhanden", False)
                return 1
            # DEN ZUSTAND VOR DEM AUFRUF FESTHALTEN. Stufe F fragt, ob der
            # Aufruf einen NEUEN Fehlereintrag erzeugt hat - das laesst sich
            # nur im Vergleich beantworten. Ein alter Eintrag von gestern
            # darf nicht als heutiger Fehlschlag durchgehen.
            def _health():
                r = conn.execute(
                    "SELECT last_error_at, last_error_type, last_error_message "
                    "FROM api_health_status WHERE source = 'gemini'").fetchone()
                return (r["last_error_at"], r["last_error_type"],
                        r["last_error_message"]) if r else (None, None, None)

            vorher = _health()
            k = GeminiClient(os.environ["GEMINI_API_KEY"])
            stand = k.budget_status()
            print(f"      Zaehler dieses Geraets: {stand['verbraucht']}/"
                  f"{stand['budget']} am {stand['tag_pazifik']} (Pazifik)")
            try:
                k.chat([{"role": "user", "content": "OK"}])
                hinweis("D NICHT PRUEFBAR - KEIN BESTANDENER TEST: Gemini "
                        "antwortet, das Tagesbudget ist NICHT leer. Der "
                        "Ausweich-Fall laesst sich damit gerade nicht "
                        "herstellen. Das ist WEDER ein Erfolg NOCH ein "
                        "Fehlschlag - der Beweis, dass die Produktion bei "
                        "leerem Budget auf OpenRouter ausweicht, steht "
                        "weiterhin AUS.")
                gemini_leer = False
            except TageskontingentErschoepft as exc:
                pruefe("D1 leeres Tagesbudget wird als solches erkannt", True,
                       str(exc)[:90])
                gemini_leer = True
            except Exception as exc:  # noqa: BLE001
                pruefe("D1 leeres Tagesbudget wird als solches erkannt", False,
                       f"stattdessen {type(exc).__name__}: {str(exc)[:80]}")
                gemini_leer = False

            print("\nE  Traegt der Ausweichanbieter?")
            if not os.environ.get("OPENROUTER_API_KEY"):
                pruefe("E1 OPENROUTER_API_KEY vorhanden", False,
                       "ohne ihn steht die Produktion still, sobald Gemini leer ist")
            else:
                from api.openrouter import OpenRouterClient
                try:
                    antwort = OpenRouterClient(
                        os.environ["OPENROUTER_API_KEY"]).chat(
                        [{"role": "user",
                          "content": "Antworte mit genau einem Wort: OK"}])
                    pruefe("E1 OpenRouter antwortet", bool(antwort),
                           antwort.strip()[:40])
                except Exception as exc:  # noqa: BLE001
                    pruefe("E1 OpenRouter antwortet", False,
                           f"{type(exc).__name__}: {str(exc)[:90]}")

            print("\nF  Wurde daraus faelschlich eine STOERUNG?")
            # Der entscheidende Unterschied: ein leeres Budget darf die Ampel
            # der Statusseite NICHT auf Rot stellen. Der Anbieter ist gesund.
            # REPARIERT 10.08. Hier stand `SELECT source, status, fehler_text`
            # - beide Spalten existieren nicht. Die Tabelle fuehrt
            # `last_error_at/_type/_message`. Der Fehler ist mir nicht
            # aufgefallen, weil mein eigener Testlauf mit --ohne-aufrufe lief
            # und diesen Block ueberhaupt nicht erreichte: eine Codezeile, die
            # nie ausgefuehrt wurde, ging in die Produktion. Der Rauchtest hat
            # als Erstes seinen eigenen Autor erwischt.
            #
            # Die Reparatur macht die Pruefung schaerfer: entscheidend ist
            # nicht, OB ein Fehlereintrag existiert (der kann von gestern
            # sein), sondern ob DIESER Aufruf einen NEUEN erzeugt hat.
            nachher = _health()
            if gemini_leer:
                neuer_eintrag = nachher[0] != vorher[0]
                pruefe("F1 das leere Budget erzeugt KEINEN neuen "
                       "Stoerungseintrag", not neuer_eintrag,
                       f"vorher {vorher[0]} -> nachher {nachher[0]}"
                       + (f" ({nachher[1]}: {(nachher[2] or '')[:60]})"
                          if neuer_eintrag else ""))
            else:
                hinweis("F NICHT PRUEFBAR - Gemini war nicht leer, also gab "
                        "es nichts, was faelschlich als Stoerung haette "
                        "verbucht werden koennen.")
    finally:
        conn.close()

    print("\n" + "=" * 72)
    print(f"{_ok} Pruefungen bestanden, {len(_fehler)} fehlgeschlagen, "
          f"{len(_warnung)} Hinweise")
    for f in _fehler:
        print(f"   FEHLER: {f}")
    # DIE ENTSCHEIDENDE AUSSAGE ZUM SCHLUSS, unmissverstaendlich.
    #
    # Der erste Bericht vom NB (10.08.) hat den Hinweis "Gemini antwortet"
    # als BESTANDENEN Test D gelistet - also genau umgekehrt. Ein "nicht
    # pruefbar" darf sich nicht wie ein Erfolg lesen, sonst gilt der Ausweg
    # auf OpenRouter als bewiesen, obwohl er nie ausprobiert wurde.
    nicht_pruefbar = [w for w in _warnung if "NICHT PRUEFBAR" in w]
    if nicht_pruefbar:
        print("\n" + "!" * 72)
        print("ACHTUNG: der WICHTIGSTE Teil wurde NICHT geprueft.")
        for w in nicht_pruefbar:
            print(f"   {w}")
        print("Der Beweis, dass die Produktion bei leerem Gemini-Budget auf")
        print("OpenRouter ausweicht, steht damit AUS - er ist nur moeglich,")
        print("solange das Budget tatsaechlich leer ist (vor 09:00 MESZ).")
        print("!" * 72)
    if not _fehler:
        print("\nDie Produktion kann laufen. Was dieser Test NICHT prueft: ob "
              "ein vollstaendiger Signallauf durchgeht - dafuer die App "
              "starten und den ersten Screening-Lauf im Log verfolgen.")
    return 1 if _fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
