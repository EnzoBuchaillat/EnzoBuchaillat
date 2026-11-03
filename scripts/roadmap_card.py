#!/usr/bin/env python3
"""Génère assets/roadmap.svg : ma feuille de route de développeur.

Pour la mettre à jour, change le statut d'une étape dans STEPS
("acquis", "en cours" ou "à venir"), puis lance : python3 scripts/roadmap_card.py
"""
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "roadmap.svg"

# (titre, sous-titre, icône, statut)
STEPS = [
    ("Fondamentaux", "C, Java, algorithmique", "terminal", "acquis"),
    ("Web & BDD", "HTML, CSS, JS, SQL", "database", "acquis"),
    ("Projets perso", "MacTidy en Java", "code", "en cours"),
    ("Stage", "À partir d'avril 2027", "briefcase", "à venir"),
    ("Alternance", "En 3e année de BUT", "cap", "à venir"),
]

W, H = 960, 340
CYAN, CYAN_DARK = "#00C8DC", "#0090a0"
BG, BORDER, MUTED, DIM, TEXT = "#0d1117", "#21262d", "#7d8590", "#30363d", "#e6edf3"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
R = 30  # rayon des hexagones

# Icônes au trait, centrées sur (0, 0), environ 22 px de côté.
ICONS = {
    "terminal": '<path d="M-9 -7 L-2 0 L-9 7"/><path d="M1 8 H10"/>',
    "code": '<path d="M-3.5 -5.5L-9 0L-3.5 5.5M3.5 -5.5L9 0L3.5 5.5M1.6 -8.5L-1.6 8.5"/>',
    "database": '<ellipse cx="0" cy="-7" rx="8.5" ry="3.2"/>'
                '<path d="M-8.5 -7V7C-8.5 8.8 -4.7 10.2 0 10.2S8.5 8.8 8.5 7V-7M-8.5 0C-8.5 1.8 -4.7 3.2 0 3.2S8.5 1.8 8.5 0"/>',
    "network": '<circle cx="0" cy="-8" r="3.2"/><circle cx="-9" cy="7" r="3.2"/>'
               '<circle cx="9" cy="7" r="3.2"/><path d="M-1.6 -5 L-7.4 4.2 M1.6 -5 L7.4 4.2 M-5.8 7 H5.8"/>',
    "shield": '<path d="M0 -11 L9 -7 V0 C9 6 5 9.5 0 11.5 C-5 9.5 -9 6 -9 0 V-7 Z"/><path d="M-4 0 L-1 3.2 L4.5 -3"/>',
    "briefcase": '<rect x="-10" y="-5" width="20" height="14" rx="2.5"/><path d="M-4 -5 V-8.5 H4 V-5 M-10 1.5 H10"/>',
    "cap": '<path d="M0 -9 L12 -3.5 L0 2 L-12 -3.5 Z"/><path d="M-6.5 -0.5 V5 C-6.5 8 6.5 8 6.5 5 V-0.5 M12 -3.5 V4"/>',
}


def hexagon(cx: float, cy: float, r: float) -> str:
    # Hexagone « pointe en haut » : sommets à -90°, -30°, 30°, 90°, 150°, 210°.
    pts = [(0, -1), (0.866, -0.5), (0.866, 0.5), (0, 1), (-0.866, 0.5), (-0.866, -0.5)]
    return " ".join(f"{cx + r * x:.1f},{cy + r * y:.1f}" for x, y in pts)


def node(i: int, x: float, y: float, title: str, sub: str, icon: str, status: str) -> str:
    out = []
    if status == "acquis":
        out.append(f'<polygon points="{hexagon(x, y, R)}" fill="url(#cyan)" filter="url(#glow)"/>')
        stroke = BG
    elif status == "en cours":
        # Anneau qui pulse autour de l'étape en cours.
        out.append(
            f'<g transform="translate({x} {y})">'
            f'<polygon points="{hexagon(0, 0, R)}" fill="none" stroke="{CYAN}" stroke-width="2">'
            f'<animateTransform attributeName="transform" type="scale" values="1;1.55" dur="2.2s" '
            f'repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0.7;0" dur="2.2s" repeatCount="indefinite"/>'
            f'</polygon></g>'
        )
        out.append(f'<polygon points="{hexagon(x, y, R)}" fill="{BG}" stroke="{CYAN}" stroke-width="2.5" filter="url(#glow)"/>')
        stroke = CYAN
    else:
        out.append(f'<polygon points="{hexagon(x, y, R)}" fill="{BG}" stroke="{DIM}" stroke-width="2" stroke-dasharray="5 4"/>')
        stroke = MUTED
    out.append(
        f'<g transform="translate({x} {y})" fill="none" stroke="{stroke}" stroke-width="2.2" '
        f'stroke-linecap="round" stroke-linejoin="round">{ICONS[icon]}</g>'
    )

    label_colour = CYAN if status != "à venir" else MUTED
    out.append(
        f'<text x="{x}" y="252" text-anchor="middle" font-family="{MONO}" font-size="11.5" '
        f'letter-spacing="1.5" fill="{label_colour}">{i + 1:02d} · {escape(status.upper())}</text>'
    )
    title_colour = TEXT if status != "à venir" else "#b1bac4"
    out.append(
        f'<text x="{x}" y="278" text-anchor="middle" font-family="{SANS}" font-size="18" '
        f'font-weight="700" fill="{title_colour}">{escape(title)}</text>'
    )
    out.append(
        f'<text x="{x}" y="300" text-anchor="middle" font-family="{SANS}" font-size="13" '
        f'fill="{MUTED}">{escape(sub)}</text>'
    )
    return "\n  ".join(out)


