"""
MENU CHA: ✅ KIỂM SOÁT CHẤT LƯỢNG (QC)
MENU CON: QC Đầu vào (nhận NVL từ NCC) | QC Đầu ra (trước khi giao khách hàng)
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from database import init_db, read_table, insert_row, delete_row
from utils import require_login, sidebar_user_box, inject_css, sheet_header, style_chart, export_excel_button, empty_chart_placeholder

st.set_page_config(page_title="Kiểm soát chất lượng — SHT/PBG", page_icon="✅", layout="wide")
init_db()
inject_css()
require_login()
sidebar_user_box()

st.title("✅ KIỂM SOÁT CHẤT LƯỢNG (QC)")

materials = read_table("materials")
suppliers = read_table("suppliers")
orders = read_table("orders")
customers = read_table("customers")

menu_con = st.tabs(["📥 QC Đầu vào (NVL)", "📤 QC Đầu ra (Sản phẩm)"])

# ====================================================================
# MENU CON 1: QC ĐẦU VÀO  (SHEET)
# ====================================================================
with menu_con[0]:
    sheet_header("📥", "SHEET: QC Đầu vào", "Kiểm tra NVL khi nhận hàng từ nhà cung cấp — theo lô (lot), lấy mẫu (AQL)")
    tab_list, tab_form, tab_chart = st.tabs(["📋 Danh sách", "➕ Nhập liệu", "📊 Biểu đồ"])

    qi = read_table("qc_inbound", order_by="inspected_at DESC")
    view = qi.copy()
    if not qi.empty:
        if not materials.empty:
            view = view.merge(materials[["id", "name"]], left_on="material_id", right_on="id", suffixes=("", "_nvl"))
        if not suppliers.empty:
            view = view.merge(suppliers[["id", "name"]], left_on="supplier_id", right_on="id", suffixes=("", "_ncc"))

    with tab_list:
        st.dataframe(view, use_container_width=True, hide_index=True)
        export_excel_button({"QC_dau_vao": view}, "qc_dau_vao.xlsx")
        if not qi.empty:
            st.markdown("###### 🗑️ Xoá bản ghi")
            sel_id = st.selectbox("Chọn theo id", qi["id"], key="qi_sel")
            if st.button("🗑️ Xoá", key="qi_del"):
                delete_row("qc_inbound", int(sel_id))
                st.warning("Đã xoá.")
                st.rerun()

    with tab_form:
        st.markdown("###### ➕ Ghi nhận kiểm tra QC đầu vào (dùng phím Tab để chuyển ô)")
        material_opts = materials[["id", "name"]].values.tolist() if not materials.empty else []
        supplier_opts = suppliers[["id", "name"]].values.tolist() if not suppliers.empty else []
        if not material_opts:
            st.warning("Cần có ít nhất 1 Nguyên vật liệu trước (📦 Danh mục).")
        else:
            with st.form("form_qi", clear_on_submit=True):
                c1, c2 = st.columns(2)
                material_choice = c1.selectbox("Nguyên vật liệu *", [f"{m[0]} - {m[1]}" for m in material_opts])
                supplier_choice = c2.selectbox(
                    "Nhà cung cấp", ["-- Chưa chọn --"] + [f"{s[0]} - {s[1]}" for s in supplier_opts]
                )
                c3, c4 = st.columns(2)
                lot_no = c3.text_input("Số lô (Lot No.)")
                received_qty = c4.number_input("Số lượng nhận", min_value=0.0, value=0.0)
                c5, c6 = st.columns(2)
                sample_size = c5.number_input("Cỡ mẫu kiểm tra (AQL)", min_value=0, value=5, step=1)
                defects_found = c6.number_input("Số lỗi phát hiện", min_value=0, value=0, step=1)
                c7, c8 = st.columns(2)
                inspector = c7.text_input("Người kiểm tra (QC)")
                approver = c8.text_input("Người duyệt")
                result = st.selectbox("Kết luận", ["Đạt", "Không đạt", "Đạt có điều kiện"])
                inspected_at = st.date_input("Ngày kiểm tra")
                submitted = st.form_submit_button("💾 Lưu vào cơ sở dữ liệu", use_container_width=True)
            if submitted:
                supplier_id = None
                if supplier_choice != "-- Chưa chọn --":
                    supplier_id = int(supplier_choice.split(" - ")[0])
                insert_row("qc_inbound", {
                    "material_id": int(material_choice.split(" - ")[0]), "supplier_id": supplier_id,
                    "lot_no": lot_no, "received_qty": received_qty, "sample_size": sample_size,
                    "defects_found": defects_found, "result": result, "inspector": inspector,
                    "approver": approver, "inspected_at": str(inspected_at),
                })
                st.success("Đã lưu kết quả QC đầu vào.")
                st.rerun()

    with tab_chart:
        if view.empty:
            empty_chart_placeholder()
        else:
            v = view.copy()
            v["defect_rate"] = (v["defects_found"] / v["sample_size"].replace(0, pd.NA) * 100).fillna(0)

            g1, g2 = st.columns(2)
            with g1:
                cnt = v.groupby("result").size().reset_index(name="Số lượt")
                fig1 = px.pie(cnt, names="result", values="Số lượt", title="① Tỷ lệ kết luận QC đầu vào (Đạt/Không đạt)")
                st.plotly_chart(style_chart(fig1), use_container_width=True)
            with g2:
                name_col = "name_ncc" if "name_ncc" in v.columns else None
                if name_col:
                    fig2 = px.bar(v.groupby(name_col)["defect_rate"].mean().reset_index(),
                                   x=name_col, y="defect_rate", title="② Tỷ lệ lỗi trung bình (%) theo nhà cung cấp")
                    st.plotly_chart(style_chart(fig2), use_container_width=True)

            g3, g4 = st.columns(2)
            with g3:
                name_col2 = "name" if "name" in v.columns else "material_id"
                fig3 = px.bar(v.groupby(name_col2)["defects_found"].sum().reset_index(),
                               x=name_col2, y="defects_found", title="③ Tổng số lỗi phát hiện theo NVL")
                st.plotly_chart(style_chart(fig3), use_container_width=True)
            with g4:
                v["inspected_at_dt"] = pd.to_datetime(v["inspected_at"], errors="coerce")
                trend = v.groupby(v["inspected_at_dt"].dt.date)["defect_rate"].mean().reset_index()
                fig4 = px.line(trend, x="inspected_at_dt", y="defect_rate", markers=True,
                                title="④ Xu hướng tỷ lệ lỗi (%) theo thời gian")
                st.plotly_chart(style_chart(fig4), use_container_width=True)

            fig5 = px.scatter(v, x="received_qty", y="defect_rate", color="result", size="sample_size",
                               hover_name=name_col2, title="⑤ Tương quan Số lượng nhận vs Tỷ lệ lỗi")
            st.plotly_chart(style_chart(fig5, height=420), use_container_width=True)

# ====================================================================
# MENU CON 2: QC ĐẦU RA  (SHEET)
# ====================================================================
with menu_con[1]:
    sheet_header("📤", "SHEET: QC Đầu ra", "Kiểm tra thành phẩm trước khi giao — nhiệt độ, định lượng suất ăn, bao bì, nhãn mác")
    tab_list, tab_form, tab_chart = st.tabs(["📋 Danh sách", "➕ Nhập liệu", "📊 Biểu đồ"])

    qo = read_table("qc_outbound", order_by="check_date DESC")
    view = qo.copy()
    if not qo.empty and not orders.empty:
        order_view = orders.copy()
        if not customers.empty:
            order_view = order_view.merge(customers[["id", "name"]], left_on="customer_id", right_on="id", suffixes=("", "_kh"))
        view = qo.merge(order_view[["id", "name"]], left_on="order_id", right_on="id", suffixes=("", "_dh"), how="left")

    with tab_list:
        st.dataframe(view, use_container_width=True, hide_index=True)
        export_excel_button({"QC_dau_ra": view}, "qc_dau_ra.xlsx")
        if not qo.empty:
            st.markdown("###### 🗑️ Xoá bản ghi")
            sel_id = st.selectbox("Chọn theo id", qo["id"], key="qo_sel")
            if st.button("🗑️ Xoá", key="qo_del"):
                delete_row("qc_outbound", int(sel_id))
                st.warning("Đã xoá.")
                st.rerun()

    with tab_form:
        st.markdown("###### ➕ Ghi nhận kiểm tra QC đầu ra (dùng phím Tab để chuyển ô)")
        order_opts = orders[["id"]].values.tolist() if not orders.empty else []
        with st.form("form_qo", clear_on_submit=True):
            order_choice = st.selectbox(
                "Đơn hàng liên quan", ["-- Không gắn đơn hàng --"] + [f"Đơn #{o[0]}" for o in order_opts]
            )
            c1, c2 = st.columns(2)
            check_date = c1.date_input("Ngày kiểm tra")
            servings_checked = c2.number_input("Số suất được kiểm tra", min_value=0.0, value=0.0)
            c3, c4 = st.columns(2)
            temp_check = c3.selectbox("Kiểm tra nhiệt độ", ["Đạt", "Không đạt"])
            portion_check = c4.selectbox("Kiểm tra định lượng suất", ["Đạt", "Không đạt"])
            c5, c6 = st.columns(2)
            packaging_check = c5.selectbox("Kiểm tra bao bì", ["Đạt", "Không đạt"])
            label_check = c6.selectbox("Kiểm tra nhãn mác", ["Đạt", "Không đạt"])
            c7, c8 = st.columns(2)
            inspector = c7.text_input("Người kiểm tra (QC)")
            approver = c8.text_input("Người duyệt")
            overall_result = st.selectbox("Kết luận chung", ["Đạt", "Không đạt", "Đạt có điều kiện"])
            submitted = st.form_submit_button("💾 Lưu vào cơ sở dữ liệu", use_container_width=True)
        if submitted:
            order_id = None
            if order_choice != "-- Không gắn đơn hàng --":
                order_id = int(order_choice.replace("Đơn #", ""))
            insert_row("qc_outbound", {
                "order_id": order_id, "check_date": str(check_date), "servings_checked": servings_checked,
                "temp_check": temp_check, "portion_check": portion_check, "packaging_check": packaging_check,
                "label_check": label_check, "inspector": inspector, "approver": approver,
                "overall_result": overall_result,
            })
            st.success("Đã lưu kết quả QC đầu ra.")
            st.rerun()

    with tab_chart:
        if view.empty:
            empty_chart_placeholder()
        else:
            v = view.copy()
            v["check_date_dt"] = pd.to_datetime(v["check_date"], errors="coerce")

            g1, g2 = st.columns(2)
            with g1:
                cnt = v.groupby("overall_result").size().reset_index(name="Số lượt")
                fig1 = px.pie(cnt, names="overall_result", values="Số lượt", title="① Tỷ lệ kết luận chung QC đầu ra")
                st.plotly_chart(style_chart(fig1), use_container_width=True)
            with g2:
                checks = ["temp_check", "portion_check", "packaging_check", "label_check"]
                fail_counts = {c: (v[c] == "Không đạt").sum() for c in checks}
                fail_df = pd.DataFrame({"Hạng mục": list(fail_counts.keys()), "Số lần không đạt": list(fail_counts.values())})
                fig2 = px.bar(fail_df, x="Hạng mục", y="Số lần không đạt", title="② Số lần không đạt theo từng hạng mục kiểm tra")
                st.plotly_chart(style_chart(fig2), use_container_width=True)

            g3, g4 = st.columns(2)
            with g3:
                trend = v.groupby(v["check_date_dt"].dt.date).size().reset_index(name="Số lượt kiểm tra")
                fig3 = px.line(trend, x="check_date_dt", y="Số lượt kiểm tra", markers=True, title="③ Số lượt kiểm tra QC đầu ra theo ngày")
                st.plotly_chart(style_chart(fig3), use_container_width=True)
            with g4:
                fig4 = px.bar(v.groupby("inspector").size().reset_index(name="Số lượt"), x="inspector", y="Số lượt",
                               title="④ Số lượt kiểm tra theo từng nhân viên QC")
                st.plotly_chart(style_chart(fig4), use_container_width=True)

            fig5 = px.scatter(v, x="servings_checked", y="overall_result", color="overall_result",
                               title="⑤ Tương quan Số suất kiểm tra vs Kết luận chung")
            st.plotly_chart(style_chart(fig5, height=420), use_container_width=True)
