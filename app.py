
from flask import Flask, redirect, request, session, url_for, render_template
from flask_wtf import FlaskForm
from flask_session import Session
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from spotipy import Spotify, util
from spotipy.oauth2 import SpotifyOAuth
from datetime import timedelta
import os, requests

app = Flask(__name__)

if __name__ == '__main__':
    app.run(debug=True)

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
Session(app)

# Spotify API credentials
SPOTIPY_CLIENT_ID = 'a3d1083e96f6486b914825dd793e7b0a'
SPOTIPY_CLIENT_SECRET = 'cea29e8759f64f238e82e1d2b266f64e'
SPOTIPY_REDIRECT_URI = 'http://localhost:5000/callback'

# Spotify API scope for playlist creation
SPOTIPY_SCOPE = 'playlist-modify-public playlist-modify-private user-library-read user-top-read playlist-read-private playlist-read-collaborative'

# Spotipy OAuth handler
sp_oauth = SpotifyOAuth(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, scope=SPOTIPY_SCOPE)

class CreatePlaylistForm(FlaskForm):
    playlist_name = StringField('Playlist Name', validators=[DataRequired()])
    submit = SubmitField('Create Playlist')

class AddSongForm(FlaskForm):
    track_uri = StringField('Spotify Track URI', validators=[DataRequired()])
    submit = SubmitField('Add Song')

@app.route('/')
def index():
    user_info = None
    #Check if user is logged in to get user_info
    if isLoggedIn():
        token_info = session['token_info']
        sp = Spotify(auth=token_info['access_token'])
        user_info = sp.me()
    return render_template('index.html', user_info=user_info)

@app.route('/login')
def login():
    if isLoggedIn():
        # user is already authenticated
        return redirect(url_for('index'))
    else:
        # user is not authenticated, initiate Spotify login process
        return redirect(sp_oauth.get_authorize_url())

@app.route('/callback')
def callback():
    token_info = sp_oauth.get_access_token(request.args['code'])
    session['token_info'] = token_info
    return redirect(url_for('index'))

@app.route('/logout', methods=['GET', 'POST'])
def logout():

    # Revoke the access token on Spotify's side
    token = session['token_info']['access_token']
    revoke_url = 'https://accounts.spotify.com/api/token/revoke'
    headers = {'Authorization': f'Bearer {token}'}
    requests.post(revoke_url, headers=headers)

    # Remove the stored token info from the session
    session.clear()

    return redirect(url_for('index'))

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


@app.route('/playlist_maker')
def playlist_maker():
    if(isLoggedIn):
        return render_template('create_playlist.html')

@app.route('/view_playlists')
def view_playlists():

    # Retrieve access token from the session
    token_info = session.get('token_info', None)

    if isLoggedIn():
        sp = Spotify(auth=token_info['access_token'])
        user_info = sp.me()

        # Retrieve user's playlists
        playlists = sp.current_user_playlists()
        print(playlists)
        return render_template('view_playlists.html', playlists=playlists)

    return redirect(url_for('index'))

@app.route('/top_artists/', defaults={'time_range': 'medium_term', 'limit': 10})
@app.route('/top_artists/<time_range>/<int:limit>', methods=['GET'])
def top_artists(time_range='medium_term', limit=10):
    if isLoggedIn():
        artists = get_artists(time_range, limit)
        return render_template('top_artists.html', top_artists=artists['items'], time_range=time_range, limit=limit if limit < artists['total'] else artists['total'])
    return redirect(url_for('index'))

def get_artists(time_range='medium_term', limit=10):
    sp = Spotify(auth_manager=sp_oauth)
    results = sp.current_user_top_artists(time_range=time_range, limit=limit)
    print(results)
    return results
        
@app.route('/top_tracks/', defaults={'time_range': 'medium_term', 'limit': 10})
@app.route('/top_tracks/<time_range>/<int:limit>', methods=['GET'])
def top_tracks(time_range='medium_term', limit=10):
    if isLoggedIn():
        artists = get_top_tracks(time_range, limit)
        return render_template('top_tracks.html', top_tracks=artists['items'], time_range=time_range, limit=limit if limit < artists['total'] else artists['total'])
    return redirect(url_for('index'))


def get_top_tracks(time_range='medium_term', limit=10):
    sp = Spotify(auth_manager=sp_oauth)
    results = sp.current_user_top_tracks(time_range=time_range, limit=limit)
    return results

def isLoggedIn():
        # Check if the access token is present and not expired
        return 'token_info' in session and not sp_oauth.is_token_expired(session['token_info'])
