"""
ELK Factory - Annotation Assistant (Scout Tool)
Streamlit UI for Human-in-the-Loop Data Collection.
Based on production-proven 'dgpc_annotation_local.py'.
"""

import streamlit as st
import os
import json
import pandas as pd
import google.generativeai as genai
from datetime import datetime
from glob import glob
from pydub import AudioSegment
import time

# --- CONFIGURATION INITIALE ---
st.set_page_config(
    page_title="ELK Scout Hub", 
    layout="wide", 
    page_icon="🛡️"
)

# --- WORKSTATION SLATE DESIGN (Preserved from v2) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Inter:wght@400;500;600;700&display=swap');
    :root {
        --slate-bg: #1a1c1e;
        --slate-card: #24272a;
        --slate-text: #e1e4e8;
        --accent-green: #28a745;
    }
    .stApp { background-color: var(--slate-bg); color: var(--slate-text); font-family: 'Inter', sans-serif; }
    .status-badge { font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; font-weight: 800; padding: 1px 8px; border: 1px solid currentColor; }
    .status-done { color: #50fa7b; }
    .status-todo { color: #ff5555; }
</style>
""", unsafe_allow_html=True)

# --- PATHS ---
DATA_DIR = "data"
AUDIO_RAW_DIR = "data/raw_audio"
AUDIO_PROC_DIR = "data/processed_audio"
ANNOTATIONS_FILE = os.path.join(DATA_DIR, "annotations.json")
CONFIG_FILE = "config.json"

for d in [DATA_DIR, AUDIO_RAW_DIR, AUDIO_PROC_DIR]: os.makedirs(d, exist_ok=True)

# --- UTILS ---
def load_data(p):
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as f: return json.load(f)
    return []

def save_all(data_list):
    with open(ANNOTATIONS_FILE, 'w', encoding='utf-8') as f: 
        json.dump(data_list, f, ensure_ascii=False, indent=2)

def process_audio(p):
    try:
        out = os.path.join(AUDIO_PROC_DIR, os.path.basename(p).split('.')[0] + ".wav")
        if not os.path.exists(out):
            AudioSegment.from_file(p).set_frame_rate(16000).set_channels(1).export(out, format="wav")
        return out
    except Exception as e:
        print(f"Audio error: {e}")
        return None

# --- APP LOGIC ---
annotations = load_data(ANNOTATIONS_FILE)
ann_map = { a.get('audio_file'): a for a in annotations }
raw_files = sorted(glob(f"{AUDIO_RAW_DIR}/*.wav") + glob(f"{AUDIO_RAW_DIR}/*.mp3") + glob(f"{AUDIO_RAW_DIR}/*.ogg"))

if not raw_files:
    st.warning(f"No audio files found in {AUDIO_RAW_DIR}. Please add calls to annotate.")
    st.stop()

if 'idx' not in st.session_state: st.session_state.idx = 0
cur_path = raw_files[st.session_state.idx]
cur_f = os.path.basename(cur_path)
is_done = cur_f in ann_map

# Sidebar
with st.sidebar:
    st.header("ELK SCOUT")
    st.text(f"Queue: {st.session_state.idx + 1}/{len(raw_files)}")
    if st.button("Next Call"): 
        st.session_state.idx = (st.session_state.idx + 1) % len(raw_files)
        st.rerun()

# Main UI
st.title(f"Handling: {cur_f}")
wav = process_audio(cur_path)
if wav:
    st.audio(wav)

# Transcription Area
default_text = ann_map[cur_f].get('transcription', "") if is_done else ""
transcription = st.text_area("Transcription Log", value=default_text, height=150)

# Attributes
c1, c2 = st.columns(2)
incident = c1.text_input("Incident Type", value=ann_map[cur_f].get('incident', "") if is_done else "")
location = c2.text_input("Location", value=ann_map[cur_f].get('location', "") if is_done else "")

if st.button("SAVE ANNOTATION", type="primary"):
    entry = {
        "audio_file": cur_f,
        "transcription": transcription,
        "incident": incident,
        "location": location,
        "timestamp": datetime.now().isoformat()
    }
    
    # Update or Append
    found = False
    for i, a in enumerate(annotations):
        if a['audio_file'] == cur_f:
            annotations[i] = entry
            found = True
            break
    if not found:
        annotations.append(entry)
        
    save_all(annotations)
    st.success("Saved!")
    time.sleep(1)
    st.session_state.idx = (st.session_state.idx + 1) % len(raw_files)
    st.rerun()
