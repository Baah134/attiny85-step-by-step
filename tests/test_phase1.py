#!/usr/bin/env python3
"""Optional developer checks; Python is not required to use the project."""
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import tempfile

SOURCE = Path(__file__).resolve().parents[1]
FAKE_AVR = r'''#!/usr/bin/env python3
import json, os, sys
if sys.argv[1:] == ['-?']:
    sys.exit(0)
with open(os.environ['TEST_LOG'], 'a') as f:
    f.write(json.dumps(['program', *sys.argv]) + '\n')
sys.exit(int(os.environ.get('TEST_PROGRAM_FAIL', '0')))
'''
FAKE_CLI = r'''#!/usr/bin/env python3
from pathlib import Path
import json, os, shutil, sys
args = sys.argv[1:]
if args == ['version']:
    print('arduino-cli Version: 1.5.1 Commit: mock Date: mock')
    sys.exit(0)
if any(k.startswith('ARDUINO_') for k in os.environ):
    sys.exit(81)
with open(os.environ['TEST_LOG'], 'a') as f:
    f.write(json.dumps(['cli', *args]) + '\n')
i = args.index('--config-file')
config = Path(args[i + 1])
args = args[:i] + args[i + 2:]
runtime = config.parent
if args[:2] == ['config', 'set']:
    data = json.loads(config.read_text())
    data[args[2]] = args[3]
    config.write_text(json.dumps(data))
elif args[:2] == ['config', 'add']:
    pass
elif args[:2] == ['core', 'update-index']:
    if os.environ.get('TEST_NETWORK_FAIL'):
        sys.exit(12)
elif args[:2] == ['core', 'install']:
    if os.environ.get('TEST_INSTALL_FAIL'):
        sys.exit(13)
    tool = runtime / 'data/packages/mock-vendor/tools/avrdude/unknown-version'
    (tool / 'bin').mkdir(parents=True, exist_ok=True)
    (tool / 'etc').mkdir(exist_ok=True)
    avr = tool / 'bin/avrdude'
    shutil.copyfile(os.environ['TEST_AVR_TEMPLATE'], avr)
    avr.chmod(0o755)
    (tool / 'etc/avrdude.conf').write_text('mock')
    compiler = runtime / 'data/packages/arduino/tools/avr-gcc/mock/bin/avr-g++'
    compiler.parent.mkdir(parents=True, exist_ok=True)
    compiler.write_text('#!/bin/sh\necho mock AVR compiler\n')
    compiler.chmod(0o755)
elif args and args[0] == 'compile':
    if os.environ.get('TEST_COMPILE_FAIL'):
        sys.exit(7)
    build = Path(args[args.index('--build-path') + 1])
    build.mkdir(parents=True, exist_ok=True)
    if not os.environ.get('TEST_NO_HEX'):
        (build / (Path(args[-1]).name + '.ino.hex')).write_text(':00000001FF\n')
elif args and args[0] == 'upload':
    if os.environ.get('TEST_UPLOAD_FAIL'):
        sys.exit(8)
elif args[:2] == ['board', 'list']:
    print('/dev/cu.mock Uno')
elif args[:2] == ['core', 'list']:
    print('arduino:avr 1.8.8\nattiny:avr 1.0.2')
'''


