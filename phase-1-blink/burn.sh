#!/usr/bin/env bash
# Phase 1: program one ATtiny85 at 1 MHz using only project-local tools.
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/../scripts/common.sh"
PORT=""
TARGET="$SCRIPT_DIR/blink"
usage() {
    echo "Usage: bash ./phase-1-blink/burn.sh -p <Uno port> [-f <sketch folder|.ino|.hex>]"
}
while getopts ":p:f:h" opt; do
    case "$opt" in
        p) PORT="$OPTARG" ;;
        f) TARGET="$OPTARG" ;;
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
    BUILD_DIR="$PROJECT_ROOT/build/phase1_1MHz"
    HEX_FILE="$BUILD_DIR/$SKETCH_NAME.ino.hex"
    # Do not accidentally reuse an older build if no new artifact is produced.
    rm -f "$HEX_FILE"
    local_cli compile --fqbn attiny:avr:ATtinyX5:cpu=attiny85,clock=internal1 \
        --build-property "compiler.path=$PHASE_COMPILER_BIN" \
        --build-path "$BUILD_DIR" "$SKETCH_DIR"
    [ -s "$HEX_FILE" ] || fail "Expected compiled HEX file missing: $HEX_FILE"
fi

echo "Programming ATtiny85 at 1 MHz through $PORT..."
"$PHASE_AVRDUDE" -C "$PHASE_AVRDUDE_CONF" \
    -p attiny85 -c stk500v1 -P "$PORT" -b 19200 \
    -U efuse:w:0xFF:m \
    -U hfuse:w:0xDF:m \
    -U lfuse:w:0x62:m \
    -U flash:w:"$HEX_FILE":i

echo "Programming succeeded. Check for seven startup flashes, then one blink cycle per second."
