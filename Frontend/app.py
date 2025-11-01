import streamlit as st
import requests
import folium
import plotly.express as px
import pandas as pd
from streamlit_folium import folium_static
from datetime import datetime

# Initialize session state
if 'live_data' not in st.session_state:
    st.session_state.live_data = None
if 'historical_data' not in st.session_state:
    st.session_state.historical_data = []

# Backend API URL
BACKEND_URL = "http://127.0.0.1:5000"

def fetch_live_data(latitude, longitude):
    try:
        response = requests.get(
            f"{BACKEND_URL}/fetch_data",
            params={"lat": latitude, "lon": longitude},
            timeout=5
        )
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException:
        return None

def fetch_historical_data(latitude, longitude):
    try:
        response = requests.get(
            f"{BACKEND_URL}/historical_data",
            params={"lat": latitude, "lon": longitude}
        )
        return response.json() if response.status_code == 200 else []
    except requests.exceptions.RequestException:
        return []

def get_traffic_status(data):
    """Analyze traffic data and generate status message"""
    if not data:
        return "⚠️ No data available", "warning"
    
    latest = data[-1]
    current = latest['current_speed']
    free_flow = latest['free_flow_speed']
    
    congestion_pct = ((free_flow - current) / free_flow) * 100 if free_flow > 0 else 0
    
    thresholds = {
        'heavy': 40,
        'moderate': 20,
        'light': 10
    }
    
    if congestion_pct >= thresholds['heavy']:
        return (
            f"🚨 Heavy Traffic Alert! {congestion_pct:.1f}% slower than normal "
            f"(Current: {current} km/h vs Free Flow: {free_flow} km/h)",
            "error"
        )
    elif congestion_pct >= thresholds['moderate']:
        return (
            f"⚠️ Moderate Traffic: {congestion_pct:.1f}% slower than usual "
            f"(Current: {current} km/h vs Normal: {free_flow} km/h)",
            "warning"
        )
    elif congestion_pct >= thresholds['light']:
        return (
            f"🚧 Light Traffic: {congestion_pct:.1f}% slower than average "
            f"(Current: {current} km/h vs Expected: {free_flow} km/h)",
            "info"
        )
    else:
        return (
            f"✅ Clear Traffic: Flowing normally at {current} km/h "
            f"(Free Flow Speed: {free_flow} km/h)",
            "success"
        )

# Sidebar controls
st.sidebar.header("🔍 Traffic Data Input")
lat = st.sidebar.text_input("🌍 Latitude", "19.0760")
lon = st.sidebar.text_input("📍 Longitude", "72.8777")
map_style = st.sidebar.selectbox("🗺️ Map Style", ["OpenStreetMap", "CartoDB Positron", "Stamen Toner"])

if st.sidebar.button("Fetch Traffic Data"):
    st.session_state.live_data = fetch_live_data(lat, lon)
    st.session_state.historical_data = fetch_historical_data(lat, lon)
    
    if st.session_state.live_data and st.session_state.historical_data:
        st.sidebar.success("✅ Data fetched successfully!")
        st.rerun()
    else:
        st.sidebar.error("❌ Partial/failed data fetch")

# Real-Time Map
st.subheader("📍 Interactive Traffic Map")
map_center = [float(lat), float(lon)]
m = folium.Map(location=map_center, zoom_start=12, tiles=map_style)
folium.CircleMarker(map_center, radius=10, color='red', fill=True).add_to(m)
folium_static(m)

# Traffic Status Analysis
st.subheader("📢 Traffic Status Alert")

if st.session_state.historical_data:
    processed_data = [{
        **item,
        "timestamp": datetime.strptime(item["timestamp"], "%Y-%m-%d %H:%M:%S"),
        "latitude": float(item["latitude"]),
        "longitude": float(item["longitude"]),
        "current_speed": float(item["current_speed"]),
        "free_flow_speed": float(item["free_flow_speed"]),
        "current_travel_time": float(item["current_travel_time"])
    } for item in st.session_state.historical_data]

    filtered_data = [
        d for d in processed_data
        if d["latitude"] == float(lat) and d["longitude"] == float(lon)
    ]

    if filtered_data:
        status_message, alert_type = get_traffic_status(filtered_data)
        
        with st.container():
            if alert_type == "success":
                st.success(status_message)
            elif alert_type == "info":
                st.info(status_message)
            elif alert_type == "warning":
                st.warning(status_message)
            else:
                st.error(status_message)
            
            # Add supplemental metrics
            latest = filtered_data[-1]
            cols = st.columns(3)
            cols[0].metric("Current Speed", f"{latest['current_speed']} km/h")
            cols[1].metric("Free Flow Speed", f"{latest['free_flow_speed']} km/h")
            congestion = (((latest['free_flow_speed'] - latest['current_speed']) / latest['free_flow_speed']) * 100) if latest['free_flow_speed'] > 0 else 0
            cols[2].metric("Congestion Level", f"{congestion:.1f}%")
    else:
        st.warning("🔍 No traffic data available for analysis")
else:
    st.warning("⚠️ No historical data available")

# Traffic Insights Dashboard
st.subheader("📊 Traffic Insights Dashboard")

if st.session_state.historical_data and filtered_data:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚦 Current vs Free Flow Speed")
        fig1 = px.bar(
            filtered_data,
            x='timestamp',
            y=['current_speed', 'free_flow_speed'],
            barmode='group',
            labels={'value': 'Speed (km/h)', 'timestamp': 'Time'},
            title="Speed Comparison"
        )
        st.plotly_chart(fig1, use_container_width=True)

        st.markdown("### 📈 Speed Difference Trend")
        speed_diff = [d['free_flow_speed'] - d['current_speed'] for d in filtered_data]
        timestamps = [d['timestamp'] for d in filtered_data]
        fig3 = px.area(
            x=timestamps,
            y=speed_diff,
            labels={'x': 'Time', 'y': 'Speed Difference (km/h)'},
            title="Congestion Level"
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        st.markdown("### ⏱️ Travel Time Patterns")
        fig2 = px.scatter(
            filtered_data,
            x='timestamp',
            y='current_travel_time',
            color='current_speed',
            size='current_travel_time',
            labels={'current_travel_time': 'Travel Time (min)', 'timestamp': 'Time'},
            title="Travel Time Distribution"
        )
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown("### 🥧 Speed Ratio Distribution")
        total_current = sum(d['current_speed'] for d in filtered_data)
        total_free_flow = sum(d['free_flow_speed'] for d in filtered_data)
        fig4 = px.pie(
            values=[total_current, total_free_flow],
            names=['Actual Speed', 'Free Flow Speed'],
            title="Speed Ratio"
        )
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("### 🌡️ Traffic Intensity Heatmap")
    fig5 = px.density_mapbox(
        filtered_data,
        lat='latitude',
        lon='longitude',
        z='current_speed',
        radius=15,
        center=dict(lat=float(lat), lon=float(lon)),
        zoom=12,
        mapbox_style="open-street-map",
        title="Real-time Traffic Heatmap"
    )
    st.plotly_chart(fig5, use_container_width=True)
elif st.session_state.historical_data:
    st.warning("⚠️ No historical data available for the selected location.")

# Download CSV Report
st.subheader("📥 Download Traffic Report")
if st.button("Download Report"):
    if st.session_state.historical_data:
        df_all = pd.DataFrame(st.session_state.historical_data)
        csv = df_all.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download CSV Report", csv, "traffic_report.csv", "text/csv")
    else:
        st.warning("⚠️ No data available for download.")

st.markdown("### 🌍 Built with ❤️ for Smart Traffic Management 🚦")
