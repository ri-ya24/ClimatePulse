import sys
from pathlib import Path
import numpy as np
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go
import os
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    try:
        GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        GEMINI_API_KEY = None

if GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
else:
    gemini_client = None


def generate_ai_climate_insight(prompt):
    if gemini_client is None:
        return "Gemini API key not found. Please check Streamlit Secrets."

    try:
        response = gemini_client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
        )
        return response.text

    except Exception as e:
        error_str = str(e)

        if "503" in error_str or "UNAVAILABLE" in error_str:
            return "Gemini is busy. Please try again in a moment."

        elif "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            return "API quota reached. Try again after some time."

        elif "401" in error_str or "API_KEY" in error_str:
            return "API key issue. Please check Streamlit Secrets."

        else:
            return f"Could not generate insight: {error_str}"
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))

st.set_page_config(
    page_title="ClimatePulse",
    page_icon="🌍",
    layout="wide",
)

CITIES = {
    "Lucknow": (26.8467, 80.9462),
    "Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Bengaluru": (12.9716, 77.5946),
    "Kolkata": (22.5726, 88.3639),
    "Chennai": (13.0827, 80.2707),
    "Hyderabad": (17.3850, 78.4867),
    "Jaipur": (26.9124, 75.7873),
    "Ahmedabad": (23.0225, 72.5714),
    "Pune": (18.5204, 73.8567),
}
CITY_NAMES = list(CITIES.keys())

HIST_START = "1990-01-01"
HIST_END = "2025-12-31"

FUTURE_START = "2026-01-01"
FUTURE_END = "2049-12-31"


def _city_coordinates():
    return (
        ",".join(str(v[0]) for v in CITIES.values()),
        ",".join(str(v[1]) for v in CITIES.values()),
    )


@st.cache_data(ttl=1800, show_spinner=False)
def get_live_city_data():
    lats, lons = _city_coordinates()

    weather_url = "https://api.open-meteo.com/v1/forecast"
    weather_params = {
        "latitude": lats,
        "longitude": lons,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,wind_speed_10m",
        "timezone": "Asia/Kolkata",
    }
    wr = requests.get(weather_url, params=weather_params, timeout=60)
    wr.raise_for_status()
    weather = wr.json()
    if isinstance(weather, dict):
        weather = [weather]

    aq_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    aq_params = {
        "latitude": lats,
        "longitude": lons,
        "current": "pm10,pm2_5,nitrogen_dioxide,sulphur_dioxide,ozone",
        "timezone": "Asia/Kolkata",
    }
    ar = requests.get(aq_url, params=aq_params, timeout=60)
    ar.raise_for_status()
    air = ar.json()
    if isinstance(air, dict):
        air = [air]

    rows = []
    for i, city in enumerate(CITY_NAMES):
        wc = weather[i].get("current", {})
        ac = air[i].get("current", {})
        rows.append({
            "City": city,
            "Temperature": wc.get("temperature_2m"),
            "Feels Like": wc.get("apparent_temperature"),
            "Humidity": wc.get("relative_humidity_2m"),
            "Wind Speed": wc.get("wind_speed_10m"),
            "Precipitation": wc.get("precipitation"),
            "PM2.5": ac.get("pm2_5"),
            "PM10": ac.get("pm10"),
            "NO2": ac.get("nitrogen_dioxide"),
            "SO2": ac.get("sulphur_dioxide"),
            "O3": ac.get("ozone"),
        })
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=True)
def get_historical_all_cities():
    csv_path = ROOT / "historical_weather.csv"

    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])

    df = df.rename(columns={
        "temperature_max": "temp_max",
        "temperature_min": "temp_min",
        "temperature_mean": "temp_mean",
        "wind_speed_max": "wind_max",
    })

    df["City"] = "Lucknow"

    return df[[
        "City",
        "date",
        "temp_max",
        "temp_min",
        "temp_mean",
        "precipitation",
        "wind_max",
    ]]

@st.cache_data(show_spinner=True)
def get_future_all_cities():
    csv_path = ROOT / "climate_projection.csv"

    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])

    df = df.rename(columns={
        "temperature_mean": "temp_mean",
        "temperature_max": "temp_max",
        "temperature_min": "temp_min",
    })

    df["City"] = "Lucknow"

    return df[[
        "City",
        "date",
        "temp_mean",
        "temp_max",
        "temp_min",
        "precipitation",
    ]]


def air_quality_score(row):
    pm25 = min(float(row["PM2.5"]) / 75 * 100, 100)
    pm10 = min(float(row["PM10"]) / 150 * 100, 100)
    no2 = min(float(row["NO2"]) / 80 * 100, 100)
    so2 = min(float(row["SO2"]) / 80 * 100, 100)
    o3 = min(float(row["O3"]) / 180 * 100, 100)
    return round(pm25 * .40 + pm10 * .20 + no2 * .15 + so2 * .10 + o3 * .15, 2)


def temperature_impact(temp):
    score = max(0, min(((float(temp) - 25) + 5) / 15 * 100, 100))
    return round(score, 2)


def add_live_scores(df):
    out = df.copy()
    out["Air Quality Impact"] = out.apply(air_quality_score, axis=1)
    out["Temperature Impact"] = out["Temperature"].apply(temperature_impact)
    out["Overall Impact"] = (
        out["Air Quality Impact"] * .60
        + out["Temperature Impact"] * .40
    ).round(2)
    return out


