import mysql.connector
import boto3
from kite_trade import KiteApp
from datetime import datetime
from circular_buffer import CircularBuffer
import pandas as pd
import time

# Database connection details
db_config = {
    'user': 'ancit',
    'password': 'Ravi@12345',
    'host': '13.127.218.213',  # Replace with your EC2 instance's public IP or DNS
    'database': 'kite_data'
}

# S3 bucket details
s3_bucket_name = 'my-trading-data-bucket'
s3_excel_key = 'live_data.xlsx'

# Establish MySQL database connection
try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    print("Connected to MySQL database successfully!")
except Exception as e:
    print("Error connecting to MySQL database:", e)

# Create a CircularBuffer instance
buffer_size = 100  # Adjust buffer size as needed
live_data_buffer = CircularBuffer(buffer_size)

# Function to fetch and store live data
def fetch_and_store_live_data(kite, buffer, duration):
    start_time = time.time()
    while True:
        elapsed_time = time.time() - start_time
        if elapsed_time >= duration:
            print("Duration reached. Stopping data fetching.")
            break

        live_data = kite.ltp(["NSE:NIFTY BANK", "NSE:NIFTY 50"])  # Fetch live data, adjust instruments as needed
        buffer.add(live_data)
        time.sleep(1)  # Adjust the interval as needed

# Main function to execute the data processing workflow
def main():
    try:
        # Establish connection to Zerodha Kite API
        user_id = "FVK571"
        password = "Ravi@966366"
        twofa = "490777"
        enctoken = get_enctoken(user_id, password, twofa)
        kite = KiteApp(enctoken=enctoken)

        # Fetch live data and store in circular buffer
        duration = 30  # Duration in seconds
        fetch_thread = threading.Thread(target=fetch_and_store_live_data, args=(kite, live_data_buffer, duration))
        fetch_thread.start()

        # Wait for the fetching thread to complete
        fetch_thread.join()

        # Get live data from circular buffer
        latest_data = live_data_buffer.get_data()

        # Convert data list to DataFrame
        df = pd.DataFrame(latest_data)

        # Save DataFrame to Excel file
        excel_file_path = 'live_data.xlsx'
        df.to_excel(excel_file_path, index=False)

        # Upload Excel file to S3 bucket
        s3_client = boto3.client('s3')
        s3_client.upload_file(excel_file_path, s3_bucket_name, s3_excel_key)
        print("Live data saved to S3 bucket:", s3_bucket_name)

        # Create MySQL table to store live data if not exists
        create_table_query = """
            CREATE TABLE IF NOT EXISTS live_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(255),
                last_price FLOAT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        cursor.execute(create_table_query)
        print("MySQL table 'live_data' created successfully!")

        # Insert live data into MySQL table
        insert_query = "INSERT INTO live_data (symbol, last_price) VALUES (%s, %s)"
        for data in latest_data:
            cursor.execute(insert_query, (data['tradingsymbol'], data['last_price']))
        conn.commit()
        print("Live data inserted into MySQL database successfully!")

    except Exception as e:
        print("Error:", e)

    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()

