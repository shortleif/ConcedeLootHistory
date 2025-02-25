import csv
import json
from datetime import datetime

def decode_gargul_string(softres_export, boss_dict, softres_file=None):
    """
    Reads a CSV file, extracts data from all columns (excluding 'Note',
    'Discord ID', and 'Plus'), handles duplicate 'Name' entries by adding
    a 'Number reserved' key for duplicate items, and returns a dictionary
    structured by raid instance and boss, with 'Name' as keys under each
    boss, and 'Item' and 'Date' at the same level as inner keys, with item
    details stored under an 'item_info' key. The inner 'Date' is stored as
    a list to track multiple soft reservations by the same character, but
    only if the dates are different. Updates the outer 'raid_dates' list
    with the maximum date from the new import if the minimum date in the
    new import is greater than the current maximum in 'raid_dates'.
    Optionally loads existing data from a JSON file.

    Args:
        softres_export: The path to the CSV file.
        boss_dict: The path to the JSON file containing boss names for
                   raid instances.
        softres_file: Optional path to a JSON file containing existing data.

    Returns:
        A dictionary with the specified structure.
    """

    try:
        with open(boss_dict, 'r', encoding='utf-8') as f:
            try:
                boss_data = json.load(f)
            except json.JSONDecodeError:  # Handle empty JSON file
                boss_data = None
    except FileNotFoundError:
        boss_data = None

    data = {}

    if softres_file:
        try:
            with open(softres_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"Error: Existing data file not found at {softres_file}")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in {softres_file}")

    try:
        with open(softres_export, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            # Find the max date in the new import
            max_date_import = None
            for row in reader:
                date_str = row['Date']
                current_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                if max_date_import is None or current_date > max_date_import:
                    max_date_import = current_date

            max_date_str = max_date_import.strftime("%Y-%m-%d") if max_date_import else None

            csvfile.seek(0)
            reader = csv.DictReader(csvfile)

            # Initialize prompted_instances here, outside the loop
            prompted_instances = {}

            for row in reader:
                name = row.pop('Name')
                item = row['Item']
                boss = row['From']  # Assuming 'From' field indicates the boss

                # Remove unnecessary keys
                row.pop('Note', None)
                row.pop('Discord ID', None)
                row.pop('Plus', None)

                # Find the raid instance based on the boss
                raid_instance = None
                if boss_data:
                    for instance, bosses in boss_data.items():
                        if boss in bosses['boss_names']:
                            raid_instance = instance
                            break
                
                if raid_instance is None and item.startswith("Desecrated"):
                    raid_instance = "Naxx"
                    
                if raid_instance is None:
                    # Use the dictionary to store prompted raid instances
                    if item in prompted_instances:
                        raid_instance = prompted_instances[item]
                    else:
                        # Prompt for raid instance
                        print(f"Warning: Boss '{boss}' not found in any raid instance.")
                        while raid_instance is None:
                            if boss_data:
                                print("Available raid instances:")
                                for instance in boss_data.keys():
                                    print(f"- {instance}")
                            raid_instance = input(f"Enter the correct raid instance for '{item}': ")
                            if raid_instance not in boss_data:
                                print("Invalid raid instance. Please try again.")
                                raid_instance = None  # Reset to None for the loop
                        # Store the prompted instance
                        prompted_instances[item] = raid_instance
                    continue

                # Structure data by raid instance and boss
                if raid_instance not in data:
                    data[raid_instance] = {}
                if boss not in data[raid_instance]:
                    data[raid_instance][boss] = {}
                if name not in data[raid_instance][boss]:
                    data[raid_instance][boss][name] = {}

                if item not in data[raid_instance][boss][name]:
                    data[raid_instance][boss][name][item] = {'item_info': row.copy()}
                    data[raid_instance][boss][name][item]['item_info']['Number reserved'] = 1
                    data[raid_instance][boss][name][item]['item_info']['Date'] = [row['Date']]
                    data[raid_instance][boss][name][item]['raid_dates'] = []

                    if max_date_str:
                        data[raid_instance][boss][name][item]['raid_dates'].append(max_date_str)
                else:
                    if 'Number reserved' in data[raid_instance][boss][name][item]['item_info']:
                        data[raid_instance][boss][name][item]['item_info']['Number reserved'] += 1
                    else:
                        data[raid_instance][boss][name][item]['item_info']['Number reserved'] = 2

                    if isinstance(data[raid_instance][boss][name][item]['item_info']['Date'], list):
                        if row['Date'] not in data[raid_instance][boss][name][item]['item_info']['Date']:
                            data[raid_instance][boss][name][item]['item_info']['Date'].append(row['Date'])
                    else:
                        if row['Date'] != data[raid_instance][boss][name][item]['item_info']['Date']:
                            data[raid_instance][boss][name][item]['item_info']['Date'] = \
                                [data[raid_instance][boss][name][item]['item_info']['Date'], row['Date']]

                    if max_date_str:
                        data[raid_instance][boss][name][item]['raid_dates'].append(max_date_str)

    except FileNotFoundError:
        print(f"Error: CSV file not found at {softres_export}")
    except Exception as e:
        print(f"Error reading or processing CSV data: {e}")

    # Convert raid_dates to YYYY-MM-DD format
    for raid_instance in data:
        for boss in data[raid_instance]:
            for name in data[raid_instance][boss]:
                for item in data[raid_instance][boss][name]:
                    data[raid_instance][boss][name][item]['raid_dates'] = [
                        datetime.strptime(date, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d") if ' ' in date else date
                        for date in data[raid_instance][boss][name][item]['raid_dates']
                    ]

    return data


def update_was_sr(raid_data, softres_data):
    """
    Updates the raid_data with a new key 'wasSr' to indicate if an item was also soft reserved
    by the same person on the same date.

    Args:
        raid_data: The dictionary containing raid data.
        softres_data: The dictionary containing soft reserve data.

    Returns:
        The updated raid_data with the 'wasSr' key added.
    """
    for character, specs in raid_data.items():
        print(f"Processing character: {character}")
        for spec, items in specs.items():
            for item_id, item_data in items.items():
                for event in item_data['lootEvents']:
                    raid_week = event['raidWeek']
                    was_sr = event.get('wasSr', False)  # Preserve existing wasSr value if True

                    # Check if the item was soft reserved by the same character on the same date
                    for raid_instance, bosses in softres_data.items():
                        for boss, softres_items in bosses.items():
                            if character in softres_items:
                                print(f"Character {character} found in softres_data under boss {boss}")
                                for softres_item, softres_item_data in softres_items[character].items():
                                    if item_id == softres_item_data['item_info']['ItemId']:
                                        print(f"Item {item_id} found for character {character} in softres_data")
                                        softres_dates = softres_item_data['raid_dates']
                                        print(f"Comparing raid_week {raid_week} with softres_dates {softres_dates}")
                                        if any(date in raid_week for date in softres_dates):
                                            was_sr = True
                                            break
                                else:
                                    print(f"Item {item_id} not found for character {character} in softres_data under boss {boss}")
                            else:
                                print(f"Character {character} not found in softres_data under boss {boss}")
                            if was_sr:
                                break
                        if was_sr:
                            break

                    event['wasSr'] = was_sr

                    if not was_sr:
                        print(f"Warning: {character} not found in soft reserve data or no matching dates for item {item_id}")

    return raid_data