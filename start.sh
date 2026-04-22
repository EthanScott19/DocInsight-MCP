#!/bin/zsh

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"
SRC_PATH="$PROJECT_ROOT/src"
REQ_PATH="$PROJECT_ROOT/requirements.txt"

if [ ! -d "$VENV_PATH" ]; then
  echo "Creating virtual environment..."
  python3 -m venv "$VENV_PATH"
fi

source "$VENV_PATH/bin/activate"

if [ -f "$REQ_PATH" ]; then
  pip install -r "$REQ_PATH"
fi

cd "$SRC_PATH"

python init_db.py
python app.py