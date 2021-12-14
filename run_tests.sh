#!/bin/bash

python -m coverage run -m pytest tests.py
python -m coverage report
