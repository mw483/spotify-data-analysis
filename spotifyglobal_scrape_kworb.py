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



