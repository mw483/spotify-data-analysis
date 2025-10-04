#client ID: 4bbb1a4e918e4a158560ed09e9c6f9e5
#redirect uri: https://example.org/callback

import spotipy
from spotipy.oauth2 import SpotifyOAuth

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="4bbb1a4e918e4a158560ed09e9c6f9e5",
                                               client_secret="d74337f850ab439eb85d628be15c9d08",
                                               redirect_uri="https://example.org/callback",
                                               scope="user-library-read"))

twice_uri = 'spotify:artist:7n2Ycct7Beij7Dj7meI4X0'

results = sp.artist_top_tracks(twice_uri)

for track in results['tracks'][:10]:
    print(track['name'])

artist = "Twice"
track = "TAKEDOWN (JEONGYEON, JIHYO, CHAEYOUNG)"

track_id = sp.search(q='artist:' + artist + ' track:' + track, type='track')

track = sp.track("1rKQjUhF9zFJmuUotr3VkV")
popularity = track["popularity"]

print(f"Popularity of TAKEDOWN (JEONGYEON, JIHYO, CHAEYOUNG) is {popularity}")