#!/usr/bin/env bash
# Install a self-contained Phase 1 toolchain. No Homebrew or global Arduino install.
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/scripts/common.sh"

[ "$(uname -s)" = Darwin ] || fail "This installer currently supports macOS."
for required in curl tar sh; do
    command -v "$required" >/dev/null 2>&1 || fail "Required macOS system utility missing: $required"
done

mkdir -p "$RUNTIME_DIR/bin"
rm -f "$RUNTIME_DIR/ready"
if ! cli_version_matches; then
    echo "Downloading Arduino CLI into the project..."
    curl -fsSL --retry 3 \
        "https://raw.githubusercontent.com/arduino/arduino-cli/$CLI_INSTALLER_COMMIT/install.sh" \
        -o "$RUNTIME_DIR/install-arduino-cli.sh"
    BINDIR="$RUNTIME_DIR/bin" sh "$RUNTIME_DIR/install-arduino-cli.sh" "$CLI_VERSION"
fi

cli_version_matches || fail "Arduino CLI did not install the expected version $CLI_VERSION."
configure_local_cli
local_cli core update-index
local_cli core install "arduino:avr@$ARDUINO_AVR_VERSION"
local_cli core install "attiny:avr@$ATTINY_AVR_VERSION"

# Check downloaded tools without installing or changing system components.
find_local_tools || fail "A downloaded AVR executable is missing or cannot run on this Mac. Review the package installation output above."

# Verify actual builds before marking setup complete; no hardware is programmed.
echo "Verifying the Uno and ATtiny85 toolchains..."
local_cli compile --fqbn arduino:avr:uno \
    --build-property "compiler.path=$PHASE_COMPILER_BIN" \
    --build-path "$RUNTIME_DIR/verify/uno" "$PROJECT_ROOT/phase-1-blink/ArduinoISP"
local_cli compile --fqbn attiny:avr:ATtinyX5:cpu=attiny85,clock=internal1 \
    --build-property "compiler.path=$PHASE_COMPILER_BIN" \
    --build-path "$RUNTIME_DIR/verify/attiny" "$PROJECT_ROOT/phase-1-blink/blink"
{
    "$LOCAL_CLI" version
    local_cli core list
    "${PHASE_COMPILER_BIN}avr-g++" --version
} > "$RUNTIME_DIR/versions.txt"
toolset_id > "$RUNTIME_DIR/ready"
echo "Setup complete: CLI, board cores, AVR compiler, and AVRDUDE are installed locally."
echo "Next: bash ./cli.sh board list"
