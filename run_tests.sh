#!/bin/bash

python -m coverage run -m pytest tests/* -v
python -m coverage report
