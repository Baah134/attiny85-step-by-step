#!/usr/bin/env python3
"""Optional developer checks; no Python dependency for Phase 2 itself."""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from test_phase1 import FAKE_CLI, FAKE_AVR

SOURCE = Path(__file__).resolve().parents[1]


def main():
    for script in (SOURCE / 'phase-2-serial').glob('*.sh'):
        subprocess.run(['bash', '-n', str(script)], check=True)
    guide = SOURCE / 'docs/phase-2-serial.md'
    for block in re.findall(r'```bash\n(.*?)\n```', guide.read_text(), re.S):
        subprocess.run(['bash', '-n'], input=block, text=True, check=True)
    for md in [SOURCE / 'README.md', guide]:
        for link in re.findall(r'\]\(([^)#]+)\)', md.read_text()):
            if not link.startswith('http'):
                assert (md.parent / link).exists(), link
    cases = 0
    with tempfile.TemporaryDirectory(prefix='phase2 integration ') as t:
        parent = Path(t)
        root = parent / 'project with spaces'
        shutil.copytree(SOURCE, root, ignore=shutil.ignore_patterns('.runtime', 'build', '__pycache__'))
        runtime = root / '.runtime'
        cli = runtime / 'bin/arduino-cli'
        cli.parent.mkdir(parents=True)
        # Reuse Phase 1 fixture. Add the bundled SoftwareSerial installation.
        fixture = FAKE_CLI.replace("    compiler.chmod(0o755)", "    compiler.chmod(0o755)\n    (runtime / 'data/packages/arduino/hardware/avr/1.8.8/libraries/SoftwareSerial').mkdir(parents=True, exist_ok=True)")
        fixture += "\nelif args and args[0] == 'monitor':\n    sys.exit(int(os.environ.get('TEST_MONITOR_FAIL', '0')))\n"
        cli.write_text(fixture)
        cli.chmod(0o755)
        avr = parent / 'fake_avr.py'
        avr.write_text(FAKE_AVR)
        log = parent / 'calls.jsonl'
        env = dict(os.environ, TEST_LOG=str(log), TEST_AVR_TEMPLATE=str(avr),
                   ARDUINO_DIRECTORIES_DATA='/wrong/global', AVRDUDE_BIN='/wrong/global/avrdude')
        log.write_text('')
        config = runtime / 'arduino-cli.yaml'
        config.write_text('{}')
        subprocess.run([str(cli), '--config-file', str(config), 'core', 'install', 'arduino:avr@1.8.8'],
                       env={k: v for k, v in env.items() if not k.startswith('ARDUINO_')}, check=True)
        (runtime / 'ready').write_text('1.5.1 1.8.8 1.0.2')

        def run(name, args, code=0, text='', **variables):
            nonlocal cases
            log.write_text('')
            result = subprocess.run(['bash', *args], cwd=root, env=dict(env, **variables),
                                    input=text, text=True, capture_output=True)
            assert result.returncode == code, (name, result.returncode, result.stdout, result.stderr)
            calls = [json.loads(line) for line in log.read_text().splitlines()]
            cases += 1
            print('PASS:', name)
            return result, calls

        def has(calls, operation):
            return any(c[0] == 'program' if operation == 'program' else operation in c for c in calls)

        standard = root / 'phase-1-blink/ArduinoISP/ArduinoISP.ino'
        standard_bytes = standard.read_bytes()
        generated = root / 'phase-2-serial/ArduinoISP_Relay/ArduinoISP_Relay.ino'
        shipped = generated.read_bytes()
        run('generator reproduces shipped relay', ['./phase-2-serial/prepare_relay.sh'])
        assert generated.read_bytes() == shipped and standard.read_bytes() == standard_bytes
        run('generator is repeatable', ['./phase-2-serial/prepare_relay.sh'])
        assert generated.read_bytes() == shipped
        standard.write_bytes(standard_bytes.replace(b'  heartbeat();', b'  changed_heartbeat();'))
        run('unexpected source fails without replacing existing relay', ['./phase-2-serial/prepare_relay.sh'], 1)
        assert generated.read_bytes() == shipped
        standard.write_bytes(standard_bytes)
        result, calls = run('check compiles Uno and 8 MHz target only', ['./phase-2-serial/check.sh'])
        assert not has(calls, 'program') and not has(calls, 'upload')
        assert any('attiny:avr:ATtinyX5:cpu=attiny85,clock=internal8' in c for c in calls)
        assert any('--library' in c and 'SoftwareSerial' in json.dumps(c) for c in calls)
        run('failed check build propagates', ['./phase-2-serial/check.sh'], 7, TEST_COMPILE_FAIL='1')
        _, calls = run('closed relay-upload confirmation stops', ['./phase-2-serial/upload_relay.sh', '/dev/cu.mock'], 1)
        assert not has(calls, 'upload')
        _, calls = run('relay upload uses correct firmware', ['./phase-2-serial/upload_relay.sh', '/dev/cu.mock'], text='\n')
        assert any('upload' in c and str(root / 'phase-2-serial/ArduinoISP_Relay') in c for c in calls)
        result, _ = run('relay upload failure never reports success', ['./phase-2-serial/upload_relay.sh', '/dev/cu.mock'], 8, text='\n', TEST_UPLOAD_FAIL='1')
        assert 'Relay uploaded' not in result.stdout
        result, calls = run('8 MHz burn uses matching fuse and port', ['./phase-2-serial/burn.sh', '-p', '/dev/cu.mock'], text='\n')
        programming = next(c for c in calls if c[0] == 'program')
        for arg in ['lfuse:w:0xE2:m', 'hfuse:w:0xDF:m', 'efuse:w:0xFF:m', '/dev/cu.mock', '19200']:
            assert arg in programming
        assert not has(calls, 'monitor')
        _, calls = run('compile failure prevents flash and monitor', ['./phase-2-serial/burn.sh', '-p', '/dev/cu.mock', '-m'], 7, text='\n\n', TEST_COMPILE_FAIL='1')
        assert not has(calls, 'program') and not has(calls, 'monitor')
        _, calls = run('stale HEX cannot hide missing output', ['./phase-2-serial/burn.sh', '-p', '/dev/cu.mock'], 1, text='\n', TEST_NO_HEX='1')
        assert not has(calls, 'program')
        _, calls = run('closed burn confirmation prevents flash', ['./phase-2-serial/burn.sh', '-p', '/dev/cu.mock'], 1)
        assert not has(calls, 'program')
        result, calls = run('flash failure prevents monitor', ['./phase-2-serial/burn.sh', '-p', '/dev/cu.mock', '-m'], 9, text='\n\n', TEST_PROGRAM_FAIL='9')
        assert not has(calls, 'monitor') and 'Programming succeeded' not in result.stdout
        result, calls = run('combined burn and monitor waits for both modes', ['./phase-2-serial/burn.sh', '-p', '/dev/cu.mock', '-m'], text='\n\n')
        assert has(calls, 'program') and has(calls, 'monitor')
        assert next(c for c in calls if 'monitor' in c)[-1] == 'baudrate=19200'
        assert 'Disconnect Uno D2' in result.stdout and 'Connect Uno D2' in result.stdout
        _, calls = run('second confirmation EOF prevents monitor', ['./phase-2-serial/burn.sh', '-p', '/dev/cu.mock', '-m'], 1, text='\n')
        assert has(calls, 'program') and not has(calls, 'monitor')
        _, calls = run('standalone monitor does not program', ['./phase-2-serial/monitor.sh', '/dev/cu.mock'], text='\n')
        assert has(calls, 'monitor') and not has(calls, 'program')
        _, calls = run('closed monitor confirmation stops', ['./phase-2-serial/monitor.sh', '/dev/cu.mock'], 1)
        assert not has(calls, 'monitor')
        run('monitor errors propagate', ['./phase-2-serial/monitor.sh', '/dev/cu.mock'], 10, text='\n', TEST_MONITOR_FAIL='10')
        hexf = root / 'prebuilt firmware.hex'
        hexf.write_text(':00000001FF\n')
        _, calls = run('HEX path with spaces bypasses compile', ['./phase-2-serial/burn.sh', '-p', '/dev/cu.mock', '-f', str(hexf)], text='\n')
        assert has(calls, 'program') and not has(calls, 'compile')
        run('missing port rejected', ['./phase-2-serial/burn.sh'], 1)
        run('help works', ['./phase-2-serial/burn.sh', '-h'])
        lib = runtime / 'data/packages/arduino/hardware/avr/1.8.8/libraries/SoftwareSerial'
        lib.rmdir()
        _, calls = run('missing SoftwareSerial stops before flash', ['./phase-2-serial/burn.sh', '-p', '/dev/cu.mock'], 1, text='\n')
        assert not has(calls, 'program')
        lib.mkdir()
        old = root
        root = parent / 'relocated project'
        old.rename(root)
        _, calls = run('relocated Phase 2 uses recalculated paths', ['./phase-2-serial/burn.sh', '-p', '/dev/cu.mock'], text='\n')
        assert str(old) not in json.dumps(calls)
        standard = root / 'phase-1-blink/ArduinoISP/ArduinoISP.ino'
        assert standard.read_bytes() == standard_bytes
        block = next(b for b in re.findall(r'```bash\n(.*?)\n```', guide.read_text(), re.S) if "<<'SKETCH'" in b)
        subprocess.run(['bash'], cwd=root, input=block, text=True, check=True)
        assert (root / 'phase-2-serial/serial_demo/serial_demo.ino').read_bytes() == (SOURCE / 'phase-2-serial/serial_demo/serial_demo.ino').read_bytes()
    print(f'PASS: {cases} Phase 2 scenarios, generator/source consistency, guide creation block, and documentation syntax/links.')


if __name__ == '__main__':
    main()
