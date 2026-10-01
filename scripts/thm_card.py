#!/usr/bin/env python3
"""Génère assets/tryhackme.svg à partir du profil public TryHackMe.

L'API de TryHackMe est derrière la protection anti-bot de Vercel : une requête
classique (curl, GitHub Actions) est bloquée. curl_cffi imite la poignée de main
TLS d'un vrai navigateur, ce qui suffit depuis une connexion résidentielle.
C'est pour ça que ce script tourne sur le Mac, pas dans GitHub Actions.

Usage : thm_card.py <pseudo>   (écrit assets/tryhackme.svg à la racine du dépôt)
Codes de sortie : 0 = carte écrite, 3 = profil inaccessible (la carte reste telle quelle).
"""
import json
import sys
from html import escape
from pathlib import Path

from curl_cffi import requests

API = "https://tryhackme.com/api/v2/public-profile"
OUT = Path(__file__).resolve().parent.parent / "assets" / "tryhackme.svg"

# Paliers officiels du capability score (help.tryhackme.com).
TIERS = [
    (90, "Senior Security Professional"),
    (60, "Mid-level Security Professional"),
    (35, "Junior Security Professional"),
    (20, "Security Student"),
    (0, "Security Enthusiast"),
]

LEAGUES = {
    "bronze": "Bronze", "silver": "Argent", "gold": "Or", "platinum": "Platine",
    "diamond": "Diamant", "ruby": "Rubis", "sapphire": "Saphir", "amethyst": "Améthyste",
    "emerald": "Émeraude", "pearl": "Perle", "obsidian": "Obsidienne",
}


def fetch(username: str) -> dict | None:
    for profile in ("chrome", "chrome131", "safari"):
        try:
            resp = requests.get(API, params={"username": username}, impersonate=profile,
                                headers={"accept": "application/json"}, timeout=25)
        except Exception:
            continue
        if resp.status_code == 200 and "json" in resp.headers.get("content-type", ""):
            payload = resp.json()
            if payload.get("status") == "success":
                return payload["data"]
    return None


def tier(score: float) -> str:
    return next(name for floor, name in TIERS if score >= floor)


def card(d: dict) -> str:
    score = float((d.get("capabilityScore") or {}).get("value") or 0)
    shown = int(score)
    bar = round(400 * min(score, 100) / 100)
    rooms = d.get("completedRoomsNumber", 0)
    badges = d.get("badgesNumber", 0)
    league = LEAGUES.get(d.get("leagueTier", ""), (d.get("leagueTier") or "").capitalize())
    stats = f"{rooms} salles terminées  ·  {badges} badges"
    if league:
        stats += f"  ·  ligue {league}"
    # Repères des paliers sur la barre (20, 35, 60, 90).
    ticks = "".join(
        f'<rect x="{40 + round(400 * t / 100) - 1}" y="104" width="2" height="12" fill="#0f1626" opacity="0.9"/>'
        for t in (20, 35, 60, 90)
    )
    font = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="480" height="170" viewBox="0 0 480 170" role="img" aria-label="TryHackMe : capability score {shown} sur 100, {escape(tier(score))}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#1c2538"/>
      <stop offset="1" stop-color="#131a2a"/>
    </linearGradient>
    <linearGradient id="fill" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#4cbb17"/>
      <stop offset="1" stop-color="#a3ea2a"/>
    </linearGradient>
  </defs>
  <rect x="0.5" y="0.5" width="479" height="169" rx="14" fill="url(#bg)" stroke="#2f3b57"/>
  <g font-family="{font}">
    <text x="40" y="38" font-size="12" font-weight="700" letter-spacing="1.5" fill="#a3ea2a">TRYHACKME</text>
    <text x="440" y="38" font-size="13" font-weight="600" fill="#9aa6c1" text-anchor="end">{escape(d.get("username", ""))}</text>
    <text x="40" y="86" font-size="44" font-weight="800" fill="#ffffff">{shown}<tspan font-size="18" font-weight="600" fill="#6f7d9c"> / 100</tspan></text>
    <text x="440" y="66" font-size="11" font-weight="600" letter-spacing="1" fill="#6f7d9c" text-anchor="end">CAPABILITY SCORE</text>
    <text x="440" y="86" font-size="15" font-weight="700" fill="#ffffff" text-anchor="end">{escape(tier(score))}</text>
    <rect x="40" y="104" width="400" height="12" rx="6" fill="#2a3550"/>
    <rect x="40" y="104" width="{bar}" height="12" rx="6" fill="url(#fill)"/>
    {ticks}
    <text x="40" y="146" font-size="13" fill="#9aa6c1">{escape(stats)}</text>
  </g>
</svg>
"""


def main() -> int:
    username = sys.argv[1] if len(sys.argv) > 1 else ""
    if not username:
        sys.stderr.write("usage: thm_card.py <pseudo>\n")
        return 2
    data = fetch(username)
    if data is None:
        sys.stderr.write("[thm-card] profil inaccessible, carte inchangée\n")
        return 3
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(card(data), encoding="utf-8")
    print(json.dumps({"score": (data.get("capabilityScore") or {}).get("value"),
                      "rooms": data.get("completedRoomsNumber")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
