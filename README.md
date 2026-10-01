# ClimatePulse — Live Climate Impact Intelligence System

###LIVE DASHBOARD: https://climatepulse-in.streamlit.app/

ClimatePulse is an AI-powered climate intelligence dashboard that combines live environmental data, historical climate analysis, machine learning, future climate projections, and Generative AI into a single interactive application.

The objective is to move beyond displaying raw weather values and instead provide interpretable insights into climate anomalies, extreme events, long-term trends, future conditions, and potential environmental impact.

## What I Built

### Live Environmental Monitoring

ClimatePulse collects live weather and air-quality data and presents:

- Temperature and feels-like temperature
- Humidity, rainfall, and wind
- PM2.5 and PM10
- Temperature impact
- Air-quality impact
- Overall climate impact

Live conditions can also be compared across 10 major Indian cities.

### Historical Climate Analysis

Historical weather data is used to establish a climate baseline and analyse long-term patterns.

The dashboard evaluates:

- Historical temperature averages
- Monthly climate patterns
- Temperature anomalies
- Long-term temperature trends
- Rainfall trends and deviations
- Consecutive dry periods

This makes it possible to answer questions such as:

> Is today's temperature unusual compared with historical conditions?

### Extreme Event Detection

ClimatePulse identifies project-defined extreme heat events using historical temperature percentiles and consecutive hot days.

It also analyses:

- Extreme heat days
- Multi-day heat events
- Long dry spells
- Unusual rainfall conditions

### Machine Learning

ClimatePulse uses two machine learning approaches.

**XGBoost Temperature Forecasting**

A short-term temperature forecasting model trained using historical temperature patterns, lag features, and rolling statistics.

The model is evaluated using:

- MAE
- RMSE
- R²
- Comparison with a naïve baseline

**Isolation Forest**

Used to identify unusual climate observations and detect potential anomalies within historical data.

### Future Climate Projections

ClimatePulse uses CMIP6-based climate projections to explore possible future changes in temperature and precipitation.

The current projection analysis uses the EC-Earth3P-HR climate model for the study period.

These projections represent possible future climate conditions rather than exact predictions.

### Climate Impact Index

The project includes a composite Climate Impact Index based on:

- Heat impact
- Rainfall deviation
- Air-quality impact
- Dryness

The index provides a single analytical indicator for interpreting and comparing environmental impact.

The index is project-defined and is not an official government climate-risk or air-quality index.

### Generative AI

Gemini is integrated to convert analytical results and machine-learning outputs into understandable natural-language insights.

AI features include:

- Climate insights
- Anomaly explanations
- Historical trend explanations
- Forecast explanations
- City comparison narratives
- Daily climate reports
- Natural-language climate queries
- What-if climate scenarios
- Actionable climate strategy recommendations

The AI layer is designed to explain the underlying analysis rather than replace the data-driven calculations.

## Data Sources

ClimatePulse combines live APIs with historical and future climate datasets:

- **Open-Meteo Forecast API** — live weather data
- **Open-Meteo Air Quality API** — live air-quality data
- **Open-Meteo Historical Weather / ERA5** — historical climate data
- **Open-Meteo Climate API / CMIP6** — future climate projections

## How the Analysis Works

The project follows a data-to-insight approach:

**Environmental Data → Climate Baselines → Anomalies & Trends → Extreme Event Detection → ML Forecasting & Anomaly Detection → Future Projections → Climate Impact Analysis → Generative AI Insights**

This allows ClimatePulse to transform environmental measurements into interpretable climate intelligence.

## Technology Stack

**Python**  
**Pandas**  
**NumPy**  
**Plotly**  
**Streamlit**  
**Scikit-learn**  
**XGBoost**  
**PostgreSQL**  
**SQLAlchemy**  
**Google Gemini API**

## Scientific Considerations

ClimatePulse distinguishes between weather observations and climate analysis.

A single unusual day is not treated as evidence of climate change. Climate-related insights are derived from historical baselines, long-term trends, anomalies, and future climate projections.

All composite impact scores and scenario scores are project-defined analytical indicators and should not be interpreted as official climate-risk indices.



## Author

**Riya Singh**

BCA | Data Analytics & AI

GitHub: https://github.com/ri-ya24
