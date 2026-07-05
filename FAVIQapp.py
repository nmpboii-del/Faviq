import streamlit as st
import pandas as pd
import os
import re
import requests
import time

# ตั้งค่าหน้า Streamlit
try:
    from PIL import Image
    fav_icon = Image.open("images/pageicon.png")
except:
    fav_icon = "🎬"

st.set_page_config(
    page_title="Artist Video Gallery & Fan Hub",
    page_icon=fav_icon,
    layout="wide"
)

# รายชื่อไฟล์สำหรับเก็บข้อมูลทั้งหมด
DATA_FILE = "artist_schedules.csv"
INFO_FILE = "important_info.txt"
MV_FILE = "mv_highlight.csv"
GIFTS_FILE = "fan_gifts.csv"      # ไฟล์เก็บข้อมูลรูปภาพที่แจก
MESSAGES_FILE = "fan_messages.csv" # ไฟล์เก็บจดหมายข้อความจากแฟนๆ

ADMIN_PASSWORD = "Nittaya_195"

# --- ฟังก์ชันช่วยจัดการระบบวิดีโอและวิวอัตโนมัติ ---
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
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Accept-Language": "en-US,en;q=0.9"}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            match = re.search(r'"viewCount":"(\d+)"', response.text)
            if match: return int(match.group(1))
    except: pass
    return None

def load_mv_highlight():
    default_data = {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "current_views": 100000, "target_views": 1000000, "title": "เพลงหลักของศิลปิน", "last_updated": 0.0}
    if os.path.exists(MV_FILE):
        try:
            df = pd.read_csv(MV_FILE)
            data = df.to_dict('records')[0]
            current_time = time.time()
            last_update_time = float(data.get('last_updated', 0.0))
            video_id = extract_youtube_id(data['url'])
            if (current_time - last_update_time) >= 3600 and video_id:
                fresh_views = fetch_live_youtube_views(video_id)
                if fresh_views and fresh_views > 0:
                    data['current_views'] = fresh_views
                    data['last_updated'] = current_time
                    pd.DataFrame([data]).to_csv(MV_FILE, index=False, encoding='utf-8-sig')
            return data
        except: return default_data
    return default_data

def save_mv_highlight(url, current_views, target_views, title):
    df = pd.DataFrame([{"url": url, "current_views": int(current_views), "target_views": int(target_views), "title": title, "last_updated": time.time()}])
    df.to_csv(MV_FILE, index=False, encoding='utf-8-sig')

# --- ฟังก์ชันจัดการข้อมูลรูปแจก และ ข้อความแฟนคลับ (ฟีเจอร์ใหม่) ---
def load_gifts():
    if os.path.exists(GIFTS_FILE):
        return pd.read_csv(GIFTS_FILE).to_dict('records')
    return []

def save_gifts(data):
    pd.DataFrame(data).to_csv(GIFTS_FILE, index=False, encoding='utf-8-sig')

def load_messages():
    if os.path.exists(MESSAGES_FILE):
        return pd.read_csv(MESSAGES_FILE).to_dict('records')
    return []

