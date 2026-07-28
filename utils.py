"""
utils.py — Hàm dùng chung cho toàn bộ app: xuất Excel, CSS giao diện,
khối "Menu con / SHEET / TAB" tái sử dụng được ở mọi trang.
"""

import io
import pandas as pd
import streamlit as st
import plotly.express as px

from database import read_table, read_query


# ------------------------------------------------------------------
# ĐĂNG NHẬP — gọi require_login() ở ĐẦU mỗi trang (kể cả trang trong pages/)
# ------------------------------------------------------------------
def require_login():
    if st.session_state.get("logged_in"):
        return True

    st.markdown("## 🔐 Đăng nhập hệ thống SHT/PBG")
    with st.form("login_form"):
        col1, col2 = st.columns(2)
        username = col1.text_input("Tên đăng nhập", key="login_user")
        password = col2.text_input("Mật khẩu", type="password", key="login_pass")
        submitted = st.form_submit_button("Đăng nhập", use_container_width=True)

    if submitted:
        df = read_query("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        if not df.empty:
            st.session_state["logged_in"] = True
            st.session_state["username"] = df.iloc[0]["username"]
            st.session_state["full_name"] = df.iloc[0]["full_name"]
            st.session_state["role"] = df.iloc[0]["role"]
            st.rerun()
        else:
            st.error("Sai tên đăng nhập hoặc mật khẩu.")

    st.caption("Tài khoản mặc định: **admin** / **admin123** (đổi lại trong trang Danh mục người dùng).")
    st.stop()


def sidebar_user_box():
    with st.sidebar:
        st.success(f"👤 {st.session_state.get('full_name', '')} ({st.session_state.get('role','')})")
        if st.button("🚪 Đăng xuất", use_container_width=True):
            for k in ["logged_in", "username", "full_name", "role"]:
                st.session_state.pop(k, None)
            st.rerun()
        st.divider()


# ------------------------------------------------------------------
# XUẤT EXCEL — dùng chung cho mọi trang, xuất nhiều sheet 1 lần
# ------------------------------------------------------------------
def export_excel_button(sheets: dict, file_name: str, label: str = "📥 Xuất Excel (.xlsx)"):
    """
    sheets: dict {"Tên sheet trong Excel": DataFrame}
    Hiển thị nút tải file .xlsx gồm nhiều sheet.
    """
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            safe_name = str(sheet_name)[:31]  # Excel giới hạn 31 ký tự/tên sheet
            (df if df is not None else pd.DataFrame()).to_excel(writer, sheet_name=safe_name, index=False)
    buffer.seek(0)
    st.download_button(
        label=label,
        data=buffer,
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )


def export_all_data_button():
    """Nút xuất TOÀN BỘ database ra 1 file Excel nhiều sheet — đặt ở sidebar."""
    tables = [
        "suppliers", "materials", "supplier_quotes", "products",
        "bom", "routing", "direct_costs", "indirect_costs", "labor_machine_hours",
        "customers", "contracts", "orders", "warehouse_tx",
    ]
    sheets = {t: read_table(t) for t in tables}
    export_excel_button(sheets, "sht_pbg_full_export.xlsx", "📥 Xuất TOÀN BỘ dữ liệu (Excel)")


# ------------------------------------------------------------------
# CSS / GIAO DIỆN CHUNG
# ------------------------------------------------------------------
def inject_css():
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.6rem; padding-bottom: 2.5rem;}
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg,#ffffff,#f4f7fb);
            border: 1px solid #e3e8ef;
            border-radius: 12px;
            padding: 14px 16px 10px 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        div[data-testid="stMetricLabel"] {font-weight:600; color:#4b5563;}
        .sheet-title {
            font-size: 1.05rem; font-weight: 700; color:#1f2d3d;
            border-left: 5px solid #2966B3; padding-left: 10px; margin: 6px 0 14px 0;
        }
        .menu-con-caption {color:#6b7280; font-size:0.85rem; margin-bottom:0.4rem;}
        button[data-baseweb="tab"] {font-weight:600;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def sheet_header(icon: str, title: str, subtitle: str = ""):
    """Tiêu đề chuẩn cho 1 SHEET (khối dữ liệu) trong Menu con."""
    st.markdown(f"<div class='sheet-title'>{icon} {title}</div>", unsafe_allow_html=True)
    if subtitle:
        st.caption(subtitle)


# ------------------------------------------------------------------
# BỘ MÀU DÙNG CHUNG CHO BIỂU ĐỒ (đồng bộ nhận diện toàn app)
# ------------------------------------------------------------------
PALETTE = ["#2966B3", "#249147", "#7A29A0", "#D97706", "#DC2626", "#0891B2", "#BE185D"]


def style_chart(fig, height=320):
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        height=height,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        colorway=PALETTE,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def empty_chart_placeholder(message="Chưa có dữ liệu để vẽ biểu đồ — hãy nhập liệu ở tab bên cạnh."):
    st.info(message)
