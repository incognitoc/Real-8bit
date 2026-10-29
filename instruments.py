"""幫朝右角色背上各自的樂器（行走姿勢）。

樂器先直立畫在自己的小圖上（琴頭朝上），旋轉後貼到角色背後；背帶、手上的東西畫在角色前面。
輸出加了留白的角色圖：原角色左上角位於 (PAD_L, PAD_T)，腳底仍貼齊圖片底邊。
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from landmarks import OUT, c, inner_outline

PAD_L, PAD_T, PAD_R = 16, 6, 10


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


def gear_raphael(bg, fg, d):
    place(bg, *acoustic_guitar(), 32, o(-1, 37))
    strap(d, o(15, 22), o(2, 40))


def gear_davidd(bg, fg, d):
    place(bg, *electric_bass(), 26, o(0, 39))
    strap(d, o(16, 22), o(2, 41))


def gear_jimmy(bg, fg, d):
    place(bg, *keytar(), 52, o(3, 31))
    strap(d, o(15, 22), o(4, 38))


def gear_anderson(bg, fg, d):
    fg.alpha_composite(snare(), o(14, 31))
    d.line([o(17, 24), o(17, 31)], fill=c('#8a90a4'))               # 背架
    d.line([o(10, 38), o(22, 28)], fill=c('#e8c890'))               # 鼓棒
    d.point(o(22, 28), fill=c('#fff2d0'))


def gear_susan(bg, fg, d):
    mic(d, *o(10, 39))


def gear_freda(bg, fg, d):
    mic(d, *o(9, 39))


GEAR = {'raphael': gear_raphael, 'davidd': gear_davidd, 'jimmy': gear_jimmy,
        'anderson': gear_anderson, 'susan': gear_susan, 'freda': gear_freda}


def equip(sprite, name):
    w, h = sprite.width + PAD_L + PAD_R, sprite.height + PAD_T
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    fg = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    if name in GEAR:
        GEAR[name](out, fg, ImageDraw.Draw(fg))
    out.alpha_composite(sprite, (PAD_L, PAD_T))
    out.alpha_composite(fg)
    return out


def main(chars_dir):
    src = Path(chars_dir)
    for name in ['susan', 'jimmy', 'davidd', 'raphael', 'freda', 'anderson']:
        equip(Image.open(src / f'{name}.png').convert('RGBA'), name).save(src / f'{name}_walk.png')


if __name__ == '__main__':
    main(sys.argv[1])
