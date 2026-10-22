#!/usr/bin/env bash
# Derive Phase 2 from the preserved standard Phase 1 sketch, without Python.
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SOURCE="$SCRIPT_DIR/../phase-1-blink/ArduinoISP/ArduinoISP.ino"
DEST="$SCRIPT_DIR/ArduinoISP_Relay/ArduinoISP_Relay.ino"
[ -f "$SOURCE" ] || { echo "Missing Phase 1 ArduinoISP source." >&2; exit 1; }
mkdir -p "$(dirname "$DEST")"
TEMP_FILE=$(mktemp "$DEST.tmp.XXXXXX")
trap 'rm -f "$TEMP_FILE"' EXIT

awk '
BEGIN {
    print "// Phase 2 additions: one-way telemetry with automatic ISP priority."
    print "// Target PB3 TX connects to Uno D4; no additional mode wire."
    print "#include <Arduino.h>"
    print "#include <SoftwareSerial.h>"
    print "unsigned long lastHostActivity = 0;"
    print "SoftwareSerial tinySerial(4, 3); // Uno RX=D4; unused TX=D3"
    print ""
}
{
    if (skip_state > 0) {
        if ((skip_state == 1 && $0 != "  if (SERIAL.available()) {") ||
            (skip_state == 2 && $0 != "    avrisp();") ||
            (skip_state == 3 && $0 != "  }")) {
            print "Unexpected ArduinoISP serial-handler layout." > "/dev/stderr"
            invalid_layout = 1
            exit 1
        }
        skip_state++
        if (skip_state == 4) skip_state = 0
        next
    }
    print
    if ($0 ~ /^  SERIAL.begin\(BAUDRATE\);$/) {
        setup_count++
        print "  tinySerial.begin(9600);"
        print "  tinySerial.stopListening();"
    }
    if ($0 ~ /^  heartbeat\(\);$/) {
        loop_count++
        print "  // Host requests take priority over target telemetry."
        print "  if (SERIAL.available()) {"
        print "    tinySerial.stopListening();"
        print "    lastHostActivity = millis();"
        print "    avrisp();"
        print "    return;"
        print "  }"
        print "  // Never receive/forward telemetry during ISP or shortly after host traffic."
        print "  if (pmode || (unsigned long)(millis() - lastHostActivity) < 250UL) {"
        print "    tinySerial.stopListening();"
        print "    return;"
        print "  }"
        print "  tinySerial.listen();"
        print "  while (tinySerial.available() && !SERIAL.available()) {"
        print "    SERIAL.write((uint8_t)tinySerial.read());"
        print "  }"
        skip_state = 1
    }
}
END {
    if (setup_count != 1 || loop_count != 1 || skip_state != 0 || invalid_layout) {
        print "Unexpected ArduinoISP source: expected one setup and one loop marker." > "/dev/stderr"
        exit 1
    }
}
' "$SOURCE" > "$TEMP_FILE"
chmod 644 "$TEMP_FILE"
mv "$TEMP_FILE" "$DEST"
echo "Created phase-2-serial/ArduinoISP_Relay/ArduinoISP_Relay.ino from Phase 1."
echo "Phase 1 source was not modified."
