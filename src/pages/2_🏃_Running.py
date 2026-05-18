"""Running Coach"""

import os
import pandas as pd
import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv()

# =========================
# ENV VARIABLES
# =========================
AGE = os.getenv("AGE")
GENDER = os.getenv("GENDER")
HEIGHT = os.getenv("HEIGHT")
WEIGHT = os.getenv("WEIGHT")

PACE_TARGET = os.getenv("PACE")
HEART_RATE_TARGET = os.getenv("HEART_RATE")
STRIDE_LENGTH_TARGET = os.getenv("STRIDE_LENGTH")
GROUND_CONTACT_TIME_TARGET = os.getenv("GROUND_CONTACT_TIME")

HEALTH_RECORD_FILE = os.getenv("HEALTH_RECORD_FILE")
HEALTH_WORKOUT_FILE = os.getenv("HEALTH_WORKOUT_FILE")

# =========================
# OLLAMA CONFIG
# =========================
OLLAMA_URL = "http://ollama:11434/api/generate"
MODEL = "llama3.2:1b"

# =========================
# STREAMLIT CONFIG
# =========================
st.set_page_config(page_title="Running", page_icon="🏃")

st.sidebar.header("Running")
st.sidebar.write(
    """
Running should be a lifelong activity. 
Approach it patiently and intelligently, and it will reward you for a long time.
"""
)

st.header("Running 🏃", divider=True)

target_column, dashboard_column, recommendation_column = st.columns(3)

# =========================
# DATA FUNCTIONS
# =========================
@st.cache_data
def load_records(file):
    return pd.read_csv(file)

@st.cache_data
def load_workouts(file):
    return pd.read_csv(file)

@st.cache_data
def get_records_for_workout(all_records, record_type, start, end):
    records = all_records.loc[all_records["type"] == record_type]
    records = records.loc[
        (records["startDate"] >= start) &
        (records["endDate"] <= end)
    ]

    if not records.empty:
        records.reset_index(drop=True, inplace=True)
        unit = records["unit"].iloc[0]

        if record_type in [
            "HeartRate",
            "RunningStrideLength",
            "RunningPower",
            "RunningVerticalOscillation",
            "RunningGroundContactTime",
            "RunningSpeed",
        ]:
            return {
                f"max {record_type} ({unit})": records["value"].max(),
                f"min {record_type} ({unit})": records["value"].min(),
                f"mean {record_type} ({unit})": records["value"].mean(),
            }

        if record_type in ["ActiveEnergyBurned", "BasalEnergyBurned"]:
            return {f"{record_type} ({unit})": records["value"].sum()}

    return {}

@st.cache_data
def get_workout_statistics(all_workouts, workout_type, all_records, record_types):
    workouts = all_workouts.loc[
        all_workouts["workoutActivityType"] == workout_type
    ]

    statistics = []

    for _, row in workouts.iterrows():
        stat = {}
        stat["type"] = workout_type
        stat[f'duration ({row["durationUnit"]})'] = row["duration"]
        stat["time"] = row["startDate"]
        stat["date"] = row["startDate"][:10]

        for record_type in record_types:
            stat.update(
                get_records_for_workout(
                    all_records,
                    record_type,
                    row["startDate"],
                    row["endDate"],
                )
            )

        if len(stat) == 24:
            pace = 1000 / 60 / stat["mean RunningSpeed (m/s)"]
            stat["pace (min/km)"] = f"{pace:.2f}"
            stat["distance (km)"] = f'{(stat["duration (min)"] / pace):.2f}'

            if float(stat["distance (km)"]) >= 0.1:
                statistics.append(stat)

    return statistics

def show_status(ok):
    if ok:
        return st.success("You have reached the target!", icon="😊")
    return st.error("You are doing fine... Keep running!", icon="😢")

# =========================
# TARGET
# =========================
with target_column:
    st.subheader("Target")

    st.write(f"""
    Pace: {PACE_TARGET} min/km  
    Heart Rate: {HEART_RATE_TARGET} bpm  
    Stride Length: {STRIDE_LENGTH_TARGET} m  
    Ground Contact Time: {GROUND_CONTACT_TIME_TARGET} ms
    """)

# =========================
# LOAD DATA
# =========================
records = load_records(HEALTH_RECORD_FILE)
workouts = load_workouts(HEALTH_WORKOUT_FILE)

runnings = get_workout_statistics(
    workouts,
    "Running",
    records,
    [
        "HeartRate",
        "RunningStrideLength",
        "RunningPower",
        "RunningVerticalOscillation",
        "RunningGroundContactTime",
        "RunningSpeed",
        "ActiveEnergyBurned",
        "BasalEnergyBurned",
    ],
)

runnings_pd = pd.DataFrame(runnings)

runnings_pd["distance (km)"] = runnings_pd["distance (km)"].astype("float")
runnings_pd["pace (min/km)"] = runnings_pd["pace (min/km)"].astype("float")

# =========================
# SELECT RUN
# =========================
running_dates = [x["time"] for x in runnings]
default_msg = "Overview"
running_dates.insert(0, default_msg)

running_date = st.selectbox("Running history", running_dates)

