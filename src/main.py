from flask import Flask, redirect, request, render_template
import requests
import json
from uuid import uuid4 as uuid
from os import getenv

SPOTIFY_CLIENT_ID = getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:3000/callback')
SPOTIFY_SCOPES = getenv('SPOTIFY_SCOPES', 'playlist-modify-public playlist-modify-private user-read-private user-read-email')

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

auth_query_parameters = {
    "client_id": SPOTIFY_CLIENT_ID,
    "response_type": "code",
    "redirect_uri": SPOTIFY_REDIRECT_URI,
    "scope": SPOTIFY_SCOPES,
    "state": STATE,
    "show_dialog": SHOW_DIALOG_str,
}

app = Flask(__name__)


@app.route("/login")
def login():
    redirect_url = f"{SPOTIFY_AUTH_URL}?"
    for param, value in auth_query_parameters.items():
        redirect_url += f"&{param}={value}"
    return redirect(redirect_url)


@app.route("/callback")
def callback():
    # Auth Step 4: Requests refresh and access tokens
    auth_token = request.args['code']
    code_payload = {
        "grant_type": "authorization_code",
        "code": auth_token,
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET,
    }
    print("x" * 100)
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload)

    # Auth Step 5: Tokens are Returned to Application
    response_data = json.loads(post_request.text)

    access_token = response_data["access_token"]
    refresh_token = response_data["refresh_token"]
    token_type = response_data["token_type"]
    expires_in = response_data["expires_in"]
    print("refresh_token: ", refresh_token)
    print("access_token: ", access_token)
    print("token_type: ", token_type)
    print("expires_in: ", expires_in)

    # Auth Step 6: Use the access token to access Spotify API
    authorization_header = {"Authorization": "Bearer {}".format(access_token)}

    # Get profile data
    user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
    profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)
    profile_data = json.loads(profile_response.text)

    # Get user playlist data
    playlist_api_endpoint = "{}/playlists".format(profile_data["href"])
    playlists_response = requests.get(playlist_api_endpoint, headers=authorization_header)
    playlist_data = json.loads(playlists_response.text)

    # Combine profile and playlist data to display
    display_arr = [profile_data] + playlist_data["items"]
    return render_template("index.html", sorted_array=display_arr)


def main():
    app.run(port=3000, debug=True)


if __name__ == "__main__":
    main()
