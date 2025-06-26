# Concede Raid Loot Tracker

A web-based tool for tracking and visualizing loot distribution in World of Warcraft Classic raids for the guild "Concede".

## Overview

This project provides a dashboard to track items looted during raids, showing:
- Latest raid loot distribution
- Total loot statistics by character for the current phase
- Raid-specific loot history
- Soft-reservation statistics and tracking

The application makes it easy to see who received what items, when they received them, and whether those items were soft-reserved by the player.

## Features

- **Latest Loot Overview**: Shows items received in the most recent raid
- **Total Loot Counts**: Tracks how many items each player has received in the current phase
- **Raid-Specific Views**: Filter loot by specific raids (Naxx, AQ, BWL, MC, etc.)
- **Soft-Reserve Tracking**: See which items were most reserved and who reserved them
- **Search Functionality**: Find specific items or players
- **Visual Indicators**: Items that were soft-reserved are marked with "(SR)"
- **Set Token Tracking**: Special tracking for Desecrated tokens

## Technical Structure

### Frontend
- HTML, CSS (with Bootstrap 5), and vanilla JavaScript
- Responsive design with dark theme
- Interactive tables with tooltips and sorting functionality
- Accordion components for organized data display

### Backend (Python)
- `main.py`: Orchestrates data processing and file operations
- `loot_converter.py`: Processes raw loot data into structured JSON
- `softres_converter.py`: Handles soft-reservation data from Gargul exports
- `blizz_item_fetch.py`: Fetches item data from Blizzard API
- `ftp_transfer.py`: Uploads processed data to a web server

### Data Storage
- Raid data stored in `data/raid_data.json`
- Soft-reserve data stored in `data/softres_data.json`
- Backup data stored in `data/backups/`
- Lookup tables in `data/lookup_tables/` for item and boss information

## How It Works

1. Export loot data from your raid tracking addon and place it in `data/import_files/loot_import.txt`
2. Export soft-reservation data from Gargul and place it in `data/import_files/softres_import.csv`
3. Run `python py/main.py` to process the data
4. The web application will display the processed information in an organized format

## Setup and Usage

### Requirements
- Python 3.x
- Web browser
- World of Warcraft Classic addon for loot tracking (e.g., Gargul)

### Installation
1. Clone this repository
2. Install Python dependencies: `pip install -r requirements.txt` (if available)
3. Setup your `.env` file with Blizzard API credentials and FTP details if needed

### Running the Application
1. Process data: `python py/main.py`
2. Open `index.html` in a web browser

## Data Updates

The system supports incremental updates - new loot data is merged with existing data, maintaining the history while adding new entries.

## Contributing

If you want to contribute to this project, please contact the repository owner.