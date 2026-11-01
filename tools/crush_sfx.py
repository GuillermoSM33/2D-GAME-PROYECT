#!/usr/bin/env python3
"""Record or import a sound and turn it into a gritty 8-bit game effect.

Usage:
  tools/crush_sfx.py record NAME [options]      Record from the microphone
  tools/crush_sfx.py convert FILE NAME [options] Use an existing file (mp4, m4a, mp3, wav...)
  tools/crush_sfx.py devices                     List the microphones ffmpeg sees

Options:
  --pitch N     Semitones up (+) or down (-); down also slows it. Default 0
  --bits N      Volume levels as bits: 8 is clean, 4 is very gritty. Default 5.
                16 writes a 16-bit file: no grit at all, for clean recorded voices
  --rate HZ     Sample rate it is crushed to: lower is grainier. Default 8000
  --start S     Keep from S seconds into the sound (after the silence is cut)
  --end S       Keep up to S seconds into the sound
  --glide N     Pitch slides N more semitones by the end (e.g. -10: a dying groan)
  --fade S      Fade-out seconds. Default 0.08
  --gate DB     Turn down what is DB below the loudest part (room hiss). Default -30;
                0 turns the gate off

For a clean voice use --bits 16 --rate 22050 --gate -20. Lower --bits/--rate
are for a deliberately gritty, retro sound.
  --seconds N   Record for N seconds instead of until Enter
  --device NAME Microphone to record from (see `devices`); default the first
  --play        Play the result when done

NAME is a path under assets/sounds, with one folder at most (zombie/growl).
Writes assets/sounds/NAME.wav (22050 Hz, mono, 8-bit, like tools/make_sfx.py),
which the next build embeds in the game. A recording is also kept untouched
in recordings/NAME.wav, so it can be crushed again with other options:
  tools/crush_sfx.py convert recordings/NAME.wav NAME --bits 4

Needs ffmpeg (records, and reads any format):
  Linux:            sudo apt install ffmpeg
  Windows (MSYS2):  pacman -S mingw-w64-ucrt-x86_64-ffmpeg
The processing itself uses only the standard library.
"""
from __future__ import annotations

import argparse
import array
import math
import platform
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_sfx import RATE, write_wav  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SOUNDS_DIR = ROOT / 'assets' / 'sounds'
RECORDINGS_DIR = ROOT / 'recordings'
WORK_RATE = 44100      # Processing rate, before crushing down
STARTUP_SEARCH = 0.1   # Seconds at the start where a mic's switch-on jump is looked for
STARTUP_JUMP = 0.25    # A sample-to-sample change this big there is the mic, not sound
STARTUP_SETTLE = 0.003 # Seconds it rings after the jump before settling
HIGH_PASS_HZ = 90.0    # Below this is not voice: the mic's start-up thump, hum, desk knocks
TRIM_WINDOW = 0.01     # Seconds per loudness measurement when trimming
TRIM_SMOOTH = 10       # Windows averaged (100 ms): sound is sustained, room noise only spikes
TRIM_THRESHOLD = 0.125 # Averaged loudness (RMS) that counts as sound: -18 dB from the loudest
FADE_IN = 0.005
FADE_OUT = 0.08        # Long enough that a cut tail dies away instead of stopping
TRIM_PAD = 0.05        # Seconds kept before and after the sound
GATE_DB = -30.0        # Default noise gate: quieter than this below the loudest is hiss
GATE_RATIO = 3.0       # Below the gate, every dB quieter becomes 3
GATE_ATTACK = 0.005    # Seconds for the gate to open when sound starts
GATE_RELEASE = 0.08    # Seconds for it to close behind a fading sound
ANTI_ALIAS = 0.45      # Low-pass cutoff as a fraction of the target sample rate
PEAK = 0.95            # Normalized loudness, like the synthesized effects


MSYS2_BIN = Path('C:/msys64/ucrt64/bin')  # Where MSYS2 installs ffmpeg on Windows


def find_tool(name: str) -> str | None:
    """On PATH, or in MSYS2's folder when started from PowerShell or cmd."""
    exe = shutil.which(name)
    if exe is None and windows_like():
        exe = shutil.which(name, path=str(MSYS2_BIN))
    return exe


def need_ffmpeg() -> str:
    exe = find_tool('ffmpeg')
    if exe is None:
        sys.exit('Falta ffmpeg. Instala:\n'
                 '  Linux:            sudo apt install ffmpeg\n'
                 '  Windows (MSYS2):  pacman -S mingw-w64-ucrt-x86_64-ffmpeg')
    return exe


