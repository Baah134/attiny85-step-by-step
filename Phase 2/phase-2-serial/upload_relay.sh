#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/../scripts/common.sh"
[ "$#" -eq 1 ] && [ -n "$1" ] || fail "Usage: bash ./phase-2-serial/upload_relay.sh <Uno port>"
UNO_PORT="$1"
ensure_local_setup
[ -s "$SCRIPT_DIR/ArduinoISP_Relay/ArduinoISP_Relay.ino" ] || fail "Run prepare_relay.sh first."
printf 'Disconnect one leg of the Uno reset capacitor, then press ENTER: '
read -r answer || fail "No confirmation received; stopping."
local_cli compile --fqbn arduino:avr:uno \
    --build-property "compiler.path=$PHASE_COMPILER_BIN" \
    --build-path "$PROJECT_ROOT/build/phase2_uno" "$SCRIPT_DIR/ArduinoISP_Relay"
local_cli upload --fqbn arduino:avr:uno -p "$UNO_PORT" \
    --input-dir "$PROJECT_ROOT/build/phase2_uno" "$SCRIPT_DIR/ArduinoISP_Relay"
echo "Relay uploaded. Reconnect the Uno reset capacitor before programming the ATtiny85."
