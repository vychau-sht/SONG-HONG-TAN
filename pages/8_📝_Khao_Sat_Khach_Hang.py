"""
MENU CHA: 📝 KHẢO SÁT KHÁCH HÀNG
Ghi nhận đánh giá của khách hàng sau mỗi đơn hàng: khẩu vị, dịch vụ, bao bì, giao hàng.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from database import init_db, read_table, insert_row, delete_row
from utils import require_login, sidebar_user_box, inject_css, sheet_header, style_chart, export_excel_button, empty_chart_placeholder

st.set_page_config(page_title="Khảo sát khách hàng — SHT/PBG", page_icon="📝", layout="wide")
init_db()
inject_css()
require_login()
sidebar_user_box()

st.title("📝 KHẢO SÁT KHÁCH HÀNG")

customers = read_table("customers")
orders = read_table("orders")
surveys = read_table("customer_surveys", order_by="survey_date DESC")

sheet_header("📝", "SHEET: Khảo sát khách hàng", "Thang điểm 1-10 cho từng tiêu chí sau mỗi đơn hàng")
tab_list, tab_form, tab_chart = st.tabs(["📋 Danh sách", "➕ Nhập liệu", "📊 Biểu đồ"])

view = surveys.copy()
if not surveys.empty:
    if not customers.empty:
        view = view.merge(customers[["id", "name"]], left_on="customer_id", right_on="id", suffixes=("", "_kh"), how="left")
    view["overall_score"] = view[["taste_score", "service_score", "packaging_score", "delivery_score"]].mean(axis=1).round(2)

# ====================================================================
# TAB: DANH SÁCH
# ====================================================================
with tab_list:
    st.dataframe(view, use_container_width=True, hide_index=True)
    export_excel_button({"Khao_sat_KH": view}, "khao_sat_khach_hang.xlsx")
    if not surveys.empty:
        st.markdown("###### 🗑️ Xoá 1 phiếu khảo sát")
        sel_id = st.selectbox("Chọn theo id", surveys["id"], key="ks_sel")
        if st.button("🗑️ Xoá", key="ks_del"):
            delete_row("customer_surveys", int(sel_id))
            st.warning("Đã xoá.")
            st.rerun()

# ====================================================================
# TAB: NHẬP LIỆU
# ====================================================================
with tab_form:
    st.markdown("###### ➕ Ghi nhận phiếu khảo sát mới (dùng phím Tab để chuyển ô)")
    customer_opts = customers[["id", "name"]].values.tolist() if not customers.empty else []
    order_opts = orders[["id"]].values.tolist() if not orders.empty else []
    if not customer_opts:
        st.warning("Cần có ít nhất 1 Khách hàng trước (🧑‍🤝‍🧑 Khách hàng & Đơn hàng).")
    else:
        with st.form("form_ks", clear_on_submit=True):
            c1, c2 = st.columns(2)
            customer_choice = c1.selectbox("Khách hàng *", [f"{c[0]} - {c[1]}" for c in customer_opts])
            order_choice = c2.selectbox("Đơn hàng liên quan", ["-- Không gắn đơn hàng --"] + [f"Đơn #{o[0]}" for o in order_opts])
            survey_date = st.date_input("Ngày khảo sát")
            c3, c4 = st.columns(2)
            taste_score = c3.slider("Điểm khẩu vị món ăn", 1, 10, 8)
            service_score = c4.slider("Điểm thái độ phục vụ", 1, 10, 8)
            c5, c6 = st.columns(2)
            packaging_score = c5.slider("Điểm bao bì / trình bày", 1, 10, 8)
            delivery_score = c6.slider("Điểm đúng giờ giao hàng", 1, 10, 8)
            respondent = st.text_input("Người trả lời khảo sát (tên/chức vụ phía KH)")
            comment = st.text_area("Ý kiến / góp ý thêm")
            submitted = st.form_submit_button("💾 Lưu vào cơ sở dữ liệu", use_container_width=True)
        if submitted:
            order_id = None
            if order_choice != "-- Không gắn đơn hàng --":
                order_id = int(order_choice.replace("Đơn #", ""))
            insert_row("customer_surveys", {
                "customer_id": int(customer_choice.split(" - ")[0]), "order_id": order_id,
                "survey_date": str(survey_date), "taste_score": taste_score, "service_score": service_score,
                "packaging_score": packaging_score, "delivery_score": delivery_score,
                "comment": comment, "respondent": respondent,
            })
            st.success("Đã lưu phiếu khảo sát.")
            st.rerun()

# ====================================================================
# TAB: BIỂU ĐỒ (6 biểu đồ)
# ====================================================================
with tab_chart:
    if view.empty:
        empty_chart_placeholder()
    else:
        v = view.copy()
        v["survey_date_dt"] = pd.to_datetime(v["survey_date"], errors="coerce")
        name_col = "name" if "name" in v.columns else "customer_id"

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("⭐ Khẩu vị TB", f"{v['taste_score'].mean():.1f}/10")
        m2.metric("⭐ Dịch vụ TB", f"{v['service_score'].mean():.1f}/10")
        m3.metric("⭐ Bao bì TB", f"{v['packaging_score'].mean():.1f}/10")
        m4.metric("⭐ Giao hàng TB", f"{v['delivery_score'].mean():.1f}/10")

        g1, g2 = st.columns(2)
        with g1:
            avg_scores = pd.DataFrame({
                "Tiêu chí": ["Khẩu vị", "Dịch vụ", "Bao bì", "Giao hàng"],
                "Điểm TB": [v["taste_score"].mean(), v["service_score"].mean(), v["packaging_score"].mean(), v["delivery_score"].mean()],
            })
            fig1 = px.line_polar(avg_scores, r="Điểm TB", theta="Tiêu chí", line_close=True,
                                  title="① Biểu đồ radar — Điểm trung bình theo 4 tiêu chí")
            fig1.update_traces(fill="toself")
            st.plotly_chart(style_chart(fig1), use_container_width=True)
        with g2:
            fig2 = px.bar(v.groupby(name_col)["overall_score"].mean().reset_index().sort_values("overall_score", ascending=False),
                           x=name_col, y="overall_score", title="② Điểm tổng thể trung bình theo khách hàng")
            st.plotly_chart(style_chart(fig2), use_container_width=True)

        g3, g4 = st.columns(2)
        with g3:
            trend = v.groupby(v["survey_date_dt"].dt.date)["overall_score"].mean().reset_index()
            fig3 = px.line(trend, x="survey_date_dt", y="overall_score", markers=True, title="③ Xu hướng điểm hài lòng theo thời gian")
            st.plotly_chart(style_chart(fig3), use_container_width=True)
        with g4:
            fig4 = px.box(v, y=["taste_score", "service_score", "packaging_score", "delivery_score"],
                           title="④ Phân bố điểm theo từng tiêu chí")
            st.plotly_chart(style_chart(fig4), use_container_width=True)

        g5, g6 = st.columns(2)
        with g5:
            bins = pd.cut(v["overall_score"], bins=[0, 5, 7, 8.5, 10], labels=["Kém (≤5)", "Trung bình (5-7)", "Tốt (7-8.5)", "Xuất sắc (>8.5)"])
            cnt = bins.value_counts().reset_index()
            cnt.columns = ["Mức đánh giá", "Số phiếu"]
            fig5 = px.pie(cnt, names="Mức đánh giá", values="Số phiếu", title="⑤ Cơ cấu mức độ hài lòng chung")
            st.plotly_chart(style_chart(fig5), use_container_width=True)
        with g6:
            fig6 = px.scatter(v, x="taste_score", y="service_score", size="overall_score", color=name_col,
                               title="⑥ Tương quan Điểm khẩu vị vs Điểm dịch vụ")
            st.plotly_chart(style_chart(fig6), use_container_width=True)