def historical_city_summary(hist):
    rows = []
    for city, g in hist.groupby("City"):
        g = g.sort_values("date").copy()
        annual = g.assign(year=g["date"].dt.year).groupby("year")["temp_mean"].mean().reset_index()
        x = annual["year"].to_numpy()
        y = annual["temp_mean"].to_numpy()
        slope = np.polyfit(x, y, 1)[0] if len(annual) > 1 else np.nan

        threshold = g["temp_max"].quantile(.95)
        hot = g["temp_max"] >= threshold
        run = 0
        events = 0
        for v in hot:
            run = run + 1 if v else 0
            if run == 3:
                events += 1

        rows.append({
            "City": city,
            "Historical Average": round(g["temp_mean"].mean(), 2),
            "Historical Trend °C/decade": round(slope * 10, 4),
            "95th Percentile Max °C": round(threshold, 2),
            "3+ Day Heat Events": events,
            "Total Observations": len(g),
        })
    return pd.DataFrame(rows)


def build_selected_trend(hist, city):
    g = hist[hist["City"] == city].copy()
    annual = g.assign(Year=g["date"].dt.year).groupby("Year")["temp_mean"].mean().reset_index()
    return annual


def future_summary(hist, future):
    h = hist.groupby("City")["temp_mean"].mean().rename("Historical Average")
    f = future.groupby("City")["temp_mean"].mean().rename("Projected Average")
    out = pd.concat([h, f], axis=1).reset_index()
    out["Average Difference"] = (out["Projected Average"] - out["Historical Average"]).round(2)

    trends = []
    for city, g in future.groupby("City"):
        annual = g.assign(Year=g["date"].dt.year).groupby("Year")["temp_mean"].mean().reset_index()
        slope = np.polyfit(annual["Year"], annual["temp_mean"], 1)[0]
        trends.append((city, slope * 10))
    trend_df = pd.DataFrame(trends, columns=["City", "Projected Trend °C/decade"])
    return out.merge(trend_df, on="City")


def anomaly_table(hist):
    frames = []
    for city, g in hist.groupby("City"):
        x = g[["temp_mean", "precipitation", "wind_max"]].copy()
        mu = x.mean()
        sd = x.std().replace(0, np.nan)
        z = ((x - mu) / sd).abs().mean(axis=1)
        temp = g.copy()
        temp["Anomaly Score"] = z.values
        temp["Anomaly"] = temp["Anomaly Score"] >= 2.0
        frames.append(temp[temp["Anomaly"]])
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True).sort_values("Anomaly Score", ascending=False)


def climate_impact_by_city(live, hist):
    # Project-defined comparative index. It is not an official climate-risk index.
    rows = []
    for city, row in live.set_index("City").iterrows():
        g = hist[hist["City"] == city].copy()
        daily_avg = g["precipitation"].mean()
        recent = g[g["date"].dt.month == pd.Timestamp.now().month]
        rainfall_score = 0
        if len(recent):
            current_mtd = recent[
                recent["date"].dt.day <= pd.Timestamp.now().day
            ]["precipitation"].sum()
            normal = g[
                (g["date"].dt.month == pd.Timestamp.now().month)
                & (g["date"].dt.day <= pd.Timestamp.now().day)
            ].groupby(g["date"].dt.year)["precipitation"].sum().mean()
            if pd.notna(normal) and normal != 0:
                rainfall_score = min(abs((current_mtd - normal) / normal * 100), 100)

        heat = temperature_impact(row["Temperature"])
        aq = air_quality_score(row)

        recent_sorted = g.sort_values("date")
        dry_days = 0
        for p in recent_sorted["precipitation"].iloc[::-1]:
            if p < 1:
                dry_days += 1
            else:
                break
        dryness = min(dry_days / 30 * 100, 100)

        overall = round(
            heat * .35
            + rainfall_score * .25
            + aq * .25
            + dryness * .15,
            2,
        )
        rows.append({
            "City": city,
            "Heat Impact": round(heat, 2),
            "Rainfall Deviation Impact": round(rainfall_score, 2),
            "Air Quality Impact": round(aq, 2),
            "Dryness Impact": round(dryness, 2),
            "Climate Impact Index": overall,
        })
    return pd.DataFrame(rows)


# -------------------- DATA --------------------
st.title(" ClimatePulse")
st.caption("Climate Data Analytics & AI Intelligence Dashboard")

try:
    live_raw = get_live_city_data()
    live = add_live_scores(live_raw)
    historical = get_historical_all_cities()
    future = get_future_all_cities()
except Exception as e:
    st.error("Data load failed. Check your internet connection and Open-Meteo availability.")
    st.exception(e)
    st.stop()

selected_city = st.selectbox(
    " Select City",
    CITY_NAMES,
    index=CITY_NAMES.index("Lucknow"),
)

selected = live[live["City"] == selected_city].iloc[0]

# -------------------- SELECTED CITY LIVE --------------------
st.header(f"🌤️ Live Environmental Overview — {selected_city}")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Temperature", f'{selected["Temperature"]:.1f} °C')
c2.metric("Feels Like", f'{selected["Feels Like"]:.1f} °C')
c3.metric("Humidity", f'{selected["Humidity"]:.0f} %')
c4.metric("Wind Speed", f'{selected["Wind Speed"]:.1f} km/h')
c5.metric("Precipitation", f'{selected["Precipitation"]:.1f} mm')

a1, a2, a3, a4, a5 = st.columns(5)
a1.metric("PM2.5", f'{selected["PM2.5"]:.1f}')
a2.metric("PM10", f'{selected["PM10"]:.1f}')
a3.metric("NO2", f'{selected["NO2"]:.1f}')
a4.metric("SO2", f'{selected["SO2"]:.1f}')
a5.metric("O3", f'{selected["O3"]:.1f}')
# -------------------- METRIC DELTA --------------------
st.subheader(" Metric Delta vs Historical Monthly Average")

hist_city = historical[historical["City"] == selected_city].copy()

current_month = pd.Timestamp.now().month
hist_month = hist_city[hist_city["date"].dt.month == current_month]

