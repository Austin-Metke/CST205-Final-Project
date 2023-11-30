
from flask import Flask, redirect, request, session, url_for, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from datetime import timedelta
import os, requests
from base64 import b64encode
from urllib.parse import urlencode

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key')

app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

# Spotify API credentials
SPOTIPY_CLIENT_ID = 'b4c8b05454bb42089878bd3ae1f648a4'
SPOTIPY_CLIENT_SECRET = '2584b9880d5c4573aa7b1da540ef2128'
SPOTIPY_REDIRECT_URI = 'http://localhost:5000/callback'

# Spotify API scope for playlist creation
SPOTIPY_SCOPE = 'playlist-modify-public playlist-modify-private'

# Spotipy OAuth handler
sp_oauth = SpotifyOAuth(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, scope=SPOTIPY_SCOPE)

# Spotify Web Playback SDK script
SPOTIFY_PLAYER_SCRIPT = 'https://sdk.scdn.co/spotify-player.js'

class CreatePlaylistForm(FlaskForm):
    playlist_name = StringField('Playlist Name', validators=[DataRequired()])
    submit = SubmitField('Create Playlist')

class AddSongForm(FlaskForm):
    track_uri = StringField('Spotify Track URI', validators=[DataRequired()])
    submit = SubmitField('Add Song')

@app.route('/')
def index():
    token_info = session.get('token_info', None)
    user_info = None

    if token_info:
        sp = Spotify(auth=token_info['access_token'])
        user_info = sp.me()

    return render_template('index.html', user_info=user_info)


@app.route('/login')
def login():
    if 'token_info' in session:
        # user is already authenticated
        return redirect(url_for('index'))
    else:
        # user is not authenticated, initiate Spotify login process
        return redirect(sp_oauth.get_authorize_url())


@app.route('/callback')
def callback():
    try:
        token_info = sp_oauth.get_access_token(request.args['code'])
        session['token_info'] = token_info
        session.permanent = True
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Error in callback: {e}")
        return "Error in callback"



@app.route('/logout', methods=['GET', 'POST'])
def logout():
    # Clear user's session
    session.clear()


    # Redirect to the Spotify logout page with a specified next parameter
    spotify_logout_url = 'https://www.spotify.com/logout/'
    next_url = url_for('logout')

    # Construct the complete logout URL
    full_logout_url = f"{spotify_logout_url}?next={next_url}"

    # Perform a temporary redirect (307) to the constructed URL
    return redirect(full_logout_url, code=302)


@app.route('/add_song/<playlist_id>', methods=['GET', 'POST'])
def add_song(playlist_id):
    form = AddSongForm()

    if form.validate_on_submit():
        token_info = session.get('token_info', None)

        if token_info:
            sp = Spotify(auth=token_info['access_token'])
            track_uri = form.track_uri.data

            # Add the song to the playlist
            sp.playlist_add_items(playlist_id, [track_uri])

    return redirect(url_for('view_playlist', playlist_id=playlist_id))

@app.route('/create_playlist', methods=['GET', 'POST'])
def create_playlist():
    form = CreatePlaylistForm()

    if form.validate_on_submit():
        # Retrieve access token from the session
        token_info = session.get('token_info', None)

        if token_info:
            sp = Spotify(auth=token_info['access_token'])
            user_info = sp.me()

            # Create a new playlist
            playlist_name = form.playlist_name.data
            playlist = sp.user_playlist_create(user_info['id'], playlist_name)


            return redirect(url_for('view_playlists'))

    return render_template('create_playlist.html', form=form)

@app.route('/view_playlists')
def view_playlists():
    # Retrieve access token from the session
    token_info = session.get('token_info', None)

    if token_info:
        sp = Spotify(auth=token_info['access_token'])
        user_info = sp.me()

        # Retrieve user's playlists
        playlists = sp.user_playlists(user_info['id'])

        return render_template('view_playlists.html', playlists=playlists)

    return "User not authenticated."


if __name__ == '__main__':
    app.run(debug=True)