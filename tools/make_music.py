#!/usr/bin/env python3
"""Compose and synthesize each stage's background music.

Usage: tools/make_music.py [--only menu ruta_1_1 ...] [--keep-wav] [assets_dir]

Writes assets/music/<track>.ogg (Vorbis, stereo, 22050 Hz) and records the
shipped hashes in docs/AUDIO_MUSIC_MANIFEST.json. Nothing here comes from a
recording, a sample library or another piece of music: every note is written
below and every sound is computed here, so the tracks carry no third-party
rights (docs/AUDIO_MUSIC.md). Each track is a seamless loop: a note or an echo
that runs past the end continues at the start, its last bar leads into its
first, and the file is cut at a quiet instant just before that first beat.

Deterministic. The synthesis uses only the standard library; encoding needs
FFmpeg with libvorbis. Compiling and playing the game need neither.
"""
from __future__ import annotations

import argparse
import array
import hashlib
import json
import math
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import wave

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / 'docs' / 'AUDIO_MUSIC_MANIFEST.json'
RATE = 22050
TARGET_RMS = 0.115
PEAK = 0.89
EDGE_FADE = .004  # Seconds at each end of the file
EDGE_LIMIT = .02   # Largest sample allowed there once decoded
NOTE_NAMES = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def hz(note: str) -> float:
    """'A4', 'F#3', 'Bb2' to a frequency."""
    semitone = NOTE_NAMES[note[0]]
    rest = note[1:]
    while rest[0] in '#b':
        semitone += 1 if rest[0] == '#' else -1
        rest = rest[1:]
    return 440.0 * 2 ** ((semitone + 12 * (int(rest) + 1) - 69) / 12)


class Track:
    """A circular stereo mix, a reverb send, and the beat grid."""

    def __init__(self, bpm: float, bars: int, seed: int, beats_per_bar: int = 4) -> None:
        self.bpm, self.bars, self.beats_per_bar = bpm, bars, beats_per_bar
        self.beat = 60.0 / bpm
        self.length = round(bars * beats_per_bar * self.beat * RATE)
        self.left = array.array('f', bytes(4 * self.length))
        self.right = array.array('f', bytes(4 * self.length))
        self.send = array.array('f', bytes(4 * self.length))
        self.rng = random.Random(seed)

    def at(self, bar: int, beat: float = 0.0, swing: float = 0.006) -> int:
        """The sample of a position, a human hair off the grid."""
        seconds = (bar * self.beats_per_bar + beat) * self.beat + self.rng.uniform(-swing, swing)
        return round(seconds * RATE)

    def mix(self, samples, start: int, pan: float = 0.0, send: float = 0.2) -> None:
        angle = (pan + 1.0) * math.pi / 4
        gl, gr = math.cos(angle), math.sin(angle)
        left, right, wet, n = self.left, self.right, self.send, self.length
        for i, s in enumerate(samples):
            at = (start + i) % n
            left[at] += s * gl
            right[at] += s * gr
            wet[at] += s * send

    def echo(self, samples, start: int, pan: float, delay: float, gain: float, repeats: int = 2) -> None:
        """A canyon's slapback: distant copies, panned away from the source."""
        for k in range(1, repeats + 1):
            copy = [s * gain ** k for s in samples]
            self.mix(copy, start + round(delay * k * RATE), -pan * .7, .35)

    def finish(self) -> tuple:
        """Adds the circular reverb, then balances the level with a soft limit."""
        wet_l, wet_r = reverb(self.send, (1427, 1693, 1867)), reverb(self.send, (1361, 1579, 1973))
        out_l = [a + b for a, b in zip(self.left, wet_l)]
        out_r = [a + b for a, b in zip(self.right, wet_r)]
        energy = math.sqrt(sum(a * a + b * b for a, b in zip(out_l, out_r)) / (2 * self.length))
        gain = TARGET_RMS / max(energy, 1e-9)
        limit = lambda v: PEAK * math.tanh(v * gain / PEAK)
        return self.cut_for_loop([limit(v) for v in out_l], [limit(v) for v in out_r])

    def cut_for_loop(self, left: list, right: list) -> tuple:
        """Moves the file's first sample to the quietest instant before the first
        beat, so the jump back lands between sounds and not on an attack. The
        notes on that beat are up to a hair early, hence the margin. A few
        milliseconds of fade take care of what the codec leaves at its edges."""
        n, window = self.length, round(.012 * RATE)
        loudness = lambda at: sum(left[(at + k) % n] ** 2 + right[(at + k) % n] ** 2 for k in range(window))
        early, late = round(.03 * RATE), round(.35 * self.beat * RATE)
        quiet = min(range(n - late, n - early, 8), key=loudness)
        at = min(range(quiet, quiet + window), key=lambda i: abs(left[i % n]) + abs(right[i % n]))
        left, right = left[at:] + left[:at], right[at:] + right[:at]
        fade = round(EDGE_FADE * RATE)
        for i in range(fade):
            amount = math.sin(math.pi / 2 * i / fade) ** 2
            for channel in (left, right):
                channel[i] *= amount
                channel[n - 1 - i] *= amount
        return left, right


