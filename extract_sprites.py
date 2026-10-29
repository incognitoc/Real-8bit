"""從角色設定表（reference/character_sheet.webp，四面 × 六人）擷取原生像素格的角色圖。

設定表本身是像素畫，一格約 4.3 px，但格線有些微漂移。做法：
1. 每一格角色先去背：從邊框往內 flood fill 淺色背景，角色的深色外框會擋住。
2. 格寬 = 角色像素高 ÷ 68（四面在設定表上大小不一，這樣輸出一樣高）；起點找格內顏色變異最小的。
3. 每人用 k-means 分成 COLORS 個色群；每一格取「出現最多的色群」而不是平均，邊緣才不會混出中間色。
輸出 sprites/<名字>_<front|left|back|right>.png（透明底、68 格高）。
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

COLS = [(88, 287), (290, 483), (486, 673), (676, 865), (868, 1063), (1066, 1251)]
NAMES = ['davidd', 'anderson', 'freda', 'susan', 'raphael', 'jimmy']
ROWS = {'front': (57, 381), 'left': (385, 696), 'back': (700, 981), 'right': (984, 1251)}
COLORS = 18
HEIGHT = 68          # 每張輸出都是 68 格高：格寬 = 該圖角色的像素高 ÷ 68（設定表各列畫的大小不一）


def background(crop):
    """淺色且和邊框相連的區域 = 背景。"""
    light = (crop.min(axis=2) > 200)
    h, w = light.shape
    mask = np.zeros((h + 2, w + 2), np.uint8)
    seed = light.astype(np.uint8)
    flood = seed.copy()
    for x, y in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]:
        if flood[y, x] == 1:
            cv2.floodFill(flood, mask, (x, y), 2)
    return flood == 2


def fit_grid(crop, fg):
    """格寬由角色高度決定；只找起點，讓每格內的顏色變異最小。"""
    a = crop.astype(float)
    rows = np.nonzero(fg.any(axis=1))[0]
    best = None
    for s in [(rows[-1] - rows[0] + 1) / HEIGHT]:
        for px in np.arange(0, s, 1.0):
            for py in np.arange(0, s, 1.0):
                nx, ny = int((a.shape[1] - px) // s), int((a.shape[0] - py) // s)
                xs, ys = px + np.arange(nx) * s, py + np.arange(ny) * s
                samples = []
                for o in (.25, .5, .75):
                    for q in (.25, .5, .75):
                        samples.append(a[(ys + o * s).astype(int)][:, (xs + q * s).astype(int)])
                cell_fg = fg[(ys + .5 * s).astype(int)][:, (xs + .5 * s).astype(int)]
                v = np.stack(samples).std(0).mean(-1)[cell_fg].mean()
                if best is None or v < best[0]:
                    best = (v, s, px, py)
    return best[1:]


def sample(crop, fg, s, px, py):
    h, w = fg.shape
    pix = crop[fg].reshape(-1, 3).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.5)
    _, lab, centers = cv2.kmeans(pix, COLORS, None, crit, 4, cv2.KMEANS_PP_CENTERS)
    labels = np.full((h, w), -1, int)
    labels[fg] = lab.ravel()
    nx, ny = int((w - px) // s), int((h - py) // s)
    out = np.zeros((ny, nx, 4), np.uint8)
    for j in range(ny):
        for i in range(nx):
            y0, x0 = int(py + j * s), int(px + i * s)
            cell = labels[y0:int(py + (j + 1) * s), x0:int(px + (i + 1) * s)]
            k = cell.ravel()
            if (k >= 0).mean() < .5:
                continue
            k = k[k >= 0]
            out[j, i, :3] = centers[np.bincount(k, minlength=COLORS).argmax()]
            out[j, i, 3] = 255
    im = Image.fromarray(out)
    return im.crop(im.getbbox())


def main(src, outdir):
    sheet = np.array(Image.open(src).convert('RGB'))
    out = Path(outdir); out.mkdir(exist_ok=True)
    for name, (x0, x1) in zip(NAMES, COLS):
        for view, (y0, y1) in ROWS.items():
            crop = sheet[y0 + 3:y1 - 3, x0 + 3:x1 - 3]
            fg = ~background(crop)
            s, px, py = fit_grid(crop, fg)
            im = sample(crop, fg, s, px, py)
            im.save(out / f'{name}_{view}.png')
            print(f'{name:9s}{view:6s} cell={s:.2f} size={im.size}')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'reference/character_sheet.webp',
         sys.argv[2] if len(sys.argv) > 2 else 'sprites')
