# Real-8bit

台北六景 8-bit 橫向捲軸關卡畫面。

![六關總覽](stages/stages_overview.png)

| 關卡 | 地標 | 角色 |
| --- | --- | --- |
| 1-1 | 台北 101 | Susan |
| 1-2 | 圓山飯店 | Jimmy |
| 1-3 | 臺北表演藝術中心 | Davidd |
| 1-4 | 臺北流行音樂中心 | Raphael |
| 1-5 | 仙跡岩登山入口 | Freda |
| 1-6 | 小油坑橋 | Anderson |

## 目錄

- `stages/`：六張 1920×1080 關卡畫面與總覽
- `landmarks/`：六個地標的透明底像素圖（576×576）與總表
- `characters/<名字>/`：手繪 8-bit 角色（帶樂器）：`right_walk1~3`、`right_jump`、`left_*`（鏡像）、`front_play1~2`（正面演奏）；`anchors.json` 記錄腳底中心，`_preview.png` 是總表

## 重新產生

需要 Python 3 與 Pillow、numpy。

```bash
pip install pillow numpy
python landmarks.py landmarks
python sprites.py characters
python scenes.py stages characters
```

角色由 `sprites.py` 逐格手繪（18×32 邏輯像素，與地標同一個像素格，場景中放大 2 倍）：
樂器 Susan、Freda 麥克風（主唱），Jimmy keytar，Davidd 電 bass，Raphael 木吉他，Anderson 行進小鼓。
