# Phase 1 — Install everything, upload ISP, then blink

**Target:** compatible macOS, an Arduino Uno with ATmega328P, and a bare ATtiny85 DIP chip. Run each numbered stage separately.

**Apple Silicon limit:** the pinned Arduino AVR compiler is distributed as an Intel macOS executable. This package does not install translation software. Setup stops if the downloaded tools cannot run. Therefore a fresh Apple Silicon Mac without the ability to run those binaries is not guaranteed to work. See [review notes](../REVIEW.md).

The project installs its own tools. Homebrew, Arduino CLI, AVRDUDE, board cores, Git, and Python are not prerequisites. macOS's built-in shell utilities and an Internet connection are required.

## 1. Create the project folder

Create a separate directory for this demonstration:

```bash
mkdir -p ATtiny85_Step_By_Step
```

Extract the supplied source package, or download this repository through GitHub's **Code → Download ZIP**. Copy the contents of the extracted repository into `ATtiny85_Step_By_Step`, so `setup.sh`, `cli.sh`, `scripts`, and `phase-1-blink` are directly inside it.

Enter the directory:

```bash
cd ATtiny85_Step_By_Step
pwd
```

If you already have the extracted repository, simply open Terminal in that folder; no second copy is necessary. All remaining commands run from its root. You can choose another folder name or location.

**Checkpoint:** `setup.sh` is present in the current directory.

## 2. Install the complete toolchain

```bash
bash ./setup.sh
```

The script performs these tasks in order:

1. Creates a private tool directory inside the project.
2. Downloads Arduino CLI 1.5.1 through a pinned revision of Arduino's official installer.
3. Creates a project-local configuration for tools, packages, libraries, and downloads.
4. Installs `arduino:avr@1.8.8` for the Uno and `attiny:avr@1.0.2` for the target.
5. Finds the AVR compiler and a complete AVRDUDE installation from those downloaded packages.
6. Checks that both executables can run.
7. Compiles the Uno ISP sketch and ATtiny85 blink sketch without programming hardware.
8. Records installed versions and marks setup complete only after both builds succeed.

AVRDUDE is installed as part of the downloaded AVR toolchain. No personal path exports or separate package manager are required. Existing global packages are not used. Exported `ARDUINO_*` settings are cleared only inside CLI subprocesses, and the build cache is configured inside the project. If setup fails, fix the reported network/compatibility error and rerun this same command; it reuses completed downloads and installations.

**Checkpoint:** the script prints `Setup complete`. A failed build prevents setup from reporting success.

## 3. Select the Uno port

Connect the Uno over USB. Keep one leg of any capacitor between Uno RESET and GND disconnected for now.

```bash
bash ./cli.sh board list
printf '\nEnter your Uno port exactly as shown above: '
read -r PORT
```

A port might look like `/dev/cu.usbmodem1301`; use the port listed for your board. Use a USB cable that carries data. If the port is missing, reconnect the board or try another cable before continuing. Some third-party USB adapters may need their vendor's driver; the project does not install unrelated USB drivers. You do not edit the script to store it. `PORT` lasts in the current terminal session. Repeat this step if you reconnect on a different port or open a new terminal.

**Checkpoint:** you selected the connected Uno's actual port.

## 4. Upload standard ArduinoISP to the Uno

The standard ISP sketch is included in the source package. It does not relay target serial data yet.

```bash
bash ./phase-1-blink/upload_isp.sh "${PORT:?Select the Uno port in Step 3 first}"
```

The script pauses so you can disconnect one leg of the Uno reset capacitor, then compiles and uploads ArduinoISP using the local tools. It stops if compilation or upload fails.

**Checkpoint:** the Uno upload succeeds. The Uno is now the programmer; the ATtiny85 application is programmed in Step 7.

## 5. Wire the ATtiny85 and LED

Disconnect USB power while wiring. Identify the ATtiny85 notch/dot and physical pin 1.

| Uno connection | ATtiny85 physical pin | Signal |
| --- | --- | --- |
| 5V | 8 | VCC |
| GND | 4 | Ground |
| Digital 10 | 1 (PB5) | RESET |
| Digital 11 | 5 (PB0) | MOSI |
| Digital 12 | 6 (PB1) | MISO |
| Digital 13 | 7 (PB2) | SCK |

Connect the application LED: **ATtiny85 pin 5 → 220-ohm resistor → LED anode; LED cathode → GND**. Put a 100 nF decoupling capacitor close to the ATtiny85 across its VCC and GND pins.

Connect the **10 µF electrolytic capacitor across Uno RESET and Uno GND**: positive lead to RESET, negative lead to GND. This keeps the Uno running ArduinoISP when the computer opens its port. Keep it connected during ATtiny85 programming; disconnect one leg whenever uploading firmware to the Uno.

