"""
Trang_chu.py — Điểm vào chính của ứng dụng (main entrypoint khi deploy Streamlit Cloud).
MENU CHA: TỔNG QUAN — dashboard tổng hợp toàn hệ thống.
Các MENU CHA khác nằm trong thư mục pages/ (Streamlit tự sinh sidebar điều hướng).
"""

import streamlit as st
import plotly.express as px
import pandas as pd

from database import init_db, read_table
from utils import require_login, sidebar_user_box, inject_css, style_chart, export_all_data_button

st.set_page_config(page_title="SHT/PBG — Hệ điều hành Sản xuất & Giá thành", page_icon="🏭", layout="wide")

init_db()
inject_css()
require_login()
sidebar_user_box()

with st.sidebar:
    st.markdown("### 📁 SHT/PBG")
    st.caption("Menu cha nằm ở danh sách trang phía trên. Menu con / SHEET / TAB nằm bên trong mỗi trang.")
    export_all_data_button()

st.title("🏭 SHT/PBG — Hệ điều hành Sản xuất & Giá thành")
st.caption("Bản 100% Python (Streamlit + SQLite) — không còn phụ thuộc Google Sheets/Docs.")

# ------------------------------------------------------------------
# SHEET: CHỈ SỐ TỔNG QUAN
# ------------------------------------------------------------------
suppliers = read_table("suppliers")
materials = read_table("materials")
products = read_table("products")
quotes = read_table("supplier_quotes")
bom = read_table("bom")
routing = read_table("routing")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Nhà cung cấp", len(suppliers))
c2.metric("Nguyên vật liệu", len(materials))
c3.metric("Sản phẩm", len(products))
c4.metric("Báo giá đã ghi nhận", len(quotes))
c5.metric("Công đoạn (routing)", len(routing))

st.divider()
st.markdown("#### 📊 Biểu đồ tổng quan hệ thống (tối thiểu 5 biểu đồ)")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["1️⃣ NVL theo NCC", "2️⃣ Giá NVL theo nhóm", "3️⃣ Top NCC", "4️⃣ Số công đoạn/SP", "5️⃣ Biến động báo giá", "6️⃣ Cơ cấu SP theo nhóm món"]
)

with tab1:
    if not materials.empty and not suppliers.empty:
        merged = materials.merge(suppliers, left_on="supplier_id", right_on="id", suffixes=("", "_ncc"))
        cnt = merged.groupby("name_ncc").size().reset_index(name="Số NVL")
        fig = px.bar(cnt, x="name_ncc", y="Số NVL", title="Số nguyên vật liệu theo từng nhà cung cấp", text="Số NVL")
        st.plotly_chart(style_chart(fig), use_container_width=True)
    else:
        st.info("Chưa có dữ liệu Nguyên vật liệu / Nhà cung cấp.")

with tab2:
    if not materials.empty:
        fig = px.box(materials, x="category", y="price", title="Phân bố đơn giá NVL theo nhóm ngành hàng", points="all")
        st.plotly_chart(style_chart(fig), use_container_width=True)
    else:
        st.info("Chưa có dữ liệu Nguyên vật liệu.")

with tab3:
    if not suppliers.empty:
        fig = px.bar(
            suppliers.sort_values("rating", ascending=False).head(10),
            x="name", y="rating", title="Top 10 nhà cung cấp theo điểm đánh giá", text="rating",
        )
        st.plotly_chart(style_chart(fig), use_container_width=True)
    else:
        st.info("Chưa có dữ liệu Nhà cung cấp.")

with tab4:
    if not routing.empty and not products.empty:
        merged = routing.merge(products, left_on="product_id", right_on="id", suffixes=("", "_sp"))
        cnt = merged.groupby("name_sp").size().reset_index(name="Số công đoạn")
        fig = px.pie(cnt, names="name_sp", values="Số công đoạn", title="Tỷ trọng số công đoạn theo từng sản phẩm")
        st.plotly_chart(style_chart(fig), use_container_width=True)
    else:
        st.info("Chưa có dữ liệu Routing / Sản phẩm.")

with tab5:
    if not quotes.empty:
        q = quotes.copy()
        q["quote_date"] = pd.to_datetime(q["quote_date"], errors="coerce")
        q = q.dropna(subset=["quote_date"]).sort_values("quote_date")
        if not q.empty:
            fig = px.line(q, x="quote_date", y="price", color="material_id", markers=True,
                           title="Biến động giá báo giá NCC theo thời gian")
            st.plotly_chart(style_chart(fig), use_container_width=True)
        else:
            st.info("Chưa có ngày báo giá hợp lệ.")
    else:
        st.info("Chưa có dữ liệu Báo giá NCC.")

with tab6:
    if not products.empty:
        cnt = products.groupby("dish_group").size().reset_index(name="Số sản phẩm")
        fig = px.treemap(cnt, path=["dish_group"], values="Số sản phẩm", title="Cơ cấu sản phẩm theo nhóm món")
        st.plotly_chart(style_chart(fig), use_container_width=True)
    else:
        st.info("Chưa có dữ liệu Sản phẩm.")

st.divider()
st.markdown(
    """
    ##### 🗂️ Điều hướng
    Dùng danh sách trang ở **sidebar bên trái** để vào từng **MENU CHA**:
    - 📦 Danh mục (Nhà cung cấp / Nguyên vật liệu / Sản phẩm)
    - 🏭 Sản xuất (BOM / Routing - Công đoạn)
    - 💰 Chi phí & Giá thành (Chi phí trực tiếp, gián tiếp, Engine tính giá thành ABC)
    - 📈 Báo giá NCC (so sánh giá, chọn NCC tốt nhất)
    """
)
