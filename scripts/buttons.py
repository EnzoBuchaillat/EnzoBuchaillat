#!/usr/bin/env python3
"""Génère les boutons arrondis du profil dans assets/buttons/ (contacts, outils, centres d'intérêt).

Pour ajouter un bouton : une ligne dans BUTTONS, puis python3 scripts/buttons.py
Les logos de marque viennent de Simple Icons (licence CC0), rangés dans scripts/icons/.
"""
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "buttons"
ICONS_DIR = Path(__file__).resolve().parent / "icons"

CYAN, BG, BORDER, TEXT = "#00C8DC", "#0d1117", "#2a3440", "#e6edf3"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
H = 44
FONT_SIZE = 15

# Icônes au trait (grille de 24 px) pour ce qui n'a pas de logo libre.
STROKE_ICONS = {
    "linkedin": '<rect x="3" y="3" width="18" height="18" rx="4"/>'
                '<path d="M8 10.5V16.5M12 16.5V10.5M12 13.3C12 11.7 13.1 10.5 14.4 10.5S16.6 11.4 16.6 13V16.5"/>'
                '<circle cx="8" cy="7.4" r="0.9" fill="currentColor" stroke="none"/>',
    "mail": '<rect x="3" y="5.5" width="18" height="13" rx="2.5"/><path d="M3.8 7.2L12 13L20.2 7.2"/>',
    "code": '<path d="M8.5 7.5L4 12L8.5 16.5M15.5 7.5L20 12L15.5 16.5M13.5 5L10.5 19"/>',
    "briefcase": '<rect x="3" y="7.5" width="18" height="12" rx="2.5"/><path d="M9 7.5V5.5H15V7.5M3 12.5H21"/>',
    "chart": '<path d="M4 19.5H20M5 15L10 10L13.5 13.2L19.5 6.5M15.5 6.5H19.5V10.5"/>',
}

# (fichier, libellé, icône) ; une icône « brand:nom » lit scripts/icons/nom.path
BUTTONS = [
    ("linkedin", "LinkedIn", "linkedin"),
    ("email", "E-mail", "mail"),
    ("tryhackme", "TryHackMe", "brand:tryhackme"),
    ("vscode", "VS Code", "code"),
    ("intellij", "IntelliJ IDEA", "brand:intellijidea"),
    ("packet-tracer", "Packet Tracer", "brand:cisco"),
    ("entrepreneuriat", "Entrepreneuriat", "briefcase"),
    ("finance", "Finance", "chart"),
]


def text_width(label: str) -> float:
    try:
        from PIL import ImageFont
        font = ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", FONT_SIZE, index=10)
        return font.getlength(label)
    except Exception:
        return len(label) * 8.4


def icon_markup(icon: str) -> str:
    if icon.startswith("brand:"):
        d = (ICONS_DIR / f"{icon[6:]}.path").read_text().strip()
        return f'<path d="{d}" fill="{CYAN}"/>'
    return (f'<g fill="none" stroke="{CYAN}" stroke-width="1.9" stroke-linecap="round" '
            f'stroke-linejoin="round" color="{CYAN}">{STROKE_ICONS[icon]}</g>')


def button(label: str, icon: str) -> str:
    tw = round(text_width(label), 1)
    w = round(48 + tw + 22)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{H}" viewBox="0 0 {w} {H}" role="img" aria-label="{escape(label)}">
  <defs>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{CYAN}" stop-opacity="0.75"/>
      <stop offset="0.6" stop-color="{BORDER}"/>
    </linearGradient>
  </defs>
  <rect x="0.75" y="0.75" width="{w - 1.5}" height="{H - 1.5}" rx="{(H - 1.5) / 2}" fill="{BG}" stroke="url(#edge)" stroke-width="1.5"/>
  <circle cx="23" cy="22" r="15" fill="{CYAN}" fill-opacity="0.12"/>
  <g transform="translate(15 14) scale(0.6667)">{icon_markup(icon)}</g>
  <text x="48" y="27" font-family="{SANS}" font-size="{FONT_SIZE}" font-weight="600" fill="{TEXT}" textLength="{tw}" lengthAdjust="spacing">{escape(label)}</text>
</svg>
'''


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, label, icon in BUTTONS:
        (OUT / f"{name}.svg").write_text(button(label, icon), encoding="utf-8")
    print(f"{len(BUTTONS)} boutons écrits dans {OUT}")
