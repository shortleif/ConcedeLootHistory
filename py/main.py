from loot_converter import convert_txt_to_JSON, get_latest_date_from_export
from softres_converter import decode_gargul_string, update_raid_data_with_softres
import json
import os


# File paths
raid_file = '../data/raid_data.json'
softres_file = '../data/softres_data.json'
exported_data = "../data/import_files/loot_import.txt"
softres_export = "../data/import_files/softres_import.csv"
boss_dict = "../data/lookup_tables/bosses_per_raid.json"

# FTP credentials
FTP_HOST = os.getenv('FTP_HOST')
FTP_USER = os.getenv('FTP_USER')
FTP_PASSWORD = os.getenv('FTP_PASSWORD')


try:
    with open(raid_file, 'r', encoding='utf-8') as f:
        try:
            existing_data = json.load(f)
        except json.JSONDecodeError:  # Handle empty JSON file
            existing_data = None
except FileNotFoundError:
    existing_data = None

raid_data = convert_txt_to_JSON(exported_data, existing_data)

# Save the JSON output to a file
with open(raid_file, 'w', encoding='utf-8') as outfile:  # Use 'w' mode to overwrite
    json.dump(raid_data, outfile, indent=4, ensure_ascii=False)

softres_data = decode_gargul_string(softres_export, boss_dict, softres_file)

try:
    with open(softres_file, 'r', encoding='utf-8') as f:
        try:
            existing_sr_data = json.load(f)
        except json.JSONDecodeError:  # Handle empty JSON file
            existing_sr_data = None
except FileNotFoundError:
    existing_sr_data = None


# Save the JSON output to a file
with open(softres_file, 'w', encoding='utf-8') as outfile:  # Use 'w' mode to overwrite
    json.dump(softres_data, outfile, indent=4, ensure_ascii=False)

# Decode the softres data
softres_data = decode_gargul_string(softres_export, boss_dict, softres_file)

# Get the latest date from the exported data
latest_date = get_latest_date_from_export(exported_data)

# Update the raid data with soft-reserved information and raidWeek
update_raid_data_with_softres(raid_file, softres_file, latest_date)

# from ftp_transfer import upload_file_to_ftp
# upload_file_to_ftp(filename, FTP_HOST, FTP_USER, FTP_PASSWORD)
