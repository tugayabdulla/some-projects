import time
import traceback

from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import Chrome
import json
import os
import pandas as pd
import sys
from twocaptcha.solver import TwoCaptcha
import logging

try:
    with open('auth.json', 'r') as f:
        auth = json.load(f)
    username = auth['username']
    password = auth['password']
except:
    username = input('Enter username:\n')
    password = input('Enter password:\n')
    auth = {'username': username, 'password': password}
    with open('auth.json', 'w') as f:
        json.dump(auth, f)

with open('lang_codes.json', 'r') as f:
    lang_codes = json.load(f)


def solveRecaptcha(sitekey, url):
    api_key = 'f857f619691c3d1375bc2d372db545b7'

    solver = TwoCaptcha(api_key)
    for _ in range(3):
        try:
            result = solver.recaptcha(
                sitekey=sitekey,
                url=url)
            break
        except Exception as e:
            print(traceback.format_exc())
            logging.error('Could not connect to 2captcha, trying again')
    else:
        logging.error('Failed 3 times, terminating.')
        sys.exit(0)
    return result


def get_driver():
    for _ in range(3):
        try:
            service = Service(ChromeDriverManager().install())
            break
        except:
            logging.error('Chromedriver installation failed')
    else:
        return None
    driver = Chrome(service=service)
    driver.maximize_window()
    while True:
        try:
            driver.get('https://www.routenote.com/login')
            break
        except:
            pass

    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.ID, 'name')))

    time.sleep(5)
    recaptcha = driver.find_elements(By.ID, 'g-recaptcha-response')
    if len(recaptcha) > 0:
        result = solveRecaptcha(
            "6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-",
            "https://www.google.com/recaptcha/api2/demo")

        code = result['code']
        driver.execute_script(
            "document.getElementById('g-recaptcha-response').innerHTML = " + "'" + code + "'")

    driver.find_element(By.ID, 'name').send_keys(username)
    time.sleep(0.2)
    driver.find_element(By.ID, 'pass').send_keys(password)
    time.sleep(0.2)
    driver.find_element(By.CLASS_NAME, 'rnb_checkbox').click()
    time.sleep(0.2)
    driver.execute_script("scrollBy(0, 100)")
    time.sleep(0.2)

    driver.find_element(By.ID, 'in_signin_button').click()

    try:
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.ID, 'Distribution'))).click()
    except:
        print(traceback.format_exc())
        logging.error('Log in failed')
        return False
    return driver


