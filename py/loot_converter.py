import json
import unicodedata
from blizz_item_fetch import get_item_data, get_access_token
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
SECRET = os.getenv("SECRET")

replacements = {
    "Harkclickone": "Harkshock",
    "Harkclicktwo": "Harkshock",
    "Sumsushi": "Minto",
    "Jwhistler": "Jwhistle",
}

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
roster_file = os.path.join(base_dir, 'data', 'roster.txt')

def convert_txt_to_JSON(roster_file, exported_data, existing_raid_data=None):
    raid_data = existing_raid_data if existing_raid_data else {}

    with open(exported_data, 'r', encoding='utf-8') as f:
        file_contents = f.read()

    file_contents = file_contents.encode("utf-8").decode("utf-8")
    lines = file_contents.splitlines()
    lines_iterator = iter(lines)
    next(lines_iterator)
    num_items = 1
    access_token = get_access_token(CLIENT_ID, SECRET)

    raids = ['AQ', 'BWL', 'MC', 'Naxx', "Scarlet", "Other", "WB"]
    item_cache = {}

    for raid in raids:
        loot_table_path = os.path.join(base_dir, 'data', 'lookup_tables', f'{raid}_loot_table.json')
        try:
            with open(loot_table_path, 'r', encoding='utf-8') as f:
                try:
                    item_cache[raid] = json.load(f)
                except json.JSONDecodeError:
                    print(f"Error decoding {raid}_loot_table.json. Assuming empty.")
                    item_cache[raid] = {}  # Treat as empty if decoding fails
        except FileNotFoundError:
            item_cache[raid] = {}

    trash_item_cache_path = os.path.join(base_dir, 'data', 'lookup_tables', 'trash_item_cache.json')
    try:
        with open(trash_item_cache_path, 'r', encoding='utf-8') as f:
            try:
                trash_items = json.load(f)
            except json.JSONDecodeError:
                print("Error decoding trash_item_cache.json. Assuming empty.")
                trash_items = {}
    except FileNotFoundError:
        trash_items = {}

    with open(roster_file, 'r', encoding='utf-8') as f:
        roster = [line.strip().replace(",", "") for line in f]
        print(roster)

    # Calculate the max date in the current import
    max_date = None
    for line in lines[1:]:
        date_time, _, _, _, _ = line.strip().split(',')
        current_date = datetime.strptime(date_time, "%Y-%m-%d")
        if max_date is None or current_date > max_date:
            max_date = current_date

    max_date_str = max_date.strftime("%Y-%m-%d") if max_date else None

    for line in lines[1:]:
        num_items += 1
        date_time, character, item_id, offspec, unique_id = line.strip().split(',')

        character = unicodedata.normalize('NFC', character)
        character = ''.join(c for c in character if c.isprintable())
        character = replacements.get(character, character)

        if character not in roster:
            print(character)
            continue

        spec = "Offspec" if offspec == "1" else "Mainspec"

        # Determine the raid and fetch item name
        item_name, current_raid = get_item_name_and_raid(item_id, access_token, trash_items, item_cache)
        print("Item:", item_name, "Current Raid:", current_raid)

        if current_raid == "Trash":
            continue

        # Construct the Wowhead link
        item_link = f"https://www.wowhead.com/classic/item={item_id}"

        if item_id not in raid_data.get(character, {}).get(spec, {}):
            if item_name:
                # Ensure Mainspec and Offspec keys exist, even if empty
                raid_data.setdefault(character, {"Mainspec": {}, "Offspec": {}})
                raid_data[character][spec][item_id] = {
                    "itemName": item_name,
                    "itemLink": item_link,
                    "raid": current_raid,
                    "lootEvents": []
                }
            else:
                # Ensure Mainspec and Offspec keys exist, even if empty
                raid_data.setdefault(character, {"Mainspec": {}, "Offspec": {}})
                raid_data[character][spec][item_id] = {
                    "itemName": item_id,
                    "itemLink": item_link,
                    "raid": current_raid,
                    "lootEvents": []
                }
        loot_events = raid_data[character][spec][item_id]["lootEvents"]
        found = False
        for event in loot_events:
            if event["id"] == unique_id:
                event["dateTime"] = event["dateTime"] + [date_time]
                event["timesLooted"] += 1
                if "raidWeek" not in event:
                    event["raidWeek"] = []
                event["raidWeek"].append(max_date_str)
                found = True
                break
        if not found:
            loot_events.append({"dateTime": [date_time], "timesLooted": 1, "id": unique_id, "raidWeek": [max_date_str]})

    # Remove "_disenchanted" to "Disenchanted"
    if "_disenchanted" in raid_data:
        del raid_data["_disenchanted"]

    return raid_data

def get_item_name_and_raid(item_id, access_token, raid_lookup, item_lookup):
    item_name = None
    raid_name = None

    # First check if item exists in our local lookup table
    if item_id in item_lookup:
        item_name = item_lookup[item_id]["name"]
        print(f"{item_name} found in local lookup")
        raid_name = item_lookup[item_id].get("raid", "Unknown")
        return item_name, raid_name

    # If not found locally, try the API
    try:
        item_data = get_item_data(item_id, access_token)
        if item_data and "name" in item_data:
            item_name = item_data["name"]
            print(f"{item_name} fetched from API")
            # Rest of the existing raid lookup logic...
        else:
            print(f"Failed to fetch item name for item ID {item_id} from API")
            raise ValueError(f"Could not get item name from API for item ID {item_id}")
    except Exception as e:
        print(f"Error fetching item data for item ID {item_id}: {e}")
        raise

    return item_name, raid_name