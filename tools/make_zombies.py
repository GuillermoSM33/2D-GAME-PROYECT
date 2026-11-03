#!/usr/bin/env python3
"""Export native 72x72 zombie sheets from approved raster source atlases.

Uses the repository's standard-library PNG reader/writer. Creative source
art is produced with imagegen; this tool only crops, aligns, resamples with
nearest-neighbor and reindexes to the game's warm palette. It never draws
faces or uniforms. The four originals in sprites/zombies/riot stay read-only.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import math
import shutil
from pathlib import Path

from embed_assets import decode_png_rgba
from make_sprites import Image

ROOT = Path(__file__).resolve().parent.parent
FRAME = 72
ALPHA_MIN = 160
ACTIONS = {'idle': 4, 'walk': 8, 'run': 8, 'attack': 6, 'hurt': 3, 'death': 8, 'caught': 4}
IDS = ['soldier', 'police', 'riot_shield'] + [
    f'civil_{sex}_{number}' for sex in ('male', 'female') for number in range(1, 6)
] + ['burned', 'skeleton', 'dog', 'sheriff', 'cowboy', 'motorcycle', 'priest',
     'jailer', 'firefighter', 'butcher', 'riot', 'elite']
ORIGINAL_HASHES = {
    'walk': '46cb16616b3d68f699ae5a878039b827e73caad8aa6ff7e6c40360e8584020ca',
    'attack': '7a9233906b625087187993f436bf8e1ce9e6f9bda6dfbaa1908bbd0b51a12fac',
    'hurt': '073e8badff14ff69edc19e734b5c64ce1227c8d67dbb1e8030ba543606cfc336',
    'death': 'f9ee929877ed6c0865511df9cc75da69d127281ac3072f94412c47b5e83c10aa',
}
SKIN_RGB = {(0x4a, 0x52, 0x40), (0x6f, 0x7a, 0x5c), (0x9a, 0xa3, 0x7e)}
EYE_RGB = (0xff, 0xf1, 0xa0)
RIOT_ATTACK_EFFECT_RGB = {(0xfb, 0xaa, 0x38), (0xd0, 0x33, 0x05)}

# Existing cowgirl/zombie ramps, including matte linen, rusty fabric and
# charcoal. Original protected colors remain exact; garments use these ramps.
PALETTE_HEX = (0x252018, 0x2c2c2c, 0x2a2e38, 0x3c4250, 0x5a6272, 0xa7a8a8,
               0x1f3256, 0x2e4a7a, 0x4a74b5, 0x4a5240, 0x6f7a5c, 0x9aa37e,
               0x463322, 0x684833, 0x876439, 0xb0834e, 0x4d5a1c, 0x76862c,
               0xa9b956, 0x6b333a, 0x902004, 0x89411f, 0xb45c32, 0xd99a5b,
               0x8f7859, 0xb4996d, 0xd7ab57, 0xfedca3, 0x424242, 0x505050,
               0x868689, 0xfff1a0, 0xfbaa38, 0xd03305, 0x8e8266, 0xb8ab8a, 0xd6c8a7)
PALETTE = tuple(((c >> 16) & 255, (c >> 8) & 255, c & 255, 255) for c in PALETTE_HEX)
CLOTH_PALETTE = tuple(c for c in PALETTE if c[:3] not in SKIN_RGB and c[:3] != EYE_RGB)


def visible_bbox(width: int, height: int, rgba: bytes) -> tuple[int, int, int, int]:
    left, top, right, bottom = width, height, -1, -1
    for y in range(height):
        for x in range(width):
            if rgba[(y * width + x) * 4 + 3] < ALPHA_MIN:
                continue
            left, right = min(left, x), max(right, x)
            top, bottom = min(top, y), max(bottom, y)
    if right < left:
        raise ValueError('La fuente no tiene una figura visible.')
    return left, top, right + 1, bottom + 1


def palette_color(red: int, green: int, blue: int) -> tuple[int, int, int, int]:
    # Clothing is not classified as skin from its green channel: that turned
    # cream linen into lime green and erased the approved source's material.
    return min(CLOTH_PALETTE, key=lambda c: (red - c[0]) ** 2 +
                                     (green - c[1]) ** 2 + (blue - c[2]) ** 2)


def from_rgba(width: int, height: int, rgba: bytes) -> Image:
    image = Image(width, height)
    image.px = [tuple(rgba[at:at + 4]) for at in range(0, len(rgba), 4)]
    return image


def original_path(action: str) -> Path:
    canonical = ROOT / 'assets/sprites/zombies/riot' / f'{action}.png'
    path = canonical
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != ORIGINAL_HASHES[action]:
        raise ValueError(f'{path}: original source is missing or changed')
    return path


@lru_cache(maxsize=None)
def original_frame(action: str, index: int = 0) -> Image:
    width, height, rgba = decode_png_rgba(original_path(action))
    image = Image(FRAME, FRAME)
    for y in range(FRAME):
        for x in range(FRAME):
            at = (y * width + index * FRAME + x) * 4
            image.set(x, y, tuple(rgba[at:at + 4]))
    return image


def original_walk_frame(index: int = 0) -> Image:
    return original_frame('walk', index)


@lru_cache(maxsize=None)
def face_box(frame: Image) -> tuple[int, int, int, int]:
    """Locate the original olive face by its surrounding grey mask rim.

    The raised claw can be higher than the face during an attack, so choosing
    the topmost green pixel incorrectly repainted the face as a helmet.
    """
    remaining = {(x, y) for y in range(FRAME) for x in range(FRAME)
                 if frame.get(x, y)[3] and frame.get(x, y)[:3] in SKIN_RGB}
    components = []
    while remaining:
        pending = [remaining.pop()]
        component = []
        while pending:
            x, y = pending.pop()
            component.append((x, y))
            for point in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if point in remaining:
                    remaining.remove(point)
                    pending.append(point)
        rim = {(x + dx, y + dy) for x, y in component
               for dx in range(-2, 3) for dy in range(-2, 3)
               if frame.get(x + dx, y + dy)[:3] == (0xa7, 0xa8, 0xa8)}
        components.append((len(rim) * 20 + len(component), component))
    if not components:
        return (29, 15, 45, 33)
    points = max(components, key=lambda item: item[0])[1]
    return (min(x for x, y in points) - 3, min(y for x, y in points) - 3,
            max(x for x, y in points) + 4, max(y for x, y in points) + 4)


def on_face(frame: Image, x: int, y: int) -> bool:
    x0, y0, x1, y1 = face_box(frame)
    return x0 <= x < x1 and y0 <= y < y1


def garment_pixel(original: Image, x: int, y: int) -> bool:
    """Registration mask: the original body/face/skin/outline never gets redrawn."""
    pixel = original.get(x, y)
    if pixel[3] == 0:
        return False
    if on_face(original, x, y):
        return False
    if any(original.get(nx, ny)[3] == 0 for nx, ny in
           ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))):
        return False
    if pixel[:3] in SKIN_RGB or pixel[:3] in (
            (0x25, 0x20, 0x18), EYE_RGB, (0x6b, 0x33, 0x3a), (0x90, 0x20, 0x04)):
        return False
    if x >= 29 and 15 <= y <= 32:
        return False
    return y <= 17 or 25 <= y <= 59


def compose_walk_uniform(source: Path) -> Image:
    """Use only the edited garment layer, clipped onto the original walk pixels.

    This is deliberately not a new-body import. All alpha, external contour,
    hands, the original abstract face, boots, and eight original poses remain
    byte-identical. Source clothing is registered per original frame bounds.
    """
    width, height, rgba = decode_png_rgba(source)
    output = Image(FRAME * 8, FRAME)
    for index in range(8):
        original = original_walk_frame(index)
        left = index * width // 8
        right = (index + 1) * width // 8
        points = [(x, y) for y in range(height) for x in range(left, right)
                  if rgba[(y * width + x) * 4 + 3] >= ALPHA_MIN]
        if not points:
            raise ValueError(f'{source}: falta el cuadro de caminar {index}.')
        sx0, sy0 = min(x for x, y in points), min(y for x, y in points)
        sx1, sy1 = max(x for x, y in points) + 1, max(y for x, y in points) + 1
        visible = [(x, y) for y in range(FRAME) for x in range(FRAME)
                   if original.get(x, y)[3]]
        tx0, ty0 = min(x for x, y in visible), min(y for x, y in visible)
        tx1, ty1 = max(x for x, y in visible) + 1, max(y for x, y in visible) + 1
        for y in range(FRAME):
            for x in range(FRAME):
                color = original.get(x, y)
                if garment_pixel(original, x, y):
                    sx = min(sx1 - 1, sx0 + int((x - tx0 + 0.5) * (sx1 - sx0) / (tx1 - tx0)))
                    sy = min(sy1 - 1, sy0 + int((y - ty0 + 0.5) * (sy1 - sy0) / (ty1 - ty0)))
                    at = (sy * width + sx) * 4
                    if rgba[at + 3] >= ALPHA_MIN:
                        # Retain the original material's small shadow/highlight
                        # clusters instead of replacing a jacket by flat color.
                        value = sum(color[c] * (0.299, 0.587, 0.114)[c] for c in range(3))
                        shade = max(-14.0, min(28.0, (value - 70.0) * .45))
                        color = palette_color(*(max(0, min(255, int(rgba[at + c] + shade)))
                                                for c in range(3)))
                output.set(index * FRAME + x, y, color)
    return output


def sheet_frames(sheet: Image) -> list[Image]:
    frames = []
    for index in range(sheet.width // FRAME):
        frame = Image(FRAME, FRAME)
        for y in range(FRAME):
            for x in range(FRAME):
                frame.set(x, y, sheet.get(index * FRAME + x, y))
        frames.append(frame)
    return frames


def sheet_from_frames(frames: list[Image]) -> Image:
    sheet = Image(len(frames) * FRAME, FRAME)
    for index, frame in enumerate(frames):
        for y in range(FRAME):
            for x in range(FRAME):
                sheet.set(index * FRAME + x, y, frame.get(x, y))
    return sheet


def add_shared_attack_effect(sheet: Image) -> Image:
    """Keep the approved riot claw slash on every generated attack sheet."""
    frames = sheet_frames(sheet)
    original = [original_frame('attack', index) for index in range(ACTIONS['attack'])]
    for index, frame in enumerate(frames):
        source = original[index]
        for y in range(FRAME):
            for x in range(FRAME):
                if source.get(x, y)[:3] in RIOT_ATTACK_EFFECT_RGB:
                    frame.set(x, y, source.get(x, y))
    return sheet_from_frames(frames)


def bounds(frame: Image) -> tuple[int, int, int, int]:
    points = [(x, y) for y in range(frame.height) for x in range(frame.width) if frame.get(x, y)[3]]
    if not points:
        raise ValueError('Empty native animation frame')
    return min(x for x, y in points), min(y for x, y in points), \
        max(x for x, y in points) + 1, max(y for x, y in points) + 1


class BodyMap:
    """Body-relative coordinates follow the original body's fall and recoil.

    This is registration of an existing pose, not a new silhouette: clothing
    samples rotate with the torso while original skin, effects and outline stay.
    """
    def __init__(self, frame: Image) -> None:
        body = [(x, y) for y in range(FRAME) for x in range(FRAME)
                if frame.get(x, y)[3] and frame.get(x, y)[:3] not in
                ((0xfb, 0xaa, 0x38), (0xd0, 0x33, 0x05), (0x90, 0x20, 0x04), EYE_RGB)]
        self.cx = sum(x for x, y in body) / len(body)
        self.cy = sum(y for x, y in body) / len(body)
        xx = sum((x - self.cx) ** 2 for x, y in body)
        yy = sum((y - self.cy) ** 2 for x, y in body)
        xy = sum((x - self.cx) * (y - self.cy) for x, y in body)
        angle = .5 * math.atan2(2 * xy, xx - yy)
        self.vx, self.vy = math.cos(angle), math.sin(angle)
        skins = [(x, y) for x, y in body if frame.get(x, y)[:3] in SKIN_RGB]
        if skins:
            hx0, hy0, hx1, hy1 = face_box(frame)
            head = ((hx0 + hx1) / 2, (hy0 + hy1) / 2)
            if (head[0] - self.cx) * self.vx + (head[1] - self.cy) * self.vy > 0:
                self.vx, self.vy = -self.vx, -self.vy
        elif self.vy < 0:
            self.vx, self.vy = -self.vx, -self.vy
        self.ux, self.uy = self.vy, -self.vx
        us = [(x - self.cx) * self.ux + (y - self.cy) * self.uy for x, y in body]
        vs = [(x - self.cx) * self.vx + (y - self.cy) * self.vy for x, y in body]
        self.u0, self.v0 = min(us), min(vs)
        self.du, self.dv = max(1.0, max(us) - self.u0), max(1.0, max(vs) - self.v0)

    def uv(self, x: float, y: float) -> tuple[float, float]:
        return (((x - self.cx) * self.ux + (y - self.cy) * self.uy - self.u0) / self.du,
                ((x - self.cx) * self.vx + (y - self.cy) * self.vy - self.v0) / self.dv)

    def xy(self, u: float, v: float) -> tuple[int, int]:
        a, b = self.u0 + u * self.du, self.v0 + v * self.dv
        return int(round(self.cx + a * self.ux + b * self.vx)), \
            int(round(self.cy + a * self.uy + b * self.vy))


def protected_pixel(frame: Image, x: int, y: int, mapping: BodyMap | None = None) -> bool:
    color = frame.get(x, y)
    if not color[3]:
        return True
    if on_face(frame, x, y):
        return True
    if color[:3] in SKIN_RGB or color[:3] in ((0x25, 0x20, 0x18), EYE_RGB,
            (0x90, 0x20, 0x04), (0xd0, 0x33, 0x05), (0xfb, 0xaa, 0x38), (0x6b, 0x33, 0x3a)):
        return True
    if any(not frame.get(x + dx, y + dy)[3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
        return True
    if mapping is not None:
        _, v = mapping.uv(x, y)
        return v > .88 or .17 < v < .31
    return not garment_pixel(frame, x, y)


def source_cells(source: Path, count: int) -> list[tuple[Image, tuple[int, int, int, int]]]:
    width, height, rgba = decode_png_rgba(source)
    atlas = from_rgba(width, height, rgba)
    result = []
    for index in range(count):
        left, right = index * width // count, (index + 1) * width // count
        cell = Image(right - left, height)
        for y in range(height):
            for x in range(cell.width):
                cell.set(x, y, atlas.get(left + x, y))
        try:
            box = visible_bbox(cell.width, cell.height, b''.join(bytes(p) for p in cell.px))
        except ValueError as error:
            raise ValueError(f'{source}: falta el cuadro {index}') from error
        result.append((cell, box))
    return result


def project_source_walk(source: Path) -> list[Image]:
    """Registered art used only for explicitly permitted equipment masks."""
    result = []
    for index, (cell, (sx0, sy0, sx1, sy1)) in enumerate(source_cells(source, 8)):
        original = original_walk_frame(index)
        tx0, ty0, tx1, ty1 = bounds(original)
        frame = Image(FRAME, FRAME)
        scale = (ty1 - ty0) / (sy1 - sy0)
        # Keep the rear/body registration while allowing a shield or hem to
        # extend in front. The native 72px canvas remains the hard limit.
        projected_width = min(62, max(tx1 - tx0, int(round((sx1 - sx0) * scale))))
        for y in range(ty0, ty1):
            sy = min(sy1 - 1, sy0 + int((y - ty0 + .5) / scale))
            for x in range(tx0, min(FRAME - 1, tx0 + projected_width)):
                sx = min(sx1 - 1, sx0 + int((x - tx0 + .5) * (sx1 - sx0) / projected_width))
                color = cell.get(sx, sy)
                if color[3] >= ALPHA_MIN:
                    frame.set(x, y, palette_color(*color[:3]))
        result.append(frame)
    return result


def equipment_region(identifier: str, x: int, y: int) -> bool:
    if identifier in ('riot', 'elite'):
        return False
    # Include the source head through the face. The source's gray face panel
    # is replaced by remove_face_equipment after registration.
    head = 12 <= x <= 53 and y <= 32
    shield = identifier == 'riot_shield' and 34 <= x <= 65 and 24 <= y <= 63
    hem = (identifier == 'priest' or identifier in ('civil_female_2', 'civil_female_5')) and \
        13 <= x <= 48 and 43 <= y <= 64
    return head or shield or hem


def equipped_walk(identifier: str, source: Path) -> Image:
    result = ([from_rgba(FRAME, FRAME, b''.join(bytes(p) for p in original_walk_frame(i).px))
               for i in range(8)] if identifier == 'riot_shield'
              else sheet_frames(compose_walk_uniform(source)))
    for index, projected in enumerate(project_source_walk(source)):
        original = original_walk_frame(index)
        for y in range(FRAME):
            for x in range(FRAME):
                old = original.get(x, y)
                if not equipment_region(identifier, x, y) or on_face(original, x, y) or \
                        old[:3] in SKIN_RGB or old[:3] == EYE_RGB:
                    continue
                # Crown/back-head may lose the obsolete helmet silhouette;
                # front shield/hem only add actual opaque equipment.
                new = projected.get(x, y)
                if new[3]:
                    result[index].set(x, y, new)
        if identifier == 'priest':
            # Register the source's light collar just under the protected
            # face rather than dropping it with the old respirator mask.
            neck = face_box(original)[3] + 1
            placed = set()
            for y in range(25, 36):
                for x in range(24, 36):
                    color = projected.get(x, y)
                    target_y = max(y, neck)
                    if color[3] and color[0] >= 180 and color[1] >= 160 and color[2] >= 110:
                        for target_x in (x, x - 1, x - 2):
                            old = original.get(target_x, target_y)
                            if target_y <= 37 and old[3] and old[:3] not in SKIN_RGB and \
                                    old[:3] != (0x25, 0x20, 0x18) and not on_face(original, target_x, target_y) and \
                                    (target_x, target_y) not in placed and len(placed) < 3:
                                result[index].set(target_x, target_y, color)
                                placed.add((target_x, target_y))
                                break
    return sheet_from_frames(result)


def remove_face_equipment(identifier: str, sheet: Image, action: str,
                          templates: list[Image] | None = None) -> Image:
    """Replace inherited riot face equipment with a rounded visible face.

    The approved riot has a mask, but generated families must expose a face.
    Recoloring the whole rectangular mask made every variant look cropped, so
    the face is rebuilt as a small pixel-art oval while preserving eyes, alpha
    and animation registration.
    """
    if identifier == 'riot':
        return sheet_from_frames(sheet_frames(sheet))
    skin = sorted(SKIN_RGB, key=lambda color: sum(color))
    frames = sheet_frames(sheet)
    for index, frame in enumerate(frames):
        original = templates[index] if templates else original_frame(action, index)
        x0, y0, x1, y1 = face_box(original)
        center = (x0 + x1 - 1) / 2
        half_width = (x1 - x0) / 2
        for y in range(max(0, y0), min(FRAME, y1)):
            vertical = (y - y0) / max(1, y1 - y0 - 1)
            roundness = 0.52 + 0.48 * math.sin(math.pi * vertical)
            left = center - half_width * roundness
            right = center + half_width * roundness
            for x in range(max(0, x0), min(FRAME, x1)):
                old = original.get(x, y)
                current = frame.get(x, y)
                if not current[3]:
                    continue
                if current[:3] == EYE_RGB:
                    continue
                if left <= x <= right:
                    shade = 0 if vertical < .22 or x < center - half_width * .45 else \
                        2 if vertical > .72 else 1
                else:
                    shade = 0
                frame.set(x, y, (*skin[shade], 255))
        for y in range(FRAME):
            for x in range(FRAME):
                if original.get(x, y)[:3] == EYE_RGB and frame.get(x, y)[3]:
                    frame.set(x, y, (*EYE_RGB, 255))
    return sheet_from_frames(frames)


def dropped_shield(original: Image, output: Image, reference: Image) -> None:
    """Lay the same source shield beside the prone torso instead of clipping
    its upright projection below the native canvas when the body falls."""
    left, top, right, bottom = bounds(original)
    ox = left + (right - left) // 4
    oy = max(1, top - 4)
    for y in range(10):
        for x in range(34):
            target_x, target_y = ox + x, oy + y
            old = original.get(target_x, target_y)
            if on_face(original, target_x, target_y) or old[:3] in SKIN_RGB or old[:3] == EYE_RGB:
                continue
            color = reference.get(35 + y * 30 // 10, 63 - x * 37 // 34)
            if color[3] and color[:3] not in SKIN_RGB:
                output.set(target_x, target_y, color)


def transfer_pose(identifier: str, walk: Image, action: str,
                  templates: list[Image] | None = None) -> Image:
    references = sheet_frames(walk)
    samples = []
    for index in range(8):
        old = original_walk_frame(index)
        mapping = BodyMap(old)
        for y in range(FRAME):
            for x in range(FRAME):
                clerical_collar = identifier == 'priest' and 24 <= x <= 36 and 28 <= y <= 37 and \
                    references[index].get(x, y)[0] >= 180 and references[index].get(x, y)[1] >= 160 and \
                    references[index].get(x, y)[2] >= 110 and old.get(x, y)[:3] not in SKIN_RGB and \
                    not on_face(old, x, y)
                if garment_pixel(old, x, y) or clerical_collar:
                    u, v = mapping.uv(x, y)
                    samples.append((u, v, old.get(x, y)[:3], references[index].get(x, y)))
    grouped = {}
    for sample in samples:
        grouped.setdefault(sample[2], []).append(sample)
    frames = []
    for index in range(ACTIONS[action]):
        old = templates[index] if templates else original_frame(action, index)
        mapping = BodyMap(old)
        out = from_rgba(FRAME, FRAME, b''.join(bytes(p) for p in old.px))
        for y in range(FRAME):
            for x in range(FRAME):
                if identifier == 'riot_shield' or protected_pixel(old, x, y, mapping):
                    continue
                u, v = mapping.uv(x, y)
                candidates = grouped.get(old.get(x, y)[:3], samples)
                nearest = min(candidates, key=lambda p: 2 * (p[0] - u) ** 2 + 4 * (p[1] - v) ** 2)
                if nearest[3]:
                    out.set(x, y, nearest[3])
        if identifier not in ('soldier', 'riot', 'elite'):
            reference = references[index % 8]
            old_reference = original_walk_frame(index % 8)
            source_map = BodyMap(old_reference)
            for y in range(FRAME):
                for x in range(FRAME):
                    u, v = mapping.uv(x, y)
                    if identifier == 'riot_shield' and abs(mapping.vx) > .75:
                        u = 1.0 - u
                    sx, sy = source_map.xy(u, v)
                    if not equipment_region(identifier, sx, sy):
                        continue
                    old_color = old.get(x, y)
                    if on_face(old, x, y) or old_color[:3] in SKIN_RGB or old_color[:3] == EYE_RGB:
                        continue
                    if .17 < v < .31 and u > .45:
                        continue
                    color = reference.get(sx, sy)
                    if color[3]:
                        out.set(x, y, color)
        if identifier == 'riot_shield' and action == 'death' and abs(mapping.vx) > .75:
            dropped_shield(old, out, references[0])
        frames.append(out)
    return sheet_from_frames(frames)


def native_motion(frame: Image, *, dx: int = 0, breath: int = 0, stride: int = 0) -> Image:
    out = Image(FRAME, FRAME)
    for y in range(FRAME):
        upper = max(0.0, min(1.0, (55 - y) / 24.0))
        shift_y = int(round(breath * upper))
        shift_x = int(round(dx * upper))
        for x in range(FRAME):
            leg = int(round(stride * max(0.0, min(1.0, (y - 44) / 18.0))))
            if x < 28:
                leg = -leg
            out.set(x, y, frame.get(x - shift_x - leg, y - shift_y))
    return out


def airborne(frame: Image, lift: int) -> Image:
    out = Image(FRAME, FRAME)
    for y in range(FRAME):
        for x in range(FRAME):
            out.set(x, y, frame.get(x, y + lift))
    return out


def running_from_walk(walk: Image) -> Image:
    walking = sheet_frames(walk)
    return sheet_from_frames([
        airborne(native_motion(walking[(i + 2) % 8], dx=2, stride=2),
                 (0, 1, 2, 0, 0, 1, 2, 0)[i]) for i in range(8)
    ])


def derived_actions(base: dict[str, Image], *, dog: bool = False) -> dict[str, Image]:
    walking, hurt = sheet_frames(base['walk']), sheet_frames(base['hurt'])
    base['idle'] = sheet_from_frames([
        native_motion(walking[0]), native_motion(walking[0], breath=-1),
        native_motion(walking[1], dx=1, breath=-1), native_motion(walking[1], dx=1),
    ])
    if 'run' not in base:
        base['run'] = running_from_walk(base['walk'])
    base['caught'] = sheet_from_frames([
        native_motion(hurt[0], dx=-1), native_motion(hurt[1], dx=1),
        native_motion(hurt[2], dx=-1), native_motion(hurt[1], dx=-1, breath=-1),
    ])
    return base


def normalize_atlas(source: Path, count: int, target_height: int, *, max_width: int = 70,
                    original_palette: bool = False, skin_priority: bool = False) -> Image:
    cells = source_cells(source, count)
    tallest = max(box[3] - box[1] for cell, box in cells)
    scale = target_height / tallest
    widest = max((box[2] - box[0]) * scale for cell, box in cells)
    scale_x = scale * min(1.0, max_width / widest)
    frames = []
    body_palette = {color for frame in range(8) for color in original_walk_frame(frame).px if color[3]}
    for cell, (left, top, right, bottom) in cells:
        width = max(1, int(round((right - left) * scale_x)))
        height = max(1, int(round((bottom - top) * scale)))
        if width > 70:
            raise ValueError(f'{source}: native figure exceeds 70px ({width}); fix the approved source')
        out = Image(FRAME, FRAME)
        ox = max(1, min(FRAME - width - 1, int(round(27.5 - width * .45))))
        oy = 67 - height
        for y in range(height):
            for x in range(width):
                color = cell.get(min(right - 1, left + int((x + .5) / scale_x)),
                                 min(bottom - 1, top + int((y + .5) / scale)))
                if color[3] >= ALPHA_MIN:
                    if original_palette:
                        native = min(body_palette, key=lambda c: sum((c[k] - color[k]) ** 2 for k in range(3)))
                    elif skin_priority and color[1] > color[0] * 1.01 and color[1] > color[2] * 1.18:
                        native = (*min(SKIN_RGB, key=lambda c: sum((c[k] - color[k]) ** 2 for k in range(3))), 255)
                    else:
                        native = min(PALETTE, key=lambda c: sum((c[k] - color[k]) ** 2 for k in range(3)))
                    out.set(ox + x, oy + y, native)
        frames.append(out)
    return sheet_from_frames(frames)


def family_palette(sheet: Image, identifier: str) -> tuple[tuple[int, int, int, int], ...]:
    """A character's source determines its colors; game ramps cap density.

    Reserve small identity accents so a collar or brass key is not discarded
    merely because it occupies fewer pixels than a coat.
    """
    counts = Counter(pixel for pixel in sheet.px if pixel[3])
    reserved = {(0x25, 0x20, 0x18, 255), (0x2c, 0x2c, 0x2c, 255)}
    reserved.update((*rgb, 255) for rgb in SKIN_RGB if (*rgb, 255) in counts)
    if identifier in ('sheriff', 'jailer'):
        reserved.update(color for color in counts if color[0] > 180 and color[1] > 140 and color[2] < color[1] * .85)
    if identifier in ('priest', 'butcher', 'firefighter'):
        reserved.update(color for color in counts if color[0] > 210 and color[1] > 170 and color[2] > 120)
    result = sorted(reserved, key=lambda c: (-counts[c], c))[:18]
    for color, _ in counts.most_common():
        if color not in result and len(result) < 18:
            result.append(color)
    return tuple(result)


def reindex(sheet: Image, palette: tuple[tuple[int, int, int, int], ...]) -> Image:
    lookup = {pixel: min(palette, key=lambda c: sum((c[k] - pixel[k]) ** 2 for k in range(3)))
              for pixel in set(sheet.px) if pixel[3]}
    out = Image(sheet.width, sheet.height)
    out.px = [lookup[pixel] if pixel[3] else (0, 0, 0, 0) for pixel in sheet.px]
    return out


# These source-space bands describe garments, not a protected RIOT face.
# A long hem stays one cutout, so a dress/apron cannot become two trousers.
HEAD_BANDS = {
    'sheriff': (25, 35), 'cowboy': (25, 35), 'police': (22, 31),
    'soldier': (23, 31), 'firefighter': (24, 33), 'motorcycle': (24, 33),
    'jailer': (22, 31), 'butcher': (21, 30), 'priest': (21, 30),
}
HEMS = {'priest': 60, 'civil_female_2': 60, 'civil_female_5': 59,
        'butcher': 55, 'jailer': 54, 'cowboy': 51, 'sheriff': 49}


@dataclass
class Cutout:
    image: Image
    pivot: tuple[float, float]


@dataclass
class HeadPose:
    neck_x: float
    neck_y: float
    angle: float
    bounds: tuple[float, float, float, float]


class OwnRig:
    """All paint comes from one approved character, including every edge.

    The head is a rigid piece attached to the torso's neck joint. Hat pixels
    can never be sampled by a whole-body UV map or land on a forearm.
    """
    def __init__(self, identifier: str, image: Image) -> None:
        self.identifier = identifier
        self.image = image
        x0, y0, x1, y1 = bounds(image)
        # The source is already aligned to the shared 27.5px body pivot.
        self.cx = 27.5
        crown, neck_y = HEAD_BANDS.get(identifier, (21, 30))
        self.neck = (self.cx + 4.0, float(neck_y))
        self.hip = (self.cx, 46.0)
        hem = HEMS.get(identifier, 46)
        self.hem = float(min(61, hem))
        images = {name: Image(FRAME, FRAME) for name in ('head', 'torso', 'back_leg', 'front_leg', 'arm')}
        self.head_mask = set()
        # Restrict the arm to the actual hand's height, keeping torso badges
        # and the continuous apron away from this moving forearm cutout.
        skin = [(x, y) for y in range(neck_y + 2, 47) for x in range(36, FRAME)
                if image.get(x, y)[3] and image.get(x, y)[:3] in SKIN_RGB]
        hand_y = sum(y for x, y in skin) / len(skin) if skin else neck_y + 8.0
        for y in range(FRAME):
            for x in range(FRAME):
                pixel = image.get(x, y)
                if not pixel[3]:
                    continue
                head = y < crown or (y <= neck_y + 1 and x >= self.cx - 1)
                if head:
                    name = 'head'
                    self.head_mask.add((x, y))
                elif y >= hem:
                    name = 'back_leg' if x < self.cx else 'front_leg'
                elif identifier != 'riot_shield' and x >= self.cx + 8 and abs(y - hand_y) <= 5 and y < 45:
                    name = 'arm'
                else:
                    name = 'torso'
                images[name].set(x, y, pixel)
        self.parts = {
            'head': Cutout(images['head'], self.neck),
            'torso': Cutout(images['torso'], self.hip),
            'back_leg': Cutout(images['back_leg'], (self.cx - 3, self.hem)),
            'front_leg': Cutout(images['front_leg'], (self.cx + 3, self.hem)),
            'arm': Cutout(images['arm'], (self.cx + 8, hand_y)),
        }


def rotate_point(point: tuple[float, float], pivot: tuple[float, float],
                   target: tuple[float, float], angle: float) -> tuple[float, float]:
    c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    dx, dy = point[0] - pivot[0], point[1] - pivot[1]
    return target[0] + c * dx - s * dy, target[1] + s * dx + c * dy


def blit_cutout(stage: Image, part: Cutout, target: tuple[float, float], angle: float,
                 *, scale_x: float = 1.0) -> None:
    if not any(pixel[3] for pixel in part.image.px):
        return
    c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    ox, oy = target[0] + 28, target[1] + 28
    for y in range(stage.height):
        for x in range(stage.width):
            dx, dy = x - ox, y - oy
            sx = part.pivot[0] + (c * dx + s * dy) / scale_x
            sy = part.pivot[1] - s * dx + c * dy
            pixel = part.image.get(int(round(sx)), int(round(sy)))
            if pixel[3]:
                stage.set(x, y, pixel)


def rig_pose(rig: OwnRig, *, torso_angle: float = 0, head_angle: float = 0,
               arm_angle: float = 0, arm_stretch: float = 1, left_angle: float = 0,
               right_angle: float = 0, hip_dx: float = 0, hip_dy: float = 0,
               lift: int = 0, depth: float = 1) -> tuple[Image, HeadPose]:
    stage = Image(128, 128)
    hip = (rig.hip[0] + hip_dx, rig.hip[1] + hip_dy)
    neck = rotate_point(rig.neck, rig.hip, hip, torso_angle)
    for name, angle in (('back_leg', left_angle), ('front_leg', right_angle)):
        joint = rotate_point(rig.parts[name].pivot, rig.hip, hip, min(torso_angle, 10) if hip_dy < 10 else torso_angle)
        blit_cutout(stage, rig.parts[name], joint, angle)
    blit_cutout(stage, rig.parts['torso'], hip, torso_angle)
    blit_cutout(stage, rig.parts['head'], neck, torso_angle + head_angle)
    arm_joint = rotate_point(rig.parts['arm'].pivot, rig.hip, hip, torso_angle)
    blit_cutout(stage, rig.parts['arm'], arm_joint, torso_angle + arm_angle, scale_x=arm_stretch)
    x0, y0, x1, y1 = bounds(stage)
    width, height = x1 - x0, y1 - y0
    scale_x = min(1.0, 70.0 / width)
    out_height = max(1, int(round(height * depth)))
    out_width = max(1, int(round(width * scale_x)))
    left = max(1, min(FRAME - out_width - 1, x0 - 28))
    top = 67 - lift - out_height
    output = Image(FRAME, FRAME)
    for y in range(out_height):
        for x in range(out_width):
            output.set(left + x, top + y,
                       stage.get(min(x1 - 1, x0 + int(x / scale_x)),
                                 min(y1 - 1, y0 + int(y / depth))))
    corners = [rotate_point(point, rig.neck, neck, torso_angle + head_angle)
               for point in ((0.0, 0.0), (72.0, 0.0), (0.0, rig.neck[1]), (72.0, rig.neck[1]))]
    convert = lambda p: (left + (p[0] + 28 - x0) * scale_x, top + (p[1] + 28 - y0) * depth)
    trace = [convert(point) for point in corners]
    nx, ny = convert(neck)
    return output, HeadPose(nx, ny, torso_angle + head_angle,
                             (min(p[0] for p in trace), min(p[1] for p in trace),
                              max(p[0] for p in trace), max(p[1] for p in trace)))


def own_actions(identifier: str, walk: Image) -> dict[str, Image]:
    """Pose motion without a single inherited helmet, pad or hit particle."""
    walking = sheet_frames(walk)
    rigs = [OwnRig(identifier, image) for image in walking]
    actions = {'walk': walk}
    actions['idle'] = sheet_from_frames([
        rig_pose(rigs[0], torso_angle=angle, hip_dx=dx)[0]
        for angle, dx in ((0, 0), (-1.5, 0), (-2, 1), (1, 1))
    ])
    actions['attack'] = sheet_from_frames([
        rig_pose(rigs[0], torso_angle=body, head_angle=head, arm_angle=arm,
                 arm_stretch=stretch, hip_dx=dx)[0]
        for body, head, arm, stretch, dx in (
            (0, 0, 0, 1, 0), (-5, -4, -60, 1, -1), (8, 1, -10, 1.6, 2),
            (12, 2, 35, 1.4, 2), (5, 0, 12, 1.15, 1), (0, 0, 0, 1, 0))
    ])
    actions['hurt'] = sheet_from_frames([
        rig_pose(rigs[0], torso_angle=body, head_angle=head, arm_angle=arm, hip_dx=dx)[0]
        for body, head, arm, dx in ((-10, -3, 10, -1), (-18, -5, 20, -2), (-6, 0, 0, 0))
    ])
    actions['caught'] = sheet_from_frames([
        rig_pose(rigs[0], torso_angle=body, head_angle=head, arm_angle=arm)[0]
        for body, head, arm in ((-9, 3, -45), (9, -3, -70), (-6, 2, -35), (7, -2, -65))
    ])
    actions['run'] = sheet_from_frames([
        rig_pose(rigs[(i + 2) % 8], torso_angle=body, head_angle=-4,
                 arm_angle=(-25, -35, 25, 35, -25, -35, 25, 15)[i],
                 left_angle=leg, right_angle=-leg, lift=(0, 0, 1, 3, 0, 0, 1, 2)[i])[0]
        for i, (body, leg) in enumerate(zip((13, 18, 24, 20, 14, 18, 24, 20),
                                            (-18, -30, -40, -20, 22, 35, 25, 0)))
    ])
    actions['death'] = sheet_from_frames([
        rig_pose(rigs[0], torso_angle=body, head_angle=head, arm_angle=arm,
                 left_angle=legs, right_angle=legs + spread, hip_dx=dx, hip_dy=dy, depth=depth)[0]
        for body, head, arm, legs, spread, dx, dy, depth in (
            (0, 0, 0, 0, 0, 0, 0, 1), (-12, 0, 15, -2, 3, -1, 0, 1),
            (-30, 3, 25, -12, 20, -2, 3, 1), (-40, 5, 30, -30, 35, -1, 6, 1),
            (25, 0, 40, 35, 10, 2, 12, 1), (55, -3, 10, 70, 8, 4, 16, .9),
            (80, 0, -15, 88, 2, 6, 18, .75), (90, 0, 0, 90, 0, 6, 18, .65))
    ])
    return actions


@lru_cache(maxsize=2)
def approved_run_master(source_dir: Path) -> list[Image]:
    source = source_dir / 'riot_run_source.png'
    if not source.is_file():
        raise ValueError(f'{source}: approved shared running source is missing')
    frames = sheet_frames(normalize_atlas(source, 8, 58, original_palette=True))
    # The approved master has flight poses at 3 and 7. Preserve suspension
    # after floor registration, with four contact phases in the same cycle.
    return [airborne(frame, (0, 0, 1, 3, 0, 0, 1, 2)[i]) for i, frame in enumerate(frames)]


def family_run(identifier: str, walk: Image, source_dir: Path) -> Image:
    if identifier == 'dog':
        frames = sheet_frames(normalize_atlas(source_dir / 'dog_run_source.png', 8, 38, max_width=52))
        return sheet_from_frames([airborne(frame, (0, 0, 1, 3, 0, 0, 1, 2)[i])
                                  for i, frame in enumerate(frames)])
    if identifier == 'skeleton':
        return running_from_walk(walk)
    master = approved_run_master(source_dir)
    if identifier in ('riot', 'elite'):
        return sheet_from_frames(master)
    run = transfer_pose(identifier, walk, 'run', templates=master)
    return remove_face_equipment(identifier, run, 'run', templates=master)


def required_sources(identifier: str, source_dir: Path) -> list[Path]:
    if identifier in ('riot', 'elite'):
        return [source_dir / 'riot_run_source.png']
    if identifier == 'dog':
        return [source_dir / f'dog_{action}_source.png' for action in ('walk', 'run', 'attack', 'death')]
    if identifier == 'skeleton':
        return [source_dir / 'skeleton_walk_clothes_source.png'] + [
            source_dir / f'skeleton_{action}_source.png' for action in ('attack', 'death')]
    return [source_dir / f'{identifier}_walk_clothes_source.png', source_dir / 'riot_run_source.png']


def export_family(identifier: str, *, source_dir: Path | None = None,
                  assets_dir: Path | None = None) -> dict[str, Path]:
    source_dir = source_dir or ROOT / 'docs/templates/zombies'
    assets_dir = assets_dir or ROOT / 'assets'
    missing = [str(path) for path in required_sources(identifier, source_dir) if not path.is_file()]
    if missing:
        raise ValueError('Missing approved source art: ' + ', '.join(missing))
    output_dir = assets_dir / 'sprites/zombies' / identifier
    output_dir.mkdir(parents=True, exist_ok=True)
    if identifier == 'riot':
        base = {action: sheet_from_frames([original_frame(action, i) for i in range(ACTIONS[action])])
                for action in ORIGINAL_HASHES}
    elif identifier == 'elite':
        base = {action: remove_face_equipment(
                    identifier,
                    sheet_from_frames([original_frame(action, i) for i in range(ACTIONS[action])]),
                    action)
                for action in ORIGINAL_HASHES}
    elif identifier in ('dog', 'skeleton'):
        height = 38 if identifier == 'dog' else 58
        walk_source = source_dir / ('dog_walk_source.png' if identifier == 'dog'
                                     else 'skeleton_walk_clothes_source.png')
        width = 52 if identifier == 'dog' else 70
        base = {'walk': normalize_atlas(walk_source, 8, height, max_width=width),
                'attack': normalize_atlas(source_dir / f'{identifier}_attack_source.png', 6, height, max_width=width),
                'death': normalize_atlas(source_dir / f'{identifier}_death_source.png', 8, height, max_width=width)}
        frames = sheet_frames(base['walk'])
        base['hurt'] = sheet_from_frames([native_motion(frames[0], dx=-1),
                                         native_motion(frames[1], dx=-2, breath=1),
                                         native_motion(frames[2], dx=-1)])
        if identifier == 'dog':
            base['run'] = normalize_atlas(source_dir / 'dog_run_source.png', 8, height, max_width=width)
    else:
        source = source_dir / f'{identifier}_walk_clothes_source.png'
        walk = remove_face_equipment(identifier, equipped_walk(identifier, source), 'walk')
        base = {'walk': walk}
        for action in ('attack', 'hurt', 'death'):
            base[action] = remove_face_equipment(identifier, transfer_pose(identifier, walk, action), action)
    base['run'] = family_run(identifier, base['walk'], source_dir)
    derived_actions(base, dog=identifier == 'dog')
    if identifier not in ('riot', 'dog'):
        base['attack'] = add_shared_attack_effect(base['attack'])
    paths = {}
    for action in ACTIONS:
        target = output_dir / f'{action}.png'
        if identifier == 'riot' and action in ORIGINAL_HASHES:
            source = original_path(action)
            if source.resolve() != target.resolve():
                shutil.copyfile(source, target)
        else:
            base[action].save(target)
        paths[action] = target
    return paths


def export_run(identifier: str, source_dir: Path, assets_dir: Path) -> Path:
    walk_path = assets_dir / 'sprites/zombies' / identifier / 'walk.png'
    if not walk_path.is_file():
        raise ValueError(f'{walk_path}: export the complete family before regenerating its run')
    walk = from_rgba(*decode_png_rgba(walk_path))
    target = walk_path.with_name('run.png')
    family_run(identifier, walk, source_dir).save(target)
    return target


def verify_assets(assets_dir: Path | None = None, identifiers: list[str] | None = None) -> dict[str, int]:
    assets_dir = assets_dir or ROOT / 'assets'
    identifiers = identifiers or IDS
    palette = set(PALETTE)
    for action in ORIGINAL_HASHES:
        for index in range(ACTIONS[action]):
            palette.update(original_frame(action, index).px)
    count = 0
    for identifier in identifiers:
        images = {}
        for action, expected in ACTIONS.items():
            path = assets_dir / 'sprites/zombies' / identifier / f'{action}.png'
            if not path.is_file():
                raise ValueError(f'{path}: missing final animation')
            width, height, rgba = decode_png_rgba(path)
            if (width, height) != (FRAME * expected, FRAME):
                raise ValueError(f'{path}: expected {FRAME * expected}x{FRAME}, got {width}x{height}')
            image = from_rgba(width, height, rgba)
            for color in image.px:
                if color[3] not in (0, 255) or (color[3] and color not in palette):
                    raise ValueError(f'{path}: non-native alpha/color {color}')
            frames = sheet_frames(image)
            unique = {b''.join(bytes(pixel) for pixel in frame.px) for frame in frames}
            if len(unique) != expected:
                raise ValueError(f'{path}: repeated animation frame ({len(unique)}/{expected})')
            for frame in frames:
                x0, y0, x1, y1 = bounds(frame)
                if x0 < 0 or x1 > FRAME or y0 < 0 or y1 > FRAME:
                    raise ValueError(f'{path}: frame outside native canvas')
            if identifier == 'riot' and action in ORIGINAL_HASHES and \
                    hashlib.sha256(path.read_bytes()).hexdigest() != ORIGINAL_HASHES[action]:
                raise ValueError(f'{path}: protected original bytes changed')
            images[action] = frames
            count += 1
        walk_height = max(bounds(frame)[3] - bounds(frame)[1] for frame in images['walk'])
        corpse_height = bounds(images['death'][-1])[3] - bounds(images['death'][-1])[1]
        if corpse_height >= walk_height * .60:
            raise ValueError(f'{identifier}: final death frame must be prone, not upright')
        if images['walk'][0].px == images['run'][0].px:
            raise ValueError(f'{identifier}: run is identical to walk')
        feet = [bounds(frame)[3] for frame in images['run']]
        if min(feet) >= max(feet):
            raise ValueError(f'{identifier}: run has no airborne/contact phases')
        if identifier == 'dog' and walk_height > 40:
            raise ValueError('dog: quadruped exceeds its native 38px body contract')
    return {'families': len(identifiers), 'sheets': count}


def review_family(identifier: str, assets_dir: Path, review_dir: Path) -> None:
    """Three useful native comparisons: walk, strike frame, prone corpse."""
    review = Image(144, FRAME * 3)
    for row, (action, index) in enumerate((('walk', 0), ('attack', 2), ('death', 7))):
        width, height, rgba = decode_png_rgba(assets_dir / 'sprites/zombies' / identifier / f'{action}.png')
        actual = sheet_frames(from_rgba(width, height, rgba))[index]
        old = original_frame(action, index)
        for y in range(FRAME):
            for x in range(FRAME):
                review.set(x, row * FRAME + y, old.get(x, y))
                review.set(FRAME + x, row * FRAME + y, actual.get(x, y))
    review.save(review_dir / f'{identifier}_native.png')
    enlarged = Image(review.width * 4, review.height * 4)
    for y in range(enlarged.height):
        for x in range(enlarged.width):
            enlarged.set(x, y, review.get(x // 4, y // 4))
    enlarged.save(review_dir / f'{identifier}_4x.png')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument('--all', action='store_true', help='export every approved family')
    selection.add_argument('--only', nargs='+', choices=IDS, help='export/verify selected families')
    parser.add_argument('--assets-dir', type=Path, default=ROOT / 'assets')
    parser.add_argument('--source-dir', type=Path, default=ROOT / 'docs/templates/zombies')
    parser.add_argument('--verify', action='store_true', help='verify final shipped PNGs; no IA sources required')
    parser.add_argument('--review-dir', type=Path, help='write native/4x walk-strike-corpse comparisons outside assets')
    parser.add_argument('--actions', choices=['run'], help='regenerate running only in existing complete families')
    args = parser.parse_args()
    selected = args.only or IDS
    if not args.verify and not (args.all or args.only):
        parser.error('Choose --all, --only ids, or --verify')
    if not args.verify:
        missing = [str(path) for identifier in selected
                   for path in required_sources(identifier, args.source_dir) if not path.is_file()]
        if missing:
            parser.error('Missing approved source art: ' + ', '.join(missing))
        for identifier in selected:
            if args.actions == 'run':
                paths = {'run': export_run(identifier, args.source_dir, args.assets_dir)}
            else:
                paths = export_family(identifier, source_dir=args.source_dir, assets_dir=args.assets_dir)
            print(f'{identifier}: {len(paths)} native animation sheets')
    result = verify_assets(args.assets_dir, selected)
    if args.review_dir:
        for identifier in selected:
            review_family(identifier, args.assets_dir, args.review_dir)
    print(f"Verified {result['families']} families / {result['sheets']} PNGs; original bytes preserved.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
