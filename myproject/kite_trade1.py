import os
try:
    import requests
except ImportError:
    os.system('python -m pip install requests')
try:
    import dateutil
except ImportError:
    os.system('python -m pip install python-dateutil')
try:
    import mysql.connector
except ImportError:
    os.system('python -m pip install mysql-connector-python')
try:
    import boto3
except ImportError:
    os.system('python -m pip install boto3')

import requests
import dateutil.parser
import mysql.connector
import boto3

def get_enctoken(userid, password, twofa):
    session = requests.Session()
    response = session.post('https://kite.zerodha.com/api/login', data={
        "user_id": userid,
        "password": password
    })
    response = session.post('https://kite.zerodha.com/api/twofa', data={
        "request_id": response.json()['data']['request_id'],
        "twofa_value": twofa,
        "user_id": response.json()['data']['user_id']
    })
    enctoken = response.cookies.get('enctoken')
    if enctoken:
        return enctoken
    else:
        raise Exception("Enter valid details !!!!")


class KiteApp:
    # Products
    PRODUCT_MIS = "MIS"
    PRODUCT_CNC = "CNC"
    PRODUCT_NRML = "NRML"
    PRODUCT_CO = "CO"

    # Order types
    ORDER_TYPE_MARKET = "MARKET"
    ORDER_TYPE_LIMIT = "LIMIT"
    ORDER_TYPE_SLM = "SL-M"
    ORDER_TYPE_SL = "SL"

    # Varieties
    VARIETY_REGULAR = "regular"
    VARIETY_CO = "co"
    VARIETY_AMO = "amo"

    # Transaction type
    TRANSACTION_TYPE_BUY = "BUY"
    TRANSACTION_TYPE_SELL = "SELL"

    # Validity
    VALIDITY_DAY = "DAY"
    VALIDITY_IOC = "IOC"

    # Exchanges
    EXCHANGE_NSE = "NSE"
    EXCHANGE_BSE = "BSE"
    EXCHANGE_NFO = "NFO"
    EXCHANGE_CDS = "CDS"
    EXCHANGE_BFO = "BFO"
    EXCHANGE_MCX = "MCX"

    def __init__(self, enctoken):
        self.headers = {"Authorization": f"enctoken {enctoken}"}
        self.session = requests.session()
        self.root_url = "https://api.kite.trade"
        self.session.get(self.root_url, headers=self.headers)

        # MySQL Database Configuration
        self.db_config = {
            'user': 'ancit',
            'password': 'Ravi@12345',
            'host': '13.127.218.213',  # Replace with your EC2 instance's public IP or DNS
            'database': 'kite_data',
        }

        # AWS S3 Configuration
        self.s3_bucket_name = 'my-trading-data-bucket'
        self.s3 = boto3.client('s3')

        # Ensure database and table are set up
        self.setup_database()

    def setup_database(self):
        conn = mysql.connector.connect(
            user=self.db_config['user'],
            password=self.db_config['password'],
            host=self.db_config['host']
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.db_config['database']}")
        conn.database = self.db_config['database']
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS instruments (
                instrument_token INT PRIMARY KEY,
                exchange_token VARCHAR(255),
                tradingsymbol VARCHAR(255),
                name VARCHAR(255),
                last_price FLOAT,
                expiry DATE,
                strike FLOAT,
                tick_size FLOAT,
                lot_size INT,
                instrument_type VARCHAR(255),
                segment VARCHAR(255),
                exchange VARCHAR(255)
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()

    def instruments(self, exchange=None):
        data = self.session.get(f"{self.root_url}/instruments", headers=self.headers).text.split("\n")
        Exchange = []
        for i in data[1:-1]:
            row = i.split(",")
            if exchange is None or exchange == row[11]:
                Exchange.append({
                    'instrument_token': int(row[0]), 'exchange_token': row[1], 'tradingsymbol': row[2],
                    'name': row[3][1:-1], 'last_price': float(row[4]),
                    'expiry': dateutil.parser.parse(row[5]).date() if row[5] != "" else None,
                    'strike': float(row[6]), 'tick_size': float(row[7]), 'lot_size': int(row[8]),
                    'instrument_type': row[9], 'segment': row[10],
                    'exchange': row[11]
                })
        return Exchange

    def store_data_in_db(self, data):
        conn = mysql.connector.connect(**self.db_config)
        cursor = conn.cursor()
        for item in data:
            cursor.execute('''
                INSERT INTO instruments (
                    instrument_token, exchange_token, tradingsymbol, name, last_price, expiry,
                    strike, tick_size, lot_size, instrument_type, segment, exchange
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    exchange_token=VALUES(exchange_token), tradingsymbol=VALUES(tradingsymbol),
                    name=VALUES(name), last_price=VALUES(last_price), expiry=VALUES(expiry),
                    strike=VALUES(strike), tick_size=VALUES(tick_size), lot_size=VALUES(lot_size),
                    instrument_type=VALUES(instrument_type), segment=VALUES(segment),
                    exchange=VALUES(exchange)
            ''', (
                item['instrument_token'], item['exchange_token'], item['tradingsymbol'], item['name'], item['last_price'],
                item['expiry'], item['strike'], item['tick_size'], item['lot_size'], item['instrument_type'],
                item['segment'], item['exchange']
            ))
        conn.commit()
        cursor.close()
        conn.close()

# Example usage:
if __name__ == "__main__":
    enctoken = get_enctoken("FVK571", "Ravi@966366", "478520")
    app = KiteApp(enctoken)
    instruments_data = app.instruments()
    app.store_data_in_db(instruments_data)
    print("Data stored successfully")

