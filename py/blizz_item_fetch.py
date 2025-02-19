import requests
from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
SECRET = os.getenv("SECRET")

def get_access_token(client_id, client_secret, region='us'):
    data = { 'grant_type': 'client_credentials' }
    response = requests.post(f'https://{region}.battle.net/oauth/token', data=data, auth=(client_id, client_secret))
    print(response.status_code)
    # print(response.text)  # Print the raw response content
    return response.json()['access_token']


def get_item_data(access_token, item_id):
    url = f'https://us.api.blizzard.com/data/wow/item/{item_id}'
    headers = {
        'Authorization': f'Bearer {access_token}'  # Use user's access token
    }
    params = {
        'namespace': 'static-classic1x-us',
        'locale': 'en_US'
    }
    response = requests.get(url, headers=headers, params=params)
    # print(response.status_code)
    return response.json()
