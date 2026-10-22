# Add Phase 2 to the existing repository

This package is an update for `Baah134/attiny85-step-by-step`, based on commit `a965f513af7225481f5bdb27751a03cbf55ad11d`. It does not contain a replacement Phase 1 folder or installer.

1. Extract the ZIP.
2. Merge the extracted `attiny85-step-by-step` contents into your existing local repository root. If using GitHub upload, upload these contents into the repository root and preserve the folder structure. Do not upload the enclosing folder as a nested project.
3. Add the new `phase-2-serial` folder, `docs/phase-2-serial.md`, the two Phase 2 test files, and this note.
4. Replace the root `README.md`, `THIRD_PARTY.md`, and `REVIEW.md` with the included versions. If you made newer edits to those three documents, merge the Phase 2 additions instead of replacing your newer edits wholesale.
5. Commit with a message such as `Add Phase 2 ISP relay and ATtiny85 serial telemetry`.

Keep all Phase 1 files, `setup.sh`, `cli.sh`, `scripts`, and the existing Phase 1 test. No changes to those files are needed.

On the computer used for the presentation, copy the Phase 2 files into the same working project where Phase 1 runs. Open `docs/phase-2-serial.md` and follow it in order. The shell scripts are invoked with `bash`, so manual execute-permission changes are not required after a browser upload/download.

Important new hardware step: add a mode jumper between **Uno digital pin 2 and Uno GND**. Keep it open for programming; connect it to GND for telemetry. The target's TX wire is **ATtiny85 physical pin 2 (PB3) → Uno digital pin 4**. These are different connections.