def reverb(send, delays: tuple, feedback: float = .74, damp: float = .45) -> list:
    """Damped combs run twice around the loop, so the tail wraps seamlessly."""
    n = len(send)
    out = [0.0] * n
    for delay in delays:
        line = [0.0] * n
        low = 0.0
        for _ in range(2):
            for i in range(n):
                held = line[i - delay]
                low = held * (1 - damp) + low * damp
                line[i] = send[i] + low * feedback
        for i in range(n):
            out[i] += line[i] / len(delays)
    return out


def pluck(track: Track, freq: float, seconds: float, gain: float, bright: float = .55,
          t60: float = 2.4, pick: float = .18) -> list:
    """A plucked string (Karplus-Strong), tuned, picked part way along."""
    rng = track.rng
    period = RATE / freq - .5
    delay = max(2, int(period))
    frac = period - delay
    coef = (1 - frac) / (1 + frac)
    line = [rng.uniform(-1, 1) for _ in range(delay)]
    low = 0.0
    for i, v in enumerate(line):
        low += bright * (v - low)
        line[i] = low
    notch = max(1, int(delay * pick))
    line = [line[i] - line[i - notch] * .7 for i in range(delay)]
    level = max(max(map(abs, line)), 1e-6)
    line = [v / level for v in line]
    decay = 10 ** (-3 / (freq * t60))
    count = round(seconds * RATE)
    out, at, prev_in, prev_out = [0.0] * count, 0, 0.0, 0.0
    fade = min(count, round(.03 * RATE))
    for i in range(count):
        here = line[at]
        following = line[(at + 1) % delay]
        filtered = (here + following) * .5 * decay
        tuned = coef * filtered + prev_in - coef * prev_out
        prev_in, prev_out = filtered, tuned
        line[at] = tuned
        at = (at + 1) % delay
        out[i] = here * gain * (1.0 if i < count - fade else (count - i) / fade)
    return out


def _envelope(i: int, count: int, attack: int, release: int) -> float:
    if i < attack:
        return i / attack
    if i > count - release:
        return (count - i) / release
    return 1.0


def voice(track: Track, freq: float, seconds: float, gain: float, partials: tuple, vibrato: float = 0.0,
          rate: float = 5.2, breath: float = 0.0, attack: float = .03, release: float = .08,
          glide_from: float | None = None) -> list:
    """A sustained tone from harmonics: a whistle, a reed, a horn, a bow."""
    count = round(seconds * RATE)
    attack_n, release_n = max(1, round(attack * RATE)), max(1, round(release * RATE))
    rng, out, phase, noise = track.rng, [0.0] * count, 0.0, 0.0
    start_phase = rng.uniform(0, math.tau)
    scoop = round(.05 * RATE)
    for i in range(count):
        depth = vibrato * min(1.0, i / (.25 * RATE))
        pitch = freq * (1 + depth * math.sin(math.tau * rate * i / RATE + start_phase))
        if glide_from and i < scoop:
            pitch *= (glide_from / freq) ** (1 - i / scoop)
        phase += math.tau * pitch / RATE
        tone = 0.0
        for harmonic, amount in partials:
            if pitch * harmonic < RATE * .45:
                tone += amount * math.sin(phase * harmonic)
        if breath:
            noise += .25 * (rng.uniform(-1, 1) - noise)
            tone += breath * noise
        out[i] = tone * gain * _envelope(i, count, attack_n, release_n)
    return out


WHISTLE = ((1, 1.0), (2, .05), (3, .012))
REED = ((1, 1.0), (2, .55), (3, .42), (4, .18), (5, .12), (6, .06))
HORN = ((1, 1.0), (2, .75), (3, .55), (4, .34), (5, .2), (6, .1), (7, .05))
BOW = ((1, 1.0), (2, .5), (3, .33), (4, .24), (5, .17), (6, .12), (7, .08), (8, .05))
ORGAN = ((1, 1.0), (2, .35), (3, .28), (4, .08), (5, .06))


