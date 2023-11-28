from flask import Flask, requests
from flask_bootstrap import Bootstrap


# https://medium.com/@maxtingle/getting-started-with-spotifys-api-spotipy-197c3dc6353b
app = Flask(__name__)
app.config['SECRET_KEY'] = 'csumb-otter'
bootstrap = Bootstrap(app)
SPOTIFY_CREATE_PLAYLIST_URL ='https://api.spotify.com/v1/users/{user_id}/playlists'
ACCESS_TOKEN = ''

def create_playlist_on_spotify(name, public):
    response = requests.post(
        SPOTIFY_CREATE_PLAYLIST_URL,
        headers={
            "Authorization" : f"Bearer {ACCESS_TOKEN}"
        },
        json={
            "name": name,
            "public": public
        }
    )
    json_resp = response.json()

    return json_resp

def main():
    playlist = create_playlist_on_spotify(
        name="My Private Playlist",
        public=False
    )
    print(f"Playlist:{playlist}")

if __name__ == '__main__':
    main()


# @app.route('/')
# def index():
#     return 'Hello, this is your Spotify API demo!'

