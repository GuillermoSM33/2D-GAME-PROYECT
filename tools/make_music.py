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
    'Cm': ['C3', 'G3', 'C4', 'Eb4', 'G4'], 'Fm': ['F2', 'C3', 'F3', 'Ab3', 'C4'],
    'Ab': ['Ab2', 'Eb3', 'Ab3', 'C4', 'Eb4'], 'Eb': ['Eb3', 'Bb3', 'Eb4', 'G4', 'Bb4'],
    'G7': ['G2', 'D3', 'F3', 'B3', 'D4'], 'C#m': ['C#3', 'G#3', 'C#4', 'E4', 'G#4'],
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


# ---- The second route: Santa Brasa and the army post past it ---------------
# A town, not the desert: nothing here is plucked or whistled. The first
# route is wood and gut (guitar, bass fiddle, harmonica, whistle); this one is
# wire and current: an electric bass, a drum kit, overdriven guitar, electric
# piano and synthesizers. Its own sounds, below, are used by no other track.

SQUARE = ((1, 1.0), (3, .33), (5, .2), (7, .14), (9, .11), (11, .09))
SAW = tuple((n, 1.0 / n) for n in range(1, 13))


def kick(track: Track, gain: float) -> list:
    """A kick drum: a low thump falling from 130 Hz, a click on its front."""
    count = round(.28 * RATE)
    out, phase = [0.0] * count, 0.0
    for i in range(count):
        t = i / RATE
        phase += math.tau * (46 + 90 * math.exp(-t * 34)) / RATE
        out[i] = (math.sin(phase) * math.exp(-t * 11) + (.5 * math.exp(-t * 400) if i < 200 else 0.0)) * gain
    return out


def snare(track: Track, gain: float, seconds: float = .2) -> list:
    """A snare: its skin's tone under a burst of wires."""
    count = round(seconds * RATE)
    rng, out, last, phase = track.rng, [0.0] * count, 0.0, 0.0
    for i in range(count):
        t = i / RATE
        white = rng.uniform(-1, 1)
        wires = white - .55 * last
        last = white
        phase += math.tau * (185 + 60 * math.exp(-t * 40)) / RATE
        out[i] = (wires * .75 * math.exp(-t * 22) + math.sin(phase) * .6 * math.exp(-t * 30)) * gain
    return out


def hat(track: Track, gain: float, open_: bool = False) -> list:
    """A hi-hat: the top of the noise only; open, it rings on."""
    count = round((.16 if open_ else .045) * RATE)
    rng, out, a, b = track.rng, [0.0] * count, 0.0, 0.0
    for i in range(count):
        white = rng.uniform(-1, 1)
        high = white - a
        a = white
        higher = high - b
        b = high
        out[i] = higher * .5 * gain * math.exp(-i / count * (4 if open_ else 6))
    return out


def e_bass(track: Track, freq: float, seconds: float, gain: float) -> list:
    """An electric bass through an amp: a saw that closes as the note dies, a little grit."""
    count = round(seconds * RATE)
    out, phase = [0.0] * count, 0.0
    step = math.tau * freq / RATE
    for i in range(count):
        t = i / RATE
        phase += step
        bright = .25 + .75 * math.exp(-t * 7)
        tone = math.sin(phase) + bright * (.5 * math.sin(2 * phase) + .33 * math.sin(3 * phase) +
                                           .22 * math.sin(4 * phase) + .15 * math.sin(5 * phase))
        env = min(1.0, i / 60) * math.exp(-t * 2.2) * min(1.0, (count - i) / 300)
        out[i] = math.tanh(tone * 1.4) * gain * env
    return out


def power_chord(track: Track, root: float, seconds: float, gain: float, muted: bool = False) -> list:
    """An overdriven guitar's fifth: root, fifth and octave sawing into a
    clipped amp. muted: the palm on the strings, a short chug."""
    count = round((min(seconds, .13) if muted else seconds) * RATE)
    out = [0.0] * count
    phases = [0.0, 0.0, 0.0]
    steps = [math.tau * root * r * d / RATE for r, d in ((1, 1.0), (1.5, 1.003), (2, .997))]
    for i in range(count):
        t = i / RATE
        tone = 0.0
        for k in range(3):
            phases[k] += steps[k]
            p = phases[k] % math.tau
            tone += (p / math.pi - 1.0)                 # A saw
        drive = 4.0 if not muted else 6.0
        env = min(1.0, i / 40) * (math.exp(-t * (26 if muted else 1.6))) * min(1.0, (count - i) / 400)
        out[i] = math.tanh(tone * drive * (.4 + .6 * env)) * gain * env
    # The speaker rolls the fizz off: a one-pole low-pass.
    low = 0.0
    for i in range(count):
        low += (.2 if muted else .32) * (out[i] - low)
        out[i] = low
    return out


