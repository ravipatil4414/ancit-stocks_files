#!/usr/bin/env python
# coding: utf-8

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from kite_trade2 import KiteApp
import threading
import pandas as pd
from pyvirtualdisplay import Display

# Replace these variables with your credentials
user_id = "FVK571"       # Login Id
password = "Ravi@966366"  # Login password
twofa = "367896"         # Login Pin or TOTP

def get_enctoken_selenium(user_id, password, twofa):
    display = Display(visible=0, size=(1920, 1080))
    display.start()

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(options=options)
    driver.get('https://kite.zerodha.com/')
    time.sleep(3)

    driver.find_element(By.ID, 'userid').send_keys(user_id)
    driver.find_element(By.ID, 'password').send_keys(password)
    driver.find_element(By.CLASS_NAME, 'button-orange').click()
    time.sleep(3)

    # Debug: Print the page source to check for the 'pin' element
    print(driver.page_source)

    try:
        # Wait for the pin element to be present
        pin_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'pin'))
        )
        pin_element.send_keys(twofa)
        driver.find_element(By.CLASS_NAME, 'button-orange').click()
        time.sleep(3)
    except Exception as e:
        print("Error finding the pin element:", e)
        driver.quit()
        display.stop()
        raise

    cookies = driver.get_cookies()
    driver.quit()
    display.stop()

    for cookie in cookies:
        if cookie['name'] == 'enctoken':
            return cookie['value']

    raise Exception("Failed to obtain enctoken")

# Get the enctoken using Selenium
enctoken = get_enctoken_selenium(user_id, password, twofa)

# Initialize KiteApp with the enctoken
kite = KiteApp(enctoken=enctoken)

# Circular buffer implementation
class CircularBuffer:
    def __init__(self, size):
        self.buffer = [None] * size
        self.size = size
        self.next_index = 0

    def add(self, data):
        self.buffer[self.next_index] = data
        self.next_index = (self.next_index + 1) % self.size

    def get_data(self):
        return self.buffer

# Initialize circular buffer
buffer_size = 1  # Adjust the size as needed
live_data_buffer = CircularBuffer(buffer_size)

# Function to continuously fetch live data and update circular buffer
def fetch_and_store_live_data(kite, buffer, duration, data_list):
    start_time = time.time()
    while True:
        elapsed_time = time.time() - start_time
        if (elapsed_time >= duration):
            print("Duration reached. Stopping data fetching.")
            break

        live_data = kite.ltp(["NSE:NIFTY BANK", "NSE:NIFTY 50"])  # Fetch live data, adjust instruments as needed
        buffer.add(live_data)
        data_list.append(live_data)  # Append data to list
        time.sleep(1)  # Adjust the interval as needed

# Define duration for data fetching (in seconds)
duration = 10  # 10 seconds

data_list = []  # List to store live data

fetch_thread = threading.Thread(target=fetch_and_store_live_data, args=(kite, live_data_buffer, duration, data_list))
fetch_thread.start()

# Main loop to access live data
while fetch_thread.is_alive():
    # Access live data from the circular buffer whenever needed
    latest_data = live_data_buffer.get_data()
    print(latest_data)
    time.sleep(1)  # Adjust the interval as needed

# Wait for the fetching thread to complete
fetch_thread.join()

# Convert data list to DataFrame
df = pd.DataFrame(data_list)

# Save DataFrame to Excel file
excel_file_path = r'/home/ubuntu/kite/live_data.xlsx'  # Adjust the path as needed
df.to_excel(excel_file_path, index=False)
print("Live data saved to:", excel_file_path)

