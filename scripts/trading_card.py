#!/usr/bin/env python3
"""Génère assets/trading.svg : mon activité GitHub présentée comme un graphique de bourse.

Le « cours » de $ENZO = mes contributions sur 7 jours glissants.
Une bougie par semaine : ouverture = cours à la fin de la semaine précédente, clôture = cours
en fin de semaine, mèches = plus haut et plus bas de la semaine. Volume = contributions de la semaine.
    GITHUB_TOKEN=$(gh auth token) python3 scripts/trading_card.py EnzoBuchaillat
"""
import os
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from activity_card import MONTHS, MONTHS_FULL, calendar  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "assets" / "trading.svg"

W, H = 960, 470
UP, DOWN = "#00C8DC", "#ff4d6d"
BG, BORDER, MUTED, GRID, TEXT = "#0d1117", "#21262d", "#7d8590", "#1b222b", "#e6edf3"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

LEFT, RIGHT = 40, 880            # zone du graphique (l'axe des prix est à droite)
P_TOP, P_BOT = 150, 322          # bougies
V_TOP, V_BOT = 340, 392          # volume


def candles(weeks):
    days = [c for w in weeks for _, c in w]
    rolling = [sum(days[max(0, i - 6): i + 1]) for i in range(len(days))]
    out, idx, prev_close = [], 0, None
    for w in weeks:
        seg = rolling[idx: idx + len(w)]
        idx += len(w)
        o = prev_close if prev_close is not None else seg[0]
        c = seg[-1]
        out.append({"o": o, "c": c, "h": max(seg + [o]), "l": min(seg + [o]),
                    "v": sum(n for _, n in w), "start": w[0][0]})
        prev_close = c
    return out, rolling


