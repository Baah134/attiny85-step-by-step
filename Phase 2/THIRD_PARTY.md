# Third-party source

`phase-1-blink/ArduinoISP/ArduinoISP.ino` is an unmodified copy of the standard ArduinoISP example from the Arduino project. Its upstream copyright and license notice are preserved in the source.

- Upstream: https://github.com/arduino/arduino-examples
- Source: https://github.com/arduino/arduino-examples/blob/58cf44a15a18560087ac18fc23238e437867dac9/examples/11.ArduinoISP/ArduinoISP/ArduinoISP.ino
- Commit: `58cf44a15a18560087ac18fc23238e437867dac9`
- Copyright notice: Randall Bohn, 2008–2011.

The Phase 1 guide downloads this same pinned source.

## Phase 2 derivative

`phase-2-serial/ArduinoISP_Relay/ArduinoISP_Relay.ino` is generated from the preserved Phase 1 standard ArduinoISP source using `phase-2-serial/prepare_relay.sh`. The upstream notice remains in the generated file. Added code initializes SoftwareSerial on Uno D4 and forwards telemetry while idle, with priority for programmer requests.

SoftwareSerial is supplied by the pinned Arduino AVR core, installed by project setup. It is not vendored in this update package.
