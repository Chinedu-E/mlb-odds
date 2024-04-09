import datetime
import re
import urllib
import unicodedata
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from bs4 import BeautifulSoup



@dataclass
class EventInfo:
    """
    Represents information about an event.
    """
    home_team: str
    away_team: str
    game_time: str

    def __post_init__(self):
        """
        Post-initialization method to split the game time into local and UTC times, and set the game date.
        """
        self.split_game_time()

    def split_game_time(self):
        """
        Split the game time into local and UTC times, and set the game date.
        """
        day, time_str = self.game_time.split(' ')
        if day == 'Tomorrow':
            self.game_date = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        else:
            self.game_date = datetime.datetime.now().strftime('%Y-%m-%d')
        full_time_str = f'{self.game_date} {time_str}'
        time_obj = datetime.datetime.strptime(full_time_str, '%Y-%m-%d %I:%M%p')
        self.game_time_local = time_obj.strftime("%H:%M")
        self.game_time_utc = time_obj.astimezone(datetime.timezone.utc).strftime("%H:%M")
        
        


class MainCategory:
    def __init__(self, category: str, subcategories: list[str]):
        self.main_category = category
        self.subcategories = subcategories


    def gather_odds(self, driver_initializer, multithread: bool) -> pd.DataFrame:
        """
        Gather odds data for all subcategories within the main category.

        Parameters:
        - driver_initializer: The driver initializer function used to initialize the Selenium web driver.

        Returns:
        - pd.DataFrame: A DataFrame containing the gathered odds data for all subcategories.
        """
        tables = []
        def gather_odds_for_subcategory(category):
            subcategory = SubCategory(self.main_category, category, driver_initializer)
            return subcategory.get_subcategory_odds()

        if multithread:
            with ThreadPoolExecutor() as executor:
                # Submit tasks for each subcategory
                futures = [executor.submit(gather_odds_for_subcategory, category) for category in self.subcategories]

                # Gather results as they become available
                for future in futures:
                    table = future.result()
                    tables.append(table)
        else:
            tables = [gather_odds_for_subcategory(category) for category in self.subcategories]
        category_table = pd.concat(tables)
        category_table.reset_index(drop=True, inplace=True)
        self.df = category_table
        return category_table

    def __add__(self, other) -> pd.DataFrame:
        """
        Concatenate two MainCategory objects' dataframes.

        Parameters:
        - other: The other MainCategory object to concatenate.

        Returns:
        - pd.DataFrame: A DataFrame containing the concatenated data from both MainCategory objects.
        """
        df = pd.concat([self.df, other.df])
        df.reset_index(drop=True, inplace=True)
        return df


