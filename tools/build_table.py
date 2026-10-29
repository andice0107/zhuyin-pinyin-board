"""從新酷音詞庫 (libchewing-data, LGPL-2.1) 產生「注音音節 → 代表字」對照表。

用法：python3 build_table.py <tsi.csv> <word.csv> <輸出 syllables.js> [<輸出 readings.json>]

挑字原則：
- 只用單字條目，依使用頻率排序。
- 這個字的「主要讀音」必須就是該音節（該讀音頻率佔此字總頻率 >= DOMINANT），
  避免破音字被語音引擎念成別的音。
- 排除「一」「不」（會變調）。
每個音節保留最多 MAX_CANDIDATES 個候選字，工具裡可以「換一個字」。
"""
import csv
import json
import sys
from collections import defaultdict

DOMINANT = 0.85
MAX_CANDIDATES = 4
MIN_FREQ = 50
EXCLUDE = set('一不儿')
# 不適合在兒童教材中出現的字
EXCLUDE |= set('屌屄肏婊姦淫嫖妓娼鴇肛')
TONES = 'ˊˇˋ˙'
# 第二個以後的候選字至少要有這個頻率，避免冷僻字
ALT_MIN_FREQ = 300
# 輕聲單字幾乎都是破音字，改用人工挑選、單獨念時語音引擎多半念輕聲的字
MANUAL = {
    'ㄇㄚ˙': '嗎嘛', 'ㄋㄜ˙': '呢', 'ㄅㄚ˙': '吧', 'ㄌㄚ˙': '啦',
    'ㄉㄜ˙': '的', 'ㄌㄜ˙': '了', 'ㄚ˙': '啊', 'ㄧㄚ˙': '呀',
    'ㄇㄣ˙': '們', 'ㄓㄜ˙': '著',
    # 結合韻一聲：詞庫裡只有冷僻字或各半的破音字，人工指定
    'ㄧㄝ': '噎', 'ㄩㄣ': '暈',
    # 依頻率挑到冷僻字的音節，換成學生較熟悉、且讀音單純的常用字
    'ㄔㄨㄤˋ': '創', 'ㄌㄧㄠˇ': '瞭', 'ㄎㄨㄟˋ': '愧潰饋', 'ㄐㄧㄡ': '揪鳩',
    'ㄉㄧㄢ': '顛癲', 'ㄎㄨㄤ': '筐', 'ㄈㄣˊ': '墳焚', 'ㄑㄧㄠˋ': '俏',
    'ㄌㄧㄣˋ': '吝', 'ㄔㄢ': '攙摻', 'ㄆㄥ': '烹', 'ㄔㄨㄛˋ': '綽',
    'ㄆㄠˊ': '袍', 'ㄘㄨㄛ': '搓', 'ㄌㄨㄢˊ': '巒', 'ㄙㄨㄥˇ': '聳',
    'ㄇㄤˇ': '蟒莽', 'ㄎㄨㄣˇ': '捆', 'ㄓㄨㄣ': '諄', 'ㄕㄜ': '奢賒',
    'ㄠˇ': '襖', 'ㄍㄚˊ': '軋', 'ㄆㄧㄠˊ': '瓢', 'ㄌㄧㄣˇ': '凜',
    'ㄊㄨㄟˊ': '頹', 'ㄙㄤˇ': '嗓', 'ㄎㄡ': '摳', 'ㄙㄡˇ': '叟',
    'ㄕㄨㄣˇ': '吮', 'ㄊㄨㄢ': '湍', 'ㄅㄛˇ': '跛', 'ㄏㄨㄥˋ': '鬨',
    'ㄋㄧㄢˇ': '捻', 'ㄇㄧㄥˇ': '茗酩', 'ㄅㄧㄥˇ': '餅丙炳秉', 'ㄆㄨˊ': '葡菩',
    'ㄏㄨㄥ': '轟烘', 'ㄖㄤˊ': '瓤', 'ㄅㄧㄣ': '賓濱', 'ㄑㄩˊ': '渠',
    'ㄔㄨㄟˊ': '垂錘槌', 'ㄎㄨㄚ': '誇夸', 'ㄅㄧㄝˇ': '癟', 'ㄏㄢ': '酣鼾',
    'ㄑㄧㄣˋ': '沁', 'ㄙㄨㄟˇ': '髓', 'ㄅㄧㄣˋ': '鬢殯', 'ㄠˊ': '遨',
}


def load(path):
    rows = []
    with open(path, encoding='utf-8') as f:
        for row in csv.reader(f):
            if not row or row[0].startswith('#') or len(row) < 3:
                continue
            word, freq, phones = row[0], row[1], row[2]
            if len(word) != 1 or ' ' in phones.strip():
                continue
            rows.append((word, int(freq or 0), phones.strip()))
    return rows


