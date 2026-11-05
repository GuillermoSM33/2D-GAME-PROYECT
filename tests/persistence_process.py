"""Exercise save files across fresh processes, with isolated Unicode paths."""
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import zlib

binary = Path(sys.argv[1]).resolve()
if not binary.exists() and binary.with_name(binary.name + '.exe').exists():
    binary = binary.with_name(binary.name + '.exe')


def run(mode, directory):
    subprocess.run([str(binary), mode, str(directory)], check=True)


with tempfile.TemporaryDirectory(prefix='vaquera-sesión-') as temporary:
    root = Path(temporary)
    checks = root / 'checks'
    checks.mkdir()
    run('checks', checks)
    assert not list(checks.glob('*.sav')), 'Timer tests must not save user data'
    for corruption in ('truncate', 'schema'):
        directory = root / corruption
        directory.mkdir()
        run('write', directory)
        run('read', directory)
        slots = list(directory.glob('avance_*.sav'))
        assert len(slots) == 2
        latest = max(slots, key=lambda p: struct.unpack_from('<Q', p.read_bytes(), 8)[0])
        old = next(p for p in slots if p != latest)
        previous = old.read_bytes()
        data = bytearray(latest.read_bytes())
        if corruption == 'truncate':
            latest.write_bytes(data[:35])
        else:
            # Correct envelope CRC with an unsupported application schema.
            data[28] = 255
            struct.pack_into('<I', data, 20, zlib.crc32(data[:20] + data[24:]))
            latest.write_bytes(data)
        (directory / 'avance_a.sav.tmp').write_bytes(b'interrupted write')
        run('recover', directory)
        assert old.read_bytes() == previous, 'Recovery overwrote the last accepted slot'
        # After recovery the selected older save is still the active fallback;
        # the newly published snapshot has identical state at a higher generation.
    failure = root / 'failure'
    failure.mkdir()
    run('write', failure)
    slots = list(failure.glob('*.sav'))
    latest = max(slots, key=lambda p: struct.unpack_from('<Q', p.read_bytes(), 8)[0])
    previous = latest.read_bytes()
    inactive = next(p for p in slots if p != latest)
    inactive.with_name(inactive.name + '.tmp').mkdir()
    run('fail', failure)
    assert latest.read_bytes() == previous, 'Failed write damaged the valid slot'
    run('read', failure)
    legacy = root / 'legacy'
    legacy.mkdir()
    def character_id(value):
        return struct.pack('<I', len(value)) + value
    # The former V1 schema: progress, clears and book, without inventory/rating.
    payload = struct.pack('<5I', 0x31535156, 1, 5, 50, 1)
    payload += character_id(b'cowgirl') + struct.pack('<5I', 2, 3, 2, 2, 77)
    payload += struct.pack('<16I', 1, *([0] * 15)) + bytes(50 * 4 * 4)
    payload += character_id(b'cowgirl') + struct.pack('<4I', 8, 10, 10, 0)
    header = b'VAQDATA\x01' + struct.pack('<QI', 1, len(payload))
    checksum = zlib.crc32(header + payload)
    (legacy / 'avance_a.sav').write_bytes(header + struct.pack('<I', checksum) + payload)
    run('legacy', legacy)
print('persistence: process restart, interrupted write, schema rejection, recovery and I/O failure OK')
