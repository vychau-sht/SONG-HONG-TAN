"""
MENU CHA: 📦 DANH MỤC
MENU CON (tab lớn): Nhà cung cấp | Nguyên vật liệu | Sản phẩm
Mỗi Menu con là 1 SHEET, bên trong có TAB: 📋 Danh sách | ➕ Nhập liệu | 📊 Biểu đồ
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from database import init_db, read_table, insert_row, update_row, delete_row, now_str
from utils import require_login, sidebar_user_box, inject_css, sheet_header, style_chart, export_excel_button, empty_chart_placeholder

st.set_page_config(page_title="Danh mục — SHT/PBG", page_icon="📦", layout="wide")
init_db()
inject_css()
require_login()
sidebar_user_box()

st.title("📦 DANH MỤC (Master Data)")

menu_con = st.tabs(["🚚 Nhà cung cấp", "🧪 Nguyên vật liệu", "🍽️ Sản phẩm"])

# ====================================================================
# MENU CON 1: NHÀ CUNG CẤP  (SHEET)
# ====================================================================
with menu_con[0]:
    sheet_header("🚚", "SHEET: Nhà cung cấp", "Quản lý danh sách NCC, đánh giá, điều khoản thanh toán")
    tab_list, tab_form, tab_chart = st.tabs(["📋 Danh sách", "➕ Nhập liệu", "📊 Biểu đồ"])

    suppliers = read_table("suppliers")

    with tab_list:
        st.dataframe(suppliers, use_container_width=True, hide_index=True)
        export_excel_button({"Nha_cung_cap": suppliers}, "nha_cung_cap.xlsx")

        if not suppliers.empty:
            st.markdown("###### ✏️ Sửa / 🗑️ Xoá")
            sel_id = st.selectbox("Chọn NCC theo id", suppliers["id"], key="ncc_sel")
            row = suppliers[suppliers["id"] == sel_id].iloc[0]
            col1, col2, col3 = st.columns(3)
            new_rating = col1.number_input("Điểm đánh giá", value=float(row["rating"]), key="ncc_edit_rating")
            new_lead = col2.number_input("Thời gian giao hàng (ngày)", value=float(row["lead_time_days"]), key="ncc_edit_lead")
            new_pay = col3.text_input("Điều khoản thanh toán", value=row["payment_terms"] or "", key="ncc_edit_pay")
            b1, b2 = st.columns(2)
            if b1.button("💾 Lưu cập nhật", use_container_width=True, key="ncc_save"):
                update_row("suppliers", int(sel_id), {"rating": new_rating, "lead_time_days": new_lead, "payment_terms": new_pay})
                st.success("Đã cập nhật.")
                st.rerun()
            if b2.button("🗑️ Xoá NCC này", use_container_width=True, key="ncc_del"):
                delete_row("suppliers", int(sel_id))
                st.warning("Đã xoá.")
                st.rerun()

    with tab_form:
        st.markdown("###### ➕ Thêm nhà cung cấp mới (dùng phím Tab để chuyển ô)")
        with st.form("form_ncc", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("Tên nhà cung cấp *")
            contact = c2.text_input("Người liên hệ / SĐT")
            c3, c4, c5 = st.columns(3)
            lead_time = c3.number_input("Thời gian giao hàng (ngày)", min_value=0.0, value=1.0)
            payment = c4.text_input("Điều khoản thanh toán", value="Công nợ 30 ngày")
            rating = c5.slider("Điểm đánh giá (0-10)", 0.0, 10.0, 7.0)
            submitted = st.form_submit_button("💾 Lưu vào cơ sở dữ liệu", use_container_width=True)
        if submitted:
            if not name.strip():
                st.error("Vui lòng nhập tên nhà cung cấp.")
            else:
                insert_row("suppliers", {
                    "name": name.strip(), "contact": contact, "lead_time_days": lead_time,
                    "payment_terms": payment, "rating": rating, "created_at": now_str(),
                })
                st.success(f"Đã lưu nhà cung cấp '{name}'.")
                st.rerun()

    with tab_chart:
        if suppliers.empty:
            empty_chart_placeholder()
        else:
            g1, g2 = st.columns(2)
            with g1:
                fig1 = px.bar(suppliers.sort_values("rating", ascending=False), x="name", y="rating",
                               title="① Điểm đánh giá theo từng NCC", text="rating")
                st.plotly_chart(style_chart(fig1), use_container_width=True)
            with g2:
                fig2 = px.histogram(suppliers, x="lead_time_days", nbins=10, title="② Phân bố thời gian giao hàng (ngày)")
                st.plotly_chart(style_chart(fig2), use_container_width=True)

            g3, g4 = st.columns(2)
            with g3:
                fig3 = px.pie(suppliers, names="payment_terms", title="③ Cơ cấu điều khoản thanh toán")
                st.plotly_chart(style_chart(fig3), use_container_width=True)
            with g4:
                fig4 = px.scatter(suppliers, x="lead_time_days", y="rating", size="rating", color="name",
                                   title="④ Tương quan: Thời gian giao hàng vs Điểm đánh giá")
                st.plotly_chart(style_chart(fig4), use_container_width=True)

            fig5 = px.bar(suppliers.sort_values("rating").tail(15), x="rating", y="name", orientation="h",
                           title="⑤ Xếp hạng NCC (thấp → cao)")
            st.plotly_chart(style_chart(fig5, height=420), use_container_width=True)

# ====================================================================
# MENU CON 2: NGUYÊN VẬT LIỆU  (SHEET)
# ====================================================================
with menu_con[1]:
    sheet_header("🧪", "SHEET: Nguyên vật liệu", "Danh mục NVL, đơn giá hiện hành, gắn với nhà cung cấp chính")
    tab_list, tab_form, tab_chart = st.tabs(["📋 Danh sách", "➕ Nhập liệu", "📊 Biểu đồ"])

    materials = read_table("materials")
    suppliers = read_table("suppliers")

    with tab_list:
        view = materials.merge(suppliers[["id", "name"]], left_on="supplier_id", right_on="id",
                                suffixes=("", "_ncc"), how="left") if not materials.empty else materials
        st.dataframe(view, use_container_width=True, hide_index=True)
        export_excel_button({"Nguyen_vat_lieu": materials}, "nguyen_vat_lieu.xlsx")

        if not materials.empty:
            st.markdown("###### ✏️ Sửa / 🗑️ Xoá")
            sel_id = st.selectbox("Chọn NVL theo id", materials["id"], key="nvl_sel")
            row = materials[materials["id"] == sel_id].iloc[0]
            col1, col2 = st.columns(2)
            new_price = col1.number_input("Đơn giá hiện hành", value=float(row["price"]), key="nvl_edit_price")
            new_stock = col2.number_input("Tồn kho tối thiểu", value=float(row["min_stock"]), key="nvl_edit_stock")
            b1, b2 = st.columns(2)
            if b1.button("💾 Lưu cập nhật", use_container_width=True, key="nvl_save"):
                update_row("materials", int(sel_id), {"price": new_price, "min_stock": new_stock})
                st.success("Đã cập nhật.")
                st.rerun()
            if b2.button("🗑️ Xoá NVL này", use_container_width=True, key="nvl_del"):
                delete_row("materials", int(sel_id))
                st.warning("Đã xoá.")
                st.rerun()

    with tab_form:
        st.markdown("###### ➕ Thêm nguyên vật liệu mới (dùng phím Tab để chuyển ô)")
        supplier_options = suppliers[["id", "name"]].values.tolist() if not suppliers.empty else []
        with st.form("form_nvl", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            code = c1.text_input("Mã NVL")
            name = c2.text_input("Tên NVL *")
            category = c3.text_input("Nhóm ngành hàng")
            c4, c5, c6 = st.columns(3)
            unit = c4.text_input("Đơn vị tính", value="kg")
            price = c5.number_input("Đơn giá hiện hành (đ)", min_value=0.0, value=0.0)
            min_stock = c6.number_input("Tồn kho tối thiểu", min_value=0.0, value=0.0)
            supplier_choice = st.selectbox(
                "Nhà cung cấp chính",
                options=["-- Chưa chọn --"] + [f"{s[0]} - {s[1]}" for s in supplier_options],
            )
            submitted = st.form_submit_button("💾 Lưu vào cơ sở dữ liệu", use_container_width=True)
        if submitted:
            if not name.strip():
                st.error("Vui lòng nhập tên nguyên vật liệu.")
            else:
                supplier_id = None
                if supplier_choice != "-- Chưa chọn --":
                    supplier_id = int(supplier_choice.split(" - ")[0])
                insert_row("materials", {
                    "code": code, "name": name.strip(), "category": category, "unit": unit,
                    "price": price, "supplier_id": supplier_id, "min_stock": min_stock, "created_at": now_str(),
                })
                st.success(f"Đã lưu nguyên vật liệu '{name}'.")
                st.rerun()

    with tab_chart:
        if materials.empty:
            empty_chart_placeholder()
        else:
            g1, g2 = st.columns(2)
            with g1:
                fig1 = px.bar(materials.sort_values("price", ascending=False).head(15), x="name", y="price",
                               title="① Top 15 NVL theo đơn giá")
                st.plotly_chart(style_chart(fig1), use_container_width=True)
            with g2:
                cnt = materials.groupby("category").size().reset_index(name="Số lượng")
                fig2 = px.pie(cnt, names="category", values="Số lượng", title="② Cơ cấu NVL theo nhóm ngành hàng")
                st.plotly_chart(style_chart(fig2), use_container_width=True)

            g3, g4 = st.columns(2)
            with g3:
                fig3 = px.box(materials, x="category", y="price", title="③ Phân bố đơn giá theo nhóm ngành hàng")
                st.plotly_chart(style_chart(fig3), use_container_width=True)
            with g4:
                fig4 = px.bar(materials, x="unit", y="price", color="category", title="④ Đơn giá theo đơn vị tính",
                               barmode="group")
                st.plotly_chart(style_chart(fig4), use_container_width=True)

            fig5 = px.scatter(materials, x="min_stock", y="price", color="category", size="price",
                               title="⑤ Tương quan: Tồn kho tối thiểu vs Đơn giá", hover_name="name")
            st.plotly_chart(style_chart(fig5, height=420), use_container_width=True)

# ====================================================================
# MENU CON 3: SẢN PHẨM  (SHEET)
# ====================================================================
with menu_con[2]:
    sheet_header("🍽️", "SHEET: Sản phẩm", "Danh mục món ăn / sản phẩm, giá bán và mục tiêu food-cost")
    tab_list, tab_form, tab_chart = st.tabs(["📋 Danh sách", "➕ Nhập liệu", "📊 Biểu đồ"])

    products = read_table("products")

    with tab_list:
        st.dataframe(products, use_container_width=True, hide_index=True)
        export_excel_button({"San_pham": products}, "san_pham.xlsx")

        if not products.empty:
            st.markdown("###### ✏️ Sửa / 🗑️ Xoá")
            sel_id = st.selectbox("Chọn sản phẩm theo id", products["id"], key="sp_sel")
            row = products[products["id"] == sel_id].iloc[0]
            col1, col2 = st.columns(2)
            new_price = col1.number_input("Giá bán", value=float(row["selling_price"]), key="sp_edit_price")
            new_fc = col2.number_input("Food cost mục tiêu tối đa (%)", value=float(row["target_food_cost_max"]), key="sp_edit_fc")
            b1, b2 = st.columns(2)
            if b1.button("💾 Lưu cập nhật", use_container_width=True, key="sp_save"):
                update_row("products", int(sel_id), {"selling_price": new_price, "target_food_cost_max": new_fc})
                st.success("Đã cập nhật.")
                st.rerun()
            if b2.button("🗑️ Xoá sản phẩm này", use_container_width=True, key="sp_del"):
                delete_row("products", int(sel_id))
                st.warning("Đã xoá.")
                st.rerun()

    with tab_form:
        st.markdown("###### ➕ Thêm sản phẩm mới (dùng phím Tab để chuyển ô)")
        with st.form("form_sp", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            code = c1.text_input("Mã sản phẩm")
            name = c2.text_input("Tên sản phẩm / món ăn *")
            dish_group = c3.text_input("Nhóm món", value="Món chính")
            c4, c5 = st.columns(2)
            selling_price = c4.number_input("Giá bán (đ/suất)", min_value=0.0, value=0.0)
            target_fc = c5.number_input("Food cost mục tiêu tối đa (%)", min_value=0.0, max_value=100.0, value=35.0)
            submitted = st.form_submit_button("💾 Lưu vào cơ sở dữ liệu", use_container_width=True)
        if submitted:
            if not name.strip():
                st.error("Vui lòng nhập tên sản phẩm.")
            else:
                insert_row("products", {
                    "code": code, "name": name.strip(), "dish_group": dish_group,
                    "selling_price": selling_price, "target_food_cost_max": target_fc, "created_at": now_str(),
                })
                st.success(f"Đã lưu sản phẩm '{name}'.")
                st.rerun()

    with tab_chart:
        if products.empty:
            empty_chart_placeholder()
        else:
            g1, g2 = st.columns(2)
            with g1:
                fig1 = px.bar(products.sort_values("selling_price", ascending=False), x="name", y="selling_price",
                               title="① Giá bán theo sản phẩm")
                st.plotly_chart(style_chart(fig1), use_container_width=True)
            with g2:
                cnt = products.groupby("dish_group").size().reset_index(name="Số lượng")
                fig2 = px.treemap(cnt, path=["dish_group"], values="Số lượng", title="② Cơ cấu sản phẩm theo nhóm món")
                st.plotly_chart(style_chart(fig2), use_container_width=True)

            g3, g4 = st.columns(2)
            with g3:
                fig3 = px.box(products, x="dish_group", y="selling_price", title="③ Phân bố giá bán theo nhóm món")
                st.plotly_chart(style_chart(fig3), use_container_width=True)
            with g4:
                fig4 = px.scatter(products, x="target_food_cost_max", y="selling_price", color="dish_group",
                                   size="selling_price", hover_name="name",
                                   title="④ Tương quan: Food-cost mục tiêu vs Giá bán")
                st.plotly_chart(style_chart(fig4), use_container_width=True)

            fig5 = px.histogram(products, x="target_food_cost_max", nbins=10, title="⑤ Phân bố Food-cost mục tiêu (%)")
            st.plotly_chart(style_chart(fig5, height=420), use_container_width=True)
