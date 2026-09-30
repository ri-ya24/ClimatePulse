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

load_dotenv()
from google import genai

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
def generate_ai_climate_insight(prompt):
    response = gemini_client.models.generate_content(
       model="gemini-3.8-flash",
        contents=prompt,
    )
    return response.text

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


@st.cache_data(ttl=86400, show_spinner=True)
def get_historical_all_cities():
    lats, lons = _city_coordinates()
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lats,
        "longitude": lons,
        "start_date": HIST_START,
        "end_date": HIST_END,
        "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum,wind_speed_10m_max",
        "timezone": "Asia/Kolkata",
        "temperature_unit": "celsius",
        "precipitation_unit": "mm",
        "wind_speed_unit": "kmh",
    }
    r = requests.get(url, params=params, timeout=180)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict):
        data = [data]

    frames = []
    for i, city in enumerate(CITY_NAMES):
        daily = data[i]["daily"]
        df = pd.DataFrame(daily)
        df["date"] = pd.to_datetime(df["time"])
        df["City"] = city
        df = df.rename(columns={
            "temperature_2m_max": "temp_max",
            "temperature_2m_min": "temp_min",
            "temperature_2m_mean": "temp_mean",
            "precipitation_sum": "precipitation",
            "wind_speed_10m_max": "wind_max",
        })
        frames.append(df[[
            "City", "date", "temp_max", "temp_min",
            "temp_mean", "precipitation", "wind_max"
        ]])
    return pd.concat(frames, ignore_index=True)


@st.cache_data(ttl=86400, show_spinner=True)
def get_future_all_cities():
    lats, lons = _city_coordinates()
    url = "https://climate-api.open-meteo.com/v1/climate"
    params = {
        "latitude": lats,
        "longitude": lons,
        "start_date": FUTURE_START,
        "end_date": FUTURE_END,
        "models": "EC_Earth3P_HR",
        "daily": "temperature_2m_mean,temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "Asia/Kolkata",
        "temperature_unit": "celsius",
        "precipitation_unit": "mm",
    }
    r = requests.get(url, params=params, timeout=180)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict):
        data = [data]

    frames = []
    for i, city in enumerate(CITY_NAMES):
        daily = data[i]["daily"]
        df = pd.DataFrame(daily)
        df["date"] = pd.to_datetime(df["time"])
        df["City"] = city
        df = df.rename(columns={
            "temperature_2m_mean": "temp_mean",
            "temperature_2m_max": "temp_max",
            "temperature_2m_min": "temp_min",
            "precipitation_sum": "precipitation",
        })
        frames.append(df[[
            "City", "date", "temp_mean", "temp_max",
            "temp_min", "precipitation"
        ]])
    return pd.concat(frames, ignore_index=True)


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
st.title("🌍 ClimatePulse")
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
    "📍 Select City",
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

st.caption("Live weather and air-quality values are current API observations; values can change between refreshes.")

# -------------------- HISTORICAL TREND --------------------
st.header(f"📈 Historical Climate Trend — {selected_city}")

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
m1.metric("Historical Average", f'{sel_sum["Historical Average"]:.2f} °C')
m2.metric("Trend", f'{sel_sum["Historical Trend °C/decade"]:.3f} °C/decade')
m3.metric("95th Percentile Max", f'{sel_sum["95th Percentile Max °C"]:.2f} °C')

# -------------------- EXTREME EVENTS --------------------
st.header(f"🔥 Extreme Events & Climate Anomalies — {selected_city}")

anom = anomaly_table(historical)
sel_anom = anom[anom["City"] == selected_city].copy()

ec1, ec2, ec3 = st.columns(3)
ec1.metric("Historical Observations", f'{len(historical[historical["City"] == selected_city]):,}')
ec2.metric("Detected Anomalies", f'{len(sel_anom):,}')
ec3.metric(
    "Anomaly Rate",
    f'{(len(sel_anom) / max(len(historical[historical["City"] == selected_city]), 1) * 100):.2f}%'
)

if len(sel_anom):
    st.dataframe(
        sel_anom[[
            "date", "temp_mean", "precipitation",
            "wind_max", "Anomaly Score"
        ]].head(20),
        use_container_width=True,
        hide_index=True,
    )

st.caption("Anomalies are statistical outliers detected from temperature, precipitation and wind; they are not automatically climate-change events.")

# -------------------- HISTORICAL VS FUTURE --------------------
st.header(f"🔮 Historical vs Future Climate — {selected_city}")

fv = future_summary(historical, future)
sel_fv = fv[fv["City"] == selected_city].iloc[0]

f1, f2, f3 = st.columns(3)
f1.metric("Historical Average", f'{sel_fv["Historical Average"]:.2f} °C')
f2.metric("Projected Average", f'{sel_fv["Projected Average"]:.2f} °C')
f3.metric("Average Difference", f'{sel_fv["Average Difference"]:+.2f} °C')

