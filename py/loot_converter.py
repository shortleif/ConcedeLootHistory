import json
import unicodedata
import os
import time
import logging
from datetime import datetime
from blizz_item_fetch import get_item_data, get_access_token
from dotenv import load_dotenv

# Set up logging
def setup_logging():
    """Set up proper logging instead of using print statements"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(os.path.dirname(__file__), "loot_converter.log")),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# Load environment variables
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
SECRET = os.getenv("SECRET")

# Character name replacements
replacements = {
    "Harkclickone": "Harkshock",
    "Harkclicktwo": "Harkshock",
    "Sumsushi": "Minto",
    "Jwhistler": "Jwhistle",
}

# Base directory path
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
VALID_RAIDS = ['AQ', 'BWL', 'MC', 'Naxx', 'Scarlet', 'Other', 'WB']

# File operations with improved error handling
def load_json_file(file_path, default=None):
    """Load a JSON file with proper error handling"""
    if default is None:
        default = {}
    
    # Create directory if it doesn't exist
    dir_path = os.path.dirname(file_path)
    os.makedirs(dir_path, exist_ok=True)
    
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"{file_path} contains invalid JSON. Using default.")
                    return default
        return default
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return default

def save_json_file(file_path, data):
    """Save data to a JSON file with proper error handling"""
    try:
        # Create directory if it doesn't exist
        dir_path = os.path.dirname(file_path)
        os.makedirs(dir_path, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
            f.flush()  # Ensure data is written to disk
        
        # Verify the file was written
        if os.path.exists(file_path):
            logger.info(f"Successfully wrote to {file_path}")
            return True
        else:
            logger.warning(f"File not created: {file_path}")
            return False
    except Exception as e:
        logger.error(f"Error writing to {file_path}: {e}", exc_info=True)
        return False

def check_file_permissions(path):
    """Check file/directory permissions and existence"""
    try:
        # Check if the file exists
        exists = os.path.exists(path)
        
        # Check if directory structure exists
        dir_path = os.path.dirname(path)
        dir_exists = os.path.exists(dir_path)
        
        # Check permissions (if exists)
        readable = False
        writable = False
        if exists:
            readable = os.access(path, os.R_OK)
            writable = os.access(path, os.W_OK)
        
        # Check if directory is writable
        dir_writable = False
        if dir_exists:
            dir_writable = os.access(dir_path, os.W_OK)
        
        result = {
            "path": path,
            "exists": exists,
            "readable": readable,
            "writable": writable,
            "dir_exists": dir_exists,
            "dir_writable": dir_writable
        }
        
        logger.info(f"Permission check: {result}")
        return result
    except Exception as e:
        logger.error(f"Error checking permissions for {path}: {e}")
        return {
            "path": path,
            "error": str(e)
        }

def get_item_data_safe(access_token, item_id):
    """Safely get item data from API with retries and error handling"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return get_item_data(access_token, item_id)
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"API call failed, retrying ({attempt+1}/{max_retries}): {e}")
                time.sleep(1)  # Add delay between retries
            else:
                logger.error(f"All retries failed for item ID {item_id}: {e}")
                return None

def load_item_caches(base_dir, valid_raids):
    """Load all item cache files"""
    item_cache = {}
    
    # Load raid-specific item caches
    for raid in valid_raids:
        loot_table_path = os.path.join(base_dir, 'data', 'lookup_tables', f'{raid}_loot_table.json')
        item_cache[raid] = load_json_file(loot_table_path)
    
    # Load trash items cache
    trash_item_cache_path = os.path.join(base_dir, 'data', 'lookup_tables', 'trash_item_cache.json')
    trash_items = load_json_file(trash_item_cache_path)
    
    return item_cache, trash_items

def load_roster(roster_file):
    """Load the roster from file"""
    try:
        with open(roster_file, 'r', encoding='utf-8') as f:
            roster = [line.strip().replace(",", "") for line in f]
            logger.info(f"Loaded roster with {len(roster)} characters")
            return roster
    except Exception as e:
        logger.error(f"Error loading roster file {roster_file}: {e}")
        return []

def calculate_max_date(lines):
    """Calculate the max date in the import data"""
    max_date = None
    for line in lines[1:]:  # Skip header
        try:
            date_time, _, _, _, _ = line.strip().split(',')
            current_date = datetime.strptime(date_time, "%Y-%m-%d")
            if max_date is None or current_date > max_date:
                max_date = current_date
        except Exception as e:
            logger.warning(f"Error parsing date in line: {line}. Error: {e}")
    
    max_date_str = max_date.strftime("%Y-%m-%d") if max_date else None
    logger.info(f"Max date in import: {max_date_str}")
    return max_date, max_date_str

