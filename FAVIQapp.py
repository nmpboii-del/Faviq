import streamlit as st
import pandas as pd
import os
import re
import requests
import time
import datetime
import base64
import json

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
EVENT_SCHEDULE_FILE = "artist_event_schedule.csv"  

ADMIN_PASSWORD = "Nittaya_195"

# 🖼️ ใส่ URL ของรูปภาพขนาด 1500*1500 ที่ต้องการใช้เป็นรูปส่วนหัวเพจตรงนี้
# (สามารถเปลี่ยนเป็น Path ของไฟล์ในเครื่องได้ เช่น "images/header.png")
from PIL import Image
HEADER_IMAGE_URL = Image.open("images/headpage.jpg")

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

# --- ฟังก์ชันระบบจัดการตารางงานศิลปิน (เพิ่มระบบ Auto-Sort เรียงวันที่) ---
def load_event_schedules():
    if os.path.exists(EVENT_SCHEDULE_FILE):
        try:
            df = pd.read_csv(EVENT_SCHEDULE_FILE)
            df['date_parsed'] = pd.to_datetime(df['วันที่'], errors='coerce')
            df = df.sort_values(by='date_parsed', ascending=True)
            df = df.drop(columns=['date_parsed'])
            return df.to_dict('records')
        except:
            return []
    return []

def save_event_schedules(data):
    pd.DataFrame(data).to_csv(EVENT_SCHEDULE_FILE, index=False, encoding='utf-8-sig')

# ฟังก์ชันดึงเฉพาะ "เลขวัน" ออกมาจากฟอร์แมตวันที่มาตรฐาน YYYY-MM-DD
def extract_only_day_num(date_str):
    if not date_str or pd.isna(date_str):
        return "-"
    try:
        parts = str(date_str).split('-')
        if len(parts) == 3:
            return str(int(parts[2])) 
        return str(date_str)
    except:
        return str(date_str)

