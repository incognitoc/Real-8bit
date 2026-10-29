"""台北六景橫向捲軸關卡畫面（16:9）。

場景層 192x108（地標原尺寸）→ 放大 2 倍到 384x216 → 疊角色（參考圖原像素格）與 HUD → 放大 5 倍輸出 1920x1080。
"""
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import landmarks as LM
from landmarks import OUT, OUT_SOFT, c, inner_outline

W, H = 192, 108
GY = 96            # 地面頂端（場景座標）
SCALE = 5
HERE = Path(__file__).parent


class Canvas:
    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.img = Image.new('RGBA', (w, h), (0, 0, 0, 0))

    def part(self, shape, shade=None, outline=OUT):
        L = Image.new('RGBA', (self.w, self.h), (0, 0, 0, 0))
        shape(ImageDraw.Draw(L))
        if shade:
            S = Image.new('RGBA', (self.w, self.h), (0, 0, 0, 0))
            shade(ImageDraw.Draw(S), S)
            sa = np.array(S)
            sa[..., 3] = np.minimum(sa[..., 3], np.array(L.getchannel('A')))
            L.alpha_composite(Image.fromarray(sa))
        if outline:
            L = inner_outline(L, outline)
        self.img.alpha_composite(L)

    def raw(self, fn):
        fn(ImageDraw.Draw(self.img))

    def paste(self, im, x, y):
        self.img.paste(im, (x, y), im)


# ------------------------------------------------------------ 背景元件
def sky(cv, colors, top=0, bottom=GY):
    d = ImageDraw.Draw(cv.img)
    n = len(colors)
    band = (bottom - top) / n
    for i, col in enumerate(colors):
        y0, y1 = int(top + i * band), int(top + (i + 1) * band)
        d.rectangle([0, y0, cv.w, y1], fill=c(col))
        if i + 1 < n:   # 交界兩列棋盤格抖色
            for x in range(0, cv.w, 2):
                d.point((x + (0 if True else 1), y1 - 1), fill=c(colors[i + 1]))
                d.point((x + 1, y1 + 0), fill=c(col))


def clouds(cv, items):
    for (x, y, s) in items:
        def shape(d, x=x, y=y, s=s):
            d.ellipse([x, y, x + 10 * s, y + 5 * s], fill=c('#ffffff'))
            d.ellipse([x + 3 * s, y - 3 * s, x + 9 * s, y + 3 * s], fill=c('#ffffff'))
            d.ellipse([x + 7 * s, y - 1 * s, x + 14 * s, y + 5 * s], fill=c('#ffffff'))
            d.rectangle([x + 2 * s, y + 3 * s, x + 12 * s, y + 5 * s], fill=c('#ffffff'))

        def sh(d, _, x=x, y=y, s=s):
            d.rectangle([x, y + 4 * s, x + 14 * s, y + 6 * s], fill=c('#dfe8f2'))
        cv.part(shape, sh, outline=OUT_SOFT)


def mountains(cv, base, height, col, seed, outline=None, step=6, shade=None):
    rnd = random.Random(seed)
    pts, y = [(0, base)], base - height // 2
    for x in range(0, cv.w + step, step):
        y = max(base - height, min(base - 2, y + rnd.randint(-4, 4)))
        pts.append((x, y))
    pts.append((cv.w, base))

    def sh(d, _):
        if shade:
            for i in range(1, len(pts) - 2):
                (x0, y0), (x1, y1) = pts[i], pts[i + 1]
                if y1 > y0:
                    d.polygon([(x0, y0), (x1, y1), (x1, base), (x0 + 2, base)], fill=c(shade))
    cv.part(lambda d: d.polygon(pts + [(cv.w, GY + 2), (0, GY + 2)], fill=c(col)), sh, outline=outline)


