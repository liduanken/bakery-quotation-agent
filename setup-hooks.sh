#!/bin/bash
# Setup script to install git hooks

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
GIT_DIR="$(git rev-parse --git-dir)"

echo "Installing git hooks..."

# Create hooks directory if it doesn't exist
mkdir -p "$GIT_DIR/hooks"

# Link pre-commit hook
if [ -f "$SCRIPT_DIR/.git-hooks/pre-commit" ]; then
    ln -sf "$SCRIPT_DIR/.git-hooks/pre-commit" "$GIT_DIR/hooks/pre-commit"
    chmod +x "$SCRIPT_DIR/.git-hooks/pre-commit"
    echo "✅ Pre-commit hook installed"
else
    echo "❌ Pre-commit hook file not found"
fi

echo "Done!"
