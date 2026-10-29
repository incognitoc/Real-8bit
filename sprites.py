"""六位團員的手繪 8-bit 角色（程式逐格畫），含樂器。

每個角色 18x32 邏輯像素（不含外框），和地標、場景同一個像素格；放進場景時放大 2 倍。
畫法：各部位用文字像素圖描述（一個字元一格，字元代表「角色」，各人有自己的色盤），
每個部位各自加 1 格深藍外框後依序疊起來，所以頭、身體、手臂、樂器之間都有清楚的分界。

輸出到 characters/<名字>/：
  right_walk1~3、right_jump、left_walk1~3、left_jump、front_play1~2
所有畫格同尺寸（CW x CH），腳底中心在 ANCHOR 記錄的位置。
"""
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from landmarks import OUT, c

CW, CH = 34, 42          # 畫格尺寸
OX, OY = 8, 8            # 角色 18x32 區塊的左上角
FOOT = (OX + 9, OY + 32)  # 腳底中心（朝右、正面皆同；朝左鏡像）

SKIN, SKIN_D = '#f4b878', '#d98e58'


# ------------------------------------------------------------ 基本工具
def grid(txt):
    rows = txt.strip('\n').split('\n')
    return [re.sub('^r[0-9]+ ?', '', r).rstrip() for r in rows]       # 每列前面的 r12 是列號，方便對位


def paint(img, rows, pal, x0=OX, y0=OY, pattern=None):
    """把文字像素圖畫進 img。'.' 不畫、'_' 擦掉；pattern(role, x, y) 可回傳替換色（格紋用）。"""
    a = np.array(img)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == '.':
                continue
            X, Y = x0 + x, y0 + y
            if not (0 <= X < img.width and 0 <= Y < img.height):
                continue
            if ch == '_':
                a[Y, X] = 0
                continue
            col = pattern(ch, x, y) if pattern else None
            col = col or pal.get(ch)
            if col is None:
                raise KeyError(f'色盤缺少 {ch!r}')
            a[Y, X] = c(col) if isinstance(col, str) else col
    return Image.fromarray(a)


def outline(img, col=OUT):
    """外框：在不透明像素外圍（上下左右）補一圈深色。"""
    a = np.array(img)
    m = a[..., 3] > 0
    p = np.pad(m, 1)
    near = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    a[near & ~m] = col
    return Image.fromarray(a)


def blank():
    return Image.new('RGBA', (CW, CH), (0, 0, 0, 0))


def part(rows, pal, pattern=None, x0=OX, y0=OY):
    return outline(paint(blank(), rows, pal, x0, y0, pattern))


def stack(*layers):
    out = blank()
    for L in layers:
        if L is not None:
            out.alpha_composite(L)
    return out


def line_part(segs, x0=OX, y0=OY):
    """手臂之類的粗線段：segs = [(點列, 顏色, 粗細), ...]，畫完一起加外框。"""
    L = blank()
    d = ImageDraw.Draw(L)
    for pts, col, w in segs:
        pts = [(x0 + x, y0 + y) for x, y in pts]
        if len(pts) == 1 or w <= 1:
            d.line(pts if len(pts) > 1 else pts * 2, fill=c(col), width=1)
        else:
            d.line(pts, fill=c(col), width=w)
        for x, y in pts:                                   # 關節補圓，避免粗線轉角缺角
            r = (w - 1) / 2
            d.rectangle([x - math.floor(r), y - math.floor(r), x + math.ceil(r), y + math.ceil(r)], fill=c(col))
    return outline(L)


def dots(img, pts, col, x0=OX, y0=OY):
    d = ImageDraw.Draw(img)
    for x, y in pts:
        d.point((x0 + x, y0 + y), fill=c(col) if isinstance(col, str) else col)
    return img


