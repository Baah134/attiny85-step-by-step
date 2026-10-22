#!/usr/bin/env bash
# Shared paths are calculated at runtime, so the project can be moved.
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
RUNTIME_DIR="$PROJECT_ROOT/.runtime"
LOCAL_CLI="$RUNTIME_DIR/bin/arduino-cli"
LOCAL_CONFIG="$RUNTIME_DIR/arduino-cli.yaml"
source "$PROJECT_ROOT/scripts/versions.sh"

fail() { echo "Error: $*" >&2; exit 1; }

local_cli() {
    # Global ARDUINO_* environment settings must not redirect this project to
    # another installation. Changes are confined to this subprocess.
    (
        while IFS= read -r setting; do
            case "$setting" in ARDUINO_*) unset "$setting" ;; esac
        done < <(compgen -e)
        "$LOCAL_CLI" --config-file "$LOCAL_CONFIG" "$@"
    )
}

cli_version_matches() {
    [ -x "$LOCAL_CLI" ] || return 1
    case "$("$LOCAL_CLI" version 2>/dev/null) " in
        *"Version: $CLI_VERSION "*) return 0 ;;
        *) return 1 ;;
    esac
}

toolset_id() { printf '%s %s %s' "$CLI_VERSION" "$ARDUINO_AVR_VERSION" "$ATTINY_AVR_VERSION"; }

configure_local_cli() {
    mkdir -p "$RUNTIME_DIR/data" "$RUNTIME_DIR/downloads" "$RUNTIME_DIR/user" "$RUNTIME_DIR/cache"
    # Write paths through the CLI, rather than hand-escaping YAML.
    printf '{}\n' > "$LOCAL_CONFIG"
    local_cli config set directories.data "$RUNTIME_DIR/data"
    local_cli config set directories.downloads "$RUNTIME_DIR/downloads"
    local_cli config set directories.user "$RUNTIME_DIR/user"
    local_cli config set build_cache.path "$RUNTIME_DIR/cache"
    local_cli config add board_manager.additional_urls \
        https://raw.githubusercontent.com/damellis/attiny/ide-1.6.x-boards-manager/package_damellis_attiny_index.json
}

find_local_tools() {
    PHASE_AVRDUDE=""
    PHASE_AVRDUDE_CONF=""
    PHASE_COMPILER_BIN=""
    shopt -s nullglob
    for candidate in "$RUNTIME_DIR"/data/packages/*/tools/avrdude/*/bin/avrdude; do
        tool_root=$(dirname "$(dirname "$candidate")")
        if [ -x "$candidate" ] && [ -f "$tool_root/etc/avrdude.conf" ] &&
            "$candidate" "-?" >/dev/null 2>&1; then
            PHASE_AVRDUDE="$candidate"
            PHASE_AVRDUDE_CONF="$tool_root/etc/avrdude.conf"
        fi
    done
    for candidate in "$RUNTIME_DIR"/data/packages/arduino/tools/avr-gcc/*/bin/avr-g++; do
        if [ -x "$candidate" ] && "$candidate" --version >/dev/null 2>&1; then
            PHASE_COMPILER_BIN="$(dirname "$candidate")/"
        fi
    done
    shopt -u nullglob
    [ -n "$PHASE_AVRDUDE" ] && [ -n "$PHASE_COMPILER_BIN" ]
}

ensure_local_setup() {
    if [ ! -f "$RUNTIME_DIR/ready" ] ||
        [ "$(cat "$RUNTIME_DIR/ready" 2>/dev/null)" != "$(toolset_id)" ] ||
        ! cli_version_matches; then
        bash "$PROJECT_ROOT/setup.sh"
    fi
    configure_local_cli
    if ! find_local_tools; then
        echo "Local tools are missing or cannot run. Rechecking the installation..."
        bash "$PROJECT_ROOT/setup.sh"
        configure_local_cli
        find_local_tools || fail "The local toolchain is not usable. See setup output."
    fi
}