class SubCategory:
    """
    Represents a subcategory within a main category.
    """
    def __init__(self, main_category: str, sub_category: str, driver_initializer):
        self.main_category = main_category
        self.sub_category = sub_category
        self.driver = driver_initializer()
        self.build_url()

        self._time_utc = None
        self._time_local = None
        self.soup = self.get_page_soup()


    @property
    def time_local(self) -> str:
        """
        Get the current local time.

        Returns:
        - str: The current local time in the format "%Y-%m-%d %H:%M:%S".
        """
        if self._time_local:
            return self._time_local
        self._time_local = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self._time_local

    @property
    def time_utc(self) -> str:
        """
        Get the current UTC time.

        Returns:
        - str: The current UTC time in the format "%Y-%m-%d %H:%M".
        """
        if self._time_utc:
            return self._time_utc
        self._time_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")
        return self._time_utc
    
    def build_url(self) -> None:
        """
        Build the URL for the subcategory based on the main category and subcategory names.
        """
        sub_enc = urllib.parse.quote_plus(self.sub_category)
        main_enc = urllib.parse.quote_plus(self.main_category)
        self.url = f'https://sportsbook.draftkings.com/leagues/baseball/mlb?category={main_enc}&sub_category={sub_enc}'

    def get_subcategory_odds(self) -> pd.DataFrame:
        """
        Gather odds data for the subcategory.

        Returns:
        - pd.DataFrame: A DataFrame containing the gathered odds data.
        """
        all_events = self.get_all_events()
        if len(all_events) == 0:
            print(f"No events found for the {self.sub_category} subcategory")
            return pd.DataFrame()
        
        print(f"Processing events for {self.sub_category}")

        tables = []
        for event in all_events:
            table = self.get_match_table(event)
            event_info = self.get_event_info(event)
            table["home_team"] = event_info.home_team
            table["away_team"] = event_info.away_team
            table["game_time_local"] = event_info.game_time_local
            table["game_time_utc"] = event_info.game_time_utc
            table["game_date"] = event_info.game_date
            tables.append(table)

        df = pd.concat(tables)
        df["main_category_type"] = self.main_category.replace("-", "_")
        df["sub_category_type"] = self.sub_category.replace("-", "_")
        df["time_now_local"] = self.time_local
        df["time_now_utc"] = self.time_utc

        print(f"Done processing events for {self.sub_category}")
        return df

    def get_page_soup(self) -> BeautifulSoup:
        """
        Get the BeautifulSoup object for the web page.

        Returns:
        - BeautifulSoup: The BeautifulSoup object representing the web page.
        """
        self.driver.get(self.url)
        self.driver.implicitly_wait(10)
        source = self.driver.page_source
        # Saving time
        self.time_local
        self.time_utc
        self.driver.close()
        soup = BeautifulSoup(source, 'html.parser')
        return soup

    def get_match_table(self, match_soup: BeautifulSoup) -> pd.DataFrame:
        """
        Get the match table data from the BeautifulSoup object.

        Parameters:
        - match_soup (BeautifulSoup): The BeautifulSoup object representing the match data.

        Returns:
        - pd.DataFrame: A DataFrame containing the match table data.
        """
        rows = match_soup.find('table').find_all('tr')[1:] # Exclude table header
        players = []
        over_under_totals = []
        odds = []
        odds_types = []
        for row in rows:
            player_name_uncleaned = row.find('th').get_text()
            player_name = player_name_uncleaned.split("New")[0]
            row_data = row.find_all('td')
            over_uncleaned = unicodedata.normalize("NFKC", row_data[0].get_text())
            under_uncleaned = unicodedata.normalize("NFKC", row_data[1].get_text())
            over_under_total1, over = clean_odds(over_uncleaned)
            over_under_total2, under = clean_odds(under_uncleaned)
            
            players += [player_name, player_name]
            odds_types += ['Over', 'Under']
            over_under_totals += [over_under_total1, over_under_total2]
            odds += [over, under]
        data = {
                'player_name': players,
                'over_under_total': over_under_totals,
                'odds': odds,
                "odd_type": odds_types,
            }
        return pd.DataFrame(data)


    def get_all_events(self) -> list[BeautifulSoup]:
        """
        Get all events/matches from the web page.

        Returns:
        - list: A list of BeautifulSoup objects representing the events.
        """
        events = self.soup.find_all('div', class_='sportsbook-event-accordion__wrapper')
        return events
    

    def get_event_info(self, event_soup: BeautifulSoup) -> EventInfo:
        """
        Get information about an event from the BeautifulSoup object.

        Parameters:
        - event_soup: The BeautifulSoup object representing the event.

        Returns:
        - EventInfo: An EventInfo object containing information about the event.
        """
        children = list(event_soup.find('div').children)[-3:-1]
        away_team, home_team = split_teams(children[0].get_text())
        game_time = children[1].get_text()
        return EventInfo(home_team, away_team, game_time)


def clean_odds(text: str) -> tuple[float, int]:
    """
    Clean the odds text and extract the over/under value and odds.

    Parameters:
    - text (str): The odds text to clean and extract information from.

    Returns:
    - tuple[float, int]: A tuple containing the over/under value and the odds.

    Example:
    >>> clean_odds('O 0.5+800')
    (0.5, 800)
    >>> clean_odds('U 0.5−2000')
    (0.5, -2000)
    """
    pattern = r'^([OU])\s(\d+\.\d+)([+\−]\d+)$'

    match = re.match(pattern, text)

    if match:
        _ = match.group(1) # bet type
        over_under = float(match.group(2))
        odds = int(match.group(3).replace('−', '-'))

        return over_under, odds
    else:
        return None, None
    

def split_teams(text: str) -> tuple[str, str]:
    """
    Split the input string into two team names.

    Parameters:
    - text (str): The input string containing team names.

    Returns:
    - tuple[str, str]: A tuple containing the names of the two teams.

    Example:
    >>> split_teams("WAS NationalsatSF Giants")
    ('WAS Nationals', 'SF Giants')
    """
    match = re.search(r'[a-z][A-Z]', text)
    if match:
        team1 = text[:match.start()+1]
        team2 = text[match.start()+1:]
        return team1.strip()[:-2], team2.strip()
    else:
        return None, None
