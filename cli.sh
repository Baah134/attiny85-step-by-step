#!/usr/bin/env bash
# Project-local Arduino CLI, configured for this project's current location.
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/scripts/common.sh"
ensure_local_setup
local_cli "$@"
