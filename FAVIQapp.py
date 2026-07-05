import streamlit as st
import pandas as pd
import os
import re
import requests
import datetime
import json

# ตั้งค่าหน้า Streamlit
st.set_page_config(page_title="Faviq Space", layout="wide")

# ไฟล์ข้อมูล
DATA_FILE = "artist_schedules.csv"
CONFIG_FILE = "system_config.json"  
ADMIN_PASSWORD = "Nittaya_195"

# --- ฟังก์ชันระบบ ---
def load_system_config():
    default_config = {
        "video_shelves": [{"type": "Variety / TV", "title": "📺 รายการโทรทัศน์"}, {"type": "Online Video / YouTube", "title": "🔴 YouTube"}]
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return default_config
    return default_config

def extract_youtube_id(url):
    if not url or pd.isna(url): return None
    regex_list = [r"(?:v=|\/v\/|embed\/|shorts\/|youtu\.be\/|\/embed\/)([a-zA-Z0-9_-]{11})", r"(?:watch\?v=)([a-zA-Z0-9_-]{11})"]
    for regex in regex_list:
        match = re.search(regex, str(url))
        if match: return match.group(1)
    return None

def get_youtube_thumbnail(url):
    video_id = extract_youtube_id(url)
    return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg" if video_id else None

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        return df.to_dict('records')
    return []

# --- เริ่มแสดงผล ---
sys_config = load_system_config()
if "schedules" not in st.session_state: st.session_state.schedules = load_data()

st.markdown("""<style>
.yt-thumbnail-container { position: relative; width: 100%; padding-top: 56.25%; overflow: hidden; border-radius: 12px; background-color: #000; }
.yt-thumbnail-img { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; }
.yt-shelf-title { font-size: 18px; font-weight: bold; margin: 20px 0 15px 0; color: #f8fafc; }
.yt-video-card-link { text-decoration: none; color: inherit; }
</style>""", unsafe_allow_html=True)

view_mode = st.sidebar.radio("MENU", ["🏠 หน้าแรกแกลเลอรี", "⚙️ ระบบหลังบ้าน"])

if view_mode == "🏠 หน้าแรกแกลเลอรี":
    st.header("🎬 Artist Hub")
    all_vids = st.session_state.schedules
    df_vids = pd.DataFrame(all_vids).sort_values(by='date', ascending=False) if all_vids else pd.DataFrame()
    
    for shelf in sys_config.get("video_shelves", []):
        df_shelf = df_vids[df_vids['type'] == shelf['type']] if not df_vids.empty else pd.DataFrame()
        if df_shelf.empty: continue
        
        st.markdown(f'<div class="yt-shelf-title">{shelf["title"]}</div>', unsafe_allow_html=True)
        s_key = f"expand_{shelf['type']}"
        if s_key not in st.session_state: st.session_state[s_key] = False
        
        records = df_shelf.to_dict('records')
        display_vids = records if st.session_state[s_key] else records[:4]
        
        cols = st.columns(4)
        for i, v in enumerate(display_vids):
            with cols[i % 4]:
                thumb = get_youtube_thumbnail(v['link']) or ""
                st.markdown(f"""<a href="{v['link']}" target="_blank" class="yt-video-card-link">
                    <div class="yt-thumbnail-container"><img class="yt-thumbnail-img" src="{thumb}"></div>
                    <div style="margin-top:8px;">{v['title']}</div>
                </a>""", unsafe_allow_html=True)
        
        if len(records) > 4:
            if st.button("🔽 ดูเพิ่มเติม" if not st.session_state[s_key] else "🔼 ยุบ", key=f"btn_{s_key}"):
                st.session_state[s_key] = not st.session_state[s_key]
                st.rerun()

elif view_mode == "⚙️ ระบบหลังบ้าน":
    st.subheader("⚙️ ระบบหลังบ้าน")
    if st.text_input("รหัสผ่าน:", type="password") == ADMIN_PASSWORD:
        st.write("ยินดีต้อนรับสู่ระบบจัดการ")
    else:
        st.error("รหัสผ่านไม่ถูกต้อง")
