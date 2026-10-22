#!/usr/bin/env bash
# Compile both Phase 2 sketches before touching hardware.
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/../scripts/common.sh"
ensure_local_setup
LIBRARY="$RUNTIME_DIR/data/packages/arduino/hardware/avr/$ARDUINO_AVR_VERSION/libraries/SoftwareSerial"
[ -d "$LIBRARY" ] || fail "SoftwareSerial library missing. Rerun bash ./setup.sh."
[ -s "$SCRIPT_DIR/ArduinoISP_Relay/ArduinoISP_Relay.ino" ] || fail "Run bash ./phase-2-serial/prepare_relay.sh first."
local_cli compile --fqbn arduino:avr:uno \
    --build-property "compiler.path=$PHASE_COMPILER_BIN" \
    --build-path "$PROJECT_ROOT/build/phase2_uno" "$SCRIPT_DIR/ArduinoISP_Relay"
local_cli compile --fqbn attiny:avr:ATtinyX5:cpu=attiny85,clock=internal8 \
    --build-property "compiler.path=$PHASE_COMPILER_BIN" \
    --library "$LIBRARY" \
    --build-path "$PROJECT_ROOT/build/phase2_8MHz" "$SCRIPT_DIR/serial_demo"
echo "Both Phase 2 sketches compiled. No hardware was programmed."
