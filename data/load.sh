#!/usr/bin/env bash
set -euo pipefail
set -x
cd "$(dirname "$0")"
curl -o prijsarchief.csv "https://www.salderingswijzer.nl/prijsarchief.csv"
curl -o knmi_uurgegevens_344.txt \
  -d "stns=344" -d "vars=Q" -d "start=2023010101" -d "end=2026101524" \
  "https://www.daggegevens.knmi.nl/klimatologie/uurgegevens"
mkdir -p raw
curl -o raw/fluvius_2024_deel1.zip \
  "https://fluvius.opendatasoft.com/api/v2/catalog/datasets/1_50-verbruiksprofielen-dm-elek-kwartierwaarden-voor-een-volledig-jaar/attachments/p6269_1_50_dmk_sample_elek_2024_deel_1_zip"
../.venv/bin/python prep_load.py raw/fluvius_2024_deel1.zip
