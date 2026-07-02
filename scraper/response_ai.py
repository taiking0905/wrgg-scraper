from google import genai
import os
import csv
import json
from dotenv import load_dotenv
from config import DATA_DIR

# .envファイルを読み込む
load_dotenv()
api_key = os.getenv('GEMINI_API')

DIFF_PATH = os.path.join(DATA_DIR, 'diff_input.json')
OUTPUT_CSV = os.path.join(DATA_DIR, 'output_ai.csv')
OUTPUT_JSON = os.path.join(DATA_DIR, 'output_ai.json')

CHAMPION_PATH= os.path.join(DATA_DIR, '..', 'champions.json')

MAX_RETRY = 5
retry_count = 0
success = False

client = genai.Client(api_key=api_key)

# 入力データ読み込み
with open(DIFF_PATH, "r", encoding="utf-8") as f:
    diff = f.read()

#  英語を日本語に応急処置
with open(CHAMPION_PATH, "r", encoding="utf-8") as f:
    champions_data = json.load(f)

# id → name_ja 辞書作成
id_to_ja = {
    champ["id"].strip().lower(): champ["name_ja"]
    for champ in champions_data
}

# Geminiプロンプト
prompt = f"""
あなたはワイルドリフトの統計アナリストです。
以下に最新パッチ差分データ（DIFF）を渡します。
scoreが大きいものを15件だけ抽出してください。


【分析条件】
- 同一チャンピオン・同一ランク内のみ比較
- 上昇・下降トレンドともに重要
- reason には trend の情報（win↑/↓ pick↑/↓ ban↑/↓）を使用
- 数字は勝手に補完せず、trend とレーン/ランクだけで記載
- score は分析にのみ使用、出力に表示しない
- reason には「選定理由（該当ランク）」と「他ランク帯やレーンとの比較」を必ず含める

【絶対遵守ルール】
1. 出力は必ず15件
2. CSV形式
3. ヘッダーは "ranking,champion,reason"
4. ダブルクォートで囲む
5. CSV以外の文章は書かない
6. 1～15の番号を振る

【出力例】
"ranking","champion","reason"
【出力例】
"ranking","champion","reason"
"1","名前","laneのrankでwin↑ pick↑ ban↑。TOPレーンでは、～"
"2","名前","laneのrankでwin↓ pick↓ ban↓。チャレンジャー帯では、～"

【reason 記載ルール】
- 1文目：このランク・レーンで選ばれた理由（trend を使用）
- 2文目：他ランク帯との比較（相対的な傾向のみ）

【データ】
DIFF:
{diff}

"""

while not success and retry_count < MAX_RETRY:
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config = {
                "max_output_tokens": 2000,
                "temperature": 0,  # フォーマット厳守
                "top_p": 0,
                "candidate_count": 1
            }
        )
        raw = response.text.strip()

        # 不要な ```csv などを削除
        if raw.startswith("```csv"):
            raw = raw[len("```csv"):].lstrip()
        if raw.endswith("```"):
            raw = raw[:-3].rstrip()

        # CSV → Dict に変換して行数チェック
        reader = csv.DictReader(raw.splitlines())
        rows = list(reader)

        # フォーマットチェック
        if reader.fieldnames != ["ranking","champion","reason"]:
            raise ValueError("CSV ヘッダーが不正")

        # 件数チェック
        if len(rows) != 15:
            raise ValueError(f"件数が不正: {len(rows)} 件")

        # 成功
        success = True

    except Exception as e:
        print("リクエスト失敗、再試行します:", e)
        retry_count += 1

if not success:
    raise RuntimeError("最大リトライ回数に達しました。Gemini から正しい CSV を取得できませんでした")

# この raw をそのまま CSV として保存
with open(OUTPUT_CSV, 'w', encoding='utf-8') as f:
    f.write(raw)

print("CSV 保存完了:", OUTPUT_CSV)

# CSV → JSON 化
parsed = []
with open(OUTPUT_CSV, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        champ_name = row["champion"].strip()
        champ_key = champ_name.lower()

        # 🔥 ここが応急処置
        if champ_key in id_to_ja:
            champ_name = id_to_ja[champ_key]

        parsed.append({
            "ranking": row["ranking"].strip(),
            "champion": champ_name,
            "reason": row["reason"].strip()
        })

# JSON 保存
with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(parsed, f, ensure_ascii=False, indent=2)

print("JSON 化完了:", OUTPUT_JSON)
