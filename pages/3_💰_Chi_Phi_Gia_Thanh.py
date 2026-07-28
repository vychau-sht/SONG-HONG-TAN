"""
MENU CHA: 💰 CHI PHÍ & GIÁ THÀNH
MENU CON: Chi phí trực tiếp | Chi phí gián tiếp (SXC) | Giờ công & giờ máy | 🧮 Tính giá thành (ABC)
Engine tính giá thành áp dụng ĐÚNG 5 bước công thức trong file Word gốc của bạn.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from database import init_db, read_table, insert_row, update_row, delete_row
from utils import require_login, sidebar_user_box, inject_css, sheet_header, style_chart, export_excel_button, empty_chart_placeholder
from costing_engine import get_labor_rate, get_overhead_rates, full_product_cost

st.set_page_config(page_title="Chi phí & Giá thành — SHT/PBG", page_icon="💰", layout="wide")
init_db()
inject_css()
require_login()
sidebar_user_box()

st.title("💰 CHI PHÍ & GIÁ THÀNH")

menu_con = st.tabs(["💵 Chi phí trực tiếp", "🏢 Chi phí gián tiếp (SXC)", "⏱️ Giờ công & Giờ máy", "🧮 Tính giá thành (ABC)"])

# ====================================================================
# MENU CON 1: CHI PHÍ TRỰC TIẾP  (SHEET)
# ====================================================================
with menu_con[0]:
    sheet_header("💵", "SHEET: Chi phí trực tiếp", "Nhân công trực tiếp + NVL trực tiếp theo từng kỳ chi phí")
    tab_list, tab_form, tab_chart = st.tabs(["📋 Danh sách", "➕ Nhập liệu", "📊 Biểu đồ"])

    dc = read_table("direct_costs", order_by="period")

    with tab_list:
        st.dataframe(dc, use_container_width=True, hide_index=True)
        export_excel_button({"Chi_phi_truc_tiep": dc}, "chi_phi_truc_tiep.xlsx")
        if not dc.empty:
            st.markdown("###### 🗑️ Xoá dòng")
            sel_id = st.selectbox("Chọn dòng theo id", dc["id"], key="dc_sel")
            if st.button("🗑️ Xoá dòng này", key="dc_del"):
                delete_row("direct_costs", int(sel_id))
                st.warning("Đã xoá.")
                st.rerun()

    with tab_form:
        st.markdown("###### ➕ Thêm chi phí trực tiếp (dùng phím Tab để chuyển ô)")
        with st.form("form_dc", clear_on_submit=True):
            c1, c2 = st.columns(2)
            period = c1.text_input("Kỳ chi phí (vd: 2026-07)", value="2026-07")
            category = c2.selectbox("Loại chi phí", ["Nhân công trực tiếp", "NVL trực tiếp", "Khác"])
            c3, c4 = st.columns(2)
            item = c3.text_input("Diễn giải khoản mục")
            amount = c4.number_input("Số tiền (đ)", min_value=0.0, value=0.0)
            submitted = st.form_submit_button("💾 Lưu vào cơ sở dữ liệu", use_container_width=True)
        if submitted:
            insert_row("direct_costs", {"period": period, "category": category, "item": item, "amount": amount})
            st.success("Đã lưu chi phí trực tiếp.")
            st.rerun()

    with tab_chart:
        if dc.empty:
            empty_chart_placeholder()
        else:
            g1, g2 = st.columns(2)
            with g1:
                fig1 = px.bar(dc.groupby(["period", "category"])["amount"].sum().reset_index(),
                               x="period", y="amount", color="category", title="① Chi phí trực tiếp theo kỳ và loại", barmode="stack")
                st.plotly_chart(style_chart(fig1), use_container_width=True)
            with g2:
                fig2 = px.pie(dc, names="category", values="amount", title="② Cơ cấu chi phí trực tiếp theo loại")
                st.plotly_chart(style_chart(fig2), use_container_width=True)

            g3, g4 = st.columns(2)
            with g3:
                fig3 = px.line(dc.groupby("period")["amount"].sum().reset_index(), x="period", y="amount",
                                markers=True, title="③ Xu hướng tổng chi phí trực tiếp theo kỳ")
                st.plotly_chart(style_chart(fig3), use_container_width=True)
            with g4:
                fig4 = px.bar(dc.sort_values("amount", ascending=False).head(10), x="item", y="amount",
                               title="④ Top 10 khoản mục chi phí trực tiếp lớn nhất")
                st.plotly_chart(style_chart(fig4), use_container_width=True)

            fig5 = px.box(dc, x="category", y="amount", title="⑤ Phân bố số tiền theo loại chi phí trực tiếp")
            st.plotly_chart(style_chart(fig5, height=420), use_container_width=True)

# ====================================================================
# MENU CON 2: CHI PHÍ GIÁN TIẾP (SXC)  (SHEET)
# ====================================================================
with menu_con[1]:
    sheet_header("🏢", "SHEET: Chi phí gián tiếp (SXC/Overhead)", "Chi phí sản xuất chung, chọn đúng cơ sở phân bổ")
    tab_list, tab_form, tab_chart = st.tabs(["📋 Danh sách", "➕ Nhập liệu", "📊 Biểu đồ"])

    ic = read_table("indirect_costs", order_by="period")

    with tab_list:
        st.dataframe(ic, use_container_width=True, hide_index=True)
        export_excel_button({"Chi_phi_gian_tiep": ic}, "chi_phi_gian_tiep.xlsx")
        if not ic.empty:
            st.markdown("###### 🗑️ Xoá dòng")
            sel_id = st.selectbox("Chọn dòng theo id", ic["id"], key="ic_sel")
            if st.button("🗑️ Xoá dòng này", key="ic_del"):
                delete_row("indirect_costs", int(sel_id))
                st.warning("Đã xoá.")
                st.rerun()

    with tab_form:
        st.markdown("###### ➕ Thêm chi phí gián tiếp (dùng phím Tab để chuyển ô)")
        with st.form("form_ic", clear_on_submit=True):
            c1, c2 = st.columns(2)
            period = c1.text_input("Kỳ chi phí (vd: 2026-07)", value="2026-07")
            group_name = c2.text_input("Nhóm chi phí SXC", value="Điện, nước, khấu hao...")
            c3, c4 = st.columns(2)
            amount = c3.number_input("Số tiền (đ)", min_value=0.0, value=0.0)
            alloc_base = c4.selectbox("Cơ sở phân bổ *", ["Theo giờ công trực tiếp", "Theo giờ máy"])
            submitted = st.form_submit_button("💾 Lưu vào cơ sở dữ liệu", use_container_width=True)
        if submitted:
            insert_row("indirect_costs", {"period": period, "group_name": group_name, "amount": amount, "alloc_base": alloc_base})
            st.success("Đã lưu chi phí gián tiếp.")
            st.rerun()

    with tab_chart:
        if ic.empty:
            empty_chart_placeholder()
        else:
            g1, g2 = st.columns(2)
            with g1:
                fig1 = px.bar(ic.groupby(["period", "alloc_base"])["amount"].sum().reset_index(),
                               x="period", y="amount", color="alloc_base", title="① SXC theo kỳ và cơ sở phân bổ", barmode="stack")
                st.plotly_chart(style_chart(fig1), use_container_width=True)
            with g2:
                fig2 = px.pie(ic, names="group_name", values="amount", title="② Cơ cấu SXC theo nhóm chi phí")
                st.plotly_chart(style_chart(fig2), use_container_width=True)

            g3, g4 = st.columns(2)
            with g3:
                fig3 = px.line(ic.groupby("period")["amount"].sum().reset_index(), x="period", y="amount",
                                markers=True, title="③ Xu hướng tổng SXC theo kỳ")
                st.plotly_chart(style_chart(fig3), use_container_width=True)
            with g4:
                fig4 = px.pie(ic, names="alloc_base", values="amount", title="④ Tỷ trọng phân bổ: giờ công vs giờ máy")
                st.plotly_chart(style_chart(fig4), use_container_width=True)

            fig5 = px.bar(ic.sort_values("amount", ascending=False).head(10), x="group_name", y="amount",
                           title="⑤ Top 10 nhóm chi phí SXC lớn nhất")
            st.plotly_chart(style_chart(fig5, height=420), use_container_width=True)

# ====================================================================
# MENU CON 3: GIỜ CÔNG & GIỜ MÁY  (SHEET)
# ====================================================================
with menu_con[2]:
    sheet_header("⏱️", "SHEET: Giờ công trực tiếp & Giờ máy", "Mẫu số dùng để tính đơn giá lao động/giờ và đơn giá SXC/giờ")
    tab_list, tab_form, tab_chart = st.tabs(["📋 Danh sách", "➕ Nhập liệu", "📊 Biểu đồ"])

    lmh = read_table("labor_machine_hours", order_by="period")

    with tab_list:
        st.dataframe(lmh, use_container_width=True, hide_index=True)
        export_excel_button({"Gio_cong_gio_may": lmh}, "gio_cong_gio_may.xlsx")
        if not lmh.empty:
            st.markdown("###### 🗑️ Xoá dòng")
            sel_id = st.selectbox("Chọn dòng theo id", lmh["id"], key="lmh_sel")
            if st.button("🗑️ Xoá dòng này", key="lmh_del"):
                delete_row("labor_machine_hours", int(sel_id))
                st.warning("Đã xoá.")
                st.rerun()

    with tab_form:
        st.markdown("###### ➕ Thêm số liệu giờ công/giờ máy theo kỳ (dùng phím Tab để chuyển ô)")
        with st.form("form_lmh", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            period = c1.text_input("Kỳ chi phí (vd: 2026-07)", value="2026-07")
            total_labor_hours = c2.number_input("Tổng giờ công trực tiếp thực tế", min_value=0.0, value=0.0)
            total_machine_hours = c3.number_input("Tổng giờ máy chạy thực tế", min_value=0.0, value=0.0)
            submitted = st.form_submit_button("💾 Lưu vào cơ sở dữ liệu", use_container_width=True)
        if submitted:
            insert_row("labor_machine_hours", {
                "period": period, "total_labor_hours": total_labor_hours, "total_machine_hours": total_machine_hours,
            })
            st.success("Đã lưu số liệu giờ công/giờ máy.")
            st.rerun()

    with tab_chart:
        if lmh.empty:
            empty_chart_placeholder()
        else:
            g1, g2 = st.columns(2)
            with g1:
                fig1 = px.bar(lmh, x="period", y=["total_labor_hours", "total_machine_hours"],
                               title="① Giờ công vs Giờ máy theo kỳ", barmode="group")
                st.plotly_chart(style_chart(fig1), use_container_width=True)
            with g2:
                fig2 = px.line(lmh, x="period", y="total_labor_hours", markers=True, title="② Xu hướng giờ công trực tiếp")
                st.plotly_chart(style_chart(fig2), use_container_width=True)

            g3, g4 = st.columns(2)
            with g3:
                fig3 = px.line(lmh, x="period", y="total_machine_hours", markers=True, title="③ Xu hướng giờ máy")
                st.plotly_chart(style_chart(fig3), use_container_width=True)
            with g4:
                ratio = lmh.copy()
                ratio["ty_le"] = ratio["total_machine_hours"] / ratio["total_labor_hours"].replace(0, pd.NA)
                fig4 = px.bar(ratio, x="period", y="ty_le", title="④ Tỷ lệ giờ máy / giờ công theo kỳ")
                st.plotly_chart(style_chart(fig4), use_container_width=True)

            fig5 = px.area(lmh, x="period", y=["total_labor_hours", "total_machine_hours"],
                            title="⑤ Tích lũy giờ công & giờ máy theo thời gian")
            st.plotly_chart(style_chart(fig5, height=420), use_container_width=True)

# ====================================================================
# MENU CON 4: TÍNH GIÁ THÀNH (ENGINE ABC)  (SHEET)
# ====================================================================
with menu_con[3]:
    sheet_header("🧮", "SHEET: Tính giá thành theo Activity-Based Costing",
                 "Áp dụng đúng 5 bước công thức của bạn: Đơn giá lao động/giờ → Chi phí NC công đoạn → Phân bổ SXC → Tổng chi phí công đoạn → Giá vốn/suất")

    products = read_table("products")
    lmh = read_table("labor_machine_hours")
    periods = sorted(lmh["period"].unique().tolist()) if not lmh.empty else []

    tab_calc, tab_chart = st.tabs(["🧮 Tính giá thành", "📊 Biểu đồ"])

    with tab_calc:
        if products.empty or not periods:
            st.warning("Cần có ít nhất 1 Sản phẩm (📦 Danh mục) và 1 kỳ Giờ công/Giờ máy (tab bên cạnh) để tính giá thành.")
        else:
            c1, c2 = st.columns(2)
            product_choice = c1.selectbox("Chọn sản phẩm", [f"{p[0]} - {p[1]}" for p in products[["id", "name"]].values.tolist()])
            period_choice = c2.selectbox("Chọn kỳ chi phí", periods)
            product_id = int(product_choice.split(" - ")[0])

            labor_rate = get_labor_rate(period_choice)
            oh_rates = get_overhead_rates(period_choice)

            m1, m2, m3 = st.columns(3)
            m1.metric("Bước 1 — Đơn giá lao động/giờ", f"{labor_rate:,.0f} đ")
            m2.metric("Bước 3 — Đơn giá SXC/giờ công", f"{oh_rates['rate_per_labor_hour']:,.0f} đ")
            m3.metric("Bước 3 — Đơn giá SXC/giờ máy", f"{oh_rates['rate_per_machine_hour']:,.0f} đ")

            result = full_product_cost(product_id, period_choice)

            st.markdown("###### Bước 2-4 — Chi tiết chi phí từng công đoạn (routing)")
            st.dataframe(result["routing_detail"], use_container_width=True, hide_index=True)

            st.markdown("###### Bước 5 — Giá vốn/suất")
            r1, r2, r3 = st.columns(3)
            r1.metric("Chi phí NVL (BOM)", f"{result['bom_cost']:,.0f} đ")
            r2.metric("Chi phí công đoạn (routing)", f"{result['routing_cost']:,.0f} đ")
            r3.metric("🎯 GIÁ VỐN/SUẤT", f"{result['total_cost']:,.0f} đ")

            export_excel_button(
                {"Chi_tiet_cong_doan": result["routing_detail"],
                 "Tong_hop": pd.DataFrame([{
                     "Sản phẩm": product_choice, "Kỳ": period_choice,
                     "Chi phí NVL (BOM)": result["bom_cost"],
                     "Chi phí công đoạn": result["routing_cost"],
                     "Giá vốn/suất": result["total_cost"],
                 }])},
                f"gia_thanh_{product_id}_{period_choice}.xlsx",
                "📥 Xuất kết quả tính giá thành (Excel)",
            )

    with tab_chart:
        if products.empty or not periods:
            empty_chart_placeholder("Cần đủ dữ liệu Sản phẩm + Kỳ chi phí để vẽ biểu đồ giá thành.")
        else:
            rows = []
            for _, p in products.iterrows():
                for per in periods:
                    res = full_product_cost(int(p["id"]), per)
                    rows.append({"product": p["name"], "period": per, "bom_cost": res["bom_cost"],
                                 "routing_cost": res["routing_cost"], "total_cost": res["total_cost"]})
            all_costs = pd.DataFrame(rows)

            g1, g2 = st.columns(2)
            with g1:
                fig1 = px.bar(all_costs, x="product", y=["bom_cost", "routing_cost"], color_discrete_sequence=None,
                               title="① Cơ cấu giá vốn: NVL vs Công đoạn (theo sản phẩm)", barmode="stack")
                st.plotly_chart(style_chart(fig1), use_container_width=True)
            with g2:
                fig2 = px.bar(all_costs.sort_values("total_cost", ascending=False), x="product", y="total_cost",
                               color="period", title="② Giá vốn/suất theo sản phẩm & kỳ")
                st.plotly_chart(style_chart(fig2), use_container_width=True)

            merged_sell = all_costs.merge(products[["id", "name", "selling_price"]], left_on="product", right_on="name", how="left")
            merged_sell["gross_margin_pct"] = (
                (merged_sell["selling_price"] - merged_sell["total_cost"]) / merged_sell["selling_price"].replace(0, pd.NA) * 100
            )

            g3, g4 = st.columns(2)
            with g3:
                fig3 = px.bar(merged_sell, x="name", y="gross_margin_pct", title="③ Biên lợi nhuận gộp (%) theo sản phẩm")
                st.plotly_chart(style_chart(fig3), use_container_width=True)
            with g4:
                fig4 = px.scatter(merged_sell, x="total_cost", y="selling_price", size="gross_margin_pct",
                                   color="name", title="④ Tương quan Giá vốn vs Giá bán")
                st.plotly_chart(style_chart(fig4), use_container_width=True)

            fig5 = px.line(all_costs.sort_values("period"), x="period", y="total_cost", color="product", markers=True,
                            title="⑤ Xu hướng giá vốn/suất theo kỳ chi phí")
            st.plotly_chart(style_chart(fig5, height=420), use_container_width=True)
