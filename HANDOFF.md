# Real-8bit 交接（2026-10-29）

真的樂團六位團員走過台北六景的 8-bit 橫向捲軸遊戲。這份文件記錄目前做到哪、素材怎麼產生、試過哪些行不通的路，以及接下來可以做什麼。

- GitHub：https://github.com/incognitoc/Real-8bit（`main`）
- 線上試玩（私人，需由擁有者從 Share 分享）：https://claude.ai/artifact/RdjNiTYXVefMQ5N72ZG4U7

## 目前狀態

| 項目 | 狀態 |
| --- | --- |
| 六關靜態關卡畫面（`stages/`） | 完成，已換成新角色 |
| 角色：六人四面原生像素圖（`sprites/`） | 完成，直接從角色設定表擷取 |
| 角色動作與樂器（`characters/`） | 完成：朝右／朝左走路三格、跳躍、正面演奏兩格 |
| 網頁遊戲（`game/`） | 可玩：六關、金幣、音箱方塊、走音怪、終點、停下來演奏、晶片音、觸控鍵 |

團員與樂器：

| 關卡 | 地標 | 團員 | 樂器 |
| --- | --- | --- | --- |
| 1-1 | 台北 101 | Susan | 麥克風（主唱） |
| 1-2 | 圓山飯店 | Jimmy | keytar |
| 1-3 | 臺北表演藝術中心 | Davidd | 電 bass |
| 1-4 | 臺北流行音樂中心 | Raphael | 木吉他 |
| 1-5 | 仙跡岩登山入口 | Freda | 麥克風（主唱） |
| 1-6 | 小油坑橋 | Anderson | 行進小鼓 |

## 素材流程

```
reference/character_sheet.webp ──extract_sprites.py──▶ sprites/<名字>_<front|left|back|right>.png
                                                            │
                                                        sprites.py（加樂器、動作）
                                                            ▼
landmarks.py ──▶ landmarks/          characters/<名字>/<畫格>.png
        │                                   │
        └──────── scenes.py ◀───────────────┤──▶ stages/（六張靜態關卡圖）
                     │                      │
                     └── build_game.py ◀────┘──▶ game/assets/ ──▶ game/index.html
```

重新產生全部（需要 Python 3、Pillow、numpy、opencv-python-headless）：

```bash
pip install pillow numpy opencv-python-headless
python landmarks.py landmarks
python extract_sprites.py reference/character_sheet.webp sprites
python sprites.py characters
python scenes.py stages characters
python build_game.py
cd game && python3 -m http.server 8765    # 開 http://localhost:8765/
```

### 各檔案負責什麼

- `extract_sprites.py`：設定表本身是像素畫（一格約 4.3 px）。去白背景 → 格寬 = 角色像素高 ÷ 68（設定表四列畫的大小不一，這樣輸出都 68 格高）→ 每格取 k-means 色群的**眾數**而不是平均，邊緣才不會糊。
- `sprites.py`：不重畫人物，在原圖上加東西。
  - 走路：腰以下（第 50 列起）依中線切成前後腳，各自位移成三格；朝右用 RIGHT、朝左用 LEFT 原圖。
  - 跳躍：前腳往前上抬、後腳往後收，背上樂器多轉 10 度。
  - 樂器：吉他／bass／keytar 背在背後並畫背帶；小鼓掛胸前加鼓棒；主唱側面手持麥克風，正面用麥克風架。
  - 正面演奏：FRONT 原圖 + 樂器擺在雙手位置；第 2 格把畫面左手往上移 3 格、上半身下沉 1 格。
  - 所有畫格 84x100，腳底中心固定在 (42, 92)（`characters/anchors.json`）。
- `scenes.py`：六關場景（192x108 基準 → 2 倍場景層 384x216 → 5 倍輸出 1920x1080）與 HUD。角色 1:1 貼在 2 倍場景層。
- `build_game.py`：輸出遊戲素材。遠景是 `scenes.py` 場景的 5 倍寬版（1920x276）：天空、山、天際線、雲與遠方地面橫跨全寬，街景每 192 格一段（單數段左右翻轉），最後一段是原本含地標的完整場景，上方多 60 px 天空；地面長條是把 `scenes.W` 暫時換成關卡長度，沿用同一個 `ground()`。
- `game/index.html`：單一檔案，沒有外部函式庫（只載 Google Fonts）。

### 遊戲重點參數（`game/index.html` 開頭）

- 畫布 384x216，整數倍（大螢幕 0.5 級距）放大；關卡長 2400 px。
- `GRAV 0.42`、`JUMP -9.2`（約 100 px 高）、`MAXV 2.5`；碰撞框 16x56。
- 懸空平台底部必須高於地面 56 px 以上，否則角色走不過去（`makeLevel()` 的平台都放在 `gy - 88` 以上）。
- 關卡由 `makeLevel(si)` 以固定種子產生（樣式：金幣弧線、磚塊平台、走音怪、階梯、高低平台）；1-1、1-2 不出現第二種怪的樣式，1-4 起階梯後多一隻怪。
- 鏡頭：遠景左右視差 0.76、上下 0.5；跳高或站上高台時鏡頭最多往上 70 px。
- 路上與頂出來的都是大音符（♫）；每塊磚／音箱頂一次出一個音符，音效是 do-mi-sol 琶音，每頂一次起音往上一級。
- 停下來 28 格（約半秒）轉正面演奏，`Audio.riff(樂器)` 疊上該樂器的晶片音；伴奏是 C–Am–F–G、120 BPM。
- 時間每 40 格減 1（約 3 分 20 秒）。

## 試過、行不通的路（不要再走）

1. **把設定表直接縮圖再壓 20 色**（最早的 `chars.py`）：五官、邊緣糊成一團，不銳利。
2. **程式逐格手繪角色**（ASCII 像素圖 + 色盤）：銳利，但不像本人。
3. **頭取自樂團海報、身體程式畫**：海報上的腿都被遮住或坐著，只能取頭；GrabCut 去背不穩，最後仍不像。

結論：**像本人 + 銳利 = 從設定表按原生格取眾數色**（目前做法）。動作一律在原圖上位移或疊加，不重畫人物。

## 已知問題與限制

- 角色 68 格高，在 216 高的畫面裡約佔 1/3，比磚塊（16 px）大很多，比例偏大頭。
- 走路是腿部位移，接縫偶爾有 1 格斷口；正面演奏的手不是真的重擺姿勢，比較像「拿著」樂器。
- 只在瀏覽器實測過 1-1 過關、1-6 GAME OVER、停下演奏、手機直立版面；六關沒有全部從頭玩到尾，聲音沒有實際試聽。
- `reference/band_poster.webp`（樂團海報）目前沒有程式使用，留作參考。
- `characters/` 與 `game/assets/chars/` 是同一份畫格的兩個副本；改角色後要重跑 `build_game.py`。

## 接下來可以做

- 角色或關卡比例：把場景層放大（例如 3 倍）讓角色相對變小，或縮減角色到約 48 格高（需重新擷取，不能非整數縮放）。
- 更多畫格：從設定表 BACK 列做「往畫面深處走」或過關時轉身。
- 關卡手工設計取代亂數產生，加入坑洞、移動平台。
- 全員集合的最終關（六人同台演奏，六種樂器音軌同時開）。
- 線上版更新：改完 `game/` 後重新發布同一個 artifact，連結不變。