if running_date != default_msg:
    running_statistics = [x for x in runnings if x["time"] == running_date][0]

    running_statistics_pd = pd.DataFrame(running_statistics, index=[0])
    running_statistics_pd["distance (km)"] = running_statistics_pd[
        "distance (km)"
    ].astype("float")

    running_statistics_pd["pace (min/km)"] = running_statistics_pd[
        "pace (min/km)"
    ].astype("float")

ask_coach = st.button(
    "Ask coach",
    type="primary",
    disabled=(running_date == default_msg),
)

# =========================
# DASHBOARD (UNCHANGED)
# =========================
with dashboard_column:
    st.subheader("Dashboard")
    analysis = st.empty()

    if running_date == default_msg:
        with analysis.container():

            total = len(runnings)

            last_n = st.slider(
                "Show recent number of runnings",
                min_value=1,
                max_value=total,
                value=total,
            )

            style = st.radio("Style", ["line", "scatter"], horizontal=True)

            overall = runnings_pd[["date", "distance (km)", "duration (min)"]]

            st.pyplot(
                overall[-last_n:]
                .plot(title="Distance and Duration", x="date", kind="bar")
                .figure
            )

            st.pyplot(
                runnings_pd[-last_n:]
                .plot(title="Pace", x="date", y="pace (min/km)", kind=style)
                .axhline(y=float(PACE_TARGET), color="red")
                .figure
            )

            st.pyplot(
                runnings_pd[-last_n:]
                .plot(
                    title="Heart Rate",
                    x="date",
                    y="mean HeartRate (count/min)",
                    kind=style,
                )
                .axhline(y=int(HEART_RATE_TARGET), color="red")
                .figure
            )

            st.pyplot(
                runnings_pd[-last_n:]
                .plot(
                    title="Stride Length",
                    x="date",
                    y="mean RunningStrideLength (m)",
                    kind=style,
                )
                .axhline(y=float(STRIDE_LENGTH_TARGET), color="red")
                .figure
            )

            st.pyplot(
                runnings_pd[-last_n:]
                .plot(
                    title="Ground Contact Time",
                    x="date",
                    y="mean RunningGroundContactTime (ms)",
                    kind=style,
                )
                .axhline(y=float(GROUND_CONTACT_TIME_TARGET), color="red")
                .figure
            )

    else:
        analysis.empty()

        show_status(float(running_statistics["pace (min/km)"]) < float(PACE_TARGET))

        st.pyplot(
            running_statistics_pd.plot(
                title="Pace",
                x="date",
                y="pace (min/km)",
                kind="scatter",
            )
            .axhline(y=float(PACE_TARGET), color="red")
            .figure
        )

        show_status(
            float(running_statistics["mean HeartRate (count/min)"])
            < float(HEART_RATE_TARGET)
        )

        st.pyplot(
            running_statistics_pd.plot(
                title="Heart Rate",
                x="date",
                y="mean HeartRate (count/min)",
                kind="scatter",
            )
            .axhline(y=int(HEART_RATE_TARGET), color="red")
            .figure
        )

        show_status(
            float(running_statistics["mean RunningStrideLength (m)"])
            > float(STRIDE_LENGTH_TARGET)
        )

        st.pyplot(
            running_statistics_pd.plot(
                title="Stride Length",
                x="date",
                y="mean RunningStrideLength (m)",
                kind="scatter",
            )
            .axhline(y=float(STRIDE_LENGTH_TARGET), color="red")
            .figure
        )

        show_status(
            float(running_statistics["mean RunningGroundContactTime (ms)"])
            < float(GROUND_CONTACT_TIME_TARGET)
        )

        st.pyplot(
            running_statistics_pd.plot(
                title="Ground Contact Time",
                x="date",
                y="mean RunningGroundContactTime (ms)",
                kind="scatter",
            )
            .axhline(y=float(GROUND_CONTACT_TIME_TARGET), color="red")
            .figure
        )

# =========================
# OLLAMA (ONLY NEW PART)
# =========================
def ask_ollama(prompt: str):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        )

        data = response.json()

        if "error" in data:
            return f"Ollama error: {data['error']}"

        return data.get("response", "No response")

    except Exception as e:
        return f"Connection error: {str(e)}"

# =========================
# RECOMMENDATION (ONLY MODIFIED)
# =========================
with recommendation_column:
    st.subheader("Recommendation")
    coach_says = st.empty()

    if running_date in st.session_state:
        coach_says.write(st.session_state[running_date])

    if ask_coach:

        SYSTEM_MESSAGE = """
You are a professional running coach.
Give clear, actionable advice in bullet points.
"""

        HUMAN_MESSAGE = f"""
User profile:
Age: {AGE}
Gender: {GENDER}
Height: {HEIGHT}
Weight: {WEIGHT}

Targets:
Pace: {PACE_TARGET}
Heart Rate: {HEART_RATE_TARGET}
Stride Length: {STRIDE_LENGTH_TARGET}
Ground Contact Time: {GROUND_CONTACT_TIME_TARGET}

Data:
{running_statistics}
"""

        full_prompt = SYSTEM_MESSAGE + "\n\n" + HUMAN_MESSAGE

        with st.spinner("Thinking with Ollama..."):
            result = ask_ollama(full_prompt)

        coach_says.write(result)
        st.session_state[running_date] = result