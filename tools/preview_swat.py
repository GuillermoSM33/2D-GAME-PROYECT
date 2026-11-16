#!/usr/bin/env python3
"""Preview the final painted SWAT assets; optional Pillow authoring utility.

Usage: python3 tools/preview_swat.py [directory_with_BMP_captures]
"""
from pathlib import Path
import sys
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/img'
BG = '#dfdcd4'


def sprite(name, f=0, width=81, character='swat'):
    with Image.open(ROOT / 'assets/sprites/characters' / character / (name + '.png')) as im:
        return im.convert('RGBA').crop((f * width, 0, (f + 1) * width, im.height))


def place(canvas, image, x, baseline, anchor=31.5, ground=68, scale=4):
    large = image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)
    canvas.paste(large, (round(x - anchor * scale), baseline - ground * scale), large)


def gif(frames, name, duration):
    strip = Image.new('RGB', (frames[0].width, frames[0].height * len(frames)))
    for i, image in enumerate(frames):
        strip.paste(image, (0, i * image.height))
    palette = strip.quantize(colors=128, dither=Image.Dither.NONE)
    reduced = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    reduced[0].save(OUT / name, save_all=True, append_images=reduced[1:],
                    duration=duration, loop=0, disposal=2, optimize=False)


def action_frame(column, seconds, shotgun=False):
    if column == 3:
        phase = seconds % 2.4
        if phase < 1.0:
            return min(15, int(phase * 16))
        if phase < 1.35:
            return 15
        if phase < 1.95:
            return max(0, 15 - int((phase - 1.35) / .6 * 16))
        return 0
    count, duration = ((8, .5), (7, .7), (8, 1.2), (16, 1), (31, 2.8))[column]
    if column == 2 and shotgun:
        duration = 1.1
    phase = seconds % (duration + .35)
    return 0 if phase >= duration else min(count - 1, int(phase / duration * count))


def actions_preview(captures=None):
    labels = ('Disparo', 'Culatazo', 'Recarga', 'Linterna', 'Agua')
    sheets = ('shoot', 'melee', 'reload', 'light', 'drink_')
    chosen = (4, 3, 4, 11, 18)
    frames = []
    for tick in range(65):
        canvas = Image.new('RGB', (1560, 530), BG)
        draw = ImageDraw.Draw(canvas)
        for row, (kind, suffix, label) in enumerate((('rifle', '', 'Rifle'), ('shotgun', '_shotgun', 'Escopeta'))):
            draw.text((12, row * 265 + 12), 'Sheriff / referencia de escala', fill='#34312d')
            place(canvas, sprite('walk', tick % 8, 42, 'cowgirl'), 110, row * 265 + 253,
                  anchor=19.5, ground=61, scale=3)
            for col, (title, sheet) in enumerate(zip(labels, sheets)):
                frame = chosen[col] if tick == 64 else action_frame(col, tick * .05, row == 1)
                name = sheet + kind if col == 4 else sheet + suffix
                draw.text(((col + 1) * 260 + 12, row * 265 + 12), label + ' / ' + title, fill='#34312d')
                place(canvas, sprite(name, frame), (col + 1) * 260 + 105, row * 265 + 253, scale=3)
        frames.append(canvas)
    frames[-1].save(OUT / 'swat_acciones.png')
    gif(frames[:-1], 'swat_acciones.gif', 50)
    if captures is None:
        return
    cache = {}
    game_frames = []
    for tick in range(65):
        canvas = Image.new('RGB', (1600, 700), BG)
        draw = ImageDraw.Draw(canvas)
        for row, kind in enumerate(('rifle', 'escopeta')):
            for col, (title, tag) in enumerate(zip(labels, ('tiro', 'culatazo', 'recarga', 'linterna', 'agua'))):
                frame = chosen[col] if tick == 64 else action_frame(col, tick * .05, row == 1)
                name = f'53_swat_{kind}_{tag}_{frame}'
                if name not in cache:
                    with Image.open(captures / (name + '.bmp')) as shot:
                        cache[name] = shot.convert('RGB').crop((420, 345, 580, 500)).resize((320, 310), Image.Resampling.NEAREST)
                canvas.paste(cache[name], (col * 320, row * 350 + 36))
                draw.text((col * 320 + 12, row * 350 + 12), kind + ' / ' + title, fill='#34312d')
        game_frames.append(canvas)
    game_frames[-1].save(OUT / 'swat_acciones_juego.png')
    gif(game_frames[:-1], 'swat_acciones_juego.gif', 50)


