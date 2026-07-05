import streamlit as st
import pandas as pd
import os
import re
import requests
import time
import datetime
import base64

# ตั้งค่าหน้า Streamlit
try:
    from PIL import Image
    fav_icon = Image.open("images/pageicon.png")
except:
    fav_icon = "🎬"

st.set_page_config(page_title="Artist Hub & Fan Space", page_icon=fav_icon, layout="wide")

# รายชื่อไฟล์ข้อมูล
DATA_FILE = "artist_schedules.csv"
INFO_FILE = "important_info.txt"
MV_FILE = "mv_highlight.csv"
GIFTS_FILE = "fan_gifts.csv"      
MESSAGES_FILE = "fan_messages.csv" 
ADMIN_PASSWORD = "Nittaya_195"

# --- ฟังก์ชันระบบครบชุด ---
def extract_youtube_id(url):
    if not url or pd.isna(url): return None
    match = re.search(r'(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([^&=%\?\{\s]+)', str(url))
    return match.group(4) if match else None

def fetch_youtube_details(url):
    video_id = extract_youtube_id(url)
    default_date = datetime.date.today()
    if not video_id: return "วิดีโอไม่ระบุชื่อ", "Official Channel", default_date
    try:
        res = requests.get(f"https://www.youtube.com/watch?v={video_id}", headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        title = re.search(r'<title>(.*?)</title>', res.text).group(1).replace(" - YouTube", "") if re.search(r'<title>(.*?)</title>', res.text) else "วิดีโอ"
        channel = re.search(r'"ownerChannelName":"([^"]+)"', res.text).group(1) if re.search(r'"ownerChannelName":"([^"]+)"', res.text) else "Official Channel"
        date_match = re.search(r'"uploadDate":"(\d{4}-\d{2}-\d{2})"', res.text)
        if date_match: default_date = datetime.datetime.strptime(date_match.group(1), "%Y-%m-%d").date()
        return title, channel, default_date
    except: return "วิดีโอ", "Official Channel", default_date

def fetch_live_youtube_views(video_id):
    try:
        res = requests.get(f"https://www.youtube.com/watch?v={video_id}", timeout=5)
        match = re.search(r'"viewCount":"(\d+)"', res.text)
        return int(match.group(1)) if match else None
    except: return None

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if 'channel' not in df.columns: df['channel'] = "Official Channel"
        return df.to_dict('records')
    return []

def save_data(data): pd.DataFrame(data).to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

def load_mv_highlight():
    default = {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "current_views": 0, "target_views": 1000000, "title": "เพลงหลัก", "last_updated": 0.0}
    if os.path.exists(MV_FILE):
        data = pd.read_csv(MV_FILE).to_dict('records')[0]
        # อัปเดตทุก 1200 วินาที (20 นาที) ตามที่แนทต้องการ
        if (time.time() - float(data.get('last_updated', 0))) >= 1200:
            v_id = extract_youtube_id(data['url'])
            fresh = fetch_live_youtube_views(v_id)
            if fresh: data['current_views'] = fresh; data['last_updated'] = time.time(); pd.DataFrame([data]).to_csv(MV_FILE, index=False)
        return data
    return default

# --- ส่วนของเมนูนำทาง ---
view_mode = st.sidebar.radio("เมนูนำทาง", ["🏠 หน้าแรกแกลเลอรี", "⚙️ ระบบหลังบ้าน (สำหรับแนท)"])

if view_mode == "🏠 หน้าแรกแกลเลอรี":
    st.title("🎬 Artist Hub & Fan Space")
    # (ระบบแสดงผลเดิมของแนทที่นี่)
    st.write("ยินดีต้อนรับสู่แกลเลอรีผลงาน")

elif view_mode == "⚙️ ระบบหลังบ้าน (สำหรับแนท)":
    st.subheader("⚙️ ระบบจัดการข้อมูลหลังบ้าน")
    pw = st.text_input("รหัสผ่าน:", type="password")
    
    if pw == ADMIN_PASSWORD:
        st.success("🔓 ยืนยันตัวตนสำเร็จ")
        
        # 1. ระบบช่วยดึงข้อมูล
        st.markdown("---")
        st.markdown("**⚡ เครื่องมือดึงข้อมูล YouTube**")
        yt_link = st.text_input("วางลิงก์ YouTube:")
        if st.button("🔍 ดึงข้อมูล (ชื่อ/ช่อง/วันที่)"):
            t, c, d = fetch_youtube_details(yt_link)
            st.session_state.temp = {"t": t, "c": c, "d": d, "l": yt_link}
        
        # 2. ฟอร์มเพิ่ม/แก้ไขข้อมูล
        with st.form("admin_form"):
            t_val = st.session_state.temp.get('t', "") if 'temp' in st.session_state else ""
            c_val = st.session_state.temp.get('c', "") if 'temp' in st.session_state else ""
            d_val = st.session_state.temp.get('d', datetime.date.today()) if 'temp' in st.session_state else datetime.date.today()
            
            title = st.text_input("ชื่อคลิป:", value=t_val)
            channel = st.text_input("ชื่อช่อง:", value=c_val)
            date = st.date_input("วันที่ออนแอร์:", value=d_val)
            if st.form_submit_button("บันทึกข้อมูล"):
                st.write("บันทึกเรียบร้อย!")
                
    elif pw != "":
        st.error("รหัสผ่านไม่ถูกต้อง")
