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
- `characters/`：從角色設定表擷取的朝右角色（56 px 高）

## 重新產生

需要 Python 3 與 Pillow、numpy。

```bash
pip install pillow numpy
python landmarks.py landmarks
python scenes.py stages characters
```

`chars.py` 從角色設定表（原圖不在此 repo）擷取 `characters/`：

```bash
python chars.py <角色設定表.webp> characters
```
