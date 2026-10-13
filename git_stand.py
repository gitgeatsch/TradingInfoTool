"""P21 (13.10.2026): Git-Stand des Geraets und Watchlist gegen das Repo - NUR LESEND.

⚠️⚠️ WARUM ES DAS GIBT. XDC und CT wurden am 08.10. am NB ueber die GUI
(`config.add_watchlist_entry`) in die Watchlist aufgenommen. Das aenderte nur
die config.yaml AM NB, nicht das Repo. Fuenf Tage lang fehlte XDC deshalb in
jeder Pruefung am Desktop, und der Pull mit HBAR waere abgebrochen
(*"Your local changes would be overwritten"*). Die Diagnose zeigte XDC die
ganze Zeit - aber nichts verglich sie mit dem Repo (Nutzerfrage 13.10.:
*"warum hast du das nicht gesehen in der Diagnose?"*). Voranalyse Schritt7
§23.48, Kontrolle K-GIT-1.

ZWEI SEITEN, zwei Funktionen:

  am NB       ``lesen()``   -> Abschnitt ``git_stand`` der Diagnose
  am Desktop  ``bewerte()`` -> Punkt 17 von ``pruefe_export_standard.py``

⚠️⚠️ OHNE SEITENEFFEKT. Jeder Aufruf traegt ``--no-optional-locks``. Ohne
diesen Schalter schreibt ``git status`` die Index-Datei neu, sobald sich ein
Zeitstempel geaendert hat - gemessen am 13.10. (Voranalyse §23.48). Kein
Zugriff auf eine Datenbank, keine Remote-URL im Ergebnis.

⚠️ OHNE ``git`` IM PFAD bleibt der Commit lesbar: er kommt aus ``.git/HEAD``
und der Ref-Datei bzw. ``packed-refs``. Nur die Liste der geaenderten Dateien
fehlt dann - und Punkt 17 sagt das, statt still gruen zu sein.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import yaml

WURZEL = Path(__file__).resolve().parent
CONFIG_REL = "Basisinfos/config.yaml"
FRIST_S = 20
# Die EINE bekannte Ortsaenderung: eine Sicherungskopie, die nach Projektregel nie committet wird (an beiden Geraeten
# geaendert). Sie wird als Infozeile gezeigt, nicht als Auffaelligkeit - jede ANDERE geaenderte Datei ist eine.
BEKANNT_GEAENDERT = {"Basisinfos/config.yaml.bak": "Sicherungskopie der config.yaml, nach Projektregel nie committen"}
# Felder, die zwischen NB-Watchlist und Repo gleich sein muessen
FELDER = ("assetklasse", "rolle", "beobachtungsstatus", "coingecko_id", "name")
_WIN_GIT = (r"C:\Program Files\Git\cmd\git.exe", r"C:\Program Files\Git\bin\git.exe")


def _git_pfad(git: str | None = None) -> str | None:
    if git is not None:
        return git or None                       # "" = bewusst ohne git (Pruefstand)
    return shutil.which("git") or next((p for p in _WIN_GIT if os.path.exists(p)), None)


def _git(git: str, wurzel: Path, *args: str, frist: float = FRIST_S) -> str:
    r = subprocess.run([git, "--no-optional-locks", *args], cwd=str(wurzel), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=frist)
    if r.returncode != 0:
        raise RuntimeError("git %s: %s" % (" ".join(args), (r.stderr or "").strip()[:200]))
    return r.stdout


def head_aus_dateien(wurzel: Path) -> tuple[str | None, str | None]:
    """(Commit, Zweig) direkt aus .git - ohne git-Programm."""
    g = wurzel / ".git"
    kopf = (g / "HEAD").read_text(encoding="utf-8").strip()
    if not kopf.startswith("ref: "):
        return kopf, None                        # losgeloester HEAD
    ref = kopf[5:]
    datei = g.joinpath(*ref.split("/"))
    if datei.exists():
        return datei.read_text(encoding="utf-8").strip(), ref.rsplit("/", 1)[-1]
    gepackt = g / "packed-refs"
    if gepackt.exists():
        for zeile in gepackt.read_text(encoding="utf-8").splitlines():
            if zeile.endswith(" " + ref) and not zeile.startswith(("#", "^")):
                return zeile.split()[0], ref.rsplit("/", 1)[-1]
    return None, ref.rsplit("/", 1)[-1]


# ══ am NB: der Abschnitt `git_stand` der Diagnose ═══════════════════════════════════════════════════════════════════════
def lesen(wurzel: Path | str | None = None, git: str | None = None, frist: float = FRIST_S) -> dict:
    """{'head', 'zweig', 'quelle_head', 'git_verfuegbar', 'geaendert': [(Kennung, Pfad)], 'stash': [...], 'fehler': [...]}.
    Wirft nie - jeder Fehler steht in 'fehler'."""
    wurzel = Path(wurzel) if wurzel else WURZEL
    aus = {"head": None, "zweig": None, "quelle_head": None, "git_verfuegbar": False, "geaendert": None, "stash": None, "fehler": []}
    try:
        aus["head"], aus["zweig"] = head_aus_dateien(wurzel)
        aus["quelle_head"] = "dateien"
    except Exception as exc:                     # noqa: BLE001 - die Diagnose darf hieran nie sterben
        aus["fehler"].append("HEAD aus .git: %s: %s" % (type(exc).__name__, exc))
    g = _git_pfad(git)
    if not g:
        aus["fehler"].append("git nicht im Pfad - geaenderte Dateien und Stash unbekannt")
        return aus
    aus["git_verfuegbar"] = True
    try:
        h = _git(g, wurzel, "rev-parse", "HEAD", frist=frist).strip()
        if aus["head"] and h != aus["head"]:
            aus["fehler"].append("HEAD aus .git %s ungleich git rev-parse %s" % (aus["head"][:8], h[:8]))
        aus["head"], aus["quelle_head"] = h, "git"
    except Exception as exc:                     # noqa: BLE001
        aus["fehler"].append("rev-parse: %s: %s" % (type(exc).__name__, exc))
    try:
        zeilen = _git(g, wurzel, "status", "--porcelain", "--untracked-files=no", frist=frist).splitlines()
        aus["geaendert"] = [(z[:2].strip(), z[3:].strip().strip('"')) for z in zeilen if z.strip()]
    except Exception as exc:                     # noqa: BLE001
        aus["fehler"].append("status: %s: %s" % (type(exc).__name__, exc))
    try:
        aus["stash"] = [z.strip() for z in _git(g, wurzel, "stash", "list", frist=frist).splitlines() if z.strip()]
    except Exception as exc:                     # noqa: BLE001
        aus["fehler"].append("stash: %s: %s" % (type(exc).__name__, exc))
    return aus


# ══ am Desktop: Punkt 17 von pruefe_export_standard.py ═════════════════════════════════════════════════════════════════
def watchlist_aus_commit(commit: str | None, wurzel: Path | str | None = None, git: str | None = None) -> tuple[dict | None, str]:
    """({Symbol: Eintrag} der config.yaml ZUM Commit des NB, Hinweis). Ist der Commit hier unbekannt: gegen HEAD, mit Hinweis."""
    wurzel = Path(wurzel) if wurzel else WURZEL
    g = _git_pfad(git)
    if not g:
        return None, "git am Desktop nicht im Pfad"
    hinweis = "gegen die config.yaml zum NB-Commit %s" % (commit or "?")[:8]
    ref = commit
    if not commit:
        ref, hinweis = "HEAD", "NB-Commit unbekannt - gegen HEAD am Desktop"
    else:
        try:
            _git(g, wurzel, "cat-file", "-e", commit + "^{commit}")
        except Exception:                        # noqa: BLE001
            ref, hinweis = "HEAD", "NB-Commit %s hier unbekannt (nicht gepusht/gefetcht?) - gegen HEAD am Desktop" % commit[:8]
    text = _git(g, wurzel, "show", "%s:%s" % (ref, CONFIG_REL))
    return {e["symbol"]: e for e in (yaml.safe_load(text) or {}).get("watchlist") or []}, hinweis


def vergleiche_watchlist(nb: dict, repo: dict) -> dict:
    """nb: `watchlist_stammdaten` der Diagnose; repo: {Symbol: Eintrag}. Felder nur, wenn die Diagnose sie traegt
    (aeltere Diagnosen ohne `name`/`coingecko_id` sollen keinen Fehlalarm machen)."""
    felder = []
    for s in nb:
        if s not in repo:
            continue
        for f in FELDER:
            if f not in nb[s]:
                continue
            a, b = nb[s].get(f), repo[s].get(f, "krypto" if f == "assetklasse" else None)
            if (a or None) != (b or None):
                felder.append((s, f, a, b))
    return {"nur_nb": [s for s in nb if s not in repo], "nur_repo": [s for s in repo if s not in nb], "felder": felder}


def bewerte(d: dict, wurzel: Path | str | None = None, git: str | None = None) -> tuple[list, list]:
    """(Auffaelligkeiten, Infozeilen) fuer Punkt 17 'NB gegen Repo'. Jede Auffaelligkeit ist ein Satz mit Handlung."""
    melden, info = [], []
    gs = d.get("git_stand")
    if not isinstance(gs, dict):
        melden.append("git_stand fehlt in der Diagnose - der NB hat P21 nicht (Pull?) oder der Abschnitt ist ausgefallen")
    else:
        if gs.get("nicht_verfuegbar"):
            melden.append("git_stand nicht verfuegbar: %s" % gs["nicht_verfuegbar"])
        info.append("NB-Commit %s (%s, Zweig %s)" % ((gs.get("head") or "?")[:8], gs.get("quelle_head"), gs.get("zweig")))
        for f in gs.get("fehler") or []:
            melden.append("git_stand: %s" % f)
        if gs.get("geaendert") is None:
            melden.append("geaenderte Dateien am NB unbekannt (git nicht verfuegbar) - lokale Aenderungen sind ungeprueft")
        for kennung, pfad in gs.get("geaendert") or []:
            if pfad in BEKANNT_GEAENDERT:
                info.append("lokal geaendert %s %s - bekannt: %s" % (kennung, pfad, BEKANNT_GEAENDERT[pfad]))
            else:
                melden.append("am NB lokal geaendert: %s %s - ins Repo uebernehmen oder verwerfen, sonst bricht der naechste Pull "
                              "ab, sobald ein Commit diese Datei aendert" % (kennung, pfad))
        if gs.get("stash"):
            melden.append("am NB liegt ein Stash (%s) - nach der Kontrolle loeschen: git stash drop" % "; ".join(gs["stash"]))
        g = _git_pfad(git)
        if g and gs.get("head"):
            try:
                n = int(_git(g, Path(wurzel) if wurzel else WURZEL, "rev-list", "--count", "%s..origin/main" % gs["head"]).strip())
                info.append("NB liegt %d Commit(s) hinter origin/main" % n)
            except Exception as exc:             # noqa: BLE001
                info.append("Abstand zu origin/main nicht bestimmbar: %s" % str(exc)[:120])
    nb = d.get("watchlist_stammdaten")
    if not isinstance(nb, dict):
        melden.append("watchlist_stammdaten fehlt - Watchlist am NB ungeprueft")
        return melden, info
    try:
        repo, hinweis = watchlist_aus_commit((gs or {}).get("head") if isinstance(gs, dict) else None, wurzel, git)
    except Exception as exc:                     # noqa: BLE001
        melden.append("Watchlist im Repo nicht lesbar: %s" % str(exc)[:160])
        return melden, info
    if repo is None:
        melden.append("Watchlist-Abgleich nicht moeglich: %s" % hinweis)
        return melden, info
    v = vergleiche_watchlist(nb, repo)
    info.append("Watchlist NB %d / Repo %d Eintraege, %s" % (len(nb), len(repo), hinweis))
    if v["nur_nb"]:
        melden.append("Watchlist nur am NB (nicht im Repo): %s - am NB ueber die GUI eingetragen? ins Repo uebernehmen" % ", ".join(v["nur_nb"]))
    if v["nur_repo"]:
        melden.append("Watchlist nur im Repo (am NB nicht): %s - Pull/Neustart am NB ausstehend oder lokal entfernt" % ", ".join(v["nur_repo"]))
    for s, f, a, b in v["felder"]:
        melden.append("Watchlist %s: %s am NB %r, im Repo %r" % (s, f, a, b))
    return melden, info
