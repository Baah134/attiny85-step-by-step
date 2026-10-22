# Phase 1 review

## Conclusion

The scripts contain no personal username, no reference to a user's existing Arduino15 directories, and no dependency on preinstalled Arduino CLI, AVRDUDE, AVR cores, Homebrew, Git, or Python. All required Arduino tools are downloaded into the project. macOS's built-in Bash, curl, tar, standard shell utilities, Internet access, a writable project folder, and compatible hardware/executables are still required.

**This is not certified to work on every Mac.** The official Arduino AVR core 1.8.8 depends on AVR GCC 7.3.0, whose macOS download is `x86_64-apple-darwin14`. Thus removing a system-translation installer does not make the compiler ARM-native. The setup checks compatibility and compiles both sketches before it reports success. It does not install or modify macOS system components.

## Changes made during review

- Pinned Arduino CLI 1.5.1, Arduino AVR core 1.8.8, and ATtiny core 1.0.2.
- Pinned the official Arduino CLI installer to commit `a008ef0b50a366acaf7f20ac83c502a798065361`.
- Kept CLI configuration, packages, downloads, user libraries, and build cache inside the project.
- Isolated CLI subprocesses from inherited `ARDUINO_*` environment overrides.
- Ignored earlier exported `AVRDUDE_BIN`/`AVRDUDE_CONF` variables.
- Calculated project paths at runtime and refreshed configuration after moving the folder.
- Selected executable/configuration pairs from the same downloaded AVRDUDE tool directory.
- Required an explicit board port; no silent selection of the first connected device.
- Stopped on failed downloads, core installs, builds, uploads, and programming operations.
- Removed stale target HEX output before compiling, so an older file cannot mask a missing new artifact.
- Withheld the ready marker until both verification builds succeed.
- Preserved the Uno capacitor prompt and stopped if input closes instead of treating it as confirmation.

## Validation completed

- Bash syntax checks for every shell file and every README/guide Bash code block.
- Relative documentation-link checks.
- 21 mocked integration scenarios using a fresh temporary folder with spaces in its path.
- First-time download/install and reuse of an existing local installation.
- Unsupported OS, download/index/install failures, and failed verification builds.
- Uno upload confirmation, closed input, and failed upload.
- ATtiny argument/fuse checks; compiler/programmer failure handling; missing HEX; missing sketch; help; and missing port.
- HEX paths containing spaces and protection against inherited global configuration/tool paths.
- Relocation and version-marker changes triggering reconfiguration/revalidation.
- Real Arduino CLI 1.5.1 executable, configuration commands, and compile/upload flags checked on Linux.

A real end-to-end toolchain download/build was attempted, but the environment blocked Arduino CLI's direct network access. No completed real build, clean-Mac install, or physical upload is claimed. Mock tests validate script control flow, not executable compatibility on every host.

Run the entire numbered guide on the presentation machine before presenting. A successful `setup.sh` run establishes that the downloaded tools can actually compile both sketches on that machine; it does not test the wiring or USB upload until those stages are performed.

## Primary sources checked

- [Arduino package index](https://downloads.arduino.cc/packages/package_index.json): Arduino AVR core 1.8.8 and its tool dependencies/host archives.
- [Arduino AVR platform recipes](https://github.com/arduino/ArduinoCore-avr/blob/master/platform.txt): compiler and upload settings.
- [ATtiny package index](https://github.com/damellis/attiny/blob/ide-1.6.x-boards-manager/package_damellis_attiny_index.json): ATtiny core version.
- [Arduino CLI 1.5.1](https://github.com/arduino/arduino-cli/releases/tag/v1.5.1): CLI binaries.
- [Pinned official CLI installer](https://github.com/arduino/arduino-cli/blob/a008ef0b50a366acaf7f20ac83c502a798065361/install.sh).

## Included tests

The developer test is `tests/test_phase1.py`; run it with Python 3 if you want to repeat the mocked checks. Python is not part of setup or programming.
