# Spotify global scraping and analysis from kworb.net (Fixed version)

# Import useful packages
from bs4 import BeautifulSoup
import pandas as pd
import requests
import re
from time import sleep
from datetime import datetime
import numpy as np

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

def parse_kworb_song_page(url, delay=2, view_type='weekly'):
    """
    Scrape streaming data from a kworb song page
    view_type: 'weekly' or 'daily' - determines which data to scrape
    Returns a DataFrame with date, position, streams for each country
    """
    print(f"Scraping: {url} ({view_type} view)")
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

        # Find the appropriate data table based on view type
        if view_type == 'weekly':
            table_container = soup.find('div', class_='weekly')
        elif view_type == 'daily':
            table_container = soup.find('div', class_='daily')
        else:
            print(f"Invalid view_type: {view_type}. Use 'weekly' or 'daily'")
            return None
            
        if not table_container:
            # Fallback to any table if specific container not found
            table_container = soup
            print(f"Could not find {view_type} container, trying any table")
        
        table = table_container.find('table')
        if not table:
            print("Could not find data table")
            return None

        # Get all rows from the table
        rows = table.find_all('tr')
        if len(rows) < 2:
            print("Table has insufficient rows")
            return None

        # Extract headers from the first row
        header_row = rows[0]
        headers = [th.get_text().strip() for th in header_row.find_all('th')]
        
        if not headers or 'Date' not in headers:
            print("Could not find proper table headers")
            return None

        print(f"Found {len(headers)} columns: {headers}")

        # Process data rows
        data_rows = []

        for row in rows[1:]:  # Skip header row
            cells = row.find_all('td')
            if not cells:
                continue

            # Get the date from first cell
            date_cell = cells[0].get_text().strip()
            
            # Skip Total and Peak rows
            if date_cell in ['Total', 'Peak']:
                continue
            
            # Check if this is a valid date row (YYYY/MM/DD format)
            if not re.match(r'^\d{4}/\d{2}/\d{2}', date_cell):
                continue

            try:
                # Convert date format from YYYY/MM/DD to YYYY-MM-DD
                date_obj = datetime.strptime(date_cell, '%Y/%m/%d')
                formatted_date = date_obj.strftime('%Y-%m-%d')

                row_data = {
                    'date': formatted_date, 
                    'title': title, 
                    'artist': artist,
                    'view_type': view_type
                }

                # Process each country column
                for i, country in enumerate(headers[1:], 1):  # Skip 'Date' column
                    if i < len(cells):
                        cell = cells[i]
                        cell_text = cell.get_text().strip()

                        # Parse position and streams
                        if cell_text == '--' or not cell_text:
                            position = None
                            streams = None
                        else:
                            # Look for position (in span with class 'p') and streams (in span with class 's')
                            position_span = cell.find('span', class_='p')
                            streams_span = cell.find('span', class_='s')
                            
                            position = int(position_span.get_text().strip()) if position_span else None
                            
                            if streams_span:
                                streams_text = streams_span.get_text().strip().replace(',', '')
                                streams = int(streams_text) if streams_text.isdigit() else None
                            else:
                                streams = None

                        # Add position and streams for this country
                        row_data[f'{country}_position'] = position
                        row_data[f'{country}_streams'] = streams

                data_rows.append(row_data)

            except Exception as e:
                print(f"Error processing row with date {date_cell}: {e}")
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

        print(f"Successfully scraped {len(df)} {view_type} records")
        return df
    
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def scrape_multiple_songs(song_ids, base_url="https://kworb.net/spotify/track/", delay=2, view_type='weekly'):
    """
    Scrape multiple songs from kworb
    song_ids: list of Spotify track IDs
    view_type: 'weekly' or 'daily' - determines which data to scrape
    """
    all_data = []

    for i, song_id in enumerate(song_ids):
        print(f"\n--- Scraping song {i+1}/{len(song_ids)} ---")
        url = f"{base_url}{song_id}.html"

        df = parse_kworb_song_page(url, delay, view_type)

        if df is not None:
            # Add song_id to the dataframe
            df['song_id'] = song_id
            all_data.append(df)
        else:
            print(f"Failed to scrape data for song ID: {song_id}")

    if all_data:
        # Combine all DataFrames
        combined_df = pd.concat(all_data, ignore_index=True)
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

# Additional utility functions
def get_song_id_from_spotify_url(spotify_url):
    """Extract song ID from Spotify URL"""
    if "track/" in spotify_url:
        return spotify_url.split("track/")[1].split("?")[0]
    return None