def drum(track: Track, top: float, bottom: float, seconds: float, gain: float, noise: float = .25) -> list:
    """A skin: a falling tone and a short slap."""
    count = round(seconds * RATE)
    rng, phase, out, low = track.rng, 0.0, [0.0] * count, 0.0
    for i in range(count):
        t = i / count
        phase += math.tau * (bottom + (top - bottom) * math.exp(-t * 9)) / RATE
        low += .35 * (rng.uniform(-1, 1) - low)
        hit = low * noise * math.exp(-t * 26)
        out[i] = (math.sin(phase) * math.exp(-t * 4.5) + hit) * gain
    return out


def shaker(track: Track, seconds: float, gain: float) -> list:
    count = round(seconds * RATE)
    rng, out, last = track.rng, [0.0] * count, 0.0
    for i in range(count):
        white = rng.uniform(-1, 1)
        high = white - last
        last = white
        t = i / count
        out[i] = high * gain * min(1.0, t * 12) * (1 - t) ** 2
    return out


def bell(track: Track, freq: float, seconds: float, gain: float) -> list:
    """A distant iron bell: its partials are not harmonic."""
    count = round(seconds * RATE)
    parts = ((.5, .45, .55), (1.0, 1.0, .8), (1.19, .55, 1.4), (1.51, .35, 2.2), (2.0, .4, 2.6), (2.67, .18, 4.2))
    out = [0.0] * count
    for ratio, amount, speed in parts:
        step = math.tau * freq * ratio / RATE
        for i in range(count):
            t = i / RATE
            out[i] += amount * math.sin(step * i) * math.exp(-t * speed)
    return [v * gain * min(1.0, i / 40) for i, v in enumerate(out)]


def melody(track: Track, line: str, first_bar: int, sound, pan: float = 0.0, send: float = .35,
           echo: tuple | None = None, gain_scale: float = 1.0) -> None:
    """Plays 'A4:2 R:1 C5:1 | ...': one group per bar, note:beats."""
    previous = None
    for offset, bar_text in enumerate(line.split('|')):
        beat = 0.0
        for item in bar_text.split():
            name, length = item.split(':')
            length = float(length)
            if name != 'R':
                freq = hz(name)
                samples = sound(track, freq, length * track.beat, previous)
                samples = [v * gain_scale for v in samples]
                start = track.at(first_bar + offset, beat, .012)
                track.mix(samples, start, pan, send)
                if echo:
                    track.echo(samples, start, pan, echo[0], echo[1])
                previous = freq
            beat += length


def chord_arp(track: Track, bar: int, notes: list, pattern: list, gain: float, pan: float = -.25,
              t60: float = 2.4, bright: float = .55) -> None:
    """Plucks one chord's notes on a bar's pattern of (beat, note index, strength)."""
    for beat, index, strength in pattern:
        sound = pluck(track, hz(notes[index]), 1.5 * track.beat + .5, gain * strength, bright, t60)
        track.mix(sound, track.at(bar, beat), pan, .22)


def strum(track: Track, bar: int, beat: float, notes: list, gain: float, spread: float = .012,
          pan: float = .15, seconds: float = 1.1, bright: float = .75, down: bool = True) -> None:
    """A rake across the strings, each a moment after the last."""
    order = notes if down else list(reversed(notes))
    for i, note in enumerate(order):
        sound = pluck(track, hz(note), seconds, gain * (1 - .05 * i), bright, 1.8, pick=.12)
        track.mix(sound, track.at(bar, beat) + round(i * spread * RATE), pan, .2)


def bass_note(track: Track, bar: int, beat: float, note: str, gain: float, seconds: float = .9) -> None:
    """An upright bass: the plucked string, and the body under it."""
    freq = hz(note)
    string = pluck(track, freq, seconds, gain, .28, 2.0, .3)
    body = [string[i] + 1.1 * gain * math.sin(math.tau * freq * i / RATE) * math.exp(-i / (.35 * RATE)) * min(1.0, i / 60)
            for i in range(len(string))]
    track.mix(body, track.at(bar, beat), 0.0, .08)


def pad(track: Track, bar: int, bars: float, notes: list, gain: float, partials=BOW, pan: float = 0.0,
        vibrato: float = .002, send: float = .4) -> None:
    seconds = bars * track.beats_per_bar * track.beat + .6
    for i, note in enumerate(notes):
        sound = voice(track, hz(note), seconds, gain, partials, vibrato, 4.1 + i * .3, 0.0, .5, .6)
        track.mix(sound, track.at(bar, 0.0, .0), pan + (i - (len(notes) - 1) / 2) * .22, send)


# ---- The chords, spelled low to high ------------------------------------

