import os
from modeule import load_json, save_json
from config import DATA_DIR

CHAMPIONS_JSON = os.path.join(DATA_DIR, 'champions.json') # チャンピオン一覧のJSON
CHAMPION_DIR = os.path.join(DATA_DIR,'champion_data')    # チャンピオン個別のディレクト

def champion_lane():
    champions = load_json(CHAMPIONS_JSON)

    for champ in champions:
        champ_id = champ.get("id")
        champ_file = os.path.join(CHAMPION_DIR, f"{champ_id}.json")
        champ_json = load_json(champ_file)

        lanes = set()
        for patch in champ_json.get("patches", []):
            for entry in patch.get("data", []):
                lane = entry.get("lane")
                if lane:
                    lanes.add(lane)

        # lanes が空でなければ追加
        if lanes:
            champ["lanes"] = sorted(list(lanes))  # ソートして配列にする

    # champions.json を上書き
    save_json(CHAMPIONS_JSON, champions)
    print("champions.json に lanes を追加しました")


def add_manual_lanes_bulk():
    # 使い方例
    lanes_dict = {
        "Nilah": ["ADC"]
    }
    champions = load_json(CHAMPIONS_JSON)

    for champion_id, lanes in lanes_dict.items():
        # 対象チャンピオンを探す
        target = next((c for c in champions if c.get("id") == champion_id), None)
        if not target:
            print(f"{champion_id} が champions.json に見つかりません")
            continue

        # lanes を追加
        target["lanes"] = sorted(list(set(lanes)))
        print(f"{champion_id} に lanes を追加しました: {target['lanes']}")

    # champions.json を上書き
    save_json(CHAMPIONS_JSON, champions)
    print("複数チャンピオンの lanes 追加が完了しました")


def main():
    champion_lane()
    add_manual_lanes_bulk()

if __name__ =="__main__":
    main()
