import json
import os

from loot_converter import convert_txt_to_JSON, update_loot_table
from softres_converter import decode_gargul_string, update_was_sr

# Base directory
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# File paths
raid_file = os.path.join(base_dir, 'data', 'raid_data.json')
softres_file = os.path.join(base_dir, 'data', 'softres_data.json')
exported_data = os.path.join(base_dir, 'data', 'import_files', 'loot_import.txt')
softres_export = os.path.join(base_dir, 'data', 'import_files', 'softres_import.csv')
boss_dict = os.path.join(base_dir, 'data', 'lookup_tables', 'bosses_per_raid.json')
roster_file = os.path.join(base_dir, 'data', 'roster.txt')

# FTP credentials
FTP_HOST = os.getenv('FTP_HOST')
FTP_USER = os.getenv('FTP_USER')
FTP_PASSWORD = os.getenv('FTP_PASSWORD')

# Handle the softres data
softres_data = decode_gargul_string(softres_export, boss_dict, softres_file, base_dir)

try:
    with open(softres_file, 'r', encoding='utf-8') as f:
        try:
            existing_sr_data = json.load(f)
        except json.JSONDecodeError:  # Handle empty JSON file
            existing_sr_data = None
except FileNotFoundError:
    existing_sr_data = None

# Save the JSON output to a file
with open(softres_file, 'w', encoding='utf-8') as outfile:
    json.dump(softres_data, outfile, indent=4, ensure_ascii=False)

# Handle the raid data
raid_data = convert_txt_to_JSON(roster_file, exported_data, existing_raid_data=None)

try:
    with open(raid_file, 'r', encoding='utf-8') as f:
        try:
            existing_raid_data = json.load(f)
        except json.JSONDecodeError:  # Handle empty JSON file
            existing_raid_data = None
except FileNotFoundError:
    existing_raid_data = None

# Merge the new raid data with the existing raid data
if existing_raid_data:
    for character, specs in raid_data.items():
        if character not in existing_raid_data:
            existing_raid_data[character] = specs
        else:
            for spec, items in specs.items():
                if spec not in existing_raid_data[character]:
                    existing_raid_data[character][spec] = items
                else:
                    for item_id, item_data in items.items():
                        if item_id not in existing_raid_data[character][spec]:
                            existing_raid_data[character][spec][item_id] = item_data
                        else:
                            existing_raid_data[character][spec][item_id]['lootEvents'].extend(item_data['lootEvents'])
    raid_data = existing_raid_data

# Update the raid data with the wasSr key
updated_raid_data = update_was_sr(raid_data, softres_data)

# Save the updated raid data to a file
with open(raid_file, 'w', encoding='utf-8') as outfile:  # Use 'w' mode to overwrite
    json.dump(updated_raid_data, outfile, indent=4, ensure_ascii=False)


# Get the latest date from the imported loot data. This will be used to set the raidWeek value.
#latest_date = get_latest_date_from_export(exported_data)

# Update the raid data with soft-reserved information and raidWeek
#update_raid_data_with_softres(raid_file, softres_file, latest_date)

# from ftp_transfer import upload_file_to_ftp
# upload_file_to_ftp(filename, FTP_HOST, FTP_USER, FTP_PASSWORD)Sc