temp_baseline = hist_month["temp_mean"].mean()
temp_delta = selected["Temperature"] - temp_baseline
pm25_delta = selected["PM2.5"] - 75
pm10_delta = selected["PM10"] - 150

d1, d2, d3 = st.columns(3)

d1.metric(
    "Temperature",
    f'{selected["Temperature"]:.1f} °C',
    f'{temp_delta:+.1f} °C vs monthly average',
    delta_color="inverse"
)

d2.metric(
    "PM2.5",
    f'{selected["PM2.5"]:.1f}',
    f'{pm25_delta:+.1f} vs reference',
    delta_color="inverse"
)

d3.metric(
    "PM10",
    f'{selected["PM10"]:.1f}',
    f'{pm10_delta:+.1f} vs reference',
    delta_color="inverse"
)

st.caption("Live weather and air-quality values are current API observations; values can change between refreshes.")
st.divider()
st.header(" Daily Climate Report")
if st.button("Generate Daily Climate Report"):

    with st.spinner("Generating today's climate report..."):

        prompt = f"""
You are a climate data analyst generating a daily environmental
report for a climate intelligence dashboard.

City: {selected_city}

Today's live environmental observations:

Temperature: {selected["Temperature"]:.1f} °C
Feels Like: {selected["Feels Like"]:.1f} °C
Humidity: {selected["Humidity"]:.0f} %
Wind Speed: {selected["Wind Speed"]:.1f} km/h
Precipitation: {selected["Precipitation"]:.1f} mm

Air quality observations:

PM2.5: {selected["PM2.5"]:.1f}
PM10: {selected["PM10"]:.1f}
NO2: {selected["NO2"]:.1f}
SO2: {selected["SO2"]:.1f}
O3: {selected["O3"]:.1f}

Project-defined impact indicators:

Air Quality Impact: {selected["Air Quality Impact"]:.2f}
Temperature Impact: {selected["Temperature Impact"]:.2f}
Overall Impact: {selected["Overall Impact"]:.2f}

Write a concise Daily Climate Report for the dashboard.

Cover:
1. Overall environmental conditions today.
2. Temperature and weather conditions.
3. Air-quality conditions.
4. Which environmental factor appears relatively more significant
   based on the provided project-defined scores.
5. A short overall interpretation.

Important:
- Use only the provided values.
- Do not invent or estimate any data.
- Overall Impact, Air Quality Impact and Temperature Impact are
  project-defined indicators.
- Do not describe them as official AQI or government scores.
- Do not claim that today's conditions prove climate change.
- Clearly distinguish live observations from interpretation.
- Keep the report concise and professional.
"""

        report = generate_ai_climate_insight(prompt)

        st.markdown(report)
        st.divider()
st.divider()
st.header(" Ask ClimatePulse")
st.caption(
    "Ask questions about the climate and environmental data in natural language."
)

user_query = st.text_input(
    "Ask a question about the climate data:",
    placeholder="e.g. Why is Lucknow's impact score higher than Mumbai?"
)

if st.button("Ask ClimatePulse"):
    if user_query.strip():

        with st.spinner("Analysing ClimatePulse data..."):

            climate_data = live[
                [
                    "City",
                    "Temperature",
                    "Feels Like",
                    "Humidity",
                    "Wind Speed",
                    "Precipitation",
                    "PM2.5",
                    "PM10",
                    "NO2",
                    "SO2",
                    "O3",
                    "Air Quality Impact",
                    "Temperature Impact",
                    "Overall Impact",
                ]
            ].copy()

            climate_data_text = climate_data.to_string(
                index=False
            )

            st.write("Your question:", user_query)

            prompt = f"""
You are the Natural Language Query assistant for ClimatePulse,
a climate data analytics dashboard.

The user asked:

{user_query}

Here is the current live environmental data available
from ClimatePulse:

{climate_data_text}

Answer the user's question using only the data provided.

Important:
- Use only the provided ClimatePulse data.
- Do not invent values.
- Do not assume missing information.
- If the question compares cities, use the actual values
  provided for those cities.
- Explain differences using relevant component scores
  such as Air Quality Impact, Temperature Impact,
  and Overall Impact.
- The impact scores are project-defined indicators,
  not official government or scientific rankings.
- Do not claim that a single day's data proves climate change.
- Keep the answer clear, concise and easy to understand.
"""

            answer = generate_ai_climate_insight(prompt)

            st.markdown(answer)

# -------------------- HISTORICAL TREND --------------------
st.header(f" Historical Climate Trend — {selected_city}")

trend = build_selected_trend(historical, selected_city)

fig = px.scatter(
    trend,
    x="Year",
    y="temp_mean",
    trendline="ols",
    labels={"temp_mean": "Annual Mean Temperature (°C)"},
    title=f"Annual Mean Temperature Trend — {selected_city}",
)

fig.update_traces(marker_size=8)

st.plotly_chart(fig, use_container_width=True)

summary = historical_city_summary(historical)

sel_sum = summary[summary["City"] == selected_city].iloc[0]

m1, m2, m3 = st.columns(3)

m1.metric(
    "Historical Average",
    f'{sel_sum["Historical Average"]:.2f} °C'
)

m2.metric(
    "Trend",
    f'{sel_sum["Historical Trend °C/decade"]:.3f} °C/decade'
)

m3.metric(
    "95th Percentile Max",
    f'{sel_sum["95th Percentile Max °C"]:.2f} °C'
)

st.subheader(" AI Historical Trend Explainer")

