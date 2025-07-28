#!/usr/bin/env bash

rm -r dist
python3 -m build
python3 -m twine upload --repository testpypi dist/*
#pip install --force-reinstall dist/flint2025_manager-0.1-py3-none-any.whl
