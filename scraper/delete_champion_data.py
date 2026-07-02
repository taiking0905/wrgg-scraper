import os
from modeule import load_json, save_json
from config import DATA_DIR

CHAMPION_DIR = os.path.join(DATA_DIR, 'champion_data')


def delete_champion_data():
    for filename in os.listdir(CHAMPION_DIR):
        filepath = os.path.join(CHAMPION_DIR, filename)

        # JSON以外はスキップ
        if not filename.endswith(".json"):
            continue

        data = load_json(filepath)
        if not data:
            continue

        patches = data.get("patches", [])

        # 5件以下なら何もしない
        if len(patches) <= 5:
            continue

        # 🔥 ソートせず「後ろ5件だけ残す」
        # 前提：append順 = 古い → 新しい
        trimmed = patches[-5:]

        data["patches"] = trimmed
        save_json(filepath, data)

        print(f"{filename}: {len(patches)} → {len(trimmed)} に削減")