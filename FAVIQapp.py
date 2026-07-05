import streamlit as st
import pandas as pd
import os
import re

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
MV_FILE = "mv_highlight.csv"  # ไฟล์ใหม่สำหรับเก็บข้อมูลลิงก์ MV ไฮไลท์และเป้าหมายยอดวิว

# รหัสผ่านหลังบ้านของแนท
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

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['date'] = df['date'].astype(str)
        if 'pinned' not in df.columns:
            df['pinned'] = False
        else:
            df['pinned'] = df['pinned'].astype(bool)
        return df.to_dict('records')
    return []

def save_data(data):
    df = pd.DataFrame(data)
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

def load_important_info():
    if os.path.exists(INFO_FILE):
        with open(INFO_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return "💡 ยินดีต้อนรับสู่คลังวิดีโอศิลปิน! (ยังไม่มีประกาศสำคัญในขณะนี้)"

def save_important_info(text):
    with open(INFO_FILE, "w", encoding="utf-8") as f:
        f.write(text)

# ฟังก์ชันโหลดและบันทึกข้อมูล MV ไฮไลท์หน้าแรก
def load_mv_highlight():
    if os.path.exists(MV_FILE):
        try:
            df = pd.read_csv(MV_FILE)
            return df.to_dict('records')[0]
        except:
            pass
    return {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "current_views": 100000,
        "target_views": 1000000,
        "title": "ตัวอย่างเพลงหลักของศิลปิน"
    }

def save_mv_highlight(url, current_views, target_views, title):
    df = pd.DataFrame([{
        "url": url,
        "current_views": int(current_views),
        "target_views": int(target_views),
        "title": title
    }])
    df.to_csv(MV_FILE, index=False, encoding='utf-8-sig')

if "schedules" not in st.session_state:
    st.session_state.schedules = load_data()

# ตกแต่งสไตล์ CSS เพิ่มเติม
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* บิลบอร์ดกล่องประกาศสำคัญ */
    .billboard-box {
        background: linear-gradient(135deg, #1e1b4b 0%, #2e1065 100%);
        border-left: 6px solid #c084fc;
        padding: 20px;
        border-radius: 14px;
        color: #f1f5f9;
        margin-bottom: 25px;
    }
    
    /* กล่องแดชบอร์ดจัดแถว MV ไฮไลท์พิเศษ */
    .mv-dashboard-box {
        background-color: #0b0f19;
        border: 2px solid #38bdf8;
        border-radius: 18px;
        padding: 20px;
        margin-bottom: 30px;
        box-shadow: 0 4px 20px rgba(56, 189, 248, 0.15);
    }
    
    /* วิดีโอการ์ดทั่วไป */
    .video-card {
        background-color: #0f172a;
        padding: 12px;
        border-radius: 14px;
        border: 1px solid #1e293b;
        margin-bottom: 25px;
        transition: transform 0.2s;
    }
    .video-card:hover {
        transform: translateY(-4px);
        border-color: #38bdf8;
    }
    
    .thumbnail-container {
        position: relative;
        width: 100%;
        padding-top: 56.25%;
        overflow: hidden;
        border-radius: 10px;
    }
    .thumbnail-img {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        object-fit: cover;
    }
    .video-title {
        font-size: 15px;
        font-weight: 600;
        margin: 12px 0 6px 0;
        color: #f8fafc;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .video-meta {
        font-size: 12px;
        color: #94a3b8;
    }
    .watch-btn {
        display: inline-block;
        background-color: #ef4444;
        color: white !important;
        padding: 6px 16px;
        font-size: 12px;
        font-weight: bold;
        border-radius: 20px;
        text-decoration: none !important;
        margin-top: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ระบบเปลี่ยนหน้ามุมมอง
view_mode = st.sidebar.radio("เมนูนำทาง", ["🏠 หน้าแรกแกลเลอรี", "⚙️ ระบบหลังบ้าน (สำหรับแนท)"])

# ==========================================
# 🏠 หน้าแรกแกลเลอรีวิดีโอและกระดานข้อมูล
# ==========================================
if view_mode == "🏠 หน้าแรกแกลเลอรี":
    st.markdown("<h1 style='text-align: center; color: #38bdf8;'>⭐ Artist Hub & Video Gallery</h1>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color: #1e293b;'>", unsafe_allow_html=True)
    
    # 1. ส่วนข้อมูลสำคัญ (ประกาศหน้าร้าน)
    important_text = load_important_info()
    st.markdown(f"""
    <div class="billboard-box">
        <h3 style="margin-top:0; color:#c084fc; font-size:17px;">📢 ประกาศและข้อมูลสำคัญจากแอดมิน</h3>
        <p style="margin-bottom:0; font-size:15px; white-space: pre-wrap;">{important_text}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. 🎯 ส่วนแผงนับวิวและตัวเล่น MV ใหม่ล่าสุด (แยกจากปักหมุด)
    mv_data = load_mv_highlight()
    st.markdown(f"### 🎵 PROJECT FOCUS: {mv_data['title']}")
    
    # สร้างกล่อง Dashboard ครอบตัวเล่นและแถบสถิติความสำเร็จ
    st.markdown('<div class="mv-dashboard-box">', unsafe_allow_html=True)
    col_mv_player, col_mv_milestone = st.columns([1.3, 1])
    
    with col_mv_player:
        yt_id = extract_youtube_id(mv_data['url'])
        if yt_id:
            # ฝังเครื่องเล่นวิดีโอตัวเต็มของ YouTube (นับยอดวิวเรียลไทม์แท้ๆ จากตรงนี้ได้เลย)
            st.video(f"https://www.youtube.com/watch?v={yt_id}")
        else:
            st.error("ลิงก์เพลงหลักที่กรอกไว้ไม่ถูกต้อง กรุณาเปลี่ยนลิงก์ในหน้าหลังบ้านครับ")
            
    with col_mv_milestone:
        st.markdown("<h4 style='color: #38bdf8; margin-top:0;'>📊 สถิติและเป้าหมายยอดวิว</h4>", unsafe_allow_html=True)
        
        c_views = mv_data['current_views']
        t_views = mv_data['target_views']
        
        # คำนวณความสำเร็จเป็นเปอร์เซ็นต์
        progress_ratio = min(float(c_views / t_views), 1.0)
        progress_percent = progress_ratio * 100
        
        # โชว์ข้อมูลความคืบหน้าด้วย UI ที่เด่นชัด
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric(label="📈 ยอดวิวล่าสุดในระบบ", value=f"{c_views:,} วิว")
        with col_m2:
            st.metric(label="🎯 เป้าหมายขั้นต่อไป", value=f"{t_views:,} วิว")
            
        # สร้างแถบความคืบหน้าความสำเร็จ (Progress Bar)
        st.markdown(f"**🔥 ความสำเร็จของโปรเจกต์: {progress_percent:.2f}%**")
        st.progress(progress_ratio)
        
        st.markdown(
            f"""
            <div style="background-color: #1e293b; padding: 12px; border-radius: 10px; margin-top: 15px; border-left: 4px solid #38bdf8;">
                <span style="font-size: 13px; color: #cbd5e1;">
                    💡 <b>ร่วมด้วยช่วยกัน:</b> แฟนๆ ทุกคนสามารถเพิ่มยอดวิวแท้จริงได้โดยตรง โดยการกดเปิดฟังเพลงที่ตัวเล่นวิดีโอซ้ายมือได้เลยน้า มาร่วมทำภารกิจให้สำเร็จไปด้วยกัน!
                </span>
            </div>
            """, 
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True) # ปิดกล่อง Dashboard
    
    # 3. ส่วนคลิปปักหมุดทั่วไป (Pinned Sectionเดิม)
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

        # 4. คลังผลงานปกติแยกหมวดหมู่
        st.markdown("### 🎬 คลังผลงานทั้งหมด")
        search_query = st.text_input("🔍 ค้นหาคลิปรายการ...", placeholder="พิมพ์คำค้นหา...")
        
        categories = ["วิดีโอทั้งหมด", "Variety / TV", "Online Video / YouTube", "Event / Concert", "Radio / Podcast"]
        selected_tabs = st.tabs(categories)
        
        df_display = df_all.sort_values(by='date', ascending=False)
        if search_query:
            df_display = df_display[df_display['title'].str.contains(search_query, case=False, na=False) | 
                                    df_display['note'].str.contains(search_query, case=False, na=False)]
            
        for i, cat in enumerate(categories):
            with selected_tabs[i]:
                df_cat = df_display if cat == "วิดีโอทั้งหมด" else df_display[df_display['type'] == cat]
                if df_cat.empty:
                    st.caption("ไม่มีวิดีโอในหมวดหมู่นี้")
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
                            if item['note'] and not pd.isna(item['note']):
                                card_html += f'<div style="font-size:12px; color:#94a3b8; font-style:italic; margin-top:4px;">💬 {item["note"]}</div>'
                            if item['link'] and not pd.isna(item['link']):
                                card_html += f'<a class="watch-btn" href="{item["link"]}" target="_blank">▶ ชมคลิป</a>'
                            card_html += "</div>"
                            st.markdown(card_html, unsafe_allow_html=True)
    else:
        st.info("คลังวิดีโอยังไม่มีข้อมูล")

# ==========================================
# ⚙️ ระบบหลังบ้านจัดการข้อมูล (สำหรับแนท)
# ==========================================
elif view_mode == "⚙️ ระบบหลังบ้าน (สำหรับแนท)":
    st.subheader("⚙️ ระบบจัดการข้อมูลหลังบ้าน")
    password_input = st.text_input("กรุณาป้อนรหัสผ่านผู้ดูแลระบบ:", type="password")
    
    if password_input == ADMIN_PASSWORD:
        st.success("🔓 ยืนยันตัวตนสำเร็จ! ยินดีต้อนรับกลับครับแนท")
        st.markdown("---")
        
        # ส่วนควบคุมที่ 1: จัดการเปลี่ยนเพลงหลัก MV โฟกัส ยอดวิวเป้าหมาย (แนทกดแก้อัพเดทได้เลย)
        st.markdown("### 🎯 ตั้งค่าเพลงหลัก / MV ใหม่ล่าสุดที่ต้องการโฟกัส")
        curr_mv = load_mv_highlight()
        
        with st.form(key="mv_highlight_form"):
            mv_title_in = st.text_input("ชื่อหัวข้อโปรเจกต์/ชื่อเพลง:", value=curr_mv['title'], placeholder="เช่น [MV] เพลงคัมแบ็คล่าสุด - ร้องโดยศิลปิน")
            mv_url_in = st.text_input("ลิงก์วิดีโอ YouTube ของ MV:", value=curr_mv['url'], placeholder="https://www.youtube.com/watch?v=...")
            
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                mv_current_in = st.number_input("อัปเดตยอดวิวล่าสุดในระบบ (ตัวเลข):", value=int(curr_mv['current_views']), step=1000)
            with col_v2:
                mv_target_in = st.number_input("ตั้งเป้าหมายยอดวิวความสำเร็จ (ตัวเลข):", value=int(curr_mv['target_views']), step=1000)
                
            mv_submit = st.form_submit_button("💾 อัปเดตเพลงโปรเจกต์หลักบนหน้าแรก")
            
        if mv_submit:
            save_mv_highlight(mv_url_in, mv_current_in, mv_target_in, mv_title_in)
            st.success("เปลี่ยนเพลงโปรเจกต์และเป้าหมายเรียบร้อยแล้ว!")
            st.rerun()
            
        st.markdown("---")
        
        # ส่วนควบคุมที่ 2: บอร์ดประกาศข้อมูลสำคัญหน้าแรก (ถอด rows=3 ออกแล้วตามที่แก้รอบก่อน)
        st.markdown("### 📝 แก้ไขข้อมูลประกาศสำคัญหน้าแรก")
        current_info = load_important_info()
        new_info_text = st.text_area("ข้อความที่จะแสดงในกล่องประกาศเด่นบนสุด (หน้าแรก):", value=current_info, height=120)
        if st.button("💾 บันทึกข้อความประกาศ"):
            save_important_info(new_info_text)
            st.success("อัปเดตประกาศหน้าแรกสำเร็จ!")
            st.rerun()
            
        st.markdown("---")
        
        # ส่วนควบคุมที่ 3: ระบบคลังวิดีโอ (กรอกฟอร์มเพิ่ม/ลบ/แก้ไข)
        if "edit_index" not in st.session_state:
            st.session_state.edit_index = None
            
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
                
            with st.form(key='admin_form_v3'):
                title = st.text_input("ชื่อรายการ / ชื่องานคลิป:", value=d_title)
                date_val = st.date_input("วันที่งาน:", value=d_date)
                w_type = st.selectbox("ประเภท:", ["Variety / TV", "Online Video / YouTube", "Event / Concert", "Radio / Podcast"], index=d_type_idx)
                link = st.text_input("ลิงก์คลิปวิดีโอปกติ:", value=d_link)
                note = st.text_area("โน้ตย่อความฟิน:", value=d_note)
                is_pinned = st.checkbox("📌 ปักหมุดคลิปนี้ไว้ในโซนแนะนำหน้าแรก", value=d_pinned)
                
                submit = st.form_submit_button(btn_txt)
                
            if submit:
                if not title.strip():
                    st.warning("กรุณากรอกชื่อด้วยครับ!")
                else:
                    item_data = {"title": title, "date": str(date_val), "type": w_type, "link": link, "note": note, "pinned": is_pinned}
                    if st.session_state.edit_index is not None:
                        st.session_state.schedules[st.session_state.edit_index] = item_data
                        st.session_state.edit_index = None
                    else:
                        st.session_state.schedules.append(item_data)
                    save_data(st.session_state.schedules)
                    st.success("บันทึกคลังวิดีโอสำเร็จ!")
                    st.rerun()
                    
            if st.session_state.edit_index is not None:
                if st.button("❌ ยกเลิกแก้ไข"):
                    st.session_state.edit_index = None
                    st.rerun()
                    
        with col_manage:
            st.markdown("### 📋 จัดการข้อมูลคลังวิดีโอ")
            if not st.session_state.schedules:
                st.info("ไม่มีรายการในระบบ")
            else:
                for idx, item in enumerate(st.session_state.schedules):
                    st.markdown("<div style='border-top:1px solid #1e293b; margin-top:8px; padding-top:8px;'></div>", unsafe_allow_html=True)
                    c_txt, c_pin, c_edit, c_del = st.columns([2.2, 0.8, 0.6, 0.6])
                    
                    is_p = item.get('pinned', False)
                    pin_status = "📌 ปักหมุดอยู่" if is_p else "◽ ทั่วไป"
                    
                    with c_txt:
                        st.write(f"**{idx+1}. {item['title']}**")
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
