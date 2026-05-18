import os
import pandas as pd
import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv()

NAME = os.getenv("NAME")
HEALTH_WORKOUT_FILE = os.getenv("HEALTH_WORKOUT_FILE")

# -----------------------
# OLLAMA CONFIG (Docker)
# -----------------------
OLLAMA_URL = "http://ollama:11434/api/generate"
MODEL = "llama3.2:1b"


# -----------------------
# SAFE OLLAMA CALL
# -----------------------
def ask_ollama(prompt: str):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )

        # Si HTTP error
        if response.status_code != 200:
            return f"HTTP Error {response.status_code}: {response.text}"

        data = response.json()

        # Debug safety
        if not isinstance(data, dict):
            return f"Invalid response format: {data}"

        # Ollama error handling
        if "error" in data:
            return f"Ollama error: {data['error']}"

        # Safe access (fix KeyError: 'response')
        return data.get("response", "No response returned by Ollama")

    except Exception as e:
        return f"Connection error to Ollama: {str(e)}"


# -----------------------
# LOAD DATA
# -----------------------
@st.cache_data
def load_workouts(file):
    return pd.read_csv(file)


workout_df = load_workouts(HEALTH_WORKOUT_FILE)


def workout_summary():
    try:
        return workout_df.describe(include="all").to_string()
    except:
        return "No workout data available"


# -----------------------
# SIMPLE ASSISTANT LOGIC
# -----------------------
def run_assistant(prompt: str):

    system_prompt = f"""
You are a personal health assistant for {NAME}.

You analyze workout data and give clear, actionable answers.

Workout dataset summary:
{workout_summary()}

Rules:
- Be concise
- Use bullet points
- Focus on actionable insights
"""

    full_prompt = system_prompt + "\n\nUser question:\n" + prompt

    return ask_ollama(full_prompt)


# -----------------------
# STREAMLIT UI
# -----------------------
st.set_page_config(page_title="Assistant", page_icon="💬")

st.title("🤖 Health Assistant (Ollama Local)")

st.sidebar.header("Assistant")
st.sidebar.write("Running fully local with Ollama")

# -----------------------
# SESSION MEMORY
# -----------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": f"Hi {NAME}! Ask me anything about your health data."
        }
    ]


# -----------------------
# DISPLAY HISTORY
# -----------------------
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])


# -----------------------
# INPUT USER
# -----------------------
if prompt := st.chat_input("Ask your question..."):

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.spinner("Thinking with Ollama..."):
        response = run_assistant(prompt)

    st.session_state.messages.append(
        {"role": "assistant", "content": response}
    )

    st.chat_message("assistant").write(response)