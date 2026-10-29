"""輸出網頁遊戲用的素材到 game/assets/。

- bg_<n>.png：各關遠景（scenes.py 的場景，不含角色、收集物、HUD），384x216，遊戲裡固定不捲動
- ground_<n>.png：各關地面長條（與遠景同一套 ground() 畫法，加長到整關長度），跟著鏡頭捲動
- brick / block / block_used / coin / note / enemy_* / goal：關卡物件，皆為 384 場景層的原生像素
- chars/<名字>/*.png：sprites.py 產生的角色畫格
用法：python build_game.py
"""
import shutil
from pathlib import Path

from PIL import Image, ImageDraw

import scenes as S
from landmarks import OUT, c, inner_outline

HERE = Path(__file__).parent
ASSETS = HERE / 'game' / 'assets'
LEVEL_W = 1200            # 每關長度（場景基準像素；遊戲中 2 倍 = 2400）
GROUND_TOP = S.GY - 12    # 地面長條從這一列開始（含小油坑的欄杆）
STYLE = {S.stage_101: 'city', S.stage_hotel: 'park', S.stage_tpac: 'city',
         S.stage_music: 'plaza', S.stage_xianjiyan: 'stone', S.stage_xiaoyoukeng: 'boardwalk'}


def background(fn):
    """遠景：照原本的場景畫，但小油坑的欄杆改由地面長條負責（否則捲動時會有兩層欄杆）。"""
    railing = S.railing
    S.railing = lambda *a, **k: None
    try:
        cv = S.Canvas()
        fn(cv)
    finally:
        S.railing = railing
    return cv.img.resize((S.W * 2, S.H * 2), Image.NEAREST)


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
    for f in ('a', 'b', 'flat'):
        enemy(f).save(ASSETS / f'enemy_{f}.png')
    goal().save(ASSETS / 'goal.png')
    shutil.copytree(HERE / 'characters', ASSETS / 'chars', ignore=shutil.ignore_patterns('_preview.png', '*.json'))
    print('assets →', ASSETS, len(list(ASSETS.rglob('*.png'))), 'png')


if __name__ == '__main__':
    main()
