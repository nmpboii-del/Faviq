# ==========================================
# 🏠 หน้าแรกแกลเลอรี (ปรับปรุงการแสดงผลทุกหมวด)
# ==========================================
if view_mode == "🏠 หน้าแรกแกลเลอรี":
    st.markdown("<h2 style='color: #f8fafc; margin-bottom: 5px;'>🎬 Artist Hub & Fan Space</h2>", unsafe_allow_html=True)
    
    gifts_list = load_gifts()
    all_vids = load_data()
    df_vids = pd.DataFrame(all_vids).sort_values(by='date', ascending=False) if all_vids else pd.DataFrame()
    
    important_text = load_important_info()
    st.markdown(f'<div class="billboard-box"><h4 style="margin-top:0; color:#ef4444; font-size:15px;">📢 ประกาศและข้อมูลสำคัญ</h4><p style="margin-bottom:0; font-size:13px; white-space: pre-wrap;">{important_text}</p></div>', unsafe_allow_html=True)
    
    # ส่วนของ MV Focus
    mv_data = load_mv_highlight()
    st.markdown(f"### 🎵 PROJECT FOCUS: {mv_data['title']}")
    # ... (ส่วนแสดงผล MV ให้คงเดิมไว้ได้ครับ) ...
    st.markdown('</div>', unsafe_allow_html=True)

    # แสดง Digital Goods เฉพาะที่หน้าแรก (ถ้ามี)
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

    # ส่วนแสดงวิดีโอทุกหมวดหมู่ที่มีคลิป
    video_shelves = sys_config.get("video_shelves", [])
    for shelf in video_shelves:
        df_shelf = df_vids[df_vids['type'] == shelf['type']] if not df_vids.empty else pd.DataFrame()
        
        # ถ้าไม่มีคลิปในหมวดนี้ ไม่โชว์หัวข้อ
        if df_shelf.empty:
            continue
            
        st.markdown(f'<div class="yt-shelf-title">{shelf["title"]}</div>', unsafe_allow_html=True)
        
        # จัดการสถานะดูเพิ่มเติมแยกแต่ละหมวด
        s_key = f"expand_{shelf['type']}"
        if s_key not in st.session_state: st.session_state[s_key] = False
        
        shelf_records = df_shelf.to_dict('records')
        display_vids = shelf_records if st.session_state[s_key] else shelf_records[:4]
        
        # แสดงคลิปในแถว (Grid 4)
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
                            <div class="yt-video-meta">📅 {v_item["date"]}</div>
                        </div>
                    </div>
                </a>
                """, unsafe_allow_html=True)
        
        # ปุ่มดูเพิ่มเติม
        if len(shelf_records) > 4:
            if st.button("🔽 ดูเพิ่มเติม" if not st.session_state[s_key] else "🔼 ยุบแถว", key=f"btn_{s_key}"):
                st.session_state[s_key] = not st.session_state[s_key]
                st.rerun()
