# Phase 2 — Modify the ISP, add telemetry, then update the burn command

**Start here after Phase 1 works.** Use the same Uno, ATtiny85, ISP wiring, LED, local toolchain, and macOS compatibility requirements. Run all commands from the repository root. Phase 1 files remain available in `phase-1-blink`.

## 1. Add the Phase 2 files and select the Uno port

Copy the Phase 2 update package into the existing repository, merging its folders. Keep the Phase 1 files and shared scripts. This phase reuses the local toolchain and does not add a separate installer or system packages.

```bash
bash ./cli.sh board list
printf '\nEnter your Uno port exactly as shown above: '
read -r PORT
```

Use your actual port. An unset or empty port stops the upload/programming commands below. Close any serial monitor before uploading or programming.

## 2. Modify a copy of standard ArduinoISP

```bash
bash ./phase-2-serial/prepare_relay.sh
```

The generator reads the preserved Phase 1 sketch and creates:

`phase-2-serial/ArduinoISP_Relay/ArduinoISP_Relay.ino`

It makes three changes:

1. Adds `SoftwareSerial tinySerial(4, 3)` to receive the target's 9600-baud TX on Uno digital pin 4. Uno pin 3 is an unused software TX output; leave it unconnected.
2. Initializes the receiver at 9600 baud.
3. Adds automatic forwarding when the programmer is idle, while retaining the heartbeat and giving host ISP requests priority.

There is no extra mode connection. The relay disables software reception during an active ISP session and waits 250 ms after host activity before resuming telemetry. You only close the monitor before programming and reopen it afterward.

This shares one USB serial stream between programming replies and telemetry. An already-transmitting application can still put bytes into that stream before the initial handshake. If a later burn cannot synchronize, temporarily disconnect the telemetry wire at Uno D4 while programming, then reconnect it for monitoring. This is a troubleshooting fallback, not a normal mode-selection step.

The generator uses macOS's built-in `awk`, not Python. It checks the expected source markers and stops if they do not match. Rerunning it recreates the Phase 2 sketch and overwrites custom edits to that generated copy. It never edits Phase 1.

**Checkpoint:** inspect the new sketch; standard ArduinoISP still exists in Phase 1.

## 3. Check compilation, then upload the relay to the Uno

Compile both Phase 2 sketches without programming hardware:

```bash
bash ./phase-2-serial/check.sh
```

**Checkpoint:** both sketches compile. The target build uses 8 MHz. The bundled Arduino AVR core supplies SoftwareSerial; no library-manager installation is needed.

Disconnect one leg of the **Uno RESET-to-GND 10 µF capacitor**, then upload:

```bash
bash ./phase-2-serial/upload_relay.sh "${PORT:?Select your Uno port in Step 1}"
```

The script pauses to confirm the capacitor is disconnected, then compiles and uploads the relay firmware. It stops on errors.

After successful upload, reconnect the Uno reset capacitor.

**Checkpoint:** the Uno now runs the modified relay sketch, while the ATtiny85 may still be running its Phase 1 blink application.

## 4. Add the telemetry wire

Disconnect USB power while changing wiring. Keep the existing ISP connections and common ground.

| Additional connection | Purpose |
| --- | --- |
| ATtiny85 physical pin 2 (PB3 / software TX) → Uno digital pin 4 | Target telemetry to Uno software RX. |

Do not confuse Uno digital pin 4 with ATtiny85 physical pin 4, which is ground. Leave ATtiny85 physical pin 3 (unused software RX) and Uno digital pin 3 (unused software TX) unconnected.

Reconnect USB and keep the Uno reset capacitor connected.

## 5. Create the target telemetry application

The supplied file is `phase-2-serial/serial_demo/serial_demo.ino`. For the presentation, recreate it in the terminal with this block. It overwrites that example file; preserve personal edits first.

```bash
mkdir -p phase-2-serial/serial_demo
cat > phase-2-serial/serial_demo/serial_demo.ino <<'SKETCH'
#include <SoftwareSerial.h>

// ATtiny85 Arduino pin 0 = PB0 = physical DIP pin 5 (LED).
// Arduino pin 3 = PB3 = physical DIP pin 2 (TX to Uno D4).
// Arduino pin 4 = PB4 = physical DIP pin 3 (unused RX).
const byte LED_PIN = 0;
SoftwareSerial telemetry(4, 3);
unsigned long packet = 0;

void setup() {
  pinMode(LED_PIN, OUTPUT);
  telemetry.begin(9600);
  for (byte i = 0; i < 5; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(50);
    digitalWrite(LED_PIN, LOW);
    delay(50);
  }
  telemetry.println(F("ATtiny85 telemetry: 8 MHz, TX 9600 baud"));
}

void loop() {
  digitalWrite(LED_PIN, HIGH);
  telemetry.print(F("[ATtiny85] Packet #"));
  telemetry.print(packet++);
  telemetry.print(F(" | uptime="));
  telemetry.print(millis() / 1000UL);
  telemetry.println(F("s | LED=ON"));
  delay(500);
  digitalWrite(LED_PIN, LOW);
  delay(500);
}
SKETCH
```

