#!/usr/bin/env python3
"""Génère assets/langages.svg : les langages les plus utilisés dans mes dépôts publics.

Additionne les octets de code par langage (API GitHub, comme la barre « Languages »
de chaque dépôt), sans les forks ni ce dépôt de profil. Même style que la carte TryHackMe.
Tourne dans GitHub Actions (.github/workflows/langages.yml), mais marche aussi en local.

Usage : langs_card.py <utilisateur>   (variable GITHUB_TOKEN facultative, évite la limite de l'API)
Codes de sortie : 0 = carte écrite, 3 = API inaccessible (la carte reste telle quelle).
"""
import json
import os
import sys
import urllib.request
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "langages.svg"
EXCLUDED = {"EnzoBuchaillat"}  # le dépôt de profil : son Python ne sert qu'aux cartes
TOP = 6

# Couleurs de GitHub (linguist), sauf C : son gris #555555 est invisible sur fond sombre.
COLORS = {
    "C": "#A8B9CC", "Java": "#b07219", "SQL": "#e38c00", "PLSQL": "#e38c00",
    "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "HTML": "#e34c26", "CSS": "#8f5bd6",
    "PHP": "#4F5D95", "Python": "#3572A5", "Shell": "#89e051", "Dockerfile": "#5d8fa6",
    "Kotlin": "#A97BFF", "C++": "#f34b7d", "Vue": "#41b883",
}
OTHER = "#6f7d9c"


def get(url: str):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "langs-card"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=20) as r:
        return json.load(r)


def totals(user: str) -> tuple[dict[str, int], int]:
    repos = get(f"https://api.github.com/users/{user}/repos?per_page=100&type=owner")
    counted = [r for r in repos if not r["fork"] and r["name"] not in EXCLUDED]
    langs: dict[str, int] = {}
    for repo in counted:
        for name, size in get(repo["languages_url"]).items():
            langs[name] = langs.get(name, 0) + size
    return langs, len(counted)


def card(langs: dict[str, int], repo_count: int) -> str:
    total = sum(langs.values())
    ranked = sorted(langs.items(), key=lambda kv: -kv[1])
    shown = [(n, s / total) for n, s in ranked[:TOP]]
    rest = sum(s for _, s in ranked[TOP:]) / total
    if rest > 0:
        shown.append(("Autres", rest))

    # Barre segmentée de 400 px, arrondie aux deux bouts grâce au clipPath.
    segments, x = [], 40.0
    for name, share in shown:
        w = 400 * share
        segments.append(f'<rect x="{x:.1f}" y="62" width="{w + 0.5:.1f}" height="12" fill="{COLORS.get(name, OTHER)}"/>')
        x += w

    # Légende sur deux colonnes.
    legend = []
    for i, (name, share) in enumerate(shown):
        cx, cy = (40 if i % 2 == 0 else 250), 104 + 24 * (i // 2)
        pct = f"{share * 100:.1f} %".replace(".", ",")
        legend.append(
            f'<circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{COLORS.get(name, OTHER)}"/>'
            f'<text x="{cx + 18}" y="{cy}" font-size="13" font-weight="600" fill="#ffffff">{escape(name)}</text>'
            f'<text x="{cx + 190}" y="{cy}" font-size="13" fill="#9aa6c1" text-anchor="end">{pct}</text>'
        )
    rows = (len(shown) + 1) // 2
    height = 104 + 24 * (rows - 1) + 30
    label = ", ".join(f"{n} {s * 100:.0f} %" for n, s in shown)
    font = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="480" height="{height}" viewBox="0 0 480 {height}" role="img" aria-label="Langages les plus utilisés : {escape(label)}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#1c2538"/>
      <stop offset="1" stop-color="#131a2a"/>
    </linearGradient>
    <clipPath id="bar"><rect x="40" y="62" width="400" height="12" rx="6"/></clipPath>
  </defs>
  <rect x="0.5" y="0.5" width="479" height="{height - 1}" rx="14" fill="url(#bg)" stroke="#2f3b57"/>
  <g font-family="{font}">
    <text x="40" y="38" font-size="12" font-weight="700" letter-spacing="1.5" fill="#7cc4ff">LANGAGES LES PLUS UTILISÉS</text>
    <text x="440" y="38" font-size="13" font-weight="600" fill="#9aa6c1" text-anchor="end">{repo_count} dépôts publics</text>
    <rect x="40" y="62" width="400" height="12" rx="6" fill="#2a3550"/>
    <g clip-path="url(#bar)">{"".join(segments)}</g>
    {"".join(legend)}
  </g>
</svg>
"""


def main() -> int:
    user = sys.argv[1] if len(sys.argv) > 1 else ""
    if not user:
        sys.stderr.write("usage: langs_card.py <utilisateur>\n")
        return 2
    try:
        langs, repo_count = totals(user)
    except Exception as exc:  # réseau, limite de l'API…
        sys.stderr.write(f"[langs-card] API inaccessible ({exc}), carte inchangée\n")
        return 3
    if not langs:
        sys.stderr.write("[langs-card] aucun langage trouvé, carte inchangée\n")
        return 3
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(card(langs, repo_count), encoding="utf-8")
    print(json.dumps({"depots": repo_count, "langages": langs}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
