import json
import unicodedata
from blizz_item_fetch import get_item_data, get_access_token
from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
SECRET = os.getenv("SECRET")

# Base directory
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
roster_file = os.path.join(base_dir, 'data', 'roster.txt')


replacements = {
    "Harkclickone": "Harkshock",
    "Harkclicktwo": "Harkshock",
    "Sumsushi": "Minto",
    "Jwhistler": "Jwhistle",
}

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

    raids = ['AQ', 'BWL', 'MC', 'Naxx', "Other", "WB"]
    item_cache = {}

    for raid in raids:
        try:
            with open(os.path.join(base_dir, 'data/lookup_tables', f'{raid}_loot_table.json'), 'r', encoding='utf-8') as f:
                try:
                    item_cache[raid] = json.load(f)
                except json.JSONDecodeError:
                    print(f"Error decoding {raid}_loot_table.json. Assuming empty.")
                    item_cache[raid] = {}  # Treat as empty if decoding fails
        except FileNotFoundError:
            item_cache[raid] = {}

    try:
        with open('trash_item_cache.json', 'r', encoding='utf-8') as f:
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

    for line in lines[1:]:
        # print(f"{round(num_items / len(lines) * 100, 2)}%")
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
        current_raid, item_name = get_item_name_and_raid(trash_items, item_id, item_cache, access_token, raids)
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
                found = True
                break
        if not found:
            loot_events.append({"dateTime": [date_time], "timesLooted": 1, "id": unique_id})

    # Remove "_disenchanted" to "Disenchanted"
    if "_disenchanted" in raid_data:
        del raid_data["_disenchanted"]

    return raid_data

def get_item_name_and_raid(trash_items, item_id, item_cache, access_token, raids):
    """
    Helper function to fetch the item name and determine the raid.
    """
    current_raid = None
    item_name = None

    for raid in raids:
        if item_id in item_cache[raid]:
            # Check for item in all valid raids
            current_raid = raid
            item_name = item_cache[current_raid][item_id]
            # print(f"Found in cache {raid, item_name}")
        elif item_id in trash_items:
            # Check for item in trash_items e.g. ZG
            current_raid = "Trash"
            item_name = trash_items[item_id]  # Geta the item name from trash_items
            print(f"Trash item found: {item_name}")

    if current_raid is None and item_name is None:
        print("############", type(item_id), "#########")
        # Item not found in any cache or trash_items, fetch from API
        item_data = get_item_data(access_token, item_id)
        try:
            if item_data:
                item_name = item_data["name"]
                print(f"{item_name} fetched from API")

                # Check for the wildcard condition
                if item_name.endswith("Qiraji Resonating Crystal"):
                    current_raid = "AQ"
                    print(f"Wildcard match: {item_name} assigned to AQ")
                else:
                    valid_raids = raids
                    while True:
                        current_raid = input(f"Enter raid for item {item_id} - {item_name} (options: {', '.join(valid_raids)}): ")
                        if current_raid in valid_raids:
                            break
                        else:
                            print("Invalid raid. Please enter a valid option.")

                if current_raid not in item_cache:
                    item_cache[current_raid] = {}
                item_cache[current_raid][item_id] = item_name

                # Update the corresponding loot table JSON file
                try:
                    with open(f"{current_raid}_loot_table.json", "r", encoding="utf-8") as f:
                        loot_table_data = json.load(f)
                except FileNotFoundError:
                    loot_table_data = {}

                loot_table_data[item_id] = item_name

                with open(f"{current_raid}_loot_table.json", "w", encoding="utf-8") as f:
                    json.dump(loot_table_data, f, indent=4, ensure_ascii=False)


            # Print "Item not found in cache" if item_name is still None
            if item_name is None:
                print(f"Item not found in cache for item ID {item_id}")

            else:
                print(f"Failed to fetch item name for item ID {item_id} from API")
        except Exception as e:
            print(f"Error fetching item data for item ID {item_id}: {e}")

    # If item_name is still None after trying the API, set it to the item_id
    if item_name is None:
        item_name = item_id  # Use item_id as a fallback
        print(f"Using item ID {item_id} as item name")

    return current_raid, item_name