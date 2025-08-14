from bs4 import BeautifulSoup
import pandas as pd
import requests
from time import sleep
from datetime import date, timedelta

dates = []
url_list = []
final = []

# date constants
today_date = date.today()
yesterday_date = today_date - timedelta(days=1)

# map site
url = "https://charts.spotify.com/charts/view/regional-global-daily/latest"
start_date = date(2025,6,22)
end_date = yesterday_date