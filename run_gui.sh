#!/bin/bash
# Convenience script to run the GUI with venv activated

cd "$(dirname "$0")"
source .venv/bin/activate
python class_roster_ui.py
