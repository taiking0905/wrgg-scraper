import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
from modeule import load_json, save_json
from config import DATA_DIR

PATCH_NOTES_JSON = os.path.join(DATA_DIR, 'patch_notes.json')# パッチノートの情報を保存するJSONファイル
PATCH_CONTENTS_JSON = os.path.join(DATA_DIR, 'patch_contents.json')# パッチ内容の情報を保存するJSONファイル

# スクレイピング
def fetch_patch_notes():
    url = "https://wildrift.leagueoflegends.com/ja-jp/news/tags/patch-notes/"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    patch_notes = []
    for a in soup.select("a[data-testid='articlefeaturedcard-component']"):
        patch_name_tag = a.select_one("div[data-testid='card-title']")
        patch_name = patch_name_tag.text.strip() if patch_name_tag else ""
        patch_link = "https://wildrift.leagueoflegends.com" + a.get("href", "")
        patch_notes.append({
            "patch_name": patch_name,
            "patch_link": patch_link
        })
    return list(reversed(patch_notes))  # 逆順にして古い順→新しい順に 

def update_patch_data():
    try:
        patch_data = fetch_patch_notes()

        existing_data = load_json(PATCH_NOTES_JSON)
        existing_links = {item["patch_link"] for item in existing_data}

        # 既存にないパッチだけ抽出して追加
        new_patches = [p for p in patch_data if p["patch_link"] not in existing_links]

        if new_patches:
            updated_data = existing_data + new_patches  # 既存の後ろに追加
            save_json(PATCH_NOTES_JSON, updated_data)
            print(f"{len(new_patches)} 件の新しいパッチを追加しました。")
        else:
            print("新しいパッチはありませんでした。")

        print("データの取得と更新が完了しました。")
        return {"success": True}
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return {"success": False, "error": str(e)}

# パッチ内容のスクレイピング
def fetch_patch_contents_for_patch(patch):
    patch_name = patch.get("patch_name", "")
    patch_link = patch.get("patch_link", "")
    patch_result = {}

    if not patch_link:
        return patch_result

    try:
        response = requests.get(patch_link)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        update_time_elem = soup.select_one("time")
        if update_time_elem and update_time_elem.get("datetime"):
            iso_datetime = update_time_elem["datetime"]
            updatetime = datetime.fromisoformat(iso_datetime.replace("Z", "+00:00")).strftime("%Y/%m/%d")
        else:
            updatetime = ""

        container_elems = soup.select(".character-changes-container")
        champions_dict = {}

        for container in container_elems:
            champion_name_elem = container.select_one(".character-name")
            champion_name = champion_name_elem.text.strip() if champion_name_elem else ""
            if not champion_name:
                continue

            change_elems = container.select(".character-change")
            changes_list = []

            for change in change_elems:
                ability_title = change.select_one(".character-ability-title")
                change_details_elem  = change.select_one(".character-change-body ul")

                ability_title_text = ability_title.text.strip() if ability_title else ""
                change_details_html = "".join(str(elem) for elem in change_details_elem) if change_details_elem else ""

                changes_list.append({
                    "ability_title": ability_title_text,
                    "change_details": change_details_html
                })

            if changes_list:
                champions_dict[champion_name] = changes_list

        if champions_dict:
            patch_result[patch_name] = {
                "update_date": updatetime,
                "champions": champions_dict
            }

    except Exception as e:
        print(f"Error fetching or parsing patch {patch_name} ({patch_link}): {e}")

    return patch_result



def update_patch_contents():
    patch_data = load_json(PATCH_NOTES_JSON)
    try:
        existing_contents = load_json(PATCH_CONTENTS_JSON)
        if not existing_contents:
            existing_contents = {}

        for patch in patch_data:
            patch_name = patch.get("patch_name")
            if patch_name not in existing_contents:
                patch_result = fetch_patch_contents_for_patch(patch)
                if patch_result:
                    existing_contents.update(patch_result)

        save_json(PATCH_CONTENTS_JSON, existing_contents)
        print(f"{len(existing_contents)} 件のパッチ内容を保存しました。")

        return {"success": True}
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return {"success": False, "error": str(e)}


def main():
    update_patch_data()
    update_patch_contents()

if __name__ =="__main__":
    main()