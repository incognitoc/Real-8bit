"""台北六景 8-bit 像素圖：96x96 邏輯像素，深藍外框、平塗加明暗，放大 6 倍輸出。"""
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

N = 96
SCALE = 6
OUT = (28, 34, 66, 255)
OUT_SOFT = (96, 108, 140, 255)


def c(h, a=255):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def inner_outline(layer, color=OUT):
    a = np.array(layer)
    m = a[..., 3] > 0
    p = np.pad(m, 1)
    interior = p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
    a[m & ~interior] = color
    return Image.fromarray(a)


class Sprite:
    def __init__(self):
        self.img = Image.new('RGBA', (N, N), (0, 0, 0, 0))

    def part(self, shape, shade=None, outline=OUT):
        L = Image.new('RGBA', (N, N), (0, 0, 0, 0))
        shape(ImageDraw.Draw(L))
        if shade:
            S = Image.new('RGBA', (N, N), (0, 0, 0, 0))
            shade(ImageDraw.Draw(S), S)
            sa = np.array(S)
            sa[..., 3] = np.minimum(sa[..., 3], np.array(L.getchannel('A')))
            L.alpha_composite(Image.fromarray(sa))
        if outline:
            L = inner_outline(L, outline)
        self.img.alpha_composite(L)

    def raw(self, fn):
        fn(ImageDraw.Draw(self.img))


def px(d, x, y, col):
    d.point((x, y), fill=col)


# ---------------------------------------------------------------- 1. 台北 101
def taipei101():
    s = Sprite()
    g, gl, gd, gw = c('#4f9e86'), c('#94d6b8'), c('#2f6b5b'), c('#c8f0d8')
    cx = 48

    # 尖塔
    s.part(lambda d: d.rectangle([cx - 1, 3, cx, 12], fill=c('#b9c2cc')),
           lambda d, _: d.line([cx - 1, 3, cx - 1, 12], fill=c('#eef2f6')))
    s.part(lambda d: d.rectangle([cx - 1, 0, cx, 3], fill=c('#ffd34d')))

    # 塔冠
    def crown(d):
        d.polygon([(cx - 5, 18), (cx - 6, 11), (cx + 5, 11), (cx + 4, 18)], fill=g)

    def crown_sh(d, _):
        d.rectangle([cx - 6, 11, cx - 3, 18], fill=gl)
        d.rectangle([cx + 2, 11, cx + 5, 18], fill=gd)
        d.line([cx - 6, 14, cx + 5, 14], fill=c('#f05a7e'))
    s.part(crown, crown_sh)

    # 八節斗形塔身（由上往下畫，下層蓋住上層的底邊）
    seg_h = 6
    for i in range(8):
        yt = 18 + i * seg_h
        yb = yt + seg_h

        def seg(d, yt=yt, yb=yb):
            d.polygon([(cx - 8, yb), (cx - 11, yt), (cx + 10, yt), (cx + 7, yb)], fill=g)

        def seg_sh(d, _, yt=yt, yb=yb):
            d.polygon([(cx - 8, yb), (cx - 11, yt), (cx - 5, yt), (cx - 4, yb)], fill=gl)
            d.polygon([(cx + 3, yb), (cx + 4, yt), (cx + 10, yt), (cx + 7, yb)], fill=gd)
            d.line([cx - 10, yt + 1, cx + 9, yt + 1], fill=c('#f05a7e'))
            for x in range(cx - 7, cx + 7, 2):
                px(d, x, yt + 3, gw)
        s.part(seg, seg_sh)

    # 底座（往上收窄）
    def base(d):
        d.polygon([(cx - 14, 93), (cx - 9, 66), (cx + 8, 66), (cx + 13, 93)], fill=g)

    def base_sh(d, _):
        d.polygon([(cx - 14, 93), (cx - 9, 66), (cx - 4, 66), (cx - 6, 93)], fill=gl)
        d.polygon([(cx + 5, 93), (cx + 3, 66), (cx + 8, 66), (cx + 13, 93)], fill=gd)
        for y in range(72, 92, 3):
            for x in range(cx - 13, cx + 13, 2):
                px(d, x, y, gw)
    s.part(base, base_sh)

    # 如意圓飾
    for ox in (-5, 4):
        s.part(lambda d, ox=ox: d.ellipse([cx + ox - 2, 66, cx + ox + 2, 70], fill=c('#ffd34d')),
               lambda d, _, ox=ox: px(d, cx + ox, 68, c('#f05a7e')))
    return s.img


