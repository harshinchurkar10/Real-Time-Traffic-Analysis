import sqlite3
import requests
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)
DATABASE = "database.db"
API_KEY = "UhhKQMV1eqBcatCLiipAtbSAgXtN7MRk"

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS traffic_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                latitude REAL,
                longitude REAL,
                timestamp TEXT,
                current_speed REAL,
                free_flow_speed REAL,
                current_travel_time REAL
            )
        ''')
        conn.commit()

def fetch_and_save_data(latitude, longitude):
    url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?key={API_KEY}&point={latitude},{longitude}"
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception(f"API Error: {response.status_code} - {response.text}")
    
    data = response.json().get("flowSegmentData", {})
    
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('''
            INSERT INTO traffic_data 
            (latitude, longitude, timestamp, current_speed, free_flow_speed, current_travel_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            latitude,
            longitude,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data.get("currentSpeed", 0),
            data.get("freeFlowSpeed", 0),
            data.get("currentTravelTime", 0)
        ))
        conn.commit()

@app.route('/fetch_data', methods=['GET'])
def handle_fetch_data():
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        fetch_and_save_data(lat, lon)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/historical_data', methods=['GET'])
def handle_historical_data():
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM traffic_data
                WHERE latitude = ? AND longitude = ?
                ORDER BY timestamp DESC
            ''', (lat, lon))
            
            columns = [desc[0] for desc in cursor.description]
            data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True)