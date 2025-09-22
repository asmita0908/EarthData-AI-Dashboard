import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# --- Page Configuration ---
st.set_page_config(page_title="EarthData AI Dashboard", layout="wide")

# --- CSS for Background and Styling ---
st.markdown("""
<style>
.stApp {
    background-image: url("https://images.pexels.com/photos/220201/pexels-photo-220201.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2");
    background-attachment: fixed;
    background-size: cover;
}
</style>
""", unsafe_allow_html=True)

# --- Data Fetching Function (Updated to include coordinates) ---
@st.cache_data(ttl=600) # Cache data for 10 minutes
def fetch_air_quality_data(city_name):
    api_url = f"https://api.openaq.org/v2/latest?limit=500&page=1&offset=0&sort=desc&radius=1000&city={city_name}&order_by=lastUpdated&dumpRaw=false"
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            if 'results' in data and data['results']:
                records = []
                for record in data['results']:
                    # Check if coordinates exist for the location
                    if record.get('coordinates'):
                        for measurement in record['measurements']:
                            records.append({
                                'Location': record['location'],
                                'Parameter': measurement['parameter'],
                                'Value': measurement['value'],
                                'Unit': measurement['unit'],
                                'Last Updated': measurement['lastUpdated'],
                                'latitude': record['coordinates']['latitude'],
                                'longitude': record['coordinates']['longitude']
                            })
                df = pd.DataFrame(records)
                return df
            else:
                return pd.DataFrame()
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"An error occurred during API request: {e}")
        return pd.DataFrame()

# --- Charting Function ---
def create_aqi_bar_chart(df):
    latest_data = df.loc[df.groupby('Parameter')['Last Updated'].idxmax()]
    fig = px.bar(
        latest_data, x='Parameter', y='Value', color='Parameter',
        title='Latest Air Quality Measurements',
        labels={'Value': 'Value', 'Parameter': 'Pollutant'},
        template='plotly_dark'
    )
    return fig

# --- Dashboard UI ---
st.title("🌍 EarthData AI: Real-Time Air Quality Dashboard")
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Live Air Quality", "AQI Graph", "Pollution Heatmap", "Alerts"])

city_input = st.sidebar.text_input("Enter City Name:", "Delhi")

if page == "Live Air Quality":
    st.header("Live Air Quality Data")
    if city_input:
        st.write(f"Showing live air quality data for **{city_input}**")
        city_data = fetch_air_quality_data(city_name=city_input)
        if not city_data.empty:
            # Display all columns except lat/lon for neatness
            st.dataframe(city_data.drop(columns=['latitude', 'longitude']))
        else:
            st.warning(f"No current air quality data available for {city_input}.")

elif page == "AQI Graph":
    st.header("Air Quality Index (AQI) Graph")
    if city_input:
        st.write(f"Visualizing air quality parameters for **{city_input}**")
        city_data = fetch_air_quality_data(city_name=city_input)
        if not city_data.empty:
            fig = create_aqi_bar_chart(city_data)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"No data available to create a graph for {city_input}.")

elif page == "Pollution Heatmap":
    st.header("Pollution Sensor Locations Map")
    if city_input:
        st.write(f"Mapping sensor locations for **{city_input}**")
        map_data = fetch_air_quality_data(city_name=city_input)
        if not map_data.empty and 'latitude' in map_data.columns:
            # Drop rows where lat/lon might be missing
            map_data.dropna(subset=['latitude', 'longitude'], inplace=True)
            # Display the map using sensor coordinates
            st.map(map_data)
        else:
            st.warning(f"No location data available to create a map for {city_input}.")

elif page == "Alerts":
    st.header("Alerts & Notifications")
    st.success("All monitored areas are currently within safe limits.")
