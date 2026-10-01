#!/bin/zsh
# Met à jour la carte TryHackMe du README et la pousse sur GitHub si elle a changé.
# Lancé chaque jour par launchd (~/Library/LaunchAgents/com.enzobuchaillat.tryhackme-card.plist).
set -e
REPO="${0:A:h:h}"
cd "$REPO"

# Environnement Python isolé, créé au premier lancement.
if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
  .venv/bin/pip install -q curl_cffi
fi

.venv/bin/python scripts/thm_card.py ORZEX

if [[ -n "$(git status --porcelain -- assets/tryhackme.svg)" ]]; then
  git pull -q --rebase --autostash
  git add assets/tryhackme.svg
  git commit -q -m "chore: mettre à jour la carte TryHackMe"
  git push -q
  echo "carte poussée"
else
  echo "carte inchangée"
fi