def diagnose_file_writing(file_path, data):
    """Test file writing capability with detailed diagnostics"""
    logger.info(f"Attempting to write to {file_path} (diagnostic test)")

    # Check current directory
    logger.info(f"Current working directory: {os.getcwd()}")
    
    # Check if parent directory exists and is writable
    dir_path = os.path.dirname(file_path)
    os.makedirs(dir_path, exist_ok=True)
    dir_writable = os.access(dir_path, os.W_OK)
    logger.info(f"Directory exists: {os.path.exists(dir_path)}, writable: {dir_writable}")
    
    # Check if file exists and is writable
    file_exists = os.path.exists(file_path)
    file_writable = file_exists and os.access(file_path, os.W_OK)
    logger.info(f"File exists: {file_exists}, writable: {file_writable}")

    # Try to write a test file
    test_success = False
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
        logger.info(f"Test write completed without exception")
        test_success = os.path.exists(file_path)
        logger.info(f"File exists after write: {test_success}")
        
        if test_success:
            # Read back to verify integrity
            with open(file_path, 'r', encoding='utf-8') as f:
                read_data = json.load(f)
            logger.info(f"File read back successfully: {str(read_data)[:100]}...")
    except Exception as e:
        logger.error(f"Test write failed: {e}", exc_info=True)
    
    return test_success

def get_item_name_and_raid(item_id, access_token, base_dir, valid_raids=None):
    """
    Get the item name and raid for an item ID. Writes to file immediately after receiving input.
    
    Parameters:
    item_id (str): The item ID to look up
    access_token (str): The Blizzard API access token
    base_dir (str): The base directory path
    valid_raids (list): List of valid raid names
    
    Returns:
    tuple: (item_name, raid_name)
    """
    if valid_raids is None:
        valid_raids = VALID_RAIDS
    
    # Convert item_id to string for consistency
    item_id = str(item_id)
    
    # First check all local lookup tables
    lookup_dir = os.path.join(base_dir, 'data', 'lookup_tables')
    
    # Ensure lookup directory exists
    os.makedirs(lookup_dir, exist_ok=True)
    
    # Check each raid's loot table for the item
    for raid_name in valid_raids:
        table_path = os.path.join(lookup_dir, f'{raid_name}_loot_table.json')
        try:
            if os.path.exists(table_path):
                with open(table_path, 'r', encoding='utf-8') as f:
                    local_lookup = json.load(f)
                    if item_id in local_lookup:
                        logger.info(f"Found item {item_id} in {raid_name} loot table")
                        return local_lookup[item_id], raid_name
        except Exception as e:
            logger.error(f"Error reading {table_path}: {e}")
    
    # Also check trash items table
    trash_table_path = os.path.join(lookup_dir, 'trash_item_cache.json')
    try:
        if os.path.exists(trash_table_path):
            with open(trash_table_path, 'r', encoding='utf-8') as f:
                trash_items = json.load(f)
                if item_id in trash_items:
                    logger.info(f"Found item {item_id} in trash items")
                    return trash_items[item_id], "Trash"
    except Exception as e:
        logger.error(f"Error reading trash items: {e}")

    # If not found locally, try API
    try:
        logger.info(f"Fetching item {item_id} from API")
        item_data = get_item_data_safe(access_token, item_id)
        
        if item_data and "name" in item_data:
            item_name = item_data["name"]
            logger.info(f"Found new item: {item_name}")
            
            # Special case for Qiraji Resonating Crystal
            if item_name.endswith("Qiraji Resonating Crystal"):
                raid_name = "AQ"
                logger.info(f"Wildcard match: {item_name} assigned to AQ")
            else:
                # Display available raid options
                logger.info("Available raid instances: " + ", ".join(valid_raids))
                
                # Get raid input and immediately process it
                raid_name = input(f"Enter the raid instance for '{item_name}' (options: {', '.join(valid_raids)}): ").strip()
                logger.info(f"User input raid name: '{raid_name}'")
                
                # Validate raid name
                if raid_name not in valid_raids:
                    logger.warning(f"Invalid raid name: {raid_name}")
                    return f"Unknown Item {item_id}", "Unknown"
            
            # Update the appropriate loot table IMMEDIATELY after input
            table_path = os.path.join(lookup_dir, f'{raid_name}_loot_table.json')
            logger.info(f"Preparing to update loot table at: {table_path}")
            
            # Run diagnostic test
            diagnostic_result = diagnose_file_writing(table_path, {item_id: item_name})
            logger.info(f"Diagnostic test result: {diagnostic_result}")
            
            # Now do the actual update
            update_success = update_loot_table(base_dir, raid_name, item_id, item_name)
            logger.info(f"Update success: {update_success}")
            
            if update_success:
                logger.info(f"Added {item_name} to {raid_name}_loot_table.json")
                return item_name, raid_name
            else:
                logger.error(f"Failed to save {table_path}")
                
                # Try direct file write as last resort
                try:
                    with open(table_path, 'w', encoding='utf-8') as f:
                        json.dump({item_id: item_name}, f, indent=2)
                    logger.info(f"Direct file write attempt completed")
                except Exception as e:
                    logger.error(f"Direct file write failed: {e}")
                
                return f"Unknown Item {item_id}", "Unknown"
        else:
            logger.warning(f"Could not get item data from API for {item_id}")
    except Exception as e:
        logger.error(f"Error processing item {item_id}: {e}", exc_info=True)

    return f"Unknown Item {item_id}", "Unknown"

