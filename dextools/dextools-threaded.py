import time

from selenium.webdriver import DesiredCapabilities, ActionChains, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import ChromiumOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import Chrome
from fake_useragent import UserAgent

import random
from multiprocessing import Process
import sys

ua = UserAgent()

if len(sys.argv) < 2:
    headless = False
else:
    headless = True

address = '0x931b22a138893258c58f3e4143b17086a97862f6'
with open('60000proxies.txt', 'r') as f:
    proxies = f.read().splitlines()


def visit(ind):
    for index in range(2):

        try:

            proxy = random.choice(proxies)
            options = ChromiumOptions()
            options.add_argument('--disable-images')
            if headless:
                options.add_argument('--headless')

            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-extensions")
            options.add_argument("--start-maximized")
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument(f"user-agent={ua.random}")
            options.add_argument("--log-level=3")

            options.add_argument(f'--proxy-server={proxy}')

            capabilities = DesiredCapabilities.CHROME.copy()
            capabilities['acceptSslCerts'] = True
            capabilities['acceptInsecureCerts'] = True
            service = Service('chromedriver')
            driver = Chrome(service=service, options=options, desired_capabilities=capabilities)
            # print('driver created')
            driver.maximize_window()
            driver.execute_script(
                'window.innerWidth = 1920; window.innerHeight = 1080; window.outerWidth = 1920; window.outerHeight = 1080;')
            driver.get('https://www.dextools.io/app')

            element = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".search-pairs")))
            element.send_keys(address)
            driver.find_element(By.CSS_SELECTOR, 'div#chains-container').find_elements(By.TAG_NAME, 'a')[2].click()

            for i in range(20):
                try:
                    if element.get_attribute('value') != address:
                        element.clear()
                        element.send_keys(address)

                    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "li.item-container")))
                    driver.find_elements(By.CSS_SELECTOR, "li.item-container")[-1].click()
                    break
                except:
                    pass
            elem = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.fav-item")))

            ActionChains(driver).click(elem).perform()

            try:
                driver.find_element(By.CSS_SELECTOR, 'a.buy-button').click()
            except:
                pass
            time.sleep(1)
            try:
                driver.find_element(By.CSS_SELECTOR, 'button.btn-disclaimer').click()
            except:
                pass

            elem = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.btn-swap-1')))

            soical_icons = driver.find_element(By.CLASS_NAME, 'social-icons').find_elements(By.TAG_NAME, 'a')

            for icon in soical_icons:
                ActionChains(driver).key_down(Keys.CONTROL).click(icon).key_up(Keys.CONTROL).perform()

            ActionChains(driver).click(elem).perform()
            # driver.execute_script("document.getElementsByClassName('btn-swap-1')[0].click();")
            while True:
                try:
                    driver.find_element(By.CSS_SELECTOR, 'div.web3modal-provider-wrapper').click()
                    break
                except:
                    time.sleep(1)
                    ActionChains(driver).click(elem).perform()
            driver.find_element(By.CSS_SELECTOR, 'div#walletconnect-qrcode-close').click()
            time.sleep(1)
            driver.find_element(By.CSS_SELECTOR, 'a.shared-button').click()
            time.sleep(1)
            n_window_handles = len(driver.window_handles)
            for i in driver.find_element(By.CSS_SELECTOR, '.share-btn').find_elements(By.TAG_NAME, 'a'):
                for i in range(20):
                    time.sleep(1)
                    try:
                        ActionChains(driver).key_down(Keys.CONTROL).click(i).key_up(Keys.CONTROL).perform()

                        if len(driver.window_handles) > n_window_handles:
                            n_window_handles = len(driver.window_handles)
                            break
                    except:
                        pass

            driver.quit()


        except Exception as e:
            driver.quit()


if __name__ == '__main__':
    thread = 4
    start = time.time()
    for _ in range(thread):
        process_obj = Process(target=visit, args=(_,))
        process_obj.start()

    for __ in range(thread):
        process_obj.join()
