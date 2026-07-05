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
    page_title="Artist Video Gallery & Dashboard",
    page_icon=fav_icon,
    layout="wide"
)

# รายชื่อไฟล์สำหรับเก็บข้อมูล
DATA_FILE = "artist_schedules.csv"
INFO_FILE = "important_info.txt"
MV_FILE = "mv_highlight.csv"

ADMIN_PASSWORD = "Nittaya_195"

# ฟังก์ชันดึง ID จากลิงก์ YouTube
def extract_youtube_id(url):
    if not url or pd.isna(url):
        return None
    youtube_regex = r'(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([^&=%\?\{\s]+)'
    match = re.search(youtube_regex, str(url))
    if match:
        return match.group(4)
    return None

def get_youtube_thumbnail(url):
    video_id = extract_youtube_id(url)
    if video_id:
        return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
    return None

# 🔥 ฟังก์ชันพิเศษ: วิ่งไปดึงยอดวิวจริงจากหลังบ้าน YouTube แบบสาธารณะ
def fetch_live_youtube_views(video_id):
    if not video_id:
        return None
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        # ดึงโค้ดหน้าเว็บตัวเต็มของคลิปนั้นๆ
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            # ใช้ Regex ค้นหาแท็ก "viewCount":"XXXX" ที่ YouTube ซ่อนไว้ในซอร์สโค้ดหน้าเว็บ
            match = re.search(r'"viewCount":"(\d+)"', response.text)
            if match:
                return int(match.group(1))
    except:
        pass
    return None

# ฟังก์ชันโหลดข้อมูล MV ไฮไลท์ และเช็กเวลาคลาวด์เพื่ออัปเดตทุก 1 ชั่วโมง
def load_mv_highlight():
    default_data = {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "current_views": 100000,
        "target_views": 1000000,
        "title": "เพลงหลักของศิลปิน",
        "last_updated": 0.0  # เก็บเวลา Timestamp ที่อัปเดตวิวรอบล่าสุด
    }
    
    if os.path.exists(MV_FILE):
        try:
            df = pd.read_csv(MV_FILE)
            data = df.to_dict('records')[0]
            
            # ตรวจสอบว่าผ่านมาเกิน 1 ชั่วโมง (3,600 วินาที) หรือยัง?
            current_time = time.time()
            last_update_time = float(data.get('last_updated', 0.0))
            video_id = extract_youtube_id(data['url'])
            
            # 🕒 ถ้าเกิน 1 ชั่วโมงแล้ว ให้ทำภารกิจดึงยอดวิวใหม่มาแทนค่าเดิมอัตโนมัติ
            if (current_time - last_update_time) >= 3600 and video_id:
                fresh_views = fetch_live_youtube_views(video_id)
                if fresh_views and fresh_views > 0:
                    data['current_views'] = fresh_views
                    data['last_updated'] = current_time
                    # บันทึกข้อมูลใหม่ลงไฟล์ทันที
                    pd.DataFrame([data]).to_csv(MV_FILE, index=False, encoding='utf-8-sig')
            return data
        except:
            return default_data
    return default_data

def save_mv_highlight(url, current_views, target_views, title):
    df = pd.DataFrame([{
        "url": url,
        "current_views": int(current_views),
        "target_views": int(target_views),
        "title": title,
        "last_updated": time.time() # บันทึกเวลาที่เปลี่ยนคลิปใหม่ล่าสุด
    }])
    df.to_csv(MV_FILE, index=False, encoding='utf-8-sig')

# --- ฟังก์ชันระบบคลังวิดีโอทั่วไปเหมือนเดิม ---
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['date'] = df['date'].astype(str)
        if 'pinned' not in df.columns: df['pinned'] = False
        else: df['pinned'] = df['pinned'].astype(bool)
        return df.to_dict('records')
    return []

def save_data(data):
    df = pd.DataFrame(data)
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

def load_important_info():
    if os.path.exists(INFO_FILE):
        with open(INFO_FILE, "r", encoding="utf-8") as f: return f.read()
    return "💡 ยินดีต้อนรับสู่คลังวิดีโอศิลปิน!"

def save_important_info(text):
    with open(INFO_FILE, "w", encoding="utf-8") as f: f.write(text)

if "schedules" not in st.session_state:
    st.session_state.schedules = load_data()

