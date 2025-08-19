# Spotify global scraping and analysis from kworb.net (Static data)

# Import useful packages
from bs4 import BeautifulSoup
import pandas as pd
import requests
import re
from time import sleep
from datetime import date, timedelta
import matplotlib.pyplot as plt
import numpy as np

# map site
url = "https://kworb.net/spotify/track/19GxfaRs5KdurzPKLVX3Cq.html"

def get_song_metadata(soup):
    """Extract song and metadata from page"""
    try:
        # Get all text content from the page
        title_text = soup.get_text()

        # Extract title
        title_match = re.search(r'Title:\s*(.+)', title_text)
        title = title_match.group(1).strip() if title_match else "Unknown"

        # Extract artist (between brackets after "Artist:")
        artist_match = re.search(r'Artist:\s*(.+)', title_text)
        artist = artist_match.group(1).strip() if artist_match else "Unknown"

        return title, artist
    except:
        return "Unknown", "Unknown"

def parse_kworb_song_page(url, delay=2):
    """
    Scrape streaming data from a kworb song page
    Returns a DataFrame with date, position, streams for each country
    """
    print(f"Scraping: {url}")
    # Set up headers to look like a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        # Make the HTTP Request
        response = requests.get(url, headers=headers)
        sleep(delay)

        if response.status_code != 200:
            print(f"Failed to fetch {url}. Status code: {response.status_code}")
            return None        
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get song metadata
        title, artist = get_song_metadata(soup)
        print(f"Song: {title} by {artist}")

        # Find the data table (usually the first table with streaming data)
        text_content = soup.get_text()        

        # Split by lines and process the tabular data
        lines = text_content.split('\n')

        # Find the header line with countries
        header_idx = None
        country_headers = []

        for i, line in enumerate(lines):
            if 'Date' in line and 'Global' in line and 'Total' in line:
                # This is our header line
                header_idx = i
                # Split and clean the header
                countries = [col.strip() for col in line.split('|') if col.strip()]
                country_headers = countries
                break           
            if not header_idx:
                print("Could not find data table header")
                return None

        print (f"Found {len(country_headers)} columns: {country_headers[:5]}...") 

        # Process data rows
        data_rows = []

        for i in range(header_idx + 1, len(lines)):
            line = lines[i].strip()

            # Skip empty lines and non-data lines
            if not line or 'Total' in line or 'Peak' in line:
                continue

            # Check if this line contains a date (YYYY/MM/DD format)
            if re.match(r'^\d{4}/\d{2}/\d{2}', line):
                # Split by | and process
                columns = [col.strip() for col in line.split('|') if col.strip()]

                if len(columns) >= len(country_headers):
                    try:
                        date_str = columns[0]
                        # Convert date format from YYYY/MM/DD to YYYY-MM-DD
                        date_obj = datetime.striptime(date_str, '%Y/%m/%d')
                        formatted_date = date_obj.strftime('%Y-%m-%d')

                        row_data = {'date': formatted_date, 'title': title, 'artist': artist}

                        # Process each country column
                        for j, country in enumerate(country_headers[1:], 1): # Skip 'Date' column
                            if j < len(columns):
                                cell_value = columns[j]

                                # Parse position and streams from format like "59 (12,988,280)" or "--
                                if cell_value == '--' or not cell_value:
                                    position = None
                                    streams = None
                                else:
                                    # Extract position and streams using regex
                                    match = re.match(r'(\d+)\s*\(([0-9,]+)\)', cell_value)
                                    if match:
                                        position = int(match.group(1))
                                        streams = int(match.group(2).replace(',', ''))
                                    else:
                                        # Handle cases where only streams are given
                                        streams_match = re.search(r'([0-9,]+)', cell_value)
                                        if streams_match:
                                            position = None
                                            streams = int(streams_match.group(1).replace(',', ''))
                                        else:
                                            position = None
                                            streams = None

                                    # Add position and streams for this country
                                    row_data[f'{country}_position'] = position
                                    row_data[f'{country}_streams'] = streams
                            
                            data_rows.append(row_data)    

                    except Exception as e:
                        print(f"Error processing line: {line[:50]}... Error: {e}")
                        continue    

        if not data_rows:
            print("No data rows found")
            return None

        # Create DataFrame
        df = pd.DataFrame(data_rows)

        # Convert date column to datetime
        df['date'] = pd.to_datetime(df['date'])

        # Sort by date
        df = df.sort_values('date')

        print(f"Successfully scraped {len(df)} daily records")
        return df
    
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def scrape_multiple_songs(song_ids, base_url="https://kworb.net/spotify/track/", delay=2)
    """
    Scrape multiple songs from kworb
    song_ids: list of Spotify track IDs
    """
    all_data = []

    for i, song_id in enumerate(song_ids):
        print(f"\n--- Scraping song {i+1}/{len(song_ids)} ---")
        url = f"{base_url}{song_id}.html"

        df = parse_kworb_song_page(url, delay)

        if df is not None:
            # Add song_id to the dataframe
            df['song_id'] = song_id
            all_data.append(df)
        else:
            print(f"Failed to scrape data for song ID: {song_id}")

    if all_data:
        # Combine all DataFramse
        combined_dd = pd.concat(all_data, ignore_index=True)
        return combined_df
    else:
        print("No data was successfully scraped")
        return None
    
