import streamlit as st
import pandas as pd
import os
import re
from PIL import Image

# ตั้งค่าหน้า Streamlit
try:
    fav_icon = Image.open("images/pageicon.png")
except FileNotFoundError:
    fav_icon = "🎬"  # เผื่อไว้ในกรณีที่ระบบออนไลน์หาภาพไม่เจอชั่วคราว ให้ใช้อิโมจิแทนเพื่อไม่ให้เว็บพังครับ

# 2. ตั้งค่าหน้าเว็บโดยใส่รูปไอคอนที่โหลดมา
st.set_page_config(
    page_title="Artist Video Gallery",
    page_icon=fav_icon,  # ใช้ไฟล์รูปภาพ pageicon.png แทนอิโมจิแล้วครับ ✨
    layout="wide"        # หน้ากว้างสไตล์ YouTube Grid
)

DATA_FILE = "artist_schedules.csv"

# พาสเวิร์ดสำหรับแนทคนเดียวในการเข้าหน้า Admin (แก้ไขเปลี่ยนตรงนี้ได้เลยครับ)
ADMIN_PASSWORD = "nat_admin_secret"

# ฟังก์ชันดึง ID ของคลิป YouTube และดึงภาพหน้าปกอัตโนมัติ
def get_youtube_thumbnail(url):
    if not url or pd.isna(url):
        return None
    # ค้นหา Video ID จากลิงก์ YouTube แบบต่างๆ
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)'
        '([^&=%\?\{\s]+)'
    )
    match = re.search(youtube_regex, str(url))
    if match:
        video_id = match.group(4)
        # ใช้ลิงก์ดึงภาพหน้าปกความละเอียดสูง (hqdefault หรือ maxresdefault)
        return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
    return None

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['date'] = df['date'].astype(str)
        return df.to_dict('records')
    return []

def save_data(data):
    df = pd.DataFrame(data)
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

if "schedules" not in st.session_state:
    st.session_state.schedules = load_data()