# ------------------------------------------------------------ 共用版型（18x32 格，r 後面是列號）
HEAD_SIDE = grid('''
r0 ..................
r1 ......SSSSSS......
r2 ....SSSSSSSSSS....
r3 ...SSSSSSSSSSSS...
r4 ..SSSSSSSSSSSSSS..
r5 ..SSSSSSSSSSSSSS..
r6 ..SSSSSSSSSSSSSS..
r7 ..SSSSSSSSSSSSSSS.
r8 ..SSSSSSSSSSSSSSS.
r9 ..SSSSSSSSSSSSSS..
r10 ..SSSSSSSSSSSSSS..
r11 ...SSSSSSSSSSSSS..
r12 ....SSSSSSSSSSSS..
r13 ......ssSSSSSs....
''')
FACE_SIDE = grid('''
r0 ..................
r1 ..................
r2 ..................
r3 ..................
r4 ..................
r5 ..................
r6 ..................
r7 ..................
r8 .......ss....E....
r9 .......ss....E....
r10 ............r.....
r11 ..............MM..
''')
HEAD_FRONT = grid('''
r0 ..................
r1 .....SSSSSSSS.....
r2 ....SSSSSSSSSS....
r3 ...SSSSSSSSSSSS...
r4 ..SSSSSSSSSSSSSS..
r5 ..SSSSSSSSSSSSSS..
r6 ..SSSSSSSSSSSSSS..
r7 ..SSSSSSSSSSSSSS..
r8 .sSSSSSSSSSSSSSSs.
r9 .sSSSSSSSSSSSSSSs.
r10 ..SSSSSSSSSSSSSS..
r11 ..SSSSSSSSSSSSSS..
r12 ...SSSSSSSSSSSS...
r13 .....sSSSSSSs.....
''')
FACE_FRONT = grid('''
r0 ..................
r1 ..................
r2 ..................
r3 ..................
r4 ..................
r5 ..................
r6 ..................
r7 ..................
r8 ......E....E......
r9 ......E....E......
r10 ....r........r....
r11 .......MWWM.......
r12 ........MM........
''')
GLASSES_SIDE = grid('''
r0 ..................
r1 ..................
r2 ..................
r3 ..................
r4 ..................
r5 ..................
r6 ..................
r7 ............GGGG..
r8 ........GGGGG..G..
r9 ............G..G..
r10 ............GGGG..
''')
GLASSES_FRONT = grid('''
r0 ..................
r1 ..................
r2 ..................
r3 ..................
r4 ..................
r5 ..................
r6 ..................
r7 ....GGGG..GGGG....
r8 ...GG..GGGG..GG...
r9 ....G..G..G..G....
r10 ....GGGG..GGGG....
''')

TORSO_SIDE = grid('''
r0
r1
r2
r3
r4
r5
r6
r7
r8
r9
r10
r11
r12
r13
r14 .....AAAAAAABB....
r15 ....AAAAAAAABBA...
r16 ....AAAAAAAABBA...
r17 ....AAAAAAAABBA...
r18 ....AAAAAAAABBA...
r19 ....AAAAAAAAABA...
r20 ....aAAAAAAAAAA...
r21 ....aaAAAAAAAAa...
''')
ARM_SIDE = grid('''
r0
r1
r2
r3
r4
r5
r6
r7
r8
r9
r10
r11
r12
r13
r14
r15 .......aAa........
r16 .......AAA........
r17 .......AAA........
r18 .......AAA........
r19 .......AAA........
r20 .......AAa........
r21 .......SSS........
r22 .......SSs........
''')
TORSO_FRONT = grid('''
r0
r1
r2
r3
r4
r5
r6
r7
r8
r9
r10
r11
r12
r13
r14 ...AAAAaBBaAAAA...
r15 ..AAAAAaBBaAAAAA..
r16 ..AAAAAaBBaAAAAA..
r17 ..AAAAAaBBaAAAAA..
r18 ..AAAAAaBBaAAAAA..
r19 ..AAAAAaBBaAAAAA..
r20 ..aAAAAaBBaAAAAa..
r21 ..aaAAAaBBaAAAaa..
''')

