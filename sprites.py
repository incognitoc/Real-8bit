"""六位團員的 8-bit 角色（帶樂器）。

頭部取自樂團海報（extract_heads.py → heads/<名字>.png），身體、手腳與樂器依海報的服裝配色用程式畫：
軀幹是多邊形，手腳是粗線段（肩→肘→手、髖→膝→踝），所以走路、跳躍、演奏都只是換關節角度。
每個部位各自加 1 格深藍外框後依序疊起來，頭、身體、手臂、樂器之間都有清楚的分界。

角色約 30x58 像素，放進場景時 1:1 貼在 2 倍場景層上（和地標相比是一半大小的像素格）。
輸出到 characters/<名字>/：
  right_walk1~3、right_jump、left_walk1~3、left_jump、front_play1~2
所有畫格同尺寸（CW x CH），腳底中心記在 characters/anchors.json。
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from landmarks import OUT, c, inner_outline

HERE = Path(__file__).parent
CW, CH = 66, 88          # 畫格尺寸
OX, OY = 18, 20          # 角色 30x58 區塊的左上角
FOOT = (OX + 15, OY + 58)  # 腳底中心

SKIN = '#f4b070'
NECK_Y = 26              # 頭部底緣（下巴）對齊的高度
HIP_Y = 43
THIGH, SHIN = 7, 7
WHITE = '#ffffff'


# ------------------------------------------------------------ 基本工具
def blank():
    return Image.new('RGBA', (CW, CH), (0, 0, 0, 0))


def outline(img, col=OUT):
    """外框：在不透明像素外圍（上下左右）補一圈深色。"""
    a = np.array(img)
    m = a[..., 3] > 0
    p = np.pad(m, 1)
    near = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    a[near & ~m] = col
    return Image.fromarray(a)


def P(x, y):
    """角色區塊座標 → 畫格座標。"""
    return (OX + x, OY + y)


def stack(*layers):
    out = blank()
    for L in layers:
        if L is not None:
            out.alpha_composite(L)
    return out


def limb(d, pts, col, w):
    """粗線段：每段畫成粗線，關節補方塊，避免轉角缺角。"""
    pts = [P(*p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        d.line([a, b], fill=c(col), width=w)
    r0, r1 = (w - 1) // 2, w // 2
    for x, y in pts:
        d.rectangle([round(x) - r0, round(y) - r0, round(x) + r1, round(y) + r1], fill=c(col))


def pattern_fill(img, fn):
    """不透明像素依 fn(x, y) 重新上色（格紋用）。"""
    a = np.array(img)
    ys, xs = np.nonzero(a[..., 3] > 0)
    for y, x in zip(ys, xs):
        a[y, x] = c(fn(x, y))
    return Image.fromarray(a)


# ------------------------------------------------------------ 服裝（配色取自海報）
JEANS = ('#3a6cb4', '#2a5090')
CHARS = {
    'susan':    dict(top=('#f6f6f8', '#c8ccd6'), inner=None, bottoms='skirt', low=('#6a6c78', '#4e505a'),
                     shoe=('#2c4a8a', WHITE), extra='sweater', instrument='mic'),
    'jimmy':    dict(top=('#3e7060', '#22443a'), inner=WHITE, bottoms='pants', low=JEANS,
                     shoe=('#22305a', WHITE), plaid=('#e6ece6', '#3e7060', '#1e3a30'), instrument='keytar'),
    'davidd':   dict(top=('#dfe4e8', '#aab4bc'), inner=WHITE, bottoms='shorts', low=('#3e70b8', '#2c5290'),
                     shoe=('#d6d8dc', WHITE), socks=True, instrument='bass'),
    'raphael':  dict(top=('#dcbc84', '#b08c58'), inner='#26262c', bottoms='pants', low=JEANS,
                     shoe=('#2a2a32', '#e8e0d0'), instrument='guitar'),
    'freda':    dict(top=('#82b4dc', '#5486b8'), inner='#1e1e26', bottoms='pants', low=('#22222c', '#14141a'),
                     shoe=('#3a68b0', WHITE), instrument='mic'),
    'anderson': dict(top=('#d84040', '#9e2a2a'), inner='#1e1e26', bottoms='pants', low=JEANS,
                     shoe=('#22305a', '#e8e0d0'), plaid=('#f4eeee', '#d84040', '#8e2626'), instrument='snare'),
}
ORDER = ['susan', 'jimmy', 'davidd', 'raphael', 'freda', 'anderson']
SWEATER = ('#8c8c94', '#66666e')


def plaid_fn(name):
    pl = CHARS[name].get('plaid')
    if not pl:
        return None
    light, mid, dark = pl

    def f(x, y):
        return (light, mid, dark)[(x // 3) % 2 + (y // 3) % 2]
    return f


def head(name):
    """海報擷取的頭，下巴中心對齊 (15, NECK_Y)。"""
    h = Image.open(HERE / 'heads' / f'{name}.png').convert('RGBA')
    L = blank()
    L.alpha_composite(h, P(15 - h.width // 2, NECK_Y - h.height))
    return outline(L)


# ------------------------------------------------------------ 軀幹
def inner_poly(view):
    if view == 'side':
        return [P(19, 25), P(21, 25), P(23, 31), P(22, 36), P(20, 36)]
    return [P(12, 26), P(18, 26), P(17, 37), P(13, 37)]


def torso(name, view):
    cfg = CHARS[name]
    top, shade = cfg['top']
    L = blank()
    d = ImageDraw.Draw(L)
    if view == 'side':
        d.polygon([P(9, 25), P(21, 25), P(23, 31), P(22, 42), P(9, 42), P(8, 31)], fill=c(top))
        d.polygon([P(8, 31), P(9, 25), P(11, 25), P(11, 42), P(9, 42)], fill=c(shade))      # 背面暗部
    else:
        d.polygon([P(5, 26), P(25, 26), P(26, 31), P(24, 42), P(6, 42), P(4, 31)], fill=c(top))
        d.rectangle([P(5, 36), P(7, 42)], fill=c(shade)); d.rectangle([P(23, 36), P(25, 42)], fill=c(shade))
    fn = plaid_fn(name)
    if fn:
        L = pattern_fill(L, fn)
        d = ImageDraw.Draw(L)
    if cfg['inner']:                         # 敞開的襯衫／外套裡的內搭
        d.polygon(inner_poly(view), fill=c(cfg['inner']))
        if view != 'side':
            d.line([P(12, 26), P(14, 38)], fill=c(shade)); d.line([P(18, 26), P(16, 38)], fill=c(shade))
    if cfg.get('extra') == 'sweater':       # 綁在肩上的灰毛衣
        if view == 'side':
            d.polygon([P(8, 25), P(22, 25), P(22, 28), P(9, 29)], fill=c(SWEATER[0]))
            d.polygon([P(19, 28), P(23, 28), P(22, 34), P(20, 34)], fill=c(SWEATER[1]))
        else:
            d.polygon([P(4, 26), P(26, 26), P(25, 29), P(5, 29)], fill=c(SWEATER[0]))
            d.polygon([P(12, 28), P(18, 28), P(17, 35), P(15, 33), P(13, 35)], fill=c(SWEATER[1]))
    if cfg['bottoms'] != 'skirt':           # 褲頭
        lo = cfg['low'][0]
        if view == 'side':
            d.rectangle([P(9, 41), P(22, 44)], fill=c(lo))
        else:
            d.rectangle([P(6, 41), P(24, 44)], fill=c(lo))
    return outline(L)


def skirt(name, view):
    if CHARS[name]['bottoms'] != 'skirt':
        return None
    col, shade = CHARS[name]['low']
    L = blank()
    d = ImageDraw.Draw(L)
    if view == 'side':
        d.polygon([P(9, 40), P(22, 40), P(25, 50), P(6, 50)], fill=c(col))
        for x in (10, 15, 20):
            d.line([P(x, 42), P(x + (x - 15) // 3, 50)], fill=c(shade))
    else:
        d.polygon([P(6, 40), P(24, 40), P(27, 50), P(3, 50)], fill=c(col))
        for x in (8, 12, 16, 20):
            d.line([P(x, 42), P(x + (x - 15) // 3, 50)], fill=c(shade))
    return outline(L)


# ------------------------------------------------------------ 腿
def leg_points(hip, thigh_deg, shin_deg):
    a, b = math.radians(thigh_deg), math.radians(shin_deg)
    knee = (hip[0] + THIGH * math.sin(a), hip[1] + THIGH * math.cos(a))
    ankle = (knee[0] + SHIN * math.sin(b), knee[1] + SHIN * math.cos(b))
    return knee, ankle


def one_leg(name, d, hip, thigh_deg, shin_deg, dark=False, side=True):
    cfg = CHARS[name]
    lo = cfg['low'][1 if dark else 0]
    knee, ankle = leg_points(hip, thigh_deg, shin_deg)
    if cfg['bottoms'] == 'pants':
        limb(d, [hip, knee, ankle], lo, 6)
    elif cfg['bottoms'] == 'shorts':
        mid = ((hip[0] + knee[0]) / 2, (hip[1] + knee[1]) / 2)
        limb(d, [mid, knee, ankle], SKIN, 4)
        limb(d, [hip, mid], lo, 7)
    else:
        limb(d, [hip, knee, ankle], SKIN, 4)
    if cfg.get('socks') or cfg['bottoms'] == 'skirt':
        limb(d, [(ankle[0], ankle[1] - 2), ankle], WHITE, 4)
    shoe, sole = cfg['shoe']
    x, y = round(ankle[0]), round(ankle[1])
    x0, x1 = (x - 3, x + 5) if side else (x - 3, x + 3)   # 側面鞋尖朝前
    d.rectangle([P(x0, y), P(x1, y + 2)], fill=c(shoe))
    d.rectangle([P(x0, y + 2), P(x1, y + 2)], fill=c(sole))


# 側面腿部姿勢：(前腳大腿, 前腳小腿, 後腳大腿, 後腳小腿) 角度，正值往前（右）
SIDE_LEGS = {
    'walk1': (4, 0, -4, -6),
    'walk2': (18, 4, -16, -26),
    'walk3': (30, 10, -28, -38),
    'jump':  (80, -5, -22, -45),
}


def legs_side(name, pose):
    tf, sf, tb, sb = SIDE_LEGS[pose]
    hip = (15, HIP_Y)
    back, front = blank(), blank()
    one_leg(name, ImageDraw.Draw(back), hip, tb, sb, dark=True)
    one_leg(name, ImageDraw.Draw(front), hip, tf, sf)
    return stack(outline(back), outline(front))


def legs_front(name):
    L = blank()
    d = ImageDraw.Draw(L)
    one_leg(name, d, (11, HIP_Y), 0, 0, side=False)
    one_leg(name, d, (19, HIP_Y), 0, 0, side=False)
    return outline(L)


# ------------------------------------------------------------ 手臂
def sleeve(name):
    pl = CHARS[name].get('plaid')
    return pl[1] if pl else CHARS[name]['top'][0]


def arm(name, pts):
    """肩→肘→手；袖子 5 格粗、手 4x4。"""
    L = blank()
    d = ImageDraw.Draw(L)
    limb(d, pts, sleeve(name), 5)
    x, y = pts[-1]
    d.rectangle([P(x - 2, y - 1), P(x + 1, y + 2)], fill=c(SKIN))
    return outline(L)


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
    d.ellipse([1, 28, 13, 44], fill=c('#b8322a'))                 # 琴身
    d.rectangle([1, 24, 4, 33], fill=c('#b8322a'))                # 上琴角（較長）
    d.rectangle([10, 27, 12, 33], fill=c('#b8322a'))              # 下琴角
    d.rectangle([10, 34, 12, 41], fill=c('#6e1c18'))              # 暗面
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
    d.rectangle([0, 11, 9, 37], fill=c('#2a2a32'))                # 琴身（黑）
    d.rectangle([8, 12, 9, 36], fill=c('#d8323a'))                # 紅色飾條
    im = inner_outline(im, OUT)
    d = ImageDraw.Draw(im)
    d.rectangle([2, 13, 6, 34], fill=c('#f6f6f6'))                # 白鍵
    for y in range(14, 34, 2):
        d.line([2, y, 6, y], fill=c('#b8bcc8'))                   # 鍵縫
    for y in (15, 17, 21, 23, 25, 29, 31):
        d.line([2, y, 3, y], fill=c('#202024'))                   # 黑鍵
    d.point((4, 4), fill=c('#ffd040')); d.point((4, 7), fill=c('#d8323a'))  # 握把上的鈕
    return im, (5, 24)


def inst(piece_anchor, angle, at):
    """直立樂器旋轉 angle 度（正值逆時針、琴頭往左倒）後，讓錨點落在角色座標 at。"""
    piece, anchor = piece_anchor
    w, h = piece.size
    rot = piece.rotate(angle, resample=Image.NEAREST, expand=True)
    t = math.radians(angle)
    vx, vy = anchor[0] + .5 - w / 2, anchor[1] + .5 - h / 2
    rx = vx * math.cos(t) + vy * math.sin(t) + rot.width / 2
    ry = -vx * math.sin(t) + vy * math.cos(t) + rot.height / 2
    L = blank()
    x, y = P(*at)
    L.alpha_composite(rot, (round(x - rx), round(y - ry)))
    return L


def snare_side(at):
    im, d = layer(15, 11)
    d.rectangle([0, 0, 14, 10], fill=c('#f0f0f4'))
    im = inner_outline(im, OUT)
    d = ImageDraw.Draw(im)
    d.line([1, 1, 13, 1], fill=c('#c83030')); d.line([1, 9, 13, 9], fill=c('#c83030'))   # 鼓圈
    for x in (2, 5, 8, 11):
        d.line([x, 2, x, 8], fill=c('#8a90a4'))                   # 張力螺桿
    L = blank()
    L.alpha_composite(im, P(*at))
    return L


def snare_front(at):
    im, d = layer(24, 12)
    d.ellipse([0, 0, 23, 5], fill=c('#e8ecf4'))                   # 鼓面
    d.rectangle([0, 3, 23, 11], fill=c('#f0f0f4'))
    im = inner_outline(im, OUT)
    d = ImageDraw.Draw(im)
    d.line([1, 4, 22, 4], fill=c('#c83030')); d.line([1, 10, 22, 10], fill=c('#9e2626'))
    for x in range(2, 21, 4):
        d.line([x, 5, x + 2, 9], fill=c('#8a90a4'))               # 斜向螺桿
    L = blank()
    L.alpha_composite(im, P(*at))
    return L


def mic(x, y):
    """麥克風：(x, y) 是握柄底端，網罩在上方。"""
    L = blank()
    d = ImageDraw.Draw(L)
    d.rectangle([P(x, y - 4), P(x + 1, y)], fill=c('#24242c'))   # 握柄
    d.rectangle([P(x - 1, y - 8), P(x + 2, y - 5)], fill=c('#c8ccd8'))  # 網罩
    d.point(P(x, y - 7), fill=c('#f4f6fa')); d.point(P(x + 1, y - 6), fill=c('#8a90a4'))
    return outline(L)


def stick(a, b):
    L = blank()
    ImageDraw.Draw(L).line([P(*a), P(*b)], fill=c('#e8c890'), width=2)
    return outline(L)


def strap(a, b, col='#3b2416'):
    L = blank()
    ImageDraw.Draw(L).line([P(*a), P(*b)], fill=c(col), width=2)
    return L


# ------------------------------------------------------------ 姿勢
# 側面手臂（肩→肘→手）；走路時手前後擺
SIDE_ARM = {
    'walk1': [(15, 27), (15, 34), (16, 40)],
    'walk2': [(15, 27), (17, 34), (20, 39)],
    'walk3': [(15, 27), (13, 34), (12, 40)],
}
RAISED = [(15, 27), (22, 27), (25, 19)]   # 跳躍：前面那隻手往前上方舉（在下巴前方，不遮臉）


def side_frame(name, pose):
    kind = CHARS[name]['instrument']
    jump = pose == 'jump'
    back, front, held = None, [], []
    if kind == 'guitar':
        back = inst(acoustic_guitar(), 30 + 10 * jump, (9, 38))
    elif kind == 'bass':
        back = inst(electric_bass(), 24 + 10 * jump, (9, 40))
    elif kind == 'keytar':
        back = inst(keytar(), 52 + 8 * jump, (9, 34))
    if back is not None:
        front.append(strap((20, 26), (10, 41)))
    if kind == 'snare':
        front.append(strap((20, 26), (21, 33), '#8a90a4'))
        front.append(snare_side((18, 33 - jump)))
    pts = RAISED if jump else SIDE_ARM[pose]
    hx, hy = pts[-1]
    if kind == 'mic':
        held.append(mic(hx - 1, hy - 1))
    if kind == 'snare':
        held.append(stick((hx, hy), (hx + 4, hy - 8) if jump else (hx + 7, hy - 5)))
    return stack(back, legs_side(name, pose), skirt(name, 'side'), torso(name, 'side'), head(name),
                 *front, arm(name, pts), *held)


# 正面演奏兩格：每格（畫面左手、畫面右手）的肩→肘→手
PLAY = {
    'guitar': [([(5, 28), (2, 34), (9, 35)], [(25, 28), (29, 33), (26, 32)]),
               ([(5, 28), (2, 36), (9, 40)], [(25, 28), (29, 33), (26, 32)])],
    'bass':   [([(5, 28), (2, 34), (10, 36)], [(25, 28), (30, 32), (27, 30)]),
               ([(5, 28), (2, 36), (12, 39)], [(25, 28), (30, 31), (28, 29)])],
    'keytar': [([(5, 28), (2, 33), (9, 36)], [(25, 28), (29, 32), (28, 34)]),
               ([(5, 28), (4, 34), (15, 36)], [(25, 28), (29, 32), (28, 34)])],
    'snare':  [([(5, 28), (1, 32), (6, 29)], [(25, 28), (28, 34), (22, 37)]),
               ([(5, 28), (2, 34), (8, 37)], [(25, 28), (29, 32), (24, 29)])],
    'mic':    [([(5, 28), (3, 34), (4, 40)], [(25, 28), (28, 33), (18, 27)]),
               ([(5, 28), (0, 21), (0, 15)], [(25, 28), (28, 33), (18, 27)])],
}


def front_frame(name, k):
    kind = CHARS[name]['instrument']
    held, extra = [], []
    if kind == 'guitar':
        held.append(inst(acoustic_guitar(), -70, (9, 38)))
    elif kind == 'bass':
        held.append(inst(electric_bass(), -65, (9, 38)))
    elif kind == 'keytar':
        held.append(inst(keytar(), -80, (13, 37)))
    elif kind == 'snare':
        held.append(snare_front((3, 38)))
    la, ra = PLAY[kind][k]
    if kind == 'snare':   # 舉高的鼓棒朝上、敲下去的碰鼓面
        extra = [stick((6, 29), (9, 20)), stick((22, 37), (17, 39))] if k == 0 else \
                [stick((8, 37), (13, 39)), stick((24, 29), (21, 20))]
    if kind == 'mic':
        extra = [mic(18, 26)]
    return stack(legs_front(name), skirt(name, 'front'), torso(name, 'front'), head(name),
                 *held, arm(name, la), arm(name, ra), *extra)


def render_all(name):
    out = {f'right_{p}': side_frame(name, p) for p in ['walk1', 'walk2', 'walk3', 'jump']}
    out['front_play1'] = front_frame(name, 0)
    out['front_play2'] = front_frame(name, 1)
    for p in ['walk1', 'walk2', 'walk3', 'jump']:
        out[f'left_{p}'] = out[f'right_{p}'].transpose(Image.FLIP_LEFT_RIGHT)
    return out


def preview(rows, scale=4, bg=(200, 220, 240, 255)):
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
                                         'left_walk3', 'front_play1', 'front_play2']])
    (root / 'anchors.json').write_text(json.dumps({
        'size': [CW, CH], 'right': list(FOOT), 'front': list(FOOT), 'left': [CW - 1 - FOOT[0], FOOT[1]],
        'note': '腳底中心（畫格像素座標）'}, ensure_ascii=False, indent=1))
    preview(rows, 3).save(root / '_preview.png')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'characters')