# ตกแต่ง CSS ให้สไตล์เหมือนหน้าแรก YouTube ผสมสไตล์มินิมอล
st.markdown(
    """
    <style>
    /* ซ่อนขอบและเมนูด้านบนบางส่วนเพื่อให้ดูคลีน */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* สไตล์สำหรับการ์ดวิดีโอสไตล์ YouTube */
    .video-card {
        background-color: transparent;
        margin-bottom: 25px;
        transition: transform 0.2s;
    }
    .video-card:hover {
        transform: translateY(-4px);
    }
    .thumbnail-container {
        position: relative;
        width: 100%;
        padding-top: 56.25%; /* อัตราส่วน 16:9 มาตรฐานภาพวิดีโอ */
        overflow: hidden;
        border-radius: 12px;
        background-color: #1e1e1e;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    .thumbnail-img {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        object-fit: cover;
    }
    .video-title {
        font-size: 15px;
        font-weight: 600;
        line-height: 1.3;
        margin: 10px 0 4px 0;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        color: #f1f5f9;
    }
    .video-meta {
        font-size: 13px;
        color: #94a3b8;
    }
    .video-note {
        font-size: 12px;
        color: #a78bfa;
        margin-top: 4px;
        font-style: italic;
    }
    
    /* สไตล์ปุ่มลิงก์ */
    .watch-btn {
        display: inline-block;
        background-color: #ef4444; /* แดง YouTube */
        color: white !important;
        padding: 6px 14px;
        font-size: 12px;
        font-weight: bold;
        border-radius: 20px;
        text-decoration: none !important;
        margin-top: 8px;
    }
    .watch-btn:hover {
        background-color: #dc2626;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# เมนูเลือกหน้าตรง Sidebar ด้านซ้าย (แยกมุมมอง)
view_mode = st.sidebar.radio("มุมมองหน้าเว็บ", ["🏠 หน้าแรก (คลังวิดีโอศิลปิน)", "⚙️ ระบบหลังบ้าน (สำหรับแนท)"])

# ==========================================
# 🏠 หน้าแรก: แสดงคลังวิดีโอสไตล์ YouTube
# ==========================================
if view_mode == "🏠 หน้าแรก (คลังวิดีโอศิลปิน)":
    
    # ส่วนหัว Banner
    st.markdown("<h1 style='text-align: center; color: #ef4444;'>🎬 Artist Video Gallery</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8;'>รวมรายการ คลิปย้อนหลัง และผลงานทั้งหมดของศิลปินไว้ที่นี่</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)
    
    if not st.session_state.schedules:
        st.info("ยังไม่มีข้อมูลวิดีโอในคลัง ระบบกำลังรอข้อมูลอัปเดตจากผู้ดูแลระบบครับ")
    else:
        # ระบบค้นหาและตัวกรองแยกหมวดหมู่สไตล์ YouTube Tabs
        search_query = st.text_input("🔍 ค้นหาชื่อรายการหรือคำสำคัญ...", placeholder="พิมพ์คำที่ต้องการค้นหาที่นี่...")
        
        categories = ["ทั้งหมด", "Variety / TV", "Online Video / YouTube", "Event / Concert", "Radio / Podcast"]
        selected_category = st.tabs(categories)
        
        # จัดการข้อมูลทั้งหมด
        df_all = pd.DataFrame(st.session_state.schedules)
        df_all['date'] = pd.to_datetime(df_all['date'])
        df_all = df_all.sort_values(by='date', ascending=False) # เรียงล่าสุดขึ้นก่อน
        
        # คัดกรองคำค้นหา
        if search_query:
            df_all = df_all[df_all['title'].str.contains(search_query, case=False, na=False) | 
                            df_all['note'].str.contains(search_query, case=False, na=False)]
            
        # วนลูปสร้างคอนเทนต์ตามแต่ละแท็บหมวดหมู่
        for i, cat in enumerate(categories):
            with selected_category[i]:
                if cat == "ทั้งหมด":
                    df_filtered = df_all
                else:
                    df_filtered = df_all[df_all['type'] == cat]
                
                if df_filtered.empty:
                    st.write("<p style='color: #64748b; padding: 20px 0;'>ไม่พบวิดีโอในหมวดหมู่นี้</p>", unsafe_allow_html=True)
                else:
                    # สร้าง Grid แถวละ 4 คลิปแบบหน้าแรก YouTube
                    records = df_filtered.to_dict('records')
                    cols = st.columns(4)
                    
                    for idx, item in enumerate(records):
                        col_idx = idx % 4
                        with cols[col_idx]:
                            # ดึงรูปหน้าปกคลิป
                            thumb_url = get_youtube_thumbnail(item['link'])
                            if not thumb_url:
                                # ถ้าไม่ใช่ลิงก์ยูทูปหรือไม่มีภาพ ให้ใช้ภาพ Placeholder สีเทาน่ารักๆ แทน
                                thumb_url = "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=500&auto=format&fit=crop&q=60"
                            
                            formatted_date = pd.to_datetime(item['date']).strftime('%d %b %Y')
                            
                            # ประกอบเป็นการ์ดวิดีโอแสดงผล
                            card_html = f"""
                            <div class="video-card">
                                <div class="thumbnail-container">
                                    <img class="thumbnail-img" src="{thumb_url}" alt="thumbnail">
                                </div>
                                <div class="video-title">{item['title']}</div>
                                <div class="video-meta">📅 {formatted_date} • {item['type']}</div>
                            """
                            if item['note'] and not pd.isna(item['note']):
                                card_html += f'<div class="video-note">💬 {item["note"]}</div>'
                            if item['link'] and not pd.isna(item['link']):
                                card_html += f'<a class="watch-btn" href="{item["link"]}" target="_blank">▶ รับชมคลิป</a>'
                                
                            card_html += "</div>"
                            st.markdown(card_html, unsafe_allow_html=True)

# ==========================================
# ⚙️ หน้าสำหรับแนท: ระบบหลังบ้านเพิ่ม/ลบข้อมูล
# ==========================================
elif view_mode == "⚙️ ระบบหลังบ้าน (สำหรับแนท)":
    st.subheader("⚙️ ระบบจัดการข้อมูลหลังบ้าน")
    
    # เช็กพาสเวิร์ดป้องกันคนอื่นแอบเข้ามาเพิ่มข้อมูล
    password_input = st.text_input("กรุณาป้อนรหัสผ่านผู้ดูแลระบบ:", type="password")
    
    if password_input == ADMIN_PASSWORD:
        st.success("🔓 ยืนยันตัวตนสำเร็จ ยินดีต้อนรับครับแนท!")
        st.markdown("---")
        
        # แบ่งเป็นฟอร์มเพิ่มข้อมูล และ ตารางลบข้อมูล
        col_form, col_manage = st.columns([1, 1.2])
        
        with col_form:
            st.markdown("### ➕ เพิ่มรายการใหม่")
            with st.form(key='admin_schedule_form', clear_on_submit=True):
                title = st.text_input("ชื่อรายการ / ชื่อคลิปงาน:", placeholder="เช่น [VIIS] - 'Barbie' Performance @ Show DC")
                date_val = st.date_input("วันที่ออกอากาศ / ไปงาน:")
                work_type = st.selectbox("ประเภทหมวดหมู่:", ["Variety / TV", "Online Video / YouTube", "Event / Concert", "Radio / Podcast"])
                link = st.text_input("ลิงก์คลิปวิดีโอ (รองรับลิงก์ YouTube เพื่อดึงภาพปกอัตโนมัติ):", placeholder="https://www.youtube.com/watch?v=...")
                note = st.text_area("บันทึกเพิ่มเติม (ข้อความสั้นๆ รีวิวความฟิน):", placeholder="เช่น คอสตูมปังมาก, ร้องสดเพราะมาก!")
                
                submit_button = st.form_submit_button("อัปโหลดขึ้นหน้าแรก")

            if submit_button:
                if not title.strip():
                    st.warning("⚠️ กรุณากรอกชื่อรายการด้วยครับ!")
                else:
                    new_item = {
                        "title": title,
                        "date": str(date_val),
                        "type": work_type,
                        "link": link,
                        "note": note
                    }
                    st.session_state.schedules.append(new_item)
                    save_data(st.session_state.schedules)
                    st.success("🎉 อัปโหลดคลิปใหม่ขึ้นหน้าแรกเรียบร้อยแล้ว!")
                    st.rerun()
                    
        with col_manage:
            st.markdown("### 🗑️ จัดการและลบรายการ")
            if not st.session_state.schedules:
                st.info("ยังไม่มีข้อมูลรายการให้จัดการ")
            else:
                # แสดงข้อมูลแบบ DataFrame เพื่อให้กดดูภาพรวมและเลือกกดลบรายตัวได้ง่าย
                df_manage = pd.DataFrame(st.session_state.schedules)
                st.write("รายการทั้งหมดที่คุณอัปโหลดไว้:")
                
                # แสดงรายการพร้อมปุ่มลบแยกตามหัวข้อ
                for idx, item in enumerate(st.session_state.schedules):
                    with st.container():
                        col_text, col_del_btn = st.columns([4, 1])
                        with col_text:
                            st.write(f"**{item['title']}** ({item['date']})")
                        with col_del_btn:
                            if st.button("🗑️ ลบ", key=f"del_{idx}"):
                                st.session_state.schedules.pop(idx)
                                save_data(st.session_state.schedules)
                                st.success("ลบรายการแล้ว!")
                                st.rerun()
                                
        # ปุ่มล้างข้อมูลทั้งหมดในกรณีฉุกเฉินอยู่ที่ด้านล่างของ Sidebar
        if st.sidebar.button("🚨 ล้างคลังข้อมูลทั้งหมด"):
            if st.sidebar.checkbox("ฉันแน่ใจว่าจะล้างข้อมูลทั้งหมด"):
                st.session_state.schedules = []
                if os.path.exists(DATA_FILE):
                    os.remove(DATA_FILE)
                st.sidebar.success("ล้างข้อมูลเรียบร้อย!")
                st.rerun()
    
    elif password_input != "":
        st.error("❌ รหัสผ่านไม่ถูกต้อง กรุณาลองใหม่อีกครั้งครับแนท")