def e_piano(track: Track, freq: float, seconds: float, gain: float) -> list:
    """An electric piano: a tine's bell over a hollow body (two-operator FM), a slow tremolo."""
    count = round(seconds * RATE)
    out = [0.0] * count
    for i in range(count):
        t = i / RATE
        index = 2.2 * math.exp(-t * 6) + .35
        tone = math.sin(math.tau * freq * t + index * math.sin(math.tau * freq * 2 * t))
        tine = .25 * math.sin(math.tau * freq * 7.02 * t) * math.exp(-t * 18)
        env = min(1.0, i / 30) * math.exp(-t * 2.4) * min(1.0, (count - i) / 300)
        out[i] = (tone + tine) * gain * env * (1 + .12 * math.sin(math.tau * 5.2 * t))
    return out


def lead_sound(gain: float, partials=SQUARE):
    """A synthesizer lead: a hollow square wave that slides into its notes."""
    def sound(track, freq, seconds, previous):
        return voice(track, freq, seconds, gain, partials, .008, 5.6, 0.0, .02, .08, previous)
    return sound


def kit(t: Track, bar: int, pattern: str, gain: float = 1.0) -> None:
    """A bar of drums in sixteenths: k kick, s snare, h hat, o open hat, . rest;
    two lines: 'k...s...k.k.s...' and the hats under it."""
    drums, hats = pattern.split('/')
    for step, c in enumerate(drums):
        if c == 'k':
            t.mix(kick(t, .55 * gain), t.at(bar, step * .25, .002), 0.0, .04)
        elif c == 's':
            t.mix(snare(t, .34 * gain), t.at(bar, step * .25, .002), .08, .16)
    for step, c in enumerate(hats):
        if c in 'ho':
            t.mix(hat(t, (.13 if step % 4 == 0 else .09) * gain, c == 'o'), t.at(bar, step * .25, .002), -.35, .05)


def root_of(chords: dict, name: str, octave: int = 0) -> float:
    return hz(chords[name][0]) * 2 ** octave


def ruta_2_1() -> Track:
    """2-1: dawn on the outskirts. Empty streets: an electric piano turning
    over a chord, a bass that walks on, a far synth; the drums come in late."""
    t = Track(100, 32, 701)
    form = (['Dm', 'Dm', 'Bb', 'C', 'Dm', 'Am', 'Bb', 'A'] * 2 + ['F', 'C', 'Bb', 'F', 'Gm', 'Dm', 'Bb', 'A'] +
            ['Dm', 'Bb', 'Gm', 'A', 'Dm', 'C', 'Bb', 'A'])
    for bar, name in enumerate(form):
        notes = CHORDS[name]
        for step, index in enumerate((1, 2, 3, 4, 3, 2, 3, 4)):
            t.mix(e_piano(t, hz(notes[index]), .9, .11 if step % 2 == 0 else .08), t.at(bar, step * .5), -.3 + .1 * (step % 3), .3)
        t.mix(e_bass(t, hz(notes[0]) / 2 if hz(notes[0]) > 90 else hz(notes[0]), 1.6, .3), t.at(bar, 0), 0.0, .05)
        t.mix(e_bass(t, hz(notes[1]) / 2, .7, .2), t.at(bar, 2.5), 0.0, .05)
        pad(t, bar, 1, [notes[2], notes[4]], .02, SAW, .2, .003, .5)
        if bar >= 8:
            kit(t, bar, 'k.......s.....k./h.h.h.h.h.h.h.o.', .8)
    a = ('D5:2 F5:1 E5:1 | D5:3 R:1 | F5:1 G5:1 Bb5:2 | A5:3 R:1 | '
         'D5:1 E5:1 F5:2 | E5:1 C5:1 A4:2 | Bb4:1 D5:1 G5:2 | A5:3 R:1')
    b = ('A5:2 G5:1 F5:1 | E5:2 C5:2 | D5:1 F5:1 Bb5:2 | A5:2 E5:2 | '
         'F5:1.5 E5:.5 D5:2 | C5:1 E5:1 A5:2 | G5:1 F5:1 D5:2 | C#5:3 R:1')
    c = ('C5:2 F5:2 | E5:1 G5:1 C6:2 | Bb5:1 A5:1 F5:2 | A5:3 R:1 | '
         'G5:1 Bb5:1 D6:2 | A5:2 F5:2 | D5:1 F5:1 Bb5:2 | A5:2 E5:2')
    d = ('D5:2 A5:2 | Bb5:2 F5:2 | G5:1 Bb5:1 D6:2 | C#6:3 R:1 | '
         'A5:2 F5:1 D5:1 | E5:1 G5:1 C6:2 | Bb5:1 G5:1 D5:2 | C#5:2 E5:2')
    sound = lead_sound(.045)
    for first, line in ((0, a), (8, b), (16, c), (24, d)):
        melody(t, line, first, sound, .35, .5, echo=(.3, .35))
    return t