# ---------------------------------------------------------------- 2. 圓山飯店
def grand_hotel():
    s = Sprite()
    rf, rfl, rfd = c('#f2a93b'), c('#ffd677'), c('#c47a1c')
    red, redd, redl = c('#d23b2e'), c('#8f2219'), c('#ef6a4f')
    cream = c('#f7e6c4')
    tree, treel, treed = c('#3f8f46'), c('#6cc163'), c('#25602c')

    # 地面
    s.part(lambda d: d.rectangle([2, 88, 93, 93], fill=c('#cfd3d6')),
           lambda d, _: d.line([2, 89, 93, 89], fill=c('#eef0f1')))

    # 主體
    def body(d):
        d.rectangle([16, 36, 79, 82], fill=red)

    def body_sh(d, _):
        d.rectangle([16, 36, 79, 39], fill=redd)
        for y in range(41, 78, 4):
            d.line([16, y + 3, 79, y + 3], fill=cream)
            for x in range(19, 77, 5):
                d.rectangle([x, y, x + 2, y + 1], fill=c('#f6d9a8'))
                px(d, x, y, c('#ffefcc'))
        for x in (17, 18):
            d.line([x, 36, x, 82], fill=redl)
        d.rectangle([76, 36, 79, 82], fill=redd)
    s.part(body, body_sh)

    # 重簷屋頂（上層）
    def roof_top(d):
        d.polygon([(34, 10), (61, 10), (73, 20), (79, 15), (77, 23), (18, 23), (16, 15), (22, 20)], fill=rf)

    def roof_sh(top, bottom):
        def f(d, _):
            for x in range(0, N, 3):
                d.line([x, top, x, bottom], fill=rfd)
            d.line([0, top + 1, N, top + 1], fill=rfl)
            d.line([0, bottom - 1, N, bottom - 1], fill=rfd)
        return f
    s.part(lambda d: d.rectangle([26, 22, 69, 28], fill=red),
           lambda d, _: [d.line([x, 23, x, 28], fill=c('#2a9d8f')) for x in range(28, 69, 4)])
    s.part(roof_top, roof_sh(10, 23))
    s.part(lambda d: d.rectangle([33, 7, 62, 10], fill=rfd),
           lambda d, _: d.line([33, 8, 62, 8], fill=rf))

    # 下層屋簷
    def roof_low(d):
        d.polygon([(23, 28), (72, 28), (84, 35), (91, 30), (89, 39), (6, 39), (4, 30), (11, 35)], fill=rf)
    s.part(roof_low, roof_sh(28, 39))

    # 入口雨庇與柱子
    s.part(lambda d: d.rectangle([34, 76, 61, 87], fill=c('#3a1b17')),
           lambda d, _: [d.rectangle([x, 76, x + 2, 87], fill=red) for x in (34, 42, 51, 59)])
    s.part(lambda d: d.polygon([(32, 71), (63, 71), (67, 76), (28, 76)], fill=rf),
           lambda d, _: d.line([28, 72, 67, 72], fill=rfl))

    # 前方圓形灌木
    s.part(lambda d: d.ellipse([30, 82, 65, 94], fill=tree),
           lambda d, _: (d.ellipse([33, 83, 50, 88], fill=treel), d.ellipse([46, 89, 66, 96], fill=treed)))

    # 兩側松樹
    for x0 in (2, 80):
        def pine(d, x0=x0):
            for k, (yt, hw) in enumerate([(46, 4), (54, 6), (63, 7), (72, 8)]):
                d.polygon([(x0 + 7, yt), (x0 + 7 - hw, yt + 12), (x0 + 7 + hw, yt + 12)], fill=tree)
            d.rectangle([x0 + 6, 84, x0 + 8, 90], fill=c('#6b4226'))

        def pine_sh(d, _, x0=x0):
            d.polygon([(x0 + 7, 46), (x0, 86), (x0 + 6, 86)], fill=treel)
            d.polygon([(x0 + 8, 46), (x0 + 15, 86), (x0 + 10, 86)], fill=treed)
        s.part(pine, pine_sh)
    return s.img