The ATtiny85 has no hardware UART. SoftwareSerial transmits on PB3 at 9600 baud. Five startup flashes identify the new application; subsequent LED cycles accompany packets containing a counter and uptime.

## 6. Introduce the Phase 2 burn script

Phase 1's [burn script](../phase-1-blink/burn.sh) remains unchanged. The new [Phase 2 burn script](../phase-2-serial/burn.sh) changes the compilation clock to `internal8`, the low fuse to `0xE2`, the default application to `serial_demo`, and adds `-m` for the monitor.

| Setting | Phase 1 | Phase 2 |
| --- | --- | --- |
| CPU clock | 1 MHz | 8 MHz |
| Low fuse | `0x62` | `0xE2` |
| High / extended fuses | `0xDF` / `0xFF` | `0xDF` / `0xFF` |
| Default sketch | Blink | Serial telemetry |
| Monitor option | None | `-m` |

Show its options:

```bash
bash ./phase-2-serial/burn.sh -h
```

Program first, without opening a monitor:

```bash
bash ./phase-2-serial/burn.sh -p "${PORT:?Select your Uno port in Step 1}"
```

At the prompt, confirm that the Uno reset capacitor is **connected**, then press Enter. The script compiles for 8 MHz and programs the fuses and flash. It reports success only after AVRDUDE succeeds.

**Checkpoint:** the target gives five quick startup flashes, followed by regular LED cycles. The serial text appears in the next step.

## 7. Display packets in the terminal

```bash
bash ./phase-2-serial/monitor.sh "${PORT:?Select your Uno port in Step 1}"
```

Keep the reset capacitor connected. The monitor opens at 19200 baud; no mode wire or switch is needed. Use the monitor to read output, and do not type data into it: host bytes are interpreted as programmer commands by the relay.

| Link | Baud rate |
| --- | --- |
| ATtiny85 PB3 → Uno D4 software serial | 9600 |
| Uno USB serial → terminal monitor | 19200 |

The rates are intentionally different. The relay receives bytes at 9600, then transmits those bytes to the computer at 19200.

Illustrative output:

```text
[ATtiny85] Packet #12 | uptime=13s | LED=ON
[ATtiny85] Packet #13 | uptime=14s | LED=ON
```

The first packet number depends on when the monitor connects. The startup banner can be missed, which is normal. Serial transmission adds time to the loop, so packet timing is approximate; the integer uptime avoids floating-point printing overhead on the ATtiny85.

Press **Ctrl+C** to exit. Close the monitor before programming again.

## 8. Combine burn and monitor after the separate steps work

```bash
bash ./phase-2-serial/burn.sh -p "${PORT:?Select your Uno port in Step 1}" -m
```

This command pauses once to confirm the capacitor is connected, then programs the target and opens the monitor automatically. If programming fails, the monitor does not start.

A precompiled HEX file can be supplied with `-f`; it must already be built for 8 MHz. Each invocation programs one chip. Disconnect target power before replacing it.

## 9. Explain the transition

> In Phase 1 the Uno only acted as an ISP programmer. We copied that sketch and added a software serial receiver. The relay handles programmer requests first and forwards telemetry while idle. We then compiled the ATtiny85 application at 8 MHz, set the matching clock fuse, and transmitted data at 9600 baud through the Uno to a 19200-baud terminal monitor.

## Return to Phase 1

Exit the monitor and use the Phase 1 burn command to restore 1 MHz blink. The Phase 2 relay can still program chips automatically. To restore the exact standard Uno firmware too, run `phase-1-blink/upload_isp.sh` and follow its capacitor prompt.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| AVRDUDE cannot synchronize | Exit the monitor, keep the Uno reset capacitor connected, and check the selected port. If a running telemetry application interferes, disconnect its wire from Uno D4 for the burn and reconnect it afterward. |
| Uno relay upload fails | Disconnect the Uno reset capacitor and close any monitor. |
| No telemetry | Check target PB3 / physical pin 2 → Uno D4, and confirm the existing common ground. |
| Garbled text | Keep the terminal at 19200, software serial endpoints at 9600, and the target build/fuses at 8 MHz. Check wiring and ground. |
| Missing SoftwareSerial library | Rerun project setup. The scripts use the copy bundled with the pinned Arduino AVR core. |
| Generator reports unexpected source | Restore the preserved standard Phase 1 ArduinoISP source before regenerating the relay. |
| First banner or packet is missing | Telemetry starts before the monitor connects. Later readable packets establish forwarding. |

These scripts cannot physically detect the capacitor or target wiring; the prompts require you to check them. Host tests and build checks do not establish electrical timing or serial reliability on your actual board.
