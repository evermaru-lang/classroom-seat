import streamlit as st
import pandas as pd
import time, threading

st.set_page_config(page_title="📱 교실 자리 실시간 티케팅", page_icon="🎟️", layout="wide")

# 서버 통합 공통 저장소
class ServerSharedState:
    def __init__(self):
        self.lock = threading.Lock()
        self.reserved_seats = {}
        self.pending_seats = {}
        self.pin = "0303"
        self.admin_pin = "ke1219"

    def get_data(self):
        with self.lock:
            now = time.time()
            expired = [s for s, (name, ts) in self.pending_seats.items() if now - ts > 30]
            for s in expired:
                del self.pending_seats[s]
            return dict(self.reserved_seats), dict(self.pending_seats)

    def try_pending(self, seat_num, student_name):
        with self.lock:
            now = time.time()
            expired = [s for s, (name, ts) in self.pending_seats.items() if now - ts > 30]
            for s in expired:
                del self.pending_seats[s]

            if seat_num in self.reserved_seats:
                return False, f"이미 [{self.reserved_seats[seat_num]}] 학생이 예매 완료한 좌석입니다."

            if seat_num in self.pending_seats:
                p_name, p_ts = self.pending_seats[seat_num]
                if p_name != student_name and (now - p_ts <= 30):
                    return False, f"다른 학생({p_name})이 이미 선점 중인 좌석입니다!"

            self.pending_seats[seat_num] = (student_name, now)
            return True, "선점 성공"

    def confirm_reservation(self, seat_num, student_name):
        with self.lock:
            self.reserved_seats[seat_num] = student_name
            if seat_num in self.pending_seats:
                del self.pending_seats[seat_num]

    def cancel_pending(self, seat_num, student_name):
        with self.lock:
            if seat_num in self.pending_seats and self.pending_seats[seat_num] == student_name:
                del self.pending_seats[seat_num]

    def reset_all(self):
        with self.lock:
            self.reserved_seats = {}
            self.pending_seats = {}

@st.cache_resource
def get_server_state():
    return ServerSharedState()

server_state = get_server_state()

