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

Phase 2 will introduce a copied/modified ISP relay, serial telemetry, and a separate burn/monitor script. Only Phase 1 is implemented here.

## Validation

All shell scripts and guide command blocks pass Bash syntax checks. The included optional developer test covers 21 simulated installation/programming scenarios, including fresh setup, relocation, configuration isolation, and error handling. The real Arduino CLI 1.5.1 executable and command flags were checked on Linux. A complete real installation/build was blocked by this environment's network restrictions; no clean-Mac or physical-hardware validation is claimed. See [REVIEW.md](REVIEW.md).

The optional tests use Python; setup and programming do not require Python. To run developer tests: `python3 tests/test_phase1.py`.