def card(weeks) -> str:
    cs, rolling = candles(weeks)
    top = max(c["h"] for c in cs) or 1
    scale = top * 1.12
    vmax = max(c["v"] for c in cs) or 1
    py = lambda v: P_BOT - (P_BOT - P_TOP) * v / scale  # noqa: E731
    step = (RIGHT - LEFT) / len(cs)
    body_w = max(3.0, step * 0.58)
    n = len(cs)

    # Lignes de prix et graduations à droite.
    grid = []
    tick = max(5, round(scale / 4 / 5) * 5)
    last_y = py(cs[-1]["c"])
    v = 0
    while v <= scale:
        y = py(v)
        label = "" if abs(y - last_y) < 14 else (
            f'<text x="{RIGHT + 10}" y="{y + 4:.1f}" font-family="{MONO}" font-size="11" fill="{MUTED}">{v}</text>')
        grid.append(f'<line x1="{LEFT}" y1="{y:.1f}" x2="{RIGHT}" y2="{y:.1f}" stroke="{GRID}" stroke-dasharray="2 4"/>'
                    + label)
        v += tick

    bodies, wicks, vols, labels, seen = [], [], [], [], set()
    for i, c in enumerate(cs):
        cx = LEFT + i * step + step / 2
        up = c["c"] >= c["o"]
        col = UP if up else DOWN
        # Apparition de gauche à droite, toutes les animations partent à 0 s (pas de flash avant le départ).
        t = 0.1 + 0.75 * i / n
        fade = (f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{t:.3f};{min(1, t + 0.08):.3f}" '
                f'dur="2.4s"/>') if t + 0.08 <= 1 else ""
        wicks.append(f'<line x1="{cx:.1f}" y1="{py(c["h"]):.1f}" x2="{cx:.1f}" y2="{py(c["l"]):.1f}" stroke="{col}" stroke-width="1.3">{fade}</line>')
        y1, y2 = py(max(c["o"], c["c"])), py(min(c["o"], c["c"]))
        hgt = max(1.6, y2 - y1)
        fill = col
        bodies.append(f'<rect x="{cx - body_w / 2:.1f}" y="{y1:.1f}" width="{body_w:.1f}" height="{hgt:.1f}" '
                      f'fill="{fill}" stroke="{col}" stroke-width="1.3" rx="0.8">{fade}</rect>')
        vh = (V_BOT - V_TOP) * c["v"] / vmax
        vols.append(f'<rect x="{cx - body_w / 2:.1f}" y="{V_BOT - vh:.1f}" width="{body_w:.1f}" height="{max(vh, 0.8):.1f}" '
                    f'fill="{col}" fill-opacity="0.35">{fade}</rect>')
        d0 = c["start"]
        if (d0.year, d0.month) not in seen and d0.day <= 7 and i > 0:
            seen.add((d0.year, d0.month))
            labels.append(f'<text x="{cx:.1f}" y="{V_BOT + 20}" text-anchor="middle" font-family="{MONO}" font-size="11" fill="{MUTED}">{MONTHS[d0.month - 1]}</text>')

    # Moyenne mobile 4 semaines sur la clôture.
    ma_pts = []
    for i in range(3, n):
        avg = sum(cs[j]["c"] for j in range(i - 3, i + 1)) / 4
        ma_pts.append(f"{LEFT + i * step + step / 2:.1f},{py(avg):.1f}")
    ma = f'<polyline points="{" ".join(ma_pts)}" fill="none" stroke="#f0b429" stroke-width="1.6" stroke-opacity="0.85"/>'

    # Dernier cours : ligne pointillée + étiquette sur l'axe, comme sur une plateforme.
    last = cs[-1]["c"]
    ly = py(last)
    last_col = UP if cs[-1]["c"] >= cs[-1]["o"] else DOWN
    price_tag = (f'<line x1="{LEFT}" y1="{ly:.1f}" x2="{RIGHT}" y2="{ly:.1f}" stroke="{last_col}" stroke-dasharray="4 3" stroke-opacity="0.8"/>'
                 f'<rect x="{RIGHT + 4}" y="{ly - 10:.1f}" width="44" height="20" rx="4" fill="{last_col}"/>'
                 f'<text x="{RIGHT + 26}" y="{ly + 4:.1f}" text-anchor="middle" font-family="{MONO}" font-size="12" font-weight="700" fill="{BG}">{last}</text>')

    # En-tête : variation sur 4 semaines et plus haut historique.
    ref = cs[-5]["c"] if n >= 5 else cs[0]["o"]
    if ref:
        change = (last - ref) / ref * 100
        change_txt = f"{'+' if change >= 0 else '−'}{abs(change):.1f} %".replace(".", ",")
    else:
        change, change_txt = (1, "nouveau") if last else (0, "0 %")
    change_col = UP if change >= 0 else DOWN
    ath_i = max(range(len(rolling)), key=lambda i: rolling[i])
    ath_day = [d for w in weeks for d, _ in w][ath_i]
    ath = f"{rolling[ath_i]} · {ath_day.day} {MONTHS_FULL[ath_day.month - 1]} {ath_day.year}"

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Mon activité GitHub en graphique de bourse : {last} contributions sur les 7 derniers jours, {escape(change_txt)} sur 4 semaines, plus haut {escape(ath)}">
  <defs>
    <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">
      <path d="M24 0 H0 V24" fill="none" stroke="#ffffff" stroke-opacity="0.03"/>
    </pattern>
  </defs>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="18" fill="{BG}" stroke="{BORDER}"/>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="18" fill="url(#grid)"/>
  <text x="40" y="54" font-family="{MONO}" font-size="13" letter-spacing="3" fill="{UP}">$ENZO // CONTRIBUTIONS GITHUB</text>
  <text x="{W - 40}" y="54" text-anchor="end" font-family="{MONO}" font-size="12" fill="{MUTED}">1 bougie = 1 semaine · cours = 7 jours glissants</text>
  <text x="40" y="104" font-family="{SANS}" font-size="38" font-weight="700" fill="{TEXT}">{last}</text>
  <text x="{40 + 24 * len(str(last)) + 14}" y="104" font-family="{MONO}" font-size="16" font-weight="700" fill="{change_col}">{escape(change_txt)}</text>
  <text x="{40 + 24 * len(str(last)) + 14}" y="124" font-family="{MONO}" font-size="11" fill="{MUTED}">SUR 4 SEMAINES</text>
  <text x="{W - 40}" y="96" text-anchor="end" font-family="{MONO}" font-size="11" letter-spacing="1.5" fill="{MUTED}">PLUS HAUT HISTORIQUE</text>
  <text x="{W - 40}" y="118" text-anchor="end" font-family="{SANS}" font-size="15" font-weight="600" fill="{TEXT}">{escape(ath)}</text>
  {"".join(grid)}
  <line x1="{LEFT}" y1="{V_BOT + 0.5}" x2="{RIGHT}" y2="{V_BOT + 0.5}" stroke="{BORDER}"/>
  {"".join(vols)}
  {ma}
  {"".join(wicks)}
  {"".join(bodies)}
  {price_tag}
  {"".join(labels)}
  <line x1="{LEFT}" y1="{H - 36}" x2="{LEFT + 16}" y2="{H - 36}" stroke="#f0b429" stroke-width="1.6"/>
  <text x="{LEFT + 22}" y="{H - 32}" font-family="{MONO}" font-size="11" fill="{MUTED}">moyenne mobile 4 semaines</text>
  <rect x="{LEFT + 220}" y="{H - 41}" width="9" height="10" fill="{UP}"/>
  <text x="{LEFT + 236}" y="{H - 32}" font-family="{MONO}" font-size="11" fill="{MUTED}">activité en hausse</text>
  <rect x="{LEFT + 380}" y="{H - 41}" width="9" height="10" fill="{DOWN}"/>
  <text x="{LEFT + 396}" y="{H - 32}" font-family="{MONO}" font-size="11" fill="{MUTED}">activité en baisse</text>
  <rect x="{LEFT + 540}" y="{H - 41}" width="9" height="10" fill="{MUTED}" fill-opacity="0.5"/>
  <text x="{LEFT + 556}" y="{H - 32}" font-family="{MONO}" font-size="11" fill="{MUTED}">volume = contributions de la semaine</text>
</svg>
'''


def main() -> int:
    user = sys.argv[1] if len(sys.argv) > 1 else ""
    if not user or not os.environ.get("GITHUB_TOKEN"):
        sys.stderr.write("usage: GITHUB_TOKEN=… trading_card.py <utilisateur>\n")
        return 2
    try:
        _, weeks = calendar(user)
    except Exception as exc:
        sys.stderr.write(f"[trading-card] API inaccessible ({exc}), carte inchangée\n")
        return 3
    OUT.write_text(card(weeks), encoding="utf-8")
    print(f"Écrit : {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
