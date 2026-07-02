import os
import json
from config import DATA_DIR

CHAMPION_DIR = os.path.join(DATA_DIR, 'champion_data')
OUTPUT_DIR = os.path.join(DATA_DIR, 'AI')
os.makedirs(OUTPUT_DIR, exist_ok=True)

threshold_win = 2.0  # win/pick/ban の差分閾値(%)
threshold = 3.0
diff_input = {}

rank_weight = {
    "Master": 8,
    "Diamond": 6,
    "Challenger": 3,
    "Legendary_rank": 1,
    "Emerald": 1
}

for file_name in os.listdir(CHAMPION_DIR):
    if not file_name.endswith('.json'):
        continue

    file_path = os.path.join(CHAMPION_DIR, file_name)
    with open(file_path, 'r', encoding='utf-8') as f:
        champ_data = json.load(f)

    if 'patches' not in champ_data or len(champ_data['patches']) < 2:
        continue

    patches = sorted(champ_data['patches'], key=lambda x: x['updatetime'])
    prev_patch = patches[-2]
    latest_patch = patches[-1]

    champ_id = champ_data.get("id", file_name.replace('.json',''))
    champ_name_ja = champ_data.get("name_ja", champ_id)  # 日本語名

    prev_dict = {(e["lane"], e["rank"]): e for e in prev_patch["data"]}
    champ_diff = []

    for latest_entry in latest_patch["data"]:
        key = (latest_entry["lane"], latest_entry["rank"])
        prev_entry = prev_dict.get(key)
        if not prev_entry:
            continue

        win_diff = latest_entry['winrate'] - prev_entry['winrate']
        pick_diff = latest_entry['pickrate'] - prev_entry['pickrate']
        ban_diff = latest_entry['banrate'] - prev_entry['banrate']
        weight = rank_weight.get(latest_entry["rank"], 1)
        score = abs(win_diff)*weight + abs(pick_diff)*weight*0.5 + abs(ban_diff)*weight*0.5

        if abs(win_diff) >= threshold_win or abs(pick_diff) >= threshold or abs(ban_diff) >= threshold:
            champ_diff.append({
                "name_ja": champ_name_ja,
                "lane": latest_entry["lane"],
                "rank": latest_entry["rank"],
                "winrate": latest_entry["winrate"],
                "pickrate": latest_entry["pickrate"],
                "banrate": latest_entry["banrate"],
                "win_diff": round(win_diff, 3),
                "pick_diff": round(pick_diff, 3),
                "ban_diff": round(ban_diff, 3),
                "score": round(score, 2),
                "trend": f"win{'↑' if win_diff>0 else '↓'} pick{'↑' if pick_diff>0 else '↓'} ban{'↑' if ban_diff>0 else '↓'}"
            })

    if champ_diff:
        diff_input[champ_id] = {
            "patch_name": latest_patch["patch_name"],
            "updatetime": latest_patch["updatetime"],
            "diff_data": champ_diff
        }

# 保存
OUTPUT_JSON = os.path.join(OUTPUT_DIR, 'diff_input.json')
with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(diff_input, f, ensure_ascii=False, indent=2)

print(f"差分データを {OUTPUT_JSON} に保存しました")
