#!/usr/bin/env python3
"""Génère assets/activite.svg : mon activité GitHub des 12 derniers mois et mes langages.

Contributions : calendrier GitHub (API GraphQL), contributions privées comprises puisque
le profil les affiche. Langages : octets de code des dépôts publics (voir langs_card.py).
Tourne chaque nuit dans GitHub Actions (.github/workflows/activite.yml), marche aussi en local :
    GITHUB_TOKEN=$(gh auth token) python3 scripts/activity_card.py EnzoBuchaillat
Codes de sortie : 0 = carte écrite, 3 = API inaccessible (la carte reste telle quelle).
"""
import json
import random
import os
import sys
import urllib.request
from datetime import date
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from langs_card import COLORS, OTHER, totals  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "assets" / "activite.svg"

W = 960
CYAN, CYAN_DARK = "#00C8DC", "#005f6b"
BG, BORDER, MUTED, DIM, TEXT = "#0d1117", "#21262d", "#7d8590", "#21262d", "#e6edf3"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONTHS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
MONTHS_FULL = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
               "septembre", "octobre", "novembre", "décembre"]
TOP_LANGS = 6

QUERY = """query($login: String!) { user(login: $login) { contributionsCollection {
  contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
} } }"""


def calendar(user: str) -> tuple[int, list[list[tuple[date, int]]]]:
    body = json.dumps({"query": QUERY, "variables": {"login": user}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}", "User-Agent": "activity-card"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        cal = json.load(r)["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = [[(date.fromisoformat(d["date"]), d["contributionCount"]) for d in w["contributionDays"]]
             for w in cal["weeks"]]
    return cal["totalContributions"], weeks


def stats(weeks):
    days = [d for w in weeks for d in w]
    active = sum(1 for _, c in days if c > 0)
    best = run = 0
    for _, c in days:
        run = run + 1 if c > 0 else 0
        best = max(best, run)
    per_month: dict[tuple[int, int], int] = {}
    for d, c in days:
        per_month[(d.year, d.month)] = per_month.get((d.year, d.month), 0) + c
    (y, m), _ = max(per_month.items(), key=lambda kv: kv[1])
    return active, best, f"{MONTHS_FULL[m - 1]} {y}"


def card(total: int, weeks, langs: dict[str, int]) -> str:
    active, streak, top_month = stats(weeks)
    first, last = weeks[0][0][0], weeks[-1][-1][0]

    figures = [
        (f"{total}", "CONTRIBUTIONS"),
        (f"{active}", "JOURS ACTIFS"),
        (f"{streak} j", "PLUS LONGUE SÉRIE"),
        (top_month, "MOIS LE PLUS ACTIF"),
    ]
    fig_svg = []
    for i, (value, label) in enumerate(figures):
        x = 40 + i * 225
        colour = CYAN if i == 0 else TEXT
        fig_svg.append(
            f'<text x="{x}" y="128" font-family="{SANS}" font-size="32" font-weight="700" fill="{colour}"'
            f'{" filter=\"url(#glow)\"" if i == 0 else ""}>{escape(value)}</text>'
            f'<text x="{x}" y="152" font-family="{MONO}" font-size="11" letter-spacing="1.5" fill="{MUTED}">{label}</text>'
        )

    # La ville : un immeuble par semaine. Hauteur = contributions de la semaine,
    # fenêtres allumées = part des jours actifs. Tirage fixe (graine = n° de semaine).
    ground, sky_top = 352, 196
    step = (W - 80) / len(weeks)
    bw = step * 0.62          # largeur de la façade
    depth_x, depth_y = step * 0.3, step * 0.22  # profondeur vue de biais
    peak = max(sum(c for _, c in w) for w in weeks) or 1
    rng = random.Random(42)
    stars = "".join(
        f'<circle cx="{rng.uniform(44, W - 44):.1f}" cy="{rng.uniform(sky_top - 20, ground - 120):.1f}" '
        f'r="{rng.choice((0.7, 0.9, 1.2))}" fill="#ffffff" opacity="{rng.uniform(0.15, 0.5):.2f}"/>'
        for _ in range(70)
    )
    # Arrière-plan : silhouette lointaine, simple décor sans lien avec les données.
    far, fx = [], 24.0
    while fx < W - 24:
        fw, fh = rng.uniform(14, 34), rng.uniform(18, 62)
        far.append(f'<rect x="{fx:.1f}" y="{ground - fh:.1f}" width="{fw:.1f}" height="{fh:.1f}" fill="#0c1a20"/>')
        fx += fw + rng.uniform(0, 3)
    buildings, labels, seen = [], [], set()
    for i, w in enumerate(weeks):
        n = sum(c for _, c in w)
        days_on = sum(1 for _, c in w if c > 0)
        x = 40 + i * step + (step - bw - depth_x) / 2
        h = 10.0 if n == 0 else 16 + (ground - sky_top - 16) * (n / peak) ** 0.8
        y = ground - h
        r = random.Random(i)
        lit_p = 0.05 if n == 0 else 0.18 + 0.8 * days_on / 7
        win = []
        cols = (x + bw * 0.16, x + bw * 0.58)
        ww = bw * 0.26
        fy = y + 5
        while fy + 3 < ground - 3:
            for cx in cols:
                if r.random() < lit_p:
                    tw = ""
                    if r.random() < 0.06:
                        tw = (f'<animate attributeName="opacity" values="1;0.15;1" dur="{r.uniform(2.5, 6):.1f}s" '
                              f'begin="{r.uniform(0, 4):.1f}s" repeatCount="indefinite"/>')
                    win.append(f'<rect x="{cx:.1f}" y="{fy:.1f}" width="{ww:.1f}" height="2.6" fill="{CYAN}">{tw}</rect>')
                else:
                    win.append(f'<rect x="{cx:.1f}" y="{fy:.1f}" width="{ww:.1f}" height="2.6" fill="#17303a"/>')
            fy += 5.6
        side = (f"{x + bw:.1f},{y:.1f} {x + bw + depth_x:.1f},{y - depth_y:.1f} "
                f"{x + bw + depth_x:.1f},{ground - depth_y:.1f} {x + bw:.1f},{ground}")
        roof = (f"{x:.1f},{y:.1f} {x + depth_x:.1f},{y - depth_y:.1f} "
                f"{x + bw + depth_x:.1f},{y - depth_y:.1f} {x + bw:.1f},{y:.1f}")
        antenna = ""
        if n == peak:
            ax = x + bw / 2 + depth_x / 2
            antenna = (f'<line x1="{ax:.1f}" y1="{y - depth_y / 2:.1f}" x2="{ax:.1f}" y2="{y - depth_y / 2 - 16:.1f}" stroke="#4a6470" stroke-width="1.2"/>'
                       f'<circle cx="{ax:.1f}" cy="{y - depth_y / 2 - 17:.1f}" r="2.2" fill="#ff4d5e" filter="url(#glow)">'
                       f'<animate attributeName="opacity" values="1;0.2;1" dur="1.6s" repeatCount="indefinite"/></circle>')
        roof_col = CYAN if n > 0 else "#1d2b33"
        buildings.append(
            f'<g><animateTransform attributeName="transform" type="translate" values="0 {h + 20:.0f};0 0" '
            f'dur="1.4s" calcMode="spline" keySplines="0.2 0.8 0.2 1"/>'
            f'<polygon points="{side}" fill="#08141a"/>'
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="url(#facade)"/>'
            f'<polygon points="{roof}" fill="{roof_col}" fill-opacity="{0.55 if n > 0 else 1}"/>'
            f'{"".join(win)}{antenna}</g>'
        )
        d0 = w[0][0]
        key = (d0.year, d0.month)
        if key not in seen and d0.day <= 7 and i > 0:
            seen.add(key)
            labels.append(f'<text x="{40 + i * step:.1f}" y="374" font-family="{MONO}" font-size="11" fill="{MUTED}">{MONTHS[d0.month - 1]}</text>')

    # Langages : barre segmentée et légende en ligne.
    total_bytes = sum(langs.values()) or 1
    ranked = sorted(langs.items(), key=lambda kv: -kv[1])
    shown = [(n, s / total_bytes) for n, s in ranked[:TOP_LANGS]]
    rest = sum(s for _, s in ranked[TOP_LANGS:]) / total_bytes
    if rest > 0.005:
        shown.append(("Autres", rest))
    seg, x = [], 40.0
    for name, share in shown:
        seg.append(f'<rect x="{x:.1f}" y="432" width="{(W - 80) * share + 0.5:.1f}" height="10" fill="{COLORS.get(name, OTHER)}"/>')
        x += (W - 80) * share
    legend, lx = [], 40.0
    for name, share in shown:
        pct = f"{share * 100:.0f} %"
        legend.append(
            f'<circle cx="{lx + 5:.1f}" cy="466" r="5" fill="{COLORS.get(name, OTHER)}"/>'
            f'<text x="{lx + 16:.1f}" y="470" font-family="{SANS}" font-size="13" font-weight="600" fill="{TEXT}">{escape(name)}'
            f'<tspan fill="{MUTED}" font-weight="400"> {pct}</tspan></text>'
        )
        lx += 16 + 8.2 * (len(name) + len(pct) + 1) + 26

    h = 502
    when = f"{first.day} {MONTHS[first.month - 1]} {first.year} au {last.day} {MONTHS[last.month - 1]} {last.year}"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="Activité GitHub en forme de ville, un immeuble par semaine : {total} contributions, {active} jours actifs, plus longue série de {streak} jours, mois le plus actif : {escape(top_month)}">
  <defs>
    <linearGradient id="facade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#123440"/><stop offset="1" stop-color="#0b1c23"/>
    </linearGradient>
    <linearGradient id="horizon" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{CYAN}" stop-opacity="0"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0.16"/>
    </linearGradient>
    <clipPath id="city"><rect x="20" y="150" width="{W - 40}" height="{ground - 150 + 0.5}"/></clipPath>
    <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="4" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">
      <path d="M24 0 H0 V24" fill="none" stroke="#ffffff" stroke-opacity="0.035"/>
    </pattern>
    <clipPath id="langs"><rect x="40" y="432" width="{W - 80}" height="10" rx="5"/></clipPath>
  </defs>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1}" rx="18" fill="{BG}" stroke="{BORDER}"/>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1}" rx="18" fill="url(#grid)"/>
  <text x="40" y="54" font-family="{MONO}" font-size="13" letter-spacing="3" fill="{CYAN}">ACTIVITÉ // 12 DERNIERS MOIS</text>
  <text x="{W - 40}" y="54" text-anchor="end" font-family="{MONO}" font-size="12.5" fill="{MUTED}">du {when}</text>
  {"".join(fig_svg)}
  <rect x="1" y="{ground - 110}" width="{W - 2}" height="110" fill="url(#horizon)"/>
  {stars}
  <g clip-path="url(#city)"><g opacity="0.9">{"".join(far)}</g>{"".join(buildings)}</g>
  <line x1="24" y1="{ground + 0.5}" x2="{W - 24}" y2="{ground + 0.5}" stroke="{CYAN}" stroke-opacity="0.5"/>
  {"".join(labels)}
  <text x="40" y="414" font-family="{MONO}" font-size="11" letter-spacing="1.5" fill="{MUTED}">LANGAGES · CODE DE MES DÉPÔTS PUBLICS</text>
  <g clip-path="url(#langs)"><rect x="40" y="432" width="{W - 80}" height="10" fill="{DIM}"/>{"".join(seg)}</g>
  {"".join(legend)}
</svg>
'''


def main() -> int:
    user = sys.argv[1] if len(sys.argv) > 1 else ""
    if not user or not os.environ.get("GITHUB_TOKEN"):
        sys.stderr.write("usage: GITHUB_TOKEN=… activity_card.py <utilisateur>\n")
        return 2
    try:
        total, weeks = calendar(user)
        langs, _ = totals(user)
    except Exception as exc:  # réseau, limite de l'API…
        sys.stderr.write(f"[activity-card] API inaccessible ({exc}), carte inchangée\n")
        return 3
    OUT.write_text(card(total, weeks, langs), encoding="utf-8")
    print(f"Écrit : {OUT} ({total} contributions)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
