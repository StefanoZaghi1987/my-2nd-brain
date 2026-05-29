#!/usr/bin/env bash
# Thin shim — delegates to the canonical Python bootstrapper (init_vault.py).
# Kept so users who reach for a .sh script by habit get the same result.
# All logic lives in init_vault.py; edit that file, not this one.
set -euo pipefail
python3 "$(dirname "$0")/init_vault.py" "$@"
