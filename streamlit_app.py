import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(
    page_title="ISS Live Tracker",
    page_icon="🛸",
    layout="wide"
)

st.title("🛸 International Space Station — Live Tracker")
st.caption("Real-time ISS location data streamed via Kafka → Snowpipe → Snowflake")

session = get_active_session()


@st.cache_data(ttl=6)
def load_data(limit=200):
    df = session.sql(f"""
        SELECT
            TO_TIMESTAMP(PARSE_JSON(RECORD_CONTENT):timestamp::INTEGER) AS TIME,
            PARSE_JSON(RECORD_CONTENT):latitude::FLOAT                  AS LATITUDE,
            PARSE_JSON(RECORD_CONTENT):longitude::FLOAT                 AS LONGITUDE,
            PARSE_JSON(RECORD_CONTENT):altitude_km::FLOAT               AS ALTITUDE_KM,
            PARSE_JSON(RECORD_CONTENT):velocity_kmh::FLOAT              AS VELOCITY_KMH
        FROM ISS_TRACKING.KAFKA.ISS_LOCATION
        ORDER BY TIME DESC
        LIMIT {limit}
    """).to_pandas()
    return df


df = load_data()

if df.empty:
    st.warning("No data yet. Make sure the producer and Kafka connector are running.")
    st.stop()

latest = df.iloc[0]

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Latitude",    f"{latest['LATITUDE']:.4f}°")
col2.metric("Longitude",   f"{latest['LONGITUDE']:.4f}°")
col3.metric("Altitude",    f"{latest['ALTITUDE_KM']:.1f} km")
col4.metric("Velocity",    f"{latest['VELOCITY_KMH']:,.0f} km/h")
col5.metric("Last Update", str(latest['TIME'])[:19])

st.divider()

st.subheader("Live Position & Recent Path")
map_df = df[["LATITUDE", "LONGITUDE"]].rename(columns={"LATITUDE": "lat", "LONGITUDE": "lon"})
st.map(map_df)
st.caption("Dots = recent ISS path (last 200 readings)")

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Altitude over Time")
    alt_df = df[["TIME", "ALTITUDE_KM"]].sort_values("TIME")
    st.line_chart(alt_df.set_index("TIME")["ALTITUDE_KM"])

with col_b:
    st.subheader("Velocity over Time")
    vel_df = df[["TIME", "VELOCITY_KMH"]].sort_values("TIME")
    st.line_chart(vel_df.set_index("TIME")["VELOCITY_KMH"])

st.divider()

with st.expander("Raw Data (last 50 records)"):
    st.dataframe(
        df.head(50).style.format({
            "LATITUDE":     "{:.4f}",
            "LONGITUDE":    "{:.4f}",
            "ALTITUDE_KM":  "{:.2f}",
            "VELOCITY_KMH": "{:,.0f}",
        }),
        use_container_width=True,
    )

st.divider()
col_r1, col_r2 = st.columns([3, 1])
col_r1.caption(f"Total records in Snowflake: **{session.sql('SELECT COUNT(*) FROM ISS_TRACKING.KAFKA.ISS_LOCATION').collect()[0][0]:,}**")
if col_r2.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()