def windows_like() -> bool:
    return platform.system() == 'Windows' or sys.platform in ('msys', 'cygwin') \
        or platform.system().startswith(('MINGW', 'MSYS', 'CYGWIN'))


def list_microphones(ffmpeg: str) -> list[str]:
    """Microphone names (Windows DirectShow). Linux records from the default source."""
    if not windows_like():
        return []
    out = subprocess.run([ffmpeg, '-hide_banner', '-list_devices', 'true', '-f', 'dshow', '-i', 'dummy'],
                         capture_output=True, text=True, encoding='utf-8', errors='replace').stderr
    return re.findall(r'"([^"]+)" \(audio\)', out)


def input_args(ffmpeg: str, device: str | None) -> list[str]:
    if windows_like():
        if device is None:
            mics = list_microphones(ffmpeg)
            if not mics:
                sys.exit('No encontré ningún micrófono. Revisa que esté conectado y permitido '
                         'en Configuración > Privacidad > Micrófono.')
            device = mics[0]
        return ['-f', 'dshow', '-i', f'audio={device}']
    if platform.system() == 'Darwin':
        return ['-f', 'avfoundation', '-i', f':{device or 0}']
    # PulseAudio, also provided by PipeWire on current distros.
    return ['-f', 'pulse', '-i', device or 'default']


def record(ffmpeg: str, name: str, seconds: float | None, device: str | None) -> Path:
    RECORDINGS_DIR.mkdir(exist_ok=True)
    raw = RECORDINGS_DIR / f'{name}.wav'
    raw.parent.mkdir(parents=True, exist_ok=True)
    cmd = [ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', *input_args(ffmpeg, device)]
    if seconds:
        cmd += ['-t', str(seconds)]
    cmd += ['-ac', '1', '-ar', str(WORK_RATE), '-c:a', 'pcm_s16le', str(raw)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    if seconds:
        print(f'Grabando {seconds:g} s... ¡ahora!')
        proc.wait()
    else:
        try:
            input('Grabando... ¡ahora! Presiona Enter para terminar. ')
        except EOFError:
            pass
        try:
            proc.communicate(b'q', timeout=5)  # ffmpeg stops cleanly on "q"
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    if not raw.exists() or raw.stat().st_size <= 44:
        sys.exit('No se grabó nada. ¿El micrófono está permitido y conectado?')
    print(f'Grabación original: {raw.relative_to(ROOT)}')
    return raw


def decode(ffmpeg: str, source: Path) -> list[float]:
    """Any audio (or a video's audio track) as mono floats at WORK_RATE."""
    out = subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-i', str(source), '-vn',
                          '-ac', '1', '-ar', str(WORK_RATE), '-f', 's16le', '-'],
                         capture_output=True)
    if out.returncode != 0:
        sys.exit(f'ffmpeg no pudo leer {source}:\n{out.stderr.decode(errors="replace")}')
    pcm = array.array('h')
    pcm.frombytes(out.stdout)
    if sys.byteorder == 'big':
        pcm.byteswap()
    return [s / 32768.0 for s in pcm]


def skip_startup_jump(samples: list[float]) -> list[float]:
    """Some mics switch on with an instant jump (0 to -0.85 in one sample) and
    then drift back over about a second. Starting after the jump (and its brief
    ringing) lets the high pass begin already settled, so neither the jump nor
    the drift is heard."""
    start = int(STARTUP_SEARCH * WORK_RATE)
    jumps = [abs(samples[i] - samples[i - 1]) for i in range(1, min(start, len(samples)))]
    if jumps and max(jumps) >= STARTUP_JUMP:
        return samples[jumps.index(max(jumps)) + 1 + int(STARTUP_SETTLE * WORK_RATE):]
    return samples


def high_pass(samples: list[float]) -> list[float]:
    """Removes what is too low to be voice. Mics often start with a slow thump:
    the signal jumps to one side and takes about a second to settle, which
    sounds like a pop and would also count as the loudest part when trimming
    and normalizing. Two one-pole filters in a row, starting already settled
    on the first sample so the cut itself makes no click."""
    rc = 1.0 / (2.0 * math.pi * HIGH_PASS_HZ)
    a = rc / (rc + 1.0 / WORK_RATE)
    out = samples
    for _ in range(2):
        filtered = []
        prev_x, prev_y = out[0], 0.0
        for x in out:
            prev_y = a * (prev_y + x - prev_x)
            prev_x = x
            filtered.append(prev_y)
        out = filtered
    return out


