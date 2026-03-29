import os
import json
import time
import streamlit as st

st.set_page_config(page_title="Speech-to-Speech Translator", layout="wide")

LOG_FILE = "translation_log.txt"
CONFIG_FILE = "config.json"

LANGUAGE_OPTIONS = {
    "Telugu": "te",
    "Hindi": "hi",
    "English": "en",
    "Tamil": "ta",
    "French": "fr",
    "Spanish": "es"
}


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"target_language": "te"}


def save_config(target_language):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"target_language": target_language}, f, indent=2)


def read_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return "No translations logged yet."


config = load_config()
current_lang = config.get("target_language", "te")

st.title("Real-Time Speech-to-Speech Translation Demo")
st.write("This UI is connected to the backend through a config file.")

st.subheader("System Pipeline")
st.code("Microphone Input -> Audio Streaming -> Noise Suppression -> VAD -> LID -> ASR -> Translation -> TTS -> Audio Output")

st.subheader("Choose Target Language")

label_list = list(LANGUAGE_OPTIONS.keys())
code_list = list(LANGUAGE_OPTIONS.values())

default_index = 0
if current_lang in code_list:
    default_index = code_list.index(current_lang)

selected_label = st.selectbox("Target language", label_list, index=default_index)
selected_code = LANGUAGE_OPTIONS[selected_label]

col1, col2 = st.columns(2)

with col1:
    if st.button("Update Target Language"):
        save_config(selected_code)
        st.success(f"Target language updated to: {selected_label} ({selected_code})")

with col2:
    st.info(f"Current backend target language: {load_config().get('target_language', 'te')}")

st.subheader("Translation Log")

if st.button("Refresh Log"):
    st.rerun()

log_text = read_log()
st.text_area("Live Logs", log_text, height=400)

st.subheader("How to Run")
st.code("Terminal 1: python app.py\nTerminal 2: streamlit run demo_ui.py")