def ruta_2_2() -> Track:
    """2-2: rain on the asphalt downtown. A bass in running eighths, a kit, a
    guitar chugging under its palm, and a square lead over it all."""
    t = Track(118, 32, 702)
    form = (['Am', 'Am', 'F', 'E', 'Am', 'G', 'F', 'E'] * 2 + ['Dm', 'Am', 'F', 'E', 'Dm', 'Am', 'Bb', 'E'] +
            ['Am', 'F', 'Dm', 'E', 'Am', 'G', 'F', 'E'])
    for bar, name in enumerate(form):
        notes = CHORDS[name]
        root = root_of(CHORDS, name)
        low = root / 2 if root > 100 else root
        for step in range(8):
            t.mix(e_bass(t, low * (2 if step == 7 else 1), .26, .26 if step % 2 == 0 else .2), t.at(bar, step * .5), 0.0, .04)
        kit(t, bar, 'k...s...k.k.s...' + '/' + 'h.h.h.h.h.h.h.h.' if bar % 4 != 3 else 'k...s...k.k.s.ss/h.h.h.h.h.h.o...')
        for step in (0, 1, 3, 4, 6, 7):
            t.mix(power_chord(t, low * 2, .2, .09, muted=True), t.at(bar, step * .5), .4, .08)
        if bar % 8 in (3, 7):
            t.mix(power_chord(t, low * 2, 1.8, .1), t.at(bar, 2), .4, .2)
        t.mix(e_piano(t, hz(notes[3]), 1.5, .05), t.at(bar, 0), -.45, .35)
    a = ('A4:1 C5:1 E5:2 | D5:1 C5:1 A4:2 | F5:1.5 E5:.5 C5:2 | B4:3 R:1 | '
         'A4:1 C5:1 E5:1 G5:1 | F5:2 D5:2 | C5:1 A4:1 F5:2 | E5:3 R:1')
    b = ('E5:1.5 G5:.5 A5:2 | G5:1 E5:1 C5:2 | F5:1 A5:1 C6:2 | B5:2 G#5:2 | '
         'A5:1 E5:1 C5:2 | D5:1 B4:1 G4:2 | A4:1 C5:1 F5:2 | E5:3 R:1')
    c = ('D5:1 F5:1 A5:2 | C5:1 E5:1 A5:2 | F5:2 C6:2 | B5:2 G#5:2 | '
         'F5:1 A5:1 D6:2 | C6:2 A5:2 | Bb5:1 D6:1 F5:2 | E5:2 B4:2')
    d = ('A5:2 E5:2 | F5:1 A5:1 C6:2 | D5:2 F5:2 | E5:2 G#5:2 | '
         'A5:1 C6:1 E6:2 | D6:1 B5:1 G5:2 | C6:1 A5:1 F5:2 | E5:3 R:1')
    sound = lead_sound(.05)
    for first, line in ((0, a), (8, b), (16, c), (24, d)):
        melody(t, line, first, sound, .2, .3, echo=(.254, .25))
    return t