def trim(samples: list[float]) -> list[float]:
    """Cuts the quiet before and after, keeping a short pad. Loudness is averaged
    over TRIM_SMOOTH windows, so clicks and room noise don't count as the sound."""
    win = max(1, int(TRIM_WINDOW * WORK_RATE))
    energy = [sum(s * s for s in samples[i:i + win]) / len(samples[i:i + win])
              for i in range(0, len(samples), win)]
    half = TRIM_SMOOTH // 2
    rms = [math.sqrt(sum(energy[max(0, w - half):w + half]) / len(energy[max(0, w - half):w + half]))
           for w in range(len(energy))]
    loudest = max(rms, default=0.0)
    if loudest == 0.0:
        sys.exit('La grabación está en silencio.')
    loud = [w for w, r in enumerate(rms) if r >= loudest * TRIM_THRESHOLD]
    pad = int(TRIM_PAD * WORK_RATE)
    return samples[max(0, loud[0] * win - pad):(loud[-1] + 1) * win + pad]


def cut(samples: list[float], start: float | None, end: float | None) -> list[float]:
    a = int((start or 0.0) * WORK_RATE)
    b = len(samples) if end is None else int(end * WORK_RATE)
    if b - a < int(0.05 * WORK_RATE):
        sys.exit('--start/--end dejan menos de 0.05 s de sonido.')
    return samples[a:b]


def shift_pitch(samples: list[float], semitones: float, glide: float = 0.0) -> list[float]:
    """Tape-style: reading faster raises the pitch and shortens it, slower lowers it.
    With glide the pitch moves from semitones to semitones + glide along the way."""
    if semitones == 0 and glide == 0:
        return samples
    out = []
    pos = 0.0
    n = len(samples)
    while pos < n - 1:
        i = int(pos)
        frac = pos - i
        out.append(samples[i] + (samples[i + 1] - samples[i]) * frac)
        pos += 2.0 ** ((semitones + glide * pos / n) / 12.0)
    return out


def normalize_and_fade(samples: list[float], fade: float = FADE_OUT) -> list[float]:
    peak = max(abs(s) for s in samples)
    gain = PEAK / peak
    n = len(samples)
    fade_in, fade_out = int(FADE_IN * WORK_RATE), int(fade * WORK_RATE)
    out = []
    for i, s in enumerate(samples):
        env = min(1.0, i / fade_in if fade_in else 1.0, (n - 1 - i) / fade_out if fade_out else 1.0)
        out.append(s * gain * env)
    return out


def noise_gate(samples: list[float], gate_db: float) -> list[float]:
    """Turns down what is quieter than gate_db below the loudest part: the room's
    hiss between sounds and in fading tails, which normalizing would otherwise
    raise and crushing would turn into crackle. Below the threshold the level
    falls GATE_RATIO times faster (a soft expander, not a hard cut), and the gain
    follows the sound with a fast attack and slow release so it never clicks."""
    if gate_db >= 0.0:
        return samples
    up = 1.0 - math.exp(-1.0 / (GATE_ATTACK * WORK_RATE))
    down = 1.0 - math.exp(-1.0 / (GATE_RELEASE * WORK_RATE))
    env, level = [], 0.0
    for s in samples:  # RMS follower
        e = s * s
        level += (e - level) * (up if e > level else down)
        env.append(math.sqrt(level))
    threshold = max(env) * 10.0 ** (gate_db / 20.0)
    out, gain = [], 1.0
    for s, e in zip(samples, env):
        target = 1.0 if e >= threshold else (e / threshold) ** (GATE_RATIO - 1.0)
        gain += (target - gain) * (up if target > gain else down)
        out.append(s * gain)
    return out


def low_pass(samples: list[float], cutoff: float) -> list[float]:
    """Two 2nd-order Butterworth stages (RBJ biquad). Run before lowering the
    sample rate: what doesn't fit would fold back as a metallic whine."""
    w0 = 2.0 * math.pi * cutoff / WORK_RATE
    alpha = math.sin(w0) / (2.0 * math.sqrt(0.5))
    cos_w0 = math.cos(w0)
    a0 = 1.0 + alpha
    b0 = b2 = (1.0 - cos_w0) / 2.0 / a0
    b1 = (1.0 - cos_w0) / a0
    a1 = -2.0 * cos_w0 / a0
    a2 = (1.0 - alpha) / a0
    out = samples
    for _ in range(2):
        x1 = x2 = y1 = y2 = 0.0
        filtered = []
        for x in out:
            y = b0 * x + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
            x2, x1, y2, y1 = x1, x, y1, y
            filtered.append(y)
        out = filtered
    return out


