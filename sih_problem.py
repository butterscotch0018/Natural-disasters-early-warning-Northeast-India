import streamlit as st
import pandas as pd
import numpy as np
import folium
import plotly.express as px
from streamlit_folium import st_folium
from datetime import datetime

st.set_page_config(
    page_title="Natural disasters Early Warning — Northeast India",
    page_icon="⛰️",
    layout="wide"
)

# ---------------- DEMO DATA ----------------
ZONES = [
    {"name": "Cherrapunji", "lat": 25.2702, "lon": 91.7323,
     "rain": 85, "moisture": 82, "slope": 78, "base": 75,
     "road": "Monitoring"},
    {"name": "Mawsynram", "lat": 25.2970, "lon": 91.5828,
     "rain": 92, "moisture": 88, "slope": 70, "base": 72,
     "road": "Open"},
    {"name": "Tura", "lat": 25.5141, "lon": 90.2025,
     "rain": 48, "moisture": 55, "slope": 62, "base": 45,
     "road": "Open"},
    {"name": "Aizawl", "lat": 23.7271, "lon": 92.7176,
     "rain": 70, "moisture": 68, "slope": 88, "base": 65,
     "road": "Monitoring"},
    {"name": "Kohima", "lat": 25.6751, "lon": 94.1086,
     "rain": 55, "moisture": 60, "slope": 80, "base": 50,
     "road": "Open"},
    {"name": "Gangtok", "lat": 27.3389, "lon": 88.6065,
     "rain": 76, "moisture": 73, "slope": 85, "base": 68,
     "road": "Monitoring"},
]

def risk_score(rain, moisture, slope, base):
    # Illustrative weighted index, not a validated ML model
    score = (
        0.35 * rain +
        0.25 * moisture +
        0.25 * slope +
        0.15 * base
    )
    return round(min(100, max(0, score)))

def risk_level(score):
    if score >= 75:
        return "Critical"
    if score >= 60:
        return "High"
    if score >= 40:
        return "Moderate"
    return "Low"

def risk_color(level):
    return {
        "Low": "#2e9d62",
        "Moderate": "#e5b52f",
        "High": "#f07835",
        "Critical": "#d62739",
    }[level]

if "reports" not in st.session_state:
    st.session_state.reports = []

if "alerts" not in st.session_state:
    st.session_state.alerts = []

# ---------------- SIDEBAR ----------------
st.sidebar.title("⛰️ Natural Disasters Early Warning — Northeast India")
st.sidebar.caption("Disaster intelligence prototype")
page = st.sidebar.radio(
    "Navigation",
    ["Overview", "Risk Map", "Field Reporting", "Alerts"]
)

st.sidebar.divider()
st.sidebar.caption("DEMONSTRATION MODE")
st.sidebar.info(
    "Risk values and locations are illustrative. "
    "No live sensor or government API is connected."
)

# ---------------- HEADER ----------------
st.title("Natural disasters early warning — Northeast India")
st.write(
    "AI-assisted landslide risk monitoring and road connectivity "
    "decision support for Northeast India."
)

# Interactive scenario controls
with st.expander("⚙️ Simulate changing weather conditions"):
    c1, c2, c3 = st.columns(3)
    with c1:
        rain_change = st.slider(
            "Rainfall intensity", 0, 100, 70,
            help="Illustrative rainfall intensity index"
        )
    with c2:
        moisture_change = st.slider(
            "Soil moisture", 0, 100, 65
        )
    with c3:
        forecast_hours = st.selectbox(
            "Forecast window", [3, 6, 12, 24]
        )

# ---------------- RISK DATA ----------------
rows = []

for z in ZONES:
    rain = round((z["rain"] + rain_change) / 2)
    moisture = round((z["moisture"] + moisture_change) / 2)
    score = risk_score(rain, moisture, z["slope"], z["base"])
    level = risk_level(score)

    rows.append({
        "Zone": z["name"],
        "Latitude": z["lat"],
        "Longitude": z["lon"],
        "Rainfall index": rain,
        "Soil moisture index": moisture,
        "Slope index": z["slope"],
        "Risk score": score,
        "Risk level": level,
        "Road status": z["road"],
    })

df = pd.DataFrame(rows)

# ---------------- OVERVIEW ----------------
if page == "Overview":
    critical = int((df["Risk level"] == "Critical").sum())
    high = int((df["Risk level"] == "High").sum())
    monitored = int(
        df["Road status"].isin(["Monitoring", "Blocked"]).sum()
    )

    a, b, c, d = st.columns(4)
    a.metric("Zones monitored", len(df))
    b.metric("High risk zones", high)
    c.metric("Critical zones", critical)
    d.metric("Roads under monitoring", monitored)

    st.subheader("Regional risk map")

    m = folium.Map(
        location=[25.7, 91.7],
        zoom_start=6,
        tiles="OpenStreetMap"
    )

    for _, r in df.iterrows():
        level = r["Risk level"]
        popup = (
            f"<b>{r['Zone']}</b><br>"
            f"Risk: {level}<br>"
            f"Risk score: {r['Risk score']}/100<br>"
            f"Road: {r['Road status']}"
        )

        folium.CircleMarker(
            location=[r["Latitude"], r["Longitude"]],
            radius=9 + r["Risk score"] / 12,
            color=risk_color(level),
            fill=True,
            fill_color=risk_color(level),
            fill_opacity=0.75,
            tooltip=f"{r['Zone']}: {level}",
            popup=folium.Popup(popup, max_width=250)
        ).add_to(m)

    st_folium(m, use_container_width=True, height=480)

    left, right = st.columns(2)

    with left:
        st.subheader("Risk by zone")
        chart = px.bar(
            df.sort_values("Risk score", ascending=True),
            x="Risk score",
            y="Zone",
            color="Risk level",
            color_discrete_map={
                level: risk_color(level)
                for level in ["Low", "Moderate", "High", "Critical"]
            },
            orientation="h",
            range_x=[0, 100]
        )
        st.plotly_chart(chart, use_container_width=True)

    with right:
        st.subheader("Weather-linked risk")
        st.line_chart(
            df.set_index("Zone")[
                ["Rainfall index", "Soil moisture index"]
            ]
        )

    st.subheader("Zone monitoring table")
    st.dataframe(
        df[["Zone", "Risk score", "Risk level", "Road status"]],
        use_container_width=True,
        hide_index=True
    )