def drink_review(captures=None):
    """Every drinking frame, plus the key poses for checking hand continuity."""
    labels = ('Porte', 'Derecha baja el arma', 'Izquierda va a la bolsa',
              'Saca la botella', 'Acerca la tapa', 'Derecha toma la tapa',
              'Retira la tapa', 'Izquierda alza la botella',
              'Derecha vuelve al arma', 'Bebe con la izquierda', 'Sorbo',
              'Baja la botella', 'Vuelve a la bolsa', 'Guarda la botella',
              'Derecha levanta el arma', 'Agarre con ambas manos')
    contact = Image.new('RGB', (1376, 1408), BG)
    draw = ImageDraw.Draw(contact)
    for key, label in enumerate(labels):
        col, row = key % 4, key // 4
        draw.text((col * 344 + 12, row * 352 + 12), f'{key * 2:02d} / {label}', fill='#34312d')
        place(contact, sprite('drink_rifle', key * 2), col * 344 + 150, row * 352 + 326)
    contact.save(OUT / 'swat_agua_secuencia.png')
    native_frames, game_frames = [], []
    for frame in range(31):
        native = Image.new('RGB', (688, 704), BG)
        game = Image.new('RGB', (640, 700), BG)
        for row, facing in enumerate(('derecha', 'izquierda')):
            for col, (kind, name) in enumerate((('rifle', 'Rifle'), ('shotgun', 'Escopeta'))):
                drawing = sprite('drink_' + kind, frame)
                if row:
                    drawing = drawing.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                place(native, drawing, col * 344 + 150, row * 352 + 326,
                      anchor=48.5 if row else 31.5)
                ImageDraw.Draw(native).text((col * 344 + 12, row * 352 + 12),
                                           f'{name} / {facing} / {frame:02d}', fill='#34312d')
                if captures is not None:
                    gun = 'rifle' if kind == 'rifle' else 'escopeta'
                    if row:
                        gun += '_izq'
                    with Image.open(captures / f'53_swat_{gun}_agua_{frame}.bmp') as shot:
                        crop = shot.convert('RGB').crop((420, 345, 580, 500))
                    game.paste(crop.resize((320, 310), Image.Resampling.NEAREST), (col * 320, row * 350 + 36))
                    ImageDraw.Draw(game).text((col * 320 + 12, row * 350 + 12),
                                              f'{name} / {facing} / {frame:02d}', fill='#34312d')
        native_frames.append(native)
        game_frames.append(game)
    gif(native_frames, 'swat_agua.gif', 90)
    if captures is not None:
        gif(game_frames, 'swat_agua_juego.gif', 90)
        game_frames[18].save(OUT / 'swat_agua_juego.png')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    frames = []
    for tick in range(32):
        canvas = Image.new('RGB', (1280, 650), BG)
        draw = ImageDraw.Draw(canvas)
        poses = (('Sheriff / escala', 'cowgirl', 'walk', tick % 8, 42),
                 ('SWAT / porte y caminar', 'swat', 'carry', tick % 8, 81),
                 ('Rifle / disparo', 'swat', 'shoot', tick // 2 % 8, 81),
                 ('Rifle / recarga', 'swat', 'reload', tick // 4, 81),
                 ('SWAT / reposo', 'swat', 'carry', 8, 81),
                 ('Escopeta / caminar', 'swat', 'carry_shotgun', tick % 8, 81),
                 ('Escopeta / disparo', 'swat', 'shoot_shotgun', tick // 2 % 8, 81),
                 ('Escopeta / recarga', 'swat', 'reload_shotgun', tick // 4, 81))
        for i, (label, character, sheet, frame, width) in enumerate(poses):
            col, row = i % 4, i // 4
            draw.text((col * 320 + 12, row * 325 + 12), label, fill='#34312d')
            place(canvas, sprite(sheet, frame, width, character), col * 320 + 120, row * 325 + 303,
                  anchor=19.5 if character == 'cowgirl' else 31.5,
                  ground=61 if character == 'cowgirl' else 68)
        frames.append(canvas)
    frames[6].save(OUT / 'swat_mangas_poses.png')
    gif(frames, 'swat_mangas_animacion.gif', 110)
    # The actual game renders are independent of the source-sheet preview.
    if len(sys.argv) > 1:
        captures = Path(sys.argv[1])
        last = '4_personajes' if (captures / '4_personajes.bmp').is_file() else '53_swat_escopeta'
        names = ('53_swat_rifle', '53_swat_rifle_disparo', '53_swat_escopeta_disparo', last)
        review = Image.new('RGB', (1280, 720), BG)
        for i, name in enumerate(names):
            shot = Image.open(captures / (name + '.bmp')).convert('RGB')
            shot = shot.resize((640, 360), Image.Resampling.NEAREST)
            review.paste(shot, ((i % 2) * 640, (i // 2) * 360))
        review.save(OUT / 'swat_mangas_juego.png')
        detail = Image.new('RGB', (1120, 500), BG)
        draw = ImageDraw.Draw(detail)
        for i, (name, label) in enumerate((('53_swat_rifle', 'Rifle / porte'),
                                          ('53_swat_rifle_disparo', 'Rifle / disparo'),
                                          ('53_swat_escopeta', 'Escopeta / porte'),
                                          ('53_swat_escopeta_disparo', 'Escopeta / disparo'))):
            shot = Image.open(captures / (name + '.bmp')).convert('RGB')
            shot = shot.crop((422, 310, 562, 500)).resize((280, 380), Image.Resampling.NEAREST)
            detail.paste(shot, (i * 280, 50))
            draw.text((i * 280 + 12, 15), label, fill='#34312d')
        detail.save(OUT / 'swat_mangas_detalle.png')
        walk = [Image.open(captures / f'53_swat_rifle_paso_{f}.bmp').convert('RGB')
                .crop((410, 305, 575, 500)).resize((330, 390), Image.Resampling.NEAREST) for f in range(8)]
        gif(walk, 'swat_mangas_caminata_juego.gif', 110)
    actions_preview(Path(sys.argv[1]) if len(sys.argv) > 1 else None)
    drink_review(Path(sys.argv[1]) if len(sys.argv) > 1 else None)
    print('Saved SWAT locomotion and five-action previews in docs/img/')


if __name__ == '__main__':
    main()
