import streamlit as st  # นำเข้าไลบรารี Streamlit สำหรับสร้างเว็บแอป
import joblib           # ใช้สำหรับโหลดและบันทึกโมเดล machine learning ที่ฝึกไว้แล้ว
import numpy as np      # ไลบรารีสำหรับการคำนวณเชิงตัวเลข
import sklearn          # ไลบรารีสำหรับ machine learning 
from PIL import Image   # ไลบรารีสำหรับจัดการรูปภาพ
import base64           # ไลบรารีสำหรับเข้ารหัสไฟล์เป็น base64 เพื่อแปลงภาพเป็น string สำหรับ HTML

# ตั้งค่าหน้า Streamlit
st.set_page_config(
    page_title="Waste Type Classifier",  # ชื่อหน้าเว็บ
    page_icon="🗑️",                 # ไอคอนแสดงบนแท็บเบราว์เซอร์
    layout="centered"               # การจัดวางเนื้อหาให้อยู่ตรงกลางหน้าจอ
)

## โหลดโมเดลและ Vectorizer
st.sidebar.info(f"เวอร์ชัน scikit-learn ที่ใช้งาน: {sklearn.__version__}")  
# แสดงเวอร์ชันของ scikit-learn ที่ใช้ใน sidebar เพื่อให้ผู้ใช้ทราบ

try:
    model = joblib.load("waste_model.pkl")          # โหลดโมเดลจำแนกประเภทขยะที่บันทึกไว้
    vectorizer = joblib.load("vectorizer.pkl")      # โหลด Vectorizer สำหรับแปลงข้อความเป็นฟีเจอร์
    st.sidebar.success("✅ โหลดโมเดลและ Vectorizer สำเร็จ!")  # แจ้งเตือนว่าโหลดสำเร็จ
    
    if hasattr(vectorizer, 'vocabulary_'):          # ตรวจสอบว่า Vectorizer มี attribute 'vocabulary_'
        st.sidebar.info(f"Vectorizer คาดหวัง {len(vectorizer.vocabulary_)} features")  # แสดงจำนวนคำใน vocabulary
    else:
        st.sidebar.warning("Vectorizer ไม่มี attribute 'vocabulary_' ซึ่งอาจบ่งชี้ว่าไม่ได้ถูก fit มาอย่างสมบูรณ์")  
        # แจ้งเตือนกรณี Vectorizer อาจไม่ถูกฝึกก่อนบันทึก

except FileNotFoundError:
    st.error("❌ ไม่พบไฟล์โมเดลหรือ Vectorizer โปรดตรวจสอบว่า 'waste_model.pkl' และ 'vectorizer.pkl' อยู่ในโฟลเดอร์เดียวกัน")  
    # แจ้งข้อผิดพลาดหากไฟล์โมเดลหรือ Vectorizer ไม่พบในไดเรกทอรี
    st.stop()  # หยุดการทำงานของแอปในกรณีนี้
except Exception as e:
    st.error(f"❌ เกิดข้อผิดพลาดในการโหลดโมเดลหรือ Vectorizer: {e}")  # แจ้งข้อผิดพลาดอื่น ๆ ที่อาจเกิดขึ้น
    st.info("💡 ข้อผิดพลาดนี้อาจเกิดจากเวอร์ชัน scikit-learn ที่ไม่ตรงกัน หรือไฟล์เสียหาย")  # แนะนำสาเหตุ
    st.stop()  # หยุดการทำงานของแอป

CONFIDENCE_THRESHOLD = 0.3  # กำหนดค่าความมั่นใจต่ำสุดที่ยอมรับได้ในการจำแนกประเภท

# ส่วนหัวของแอปและการตกแต่ง UI
HEADER_IMAGE_PATH = "C:/Users/hp/Documents/Study/AI/headder.png" # กำหนดพาธรูปภาพส่วนหัวของแอป

