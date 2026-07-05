import streamlit as st  # นำเข้าไลบรารี Streamlit สำหรับสร้างเว็บแอป
import pandas as pd     # ใช้จัดการข้อมูลตารางและการบันทึกไฟล์ CSV
import os               # ใช้สำหรับตรวจสอบที่อยู่ไฟล์
from PIL import Image   # ไลบรารีสำหรับจัดการรูปภาพ
import base64           # ไลบรารีสำหรับเข้ารหัสไฟล์เป็น base64

# ตั้งค่าหน้า Streamlit
fav_icon = Image.open("images/pageicon.png") 
st.set_page_config(
    page_title="Artist Schedule Tracker",
    page_icon=fav_icon,  # ดึงภาพจากโฟลเดอร์ images มาใช้เป็นไอคอน ✨
    layout="centered"
)

st.set_page_config(
    page_title="Artist Schedule Tracke",  # ชื่อหน้าเว็บ
    page_icon="✨",                         # ไอคอนแสดงบนแท็บเบราว์เซอร์
    layout="centered"                       # การจัดวางเนื้อหาให้อยู่ตรงกลางหน้าจอ
)

# ไฟล์สำหรับเก็บข้อมูลตารางงาน (อยู่ในโฟลเดอร์เดียวกับโค้ด)
DATA_FILE = "artist_schedules.csv"

# ฟังก์ชันโหลดข้อมูล
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        # แปลงคอลัมน์ date เป็นสตริงเพื่อความง่ายในการจัดการ
        df['date'] = df['date'].astype(str)
        return df.to_dict('records')
    return []

# ฟังก์ชันบันทึกข้อมูล
def save_data(data):
    df = pd.DataFrame(data)
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

# โหลดข้อมูลเข้าสู่ Session State ตอนเปิดแอปครั้งแรก
if "schedules" not in st.session_state:
    st.session_state.schedules = load_data()

# ส่วนหัวของแอปและการตกแต่ง UI (ใช้รูปภาพหัวเว็บเดิมของคุณ)
HEADER_IMAGE_PATH = "C:/Users/hp/Documents/Study/AI/headder.png" 

@st.cache_data  # cache ข้อมูลรูปภาพเพื่อไม่ให้โหลดซ้ำทุกครั้งที่มีการรีเฟรช
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return ""

header_image_base64 = get_base64_of_bin_file(HEADER_IMAGE_PATH)

# ปรับปรุงสไตล์ CSS ตามโครงสร้างเดิม เปลี่ยนโทนสีให้สดใสและเข้ากับศิลปิน
st.markdown(
    f"""
    <style>
    .header-container {{
        background-image: url("data:image/png;base64,{header_image_base64}");
        background-size: cover;
        background-position: center;
        padding: 50px 20px;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 30px;
        min-height: 180px;
    }}
    /* ปรับปรุงสีข้อความในช่อง input */
    .stTextInput>div>div>input, .stSelectbox>div>div>div {{
        background-color: #f8fafc;
        color: black !important;
    }}
    /* สไตล์ปุ่มกดอัปเดตงาน */
    .stButton>button {{
        background-color: #8B5CF6; /* สีม่วงสดใส */
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        border: none;
        font-size: 1em;
        width: 100%;
    }}
    .stButton>button:hover {{
        background-color: #7C3AED;
    }}
    /* สไตล์การ์ดแสดงรายการงาน */
    .schedule-card {{
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin-bottom: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
    /* สไตล์ Tag แยกประเภท */
    .badge {{
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75em;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 8px;
    }}
    .bg-tv {{ background-color: #DBEAFE; color: #1E40AF; border: 1px solid #BFDBFE; }}
    .bg-youtube {{ background-color: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5; }}
    .bg-concert {{ background-color: #F3E8FF; color: #6B21A8; border: 1px solid #E9D5FF; }}
    .bg-podcast {{ background-color: #FEF3C7; color: #92400E; border: 1px solid #FDE68A; }}
    </style>
    <div class="header-container">
    </div>
    """, 
    unsafe_allow_html=True
)

st.title("✨ My Artist Schedule Tracker")
st.write("บันทึกและติดตามคลังตารางงาน คลิปย้อนหลัง หรือรายการที่ศิลปินไปออก")