def scrape_both_views(song_ids, base_url="https://kworb.net/spotify/track/", delay=2):
    """
    Scrape both weekly and daily data for multiple songs
    song_ids: list of Spotify track IDs
    Returns a dictionary with 'weekly' and 'daily' DataFrames
    """
    results = {}
    
    print("=== Scraping Weekly Data ===")
    weekly_df = scrape_multiple_songs(song_ids, base_url, delay, 'weekly')
    results['weekly'] = weekly_df
    
    print("\n=== Scraping Daily Data ===")
    daily_df = scrape_multiple_songs(song_ids, base_url, delay, 'daily')
    results['daily'] = daily_df
    
    return results
def create_streaming_chart(df, song_id, countries=['Global', 'US', 'PH']):
    """Create a streaming chart for visualization"""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates

        song_data = df[df['song_id'] == song_id].copy()
        if song_data.empty:
            print(f"No data found for song ID: {song_id}")
            return
        
        title = song_data['title'].iloc[0]
        artist = song_data['artist'].iloc[0]
        view_type = song_data['view_type'].iloc[0] if 'view_type' in song_data.columns else 'weekly'

        plt.figure(figsize=(12,8))

        for country in countries:
            streams_col = f'{country}_streams'
            if streams_col in song_data.columns:
                data = song_data.dropna(subset=[streams_col])
                if not data.empty:
                    plt.plot(data['date'], data[streams_col], marker='o', label=country, linewidth=2)

        plt.title(f'{view_type.capitalize()} Streams: {title} by {artist}', fontsize=14, fontweight='bold')
        plt.xlabel('Date')
        plt.ylabel(f'{view_type.capitalize()} Streams')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Format x-axis based on view type
        if view_type == 'daily':
            plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=7))
        else:
            plt.gca().xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
            
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.show()
        
    except ImportError:
        print("Matplotlib not installed. Install with: pip install matplotlib")
    except Exception as e:
        print(f"Error creating chart: {e}")

# Example usage
if __name__ == "__main__":
    # Example song IDs (you can replace with your own)
    song_ids = [
        "19GxfaRs5KdurzPKLVX3Cq",  # TWICE - TAKEDOWN
        "1CPZ5BxNNd0n0nF4Orb9JS",  # Golden (from your original example)
    ]

    print("Scraping song streaming data from kworb.net...")

    # Option 1: Scrape only weekly data
    print("\n=== Weekly Data Only ===")
    weekly_df = scrape_multiple_songs(song_ids, delay=2, view_type='weekly')
    if weekly_df is not None:
        weekly_df.to_csv('kworb_weekly_data.csv', index=False)
        print(f"Weekly data saved to 'kworb_weekly_data.csv' ({len(weekly_df)} records)")

    # Option 2: Scrape only daily data  
    print("\n=== Daily Data Only ===")
    daily_df = scrape_multiple_songs(song_ids, delay=2, view_type='daily')
    if daily_df is not None:
        daily_df.to_csv('kworb_daily_data.csv', index=False)
        print(f"Daily data saved to 'kworb_daily_data.csv' ({len(daily_df)} records)")

    # Option 3: Scrape both weekly and daily data
    print("\n=== Both Weekly and Daily Data ===")
    both_data = scrape_both_views(song_ids, delay=2)
    
    if both_data['weekly'] is not None:
        both_data['weekly'].to_csv('kworb_weekly_data.csv', index=False)
        print(f"Weekly data: {len(both_data['weekly'])} records")
        
    if both_data['daily'] is not None:
        both_data['daily'].to_csv('kworb_daily_data.csv', index=False)
        print(f"Daily data: {len(both_data['daily'])} records")

    # Analyze trends
    if weekly_df is not None:
        analyze_streaming_trends(weekly_df, 'Global')
        
    if daily_df is not None:
        analyze_streaming_trends(daily_df, 'Global')
        
    # Create charts
    if weekly_df is not None and len(song_ids) > 0:
        create_streaming_chart(weekly_df, song_ids[0], ['Global', 'US', 'PH'])
        
    if daily_df is not None and len(song_ids) > 0:
        create_streaming_chart(daily_df, song_ids[0], ['Global', 'US', 'PH'])

print("Kworb scraper ready!")
print("Usage examples:")
print("- Weekly data: scrape_multiple_songs(song_ids, view_type='weekly')")
print("- Daily data: scrape_multiple_songs(song_ids, view_type='daily')")
print("- Both views: scrape_both_views(song_ids)")