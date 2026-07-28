"""
MENU CHA: 🏭 SẢN XUẤT
MENU CON: BOM (định mức NVL) | Routing (công đoạn sản xuất)
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from database import init_db, read_table, insert_row, update_row, delete_row
from utils import require_login, sidebar_user_box, inject_css, sheet_header, style_chart, export_excel_button, empty_chart_placeholder

st.set_page_config(page_title="Sản xuất — SHT/PBG", page_icon="🏭", layout="wide")
init_db()
inject_css()
require_login()
sidebar_user_box()

st.title("🏭 SẢN XUẤT")

products = read_table("products")
materials = read_table("materials")
product_opts = products[["id", "name"]].values.tolist() if not products.empty else []
material_opts = materials[["id", "name"]].values.tolist() if not materials.empty else []

menu_con = st.tabs(["🧾 BOM (Định mức NVL)", "⚙️ Routing (Công đoạn)"])

# ====================================================================
# MENU CON 1: BOM  (SHEET)
# ====================================================================
with menu_con[0]:
    sheet_header("🧾", "SHEET: BOM — Bill of Materials", "Định mức NVL cho từng sản phẩm, có tính hao hụt sơ chế/chế biến/vận chuyển")
    tab_list, tab_form, tab_chart = st.tabs(["📋 Danh sách", "➕ Nhập liệu", "📊 Biểu đồ"])

    bom = read_table("bom")
    view = bom.copy()
    if not bom.empty:
        view = bom.merge(products[["id", "name"]], left_on="product_id", right_on="id", suffixes=("", "_sp")) \
                  .merge(materials[["id", "name", "price"]], left_on="material_id", right_on="id", suffixes=("", "_nvl"))

    with tab_list:
        st.dataframe(view, use_container_width=True, hide_index=True)
        export_excel_button({"BOM": view}, "bom.xlsx")

        if not bom.empty:
            st.markdown("###### ✏️ Sửa / 🗑️ Xoá dòng BOM")
            sel_id = st.selectbox("Chọn dòng BOM theo id", bom["id"], key="bom_sel")
            row = bom[bom["id"] == sel_id].iloc[0]
            c1, c2, c3, c4 = st.columns(4)
            raw_qty = c1.number_input("Định mức thô", value=float(row["raw_qty"]), key="bom_raw")
            yp = c2.number_input("Hiệu suất sơ chế (0-1)", value=float(row["yield_prep"]), key="bom_yp")
            yc = c3.number_input("Hiệu suất chế biến (0-1)", value=float(row["yield_cook"]), key="bom_yc")
            tl = c4.number_input("Hao hụt vận chuyển (0-1)", value=float(row["transport_loss"]), key="bom_tl")
            b1, b2 = st.columns(2)
            if b1.button("💾 Lưu cập nhật", use_container_width=True, key="bom_save"):
                update_row("bom", int(sel_id), {"raw_qty": raw_qty, "yield_prep": yp, "yield_cook": yc, "transport_loss": tl})
                st.success("Đã cập nhật.")
                st.rerun()
            if b2.button("🗑️ Xoá dòng này", use_container_width=True, key="bom_del"):
                delete_row("bom", int(sel_id))
                st.warning("Đã xoá.")
                st.rerun()

    with tab_form:
        st.markdown("###### ➕ Thêm dòng BOM mới (dùng phím Tab để chuyển ô)")
        if not product_opts or not material_opts:
            st.warning("Cần có ít nhất 1 Sản phẩm và 1 Nguyên vật liệu trước (vào 📦 Danh mục để thêm).")
        else:
            with st.form("form_bom", clear_on_submit=True):
                c1, c2 = st.columns(2)
                product_choice = c1.selectbox("Sản phẩm *", [f"{p[0]} - {p[1]}" for p in product_opts])
                material_choice = c2.selectbox("Nguyên vật liệu *", [f"{m[0]} - {m[1]}" for m in material_opts])
                stage = st.text_input("Công đoạn sử dụng NVL này", value="Sơ chế")
                c3, c4, c5, c6 = st.columns(4)
                raw_qty = c3.number_input("Định mức thô (theo đơn vị NVL)", min_value=0.0, value=0.1)
                yield_prep = c4.number_input("Hiệu suất sơ chế (0-1)", min_value=0.01, max_value=1.0, value=0.95)
                yield_cook = c5.number_input("Hiệu suất chế biến (0-1)", min_value=0.01, max_value=1.0, value=0.90)
                transport_loss = c6.number_input("Hao hụt vận chuyển (0-1)", min_value=0.0, max_value=1.0, value=0.02)
                submitted = st.form_submit_button("💾 Lưu vào cơ sở dữ liệu", use_container_width=True)
            if submitted:
                insert_row("bom", {
                    "product_id": int(product_choice.split(" - ")[0]),
                    "material_id": int(material_choice.split(" - ")[0]),
                    "stage": stage, "raw_qty": raw_qty, "yield_prep": yield_prep,
                    "yield_cook": yield_cook, "transport_loss": transport_loss,
                })
                st.success("Đã lưu dòng BOM.")
                st.rerun()

    with tab_chart:
        if view.empty:
            empty_chart_placeholder()
        else:
            v = view.copy()
            v["effective_qty"] = v["raw_qty"] / (v["yield_prep"] * v["yield_cook"]) * (1 + v["transport_loss"])
            v["material_cost"] = v["effective_qty"] * v["price"]

            g1, g2 = st.columns(2)
            with g1:
                fig1 = px.bar(v.groupby("name")["material_cost"].sum().reset_index(),
                               x="name", y="material_cost", title="① Tổng chi phí NVL (BOM) theo sản phẩm")
                st.plotly_chart(style_chart(fig1), use_container_width=True)
            with g2:
                fig2 = px.pie(v, names="stage", values="material_cost", title="② Cơ cấu chi phí NVL theo công đoạn sử dụng")
                st.plotly_chart(style_chart(fig2), use_container_width=True)

            g3, g4 = st.columns(2)
            with g3:
                fig3 = px.bar(v.sort_values("material_cost", ascending=False).head(15),
                               x="name_nvl", y="material_cost", title="③ Top 15 NVL tốn chi phí nhất (đã trừ hao hụt)")
                st.plotly_chart(style_chart(fig3), use_container_width=True)
            with g4:
                fig4 = px.scatter(v, x="yield_prep", y="yield_cook", size="material_cost", color="name",
                                   title="④ Tương quan hiệu suất sơ chế vs chế biến")
                st.plotly_chart(style_chart(fig4), use_container_width=True)

            fig5 = px.box(v, x="stage", y="transport_loss", title="⑤ Phân bố tỉ lệ hao hụt vận chuyển theo công đoạn")
            st.plotly_chart(style_chart(fig5, height=420), use_container_width=True)

# ====================================================================
# MENU CON 2: ROUTING  (SHEET)
# ====================================================================
with menu_con[1]:
    sheet_header("⚙️", "SHEET: Routing — Công đoạn sản xuất", "Cycle time, số nhân công, cơ sở phân bổ SXC cho từng công đoạn")
    tab_list, tab_form, tab_chart = st.tabs(["📋 Danh sách", "➕ Nhập liệu", "📊 Biểu đồ"])

    routing = read_table("routing", order_by="product_id, seq")
    view = routing.copy()
    if not routing.empty:
        view = routing.merge(products[["id", "name"]], left_on="product_id", right_on="id", suffixes=("", "_sp"))

    with tab_list:
        st.dataframe(view, use_container_width=True, hide_index=True)
        export_excel_button({"Routing": view}, "routing.xlsx")

        if not routing.empty:
            st.markdown("###### ✏️ Sửa / 🗑️ Xoá công đoạn")
            sel_id = st.selectbox("Chọn công đoạn theo id", routing["id"], key="rt_sel")
            row = routing[routing["id"] == sel_id].iloc[0]
            c1, c2, c3 = st.columns(3)
            cycle = c1.number_input("Cycle time (giây)", value=float(row["cycle_time_sec"]), key="rt_cycle")
            ops = c2.number_input("Số nhân công (operators)", value=float(row["operators"]), key="rt_ops")
            alloc = c3.selectbox("Cơ sở phân bổ SXC", ["Theo giờ công trực tiếp", "Theo giờ máy"],
                                  index=0 if row["alloc_base"] == "Theo giờ công trực tiếp" else 1, key="rt_alloc")
            b1, b2 = st.columns(2)
            if b1.button("💾 Lưu cập nhật", use_container_width=True, key="rt_save"):
                update_row("routing", int(sel_id), {"cycle_time_sec": cycle, "operators": ops, "alloc_base": alloc})
                st.success("Đã cập nhật.")
                st.rerun()
            if b2.button("🗑️ Xoá công đoạn này", use_container_width=True, key="rt_del"):
                delete_row("routing", int(sel_id))
                st.warning("Đã xoá.")
                st.rerun()

    with tab_form:
        st.markdown("###### ➕ Thêm công đoạn mới (dùng phím Tab để chuyển ô)")
        if not product_opts:
            st.warning("Cần có ít nhất 1 Sản phẩm trước (vào 📦 Danh mục để thêm).")
        else:
            with st.form("form_routing", clear_on_submit=True):
                c1, c2 = st.columns(2)
                product_choice = c1.selectbox("Sản phẩm *", [f"{p[0]} - {p[1]}" for p in product_opts])
                seq = c2.number_input("Thứ tự công đoạn", min_value=1, value=1, step=1)
                c3, c4 = st.columns(2)
                step_name = c3.text_input("Tên công đoạn *", value="Sơ chế")
                station = c4.text_input("Trạm / khu vực", value="Khu sơ chế")
                c5, c6, c7 = st.columns(3)
                cycle_time = c5.number_input("Cycle time (giây) *", min_value=0.0, value=60.0)
                operators = c6.number_input("Số nhân công", min_value=0.0, value=1.0)
                alloc_base = c7.selectbox("Cơ sở phân bổ SXC", ["Theo giờ công trực tiếp", "Theo giờ máy"])
                c8, c9, c10 = st.columns(3)
                wait_before = c8.number_input("Thời gian chờ trước (giây)", min_value=0.0, value=0.0)
                wait_after = c9.number_input("Thời gian chờ sau (giây)", min_value=0.0, value=0.0)
                downtime = c10.number_input("Thời gian dừng máy (giây)", min_value=0.0, value=0.0)
                submitted = st.form_submit_button("💾 Lưu vào cơ sở dữ liệu", use_container_width=True)
            if submitted:
                insert_row("routing", {
                    "product_id": int(product_choice.split(" - ")[0]), "seq": seq, "step_name": step_name,
                    "station": station, "alloc_base": alloc_base, "cycle_time_sec": cycle_time,
                    "operators": operators, "wait_before_sec": wait_before, "wait_after_sec": wait_after,
                    "downtime_sec": downtime,
                })
                st.success("Đã lưu công đoạn.")
                st.rerun()

    with tab_chart:
        if view.empty:
            empty_chart_placeholder()
        else:
            g1, g2 = st.columns(2)
            with g1:
                fig1 = px.bar(view, x="step_name", y="cycle_time_sec", color="name",
                               title="① Cycle time theo từng công đoạn")
                st.plotly_chart(style_chart(fig1), use_container_width=True)
            with g2:
                fig2 = px.pie(view, names="alloc_base", title="② Cơ cấu cơ sở phân bổ SXC (giờ công vs giờ máy)")
                st.plotly_chart(style_chart(fig2), use_container_width=True)

            g3, g4 = st.columns(2)
            with g3:
                fig3 = px.bar(view.groupby("name")["operators"].sum().reset_index(),
                               x="name", y="operators", title="③ Tổng số nhân công theo sản phẩm")
                st.plotly_chart(style_chart(fig3), use_container_width=True)
            with g4:
                fig4 = px.scatter(view, x="cycle_time_sec", y="downtime_sec", size="operators", color="station",
                                   title="④ Tương quan Cycle time vs Thời gian dừng máy")
                st.plotly_chart(style_chart(fig4), use_container_width=True)

            fig5 = px.line(view.sort_values(["product_id", "seq"]), x="seq", y="cycle_time_sec", color="name",
                            markers=True, title="⑤ Lộ trình cycle time theo thứ tự công đoạn (từng sản phẩm)")
            st.plotly_chart(style_chart(fig5, height=420), use_container_width=True)