# สไตล์การแสดงผล CSS 
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
    .video-title { font-size: 15px; font-weight: 600; margin: 12px 0 6px 0; color: #f8fafc; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
    .video-meta { font-size: 12px; color: #94a3b8; }
    .watch-btn { display: inline-block; background-color: #ef4444; color: white !important; padding: 6px 16px; font-size: 12px; font-weight: bold; border-radius: 20px; text-decoration: none !important; margin-top: 10px; }
    </style>
    """,
    unsafe_allow_html=True
)

view_mode = st.sidebar.radio("เมนูนำทาง", ["🏠 หน้าแรกแกลเลอรี", "⚙️ ระบบหลังบ้าน (สำหรับแนท)"])

# ==========================================
# 🏠 หน้าแรกแกลเลอรีวิดีโอและกระดานข้อมูล
# ==========================================
if view_mode == "🏠 หน้าแรกแกลเลอรี":
    st.markdown("<h1 style='text-align: center; color: #38bdf8;'>⭐ Artist Hub & Video Gallery</h1>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color: #1e293b;'>", unsafe_allow_html=True)
    
    important_text = load_important_info()
    st.markdown(f"""
    <div class="billboard-box">
        <h3 style="margin-top:0; color:#c084fc; font-size:17px;">📢 ประกาศและข้อมูลสำคัญจากแอดมิน</h3>
        <p style="margin-bottom:0; font-size:15px; white-space: pre-wrap;">{important_text}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 🎯 แผงแดชบอร์ดนับยอดวิวอัตโนมัติ
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
        
        # แสดงเวลาที่ระบบดึงค่ารอบล่าสุดให้ผู้ใช้เห็นเพื่อความชัดเจน
        if mv_data.get('last_updated', 0) > 0:
            import datetime
            update_str = datetime.datetime.fromtimestamp(mv_data['last_updated']).strftime('%H:%M:%S')
            st.write(f"<span style='color:#64748b; font-size:12px;'>🔄 ดึงยอดวิวล่าสุดเมื่อเวลา: {update_str} น. (ระบบจะเช็กข้อมูลใหม่ทุกชั่วโมง)</span>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    
    # 📌 ส่วนคลิปปักหมุดเด่นเพิ่มเติม
    if st.session_state.schedules:
        df_all = pd.DataFrame(st.session_state.schedules)
        df_pinned = df_all[df_all['pinned'] == True]
        if not df_pinned.empty:
            st.markdown("### 📌 คลิปแนะนำเด่นเพิ่มเติม")
            p_records = df_pinned.to_dict('records')
            p_cols = st.columns(len(p_records) if len(p_records) <= 4 else 4)
            for p_idx, p_item in enumerate(p_records):
                p_col_idx = p_idx % 4
                with p_cols[p_col_idx]:
                    p_thumb = get_youtube_thumbnail(p_item['link']) or "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=500"
                    st.markdown(f"""
                    <div class="video-card" style="border: 1px dashed #f59e0b;">
                        <div class="thumbnail-container"><img class="thumbnail-img" src="{p_thumb}"></div>
                        <div class="video-title" style="color: #f59e0b;">{p_item['title']}</div>
                        <div class="video-meta">📅 {p_item['date']} • {p_item['type']}</div>
                    """, unsafe_allow_html=True)
                    if p_item['note'] and not pd.isna(p_item['note']):
                        st.markdown(f"<div style='font-size:12px; color:#cbd5e1; margin-top:4px; font-style:italic;'>💬 {p_item['note']}</div>", unsafe_allow_html=True)
                    if p_item['link'] and not pd.isna(p_item['link']):
                        st.markdown(f"<a class='watch-btn' style='background-color:#f59e0b; color:#0f172a !important;' href='{p_item['link']}' target='_blank'>▶ ชมคลิป</a>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<hr style='border-color: #1e293b;'>", unsafe_allow_html=True)

        # 🎬 คลังผลงานปกติแยกหมวดหมู่
        st.markdown("### 🎬 คลังผลงานทั้งหมด")
        search_query = st.text_input("🔍 ค้นหาคลิปรายการ...", placeholder="พิมพ์คำค้นหา...")
        
        categories = ["วิดีโอทั้งหมด", "Variety / TV", "Online Video / YouTube", "Event / Concert", "Radio / Podcast"]
        selected_tabs = st.tabs(categories)
        
        df_display = df_all.sort_values(by='date', ascending=False)
        if search_query:
            df_display = df_display[df_display['title'].str.contains(search_query, case=False, na=False) | df_display['note'].str.contains(search_query, case=False, na=False)]
            
        for i, cat in enumerate(categories):
            with selected_tabs[i]:
                df_cat = df_display if cat == "วิดีโอทั้งหมด" else df_display[df_display['type'] == cat]
                if df_cat.empty: st.caption("ไม่มีวิดีโอในหมวดหมู่นี้")
                else:
                    cat_records = df_cat.to_dict('records')
                    cols = st.columns(4)
                    for idx, item in enumerate(cat_records):
                        col_idx = idx % 4
                        with cols[col_idx]:
                            thumb = get_youtube_thumbnail(item['link']) or "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=500"
                            card_html = f"""
                            <div class="video-card">
                                <div class="thumbnail-container"><img class="thumbnail-img" src="{thumb}"></div>
                                <div class="video-title">{item['title']}</div>
                                <div class="video-meta">📅 {item['date']} • {item['type']}</div>
                            """
                            if item['note'] and not pd.isna(item['note']): card_html += f'<div style="font-size:12px; color:#94a3b8; font-style:italic; margin-top:4px;">💬 {item["note"]}</div>'
                            if item['link'] and not pd.isna(item['link']): card_html += f'<a class="watch-btn" href="{item["link"]}" target="_blank">▶ ชมคลิป</a>'
                            card_html += "</div>"
                            st.markdown(card_html, unsafe_allow_html=True)

# ==========================================
# ⚙️ ระบบหลังบ้านจัดการข้อมูล (สำหรับแนท)
# ==========================================
elif view_mode == "⚙️ ระบบหลังบ้าน (สำหรับแนท)":
    st.subheader("⚙️ ระบบจัดการข้อมูลหลังบ้าน")
    password_input = st.text_input("กรุณาป้อนรหัสผ่านผู้ดูแลระบบ:", type="password")
    
    if password_input == ADMIN_PASSWORD:
        st.success("🔓 ยืนยันตัวตนสำเร็จ!")
        st.markdown("---")
        
        # ส่วนตั้งค่าเพลงโฟกัส (ลดเหลือแค่กรอกลิงก์, ชื่อ, และยอดวิวเป้าหมาย เพราะตัววิวปัจจุบันมันดึงอัตโนมัติแล้วครับ)
        st.markdown("### 🎯 ตั้งค่าเพลงโปรเจกต์โฟกัส / MV ใหม่ล่าสุด")
        curr_mv = load_mv_highlight()
        
        with st.form(key="mv_highlight_form"):
            mv_title_in = st.text_input("ชื่อหัวข้อโปรเจกต์/ชื่อเพลง:", value=curr_mv['title'])
            mv_url_in = st.text_input("ลิงก์วิดีโอ YouTube ของ MV เพลงหลัก:", value=curr_mv['url'])
            mv_target_in = st.number_input("ตั้งเป้าหมายยอดวิวความสำเร็จ (ตัวเลข):", value=int(curr_mv['target_views']), step=10000)
            
            st.info("💡 ยอดวิวปัจจุบันจะถูกดึงอัตโนมัติจาก YouTube ทุกๆ 1 ชม. โดยคุณไม่ต้องคีย์ด้วยมืออีกต่อไป หรือคุณสามารถพิมพ์บังคับค่าเริ่มต้นชั่วคราวด้านล่างนี้ได้ครับ:")
            mv_current_in = st.number_input("บังคับค่ายอดวิวเริ่มต้นชั่วคราว:", value=int(curr_mv['current_views']))
            
            mv_submit = st.form_submit_button("💾 บันทึกและเริ่มดึงข้อมูลอัตโนมัติ")
            
        if mv_submit:
            # สั่งรีเซ็ตเวลาอัปเดต เพื่อให้ระบบเริ่มดึงยอดวิวจริงทันทีรอบแรก
            save_mv_highlight(mv_url_in, mv_current_in, mv_target_in, mv_title_in)
            # แอบเคลียร์ค่าเวลาเพื่อให้ดึงสดๆ ทันทีที่กดปุ่ม
            if os.path.exists(MV_FILE):
                df_temp = pd.read_csv(MV_FILE)
                if not df_temp.empty:
                    df_temp.loc[0, 'last_updated'] = 0.0
                    df_temp.to_csv(MV_FILE, index=False)
            st.success("เปลี่ยนเพลงโปรเจกต์หลักและระบบเริ่มทำงานแล้ว!")
            st.rerun()
            
        st.markdown("---")
        # ส่วนควบคุมประกาศสำคัญ
        st.markdown("### 📝 แก้ไขข้อมูลประกาศสำคัญหน้าแรก")
        current_info = load_important_info()
        new_info_text = st.text_area("ข้อความที่จะแสดงในกล่องประกาศเด่นบนสุด (หน้าแรก):", value=current_info, height=120)
        if st.button("💾 บันทึกข้อความประกาศ"):
            save_important_info(new_info_text)
            st.success("อัปเดตประกาศสำเร็จ!")
            st.rerun()
            
        st.markdown("---")
        # ส่วนกรอกข้อมูลคลังวิดีโออื่นย่อยๆ 
        if "edit_index" not in st.session_state: st.session_state.edit_index = None
        col_form, col_manage = st.columns([1, 1.2])
        
        with col_form:
            if st.session_state.edit_index is not None:
                st.markdown(f"### 📝 แก้ไขรายการที่ {st.session_state.edit_index + 1}")
                curr = st.session_state.schedules[st.session_state.edit_index]
                d_title, d_link, d_note = curr["title"], curr["link"], curr["note"]
                d_pinned = bool(curr["pinned"]) if "pinned" in curr else False
                import datetime
                try: d_date = datetime.datetime.strptime(curr["date"], "%Y-%m-%d").date()
                except: d_date = datetime.date.today()
                options = ["Variety / TV", "Online Video / YouTube", "Event / Concert", "Radio / Podcast"]
                d_type_idx = options.index(curr["type"]) if curr["type"] in options else 0
                btn_txt = "🔄 อัปเดตข้อมูลที่แก้ไข"
            else:
                st.markdown("### ➕ เพิ่มคลิปรายการใหม่")
                d_title, d_link, d_note, d_pinned = "", "", "", False
                import datetime
                d_date = datetime.date.today()
                d_type_idx = 0
                btn_txt = "🚀 อัปโหลดขึ้นหน้าแรก"
                
            with st.form(key='admin_form_v4'):
                title = st.text_input("ชื่อรายการ / ชื่องานคลิป:", value=d_title)
                date_val = st.date_input("วันที่งาน:", value=d_date)
                w_type = st.selectbox("ประเภท:", ["Variety / TV", "Online Video / YouTube", "Event / Concert", "Radio / Podcast"], index=d_type_idx)
                link = st.text_input("ลิงก์คลิปวิดีโอปกติ:", value=d_link)
                note = st.text_area("โน้ตย่อความฟิน:", value=d_note)
                is_pinned = st.checkbox("📌 ปักหมุดคลิปนี้ไว้ในโซนแนะนำหน้าแรก", value=d_pinned)
                submit = st.form_submit_button(btn_txt)
                
            if submit:
                if not title.strip(): st.warning("กรุณากรอกชื่อด้วยครับ!")
                else:
                    item_data = {"title": title, "date": str(date_val), "type": w_type, "link": link, "note": note, "pinned": is_pinned}
                    if st.session_state.edit_index is not None:
                        st.session_state.schedules[st.session_state.edit_index] = item_data
                        st.session_state.edit_index = None
                    else: st.session_state.schedules.append(item_data)
                    save_data(st.session_state.schedules)
                    st.success("บันทึกสำเร็จ!")
                    st.rerun()
            if st.session_state.edit_index is not None:
                if st.button("❌ ยกเลิกแก้ไข"):
                    st.session_state.edit_index = None
                    st.rerun()
                    
        with col_manage:
            st.markdown("### 📋 จัดการข้อมูลคลังวิดีโอ")
            if not st.session_state.schedules: st.info("ไม่มีรายการในระบบ")
            else:
                for idx, item in enumerate(st.session_state.schedules):
                    st.markdown("<div style='border-top:1px solid #1e293b; margin-top:8px; padding-top:8px;'></div>", unsafe_allow_html=True)
                    c_txt, c_pin, c_edit, c_del = st.columns([2.2, 0.8, 0.6, 0.6])
                    is_p = item.get('pinned', False)
                    pin_status = "📌 ปักหมุดอยู่" if is_p else "◽ ทั่วไป"
                    with c_txt: st.write(f"**{idx+1}. {item['title']}**")
                    with c_pin:
                        if st.button(pin_status, key=f"quick_pin_{idx}"):
                            item['pinned'] = not is_p
                            save_data(st.session_state.schedules)
                            st.rerun()
                    with c_edit:
                        if st.button("📝", key=f"edit_{idx}"):
                            st.session_state.edit_index = idx
                            st.rerun()
                    with c_del:
                        if st.button("🗑️", key=f"del_{idx}"):
                            st.session_state.schedules.pop(idx)
                            save_data(st.session_state.schedules)
                            st.rerun()
    elif password_input != "":
        st.error("รหัสผ่านไม่ถูกต้อง")
