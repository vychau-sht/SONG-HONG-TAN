"""
MENU CHA: 🧑‍🤝‍🧑 KHÁCH HÀNG & ĐƠN HÀNG
MENU CON: Khách hàng | Hợp đồng | Đơn hàng
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from database import init_db, read_table, insert_row, update_row, delete_row, now_str
from utils import require_login, sidebar_user_box, inject_css, sheet_header, style_chart, export_excel_button, empty_chart_placeholder

st.set_page_config(page_title="Khách hàng & Đơn hàng — SHT/PBG", page_icon="🧑‍🤝‍🧑", layout="wide")
init_db()
inject_css()
require_login()
sidebar_user_box()

st.title("🧑‍🤝‍🧑 KHÁCH HÀNG & ĐƠN HÀNG")

products = read_table("products")
customers = read_table("customers")

menu_con = st.tabs(["👥 Khách hàng", "📜 Hợp đồng", "🧾 Đơn hàng"])

# ====================================================================
# MENU CON 1: KHÁCH HÀNG  (SHEET)
# ====================================================================
with menu_con[0]:
    sheet_header("👥", "SHEET: Khách hàng", "Danh mục khách hàng, loại hợp đồng, sản lượng tối thiểu")
    tab_list, tab_form, tab_chart = st.tabs(["📋 Danh sách", "➕ Nhập liệu", "📊 Biểu đồ"])

    with tab_list:
        st.dataframe(customers, use_container_width=True, hide_index=True)
        export_excel_button({"Khach_hang": customers}, "khach_hang.xlsx")
        if not customers.empty:
            st.markdown("###### ✏️ Sửa / 🗑️ Xoá")
            sel_id = st.selectbox("Chọn khách hàng theo id", customers["id"], key="kh_sel")
            row = customers[customers["id"] == sel_id].iloc[0]
            c1, c2 = st.columns(2)
            new_status = c1.selectbox("Trạng thái", ["Đang hoạt động", "Tạm ngưng", "Đã kết thúc"],
                                       index=["Đang hoạt động", "Tạm ngưng", "Đã kết thúc"].index(row["status"]) if row["status"] in ["Đang hoạt động", "Tạm ngưng", "Đã kết thúc"] else 0,
                                       key="kh_edit_status")
            new_adj = c2.number_input("Điều chỉnh giá (%)", value=float(row["price_adj"]), key="kh_edit_adj")
            b1, b2 = st.columns(2)
            if b1.button("💾 Lưu cập nhật", use_container_width=True, key="kh_save"):
                update_row("customers", int(sel_id), {"status": new_status, "price_adj": new_adj})
                st.success("Đã cập nhật.")
                st.rerun()
            if b2.button("🗑️ Xoá khách hàng này", use_container_width=True, key="kh_del"):
                delete_row("customers", int(sel_id))
                st.warning("Đã xoá.")
                st.rerun()

    with tab_form:
        st.markdown("###### ➕ Thêm khách hàng mới (dùng phím Tab để chuyển ô)")
        with st.form("form_kh", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("Tên khách hàng *")
            contract_type = c2.selectbox("Loại hợp đồng", ["Theo suất ăn", "Theo tháng", "Theo sự kiện", "Khác"])
            c3, c4 = st.columns(2)
            min_volume = c3.number_input("Sản lượng tối thiểu (suất/tháng)", min_value=0.0, value=0.0)
            price_adj = c4.number_input("Điều chỉnh giá (%)", value=0.0)
            status = st.selectbox("Trạng thái", ["Đang hoạt động", "Tạm ngưng", "Đã kết thúc"])
            submitted = st.form_submit_button("💾 Lưu vào cơ sở dữ liệu", use_container_width=True)
        if submitted:
            if not name.strip():
                st.error("Vui lòng nhập tên khách hàng.")
            else:
                insert_row("customers", {
                    "name": name.strip(), "contract_type": contract_type, "min_volume": min_volume,
                    "price_adj": price_adj, "status": status, "created_at": now_str(),
                })
                st.success(f"Đã lưu khách hàng '{name}'.")
                st.rerun()

    with tab_chart:
        if customers.empty:
            empty_chart_placeholder()
        else:
            g1, g2 = st.columns(2)
            with g1:
                cnt = customers.groupby("status").size().reset_index(name="Số lượng")
                fig1 = px.pie(cnt, names="status", values="Số lượng", title="① Cơ cấu khách hàng theo trạng thái")
                st.plotly_chart(style_chart(fig1), use_container_width=True)
            with g2:
                fig2 = px.bar(customers.sort_values("min_volume", ascending=False), x="name", y="min_volume",
                               title="② Sản lượng tối thiểu theo khách hàng")
                st.plotly_chart(style_chart(fig2), use_container_width=True)

            g3, g4 = st.columns(2)
            with g3:
                cnt2 = customers.groupby("contract_type").size().reset_index(name="Số lượng")
                fig3 = px.bar(cnt2, x="contract_type", y="Số lượng", title="③ Số khách hàng theo loại hợp đồng")
                st.plotly_chart(style_chart(fig3), use_container_width=True)
            with g4:
                fig4 = px.box(customers, x="contract_type", y="price_adj", title="④ Phân bố điều chỉnh giá theo loại hợp đồng")
                st.plotly_chart(style_chart(fig4), use_container_width=True)

            fig5 = px.scatter(customers, x="min_volume", y="price_adj", color="status", size="min_volume",
                               hover_name="name", title="⑤ Tương quan Sản lượng tối thiểu vs Điều chỉnh giá")
            st.plotly_chart(style_chart(fig5, height=420), use_container_width=True)

# ====================================================================
# MENU CON 2: HỢP ĐỒNG  (SHEET)
# ====================================================================
with menu_con[1]:
    sheet_header("📜", "SHEET: Hợp đồng", "Hợp đồng ký với khách hàng, thời hạn hiệu lực, giá trị")
    tab_list, tab_form, tab_chart = st.tabs(["📋 Danh sách", "➕ Nhập liệu", "📊 Biểu đồ"])

    contracts = read_table("contracts", order_by="sign_date DESC")
    view = contracts.copy()
    if not contracts.empty and not customers.empty:
        view = contracts.merge(customers[["id", "name"]], left_on="customer_id", right_on="id", suffixes=("", "_kh"))

    with tab_list:
        st.dataframe(view, use_container_width=True, hide_index=True)
        export_excel_button({"Hop_dong": view}, "hop_dong.xlsx")
        if not contracts.empty:
            st.markdown("###### 🗑️ Xoá hợp đồng")
            sel_id = st.selectbox("Chọn hợp đồng theo id", contracts["id"], key="hd_sel")
            if st.button("🗑️ Xoá", key="hd_del"):
                delete_row("contracts", int(sel_id))
                st.warning("Đã xoá.")
                st.rerun()

    with tab_form:
        st.markdown("###### ➕ Thêm hợp đồng mới (dùng phím Tab để chuyển ô)")
        customer_opts = customers[["id", "name"]].values.tolist() if not customers.empty else []
        if not customer_opts:
            st.warning("Cần có ít nhất 1 Khách hàng trước (tab '👥 Khách hàng').")
        else:
            with st.form("form_hd", clear_on_submit=True):
                c1, c2 = st.columns(2)
                customer_choice = c1.selectbox("Khách hàng *", [f"{c[0]} - {c[1]}" for c in customer_opts])
                contract_no = c2.text_input("Số hợp đồng *")
                c3, c4, c5 = st.columns(3)
                sign_date = c3.date_input("Ngày ký")
                eff_from = c4.date_input("Hiệu lực từ")
                eff_to = c5.date_input("Hiệu lực đến")
                c6, c7 = st.columns(2)
                contract_value = c6.number_input("Giá trị hợp đồng (đ)", min_value=0.0, value=0.0)
                status = c7.selectbox("Trạng thái", ["Hiệu lực", "Hết hạn", "Thanh lý"])
                submitted = st.form_submit_button("💾 Lưu vào cơ sở dữ liệu", use_container_width=True)
            if submitted:
                insert_row("contracts", {
                    "customer_id": int(customer_choice.split(" - ")[0]), "contract_no": contract_no,
                    "sign_date": str(sign_date), "effective_from": str(eff_from), "effective_to": str(eff_to),
                    "contract_value": contract_value, "status": status,
                })
                st.success("Đã lưu hợp đồng.")
                st.rerun()

    with tab_chart:
        if view.empty:
            empty_chart_placeholder()
        else:
            g1, g2 = st.columns(2)
            with g1:
                fig1 = px.bar(view.sort_values("contract_value", ascending=False), x="name", y="contract_value",
                               title="① Giá trị hợp đồng theo khách hàng")
                st.plotly_chart(style_chart(fig1), use_container_width=True)
            with g2:
                cnt = view.groupby("status").size().reset_index(name="Số lượng")
                fig2 = px.pie(cnt, names="status", values="Số lượng", title="② Cơ cấu hợp đồng theo trạng thái")
                st.plotly_chart(style_chart(fig2), use_container_width=True)

            g3, g4 = st.columns(2)
            with g3:
                v = view.copy()
                v["sign_date_dt"] = pd.to_datetime(v["sign_date"], errors="coerce")
                fig3 = px.line(v.sort_values("sign_date_dt"), x="sign_date_dt", y="contract_value", markers=True,
                                title="③ Xu hướng giá trị hợp đồng ký theo thời gian")
                st.plotly_chart(style_chart(fig3), use_container_width=True)
            with g4:
                fig4 = px.box(view, x="status", y="contract_value", title="④ Phân bố giá trị hợp đồng theo trạng thái")
                st.plotly_chart(style_chart(fig4), use_container_width=True)

            fig5 = px.treemap(view, path=["name"], values="contract_value", title="⑤ Tỷ trọng giá trị hợp đồng theo khách hàng")
            st.plotly_chart(style_chart(fig5, height=420), use_container_width=True)

# ====================================================================
# MENU CON 3: ĐƠN HÀNG  (SHEET)
# ====================================================================
with menu_con[2]:
    sheet_header("🧾", "SHEET: Đơn hàng", "Đơn hàng của khách hàng, sản phẩm, ngày giao, trạng thái xử lý")
    tab_list, tab_form, tab_chart = st.tabs(["📋 Danh sách", "➕ Nhập liệu", "📊 Biểu đồ"])

    orders = read_table("orders", order_by="order_date DESC")
    view = orders.copy()
    if not orders.empty:
        if not customers.empty:
            view = view.merge(customers[["id", "name"]], left_on="customer_id", right_on="id", suffixes=("", "_kh"))
        if not products.empty:
            view = view.merge(products[["id", "name"]], left_on="product_id", right_on="id", suffixes=("", "_sp"))

    with tab_list:
        st.dataframe(view, use_container_width=True, hide_index=True)
        export_excel_button({"Don_hang": view}, "don_hang.xlsx")
        if not orders.empty:
            st.markdown("###### ✏️ Sửa trạng thái / 🗑️ Xoá")
            sel_id = st.selectbox("Chọn đơn hàng theo id", orders["id"], key="dh_sel")
            row = orders[orders["id"] == sel_id].iloc[0]
            c1, c2 = st.columns(2)
            new_status = c1.selectbox("Trạng thái", ["Mới", "Đang sản xuất", "Đã giao", "Huỷ"],
                                       index=["Mới", "Đang sản xuất", "Đã giao", "Huỷ"].index(row["status"]) if row["status"] in ["Mới", "Đang sản xuất", "Đã giao", "Huỷ"] else 0,
                                       key="dh_edit_status")
            new_priority = c2.selectbox("Độ ưu tiên", ["Thấp", "Bình thường", "Cao", "Khẩn"],
                                         index=["Thấp", "Bình thường", "Cao", "Khẩn"].index(row["priority"]) if row["priority"] in ["Thấp", "Bình thường", "Cao", "Khẩn"] else 1,
                                         key="dh_edit_priority")
            b1, b2 = st.columns(2)
            if b1.button("💾 Lưu cập nhật", use_container_width=True, key="dh_save"):
                update_row("orders", int(sel_id), {"status": new_status, "priority": new_priority})
                st.success("Đã cập nhật.")
                st.rerun()
            if b2.button("🗑️ Xoá đơn hàng này", use_container_width=True, key="dh_del"):
                delete_row("orders", int(sel_id))
                st.warning("Đã xoá.")
                st.rerun()

    with tab_form:
        st.markdown("###### ➕ Thêm đơn hàng mới (dùng phím Tab để chuyển ô)")
        customer_opts = customers[["id", "name"]].values.tolist() if not customers.empty else []
        product_opts = products[["id", "name"]].values.tolist() if not products.empty else []
        if not customer_opts:
            st.warning("Cần có ít nhất 1 Khách hàng trước (tab '👥 Khách hàng').")
        else:
            with st.form("form_dh", clear_on_submit=True):
                c1, c2 = st.columns(2)
                customer_choice = c1.selectbox("Khách hàng *", [f"{c[0]} - {c[1]}" for c in customer_opts])
                product_choice = c2.selectbox(
                    "Sản phẩm", ["-- Chưa chọn --"] + [f"{p[0]} - {p[1]}" for p in product_opts]
                )
                c3, c4 = st.columns(2)
                order_date = c3.date_input("Ngày đặt hàng")
                delivery_date = c4.date_input("Ngày giao hàng")
                c5, c6, c7 = st.columns(3)
                servings = c5.number_input("Số suất", min_value=0.0, value=0.0)
                priority = c6.selectbox("Độ ưu tiên", ["Thấp", "Bình thường", "Cao", "Khẩn"], index=1)
                status = c7.selectbox("Trạng thái", ["Mới", "Đang sản xuất", "Đã giao", "Huỷ"])
                submitted = st.form_submit_button("💾 Lưu vào cơ sở dữ liệu", use_container_width=True)
            if submitted:
                product_id = None
                if product_choice != "-- Chưa chọn --":
                    product_id = int(product_choice.split(" - ")[0])
                insert_row("orders", {
                    "customer_id": int(customer_choice.split(" - ")[0]), "product_id": product_id,
                    "order_date": str(order_date), "delivery_date": str(delivery_date),
                    "servings": servings, "priority": priority, "status": status,
                })
                st.success("Đã lưu đơn hàng.")
                st.rerun()

    with tab_chart:
        if view.empty:
            empty_chart_placeholder()
        else:
            g1, g2 = st.columns(2)
            with g1:
                cnt = view.groupby("status").size().reset_index(name="Số đơn")
                fig1 = px.pie(cnt, names="status", values="Số đơn", title="① Cơ cấu đơn hàng theo trạng thái")
                st.plotly_chart(style_chart(fig1), use_container_width=True)
            with g2:
                cnt2 = view.groupby("priority").size().reset_index(name="Số đơn")
                fig2 = px.bar(cnt2, x="priority", y="Số đơn", title="② Số đơn hàng theo độ ưu tiên")
                st.plotly_chart(style_chart(fig2), use_container_width=True)

            g3, g4 = st.columns(2)
            with g3:
                v = view.copy()
                v["order_date_dt"] = pd.to_datetime(v["order_date"], errors="coerce")
                trend = v.groupby(v["order_date_dt"].dt.date)["servings"].sum().reset_index()
                fig3 = px.line(trend, x="order_date_dt", y="servings", markers=True, title="③ Tổng số suất đặt hàng theo ngày")
                st.plotly_chart(style_chart(fig3), use_container_width=True)
            with g4:
                if "name_kh" in view.columns or "name" in view.columns:
                    name_col = "name_kh" if "name_kh" in view.columns else "name"
                    cnt3 = view.groupby(name_col)["servings"].sum().reset_index()
                    fig4 = px.bar(cnt3.sort_values("servings", ascending=False).head(10), x=name_col, y="servings",
                                   title="④ Top 10 khách hàng theo tổng số suất đặt")
                    st.plotly_chart(style_chart(fig4), use_container_width=True)

            fig5 = px.scatter(view, x="servings", y="priority", color="status",
                               title="⑤ Tương quan Số suất vs Độ ưu tiên")
            st.plotly_chart(style_chart(fig5, height=420), use_container_width=True)
