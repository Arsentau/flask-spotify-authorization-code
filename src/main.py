import base64
import json
from os import getenv
from uuid import uuid4 as uuid
from routes.routes import Routes, refresh_access_token

import requests
from flask import Flask, redirect, render_template, request

SPOTIFY_CLIENT_ID = getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = getenv(
    'SPOTIFY_REDIRECT_URI',
    'http://localhost:3000/callback'
)
DEFAULT_SCOPES = 'user-library-read user-read-playback-position'
SPOTIFY_SCOPES = getenv('SPOTIFY_SCOPES', DEFAULT_SCOPES)

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

# Server-side Parameters
CLIENT_SIDE_URL = "http://localhost"
PORT = 3000
STATE = uuid()
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()


class AuthState:
    def __init__(self):
        self.code = ""
        self.access_token = ""
        self.refresh_token = ""
        self.token_type = ""
        self.expires_in = ""

    def set_code(self, code):
        self.code = code

    def get_code(self):
        return self.code

    def set_access_token(self, access_token):
        self.access_token = access_token

    def get_access_token(self):
        return self.access_token

    def get_refresh_token(self):
        return self.refresh_token

    def set_token_data(
        self,
        access_token,
        refresh_token,
        token_type,
        expires_in
    ):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_type = token_type
        self.expires_in = expires_in

    def get_token_data(self):
        return self.access_token, self.refresh_token


AUTH = AuthState()


auth_query_parameters = {
    "client_id": SPOTIFY_CLIENT_ID,
    "response_type": "code",
    "redirect_uri": SPOTIFY_REDIRECT_URI,
    "scope": SPOTIFY_SCOPES,
    "state": STATE,
    "show_dialog": SHOW_DIALOG_str,
}

app = Flask(__name__)


@app.route(Routes.login.value)
def login():
    redirect_url = f"{SPOTIFY_AUTH_URL}?"
    for param, value in auth_query_parameters.items():
        redirect_url += f"&{param}={value}"
    return redirect(redirect_url)


@app.route(Routes.refresh_token.value)
def refresh():
    next_url = request.args.get('next', Routes.home.value)
    refresh_token = AUTH.get_refresh_token()
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        "Authorization": "Basic " + base64.b64encode(
            f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
            .encode())
        .decode()
    }
    response = requests.post(
        SPOTIFY_TOKEN_URL,
        data=payload,
        headers=headers
    )

    if response.status_code != 200:
        return redirect(Routes.login.value)
    response_data = json.loads(response.text)
    access_token = response_data.get("access_token")
    AUTH.set_access_token(access_token)
    return redirect(next_url)


@app.route(Routes.callback.value)
def callback():
    # Auth Step 4: Requests refresh and access tokens
    auth_token = request.args['code']
    AUTH.set_code(auth_token)
    code_payload = {
        "grant_type": "authorization_code",
        "code": AUTH.get_code(),
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET,
    }
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload)

    # Auth Step 5: Tokens are Returned to Application
    response_data = json.loads(post_request.text)
    access_token = response_data.get("access_token")
    refresh_token = response_data.get("refresh_token")
    token_type = response_data.get("token_type")
    expires_in = response_data.get("expires_in")

    AUTH.set_token_data(access_token, refresh_token, token_type, expires_in)
    return redirect(Routes.home.value)


@app.route(Routes.home.value)
def index():
    if AUTH.get_code() == "":
        return redirect(Routes.login.value)

    access_token = AUTH.get_access_token()
    # Auth Step 6: Use the access token to access Spotify API
    authorization_header = {"Authorization": "Bearer {}".format(access_token)}

    # Get profile data
    user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
    profile_response = requests.get(
        user_profile_api_endpoint,
        headers=authorization_header
    )

    # Here we check if the access token is expired, if so we should refresh it
    refresh_access_token(profile_response.status_code, Routes.home.value)

    profile_data = json.loads(profile_response.text)

    # Get user playlist data
    playlist_api_endpoint = "{}/playlists".format(profile_data.get("href"))
    playlists_response = requests.get(
        playlist_api_endpoint,
        headers=authorization_header
    )

    playlist_data = json.loads(playlists_response.text)

    # Get episodes data
    episodes_api_endpoint = "{}/me/episodes".format(SPOTIFY_API_URL)
    episodes_response = requests.get(
        episodes_api_endpoint,
        headers=authorization_header
    )
    episodes_data = json.loads(episodes_response.text)

    # Combine profile and playlist data to display
    context = {
        "profile": json.dumps(profile_data, indent=2),
        "playlists": json.dumps(playlist_data, indent=2),
        "episodes": json.dumps(episodes_data, indent=2),
    }
    return render_template("index.html", context=context)


@app.route(Routes.saved_shows.value)
def get_saved_shows():
    if AUTH.get_code() == "":
        return redirect(Routes.login.value)

    access_token = AUTH.get_access_token()
    # Auth Step 6: Use the access token to access Spotify API
    authorization_header = {"Authorization": "Bearer {}".format(access_token)}

    # Get episodes data
    episodes_api_endpoint = "{}/me/shows".format(SPOTIFY_API_URL)
    episodes_response = requests.get(
        episodes_api_endpoint,
        headers=authorization_header
    )
    refresh_access_token(
        episodes_response.status_code,
        Routes.saved_shows.value
    )
    episodes_data = json.loads(episodes_response.text)
    shows = [show['show'] for show in episodes_data['items']]
    shows_links = []
    for show in shows:
        href = Routes.show_episodes.value.replace(
            '<show_id>',
            show['id']
        )
        shows_links.append({'name': show['name'], 'href': href})

    # Combine profile and playlist data to display
    context = {
        "saved_shows": json.dumps(episodes_data, indent=2),
        "shows": shows_links,
    }
    return render_template("saved-shows.html", context=context)


@app.route(Routes.show_episodes.value)
def get_show_episodes(show_id):
    if AUTH.get_code() == "":
        return redirect(Routes.login.value)

    access_token = AUTH.get_access_token()
    # Auth Step 6: Use the access token to access Spotify API
    authorization_header = {"Authorization": "Bearer {}".format(access_token)}

    # Get episodes data
    episodes_api_endpoint = "{}/shows/{}/episodes".format(
        SPOTIFY_API_URL,
        show_id
    )
    episodes_response = requests.get(
        episodes_api_endpoint,
        headers=authorization_header
    )
    refresh_access_token(
        episodes_response.status_code,
        Routes.show_episodes.value
    )
    episodes_data = json.loads(episodes_response.text)

    # Combine profile and playlist data to display
    context = {
        "episodes": json.dumps(episodes_data, indent=2),
    }
    return render_template("show-episodes.html", context=context)

def main():
    app.run(port=3000, debug=True)


if __name__ == "__main__":
    main()