CHORDS = {
    'Am': ['A2', 'E3', 'A3', 'C4', 'E4'], 'C': ['C3', 'G3', 'C4', 'E4', 'G4'],
    'Dm': ['D3', 'A3', 'D4', 'F4', 'A4'], 'E': ['E2', 'B2', 'E3', 'G#3', 'B3'],
    'Em': ['E2', 'B2', 'E3', 'G3', 'B3'], 'F': ['F2', 'C3', 'F3', 'A3', 'C4'],
    'G': ['G2', 'D3', 'G3', 'B3', 'D4'], 'A': ['A2', 'E3', 'A3', 'C#4', 'E4'],
    'Bb': ['Bb2', 'F3', 'Bb3', 'D4', 'F4'], 'Gm': ['G2', 'D3', 'G3', 'Bb3', 'D4'],
    'B7': ['B2', 'F#3', 'A3', 'D#4', 'F#4'], 'F#m': ['F#2', 'C#3', 'F#3', 'A3', 'C#4'],
    'D': ['D3', 'A3', 'D4', 'F#4', 'A4'], 'Bm': ['B2', 'F#3', 'B3', 'D4', 'F#4'],
    'C#': ['C#3', 'G#3', 'C#4', 'F4', 'G#4'], 'F#dim': ['F#2', 'C3', 'F#3', 'A3', 'C4'],
}


def whistle_sound(gain: float):
    def sound(track, freq, seconds, previous):
        return voice(track, freq, seconds, gain, WHISTLE, .006, 5.4, .018, .04, .1, previous)
    return sound


def reed_sound(gain: float):
    def sound(track, freq, seconds, previous):
        return voice(track, freq, seconds, gain, REED, .009, 5.8, .02, .03, .07, previous)
    return sound


def horn_sound(gain: float):
    def sound(track, freq, seconds, previous):
        return voice(track, freq, seconds, gain, HORN, .005, 5.0, .012, .05, .09, previous)
    return sound


# ---- 1-1: dust at sundown. Lonesome, unhurried, a long road ahead ---------

def ruta_1_1() -> Track:
    t = Track(88, 32, 101)
    form = ['Am', 'Am', 'F', 'E', 'Am', 'G', 'F', 'E'] * 2 + ['C', 'G', 'Am', 'Em', 'F', 'C', 'Dm', 'E'] + \
           ['Am', 'Am', 'F', 'E', 'Am', 'G', 'F', 'Am']
    gallop = [(0, 0, 1.0), (1, 2, .7), (1.5, 3, .55), (1.75, 2, .45), (2, 1, .85), (3, 3, .65), (3.5, 4, .5), (3.75, 3, .42)]
    for bar, name in enumerate(form):
        notes = CHORDS[name]
        chord_arp(t, bar, notes, gallop, .34, -.5)
        bass_note(t, bar, 0, notes[0], .42)
        bass_note(t, bar, 2, notes[1], .3)
        if bar >= 8:
            for beat in (.5, 1.5, 2.5, 3.5):
                t.mix(shaker(t, .1, .05), t.at(bar, beat), .4, .05)
    a = ('E5:3 D5:.5 C5:.5 | A4:3 R:1 | C5:1.5 D5:.5 F5:2 | E5:3 R:1 | '
         'E5:1.5 G5:.5 A5:2 | G5:1 E5:1 D5:2 | C5:1 D5:1 C5:1 A4:1 | B4:3 R:1')
    b = ('E5:3 G5:.5 F5:.5 | E5:1.5 C5:.5 A4:2 | C5:1 F5:1 A5:2 | G#5:2 E5:2 | '
         'A5:1.5 G5:.5 E5:2 | D5:1 E5:1 G5:2 | F5:1 E5:1 D5:1 C5:1 | B4:3 R:1')
    c = ('G5:2 E5:1 C5:1 | D5:2 B4:2 | C5:1.5 E5:.5 A5:2 | G5:1 E5:1 B4:2 | '
         'A4:1 C5:1 F5:2 | E5:1 C5:1 G4:2 | A4:1 D5:1 F5:2 | E5:3 R:1')
    d = ('E5:3 D5:.5 C5:.5 | A4:2 C5:2 | D5:1.5 F5:.5 A5:2 | G#5:2 B4:2 | '
         'C5:1.5 E5:.5 A5:2 | B5:1 G5:1 D5:2 | C5:1 A4:1 G4:1 B4:1 | A4:2 C5:1 D5:1')
    sound = whistle_sound(.10)
    for first, line in ((0, a), (8, b), (16, c), (24, d)):
        melody(t, line, first, sound, .35, .42, echo=(.34, .34))
    for beat, note in ((3, 'G2'), (3.5, 'G#2')):  # The bass walks back up to the first A
        bass_note(t, 31, beat, note, .34, .5)
    return t


# ---- 1-2: the rain catches up. Quicker, closer, always moving -------------

