from enum import Enum

from flask import redirect


class Routes(Enum):
    home = '/'
    login = '/login'
    callback = '/callback'
    refresh_token = '/refresh-token'
    saved_shows = '/saved-shows'
    show_episodes = '/show/<show_id>/episodes'


def refresh_access_token(status_code: int, next_url: Routes):
    if status_code != 200:
        return redirect(
            Routes.refresh_token.value + f"?next={next_url}"
        )
