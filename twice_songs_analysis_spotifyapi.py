#client ID: 4bbb1a4e918e4a158560ed09e9c6f9e5
#redirect uri: https://example.org/callback

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from scipy import stats

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="f88aa52e4f5b4077a997ba7b58167dd4",
                    client_secret="448cc60a566c449b865f075d7eabece1",
                    redirect_uri="https://example.org/callback",
                    scope="playlist-read-private user-library-read"))

# Playlist of all Twice songs + solos
# https://open.spotify.com/playlist/3US084x6JlblpTGhtI1TXA?si=922440a0ff6746a8

all_twice_playlist_id = "3US084x6JlblpTGhtI1TXA"

def get_all_playlist_tracks(id):
    all_tracks = []

    # Initial request
    results = sp.playlist_items(id)

    while results:
        for item in results['items']:
            if item['track']:
                all_tracks.append(item['track'])

        # Since the limit is 100, we need to check the next page
        if results['next']:
            results = sp.next(results)
        else:
            results = None
    
    return all_tracks

all_twice_songs = get_all_playlist_tracks(all_twice_playlist_id)

# Create pandas df from list of songs
df = pd.DataFrame(all_twice_songs)

# Clean up the dataframe
twice_all_songs_info = df[['name','artists','duration_ms','id']]

# Clean up by extracting artist names only
twice_all_songs_info['artist_names'] = twice_all_songs_info['artists'].apply(
    lambda artist_list: ', '.join(artist['name'] for artist in artist_list)
)

# Get duration in seconds and minutes

def convert_to_mm_ss(s):
    minutes = (int(s // 60))
    seconds = (int(s % 60))
    return f"{minutes}:{seconds:02d}"

twice_all_songs_info['duration_s_notrounded'] = twice_all_songs_info['duration_ms'] / 1000
twice_all_songs_info['duration_s'] = twice_all_songs_info['duration_s_notrounded'].round(0)
twice_all_songs_info['duration_min'] = twice_all_songs_info['duration_s'] / 60
twice_all_songs_info['duration_mm_ss'] = twice_all_songs_info['duration_s'].apply(convert_to_mm_ss)

df_v1 = twice_all_songs_info[['name', 'artist_names', 'duration_s', 'duration_min', 'duration_mm_ss', 'id']]

df_v1.to_csv('all_twice_songs_info', index=False, encoding='utf-8-sig')

# --- old ---
# twice_uri = 'spotify:artist:7n2Ycct7Beij7Dj7meI4X0'

# results = sp.artist_top_tracks(twice_uri)

# for track in results['tracks'][:10]:
#     print(track['name'])

# artist = "Twice"
# track = "TAKEDOWN (JEONGYEON, JIHYO, CHAEYOUNG)"

# track_id = sp.search(q='artist:' + artist + ' track:' + track, type='track')

# track = sp.track("1rKQjUhF9zFJmuUotr3VkV")
# popularity = track["popularity"]

