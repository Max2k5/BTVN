import streamlit as st
import sqlite3
import pandas as pd

# --- KHỞI TẠO CƠ SỞ DỮ LIỆU ---
def init_db():
    conn = sqlite3.connect("quiz_data.db")
    cursor = conn.cursor()
    # Bảng lưu câu hỏi
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            op1 TEXT, op2 TEXT, op3 TEXT, op4 TEXT,
            correct_ans TEXT
        )
    ''')
    # Bảng lưu kết quả học sinh
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_class TEXT,
            stt INTEGER,
            score REAL
        )
    ''')
    # Thêm câu hỏi mẫu nếu bảng trống
    cursor.execute("SELECT COUNT(*) FROM questions")
    if cursor.fetchone()[0] == 0:
        sample_questions = [
            (r"Cho tam giác ABC có các cạnh BC = a, CA = b, AB = c. Khẳng định nào sau đây là đúng?", 
             r"$a^2=b^2+c^2-2bc.cos(A)$", 
             r"$a^2=b^2+c^2+2bc.cos(A)$", 
             r"$a^2=b^2+c^2-bc.cos(A)$", 
             r"$b^2=a^2+c^2-2ac.cos(A)$", 
             r"$a^2=b^2+c^2-2bc.cos(A)$"),
            (r"Cho tam giác ABC có góc B bằng $60^o$, BC = 8 cm, AB = 5 cm. Tính độ dài cạnh AC.", 
             r"$AC=8$ cm", 
             r"$AC=\sqrt{129}$ cm", 
             r"$AC=7$ cm", 
             r"$AC=\sqrt{97}$ cm", 
             r"$AC=7$ cm"),
        ]
        cursor.executemany("INSERT INTO questions (question, op1, op2, op3, op4, correct_ans) VALUES (?, ?, ?, ?, ?, ?)", sample_questions)
    conn.commit()
    conn.close()

init_db()

# --- CÁC HÀM TƯƠNG TÁC CSDL ---
def get_db_connection():
    return sqlite3.connect("quiz_data.db")

# --- GIAO DIỆN CHÍNH ---
st.set_page_config(page_title="Trắc nghiệm lớp 10", layout="centered")
st.title("📝 Bài tập về nhà lớp 10")

# Thanh điều hướng bên trái (Sidebar) để chọn vai trò
role = st.sidebar.selectbox("Bạn là:", ["Học sinh", "Giáo viên (Quản trị)"])

# ---------------------------------------------------------
# MÀN HÌNH HỌC SINH
# ---------------------------------------------------------
if role == "Học sinh":
    st.header("✍️ Khu vực làm bài của Học sinh")
    
    # 1. Nhập thông tin định danh
    col1, col2 = st.columns(2)
    with col1:
        student_class = st.text_input("Nhập tên lớp (VD: 10A1, 11A2):").strip().upper()
    with col2:
        stt = st.number_input("Nhập Số thứ tự (STT) trong lớp:", min_value=1, max_value=100, step=1)

    if student_class:
        # Lấy danh sách câu hỏi từ DB
        conn = get_db_connection()
        df_ques = pd.read_sql_query("SELECT * FROM questions", conn)
        
        # Xem lịch sử làm bài và điểm trung bình hiện tại
        df_sub = pd.read_sql_query(f"SELECT score FROM submissions WHERE student_class='{student_class}' AND stt={stt}", conn)
        conn.close()
        
        if not df_sub.empty:
            avg_score = df_sub['score'].mean()
            st.info(f"💡 Bạn đã làm bài này **{len(df_sub)} lần**. Điểm trung bình hiện tại của bạn là: **{avg_score:.2f} điểm**.")
        else:
            st.write("👋 Đây là lần đầu tiên bạn làm bài này. Cố lên nhé!")

        if df_ques.empty:
            st.warning("Hiện tại chưa có câu hỏi nào trong hệ thống!")
        else:
            st.write("---")
            st.subheader("BÀI LÀM")
            
            # Tạo form để lưu câu trả lời mà không bị reload trang liên tục
            with st.form(key="quiz_form"):
                user_answers = {}
                for idx, row in df_ques.iterrows():
                    st.markdown(f"**Câu {idx+1}: {row['question']}**")
                    options = [row['op1'], row['op2'], row['op3'], row['op4']]
                    user_answers[row['id']] = st.radio(f"Chọn đáp án cho câu {idx+1}:", options, key=f"q_{row['id']}", label_visibility="collapsed")
                    st.write("")
                
                submit_button = st.form_submit_with_confidence = st.form_submit_button(label="🚀 Nộp bài")
            
            # Xử lý sau khi nhấn Nộp bài
            if submit_button:
                correct_count = 0
                total_questions = len(df_ques)
                
                for idx, row in df_ques.iterrows():
                    if user_answers[row['id']] == row['correct_ans']:
                        correct_count += 1
                
                # Tính điểm hệ 10
                score = (correct_count / total_questions) * 10
                
                # Lưu kết quả vào CSDL
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO submissions (student_class, stt, score) VALUES (?, ?, ?)", (student_class, stt, score))
                conn.commit()
                
                # Tính lại điểm trung bình mới
                df_sub_new = pd.read_sql_query(f"SELECT score FROM submissions WHERE student_class='{student_class}' AND stt={stt}", conn)
                conn.close()
                
                st.success(f"🎉 Bạn đã nộp bài thành công!")
                st.metric(label="Điểm lần này", value=f"{score:.2f} / 10")
                st.metric(label="Điểm trung bình mới", value=f"{df_sub_new['score'].mean():.2f} / 10")