def ruta_1_2() -> Track:
    t = Track(108, 36, 202)
    form = (['Dm', 'Dm', 'Bb', 'A', 'Dm', 'C', 'Bb', 'A'] * 2 + ['F', 'C', 'Dm', 'Am', 'Bb', 'F', 'Gm', 'A'] +
            ['Dm', 'Dm', 'Bb', 'A', 'Dm', 'C', 'Bb', 'A'] + ['Dm', 'Dm', 'Bb', 'A'])
    drive = [(b + o, i, s) for b in range(4) for o, i, s in ((0, 2, .9), (.5, 3, .55), (.75, 2, .5))]
    for bar, name in enumerate(form):
        notes = CHORDS[name]
        chord_arp(t, bar, notes, drive, .26, -.5, 1.6, .55)
        bass_note(t, bar, 0, notes[0], .46, .6)
        bass_note(t, bar, 1.5, notes[0], .3, .4)
        bass_note(t, bar, 2.5, notes[1], .36, .5)
        t.mix(drum(t, 120, 58, .4, .34), t.at(bar, 0), 0.0, .1)
        t.mix(drum(t, 150, 72, .28, .17), t.at(bar, 2.5), .1, .1)
        for beat in (.5, 1.5, 2.5, 3.5):
            t.mix(shaker(t, .09, .07), t.at(bar, beat), -.4, .03)
    a = ('D5:1.5 F5:.5 A5:1 F5:1 | E5:1 D5:1 A4:2 | D5:1 F5:1 Bb5:2 | A5:3 R:1 | '
         'F5:1.5 G5:.5 A5:1 D5:1 | E5:1 C5:1 G4:2 | Bb4:1 D5:1 F5:1 G5:1 | E5:3 R:1')
    b = ('A5:1.5 G5:.5 F5:1 D5:1 | C5:1 A4:1 D5:2 | F5:1 Bb5:1 A5:1 F5:1 | E5:2 C#5:2 | '
         'D5:1 F5:1 A5:1.5 C6:.5 | Bb5:1 G5:1 E5:2 | F5:1 D5:1 Bb4:1 D5:1 | C#5:3 R:1')
    c = ('C5:1.5 F5:.5 A5:2 | G5:1 E5:1 C5:2 | D5:1.5 A5:.5 F5:2 | E5:1 C5:1 A4:2 | '
         'Bb4:1 D5:1 F5:2 | A5:1 F5:1 C5:2 | Bb4:1 D5:1 G5:2 | A5:2 E5:2')
    d = ('D5:.5 F5:.5 A5:2 G5:1 | F5:1 E5:1 D5:2 | Bb5:1.5 A5:.5 F5:2 | E5:3 R:1 | '
         'A5:1 F5:1 D5:1 F5:1 | E5:1 G5:1 C5:2 | D5:1 F5:1 Bb5:2 | A5:2 C#5:2 | '
         'D5:3 F5:1 | A5:3 R:1 | F5:1 G5:1 Bb5:2 | A5:2 G5:1 E5:1')
    sound = reed_sound(.06)
    for first, line in ((0, a), (8, b), (16, c), (24, d)):
        melody(t, line, first, sound, .4, .28, echo=(.277, .22))
    for beat, note in ((3, 'A2'), (3.5, 'C#3')):
        bass_note(t, 35, beat, note, .4, .4)
    return t


# ---- 1-3: holy ground. Slow, a breather, nobody here is at rest -----------

def ruta_1_3() -> Track:
    t = Track(58, 22, 303)
    form = ['Em', 'Em', 'C', 'B7', 'Am', 'Em', 'F#dim', 'B7', 'Em', 'C', 'Am', 'Em', 'C', 'Am', 'B7', 'Em',
            'Em', 'C', 'Am', 'B7', 'Em', 'B7']
    for bar, name in enumerate(form):
        notes = CHORDS[name]
        pad(t, bar, 1, [notes[1], notes[2], notes[3]], .05, ORGAN, 0.0, .0015, .55)
        pad(t, bar, 1, [notes[0]], .045, BOW, 0.0, .001, .25)
        if bar % 2 == 0:
            t.mix(bell(t, hz('E4'), 4.5, .11), t.at(bar, 0, .0), -.45, .55)
        for beat, index, strength in ((1, 4, .6), (2.5, 3, .45)):
            sound = pluck(t, hz(notes[index]), 2.6, .26 * strength, .45, 3.2)
            start = t.at(bar, beat)
            t.mix(sound, start, .5, .4)
            t.echo(sound, start, .5, .52, .34)
    a = ('R:2 B4:2 | G4:3 R:1 | E5:2 C5:2 | B4:3 R:1 | A4:2 C5:2 | B4:2 G4:2 | A4:2 F#4:2 | B4:3 R:1')
    b = ('R:2 E5:2 | C5:2 G4:2 | A4:2 E5:2 | B4:3 R:1 | G4:2 E5:2 | C5:2 A4:2 | D#5:2 B4:2 | E5:3 R:1')
    c = ('R:4 | R:2 C5:2 | E5:2 A4:2 | D#5:3 R:1 | B4:3 G4:1 | F#4:2 A4:2')
    sound = whistle_sound(.10)
    for first, line in ((0, a), (8, b), (16, c)):
        melody(t, line, first, sound, -.4, .7, echo=(.62, .42))
    return t


