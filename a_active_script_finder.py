# from time import sleep
import os
from os import path
from time import sleep
from selenium import webdriver
# import os
import glob
import pandas as pd

def get_active_scripts_from_nse():
    chrome_options = webdriver.ChromeOptions()
    dl_directory = path.dirname(path.abspath(__file__))
    chrome_options.add_experimental_option(name='detach', value=True)
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": dl_directory,  # Change to your download directory
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    chrome_options.add_argument("--headless")  # Run headless Chrome
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

        return True

    finally:
        # Close the WebDriver
        sleep(2)
        driver.quit()
        pass

# Close the browser
# driver.quit()

def get_active_scripts():
    is_data = False
    while not is_data:
        is_data = get_active_scripts_from_nse()
        # print(is_data)
        if is_data:
            is_data = True
        # print(data)

    if is_data:
        # Directory where the files are located
        dl_directory = path.dirname(path.abspath(__file__))

        # Search for files starting with 'MA-Equities' in the specified directory
        csv_files = glob.glob(path.join(dl_directory, 'MA-Equities*.csv'))
        # Check if any such file exists
        if csv_files:
            # Get the first matching file (if there are multiple, only the first one will be renamed)
            file_to_rename = csv_files[0]

            # Define the new file name
            new_file_name = path.join(dl_directory, 'latest.csv')

            # Rename the file
            os.rename(file_to_rename, new_file_name)

            # print(f"File '{file_to_rename}' renamed to '{new_file_name}'")

            # Analysing latest.csv file
            df = pd.read_csv(new_file_name)

            # Clean the column names (remove extra spaces and newlines)
            df.columns = df.columns.str.strip()

            # Remove commas from numeric columns and convert them to numeric types
            df['LTP'] = df['LTP'].str.replace(',', '').astype(float)
            df['%CHNG'] = df['%CHNG'].astype(float)

            # Filter the data for LTP > 100 and %CHNG > 1%
            # filtered_scripts = df[(df['LTP'] > 100) & ((df['%CHNG'] > 1) | (df['%CHNG'] < -1.5)) & (df['LTP'] < 2000)]
            filtered_scripts = df[(df['LTP'] > 100) & (df['%CHNG'] > 1) & (df['LTP'] < 2000)]
            # Extract the 'SYMBOL' column for the filtered data
            filtered_scripts_list = filtered_scripts['SYMBOL'].tolist()

            # Print the filtered list of scripts
            # print(filtered_scripts_list)

            # Save the filtered list to a text file
            a_latest_scripts = path.join(dl_directory, 'a_latest_scripts.txt')

            with open(a_latest_scripts, 'w') as f:
                for index, row in filtered_scripts.iterrows():
                    f.write(f"{row['SYMBOL']}-{row['LTP']}\n")

        else:
            print("No file starting with 'MA-Equities' found.")