def do_process(driver, release_folder):
    data = pd.read_excel(os.path.join(release_folder, 'data.xlsx'))
    data = data.astype('str')
    upc = data.iloc[2, 0].strip('nan') or ''
    release_title = data.iloc[2, 1]
    album_version = data.iloc[2, 6].strip('nan') or ''
    is_compilation_album = data.iloc[2, 11] == 'Yes'
    artist_names = data.iloc[2, 12].split(';')
    artist_roles = data.iloc[2, 17].split(';')
    album_genre = data.iloc[2, 22]
    album_secondary_genre = data.iloc[2, 23].strip('nan') or 'None'
    cc_right_year = data.iloc[2, 24]
    cc_right_holder = data.iloc[2, 25]
    sc_right_year = data.iloc[2, 26]
    sc_right_holder = data.iloc[2, 27]
    record_label_name = data.iloc[2, 28]
    release_date = data.iloc[2, 29].replace('-', '/').split()[0]
    sales_start_date = data.iloc[2, 30].replace('-', '/').split()[0]
    explicit_content = data.iloc[2, 31]
    if explicit_content == 'Clean':
        explicit_content = 'Cleaned Version'
    track_titles = list(data.iloc[7:, 2].values)
    track_title_version = list(data.iloc[7:, 7].values)
    track_title_version = [i.strip('nan') or '' for i in track_title_version]
    track_artists = [i.split(';') for i in list(data.iloc[7:, 12].values)]
    track_artist_roles = [i.split(';') for i in list(data.iloc[7:, 17].values)]
    track_languages = list(data.iloc[7:, 22].values)
    spotify_uris = [i.split(';') for i in list(data.iloc[7:, 23].values)]
    isrcs = [i.strip('nan') or '' for i in list(data.iloc[7:, 0].values)]
    audio_language = data.iloc[2, 34]

    try:
        artwork_path = os.listdir(os.path.join(release_folder, 'artwork'))[0]
        print(f'Found artwork file: {artwork_path}')
    except Exception as e:
        print(traceback.format_exc())
        print('\n' * 3)
        print('Could not find artwork file, terminating')
        time.sleep(5)
        sys.exit(0)

    try:
        audio_files = os.listdir(os.path.join(release_folder, 'audios'))
        if len(audio_files) != len(track_titles):
            print(
                'The number of tracks in the spreadsheet and the number of audio files in the folder *audios* does not match, terminating')
            time.sleep(5)
            sys.exit(0)
    except:
        print('There is a problem with audios folder, terminating')
        time.sleep(5)
        sys.exit(0)
    audio_files.sort(key=lambda x: int(x.split('.')[0]))

    while True:
        try:
            driver.get('https://www.routenote.com/rn/create_album')
            break
        except:
            pass
    WebDriverWait(driver, 60).until(EC.presence_of_element_located(
        (By.ID, 'edit_album_info_release'))).send_keys(release_title)
    time.sleep(0.2)
    WebDriverWait(driver, 60).until(EC.presence_of_element_located(
        (By.ID, 'edit_album_info_upc'))).send_keys(upc)
    time.sleep(0.5)

    driver.find_element(By.ID, 'edit-album-save-image').click()

    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'buttoncls')))
    time.sleep(2)
    album_details = driver.find_elements(By.CLASS_NAME, 'buttoncls')[0]

    album_details.click()

    album_version_input = WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.ID, 'album_version')))
    album_version_input.send_keys(album_version)

    if is_compilation_album:
        driver.find_element(By.ID, 'Yes').click()
    else:
        driver.find_element(By.ID, 'No').click()

    n_artists = len(artist_names)
    time.sleep(0.2)
    for i in range(n_artists - 1):
        driver.execute_script("scrollBy(0, 100)")

        driver.find_element(By.ID, 'add_mul').click()

        time.sleep(0.2)

    elem = driver.find_element(
        By.ID, 'edit_album_info_artist')
    for i in artist_names[0]:
        elem.send_keys(i)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located(
        (By.CLASS_NAME, 'autocomplete-suggestion')))
    suggs = driver.find_elements(By.CLASS_NAME, 'autocomplete-suggestion')
    for i in suggs:
        if i.get_attribute('data-val') == artist_names[0]:
            i.click()
            break

    for i in range(2, n_artists + 1):
        artist_name = artist_names[i - 1]
        artist_role = artist_roles[i - 1]
        artist_name_input = driver.find_element(By.ID, f'second_art_{i - 1}')
        for j in artist_name:
            artist_name_input.send_keys(j)
            time.sleep(0.05)
        artist_name_input.send_keys('tt')

        actions = ActionChains(driver)
        actions.move_to_element(artist_name_input)
        actions.click(artist_name_input)
        actions.key_down(Keys.BACKSPACE)
        actions.perform()
        artist_name_input.send_keys(Keys.BACKSPACE)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located(
            (By.XPATH, f'//div[@data-val="{artist_name}"]')))

        suggs = driver.find_elements(
            By.XPATH, f'//div[@data-val="{artist_name}"]')
        for j in suggs:
            print(j.get_attribute('data-val'), artist_name)
            if j.get_attribute('data-val') == artist_name:
                j.click()
                break
        artist_role_select = driver.find_element(By.ID, f'role_{i - 1}')
        select = Select(artist_role_select)
        select.select_by_value(artist_role)
    album_genre_select = Select(
        driver.find_element(By.ID, 'edit_album_info_genre'))
    album_genre_select.select_by_value(album_genre)

    album_secondary_genre_select = Select(
        driver.find_element(By.ID, 'edit_album_info_sec_genre'))
    album_secondary_genre_select.select_by_value(album_secondary_genre)

    driver.find_element(By.ID, 'cpy_year').clear()
    driver.find_element(By.ID, 'cpy_year').send_keys(str(cc_right_year))
    driver.find_element(By.ID, 'cpy_name').send_keys(cc_right_holder)

    driver.find_element(By.ID, 'edit_album_info_pcopyyear').clear()
    driver.find_element(By.ID, 'edit_album_info_pcopyyear').send_keys(
        str(sc_right_year))
    driver.find_element(
        By.ID, 'edit_album_info_pcopyname').send_keys(sc_right_holder)

    record_label_name_input = driver.find_element(
        By.ID, 'edit_album_info_label')
    record_label_name_input.send_keys(record_label_name)

    element = driver.find_element(By.ID, 'edit_album_info_org_date')
    driver.execute_script("arguments[0].removeAttribute('readonly')", element)

    element.send_keys(release_date)

    element = driver.find_element(By.ID, 'edit_album_info_sale_date')
    driver.execute_script("arguments[0].removeAttribute('readonly')", element)
    element.send_keys(sales_start_date)
    explicit_content_select = Select(
        driver.find_element(By.ID, 'edit_album_info_explicit'))
    explicit_content_select.select_by_value(explicit_content)

    lang_select = Select(driver.find_element(
        By.ID, 'edit_album_info_language'))
    lang_select.select_by_value(lang_codes[audio_language])
    driver.execute_script("scrollTo(0, document.body.scrollHeight)")
    driver.find_element(By.ID, 'edit-album-save-image').click()

    WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable((By.CLASS_NAME, 'buttoncls')))
    time.sleep(5)
    add_audio = driver.find_elements(By.CLASS_NAME, 'buttoncls')[1]
    add_audio.click()

    for i in range(len(track_titles) - 1):
        driver.find_element(By.ID, 'rn_track').click()
        time.sleep(0.2)

    driver.execute_script("scrollTo(0, 100)")
    for i in range(len(track_titles)):
        ind = i + 1
        element = driver.find_element(By.ID, f'edit-Origin{ind}')
        path = os.path.join(release_folder, 'audios', audio_files[i])
        element.send_keys(path)

    for i in range(len(track_titles)):
        ind = i + 1
        element = driver.find_element(By.ID, f'edit-tracknio{ind}')
        element.send_keys(track_titles[i])

    url = driver.current_url
    driver.execute_script("scrollTo(0, document.body.scrollHeight)")
    while url == driver.current_url:
        time.sleep(5)

        driver.find_element(By.ID, 'edit-submit').click()

    for i in range(len(track_titles)):
        select = Select(driver.find_element(
            By.ID, f'edit_album_info_explicit{i}'))
        select.select_by_value('Not Explicit')
        lang_select = Select(driver.find_element(
            By.ID, f'edit_album_info_language{i}'))
        lang = track_languages[i]
        lang_select.select_by_value(lang_codes[lang])

    driver.execute_script("scrollTo(0, document.body.scrollHeight)")
    driver.find_element(By.ID, 'edit-submit').click()
    time.sleep(10)
    generate_isrc = driver.find_elements(
        By.XPATH, "//input[@value = 'Generate ISRC']")
    if len(generate_isrc) > 0:
        for i in range(len(generate_isrc)):
            driver.execute_script(
                "arguments[0].scrollIntoView();", generate_isrc[i])
            generate_isrc[i].click()
            time.sleep(0.2)

        driver.execute_script("scrollTo(0, document.body.scrollHeight)")
        driver.find_element(By.ID, 'edit-submit').click()
    im_finished = WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable((By.ID, 'edit-Im-Finished')))

    try:
        im_finished.click()
    except:
        pass

    WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable((By.CLASS_NAME, 'buttoncls')))
    time.sleep(5)
    add_artwork = driver.find_elements(By.CLASS_NAME, 'buttoncls')[2]
    driver.execute_script("arguments[0].scrollIntoView();", add_artwork)
    add_artwork.click()

    driver.find_element(By.ID, 'audio_images1').send_keys(
        os.path.join(release_folder, 'artwork', artwork_path))

    driver.execute_script("scrollTo(0, document.body.scrollHeight)")
    url = driver.current_url
    while url == driver.current_url:
        try:
            driver.find_element(By.ID, 'addart_savbtn').click()
        except:
            time.sleep(10)

    WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable((By.CLASS_NAME, 'buttoncls')))
    time.sleep(5)
    manage_stores = driver.find_elements(By.CLASS_NAME, 'buttoncls')[3]
    driver.execute_script("arguments[0].scrollIntoView();", manage_stores)
    manage_stores.click()

    elem = WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable((By.ID, 'edit-album-save-image')))
    driver.execute_script("arguments[0].scrollIntoView();", elem)
    elem.click()

    elem = WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable((By.ID, 'submit_chk')))
    upc = driver.find_element(By.CLASS_NAME, 'album').find_element(
        By.TAG_NAME, 'span').text
    with open('upc.csv', 'a') as f:
        release_name = release.split('/')[-1]
        f.write(f'{release_name},{upc}')
    elem.click()
    elem = driver.find_element(By.CLASS_NAME, 'distribtnlinkpre')

    driver.execute_script("arguments[0].scrollIntoView();", elem)

    elem.click()
    time.sleep(0.2)

    return True


releases = os.listdir('releases')
untouched = set(releases)
for _ in range(2):
    driver = get_driver()
    releases = list(untouched)
    releases.sort()
    for release in releases:

        result = do_process(driver, os.path.join(
            os.getcwd(), 'releases', release))
        if not result:
            print(f'Trying {release} again, failed')
            result = do_process(driver, os.path.join(
                os.getcwd(), 'releases', release))

        if result:
            untouched.remove(release)
        else:
            print(f'{release} failed again, will try again in the second run')
    driver.quit()
    if len(untouched) == 0:
        break
