from os import getenv
import requests


def get_access_token(client_id: str):
    auth_url = 'https://accounts.spotify.com/api/token'
    auth_data = {
        'grant_type': 'client_credentials',
    }
    client_secret = getenv('SPOTIFY_CLIENT_SECRET')
    auth = (client_id, client_secret)

    response = requests.post(auth_url, data=auth_data, auth=auth)
    if response.status_code != 200:
        raise PermissionError(response.json())
    token_data = response.json()
    print(token_data)
    return token_data['access_token']