def process_loot_line(line, roster, raid_data, item_cache, trash_items, access_token, max_date_str, base_dir):
    """Process a single line of loot data"""
    try:
        date_time, character, item_id, offspec, unique_id = line.strip().split(',')
        
        # Normalize character name
        character = unicodedata.normalize('NFC', character)
        character = ''.join(c for c in character if c.isprintable())
        character = replacements.get(character, character)
        
        if character not in roster:
            logger.warning(f"Character not in roster: {character}")
            return
        
        spec = "Offspec" if offspec == "1" else "Mainspec"
        
        # Determine the raid and fetch item name
        item_name, current_raid = get_item_name_and_raid(item_id, access_token, base_dir)
        logger.info(f"Item: {item_name}, Current Raid: {current_raid}")
        
        if current_raid == "Trash":
            logger.info(f"Skipping trash item: {item_name}")
            return
        
        # Construct the Wowhead link
        item_link = f"https://www.wowhead.com/classic/item={item_id}"
        
        # Ensure character exists in raid_data
        if character not in raid_data:
            raid_data[character] = {"Mainspec": {}, "Offspec": {}}
        
        # Ensure spec exists for this character
        if spec not in raid_data[character]:
            raid_data[character][spec] = {}
        
        # Add item if it doesn't exist for this character/spec
        if item_id not in raid_data[character][spec]:
            raid_data[character][spec][item_id] = {
                "itemName": item_name if item_name else item_id,
                "itemLink": item_link,
                "raid": current_raid,
                "lootEvents": []
            }
        
        # Process loot events
        loot_events = raid_data[character][spec][item_id]["lootEvents"]
        found = False
        
        # Check if this unique_id already exists
        for event in loot_events:
            if event["id"] == unique_id:
                event["dateTime"] = event["dateTime"] + [date_time]
                event["timesLooted"] += 1
                if "raidWeek" not in event:
                    event["raidWeek"] = []
                event["raidWeek"].append(max_date_str)
                found = True
                break
        
        # Add new loot event if not found
        if not found:
            loot_events.append({
                "dateTime": [date_time],
                "timesLooted": 1,
                "id": unique_id,
                "raidWeek": [max_date_str]
            })
        
    except Exception as e:
        logger.error(f"Error processing loot line: {line}. Error: {e}", exc_info=True)

def convert_txt_to_JSON(roster_file, exported_data, existing_raid_data=None):
    """
    Convert a text export of loot history to JSON format
    
    Parameters:
    roster_file (str): Path to the roster file
    exported_data (str): Path to the exported data file
    existing_raid_data (dict): Existing raid data to update
    
    Returns:
    dict: Updated raid data
    """
    logger.info(f"Converting {exported_data} to JSON")
    raid_data = existing_raid_data if existing_raid_data else {}
    
    try:
        # Read and parse the exported data
        with open(exported_data, 'r', encoding='utf-8') as f:
            file_contents = f.read()
        
        file_contents = file_contents.encode("utf-8").decode("utf-8")
        lines = file_contents.splitlines()
        
        # Get access token for API
        access_token = get_access_token(CLIENT_ID, SECRET)
        
        # Load item caches and roster
        item_cache, trash_items = load_item_caches(base_dir, VALID_RAIDS)
        roster = load_roster(roster_file)
        
        # Calculate max date
        max_date, max_date_str = calculate_max_date(lines)
        
        # Process each line (skip header)
        line_count = 0
        for line in lines[1:]:
            line_count += 1
            logger.info(f"Processing line {line_count} of {len(lines)-1}")
            process_loot_line(line, roster, raid_data, item_cache, trash_items, access_token, max_date_str, base_dir)
        
        # Clean up data
        if "_disenchanted" in raid_data:
            del raid_data["_disenchanted"]
            logger.info("Removed _disenchanted from raid data")
        
        logger.info(f"Successfully processed {line_count} loot entries")
        return raid_data
        
    except Exception as e:
        logger.error(f"Error converting file: {e}", exc_info=True)
        return raid_data

