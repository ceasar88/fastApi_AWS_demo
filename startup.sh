#!/bin/bash
python3 -m venv ./venv
source ./venv/bin/activate
cd api
cd src
pip install -r requirements.txt
pip install --editable .
python functions/app.py