def main(tsi_path, word_path, out_path):
    freq = defaultdict(lambda: defaultdict(int))
    for ch, f, ph in load(tsi_path):
        freq[ch][ph] += f
    # word.csv 只用來補齊「所有可能讀音」(頻率 0)，讓破音字不會被誤判為單音字
    all_phones = set()
    for ch, _, ph in load(word_path):
        freq[ch][ph] += 0
        all_phones.add(ph)

    table = defaultdict(list)
    for ch, readings in freq.items():
        if ch in EXCLUDE or not ('一' <= ch <= '鿿'):
            continue
        total = sum(readings.values())
        if total < MIN_FREQ:
            continue
        for ph, f in readings.items():
            if f / total >= DOMINANT:
                table[ph].append((f, ch))

    out = {}
    for ph, items in table.items():
        if not ph or ph[0] in TONES:
            continue
        items.sort(reverse=True)
        picked = [items[0]] + [it for it in items[1:] if it[0] >= ALT_MIN_FREQ]
        out[ph] = ''.join(ch for _, ch in picked[:MAX_CANDIDATES])
    for ph, chars in MANUAL.items():
        out[ph] = chars

    keys = sorted(out)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('// 自動產生：tools/build_table.py（資料來源：新酷音 libchewing-data，LGPL-2.1）\n')
        f.write('// 鍵：注音音節（一聲不標調號），值：代表字候選（第一個為預設）\n')
        f.write('const SYLLABLE_CHARS = ')
        json.dump({k: out[k] for k in keys}, f, ensure_ascii=False, separators=(',', ':'))
        f.write(';\n')
        # 詞庫中出現過的所有音節（含聲調），用來判斷組合是否為國語中存在的音
        valid = sorted({ph for ph in all_phones if ph and ph[0] not in TONES})
        f.write('// 國語中存在的所有音節（含聲調）\n')
        f.write('const VALID_SYLLABLES = new Set(')
        json.dump(valid, f, ensure_ascii=False, separators=(',', ':'))
        f.write(');\n')
    print(f'{len(out)} syllables written to {out_path}', file=sys.stderr)


# 常用詞的標準讀音（詞庫沒有標輕聲或讀音不一的，依教育部國語辭典）
PHRASE_MANUAL = {
    '什麼': 'ㄕㄣˊ ㄇㄜ˙', '衣服': 'ㄧ ㄈㄨ˙', '朋友': 'ㄆㄥˊ ㄧㄡ˙', '時候': 'ㄕˊ ㄏㄡ˙',
    '漂亮': 'ㄆㄧㄠˋ ㄌㄧㄤ˙', '先生': 'ㄒㄧㄢ ㄕㄥ˙', '爺爺': 'ㄧㄝˊ ㄧㄝ˙', '奶奶': 'ㄋㄞˇ ㄋㄞ˙',
    '叔叔': 'ㄕㄨˊ ㄕㄨ˙', '伯伯': 'ㄅㄛˊ ㄅㄛ˙', '弟弟': 'ㄉㄧˋ ㄉㄧ˙', '姐姐': 'ㄐㄧㄝˇ ㄐㄧㄝ˙',
    '寶寶': 'ㄅㄠˇ ㄅㄠ˙',
}


def build_readings(tsi_path, out_path):
    """產生「國字 → 注音」資料，給「輸入文字自動帶入注音」使用。

    c：每個字最常用的讀音，依讀音分組 {注音: 字串}
    p：讀音和逐字預設讀音不同的詞（破音字、輕聲），格式「詞:注音 注音|…」
    """
    char_freq = defaultdict(lambda: defaultdict(int))
    phrases = defaultdict(dict)
    with open(tsi_path, encoding='utf-8') as f:
        for row in csv.reader(f):
            if not row or row[0].startswith('#') or len(row) < 3:
                continue
            word, freq, phones = row[0], int(row[1] or 0), row[2].split()
            if len(word) == 1 and len(phones) == 1:
                char_freq[word][phones[0]] += freq
            elif 2 <= len(word) <= 4 and len(phones) == len(word):
                reading = ' '.join(phones)
                phrases[word][reading] = max(freq, phrases[word].get(reading, 0))

    default = {ch: max(r.items(), key=lambda x: x[1])[0]
               for ch, r in char_freq.items()
               if sum(r.values()) >= 1 and '一' <= ch <= '鿿'}
    by_reading = defaultdict(str)
    for ch, ph in sorted(default.items()):
        by_reading[ph] += ch

    exceptions = []
    for word, readings in phrases.items():
        # 頻率相同時，選標了輕聲的讀法（課本寫法，如 媽媽 ㄇㄚ ˙ㄇㄚ）
        best, f = max(readings.items(), key=lambda x: (x[1], x[0].count('˙')))
        best = PHRASE_MANUAL.get(word, best)
        if f < 1 or any(ch not in default for ch in word):
            continue
        if best != ' '.join(default[ch] for ch in word):
            exceptions.append(f'{word}:{best}')
    for word, best in PHRASE_MANUAL.items():
        if word not in phrases:
            exceptions.append(f'{word}:{best}')

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({'c': by_reading, 'p': '|'.join(sorted(exceptions))}, f,
                  ensure_ascii=False, separators=(',', ':'))
    print(f'{len(default)} chars, {len(exceptions)} phrases written to {out_path}', file=sys.stderr)


if __name__ == '__main__':
    main(*sys.argv[1:4])
    if len(sys.argv) > 4:
        build_readings(sys.argv[1], sys.argv[4])
