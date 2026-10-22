#!/usr/bin/env bash
# Phase 2: program at 8 MHz, optionally opening the relay monitor afterward.
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/../scripts/common.sh"
PORT=""
TARGET="$SCRIPT_DIR/serial_demo"
OPEN_MONITOR=false
usage() {
    echo "Usage: bash ./phase-2-serial/burn.sh -p <Uno port> [-f <sketch|.ino|.hex>] [-m]"
    echo "Fixed 8 MHz target clock; -m opens the 19200-baud monitor after a successful burn."
}
while getopts ":p:f:mh" opt; do
    case "$opt" in
        p) PORT="$OPTARG" ;;
        f) TARGET="$OPTARG" ;;
        m) OPEN_MONITOR=true ;;
        h) usage; exit 0 ;;
        *) usage >&2; exit 1 ;;
    esac
done
shift "$((OPTIND - 1))"
[ "$#" -eq 0 ] || fail "Unexpected arguments."
[ -n "$PORT" ] || fail "Specify the Uno port with -p. Run bash ./cli.sh board list."
ensure_local_setup

if [[ "$TARGET" == *.hex ]]; then
    [ -s "$TARGET" ] || fail "HEX file missing or empty: $TARGET"
    HEX_FILE="$TARGET"
else
    if [ -d "$TARGET" ]; then
        SKETCH_DIR=$(cd "$TARGET" && pwd)
    elif [[ "$TARGET" == *.ino ]] && [ -f "$TARGET" ]; then
        SKETCH_DIR=$(cd "$(dirname "$TARGET")" && pwd)
    else
        fail "Sketch not found: $TARGET"
    fi
    SKETCH_NAME=$(basename "$SKETCH_DIR")
    [ -f "$SKETCH_DIR/$SKETCH_NAME.ino" ] || fail "Expected $SKETCH_NAME.ino in sketch folder."
    LIBRARY="$RUNTIME_DIR/data/packages/arduino/hardware/avr/$ARDUINO_AVR_VERSION/libraries/SoftwareSerial"
    [ -d "$LIBRARY" ] || fail "SoftwareSerial library missing. Rerun bash ./setup.sh."
    BUILD_DIR="$PROJECT_ROOT/build/phase2_8MHz"
    HEX_FILE="$BUILD_DIR/$SKETCH_NAME.ino.hex"
    rm -f "$HEX_FILE"
    local_cli compile --fqbn attiny:avr:ATtinyX5:cpu=attiny85,clock=internal8 \
        --build-property "compiler.path=$PHASE_COMPILER_BIN" \
        --library "$LIBRARY" --build-path "$BUILD_DIR" "$SKETCH_DIR"
    [ -s "$HEX_FILE" ] || fail "Expected compiled HEX file missing: $HEX_FILE"
fi

printf 'Keep the Uno reset capacitor connected, then press ENTER to program: '
read -r answer || fail "No confirmation received; stopping."
echo "Programming ATtiny85 at 8 MHz through $PORT..."
"$PHASE_AVRDUDE" -C "$PHASE_AVRDUDE_CONF" \
    -p attiny85 -c stk500v1 -P "$PORT" -b 19200 \
    -U efuse:w:0xFF:m \
    -U hfuse:w:0xDF:m \
    -U lfuse:w:0xE2:m \
    -U flash:w:"$HEX_FILE":i

echo "Programming succeeded. Software TX is 9600 baud; relay monitor is 19200 baud."
if [ "$OPEN_MONITOR" = true ]; then
    bash "$SCRIPT_DIR/monitor.sh" "$PORT"
fi
