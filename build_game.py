"""輸出網頁遊戲用的素材到 game/assets/。

- bg_<n>.png：各關遠景，橫向 5 倍寬（1920x276，上方多 60 px 天空），遊戲裡以視差捲動（左右、跳高時上下）
- ground_<n>.png：各關地面長條（與遠景同一套 ground() 畫法，加長到整關長度），跟著鏡頭捲動
- brick / block / block_used / coin / note / bignote（路上的大音符）/ enemy_* / goal：關卡物件，皆為 384 場景層的原生像素
- chars/<名字>/*.png：sprites.py 產生的角色畫格
- music/bgm<n>.mp3：關卡背景音樂，從 repo 的 music/ 複製（1、3、5 關 bgm1，2、4 關 bgm2，6 關 bgm3）
用法：python build_game.py
"""
import shutil
from contextlib import contextmanager
from pathlib import Path

from PIL import Image, ImageDraw

import scenes as S
from landmarks import OUT, c, inner_outline

HERE = Path(__file__).parent
ASSETS = HERE / 'game' / 'assets'
LEVEL_W = 1200            # 每關長度（場景基準像素；遊戲中 2 倍 = 2400）
GROUND_TOP = S.GY - 12    # 地面長條從這一列開始（含小油坑的欄杆）
TILES = 5                 # 遠景橫向是原場景的幾倍寬
EXTRA_TOP = 30            # 遠景上方多畫的天空（基準像素），跳高時鏡頭往上才看得到
STYLE = {S.stage_101: 'city', S.stage_hotel: 'park', S.stage_tpac: 'city',
         S.stage_music: 'plaza', S.stage_xianjiyan: 'stone', S.stage_xiaoyoukeng: 'boardwalk',
         S.stage_chifeng: 'alley'}


BACKDROP = ['sky', 'clouds', 'mountains', 'skyline', 'ground', 'railing']   # 跨整個寬度的遠景
STREET = ['building', 'tree', 'lamp', 'scooter', 'signpost', 'silvergrass', 'landmark']   # 固定座標的街景


@contextmanager
def patched(**fns):
    """暫時替換 scenes 裡的函式或常數。"""
    old = {k: getattr(S, k) for k in fns}
    for k, v in fns.items():
        setattr(S, k, v)
    try:
        yield
    finally:
        for k, v in old.items():
            setattr(S, k, v)


def noop(*a, **k):
    return None


def background(fn):
    """5 倍寬遠景：天空、山、天際線、雲橫跨整個寬度；街景（建築、樹、路燈）每 192 格一段，
    前四段不放地標、單數段左右翻轉避免重複感，最後一段是原本的完整場景（終點前看到地標）。"""
    base = S.W
    wide = base * TILES
    clouds = S.clouds

    def many_clouds(cv, items):   # 原本的雲每段重複一次，位置錯開
        clouds(cv, [(x + k * base + (k * 37) % 40 - 20, y + (k * 11) % 9 - 4, s)
                    for k in range(TILES) for (x, y, s) in items])

    cv = S.Canvas(wide, S.H)
    with patched(W=wide, clouds=many_clouds, railing=noop, **{k: noop for k in STREET}):   # 地面也畫，鏡頭上移時遠方地面不會破洞
        fn(cv)
    for k in range(TILES):
        last = k == TILES - 1
        tile = S.Canvas()
        skip = {n: noop for n in BACKDROP}
        if not last:
            skip['landmark'] = noop
        with patched(**skip):
            fn(tile)
        if not last:   # 地標空出來的中段補路燈和樹
            S.lamp(tile, 96 + (k % 2) * 20, lit=fn is S.stage_101)
            S.tree(tile, 120 - (k % 2) * 30, 1 + (k % 2))
        layer = tile.img.transpose(Image.FLIP_LEFT_RIGHT) if k % 2 else tile.img
        cv.img.alpha_composite(layer, (k * S.W, 0))
    # 上方補天空：沿用最上面一列的顏色
    top = cv.img.getpixel((0, 0))
    full = Image.new('RGBA', (wide, S.H + EXTRA_TOP), top)
    full.alpha_composite(cv.img, (0, EXTRA_TOP))
    return full.resize((full.width * 2, full.height * 2), Image.NEAREST)


def ground_strip(fn):
    """整關長度的地面：暫時把 scenes.W 換成關卡長度，沿用同一個 ground() 畫法。"""
    w0 = S.W
    S.W = LEVEL_W
    try:
        cv = S.Canvas(LEVEL_W, S.H)
        S.ground(cv, STYLE[fn])
        if fn is S.stage_xiaoyoukeng:
            S.railing(cv)
    finally:
        S.W = w0
    strip = cv.img.crop((0, GROUND_TOP, LEVEL_W, S.H))
    return strip.resize((strip.width * 2, strip.height * 2), Image.NEAREST)


def sprite(w, h, draw):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw(ImageDraw.Draw(im))
    return im