def ruta_2_3() -> Track:
    """2-3: the rail yard. Hats in sixteenths like wheels on the joints, a
    bass that never leaves its note, guitar stabs on the off-beats, a saw lead."""
    t = Track(126, 32, 703)
    form = (['Em', 'Em', 'C', 'B7', 'Em', 'D', 'C', 'B7'] * 2 + ['Am', 'Em', 'C', 'B7', 'Am', 'Em', 'F#dim', 'B7'] +
            ['Em', 'C', 'Am', 'B7', 'Em', 'D', 'C', 'B7'])
    for bar, name in enumerate(form):
        root = root_of(CHORDS, name)
        low = root / 2 if root > 100 else root
        kit(t, bar, 'k..k..k.s..k..k./hhhhhhhhhhhhhhho')
        for step in (0, 1.5, 3, 4.5, 6, 7):
            t.mix(e_bass(t, low, .3, .25), t.at(bar, step * .5), 0.0, .04)
        for beat in (1.5, 3.5):
            t.mix(power_chord(t, low * 2, .32, .1), t.at(bar, beat), -.4, .15)
        if bar % 4 == 0:
            pad(t, bar, 4, [CHORDS[name][1], CHORDS[name][3]], .018, SAW, 0.0, .003, .5)
    a = ('E5:3 G5:1 | F#5:2 D#5:2 | E5:1 G5:1 C6:2 | B5:3 R:1 | '
         'E5:1 B4:1 E5:1 G5:1 | F#5:1 D5:1 A4:2 | G5:1 E5:1 C5:2 | B4:3 R:1')
    b = ('B5:2 A5:1 G5:1 | F#5:2 B4:2 | C5:1 E5:1 G5:2 | F#5:2 D#5:2 | '
         'E5:1 G5:1 B5:2 | A5:1 F#5:1 D5:2 | E5:1 G5:1 C6:2 | B5:3 R:1')
    c = ('A4:1 C5:1 E5:2 | G5:2 E5:2 | C6:1.5 B5:.5 G5:2 | F#5:2 D#5:2 | '
         'A5:1 C6:1 E6:2 | B5:2 G5:2 | A5:1 F#5:1 C5:2 | B4:3 R:1')
    d = ('E5:2 B5:2 | C6:2 G5:2 | A5:1 C6:1 E6:2 | D#6:3 R:1 | '
         'E6:1 B5:1 G5:2 | F#5:1 A5:1 D6:2 | C6:1 G5:1 E5:2 | D#5:2 F#5:2')
    sound = lead_sound(.04, SAW)
    for first, line in ((0, a), (8, b), (16, c), (24, d)):
        melody(t, line, first, sound, .3, .4, echo=(.238, .3))
    return t


def ruta_2_4() -> Track:
    """2-4: downtown by night. A sub pulse, a cold synth pad, a snare far off
    in a big room, an electric piano's bell, and a lead that wails like a siren."""
    t = Track(86, 28, 704)
    form = (['C#m', 'C#m', 'A', 'G#3x', 'F#m', 'C#m', 'D', 'G#3x'] * 2 +
            ['A', 'E', 'F#m', 'C#m', 'D', 'A', 'F#m', 'G#3x'] + ['C#m', 'A', 'F#m', 'G#3x'])
    chords = dict(CHORDS)
    chords['G#3x'] = ['G#2', 'D#3', 'G#3', 'C4', 'D#4']
    for bar, name in enumerate(form):
        notes = chords[name]
        low = hz(notes[0]) / 2 if hz(notes[0]) > 90 else hz(notes[0])
        pad(t, bar, 1, [notes[1], notes[2], notes[3]], .028, SAW, 0.0, .004, .55)
        for beat, strength in ((0, 1.0), (.75, .6), (2.5, .8)):
            t.mix(e_bass(t, low, .5, .3 * strength), t.at(bar, beat), 0.0, .04)
        t.mix(kick(t, .5), t.at(bar, 0, .002), 0.0, .05)
        t.mix(snare(t, .2, .3), t.at(bar, 2, .002), .1, .6)
        for step in (2, 6, 10, 14):
            t.mix(hat(t, .06), t.at(bar, step * .25, .002), -.4, .1)
        for step, index in ((0, 4), (3, 3), (6, 4), (11, 2)):
            t.mix(e_piano(t, hz(notes[index]) * 2, 1.2, .045), t.at(bar, step * .25), .45, .5)
    a = ('R:2 G#5:2 | E5:3 R:1 | C#5:2 E5:2 | D#5:3 R:1 | '
         'F#5:2 A5:2 | G#5:2 E5:2 | F#5:1.5 A5:.5 D5:2 | C5:3 R:1')
    b = ('G#5:2 C#6:2 | B5:2 G#5:2 | A5:2 E5:2 | D#5:3 R:1 | '
         'C#6:2 E6:2 | B5:1 G#5:1 E5:2 | F#5:2 A5:2 | G#5:3 R:1')
    c = ('E5:2 A5:2 | G#5:2 B5:2 | A5:2 F#5:2 | E5:3 R:1 | '
         'F#5:1 A5:1 D6:2 | C#6:2 A5:2 | F#5:2 C#5:2 | C5:3 R:1')
    d = ('C#5:2 G#5:2 | E5:2 A5:2 | F#5:2 C#6:2 | C6:3 R:1')
    sound = lead_sound(.04)
    for first, line in ((0, a), (8, b), (16, c), (24, d)):
        melody(t, line, first, sound, -.25, .6, echo=(.349, .4))
    return t


