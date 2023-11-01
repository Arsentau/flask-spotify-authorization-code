import requests


def get_user_podcasts(user_id, access_token):
    api_url = f'https://api.spotify.com/v1/users/{user_id}/playlists'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    response = requests.get(api_url, headers=headers)
    if response.status_code != 200:
        raise PermissionError(response.json())
    playlists = response.json()
    for playlist in playlists['items']:
        print(playlist['name'])
