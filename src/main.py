from flask import Flask, redirect, request, render_template
import requests
import json
from uuid import uuid4 as uuid
from os import getenv

SPOTIFY_CLIENT_ID = getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:3000/callback')
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


class CodeState:
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
    
    def set_token_data(self, access_token, refresh_token, token_type, expires_in):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_type = token_type
        self.expires_in = expires_in
    
    def get_token_data(self):
        return self.access_token, self.refresh_token, self.token_type, self.expires_in


USER_CODE = CodeState()


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
    USER_CODE.set_code(auth_token)
    code_payload = {
        "grant_type": "authorization_code",
        "code": USER_CODE.get_code(),
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
    USER_CODE.set_token_data(access_token, refresh_token, token_type, expires_in)
    return redirect("/")


@app.route("/")
def index():
    if USER_CODE.get_code() == "":
        return redirect("/login")

    (access_token, refresh_token, token_type, expires_in) = USER_CODE.get_token_data()
    # Auth Step 6: Use the access token to access Spotify API
    authorization_header = {"Authorization": "Bearer {}".format(access_token)}

    # Get profile data
    user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
    profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)
    profile_data = json.loads(profile_response.text)
    print("profile_data: ", profile_data)

    # Get user playlist data
    playlist_api_endpoint = "{}/playlists".format(profile_data.get("href"))
    playlists_response = requests.get(playlist_api_endpoint, headers=authorization_header)
    playlist_data = json.loads(playlists_response.text)

    # Get episodes data
    episodes_api_endpoint = "{}/me/episodes".format(SPOTIFY_API_URL)
    episodes_response = requests.get(episodes_api_endpoint, headers=authorization_header)
    episodes_data = json.loads(episodes_response.text)

    # Combine profile and playlist data to display
    context = {
        "profile": json.dumps(profile_data, indent=2),
        "playlists": json.dumps(playlist_data, indent=2),
        "episodes": json.dumps(episodes_data, indent=2),
    }
    return render_template("index.html", context=context)


def main():
    app.run(port=3000, debug=True)


if __name__ == "__main__":
    main()