if st.button("Explain this trend"):

    with st.spinner("Analysing historical climate trend..."):

        prompt = f"""
You are a climate data analyst explaining a historical
temperature trend shown in a climate dashboard.

City: {selected_city}

Historical average temperature:
{sel_sum["Historical Average"]:.2f} °C

Historical temperature trend:
{sel_sum["Historical Trend °C/decade"]:.3f} °C per decade

95th percentile of maximum temperature:
{sel_sum["95th Percentile Max °C"]:.2f} °C

Explain this trend in simple language.

Cover:
1. What the historical average represents.
2. What the temperature trend per decade means.
3. Whether the trend indicates warming or cooling based only
   on the value provided.
4. What the 95th percentile tells us about unusually hot days.
5. What this trend means in the context of long-term climate
   observations.

Important:
- Use only the values provided.
- Do not invent data.
- Do not claim that this trend alone proves climate change.
- Clearly distinguish a historical statistical trend from
  attribution to climate change.
- Keep the explanation concise and suitable for a dashboard.
"""

        insight = generate_ai_climate_insight(prompt)

        st.markdown(insight)

# -------------------- EXTREME EVENTS --------------------
st.header(f" Extreme Events & Climate Anomalies — {selected_city}")

anom = anomaly_table(historical)

sel_anom = anom[anom["City"] == selected_city].copy()

ec1, ec2, ec3 = st.columns(3)

ec1.metric(
    "Historical Observations",
    f'{len(historical[historical["City"] == selected_city]):,}'
)

ec2.metric(
    "Detected Anomalies",
    f'{len(sel_anom):,}'
)

total_obs = len(historical[historical["City"] == selected_city])

anomaly_rate = (
    len(sel_anom) / max(total_obs, 1) * 100
)

ec3.metric(
    "Anomaly Rate",
    f"{anomaly_rate:.2f}%"
)