# ---- 1-4: a moon with no owner. Something breathes close by ---------------

def ruta_1_4() -> Track:
    t = Track(76, 28, 404)
    form = (['F#m', 'F#m', 'D', 'C#', 'Bm', 'F#m', 'D', 'C#'] * 2 + ['Bm', 'F#m', 'D', 'A', 'Bm', 'C#', 'F#m', 'C#'] +
            ['F#m', 'D', 'Bm', 'C#'])
    for bar, name in enumerate(form):
        notes = CHORDS[name]
        pad(t, bar, 1, [notes[0], notes[1]], .055, BOW, 0.0, .003, .35)
        # Tremolo: the top note picked over and over, swelling through the bar.
        for step in range(16):
            beat = step * .25
            swell = .4 + .6 * math.sin(math.pi * (step + .5) / 16)
            sound = pluck(t, hz(notes[4]), .5, .15 * swell, .6, 1.2)
            t.mix(sound, t.at(bar, beat, .004), -.5, .25)
        for beat, strength in ((0, 1.0), (.5, .62)):  # A heartbeat
            t.mix(drum(t, 86, 44, .5, .36 * strength, .1), t.at(bar, beat), 0.0, .12)
        bass_note(t, bar, 2.5, notes[0], .24, .8)
    a = ('R:2 C#6:2 | A5:3 R:1 | F#5:2 A5:2 | G#5:3 R:1 | D5:2 F#5:2 | C#5:3 R:1 | D5:1.5 F#5:.5 A5:2 | G#5:3 R:1')
    b = ('C#6:2 E6:2 | C#6:1 A5:1 F#5:2 | A5:2 D6:2 | C#6:3 R:1 | B5:2 F#5:2 | A5:2 C#5:2 | D5:2 A5:2 | G#5:3 R:1')
    c = ('R:2 B5:2 | C#6:2 A5:2 | F#5:2 D6:2 | C#6:2 E5:2 | D5:2 F#5:2 | F5:2 G#5:2 | A5:2 C#6:2 | C#5:3 R:1')
    d = ('F#5:2 C#6:2 | A5:2 F#5:2 | D5:2 B5:2 | G#5:2 F5:1 C#6:1')
    sound = whistle_sound(.085)
    for first, line in ((0, a), (8, b), (16, c), (24, d)):
        melody(t, line, first, sound, .45, .6, echo=(.395, .4))
    return t


# ---- 1-5: the last duel. The whole town is watching, and none of it alive -

