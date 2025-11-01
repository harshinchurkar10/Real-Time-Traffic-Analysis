import sqlite3
import requests
import pandas as pd
from datetime import datetime

DATABASE = "database.db"
API_KEY = "UhhKQMV1eqBcatCLiipAtbSAgXtN7MRk"  

def init_db():
    """Initialize the database and create tables if they don't exist."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
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
    """Fetch traffic data from TomTom API and store in SQLite."""
    url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?key={API_KEY}&point={latitude},{longitude}"
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception(f"API Request Failed! HTTP Status Code: {response.status_code}\nResponse: {response.text}")
    
    data = response.json().get("flowSegmentData", {})
    if not data:
        raise Exception("No traffic data found in the API response.")
    
    current_speed = data.get("currentSpeed", 0)
    free_flow_speed = data.get("freeFlowSpeed", 0)
    current_travel_time = data.get("currentTravelTime", 0)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO traffic_data (latitude, longitude, timestamp, current_speed, free_flow_speed, current_travel_time)
            VALUES (?, ?, ?, ?, ?, ?)''',
            (latitude, longitude, timestamp, current_speed, free_flow_speed, current_travel_time))
        conn.commit()
    
    print("✅ Traffic data stored successfully!")

if __name__ == '__main__':
    init_db()
    location_input = input("Enter location (latitude,longitude): ").strip()
    try:
        latitude, longitude = map(float, location_input.split(","))
    except Exception:
        print("❌ Invalid input! Please enter latitude and longitude as numbers separated by a comma.")
        exit(1)
    
    fetch_and_save_data(latitude, longitude)
