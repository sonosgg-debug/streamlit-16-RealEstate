import os
import datetime
import pandas as pd
import streamlit as st

import data_manager
import chart_builder

# 1. Page Configuration
st.set_page_config(
    page_title="부동산 vs 주식 투자 수익률 비교",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS styling (matching 00 Bookmarks design system)
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    
    /* Main Content Area - reduce top padding */
    .main .block-container,
    [data-testid="stMainBlockContainer"] {
        padding-top: 3.0rem !important;
        padding-bottom: 3.0rem !important;
        max-width: 1400px;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #1e293b !important;
        border-right: 1px solid #334155;
    }
    
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #f8fafc !important;
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Input fields & widgets styling */
    .stDateInput input {
        background-color: #334155 !important;
        color: #f8fafc !important;
        border: 1px solid #475569 !important;
        border-radius: 6px !important;
    }
    
    /* KPI Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #1e293b, #0f172a);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 14px 16px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s, border-color 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #38bdf8;
    }
    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #94a3b8;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
    }
    .metric-value {
        font-size: 1.35rem;
        font-weight: 800;
        line-height: 1.2;
    }
    .metric-sub {
        font-size: 0.75rem;
        color: #64748b;
        margin-top: 4px;
    }
    
    /* Info Box */
    .custom-info-box {
        background-color: rgba(30, 41, 59, 0.6);
        border: 1px solid #334155;
        border-left: 4px solid #38bdf8;
        border-radius: 6px;
        padding: 10px 14px;
        font-size: 0.85rem;
        color: #cbd5e1;
        margin-bottom: 16px;
    }

    /* Buttons styling */
    div.stButton > button {
        border-radius: 6px !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }

    /* Ensure sidebar has comfortable width */
    section[data-testid="stSidebar"] {
        min-width: 320px !important;
    }

    /* Reduce column gap in sidebar for quick select buttons */
    section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
        gap: 4px !important;
    }

    /* Sidebar Quick Select button horizontal layout fix */
    section[data-testid="stSidebar"] div.stButton > button {
        border-radius: 6px !important;
        font-weight: 700 !important;
        padding-left: 2px !important;
        padding-right: 2px !important;
        padding-top: 4px !important;
        padding-bottom: 4px !important;
        min-height: 36px !important;
        height: 36px !important;
        white-space: nowrap !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    /* Force text inside buttons to stay horizontal without wrapping */
    section[data-testid="stSidebar"] div.stButton > button p {
        white-space: nowrap !important;
        overflow: visible !important;
        font-size: 0.85rem !important;
        font-weight: 700 !important;
        line-height: 1 !important;
        margin: 0 !important;
        padding: 0 !important;
        display: inline-block !important;
    }

    /* =========================================================
       사이드바 접기(<<) 및 펼치기(>>) 버튼 항상 표시 및 시인성 강화
       ========================================================= */
    /* 1. 사이드바가 열려 있을 때 접기 버튼 (<<) 상시 표시 */
    [data-testid="stSidebarCollapseButton"] {
        visibility: visible !important;
        opacity: 1 !important;
        display: inline-flex !important;
    }
    
    [data-testid="stSidebarCollapseButton"] button {
        visibility: visible !important;
        opacity: 1 !important;
        color: #f8fafc !important;
        background-color: #334155 !important;
        border: 1px solid #475569 !important;
        border-radius: 8px !important;
        width: 36px !important;
        height: 36px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3) !important;
        transition: all 0.2s ease !important;
    }
    
    [data-testid="stSidebarCollapseButton"] button:hover {
        background-color: #38bdf8 !important;
        color: #0f172a !important;
        border-color: #38bdf8 !important;
    }

    /* 2. 사이드바 헤더 영역 패딩 및 정렬 보정 */
    [data-testid="stSidebarHeader"] {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
    }

    /* 3. 사이드바가 닫혔을 때 다시 여는 버튼 (>>) 시인성 강화 */
    [data-testid="stSidebarCollapsedControl"] {
        visibility: visible !important;
        opacity: 1 !important;
    }
    
    [data-testid="stSidebarCollapsedControl"] button {
        background-color: #1e293b !important;
        border: 1px solid #475569 !important;
        border-radius: 8px !important;
        color: #38bdf8 !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4) !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. Data Initialization
if 'df_combined' not in st.session_state or 'meta' not in st.session_state:
    with st.spinner("데이터 로딩 중..."):
        df_loaded, meta_loaded = data_manager.load_combined_data(force_update=False)
        st.session_state.df_combined = df_loaded
        st.session_state.meta = meta_loaded

df_combined = st.session_state.df_combined
meta = st.session_state.meta

if df_combined is None or df_combined.empty:
    st.error(meta.get("error", "데이터를 불러올 수 없습니다. KBData 폴더를 확인해 주세요."))
    st.stop()

# Determine valid date ranges from data
min_dt = df_combined.index[0].to_pydatetime().date() # 1986-01-01
# Last common real estate valid date
latest_kb_date = df_combined["강남11개구"].dropna().index[-1].to_pydatetime().date()
max_dt = latest_kb_date

# Date session state initialization (directly linked to widget keys)
if 'cal_start' not in st.session_state:
    st.session_state['cal_start'] = min_dt
if 'cal_end' not in st.session_state:
    st.session_state['cal_end'] = max_dt
if 'quick_select' not in st.session_state:
    st.session_state['quick_select'] = "MAX"

# Helper for Quick Select calculation
def apply_quick_select(choice):
    st.session_state['quick_select'] = choice
    end_d = max_dt
    if choice == "1Y":
        start_d = datetime.date(end_d.year - 1, end_d.month, 1)
    elif choice == "5Y":
        start_d = datetime.date(end_d.year - 5, end_d.month, 1)
    elif choice == "10Y":
        start_d = datetime.date(end_d.year - 10, end_d.month, 1)
    elif choice == "20Y":
        start_d = datetime.date(end_d.year - 20, end_d.month, 1)
    else: # MAX
        start_d = min_dt
        
    if start_d < min_dt:
        start_d = min_dt
        
    # Directly update session_state keys tied to st.date_input
    st.session_state['cal_start'] = start_d
    st.session_state['cal_end'] = end_d

# 4. Sidebar Controls
with st.sidebar:
    st.markdown("### ⚙️ 조회 설정")
    
    st.markdown("<p style='font-size: 0.9rem; font-weight: 600; margin-bottom: 5px; color: #cbd5e1;'>📅 조회 기간</p>", unsafe_allow_html=True)
    
    col_s, col_e = st.columns(2)
    with col_s:
        st.date_input(
            "시작일",
            key="cal_start",
            min_value=min_dt,
            max_value=max_dt
        )
    with col_e:
        st.date_input(
            "종료일",
            key="cal_end",
            min_value=min_dt,
            max_value=max_dt
        )

    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.9rem; font-weight: 600; margin-bottom: 6px; color: #cbd5e1;'>⚡ 빠른 선택</p>", unsafe_allow_html=True)
    
    # 5 quick select options: 1Y, 5Y, 10Y, 20Y, MAX
    q_cols = st.columns(5)
    options = ["1Y", "5Y", "10Y", "20Y", "MAX"]
    for idx, opt in enumerate(options):
        with q_cols[idx]:
            is_active = (st.session_state.get('quick_select') == opt)
            btn_type = "primary" if is_active else "secondary"
            st.button(
                opt,
                key=f"btn_quick_{opt}",
                type=btn_type,
                use_container_width=True,
                on_click=apply_quick_select,
                args=(opt,)
            )

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    
    # Buttons: Update & 조회
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        btn_update = st.button("🔄 Update", use_container_width=True, help="KBData 폴더의 최신 엑셀 및 주식 데이터를 재동기화합니다.")
    with btn_col2:
        btn_search = st.button("🔍 조회", type="primary", use_container_width=True, help="선택한 기간으로 차트를 새로고침합니다.")

    if btn_update:
        with st.spinner("최신 데이터 갱신 중..."):
            df_updated, meta_updated = data_manager.load_combined_data(force_update=True)
            if df_updated is not None:
                st.session_state.df_combined = df_updated
                st.session_state.meta = meta_updated
                st.success("데이터 갱신 완료!")
                st.rerun()
            else:
                st.error(meta_updated.get("error", "업데이트 실패"))
                
    if btn_search:
        # Reset quick_select indicator to custom if dates differ
        st.rerun()

    st.markdown("---")
    
    # Data Status & File Info
    st.markdown("<p style='font-size: 0.85rem; font-weight: 700; color: #94a3b8; margin-bottom: 6px;'>📁 데이터 소스 현황</p>", unsafe_allow_html=True)
    kb_name = meta.get("kb_file_name", "미상")
    kb_mtime = meta.get("kb_file_mtime", "-")
    start_str = meta.get("start_date", "-")
    end_str = meta.get("end_date", "-")
    
    st.markdown(f"""
    <div style='font-size: 0.8rem; color: #94a3b8; line-height: 1.5; background-color: #0f172a; padding: 10px; border-radius: 6px; border: 1px solid #334155;'>
        • <b>KB 파일</b>: <span style='color: #38bdf8;'>{kb_name}</span><br>
        • <b>갱신 일시</b>: {kb_mtime}<br>
        • <b>수집 범위</b>: {start_str} ~ {end_str}<br>
        • <b>주식 지수</b>: KOSPI, S&P 500 (월말 종가)
    </div>
    """, unsafe_allow_html=True)
    
    # File Uploader Dropzone for user convenience
    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.85rem; font-weight: 700; color: #94a3b8; margin-bottom: 4px;'>📤 새 KB 엑셀 업로드</p>", unsafe_allow_html=True)
    uploaded = st.file_uploader("새 파일 드롭", type=["xlsx", "xls"], label_visibility="collapsed")
    if uploaded is not None:
        ok, msg = data_manager.save_uploaded_kb_file(uploaded)
        if ok:
            st.success(msg)
            df_reloaded, meta_reloaded = data_manager.load_combined_data(force_update=False)
            st.session_state.df_combined = df_reloaded
            st.session_state.meta = meta_reloaded
            st.rerun()
        else:
            st.error(msg)

# 5. Main Content Area
# Title and Subtitle styled exactly like "00 Bookmarks"
st.markdown(
    "<h1 style='text-align: center; font-size: 1.8rem; font-weight: 800; line-height: 1.35; margin: 0 0 10px 0; color: #8AB4F8 !important;'>"
    "부동산 vs 주식 투자 수익률 비교"
    "</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "<div style='text-align: center; font-size: 0.9rem; color: #94a3b8; margin-bottom: 15px;'>"
    "KB부동산이 제공하는 '월간 아파트 매매가격지수'를 통해 부동산과 주식의 투자수익률을 비교합니다."
    "</div>",
    unsafe_allow_html=True
)
st.markdown("<hr style='border: 0; height: 1px; background-color: #334155; margin-bottom: 22px;'>", unsafe_allow_html=True)

# 6. Data Calculation for selected period
start_val = st.session_state.get('cal_start', min_dt)
end_val = st.session_state.get('cal_end', max_dt)

if start_val > end_val:
    st.warning("시작일이 종료일보다 늦을 수 없습니다. 기간을 다시 선택해 주세요.")
    st.stop()

df_returns, df_sliced, notes = chart_builder.calculate_returns(df_combined, start_val, end_val)
metrics_df = chart_builder.calculate_metrics(df_returns, df_sliced)

if df_returns is None or df_returns.empty:
    st.error("해당 기간의 데이터를 찾을 수 없습니다.")
    st.stop()

# Notice if any indicator starts later (e.g. 수도권 starts 1999-01)
if notes:
    notice_text = " • ".join(notes.values())
    st.markdown(f"<div class='custom-info-box'>ℹ️ {notice_text}</div>", unsafe_allow_html=True)

# 7. Summary Metric Cards (KPI)
st.markdown("<div style='margin-bottom: 12px; font-weight: 700; font-size: 1.05rem; color: #e2e8f0;'>📊 기간 누적 수익률 요약</div>", unsafe_allow_html=True)

kpi_cols = st.columns(6)
for idx, col_name in enumerate(chart_builder.COLOR_PALETTE.keys()):
    with kpi_cols[idx]:
        color = chart_builder.COLOR_PALETTE.get(col_name, "#ffffff")
        m_row = metrics_df[metrics_df["지표"] == col_name]
        
        if not m_row.empty:
            tot_ret = m_row["누적 수익률 (%)"].values[0]
            cagr_val = m_row["CAGR (연평균 %)"].values[0]
            sign = "+" if tot_ret > 0 else ""
            ret_color = "#f43f5e" if tot_ret > 0 else ("#38bdf8" if tot_ret < 0 else "#94a3b8")
            
            cagr_str = f"연평균 {cagr_val:.1f}%" if pd.notna(cagr_val) else "-"
            st.markdown(f"""
            <div class='metric-card' style='border-top: 3px solid {color};'>
                <div class='metric-label'>
                    <span style='display:inline-block; width:8px; height:8px; border-radius:50%; background-color:{color};'></span>
                    {col_name}
                </div>
                <div class='metric-value' style='color: {ret_color};'>
                    {sign}{tot_ret:,.1f}%
                </div>
                <div class='metric-sub'>{cagr_str}</div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

# 8. Interactive Plotly Line Chart
fig = chart_builder.build_comparison_chart(df_returns, df_sliced)
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True, 'responsive': True})

# 9. Statistical Comparison Table & CSV Download
st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📋 투자 성과 비교 분석표", "📥 원본/가공 데이터 보기"])

with tab1:
    if not metrics_df.empty:
        # Format metrics table for display
        df_disp = metrics_df.copy()
        
        # Highlight formatting
        def highlight_ret(val):
            if isinstance(val, (int, float)):
                if val > 0:
                    return 'color: #fca5a5; font-weight: 700;'
                elif val < 0:
                    return 'color: #93c5fd; font-weight: 700;'
            return ''

        formatted_df = df_disp.style.format({
            "시작 원본값": "{:,.2f}",
            "최종 원본값": "{:,.2f}",
            "누적 수익률 (%)": "{:+,.2f}%",
            "CAGR (연평균 %)": "{:+,.2f}%",
            "MDD (최대 낙폭 %)": "{:.2f}%",
            "월간 최대상승 (%)": "{:+,.2f}%",
            "월간 최대하락 (%)": "{:+,.2f}%",
        }).map(highlight_ret, subset=["누적 수익률 (%)", "CAGR (연평균 %)", "월간 최대상승 (%)", "월간 최대하락 (%)"])

        st.dataframe(formatted_df, use_container_width=True, hide_index=True)
        st.caption("※ CAGR(연평균 복리 수익률) 및 MDD(최대 낙폭)는 해당 자산의 장기 성장성과 리스크(변동성 방어력)를 평가하는 지표입니다.")

with tab2:
    st.markdown("<p style='font-size: 0.9rem; color: #cbd5e1;'>조회된 기간의 누적 수익률(%) 시계열 데이터입니다.</p>", unsafe_allow_html=True)
    
    df_download = df_returns.copy()
    df_download.index = df_download.index.strftime('%Y-%m')
    
    st.dataframe(df_download.style.format("{:+,.2f}%"), use_container_width=True)
    
    import io
    
    csv_data = df_download.to_csv(encoding="utf-8-sig")
    
    # Generate multi-sheet Excel in memory
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df_download.to_excel(writer, sheet_name="누적수익률(%)", index_label="기준월")
        if not metrics_df.empty:
            metrics_df.to_excel(writer, sheet_name="투자성과비교", index=False)
        df_raw_down = df_sliced.copy()
        df_raw_down.index = df_raw_down.index.strftime('%Y-%m')
        df_raw_down.to_excel(writer, sheet_name="원본지수종가", index_label="기준월")
    excel_data = excel_buffer.getvalue()

    d_col1, d_col2 = st.columns(2)
    with d_col1:
        st.download_button(
            label="📥 수익률 데이터 CSV 다운로드",
            data=csv_data,
            file_name=f"부동산_주식_수익률비교_{start_val.strftime('%Y%m')}_{end_val.strftime('%Y%m')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    with d_col2:
        st.download_button(
            label="📊 수익률 데이터 엑셀 다운로드",
            data=excel_data,
            file_name=f"부동산_주식_수익률비교_{start_val.strftime('%Y%m')}_{end_val.strftime('%Y%m')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
