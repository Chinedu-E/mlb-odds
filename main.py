import time

import schedule
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from utils import MainCategory

categories = {
    'batter-props':['home-runs', 'hits', 'total-bases', 'rbis', 'runs-scored', 'hits-+-runs-+-rbis', 'stolen-bases', 'strikeouts', 'singles', 'doubles', 'walks'],
    'pitcher-props':['strikeouts-thrown', 'outs-recorded', 'hits-allowed', 'earned-runs-allowed', 'walks-allowed']
}

options = Options()
options.add_argument("--silent")
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--mute-audio")
options.add_argument("--allow-running-insecure-content")
options.add_argument("--disable-gpu")
options.add_argument("--disable-logging")
user_agent = 'Moilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebkit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
options.add_argument(f"user-agent={user_agent}")


def initialize_driver():
    return webdriver.Chrome(options=options)


def get_odds(multithread: bool):
    batter_props = MainCategory('batter-props', categories['batter-props'])
    pitcher_props = MainCategory('pitcher-props', categories['pitcher-props'])
    print("Gathering data for main category: batter props")
    batter_props.gather_odds(initialize_driver, multithread)
    print("Gathering data for main category: pitcher props" )
    pitcher_props.gather_odds(initialize_driver, multithread)

    df = batter_props + pitcher_props
    print(df)


def main(args):
    get_odds(args.multithread) # Run in it once on program startup

    schedule.every(20).minutes.do(get_odds, args.multithread)

    # Main loop to run the scheduled tasks
    while True:
        # Run pending scheduled tasks
        schedule.run_pending()
        # Wait for 1 minute before checking again
        time.sleep(60)




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--multithread', action='store_false', help='Enable multithreading')
    args = parser.parse_args()
    main(args)