def update_loot_table(base_dir, raid_name, item_id, item_name):
    """Update the appropriate loot table with new item information"""
    loot_table_path = os.path.join(base_dir, 'data', 'lookup_tables', f'{raid_name}_loot_table.json')
    logger.info(f"Updating loot table at {loot_table_path}")
    
    # Create directory if it doesn't exist
    dir_path = os.path.dirname(loot_table_path)
    os.makedirs(dir_path, exist_ok=True)
    
    # Check if the directory is writable
    if not os.access(dir_path, os.W_OK):
        logger.error(f"Directory {dir_path} is not writable!")
        return False
    
    # Load existing loot table or create new
    try:
        if os.path.exists(loot_table_path):
            with open(loot_table_path, 'r', encoding='utf-8') as f:
                try:
                    loot_table = json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"{loot_table_path} contains invalid JSON. Creating new.")
                    loot_table = {}
        else:
            loot_table = {}
    except Exception as e:
        logger.error(f"Error loading loot table: {e}")
        loot_table = {}
    
    # Add or update item
    loot_table[str(item_id)] = item_name
    logger.info(f"Added item {item_id} to loot table")
    
    # Save updated loot table
    try:
        with open(loot_table_path, 'w', encoding='utf-8') as f:
            json.dump(loot_table, f, indent=2, ensure_ascii=False, sort_keys=True)
            f.flush()  # Ensure data is written to disk
        
        # Verify file was written
        if os.path.exists(loot_table_path):
            file_size = os.path.getsize(loot_table_path)
            logger.info(f"Successfully updated {raid_name}_loot_table.json (size: {file_size} bytes)")
            return True
        else:
            logger.error(f"File wasn't created: {loot_table_path}")
            return False
    except Exception as e:
        logger.error(f"Error writing to {loot_table_path}: {e}", exc_info=True)
        return False

def verify_directories(base_dir):
    """Verify all necessary directories exist and are writable"""
    dirs_to_check = [
        os.path.join(base_dir, 'data'),
        os.path.join(base_dir, 'data', 'lookup_tables'),
        os.path.join(base_dir, 'output')
    ]
    
    for directory in dirs_to_check:
        os.makedirs(directory, exist_ok=True)
        if not os.access(directory, os.W_OK):
            logger.error(f"Directory {directory} is not writable!")
            return False
    
    logger.info("All required directories exist and are writable")
    return True

def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert loot history export to JSON.')
    parser.add_argument('--roster', type=str, required=True, help='Path to the roster file')
    parser.add_argument('--export', type=str, required=True, help='Path to the exported loot history data')
    parser.add_argument('--output', type=str, help='Output path for the JSON file')
    parser.add_argument('--merge', type=str, help='Existing JSON file to merge with')
    args = parser.parse_args()
    
    # Verify directories
    if not verify_directories(base_dir):
        return 1
    
    # Set default output path if not provided
    if not args.output:
        output_dir = os.path.join(base_dir, 'output')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = os.path.join(output_dir, f'loot_history_{timestamp}.json')
    
    # Load existing data if merging
    existing_data = None
    if args.merge:
        try:
            with open(args.merge, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            logger.info(f"Loaded existing data from {args.merge}")
        except Exception as e:
            logger.error(f"Failed to load existing data: {e}")
            return 1
    
    # Convert the data
    try:
        logger.info("Starting conversion process...")
        raid_data = convert_txt_to_JSON(args.roster, args.export, existing_data)
        
        # Save the result
        output_dir = os.path.dirname(args.output)
        os.makedirs(output_dir, exist_ok=True)
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(raid_data, f, indent=2, ensure_ascii=False, sort_keys=True)
        
        logger.info(f"Successfully saved output to {args.output}")
        return 0
    
    except Exception as e:
        logger.error(f"Conversion failed: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    exit_code = main()
    exit(exit_code)