def ruta_2_5() -> Track:
    """2-5: the army post. Everything at once: a double kick, a snare on the
    two and the four, guitars held and chugging, a bass in eighths, the lead on top."""
    t = Track(138, 48, 705)
    form = (['Cm', 'Cm', 'Ab', 'G', 'Cm', 'Bb', 'Ab', 'G'] * 2 + ['Fm', 'Cm', 'Ab', 'G', 'Fm', 'Cm', 'Ab', 'G'] +
            ['Cm', 'Cm', 'Ab', 'G', 'Cm', 'Bb', 'Ab', 'G'] + ['Ab', 'Eb', 'Fm', 'Cm', 'Ab', 'Bb', 'Fm', 'G'] +
            ['Cm', 'Ab', 'Fm', 'G', 'Cm', 'Bb', 'Ab', 'G'])
    assert len(form) == 48
    for bar, name in enumerate(form):
        root = root_of(CHORDS, name)
        low = root / 2 if root > 100 else root
        fill = bar % 8 == 7
        kit(t, bar, ('k.k.s.k.k.k.s.k.' if not fill else 'k.k.s.k.ssssssss') + '/' + 'h.h.h.h.h.h.h.h.')
        for step in range(8):
            t.mix(e_bass(t, low, .2, .24), t.at(bar, step * .5), 0.0, .04)
        t.mix(power_chord(t, low * 2, 1.7, .085), t.at(bar, 0), -.45, .15)
        for step in (4, 5, 7):
            t.mix(power_chord(t, low * 2, .2, .085, muted=True), t.at(bar, step * .5), .45, .08)
        if 16 <= bar < 24 or bar >= 32:
            pad(t, bar, 1, [CHORDS[name][2], CHORDS[name][4]], .016, SAW, 0.0, .003, .4)
    a = ('C5:2 Eb5:1 G5:1 | F5:2 Eb5:2 | Ab5:1.5 G5:.5 F5:2 | D5:3 R:1 | '
         'C5:1 Eb5:1 G5:2 | Bb5:1 Ab5:1 G5:2 | F5:1 Ab5:1 C6:2 | B5:3 R:1')
    b = ('G5:1.5 Ab5:.5 G5:1 Eb5:1 | C5:2 G4:2 | Ab4:1 C5:1 Eb5:2 | D5:3 R:1 | '
         'C6:1.5 Bb5:.5 Ab5:1 G5:1 | F5:1 D5:1 Bb4:2 | Ab5:1 F5:1 C5:2 | B4:2 D5:2')
    c = ('F5:2 Ab5:2 | G5:1 Eb5:1 C5:2 | Eb5:1 Ab5:1 C6:2 | B5:3 R:1 | '
         'Ab5:1 C6:1 F6:2 | Eb6:1 C6:1 G5:2 | F5:1 Ab5:1 C6:2 | D6:2 B5:2')
    d = ('C6:2 G5:1 Eb5:1 | D5:2 G5:2 | Ab5:1.5 G5:.5 F5:2 | G5:3 R:1 | '
         'Eb5:1 G5:1 C6:2 | D6:1 Bb5:1 F5:2 | Eb5:1 Ab5:1 C6:2 | B5:3 R:1')
    e = ('Eb5:2 Ab5:2 | G5:1 Bb5:1 Eb6:2 | C6:2 Ab5:2 | G5:3 R:1 | '
         'Ab5:1 C6:1 Eb6:2 | D6:1 Bb5:1 F5:2 | Ab5:1 F5:1 C5:2 | D5:2 B4:2')
    f = ('C5:1 Eb5:1 G5:2 | Ab5:2 C6:2 | F5:1 Ab5:1 C6:2 | B5:3 R:1 | '
         'C6:2 G5:1 Eb5:1 | D5:1 F5:1 Bb5:2 | C6:1 Ab5:1 F5:2 | G5:2 B5:2')
    sound = lead_sound(.05)
    for first, line in ((0, a), (8, b), (16, c), (24, d), (32, e), (40, f)):
        melody(t, line, first, sound, .15, .3, echo=(.217, .22))
    return t


