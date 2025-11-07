#!/bin/bash
set -e

# User-friendly setup script for prometheus-metric-summarizer virtual environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
VENV_DIR="../venv"

echo "Project root detected at: $PROJECT_ROOT"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    if ! python3 -m venv "$VENV_DIR"; then
        echo "Error: Failed to create virtual environment." >&2
        exit 1
    fi
else
    echo "Virtual environment already exists at $VENV_DIR"
fi

echo "Activating virtual environment..."
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    echo "Installing requirements from requirements.txt..."
    if ! pip install -r "$PROJECT_ROOT/requirements.txt"; then
        echo "Error: Failed to install requirements." >&2
        exit 1
    fi
else
    echo "No requirements.txt found, skipping requirements installation."
fi

if [ -f "$PROJECT_ROOT/pyproject.toml" ]; then
    echo "Performing editable install of the project..."
    if ! pip install -e "$PROJECT_ROOT"; then
        echo "Error: Failed to perform editable install." >&2
        exit 1
    fi
else
    echo "No pyproject.toml found, skipping editable install."
fi

echo
echo "Setup complete. Virtual environment is activated."
echo "You can now run 'promsum' or other commands within this shell."
echo "To deactivate the virtual environment, run 'deactivate'."
echo
exec "$SHELL" -i