# แบ่งหน้าจอเป็น 2 ฝั่ง: ฝั่งซ้ายกรอกฟอร์ม / ฝั่งขวาแสดงรายการงาน
col_form, col_display = st.columns([1.2, 2])

with col_form:
    st.subheader("➕ เพิ่มรายการใหม่")
    
    with st.form(key='schedule_form', clear_on_submit=True):
        title = st.text_input("ชื่อรายการ / งาน:", placeholder="เช่น เจาะใจ, คอนเสิร์ต Open Air")
        date_val = st.date_input("วันที่ออกอากาศ / ไปงาน:")
        work_type = st.selectbox("ประเภทงาน:", ["Variety / TV", "Online Video / YouTube", "Event / Concert", "Radio / Podcast"])
        link = st.text_input("ลิงก์ (ถ้ามี):", placeholder="https://youtube.com/...")
        note = st.text_area("บันทึกเพิ่มเติม:", placeholder="เช่น หล่อมาก, เมนร้องไฮโน้ตสะใจ...")
        
        submit_button = st.form_submit_button("บันทึกตารางงาน")

    # Logic เมื่อกดบันทึก
    if submit_button:
        if not title.strip():
            st.warning("⚠️ กรุณากรอกชื่อรายการ!")
        else:
            new_item = {
                "title": title,
                "date": str(date_val),
                "type": work_type,
                "link": link,
                "note": note
            }
            # เพิ่มข้อมูลเข้าลิสต์และเซฟลงไฟล์
            st.session_state.schedules.append(new_item)
            save_data(st.session_state.schedules)
            st.success("🎉 บันทึกตารางงานสำเร็จ!")
            st.rerun()

with col_display:
    st.subheader(f"📋 รายการทั้งหมด ({len(st.session_state.schedules)} รายการ)")
    
    if not st.session_state.schedules:
        st.info("ยังไม่มีข้อมูลตารางงาน แอดรายการแรกของคุณที่ฟอร์มซ้ายมือได้เลย!")
    else:
        # เรียงลำดับวันที่ล่าสุดขึ้นก่อน
        sorted_schedules = sorted(st.session_state.schedules, key=lambda x: x['date'], reverse=True)
        
        # วนลูปแสดงผลรายการงาน
        for idx, item in enumerate(sorted_schedules):
            # เลือกคลาสสีตามประเภทงาน
            bg_class = "bg-tv"
            if "YouTube" in item['type']: bg_class = "bg-youtube"
            elif "Concert" in item['type']: bg_class = "bg-concert"
            elif "Podcast" in item['type']: bg_class = "bg-podcast"
            
            # สร้างกล่องแสดงตารางงานแบบ HTML Card
            card_html = f"""
            <div class="schedule-card">
                <div class="badge {bg_class}">{item['type']}</div>
                <span style="color: #94a3b8; font-size: 0.8em; float: right;">📅 {item['date']}</span>
                <h4 style="margin: 5px 0 10px 0; font-weight: bold; color: #1e293b;">{item['title']}</h4>
            """
            
            if item['note']:
                card_html += f'<p style="font-size: 0.85em; color: #64748b; background-color: #f8fafc; padding: 8px; border-radius: 6px; font-style: italic; margin-bottom: 8px;">💬 {item["note"]}</p>'
            
            if item['link']:
                card_html += f'<a href="{item["link"]}" target="_blank" style="font-size: 0.85em; color: #8B5CF6; text-decoration: none; font-weight: bold;">🔗 ลิงก์รับชม/รายละเอียด</a>'
                
            card_html += "</div>"
            st.markdown(card_html, unsafe_allow_html=True)

# เพิ่มปุ่มสำหรับล้างข้อมูลทั้งหมดที่ด้านล่างสุดของ Sidebar (เผื่อเคลียร์คิว)
if st.sidebar.button("🗑️ ล้างข้อมูลทั้งหมด"):
    if st.sidebar.checkbox("ยืนยันว่าจะลบข้อมูลทั้งหมดจริงๆ"):
        st.session_state.schedules = []
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        st.sidebar.success("ลบข้อมูลทั้งหมดแล้ว!")
        st.rerun()