def crush(samples: list[float], rate: int, bits: int) -> list[float]:
    """Down to the game's RATE, holding each value for 1/rate s (the grain) and
    rounding it to 2**bits levels (the grit)."""
    samples = low_pass(samples, min(rate, RATE) * ANTI_ALIAS)
    levels = (2 ** bits) / 2.0
    hold = max(1.0, RATE / rate)
    out = []
    held = 0.0
    n_out = int(len(samples) * RATE / WORK_RATE)
    for j in range(n_out):
        if j % hold < 1.0:
            src = samples[min(len(samples) - 1, int(j * WORK_RATE / RATE))]
            held = round(src * levels) / levels
        out.append(max(-1.0, min(1.0, held)))
    return out


def write_wav16(path: Path, samples: list[float]) -> None:
    """16-bit PCM: an 8-bit file hisses about 48 dB down, which a fading voice reaches."""
    pcm = array.array('h', (max(-32767, min(32767, round(s * 32767))) for s in samples))
    if sys.byteorder == 'big':
        pcm.byteswap()
    data = pcm.tobytes()
    header = struct.pack('<4sI4s4sIHHIIHH4sI', b'RIFF', 36 + len(data), b'WAVE',
                         b'fmt ', 16, 1, 1, RATE, RATE * 2, 2, 16, b'data', len(data))
    path.write_bytes(header + data)


def process(ffmpeg: str, source: Path, name: str, args: argparse.Namespace) -> Path:
    samples = decode(ffmpeg, source)
    samples = skip_startup_jump(samples)
    samples = high_pass(samples)
    samples = trim(samples)
    samples = noise_gate(samples, args.gate)
    samples = cut(samples, args.start, args.end)
    samples = shift_pitch(samples, args.pitch, args.glide)
    samples = normalize_and_fade(samples, args.fade)
    samples = crush(samples, args.rate, args.bits)
    target = SOUNDS_DIR / f'{name}.wav'
    target.parent.mkdir(parents=True, exist_ok=True)
    if args.bits > 8:
        write_wav16(target, samples)
    else:
        write_wav(target, samples)
    print(f'Efecto: {target.relative_to(ROOT)} ({len(samples) / RATE:.2f} s, '
          f'{args.bits} bits, {args.rate} Hz, tono {args.pitch:+g}'
          + (f' {args.glide:+g} al final' if args.glide else '') + ')')
    print('Recompila (Ctrl+Shift+B o ./build.sh) para meterlo en el juego.')
    return target


def play(path: Path) -> None:
    ffplay = find_tool('ffplay')
    if ffplay is None:
        print('(No encontré ffplay para reproducirlo; ábrelo con cualquier reproductor.)')
        return
    subprocess.run([ffplay, '-hide_banner', '-loglevel', 'error', '-nodisp', '-autoexit', str(path)])


def valid_name(name: str) -> str:
    if not re.fullmatch(r'[a-z0-9_]+(/[a-z0-9_]+)?', name):
        raise argparse.ArgumentTypeError('usa minúsculas, números y _, con una carpeta opcional '
                                         '(ej. zombie/growl)')
    return name


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0],
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    for cmd in ('record', 'convert'):
        p = sub.add_parser(cmd)
        if cmd == 'convert':
            p.add_argument('file', type=Path)
        p.add_argument('name', type=valid_name)
        p.add_argument('--pitch', type=float, default=0.0)
        p.add_argument('--bits', type=int, default=5, choices=[*range(2, 9), 16])
        p.add_argument('--rate', type=int, default=8000)
        p.add_argument('--start', type=float)
        p.add_argument('--end', type=float)
        p.add_argument('--glide', type=float, default=0.0)
        p.add_argument('--fade', type=float, default=FADE_OUT)
        p.add_argument('--gate', type=float, default=GATE_DB)
        p.add_argument('--play', action='store_true')
        if cmd == 'record':
            p.add_argument('--seconds', type=float)
            p.add_argument('--device')
    sub.add_parser('devices')
    args = parser.parse_args()

    ffmpeg = need_ffmpeg()
    if args.command == 'devices':
        mics = list_microphones(ffmpeg)
        if windows_like():
            print('\n'.join(mics) if mics else 'No encontré micrófonos.')
        else:
            print('En Linux se graba de la entrada predeterminada (PulseAudio/PipeWire);\n'
                  'otra fuente: --device NOMBRE (lista con: pactl list short sources)')
        return 0

    if args.command == 'record':
        source = record(ffmpeg, args.name, args.seconds, args.device)
    else:
        source = args.file
        if not source.exists():
            sys.exit(f'No existe {source}')
    target = process(ffmpeg, source, args.name, args)
    if args.play:
        play(target)
    return 0


if __name__ == '__main__':
    sys.exit(main())
