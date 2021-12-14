#!/bin/bash

python -m coverage run -m pytest tests.py -v
python -m coverage report
