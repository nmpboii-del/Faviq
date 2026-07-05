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

st.set_page_config(
    page_title="Artist Hub & Fan Space",
    page_icon=fav_icon,
    layout="wide"
)

# รายชื่อไฟล์ข้อมูล
DATA_FILE = "artist_schedules.csv"
INFO_FILE = "important_info.txt"
MV_FILE = "mv_highlight.csv"
GIFTS_FILE = "fan_gifts.csv"      
MESSAGES_FILE = "fan_messages.csv" 

ADMIN_PASSWORD = "Nittaya_195"

# --- ฟังก์ชันระบบช่วยดึงข้อมูล ---
def extract_youtube_id(url):
    if not url or pd.isna(url): return None
    youtube_regex = r'(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([^&=%\?\{\s]+)'
    match = re.search(youtube_regex, str(url))
    return match.group(4) if match else None

def get_youtube_thumbnail(url):
    video_id = extract_youtube_id(url)
    return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg" if video_id else None

def fetch_live_youtube_views(video_id):
    if not video_id: return None
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            match = re.search(r'"viewCount":"(\d+)"', response.text)
            return int(match.group(1)) if match else None
    except: pass
    return None

def load_mv_highlight():
    default_data = {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "current_views": 100000, "target_views": 1000000, "title": "เพลงหลักของศิลปิน", "last_updated": 0.0}
    if os.path.exists(MV_FILE):
        try:
            df = pd.read_csv(MV_FILE)
            data = df.to_dict('records')[0]
            current_time = time.time()
            if (current_time - float(data.get('last_updated', 0.0))) >= 3600:
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
        df = pd.read_csv(DATA_FILE)
        df['date'] = df['date'].astype(str)
        if 'pinned' not in df.columns: df['pinned'] = False
        else: df['pinned'] = df['pinned'].astype(bool)
        return df.to_dict('records')
    return []

def save_data(data): pd.DataFrame(data).to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

