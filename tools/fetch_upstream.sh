#!/bin/sh
# Holt die Vorlage von Krypton in genau dem Stand, auf dem die Schrift aufbaut.
#   sh tools/fetch_upstream.sh            # Source Code Pro (nötig für den Build)
#   sh tools/fetch_upstream.sh --plex     # zusätzlich IBM Plex (nur Beschriftung in Probeabzügen)
set -eu
cd "$(dirname "$0")/.."

fetch() {  # Ziel, Repository, Commit
  if [ -d "$1/.git" ] && [ "$(git -C "$1" rev-parse HEAD)" = "$3" ]; then
    echo "$1: schon auf $3"; return
  fi
  rm -rf "$1"; mkdir -p "$1"
  git -C "$1" init -q
  git -C "$1" remote add origin "$2"
  git -C "$1" fetch -q --depth 1 origin "$3"
  git -C "$1" checkout -q FETCH_HEAD
  echo "$1: $2 @ $3"
}

# Source Code Pro (Adobe, OFL 1.1, Reserved Font Name "Source"), Branch main
fetch upstream/scp https://github.com/adobe-fonts/source-code-pro.git 2742c359adc781719571242f5e9e32bc77f1f74b

if [ "${1:-}" = "--plex" ]; then
  # IBM Plex (OFL 1.1), nur als Beschriftungsschrift in tools/proof.py, cmp.py, smallsizes.py
  fetch upstream/plex https://github.com/IBM/plex.git bc6a7e4b37634eb79785d59781893db63ee3edcb
fi
