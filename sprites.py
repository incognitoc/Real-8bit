"""六位團員的遊戲畫格：以設定表擷取的原生像素圖（sprites/，extract_sprites.py）為底，加上樂器與動作。

不重畫人物：
- 走路：朝右用設定表的 RIGHT、朝左用 LEFT。腿部依左右切開，前後腳各自位移成三格步伐。
- 跳躍：前腳往前上抬、後腳往後收；背上的樂器因慣性往後甩。
- 正面演奏：用 FRONT，樂器擺在原本垂著的雙手位置；第 2 格把撥弦／敲鼓的那隻手往上移、上半身微微下沉。
  主唱用麥克風架，不必改手。

輸出 characters/<名字>/：right_walk1~3、right_jump、left_walk1~3、left_jump、front_play1~2，
所有畫格同尺寸（CW x CH），腳底中心在 FOOT（characters/anchors.json）。
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from landmarks import OUT, c, inner_outline

HERE = Path(__file__).parent
SRC = HERE / 'sprites'
CW, CH = 84, 100
FOOT = (42, 92)          # 腳底中心（畫格座標）
ORDER = ['susan', 'jimmy', 'davidd', 'raphael', 'freda', 'anderson']
INSTRUMENT = {'susan': 'mic', 'freda': 'mic', 'jimmy': 'keytar', 'davidd': 'bass',
              'raphael': 'guitar', 'anderson': 'snare'}
HIP = 50                 # 腿部從這一列開始（68 格高的原圖）


def load(name, view):
    return Image.open(SRC / f'{name}_{view}.png').convert('RGBA')


def blank():
    return Image.new('RGBA', (CW, CH), (0, 0, 0, 0))


def origin(sprite):
    """原圖貼進畫格的左上角：腳底（最下面幾列）的中心對齊 FOOT。"""
    a = np.array(sprite)[..., 3] > 0
    xs = np.nonzero(a[-4:].any(axis=0))[0]
    return FOOT[0] - (xs.min() + xs.max()) // 2, FOOT[1] - sprite.height


def paste_arr(dst, src, x, y):
    h, w = src.shape[:2]
    H, W = dst.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x1 <= x0 or y1 <= y0:
        return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    m = s[..., 3] > 0
    dst[y0:y1, x0:x1][m] = s[m]


# ------------------------------------------------------------ 腿部（側面朝右）
# 每格：(前腳 dx, dy, 後腳 dx, dy)
STEPS = {'walk1': (0, 0, 0, 0), 'walk2': (1, 0, -1, 0), 'walk3': (3, 0, -2, -1), 'jump': (4, -6, -3, -2)}


def legs_split(sprite, step):
    """把 HIP 以下依腿部中線切成後腳（左）、前腳（右），各自位移。回傳 numpy RGBA。"""
    a = np.array(sprite)
    legs = a[HIP:].copy()
    xs = np.nonzero(legs[2, :, 3])[0]
    mid = (xs.min() + xs.max() + 1) // 2
    back, front = legs.copy(), legs.copy()
    back[:, mid:] = 0
    front[:, :mid] = 0
    out = np.zeros_like(a)
    body = a.copy(); body[HIP:] = 0
    fdx, fdy, bdx, bdy = STEPS[step]
    paste_arr(out, back, bdx, HIP + bdy)
    paste_arr(out, body, 0, 0)
    paste_arr(out, front, fdx, HIP + fdy)
    return out


# ------------------------------------------------------------ 樂器（直立畫，琴頭朝上；回傳圖與錨點）
def layer(w, h):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


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
    d.rectangle([4, 0, 8, 5], fill=c('#2a2a30'))                  # 琴頭
    d.rectangle([5, 5, 7, 30], fill=c('#e3bd7a'))                 # 楓木琴頸
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
    for y in (1, 3):
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


def snare_side():
    im, d = layer(15, 11)
    d.rectangle([0, 0, 14, 10], fill=c('#f0f0f4'))
    im = inner_outline(im, OUT)
    d = ImageDraw.Draw(im)
    d.line([1, 1, 13, 1], fill=c('#c83030')); d.line([1, 9, 13, 9], fill=c('#c83030'))   # 鼓圈
    for x in (2, 5, 8, 11):
        d.line([x, 2, x, 8], fill=c('#8a90a4'))                   # 張力螺桿
    return im


def snare_front():
    im, d = layer(22, 12)
    d.ellipse([0, 0, 21, 5], fill=c('#e8ecf4'))                   # 鼓面
    d.rectangle([0, 3, 21, 11], fill=c('#f0f0f4'))
    im = inner_outline(im, OUT)
    d = ImageDraw.Draw(im)
    d.line([1, 4, 20, 4], fill=c('#c83030')); d.line([1, 10, 20, 10], fill=c('#9e2626'))
    for x in range(2, 19, 4):
        d.line([x, 5, x + 2, 9], fill=c('#8a90a4'))               # 斜向螺桿
    return im


def mic_stand(height):
    """麥克風架：上端是麥克風，往下是直桿與三腳底座。"""
    im, d = layer(11, height)
    d.rectangle([3, 0, 6, 3], fill=c('#c8ccd8'))                  # 網罩
    d.rectangle([4, 4, 5, 6], fill=c('#24242c'))                  # 握柄
    d.line([4, 7, 4, height - 3], fill=c('#4a4e5a'), width=2)     # 直桿
    d.line([0, height - 1, 4, height - 4], fill=c('#4a4e5a'), width=2)
    d.line([9, height - 1, 5, height - 4], fill=c('#4a4e5a'), width=2)
    im = outline(im)
    ImageDraw.Draw(im).point((4, 1), fill=c('#f4f6fa'))
    return im


def outline(img, col=OUT):
    """外框：在不透明像素外圍（上下左右）補一圈深色。"""
    a = np.array(img)
    m = a[..., 3] > 0
    p = np.pad(m, 1)
    near = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    a[near & ~m] = col
    return Image.fromarray(a)


def rotated(piece_anchor, angle):
    """直立樂器旋轉 angle 度（正值逆時針、琴頭往左倒）；回傳旋轉後的圖與錨點的新位置。"""
    piece, anchor = piece_anchor
    w, h = piece.size
    rot = piece.rotate(angle, resample=Image.NEAREST, expand=True)
    t = math.radians(angle)
    vx, vy = anchor[0] + .5 - w / 2, anchor[1] + .5 - h / 2
    return rot, (vx * math.cos(t) + vy * math.sin(t) + rot.width / 2,
                 -vx * math.sin(t) + vy * math.cos(t) + rot.height / 2)


def put(layer_img, im, x, y):
    layer_img.alpha_composite(im, (round(x), round(y)))


def put_at(layer_img, piece_anchor, angle, x, y):
    rot, (ax, ay) = rotated(piece_anchor, angle)
    put(layer_img, rot, x - ax, y - ay)


def line(layer_img, a, b, col, w=1):
    ImageDraw.Draw(layer_img).line([a, b], fill=c(col), width=w)


def stick(layer_img, a, b):
    L = Image.new('RGBA', layer_img.size, (0, 0, 0, 0))
    ImageDraw.Draw(L).line([a, b], fill=c('#e8c890'), width=2)
    layer_img.alpha_composite(outline(L))


# ------------------------------------------------------------ 側面（朝右）
def edges(a, y):
    xs = np.nonzero(a[y, :, 3])[0]
    return xs.min(), xs.max()


def side_frame(name, view, step):
    """view='right' 直接用；'left' 先翻成朝右處理，最後再翻回去。"""
    sprite = load(name, view)
    if view == 'left':
        sprite = sprite.transpose(Image.FLIP_LEFT_RIGHT)
    jump = step == 'jump'
    body = legs_split(sprite, step)
    ox, oy = origin(sprite)
    back_x, front_x = edges(body, 40)
    bx, fx = ox + back_x, ox + front_x
    kind = INSTRUMENT[name]
    behind, front = blank(), blank()
    swing = 10 * jump
    if kind == 'guitar':
        put_at(behind, acoustic_guitar(), 30 + swing, bx + 3, oy + 45)
    elif kind == 'bass':
        put_at(behind, electric_bass(), 24 + swing, bx + 3, oy + 46)
    elif kind == 'keytar':
        put_at(behind, keytar(), 52 + swing, bx + 4, oy + 41)
    if kind in ('guitar', 'bass', 'keytar'):
        line(front, (fx - 4, oy + 31), (bx + 3, oy + 47), '#3b2416', 2)   # 背帶
    if kind == 'snare':
        line(front, (fx - 5, oy + 31), (fx - 4, oy + 41), '#8a90a4', 2)   # 背架
        put(front, snare_side(), fx - 7, oy + 40 - jump * 2)
        stick(front, (fx - 6, oy + 50), (fx + 4, oy + 38 - jump * 6))
    if kind == 'mic':
        hx, hy = fx - 5, oy + 47
        L = blank()
        d = ImageDraw.Draw(L)
        d.rectangle([hx, hy - 5, hx + 1, hy], fill=c('#24242c'))          # 握柄
        d.rectangle([hx - 1, hy - 9, hx + 2, hy - 6], fill=c('#c8ccd8'))  # 網罩
        front.alpha_composite(outline(L))
    out = blank()
    out.alpha_composite(behind)
    paste = np.array(out)
    paste_arr(paste, body, ox, oy)
    out = Image.fromarray(paste)
    out.alpha_composite(front)
    if view == 'left':
        out = out.transpose(Image.FLIP_LEFT_RIGHT)
    return out


# ------------------------------------------------------------ 正面演奏
def hands(sprite):
    """正面原圖兩手大約位置（左右下緣）。"""
    w = sprite.width
    return (4, 45), (w - 5, 45)


def move_block(a, box, dx, dy):
    """把 box 範圍的像素整塊位移（用於撥弦的手）；原位置留空。"""
    x0, y0, x1, y1 = box
    blk = a[y0:y1, x0:x1].copy()
    a[y0:y1, x0:x1] = 0
    paste_arr(a, blk, x0 + dx, y0 + dy)


def front_frame(name, k):
    sprite = load(name, 'front')
    ox, oy = origin(sprite)
    a = np.array(sprite)
    (lx, ly), (rx, ry) = hands(sprite)
    kind = INSTRUMENT[name]
    w = sprite.width
    if k == 1 and kind != 'mic':
        # 撥弦／敲鼓：畫面左手往上 3 格；上半身（腰以上）下沉 1 格
        move_block(a, (0, ly - 5, 8, ly + 5), 1, -3)
    if k == 1:
        upper = a[:HIP].copy(); a[:HIP] = 0
        paste_arr(a, upper, 0, 1)
    over, behind = blank(), blank()
    cx = ox + w // 2
    if kind == 'guitar':
        put_at(over, acoustic_guitar(), -68, ox + lx + 9, oy + ly + 1)
    elif kind == 'bass':
        put_at(over, electric_bass(), -62, ox + lx + 9, oy + ly + 1)
    elif kind == 'keytar':
        put_at(over, keytar(), -84, cx + 2, oy + ly + 1)
    elif kind == 'snare':
        line(over, (ox + 7, oy + 30), (cx - 6, oy + 47), '#8a90a4', 1)
        line(over, (ox + w - 8, oy + 30), (cx + 6, oy + 47), '#8a90a4', 1)
        put(over, snare_front(), cx - 11, oy + 47)
        up = (k == 0)
        stick(over, (ox + lx + 1, oy + ly - (3 if k else 0)), (cx - 4, oy + 47) if not up else (ox + lx + 4, oy + ly - 10))
        stick(over, (ox + rx, oy + ry), (cx + 4, oy + 47) if up else (ox + rx - 3, oy + ry - 10))
    elif kind == 'mic':
        put(behind, mic_stand(60), cx - 5, oy + 14 + k)
    out = blank()
    out.alpha_composite(behind)
    arr = np.array(out)
    paste_arr(arr, a, ox, oy)
    out = Image.fromarray(arr)
    out.alpha_composite(over)
    if kind == 'mic':   # 架上的麥克風要在嘴前，蓋在人物上面
        top = mic_stand(60).crop((0, 0, 11, 8))
        put(out, top, cx - 5, oy + 14 + k)
    return out


def render_all(name):
    out = {}
    for view in ('right', 'left'):
        for step in ('walk1', 'walk2', 'walk3', 'jump'):
            out[f'{view}_{step}'] = side_frame(name, view, step)
    out['front_play1'] = front_frame(name, 0)
    out['front_play2'] = front_frame(name, 1)
    return out


def preview(rows, scale=3, bg=(200, 220, 240, 255)):
    sheet = Image.new('RGBA', (CW * len(rows[0]), CH * len(rows)), bg)
    for r, row in enumerate(rows):
        for k, f in enumerate(row):
            sheet.alpha_composite(f, (k * CW, r * CH))
    return sheet.resize((sheet.width * scale, sheet.height * scale), Image.NEAREST)


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
                                         'left_walk3', 'left_jump', 'front_play1', 'front_play2']])
    (root / 'anchors.json').write_text(json.dumps({
        'size': [CW, CH], 'foot': list(FOOT), 'note': '所有畫格的腳底中心（畫格像素座標）'},
        ensure_ascii=False, indent=1))
    preview(rows).save(root / '_preview.png')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'characters')