@st.cache_data  # cache ข้อมูลรูปภาพเพื่อไม่ให้โหลดซ้ำทุกครั้งที่มีการรีเฟรช
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:  # เปิดไฟล์ภาพแบบไบนารี่
        data = f.read()              # อ่านข้อมูลไฟล์ทั้งหมด
    return base64.b64encode(data).decode()  # แปลงข้อมูลเป็น base64 แล้วแปลงเป็น string

header_image_base64 = get_base64_of_bin_file(HEADER_IMAGE_PATH)  # ดึงข้อมูลรูปภาพในรูปแบบ base64

# ใช้ markdown เพื่อใส่ CSS สำหรับตกแต่งหน้าเว็บ และแสดงภาพพื้นหลังส่วนหัวเป็น base64
st.markdown(
    f"""
    <style>
    .header-container {{
        background-image: url("data:image/png;base64,{header_image_base64}"); /* ตั้งภาพพื้นหลังเป็น base64 */
        background-size: cover;          /* ให้ภาพขยายเต็มพื้นที่ */
        background-position: center;    /* จัดภาพให้อยู่กึ่งกลาง */
        padding: 50px 20px;              /* กำหนดช่องว่างภายใน */
        border-radius: 10px;             /* มุมโค้งมน */
        text-align: center;              /* จัดข้อความกึ่งกลาง */
        color: white;                   /* สีข้อความขาว */
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.0); /* เงาข้อความ (ในที่นี้ใส่โปร่งใส) */
        margin-bottom: 30px;             /* เว้นช่องว่างด้านล่าง */
        position: relative; 
        overflow: hidden; 
        min-height: 200px;               /* ความสูงขั้นต่ำ */
    }}
    /* ปรับปรุงสีข้อความเป็นสีดำในช่อง input */
    .stTextInput>div>div>input {{
        background-color: #f0f2f6;       /* สีพื้นหลังช่อง input */
        padding: 10px;                   /* ช่องว่างภายในช่อง input */
        border-radius: 5px;              /* มุมโค้งมนของช่อง input */
        border: 1px solid #ccc;          /* เส้นขอบสีเทาอ่อน */
        color: black !important;         /* สีข้อความเป็นดำ แม้จะถูก override */
    }}
    .stButton>button {{
        background-color: #4CAF50;       /* สีปุ่มเป็นเขียว */
        color: white;                    /* สีข้อความปุ่มเป็นขาว */
        padding: 10px 20px;              /* ขนาดปุ่ม */
        border-radius: 5px;              /* มุมโค้งมนของปุ่ม */
        border: none;                   /* ไม่มีเส้นขอบ */
        font-size: 1.1em;               /* ขนาดฟอนต์ */
        cursor: pointer;                /* เปลี่ยนเคอร์เซอร์เมื่อชี้ */
    }}
    .stButton>button:hover {{
        background-color: #45a049;       /* สีปุ่มเมื่อ hover */
    }}
    .result-box {{
        padding: 20px;                   /* ช่องว่างภายในกล่องผลลัพธ์ */
        border-radius: 10px;             /* มุมโค้งมน */
        margin-top: 20px;                /* เว้นช่องว่างด้านบน */
        font-size: 1.2em;                /* ขนาดฟอนต์ */
        font-weight: bold;               /* ตัวหนา */
        color: white;                   /* สีข้อความขาว */
        text-align: center;              /* จัดข้อความกึ่งกลาง */
    }}
    .organic-bg {{ background-color: #339933; }} /* สีพื้นหลังเขียวสำหรับขยะอินทรีย์ */
    .recycle-bg {{ background-color: #ffcc00; }} /* สีพื้นหลังเหลืองสำหรับขยะรีไซเคิล */
    .hazardous-bg {{ background-color: #cc0000; }} /* สีพื้นหลังแดงสำหรับขยะอันตราย */
    .general-bg {{ background-color: #336699; }} /* สีพื้นหลังน้ำเงินสำหรับขยะทั่วไป */
    </style>
    <div class="header-container">
        </div>  <!-- ส่วนหัวมีภาพพื้นหลัง ไม่มีข้อความใดใน div นี้ -->
    """, 
    unsafe_allow_html=True  # อนุญาตให้ใส่ HTML/ CSS โดยตรงใน markdown
)

