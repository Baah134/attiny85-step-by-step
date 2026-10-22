# ATtiny85 — Step by Step

A macOS terminal demonstration: install the tools, upload standard ArduinoISP to an Arduino Uno, and program a bare ATtiny85 to blink at 1 MHz.

**Compatibility:** setup is independent of your existing Arduino installation, but this is not a guarantee for every Mac. Arduino's pinned AVR compiler is an Intel macOS binary. A clean Apple Silicon Mac that cannot execute that binary will fail the compatibility/build checks. This package does not install processor-translation software or alter macOS system components. See the [review notes](REVIEW.md).

## Start here

Download or copy this repository to any writable folder. You do not need Arduino CLI, AVRDUDE, AVR cores, Homebrew, Git, or Python installed beforehand. Setup uses macOS's built-in Bash, curl, tar, and standard shell utilities, plus an Internet connection.

From the repository root:

```bash
bash ./setup.sh
bash ./cli.sh board list
```

Setup downloads its own Arduino CLI and installs the board cores, AVR compiler, and AVRDUDE inside this project. It verifies the Uno and ATtiny85 builds before declaring success. Existing Arduino installations and exported AVRDUDE paths are not used.

**Follow the [Phase 1 numbered walkthrough](docs/phase-1-blink.md)** for wiring, the reset capacitor, programmer upload, and the burn command. Run each stage separately during the presentation.

## Tool isolation and moving the project

All generated tools, configuration, downloads, and libraries live inside `.runtime/`. Paths are calculated from the current repository location each time a script runs. The installation does not depend on a personal username, global Arduino15 directory, fixed tool version, or shell exports. Reviewed versions are pinned in `scripts/versions.sh`: Arduino CLI 1.5.1, Arduino AVR core 1.8.8, and ATtiny core 1.0.2. The official CLI installer is pinned to a source commit. Installed versions are recorded in `.runtime/versions.txt`.

The programming scripts automatically invoke setup if the local toolchain is absent. Run setup explicitly for a presentation so installation is complete before connecting hardware. Internet is required for the initial install, repairs, and new dependencies. Keep the downloaded runtime with the project to reuse the installed tools on a compatible Mac. If the Mac architecture or OS compatibility changes, setup may need to download compatible tools again.

The installer currently supports macOS. Native Windows and Linux setup are not implemented in this version.

## Phase 1 files

| File | Purpose |
| --- | --- |
| [setup.sh](setup.sh) | Download and verify the complete local toolchain. |
| [cli.sh](cli.sh) | Run this project's configured Arduino CLI. |
| [scripts/common.sh](scripts/common.sh) | Isolate configuration/environment, resolve local paths, and select runnable tools. |
| [scripts/versions.sh](scripts/versions.sh) | Reviewed CLI, core, and installer versions. |
| [phase-1-blink/upload_isp.sh](phase-1-blink/upload_isp.sh) | Compile/upload standard ArduinoISP to the Uno. |
| [phase-1-blink/ArduinoISP/ArduinoISP.ino](phase-1-blink/ArduinoISP/ArduinoISP.ino) | Arduino's unmodified standard programmer sketch. |
| [phase-1-blink/blink/blink.ino](phase-1-blink/blink/blink.ino) | Seven startup flashes, then 500 ms on and 500 ms off. |
| [phase-1-blink/burn.sh](phase-1-blink/burn.sh) | Compile, set 1 MHz fuses, and program one ATtiny85. |
| [THIRD_PARTY.md](THIRD_PARTY.md) | Attribution for ArduinoISP. |

## Phase 2: Display ATtiny85 telemetry in the terminal

[Open the Phase 2 numbered walkthrough](docs/phase-2-serial.md) after Phase 1 works.

1. Generate a relay sketch from a copy of standard ArduinoISP.
2. Compile both new sketches, then upload the relay to the Uno.
3. Add target TX → Uno D4 and a mode jumper between Uno D2 and GND.
4. Introduce the 8 MHz telemetry application and a separate Phase 2 burn script.
5. Program with D2 open; connect D2 to GND to monitor telemetry.

Phase 1 files and the shared installer remain unchanged. Phase 2 uses the same project-local tools, adds no system-package installation, and keeps the two baud rates explicit: 9600 from target to Uno, 19200 from Uno to terminal.

| Phase 2 file | Purpose |
| --- | --- |
| [prepare_relay.sh](phase-2-serial/prepare_relay.sh) | Derive the relay without changing standard Phase 1 source. |
| [ArduinoISP_Relay.ino](phase-2-serial/ArduinoISP_Relay/ArduinoISP_Relay.ino) | ISP/telemetry firmware selected by Uno D2. |
| [serial_demo.ino](phase-2-serial/serial_demo/serial_demo.ino) | ATtiny85 software serial at 9600 baud, built for 8 MHz. |
| [check.sh](phase-2-serial/check.sh) | Compile both Phase 2 sketches without programming hardware. |
| [upload_relay.sh](phase-2-serial/upload_relay.sh) | Upload the modified Uno firmware. |
| [burn.sh](phase-2-serial/burn.sh) | Program the target at 8 MHz; optionally open the monitor with `-m`. |
| [monitor.sh](phase-2-serial/monitor.sh) | View telemetry without programming again. |

Read the Phase 2 walkthrough before using these commands; the mode jumper and capacitor must be in the indicated positions.

## Validation

All shell scripts and guide command blocks pass Bash syntax checks. The included optional developer test covers 21 simulated installation/programming scenarios, including fresh setup, relocation, configuration isolation, and error handling. The real Arduino CLI 1.5.1 executable and command flags were checked on Linux. A complete real installation/build was blocked by this environment's network restrictions; no clean-Mac or physical-hardware validation is claimed. See [REVIEW.md](REVIEW.md).

The optional tests use Python; setup and programming do not require Python. To run developer tests: `python3 tests/test_phase1.py`.

### Phase 2 validation

The Phase 2 scripts pass 23 simulated integration scenarios, and the generated relay's actual setup/loop passes a host C++ mode-logic simulation. Both new sketches also pass real AVR builds on Linux with the pinned cores. The telemetry build uses 2,542 bytes of ATtiny85 flash and 134 bytes of static RAM. Physical uploads, serial timing, and a clean macOS installation still need validation on your hardware. See the [Phase 2 review addendum](REVIEW.md#phase-2-addendum).
