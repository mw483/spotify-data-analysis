# %%
# Import libraries
import pandas as pd
import numpy as np
import glob
import re
from datetime import datetime, timedelta
from scipy import stats
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

# File paths with glob
path = "C:\Users\mikae\Documents\GitHub\spotify-data-analysis\spotify_data_analysis_supplementary\spotify_official_csv"
file_pattern = path + '*.csv'

# Read csv files
# Flow: 
# Read all csv and append it into the dataframes list
# Get the dates off the path and put them into their own column
def read_spotify_data(file_pattern):
    all_files = glob.glob(file_pattern)
    dataframes = []

    for file in all_files:
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', file)
        if date_match:
            date_str = date_match.group(1)
        date = pd.to_datetime(date_str)

        df = pd.read_csv(file)
        df['date'] = date
        dataframes.append(df)

    return pd.concat(dataframes, ignore_index=True)

concatenated_df = read_spotify_data(file_pattern)

# Calculate daily streams change, replace NaN with 0.
# Sort values and group by needed because .diff() calculates the diff between rows.
concatenated_df = concatenated_df.sort_values(['track_name', 'date'])
concatenated_df['streams_change'] = concatenated_df.groupby('track_name')['streams'].diff().fillna(0)

# Calculate percentage change of streams
concatenated_df['streams_percent_change'] = concatenated_df.groupby('track_name')['streams'].pct_change().fillna(0) * 100

# Get day of week, mark if weekend
concatenated_df['day_of_week'] = concatenated_df['date'].dt.day_name()
concatenated_df['is_weekend'] = concatenated_df['date'].dt.weekday >= 5

concatenated_df

# Daily stream totals dataframe
daily_totals = concatenated_df.groupby('date').agg({
    'streams' : 'sum',
    'streams_change' : 'mean'
}).rename(columns={
    'streams_change' : 'mean_streams_change'
})

daily_totals['day_of_week'] = daily_totals.index.day_name()
daily_totals['is_weekend'] = daily_totals.index.weekday >= 5

daily_totals

# %%
# Functions to calculate overall trends



# %%
# Functions to filter the dataframe 

def filter_by_rank(df, max_rank):
    return df[(df['rank'] <= max_rank)]

def filter_by_songs(df, songs):
    if isinstance(songs, str):
        songs = [songs]
    return df[df['track_name'].isin(songs)]

def filter_by_date_range(df, start_date, end_date):
    return df[(df['date'] >= start_date) & (df['date'] <= end_date)]

def filter_by_artist(df, artists):
    if isinstance(artists, str):
        artists = [artists]
    return df[df['artist_names'].isin(artists)]

def filter_spotify_data(df, 
                        max_rank=None,
                        songs=None,
                        artists=None,
                        start_date=None,
                        end_date=None,
                        ):
    """
    Master filtering function with multiple optional parameters
    """
    filtered_df = df.copy()
    if max_rank:
        filtered_df = filter_by_rank(filtered_df, max_rank)
    if songs:
        filtered_df = filter_by_songs(filtered_df, songs)
    if artists:
        filtered_df = filter_by_artist(filtered_df, artists)
    if start_date and end_date:
        filtered_df = filter_by_date_range(filtered_df, start_date, end_date)
    
    return filtered_df

# Select filtering parameters to filter
max_rank = 10

SONG_GROUPS = {
    'twice_songs': [
        'TAKEDOWN (JEONGYEON, JIHYO, CHAEYOUNG)',
        'Strategy'
    ],
    'KPDH_songs': [
        'Golden',
        'Your Idol',
        'Soda Pop',
        'How It’s Done',
        'What It Sounds Like',
        'Free',
        'Takedown',
        'TAKEDOWN (JEONGYEON, JIHYO, CHAEYOUNG)',
        'Strategy'
    ],
    'KPDH_songs_excluding_twice': [
        'Golden',
        'Your Idol',
        'Soda Pop',
        'How It’s Done',
        'What It Sounds Like',
        'Free',
        'Takedown',
    ],
    'one_song': [
        'TAKEDOWN (JEONGYEON, JIHYO, CHAEYOUNG)'
    ]
}

start_date = '2025-08-23'
end_date = '2025-09-12'

artists = ['Sabrina Carpenter']

# filter_spotify_data(df, 
#                         max_rank=None,
#                         songs=None,
#                         artists=None,
#                         start_date=None,
#                         end_date=None,
#                         ):

filtered_df = filter_spotify_data(concatenated_df, None, SONG_GROUPS['one_song'], None, start_date, end_date)
print(filtered_df)

# %%
# Plot simple line graph with plotly
fig1 = px.line(filtered_df, x='date', y='streams', color='track_name')
fig1.update_layout(
    title='Daily Spotify Global Streams Change by Track',
    xaxis_title='Date',
    yaxis_title='Streams Percent Change',
    legend_title='Track Name',
    hovermode='x unified',  # Shows all values at a specific date
    width=900,
    height=450,
)

# Weekend background shading for the plot
weekend_dates = filtered_df[filtered_df['is_weekend'] == True]['date'].unique()
for weekend_date in weekend_dates:
    fig1.add_vrect(
        x0 = weekend_date - pd.Timedelta(hours=12),
        x1 = weekend_date + pd.Timedelta(hours=12),
        fillcolor = "gray",
        opacity = 0.2,
        line_width = 0,
    )

fig1.show()

# %%
# Functions for regression analysis