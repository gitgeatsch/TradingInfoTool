"""Patch: GEGENPRUEFUNG TAGESZEIT fuer die feine Altersachse (nachtraeglich 28.09.).

Anlass: die Wirkung des oberen Rands ist ueber das Alter tagesperiodisch
(hoch bei 0/24/48 h, tief bei 6-12/36 h). Zwei Erklaerungen: echter
Tagesrhythmus - oder die UHRZEIT der festen Anker (00/06/12/18 UTC): ist q5
je Ankerstunde verschieden und haeufen sich die Randwerte eines Merkmals zu
bestimmten Stunden, misst der Rand zum Teil die Uhrzeit; die Nullwelt
(Verschiebung um beliebige Stunden) zieht das nicht ab.

T1  Dq ALLER Anker je Ankerstunde - gibt es einen Uhrzeiteffekt?
T2  Anteil der Randanker je Ankerstunde (Alter 0) - haeufen sie sich?
T3  Rand TAGESBEREINIGT: je Ankerstunde Dq(Rand) - Dq(alle Anker dieser Stunde),
    mit den Randankern gewichtet
T4  Nullwelt TAGESGLEICH: Verschiebung um ganze Tage (Vielfache von 24 Zeilen)
    - erhaelt die Uhrzeit; z gegen diese Nullwelt

Aendert KEIN vorab festgelegtes Urteil - es ordnet ein.
"""
import io

p = "messe_k1_wirkungskurven.py"
s = io.open(p, encoding="utf-8").read()


def ers(a, b):
    global s
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)


ers('''    print("  Pruef-Vers = Dq der Pruefzeit minus Versatz (E-11) · 2022 mit Moment-Bezug · Umkehr = jenseits der "
          "Grenze mit Gegenzeichen zu 0 h UND Pruefzeit ebenso (Abschnitt 10c)")
''', '''    print("  Pruef-Vers = Dq der Pruefzeit minus Versatz (E-11) · 2022 mit Moment-Bezug · Umkehr = jenseits der "
          "Grenze mit Gegenzeichen zu 0 h UND Pruefzeit ebenso (Abschnitt 10c)")

    # ══ GEGENPRUEFUNG TAGESZEIT (nachtraeglich 28.09., aendert kein Urteil) ══
    stunde = (STD[IDX] % 24).astype(np.int64)

    def dq(ix, na=sNA, nb=sNB):
        return (sA[ix].sum() / max(sA[ix].sum() + sB[ix].sum(), 1e-12)
                - na[ix].sum() / max(na[ix].sum() + nb[ix].sum(), 1e-12))

    print()
    print("=" * 120)
    print("GEGENPRUEFUNG TAGESZEIT (nachtraeglich 28.09., aendert kein vorab festgelegtes Urteil): misst der Rand "
          "die UHRZEIT der festen Anker?")
    for nm, sel in (("Suche", m_such), ("Pruef", m_pruef)):
        print("  T1 Dq aller Anker je Ankerstunde, %s: %s" % (nm, " · ".join(
            "%02d h %+.4f (%d)" % (h, dq(np.flatnonzero(sel & (stunde == h))), int((sel & (stunde == h)).sum()))
            for h in GITTER)))

    def rand_tb(st, sel, sl):
        tot, nn = 0.0, 0
        for h in GITTER:
            ia = np.flatnonzero(sel & (stunde == h) & (st >= 0))
            ie = ia[np.isin(st[ia], sl)]
            if len(ie) < 30:
                continue
            tot += len(ie) * (dq(ie) - dq(ia))
            nn += len(ie)
        return tot / nn if nn else np.nan

    rng_t = np.random.default_rng(SAAT + 24)

    def verschiebe_tage(v):
        aus = np.empty_like(v)
        for tl in teile:
            Lt = len(tl)
            if Lt > 2 * MIN_VERSATZ:
                r = 24 * int(rng_t.integers(MIN_VERSATZ // 24, (Lt - MIN_VERSATZ) // 24))
            else:
                r = 0
            aus[tl] = np.roll(v[tl], r)
        return aus

    print("  T2 Anteil der Randanker (oben, 0 h, Suche) je Ankerstunde 00/06/12/18 - gleichverteilt waeren je 25 %")
    for k in namen:
        st0 = stufe(gealtert(KURVEN[k], 0), GRENZEN[k])
        ie = np.flatnonzero(m_such & np.isin(st0, (10, 11)))
        anteil = [100.0 * np.mean(stunde[ie] == h) for h in GITTER]
        print("     %-24s %s" % (k, "  ".join("%02d h %4.1f %%" % (h, a) for h, a in zip(GITTER, anteil))))
    tn = {k: np.full((ZIEHUNGEN, nL), np.nan) for k in namen}
    for zi in range(ZIEHUNGEN):
        for k in namen:
            v_sh = verschiebe_tage(KURVEN[k])
            for li, L in enumerate(ALTER_FEIN):
                tn[k][zi, li] = rand_dq(stufe(gealtert(v_sh, L), GRENZEN[k]), m_such, sNA, sNB)[1]
    print("  T3/T4 oberer Rand: tagesbereinigt (Suche, Pruefzeit) und z gegen die TAGESGLEICHE Nullwelt")
    print("  %-24s %-9s %s" % ("", "", "  ".join("%3dh" % L for L in ALTER_FEIN)))
    for k in namen:
        tb_s, tb_p, zt = [], [], []
        for li, L in enumerate(ALTER_FEIN):
            st = stufe(gealtert(KURVEN[k], L), GRENZEN[k])
            tb_s.append(rand_tb(st, m_such, (10, 11)))
            tb_p.append(rand_tb(st, m_pruef, (10, 11)))
            m_, s_ = np.nanmean(tn[k][:, li]), max(np.nanstd(tn[k][:, li], ddof=1), 1e-9)
            zt.append((werte[k][li][0][1] - m_) / s_)
        print("  %-24s %-9s %s" % (k, "roh", " ".join("%+.3f" % werte[k][li][0][1] for li in range(nL))))
        print("  %-24s %-9s %s" % ("", "tb Such", " ".join("%+.3f" % x if np.isfinite(x) else "  -   " for x in tb_s)))
        print("  %-24s %-9s %s" % ("", "tb Pruef", " ".join("%+.3f" % x if np.isfinite(x) else "  -   " for x in tb_p)))
        print("  %-24s %-9s %s" % ("", "z Tag", " ".join("%+5.1f " % x if np.isfinite(x) else "  -   " for x in zt)))
    print("  tb = je Ankerstunde Dq(Rand) minus Dq(alle Anker dieser Stunde), mit den Randankern gewichtet; "
          "z Tag = gegen Verschiebungen um ganze Tage (Uhrzeit bleibt erhalten)")
''')
io.open(p, "w", encoding="utf-8").write(s)
print("ok")