_LEG_TOP = ['' for _ in range(22)]
LEGS = {
    'stand': _LEG_TOP + grid('''
r22 ....PPPPPPPPPPP...
r23 ....PPPPPPPPPPP...
r24 .....LLLLLLLLL....
r25 .....LLLLlLLLL....
r26 .....LLLLlLLLL....
r27 .....LLLLlLLLL....
r28 .....LLLLlLLLL....
r29 .....LLLLlLLLL....
r30 .....KKKKKKKKKK...
r31 .....kkkkkkkkkk...
'''),
    'small': _LEG_TOP + grid('''
r22 ....PPPPPPPPPPP...
r23 ....PPPPPPPPPPP...
r24 ....LLLLLlLLLLL...
r25 ....LLLL.lLLLL....
r26 ....LLLL..LLLL....
r27 ...LLLL...LLLLL...
r28 ...LLLL....LLLL...
r29 ...LLL.....LLLL...
r30 ..KKKKK....KKKKK..
r31 ..kkkk.....kkkkk..
'''),
    'stride': _LEG_TOP + grid('''
r22 ....PPPPPPPPPPP...
r23 ....PPPPPPPPPPP...
r24 ....LLLLLlLLLLL...
r25 ...LLLLL.lLLLLL...
r26 ...LLLL...LLLLL...
r27 ..LLLL.....LLLLL..
r28 ..LLLL.....LLLLL..
r29 .LLLL.......LLLL..
r30 KKKKK.......KKKKK.
r31 kkkk........kkkkk.
'''),
    'jump': _LEG_TOP + grid('''
r22 ....PPPPPPPPPPP...
r23 ....PPPPPPPPPPPP..
r24 ....LLLLLLLLLLLLL.
r25 ....LLLLL..LLLLLL.
r26 ...LLLL.....LLLLL.
r27 ..LLLL......KKKKKK
r28 .LLLL.......kkkkkk
r29 KKKK..............
r30 kkk...............
'''),
    'front': _LEG_TOP + grid('''
r22 ...PPPPPPPPPPPP...
r23 ...PPPPPPPPPPPP...
r24 ....LLLLLLLLLL....
r25 ....LLLLllLLLL....
r26 ....LLLL..LLLL....
r27 ....LLLL..LLLL....
r28 ....LLLL..LLLL....
r29 ....LLLL..LLLL....
r30 ...KKKKK..KKKKK...
r31 ...kkkkk..kkkkk...
'''),
}

SKIRT_SIDE = _LEG_TOP + grid('''
r22 ....QQQQQQQQQQQ...
r23 ....QQQQQQQQQQQ...
r24 ...QQqQQQqQQQQQ...
r25 ...QQqQQQqQQQqQQ..
r26 ..QQqQQQqQQQqQQQ..
''')
SKIRT_FRONT = _LEG_TOP + grid('''
r22 ...QQQQQQQQQQQQ...
r23 ...QQQQQQQQQQQQ...
r24 ..QQqQQqQQqQQqQQ..
r25 .QQqQQqQQqQQqQQQQ.
r26 .QQqQQqQQqQQqQQqQ.
''')
SWEATER_SIDE = grid('''
r0
r1
r2
r3
r4
r5
r6
r7
r8
r9
r10
r11
r12
r13
r14 .....YYYYYYYY.....
r15 ....YyYYYYYYYY....
r16 ...........YYY....
r17 ...........YyY....
r18 ............Y.....
''')
SWEATER_FRONT = grid('''
r0
r1
r2
r3
r4
r5
r6
r7
r8
r9
r10
r11
r12
r13
r14 ...YYYYYYYYYYYY...
r15 ..YYyYYYYYYYYyYY..
r16 ......YYYYYY......
r17 .......YyyY.......
r18 ........YY........
''')


def leg_rows(template, bottoms):
    """把腿部版型的 L/l 依下身款式換成實際角色：長褲全是 P；短褲、裙子下半截露出皮膚與襪子。"""
    out = []
    for y, row in enumerate(template):
        if bottoms == 'pants':
            row = row.replace('L', 'P').replace('l', 'p')
        elif bottoms == 'shorts':
            row = row.replace('L', 'P' if y <= 25 else ('S' if y <= 28 else 'W')).replace('l', 'p' if y <= 25 else 's')
        elif bottoms == 'skirt':
            row = row.replace('L', 'S' if y <= 28 else 'W').replace('l', 's')
        out.append(row)
    return out


