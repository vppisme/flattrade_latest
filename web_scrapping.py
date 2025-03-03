# from time import sleep
from os import path
from time import sleep
from selenium import webdriver

def get_active_scripts():
    chrome_options = webdriver.ChromeOptions()
    dl_directory = path.dirname(path.abspath(__file__))
    chrome_options.add_experimental_option(name='detach', value=True)
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": dl_directory,  # Change to your download directory
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    # chrome_options.add_argument("--headless")  # Run headless Chrome
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Disable automation flag
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    driver = webdriver.Chrome(chrome_options)
    try:
        # Navigate to the NSE website
        is_element = False
        driver.get("https://www.nseindia.com/market-data/most-active-equities")
        sleep(5)
        driver.get("https://www.nseindia.com/api/live-analysis-most-active-securities?index=value&csv=true")

        return 'Got Data'

    finally:
        # Close the WebDriver
        sleep(2)
        # driver.quit()
        pass

# Close the browser
# driver.quit()


is_data = False

while not is_data:
    data = get_active_scripts()
    print(data)
    if data != None:
        is_data = True
    # print(data)
