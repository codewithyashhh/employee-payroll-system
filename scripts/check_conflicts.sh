#!/usr/bin/env bash
set -euo pipefail
if rg -n "<<<<<<<|=======|>>>>>>>" app.py templates static README.md >/tmp/conflict_scan.txt; then
  echo "Merge conflict markers detected:"
  cat /tmp/conflict_scan.txt
  exit 1
fi

echo "No merge conflict markers detected."
