#!/usr/bin/env bash
set -euo pipefail
set -x
cd "$(dirname "$0")"
curl -o prijsarchief.csv "https://www.salderingswijzer.nl/prijsarchief.csv"
curl -o knmi_uurgegevens_344.txt \
  -d "stns=344" -d "vars=Q" -d "start=2023010101" -d "end=2026101524" \
  "https://www.daggegevens.knmi.nl/klimatologie/uurgegevens"