def main():
    for p in SOURCE.rglob('*.sh'):
        subprocess.run(['bash', '-n', str(p)], check=True)
    for md in [SOURCE / 'README.md', SOURCE / 'docs/phase-1-blink.md']:
        for block in re.findall(r'```bash\n(.*?)\n```', md.read_text(), re.S):
            subprocess.run(['bash', '-n'], input=block, text=True, check=True)
        for link in re.findall(r'\]\(([^)#]+)\)', md.read_text()):
            if not link.startswith('http'):
                assert (md.parent / link).exists(), link
    cases = 0
    with tempfile.TemporaryDirectory(prefix='phase1 review ') as t:
        parent = Path(t)
        root = parent / 'fresh project'
        shutil.copytree(SOURCE, root, ignore=shutil.ignore_patterns('.runtime', 'build', '__pycache__'))
        fakebin = parent / 'system'
        fakebin.mkdir()
        log = parent / 'calls.jsonl'
        cli_template = parent / 'fake_cli.py'
        cli_template.write_text(FAKE_CLI)
        avr_template = parent / 'fake_avr.py'
        avr_template.write_text(FAKE_AVR)

        def executable(path, code):
            path.write_text(code)
            path.chmod(0o755)

        executable(fakebin / 'uname', '#!/bin/sh\nif [ "$1" = -s ]; then echo "${TEST_OS:-Darwin}"; else echo x86_64; fi\n')
        executable(fakebin / 'curl', r'''#!/usr/bin/env python3
from pathlib import Path
import json, os, sys
with open(os.environ['TEST_LOG'], 'a') as f:
    f.write(json.dumps(['download', *sys.argv[1:]]) + '\n')
if os.environ.get('TEST_DOWNLOAD_FAIL'):
    sys.exit(11)
p = Path(sys.argv[sys.argv.index('-o') + 1])
p.write_text('#!/bin/sh\ncp "$TEST_CLI_TEMPLATE" "$BINDIR/arduino-cli"\nchmod +x "$BINDIR/arduino-cli"\n')
''')
        env = dict(os.environ, PATH=str(fakebin) + ':' + os.environ['PATH'],
                   TEST_LOG=str(log), TEST_CLI_TEMPLATE=str(cli_template),
                   TEST_AVR_TEMPLATE=str(avr_template),
                   ARDUINO_DIRECTORIES_DATA='/wrong/global/data',
                   ARDUINO_CONFIG_FILE='/wrong/global/config',
                   AVRDUDE_BIN='/wrong/global/avrdude', AVRDUDE_CONF='/wrong/global/avrdude.conf')

        def run(name, args, expected=0, text='', **variables):
            nonlocal cases
            log.write_text('')
            result = subprocess.run(['bash', *args], cwd=root, env=dict(env, **variables),
                                    input=text, text=True, capture_output=True)
            assert result.returncode == expected, (name, result.returncode, result.stdout, result.stderr)
            calls = [json.loads(line) for line in log.read_text().splitlines()]
            cases += 1
            print('PASS:', name)
            return result, calls

        def has(calls, kind):
            return any(c[0] == kind for c in calls)

        run('unsupported OS stops before downloads', ['./setup.sh'], 1, TEST_OS='Linux')
        _, calls = run('download failure stops setup', ['./setup.sh'], 11, TEST_DOWNLOAD_FAIL='1')
        assert not (root / '.runtime/ready').exists()
        run('index/network failure stops setup', ['./setup.sh'], 12, TEST_NETWORK_FAIL='1')
        run('package installation failure stops setup', ['./setup.sh'], 13, TEST_INSTALL_FAIL='1')
        run('setup build failure never creates ready marker', ['./setup.sh'], 7, TEST_COMPILE_FAIL='1')
        assert not (root / '.runtime/ready').exists()
        _, calls = run('first-time setup installs both pinned cores and builds sketches', ['./setup.sh'])
        assert any('arduino:avr@1.8.8' in c for c in calls)
        assert any('attiny:avr@1.0.2' in c for c in calls)
        _, calls = run('existing local setup reused', ['./cli.sh', 'board', 'list'])
        assert not has(calls, 'download')
        config = json.loads((root / '.runtime/arduino-cli.yaml').read_text())
        assert all(str(root) in value for value in config.values())
        assert config['build_cache.path'].endswith('/.runtime/cache')
        run('Uno upload pauses for capacitor confirmation', ['./phase-1-blink/upload_isp.sh', '/dev/cu.mock'], text='\n')
        _, calls = run('closed input prevents Uno upload', ['./phase-1-blink/upload_isp.sh', '/dev/cu.mock'], 1)
        assert not any('upload' in c for c in calls)
        result, _ = run('Uno upload failure never reports success', ['./phase-1-blink/upload_isp.sh', '/dev/cu.mock'], 8, text='\n', TEST_UPLOAD_FAIL='1')
        assert 'Uno upload complete' not in result.stdout
        result, calls = run('burn ignores exported global tools and config', ['./phase-1-blink/burn.sh', '-p', '/dev/cu.mock'])
        programming = next(c for c in calls if c[0] == 'program')
        assert '/wrong/global' not in json.dumps(calls)
        for arg in ['attiny85', 'stk500v1', '/dev/cu.mock', '19200', 'lfuse:w:0x62:m', 'hfuse:w:0xDF:m', 'efuse:w:0xFF:m']:
            assert arg in programming, arg
        _, calls = run('target compile failure prevents programming', ['./phase-1-blink/burn.sh', '-p', '/dev/cu.mock'], 7, TEST_COMPILE_FAIL='1')
        assert not has(calls, 'program')
        _, calls = run('stale HEX cannot mask a missing new build', ['./phase-1-blink/burn.sh', '-p', '/dev/cu.mock'], 1, TEST_NO_HEX='1')
        assert not has(calls, 'program')
        result, _ = run('programmer failure never reports success', ['./phase-1-blink/burn.sh', '-p', '/dev/cu.mock'], 9, TEST_PROGRAM_FAIL='9')
        assert 'Programming succeeded' not in result.stdout
        hexfile = root / 'test firmware.hex'
        hexfile.write_text(':00000001FF\n')
        _, calls = run('HEX input with spaces skips compilation', ['./phase-1-blink/burn.sh', '-p', '/dev/cu.mock', '-f', str(hexfile)])
        assert not any('compile' in c for c in calls)
        run('missing target reports error', ['./phase-1-blink/burn.sh', '-p', '/dev/cu.mock', '-f', 'missing.ino'], 1)
        run('missing port rejected', ['./phase-1-blink/burn.sh'], 1)
        run('help works', ['./phase-1-blink/burn.sh', '-h'])
        old = root
        root = parent / 'moved project'
        old.rename(root)
        _, calls = run('moved project recalculates paths', ['./phase-1-blink/burn.sh', '-p', '/dev/cu.mock'])
        assert str(old) not in json.dumps(calls)
        config = json.loads((root / '.runtime/arduino-cli.yaml').read_text())
        assert all(str(root) in value for value in config.values())
        shutil.rmtree(root / '.runtime')
        _, calls = run('missing tools automatically invoke setup', ['./phase-1-blink/burn.sh', '-p', '/dev/cu.mock'])
        assert has(calls, 'download') and has(calls, 'program')
        (root / '.runtime/ready').write_text('old versions')
        _, calls = run('changed toolset marker revalidates installation', ['./cli.sh', 'board', 'list'])
        assert any('arduino:avr@1.8.8' in c for c in calls)
    print(f'PASS: {cases} integration scenarios, shell syntax, and documentation links.')


if __name__ == '__main__':
    main()