# ---------------------------------------------------------------- 3. 台北表演藝術中心
def tpac():
    s = Sprite()
    rnd = random.Random(3)
    sv, svl, svd, svdd = c('#c4cad3'), c('#eef1f5'), c('#8d95a2'), c('#666e7c')
    gl, gll, gld = c('#5f7f92'), c('#a9c3cf'), c('#40596a')

    # 廣場
    s.part(lambda d: d.rectangle([2, 86, 93, 93], fill=c('#d5d1c8')),
           lambda d, _: d.line([2, 87, 93, 87], fill=c('#efece6')))

    # 量體側面與正面
    s.part(lambda d: d.polygon([(78, 22), (88, 16), (88, 70), (78, 74)], fill=gld),
           lambda d, _: [d.line([78, y + 4, 88, y - 2], fill=gl) for y in range(22, 74, 4)])
    s.part(lambda d: d.polygon([(42, 22), (52, 16), (88, 16), (78, 22)], fill=c('#7b98a8')))

    def box(d):
        d.rectangle([42, 22, 78, 74], fill=gl)

    def box_sh(d, _):
        for y in range(24, 74, 3):
            d.line([42, y, 78, y], fill=gll)
        d.rectangle([42, 22, 45, 74], fill=c('#7fa1b2'))
        for x in (56, 67):
            d.line([x, 22, x, 74], fill=gld)
    s.part(box, box_sh)

    # 架高的玻璃大廳與柱
    s.part(lambda d: d.rectangle([46, 74, 84, 86], fill=c('#2f3a44')),
           lambda d, _: (d.rectangle([52, 77, 80, 86], fill=c('#ffd98a')),
                         [d.line([x, 77, x, 86], fill=c('#d9a94a')) for x in range(55, 80, 4)]))
    for x in (48, 82):
        s.part(lambda d, x=x: d.rectangle([x - 1, 74, x + 1, 86], fill=c('#b7b9bd')))

    # 支撐球體的基座
    s.part(lambda d: d.polygon([(26, 86), (30, 70), (40, 70), (44, 86)], fill=c('#9aa0a8')),
           lambda d, _: d.polygon([(38, 70), (40, 70), (44, 86), (40, 86)], fill=svdd))

    # 球體
    cx, cy, r = 32, 46, 26

    def sphere(d):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=sv)

    def sphere_sh(d, _):
        d.ellipse([cx - r + 8, cy - r + 10, cx + r + 10, cy + r + 10], fill=svd)
        d.ellipse([cx - r + 2, cy - r + 2, cx + r - 6, cy + r - 6], fill=sv)
        d.ellipse([cx - 18, cy - 20, cx - 4, cy - 8], fill=svl)
        d.ellipse([cx - 15, cy - 18, cx - 10, cy - 13], fill=c('#ffffff'))
        for rx in (9, 18):
            d.ellipse([cx - rx, cy - r, cx + rx, cy + r], outline=svdd)
        d.ellipse([cx - r, cy - 7, cx + r, cy + 7], outline=svdd)
        d.line([cx - r, cy - 16, cx + r, cy - 16], fill=svd)
        d.line([cx - r, cy + 16, cx + r, cy + 16], fill=svdd)
    s.part(sphere, sphere_sh)
    return s.img


