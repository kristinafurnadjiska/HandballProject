from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import pandas as pd

def get_column_names(driver):
    columns_path = "//*[@class='table-wrapper']/table/thead/tr/th"
    columns = wait_and_find_all(driver, columns_path)

    column_names = []
    for column in columns:
        column_names.append(column.text.strip())
    
    return column_names

def get_player_data(row, season):
    stats = []

    columns = row.find_elements(By.TAG_NAME, 'td')

    for column in columns:
        stats.append(column.text.strip())
    
    player_dict = {
        'Rank' : stats[0],
        'Player' : stats[1],
        'Team' : stats[2],
        'Position' : stats[3],
        'Games' : stats[4],
        'Goals ⇵' : stats[5],
        'Shots ⇵' : stats[6],
        'Shooting Accuracy ⇵' : stats[7],
        'Season' : season
    }

    return player_dict
    
def wait_and_find(driver, x_path, time=10):
    WebDriverWait(driver, time).until(
        EC.presence_of_element_located((By.XPATH, x_path))
    )

    return driver.find_element(By.XPATH, x_path)

def wait_and_find_all(driver, x_path, time=10):
    WebDriverWait(driver, time).until(
        EC.presence_of_all_elements_located((By.XPATH, x_path))
    )

    return driver.find_elements(By.XPATH, x_path)

def open_page(url):
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    driver.get(url)

    return driver

def accept_cookies(driver):

    cookie_button_path = "//button[@data-cy='banner-ack-btn']"
    cookie_button = wait_and_find(driver, cookie_button_path, 10)

    cookie_button.click()

def find_next_button(driver):
    try:

        next_button_path = "//button[text()='forward']"
        next_button = wait_and_find(driver, next_button_path)

        print(next_button.get_attribute('class'))

        if 'disabled' in next_button.get_attribute('class'):
            return None  
        
        return next_button

    except Exception:
            return None  
    
def find_seasons(driver):

    dropdown_path = "(//div[contains(@class, 'v-select__selection')])[3]"

    dropdown = wait_and_find(driver, dropdown_path, 2)
    dropdown.click()


    container_path = "//div[@class = 'v-overlay-container']"
    container = wait_and_find(driver, container_path, 10)


    element_path = "v-list-item"
    elements = container.find_elements(By.CLASS_NAME, element_path)

    seasons = []

    for el in elements:
        if el.text not in seasons:
            seasons.append(el.text)

    dropdown = wait_and_find(driver, dropdown_path, 2)
    dropdown.click()

    return seasons

def open_season(driver, season):

    dropdown_path = "(//div[contains(@class, 'v-select__selection')])[3]"
    dropdown = wait_and_find(driver, dropdown_path, 2)

    ActionChains(driver).scroll_to_element(dropdown).click(dropdown).perform()


    container_path = "//div[@class = 'v-overlay-container']"
    container = wait_and_find(driver, container_path, 10)

    season_path = f"//div[contains(text(), '{season}')]"
    season = wait_and_find_all(container, season_path, 10)
    season = season[-1]

    ActionChains(driver).scroll_to_element(season).click(season).perform()

def collect_season_player_data(driver, season):

    players = []

    rows_path = "//*[@class='table-wrapper']/table/tbody/tr"
    rows = wait_and_find_all(driver, rows_path)

    while True:
        if len(rows) > 1:
            break

        rows = wait_and_find_all(driver, rows_path)

    for row in rows:
        
        player = get_player_data(row, season)
        players.append(player)

    return players    

def collect_season_data(driver, season):

    open_season(driver, season)

    players = []

    buttons_path = "//div[@class='pagination']/button"
    buttons = wait_and_find_all(driver, buttons_path)
    last_element = buttons[-2]
    size = int(last_element.text) + 1

    for i in range(1, size):

        current_button_path = f"//div[@class='pagination']/button[contains(text(), '{i}')]"
        current_button = wait_and_find(driver, current_button_path)

        ActionChains(driver).scroll_to_element(current_button).click(current_button).perform()
        page_players = collect_season_player_data(driver, season)
        players.extend(page_players)

    return players

def save_to_csv(players, column_names, season):

    escape_season = season.replace("/", "_")
    file_name = f"players_stats_{escape_season}.csv"

    data = pd.DataFrame(data=players, columns=column_names)
    data.to_csv(file_name, encoding='utf-8')

    print(f'Saved {len(data)} records to {file_name}')

if __name__ == '__main__':

    url = 'https://www.daikin-hbl.de/en/feldspieler-1'
    start = 1
    end = 9

    driver = open_page(url)
    accept_cookies(driver)

    columns = get_column_names(driver)
    columns.append('Season')


    seasons = find_seasons(driver)

    for season in seasons[start:end]:
        players = collect_season_data(driver, season)
        save_to_csv(players, columns, season)

    driver.quit()