def load_important_info():
    if os.path.exists(INFO_FILE):
        with open(INFO_FILE, "r", encoding="utf-8") as f: return f.read()
    return "💡 ยินดีต้อนรับสู่คลังวิดีโอศิลปิน!"

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
    
    /* สไตล์ YouTube Video Card Container */
    .yt-video-card-link {
        text-decoration: none !important;
        color: inherit !important;
        display: block;
        margin-bottom: 20px;
    }
    .yt-video-card {
        background-color: transparent;
        transition: transform 0.2s ease;
    }
    .yt-video-card:hover {
        transform: scale(1.02);
    }
    .yt-thumbnail-container {
        position: relative;
        width: 100%;
        padding-top: 56.25%; /* 16:9 Aspect Ratio */
        overflow: hidden;
        border-radius: 12px;
        background-color: #000;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    }
    .yt-thumbnail-img {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .yt-video-details {
        margin-top: 10px;
        padding: 0 2px;
    }
    .yt-video-title {
        font-size: 14px;
        font-weight: 600;
        color: #f8fafc;
        line-height: 1.3;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        margin-bottom: 4px;
    }
    .yt-video-channel {
        font-size: 12px;
        color: #94a3b8;
        margin-bottom: 2px;
    }
    .yt-video-meta {
        font-size: 12px;
        color: #94a3b8;
    }
    
    /* สไตล์ของแจก */
    .gift-card { background-color: #0f172a; border: 1px solid #334155; border-radius: 14px; padding: 12px; text-align: center; margin-bottom: 15px; }
    .gift-img-container { width: 100%; height: 160px; overflow: hidden; border-radius: 10px; background-color: #020617; margin-bottom: 8px; }
    .gift-img { width: 100%; height: 100%; object-fit: cover; border-radius: 10px; }
    
    .download-btn { display: block; background-color: #ef4444; color: white !important; padding: 6px 10px; font-size: 12px; font-weight: bold; border-radius: 10px; text-decoration: none !important; text-align: center; margin-top: 5px; }
    .yt-shelf-title { font-size: 18px; font-weight: bold; color: #f8fafc; margin: 20px 0 15px 0; display: flex; align-items: center; gap: 8px; }
    .yt-play-all { font-size: 14px; color: #94a3b8; font-weight: normal; cursor: pointer; text-decoration: none; }
    .letter-card { background-color: #1e293b; border-left: 4px solid #ef4444; border-radius: 8px; padding: 12px; margin-bottom: 10px; }
    
    /* ปรับแต่งส่วนของ Tabs ของ Streamlit ให้เหมือน YouTube */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        border-bottom: 1px solid #2d3748;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 16px;
        font-weight: 600;
        padding-bottom: 8px;
        background-color: transparent !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

view_mode = st.sidebar.radio("เมนูนำทาง", ["🏠 หน้าแรกแกลเลอรี", "⚙️ ระบบหลังบ้าน (สำหรับแนท)"])

# ==========================================
# 🏠 หน้าแรกแกลเลอรี
# ==========================================
if view_mode == "🏠 หน้าแรกแกลเลอรี":
    st.markdown("<h2 style='color: #f8fafc; margin-bottom: 5px;'>🎬 Artist Hub & Fan Space</h2>", unsafe_allow_html=True)
    
    # ดึงข้อมูลมาเตรียมไว้
    gifts_list = load_gifts()
    all_vids = load_data()
    df_vids = pd.DataFrame(all_vids).sort_values(by='date', ascending=False) if all_vids else pd.DataFrame()
    
    # 1. บอร์ดประกาศสำคัญ
    important_text = load_important_info()
    st.markdown(f'<div class="billboard-box"><h4 style="margin-top:0; color:#ef4444; font-size:15px;">📢 ประกาศและข้อมูลสำคัญ</h4><p style="margin-bottom:0; font-size:13px; white-space: pre-wrap;">{important_text}</p></div>', unsafe_allow_html=True)
    
    # 2. แดชบอร์ดเพลงโปรเจกต์หลัก MV Focus
    mv_data = load_mv_highlight()
    st.markdown(f"### 🎵 PROJECT FOCUS: {mv_data['title']}")
    st.markdown('<div class="mv-dashboard-box">', unsafe_allow_html=True)
    col_mv_player, col_mv_milestone = st.columns([1.3, 1])
    with col_mv_player:
        yt_id = extract_youtube_id(mv_data['url'])
        if yt_id: st.video(f"https://www.youtube.com/watch?v={yt_id}")
        else: st.error("ลิงก์เพลงหลักไม่ถูกต้อง")
    with col_mv_milestone:
        st.markdown("<h4 style='color: #38bdf8; margin-top:0;'>📊 สถิติเป้าหมายอัตโนมัติ (อัปเดตทุก 1 ชม.)</h4>", unsafe_allow_html=True)
        c_views, t_views = int(mv_data['current_views']), int(mv_data['target_views'])
        progress_ratio = min(float(c_views / t_views), 1.0) if t_views > 0 else 0.0
        st.columns(2)[0].metric(label="📈 ยอดวิวบน YouTube", value=f"{c_views:,} วิว")
        st.columns(2)[1].metric(label="🎯 เป้าหมาย", value=f"{t_views:,} วิว")
        st.markdown(f"**🔥 ความสำเร็จของโปรเจกต์: {progress_ratio*100:.2f}%**")
        st.progress(progress_ratio)
        if mv_data.get('last_updated', 0) > 0:
            thailand_time = float(mv_data['last_updated']) + 25200 
            update_str = datetime.datetime.fromtimestamp(thailand_time).strftime('%H:%M:%S')
            st.write(f"<span style='color:#64748b; font-size:12px;'>🔄 ข้อมูลเมื่อเวลา: {update_str} น.</span>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # --------------------------------------------------
    # แท็บนำทางถูกย้ายมาอยู่ตรงนี้ (ใต้ Project Focus ตามสั่ง)
    # --------------------------------------------------
    tab_home, tab_videos, tab_gifts, tab_letters = st.tabs(["หน้าแรก", "วิดีโอทั้งหมด", "🎨 ของแจกสำหรับแฟนๆ", "💌 ส่งจดหมาย"])
    
    # ---- TAB 1: หน้าแรก ----
    with tab_home:
        # โซนปักหมุดแนะนำพิเศษ (Pinned Highlights)
        pinned_gifts = [g for g in gifts_list if g.get('pinned', False)]
        pinned_vids = [v for v in all_vids if v.get('pinned', False)]
        
        if pinned_vids:
            st.markdown('<div class="yt-shelf-title">📌 ผลงานแนะนำยอดนิยม / ห้ามพลาด <span class="yt-play-all">▶ เล่นทั้งหมด</span></div>', unsafe_allow_html=True)
            pv_cols = st.columns(4)
            for pv_idx, pv_item in enumerate(pinned_vids[:4]):
                with pv_cols[pv_idx % 4]:
                    thumb = get_youtube_thumbnail(pv_item['link']) or "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=500"
                    click_url = pv_item['link'] if pv_item['link'] and not pd.isna(pv_item['link']) else "#"
                    
                    # แก้ไขจุดที่ทำให้ HTML เออเร่อหลุดออกไปนอกการ์ด
                    note_html = f'<div style="font-size:12px; color:#f59e0b; font-style:italic; margin-top:2px;">💬 {pv_item["note"]}</div>' if ('note' in pv_item and pv_item['note'] and not pd.isna(pv_item['note'])) else ''
                    
                    st.markdown(f"""
                    <a href="{click_url}" target="_blank" class="yt-video-card-link">
                        <div class="yt-video-card">
                            <div class="yt-thumbnail-container">
                                <img class="yt-thumbnail-img" src="{thumb}">
                            </div>
                            <div class="yt-video-details">
                                <div class="yt-video-title">📌 {pv_item["title"]}</div>
                                <div class="yt-video-channel">Admin Update • {pv_item["type"]}</div>
                                <div class="yt-video-meta">📅 {pv_item["date"]}</div>
                                {note_html}
                            </div>
                        </div>
                    </a>
                    """, unsafe_allow_html=True)
                    
        # ** เพิ่มหัวข้อของแจกแบบแนวนอน ต่อจากโซนแนะนำทันที **
        if gifts_list:
            st.markdown('<div class="yt-shelf-title">🎨 ของแจกสำหรับแฟนๆ / Fan Gifts</div>', unsafe_allow_html=True)
            g_home_cols = st.columns(4)
            for g_idx, g_item in enumerate(gifts_list[:4]): # แสดงผลตัวอย่างสูงสุด 4 ชิ้นแรกในหน้าแรก
                with g_home_cols[g_idx % 4]:
                    img_src = g_item['img_url']
                    if img_src and not str(img_src).startswith("http"): img_src = f"data:image/png;base64,{img_src}"
                    pin_badge = '<span style="color:#f59e0b; font-weight:bold;">📌 [แนะนำ]</span> ' if g_item.get('pinned', False) else ''
                    st.markdown(f"""
                    <div class="gift-card">
                        <div class="gift-img-container">
                            <img class="gift-img" src="{img_src}">
                        </div>
                        <div class="video-title" style="text-align:center; font-size:14px; font-weight:600; color:#f8fafc; margin-bottom:5px;">{pin_badge}{g_item["title"]}</div>
                        <a class="download-btn" href="{g_item["download_url"]}" target="_blank">📥 โหลดรูปเต็ม</a>
                    </div>
                    """, unsafe_allow_html=True)

        # แสดงผลชั้นวางปกติ 2 หมวดหมู่ตัวอย่างในหน้าแรก
        if not df_vids.empty:
            homepage_shelves = [
                {"type": "Variety / TV", "title": "📺 รายการโทรทัศน์ / Variety & TV Shows"},
                {"type": "Online Video / YouTube", "title": "🔴 คลิปออนไลน์ / YouTube & Social Media Content"}
            ]
            for shelf in homepage_shelves:
                df_shelf = df_vids[df_vids['type'] == shelf['type']]
                if not df_shelf.empty:
                    st.markdown(f'<div class="yt-shelf-title">{shelf["title"]} <span class="yt-play-all">▶ เล่นทั้งหมด</span></div>', unsafe_allow_html=True)
                    v_cols = st.columns(4)
                    for v_idx, v_item in enumerate(df_shelf.to_dict('records')[:4]):
                        with v_cols[v_idx % 4]:
                            thumb = get_youtube_thumbnail(v_item['link']) or "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=500"
                            click_url = v_item['link'] if v_item['link'] and not pd.isna(v_item['link']) else "#"
                            note_html = f'<div style="font-size:11px; color:#94a3b8; font-style:italic;">💬 {v_item["note"]}</div>' if ('note' in v_item and v_item['note'] and not pd.isna(v_item['note'])) else ''
                            
                            st.markdown(f"""
                            <a href="{click_url}" target="_blank" class="yt-video-card-link">
                                <div class="yt-video-card">
                                    <div class="yt-thumbnail-container">
                                        <img class="yt-thumbnail-img" src="{thumb}">
                                    </div>
                                    <div class="yt-video-details">
                                        <div class="yt-video-title">{v_item["title"]}</div>
                                        <div class="yt-video-channel">Official Channel</div>
                                        <div class="yt-video-meta">📅 {v_item["date"]}</div>
                                        {note_html}
                                    </div>
                                </div>
                            </a>
                            """, unsafe_allow_html=True)

    # ---- TAB 2: วิดีโอทั้งหมด (แยกหมวดหมู่จัดเต็ม) ----
    with tab_videos:
        video_shelves = [
            {"type": "Variety / TV", "title": "📺 รายการโทรทัศน์ / Variety & TV Shows"},
            {"type": "Online Video / YouTube", "title": "🔴 คลิปออนไลน์ / YouTube & Social Media Content"},
            {"type": "Event / Concert", "title": "🎤 งานอีเวนต์และคอนเสิร์ต / Live Events & Concerts"},
            {"type": "Radio / Podcast", "title": "📻 รายการวิทยุและพอดแคสต์ / Radio & Podcasts"}
        ]
        
        for shelf in video_shelves:
            st.markdown(f'<div class="yt-shelf-title">{shelf["title"]}</div>', unsafe_allow_html=True)
            if df_vids.empty: 
                st.caption("ยังไม่มีข้อมูลวิดีโอในคลัง")
            else:
                df_shelf = df_vids[df_vids['type'] == shelf['type']]
                if df_shelf.empty: 
                    st.caption("ยังไม่มีวิดีโอในหมวดหมู่นี้")
                else:
                    shelf_records = df_shelf.to_dict('records')
                    state_key = f"show_all_{shelf['type'].replace(' ', '_')}"
                    if state_key not in st.session_state: st.session_state[state_key] = False
                    
                    display_vids = shelf_records if st.session_state[state_key] else shelf_records[:4]
                    v_cols = st.columns(4)
                    for v_idx, v_item in enumerate(display_vids):
                        with v_cols[v_idx % 4]:
                            thumb = get_youtube_thumbnail(v_item['link']) or "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=500"
                            click_url = v_item['link'] if v_item['link'] and not pd.isna(v_item['link']) else "#"
                            note_html = f'<div style="font-size:11px; color:#94a3b8; font-style:italic;">💬 {v_item["note"]}</div>' if ('note' in v_item and v_item['note'] and not pd.isna(v_item['note'])) else ''
                            
                            st.markdown(f"""
                            <a href="{click_url}" target="_blank" class="yt-video-card-link">
                                <div class="yt-video-card">
                                    <div class="yt-thumbnail-container">
                                        <img class="yt-thumbnail-img" src="{thumb}">
                                    </div>
                                    <div class="yt-video-details">
                                        <div class="yt-video-title">{v_item["title"]}</div>
                                        <div class="yt-video-channel">Official Content</div>
                                        <div class="yt-video-meta">📅 {v_item["date"]}</div>
                                        {note_html}
                                    </div>
                                </div>
                            </a>
                            """, unsafe_allow_html=True)
                            
                    if len(shelf_records) > 4:
                        v_btn_label = "🔼 ยุบแถว" if st.session_state[state_key] else f"🔽 ดูเพิ่มเติมในหมวดนี้ ({len(shelf_records)-4} คลิป)"
                        if st.button(v_btn_label, key=f"btn_{state_key}"):
                            st.session_state[state_key] = not st.session_state[state_key]
                            st.rerun()

    # ---- TAB 3: ของแจกสำหรับแฟนๆ ----
    with tab_gifts:
        st.markdown('<div class="yt-shelf-title">🎨 รูปภาพแจกฟรีและของสมนาคุณสำหรับแฟนคลับ</div>', unsafe_allow_html=True)
        if not gifts_list: 
            st.caption("ขณะนี้ยังไม่มีรูปภาพของแจกเปิดให้ดาวน์โหลด")
        else:
            g_cols = st.columns(4)
            for g_idx, g_item in enumerate(gifts_list):
                with g_cols[g_idx % 4]:
                    img_src = g_item['img_url']
                    if img_src and not str(img_src).startswith("http"): img_src = f"data:image/png;base64,{img_src}"
                    pin_badge = '<span style="color:#f59e0b; font-weight:bold;">📌 [แนะนำ]</span> ' if g_item.get('pinned', False) else ''
                    st.markdown(f"""
                    <div class="gift-card">
                        <div class="gift-img-container">
                            <img class="gift-img" src="{img_src}">
                        </div>
                        <div class="video-title" style="text-align:center; font-size:14px; font-weight:600; color:#f8fafc; margin-bottom:5px;">{pin_badge}{g_item["title"]}</div>
                        <a class="download-btn" href="{g_item["download_url"]}" target="_blank">📥 โหลดรูปเต็ม</a>
                    </div>
                    """, unsafe_allow_html=True)

    # ---- TAB 4: กล่องส่งจดหมาย ----
    with tab_letters:
        st.markdown("<h3 style='color: #ef4444; margin-top:10px;'>💌 Fan Letter Box</h3>", unsafe_allow_html=True)
        st.write("คุณสามารถเขียนความรู้สึก คำติชม หรือคำให้กำลังใจส่งตรงถึงแอดมินระบบได้ที่นี่เลยครับ")
        with st.form(key="fan_message_form_v8", clear_on_submit=True):
            fan_name = st.text_input("ชื่อเล่นของคุณ:")
            fan_msg = st.text_area("ข้อความที่คุณอยากฝากถึงแอดมิน:")
            submit_letter = st.form_submit_button("✉️ ส่งจดหมายลับ")
        if submit_letter and fan_msg.strip():
            save_message(fan_name.strip() if fan_name.strip() else "แฟนคลับผู้ไม่ประสงค์ออกนาม", fan_msg.strip())
            st.success("💖 ส่งจดหมายสำเร็จแล้ว! ขอบคุณสำหรับทุกกำลังใจนะครับ")

# ==========================================
# ⚙️ ระบบหลังบ้านจัดการข้อมูล (สำหรับแนท)
# ==========================================
elif view_mode == "⚙️ ระบบหลังบ้าน (สำหรับแนท)":
    st.subheader("⚙️ ระบบจัดการข้อมูลหลังบ้าน")
    password_input = st.text_input("กรุณาป้อนรหัสผ่านผู้ดูแลระบบ:", type="password")
    
    if password_input == ADMIN_PASSWORD:
        st.success("🔓 ยืนยันตัวตนสำเร็จ! โหมดไฮบริดสองเลย์เอาต์พร้อมทำงานแล้วครับแนท")
        st.markdown("---")
        
        if "edit_index" not in st.session_state: st.session_state.edit_index = None
        if "edit_gift_index" not in st.session_state: st.session_state.edit_gift_index = None

        # 🎯 1. ตั้งค่าเพลงโปรเจกต์โฟกัส
        with st.expander("🎯 1. ตั้งค่าเพลงโปรเจกต์โฟกัส / MV ล่าสุด"):
            curr_mv = load_mv_highlight()
            with st.form(key="mv_form_exp"):
                mv_title_in = st.text_input("ชื่อเพลง:", value=curr_mv['title'])
                mv_url_in = st.text_input("ลิงก์ YouTube MV:", value=curr_mv['url'])
                mv_target_in = st.number_input("เป้าหมายยอดวิว:", value=int(curr_mv['target_views']), step=10000)
                mv_current_in = st.number_input("บังคับค่ายอดวิวเริ่มต้นชั่วคราว:", value=int(curr_mv['current_views']))
                mv_submit = st.form_submit_button("💾 บันทึก")
            if mv_submit:
                save_mv_highlight(mv_url_in, mv_current_in, mv_target_in, mv_title_in)
                if os.path.exists(MV_FILE):
                    df_t = pd.read_csv(MV_FILE); df_t.loc[0, 'last_updated'] = 0.0; df_t.to_csv(MV_FILE, index=False)
                st.success("บันทึกเพลงหลักแล้ว!"); st.rerun()

        # 📢 2. แก้ไขกระดานประกาศ
        with st.expander("📢 2. แก้ไขข้อมูลกระดานประกาศสำคัญหน้าแรก"):
            current_info = load_important_info()
            new_info_text = st.text_area("ข้อความประกาศ:", value=current_info, height=100)
            if st.button("💾 บันทึกประกาศ"):
                save_important_info(new_info_text)
                st.success("อัปเดตประกาศสำเร็จ!"); st.rerun()

        # 🎨 3. จัดการรูปภาพแจกฟรี
        with st.expander("🎨 3. จัดการรูปภาพแจกฟรีให้แฟนคลับ (แก้ไข/ปักหมุด/ลบ)"):
            gifts_data = load_gifts()
            col_g1, col_g2 = st.columns([1, 1.2])
            with col_g1:
                if st.session_state.edit_gift_index is not None:
                    st.markdown(f"**📝 แก้ไขของแจกชิ้นที่ {st.session_state.edit_gift_index + 1}**")
                    curr_gift = gifts_data[st.session_state.edit_gift_index]
                    default_g_title = curr_gift['title']
                    default_g_down = curr_gift['download_url']
                    default_g_pin = bool(curr_gift.get('pinned', False))
                    gift_btn_txt = "🔄 อัปเดตข้อมูลของแจก"
                else:
                    st.markdown("**➕ เพิ่มของแจกชิ้นใหม่**")
                    default_g_title = ""
                    default_g_down = ""
                    default_g_pin = False
                    gift_btn_txt = "🚀 อัปโหลดขึ้นหน้าแรก"
                with st.form(key="add_gift_exp_v8", clear_on_submit=False):
                    g_title = st.text_input("ชื่อของแจก:", value=default_g_title)
                    uploaded_img_file = st.file_uploader("เลือกรูปภาพตัวอย่างใหม่จากคอม:", type=["png", "jpg", "jpeg"])
                    g_down_url = st.text_input("ลิงก์ดาวน์โหลดรูปเต็ม (Google Drive):", value=default_g_down)
                    g_is_pinned = st.checkbox("📌 ปักหมุดรูปนี้ในโซนแนะนำของแจกบนสุด", value=default_g_pin)
                    gift_submit = st.form_submit_button(gift_btn_txt)
                if gift_submit and g_title and g_down_url:
                    base64_img = None
                    if uploaded_img_file: base64_img = base64.b64encode(uploaded_img_file.getvalue()).decode()
                    if st.session_state.edit_gift_index is not None:
                        gifts_data[st.session_state.edit_gift_index]['title'] = g_title
                        gifts_data[st.session_state.edit_gift_index]['download_url'] = g_down_url
                        gifts_data[st.session_state.edit_gift_index]['pinned'] = g_is_pinned
                        if base64_img: gifts_data[st.session_state.edit_gift_index]['img_url'] = base64_img
                        st.session_state.edit_gift_index = None
                        st.success("อัปเดตของแจกสำเร็จ!")
                    else:
                        if uploaded_img_file:
                            gifts_data.append({"title": g_title, "img_url": base64_img, "download_url": g_down_url, "pinned": g_is_pinned})
                            st.success("เพิ่มของแจกสำเร็จ!")
                        else: st.warning("กรุณาเลือกไฟล์รูปภาพตัวอย่างด้วยครับ")
                    save_gifts(gifts_data); st.rerun()
                if st.session_state.edit_gift_index is not None:
                    if st.button("❌ Cancel แก้ไขของแจก"): st.session_state.edit_gift_index = None; st.rerun()
            with col_g2:
                st.markdown("**📋 รายการของแจกปัจจุบัน**")
                for g_i, g_item in enumerate(gifts_data):
                    g_c1, g_c2, g_c3, g_c4 = st.columns([2, 0.9, 0.6, 0.5])
                    g_c1.write(f"{g_i + 1}. {g_item['title']}")
                    g_pin_val = g_item.get('pinned', False)
                    g_pin_lbl = "📌 หมุดอยู่" if g_pin_val else "◽ ทั่วไป"
                    if g_c2.button(g_pin_lbl, key=f"quick_pin_g_{g_i}"): g_item['pinned'] = not g_pin_val; save_gifts(gifts_data); st.rerun()
                    if g_c3.button("📝", key=f"edit_g_{g_i}"): st.session_state.edit_gift_index = g_i; st.rerun()
                    if g_c4.button("🗑️", key=f"del_g_{g_i}"):
                        if st.session_state.edit_gift_index == g_i: st.session_state.edit_gift_index = None
                        gifts_data.pop(g_i); save_gifts(gifts_data); st.rerun()

        # 🎬 4. จัดการคลังวิดีโอทั่วไป
        with st.expander("🎬 4. จัดการคลังผลงานวิดีโอและคิวงานทั่วไป"):
            col_v_form, col_v_manage = st.columns([1, 1.2])
            with col_v_form:
                if st.session_state.edit_index is not None:
                    st.markdown(f"**📝 แก้ไขวิดีโอรายการที่ {st.session_state.edit_index + 1}**")
                    curr = st.session_state.schedules[st.session_state.edit_index]
                    d_title, d_link, d_note = curr["title"], curr["link"], curr["note"]
                    d_pinned = bool(curr.get('pinned', False))
                    try: d_date = datetime.datetime.strptime(curr["date"], "%Y-%m-%d").date()
                    except: d_date = datetime.date.today()
                    options = ["Variety / TV", "Online Video / YouTube", "Event / Concert", "Radio / Podcast"]
                    d_type_idx = options.index(curr["type"]) if curr["type"] in options else 0
                    btn_txt = "🔄 อัปเดตวิดีโอ"
                else:
                    st.markdown("**➕ เพิ่มวิดีโอใหม่**")
                    d_title, d_link, d_note = "", "", ""
                    d_pinned = False
                    d_date = datetime.date.today()
                    d_type_idx = 0
                    btn_txt = "🚀 อัปโหลดเข้าคลัง"
                with st.form(key='admin_vid_exp_v8'):
                    title = st.text_input("ชื่อคลิป:", value=d_title)
                    date_val = st.date_input("วันที่:", value=d_date)
                    w_type = st.selectbox("ประเภท:", ["Variety / TV", "Online Video / YouTube", "Event / Concert", "Radio / Podcast"], index=d_type_idx)
                    link = st.text_input("ลิงก์คลิป:", value=d_link)
                    note = st.text_area("โน้ตย่อ:", value=d_note)
                    is_pinned = st.checkbox("📌 ปักหมุดคลิปนี้ในโซนวิดีโอแนะนำหน้าแรก", value=d_pinned)
                    vid_submit = st.form_submit_button(btn_txt)
                if vid_submit and title.strip():
                    item_data = {"title": title, "date": str(date_val), "type": w_type, "link": link, "note": note, "pinned": is_pinned}
                    if st.session_state.edit_index is not None:
                        st.session_state.schedules[st.session_state.edit_index] = item_data
                        st.session_state.edit_index = None
                    else: st.session_state.schedules.append(item_data)
                    save_data(st.session_state.schedules); st.success("บันทึกสำเร็จ!"); st.rerun()
                if st.session_state.edit_index is not None:
                    if st.button("❌ Cancel แก้ไขวิดีโอ"): st.session_state.edit_index = None; st.rerun()
            with col_v_manage:
                st.markdown("**📋 รายการวิดีโอปัจจุบัน**")
                for idx, item in enumerate(st.session_state.schedules):
                    v_c1, v_c2, v_c3, v_c4 = st.columns([2, 0.9, 0.6, 0.5])
                    v_c1.write(f"{idx+1}. {item['title']} ({item['type']})")
                    v_pin_val = item.get('pinned', False)
                    v_pin_lbl = "📌 หมุดอยู่" if v_pin_val else "◽ ทั่วไป"
                    if v_c2.button(v_pin_lbl, key=f"quick_pin_v_{idx}"): item['pinned'] = not v_pin_val; save_data(st.session_state.schedules); st.rerun()
                    if v_c3.button("📝", key=f"edit_v_{idx}"): st.session_state.edit_index = idx; st.rerun()
                    if v_c4.button("🗑️", key=f"del_v_{idx}"): 
                        if st.session_state.edit_index == idx: st.session_state.edit_index = None
                        st.session_state.schedules.pop(idx); save_data(st.session_state.schedules); st.rerun()

        # 📬 5. เปิดกล่องอ่านจดหมายลับ
        with st.expander("📬 5. เปิดกล่องอ่านจดหมายลับจากแฟนคลับ (Fan Letters)"):
            messages_list = load_messages()
            if not messages_list: st.info("กล่องจดหมายว่างอยู่ครับ")
            else:
                messages_list.reverse()
                for m_idx, m_item in enumerate(messages_list):
                    st.markdown(f'<div class="letter-card"><span style="font-size:11px; color:#94a3b8;">📅 {m_item["timestamp"]}</span><br><span style="font-weight:bold; color:#38bdf8;">👤 คุณ: {m_item["name"]}</span><br><p style="margin-top:4px; color:#e2e8f0; font-size:14px;">💬 {m_item["message"]}</p></div>', unsafe_allow_html=True)
                if st.button("🗑️ ล้างกล่องจดหมายทั้งหมด"):
                    if os.path.exists(MESSAGES_FILE): os.remove(MESSAGES_FILE)
                    st.success("ล้างตู้จดหมายเรียบร้อย!"); st.rerun()
                        
    elif password_input != "": st.error("รหัสผ่านไม่ถูกต้อง")