# CSS 스타일링
st.markdown("""
<style>
    header[data-testid="stHeader"] { display: none !important; }
    .block-container { padding-top: 1rem !important; padding-bottom: 1.2rem !important; padding-left: 0.3rem !important; padding-right: 0.3rem !important; max-width: 920px !important; margin: 0 auto !important; }
    .main-title-box { text-align: center; background: linear-gradient(135deg, #1e293b, #0f172a); color: #ffffff !important; padding: 10px 6px; border-radius: 8px; font-size: 18px; font-weight: 800; margin-bottom: 10px; box-shadow: 0 3px 6px rgba(0,0,0,0.15); word-break: keep-all; }
    div[data-testid="stHorizontalBlock"], div[data-testid="stHorizontalBlock"]:has(> div) { display: grid !important; grid-template-columns: repeat(6, 1fr) !important; grid-auto-flow: row !important; gap: 3px !important; width: 100% !important; margin-bottom: 3px !important; }
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"], div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"], div[data-testid="column"], div[data-testid="stColumn"] { width: 100% !important; min-width: 0 !important; max-width: 100% !important; flex: none !important; padding: 0 !important; margin: 0 !important; }
    div[data-testid="stElementContainer"], div[data-testid="stButton"] { width: 100% !important; margin: 0 !important; padding: 0 !important; }
    .stButton > button, .fixed-seat-box { width: 100% !important; min-height: 48px !important; height: auto !important; padding: 2px 1px !important; margin: 0 !important; border-radius: 6px !important; display: flex !important; flex-direction: column !important; align-items: center !important; justify-content: center !important; line-height: 1.15 !important; white-space: pre-wrap !important; word-break: keep-all !important; font-size: 10.5px !important; font-weight: 800 !important; box-sizing: border-box !important; }
    .stButton > button *, .stButton > button p, .stButton > button div, .stButton > button span { color: #ffffff !important; font-size: 10.5px !important; font-weight: 800 !important; margin: 0 !important; padding: 0 !important; line-height: 1.15 !important; text-align: center !important; word-break: keep-all !important; display: block !important; }
    .stButton > button:not(:disabled) { background-color: #22c55e !important; color: #ffffff !important; border: 1.5px solid #16a34a !important; box-shadow: 0 1px 3px rgba(34, 197, 94, 0.25) !important; }
    .stButton > button:not(:disabled):hover { background-color: #16a34a !important; color: #ffffff !important; }
    .stButton > button:disabled { background-color: #ef4444 !important; color: #ffffff !important; border: 1.5px solid #dc2626 !important; opacity: 0.98 !important; }
    .fixed-seat-box { background-color: #6b7280 !important; color: #ffffff !important; border: 1.5px solid #4b5563 !important; text-align: center !important; font-size: 9.5px !important; line-height: 1.1 !important; }
    @media (min-width: 768px) {
        .block-container { padding-top: 1.5rem !important; padding-left: 1rem !important; padding-right: 1rem !important; }
        .main-title-box { font-size: 22px !important; padding: 12px 10px !important; margin-bottom: 14px !important; }
        div[data-testid="stHorizontalBlock"] { gap: 5px !important; margin-bottom: 5px !important; }
        .stButton > button, .fixed-seat-box { min-height: 62px !important; font-size: 14px !important; padding: 4px 2px !important; }
        .stButton > button *, .stButton > button p, .stButton > button div, .stButton > button span { font-size: 14px !important; line-height: 1.25 !important; }
        .fixed-seat-box { font-size: 12px !important; }
    }
    .notice-box { background-color: #f0fdf4; border: 1.5px solid #22c55e; border-radius: 8px; padding: 10px; margin-bottom: 10px; font-size: 11.5px; line-height: 1.45; }
    .notice-title { font-weight: bold; color: #15803d; font-size: 12.5px; margin-bottom: 4px; }
    .top-structure { background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 8px; display: flex; justify-content: space-between; align-items: center; font-size: 10.5px; font-weight: bold; color: #334155; margin-bottom: 6px; }
    .side-indicator { display: flex; justify-content: space-between; font-size: 10.5px; font-weight: bold; padding: 5px 8px; background: #e2e8f0; border-radius: 6px; margin-bottom: 8px; }
    .side-corridor { color: #334155; } .side-window { color: #0284c7; }
    .legend-box { display: flex; justify-content: space-around; background: #ffffff; border-radius: 6px; padding: 6px 4px; font-size: 10.5px; font-weight: bold; margin-bottom: 8px; border: 1.5px solid #e2e8f0; }
    .legend-item { display: flex; align-items: center; gap: 4px; }
    .dot { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }
    .dot-green { background-color: #22c55e; border: 1px solid #16a34a; }
    .dot-red { background-color: #ef4444; border: 1px solid #dc2626; }
    .dot-gray { background-color: #6b7280; border: 1px solid #4b5563; }
    .bottom-structure { margin-top: 10px; display: flex; flex-direction: column; gap: 5px; }
    .door-bottom { display: flex; justify-content: space-between; font-size: 10.5px; font-weight: bold; color: #475569; }
    .desk-row { display: flex; gap: 6px; }
    .teacher-desk { flex: 2; background: linear-gradient(135deg, #1e293b, #0f172a); color: #f8fafc; text-align: center; padding: 8px 4px; border-radius: 6px; font-size: 12px; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.15); }
    .assistant-desk { flex: 1; background: #e2e8f0; color: #334155; text-align: center; padding: 6px 2px; border-radius: 6px; font-size: 10px; font-weight: bold; border: 1px dashed #94a3b8; display: flex; align-items: center; justify-content: center; line-height: 1.15; }
</style>
""", unsafe_allow_html=True)