Optional Uno status LEDs each need a series resistor: digital 9 heartbeat, digital 8 error, digital 7 programming activity.

Reconnect USB after checking the wiring.

**Checkpoint:** the target has power, common ground, and the six ISP connections. The reset capacitor is fitted on the Uno.

## 6. Create and explain the blink application

The example is supplied in the repository. For the presentation, this command recreates it from the terminal. It overwrites `phase-1-blink/blink/blink.ino`, so preserve personal changes before running it.

```bash
mkdir -p phase-1-blink/blink
cat > phase-1-blink/blink/blink.ino <<'SKETCH'
// ATtiny85 Arduino pin 0 = PB0 = physical DIP pin 5.
const byte LED_PIN = 0;

void setup() {
  pinMode(LED_PIN, OUTPUT);

  // Seven quick flashes identify the start of this firmware.
  for (byte count = 0; count < 7; count++) {
    digitalWrite(LED_PIN, HIGH);
    delay(50);
    digitalWrite(LED_PIN, LOW);
    delay(50);
  }
}

void loop() {
  digitalWrite(LED_PIN, HIGH);
  delay(500);
  digitalWrite(LED_PIN, LOW);
  delay(500);
}
SKETCH
```

Arduino pin `0` is PB0 / ATtiny85 physical pin 5. `setup()` produces seven rapid flashes. `loop()` then gives 500 ms on and 500 ms off, approximately one full blink cycle per second.

The phase's [burn script](../phase-1-blink/burn.sh) is already supplied. It calls the local toolchain and compiles the target for 1 MHz. A missing local installation triggers setup automatically.

## 7. Compile, set fuses, and program the ATtiny85

Keep the Uno reset capacitor connected. Select the port again if it changed.

```bash
bash ./phase-1-blink/burn.sh -p "${PORT:?Select the Uno port in Step 3 first}"
```

| Setting | Value |
| --- | --- |
| Target | `attiny85` |
| Programmer | `stk500v1` (standard ArduinoISP) |
| Host baud rate | `19200` |
| Compilation clock | `internal1` / 1 MHz |
| Low fuse | `0x62` |
| High fuse | `0xDF` |
| Extended fuse | `0xFF` |

The low fuse configures the internal 8 MHz oscillator divided by 8 to match the compilation clock. The script writes all three fuse bytes on every burn; review them before reusing a chip with custom settings. It writes application flash over ISP and does not install an ATtiny85 bootloader.

**Checkpoint:** AVRDUDE finishes without errors and the script reports success. Watch for seven quick startup flashes, then one blink cycle per second. Compilation or programming failures stop the script before success is reported.

To program a different sketch or an existing HEX file:

```bash
bash ./phase-1-blink/burn.sh -p "${PORT:?Select the Uno port first}" -f phase-1-blink/blink/blink.ino
```

For HEX input, the firmware must already be compiled for 1 MHz. Each invocation programs one chip. Disconnect target power before replacing chips.

## 8. Explain the result

> We install the toolchain inside the project, upload ArduinoISP to the Uno, and connect the Uno to the ATtiny85 over ISP. The burn script compiles the blink application for 1 MHz, sets matching fuse values, and programs flash. The LED gives seven startup flashes and then repeats one blink cycle per second.

Phase 1 ends here. Phase 2 will copy and modify the ISP source for serial forwarding, add the telemetry application, and introduce a separate burn/monitor script while preserving Phase 1.

## Moving or repairing the project

You can move the complete project folder to another writable location. The scripts recalculate paths and regenerate the local CLI configuration. They do not refer to the original username or folder. If the local tools are absent, the scripts install them again.

To repair/recheck the installation explicitly:

```bash
bash ./setup.sh
```

To redownload everything, close any running builds, remove only the project's generated tool directory, and run setup again:

```bash
rm -rf ./.runtime
bash ./setup.sh
```

This reset command must be run from the repository root. It removes downloaded tools, not source files. Old exported variables such as `AVRDUDE_BIN` and `AVRDUDE_CONF` are ignored by this version.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Setup download fails | Check Internet access and retry `bash ./setup.sh`. |
| Downloaded tool cannot run | Review the package installation output and executable compatibility. Setup stops without changing macOS system components. |
| Uno upload fails | Disconnect the Uno reset capacitor, close serial monitors, and confirm the port. |
| ATtiny85 signature/programming error | Check target power, orientation, ground, ISP wiring, and reconnect the Uno reset capacitor. |
| Blink speed is wrong | Check compilation and fuse programming completed successfully at 1 MHz. |
| No LED output | Check physical pin 5, LED polarity, resistor, and the programming log. |
| `PORT` is unset | Repeat Step 3. |

Shell and mocked toolchain checks do not replace running this guide on your actual Mac, Uno, and ATtiny85 before the presentation.