def trace(x1: float, y1: float, x2: float, y2: float) -> str:
    # Piste de circuit imprimé : horizontale, coude à 45°, horizontale.
    xm = (x1 + x2) / 2
    d = abs(y2 - y1)
    return f"M{x1 + R * 0.866:.1f} {y1} H{xm - d / 2:.1f} L{xm + d / 2:.1f} {y2} H{x2 - R * 0.866:.1f}"


def card() -> str:
    xs = [110 + i * 185 for i in range(len(STEPS))]
    ys = [140 if i % 2 == 0 else 180 for i in range(len(STEPS))]
    statuses = [s[3] for s in STEPS]
    current = statuses.index("en cours") if "en cours" in statuses else None
    done = statuses.count("acquis")

    traces, vias = [], []
    for i in range(len(STEPS) - 1):
        d = trace(xs[i], ys[i], xs[i + 1], ys[i + 1])
        lit = statuses[i] == "acquis"
        if lit:
            traces.append(f'<path d="{d}" fill="none" stroke="{CYAN}" stroke-width="2.5" filter="url(#glow)"/>')
        else:
            traces.append(f'<path d="{d}" fill="none" stroke="{DIM}" stroke-width="2" stroke-dasharray="6 5"/>')
        xm, dy = (xs[i] + xs[i + 1]) / 2, abs(ys[i + 1] - ys[i])
        for vx, vy in ((xm - dy / 2, ys[i]), (xm + dy / 2, ys[i + 1])):
            vias.append(f'<circle cx="{vx:.1f}" cy="{vy}" r="3.5" fill="{BG}" stroke="{CYAN if lit else DIM}" stroke-width="2"/>')

    # Paquet de données qui circule sur les pistes déjà allumées, jusqu'à l'étape en cours.
    packet = ""
    if current:
        route = " ".join(trace(xs[i], ys[i], xs[i + 1], ys[i + 1]) for i in range(current))
        packet = (
            f'<circle r="4.5" fill="#ffffff" filter="url(#glow)">'
            f'<animateMotion dur="{1.6 * current:.1f}s" repeatCount="indefinite" path="{route}"/></circle>'
        )

    nodes = [node(i, xs[i], ys[i], *STEPS[i]) for i in range(len(STEPS))]

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Feuille de route de développeur : {done} étapes acquises sur {len(STEPS)}">
  <defs>
    <linearGradient id="cyan" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{CYAN}"/><stop offset="1" stop-color="{CYAN_DARK}"/>
    </linearGradient>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="3.5" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">
      <path d="M24 0 H0 V24" fill="none" stroke="#ffffff" stroke-opacity="0.035"/>
    </pattern>
  </defs>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="18" fill="{BG}" stroke="{BORDER}"/>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="18" fill="url(#grid)"/>
  <text x="40" y="54" font-family="{MONO}" font-size="13" letter-spacing="3" fill="{CYAN}">ROADMAP // DÉVELOPPEUR</text>
  <text x="{W - 40}" y="54" text-anchor="end" font-family="{MONO}" font-size="12.5" fill="{MUTED}">{done} / {len(STEPS)} étapes acquises</text>
  {chr(10).join("  " + t for t in traces).strip()}
  {chr(10).join("  " + v for v in vias).strip()}
  {packet}
  {chr(10).join("  " + n for n in nodes).strip()}
</svg>
'''


if __name__ == "__main__":
    OUT.write_text(card(), encoding="utf-8")
    print(f"Écrit : {OUT}")
