import requests
from dotenv import load_dotenv
import os
import json

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
SECRET = os.getenv("SECRET")

def get_access_token(client_id, client_secret, region='us'):
    data = { 'grant_type': 'client_credentials' }
    response = requests.post(f'https://{region}.battle.net/oauth/token', data=data, auth=(client_id, client_secret))
    print(response.status_code)
    # print(response.text)  # Print the raw response content
    return response.json()['access_token']


def get_item_data(item_id, access_token):
    url = f"https://us.api.blizzard.com/data/wow/item/{item_id}"
    params = {
        "namespace": "static-us",
        "locale": "en_US",
        "access_token": access_token
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request failed for item {item_id}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON response for item {item_id}: {e}")
        return None