# ------------------------------------------------------------ 六位團員：髮型（側面朝右／正面）與色盤
HAIR = {
    'susan': (grid('''
r0 ......hHHHHh......
r1 ....HHHHHHHHHH....
r2 ...HHHHHHHHHHHH...
r3 ..HHHHHHHHHHHHHH..
r4 ..HHHHHHHHHHHHHHH.
r5 ..HHHHHHHHHHHHHH..
r6 .HHHHHHHHHHHHH....
r7 .HHHhHHHHHH.......
r8 .HHHHHHHHH........
r9 .HHHHhHHHH........
r10 .HHHHHHHHH........
r11 .HHHHHHHH.........
r12 .hHHHHHHh.........
'''), grid('''
r0 .....hHHHHHHh.....
r1 ...HHHHHHHHHHHH...
r2 ..HHHHHHHHHHHHHH..
r3 .HHHHHHHHHHHHHHHH.
r4 .HHHHHHHHHHHHHHHH.
r5 .HHHHHHHHHHHHHHHH.
r6 .HHH.HHH.HHH.HHHH.
r7 .HHH..........HHH.
r8 .HH............HH.
r9 .HH............HH.
r10 .HH............HH.
r11 .HHH..........HHH.
r12 .HHHh........hHHH.
r13 ..hH..........Hh..
''')),
    'jimmy': (grid('''
r0 .....hHHhHHh......
r1 ...HHHHHHHHHHHH...
r2 ..HHHHHhHHHHHHHH..
r3 .HHhHHHHHHHHHHHHH.
r4 .HHHHHHHHHHHHHHH..
r5 .HHHhHHHHHHHHHh...
r6 .HHHHHHHHH........
r7 .HHhHHHH..........
r8 ..HHHHH...........
r9 ..HHHH............
r10 ..HHH.............
r11 ...H..............
'''), grid('''
r0 ....hHHhHHhHHh....
r1 ...HHHHHHHHHHHH...
r2 ..HHHHHhHHHHHHHH..
r3 .HHHHHHHHHHHHHHHH.
r4 .HHhHHHHHHHHHhHHH.
r5 .HHHHHHHHHHHHHHHH.
r6 .HHHHhHHHHHHhHHHH.
r7 .HH.HH.HH.HH.H.HH.
r8 .HH............HH.
r9 .H..............H.
''')),
    'davidd': (grid('''
r0 .....CCCCCC.......
r1 ...CCCCCCCCCC.....
r2 ..CCCCCCCCCCCC....
r3 ..CCCCCCCCCCCCC...
r4 ..CCCCCCCCCCCCcccc
r5 ..hHHHHH..........
r6 ..HHHHHH..........
r7 ..HHHhH...........
r8 ..HHHH............
r9 ...HH.............
'''), grid('''
r0 .....CCCCCCCC.....
r1 ...CCCCCCCCCCCC...
r2 ..CCCCCCCwwCCCCC..
r3 ..CCCCCCCCCCCCCC..
r4 .cccccccccccccccc.
r5 .HH..cccccccc..HH.
r6 .HH............HH.
r7 .H..............H.
''')),
    'raphael': (grid('''
r0 ......hHHHh.......
r1 ....hHHHHHHHH.....
r2 ...HHHHHHHHHHHh...
r3 ..hHHHHHHHHHHHHH..
r4 ..HHHHHHHHHHHHHH..
r5 ..HHHhHHHHHH......
r6 ..HHHHHH..........
r7 ..hHHHH...........
r8 ..HHHH............
r9 ..HHH.............
r10 ...H.............
r11 ..........x.x.....
r12 .........x.x.x....
'''), grid('''
r0 .....hHHHHHHh.....
r1 ...hHHHHHHHHHHh...
r2 ..HHHHhHHHHHHHHH..
r3 ..HHHHHHHHhHHHHH..
r4 .HHHHHHHHHHHHHHHH.
r5 .HHHHHH....HHHHHH.
r6 .HHH.........HHHH.
r7 .HH............HH.
r8 .H..............H.
r9 ..................
r10 ..................
r11 ...x.x......x.x...
r12 ....x.x....x.x....
''')),
    'freda': (grid('''
r0 ......hHHHHh......
r1 ....HHHHHHHHHH....
r2 ...HHHHHHHHHHHH...
r3 ..HHHHHHHHHHHHHH..
r4 ..HHHHHHHHHHHHHHH.
r5 .HHHHHHHHHHHHHH...
r6 .HHHHHHHHHHHH.....
r7 .HHHHHHHHH........
r8 HHHHhHHHHH........
r9 HHHHHHHHH.........
r10 HHHHHHHHH.........
r11 HHHHhHHHH.........
r12 HHHHHHHH..........
r13 HHHHHHHH..........
r14 HHHHHHH...........
r15 .HHHHHH...........
r16 .HHHHH............
r17 ..hHH.............
'''), grid('''
r0 .....hHHHHHHh.....
r1 ...HHHHHHHHHHHH...
r2 ..HHHHHHHHHHHHHH..
r3 .HHHHHHHHHHHHHHHH.
r4 .HHHHHHHhHHHHHHHH.
r5 .HHHHHH...HHHHHHH.
r6 .HHHHH......HHHHH.
r7 HHHH..........HHHH
r8 HHH............HHH
r9 HHH............HHH
r10 HHH............HHH
r11 HHH............HHH
r12 HHHH..........HHHH
r13 HHHH..........HHHH
r14 HHHH..........HHHH
r15 HHHH..........HHHH
r16 .HHH..........HHH.
r17 .hH............Hh.
''')),
    'anderson': (grid('''
r0 ....CCCCCC........
r1 ...CCcCCCCCC......
r2 ..CCCCCCCCCCC.....
r3 ..CCcCCCCCCCCC....
r4 ..CCCCCCCCCCCCC...
r5 ..cccccccccccccc..
r6 .HHHHHHH..........
r7 .HHhHHHH..........
r8 .HHHHHH...........
r9 HHHHHHH...........
r10 HHhHHHH...........
r11 HHHHHHH..XXXXX....
r12 .HHHHHXXXXXXXXXX..
r13 .HHHH..XXXXXXXX...
r14 ..HHH....XXXXX....
r15 ...H..............
'''), grid('''
r0 .....CCCCCCCC.....
r1 ....CCCCcCCCCC....
r2 ...CCCCCCCCcCCC...
r3 ..CCcCCCCCCCCCCC..
r4 ..cccccccccccccc..
r5 .HHH..........HHH.
r6 .HH............HH.
r7 HHH............HHH
r8 HHH............HHH
r9 HHH............HHH
r10 HHHXX........XXHHH
r11 HHHXXXX....XXXXHHH
r12 .HHXXXXXXXXXXXXHH.
r13 .HH.XXXXXXXXXX.HH.
r14 .HH...XXXXXX...HH.
r15 ..H............H..
''')),
}

