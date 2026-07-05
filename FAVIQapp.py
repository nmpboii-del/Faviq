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
LIVE_SCHEDULE_FILE = "artist_live_schedules.csv"  # ไฟล์เก็บตารางงานจริงของศิลปิน

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

# --- ฟังก์ชันระบบจัดการตารางงานศิลปิน (Live Schedule) ---
def load_live_schedules():
    if os.path.exists(LIVE_SCHEDULE_FILE):
        try:
            df = pd.read_csv(LIVE_SCHEDULE_FILE)
            df['date'] = df['date'].astype(str)
            df = df.sort_values(by='date', ascending=True)
            return df.to_dict('records')
        except: return []
    return []

def save_live_schedules(data):
    pd.DataFrame(data).to_csv(LIVE_SCHEDULE_FILE, index=False, encoding='utf-8-sig')

# --- ฟังก์ชันระบบช่วยดึงข้อมูลวิดีโอ ---
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
    cleaned = re.sub(r'</?(div|a|span)[^>]*>', '', cleaned, flags=re.IGNORECASE)   
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

# --- ตกแต่ง CSS หน้าเว็บสไตล์ YouTube & คัสตอมตารางงาน ---
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
    
    /* สไตล์ตารางงานคล้ายแผ่นภาพโปสเตอร์ */
    .schedule-container { background: linear-gradient(180deg, #111827 0%, #030712 100%); border-radius: 16px; padding: 18px; border: 1px solid #374151; max-height: 650px; overflow-y: auto; }
    .schedule-item { display: flex; align-items: flex-start; gap: 15px; padding: 12px 0; border-bottom: 1px solid #1f2937; }
    .schedule-item:last-child { border-bottom: none; }
    .schedule-date-box { background: #facc15; color: #000; font-size: 24px; font-weight: 800; min-width: 55px; height: 55px; display: flex; align-items: center; justify-content: center; border-radius: 10px; box-shadow: 0 4px 10px rgba(250, 204, 21, 0.2); }
    .schedule-info { flex-grow: 1; }
    .schedule-title { font-size: 15px; font-weight: 700; color: #facc15; margin-bottom: 2px; text-transform: uppercase; }
    .schedule-meta-text { font-size: 12px; color: #e5e7eb; margin-bottom: 1px; display: flex; align-items: center; gap: 4px; }
    .schedule-note { font-size: 11px; color: #9ca3af; font-style: italic; margin-top: 3px; }
    
    .gift-card { background-color: #0f172a; border: 1px solid #334155; border-radius: 14px; padding: 12px; text-align: center; margin-bottom: 15px; }
    .gift-img-container { width: 100%; height: 160px; overflow: hidden; border-radius: 10px; background-color: #020617; margin-bottom: 8px; }
    .gift-img { width: 100%; height: 100%; object-fit: cover; border-radius: 10px; }
    
    .download-btn { display: block; background-color: #ef4444; color: white !important; padding: 6px 10px; font-size: 12px; font-weight: bold; border-radius: 10px; text-decoration: none !important; text-align: center; margin-top: 5px; }
    .yt-shelf-title { font-size: 18px; font-weight: bold; color: #f8fafc; margin: 20px 0 15px 0; display: flex; align-items: center; gap: 8px; }
    .letter-card { background-color: #1e293b; border-left: 4px solid #ef4444; border-radius: 8px; padding: 12px; margin-bottom: 10px; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 24px; border-bottom: 1px solid #2d3748; }
    .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: 600; padding-bottom: 8px; background-color: transparent !important; }
    </style>
    """,
    unsafe_allow_html=True
)

view_mode = st.sidebar.radio("MENU", ["🏠 หน้าแรกแกลเลอรี", "⚙️ ระบบหลังบ้าน"])

# ==========================================
# 🏠 หน้าแรกแกลเลอรี
# ==========================================
if view_mode == "🏠 หน้าแรกแกลเลอรี":
    st.markdown("<h2 style='color: #f8fafc; margin-bottom: 5px;'>🎬 Artist Hub & Fan Space</h2>", unsafe_allow_html=True)
    
    gifts_list = load_gifts()
    all_vids = load_data()
    df_vids = pd.DataFrame(all_vids).sort_values(by='date', ascending=False) if all_vids else pd.DataFrame()
    live_schedules_list = load_live_schedules()
    
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
                    st.markdown('<div class="yt-shelf-title">🎨 คลังดาวน์โหลดรูปภาพ Digital Goods ทั้งหมด</div>', unsafe_allow_html=True)
                    if not gifts_list: 
                        st.info("ขณะนี้ยังไม่มีรูปภาพเปิดให้ดาวน์โหลด สามารถเพิ่มรูปภาพได้จากระบบหลังบ้านครับ")
                    else:
                        g_cols = st.columns(4)
                        for g_idx, g_item in enumerate(gifts_list):
                            with g_cols[g_idx % 4]:
                                img_src = g_item['img_url']
                                if img_src and not str(img_src).startswith("http"): img_src = f"data:image/png;base64,{img_src}"
                                st.markdown(f"""
                                <div class="gift-card">
                                    <div class="gift-img-container"><img class="gift-img" src="{img_src}"></div>
                                    <div style="font-size:14px; font-weight:600; color:#f8fafc; margin-bottom:5px;">{g_item["title"]}</div>
                                    <a class="download-btn" href="{g_item["download_url"]}" target="_blank">📥 โหลดรูปเต็ม</a>
                                </div>
                                """, unsafe_allow_html=True)

                elif t_type == "home_dashboard":
                    col_left_side, col_right_side = st.columns([1, 1])
                    
                    with col_left_side:
                        pinned_vids = [v for v in all_vids if v.get('pinned', False)]
                        st.markdown('<div class="yt-shelf-title">📌 ผลงานแนะนำยอดนิยม</div>', unsafe_allow_html=True)
                        if pinned_vids:
                            pv_cols = st.columns(2)
                            for pv_idx, pv_item in enumerate(pinned_vids[:4]):
                                with pv_cols[pv_idx % 2]:
                                    thumb = get_youtube_thumbnail(pv_item['link']) or "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=500"
                                    click_url = pv_item['link'] if pv_item['link'] and not pd.isna(pv_item['link']) else "#"
                                    note_html = f'<div style="font-size:12px; color:#f59e0b; font-style:italic; margin-top:2px;">💬 {pv_item["note"]}</div>' if ('note' in pv_item and pv_item['note'] and not pd.isna(pv_item['note'])) else ''
                                    st.markdown(f"""
                                    <a href="{click_url}" target="_blank" class="yt-video-card-link">
                                        <div class="yt-video-card">
                                            <div class="yt-thumbnail-container"><img class="yt-thumbnail-img" src="{thumb}"></div>
                                            <div class="yt-video-details">
                                                <div class="yt-video-title">📌 {pv_item["title"]}</div>
                                                <div class="yt-video-channel">👤 {pv_item.get('channel', 'Official Channel')}</div>
                                                <div class="yt-video-meta">📅 {pv_item["date"]}</div>
                                                {note_html}
                                            </div>
                                        </div>
                                    </a>
                                    """, unsafe_allow_html=True)
                        else:
                            st.caption("ยังไม่มีผลงานปักหมุดแนะนำ")
                            
                    with col_right_side:
                        st.markdown('<div class="yt-shelf-title">📅 ตารางงานศิลปิน (Schedule)</div>', unsafe_allow_html=True)
                        if live_schedules_list:
                            html_content = '<div class="schedule-container">'
                            for s_item in live_schedules_list:
                                try:
                                    day_num = datetime.datetime.strptime(s_item['date'], "%Y-%m-%d").strftime("%d")
                                AntiExcept:
                                    day_num = "🗓️"
                                note_txt = f'<div class="schedule-note">* {s_item["note"]}</div>' if s_item.get('note') else ''
                                html_content += f"""
                                <div class="schedule-item">
                                    <div class="schedule-date-box">{day_num}</div>
                                    <div class="schedule-info">
                                        <div class="schedule-title">{s_item['title']}</div>
                                        <div class="schedule-meta-text">⏰ <b>Time:</b> {s_item['time']}</div>
                                        <div class="schedule-meta-text">📍 <b>Location/Channel:</b> {s_item['location']}</div>
                                        {note_txt}
                                    </div>
                                </div>
                                """
                            html_content += '</div>'
                            st.markdown(html_content, unsafe_allow_html=True)
                        else:
                            st.info("ขณะนี้ยังไม่มีคิวงานที่กำหนดไว้")
                    
                    st.markdown("---")
                    
                    if gifts_list:
                        st.markdown('<div class="yt-shelf-title">🎨 ล่าสุดจาก Digital Goods โหลดฟรี!</div>', unsafe_allow_html=True)
                        g_home_cols = st.columns(4)
                        for g_idx, g_item in enumerate(gifts_list[:4]):
                            with g_home_cols[g_idx % 4]:
                                img_src = g_item['img_url']
                                if img_src and not str(img_src).startswith("http"): img_src = f"data:image/png;base64,{img_src}"
                                st.markdown(f"""
                                <div class="gift-card">
                                    <div class="gift-img-container"><img class="gift-img" src="{img_src}"></div>
                                    <div style="font-size:14px; font-weight:600; color:#f8fafc; margin-bottom:5px;">{g_item["title"]}</div>
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
                    st.markdown(f'<div class="yt-shelf-title">📂 หมวดหมู่: {t_target}</div>', unsafe_allow_html=True)
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

                elif t_type == "fan_letters":
                    with st.form(key=f"fan_msg_form_{index}", clear_on_submit=True):
                        fan_name = st.text_input("ชื่อเล่นของคุณ:")
                        fan_msg = st.text_area("ข้อความที่คุณอยากฝากถึงแอดมิน:")
                        submit_letter = st.form_submit_button("✉️ ส่งจดหมายลับ")
                    if submit_letter and fan_msg.strip():
                        save_message(fan_name.strip() if fan_name.strip() else "แฟนคลับผู้ไม่ประสงค์ออกนาม", fan_msg.strip())
                        st.success("💖 ส่งจดหมายสำเร็จแล้ว!")

# ==========================================
# ⚙️ ระบบหลังบ้านจัดการข้อมูล
# ==========================================
elif view_mode == "⚙️ ระบบหลังบ้าน":
    st.subheader("⚙️ ระบบจัดการข้อมูลหลังบ้าน")
    password_input = st.text_input("กรุณาป้อนรหัสผ่านผู้ดูแลระบบ:", type="password")
    
    if password_input == ADMIN_PASSWORD:
        st.success("🔓 ยืนยันตัวตนสำเร็จ!")
        st.markdown("---")
        
        if "edit_index" not in st.session_state: st.session_state.edit_index = None
        if "edit_gift_index" not in st.session_state: st.session_state.edit_gift_index = None
        if "edit_live_schedule_index" not in st.session_state: st.session_state.edit_live_schedule_index = None

        with st.expander("🛠️ จัดการโครงสร้างแท็บเมนูด้านบน และเพิ่ม/ลดแท็บอิสระ"):
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
            
            if st.button("💾 บันทึกการแก้ไขชื่อแท็บ"):
                sys_config["tabs"] = updated_tabs
                save_system_config(sys_config)
                st.success("บันทึกโครงสร้างแท็บเรียบร้อยแล้ว!")
                st.rerun()
                
            st.markdown("---")
            st.markdown("#### ➕ เพิ่มแท็บเมนูใหม่แบบกำหนดเอง")
            new_t_title = st.text_input("ชื่อแท็บใหม่ (เช่น 🔴 Live Stream):")
            new_t_type = st.selectbox("ประเภทของเนื้อหาที่จะแสดงในแท็บนี้:", [
                ("all_videos", "แสดงวิดีโอทุกหมวดหมู่แยกตาม Shelf"),
                ("digital_goods", "แสดงรูปภาพคลังดาวน์โหลด Digital Goods"),
                ("fan_letters", "แสดงฟอร์มส่งจดหมายจากแฟนคลับ"),
                ("single_shelf_only", "คัดกรองเฉพาะวิดีโอ 1 หมวดหมู่เจาะจง")
            ], format_func=lambda x: x[1])
            
            new_t_target = ""
            if new_t_type[0] == "single_shelf_only":
                all_shelves = [s["type"] for s in sys_config.get("video_shelves", [])]
                new_t_target = st.selectbox("เลือกหมวดหมู่วิดีโอที่จะนำมาดึงข้อมูล:", all_shelves)
                
            if st.button("➕ เพิ่มแท็บระบบ"):
                if not new_t_title.strip():
                    st.error("กรุณากรอกชื่อแท็บ")
                else:
                    new_tab_obj = {
                        "id": f"custom_tab_{int(time.time())}",
                        "title": new_t_title.strip(),
                        "type": new_t_type[0],
                        "target": new_t_target
                    }
                    sys_config["tabs"].append(new_tab_obj)
                    save_system_config(sys_config)
                    st.success(f"เพิ่มแท็บ '{new_t_title}' สำเร็จแล้ว!")
                    st.rerun()

        with st.expander("📢 1. จัดการข้อความประกาศ (Important Billboard)"):
            current_info = load_important_info()
            info_input = st.text_area("แก้ไขข้อความประกาศสำคัญหน้าแรก:", value=current_info, height=120)
            if st.button("💾 บันทึกประกาศ"):
                save_important_info(info_input)
                st.success("อัปเดตประกาศสำเร็จ!")
                st.rerun()

        with st.expander("🎵 2. ตั้งค่าวิดีโอโปรเจกต์หลัก (Project Focus MV)"):
            mv_data = load_mv_highlight()
            mv_url = st.text_input("ลิงก์ YouTube MV เพลงหลัก:", value=mv_data['url'])
            mv_title = st.text_input("ชื่อเพลง/โปรเจกต์:", value=mv_data['title'])
            mv_target = st.number_input("เป้าหมายยอดวิว (วิว):", value=int(mv_data['target_views']), step=10000)
            mv_current = st.number_input("ยอดวิวเริ่มต้นตอนนี้ (วิว):", value=int(mv_data['current_views']), step=1000)
            
            if st.button("💾 บันทึกโปรเจกต์ MV"):
                save_mv_highlight(mv_url, mv_current, mv_target, mv_title)
                st.success("บันทึกข้อมูลโปรเจกต์หลักเรียบร้อย!")
                st.rerun()

        with st.expander("📅 3. จัดการตารางงานศิลปิน (Artist Schedule)"):
            st.markdown("### ➕ เพิ่ม / แก้ไข ตารางงาน")
            live_schedules = load_live_schedules()
            
            edit_s_idx = st.session_state.edit_live_schedule_index
            if edit_s_idx is not None and edit_s_idx < len(live_schedules):
                st.info(f"กำลังแก้ไขรายการตารางงานที่ {edit_s_idx + 1}")
                s_item = live_schedules[edit_s_idx]
                try: s_date_val = datetime.datetime.strptime(s_item['date'], "%Y-%m-%d").date()
                except: s_date_val = datetime.date.today()
                s_title_val = s_item['title']
                s_time_val = s_item['time']
                s_loc_val = s_item['location']
                s_note_val = s_item.get('note', '')
            else:
                s_date_val = datetime.date.today()
                s_title_val = ""
                s_time_val = "18:00"
                s_loc_val = "YouTube Live"
                s_note_val = ""

            s_date = st.date_input("วันที่จัดงาน:", value=s_date_val)
            s_title = st.text_input("ชื่องาน/รายการคอนเสิร์ต:", value=s_title_val)
            s_time = st.text_input("เวลา (เช่น 19:00 - 21:00 น.):", value=s_time_val)
            s_loc = st.text_input("ช่องทาง/สถานที่จัดงาน:", value=s_loc_val)
            s_note = st.text_input("หมายเหตุเพิ่มเติม (ถ้ามี):", value=s_note_val)

            c_s1, c_s2 = st.columns(2)
            if edit_s_idx is not None:
                if c_s1.button("💾 ยืนยันการอัปเดตตารางงาน"):
                    live_schedules[edit_s_idx] = {
                        "date": str(s_date), "title": s_title.strip(), "time": s_time.strip(),
                        "location": s_loc.strip(), "note": s_note.strip()
                    }
                    save_live_schedules(live_schedules)
                    st.session_state.edit_live_schedule_index = None
                    st.success("อัปเดตตารางงานสำเร็จ!")
                    st.rerun()
                if c_s2.button("❌ ยกเลิกการแก้ไข"):
                    st.session_state.edit_live_schedule_index = None
                    st.rerun()
            else:
                if st.button("➕ เพิ่มลงตารางงานศิลปิน"):
                    if not s_title.strip(): st.error("กรุณาระบุชื่องาน")
                    else:
                        new_schedule = {
                            "date": str(s_date), "title": s_title.strip(), "time": s_time.strip(),
                            "location": s_loc.strip(), "note": s_note.strip()
                        }
                        live_schedules.append(new_schedule)
                        save_live_schedules(live_schedules)
                        st.success("เพิ่มตารางงานเรียบร้อยแล้ว!")
                        st.rerun()

            st.markdown("---")
            st.markdown("### 📋 รายการตารางงานปัจจุบัน")
            if not live_schedules: st.info("ไม่มีรายการคิวงาน")
            else:
                for idx, item in enumerate(live_schedules):
                    col_i1, col_i2, col_i3, col_i4 = st.columns([1, 2, 2, 1])
                    col_i1.write(f"📅 {item['date']}")
                    col_i2.write(f"🎤 **{item['title']}** ({item['time']})")
                    col_i3.write(f"📍 {item['location']}")
                    
                    if col_i4.button("✏️", key=f"edit_ls_{idx}"):
                        st.session_state.edit_live_schedule_index = idx
                        st.rerun()
                    if col_i4.button("🗑️", key=f"del_ls_{idx}"):
                        live_schedules.pop(idx)
                        save_live_schedules(live_schedules)
                        st.rerun()

        with st.expander("🎬 4. อัปโหลดและจัดการคลังวิดีโอ (Video Bank)"):
            st.markdown("### ➕ เพิ่ม / แก้ไข ข้อมูลวิดีโอ")
            shelf_options = [s["type"] for s in sys_config.get("video_shelves", [])]
            
            edit_idx = st.session_state.edit_index
            if edit_idx is not None and edit_idx < len(st.session_state.schedules):
                st.info(f"กำลังแก้ไขวิดีโอรายการที่ {edit_idx + 1}")
                v_item = st.session_state.schedules[edit_idx]
                v_link_default = v_item['link']
                v_title_default = v_item['title']
                v_channel_default = v_item.get('channel', 'Official Channel')
                try: v_date_default = datetime.datetime.strptime(v_item['date'], "%Y-%m-%d").date()
                except: v_date_default = datetime.date.today()
                v_type_default = v_item['type'] if v_item['type'] in shelf_options else shelf_options[0]
                v_pinned_default = bool(v_item.get('pinned', False))
                v_note_default = v_item.get('note', '')
            else:
                v_link_default = ""
                v_title_default = ""
                v_channel_default = "Official Channel"
                v_date_default = datetime.date.today()
                v_type_default = shelf_options[0]
                v_pinned_default = False
                v_note_default = ""

            v_link = st.text_input("ลิงก์ YouTube วิดีโอ:", value=v_link_default, key="input_v_link")
            
            if st.button("🔍 ดึงข้อมูลอัตโนมัติจาก YouTube"):
                if v_link.strip():
                    f_title, f_channel, f_date = fetch_youtube_details(v_link.strip())
                    st.session_state.fetched_title_val = f_title
                    st.session_state.fetched_channel_val = f_channel
                    st.session_state.fetched_date_val = f_date
                    st.success("ดึงข้อมูลสำเร็จ! ระบบใส่ข้อมูลลงฟอร์มให้เรียบร้อย")

            v_title = st.text_input("ชื่อวิดีโอ (Title):", value=st.session_state.get("fetched_title_val", v_title_default))
            v_channel = st.text_input("ชื่อช่องผู้สร้าง (Channel):", value=st.session_state.get("fetched_channel_val", v_channel_default))
            v_date = st.date_input("วันที่เผยแพร่ (Publish Date):", value=st.session_state.get("fetched_date_val", v_date_default))
            v_type = st.selectbox("หมวดหมู่การจัดวาง (Shelf Type):", shelf_options, index=shelf_options.index(v_type_default))
            v_pinned = st.checkbox("📌 ปักหมุดวิดีโอนี้เป็นผลงานแนะนำหน้าหลัก", value=v_pinned_default)
            v_note = st.text_input("ข้อความสั้นแนบแถมพิเศษ (Note):", value=v_note_default)

            v_b1, v_b2 = st.columns(2)
            if edit_idx is not None:
                if v_b1.button("💾 บันทึกการอัปเดตข้อมูลวิดีโอ"):
                    st.session_state.schedules[edit_idx] = {
                        "date": str(v_date), "title": clean_html_tags(v_title),
                        "link": v_link.strip(), "type": v_type, "pinned": v_pinned,
                        "channel": v_channel.strip(), "note": clean_html_tags(v_note)
                    }
                    save_data(st.session_state.schedules)
                    st.session_state.edit_index = None
                    for k in ["fetched_title_val", "fetched_channel_val", "fetched_date_val"]:
                        if k in st.session_state: del st.session_state[k]
                    st.success("อัปเดตข้อมูลวิดีโอสำเร็จ!")
                    st.rerun()
                if v_b2.button("❌ ยกเลิกการแก้คลังวิดีโอ"):
                    st.session_state.edit_index = None
                    for k in ["fetched_title_val", "fetched_channel_val", "fetched_date_val"]:
                        if k in st.session_state: del st.session_state[k]
                    st.rerun()
            else:
                if st.button("➕ เพิ่มวิดีโอลงในระบบ"):
                    if not v_title.strip() or not v_link.strip(): st.error("กรุณากรอกข้อมูลให้ครบถ้วน")
                    else:
                        new_video = {
                            "date": str(v_date), "title": clean_html_tags(v_title),
                            "link": v_link.strip(), "type": v_type, "pinned": v_pinned,
                            "channel": v_channel.strip(), "note": clean_html_tags(v_note)
                        }
                        st.session_state.schedules.append(new_video)
                        save_data(st.session_state.schedules)
                        for k in ["fetched_title_val", "fetched_channel_val", "fetched_date_val"]:
                            if k in st.session_state: del st.session_state[k]
                        st.success("เพิ่มข้อมูลวิดีโอใหม่เรียบร้อย!")
                        st.rerun()

            st.markdown("---")
            st.markdown("### 📋 รายการวิดีโอทั้งหมดที่มีอยู่")
            if not st.session_state.schedules: st.info("ไม่มีข้อมูลวิดีโอ")
            else:
                for idx, v_item in enumerate(st.session_state.schedules):
                    v_c1, v_c2, v_c3, v_c4 = st.columns([1, 3, 1, 1])
                    v_c1.write(f"📅 {v_item['date']}")
                    v_c2.write(f"🎥 **{v_item['title']}** | ช่อง: `{v_item.get('channel','-')}`")
                    v_c3.caption(f"หมวดหมู่: `{v_item['type']}` " + ("📌" if v_item.get('pinned') else ""))
                    
                    if v_c4.button("✏️", key=f"edit_v_{idx}"): 
                        st.session_state.edit_index = idx
                        st.rerun()
                    if v_c4.button("🗑️", key=f"del_v_{idx}"): 
                        st.session_state.schedules.pop(idx)
                        save_data(st.session_state.schedules)
                        st.rerun()

        with st.expander("📬 5. เปิดกล่องอ่านจดหมายลับจากแฟนคลับ (Fan Letters)"):
            messages_list = load_messages()
            if not messages_list: st.info("กล่องจดหมายว่างอยู่")
            else:
                messages_list.reverse()
                for m_idx, m_item in enumerate(messages_list):
                    st.markdown(f'<div class="letter-card"><span style="font-size:11px; color:#94a3b8;">📅 {m_item["timestamp"]}</span><br><span style="font-weight:bold; color:#38bdf8;">👤 คุณ: {m_item["name"]}</span><br><p style="margin-top:4px; color:#e2e8f0; font-size:14px;">💬 {m_item["message"]}</p></div>', unsafe_allow_html=True)
