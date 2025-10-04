# spotify-data-analysis
Data analysis project from spotify based on csv from Spotify Global
https://charts.spotify.com/charts/overview/global

**spotify_chart_csvbuttonclicker.py**
Run to download Spotify Global CSV files by automating clicking the button in the page
Code structure
Libraries:
1. selenium & related packages
2. webdriver_manager.chrome
3. time
4. datetime
Functions:
1. generate_date_list(start_date, end_date)
    - Generates list of dates between start_date and end_date (inclusive)
    - Uses a simple while loop to append the requested dates to the list
    - Returns the list of dates
2. setup_driver()
    - Initializes chrome driver
    - Many options to optimize usage
3. download_csv_for_date(driver, date, is_first_run=False)
    - Downloads csv for each specific date
    - In the first run, opens the browser, tell user to login. Click enter on terminal after login.
    - After login and first run, will not ask to login again
    - Looks for the csv download button within the page through the selector
4. main()
    - Runs all the functions
    - Gets the START_DATE and END_DATE to generate list of dates
    - Runs the download_csv_for_date function for each date and downloads the csv files
    - Extra print lines for debugging and showing progress