st.caption("Historical values use 1990–2025 reanalysis data. Future values use an EC-Earth3P-HR climate-model projection and are not certain future observations.")

compare_plot = pd.DataFrame({
    "Period": ["Historical (1990–2025)", "Projected (2026–2049)"],
    "Average Temperature": [
        sel_fv["Historical Average"],
        sel_fv["Projected Average"],
    ],
})
fig = px.bar(
    compare_plot,
    x="Period",
    y="Average Temperature",
    text_auto=".2f",
    title=f"Historical vs Projected Average — {selected_city}",
    labels={"Average Temperature": "Temperature (°C)"},
)
st.plotly_chart(fig, use_container_width=True)

# -------------------- FUTURE PROJECTION --------------------
st.header(f"🌡️ Future Climate Projection — {selected_city}")

future_city = future[future["City"] == selected_city].copy()
future_annual = (
    future_city.assign(Year=future_city["date"].dt.year)
    .groupby("Year")["temp_mean"]
    .mean()
    .reset_index()
)

fig = px.line(
    future_annual,
    x="Year",
    y="temp_mean",
    markers=True,
    title=f"Projected Annual Mean Temperature — {selected_city}",
    labels={"temp_mean": "Projected Mean Temperature (°C)"},
)
st.plotly_chart(fig, use_container_width=True)

st.caption("Projection is model-based and should not be interpreted as a guaranteed future observation.")

# -------------------- CLIMATE IMPACT INDEX --------------------
st.header("🌍 Climate Impact Index")

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

st.subheader("🤖 AI Climate Insight")

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
st.header(f"🤖 ML Temperature Forecast — {selected_city}")

@st.cache_resource(show_spinner=True)
def train_city_xgb(city):
    import xgboost as xgb
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    df = historical[historical["City"] == city].sort_values("date").copy()

    # Same feature engineering concept used for the original Lucknow model.
    df["temperature_lag_1"] = df["temp_mean"].shift(1)
    df["temperature_lag_2"] = df["temp_mean"].shift(2)
    df["temperature_lag_7"] = df["temp_mean"].shift(7)
    df["temperature_rolling_7"] = df["temp_mean"].rolling(7).mean()
    df["temperature_rolling_30"] = df["temp_mean"].rolling(30).mean()

    # Next-day temperature is the prediction target.
    df["target"] = df["temp_mean"].shift(-1)

    feature_cols = [
        "temperature_lag_1",
        "temperature_lag_2",
        "temperature_lag_7",
        "temperature_rolling_7",
        "temperature_rolling_30",
    ]

    model_df = df.dropna(subset=feature_cols + ["target"]).copy()

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

    model.fit(train[feature_cols], train["target"])

    pred = model.predict(test[feature_cols])

    mae = mean_absolute_error(test["target"], pred)
    rmse = np.sqrt(mean_squared_error(test["target"], pred))
    r2 = r2_score(test["target"], pred)

    # Build the next-day input from the latest available observation.
    latest = pd.DataFrame({
        "temperature_lag_1": [df["temp_mean"].iloc[-1]],
        "temperature_lag_2": [df["temp_mean"].iloc[-2]],
        "temperature_lag_7": [df["temp_mean"].iloc[-7]],
        "temperature_rolling_7": [df["temp_mean"].iloc[-7:].mean()],
        "temperature_rolling_30": [df["temp_mean"].iloc[-30:].mean()],
    })

    next_prediction = float(model.predict(latest)[0])
    next_day = df["date"].max() + pd.Timedelta(days=1)

    return next_prediction, next_day, mae, rmse, r2


try:
    prediction, forecast_date, city_mae, city_rmse, city_r2 = train_city_xgb(selected_city)

    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Next-Day Forecast", f"{prediction:.2f} °C")
    p2.metric("MAE", f"{city_mae:.2f} °C")
    p3.metric("RMSE", f"{city_rmse:.2f} °C")
    p4.metric("R²", f"{city_r2:.3f}")

    st.caption(
        f"Forecast date: {forecast_date.date()}. "
        f"This is a city-specific XGBoost model trained on {selected_city}'s historical data."
    )
except Exception as e:
    st.warning(f"Could not train the XGBoost model for {selected_city}.")
    st.exception(e)

# -------------------- CITY COMPARISON LAST --------------------
st.divider()
st.header("🏙️ City Comparison — All 10 Cities")
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

st.subheader("📊 Historical & Future City Summary")

city_summary = summary.merge(
    fv[["City", "Projected Average", "Average Difference", "Projected Trend °C/decade"]],
    on="City",
    how="left",
)

st.dataframe(
    city_summary.sort_values("Average Difference", ascending=False),
    use_container_width=True,
    hide_index=True,
)

fig = px.bar(
    city_summary.sort_values("Average Difference"),
    x="Average Difference",
    y="City",
    orientation="h",
    title="Historical-to-Projected Average Temperature Difference",
    labels={"Average Difference": "Projected − Historical (°C)"},
)
st.plotly_chart(fig, use_container_width=True)


