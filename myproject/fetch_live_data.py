# fetch_live_data.py

from kite_trade import *
import threading
import time
import pandas as pd

user_id = "FVK571"
password = "Ravi@966366"
twofa = "your_twofa"

enctoken = get_enctoken(user_id, password, twofa)
kite = KiteApp(enctoken=enctoken)

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

buffer_size = 1  # Adjust the size as needed
live_data_buffer = CircularBuffer(buffer_size)

def fetch_and_store_live_data(kite, buffer, duration, data_list):
    start_time = time.time()
    while True:
        elapsed_time = time.time() - start_time
        if elapsed_time >= duration:
            print("Duration reached. Stopping data fetching.")
            break
        
        live_data = kite.ltp(["NSE:NIFTY BANK", "NSE:NIFTY 50"])  # Fetch live data, adjust instruments as needed
        buffer.add(live_data)
        data_list.append(live_data)  # Append data to list
        time.sleep(1)  # Adjust the interval as needed

duration = 30  # Duration for data fetching in seconds

data_list = []  # List to store live data

fetch_thread = threading.Thread(target=fetch_and_store_live_data, args=(kite, live_data_buffer, duration, data_list))
fetch_thread.start()

while fetch_thread.is_alive():
    latest_data = live_data_buffer.get_data()
    print(latest_data)
    time.sleep(1)  # Adjust the interval as needed 

fetch_thread.join()

df = pd.DataFrame(data_list)
excel_file_path = '/home/ubuntu/myproject/live_data.xlsx'
df.to_excel(excel_file_path, index=False)
print("Live data saved to:", excel_file_path)