# ---------------------------------------------------------------- 4. 台北流行音樂中心
def music_center():
    s = Sprite()
    gold, goldl, goldd, golddd = c('#cfae6e'), c('#f0d9a6'), c('#9c7c45'), c('#6f5630')
    con, conl, cond = c('#c9c7c0'), c('#e7e5df'), c('#8e8c86')

    # 地坪
    s.part(lambda d: d.rectangle([2, 86, 93, 93], fill=c('#d8cdb8')),
           lambda d, _: [d.line([x, 88, x - 3, 93], fill=c('#c2b59c')) for x in range(6, 96, 8)])

    # 底層深色玻璃與柱
    s.part(lambda d: d.rectangle([10, 66, 86, 86], fill=c('#36424c')),
           lambda d, _: (d.rectangle([10, 66, 86, 70], fill=c('#1f272e')),
                         [d.line([x, 71, x, 86], fill=c('#5d7180')) for x in range(14, 86, 5)]))
    for x in (12, 30, 64, 82):
        s.part(lambda d, x=x: d.polygon([(x - 3, 86), (x - 2, 68), (x + 2, 68), (x + 3, 86)], fill=con),
               lambda d, _, x=x: d.line([x + 1, 68, x + 2, 86], fill=cond))

    # 清水模平台
    s.part(lambda d: d.rectangle([4, 60, 91, 67], fill=con),
           lambda d, _: (d.line([4, 61, 91, 61], fill=conl), d.line([4, 66, 91, 66], fill=cond)))

    # 結晶狀金屬屋頂：上緣頂點與下緣錨點交錯成三角面
    top = [(5, 60), (6, 50), (14, 40), (22, 44), (31, 28), (40, 36), (48, 22),
           (57, 34), (66, 26), (75, 40), (84, 36), (91, 48), (91, 60)]
    bottom = [(5, 60), (10, 60), (18, 60), (26, 60), (34, 60), (42, 60), (50, 60),
              (58, 60), (66, 60), (74, 60), (82, 60), (88, 60), (91, 60)]
    shades = [goldl, gold, goldd, gold, goldl, goldd]

    def roof(d):
        d.polygon(top + [(91, 60), (5, 60)], fill=gold)

    def roof_sh(d, _):
        k = 0
        for i in range(len(top) - 1):
            d.polygon([top[i], top[i + 1], bottom[i]], fill=shades[k % 6]); k += 1
            d.polygon([top[i + 1], bottom[i + 1], bottom[i]], fill=shades[k % 6]); k += 1
        for i in range(len(top) - 1):
            d.line([top[i + 1], bottom[i]], fill=golddd)
        # 金屬板直向肋條
        for x in range(6, 92, 3):
            d.line([x, 52, x, 59], fill=goldd)
    s.part(roof, roof_sh)
    return s.img