SEAT_GRID = [
    [None, "이동수업<br>책걸상", "5", "14", "20", "11"],
    ["이동수업<br>책걸상", "고정", "22", "6", "4", "26"],
    ["고정", "28", "24", "1", "13", "17"],
    ["19", "7", "2", "31", "16", "27"],
    ["25", "29", "18", "32", "10", "21"],
    ["9", "15", "30", "23", "33", "12"]
]

if 'my_pending_seat' not in st.session_state: st.session_state.my_pending_seat = None
if 'my_start_time' not in st.session_state: st.session_state.my_start_time = None

st.markdown('<div class="main-title-box">🎟️ 교실 자리 실시간 티케팅</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📱 좌석 선택 티케팅", "🔒 선생님 전용 관리자"])

with tab1:
    st.markdown("""
    <div class="notice-box">
        <div class="notice-title">📢 학생 실시간 티케팅 이용 수칙</div>
        1. <b>1인 1좌석 (본인 실명 사용)</b>: 타인 이름 도용 시 예매 무효 처리<br>
        2. <b>30초 제한시간 엄수</b>: 좌석 클릭 시 실시간 선점되며, 30초 내 [최종 확정] 누르기<br>
        3. <b>실시간 좌석 연동</b>: 다른 학생이 예매/선점 중인 좌석은 🔴 빨간색으로 자동 전환됩니다.
    </div>
    """, unsafe_allow_html=True)

    col_btn, col_info = st.columns()
    with col_btn:
        if st.button("🔄 좌석 현황 새로고침"):
            st.rerun()

    st.subheader("1️⃣ 학생 정보 입력")
    student_name = st.text_input("학생 이름 또는 번호:", placeholder="예: 10101 홍길동")
    input_pin = st.text_input("티케팅 인증번호:", type="password", placeholder="비밀번호 입력")
        
    st.markdown("---")
    st.subheader("2️⃣ 좌석 선택 (실시간 교실 배치도)")
    
    st.markdown('<div class="top-structure"><span>🚪 뒷문(복도)</span><span>🧍‍♂️ 스탠딩책상 ③②① (교실뒤)</span><span>🪟 창문</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="side-indicator"><span class="side-corridor">👈 🚪 복도 쪽</span><span class="side-window">🪟 창문 쪽 👉</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="legend-box"><div class="legend-item"><span class="dot dot-green"></span> 선택 가능 (초록)</div><div class="legend-item"><span class="dot dot-red"></span> 예매/선점중 (빨간)</div><div class="legend-item"><span class="dot dot-gray"></span> 이동/고정 (회색)</div></div>', unsafe_allow_html=True)
    
    reserved_seats, pending_seats = server_state.get_data()
    
    for row_idx, row in enumerate(SEAT_GRID):
        cols = st.columns(6)
        for col_idx, seat in enumerate(row):
            with cols[col_idx]:
                if seat is None:
                    st.write("")
                elif "이동수업" in seat or "고정" in seat:
                    st.markdown(f'<div class="fixed-seat-box">{seat}</div>', unsafe_allow_html=True)
                else:
                    seat_num = seat
                    if seat_num in reserved_seats:
                        occupant = reserved_seats[seat_num]
                        st.button(f"{seat_num}번\n[{occupant}]", key=f"seat_{seat_num}", disabled=True)
                    elif seat_num in pending_seats:
                        p_name, p_ts = pending_seats[seat_num]
                        if p_name == student_name.strip() and student_name.strip() != "":
                            st.button(f"{seat_num}번\n(내가선점)", key=f"seat_{seat_num}", disabled=True)
                        else:
                            st.button(f"{seat_num}번\n(선점중)", key=f"seat_{seat_num}", disabled=True)
                    else:
                        if st.button(f"{seat_num}번", key=f"seat_{seat_num}"):
                            if not student_name.strip():
                                st.error("⚠️ 이름을 먼저 입력해주세요!")
                            elif input_pin != server_state.pin:
                                st.error("⚠️ 인증번호가 올바르지 않습니다!")
                            elif student_name.strip() in reserved_seats.values():
                                st.warning(f"⚠️ '{student_name}'님은 이미 예매를 완료하셨습니다.")
                            else:
                                success, msg = server_state.try_pending(seat_num, student_name.strip())
                                if success:
                                    st.session_state.my_pending_seat = seat_num
                                    st.session_state.my_start_time = time.time()
                                    st.rerun()
                                else:
                                    st.error(f"⚠️ {msg}")

    st.markdown('<div class="bottom-structure"><div class="door-bottom"><span>🚪 앞문 (복도)</span><span>🪟 창문</span></div><div class="desk-row"><div class="teacher-desk">📺 교탁 / 칠판 (교실 앞쪽)</div><div class="assistant-desk">학습주도 이끌이<br>(보조) 책걸상</div></div></div>', unsafe_allow_html=True)

    if st.session_state.my_pending_seat:
        st.markdown("---")
        st.warning(f"⏱️ **[{st.session_state.my_pending_seat}번 좌석]** 선점 중! 30초 안에 확정해 주세요.")
        elapsed = time.time() - st.session_state.my_start_time
        remaining = max(0, int(30 - elapsed))
        st.progress(remaining / 30)
        st.write(f"⏳ 남은 시간: **{remaining}초**")
        
        if remaining > 0:
            if st.button("🎉 [최종 티케팅 확정하기]", type="primary"):
                server_state.confirm_reservation(st.session_state.my_pending_seat, student_name.strip())
                st.session_state.my_pending_seat = None
                st.session_state.my_start_time = None
                st.balloons()
                st.success("티케팅 성공! 서버에 즉시 등록되었습니다.")
                st.rerun()
            else:
                time.sleep(1)
                st.rerun()
        else:
            st.error("❌ 30초 시간이 초과되어 선점이 취소되었습니다.")
            server_state.cancel_pending(st.session_state.my_pending_seat, student_name.strip())
            if st.button("확인"):
                st.session_state.my_pending_seat = None
                st.session_state.my_start_time = None
                st.rerun()

with tab2:
    st.subheader("🔒 선생님 전용 관리자")
    admin_input = st.text_input("관리자 비밀번호를 입력하세요:", type="password", placeholder="비밀번호 입력")
    
    if admin_input == server_state.admin_pin:
        st.success("🔓 관리자 인증에 성공했습니다.")
        st.markdown("---")
        
        st.subheader("⚙️ 설정을 변경합니다")
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            new_pin = st.text_input("학생 인증번호 변경:", value=server_state.pin)
            if st.button("학생 인증번호 변경 저장"):
                server_state.pin = new_pin
                st.success("학생 인증번호가 변경되었습니다.")
        with c_p2:
            new_admin_pin = st.text_input("관리자 암호 변경:", value=server_state.admin_pin)
            if st.button("관리자 암호 변경 저장"):
                server_state.admin_pin = new_admin_pin
                st.success("관리자 암호가 변경되었습니다.")
                
        st.markdown("---")
        r_seats, p_seats = server_state.get_data()
        st.metric("현재 완료된 예매 현황", f"{len(r_seats)} / 31석")
        if r_seats:
            df = pd.DataFrame(list(r_seats.items()), columns=["좌석번호", "학생이름"])
            st.dataframe(df, use_container_width=True)
            st.download_button("📥 결과 엑셀(CSV) 다운로드", df.to_csv(index=False, encoding='utf-8-sig'), "seat_result.csv")
            
        if st.button("🔄 전체 예약 및 선점 초기화"):
            server_state.reset_all()
            st.session_state.my_pending_seat = None
            st.success("모든 예약 정보가 초기화되었습니다.")
            st.rerun()
    elif admin_input != "":
        st.error("❌ 관리자 비밀번호가 틀렸습니다.")
    else:
        st.info("🔑 선생님 전용 비밀번호를 입력해야 결과 확인 및 관리가 가능합니다.")
