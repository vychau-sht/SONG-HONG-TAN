"""
MENU CHA: 📦 KHO VẬN
MENU CON: Nhập/Xuất kho | 📊 Tồn kho hiện tại
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from database import init_db, read_table, insert_row, delete_row
from utils import require_login, sidebar_user_box, inject_css, sheet_header, style_chart, export_excel_button, empty_chart_placeholder

st.set_page_config(page_title="Kho vận — SHT/PBG", page_icon="📦", layout="wide")
init_db()
inject_css()
require_login()
sidebar_user_box()

st.title("📦 KHO VẬN")

materials = read_table("materials")
tx = read_table("warehouse_tx", order_by="tx_date DESC")

menu_con = st.tabs(["🔄 Nhập/Xuất kho", "📊 Tồn kho hiện tại"])

# ====================================================================
# MENU CON 1: NHẬP/XUẤT KHO  (SHEET)
# ====================================================================
with menu_con[0]:
    sheet_header("🔄", "SHEET: Nhập/Xuất kho", "Ghi nhận từng lượt nhập hoặc xuất nguyên vật liệu")
    tab_list, tab_form, tab_chart = st.tabs(["📋 Danh sách", "➕ Nhập liệu", "📊 Biểu đồ"])

    view = tx.copy()
    if not tx.empty and not materials.empty:
        view = tx.merge(materials[["id", "name", "unit"]], left_on="material_id", right_on="id", suffixes=("", "_nvl"))

    with tab_list:
        st.dataframe(view, use_container_width=True, hide_index=True)
        export_excel_button({"Nhap_xuat_kho": view}, "nhap_xuat_kho.xlsx")
        if not tx.empty:
            st.markdown("###### 🗑️ Xoá 1 giao dịch")
            sel_id = st.selectbox("Chọn theo id", tx["id"], key="tx_sel")
            if st.button("🗑️ Xoá", key="tx_del"):
                delete_row("warehouse_tx", int(sel_id))
                st.warning("Đã xoá.")
                st.rerun()

    with tab_form:
        st.markdown("###### ➕ Ghi nhận giao dịch kho mới (dùng phím Tab để chuyển ô)")
        material_opts = materials[["id", "name"]].values.tolist() if not materials.empty else []
        if not material_opts:
            st.warning("Cần có ít nhất 1 Nguyên vật liệu trước (📦 Danh mục).")
        else:
            with st.form("form_tx", clear_on_submit=True):
                c1, c2 = st.columns(2)
                material_choice = c1.selectbox("Nguyên vật liệu *", [f"{m[0]} - {m[1]}" for m in material_opts])
                tx_type = c2.selectbox("Loại giao dịch *", ["Nhập", "Xuất"])
                c3, c4 = st.columns(2)
                qty = c3.number_input("Số lượng *", min_value=0.0, value=0.0)
                tx_date = c4.date_input("Ngày giao dịch")
                c5, c6 = st.columns(2)
                reference = c5.text_input("Chứng từ tham chiếu (số PO, đơn hàng...)")
                keeper = c6.text_input("Thủ kho / người ghi nhận")
                note = st.text_input("Ghi chú")
                submitted = st.form_submit_button("💾 Lưu vào cơ sở dữ liệu", use_container_width=True)
            if submitted:
                if qty <= 0:
                    st.error("Số lượng phải lớn hơn 0.")
                else:
                    insert_row("warehouse_tx", {
                        "material_id": int(material_choice.split(" - ")[0]), "tx_type": tx_type, "qty": qty,
                        "tx_date": str(tx_date), "reference": reference, "keeper": keeper, "note": note,
                    })
                    st.success("Đã lưu giao dịch kho.")
                    st.rerun()

    with tab_chart:
        if view.empty:
            empty_chart_placeholder()
        else:
            v = view.copy()
            v["tx_date_dt"] = pd.to_datetime(v["tx_date"], errors="coerce")

            g1, g2 = st.columns(2)
            with g1:
                fig1 = px.bar(v.groupby(["name", "tx_type"])["qty"].sum().reset_index(),
                               x="name", y="qty", color="tx_type", title="① Số lượng Nhập/Xuất theo NVL", barmode="group")
                st.plotly_chart(style_chart(fig1), use_container_width=True)
            with g2:
                cnt = v.groupby("tx_type")["qty"].sum().reset_index()
                fig2 = px.pie(cnt, names="tx_type", values="qty", title="② Tỷ trọng tổng khối lượng Nhập vs Xuất")
                st.plotly_chart(style_chart(fig2), use_container_width=True)

            g3, g4 = st.columns(2)
            with g3:
                trend = v.groupby([v["tx_date_dt"].dt.date, "tx_type"])["qty"].sum().reset_index()
                fig3 = px.line(trend, x="tx_date_dt", y="qty", color="tx_type", markers=True,
                                title="③ Xu hướng Nhập/Xuất kho theo thời gian")
                st.plotly_chart(style_chart(fig3), use_container_width=True)
            with g4:
                cnt2 = v.groupby("keeper").size().reset_index(name="Số giao dịch")
                fig4 = px.bar(cnt2.sort_values("Số giao dịch", ascending=False), x="keeper", y="Số giao dịch",
                               title="④ Số giao dịch theo thủ kho")
                st.plotly_chart(style_chart(fig4), use_container_width=True)

            fig5 = px.box(v, x="tx_type", y="qty", title="⑤ Phân bố số lượng mỗi lượt Nhập/Xuất")
            st.plotly_chart(style_chart(fig5, height=420), use_container_width=True)

# ====================================================================
# MENU CON 2: TỒN KHO HIỆN TẠI  (SHEET, tính từ Nhập-Xuất)
# ====================================================================
with menu_con[1]:
    sheet_header("📊", "SHEET: Tồn kho hiện tại", "Tồn = Tổng Nhập − Tổng Xuất, so với Tồn kho tối thiểu đã khai báo")
    tab_summary, tab_chart = st.tabs(["📋 Bảng tồn kho", "📊 Biểu đồ"])

    if tx.empty or materials.empty:
        with tab_summary:
            empty_chart_placeholder("Chưa đủ dữ liệu Nhập/Xuất kho để tính tồn.")
        with tab_chart:
            empty_chart_placeholder("Chưa đủ dữ liệu Nhập/Xuất kho để tính tồn.")
    else:
        pivot = tx.pivot_table(index="material_id", columns="tx_type", values="qty", aggfunc="sum", fill_value=0).reset_index()
        if "Nhập" not in pivot.columns:
            pivot["Nhập"] = 0
        if "Xuất" not in pivot.columns:
            pivot["Xuất"] = 0
        pivot["Tồn hiện tại"] = pivot["Nhập"] - pivot["Xuất"]
        stock = pivot.merge(materials[["id", "name", "unit", "min_stock"]], left_on="material_id", right_on="id")
        stock["Cảnh báo"] = stock.apply(lambda r: "⚠️ Dưới mức tối thiểu" if r["Tồn hiện tại"] < r["min_stock"] else "✅ Ổn định", axis=1)

        with tab_summary:
            st.dataframe(
                stock[["name", "unit", "Nhập", "Xuất", "Tồn hiện tại", "min_stock", "Cảnh báo"]],
                use_container_width=True, hide_index=True,
            )
            export_excel_button({"Ton_kho": stock}, "ton_kho_hien_tai.xlsx")

        with tab_chart:
            g1, g2 = st.columns(2)
            with g1:
                fig1 = px.bar(stock.sort_values("Tồn hiện tại", ascending=False), x="name", y="Tồn hiện tại",
                               color="Cảnh báo", title="① Tồn kho hiện tại theo NVL")
                st.plotly_chart(style_chart(fig1), use_container_width=True)
            with g2:
                cnt = stock.groupby("Cảnh báo").size().reset_index(name="Số NVL")
                fig2 = px.pie(cnt, names="Cảnh báo", values="Số NVL", title="② Tỷ lệ NVL dưới mức tồn kho tối thiểu")
                st.plotly_chart(style_chart(fig2), use_container_width=True)

            g3, g4 = st.columns(2)
            with g3:
                fig3 = px.bar(stock, x="name", y=["Nhập", "Xuất"], title="③ Tổng Nhập vs Xuất theo NVL", barmode="group")
                st.plotly_chart(style_chart(fig3), use_container_width=True)
            with g4:
                fig4 = px.scatter(stock, x="min_stock", y="Tồn hiện tại", color="Cảnh báo", size="Tồn hiện tại",
                                   hover_name="name", title="④ Tương quan Tồn tối thiểu vs Tồn hiện tại")
                st.plotly_chart(style_chart(fig4), use_container_width=True)

            fig5 = px.bar(stock.sort_values("Tồn hiện tại").head(15), x="Tồn hiện tại", y="name", orientation="h",
                           title="⑤ 15 NVL có tồn kho thấp nhất — ưu tiên nhập bổ sung")
            st.plotly_chart(style_chart(fig5, height=420), use_container_width=True)