def ruta_1_5() -> Track:
    t = Track(124, 48, 505)
    form = (['E', 'E', 'F', 'E', 'Am', 'G', 'F', 'E'] * 3 + ['Am', 'E', 'F', 'E', 'Dm', 'Am', 'F', 'E'] +
            ['E', 'E', 'F', 'E', 'Am', 'G', 'F', 'E'] + ['Am', 'E', 'F', 'E', 'Dm', 'Am', 'F', 'E'])
    assert len(form) == 48
    for bar, name in enumerate(form):
        notes = CHORDS[name]
        for beat, strength, down in ((0, 1.0, True), (1.5, .62, False), (2, .85, True), (3.5, .6, False)):
            strum(t, bar, beat, notes[1:], .17 * strength, .010, -.4, .9, .78, down)
        for beat, note in ((0, 0), (.75, 0), (1.5, 1), (2, 0), (2.75, 0), (3.5, 1)):
            bass_note(t, bar, beat, notes[note], .2, .4)
        t.mix(drum(t, 110, 52, .5, .42), t.at(bar, 0), 0.0, .15)
        t.mix(drum(t, 110, 52, .5, .3), t.at(bar, 2), 0.0, .15)
        for beat, strength in ((1, .5), (1.5, .35), (3, .55), (3.5, .4)):
            t.mix(drum(t, 190, 96, .22, .24 * strength, .5), t.at(bar, beat), .25, .12)
        if bar % 4 == 0:
            pad(t, bar, 4, [notes[0], notes[1]], .04, BOW, 0.0, .003, .3)
    a = ('E5:2 F5:1 G#5:1 | E5:3 R:1 | F5:1.5 A5:.5 C6:2 | B5:3 R:1 | '
         'A5:1 C6:1 E6:2 | D6:1 B5:1 G5:2 | A5:1 G#5:1 F5:2 | E5:3 R:1')
    b = ('B5:1.5 C6:.5 B5:1 G#5:1 | E5:2 B4:2 | C5:1 F5:1 A5:2 | G#5:3 R:1 | '
         'E6:1.5 D6:.5 C6:1 A5:1 | B5:1 G5:1 D5:2 | C6:1 A5:1 F5:2 | G#5:2 E5:2')
    c = ('R:4 | R:2 B4:1 E5:1 | F5:2 C5:2 | E5:3 R:1 | R:4 | R:2 G5:1 B5:1 | C6:2 A5:2 | B5:3 R:1')
    d = ('A5:1.5 C6:.5 E6:2 | G#5:1 B5:1 E6:2 | F6:1.5 E6:.5 C6:2 | B5:3 R:1 | '
         'D6:1 F6:1 A5:2 | C6:1 E6:1 A5:2 | C6:1 B5:1 A5:2 | G#5:3 R:1')
    e = ('E5:1 G#5:1 B5:2 | E6:3 R:1 | F6:1.5 E6:.5 C6:2 | B5:2 G#5:2 | '
         'A5:1 C6:1 E6:2 | D6:1 B5:1 G5:2 | F5:1 A5:1 C6:2 | B5:3 R:1')
    f = ('E6:2 C6:1 A5:1 | B5:2 E5:2 | F5:1 A5:1 C6:2 | B5:2 G#5:2 | '
         'D6:1 C6:1 A5:2 | E6:1 C6:1 A5:2 | F6:1 E6:1 C6:2 | E6:2 B5:1 G#5:1')
    sound = horn_sound(.085)
    for first, line in ((0, a), (8, b), (16, c), (24, d), (32, e), (40, f)):
        melody(t, line, first, sound, .4, .3, echo=(.242, .2))
    for step in range(8):  # The drums roll into the top
        t.mix(drum(t, 190, 96, .2, .13 + .018 * step, .5), t.at(47, 2 + step * .25), .25, .12)
    return t


# ---- The menu: a fire at the ranch, before anyone rides out ----------------

def menu() -> Track:
    t = Track(72, 24, 606)
    form = (['G', 'Em', 'C', 'D', 'G', 'Em', 'C', 'G'] + ['Em', 'C', 'G', 'D', 'Em', 'C', 'Am', 'D'] +
            ['G', 'Em', 'C', 'D', 'G', 'C', 'G', 'D'])
    # Thumb on the low strings, fingers answering above: a fireside picking.
    picking = [(0, 0, 1.0), (.5, 3, .55), (1, 1, .8), (1.5, 4, .5), (2, 0, .9), (2.5, 3, .55), (3, 1, .75), (3.5, 2, .5)]
    for bar, name in enumerate(form):
        notes = CHORDS[name]
        chord_arp(t, bar, notes, picking, .3, -.45, 3.0, .5)
        bass_note(t, bar, 0, notes[0], .2, 1.2)
        if bar >= 8:
            pad(t, bar, 1, [notes[1], notes[2]], .018, ORGAN, .1, .002, .4)
    a = ('D5:2 B4:1 G4:1 | B4:1.5 G4:.5 E4:2 | E5:2 C5:1 A4:1 | D5:3 R:1 | '
         'D5:1.5 E5:.5 G5:2 | E5:1 B4:1 G4:2 | A4:1 C5:1 E5:2 | D5:3 R:1')
    b = ('B4:1.5 E5:.5 G5:2 | E5:1 C5:1 G4:2 | D5:1.5 B4:.5 G4:2 | A4:3 R:1 | '
         'G4:1 B4:1 E5:2 | G5:1 E5:1 C5:2 | E5:1 C5:1 A4:2 | D5:2 F#4:1 A4:1')
    c = ('G4:1 B4:1 D5:2 | E5:1.5 D5:.5 B4:2 | C5:1 E5:1 G5:2 | F#5:3 R:1 | '
         'G5:2 D5:1 B4:1 | C5:1 E5:1 G5:2 | D5:1 B4:1 G4:2 | A4:2 C5:1 B4:.5 A4:.5')
    harmonica = reed_sound(.042)
    whistle = whistle_sound(.075)
    melody(t, a, 0, whistle, .35, .5, echo=(.42, .3))
    melody(t, b, 8, harmonica, .35, .35, echo=(.42, .2))
    melody(t, c, 16, whistle, .35, .5, echo=(.42, .3))
    return t


