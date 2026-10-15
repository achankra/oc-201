#!/usr/bin/env bash
# Install the OpenChoreo developer and platform engineer skills.
# To see every skill first: npx skills add openchoreo/skills --list
set -eu

if ! command -v npx >/dev/null 2>&1; then
  echo "npx was not found. Install Node.js 18 or newer first." >&2
  exit 1
fi

npx skills add openchoreo/skills --skill openchoreo-developer
npx skills add openchoreo/skills --skill openchoreo-platform-engineer