if len(sel_anom):

    st.dataframe(
        sel_anom[
            [
                "date",
                "temp_mean",
                "precipitation",
                "wind_max",
                "Anomaly Score",
            ]
        ].head(20),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader(" AI Anomaly Explainer")

    selected_anomaly = st.selectbox(
        "Select an anomaly to explain",
        sel_anom.index,
        format_func=lambda i: (
            f'{sel_anom.loc[i, "date"].date()} — '
            f'Anomaly Score: '
            f'{sel_anom.loc[i, "Anomaly Score"]:.2f}'
        ),
    )

    if st.button("Why is this unusual?"):

        row = sel_anom.loc[selected_anomaly]

        with st.spinner("Analysing this anomaly..."):

            prompt = f"""
You are a climate data analyst explaining a statistical anomaly
detected in a climate dashboard.

City: {selected_city}
Date: {row["date"].date()}

Observed values:
Temperature: {row["temp_mean"]:.2f} °C
Precipitation: {row["precipitation"]:.2f} mm
Maximum Wind Speed: {row["wind_max"]:.2f}

Anomaly Score: {row["Anomaly Score"]:.2f}

The anomaly was detected because the combined standardized
deviation of temperature, precipitation and wind was at least
2.0.

Explain in simple language:

1. What makes this observation unusual compared with the
historical conditions of this city.

2. Which of the three variables appears most unusual.

3. What this combination of conditions could indicate.

Important:
- Do not invent data.
- Do not claim that this anomaly proves climate change.
- Clearly distinguish a statistical anomaly from a climate-change event.
- Keep the explanation concise and suitable for a dashboard.
"""

            insight = generate_ai_climate_insight(prompt)

            st.markdown(insight)

st.caption(
    "Anomalies are statistical outliers detected from temperature, "
    "precipitation and wind; they are not automatically "
    "climate-change events."
)
# -------------------- CLIMATE RISK CALENDAR --------------------
st.header(" Climate Risk Calendar")

risk_city = historical[historical["City"] == selected_city].copy()

risk_city["month"] = risk_city["date"].dt.month
risk_city["month_name"] = risk_city["date"].dt.strftime("%b")

monthly_risk = (
    risk_city
    .groupby(["month", "month_name"])
    .agg(
        avg_temp=("temp_mean", "mean"),
        max_temp=("temp_max", "max"),
        total_rainfall=("precipitation", "sum"),
    )
    .reset_index()
    .sort_values("month")
)
def classify_climate_risk(row):
    max_temp = row["max_temp"]

    if max_temp >= 42:
        return "🔴 Extreme"
    elif max_temp >= 38:
        return "🟠 High"
    elif max_temp >= 34:
        return "🟡 Moderate"
    else:
        return "🟢 Low"


monthly_risk["Risk Level"] = monthly_risk.apply(
    classify_climate_risk,
    axis=1
)

st.dataframe(
    monthly_risk[
        [
            "month_name",
            "avg_temp",
            "max_temp",
            "total_rainfall",
            "Risk Level",
        ]
    ].rename(
        columns={
            "month_name": "Month",
            "avg_temp": "Avg Temperature (°C)",
            "max_temp": "Maximum Temperature (°C)",
            "total_rainfall": "Total Rainfall (mm)",
        }
    ),
    use_container_width=True,
    hide_index=True,
)
st.markdown("####  Risk Interpretation")

risk_counts = monthly_risk["Risk Level"].value_counts()

c1, c2, c3, c4 = st.columns(4)

c1.metric("🟢 Low Risk Months", risk_counts.get("🟢 Low", 0))
c2.metric("🟡 Moderate Risk Months", risk_counts.get("🟡 Moderate", 0))
c3.metric("🟠 High Risk Months", risk_counts.get("🟠 High", 0))
c4.metric("🔴 Extreme Risk Months", risk_counts.get("🔴 Extreme", 0))
# -------------------- CLIMATE EVENT DETECTION --------------------
st.header(" Climate Event Detection + Timeline")

event_city = historical[historical["City"] == selected_city].copy()

# Project-defined heat-event threshold
heat_threshold = event_city["temp_max"].quantile(0.95)

event_city["heat_day"] = event_city["temp_max"] >= heat_threshold

st.write(
    f"Heat-event threshold: **{heat_threshold:.1f} °C** "
    "(95th percentile of historical maximum temperature)"
)
# Detect consecutive heat events (minimum 3 days)
event_city = event_city.sort_values("date").reset_index(drop=True)

event_city["heat_group"] = (
    event_city["heat_day"].ne(event_city["heat_day"].shift())
).cumsum()

heat_events = (
    event_city[event_city["heat_day"]]
    .groupby("heat_group")
    .agg(
        start_date=("date", "min"),
        end_date=("date", "max"),
        duration_days=("date", "count"),
        peak_temperature=("temp_max", "max"),
    )
    .reset_index(drop=True)
)

heat_events = heat_events[
    heat_events["duration_days"] >= 3
].sort_values(
    "peak_temperature",
    ascending=False
)
st.subheader(" Historical Heat Events")

if heat_events.empty:
    st.info("No heat events of 3 or more consecutive days were detected.")
else:
    st.dataframe(
        heat_events[
            [
                "start_date",
                "end_date",
                "duration_days",
                "peak_temperature",
            ]
        ].rename(
            columns={
                "start_date": "Start Date",
                "end_date": "End Date",
                "duration_days": "Duration (Days)",
                "peak_temperature": "Peak Temperature (°C)",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.subheader(" Heat Event Timeline")

if not heat_events.empty:
    timeline_fig = px.scatter(
        heat_events,
        x="start_date",
        y="peak_temperature",
        size="duration_days",
        hover_data=[
            "start_date",
            "end_date",
            "duration_days",
            "peak_temperature",
        ],
        labels={
            "start_date": "Event Start",
            "peak_temperature": "Peak Temperature (°C)",
            "duration_days": "Duration (Days)",
        },
        title="Historical Heat Events — Peak Temperature & Duration",
    )

    timeline_fig.update_layout(
        xaxis_title="Event Start Date",
        yaxis_title="Peak Temperature (°C)",
    )

    st.plotly_chart(timeline_fig, use_container_width=True)
# -------------------- CLIMATE IMPACT INDEX --------------------
st.header(" Climate Impact Index")

impact = climate_impact_by_city(live_raw, historical)
sel_impact = impact[impact["City"] == selected_city].iloc[0]

i1, i2, i3, i4, i5 = st.columns(5)

i1.metric("Heat", f'{sel_impact["Heat Impact"]:.2f}/100')
i2.metric("Rainfall", f'{sel_impact["Rainfall Deviation Impact"]:.2f}/100')
i3.metric("Air Quality", f'{sel_impact["Air Quality Impact"]:.2f}/100')
i4.metric("Dryness", f'{sel_impact["Dryness Impact"]:.2f}/100')
i5.metric("Overall", f'{sel_impact["Climate Impact Index"]:.2f}/100')

st.caption(
    "Project-defined analytical index using heat, rainfall deviation, air quality and dryness. "
    "It is not an official government or scientific climate-risk index."
)

st.subheader(" AI Climate Insight")

if st.button("Generate AI Climate Insight"):

    with st.spinner("Analysing climate conditions..."):

        prompt = f"""
You are a climate data analyst helping explain a climate dashboard.

City: {selected_city}

Project-defined climate indicators:
Heat Impact: {sel_impact["Heat Impact"]:.2f}/100
Rainfall Deviation Impact: {sel_impact["Rainfall Deviation Impact"]:.2f}/100
Air Quality Impact: {sel_impact["Air Quality Impact"]:.2f}/100
Dryness Impact: {sel_impact["Dryness Impact"]:.2f}/100
Overall Climate Impact Index: {sel_impact["Climate Impact Index"]:.2f}/100

Explain these results in simple language.

Cover:
1. What the overall Climate Impact Index represents.
2. Which factors are contributing most to the current index.
3. What the heat, rainfall, air-quality and dryness values indicate.
4. What these conditions could mean for people and the local environment.

Important:
- Do not invent any data.
- Do not claim that one day's weather proves climate change.
- Clearly describe the Climate Impact Index as a project-defined analytical index.
- Keep the explanation concise and suitable for a dashboard.
"""

        insight = generate_ai_climate_insight(prompt)

        st.markdown(insight)

# -------------------- ML FORECAST --------------------
st.header(f" ML Temperature Forecast — {selected_city}")

@st.cache_resource(show_spinner=True)
def train_city_xgb(city):

    import xgboost as xgb
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    # Historical data is used to train the model.
    df = (
        historical[historical["City"] == city]
        .sort_values("date")
        .copy()
    )

    # Feature engineering.
    df["temperature_lag_1"] = df["temp_mean"].shift(1)
    df["temperature_lag_2"] = df["temp_mean"].shift(2)
    df["temperature_lag_7"] = df["temp_mean"].shift(7)

    df["temperature_rolling_7"] = (
        df["temp_mean"].rolling(7).mean()
    )

    df["temperature_rolling_30"] = (
        df["temp_mean"].rolling(30).mean()
    )

    # Target = next day's temperature.
    df["target"] = df["temp_mean"].shift(-1)

    feature_cols = [
        "temperature_lag_1",
        "temperature_lag_2",
        "temperature_lag_7",
        "temperature_rolling_7",
        "temperature_rolling_30",
    ]

    model_df = df.dropna(
        subset=feature_cols + ["target"]
    ).copy()

    # Time-based train/test split.
    split = int(len(model_df) * 0.80)

    train = model_df.iloc[:split]
    test = model_df.iloc[split:]

    model = xgb.XGBRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="reg:squarederror",
        random_state=42,
        n_jobs=4,
    )

    model.fit(
        train[feature_cols],
        train["target"],
    )

    # Model evaluation.
    pred = model.predict(test[feature_cols])

    mae = mean_absolute_error(
        test["target"],
        pred,
    )

    rmse = np.sqrt(
        mean_squared_error(
            test["target"],
            pred,
        )
    )

    r2 = r2_score(
        test["target"],
        pred,
    )

    # --------------------------------------------------
    # CURRENT LIVE TEMPERATURE
    # --------------------------------------------------

    current_live_temp = float(
        live_raw.loc[
            live_raw["City"] == city,
            "Temperature"
        ].iloc[0]
    )

    # --------------------------------------------------
    # BUILD TOMORROW'S FORECAST INPUT
    # --------------------------------------------------

    latest = pd.DataFrame({
        "temperature_lag_1": [
            current_live_temp
        ],

        "temperature_lag_2": [
            df["temp_mean"].iloc[-1]
        ],

        "temperature_lag_7": [
            df["temp_mean"].iloc[-7]
        ],

        "temperature_rolling_7": [
            pd.concat([
                df["temp_mean"].iloc[-6:],
                pd.Series([current_live_temp])
            ]).mean()
        ],

        "temperature_rolling_30": [
            pd.concat([
                df["temp_mean"].iloc[-29:],
                pd.Series([current_live_temp])
            ]).mean()
        ],
    })

    # Generate tomorrow's prediction.
    next_prediction = float(
        model.predict(latest)[0]
    )

    # Tomorrow based on the current date.
    next_day = (
        pd.Timestamp.now().normalize()
        + pd.Timedelta(days=1)
    )

    return (
        next_prediction,
        next_day,
        mae,
        rmse,
        r2,
        latest.iloc[0].to_dict(),
    )

try:
    prediction, forecast_date, city_mae, city_rmse, city_r2, forecast_features = train_city_xgb(selected_city)

    p1, p2, p3, p4 = st.columns(4)

    p1.metric("Next-Day Forecast", f"{prediction:.2f} °C")
    p2.metric("MAE", f"{city_mae:.2f} °C")
    p3.metric("RMSE", f"{city_rmse:.2f} °C")
    p4.metric("R²", f"{city_r2:.3f}")

    st.caption(
        f"Forecast date: {forecast_date.date()}. "
        f"This is a city-specific XGBoost model trained on {selected_city}'s historical data."
    )

    st.subheader(" AI XGBoost Forecast Explanation")

    if st.button("Explain this forecast"):

        with st.spinner("Analysing XGBoost forecast..."):

            prompt = f"""
You are a climate data analyst explaining a machine-learning
temperature forecast from a climate dashboard.

City: {selected_city}
Forecast date: {forecast_date.date()}

Predicted temperature: {prediction:.2f} °C

XGBoost model evaluation:
MAE: {city_mae:.2f} °C
RMSE: {city_rmse:.2f} °C
R²: {city_r2:.3f}

Features used for this next-day prediction:
Previous day temperature:
{forecast_features["temperature_lag_1"]:.2f} °C

Temperature two days earlier:
{forecast_features["temperature_lag_2"]:.2f} °C

Temperature seven days earlier:
{forecast_features["temperature_lag_7"]:.2f} °C

7-day rolling average:
{forecast_features["temperature_rolling_7"]:.2f} °C

30-day rolling average:
{forecast_features["temperature_rolling_30"]:.2f} °C

Explain this forecast in simple language.

Cover:
1. What temperature the model predicts.
2. How recent temperature patterns are reflected in the prediction.
3. What the 7-day and 30-day rolling averages tell us.
4. Briefly explain MAE, RMSE and R² and what the provided values indicate about model performance.

Important:
- Do not invent any data.
- Do not perform a new prediction.
- The XGBoost model has already generated the prediction.
- Gemini is only explaining the model output.
- Do not claim that this forecast proves climate change.
- Keep the explanation concise and suitable for a dashboard.
"""

            insight = generate_ai_climate_insight(prompt)

            st.markdown(insight)

except Exception as e:
    st.warning(f"Could not train the XGBoost model for {selected_city}.")
    st.exception(e)
# -------------------- CITY COMPARISON LAST --------------------
st.divider()
st.header(" City Comparison — All 10 Cities")
st.caption("Live comparative analytics across all configured cities. Scores are project-defined.")

st.dataframe(
    live[[
        "City", "Temperature", "Feels Like", "Humidity",
        "PM2.5", "PM10", "Air Quality Impact",
        "Temperature Impact", "Overall Impact"
    ]].sort_values("Overall Impact", ascending=False),
    use_container_width=True,
    hide_index=True,
)

fig = px.bar(
    live.sort_values("Overall Impact"),
    x="Overall Impact",
    y="City",
    orientation="h",
    title="Overall City Impact Comparison",
    labels={"Overall Impact": "Overall Impact Score (project-defined)"},
)
st.plotly_chart(fig, use_container_width=True)

comparison_long = live.melt(
    id_vars="City",
    value_vars=["Air Quality Impact", "Temperature Impact"],
    var_name="Metric",
    value_name="Score",
)

fig = px.bar(
    comparison_long,
    x="City",
    y="Score",
    color="Metric",
    barmode="group",
    title="Air Quality vs Temperature Impact",
    labels={"Score": "Impact Score (project-defined)"},
)
st.plotly_chart(fig, use_container_width=True)

st.subheader(" Historical & Future City Summary")

fv = future_summary(historical, future)

city_summary = summary.merge(
    fv[
        [
            "City",
            "Projected Average",
            "Average Difference",
            "Projected Trend °C/decade",
        ]
    ],
    on="City",
    how="left",
)

st.dataframe(
    city_summary.sort_values(
        "Average Difference",
        ascending=False
    ),
    use_container_width=True,
    hide_index=True,
)


st.subheader(" AI City Comparison Narrative")

if st.button("Explain City Comparison"):

    with st.spinner("Analysing city comparison..."):

        comparison_data = live[
            [
                "City",
                "Temperature",
                "Feels Like",
                "Humidity",
                "PM2.5",
                "PM10",
                "Air Quality Impact",
                "Temperature Impact",
                "Overall Impact",
            ]
        ].sort_values(
            "Overall Impact",
            ascending=False
        )

        comparison_text = comparison_data.to_string(
            index=False
        )

        prompt = f"""
You are a climate data analyst explaining a
multi-city environmental comparison.

The dashboard contains live environmental data
for 10 Indian cities.

Here is the data calculated by Python:

{comparison_text}

Explain the comparison in simple language.

Cover:
1. Which cities have relatively higher and lower
   overall impact scores based on the provided data.
2. How temperature and air-quality conditions differ
   across the cities.
3. Which cities show relatively higher air-quality
   impact and which show relatively higher
   temperature impact.
4. Mention any notable patterns visible in the data.

Important:
- Use only the values provided.
- Do not invent or estimate any values.
- Do not calculate a new environmental index.
- The Overall Impact score is project-defined.
- Do not describe the score as an official AQI,
  government ranking, or scientific climate-risk score.
- Do not claim that a single day's comparison proves
  long-term climate change.
- Keep the explanation concise and suitable for a
  dashboard.
"""

        insight = generate_ai_climate_insight(prompt)

        st.markdown(insight)
        # -------------------- WHAT-IF SCENARIO SIMULATOR --------------------
st.header(" What-if Climate Scenario Simulator")

st.caption(
    "Adjust the environmental conditions to explore how a hypothetical "
    "scenario could change the project-defined climate impact score."
)

s1, s2, s3 = st.columns(3)

temp_change = s1.slider(
    " Temperature Change (°C)",
    min_value=-3.0,
    max_value=5.0,
    value=0.0,
    step=0.5,
)

pm25_change = s2.slider(
    " PM2.5 Change (%)",
    min_value=-50,
    max_value=100,
    value=0,
    step=10,
)

rainfall_change = s3.slider(
    " Rainfall Change (%)",
    min_value=-50,
    max_value=50,
    value=0,
    step=10,
)
# Scenario calculation

scenario_temp = selected["Temperature"] + temp_change
scenario_pm25 = selected["PM2.5"] * (1 + pm25_change / 100)

base_rainfall = historical[
    historical["City"] == selected_city
]["precipitation"].mean()

scenario_rainfall = base_rainfall * (1 + rainfall_change / 100)

scenario_temp_impact = temperature_impact(scenario_temp)

scenario_pm25_impact = min(
    scenario_pm25 / 75 * 100,
    100
)

scenario_rainfall_impact = min(
    abs(scenario_rainfall - base_rainfall)
    / max(base_rainfall, 1) * 100,
    100
)

scenario_index = round(
    scenario_temp_impact * 0.40
    + scenario_pm25_impact * 0.35
    + scenario_rainfall_impact * 0.25,
    2
)

current_index = round(
    temperature_impact(selected["Temperature"]) * 0.40
    + min(selected["PM2.5"] / 75 * 100, 100) * 0.35
    + 0 * 0.25,
    2
)

st.subheader(" Scenario Impact")

r1, r2, r3 = st.columns(3)

r1.metric(
    "Scenario Temperature",
    f"{scenario_temp:.1f} °C",
    f"{temp_change:+.1f} °C"
)

r2.metric(
    "Scenario PM2.5",
    f"{scenario_pm25:.1f}",
    f"{pm25_change:+.0f}%"
)

r3.metric(
    "Scenario Impact Index",
    f"{scenario_index:.1f}",
    f"{scenario_index - current_index:+.1f}",
    delta_color="inverse"
)
st.markdown("###  Scenario Interpretation")

impact_change = scenario_index - current_index

if impact_change > 5:
    impact_message = "This scenario indicates a substantial increase in the project-defined climate impact."
elif impact_change > 0:
    impact_message = "This scenario indicates a moderate increase in the project-defined climate impact."
elif impact_change < -5:
    impact_message = "This scenario indicates a substantial reduction in the project-defined climate impact."
elif impact_change < 0:
    impact_message = "This scenario indicates a moderate reduction in the project-defined climate impact."
else:
    impact_message = "This scenario produces little change in the project-defined climate impact."

st.info(
    f"Under this hypothetical scenario, the temperature changes by "
    f"{temp_change:+.1f}°C, PM2.5 changes by {pm25_change:+.0f}%, "
    f"and rainfall changes by {rainfall_change:+.0f}%. "
    f"The calculated impact index changes by {impact_change:+.1f} points. "
    f"{impact_message}"
)

st.caption(
    "This is a project-defined what-if simulation, not a climate forecast "
    "or official risk assessment."
)
st.markdown("###  Recommended Actions")

recommendations = []

if temp_change > 0:
    recommendations.append(
        " Heat preparedness: increase heat-alert monitoring, review cooling "
        "requirements, and plan measures for vulnerable populations."
    )

if pm25_change > 0:
    recommendations.append(
        " Air-quality response: strengthen PM2.5 monitoring and consider "
        "traffic, dust and emission-control measures during high-pollution periods."
    )

if rainfall_change < 0:
    recommendations.append(
        " Water planning: prepare for reduced rainfall through water "
        "conservation and drought-readiness measures."
    )

if rainfall_change > 0:
    recommendations.append(
        " Rainfall preparedness: review drainage, water-storage and "
        "flood-management capacity for periods of increased rainfall."
    )

if not recommendations:
    recommendations.append(
        " No major intervention is suggested for the selected baseline scenario. "
        "Continue routine environmental monitoring."
    )

for recommendation in recommendations:
    st.write(recommendation)
    # -------------------- ACTIONABLE CLIMATE STRATEGY ADVISOR --------------------
st.header("Actionable Climate Strategy Advisor")

st.caption(
    "Translate climate indicators into practical business and operational "
    "actions using the available environmental data."
)

st.markdown("### Generate Business Risk Strategy")

if st.button("Generate Business Risk Strategy"):

    # Prepare strategy data
    strategy_hist = historical[
        historical["City"] == selected_city
    ].copy()

    strategy_hist["month"] = strategy_hist["date"].dt.month

    current_month = pd.Timestamp.now().month

    monthly_hist = strategy_hist[
        strategy_hist["month"] == current_month
    ]

    monthly_temp_baseline = monthly_hist["temp_mean"].mean()

    temperature_delta = (
        selected["Temperature"] - monthly_temp_baseline
    )

    # Historical heat threshold
    heat_threshold = strategy_hist["temp_max"].quantile(0.95)

    strategy_hist["heat_day"] = (
        strategy_hist["temp_max"] >= heat_threshold
    )

    strategy_hist["heat_group"] = (
        strategy_hist["heat_day"]
        .ne(strategy_hist["heat_day"].shift())
        .cumsum()
    )

    strategy_heat_events = (
        strategy_hist[strategy_hist["heat_day"]]
        .groupby("heat_group")
        .agg(
            start_date=("date", "min"),
            end_date=("date", "max"),
            duration_days=("date", "count"),
            peak_temperature=("temp_max", "max"),
        )
        .reset_index(drop=True)
    )

    strategy_heat_events = strategy_heat_events[
        strategy_heat_events["duration_days"] >= 3
    ]

    heat_event_count = len(strategy_heat_events)

    # Historical temperature baseline
    hist_mean = strategy_hist["temp_mean"].mean()

    # Future projection
    future_city = future[
        future["City"] == selected_city
    ].copy()

    if not future_city.empty:
        future_mean = future_city["temp_mean"].mean()
        future_change = future_mean - hist_mean
    else:
        future_mean = hist_mean
        future_change = 0.0

    with st.spinner("Generating business strategy..."):

        strategy_prompt = f"""
You are a Climate Business Analyst.

Analyze the following environmental intelligence for {selected_city}.

Current temperature: {selected["Temperature"]:.1f} °C
Historical monthly temperature average: {monthly_temp_baseline:.1f} °C
Temperature anomaly: {temperature_delta:+.1f} °C
PM2.5: {selected["PM2.5"]:.1f}
PM10: {selected["PM10"]:.1f}
Historical heat events lasting at least 3 consecutive days: {heat_event_count}
Historical 95th percentile maximum temperature: {heat_threshold:.1f} °C
Historical mean temperature: {hist_mean:.2f} °C
Future projected mean temperature: {future_mean:.2f} °C
Future vs historical mean difference: {future_change:+.2f} °C

Generate a business-oriented climate strategy table.

Return ONLY a Markdown table with exactly these six columns:

| Priority | Business Area | Evidence | Business Impact | Recommended Action | KPI to Monitor |
|---|---|---|---|---|---|

Rules:
- Priority must be exactly High, Medium, or Monitor.
- Do not use Critical or any other priority label.
- Use only the environmental data provided above as evidence.
- Do not invent measurements or statistics.
- Keep recommendations practical and business-oriented.
- Business Impact should describe possible operational implications,
  not guaranteed outcomes.
- Recommended Action should be realistic and proportionate to the evidence.
- Do not assume that a specific technology, medical intervention,
  infrastructure investment, or financial decision is required unless
  supported by the provided data.
- KPI to Monitor should identify measurable indicators relevant to the issue.
- Do not provide an introduction, conclusion, or text outside the table.
- Do not use emojis.
"""

        strategy_result = generate_ai_climate_insight(
            strategy_prompt
        )

        st.markdown(strategy_result)

        st.session_state["last_strategy_table"] = strategy_result
        # -------------------- DOWNLOAD STRATEGY REPORT --------------------

if "last_strategy_table" in st.session_state:

    report_text = f"""
# Climate Strategy Report

## City
{selected_city}

## Current Environmental Snapshot

- Current Temperature: {selected["Temperature"]:.1f} °C
- PM2.5: {selected["PM2.5"]:.1f}
- PM10: {selected["PM10"]:.1f}
- Humidity: {selected["Humidity"]:.1f}%
- Feels Like Temperature: {selected["Feels Like"]:.1f} °C

## Historical Climate Evidence

- Historical Monthly Temperature Average: {monthly_temp_baseline:.1f} °C
- Current Temperature Anomaly: {temperature_delta:+.1f} °C
- Historical Heat Events (3+ consecutive days): {heat_event_count}
- Historical 95th Percentile Maximum Temperature: {heat_threshold:.1f} °C
- Historical Mean Temperature: {hist_mean:.2f} °C

## Future Climate Projection

- Projected Mean Temperature: {future_mean:.2f} °C
- Future vs Historical Mean Difference: {future_change:+.2f} °C

## Business Risk Strategy

{st.session_state["last_strategy_table"]}

## Methodology Note

This report translates the environmental indicators available in ClimatePulse
into business-oriented risk considerations and monitoring actions.

Climate thresholds, impact scores and recommendations used by ClimatePulse
are project-defined and should not be interpreted as official climate-risk
assessments.

Environmental observations and projections describe conditions and modeled
patterns; they do not by themselves establish causation for individual events.

Generated by ClimatePulse.
"""

    st.download_button(
        label="Download Strategy Report",
        data=report_text,
        file_name=f"{selected_city}_climate_strategy_report.md",
        mime="text/markdown",
    )