# ---------------------------------------------------------
# MÀN HÌNH GIÁO VIÊN
# ---------------------------------------------------------
else:
    st.header("🔒 Khu vực quản lý của Giáo viên")
    
    # Cơ chế đăng nhập đơn giản
    password = st.text_input("Nhập mật khẩu quản trị:", type="password")
    if password == st.secrets["admin_password"]:  # Bạn có thể đổi mật khẩu ở đây
        st.success("Đăng nhập thành công!")
        
        tab1, tab2 = st.tabs(["📊 Xem kết quả học sinh", "⚙️ Quản lý câu hỏi"])
        
        with tab1:
            st.subheader("Danh sách bài làm của học sinh")
            conn = get_db_connection()
            # Lấy toàn bộ danh sách thô
            df_all = pd.read_sql_query("SELECT student_class AS 'Lớp', stt AS 'STT', score AS 'Điểm' FROM submissions", conn)
            
            if df_all.empty:
                st.write("Chưa có học sinh nào nộp bài.")
            else:
                # Tính điểm trung bình của từng học sinh bằng bảng pivot hoặc groupby
                df_report = df_all.groupby(['Lớp', 'STT']).agg(
                    Số_lần_làm=('Điểm', 'count'),
                    Điểm_trung_bình=('Điểm', 'mean')
                ).reset_index()
                
                st.markdown("**Bảng tổng hợp điểm trung bình cuối cùng:**")
                st.dataframe(df_report.style.format({"Điểm_trung_bình": "{:.2f}"}))
                
                st.markdown("**Chi tiết tất cả các lượt thử:**")
                st.dataframe(df_all)
            conn.close()
            
            st.write("---")
            st.subheader("🚨 Khu vực dọn dẹp dữ liệu")
            
            # Tạo nút bấm xóa toàn bộ lịch sử
            if st.button("🗑️ Xóa TOÀN BỘ lịch sử làm bài", type="secondary"):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM submissions")  # Lệnh xóa sạch bảng bài nộp
                conn.commit()
                conn.close()
                st.success("Đã xóa sạch toàn bộ lịch sử làm bài của học sinh!")
                st.rerun()  # Tải lại trang để cập nhật giao diện trống
            
        with tab2:
            st.subheader("Thêm câu hỏi mới")
            with st.form("add_question_form"):
                new_q = st.text_area("Nội dung câu hỏi:")
                op1 = st.text_input("Đáp án A:")
                op2 = st.text_input("Đáp án B:")
                op3 = st.text_input("Đáp án C:")
                op4 = st.text_input("Đáp án D:")
                correct_ans = st.selectbox("Đáp án đúng là:", [op1, op2, op3, op4], help="Chọn chuỗi trùng khớp hoàn toàn với 1 trong 4 đáp án trên")
                
                submit_q = st.form_submit_button("Thêm câu hỏi")
                
            if submit_q and new_q:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO questions (question, op1, op2, op3, op4, correct_ans) VALUES (?, ?, ?, ?, ?, ?)",
                    (new_q, op1, op2, op3, op4, correct_ans)
                )
                conn.commit()
                conn.close()
                st.success("Đã thêm câu hỏi thành công! Hãy F5 hoặc chuyển tab để cập nhật bài trắc nghiệm.")
    elif password != "":
        st.error("Sai mật khẩu! Vui lòng thử lại.")
