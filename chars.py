"""從參考角色表擷取朝右（RIGHT 列）的角色，去背並縮回像素格。"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

COLS = [(88, 287), (290, 483), (486, 673), (676, 865), (868, 1063), (1066, 1251)]
NAMES = ['davidd', 'anderson', 'freda', 'susan', 'raphael', 'jimmy']
ROWS = {'front': (57, 381), 'left': (385, 696), 'back': (700, 981), 'right': (984, 1251)}
MAGENTA = (255, 0, 255)


def cut(sheet, name, row='right', height=56):
    x0, x1 = COLS[NAMES.index(name)]
    y0, y1 = ROWS[row]
    im = sheet.crop((x0 + 3, y0 + 3, x1 - 3, y1 - 3)).convert('RGB')
    w, h = im.size
    for p in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]:
        if im.getpixel(p) != MAGENTA:
            ImageDraw.floodfill(im, p, MAGENTA, thresh=60)
    a = np.array(im)
    alpha = ~np.all(a == MAGENTA, axis=-1)
    rgba = np.dstack([a, (alpha * 255).astype(np.uint8)])
    img = Image.fromarray(rgba, 'RGBA')
    img = img.crop(img.getbbox())
    # 縮回像素格：先縮再把半透明邊緣二值化，顏色量化成有限色盤
    tw = round(img.width * height / img.height)
    small = img.resize((tw, height), Image.BOX)
    sa = np.array(small)
    keep = sa[..., 3] > 110
    rgb = Image.fromarray(sa[..., :3]).quantize(colors=20, method=Image.Quantize.MEDIANCUT).convert('RGB')
    out = np.dstack([np.array(rgb), (keep * 255).astype(np.uint8)])
    return Image.fromarray(out, 'RGBA')


if __name__ == '__main__':
    sheet = Image.open(sys.argv[1])
    out = Path(sys.argv[2]); out.mkdir(exist_ok=True)
    row = []
    for n in NAMES:
        s = cut(sheet, n)
        s.save(out / f'{n}.png')
        row.append(s)
    W = sum(s.width + 4 for s in row)
    prev = Image.new('RGBA', (W, 60), (200, 220, 240, 255))
    x = 0
    for s in row:
        prev.alpha_composite(s, (x, 2)); x += s.width + 4
    prev.resize((W * 8, 480), Image.NEAREST).save(out / '_preview.png')
