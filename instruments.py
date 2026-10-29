"""幫朝右角色背上各自的樂器：行走（walk）與跳躍（jump）兩種姿勢。

樂器先直立畫在自己的小圖上（琴頭朝上），旋轉後貼到角色背後；背帶、手上的東西畫在角色前面。
輸出加了留白的角色圖：原角色左上角位於 (PAD_L, PAD_T)，行走姿勢腳底貼齊圖片底邊。
跳躍姿勢從同一張側面圖改出來：前腳膝蓋抬高、後腳伸直，一手往前上方舉，背上的樂器因慣性往後甩。
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from landmarks import OUT, c, inner_outline

PAD_L, PAD_T, PAD_R = 16, 6, 12


def layer(w, h):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


# ------------------------------------------------------------ 直立樂器（琴頭朝上）
def acoustic_guitar():
    im, d = layer(13, 37)
    d.rectangle([4, 0, 8, 4], fill=c('#5a3418'))                  # 琴頭
    d.rectangle([5, 4, 7, 17], fill=c('#7a4a22'))                 # 琴頸
    d.ellipse([2, 14, 10, 25], fill=c('#e5a858'))                 # 上半琴身
    d.ellipse([0, 21, 12, 36], fill=c('#e5a858'))                 # 下半琴身
    d.rectangle([9, 23, 11, 33], fill=c('#c07830'))               # 暗面
    im = inner_outline(im, OUT)
    d = ImageDraw.Draw(im)
    d.line([6, 5, 6, 17], fill=c('#3e2210'))                      # 指板
    d.ellipse([5, 22, 7, 24], fill=c('#2a160a'))                  # 音孔
    d.line([4, 30, 8, 30], fill=c('#5a3418'))                     # 琴橋
    for y in (1, 3):
        d.point((3, y), fill=c('#d8d8e0')); d.point((9, y), fill=c('#d8d8e0'))
    return im, (6, 28)


def electric_bass():
    im, d = layer(14, 45)
    d.rectangle([4, 0, 8, 6], fill=c('#2a2a30'))                  # 琴頭
    d.rectangle([5, 6, 7, 30], fill=c('#e3bd7a'))                 # 楓木琴頸
    d.ellipse([1, 28, 13, 44], fill=c('#d23a3a'))                 # 琴身
    d.rectangle([1, 24, 4, 33], fill=c('#d23a3a'))                # 上琴角（較長）
    d.rectangle([10, 27, 12, 33], fill=c('#d23a3a'))              # 下琴角
    d.rectangle([10, 34, 12, 41], fill=c('#9e2828'))              # 暗面
    im = inner_outline(im, OUT)
    d = ImageDraw.Draw(im)
    d.rectangle([3, 31, 8, 39], fill=c('#f2f2f2'))                # 護板
    d.line([4, 33, 8, 33], fill=c('#202024'))                     # 拾音器
    d.line([4, 37, 8, 37], fill=c('#202024'))
    for y in (11, 17, 23):
        d.point((6, y), fill=c('#5a3418'))                        # 把位點
    for y in (1, 3, 5):
        d.point((3, y), fill=c('#d8d8e0')); d.point((9, y), fill=c('#d8d8e0'))
    return im, (7, 36)


def keytar():
    im, d = layer(10, 38)
    d.rectangle([3, 0, 6, 12], fill=c('#2a2a36'))                 # 握把
    d.rectangle([0, 11, 9, 37], fill=c('#e84a6e'))                # 琴身
    d.rectangle([8, 12, 9, 36], fill=c('#b8304e'))
    im = inner_outline(im, OUT)
    d = ImageDraw.Draw(im)
    d.rectangle([2, 13, 6, 34], fill=c('#f6f6f6'))                # 白鍵
    for y in range(14, 34, 2):
        d.line([2, y, 6, y], fill=c('#b8bcc8'))                   # 鍵縫
    for y in (15, 17, 21, 23, 25, 29, 31):
        d.line([2, y, 3, y], fill=c('#202024'))                   # 黑鍵
    d.point((4, 4), fill=c('#ffd040')); d.point((4, 7), fill=c('#5ad0ff'))  # 握把上的鈕
    return im, (5, 24)


def place(base, piece, anchor, angle, at):
    """把直立樂器旋轉 angle 度（逆時針，琴頭往左倒）後，讓錨點落在 at。"""
    w, h = piece.size
    rot = piece.rotate(angle, resample=Image.NEAREST, expand=True)
    t = math.radians(angle)
    vx, vy = anchor[0] - w / 2, anchor[1] - h / 2
    rx = vx * math.cos(t) + vy * math.sin(t) + rot.width / 2
    ry = -vx * math.sin(t) + vy * math.cos(t) + rot.height / 2
    base.alpha_composite(rot, (round(at[0] - rx), round(at[1] - ry)))


# ------------------------------------------------------------ 前景（背帶、手持）
def strap(d, a, b, col='#3b2416'):
    d.line([a, b], fill=c(col))


def mic(d, x, y):
    """手握麥克風：x, y 為拳頭位置。"""
    d.rectangle([x - 1, y - 5, x + 1, y], fill=OUT)
    d.line([x, y - 5, x, y], fill=c('#24242c'))                   # 握柄
    d.rectangle([x - 2, y - 9, x + 2, y - 5], fill=OUT)
    d.rectangle([x - 1, y - 8, x + 1, y - 6], fill=c('#c8ccd8'))  # 網罩
    d.point((x, y - 8), fill=c('#f4f6fa')); d.point((x, y - 7), fill=c('#8a90a4'))


def snare():
    """胸前的行進小鼓（側面）與鼓棒。"""
    im, d = layer(14, 11)
    d.rectangle([0, 0, 13, 10], fill=c('#f0f0f4'))
    im = inner_outline(im, OUT)
    d = ImageDraw.Draw(im)
    d.line([1, 1, 12, 1], fill=c('#c83030'))                      # 上鼓圈
    d.line([1, 9, 12, 9], fill=c('#c83030'))                      # 下鼓圈
    for x in (2, 5, 8, 11):
        d.line([x, 2, x, 8], fill=c('#8a90a4'))                   # 張力螺桿
    d.line([1, 5, 12, 5], fill=c('#d8dce6'))
    return im


# ------------------------------------------------------------ 每個人的裝備（原角色座標，經 o() 換到留白後）
def o(x, y):
    return x + PAD_L, y + PAD_T


def gear_raphael(bg, fg, d, j):
    place(bg, *acoustic_guitar(), 32 + 8 * j, o(-1, 37))
    strap(d, o(15, 22), o(2, 40))


def gear_davidd(bg, fg, d, j):
    place(bg, *electric_bass(), 26 + 8 * j, o(0, 39))
    strap(d, o(16, 22), o(2, 41))


def gear_jimmy(bg, fg, d, j):
    place(bg, *keytar(), 52 + 8 * j, o(3, 31))
    strap(d, o(15, 22), o(4, 38))


def gear_anderson(bg, fg, d, j):
    fg.alpha_composite(snare(), o(14, 31 - j))                     # 跳起時小鼓往上彈 1 格
    d.line([o(17, 24), o(17, 31 - j)], fill=c('#8a90a4'))           # 背架
    if not j:
        d.line([o(10, 38), o(22, 28)], fill=c('#e8c890'))           # 鼓棒
        d.point(o(22, 28), fill=c('#fff2d0'))


def gear_susan(bg, fg, d, j):
    if not j:
        mic(d, *o(10, 39))


def gear_freda(bg, fg, d, j):
    if not j:
        mic(d, *o(9, 39))


GEAR = {'raphael': gear_raphael, 'davidd': gear_davidd, 'jimmy': gear_jimmy,
        'anderson': gear_anderson, 'susan': gear_susan, 'freda': gear_freda}


def jump_sprite(sprite, hip=44):
    a = np.array(sprite)
    h, w = a.shape[:2]
    legs = a[hip:].copy()
    xs = np.nonzero(legs[0, :, 3])[0]
    mid = (xs.min() + xs.max() + 1) // 2
    back, front = legs.copy(), legs.copy()
    back[:, mid:] = 0
    front[:, :mid] = 0
    pad = 4                                                        # 往左右各留 4 格給伸出去的腳
    out = np.zeros((h, w + pad * 2, 4), np.uint8)
    body = a.copy(); body[hip:] = 0
    paste(out, back, pad, hip)
    paste(out, body, pad, 0)
    paste(out, front, pad + 3, hip - 7)
    return Image.fromarray(out), pad


SKIN = '#f4b860'
# 跳躍時往上舉的手拿什麼：麥克風、鼓棒，其餘握拳
RAISED = {'susan': 'mic', 'freda': 'mic', 'anderson': 'stick'}


def raised_arm(sprite, name, x0, y0):
    """前方一隻手往前上方舉（在臉的前面，不蓋住臉）。袖子顏色取自肩膀。"""
    a = np.array(sprite)
    sleeve = tuple(int(v) for v in a[y0 + 27, x0 + 14, :3]) + (255,)
    L = Image.new('RGBA', sprite.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    sx, sy, ex, ey, fx, fy = x0 + 15, y0 + 26, x0 + 20, y0 + 20, x0 + 24, y0 + 12
    d.line([sx, sy, ex, ey], fill=sleeve, width=5)                 # 上臂（袖子）
    d.line([ex, ey, fx, fy + 1], fill=c(SKIN), width=4)            # 前臂
    d.rectangle([fx - 2, fy - 2, fx + 2, fy + 2], fill=c(SKIN))    # 拳頭
    L = inner_outline(L, OUT)
    d = ImageDraw.Draw(L)
    kind = RAISED.get(name)
    if kind == 'mic':
        mic(d, fx, fy - 2)
    elif kind == 'stick':
        d.line([fx, fy - 2, fx - 3, fy - 10], fill=c('#e8c890'))
        d.point((fx - 3, fy - 10), fill=c('#fff2d0'))
    sprite.alpha_composite(L)


def paste(dst, src, x, y):
    h, w = src.shape[:2]
    H, W = dst.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    m = s[..., 3] > 0
    dst[y0:y1, x0:x1][m] = s[m]


def equip(sprite, name, pose='walk'):
    j = int(pose == 'jump')
    shift, top = 0, 12 * j                                         # 跳躍：左右多 shift 格給腳、上方多 top 格給舉高的手
    if j:
        sprite, shift = jump_sprite(sprite)
        sprite = sprite.crop((0, -top, sprite.width, sprite.height))
        raised_arm(sprite, name, shift, top)
    w, h = sprite.width - 2 * shift + PAD_L + PAD_R, sprite.height + PAD_T
    bg = Image.new('RGBA', (w, h - top), (0, 0, 0, 0))
    fg = Image.new('RGBA', (w, h - top), (0, 0, 0, 0))
    if name in GEAR:
        GEAR[name](bg, fg, ImageDraw.Draw(fg), j)
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    out.alpha_composite(bg, (0, top))
    out.alpha_composite(sprite, (PAD_L - shift, PAD_T))
    out.alpha_composite(fg, (0, top))
    return out


def main(chars_dir):
    src = Path(chars_dir)
    for name in ['susan', 'jimmy', 'davidd', 'raphael', 'freda', 'anderson']:
        base = Image.open(src / f'{name}.png').convert('RGBA')
        for pose in ('walk', 'jump'):
            equip(base, name, pose).save(src / f'{name}_{pose}.png')


if __name__ == '__main__':
    main(sys.argv[1])