COMMON = {'S': SKIN, 's': SKIN_D, 'E': '#1c2242', 'M': '#a83a44', 'W': '#ffffff', 'r': '#f39a8a',
          'K': '#3a78d8', 'k': '#ffffff'}
JEANS = {'P': '#3a72c8', 'p': '#2a5498'}

CHARS = {
    'susan': dict(pal={'H': '#6a3a24', 'h': '#4a2616', 'A': '#f6f6f8', 'a': '#c6cad6', 'B': '#f6f6f8',
                       'Y': '#9aa0ac', 'y': '#6e7482', 'Q': '#4a4e7e', 'q': '#34385e', 'P': '#4a4e7e', 'p': '#34385e'},
                  bottoms='skirt', extra='sweater', instrument='mic'),
    'jimmy': dict(pal={'H': '#2a1e1a', 'h': '#4a3a30', 'A': '#4aa08a', 'a': '#1e5e50', 'B': '#ffffff',
                       'G': '#1c1c28', **JEANS},
                  bottoms='pants', glasses=True, plaid=('#e8f4ee', '#4aa08a', '#1e5e50'), instrument='keytar'),
    'davidd': dict(pal={'C': '#23407e', 'c': '#162a5a', 'w': '#ffffff', 'H': '#1c1c28', 'h': '#3a3a48',
                        'A': '#e8f2fa', 'a': '#b0c8dc', 'B': '#ffffff', 'P': '#3c6cc0', 'p': '#2a4e90',
                        'K': '#c4c8d2'},
                   bottoms='shorts', instrument='bass'),
    'raphael': dict(pal={'H': '#b8b8c0', 'h': '#6c6c76', 'A': '#e8b848', 'a': '#b8862a', 'B': '#26262e',
                         'G': '#2a2a30', 'x': '#c48a62', 'K': '#22305a', 'k': '#e8e0d0', **JEANS},
                    bottoms='pants', glasses=True, instrument='guitar'),
    'freda': dict(pal={'H': '#1c1a24', 'h': '#3a3646', 'A': '#5cbcee', 'a': '#3a8cc4', 'B': '#1c1c28',
                       'P': '#1c2440', 'p': '#10162a', 'K': '#3a7ad8'},
                  bottoms='pants', instrument='mic'),
    'anderson': dict(pal={'C': '#2f5fb8', 'c': '#1f4488', 'H': '#8a7a6a', 'h': '#5a4a3e', 'X': '#ececf0',
                          'A': '#e04848', 'a': '#9e2a2a', 'B': '#1c2244', 'G': '#9a6a2a',
                          'K': '#22305a', 'k': '#e8e0d0', **JEANS},
                     bottoms='pants', glasses=True, plaid=('#f6f0f0', '#e04848', '#9e2a2a'), instrument='snare'),
}
ORDER = ['susan', 'jimmy', 'davidd', 'raphael', 'freda', 'anderson']


def palette(name):
    return {**COMMON, **CHARS[name]['pal']}


