import os
import mysql.connector
import requests
import dateutil.parser

# Install necessary dependencies if not already installed
try:
    import mysql.connector
except ImportError:
    os.system('python -m pip install mysql-connector-python')

try:
    import requests
except ImportError:
    os.system('python -m pip install requests')

try:
    import dateutil
except ImportError:
    os.system('python -m pip install python-dateutil')

# Database configuration
db_config = {
    'user': 'ancit',
    'password': 'Ravi12345',
    'host': 'database-1.cfyqg0kwq7od.ap-south-1.rds.amazonaws.com',
    'database': 'kite_data'
}

# Establish database connection
connection = mysql.connector.connect(**db_config)
cursor = connection.cursor()

# Create database if it doesn't exist
cursor.execute("CREATE DATABASE IF NOT EXISTS kite_data")
cursor.execute("USE kite_data")

# Create table if it doesn't exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS enctokens (
        id INT AUTO_INCREMENT PRIMARY KEY,
        userid VARCHAR(255) NOT NULL,
        enctoken VARCHAR(255) NOT NULL
    )
""")

def get_enctoken(userid, password, twofa):
    session = requests.Session()
    login_response = session.post('https://kite.zerodha.com/api/login', data={
        "user_id": userid,
        "password": password
    })
    
    if login_response.status_code != 200 or 'data' not in login_response.json():
        raise Exception(f"Login failed: {login_response.text}")

    request_id = login_response.json()['data']['request_id']
    user_id = login_response.json()['data']['user_id']
    
    twofa_response = session.post('https://kite.zerodha.com/api/twofa', data={
        "request_id": request_id,
        "twofa_value": twofa,
        "user_id": user_id
    })
    
    if twofa_response.status_code != 200 or 'enctoken' not in twofa_response.cookies:
        raise Exception(f"2FA failed: {twofa_response.text}")

    enctoken = twofa_response.cookies.get('enctoken')
    if enctoken:
        # Insert enctoken into database
        query = "INSERT INTO enctokens (userid, enctoken) VALUES (%s, %s)"
        cursor.execute(query, (userid, enctoken))
        connection.commit()
        return enctoken
    else:
        raise Exception("Failed to retrieve enctoken")

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

    def instruments(self, exchange=None):
        data = self.session.get(f"{self.root_url}/instruments", headers=self.headers).text.split("\n")
        Exchange = []
        for i in data[1:-1]:
            row = i.split(",")
            if exchange is None or exchange == row[11]:
                Exchange.append({'instrument_token': int(row[0]), 'exchange_token': row[1], 'tradingsymbol': row[2],
                                 'name': row[3][1:-1], 'last_price': float(row[4]),
                                 'expiry': dateutil.parser.parse(row[5]).date() if row[5] != "" else None,
                                 'strike': float(row[6]), 'tick_size': float(row[7]), 'lot_size': int(row[8]),
                                 'instrument_type': row[9], 'segment': row[10],
                                 'exchange': row[11]})
        return Exchange

    def quote(self, instruments):
        data = self.session.get(f"{self.root_url}/quote", params={"i": instruments}, headers=self.headers).json()["data"]
        return data

    def ltp(self, instruments):
        data = self.session.get(f"{self.root_url}/quote/ltp", params={"i": instruments}, headers=self.headers).json()["data"]
        return data

    def historical_data(self, instrument_token, from_date, to_date, interval, continuous=False, oi=False):
        params = {"from": from_date,
                  "to": to_date,
                  "interval": interval,
                  "continuous": 1 if continuous else 0,
                  "oi": 1 if oi else 0}
        lst = self.session.get(
            f"{self.root_url}/instruments/historical/{instrument_token}/{interval}", params=params,
            headers=self.headers).json()["data"]["candles"]
        records = []
        for i in lst:
            record = {"date": dateutil.parser.parse(i[0]), "open": i[1], "high": i[2], "low": i[3],
                      "close": i[4], "volume": i[5],}
            if len(i) == 7:
                record["oi"] = i[6]
            records.append(record)
        return records

    def margins(self):
        margins = self.session.get(f"{self.root_url}/user/margins", headers=self.headers).json()["data"]
        return margins

    def orders(self):
        orders = self.session.get(f"{self.root_url}/orders", headers=self.headers).json()["data"]
        return orders

    def positions(self):
        positions = self.session.get(f"{self.root_url}/portfolio/positions", headers=self.headers).json()["data"]
        return positions

    def place_order(self, variety, exchange, tradingsymbol, transaction_type, quantity, product, order_type, price=None,
                    validity=None, disclosed_quantity=None, trigger_price=None, squareoff=None, stoploss=None,
                    trailing_stoploss=None, tag=None):
        params = locals()
        del params["self"]
        for k in list(params.keys()):
            if params[k] is None:
                del params[k]
        order_id = self.session.post(f"{self.root_url}/orders/{variety}",
                                     data=params, headers=self.headers).json()["data"]["order_id"]
        return order_id

    def modify_order(self, variety, order_id, parent_order_id=None, quantity=None, price=None, order_type=None,
                     trigger_price=None, validity=None, disclosed_quantity=None):
        params = locals()
        del params["self"]
        for k in list(params.keys()):
            if params[k] is None:
                del params[k]

        order_id = self.session.put(f"{self.root_url}/orders/{variety}/{order_id}",
                                    data=params, headers=self.headers).json()["data"]["order_id"]
        return order_id

    def cancel_order(self, variety, order_id, parent_order_id=None):
        order_id = self.session.delete(f"{self.root_url}/orders/{variety}/{order_id}",
                                       data={"parent_order_id": parent_order_id} if parent_order_id else {},
                                       headers=self.headers).json()["data"]["order_id"]
        return order_id

# Example usage:
if __name__ == "__main__":
    userid = os.getenv('KITE_USER_ID')  # Replace with your actual user ID
    password = os.getenv('KITE_PASSWORD')  # Replace with your actual password
    twofa = os.getenv('KITE_2FA')  # Replace with your actual 2FA value

    if not userid or not password or not twofa:
        raise ValueError("Please set the KITE_USER_ID, KITE_PASSWORD, and KITE_2FA environment variables")

    try:
        enctoken = get_enctoken(userid, password, twofa)
        kite = KiteApp(enctoken)
        
        # Fetch instruments and print them
        instruments = kite.instruments()
        print(instruments)
    except Exception as e:
        print(f"Error: {e}")

