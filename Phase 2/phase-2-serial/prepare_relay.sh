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
    print "// Phase 2 additions: one-way telemetry and a hardware mode selector."
    print "// Uno D2 open = programmer; D2 connected to GND = telemetry."
    print "#include <Arduino.h>"
    print "#include <SoftwareSerial.h>"
    print "const uint8_t RELAY_MODE_PIN = 2;"
    print "SoftwareSerial tinySerial(4, 3); // Uno RX=D4; unused TX=D3"
    print ""
}
{
    print
    if ($0 ~ /^  SERIAL.begin\(BAUDRATE\);$/) {
        setup_count++
        print "  pinMode(RELAY_MODE_PIN, INPUT_PULLUP);"
        print "  tinySerial.begin(9600);"
        print "  tinySerial.stopListening();"
    }
    if ($0 ~ /^  heartbeat\(\);$/) {
        loop_count++
        print "  // Keep telemetry separate from the STK500 programmer protocol."
        print "  if (!pmode && digitalRead(RELAY_MODE_PIN) == LOW) {"
        print "    tinySerial.listen();"
        print "    while (tinySerial.available()) {"
        print "      SERIAL.write((uint8_t)tinySerial.read());"
        print "    }"
        print "    // Terminal keystrokes must not enter the ISP command parser."
        print "    while (SERIAL.available()) { SERIAL.read(); }"
        print "    return;"
        print "  }"
        print "  // Disable software RX interrupts during programmer communication."
        print "  tinySerial.stopListening();"
    }
}
END {
    if (setup_count != 1 || loop_count != 1) {
        print "Unexpected ArduinoISP source: expected one setup and one loop marker." > "/dev/stderr"
        exit 1
    }
}
' "$SOURCE" > "$TEMP_FILE"
chmod 644 "$TEMP_FILE"
mv "$TEMP_FILE" "$DEST"
echo "Created phase-2-serial/ArduinoISP_Relay/ArduinoISP_Relay.ino from Phase 1."
echo "Phase 1 source was not modified."