# แสดงข้อความชี้แนะให้ผู้ใช้ป้อนรายละเอียดขยะเพื่อจำแนกประเภท
st.write(
    "กรุณาป้อนรายละเอียดของขยะเพื่อทำการจำแนกประเภท "
    "ตัวอย่าง: ขวดพลาสติก, กระดาษหนังสือพิมพ์, เปลือกส้ม"
)

# ตรวจสอบว่า session state มีค่าเก็บข้อความอินพุตแล้วหรือไม่ ถ้ายังไม่มีตั้งเป็นค่าว่าง
if "waste_description_input" not in st.session_state:
    st.session_state.waste_description_input = ""

# Form Input
# สร้างฟอร์มให้ผู้ใช้กรอกคำอธิบายขยะและปุ่มส่งข้อมูล
with st.form(key='waste_classifier_form'):
    text_input = st.text_input("ป้อนคำอธิบายของขยะที่นี่:", key="waste_description_input")
    submit_button = st.form_submit_button("จำแนกประเภทขยะ")  # ปุ่มส่งฟอร์ม

# Logic การจำแนกและแสดงผลลัพธ์
if submit_button:  # เมื่อผู้ใช้กดปุ่มส่งฟอร์ม
    if not text_input.strip():  # ตรวจสอบว่ากรอกข้อความจริงหรือไม่ (ไม่ใช่แค่ช่องว่าง)
        st.warning("⚠️ กรุณาป้อนข้อมูลในช่องข้อความ!")  # แจ้งเตือนให้กรอกข้อมูล
    else:
        X = vectorizer.transform([text_input])  # แปลงข้อความเป็น feature vector ด้วย vectorizer
        
        st.sidebar.info(f"Input ที่ถูกแปลงมี {X.shape[1]} features")  # แสดงจำนวน features ของ input
        
        # ตรวจสอบว่า features ของ input ตรงกับที่โมเดลคาดหวังหรือไม่
        if hasattr(model, 'n_features_in_') and X.shape[1] != model.n_features_in_:
            st.error(f"❌ จำนวน Features ของ Input ({X.shape[1]}) ไม่ตรงกับที่ Model คาดหวัง ({model.n_features_in_})")
            st.info("💡 ปัญหานี้มักเกิดจากการที่ Vectorizer ที่ใช้โหลดมาไม่ตรงกับ Vectorizer ที่ใช้เทรนโมเดล")
            st.stop()  # หยุดการทำงานถ้าไม่ตรงกัน
        
        probs = model.predict_proba(X)[0]  # ทำนายความน่าจะเป็นของแต่ละคลาส
        max_prob = np.max(probs)            # ค่าความน่าจะเป็นสูงสุด
        predicted_label = model.classes_[np.argmax(probs)]  # คลาสที่โมเดลทำนาย
        
        st.markdown("---")  # เส้นแบ่ง
        
        if max_prob < CONFIDENCE_THRESHOLD:  # ถ้าค่าความมั่นใจต่ำกว่ากำหนด
            st.error("❌ ไม่ทราบประเภท กรุณาลองป้อนคำอธิบายขยะที่เฉพาะเจาะจงมากขึ้น")
        else:
            # กำหนดพาธรูปภาพ, คลาสสีพื้นหลัง และคำอธิบาย ตามผลการจำแนก
            image_path = ""
            bg_class = ""
            description_text = ""

            if predicted_label == "ขยะอินทรีย์":
                image_path = "C:/Users/hp/Documents/Study/AI/ถังขยะสีเขียว-Photoroom.png" 
                bg_class = "organic-bg"
                description_text = "🗑️ **ขยะอินทรีย์ / ขยะเปียก => ถังขยะสีเขียว:** คือขยะที่ย่อยสลายได้ตามธรรมชาติ เช่น เศษอาหาร ผัก ผลไม้ ใบไม้ กิ่งไม้ สามารถนำไปทำปุ๋ยหมักได้"
            elif predicted_label == "ขยะรีไซเคิล":
                image_path = "C:/Users/hp/Documents/Study/AI/ถังขยะสีเหลือง-Photoroom.png" 
                bg_class = "recycle-bg"
                description_text = "♻️ **ขยะรีไซเคิล => ถังขยะสีเหลือง:** คือขยะที่สามารถนำกลับมาใช้ใหม่ได้ เช่น ขวดพลาสติก แก้ว กระดาษ โลหะ ควรแยกประเภทและทำความสะอาดก่อนทิ้งเพื่อนำไปรีไซเคิล"
            elif predicted_label == "ขยะอันตราย":
                image_path = "C:/Users/hp/Documents/Study/AI/ถังขยะสีแดง-Photoroom.png" 
                bg_class = "hazardous-bg"
                description_text = "⚠️ **ขยะอันตราย / ขยะมีพิษ => ถังขยะสีแดง :** คือขยะที่มีสารพิษหรือเป็นอันตราย เช่น ถ่านไฟฉาย แบตเตอรี่ หลอดไฟ กระป๋องสเปรย์ สารเคมีต่างๆ ต้องทิ้งอย่างระมัดระวังและแยกจากขยะทั่วไป"
            elif predicted_label == "ขยะทั่วไป":
                image_path = "C:/Users/hp/Documents/Study/AI/ถังขยะสีน้ำเงิน-Photoroom.png" 
                bg_class = "general-bg"
                description_text = "🚮 **ขยะทั่วไป => ถังขยะสีน้ำเงิน:** คือขยะอื่นๆ ที่ไม่สามารถจัดอยู่ในประเภทข้างต้นได้ หรือเป็นขยะที่ย่อยสลายยากและไม่คุ้มค่ากับการรีไซเคิล เช่น ถุงพลาสติก ซองขนม โฟม ผ้าอ้อม"
            
            col1, col2 = st.columns([1, 3])  # แบ่งคอลัมน์แสดงภาพและข้อความผลลัพธ์
            with col1:
                if image_path:
                    try:
                        st.image(image_path, width=100)  # แสดงรูปภาพถังขยะที่เหมาะสม
                    except FileNotFoundError:
                        st.warning("รูปภาพถังขยะไม่พบ โปรดตรวจสอบพาธ")  # แจ้งเตือนถ้ารูปภาพไม่พบ
            with col2:
                # แสดงผลการจำแนกด้วยกล่องสีที่เหมาะสม
                st.markdown(f'<div class="result-box {bg_class}">ผลการจำแนก: **{predicted_label}**</div>', unsafe_allow_html=True)
            
            st.info(description_text)  # แสดงคำอธิบายเพิ่มเติมเกี่ยวกับประเภทขยะ

# รูปภาพให้ความรู้
st.markdown("---")  # เส้นแบ่ง
st.subheader("💡 การแยกขยะอย่างถูกวิธี เพื่อโลกที่ยั่งยืน 💡")  # หัวข้อย่อย
st.write("การแยกขยะตั้งแต่ต้นทางเป็นสิ่งสำคัญมากในการลดปริมาณขยะและช่วยให้กระบวนการรีไซเคิลมีประสิทธิภาพยิ่งขึ้น")  # ข้อความ
try:
    st.image("C:/Users/hp/Documents/Study/AI/b750b977276c911f043c478792890a36.jpg", use_container_width=True)  
    # แสดงรูปภาพให้ความรู้ กำหนดให้ขยายเต็มความกว้าง container
except FileNotFoundError:
    st.warning("ไม่พบรูปภาพ โปรดตรวจสอบว่าไฟล์อยู่ในโฟลเดอร์ที่ถูกต้องและตั้งชื่อถูกต้อง")  # แจ้งเตือนถ้ารูปภาพไม่พบ