# ---------------- RISK MAP ----------------
elif page == "Risk Map":
    st.subheader("Explore vulnerable zones")

    selected = st.selectbox("Select zone", df["Zone"].tolist())
    r = df[df["Zone"] == selected].iloc[0]

    x, y, z = st.columns(3)
    x.metric("Risk score", f"{r['Risk score']}/100")
    y.metric("Risk level", r["Risk level"])
    z.metric("Road status", r["Road status"])

    st.write(f"Selected zone: **{selected}**")
    st.write(
        f"Illustrative forecast window: next {forecast_hours} hours. "
        "This is a scenario, not a calibrated forecast."
    )

    factors = pd.DataFrame({
        "Factor": [
            "Rainfall", "Soil moisture",
            "Slope", "Historical susceptibility"
        ],
        "Index": [
            r["Rainfall index"], r["Soil moisture index"],
            r["Slope index"], ZONES[
                df.index[df["Zone"] == selected][0]
            ]["base"]
        ]
    })

    st.plotly_chart(
        px.bar(
            factors, x="Factor", y="Index",
            range_y=[0, 100], title="Illustrative risk factors"
        ),
        use_container_width=True
    )

    st.warning(
        "A high score indicates a demonstration risk category, "
        "not a confirmed probability of a landslide."
    )

# ---------------- FIELD REPORTING ----------------
elif page == "Field Reporting":
    st.subheader("Submit a field incident")
    st.write(
        "Record a reported crack, slope movement, landslide "
        "or road blockage. Reports remain in this demo session."
    )

    with st.form("incident_form"):
        reporter = st.text_input("Reporter / team")
        zone = st.selectbox("Area", df["Zone"].tolist())
        incident = st.selectbox(
            "Incident type",
            [
                "Slope cracks",
                "Slope movement",
                "Landslide",
                "Road blockage",
                "Falling debris",
                "Other"
            ]
        )
        severity = st.select_slider(
            "Observed severity",
            options=["Low", "Moderate", "High", "Critical"]
        )
        description = st.text_area("Description")
        photo = st.file_uploader(
            "Upload optional photograph",
            type=["jpg", "jpeg", "png"]
        )

        submitted = st.form_submit_button("Submit report")

        if submitted:
            if not description.strip():
                st.error("Please provide an incident description.")
            else:
                st.session_state.reports.append({
                    "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Reporter": reporter or "Anonymous",
                    "Zone": zone,
                    "Incident": incident,
                    "Severity": severity,
                    "Description": description,
                    "Photo name": photo.name if photo else "None",
                    "Status": "Pending verification"
                })
                if severity in ["High", "Critical"]:
                    st.session_state.alerts.append({
                        "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Zone": zone,
                        "Severity": severity,
                        "Message": f"Field report: {incident}",
                        "Status": "Demo alert — not sent"
                    })
                st.success("Report recorded in this demo session.")

    st.subheader("Submitted reports")
    if st.session_state.reports:
        st.dataframe(
            pd.DataFrame(st.session_state.reports).drop(
                columns=["Description"]
            ),
            use_container_width=True,
            hide_index=True
        )
        st.caption(
            "Reports are held in memory and will be lost when "
            "the application session resets."
        )
    else:
        st.info("No field reports submitted yet.")

# ---------------- ALERTS ----------------
elif page == "Alerts":
    st.subheader("Early warning centre")
    st.caption(
        "Demonstration alerts only. No real SMS or emergency "
        "notifications are sent."
    )

    high_zones = df[df["Risk level"].isin(["High", "Critical"])]

    for _, r in high_zones.iterrows():
        st.warning(
            f"**{r['Risk level']} risk — {r['Zone']}**\n\n"
            f"Score: {r['Risk score']}/100. "
            "Recommended action: verify current conditions and "
            "follow authorized local disaster protocols."
        )

    st.subheader("Simulate an alert")
    with st.form("alert_form"):
        alert_zone = st.selectbox("Alert area", df["Zone"].tolist())
        alert_severity = st.selectbox(
            "Alert severity", ["Moderate", "High", "Critical"]
        )
        channel = st.selectbox(
            "Intended channel",
            ["SMS", "Mobile app", "District dashboard"]
        )
        message = st.text_area(
            "Warning message",
            "Heavy rainfall may increase landslide risk. "
            "Avoid vulnerable slopes and follow official advisories."
        )
        send = st.form_submit_button("Create demo alert")

        if send:
            st.session_state.alerts.append({
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Zone": alert_zone,
                "Severity": alert_severity,
                "Message": message,
                "Status": f"Simulated via {channel} — not sent"
            })
            st.success("Demo alert created. No message was transmitted.")

    st.subheader("Alert history")
    if st.session_state.alerts:
        st.dataframe(
            pd.DataFrame(st.session_state.alerts),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No alerts created in this session.")

st.divider()
st.caption(
    "NER Sentinel AI | Prototype v0.1 | "
    "Illustrative data only — not for operational emergency use."
)