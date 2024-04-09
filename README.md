
# MLB Odds Web Scraping
This is a Python application for web scraping MLB (Major League Baseball)
player odds from DraftKings Sportsbook using the Selenium library. The scraped data
will be returned as a pandas dataframe



## Technologies Used
- Python
- Selenium (for webpage loading)
- BeautifulSoup (for HTML parsing)
- Pandas (Displaying scraped table)
- Concurrent programming (Threading for perfomance gains)
- Schedule (For running functions at certain intervals)
## Methodology
- **Initialize WebDriver**: Set up a Selenium WebDriver with Chrome options configured for headless browsing.
- **Define Categories**: Define the main categories for player props, such as batter props and pitcher props, along with their corresponding subcategories.
- **Scrape Odds**: Implement web scraping functions to extract odds data for each subcategory using BeautifulSoup and WebDriver.
- **Multithreaded Scraping**: Use concurrent programming techniques to execute the scraping process for multiple subcategories concurrently, improving efficiency. This was made easier due to fact the url always took the form `https://sportsbook.draftkings.com/leagues/baseball/mlb?category=MAIN_CATEGORY&subcategory=SUB_CATEGORY`
- **Data Processing**: Structure the scraped data into a DataFrame format using Pandas for easy analysis and manipulation.
- **Scheduling**: Set up a schedule to periodically scrape the odds data at regular intervals (e.g., every 20 minutes) using the Schedule library.
## Run Locally

1. Clone the project

```bash
   git clone https://github.com/Chinedu-E/mlb-odds.git
```

2. Go to the project directory

```bash
  cd mlb-odds
```

3. Install dependencies (ideally in a virtual env)

```bash
  pip install -r requirements.txt
```

4. Execute the main script to start scraping MLB odds data every 20 minutes:

```bash
  python main.py

```

By default, the program uses multithreading to gather odds from all subcategories. To turn this off, simply add a flag

```bash
  python main.py -m

```

You can also adjust how often you want to gather the odds. The default is 20 minutes. For example if we want every 5 minutes:

```bash
  python main.py --gather-freq 5

```
 You can save the odds to a csv in the current directory for better inspection using the `-s` flag 
 ```bash
  python main.py -s

```

## Additional Information
- If there no events for a given subcategory, the program simply skips that subcategory. This is important to note because some subcategories might be absent depending on when the program is run.

- There also exists a chance that the time at which the program is run coincides with when DraftKings would be updating the odds on their end. This would result in an empty DataFrame.