# ---------------------------------------------------------------- 5. 仙跡岩登山入口
def xianjiyan():
    s = Sprite()
    rnd = random.Random(5)
    rf, rfl, rfd = c('#f0a23a'), c('#ffd27a'), c('#b8681c')
    red, redl, redd = c('#d8352a'), c('#f26b55'), c('#8e1f17')
    yel, yeld = c('#f2c230'), c('#c18f12')
    leaf, leafl, leafd = c('#4f9a45'), c('#86cc6a'), c('#2d6a2e')

    # 背景樹叢
    def bush(d):
        for (x, y, r) in [(10, 30, 14), (26, 20, 13), (46, 16, 13), (66, 18, 14), (84, 28, 13),
                          (90, 48, 10), (6, 50, 10), (48, 34, 18)]:
            d.ellipse([x - r, y - r, x + r, y + r], fill=leaf)

    def bush_sh(d, _):
        for _i in range(260):
            x, y = rnd.randrange(N), rnd.randrange(N)
            d.point((x, y), fill=leafd if rnd.random() < .55 else leafl)
    s.part(bush, bush_sh)

    # 石階
    def stairs(d):
        d.polygon([(22, 93), (34, 46), (62, 46), (74, 93)], fill=c('#9a9a94'))

    def stairs_sh(d, _):
        y, step = 48, 2
        while y < 93:
            d.line([0, y, N, y], fill=c('#c9c9c2'))
            d.line([0, y + 1, N, y + 1], fill=c('#6f6f6a'))
            y += step + (1 if y > 70 else 0) + 1
        d.line([44, 90, 52, 50], fill=c('#e6e8ea'))
        d.line([45, 90, 53, 50], fill=c('#8c9096'))
    s.part(stairs, stairs_sh)

    # 紅柱（含對聯）
    for x0 in (18, 72):
        s.part(lambda d, x0=x0: d.rectangle([x0, 36, x0 + 6, 82], fill=red),
               lambda d, _, x0=x0: (d.line([x0 + 1, 36, x0 + 1, 82], fill=redl),
                                    d.line([x0 + 5, 36, x0 + 5, 82], fill=redd),
                                    [d.rectangle([x0 + 3, y, x0 + 3, y + 1], fill=yel) for y in range(42, 78, 4)]))
        s.part(lambda d, x0=x0: d.rectangle([x0 - 3, 80, x0 + 9, 93], fill=yel),
               lambda d, _, x0=x0: (d.ellipse([x0, 83, x0 + 6, 89], fill=yeld),
                                    d.ellipse([x0 + 1, 84, x0 + 5, 88], fill=c('#a8780c')),
                                    d.line([x0 - 3, 81, x0 + 9, 81], fill=c('#ffe27a'))))

    # 彩繪橫樑（龍紋）
    def beam(d):
        d.rectangle([14, 31, 82, 38], fill=red)

    def beam_sh(d, _):
        for x0, col in ((14, c('#2a9d8f')), (76, c('#2a9d8f'))):
            d.rectangle([x0, 31, x0 + 6, 38], fill=col)
            d.line([x0 + 1, 34, x0 + 5, 34], fill=c('#2f5fb5'))
        for x in range(23, 74, 2):
            y = 34 + (1 if (x // 4) % 2 else -1)
            d.point((x, y), fill=yel)
            d.point((x, y + 1), fill=yel)
        d.line([14, 32, 82, 32], fill=redl)
    s.part(beam, beam_sh)

    # 白牆帶、藍色斗栱、匾額
    s.part(lambda d: d.rectangle([16, 25, 80, 31], fill=c('#eceae4')))
    for x0 in (10, 78):
        s.part(lambda d, x0=x0: d.rectangle([x0, 24, x0 + 8, 33], fill=c('#2f5fb5')),
               lambda d, _, x0=x0: (d.rectangle([x0, 24, x0 + 8, 26], fill=c('#2a9d8f')),
                                    d.line([x0 + 1, 27, x0 + 1, 33], fill=c('#6f97e0'))))

    def plaque(d):
        d.rectangle([33, 24, 63, 32], fill=c('#1d1a1a'))

    def plaque_sh(d, _):
        # 三個小金字（仙・跡・巖 的簡化筆畫）
        glyphs = [
            ['1.1.1', '1.111', '1.1.1', '1.111', '1.1.1'],
            ['111.1', '.1.11', '111.1', '.1.11', '1.1.1'],
            ['11111', '1.1.1', '11111', '.1.1.', '1.1.1'],
        ]
        for gi, g in enumerate(glyphs):
            for yy, row in enumerate(g):
                for xx, ch in enumerate(row):
                    if ch == '1':
                        d.point((37 + gi * 8 + xx, 26 + yy), fill=c('#f4c74a'))
    s.part(plaque, plaque_sh)

    # 琉璃瓦屋頂
    def roof(d):
        d.polygon([(22, 10), (74, 10), (84, 17), (93, 11), (91, 21), (86, 25), (10, 25),
                   (5, 21), (3, 11), (12, 17)], fill=rf)

    def roof_sh(d, _):
        for x in range(0, N, 3):
            d.line([x, 10, x, 25], fill=rfd)
            d.line([x + 1, 10, x + 1, 25], fill=rfl)
        for x in range(9, 88, 3):
            d.point((x, 23), fill=c('#fff1c2'))
    s.part(roof, roof_sh)
    s.part(lambda d: d.rectangle([20, 7, 76, 10], fill=rfd),
           lambda d, _: d.line([20, 8, 76, 8], fill=rf))
    for x0 in (16, 75):
        s.part(lambda d, x0=x0: d.polygon([(x0, 10), (x0 + 1, 2), (x0 + 5, 4), (x0 + 3, 7), (x0 + 5, 10)], fill=rf),
               lambda d, _, x0=x0: d.point((x0 + 2, 4), fill=rfl))
    return s.img


# ---------------------------------------------------------------- 6. 小油坑
def xiaoyoukeng():
    s = Sprite()
    rnd = random.Random(7)
    gr, grl, grd = c('#5fae4a'), c('#9ad86f'), c('#3d7f36')
    rk, rkl, rkd = c('#6d6762'), c('#9a948c'), c('#46413e')
    sul = c('#e9d65c')

    # 山坡
    hill = [(0, 93), (0, 50), (10, 40), (22, 30), (34, 38), (44, 52), (52, 54), (62, 40),
            (74, 26), (84, 24), (95, 36), (95, 93)]

    def hill_d(d):
        d.polygon(hill, fill=gr)

    def hill_sh(d, _):
        d.polygon([(0, 93), (0, 60), (14, 48), (20, 93)], fill=grl)
        d.polygon([(80, 93), (88, 40), (95, 46), (95, 93)], fill=grd)
        for _i in range(220):
            x, y = rnd.randrange(N), rnd.randrange(24, N)
            col = grd if rnd.random() < .6 else grl
            d.point((x, y), fill=col)
            d.point((x, y - 1), fill=col)
    s.part(hill_d, hill_sh)

    # 噴氣孔岩壁
    crater = [(30, 44), (40, 54), (52, 58), (60, 48), (68, 38), (74, 46), (72, 66),
              (60, 80), (44, 82), (32, 70), (28, 56)]

    def crater_d(d):
        d.polygon(crater, fill=rk)

    def crater_sh(d, _):
        d.polygon([(30, 44), (40, 54), (52, 58), (48, 70), (34, 66)], fill=rkd)
        for _i in range(140):
            x, y = rnd.randrange(26, 76), rnd.randrange(36, 84)
            d.point((x, y), fill=rkl if rnd.random() < .6 else rkd)
        for (x, y) in [(56, 70), (60, 66), (44, 76), (66, 56), (38, 72)]:
            d.rectangle([x, y, x + 2, y + 1], fill=sul)
            d.point((x + 1, y - 1), fill=c('#fff3a0'))
    s.part(crater_d, crater_sh)

    # 硫磺噴氣（白煙團）
    puffs_main = [(52, 64, 7), (47, 54, 9), (55, 44, 10), (46, 34, 10), (56, 24, 9),
                  (48, 15, 8), (60, 34, 7), (40, 44, 6)]
    puffs_side = [(68, 58, 5), (72, 48, 6), (75, 38, 5)]
    for puffs in (puffs_main, puffs_side):
        def steam(d, puffs=puffs):
            for (x, y, r) in puffs:
                d.ellipse([x - r, y - r, x + r, y + r], fill=c('#ffffff'))

        def steam_sh(d, _, puffs=puffs):
            for (x, y, r) in puffs:
                d.ellipse([x - r + 3, y - r + 3, x + r + 2, y + r + 2], fill=c('#d6dce6'))
            for (x, y, r) in puffs:
                d.ellipse([x - r + 1, y - r + 1, x + r - 3, y + r - 3], fill=c('#ffffff'))
        s.part(steam, steam_sh, outline=OUT_SOFT)
    return s.img


# ---------------------------------------------------------------- 7. 赤峰街（老公寓一樓汽車音響行＋倉庫）
def chifeng():
    s = Sprite()
    tile, tilel, tiled = c('#d9cdb0'), c('#efe6cf'), c('#a8997a')
    brick, brickl, brickd = c('#a8503a'), c('#c86a50'), c('#6e2e20')
    iron, ironl = c('#4a4e5a'), c('#8a90a4')

    # 人行道
    s.part(lambda d: d.rectangle([2, 86, 93, 93], fill=c('#bdb8ad')),
           lambda d, _: [d.line([x, 87, x, 93], fill=c('#a29d92')) for x in range(6, 96, 8)])

    # 左：紅磚倉庫，鐵皮山牆屋頂、大拉門
    s.part(lambda d: d.polygon([(2, 46), (18, 36), (34, 46)], fill=c('#7a8a9a')),
           lambda d, _: [d.line([x, 46, 18, 36], fill=c('#5a6878')) for x in range(4, 34, 4)])

    def wh(d):
        d.rectangle([3, 46, 33, 86], fill=brick)

    def wh_sh(d, _):
        for y in range(48, 86, 3):
            d.line([3, y, 33, y], fill=brickd)
            for x in range(3 + (y // 3 % 2) * 3, 34, 6):
                d.line([x, y + 1, x, y + 2], fill=brickd)
        d.rectangle([3, 50, 33, 53], fill=c('#efe6cf'))                       # 白色字帶
        for x in range(6, 31, 3):
            d.rectangle([x, 51, x + 1, 52], fill=c('#2a2a34'))
        d.rectangle([14, 40, 22, 44], fill=c('#ffd98a'))                      # 山牆小窗
        d.rectangle([7, 58, 29, 86], fill=c('#3f6b52'))                       # 綠色大拉門
        d.line([7, 58, 29, 86], fill=c('#2c4c3a')); d.line([29, 58, 7, 86], fill=c('#2c4c3a'))
        d.line([18, 58, 18, 86], fill=c('#2c4c3a'))
        d.rectangle([4, 47, 5, 85], fill=brickl)
    s.part(wh, wh_sh)

    # 右：四層老公寓，頂樓加蓋與水塔
    s.part(lambda d: d.rectangle([52, 8, 76, 16], fill=c('#7ea6c8')),
           lambda d, _: [d.line([x, 8, x, 16], fill=c('#5a82a6')) for x in range(53, 76, 2)])
    s.part(lambda d: d.ellipse([80, 4, 90, 16], fill=c('#d8dce4')),
           lambda d, _: (d.line([82, 6, 82, 14], fill=c('#ffffff')), d.line([80, 10, 90, 10], fill=c('#9aa0ac'))))

    def apt(d):
        d.rectangle([36, 16, 92, 86], fill=tile)

    def apt_sh(d, _):
        d.rectangle([88, 16, 92, 86], fill=tiled)
        d.line([37, 16, 37, 86], fill=tilel)
        for y in range(18, 66, 2):                                           # 磁磚縫
            d.line([36, y, 88, y], fill=c('#cfc2a3'))
        for fy in (18, 30, 42, 54):                                          # 每層：鐵窗、冷氣、盆栽
            d.line([36, fy + 11, 92, fy + 11], fill=tiled)
            for wx in (40, 64):
                d.rectangle([wx, fy + 2, wx + 18, fy + 9], fill=c('#36424c'))
                d.rectangle([wx + 1, fy + 3, wx + 17, fy + 5], fill=c('#6e8aa0'))
                for bx in range(wx, wx + 19, 3):
                    d.line([bx, fy + 1, bx, fy + 10], fill=iron)
                d.line([wx - 1, fy + 1, wx + 19, fy + 1], fill=ironl)
                d.line([wx - 1, fy + 10, wx + 19, fy + 10], fill=ironl)
            d.rectangle([84, fy + 4, 89, fy + 8], fill=c('#f4f4f2'))           # 冷氣室外機
            d.point((86, fy + 6), fill=c('#9aa0ac'))
            d.rectangle([42, fy + 8, 46, fy + 9], fill=c('#4f9a45'))           # 盆栽
            d.point((44, fy + 7), fill=c('#86cc6a'))
        # 一樓：汽車音響行
        d.rectangle([36, 64, 92, 69], fill=c('#d8352a'))                      # 紅色招牌
        for x in (42, 56, 70):
            d.ellipse([x, 64, x + 5, 69], fill=c('#ffd34d'))                  # 喇叭圖示
            d.point((x + 2, 66), fill=c('#2a2a34'))
        d.rectangle([76, 65, 88, 68], fill=c('#ffffff'))
        d.rectangle([38, 70, 90, 86], fill=c('#1e2028'))                      # 店內
        for y in range(70, 74):
            d.line([38, y, 90, y], fill=c('#9aa0ac') if y % 2 else c('#6e7480'))   # 捲門拉上一半
        for (x, y, r) in [(41, 76, 5), (52, 78, 4), (61, 75, 5), (72, 78, 4), (81, 76, 5)]:
            d.rectangle([x - r, y - r, x + r, y + r + 4], fill=c('#2e3038'))
            d.ellipse([x - r + 1, y - r + 1, x + r - 1, y + r - 1], fill=c('#5a5e6a'))
            d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=c('#c8ccd8'))
        d.rectangle([46, 83, 58, 86], fill=c('#2a2a2a'))                      # 輪胎
        d.line([47, 84, 57, 84], fill=c('#4a4a4a'))
    s.part(apt, apt_sh)

    # 直式招牌
    s.part(lambda d: d.rectangle([33, 26, 37, 62], fill=c('#f2c230')),
           lambda d, _: [d.rectangle([34, y, 36, y + 2], fill=c('#d8352a')) for y in range(28, 61, 5)])
    return s.img


LANDMARKS = [
    ('taipei101', '台北 101', taipei101),
    ('grand_hotel', '圓山飯店', grand_hotel),
    ('tpac', '台北表演藝術中心', tpac),
    ('music_center', '台北流行音樂中心', music_center),
    ('xianjiyan', '仙跡岩登山入口', xianjiyan),
    ('xiaoyoukeng', '小油坑', xiaoyoukeng),
    ('chifeng', '赤峰街', chifeng),
]


def find_font(size):
    for p in ['/System/Library/Fonts/PingFang.ttc', '/System/Library/Fonts/Hiragino Sans GB.ttc',
              '/System/Library/Fonts/STHeiti Medium.ttc']:
        if Path(p).exists():
            return ImageFont.truetype(p, size, index=0)
    return ImageFont.load_default()


def main(outdir):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    sprites = []
    for key, name, fn in LANDMARKS:
        im = fn()
        big = im.resize((N * SCALE, N * SCALE), Image.NEAREST)
        big.save(out / f'{key}.png')
        sprites.append((name, big))

    # 仿參考圖的總表：白底、淡藍格線、上方標名
    cell, head, cols = N * SCALE + 48, 72, 3
    rows = (len(sprites) + cols - 1) // cols
    sheet = Image.new('RGBA', (cell * cols + 2, (cell + head) * rows + 2), (255, 255, 255, 255))
    d = ImageDraw.Draw(sheet)
    font = find_font(34)
    grid = (168, 200, 232, 255)
    for i, (name, big) in enumerate(sprites):
        cx, cy = (i % cols) * cell, (i // cols) * (cell + head)
        d.rectangle([cx, cy, cx + cell, cy + head], outline=grid, width=2)
        d.rectangle([cx, cy + head, cx + cell, cy + head + cell], outline=grid, width=2)
        tw = d.textlength(name, font=font)
        d.text((cx + (cell - tw) / 2, cy + 16), name, font=font, fill=OUT)
        sheet.alpha_composite(big, (cx + 24, cy + head + 24))
    sheet.convert('RGB').save(out / 'taipei_landmarks_sheet.png')


if __name__ == '__main__':
    main(sys.argv[1])