def block(used=False):
    """音箱方塊：從下面頂會跳出金幣；頂過之後變暗。"""
    def draw(d):
        d.rectangle([0, 0, 15, 15], fill=c('#2a2a34' if not used else '#5a5248'), outline=OUT)
        d.rectangle([2, 2, 13, 13], fill=c('#3c3c4a' if not used else '#6e6458'))
        if not used:
            d.ellipse([4, 4, 11, 11], fill=c('#16161c'), outline=c('#8a8aa0'))
            d.ellipse([6, 6, 9, 9], fill=c('#ffd34d'))
        for x, y in [(2, 2), (13, 2), (2, 13), (13, 13)]:
            d.point((x, y), fill=c('#c8ccd8'))
    return sprite(16, 16, draw)


def enemy(frame):
    """走音怪：紫色降記號形狀的小怪，兩格走路、一格被踩扁。"""
    def draw(d):
        if frame == 'flat':
            d.ellipse([0, 10, 17, 15], fill=c('#8a4fc8'), outline=OUT)
            d.line([5, 12, 7, 12], fill=OUT); d.line([10, 12, 12, 12], fill=OUT)
            return
        dy = 0 if frame == 'a' else 1
        d.rectangle([2, 0 + dy, 4, 9], fill=c('#5a2e90'), outline=OUT)            # ♭ 的直桿
        d.ellipse([1, 4 + dy, 17, 15], fill=c('#8a4fc8'), outline=OUT)
        d.ellipse([3, 6 + dy, 8, 9 + dy], fill=c('#b88ae8'))
        d.rectangle([7, 7 + dy, 8, 10 + dy], fill=c('#ffffff')); d.rectangle([12, 7 + dy, 13, 10 + dy], fill=c('#ffffff'))
        d.point((8, 9 + dy), fill=OUT); d.point((13, 9 + dy), fill=OUT)
        d.line([6, 6 + dy, 9, 7 + dy], fill=OUT); d.line([11, 7 + dy, 14, 6 + dy], fill=OUT)   # 生氣的眉毛
        fx = (3, 12) if frame == 'a' else (5, 10)
        for x in fx:
            d.rectangle([x, 15, x + 2, 15], fill=OUT)
    return sprite(18, 16, draw)


def big_note():
    """路上的大音符（♫，取代金幣）：金色、深藍外框。"""
    def draw(d):
        d.polygon([(6, 3), (17, 0), (17, 4), (6, 7)], fill=c('#ffd34d'))           # 符桁
        d.rectangle([6, 3, 8, 18], fill=c('#ffd34d')); d.rectangle([15, 1, 17, 16], fill=c('#ffd34d'))  # 符桿
        d.ellipse([0, 14, 8, 21], fill=c('#ffd34d')); d.ellipse([9, 12, 17, 19], fill=c('#ffd34d'))     # 符頭
    im = inner_outline(sprite(18, 22, draw), OUT)
    d = ImageDraw.Draw(im)
    d.point((3, 16), fill=c('#fff3b0')); d.point((12, 14), fill=c('#fff3b0')); d.line([8, 4, 15, 2], fill=c('#fff3b0'))
    return im


def goal():
    """終點：麥克風架造型的旗桿，旗子寫 REAL。"""
    def draw(d):
        d.rectangle([20, 8, 22, 95], fill=c('#8a90a4'), outline=OUT)
        d.ellipse([16, 0, 26, 10], fill=c('#c8ccd8'), outline=OUT)
        d.point((19, 3), fill=c('#ffffff'))
        d.polygon([(23, 12), (46, 18), (23, 26)], fill=c('#ff4f6d'), outline=OUT)
        d.line([25, 18, 38, 18], fill=c('#ffd0d8'))
        d.rectangle([12, 90, 30, 95], fill=c('#4a4e5a'), outline=OUT)
    return sprite(48, 96, draw)


def main():
    if ASSETS.exists():
        shutil.rmtree(ASSETS)
    ASSETS.mkdir(parents=True)
    for i, st in enumerate(S.STAGES):
        fn = st[4]
        background(fn).save(ASSETS / f'bg_{i + 1}.png')
        ground_strip(fn).save(ASSETS / f'ground_{i + 1}.png')
    bk = sprite(16, 16, lambda d: S.bricks(d, 0, 0, 1))
    bk.save(ASSETS / 'brick.png')
    block().save(ASSETS / 'block.png')
    block(True).save(ASSETS / 'block_used.png')
    sprite(8, 10, lambda d: S.coin(d, 0, 0)).save(ASSETS / 'coin.png')
    sprite(11, 12, lambda d: S.note(d, 0, 0)).save(ASSETS / 'note.png')
    big_note().save(ASSETS / 'bignote.png')
    for f in ('a', 'b', 'flat'):
        enemy(f).save(ASSETS / f'enemy_{f}.png')
    goal().save(ASSETS / 'goal.png')
    shutil.copytree(HERE / 'characters', ASSETS / 'chars', ignore=shutil.ignore_patterns('_preview.png', '*.json'))
    shutil.copytree(HERE / 'music', ASSETS / 'music')
    print('assets →', ASSETS, len(list(ASSETS.rglob('*.png'))), 'png')


if __name__ == '__main__':
    main()
