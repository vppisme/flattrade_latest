# from telnetlib import EC
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import telegram_bot
import my_totp


def get_redirect_url(api_url, user_id, passwd, totp_key):

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    # chrome_options.add_experimental_option(name='detach', value=True)
    chrome_options.add_argument("--nos-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Disable automation flag
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")


    driver = webdriver.Chrome(chrome_options)
    driver.get(api_url)
    sleep(3)

    # Get TOTP
    # totp_number = telegram_bot.get_totp_number()
    # print(totp_number)
    totp_number = my_totp.get_totp_code(totp_key)

    # Entering Username
    # username = driver.find_element(By.CSS_SELECTOR, value='#input-19')
    username =  WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '#input-19')))
    # sleep(1)
    # Entering Password
    username.send_keys(str(user_id).strip())

    password = driver.find_element(By.CSS_SELECTOR, value='#pwd')
    password.send_keys(str(passwd).strip())

    # Entering TOTP
    totp = driver.find_element(By.CSS_SELECTOR, value="#pan")
    totp.send_keys(str(totp_number).strip())

    # Click on Submit button
    login_btn = driver.find_element(By.CSS_SELECTOR, value="#sbmt")
    login_btn.send_keys(Keys.ENTER)

    try:
        WebDriverWait(driver, 20).until(EC.url_contains('code'))
        sleep(3)
        redirect_url = driver.current_url
        driver.quit()
        return redirect_url
    except:
        print("Page loading takes too much time")
        driver.quit()
        return None