def plaid_fn(name):
    """格紋襯衫：A/a 依 2x2 格交錯成淺、中、深三色（a 是暗面，整體再暗一階）。"""
    pl = CHARS[name].get('plaid')
    if not pl:
        return None
    light, mid, dark = pl

    def f(ch, x, y):
        if ch not in 'Aa':
            return None
        n = (x // 2) % 2 + (y // 2) % 2
        if ch == 'a':
            n = min(n + 1, 2)
        return (light, mid, dark)[n]
    return f


# ------------------------------------------------------------ 組裝
def head(name, view):
    cfg, pal = CHARS[name], palette(name)
    side = view == 'side'
    img = paint(blank(), HEAD_SIDE if side else HEAD_FRONT, pal)
    img = paint(img, FACE_SIDE if side else FACE_FRONT, pal)
    img = paint(img, HAIR[name][0 if side else 1], pal)
    if cfg.get('glasses'):
        img = paint(img, GLASSES_SIDE if side else GLASSES_FRONT, pal)
    if name == 'anderson' and not side:
        img = paint(img, FACE_FRONT[11:13] and [''] * 11 + ['.......MWWM.......'], pal)   # 鬍子中間露出嘴
    return outline(img)


def body_parts(name, view, legs='stand', arm=ARM_SIDE):
    """回傳 (腿, 裙, 身體, 手臂) 四個已加外框的部位；正面不含手臂。"""
    cfg, pal, pat = CHARS[name], palette(name), plaid_fn(name)
    side = view == 'side'
    L = part(leg_rows(LEGS[legs if side else 'front'], cfg['bottoms']), pal)
    skirt = part(SKIRT_SIDE if side else SKIRT_FRONT, pal) if cfg['bottoms'] == 'skirt' else None
    torso = paint(blank(), TORSO_SIDE if side else TORSO_FRONT, pal, pattern=pat)
    if cfg.get('extra') == 'sweater':
        torso = paint(torso, SWEATER_SIDE if side else SWEATER_FRONT, pal)
    torso = outline(torso)
    a = part(arm, pal, pattern=pat) if side and arm else None
    return L, skirt, torso, a


def bare(name, view='side', legs='stand'):
    L, skirt, torso, a = body_parts(name, view, legs)
    return stack(L, skirt, torso, head(name, view), a)


def preview(frames, scale=6, bg=(200, 220, 240, 255)):
    W = sum(f.width for f in frames[0])
    sheet = Image.new('RGBA', (W, CH * len(frames)), bg)
    for r, row in enumerate(frames):
        x = 0
        for f in row:
            sheet.alpha_composite(f, (x, r * CH)); x += f.width
    return sheet.resize((sheet.width * scale, sheet.height * scale), Image.NEAREST)


# ------------------------------------------------------------ 樂器（直立畫，琴頭朝上）
INST_PAL = {'D': '#5a3418', 'N': '#7a4a22', 'T': '#e5a858', 't': '#c07830', 'O': '#2a160a',
            'R': '#d23a3a', 'r': '#9e2828', 'W': '#f4f4f6', 'K': '#202024', 'Y': '#ffd040', 'B': '#5ad0ff',
            'G': '#8a90a4', 'L': '#e8ecf4', 'n': '#e3bd7a', 'P': '#e84a6e', 'p': '#b8304e'}
GUITAR = (grid('''
r0 ..DDDD..
r1 ..DDDD..
r2 ..DDDD..
r3 ...NN...
r4 ...NN...
r5 ...NN...
r6 ...NN...
r7 ...NN...
r8 ...NN...
r9 ..TTTT..
r10 .TTTTTt.
r11 .TTTTTt.
r12 .TTOOTt.
r13 ..TOOT..
r14 .TTTTTt.
r15 TTTTTTTt
r16 TTTTTTTt
r17 TTDDDDTt
r18 TTTTTTTt
r19 .TTTTTt.
r20 ..TTTT..
'''), (4, 15))
BASS = (grid('''
r0 ..KKK...
r1 ..KKK...
r2 ..KKK...
r3 ...nn...
r4 ...nn...
r5 ...nn...
r6 ...nn...
r7 ...nn...
r8 ...nn...
r9 ...nn...
r10 ...nn...
r11 ...nn...
r12 ...nn...
r13 ...nn...
r14 ...nn...
r15 RR.nn...
r16 RR.nn.R.
r17 RRRnnRR.
r18 RRRRRRRr
r19 RRWWWWRr
r20 RRWKKWRr
r21 RRWWWWRr
r22 RRWKKWRr
r23 .RRRRRr.
r24 ..RRRr..
'''), (4, 20))
KEYTAR = (grid('''
r0 .KK...
r1 .KY...
r2 .KK...
r3 .KK...
r4 .KB...
r5 .KK...
r6 .KK...
r7 PPPPPP
r8 PWWWWp
r9 PKKWWp
r10 PWWWWp
r11 PKKWWp
r12 PWWWWp
r13 PKKWWp
r14 PWWWWp
r15 PWWWWp
r16 PKKWWp
r17 PWWWWp
r18 PKKWWp
r19 PWWWWp
r20 PPPPPp
'''), (3, 13))
SNARE_SIDE = grid('''
r0 RRRRRRRRR
r1 WGWWGWWGW
r2 WGWWGWWGW
r3 WGWWGWWGW
r4 RRRRRRRRR
''')
SNARE_FRONT = grid('''
r0 .LLLLLLLLLLLL.
r1 RRRRRRRRRRRRRR
r2 WGWWGWWGWWGWWG
r3 WGWWGWWGWWGWWG
r4 WGWWGWWGWWGWWG
r5 rrrrrrrrrrrrrr
''')
STRAP = '#3b2416'
STICK, STICK_TIP = '#e8c890', '#fff2d0'
MIC_HEAD, MIC_HANDLE = '#c8ccd8', '#24242c'


def inst_part(inst, angle, at):
    """直立樂器旋轉 angle 度（正值逆時針、琴頭往左倒）後，讓錨點落在格座標 at，再加外框。"""
    rows, anchor = inst
    piece = paint(Image.new('RGBA', (max(map(len, rows)), len(rows)), (0, 0, 0, 0)), rows, INST_PAL, 0, 0)
    w, h = piece.size
    rot = piece.rotate(angle, resample=Image.NEAREST, expand=True)
    t = math.radians(angle)
    vx, vy = anchor[0] + .5 - w / 2, anchor[1] + .5 - h / 2
    rx = vx * math.cos(t) + vy * math.sin(t) + rot.width / 2
    ry = -vx * math.sin(t) + vy * math.cos(t) + rot.height / 2
    L = blank()
    L.alpha_composite(rot, (round(OX + at[0] - rx), round(OY + at[1] - ry)))
    return outline(L)


def mic_part(x, y):
    """麥克風：(x, y) 是握柄底端，網罩（3x2）在上方。"""
    L = blank()
    L = paint(L, ['.H.', '.H.', '.H.'], {'H': MIC_HANDLE}, OX + x - 1, OY + y - 2)
    L = paint(L, ['GGG', 'GgG'], {'G': MIC_HEAD, 'g': '#8a90a4'}, OX + x - 1, OY + y - 4)
    return outline(L)


def stick_part(a, b):
    L = line_part([([a, b], STICK, 1)])
    return dots(L, [b], STICK_TIP)


# ------------------------------------------------------------ 姿勢
def sleeve(name):
    pl = CHARS[name].get('plaid')
    return pl[1] if pl else CHARS[name]['pal']['A']


def arm_part(name, pts):
    """正面手臂：pts 是肩→肘→手的格座標，袖子 3 格粗、手 2x2。"""
    return line_part([(pts, sleeve(name), 3), ([pts[-1]], SKIN, 2)])


def side_frame(name, legs='stand'):
    cfg = CHARS[name]
    inst = cfg['instrument']
    jump = legs == 'jump'
    L, skirt, torso, arm = body_parts(name, 'side', legs, None if jump else ARM_SIDE)
    back = front = held = raised = None
    straps = []
    if inst == 'guitar':
        back = inst_part(GUITAR, 30 + 10 * jump, (5, 19))
    elif inst == 'bass':
        back = inst_part(BASS, 25 + 10 * jump, (5, 20))
    elif inst == 'keytar':
        back = inst_part(KEYTAR, 55 + 8 * jump, (4, 17))
    if back is not None:
        straps = [(12, 14), (11, 15), (10, 16), (9, 17), (8, 18), (7, 19), (6, 20)]
    if inst == 'snare':
        front = part(SNARE_SIDE, INST_PAL, x0=OX + 12, y0=OY + 18 - jump)
        straps = [(13, 14), (13, 15), (13, 16), (13, 17)]
    if jump:   # 前面那隻手先往前、再從下巴前方往上舉（不遮臉）
        raised = [line_part([([(9, 16), (16, 16), (18, 10)], sleeve(name), 3), ([(18, 9)], SKIN, 3)])]
        if inst == 'mic':
            raised.append(mic_part(18, 8))
        if inst == 'snare':
            raised.append(stick_part((18, 8), (20, 2)))
    else:
        if inst == 'mic':
            held = mic_part(8, 22)
        if inst == 'snare':
            held = stick_part((9, 22), (15, 17))
    torso = dots(torso, straps, '#8a90a4' if inst == 'snare' else STRAP)
    return stack(back, L, skirt, torso, head(name, 'side'), front, arm, held, *(raised or []))


# 正面演奏兩格：每格是（左手、右手）的肩→肘→手座標；「左」指畫面左邊
PLAY = {
    'guitar': [([(2, 15), (0, 19), (5, 20)], [(15, 15), (18, 18), (15, 17)]),
               ([(2, 15), (0, 20), (5, 23)], [(15, 15), (18, 18), (15, 17)])],
    'bass':   [([(2, 15), (0, 19), (6, 20)], [(15, 15), (18, 18), (16, 16)]),
               ([(2, 15), (0, 20), (7, 22)], [(15, 15), (18, 17), (17, 15)])],
    'keytar': [([(2, 15), (0, 19), (5, 20)], [(15, 15), (17, 18), (16, 19)]),
               ([(2, 15), (1, 19), (9, 20)], [(15, 15), (17, 18), (16, 19)])],
    'snare':  [([(2, 15), (0, 18), (3, 16)], [(15, 15), (17, 19), (13, 20)]),
               ([(2, 15), (0, 19), (4, 20)], [(15, 15), (17, 18), (14, 16)])],
    'mic':    [([(2, 15), (1, 19), (1, 21)], [(15, 15), (16, 19), (10, 16)]),
               ([(2, 15), (-1, 12), (-1, 9)], [(15, 15), (16, 19), (10, 16)])],
}


def front_frame(name, k):
    inst = CHARS[name]['instrument']
    L, skirt, torso, _ = body_parts(name, 'front')
    held = []
    if inst == 'guitar':
        held.append(inst_part(GUITAR, -70, (5, 21)))
    elif inst == 'bass':
        held.append(inst_part(BASS, -65, (5, 21)))
    elif inst == 'keytar':
        held.append(inst_part(KEYTAR, -80, (7, 21)))
    elif inst == 'snare':
        held.append(part(SNARE_FRONT, INST_PAL, x0=OX + 2, y0=OY + 21))
    la, ra = PLAY[inst][k]
    arms = [arm_part(name, la), arm_part(name, ra)]
    extra = []
    if inst == 'snare':   # 舉高的那支鼓棒朝上、敲下去的那支碰鼓面
        extra = [stick_part((3, 16), (5, 10)), stick_part((13, 20), (10, 21))] if k == 0 else \
                [stick_part((4, 20), (7, 21)), stick_part((14, 16), (12, 10))]
    if inst == 'mic':
        extra = [mic_part(10, 15)]
    return stack(L, skirt, torso, head(name, 'front'), *held, *arms, *extra)


FRAMES = {
    'right_walk1': lambda n: side_frame(n, 'stand'),
    'right_walk2': lambda n: side_frame(n, 'small'),
    'right_walk3': lambda n: side_frame(n, 'stride'),
    'right_jump': lambda n: side_frame(n, 'jump'),
    'front_play1': lambda n: front_frame(n, 0),
    'front_play2': lambda n: front_frame(n, 1),
}


def render_all(name):
    out = {k: f(name) for k, f in FRAMES.items()}
    for k in ['walk1', 'walk2', 'walk3', 'jump']:
        out[f'left_{k}'] = out[f'right_{k}'].transpose(Image.FLIP_LEFT_RIGHT)
    return out


def main(outdir):
    root = Path(outdir)
    rows = []
    for name in ORDER:
        d = root / name
        d.mkdir(parents=True, exist_ok=True)
        frames = render_all(name)
        for k, im in frames.items():
            im.save(d / f'{k}.png')
        rows.append([frames[k] for k in ['right_walk1', 'right_walk2', 'right_walk3', 'right_jump',
                                         'left_walk1', 'front_play1', 'front_play2']])
    (root / 'anchors.json').write_text(json.dumps({
        'size': [CW, CH], 'right': list(FOOT), 'front': list(FOOT), 'left': [CW - 1 - FOOT[0], FOOT[1]],
        'note': '腳底中心（畫格像素座標）；場景與遊戲放大 2 倍使用'}, ensure_ascii=False, indent=1))
    preview(rows, 5).save(root / '_preview.png')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'characters')