def save_message(name, message):
    new_msg = {"timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), "name": name, "message": message}
    messages = load_messages()
    messages.append(new_msg)
    pd.DataFrame(messages).to_csv(MESSAGES_FILE, index=False, encoding='utf-8-sig')

# --- โหลดคลังวิดีโอและประกาศเดิม ---
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['date'] = df['date'].astype(str)
        if 'pinned' not in df.columns: df['pinned'] = False
        else: df['pinned'] = df['pinned'].astype(bool)
        return df.to_dict('records')
    return []

def save_data(data):
    pd.DataFrame(data).to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

def load_important_info():
    if os.path.exists(INFO_FILE):
        with open(INFO_FILE, "r", encoding="utf-8") as f: return f.read()
    return "💡 ยินดีต้อนรับสู่คลังวิดีโอศิลปิน!"

def save_important_info(text):
    with open(INFO_FILE, "w", encoding="utf-8") as f: f.write(text)

if "schedules" not in st.session_state: st.session_state.schedules = load_data()

import datetime

# --- สไตล์การตกแต่ง CSS เพิ่มเติมสำหรับฟีเจอร์ใหม่ ---
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .billboard-box { background: linear-gradient(135deg, #1e1b4b 0%, #2e1065 100%); border-left: 6px solid #c084fc; padding: 20px; border-radius: 14px; color: #f1f5f9; margin-bottom: 25px; }
    .mv-dashboard-box { background-color: #0b0f19; border: 2px solid #38bdf8; border-radius: 18px; padding: 20px; margin-bottom: 30px; box-shadow: 0 4px 20px rgba(56, 189, 248, 0.15); }
    .video-card { background-color: #0f172a; padding: 12px; border-radius: 14px; border: 1px solid #1e293b; margin-bottom: 25px; transition: transform 0.2s; }
    .video-card:hover { transform: translateY(-4px); border-color: #38bdf8; }
    .thumbnail-container { position: relative; width: 100%; padding-top: 56.25%; overflow: hidden; border-radius: 10px; }
    .thumbnail-img { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; }
    
    /* สไตล์สำหรับการ์ดแจกรูปภาพ */
    .gift-card { background-color: #0f172a; border: 1px solid #334155; border-radius: 14px; padding: 10px; text-align: center; margin-bottom: 20px; }
    .gift-img { width: 100%; border-radius: 10px; height: 180px; object-fit: cover; margin-bottom: 10px; }
    
    /* สไตล์สำหรับการ์ดเปิดอ่านจดหมายในหลังบ้าน */
    .letter-card { background-color: #1e293b; border-left: 4px solid #10b981; border-radius: 8px; padding: 12px; margin-bottom: 10px; }
    
    .video-title { font-size: 15px; font-weight: 600; margin: 12px 0 6px 0; color: #f8fafc; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
    .video-meta { font-size: 12px; color: #94a3b8; }
    .watch-btn { display: inline-block; background-color: #ef4444; color: white !important; padding: 6px 16px; font-size: 12px; font-weight: bold; border-radius: 20px; text-decoration: none !important; margin-top: 10px; text-align: center;}
    .download-btn { display: block; background-color: #10b981; color: white !important; padding: 8px 12px; font-size: 13px; font-weight: bold; border-radius: 10px; text-decoration: none !important; text-align: center; margin-top: 5px; }
    .download-btn:hover { background-color: #059669; }
    </style>
    """,
    unsafe_allow_html=True
)

view_mode = st.sidebar.radio("เมนูนำทาง", ["🏠 หน้าแรกแกลเลอรี", "⚙️ ระบบหลังบ้าน (สำหรับแนท)"])

# ==========================================
# 🏠 หน้าแรกแกลเลอรีวิดีโอและศูนย์แฟนคลับ
# ==========================================
if view_mode == "🏠 หน้าแรกแกลเลอรี":
    st.markdown("<h1 style='text-align: center; color: #38bdf8;'>⭐ Artist Hub & Fan Space</h1>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color: #1e293b;'>", unsafe_allow_html=True)
    
    # 1. ส่วนข้อมูลสำคัญ (ประกาศหน้าร้าน)
    important_text = load_important_info()
    st.markdown(f"""
    <div class="billboard-box">
        <h3 style="margin-top:0; color:#c084fc; font-size:17px;">📢 ประกาศและข้อมูลสำคัญจากแอดมิน</h3>
        <p style="margin-bottom:0; font-size:15px; white-space: pre-wrap;">{important_text}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. แดชบอร์ดโฟกัส MV หลัก
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
        c_views = int(mv_data['current_views'])
        t_views = int(mv_data['target_views'])
        progress_ratio = min(float(c_views / t_views), 1.0) if t_views > 0 else 0.0
        progress_percent = progress_ratio * 100
        
        col_m1, col_m2 = st.columns(2)
        with col_m1: st.metric(label="📈 ยอดวิวปัจจุบันบน YouTube", value=f"{c_views:,} วิว")
        with col_m2: st.metric(label="🎯 เป้าหมายโปรเจกต์", value=f"{t_views:,} วิว")
            
        st.markdown(f"**🔥 ความสำเร็จของโปรเจกต์: {progress_percent:.2f}%**")
        st.progress(progress_ratio)
        if mv_data.get('last_updated', 0) > 0:
            update_str = datetime.datetime.fromtimestamp(mv_data['last_updated']).strftime('%H:%M:%S')
            st.write(f"<span style='color:#64748b; font-size:12px;'>🔄 ดึงยอดวิวล่าสุดเมื่อเวลา: {update_str} น.</span>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # แบ่งฝั่งล่าง: ฝั่งซ้ายโชว์คลังคลิปและของแจก / ฝั่งขวาเปิดกล่องรับความรู้สึกจากแฟนๆ
    col_left_content, col_right_fanbox = st.columns([2.2, 1])
    
    with col_left_content:
        # 3. แถบหมวดหมู่แบ่งผลงาน และเพิ่มแท็บ "🎨 ของแจกสำหรับแฟนๆ"
        categories = ["วิดีโอทั้งหมด", "Variety / TV", "Online Video / YouTube", "Event / Concert", "🎨 ของแจกสำหรับแฟนๆ"]
        selected_tabs = st.tabs(categories)
        
        # ค้นหาในวิดีโอทั่วไป
        if st.session_state.schedules:
            df_display = pd.DataFrame(st.session_state.schedules).sort_values(by='date', ascending=False)
        else:
            df_display = pd.DataFrame()
            
        for i, cat in enumerate(categories):
            with selected_tabs[i]:
                if cat == "🎨 ของแจกสำหรับแฟนๆ":
                    # --- แสดงผลหน้าแจกรูปภาพวอลเปเปอร์ ---
                    gifts_list = load_gifts()
                    if not gifts_list:
                        st.caption("ขณะนี้ยังไม่มีรูปภาพแจกฟรี แวะมาเช็กใหม่คราวหน้านะครับ!")
                    else:
                        g_cols = st.columns(3)
                        for g_idx, g_item in enumerate(gifts_list):
                            g_col_idx = g_idx % 3
                            with g_cols[g_col_idx]:
                                st.markdown(f"""
                                <div class="gift-card">
                                    <img class="gift-img" src="{g_item['img_url']}">
                                    <div style="font-weight:bold; font-size:14px; color:#f8fafc; margin-bottom:5px;">{g_item['title']}</div>
                                    <a class="download-btn" href="{g_item['download_url']}" target="_blank">📥 ดาวน์โหลดรูปเต็ม</a>
                                </div>
                                """, unsafe_allow_html=True)
                else:
                    # --- แสดงผลวิดีโอตามปกติ ---
                    if df_display.empty:
                        st.caption("ไม่มีวิดีโอในระบบ")
                    else:
                        df_cat = df_display if cat == "วิดีโอทั้งหมด" else df_display[df_display['type'] == cat]
                        if df_cat.empty: st.caption("ไม่มีวิดีโอในหมวดหมู่นี้")
                        else:
                            cat_records = df_cat.to_dict('records')
                            cols = st.columns(3) # ปรับเหลือ 3 คอลัมน์เพื่อให้เข้ากับเลย์เอาต์แบ่งฝั่ง
                            for idx, item in enumerate(cat_records):
                                col_idx = idx % 3
                                with cols[col_idx]:
                                    thumb = get_youtube_thumbnail(item['link']) or "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=500"
                                    st.markdown(f"""
                                    <div class="video-card">
                                        <div class="thumbnail-container"><img class="thumbnail-img" src="{thumb}"></div>
                                        <div class="video-title">{item['title']}</div>
                                        <div class="video-meta">📅 {item['date']} • {item['type']}</div>
                                    """, unsafe_allow_html=True)
                                    if item['note'] and not pd.isna(item['note']): st.markdown(f'<div style="font-size:12px; color:#94a3b8; font-style:italic; margin-top:4px;">💬 {item["note"]}</div>', unsafe_allow_html=True)
                                    if item['link'] and not pd.isna(item['link']): st.markdown(f'<a class="watch-btn" href="{item["link"]}" target="_blank">▶ ชมคลิป</a>', unsafe_allow_html=True)
                                    st.markdown("</div>", unsafe_allow_html=True)
                                    
    with col_right_fanbox:
        # 4. 💌 ส่วนกล่องรับข้อความส่งความสุขถึงแอดมินนัท
        st.markdown("<h3 style='color: #10b981; margin-top:0;'>💌 Fan Letter Box</h3>", unsafe_allow_html=True)
        st.write("พิมพ์ข้อความส่งความในใจ รีวิวความฟิน หรือแวะมาทักทายแอดมินนัทได้ที่นี่เลยน้า! (ข้อความจะถูกส่งถึงแอดมินโดยตรงแบบส่วนตัว)")
        
        with st.form(key="fan_message_form", clear_on_submit=True):
            fan_name = st.text_input("ชื่อเล่น / นามปากกาของคุณ:", placeholder="เช่น นุชคนดี, แฟนคลับเบอร์ 1")
            fan_msg = st.text_area("ข้อความที่คุณอยากบอกแอดมิน:", placeholder="พิมพ์ความในใจยาวๆ ตรงนี้ได้เลยน้า...")
            submit_letter = st.form_submit_button("✉️ ส่งจดหมายลับถึงแอดมิน")
            
        if submit_letter:
            if not fan_msg.strip():
                st.warning("กรุณาพิมพ์ข้อความก่อนส่งด้วยน้า!")
            else:
                name_to_save = fan_name.strip() if fan_name.strip() else "แฟนคลับผู้ไม่ประสงค์ออกนาม"
                save_message(name_to_save, fan_msg.strip())
                st.success("💖 ส่งจดหมายถึงแอดมินเรียบร้อยแล้ว! ขอบคุณสำหรับกำลังใจนะครับ")

# ==========================================
# ⚙️ ระบบหลังบ้านจัดการข้อมูล (สำหรับแนท)
# ==========================================
elif view_mode == "⚙️ ระบบหลังบ้าน (สำหรับแนท)":
    st.subheader("⚙️ ระบบจัดการข้อมูลหลังบ้าน")
    password_input = st.text_input("กรุณาป้อนรหัสผ่านผู้ดูแลระบบ:", type="password")
    
    if password_input == ADMIN_PASSWORD:
        st.success("🔓 ยืนยันตัวตนสำเร็จ!")
        st.markdown("---")
        
        # แบ่งหลังบ้านเป็น 2 คอลัมน์: ฝั่งซ้ายกรอกฟอร์มต่างๆ / ฝั่งขวาอ่านจดหมายแฟนคลับและจัดการไฟล์
        col_adm_left, col_adm_right = st.columns([1.1, 1])
        
        with col_adm_left:
            # 🎯 ตั้งค่าเพลง MV ไฮไลท์
            st.markdown("### 🎯 ตั้งค่าเพลงโปรเจกต์โฟกัส / MV ล่าสุด")
            curr_mv = load_mv_highlight()
            with st.form(key="mv_highlight_form_v5"):
                mv_title_in = st.text_input("ชื่อหัวข้อเพลง:", value=curr_mv['title'])
                mv_url_in = st.text_input("ลิงก์ YouTube MV:", value=curr_mv['url'])
                mv_target_in = st.number_input("เป้าหมายยอดวิวความสำเร็จ:", value=int(curr_mv['target_views']), step=10000)
                mv_current_in = st.number_input("บังคับค่ายอดวิวเริ่มต้นชั่วคราว:", value=int(curr_mv['current_views']))
                mv_submit = st.form_submit_button("💾 บันทึกโปรเจกต์หลัก")
            if mv_submit:
                save_mv_highlight(mv_url_in, mv_current_in, mv_target_in, mv_title_in)
                if os.path.exists(MV_FILE):
                    df_t = pd.read_csv(MV_FILE)
                    df_t.loc[0, 'last_updated'] = 0.0
                    df_t.to_csv(MV_FILE, index=False)
                st.success("อัปเดตเพลงหลักแล้ว!")
                st.rerun()
                
            st.markdown("---")
            # 📝 แผงควบคุมบอร์ดประกาศข่าวสำคัญ
            st.markdown("### 📝 แก้ไขข้อมูลประกาศสำคัญหน้าแรก")
            current_info = load_important_info()
            new_info_text = st.text_area("ข้อความบอร์ดประกาศ:", value=current_info, height=100)
            if st.button("💾 บันทึกประกาศ"):
                save_important_info(new_info_text)
                st.success("อัปเดตประกาศสำเร็จ!")
                st.rerun()
                
            st.markdown("---")
            # 🎨 ระบบอัปเดตรูปแจกแฟนคลับ (ฟีเจอร์ใหม่หลังบ้าน)
            st.markdown("### 🎨 จัดการรูปภาพแจกฟรี (Wallpapers / Frames)")
            gifts_data = load_gifts()
            with st.form(key="add_gift_form", clear_on_submit=True):
                g_title = st.text_input("ชื่อรูปภาพ/เซ็ตของแจก:", placeholder="เช่น วอลเปเปอร์หน้าจอมือถือธีมชมพูหวาน")
                g_img_url = st.text_input("ลิงก์ URL รูปภาพตัวอย่าง (Thumbnail):", placeholder="https://ตัวอย่างรูป.png")
                g_down_url = st.text_input("ลิงก์ URL สำหรับให้กดดาวน์โหลดรูปชัดเต็มๆ (เช่น ลิงก์ Google Drive):", placeholder="https://drive.google.com/...")
                gift_submit = st.form_submit_button("🚀 อัปโหลดของแจกขึ้นหน้าแรก")
            if gift_submit:
                if not g_title or not g_img_url or not g_down_url:
                    st.warning("กรุณากรอกข้อมูลรูปภาพแจกให้ครบทุกช่องน้า!")
                else:
                    gifts_data.append({"title": g_title, "img_url": g_img_url, "download_url": g_down_url})
                    save_gifts(gifts_data)
                    st.success("เพิ่มของแจกแฟนคลับเข้าแท็บเรียบร้อย!")
                    st.rerun()
                    
            # แสดงรายการของแจกที่เคยลงไว้และปุ่มกดลบ
            if gifts_data:
                st.write("รายการของแจกปัจจุบัน:")
                for g_i, g_item in enumerate(gifts_data):
                    g_c1, g_c2 = st.columns([3, 1])
                    g_c1.write(f"- {g_item['title']}")
                    if g_c2.button("ลบ", key=f"del_g_{g_i}"):
                        gifts_data.pop(g_i)
                        save_gifts(gifts_data)
                        st.rerun()
                        
        with col_adm_right:
            # 📨 💌 แผงเปิดอ่านจดหมายลับจากแฟนคลับ (มีให้ส่องข้อความเฉพาะแนทคนเดียว)
            st.markdown("### 📬 เปิดกล่องจดหมายจากแฟนคลับ (Fan Letters)")
            messages_list = load_messages()
            
            if not messages_list:
                st.info("ตอนนี้กล่องจดหมายยังว่างอยู่ รอแฟนๆ แวะมาหย่อนข้อความอยู่น้า 🎁")
            else:
                # เรียงจดหมายใหม่ล่าสุดอยู่บนสุด
                messages_list.reverse()
                st.write(f"คุณได้รับจดหมายทั้งหมด {len(messages_list)} ฉบับ:")
                
                # แสดงจดหมายเป็นกล่องๆ การ์ด
                for m_idx, m_item in enumerate(messages_list):
                    st.markdown(f"""
                    <div class="letter-card">
                        <span style="font-size:11px; color:#94a3b8;">📅 {m_item['timestamp']}</span><br>
                        <span style="font-weight:bold; color:#38bdf8;">👤 คุณ: {m_item['name']}</span><br>
                        <p style="margin-top:6px; margin-bottom:0; color:#e2e8f0; font-size:14px; white-space: pre-wrap;">💬 {m_item['message']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                if st.button("🗑️ ล้างกล่องจดหมายทั้งหมด"):
                    if os.path.exists(MESSAGES_FILE): os.remove(MESSAGES_FILE)
                    st.success("ล้างตู้จดหมายเรียบร้อย!")
                    st.rerun()

            st.markdown("---")
            # 📋 ส่วนคลังวิดีโอย่อยเดิม
            st.markdown("### 🎬 จัดการคลังวิดีโอทั่วไป")
            if "edit_index" not in st.session_state: st.session_state.edit_index = None
            
            with st.form(key='admin_video_form_v5'):
                title = st.text_input("ชื่อคลิปรายการ:")
                date_val = st.date_input("วันที่:")
                w_type = st.selectbox("ประเภท:", ["Variety / TV", "Online Video / YouTube", "Event / Concert", "Radio / Podcast"])
                link = st.text_input("ลิงก์คลิป:")
                note = st.text_area("โน้ตย่อย:")
                is_pinned = st.checkbox("📌 ปักหมุดในโซนแนะนำ")
                vid_submit = st.form_submit_button("🚀 บันทึกเข้าคลังวิดีโอ")
            if vid_submit:
                if not title.strip(): st.warning("กรุณากรอกชื่อด้วยครับ!")
                else:
                    st.session_state.schedules.append({"title": title, "date": str(date_val), "type": w_type, "link": link, "note": note, "pinned": is_pinned})
                    save_data(st.session_state.schedules)
                    st.success("บันทึกคลังวิดีโอสำเร็จ!")
                    st.rerun()
                    
            # แสดงตารางกดลบวิดีโอทั่วไปแบบมินิ
            if st.session_state.schedules:
                for idx, item in enumerate(st.session_state.schedules):
                    v_c1, v_c2 = st.columns([4, 1])
                    v_c1.write(f"{idx+1}. {item['title']}")
                    if v_c2.button("🗑️", key=f"del_v_{idx}"):
                        st.session_state.schedules.pop(idx)
                        save_data(st.session_state.schedules)
                        st.rerun()
