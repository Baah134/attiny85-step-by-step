#!/usr/bin/env bash
# Upload standard ArduinoISP to the Uno, before target programming.
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/../scripts/common.sh"
[ "$#" -eq 1 ] && [ -n "$1" ] || fail "Usage: bash ./phase-1-blink/upload_isp.sh <Uno port>"
UNO_PORT="$1"
ensure_local_setup
printf 'Disconnect one leg of the Uno reset capacitor, then press ENTER: '
read -r answer || fail "No confirmation received; stopping."
local_cli compile --fqbn arduino:avr:uno \
    --build-property "compiler.path=$PHASE_COMPILER_BIN" \
    --build-path "$PROJECT_ROOT/build/uno" "$SCRIPT_DIR/ArduinoISP"
local_cli upload --fqbn arduino:avr:uno -p "$UNO_PORT" \
    --input-dir "$PROJECT_ROOT/build/uno" "$SCRIPT_DIR/ArduinoISP"
echo "Uno upload complete. Reconnect the Uno reset capacitor before programming the ATtiny85."
