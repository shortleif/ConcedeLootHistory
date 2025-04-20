import time
import json

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup

def extract_data_from_wowhead(url):
    options = Options()
    options.add_argument('--no-sandbox')  # Add more arguments if needed

    driver = webdriver.Chrome(options=options)

    driver.get(url)

    wait = WebDriverWait(driver, 10)
    try:
        reject_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#onetrust-reject-all-handler")))
        reject_button.click()
    except:
        print("Could not find or click the reject button.")
        driver.quit()
        return []

    all_extracted_data = []  # Accumulate data from all pages

    num_clicks = 8  # Change this to the desired number of clicks

    for _ in range(num_clicks +1): # added one extra click to collect the first page data as well
        try:
            # Wait for the table to load (adjust the timeout as needed)
            table = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'listview-mode-default'))
            )
        except:
            print("Error: Table did not load within the timeout period.")
            driver.quit()
            return []

        soup = BeautifulSoup(table.get_attribute('outerHTML'), 'html.parser')

        headers = [th.text.strip() for th in soup.find_all('th')]
        data = []

        for row in soup.find_all('tr')[1:]:  # Skip the header row
            row_data = {}
            cells = row.find_all('td')

            name_cell = cells[2]
            try:
                link = name_cell.find('a', class_='listview-cleartext')['href']
                row_data['Link'] = link
            except:
                print("Error: Could not find link in name cell.")
                continue  # Skip this row if there's an error

            for i, cell in enumerate(cells[1:]):
                row_data[headers[i]] = cell.text.strip()
            data.append(row_data)

        all_extracted_data.extend(data) #add the collected data to the main data collector

        try:
            next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Next')]")))
            ActionChains(driver).click(next_button).perform()
            time.sleep(1)
        except:
            print("No more 'Next' buttons or an error occurred.")
            break #exit if there are no more next pages

    driver.quit()
    return all_extracted_data

#url = "https://www.wowhead.com/classic/items/quality:2:3:4:5?filter=214;3456;0"
url = "https://www.wowhead.com/classic/zone=16236/scarlet-enclave"
extracted_data = extract_data_from_wowhead(url)

item_data = {}
for row_data in extracted_data:
    try:
        link = row_data['Link']
        item_id = link.split('/')[-2].split('=')[-1]
        item_name = row_data['Name']
        item_data[item_id] = item_name
    except:
        print("Error extracting item ID or name.")

filename = "Naxx_loot_table.json"

try:
    with open(filename, 'r+') as f:  # Open in read and write mode
        try:
            existing_data = json.load(f)
        except json.JSONDecodeError:
            existing_data = {}
        existing_data.update(item_data)
        f.seek(0)  # Go to the beginning of the file
        json.dump(existing_data, f, indent=4)
        f.truncate()  # Remove any remaining content
except FileNotFoundError:
    with open(filename, 'w') as f:  # Create the file if it doesn't exist
        json.dump(item_data, f, indent=4)

print(f"Data saved to {filename}")