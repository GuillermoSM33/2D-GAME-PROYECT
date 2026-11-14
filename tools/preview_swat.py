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
        names = ('53_swat_rifle', '53_swat_rifle_disparo', '53_swat_escopeta_disparo', '4_personajes')
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
    print('Saved docs/img/swat_mangas_{poses.png,animacion.gif,juego.png}')


if __name__ == '__main__':
    main()
