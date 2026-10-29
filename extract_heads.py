"""從樂團海報（reference/band_poster.webp）擷取六位團員的頭部像素圖。

海報本身是像素畫，一格約 9.2 px（格線不完全整齊）。做法：
GrabCut 去背（補回臉內的洞）→ 每人分成 10 個色群 → 以 6.2 px 為一格，每格取最多的色群。
輸出 heads/<名字>.png（透明底、未加外框；外框由 sprites.py 疊圖時統一加）。
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

CELL = 6.2           # 海報一格約 9.2 px；取樣用較細的 6.2 px，五官才留得住
# 頭部範圍（海報原圖座標，頭置中）；face 是一定要保留的橢圓（中心、半徑，皆為框的比例）；flip=True 表示原圖臉朝畫面左邊，擷取後翻成朝右
HEADS = {
    'davidd':   dict(box=(362, 285, 525, 470)),
    'anderson': dict(box=(500, 130, 660, 300)),
    'freda':    dict(box=(718, 150, 886, 320), face=[(.55, .52, .3, .3)]),
    'susan':    dict(box=(895, 150, 1065, 320)),
    'raphael':  dict(box=(1110, 60, 1275, 240)),
    'jimmy':    dict(box=(1238, 405, 1393, 568), face=[(.42, .55, .3, .3), (.55, .3, .38, .25)], flip=True),
}
COLORS = 10


def cut(img, box, fg_box=None):
    """GrabCut：框內橢圓是「可能前景」，中間較小的橢圓是「確定前景」（臉），其餘是可能背景。"""
    crop = np.array(img.crop(box))
    h, w = crop.shape[:2]
    bgr = cv2.cvtColor(crop, cv2.COLOR_RGB2BGR)
    mask = np.full((h, w), cv2.GC_PR_BGD, np.uint8)
    cv2.ellipse(mask, (w // 2, h // 2), (int(w * .47), int(h * .47)), 0, 0, 360, cv2.GC_PR_FGD, -1)
    cv2.ellipse(mask, (w // 2, int(h * .55)), (int(w * .22), int(h * .2)), 0, 0, 360, cv2.GC_FGD, -1)
    mask[:2], mask[-2:], mask[:, :2], mask[:, -2:] = cv2.GC_BGD, cv2.GC_BGD, cv2.GC_BGD, cv2.GC_BGD
    cv2.grabCut(bgr, mask, None, np.zeros((1, 65)), np.zeros((1, 65)), 8, cv2.GC_INIT_WITH_MASK)
    fg = np.isin(mask, (cv2.GC_FGD, cv2.GC_PR_FGD))
    # GrabCut 偶爾會把半邊臉切掉：臉部橢圓內一律保留
    face = np.zeros((h, w), np.uint8)
    for cx, cy, rx, ry in fg_box or [(.5, .55, .3, .3)]:
        cv2.ellipse(face, (int(w * cx), int(h * cy)), (int(w * rx), int(h * ry)), 0, 0, 360, 1, -1)
    return crop, fg | face.astype(bool)


def largest(m):
    """只留最大的一塊前景（去掉旁邊被一起切進來的樂器、衣領碎片）。"""
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), connectivity=4)
    if n <= 2:
        return m
    return lab == 1 + stats[1:, cv2.CC_STAT_AREA].argmax()


def fill_holes(m):
    """前景遮罩補洞：眼睛、眼鏡、嘴巴這些深色區塊被 GrabCut 當背景時補回來。"""
    h, w = m.shape
    ff = (~m).astype(np.uint8)
    pad = np.pad(ff, 1, constant_values=1)
    flood = pad.copy()
    cv2.floodFill(flood, None, (0, 0), 2)
    outside = flood[1:-1, 1:-1] == 2
    return ~outside


def pixelate(crop, fg):
    """每格取「最多的色群」而非平均，邊界才不會混出中間色。"""
    h, w = fg.shape
    nw, nh = round(w / CELL), round(h / CELL)
    src = cv2.medianBlur(crop, 3).reshape(-1, 3).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    _, labels, centers = cv2.kmeans(src, COLORS, None, crit, 4, cv2.KMEANS_PP_CENTERS)
    labels = labels.reshape(h, w)
    fg = fill_holes(fg)
    idx = np.zeros((nh, nw), int)
    alpha = np.zeros((nh, nw), bool)
    for j in range(nh):
        for i in range(nw):
            y0, y1 = int(j * h / nh), int((j + 1) * h / nh)
            x0, x1 = int(i * w / nw), int((i + 1) * w / nw)
            cell = labels[y0:y1, x0:x1]
            idx[j, i] = np.bincount(cell.ravel(), minlength=COLORS).argmax()
            alpha[j, i] = fg[y0:y1, x0:x1].mean() > .5
    out = np.dstack([centers.astype(np.uint8)[idx], (alpha * 255).astype(np.uint8)])
    im = Image.fromarray(out)
    return im.crop(im.getbbox())


def main(src, outdir):
    img = Image.open(src).convert('RGB')
    out = Path(outdir); out.mkdir(exist_ok=True)
    for name, cfg in HEADS.items():
        crop, fg = cut(img, cfg['box'], cfg.get('face'))
        fg = largest(fg)
        head = pixelate(crop, fg)
        if cfg.get('flip'):
            head = head.transpose(Image.FLIP_LEFT_RIGHT)
        head.save(out / f'{name}.png')
        print(name, head.size)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'reference/band_poster.webp', sys.argv[2] if len(sys.argv) > 2 else 'heads')
