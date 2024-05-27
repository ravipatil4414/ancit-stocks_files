from flask import Flask, jsonify
import mysql.connector

app = Flask(__name__)

def get_data_from_db():
    conn = mysql.connector.connect(
        host="13.233.81.176",
        user="stock_user",
        password="Ravi@12345",
        database="stock_data"
    )
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM processed_data")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

@app.route('/data', methods=['GET'])
def get_data():
    data = get_data_from_db()
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='172.31.42.19', port=5000)

