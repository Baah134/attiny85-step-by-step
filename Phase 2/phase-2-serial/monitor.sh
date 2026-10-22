#!/usr/bin/env bash
# Open the relay monitor without flashing the target again.
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/../scripts/common.sh"
[ "$#" -eq 1 ] && [ -n "$1" ] || fail "Usage: bash ./phase-2-serial/monitor.sh <Uno port>"
UNO_PORT="$1"
ensure_local_setup
echo "Keep the Uno reset capacitor connected."
echo "Monitor: $UNO_PORT at 19200 baud. ATtiny software TX stays at 9600 baud."
echo "Press Ctrl+C to exit. Close this monitor before programming again."
local_cli monitor -p "$UNO_PORT" -c baudrate=19200
