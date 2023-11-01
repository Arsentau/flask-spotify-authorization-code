from spotify.auth import get_access_token
from spotify.podcast import get_user_podcasts
from os import getenv


def main():
    client_id = getenv('SPOTIFY_CLIENT_ID')
    try:
        token = get_access_token(client_id)

    except Exception as e:
        print(e)
    try:
        podcast = get_user_podcasts(client_id, token)
        print(podcast)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