def menu_2() -> Track:
    """The menus once she has reached the city: a dead sign's hum of a pad,
    an electric piano picking over it, a bass note a bar, a kick like a pulse."""
    t = Track(84, 24, 707)
    form = (['Cm', 'Ab', 'Fm', 'G', 'Cm', 'Ab', 'Eb', 'G'] + ['Fm', 'Cm', 'Ab', 'G', 'Fm', 'Cm', 'Ab', 'G'] +
            ['Cm', 'Ab', 'Fm', 'G', 'Cm', 'Bb', 'Ab', 'G'])
    for bar, name in enumerate(form):
        notes = CHORDS[name]
        low = hz(notes[0]) / 2 if hz(notes[0]) > 90 else hz(notes[0])
        pad(t, bar, 1, [notes[1], notes[2], notes[4]], .024, SAW, 0.0, .003, .55)
        t.mix(e_bass(t, low, 2.2, .26), t.at(bar, 0), 0.0, .05)
        for step, index in enumerate((2, 3, 4, 3, 2, 4, 3, 2)):
            t.mix(e_piano(t, hz(notes[index]) * (2 if step in (2, 5) else 1), 1.1, .075), t.at(bar, step * .5),
                  -.35 + .1 * (step % 4), .4)
        t.mix(kick(t, .36), t.at(bar, 0, .002), 0.0, .05)
        if bar >= 8:
            t.mix(kick(t, .26), t.at(bar, 2.5, .002), 0.0, .05)
            for step in (4, 12):
                t.mix(hat(t, .05), t.at(bar, step * .25, .002), .4, .1)
    a = ('G5:3 Eb5:1 | C5:3 R:1 | Ab5:2 F5:2 | D5:3 R:1 | G5:2 C6:2 | Ab5:3 R:1 | Bb5:2 G5:2 | D5:3 R:1')
    b = ('C6:2 Ab5:2 | G5:3 Eb5:1 | C5:2 Eb5:2 | D5:3 R:1 | Ab5:2 C6:2 | G5:2 Eb5:2 | C5:1 Eb5:1 Ab5:2 | G5:3 R:1')
    c = ('Eb5:2 G5:2 | Ab5:3 R:1 | C6:2 Ab5:2 | B5:3 R:1 | G5:3 Eb5:1 | F5:2 D5:2 | Eb5:1 C5:1 Ab4:2 | G4:3 R:1')
    sound = lead_sound(.035)
    for first, line in ((0, a), (8, b), (16, c)):
        melody(t, line, first, sound, .3, .6, echo=(.357, .4))
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
    'menu_2': ('Neón apagado', 'Menús (fase 2)', 'Menús con el fondo de la ciudad. Colchón de sintetizador, piano eléctrico, bajo y un pulso de bombo.', menu_2),
    'ruta_2_1': ('Santa Brasa al alba', '2-1', 'Las afueras al amanecer. Piano eléctrico en arpegio, bajo eléctrico, sintetizador lejano; la batería entra tarde.', ruta_2_1),
    'ruta_2_2': ('Lluvia en el asfalto', '2-2', 'El centro bajo la lluvia. Bajo en corcheas, batería, guitarra distorsionada apagada con la palma y sintetizador solista.', ruta_2_2),
    'ruta_2_3': ('Vías muertas', '2-3', 'El patio de maniobras. Platillos en semicorcheas como ruedas en las juntas, bajo ostinato, golpes de guitarra a contratiempo.', ruta_2_3),
    'ruta_2_4': ('Toque de sirenas', '2-4', 'El centro de noche. Subgrave, colchón frío de sintetizador, caja lejana con eco, campana de piano eléctrico y un solista que aúlla.', ruta_2_4),
    'ruta_2_5': ('Puesto Cerro Gris', '2-5', 'La base militar y su jefe. Doble bombo, caja en dos y cuatro, guitarras sostenidas y apagadas, bajo en corcheas.', ruta_2_5),
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
