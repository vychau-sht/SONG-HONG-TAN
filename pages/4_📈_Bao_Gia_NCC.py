"""
MENU CHA: 📈 BÁO GIÁ NCC
MENU CON: Nhập báo giá | 📊 So sánh & Xếp hạng (thay thế tính năng cốt lõi cũ trong Apps Script:
tự động chọn giá thấp nhất / nhì / ba và tô màu xanh lá / tím / xanh dương).
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from database import init_db, read_table, insert_row, delete_row, now_str
from utils import require_login, sidebar_user_box, inject_css, sheet_header, style_chart, export_excel_button, empty_chart_placeholder

st.set_page_config(page_title="Báo giá NCC — SHT/PBG", page_icon="📈", layout="wide")
init_db()
inject_css()
require_login()
sidebar_user_box()

st.title("📈 BÁO GIÁ NHÀ CUNG CẤP")

suppliers = read_table("suppliers")
materials = read_table("materials")
quotes = read_table("supplier_quotes", order_by="quote_date DESC")

menu_con = st.tabs(["📝 Nhập báo giá", "🏆 So sánh & Xếp hạng", "📊 Biểu đồ"])

# ====================================================================
# MENU CON 1: NHẬP BÁO GIÁ  (SHEET)
# ====================================================================
with menu_con[0]:
    sheet_header("📝", "SHEET: Nhập báo giá NCC", "Mỗi lần 1 NCC báo giá 1 NVL — hệ thống lưu lại toàn bộ lịch sử")
    tab_list, tab_form = st.tabs(["📋 Danh sách", "➕ Nhập liệu"])

    with tab_list:
        view = quotes.copy()
        if not quotes.empty:
            view = quotes.merge(suppliers[["id", "name"]], left_on="supplier_id", right_on="id", suffixes=("", "_ncc")) \
                          .merge(materials[["id", "name"]], left_on="material_id", right_on="id", suffixes=("", "_nvl"))
        st.dataframe(view, use_container_width=True, hide_index=True)
        export_excel_button({"Bao_gia_NCC": view}, "bao_gia_ncc.xlsx")
        if not quotes.empty:
            st.markdown("###### 🗑️ Xoá 1 lượt báo giá")
            sel_id = st.selectbox("Chọn theo id", quotes["id"], key="bg_sel")
            if st.button("🗑️ Xoá", key="bg_del"):
                delete_row("supplier_quotes", int(sel_id))
                st.warning("Đã xoá.")
                st.rerun()

    with tab_form:
        st.markdown("###### ➕ Ghi nhận báo giá mới (dùng phím Tab để chuyển ô)")
        supplier_opts = suppliers[["id", "name"]].values.tolist() if not suppliers.empty else []
        material_opts = materials[["id", "name"]].values.tolist() if not materials.empty else []
        if not supplier_opts or not material_opts:
            st.warning("Cần có ít nhất 1 Nhà cung cấp và 1 Nguyên vật liệu trước (vào 📦 Danh mục để thêm).")
        else:
            with st.form("form_quote", clear_on_submit=True):
                c1, c2 = st.columns(2)
                supplier_choice = c1.selectbox("Nhà cung cấp *", [f"{s[0]} - {s[1]}" for s in supplier_opts])
                material_choice = c2.selectbox("Nguyên vật liệu *", [f"{m[0]} - {m[1]}" for m in material_opts])
                c3, c4 = st.columns(2)
                price = c3.number_input("Mức giá báo (đ) *", min_value=0.0, value=0.0)
                quote_date = c4.date_input("Ngày báo giá")
                note = st.text_input("Ghi chú")
                submitted = st.form_submit_button("💾 Lưu báo giá", use_container_width=True)
            if submitted:
                if price <= 0:
                    st.error("Mức giá phải lớn hơn 0.")
                else:
                    insert_row("supplier_quotes", {
                        "supplier_id": int(supplier_choice.split(" - ")[0]),
                        "material_id": int(material_choice.split(" - ")[0]),
                        "price": price, "quote_date": str(quote_date), "note": note, "created_at": now_str(),
                    })
                    st.success("Đã lưu báo giá.")
                    st.rerun()

# ====================================================================
# MENU CON 2: SO SÁNH & XẾP HẠNG  (SHEET) — tính năng lõi cốt lõi gốc
# ====================================================================
with menu_con[1]:
    sheet_header("🏆", "SHEET: So sánh & Xếp hạng giá theo NVL",
                 "🟢 Giá thấp nhất — được chọn  |  🟣 Giá thấp nhì — dự phòng  |  🔵 Giá thấp ba — tiến triển")

    if quotes.empty:
        st.info("Chưa có báo giá nào — hãy nhập ở tab '📝 Nhập báo giá'.")
    else:
        merged = quotes.merge(suppliers[["id", "name"]], left_on="supplier_id", right_on="id", suffixes=("", "_ncc")) \
                        .merge(materials[["id", "name"]], left_on="material_id", right_on="id", suffixes=("", "_nvl"))

        # Chỉ lấy báo giá MỚI NHẤT của mỗi (NCC, NVL) để so sánh — giống logic Apps Script gốc
        latest = merged.sort_values("quote_date").groupby(["material_id", "supplier_id"]).tail(1)

        results = []
        for mat_id, grp in latest.groupby("material_id"):
            sorted_grp = grp.sort_values("price").reset_index(drop=True)
            for rank, row in sorted_grp.iterrows():
                hang = rank + 1
                mau = {1: "🟢", 2: "🟣", 3: "🔵"}.get(hang, "⚪")
                results.append({
                    "Nguyên vật liệu": row["name_nvl"], "Nhà cung cấp": row["name_ncc"],
                    "Mức giá": row["price"], "Hạng": f"{mau} #{hang}", "Ngày báo giá": row["quote_date"],
                })
        rank_df = pd.DataFrame(results)

        def highlight_rank(row):
            if "#1" in row["Hạng"]:
                return ["background-color:#249147; color:white"] * len(row)
            if "#2" in row["Hạng"]:
                return ["background-color:#7A29A0; color:white"] * len(row)
            if "#3" in row["Hạng"]:
                return ["background-color:#2966B3; color:white"] * len(row)
            return [""] * len(row)

        st.dataframe(rank_df.style.apply(highlight_rank, axis=1), use_container_width=True, hide_index=True)
        export_excel_button({"Xep_hang_gia": rank_df}, "xep_hang_gia_ncc.xlsx")

# ====================================================================
# MENU CON 3: BIỂU ĐỒ
# ====================================================================
with menu_con[2]:
    sheet_header("📊", "SHEET: Biểu đồ phân tích báo giá NCC")
    if quotes.empty:
        empty_chart_placeholder()
    else:
        merged = quotes.merge(suppliers[["id", "name"]], left_on="supplier_id", right_on="id", suffixes=("", "_ncc")) \
                        .merge(materials[["id", "name"]], left_on="material_id", right_on="id", suffixes=("", "_nvl"))
        merged["quote_date_dt"] = pd.to_datetime(merged["quote_date"], errors="coerce")

        g1, g2 = st.columns(2)
        with g1:
            fig1 = px.line(merged.sort_values("quote_date_dt"), x="quote_date_dt", y="price", color="name_nvl",
                            markers=True, title="① Biến động giá theo thời gian (từng NVL)")
            st.plotly_chart(style_chart(fig1), use_container_width=True)
        with g2:
            fig2 = px.box(merged, x="name_ncc", y="price", title="② Phân bố mức giá báo theo từng NCC")
            st.plotly_chart(style_chart(fig2), use_container_width=True)

        g3, g4 = st.columns(2)
        with g3:
            cnt = merged.groupby("name_ncc").size().reset_index(name="Số lượt báo giá")
            fig3 = px.bar(cnt.sort_values("Số lượt báo giá", ascending=False), x="name_ncc", y="Số lượt báo giá",
                           title="③ Số lượt báo giá theo từng NCC")
            st.plotly_chart(style_chart(fig3), use_container_width=True)
        with g4:
            avg_price = merged.groupby("name_nvl")["price"].mean().reset_index()
            fig4 = px.bar(avg_price.sort_values("price", ascending=False).head(15), x="name_nvl", y="price",
                           title="④ Top 15 NVL có giá báo trung bình cao nhất")
            st.plotly_chart(style_chart(fig4), use_container_width=True)

        fig5 = px.scatter(merged, x="quote_date_dt", y="price", color="name_ncc", size="price",
                           hover_name="name_nvl", title="⑤ Toàn cảnh báo giá: Thời gian vs Mức giá vs NCC")
        st.plotly_chart(style_chart(fig5, height=420), use_container_width=True)
