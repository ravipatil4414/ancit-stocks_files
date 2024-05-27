# Required imports
from kite_trade import *
import threading
import time
import pandas as pd

# Function to login to Zerodha API
def login(user_id, password, twofa):
    enctoken = get_enctoken(user_id, password, twofa)
    kite = KiteApp(enctoken=enctoken)
    return kite

# Function to logoff from Zerodha API
def logoff(kite):
    # Perform any cleanup operations if needed
    pass

# Function to fetch live data and write to circular buffer
def fetch_and_store_live_data(kite, buffer, duration, interval):
    start_time = time.time()
    while True:
        elapsed_time = time.time() - start_time
        if elapsed_time >= duration:
            print("Duration reached. Stopping data fetching.")
            break
        
        live_data = kite.ltp(["NSE:NIFTY BANK", "NSE:NIFTY 50"])  # Fetch live data, adjust instruments as needed
        buffer.add(live_data)
        time.sleep(interval)

# Main task execution
def main():
    # Login to Zerodha API
    user_id = "your_user_id"
    password = "your_password"
    twofa = "your_twofa"
    kite = login(user_id, password, twofa)
    
    # Circular buffer setup
    buffer_size = 1
    live_data_buffer = CircularBuffer(buffer_size)

    # Fetch live data and store in circular buffer
    duration = 30  # Duration for data fetching in seconds
    interval = 1   # Interval between data fetches in seconds
    fetch_thread = threading.Thread(target=fetch_and_store_live_data, args=(kite, live_data_buffer, duration, interval))
    fetch_thread.start()

    # Main thread: Read from circular buffer and print data
    while fetch_thread.is_alive():
        latest_data = live_data_buffer.get_data()
        print(latest_data)
        time.sleep(interval)

    # Join fetch thread
    fetch_thread.join()

    # Logoff from Zerodha API
    logoff(kite)

    # Save collected data to Excel
    df = pd.DataFrame(data_list)
    excel_file_path = 'live_data.xlsx'
    df.to_excel(excel_file_path, index=False)
    print("Live data saved to:", excel_file_path)

# Entry point of the script
if __name__ == "__main__":
    main()

