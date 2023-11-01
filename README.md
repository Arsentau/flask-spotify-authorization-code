# Spotify API

## Problem

Show a list of Spotify user's podcast

## Authentication

There are different way to perform the authorization process in the Spotify API [Check here for more info](https://developer.spotify.com/documentation/web-api/concepts/authorization)

Considering the provided information about the alternatives, the one that fits better is **Authorization Code**.

> If you are developing a long-running application (e.g. web app running on the server) in which the user grants permission only once, and the client secret can be safely stored, then the authorization code flow is the recommended choice.

Overall it works in the following way:

1) Login in [Spotify for Developers](https://developer.spotify)
2) Create a new app in [Dashboard](https://developer.spotify.com/dashboard) and save the `CLIENT_ID` and `CLIENT_SECRET`
3) Use `/login` endpoint (of this implementation) to trigger the authorization process by redirecting to the specific Spotify's OAuth url with the proper query params (here the state param should be included in order to validate the request afterwards)
4) In the Spotify's OAuth url handles the user's auth in Spotify and ask the user to grant determined permissions
5) Once granted the user is redirected to the Redirect URI set in the Dashboard, here we receive the `code` and we can verify the `state` param in order to provide protection against attacks such as cross-site request forgery
6) With the code, the access token can be requested

## How to run this example

### Set the env variables

In this PoC the env variables are set by using [direnv](https://direnv.net/), so you can create a `.envrc` file:

```bash
cp .envrc.example .envrc
```

Then you can edit the `.envrc` file and set the proper values for the variables.

### Run the app in development mode

First it's necessary  to create a virtual environment and install the dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.dev.txt
```

Then you can run the app:

```bash
cd src/ && python3 -m main
```

### Test the app

Go to [http://localhost:3000/login](http://localhost:3000/login) and follow the steps to login in Spotify and grant the permissions.
Once the permissions are granted you will be redirected to the callback url and you will see the list of podcasts.
