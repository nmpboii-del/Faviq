import streamlit as st
import pandas as pd
import os
import re
import requests
import time
import datetime
import base64
import json  # ใช้สำหรับเก็บค่าคอนฟิกหัวข้อและแท็บแบบ Dynamic

# ตั้งค่าหน้า Streamlit
try:
    from PIL import Image
    fav_icon = Image.open("images/pageicon.png")
except:
    fav_icon = "🎬"

st.set_page_config(
    page_title="Faviq Space",
    page_icon=fav_icon,
    layout="wide"
)

# รายชื่อไฟล์ข้อมูล
DATA_FILE = "artist_schedules.csv"
INFO_FILE = "important_info.txt"
MV_FILE = "mv_highlight.csv"
GIFTS_FILE = "fan_gifts.csv"      
MESSAGES_FILE = "fan_messages.csv" 
CONFIG_FILE = "system_config.json"  

ADMIN_PASSWORD = "Nittaya_195"

# --- ฟังก์ชันจัดการโครงสร้างหัวข้อ/หมวดหมู่ระบบ ---
def load_system_config():
    default_config = {
        "tabs": [
            {"id": "home", "title": "หน้าแรก", "type": "home_dashboard", "target": ""},
            {"id": "tab_all_vids", "title": "วิดีโอทั้งหมด", "type": "all_videos", "target": ""},
            {"id": "tab_gifts", "title": "🎨 Digital Goods", "type": "digital_goods", "target": ""},
            {"id": "tab_letters", "title": "💌 ส่งข้อความ", "type": "fan_letters", "target": ""}
        ],
        "video_shelves": [
            {"type": "Variety / TV", "title": "📺 รายการโทรทัศน์ / Variety & TV Shows"},
            {"type": "Online Video / YouTube", "title": "🔴 คลิปออนไลน์ / YouTube & Social Media Content"},
            {"type": "Event / Concert", "title": "🎤 งานอีเวนต์และคอนเสิร์ต / Live Events & Concerts"},
            {"type": "Radio / Podcast", "title": "📻 รายการวิทยุและพอดแคสต์ / Radio & Podcasts"}
        ]
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default_config
    return default_config

def save_system_config(config_data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, ensure_ascii=False, indent=4)

sys_config = load_system_config()

# --- ฟังก์ชันระบบช่วยดึงข้อมูล (ปรับปรุงใหม่ รองรับขีดกลาง - แบบในรูปภาพ image_28a921.png) ---
def extract_youtube_id(url):
    if not url or pd.isna(url): return None
    regex_list = [
        r"(?:v=|\/v\/|embed\/|shorts\/|youtu\.be\/|\/embed\/)([a-zA-Z0-9_-]{11})",
        r"(?:watch\?v=)([a-zA-Z0-9_-]{11})"
    ]
    for regex in regex_list:
        match = re.search(regex, str(url))
        if match:
            return match.group(1)
    return None

def get_youtube_thumbnail(url):
    video_id = extract_youtube_id(url)
    return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg" if video_id else None

def fetch_youtube_details(url):
    video_id = extract_youtube_id(url)
    default_date = datetime.date.today()
    title = "วิดีโอ YouTube"
    channel = "Official Channel"
    if not video_id: return title, channel, default_date
    
    # วิธีที่ 1: ดึงผ่าน oEmbed (ปลอดภัยและเร็วที่สุด)
    try:
        embed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        res = requests.get(embed_url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            title = data.get("title", "วิดีโอ YouTube")
            channel = data.get("author_name", "Official Channel")
            return title, channel, default_date
    except: pass
    
    # วิธีที่ 2: ดึงตรงจากหน้าเว็บ (Fallback สำรอง)
    try:
        watch_url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept-Language": "th-TH,th;q=0.9"}
        res = requests.get(watch_url, headers=headers, timeout=5)
        if res.status_code == 200:
            title_match = re.search(r'<title>(.*?)</title>', res.text)
            if title_match: title = title_match.group(1).replace(" - YouTube", "").strip()
            
            channel_match = re.search(r'"ownerChannelName":"([^"]+)"', res.text) or re.search(r'"author":"([^"]+)"', res.text)
            if channel_match: channel = channel_match.group(1).strip()
            
            date_match = re.search(r'"publishDate":"([^"]+)"', res.text) or re.search(r'"uploadDate":"([^"]+)"', res.text) or re.search(r'<meta itemprop="datePublished" content="([^"]+)"', res.text)
            if date_match:
                parsed_date = date_match.group(1)[:10]
                default_date = datetime.datetime.strptime(parsed_date, "%Y-%m-%d").date()
    except: pass
    
    return title, channel, default_date

def fetch_live_youtube_views(video_id):
    if not video_id: return None
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            match = re.search(r'"viewCount":"(\d+)"', response.text)
            return int(match.group(1)) if match else None
    except: pass
    return None

def clean_html_tags(text):
    if not text or pd.isna(text): return ""
    cleaned = str(text)
    cleaned = re.sub(r'</?div[^>]*>', '', cleaned)
    cleaned = re.sub(r'</?a[^>]*>', '', cleaned)   
    cleaned = re.sub(r'</?span[^>]*>', '', cleaned) 
    return cleaned.strip()

def load_mv_highlight():
    default_data = {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "current_views": 100000, "target_views": 1000000, "title": "เพลงหลักของศิลปิน", "last_updated": 0.0}
    if os.path.exists(MV_FILE):
        try:
            df = pd.read_csv(MV_FILE)
            data = df.to_dict('records')[0]
            current_time = time.time()
            if (current_time - float(data.get('last_updated', 0.0))) >= 600:
                v_id = extract_youtube_id(data['url'])
                fresh = fetch_live_youtube_views(v_id) if v_id else None
                if fresh:
                    data['current_views'] = fresh
                    data['last_updated'] = current_time
                    pd.DataFrame([data]).to_csv(MV_FILE, index=False, encoding='utf-8-sig')
            return data
        except: return default_data
    return default_data

def save_mv_highlight(url, current_views, target_views, title):
    pd.DataFrame([{"url": url, "current_views": int(current_views), "target_views": int(target_views), "title": title, "last_updated": time.time()}]).to_csv(MV_FILE, index=False, encoding='utf-8-sig')

def load_gifts():
    if os.path.exists(GIFTS_FILE):
        df = pd.read_csv(GIFTS_FILE)
        if 'pinned' not in df.columns: df['pinned'] = False
        else: df['pinned'] = df['pinned'].astype(bool)
        return df.to_dict('records')
    return []

def save_gifts(data): pd.DataFrame(data).to_csv(GIFTS_FILE, index=False, encoding='utf-8-sig')

def load_messages(): return pd.read_csv(MESSAGES_FILE).to_dict('records') if os.path.exists(MESSAGES_FILE) else []

def save_message(name, message):
    new_msg = {"timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), "name": name, "message": message}
    messages = load_messages()
    messages.append(new_msg)
    pd.DataFrame(messages).to_csv(MESSAGES_FILE, index=False, encoding='utf-8-sig')

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            if df.empty: return []
            df['date'] = df['date'].astype(str)
            if 'pinned' not in df.columns: df['pinned'] = False
            else: df['pinned'] = df['pinned'].astype(bool)
            if 'channel' not in df.columns: df['channel'] = "Official Channel"
            records = df.to_dict('records')
            for r in records:
                r['title'] = clean_html_tags(r.get('title', ''))
                r['note'] = clean_html_tags(r.get('note', ''))
                if pd.isna(r.get('channel')) or r.get('channel') == "":
                    r['channel'] = "Official Channel"
            return records
        except: return []
    return []

def save_data(data): pd.DataFrame(data).to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

def load_important_info():
    if os.path.exists(INFO_FILE):
        with open(INFO_FILE, "r", encoding="utf-8") as f: return f.read()
    return "Faviq"

def save_important_info(text):
    with open(INFO_FILE, "w", encoding="utf-8") as f: f.write(text)

if "schedules" not in st.session_state: st.session_state.schedules = load_data()

# --- ตกแต่ง CSS หน้าเว็บสไตล์ YouTube ---
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .billboard-box { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); border-left: 6px solid #ef4444; padding: 20px; border-radius: 14px; color: #f1f5f9; margin-bottom: 25px; border: 1px solid #1e293b; }
    .mv-dashboard-box { background-color: #0b0f19; border: 1px solid #38bdf8; border-radius: 18px; padding: 20px; margin-bottom: 30px; }
    
    .yt-video-card-link { text-decoration: none !important; color: inherit !important; display: block; margin-bottom: 20px; }
    .yt-video-card { background-color: transparent; transition: transform 0.2s ease; }
    .yt-video-card:hover { transform: scale(1.02); }
    .yt-thumbnail-container { position: relative; width: 100%; padding-top: 56.25%; overflow: hidden; border-radius: 12px; background-color: #000; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
    .yt-thumbnail-img { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; }
    .yt-video-details { margin-top: 10px; padding: 0 2px; }
    .yt-video-title { font-size: 14px; font-weight: 600; color: #f8fafc; line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; margin-bottom: 4px; }
    .yt-video-channel { font-size: 12px; color: #ef4444; font-weight: 500; margin-bottom: 2px; }
    .yt-video-meta { font-size: 12px; color: #94a3b8; }
    
    .gift-card { background-color: #0f172a; border: 1px solid #334155; border-radius: 14px; padding: 12px; text-align: center; margin-bottom: 15px; }
    .gift-img-container { width: 100%; height: 160px; overflow: hidden; border-radius: 10px; background-color: #020617; margin-bottom: 8px; }
    .gift-img { width: 100%; height: 100%; object-fit: cover; border-radius: 10px; }
    
    .download-btn { display: block; background-color: #ef4444; color: white !important; padding: 6px 10px; font-size: 12px; font-weight: bold; border-radius: 10px; text-decoration: none !important; text-align: center; margin-top: 5px; }
    .yt-shelf-title { font-size: 18px; font-weight: bold; color: #f8fafc; margin: 20px 0 15px 0; display: flex; align-items: center; gap: 8px; }
    .yt-play-all { font-size: 14px; color: #94a3b8; font-weight: normal; cursor: pointer; text-decoration: none; }
    .letter-card { background-color: #1e293b; border
