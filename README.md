# Real-8bit

台北六景 8-bit 橫向捲軸關卡畫面。

![六關總覽](stages/stages_overview.png)

| 關卡 | 地標 | 角色 |
| --- | --- | --- |
| 1-1 | 台北 101 | Susan |
| 1-2 | 仙跡岩登山入口 | Freda |
| 1-3 | 圓山飯店 | Jimmy |
| 1-4 | 臺北表演藝術中心 | Davidd |
| 1-5 | 臺北流行音樂中心 | Raphael |
| 1-6 | 小油坑橋 | Anderson |

## 網頁遊戲

`game/` 是可以玩的橫向捲軸遊戲（六關、每關一位團員）：← → 移動、空白鍵／↑ 跳躍，
停下來就會轉正面演奏自己的樂器（WebAudio 晶片音），踩走音怪、頂音箱拿金幣，碰到終點旗桿過關。手機有觸控鍵。

```bash
python build_game.py          # 由 scenes.py／sprites.py 產生 game/assets/
cd game && python3 -m http.server 8765   # 開 http://localhost:8765/
```

## 目錄

- `stages/`：六張 1920×1080 關卡畫面與總覽
- `landmarks/`：六個地標的透明底像素圖（576×576）與總表
- `sprites/`：從角色設定表擷取的原生像素角色（六人 × 正面／朝左／背面／朝右，68 格高）
- `characters/<名字>/`：8-bit 角色（帶樂器）：`right_walk1~3`、`right_jump`、`left_*`（鏡像）、`front_play1~2`（正面演奏）；`anchors.json` 記錄腳底中心，`_preview.png` 是總表

## 重新產生

需要 Python 3 與 Pillow、numpy、opencv-python-headless（擷取角色用）。

```bash
pip install pillow numpy opencv-python-headless
python landmarks.py landmarks
python extract_sprites.py reference/character_sheet.webp sprites
python sprites.py characters
python scenes.py stages characters
```

角色直接取自角色設定表 `reference/character_sheet.webp`（`extract_sprites.py`：去背、依角色高度定格寬、每格取眾數色群，不重畫）。
`sprites.py` 在原圖上加樂器與動作：走路三格與跳躍由腿部切開位移而成，朝左用設定表的 LEFT，正面演奏用 FRONT。
樂器：Susan、Freda 麥克風（主唱，正面用麥克風架），Jimmy keytar，Davidd 電 bass，Raphael 木吉他，Anderson 行進小鼓。
