# 注音拼音教學板

網址：https://andice0107.github.io/zhuyin-pinyin-board/

注音符號拼音教學工具，提供三種念法：

- **逐音唸直拼**：每個符號分開唸，再唸整個字音
- **結合韻拼法**：介音＋韻符合成結合韻（帶聲調）一起唸，聲符分開唸
- **唸整個字音**

## 檔案

| 檔案 | 用途 |
|---|---|
| `index.html` | 工具主程式 |
| `syllables.js` | 注音音節 → 示範字對照表（由 `tools/build_table.py` 產生） |
| `readings.json` | 國字 → 注音資料（輸入文字自動帶入注音用，由 `tools/build_table.py` 產生） |
| `voice-pack.json` | 老師的錄音（聲符本音等），網頁開啟時自動載入 |

## 更新錄音

在工具裡錄好音後按「匯出語音包」，用新的 `voice-pack.json` 取代這裡的檔案即可。

## 重新產生示範字表

```bash
python3 tools/build_table.py tsi.csv word.csv syllables.js readings.json
```

`tsi.csv`、`word.csv` 取自 [libchewing-data](https://github.com/chewing/libchewing-data)（LGPL-2.1）。
