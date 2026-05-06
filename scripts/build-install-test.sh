#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_DIR
cd ..
mkdir -p dist
rm dist/*
python3 -m build
pip install --force-reinstall --no-deps dist/threequick*.whl
python3 scripts/example.py
# python3 -m twine upload --repository testpypi dist/*