# ฟังก์ชันแปลง วันที่มาตรฐาน เป็นชื่อเดือนภาษาไทย + ปี พ.ศ. สำหรับทำหัวข้อจัดหมวดหมู่
def get_thai_month_year(date_str):
    if not date_str or pd.isna(date_str):
        return "ไม่ระบุเดือน"
    months_th = ["", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
    try:
        parts = str(date_str).split('-')
        if len(parts) == 3:
            year = int(parts[0]) + 543 # เปลี่ยนเป็น พ.ศ.
            month = int(parts[1])
            return f"{months_th[month]} {year}"
    except:
        pass
    return "ไม่ระบุเดือน"

# --- ฟังก์ชันระบบช่วยดึงข้อมูล ---
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
    
    try:
        embed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        res = requests.get(embed_url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            title = data.get("title", "วิดีโอ YouTube")
            channel = data.get("author_name", "Official Channel")
            return title, channel, default_date
    except: pass
    
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
        if 'description' not in df.columns: df['description'] = ""
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

# --- ตกแต่ง CSS หน้าเว็บสไตล์ YouTube (ปรับพฤติกรรม Past Event ให้ไม่มีเส้นขีดฆ่า) ---
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
    
    /* สไตล์การ์ดตารางงานปกติ */
    .schedule-item-box { display: flex; align-items: center; background-color: #0d1321; border-radius: 12px; padding: 15px; margin-bottom: 15px; border: 1px solid #1e293b; }
    .schedule-date-badge { flex-shrink: 0; width: 75px; height: 75px; background-color: #facc15; border-radius: 16px; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: 800; color: #000; box-shadow: 0 4px 10px rgba(250, 204, 21, 0.2); margin-right: 18px; text-align: center; line-height: 1; }
    .schedule-content-info { flex-grow: 1; color: #f1f5f9; }
    .schedule-title-text { font-size: 17px; font-weight: 700; color: #facc15; margin-bottom: 6px; }
    .schedule-meta-row { font-size: 14px; color: #cbd5e1; display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
    .schedule-meta-row-two-lines { font-size: 14px; color: #cbd5e1; margin-bottom: 4px; }
    .schedule-indent-text { padding-left: 20px; color: #f1f5f9; font-weight: 500; word-break: break-all; }
    .schedule-note-text { font-size: 12px; color: #94a3b8; font-style: italic; margin-top: 6px; }

    /* สไตล์การ์ดตารางงานที่ผ่านมาแล้ว (ทำแค่สีเทาหม่น ไม่ขีดฆ่า) */
    .schedule-item-box.past-event { background-color: #1a1f2c; opacity: 0.6; border: 1px solid #334155; }
    .schedule-date-badge.past-badge { background-color: #64748b; color: #e2e8f0; box-shadow: none; }
    .schedule-title-text.past-title { color: #94a3b8; text-decoration: none !important; }

    .gift-card { background-color: #0f172a; border: 1px solid #334155; border-radius: 14px; padding: 12px; text-align: center; margin-bottom: 15px; }
    .gift-img-container { width: 100%; height: 160px; overflow: hidden; border-radius: 10px; background-color: #020617; margin-bottom: 8px; }
    .gift-img { width: 100%; height: 100%; object-fit: cover; border-radius: 10px; }
    
    .download-btn { display: block; background-color: #ef4444; color: white !important; padding: 6px 10px; font-size: 12px; font-weight: bold; border-radius: 10px; text-decoration: none !important; text-align: center; margin-top: 5px; }
    .yt-shelf-title { font-size: 18px; font-weight: bold; color: #f8fafc; margin: 20px 0 15px 0; display: flex; align-items: center; gap: 8px; }
    .month-group-title { font-size: 16px; font-weight: bold; color: #38bdf8; background-color: #1e293b; padding: 6px 14px; border-radius: 8px; margin: 15px 0 10px 0; display: inline-block; }
    .letter-card { background-color: #1e293b; border-left: 4px solid #ef4444; border-radius: 8px; padding: 12px; margin-bottom: 10px; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 24px; border-bottom: 1px solid #2d3748; }
    .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: 600; padding-bottom: 8px; background-color: transparent !important; }
    
    /* ควบคุมขนาดและเอฟเฟกต์ของรูปภาพ Header */
    .header-banner-container { width: 100%; display: flex; justify-content: center; margin-bottom: 20px; border-radius: 16px; overflow: hidden; }
    </style>
    """,
    unsafe_allow_html=True
)

view_mode = st.sidebar.radio("MENU", ["🏠 HOME", "⚙️ SYSTEM"])

# ==========================================
# 🏠 หน้าแรกแกลเลอรี
# ==========================================
if view_mode == "🏠 HOME":
    # 🖼️ แสดงรูปภาพส่วนหัวเพจ (Header) ด้านบนสุดของหน้าแกลเลอรี
    st.image(HEADER_IMAGE_URL, use_container_width=True)
    
    st.markdown("<h2 style='color: #f8fafc; margin-top: 15px; margin-bottom: 5px;'>🎬 Artist Hub & Fan Space</h2>", unsafe_allow_html=True)
    
    gifts_list = load_gifts()
    all_vids = load_data()
    df_vids = pd.DataFrame(all_vids).sort_values(by='date', ascending=False) if all_vids else pd.DataFrame()
    
    important_text = load_important_info()
    st.markdown(f'<div class="billboard-box"><h4 style="margin-top:0; color:#ef4444; font-size:15px;">📢 ประกาศและข้อมูลสำคัญ</h4><p style="margin-bottom:0; font-size:13px; white-space: pre-wrap;">{important_text}</p></div>', unsafe_allow_html=True)
    
    mv_data = load_mv_highlight()
    st.markdown(f"### 🎵 PROJECT FOCUS: {mv_data['title']}")
    st.markdown('<div class="mv-dashboard-box">', unsafe_allow_html=True)
    col_mv_player, col_mv_milestone = st.columns([1.3, 1])
    with col_mv_player:
        yt_id = extract_youtube_id(mv_data['url'])
        if yt_id: st.video(f"https://www.youtube.com/watch?v={yt_id}")
        else: st.error("ลิงก์เพลงหลักไม่ถูกต้อง")
    with col_mv_milestone:
        st.markdown("<h4 style='color: #38bdf8; margin-top:0;'>📊 สถิติเป้าหมายปัจจุบัน </h4>", unsafe_allow_html=True)
        c_views, t_views = int(mv_data['current_views']), int(mv_data['target_views'])
        progress_ratio = min(float(c_views / t_views), 1.0) if t_views > 0 else 0.0
        
        col_metric1, col_metric2 = st.columns(2)
        col_metric1.metric(label="📈 ยอดวิวบน YouTube", value=f"{c_views:,} view")
        col_metric2.metric(label="🎯 เป้าหมาย", value=f"{t_views:,} view")
        
        st.markdown(f"**🔥 ความคืบหน้า: {progress_ratio*100:.2f}%**")
        st.progress(progress_ratio)
        if mv_data.get('last_updated', 0) > 0:
            thailand_time = float(mv_data['last_updated']) + 25200 
            update_str = datetime.datetime.fromtimestamp(thailand_time).strftime('%H:%M:%S')
            st.write(f"<span style='color:#64748b; font-size:12px;'>🔄 เวลาที่อัปเดตล่าสุด(อัปเดตทุก 10 นาที): {update_str} น.</span>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    defined_tabs = sys_config.get("tabs", [])
    valid_tabs = []
    if isinstance(defined_tabs, list):
        for t in defined_tabs:
            if isinstance(t, dict) and "title" in t:
                valid_tabs.append(t)

    if not valid_tabs:
        st.warning("ยังไม่ได้ตั้งค่าแท็บเมนูในระบบหลังบ้าน")
    else:
        tab_objects = st.tabs([t["title"] for t in valid_tabs])
        
        for index, tab_info in enumerate(valid_tabs):
            with tab_objects[index]:
                t_title_text = str(tab_info.get("title", "")).lower()
                t_type = str(tab_info.get("type", "")).strip()
                t_target = tab_info.get("target", "")
                
                if t_type == "digital_goods" or "digital" in t_title_text or "good" in t_title_text or "gift" in t_title_text:
                    st.markdown('<div class="yt-shelf-title">🎨 Digital Goods </div>', unsafe_allow_html=True)
                    if not gifts_list: 
                        st.info("ขณะนี้ยังไม่มีรูปภาพเปิดให้ดาวน์โหลด ")
                    else:
                        g_cols = st.columns(4)
                        for g_idx, g_item in enumerate(gifts_list):
                            with g_cols[g_idx % 4]:
                                img_src = g_item['img_url']
                                if img_src and not str(img_src).startswith("http"): img_src = f"data:image/png;base64,{img_src}"
                                desc_html = f'<div style="font-size:12px; color:#94a3b8; margin-bottom:8px; min-height:18px; display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical; overflow:hidden;">{g_item.get("description", "")}</div>' if g_item.get("description") else '<div style="margin-bottom:8px;"></div>'
                                st.markdown(f"""
                                <div class="gift-card">
                                    <div class="gift-img-container"><img class="gift-img" src="{img_src}"></div>
                                    <div style="font-size:14px; font-weight:600; color:#f8fafc; margin-bottom:5px;">{g_item["title"]}</div>
                                    {desc_html}
                                    <a class="download-btn" href="{g_item["download_url"]}" target="_blank">📥 โหลดรูปเต็ม</a>
                                </div>
                                """, unsafe_allow_html=True)

                elif t_type == "home_dashboard":
                    col_dashboard_left, col_dashboard_right = st.columns([1, 1])
                    
                    with col_dashboard_left:
                        st.markdown('<div class="yt-shelf-title">📌 ผลงานแนะนำ </div>', unsafe_allow_html=True)
                        pinned_vids = [v for v in all_vids if v.get('pinned', False)]
                        if pinned_vids:
                            for pv_idx, pv_item in enumerate(pinned_vids):
                                thumb = get_youtube_thumbnail(pv_item['link']) or "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=500"
                                click_url = pv_item['link'] if pv_item['link'] and not pd.isna(pv_item['link']) else "#"
                                note_html = f'<div style="font-size:14px; color:#f59e0b; font-style:italic; margin-top:5px;">💬 {pv_item["note"]}</div>' if ('note' in pv_item and pv_item['note'] and not pd.isna(pv_item['note'])) else ''
                                st.markdown(f"""
                                <a href="{click_url}" target="_blank" class="yt-video-card-link">
                                    <div class="yt-video-card" style="margin-bottom: 25px;">
                                        <div class="yt-thumbnail-container" style="padding-top: 56.25%;"><img class="yt-thumbnail-img" src="{thumb}"></div>
                                        <div class="yt-video-details" style="padding: 8px 4px;">
                                            <div class="yt-video-title" style="font-size: 18px; margin-bottom:6px;">📌 {pv_item["title"]}</div>
                                            <div class="yt-video-channel" style="font-size: 14px;">👤 {pv_item.get('channel', 'Official Channel')}</div>
                                            <div class="yt-video-meta" style="font-size: 13px;">📅 {pv_item["date"]}</div>
                                            {note_html}
                                        </div>
                                    </div>
                                </a>
                                """, unsafe_allow_html=True)
                        else:
                            st.info("ยังไม่มีคลิปปักหมุดในขณะนี้")
                            
                    with col_dashboard_right:
                        st.markdown('<div class="yt-shelf-title">📅 ตารางงาน FAVIQ (ที่กำลังจะถึง)</div>', unsafe_allow_html=True)
                        event_list = load_event_schedules()
                        today = datetime.date.today()
                        
                        upcoming_events = []
                        for ev in event_list:
                            try:
                                ev_date_obj = datetime.datetime.strptime(ev.get('วันที่', ''), "%Y-%m-%d").date()
                                if ev_date_obj >= today:
                                    upcoming_events.append(ev)
                            except:
                                upcoming_events.append(ev)
                                
                        if upcoming_events:
                            for ev in upcoming_events[:3]:
                                display_day = extract_only_day_num(ev.get('วันที่', '-'))
                                note_snippet = f'<div class="schedule-note-text">*{ev.get("หมายเหตุ", "")}</div>' if ev.get("หมายเหตุ") else ''
                                st.markdown(f"""
                                <div class="schedule-item-box">
                                    <div class="schedule-date-badge">{display_day}</div>
                                    <div class="schedule-content-info">
                                        <div class="schedule-title-text">{ev.get('รายการ', '-')}</div>
                                        <div class="schedule-meta-row">⏰ <b>Time:</b> {ev.get('เวลา', '-')}</div>
                                        <div class="schedule-meta-row-two-lines">
                                            📍 <b>Location/Channel:</b>
                                            <div class="schedule-indent-text">{ev.get('สถานที่/ช่อง', '-')}</div>
                                        </div>
                                        {note_snippet}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info("ไม่มีงานใหม่ที่กำลังจะถึงในระยะนี้")

                    st.markdown("---")

                    if gifts_list:
                        st.markdown('<div class="yt-shelf-title">🎨 Digital Goods </div>', unsafe_allow_html=True)
                        g_home_cols = st.columns(4)
                        for g_idx, g_item in enumerate(gifts_list[:4]):
                            with g_home_cols[g_idx % 4]:
                                img_src = g_item['img_url']
                                if img_src and not str(img_src).startswith("http"): img_src = f"data:image/png;base64,{img_src}"
                                desc_html = f'<div style="font-size:12px; color:#94a3b8; margin-bottom:8px; min-height:18px; display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical; overflow:hidden;">{g_item.get("description", "")}</div>' if g_item.get("description") else '<div style="margin-bottom:8px;"></div>'
                                st.markdown(f"""
                                <div class="gift-card">
                                    <div class="gift-img-container"><img class="gift-img" src="{img_src}"></div>
                                    <div style="font-size:14px; font-weight:600; color:#f8fafc; margin-bottom:5px;">{g_item["title"]}</div>
                                    {desc_html}
                                    <a class="download-btn" href="{g_item["download_url"]}" target="_blank">📥 โหลดรูปเต็ม</a>
                                </div>
                                """, unsafe_allow_html=True)
                                
                    homepage_shelves = sys_config.get("video_shelves", [])
                    for shelf in homepage_shelves:
                        df_shelf = df_vids[df_vids['type'] == shelf['type']] if not df_vids.empty else pd.DataFrame()
                        if not df_shelf.empty:
                            st.markdown(f'<div class="yt-shelf-title">{shelf["title"]}</div>', unsafe_allow_html=True)
                            shelf_records = df_shelf.to_dict('records')
                            
                            s_key = f"sh_home_{shelf['type'].replace(' ', '_').replace('/', '_')}"
                            if s_key not in st.session_state: st.session_state[s_key] = False
                            
                            display_vids = shelf_records if st.session_state[s_key] else shelf_records[:4]
                            
                            v_cols = st.columns(4)
                            for v_idx, v_item in enumerate(display_vids):
                                with v_cols[v_idx % 4]:
                                    thumb = get_youtube_thumbnail(v_item['link']) or "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=500"
                                    st.markdown(f"""
                                    <a href="{v_item['link']}" target="_blank" class="yt-video-card-link">
                                        <div class="yt-video-card">
                                            <div class="yt-thumbnail-container"><img class="yt-thumbnail-img" src="{thumb}"></div>
                                            <div class="yt-video-details">
                                                <div class="yt-video-title">{v_item["title"]}</div>
                                                <div class="yt-video-channel">👤 {v_item.get('channel', 'Official Channel')}</div>
                                                <div class="yt-video-meta">📅 {v_item["date"]}</div>
                                            </div>
                                        </div>
                                    </a>
                                    """, unsafe_allow_html=True)
                            
                            if len(shelf_records) > 4:
                                if st.button("🔽 ดูเพิ่มเติม" if not st.session_state[s_key] else "🔼 ยุบแถว", key=f"btn_home_{s_key}"):
                                    st.session_state[s_key] = not st.session_state[s_key]
                                    st.rerun()

                elif t_type == "all_videos":
                    video_shelves = sys_config.get("video_shelves", [])
                    has_any_video = False
                    
                    for shelf in video_shelves:
                        df_shelf = df_vids[df_vids['type'] == shelf['type']] if not df_vids.empty else pd.DataFrame()
                        
                        if not df_shelf.empty:
                            has_any_video = True
                            st.markdown(f'<div class="yt-shelf-title">{shelf["title"]}</div>', unsafe_allow_html=True)
                            shelf_records = df_shelf.to_dict('records')
                            s_key = f"sh_all_{shelf['type'].replace(' ', '_').replace('/', '_')}"
                            if s_key not in st.session_state: st.session_state[s_key] = False
                            display_vids = shelf_records if st.session_state[s_key] else shelf_records[:4]
                            
                            v_cols = st.columns(4)
                            for v_idx, v_item in enumerate(display_vids):
                                with v_cols[v_idx % 4]:
                                    thumb = get_youtube_thumbnail(v_item['link']) or "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=500"
                                    st.markdown(f"""
                                    <a href="{v_item['link']}" target="_blank" class="yt-video-card-link">
                                        <div class="yt-video-card">
                                            <div class="yt-thumbnail-container"><img class="yt-thumbnail-img" src="{thumb}"></div>
                                            <div class="yt-video-details">
                                                <div class="yt-video-title">{v_item["title"]}</div>
                                                <div class="yt-video-channel">👤 {v_item.get('channel', 'Official Channel')}</div>
                                                <div class="yt-video-meta">📅 {v_item["date"]}</div>
                                            </div>
                                        </div>
                                    </a>
                                    """, unsafe_allow_html=True)
                            if len(shelf_records) > 4:
                                if st.button("🔽 ดูเพิ่มเติม" if not st.session_state[s_key] else "🔼 ยุบแถว", key=f"btn_{s_key}"):
                                    st.session_state[s_key] = not st.session_state[s_key]
                                    st.rerun()
                                    
                    if not has_any_video:
                        st.info("ขณะนี้ยังไม่มีข้อมูลวิดีโอในระบบ")

                elif t_type == "single_shelf_only":
                    st.markdown(f'<div class="yt-shelf-title">📂 : {t_target}</div>', unsafe_allow_html=True)
                    df_shelf = df_vids[df_vids['type'] == t_target] if not df_vids.empty else pd.DataFrame()
                    if df_shelf.empty:
                        st.caption("ยังไม่มีข้อมูลวิดีโอในหมวดหมู่นี้")
                    else:
                        v_cols = st.columns(4)
                        for v_idx, v_item in enumerate(df_shelf.to_dict('records')):
                            with v_cols[v_idx % 4]:
                                thumb = get_youtube_thumbnail(v_item['link']) or "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=500"
                                st.markdown(f"""
                                <a href="{v_item['link']}" target="_blank" class="yt-video-card-link">
                                    <div class="yt-video-card">
                                        <div class="yt-thumbnail-container"><img class="yt-thumbnail-img" src="{thumb}"></div>
                                        <div class="yt-video-details">
                                            <div class="yt-video-title">{v_item["title"]}</div>
                                            <div class="yt-video-channel">👤 {v_item.get('channel', 'Official Channel')}</div>
                                            <div class="yt-video-meta">📅 {v_item["date"]}</div>
                                        </div>
                                    </div>
                                </a>
                                """, unsafe_allow_html=True)

                elif t_type == "artist_events_all":
                    st.markdown('<div class="yt-shelf-title">🗓️ ตารางงานทั้งหมด </div>', unsafe_allow_html=True)
                    event_list = load_event_schedules()
                    today = datetime.date.today()
                    
                    if not event_list:
                        st.info("ขณะนี้ไม่มีข้อมูลตารางงานในระบบ")
                    else:
                        events_by_month = {}
                        for ev in event_list:
                            month_key = get_thai_month_year(ev.get('วันที่', ''))
                            if month_key not in events_by_month:
                                events_by_month[month_key] = []
                            events_by_month[month_key].append(ev)
                        
                        for month_name, items in events_by_month.items():
                            st.markdown(f'<div class="month-group-title">📅 ประจำเดือน: {month_name}</div>', unsafe_allow_html=True)
                            
                            for ev in items:
                                display_day = extract_only_day_num(ev.get('วันที่', '-'))
                                note_snippet = f'<div class="schedule-note-text">*{ev.get("หมายเหตุ", "")}</div>' if ev.get("หมายเหตุ") else ''
                                
                                is_past = False
                                try:
                                    ev_date_obj = datetime.datetime.strptime(ev.get('วันที่', ''), "%Y-%m-%d").date()
                                    if ev_date_obj < today:
                                        is_past = True
                                except:
                                    pass
                                
                                box_class = "schedule-item-box past-event" if is_past else "schedule-item-box"
                                badge_style = "background-color: #64748b; color:#fff; box-shadow: none;" if is_past else "background-color: #3b82f6; color:#fff; box-shadow: 0 4px 10px rgba(59, 130, 246, 0.2);"
                                title_style = "color: #94a3b8; font-size: 19px;" if is_past else "color: #60a5fa; font-size: 19px;"
                                
                                st.markdown(f"""
                                <div class="{box_class}">
                                    <div class="schedule-date-badge" style="{badge_style}">{display_day}</div>
                                    <div class="schedule-content-info">
                                        <div class="schedule-title-text" style="{title_style}">{ev.get('รายการ', '-')}</div>
                                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 10px; margin-top: 8px;">
                                            <div class="schedule-meta-row" style="font-size: 14px;">⏰ <b>เวลา:</b> {ev.get('เวลา', '-')}</div>
                                            <div class="schedule-meta-row-two-lines" style="font-size: 14px;">📍 <b>สถานที่ / ช่องรับชม:</b> {ev.get('สถานที่/ช่อง', '-')}</div>
                                        </div>
                                        {note_snippet}
                                    </div>
                                 </div>
                                """, unsafe_allow_html=True)

                elif t_type == "fan_letters":
                    with st.form(key=f"fan_msg_form_{index}", clear_on_submit=True):
                        fan_name = st.text_input("ชื่อเล่นของคุณ:")
                        fan_msg = st.text_area("ข้อความที่คุณอยากฝากถึงแอดมิน:")
                        submit_letter = st.form_submit_button("✉️ ส่งจดหมายลับ")
                    if submit_letter and fan_msg.strip():
                        save_message(fan_name.strip() if fan_name.strip() else "แฟนคลับผู้ไม่ประสงค์ออกนาม", fan_msg.strip())
                        st.success("💖 ส่งจดหมายสำเร็จแล้ว!")

# ==========================================
# ⚙️ SYSTEM
# ==========================================
elif view_mode == "⚙️ SYSTEM":
    st.subheader("⚙️ SYSTEM")
    password_input = st.text_input("กรุณาป้อนรหัสผ่านผู้ดูแลระบบ:", type="password")
    
    if password_input == ADMIN_PASSWORD:
        st.success("🔓 ยืนยันตัวตนสำเร็จ!")
        st.markdown("---")
        
        if "edit_index" not in st.session_state: st.session_state.edit_index = None
        if "edit_gift_index" not in st.session_state: st.session_state.edit_gift_index = None
        if "edit_event_index" not in st.session_state: st.session_state.edit_event_index = None

        with st.expander("🛠️ จัดการโครงสร้างแท็บเมนูด้านบน "):
            st.markdown("### 📋 รายการแท็บปัจจุบันที่มีอยู่บนหน้าหลัก")
            updated_tabs = []
            for t_idx, t_item in enumerate(sys_config.get("tabs", [])):
                if not isinstance(t_item, dict) or "title" not in t_item: continue
                col_t1, col_t2, col_t3, col_t4 = st.columns([1.5, 1.5, 1.5, 0.5])
                t_title = col_t1.text_input(f"ชื่อป้ายแท็บที่ {t_idx+1}", value=t_item["title"], key=f"tab_title_in_{t_idx}")
                col_t2.caption(f"ประเภทเนื้อหา: `{t_item.get('type', '')}`")
                if t_item.get('target'): col_t3.caption(f"เป้าหมายดึงข้อมูล: `{t_item['target']}`")
                else: col_t3.caption("-")
                
                if col_t4.button("🗑️", key=f"del_tab_btn_{t_idx}"):
                    if len(sys_config.get("tabs", [])) <= 1:
                        st.error("ต้องเหลือไว้อย่างน้อย 1 แท็บครับ")
                    else:
                        sys_config["tabs"].pop(t_idx)
                        save_system_config(sys_config)
                        st.success("ลบแท็บเมนูเรียบร้อย!")
                        st.rerun()
                
                updated_tabs.append({
                    "id": t_item.get("id", f"tab_{t_idx}"),
                    "title": t_title,
                    "type": t_item.get("type", "all_videos"),
                    "target": t_item.get("target", "")
                })
            
            if st.button("💾 บันทึกการแก้ไขชื่อแท็บ", key="save_existing_tabs_name"):
                sys_config["tabs"] = updated_tabs
                save_system_config(sys_config)
                st.success("อัปเดตชื่อแท็บสำเร็จ!")
                st.rerun()

            st.markdown("---")
            st.markdown("### ➕ เพิ่มแท็บเมนูใหม่เข้าสู่หน้าหลัก")
            with st.form(key="create_new_tab_form"):
                new_tab_title = st.text_input("ระบุชื่อแท็บใหม่ที่ต้องการให้แสดง:")
                new_tab_content_type = st.selectbox(
                    "ระบุประเภทข้อมูลที่จะนำมาแสดงในแท็บนี้:",
                    [
                        ("home_dashboard", "แดชบอร์ดหน้าแรก (มีประกาศ เพลงโฟกัส คลังภาพแนะนำ และวิดีโอแนะนำ)"),
                        ("artist_events_all", "🗓️ ตารางงานศิลปินทั้งหมด"),
                        ("all_videos", "หน้าคลังรวมวิดีโอทุกหมวดหมู่"),
                        ("single_shelf_only", "ดึงเฉพาะวิดีโอหมวดหมู่ใดหมวดหมู่หนึ่งมาโชว์"),
                        ("digital_goods", "โหลดรูปภาพ Digital Goods"),
                        ("fan_letters", "กล่องข้อความ / ส่งจดหมาย")
                    ],
                    format_func=lambda x: x[1]
                )
                shelf_options = [s["type"] for s in sys_config.get("video_shelves", [])]
                chosen_shelf_target = st.selectbox("กรณีเลือก 'ดึงเฉพาะวิดีโอหมวดหมู่เดียว' ให้ระบุหมวดหมู่เป้าหมายตรงนี้:", shelf_options if shelf_options else ["-"])
                add_tab_submit = st.form_submit_button("🚀 ยืนยันเพิ่มแท็บเข้าสู่หน้าหลัก")
                
                if add_tab_submit and new_tab_title.strip():
                    unique_id = f"tab_{int(time.time())}"
                    actual_type = new_tab_content_type[0] if isinstance(new_tab_content_type, tuple) else new_tab_content_type
                    target_val = chosen_shelf_target if actual_type == "single_shelf_only" else ""
                    if "tabs" not in sys_config or not isinstance(sys_config["tabs"], list): sys_config["tabs"] = []
                    sys_config["tabs"].append({"id": unique_id, "title": new_tab_title.strip(), "type": actual_type, "target": target_val})
                    save_system_config(sys_config)
                    st.success(f"เพิ่มแท็บ '{new_tab_title}' สำเร็จแล้ว!")
                    st.rerun()

            st.markdown("---")
            st.markdown("### 📂 จัดการหมวดหมู่ประ/เภทวิดีโอ (Video Shelves)")
            with st.form(key="add_shelf_form_new"):
                new_type_id = st.text_input("รหัสหมวดหมู่ (ภาษาอังกฤษ ห้ามซ้ำ เช่น Vlog):")
                new_type_title = st.text_input("ชื่อป้ายหมวดหมู่แสดงผลบนเว็บ (เช่น 📸 วล็อก):")
                add_shelf_submit = st.form_submit_button("➕ บันทึกหมวดหมู่")
                if add_shelf_submit and new_type_id.strip() and new_type_title.strip():
                    if not any(s['type'] == new_type_id.strip() for s in sys_config["video_shelves"]):
                        sys_config["video_shelves"].append({"type": new_type_id.strip(), "title": new_type_title.strip()})
                        save_system_config(sys_config)
                        st.success("เพิ่มหมวดหมู่เรียบร้อย!")
                        st.rerun()

            for s_idx, s_item in enumerate(list(sys_config["video_shelves"])):
                col_s1, col_s2, col_s3 = st.columns([1.5, 2, 0.5])
                col_s1.text(f"ID: {s_item['type']}")
                updated_title = col_s2.text_input(f"ชื่อป้ายหมวดหมู่ของ {s_item['type']}", value=s_item['title'], key=f"shelf_title_edit_{s_idx}")
                sys_config["video_shelves"][s_idx]["title"] = updated_title
                if col_s3.button("🗑️", key=f"del_shelf_btn_{s_idx}"):
                    sys_config["video_shelves"].pop(s_idx)
                    save_system_config(sys_config)
                    st.success("ลบหมวดหมู่สำเร็จ!")
                    st.rerun()

        with st.expander("🎯 1. ตั้งค่า PROJECT FOCUS"):
            curr_mv = load_mv_highlight()
            with st.form(key="mv_form_exp"):
                mv_title_in = st.text_input("ชื่อเพลง:", value=curr_mv['title'])
                mv_url_in = st.text_input("ลิงก์ YouTube MV:", value=curr_mv['url'])
                mv_target_in = st.number_input("เป้าหมายยอดวิว:", value=int(curr_mv['target_views']), step=10000)
                mv_current_in = st.number_input("ยอดวิวปัจจุบัน:", value=int(curr_mv['current_views']))
                mv_submit = st.form_submit_button("💾 บันทึก")
            if mv_submit:
                save_mv_highlight(mv_url_in, mv_current_in, mv_target_in, mv_title_in)
                st.success("บันทึกเพลงหลักแล้ว!"); st.rerun()

        with st.expander("📢 2. แก้ไขข้อมูลกระดานประกาศสำคัญหน้าแรก"):
            current_info = load_important_info()
            new_info_text = st.text_area("ข้อความประกาศ:", value=current_info, height=100)
            if st.button("💾 บันทึกประกาศ"):
                save_important_info(new_info_text)
                st.success("อัปเดตประกาศสำเร็จ!"); st.rerun()

        with st.expander("🎨 3. จัดการ Digital goods "):
            gifts_data = load_gifts()
            col_g1, col_g2 = st.columns([1, 1.2])
            with col_g1:
                if st.session_state.edit_gift_index is not None:
                    curr_gift = gifts_data[st.session_state.edit_gift_index]
                    default_g_title, default_g_down = curr_gift['title'], curr_gift['download_url']
                    default_g_desc = curr_gift.get('description', '')
                    default_g_pin = bool(curr_gift.get('pinned', False))
                    gift_btn_txt = "🔄 อัปเดตข้อมูล Digital goods"
                else:
                    default_g_title, default_g_down, default_g_desc, default_g_pin = "", "", "", False
                    gift_btn_txt = "🚀 อัปโหลดขึ้นหน้าแรก"
                with st.form(key="add_gift_exp_v8"):
                    g_title = st.text_input("ชื่อ Goods:", value=default_g_title)
                    g_desc = st.text_area("รายละเอียด / คำอธิบาย:", value=default_g_desc, help="รายละเอียดสั้นๆ เกี่ยวกับไฟล์นี้")
                    uploaded_img_file = st.file_uploader("เลือกรูปภาพตัวอย่าง:", type=["png", "jpg", "jpeg"])
                    g_down_url = st.text_input("ลิงก์ดาวน์โหลดรูป:", value=default_g_down)
                    g_is_pinned = st.checkbox("📌 ปักหมุดในโซนแนะนำ", value=default_g_pin)
                    gift_submit = st.form_submit_button(gift_btn_txt)
                if gift_submit and g_title and g_down_url:
                    base64_img = None
                    if uploaded_img_file: base64_img = base64.b64encode(uploaded_img_file.getvalue()).decode()
                    if st.session_state.edit_gift_index is not None:
                        gifts_data[st.session_state.edit_gift_index] = {
                            "title": g_title, 
                            "description": g_desc,
                            "download_url": g_down_url, 
                            "pinned": g_is_pinned, 
                            "img_url": base64_img if base64_img else gifts_data[st.session_state.edit_gift_index]['img_url']
                        }
                        st.session_state.edit_gift_index = None
                    else:
                        if uploaded_img_file: 
                            gifts_data.append({
                                "title": g_title, 
                                "description": g_desc,
                                "img_url": base64_img, 
                                "download_url": g_down_url, 
                                "pinned": g_is_pinned
                            })
                    save_gifts(gifts_data); st.rerun()
            with col_g2:
                for g_i, g_item in enumerate(gifts_data):
                    g_c1, g_c2, g_c3, g_c4 = st.columns([2, 0.9, 0.6, 0.5])
                    g_c1.write(f"{g_i + 1}. {g_item['title']}")
                    if g_c3.button("📝", key=f"edit_g_{g_i}"): st.session_state.edit_gift_index = g_i; st.rerun()
                    if g_c4.button("🗑️", key=f"del_g_{g_i}"): gifts_data.pop(g_i); save_gifts(gifts_data); st.rerun()

        with st.expander("🗓️ จัดการตารางงานศิลปิน "):
            current_events_list = load_event_schedules()
            
            if st.session_state.edit_event_index is not None:
                st.markdown("### 📝 แก้ไขรายการตารางงาน")
                ev_curr = current_events_list[st.session_state.edit_event_index]
                try:
                    default_ev_date = datetime.datetime.strptime(str(ev_curr.get("วันที่", "")), "%Y-%m-%d").date()
                except:
                    default_ev_date = datetime.date.today()
                default_ev_title = ev_curr.get("รายการ", "")
                default_ev_time = ev_curr.get("เวลา", "")
                default_ev_location = ev_curr.get("สถานที่/ช่อง", "")
                default_ev_note = ev_curr.get("หมายเหตุ", "")
                event_btn_txt = "🔄 อัปเดตตารางงาน"
            else:
                st.markdown("### ➕ เพิ่มรายการตารางงานใหม่")
                default_ev_date = datetime.date.today()
                default_ev_title, default_ev_time, default_ev_location, default_ev_note = "", "", "", ""
                event_btn_txt = "💾 บันทึกตารางงาน"
                
            with st.form(key="add_event_schedule_form", clear_on_submit=False):
                ev_date = st.date_input("เลือกวันที่จัดงาน:", value=default_ev_date)
                ev_title = st.text_input("รายการ / ชื่องาน:", value=default_ev_title)
                ev_time = st.text_input("เวลา (เช่น 21:45 น. หรือ 15.30):", value=default_ev_time)
                ev_location = st.text_input("สถานที่ / ช่องทางการรับชม:", value=default_ev_location)
                ev_note = st.text_input("หมายเหตุเล็กๆ:", value=default_ev_note)
                submit_event = st.form_submit_button(event_btn_txt)
                
                if submit_event and ev_title.strip():
                    item_event_data = {
                        "วันที่": str(ev_date), 
                        "รายการ": clean_html_tags(ev_title),
                        "เวลา": clean_html_tags(ev_time),
                        "สถานที่/ช่อง": clean_html_tags(ev_location),
                        "หมายเหตุ": clean_html_tags(ev_note)
                    }
                    if st.session_state.edit_event_index is not None:
                        current_events_list[st.session_state.edit_event_index] = item_event_data
                        st.session_state.edit_event_index = None
                        st.success("อัปเดตตารางงานสำเร็จแล้ว!")
                    else:
                        current_events_list.append(item_event_data)
                        st.success("เพิ่มข้อมูลลงตารางงานสำเร็จแล้ว!")
                        
                    save_event_schedules(current_events_list)
                    st.rerun()
                    
            if st.session_state.edit_event_index is not None:
                if st.button("❌ ยกเลิกการแก้ไข"):
                    st.session_state.edit_event_index = None
                    st.rerun()
            
            st.markdown("---")
            st.markdown("### 📋 ตารางงานทั้งหมดที่มีในระบบ")
            if not current_events_list:
                st.info("ขณะนี้ยังไม่มีรายการตารางงาน")
            else:
                for ev_idx, ev_item in enumerate(current_events_list):
                    col_ev_info, col_ev_actions = st.columns([3.5, 1.5])
                    with col_ev_info:
                        display_day = extract_only_day_num(ev_item.get('วันที่', '-'))
                        m_group = get_thai_month_year(ev_item.get('วันที่', ''))
                        st.write(f"**[{display_day}] {ev_item.get('รายการ', '-')}** \n<br><span style='color:#facc15; font-size:12px;'>📁 กลุ่มเดือน: {m_group} | 📅 วันที่: {ev_item.get('วันที่', '-')} | ⏰ เวลา: {ev_item.get('เวลา', '-')}</span>", unsafe_allow_html=True)
                    with col_ev_actions:
                        act_c1, act_c2 = st.columns(2)
                        if act_c1.button("📝 แก้ไข", key=f"edit_ev_btn_{ev_idx}"):
                            st.session_state.edit_event_index = ev_idx
                            st.rerun()
                        if act_c2.button("🗑️ ลบงาน", key=f"del_ev_btn_{ev_idx}"):
                            current_events_list.pop(ev_idx)
                            save_event_schedules(current_events_list)
                            st.success("ลบรายการสำเร็จ!")
                            st.rerun()

        with st.expander("🎬 4. จัดการวิดีโอทั้วไป"):
            st.markdown("**⚡ เครื่องมือช่วยดึงข้อมูลด่วนจากลิงก์ YouTube**")
            yt_fetch_link = st.text_input("วางลิงก์ YouTube ดึงข้อมูลอัตโนมัติ:", key="yt_fetch_link_input_v2")
            if st.button("🔍 ดึงชื่อคลิป ชื่อช่อง และวันที่ออนแอร์", key="btn_fetch_yt_v2"):
                if yt_fetch_link.strip():
                    with st.spinner("กำลังแกะข้อมูลจากหลังบ้าน YouTube..."):
                        fetched_title, fetched_channel, fetched_date = fetch_youtube_details(yt_fetch_link)
                        st.session_state["fetched_title_val_v2"] = fetched_title
                        st.session_state["fetched_channel_val_v2"] = fetched_channel
                        st.session_state["fetched_date_val_v2"] = fetched_date
                        st.session_state["fetched_link_val_v2"] = yt_fetch_link
                        st.success("ดึงข้อมูลสำเร็จ! ข้อมูลถูกนำไปใช้ในช่องกรอกด้านล่างแล้ว")
                        st.rerun()

            st.markdown("---")
            available_options = [s["type"] for s in sys_config.get("video_shelves", [])]
            if not available_options: available_options = ["Variety / TV"]

            col_v_form, col_v_manage = st.columns([1, 1.2])
            with col_v_form:
                if st.session_state.edit_index is not None:
                    curr = st.session_state.schedules[st.session_state.edit_index]
                    d_title = curr["title"]
                    d_channel = curr.get("channel", "Official Channel")
                    d_link = curr["link"]
                    d_note = curr["note"]
                    d_pinned = bool(curr.get('pinned', False))
                    try: d_date = datetime.datetime.strptime(curr["date"], "%Y-%m-%d").date()
                    except: d_date = datetime.date.today()
                    d_type_idx = available_options.index(curr["type"]) if curr["type"] in available_options else 0
                    btn_txt = "🔄 อัปเดตวิดีโอ"
                else:
                    d_title = st.session_state.get("fetched_title_val_v2", "")
                    d_channel = st.session_state.get("fetched_channel_val_v2", "")
                    d_date = st.session_state.get("fetched_date_val_v2", datetime.date.today())
                    d_link = st.session_state.get("fetched_link_val_v2", "")
                    d_note, d_pinned, d_type_idx = "", False, 0
                    btn_txt = "🚀 อัปโหลดเข้าคลัง"
                
                with st.form(key='admin_vid_form_v13'):
                    title = st.text_input("ชื่อคลิป:", value=d_title)
                    channel = st.text_input("ชื่อช่องต้นทาง:", value=d_channel)
                    date_val = st.date_input("วันที่ออนแอร์:", value=d_date)
                    w_type = st.selectbox("ประเภท:", available_options, index=d_type_idx)
                    link = st.text_input("ลิงก์คลิป:", value=d_link)
                    note = st.text_area("โน้ตย่อ:", value=d_note)
                    is_pinned = st.checkbox("📌 ปักหมุดคลิปนี้ในโซนวิดีโอแนะนำหน้าแรก", value=d_pinned)
                    vid_submit = st.form_submit_button(btn_txt)
                
                if vid_submit and title.strip():
                    item_data = {
                        "title": clean_html_tags(title), 
                        "channel": clean_html_tags(channel) if channel.strip() else "Official Channel", 
                        "date": str(date_val), 
                        "type": w_type, 
                        "link": link, 
                        "note": clean_html_tags(note), 
                        "pinned": is_pinned
                    }
                    if st.session_state.edit_index is not None:
                        st.session_state.schedules[st.session_state.edit_index] = item_data
                        st.session_state.edit_index = None
                    else: 
                        st.session_state.schedules.append(item_data)
                    
                    for k in ["fetched_title_val_v2", "fetched_channel_val_v2", "fetched_date_val_v2", "fetched_link_val_v2"]:
                        if k in st.session_state: del st.session_state[k]
                        
                    save_data(st.session_state.schedules)
                    st.success("บันทึกข้อมูลสำเร็จ!")
                    st.rerun()

            with col_v_manage:
                st.markdown("**📋 รายการวิดีโอปัจจุบัน**")
                for idx, item in enumerate(st.session_state.schedules):
                    v_c1, v_c2, v_c3, v_c4 = st.columns([2, 0.9, 0.6, 0.5])
                    v_c1.write(f"{idx+1}. {item['title']} \n<br><span style='color:#ef4444; font-size:11px;'>👤 ช่อง: {item.get('channel', 'Official Channel')} | 📂 หมวด: {item['type']}</span>", unsafe_allow_html=True)
                    if v_c2.button("📌 หมุดอยู่" if item.get('pinned', False) else "◽ ทั่วไป", key=f"quick_pin_v_{idx}"): 
                        item['pinned'] = not item.get('pinned', False)
                        save_data(st.session_state.schedules)
                        st.rerun()
                    if v_c3.button("📝", key=f"edit_v_{idx}"): 
                        st.session_state.edit_index = idx
                        for k in ["fetched_title_val_v2", "fetched_channel_val_v2", "fetched_date_val_v2", "fetched_link_val_v2"]:
                            if k in st.session_state: del st.session_state[k]
                        st.rerun()
                    if v_c4.button("🗑️", key=f"del_v_{idx}"): 
                        st.session_state.schedules.pop(idx)
                        save_data(st.session_state.schedules)
                        st.rerun()

        with st.expander("📬 5. เปิดกล่องอ่านจดหมาย (Fan Letters)"):
            messages_list = load_messages()
            if not messages_list: st.info("กล่องจดหมายว่างอยู่")
            else:
                messages_list.reverse()
                for m_idx, m_item in enumerate(messages_list):
                    st.markdown(f'<div class="letter-card"><span style="font-size:11px; color:#94a3b8;">📅 {m_item["timestamp"]}</span><br><span style="font-weight:bold; color:#38bdf8;">👤 คุณ: {m_item["name"]}</span><br><p style="margin-top:4px; color:#e2e8f0; font-size:14px;">💬 {m_item["message"]}</p></div>', unsafe_allow_html=True)
                if st.button("🗑️ ล้างกล่องจดหมายทั้งหมด"):
                    if os.path.exists(MESSAGES_FILE): os.remove(MESSAGES_FILE)
                    st.success("ล้างตู้จดหมายเรียบร้อย!"); st.rerun()
                        
    elif password_input != "": st.error("รหัสผ่านไม่ถูกต้อง")
