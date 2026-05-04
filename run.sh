#!/usr/bin/env bash
# Run the policy formalization pipeline.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -f "${SCRIPT_DIR}/.env" ]; then
    set -a
    source "${SCRIPT_DIR}/.env"
    set +a
fi

: "${ANTHROPIC_API_KEY:?Set ANTHROPIC_API_KEY in .env or environment}"

exec "${SCRIPT_DIR}/.venv/bin/python" "${SCRIPT_DIR}/scripts/run_pipeline.py" "$@"