TRACKS = {
    'menu': ('Fogata en el rancho', 'Menús', 'Pantallas de menú: calma antes de salir. Guitarra de dedos junto al fuego, silbido y armónica.', menu),
    'ruta_1_1': ('Polvo al ocaso', '1-1', 'Atardecer con viento. Western melancólico sin prisa: guitarra al galope, contrabajo y silbido con eco de cañón.', ruta_1_1),
    'ruta_1_2': ('Lluvia de plomo', '1-2', 'Atardecer con lluvia y más zombis. Más rápido y tenso: guitarra corrida, tambor, sonaja y armónica.', ruta_1_2),
    'ruta_1_3': ('Campo santo', '1-3', 'Cementerio: el respiro del juego. Muy lento e inquietante: armonio, cuerda grave, campana lejana y silbido.', ruta_1_3),
    'ruta_1_4': ('Luna sin dueño', '1-4', 'Noche con viento y el salto de dificultad. Guitarra en trémolo sobre cuerda grave, latido y silbido alto.', ruta_1_4),
    'ruta_1_5': ('Último duelo', '1-5', 'Pueblo fantasma, tormenta y jefe. Duelo final: rasgueos, tambores de guerra y trompeta.', ruta_1_5),
}


def write_wav(path: Path, left: list, right: list) -> None:
    pcm = array.array('h', (0 for _ in range(2 * len(left))))
    for i, (a, b) in enumerate(zip(left, right)):
        pcm[2 * i] = round(max(-1.0, min(1.0, a)) * 32767)
        pcm[2 * i + 1] = round(max(-1.0, min(1.0, b)) * 32767)
    if sys.byteorder == 'big':
        pcm.byteswap()
    with wave.open(str(path), 'wb') as out:
        out.setnchannels(2)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(pcm.tobytes())


def check_edges(ffmpeg: str, path: Path, samples: int, name: str) -> None:
    """What the player hears at the jump: the exact length, and quiet edges."""
    raw = subprocess.run([ffmpeg, '-loglevel', 'error', '-i', str(path), '-f', 's16le', '-ar', str(RATE), '-'],
                         check=True, capture_output=True).stdout
    pcm = array.array('h', raw)
    if sys.byteorder == 'big':
        pcm.byteswap()
    if len(pcm) != 2 * samples:
        raise SystemExit(f'music/{name}: decodes to {len(pcm) // 2} samples, expected {samples}')
    edge = max(map(abs, pcm[:8].tolist() + pcm[-8:].tolist())) / 32768
    if edge > EDGE_LIMIT:
        raise SystemExit(f'music/{name}: its edges are not quiet enough for the loop ({edge:.4f})')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('assets', nargs='?', type=Path, default=ROOT / 'assets')
    parser.add_argument('--only', nargs='+', choices=sorted(TRACKS))
    parser.add_argument('--keep-wav', type=Path, help='also leave the uncompressed mixes in this folder')
    args = parser.parse_args()
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        print('make_music: falta ffmpeg (sudo apt install ffmpeg / pacman -S mingw-w64-ucrt-x86_64-ffmpeg)', file=sys.stderr)
        return 1
    folder = args.assets / 'music'
    folder.mkdir(parents=True, exist_ok=True)
    entries = json.loads(MANIFEST.read_text(encoding='utf-8'))['tracks'] if MANIFEST.exists() else {}
    for name in args.only or sorted(TRACKS):
        title, stage, mood, compose = TRACKS[name]
        track = compose()
        left, right = track.finish()
        with tempfile.TemporaryDirectory(prefix='vaquera-music-') as temp:
            mix = Path(temp) / f'{name}.wav'
            write_wav(mix, left, right)
            target = folder / f'{name}.ogg'
            subprocess.run([ffmpeg, '-y', '-loglevel', 'error', '-i', str(mix), '-map_metadata', '-1',
                            '-c:a', 'libvorbis', '-q:a', '3', '-fflags', '+bitexact', str(target)], check=True)
            if args.keep_wav:
                args.keep_wav.mkdir(parents=True, exist_ok=True)
                shutil.copy(mix, args.keep_wav / mix.name)
        check_edges(ffmpeg, target, track.length, name)
        entries[name] = {
            'title': title, 'stage': stage, 'mood': mood, 'seconds': round(track.length / RATE, 3),
            'samples': track.length, 'bpm': track.bpm, 'bars': track.bars,
            'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'bytes': target.stat().st_size,
        }
        print(f'make_music: music/{name}.ogg, {title}, {track.length / RATE:.1f} s, {target.stat().st_size // 1024} KB')
    if args.assets.resolve() == (ROOT / 'assets').resolve():
        MANIFEST.write_text(json.dumps({'license': 'Composed and synthesized by tools/make_music.py; no third-party material.',
                                        'tracks': dict(sorted(entries.items()))}, ensure_ascii=False, indent=2) + '\n',
                            encoding='utf-8', newline='\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