def analyze_streaming_trends(df, country='Global'):
    """
    Analyze streaming trends for a specific country
    """
    if df is None or df.empty:
        print("No data to analyze")
        return
    
    streams_col = f'{country}_streams'
    position_col = f'{country}_position'

    if streams_col not in df.columns:
        print(f"No data found for {country}")
        available_countries = [col.replace('_streams', '') for col in df.columns if '_streams' in col]
        print(f"Available countries: {available_countries}")
        return
    
    # Group by song for analysis
    for song_id in df['song_id'].unique():
        song_data = df[df['song_id'] == song_id].copy()
        song_data = song_data.dropna(subset=[streams_col])

        if song_data.empty:
            continue

        title = song_data['title'].iloc[0]
        artist = song_data['artist'].iloc[0]

        print(f"\n=== {title} by {artist} ({country}) ===")
        print(f"Date range: {song_data['date'].min().strftime('%Y-%m-%d')} to {song_data['date'].max().strftime('%Y-%m-%d')}")
        print(f"Total days tracked: {len(song_data)}")

        if not song_data[streams_col].isna().all():
            total_streams = song_data[streams_col].sum()
            avg_daily_streams = song_data[streams_col].mean()
            peak_streams = song_data[streams_col].max()
            peak_date = song_data.loc[song_data[streams_col].idxmax(), 'date']

            print(f"Total streams: {total_streams:,}")
            print(f"Average daily streams: {avg_daily_streams:,.0f}")
            print(f"Peak daily streams: {peak_streams:,} on {peak_date.strftime('%Y-%m-%d')}")
        
        if position_col in song_data.columns and not song_data[position_col].isna().all():
            best_position = song_data[position_col].min()
            best_position_date = song_data.loc[song_data[position_col].idxmin(), 'date']
            print(f"Best chart position: #{best_position} on {best_position_date.strftime('%Y-%m-%d')}")

# Example usage
if __name__ == "__main__":
    # Example song IDs (you can replace with your own)
    song_ids = [
        "19GxfaRs5KdurzPKLVX3Cq",  # TWICE - TAKEDOWN
        "1CPZ5BxNNd0n0nF4Orb9JS",  # Golden (from your original example)
    ]

    print("Scraping song streaming data from kworb.net...")

    # Scrape the data
    df = scrape_multiple_songs(song_ids, delay =2)

    if df is not None:
        # Save to csv
        df.to_csv('kworb_streaming_data.csv', index=False)
        print(f"\nData saved to 'kworb_streaming_data.csv'")
        print(f"Total records: {len(df)}")
        






            


                                





