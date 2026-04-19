#!/bin/bash
# Weekly Scorecard Dashboard — one-click refresh (macOS / Linux)
# Double-click this file in Finder to rebuild the dashboard from your archive.

set -e
cd "$(dirname "$0")"

echo "================================================"
echo "  Weekly Scorecard — Dashboard Refresh"
echo "================================================"
echo

# Find a python3 interpreter
PY=""
for cand in python3 python; do
  if command -v $cand >/dev/null 2>&1; then
    PY=$cand
    break
  fi
done

if [ -z "$PY" ]; then
  echo "ERROR: no Python 3 found on PATH."
  echo "Install Python from https://www.python.org/downloads/ and try again."
  read -p "Press Enter to close..." _
  exit 1
fi

# Ensure required libraries exist (quiet install if missing)
$PY -c "import pandas, numpy, openpyxl" 2>/dev/null || {
  echo "Installing required Python packages (one-time setup)..."
  $PY -m pip install --user pandas numpy openpyxl --quiet || {
    echo "pip install failed. Try:  $PY -m pip install pandas numpy openpyxl"
    read -p "Press Enter to close..." _
    exit 1
  }
}

$PY .scorecard/refresh.py

echo
echo "Dashboard rebuilt. Opening Signal_Dashboard.xlsx..."
if command -v open >/dev/null 2>&1; then
  open "Signal_Dashboard.xlsx" || true
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "Signal_Dashboard.xlsx" || true
fi

echo
read -p "Press Enter to close..." _
