import json
import os
import traceback
from typing import Union

from dotenv import load_dotenv
from telegram import Bot
import re
from bs4 import BeautifulSoup

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import Chrome
from fake_useragent import UserAgent
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()


class Client:

    def __init__(self, bot_token: str, channel_id: Union[int, str]):
        """Constructor for client. Accepts bot_token adn channel_id as parameters."""
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.batch_size = 500
        self.bot = Bot(token=self.bot_token)

    def fetch_prices(self) -> dict:

        ua = UserAgent()

        options = Options()
        options.headless = True
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-extensions")
        options.add_argument("--start-maximized")
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument(f"user-agent={ua.random}")

        driver = Chrome(service=Service(ChromeDriverManager().install()), options=options)

        driver.maximize_window()
        driver.get('https://dexscreener.com/ethereum')

        price_dict = {}
        time.sleep(5)
        while True:
            for _ in range(10):
                try:
                    text = driver.find_element(By.XPATH, '//*[contains(text(), "Showing")]').text
                    break
                except Exception as e:
                    time.sleep(1)
            else:
                break
            rows = driver.find_element(By.TAG_NAME, 'main').find_elements(By.CSS_SELECTOR, 'a.chakra-link')

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            pairs = soup.find('main').find_all('a', class_='chakra-link')
            for pair in pairs:
                try:
                    token_name = pair.div.find_all('span')[-1].text
                    try:
                        price = pair.find_all('div')[1].span['title']
                    except:
                        price = pair.find_all('div')[1].text
                    liq = pair.find_all('div')[8].text
                    last_letter = liq[-1]
                    liq_float = float(liq[1:-1].replace('.', ''))
                    if last_letter == 'M' or (last_letter == 'K' and liq_float > 50000):
                        price = float(price.replace('$', '').replace(',', ''))
                        if token_name not in price_dict:
                            price_dict[token_name] = price
                except:
                    continue

            text = driver.find_element(By.XPATH, '//*[contains(text(), "Showing")]').text
            s, e, total = re.findall(r'[0-9,]+', text)
            total = int(total.replace(',', ''))
            e = int(e.replace(',', ''))
            if e >= total:
                break
            else:
                driver.execute_script('arguments[0].click();', rows[-1])
        driver.quit()
        return price_dict

    def do(self) -> None:
        """
        Main function. Fetches list of tokens, fetches prices for each token, and sends a message if price is above ATH.
        Finally, saves new ATH to file. This function is called every minute.
        :return:
        """
        while True:
            with open('prices.json', 'r') as f:
                ath_values = json.load(f)
            new_prices = self.fetch_prices()
            for token, price in new_prices.items():
                if token not in ath_values:
                    ath_values[token] = price
                else:
                    if price > ath_values[token]:
                        ath_values[token] = price
                        self.send_message(token, price)
            with open('prices.json', 'w') as f:
                json.dump(ath_values, f)
            time.sleep(60)

    def send_message(self, name: str, price: float) -> None:
        price_str = f'{price:,.20f}'.rstrip('0') if 'e' in str(price) else f'{price:,}'
        message = f'Dexscreener\n\n{name} reached new ATH!\n' \
                  f'Current price: ${price_str}'
        self.bot.send_message(chat_id=self.channel_id, text=message, timeout=30)
        time.sleep(3)


BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
client = Client(BOT_TOKEN, CHANNEL_ID)

try:
    client.do()
except Exception:
    print(traceback.format_exc())
    # client.bot.send_message(812891027, traceback.format_exc(), timeout=30)