def skyline(cv, base, col, seed, lit=None, hmin=10, hmax=40, wmin=6, wmax=14):
    rnd = random.Random(seed)
    d = ImageDraw.Draw(cv.img)
    x = -2
    while x < cv.w:
        w, h = rnd.randint(wmin, wmax), rnd.randint(hmin, hmax)
        d.rectangle([x, base - h, x + w - 1, base], fill=c(col))
        if rnd.random() < .25:
            d.rectangle([x + w // 2, base - h - 4, x + w // 2, base - h], fill=c(col))
        if lit:
            for yy in range(base - h + 2, base, 3):
                for xx in range(x + 1, x + w - 1, 2):
                    if rnd.random() < .22:
                        d.point((xx, yy), fill=c(lit))
        x += w + rnd.randint(0, 2)


def building(cv, x, w, h, body, dark, light, win, seed=0, win_lit=None, lit_p=.35,
             arcade=True, glass=False, signs=(), tank=False, grille=False):
    rnd = random.Random(seed)
    top = GY - h

    def shape(d):
        d.rectangle([x, top, x + w - 1, GY - 1], fill=c(body))
        if tank:
            d.rectangle([x + 3, top - 5, x + 8, top], fill=c('#d9dde0'))

    def sh(d, _):
        if glass:
            for xx in range(x + 2, x + w - 1, 3):
                d.line([xx, top, xx, GY - 1], fill=c(light))
            for yy in range(top + 3, GY - 6, 4):
                d.line([x, yy, x + w, yy], fill=c(dark))
                for xx in range(x + 1, x + w - 1, 3):
                    if win_lit and rnd.random() < lit_p:
                        d.point((xx + 1, yy - 1), fill=c(win_lit))
        else:
            d.line([x + 1, top, x + 1, GY - 1], fill=c(light))
            for yy in range(top + 4, GY - 9, 5):
                for xx in range(x + 3, x + w - 4, 5):
                    col = win_lit if (win_lit and rnd.random() < lit_p) else win
                    d.rectangle([xx, yy, xx + 2, yy + 2], fill=c(col))
                    if grille:
                        d.line([xx, yy + 1, xx + 2, yy + 1], fill=c(dark))
                        d.point((xx + 1, yy), fill=c(dark))
        d.rectangle([x + w - 3, top, x + w - 1, GY - 1], fill=c(dark))
        d.line([x, top + 1, x + w, top + 1], fill=c(dark))
        if tank:
            d.line([x + 4, top - 4, x + 4, top], fill=c('#ffffff'))
        if arcade:  # 騎樓
            d.rectangle([x + 1, GY - 8, x + w - 2, GY - 1], fill=c('#3b3334'))
            d.rectangle([x + 2, GY - 6, x + w - 3, GY - 1], fill=c('#ffd98a'))
            for xx in range(x + 1, x + w - 1, 7):
                d.rectangle([xx, GY - 8, xx + 1, GY - 1], fill=c(body))
    cv.part(shape, sh)
    for (sx, sy, sh_, col) in signs:   # 直式招牌
        cv.part(lambda d, sx=sx, sy=sy, sh_=sh_, col=col: d.rectangle([x + sx, top + sy, x + sx + 4, top + sy + sh_], fill=c(col)),
                lambda d, _, sx=sx, sy=sy, sh_=sh_: [d.point((x + sx + 2, yy), fill=c('#ffffff')) for yy in range(top + sy + 2, top + sy + sh_ - 1, 2)])


def tree(cv, x, size=1, col=('#4f9a45', '#86cc6a', '#2d6a2e')):
    r = 6 * size
    cy = GY - 8 - r

    cv.part(lambda d: d.rectangle([x - 1, cy, x + 1, GY - 1], fill=c('#7a4a2a')))

    def shape(d):
        d.ellipse([x - r, cy - r, x + r, cy + r], fill=c(col[0]))
        d.ellipse([x - r - 3, cy - 2, x - 1, cy + r - 1], fill=c(col[0]))
        d.ellipse([x + 1, cy - 2, x + r + 3, cy + r - 1], fill=c(col[0]))

    def sh(d, _):
        d.ellipse([x - r + 1, cy - r + 1, x + 1, cy], fill=c(col[1]))
        d.rectangle([x - r - 3, cy + r - 3, x + r + 3, cy + r], fill=c(col[2]))
        d.ellipse([x + 2, cy + 1, x + r + 3, cy + r], fill=c(col[2]))
    cv.part(shape, sh)


def lamp(cv, x, lit=False):
    cv.part(lambda d: (d.rectangle([x, GY - 22, x + 1, GY - 1], fill=c('#4a5563')),
                       d.rectangle([x, GY - 22, x + 5, GY - 21], fill=c('#4a5563'))))
    cv.part(lambda d: d.rectangle([x + 3, GY - 21, x + 6, GY - 19], fill=c('#fff3b0' if lit else '#dfe6ea')))


def scooter(cv, x, col='#e04848'):
    def shape(d):
        d.polygon([(x, GY - 7), (x + 3, GY - 9), (x + 10, GY - 9), (x + 13, GY - 5), (x + 2, GY - 4)], fill=c(col))
        d.rectangle([x + 11, GY - 14, x + 12, GY - 6], fill=c('#4a5563'))
        d.rectangle([x + 9, GY - 15, x + 14, GY - 14], fill=c('#4a5563'))
        d.rectangle([x + 2, GY - 11, x + 8, GY - 9], fill=c('#2b2b33'))
    cv.part(shape, lambda d, _: d.line([x + 3, GY - 8, x + 10, GY - 8], fill=c('#ffffff')))
    for wx in (x + 2, x + 11):
        cv.part(lambda d, wx=wx: d.ellipse([wx - 2, GY - 5, wx + 2, GY - 1], fill=c('#2b2b33')),
                lambda d, _, wx=wx: d.point((wx, GY - 3), fill=c('#c9ced6')))


def silvergrass(cv, xs, seed=1):
    rnd = random.Random(seed)
    d = ImageDraw.Draw(cv.img)
    for x in xs:
        for k in range(5):
            h = rnd.randint(7, 13)
            xx = x + k * 2 - 4
            lean = rnd.choice([-1, 1])
            d.line([xx, GY - 1, xx + lean, GY - h], fill=c('#7e9b5a'))
            d.rectangle([xx + lean - 1, GY - h - 3, xx + lean + 1, GY - h], fill=c('#efe6cf'))
            d.point((xx + lean, GY - h - 4), fill=c('#fff8e6'))


def signpost(cv, x, col='#7a4a2a', board='#f3e3b8'):
    cv.part(lambda d: d.rectangle([x + 4, GY - 16, x + 6, GY - 1], fill=c(col)))
    cv.part(lambda d: d.polygon([(x - 2, GY - 22), (x + 10, GY - 22), (x + 13, GY - 19), (x + 10, GY - 16), (x - 2, GY - 16)], fill=c(board)),
            lambda d, _: d.line([x, GY - 19, x + 8, GY - 19], fill=c('#7a4a2a')))


# ------------------------------------------------------------ 地面
def ground(cv, style):
    d = ImageDraw.Draw(cv.img)
    if style == 'city':
        d.rectangle([0, GY, W, H], fill=c('#b5583f'))
        d.rectangle([0, GY, W, GY + 2], fill=c('#d6d3cb'))
        d.line([0, GY + 3, W, GY + 3], fill=OUT)
        for row, y in enumerate(range(GY + 4, H, 4)):
            d.line([0, y + 3, W, y + 3], fill=c('#7a3528'))
            for x in range(-(row % 2) * 4, W, 8):
                d.line([x, y, x, y + 3], fill=c('#7a3528'))
                d.line([x + 1, y, x + 6, y], fill=c('#cf7356'))
    elif style == 'park':
        d.rectangle([0, GY, W, H], fill=c('#9a6a3e'))
        d.rectangle([0, GY, W, GY + 3], fill=c('#5fae4a'))
        for x in range(0, W, 3):
            d.point((x, GY - 1 + (x % 2)), fill=c('#5fae4a'))
            d.point((x + 1, GY + 3), fill=c('#3d7f36'))
        rnd = random.Random(2)
        for _ in range(40):
            x, y = rnd.randrange(W), rnd.randrange(GY + 6, H)
            d.rectangle([x, y, x + 1, y], fill=c('#c9935c'))
            d.point((x, y + 1), fill=c('#6e4a2a'))
    elif style == 'plaza':
        d.rectangle([0, GY, W, H], fill=c('#d8cdb8'))
        d.line([0, GY, W, GY], fill=OUT)
        d.line([0, GY + 1, W, GY + 1], fill=c('#f1e9d8'))
        for y in range(GY + 4, H, 4):
            d.line([0, y, W, y], fill=c('#b9ab90'))
        for x in range(0, W, 12):
            d.line([x, GY + 2, x - 4, H], fill=c('#b9ab90'))
    elif style == 'stone':
        d.rectangle([0, GY, W, H], fill=c('#8f8e88'))
        d.line([0, GY, W, GY], fill=OUT)
        d.line([0, GY + 1, W, GY + 1], fill=c('#c8c6bd'))
        rnd = random.Random(4)
        for row, y in enumerate(range(GY + 3, H, 5)):
            x = -rnd.randint(0, 6)
            while x < W:
                w = rnd.randint(6, 11)
                d.rectangle([x, y, x + w - 1, y + 4], outline=c('#5f5e59'))
                d.line([x + 1, y + 1, x + w - 2, y + 1], fill=c('#b3b1a8'))
                x += w
    elif style == 'boardwalk':
        # 小油坑步道橋：底下是草坡，橋面木板與欄杆
        d.rectangle([0, GY, W, H], fill=c('#4f8f43'))
        rnd = random.Random(9)
        for _ in range(120):
            x, y = rnd.randrange(W), rnd.randrange(GY, H)
            d.point((x, y), fill=c('#3d7f36') if rnd.random() < .6 else c('#7cc062'))
        for x in range(4, W, 22):
            d.rectangle([x, GY + 3, x + 2, H], fill=c('#5b3a22'))
            d.line([x, GY + 3, x, H], fill=c('#8a5a34'))
        d.rectangle([0, GY - 1, W, GY + 3], fill=c('#a8743f'))
        d.line([0, GY - 1, W, GY - 1], fill=OUT)
        d.line([0, GY, W, GY], fill=c('#d49a5c'))
        d.line([0, GY + 3, W, GY + 3], fill=OUT)
        for x in range(0, W, 5):
            d.line([x, GY + 1, x, GY + 2], fill=c('#6e4526'))


def railing(cv, y_top=GY - 12):
    def shape(d):
        d.rectangle([0, y_top, W, y_top + 2], fill=c('#a8743f'))
        d.rectangle([0, y_top + 6, W, y_top + 7], fill=c('#a8743f'))
        for x in range(2, W, 14):
            d.rectangle([x, y_top, x + 2, GY - 1], fill=c('#8a5a34'))
    cv.part(shape, lambda d, _: d.line([0, y_top + 1, W, y_top + 1], fill=c('#d49a5c')))


# ------------------------------------------------------------ 收集物（在 384 尺度畫，比較細）
def coin(d, x, y):
    d.ellipse([x, y, x + 6, y + 8], fill=c('#ffd34d'), outline=OUT)
    d.line([x + 3, y + 2, x + 3, y + 6], fill=c('#c98a12'))
    d.point((x + 2, y + 2), fill=c('#fff3b0'))


def note(d, x, y):
    d.rectangle([x + 5, y, x + 6, y + 8], fill=OUT)
    d.rectangle([x + 5, y, x + 9, y + 1], fill=OUT)
    d.ellipse([x, y + 6, x + 6, y + 11], fill=c('#ff6fa8'), outline=OUT)


def bricks(d, x, y, n, col=('#c8643f', '#e88a63', '#7a3528')):
    for i in range(n):
        bx = x + i * 16
        d.rectangle([bx, y, bx + 15, y + 15], fill=c(col[0]), outline=OUT)
        d.line([bx + 1, y + 1, bx + 14, y + 1], fill=c(col[1]))
        d.line([bx + 1, y + 7, bx + 14, y + 7], fill=c(col[2]))
        d.line([bx + 7, y + 1, bx + 7, y + 7], fill=c(col[2]))
        d.line([bx + 3, y + 8, bx + 3, y + 14], fill=c(col[2]))
        d.line([bx + 11, y + 8, bx + 11, y + 14], fill=c(col[2]))


# ------------------------------------------------------------ HUD
FONT_PATH = next(p for p in ['/System/Library/Fonts/PingFang.ttc', '/System/Library/Fonts/Hiragino Sans GB.ttc',
                             '/System/Library/Fonts/STHeiti Medium.ttc'] if Path(p).exists())
HEART = ['.11.11.', '1111111', '1111111', '.11111.', '..111..', '...1...']


def text(d, xy, s, size, fill=(255, 255, 255, 255), anchor='la'):
    f = ImageFont.truetype(FONT_PATH, size, index=0)
    x, y = xy
    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (2, 2), (-2, -2), (2, -2), (-2, 2)]:
        d.text((x + dx, y + dy), s, font=f, fill=OUT, anchor=anchor)
    d.text((x, y), s, font=f, fill=fill, anchor=anchor)


def hud(img, player, stage, title, coins, time):
    """HUD 畫在 960x540 圖層（像素為場景的 1/5），字才清楚；再放大 2 倍疊上去。"""
    L = Image.new('RGBA', (960, 540), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    d.fontmode = '1'
    d.rectangle([0, 0, 960, 74], fill=(18, 22, 52, 150))
    d.line([0, 75, 960, 75], fill=(18, 22, 52, 200), width=3)
    text(d, (24, 10), player, 26)
    for i in range(3):
        for yy, row in enumerate(HEART):
            for xx, ch in enumerate(row):
                if ch == '1':
                    d.rectangle([24 + i * 26 + xx * 3, 46 + yy * 3, 26 + i * 26 + xx * 3, 48 + yy * 3], fill=c('#ff4f6d'))
        d.rectangle([27 + i * 26, 49, 29 + i * 26, 51], fill=c('#ffd0d8'))
    text(d, (480, 8), f'STAGE {stage}', 24, anchor='ma')
    text(d, (480, 38), title, 26, fill=c('#ffe27a'), anchor='ma')
    d.ellipse([744, 14, 762, 38], fill=c('#ffd34d'), outline=OUT, width=3)
    d.rectangle([751, 20, 754, 32], fill=c('#c98a12'))
    text(d, (772, 10), f'×{coins:02d}', 26)
    text(d, (936, 10), 'TIME', 24, anchor='ra')
    text(d, (936, 38), f'{time}', 26, anchor='ra')
    img.alpha_composite(L.resize((1920, 1080), Image.NEAREST))


# ------------------------------------------------------------ 六關
def landmark(cv, fn, x, y=GY - 94):
    cv.paste(fn(), x, y)


def stage_101(cv):
    sky(cv, ['#2b2f7a', '#463c94', '#6c48a0', '#a3549e', '#d8648a', '#f38a6c', '#f8b36a'])
    mountains(cv, GY - 6, 18, '#5a4a8a', seed=11)
    skyline(cv, GY, '#3f3a78', 12, lit='#f6c66a', hmin=12, hmax=44)
    building(cv, 2, 22, 70, '#3b5b8a', '#26406a', '#6b8fc0', '#24385c', seed=1, win_lit='#ffd977', glass=True, arcade=False)
    building(cv, 26, 18, 52, '#5b6d8f', '#3d4c68', '#8da0c0', '#2a3550', seed=2, win_lit='#ffd977', arcade=True)
    building(cv, 150, 20, 64, '#2f6f86', '#1f4c5e', '#69b0c8', '#1d3c4a', seed=3, win_lit='#ffe39a', glass=True, arcade=False)
    building(cv, 172, 20, 48, '#6a5a8a', '#4a3e66', '#9a8bc0', '#2f2848', seed=4, win_lit='#ffd977', arcade=True,
             signs=[(3, 6, 18, '#e8475a'), (11, 10, 14, '#2fb3a3')])
    landmark(cv, LM.taipei101, 70)
    for x in (52, 140):
        lamp(cv, x, lit=True)
    tree(cv, 62, 1, ('#3f7f62', '#6fb58f', '#24503d'))
    tree(cv, 146, 1, ('#3f7f62', '#6fb58f', '#24503d'))
    ground(cv, 'city')


def stage_hotel(cv):
    sky(cv, ['#4f9fe0', '#6cb4ec', '#8fc8f2', '#b4dcf7', '#d6ecfa'])
    clouds(cv, [(12, 14, 1), (130, 10, 1), (160, 26, 1)])
    mountains(cv, GY - 10, 26, '#86b0a4', seed=21)
    mountains(cv, GY, 22, '#4f9a55', seed=22, outline=OUT, step=10, shade='#3d7f44')
    for x in (10, 26, 40, 174):
        tree(cv, x, 1 if x % 3 else 2, ('#3f8f46', '#6cc163', '#25602c'))
    landmark(cv, LM.grand_hotel, 70)
    lamp(cv, 58)
    lamp(cv, 166)
    signpost(cv, 182, board='#d23b2e')
    ground(cv, 'park')


def stage_tpac(cv):
    sky(cv, ['#9cc0d8', '#b2cfe1', '#c6dce8', '#d9e7ef', '#e8f0f4'])
    mountains(cv, GY - 8, 22, '#9eb3c2', seed=31)
    skyline(cv, GY, '#b3c1cc', 32, hmin=8, hmax=26)
    building(cv, 0, 16, 46, '#e8d7b8', '#b8a07a', '#fff1d6', '#7f8b96', seed=5, grille=True,
             signs=[(4, 6, 16, '#e8475a')])
    building(cv, 17, 14, 38, '#d98c6a', '#a8603f', '#f2b294', '#6f7d88', seed=6,
             signs=[(4, 4, 14, '#f2c230')])
    # 捷運高架與劍潭站
    cv.part(lambda d: d.rectangle([140, 56, W, 62], fill=c('#c9c7c0')),
            lambda d, _: (d.line([140, 57, W, 57], fill=c('#ecebe6')), d.line([140, 61, W, 61], fill=c('#8e8c86'))))
    for x in (148, 176):
        cv.part(lambda d, x=x: d.rectangle([x, 62, x + 5, GY - 1], fill=c('#b7b5ad')),
                lambda d, _, x=x: d.line([x + 4, 62, x + 4, GY - 1], fill=c('#8e8c86')))
    cv.part(lambda d: d.rectangle([144, 44, W, 55], fill=c('#f4f4f2')),
            lambda d, _: (d.rectangle([144, 48, W, 49], fill=c('#e2403a')),
                          [d.rectangle([x, 45, x + 4, 47], fill=c('#6f9fc0')) for x in range(147, W, 8)]))
    building(cv, 182, 12, 30, '#e0b46a', '#b0843a', '#f7d79a', '#6f7d88', seed=7, arcade=True)
    landmark(cv, LM.tpac, 52)
    tree(cv, 44, 1)
    lamp(cv, 160)
    scooter(cv, 162, '#3f7fd0')
    ground(cv, 'city')


def stage_music(cv):
    sky(cv, ['#2f7fd9', '#4b95e3', '#6dade9', '#94c4f0', '#bcdaf6'])
    clouds(cv, [(8, 20, 1), (60, 8, 1), (150, 16, 1)])
    skyline(cv, GY, '#a9bccb', 41, hmin=18, hmax=52, wmin=10, wmax=18)
    building(cv, 2, 20, 60, '#dfe5ea', '#a9b4bd', '#ffffff', '#7fa6c4', seed=8, glass=True, arcade=False)
    building(cv, 168, 22, 70, '#7fa6c4', '#56809f', '#b5d2e6', '#3e6582', seed=9, glass=True, arcade=False)
    landmark(cv, LM.music_center, 72)
    for x in (32, 160):
        tree(cv, x, 1)
    lamp(cv, 46)
    ground(cv, 'plaza')


def stage_xianjiyan(cv):
    sky(cv, ['#5daee0', '#79bde6', '#9acdec', '#bfe0f2'])
    clouds(cv, [(120, 12, 1)])
    mountains(cv, GY, 54, '#3f8a45', seed=51, outline=OUT, step=12, shade='#2d6a33')
    rnd = random.Random(52)
    d = ImageDraw.Draw(cv.img)
    for _ in range(160):
        x, y = rnd.randrange(W), rnd.randrange(44, GY)
        if cv.img.getpixel((x, y))[:3] == c('#3f8a45')[:3]:
            d.point((x, y), fill=c('#6cc163'))
    building(cv, 0, 20, 44, '#e6dcc6', '#b6a98c', '#fff6e2', '#6f7d88', seed=10, grille=True, tank=True,
             signs=[(13, 6, 14, '#2fb3a3')])
    building(cv, 21, 18, 36, '#c9d6c7', '#97a894', '#eef5ec', '#6f7d88', seed=11, grille=True, tank=True)
    building(cv, 168, 24, 40, '#e9c9a8', '#b8946e', '#fff0de', '#6f7d88', seed=12, grille=True, tank=True,
             signs=[(4, 6, 16, '#e8475a')])
    landmark(cv, LM.xianjiyan, 76)
    scooter(cv, 172, '#f2c230')
    lamp(cv, 44)
    ground(cv, 'stone')


def stage_xiaoyoukeng(cv):
    sky(cv, ['#aebdc7', '#c1ced5', '#d3dde2', '#e3eaed', '#eef2f4'])
    mountains(cv, GY - 14, 34, '#9fb3a8', seed=61)
    mountains(cv, GY - 4, 22, '#7fa08a', seed=62, step=10)
    clouds(cv, [(10, 30, 1), (140, 18, 1)])
    landmark(cv, LM.xiaoyoukeng, 84, GY - 90)
    silvergrass(cv, [8, 22, 36, 52, 66, 182])
    signpost(cv, 34)
    ground(cv, 'boardwalk')
    railing(cv)


STAGES = [
    ('1-1', '台北 101', 'susan', 'SUSAN', stage_101, 'coin', 30, (88, 128), (40, 104, 2)),
    ('1-2', '圓山飯店', 'jimmy', 'JIMMY', stage_hotel, 'coin', 70, (14, 104), (12, 124, 2)),
    ('1-3', '臺北表演藝術中心', 'davidd', 'DAVIDD', stage_tpac, 'coin', 40, (96, 150), None),
    ('1-4', '臺北流行音樂中心', 'raphael', 'RAPHAEL', stage_music, 'note', 46, (100, 92), None),
    ('1-5', '仙跡岩登山入口', 'freda', 'FREDA', stage_xianjiyan, 'coin', 54, (176, 150), (8, 116, 2)),
    ('1-6', '小油坑橋', 'anderson', 'ANDERSON', stage_xiaoyoukeng, 'coin', 46, (100, 120), (24, 112, 3)),
]


def render(idx, chars_dir):
    stage, title, char, player, fn, pickup, cx, (kx, ky), brk = STAGES[idx]
    cv = Canvas()
    fn(cv)
    big = cv.img.resize((W * 2, H * 2), Image.NEAREST)
    d = ImageDraw.Draw(big)

    # 收集物：角色前方一道弧線
    for k in range(5):
        x = kx + k * 14
        y = ky - int(16 * np.sin(np.pi * k / 4))
        (note if pickup == 'note' else coin)(d, x, y)
    if brk:
        bricks(d, *brk)

    # 角色（腳踩地面，朝右）
    sp = Image.open(Path(chars_dir) / f'{char}.png')
    fy = GY * 2 + (0 if fn is not stage_xiaoyoukeng else -2)
    shadow = Image.new('RGBA', big.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse([cx + 2, fy - 3, cx + sp.width - 2, fy + 2], fill=(20, 24, 50, 90))
    big.alpha_composite(shadow)
    big.alpha_composite(sp, (cx, fy - sp.height))

    final = big.resize((W * 2 * SCALE, H * 2 * SCALE), Image.NEAREST)
    hud(final, player, stage, title, coins=idx * 7 + 3, time=300 - idx * 17)
    return final


def main(outdir, chars_dir):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    frames = []
    for i, st in enumerate(STAGES):
        f = render(i, chars_dir)
        f.convert('RGB').save(out / f'stage_{st[0]}_{st[2]}.png')
        frames.append(f)
    # 縮圖總覽 3x2
    tw, th = 640, 360
    sheet = Image.new('RGB', (tw * 3 + 16, th * 2 + 12), (255, 255, 255))
    for i, f in enumerate(frames):
        sheet.paste(f.resize((tw, th), Image.NEAREST).convert('RGB'), (4 + (i % 3) * (tw + 4), 4 + (i // 3) * (th + 4)))
    sheet.save(out / 'stages_overview.png')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
