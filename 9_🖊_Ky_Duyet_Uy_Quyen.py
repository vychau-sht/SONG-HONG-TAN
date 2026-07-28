"""
MENU CHA: ✍️ KÝ DUYỆT ĐIỆN TỬ & ỦY QUYỀN
MENU CON: Ký duyệt (đơn hàng/hợp đồng/chi phí...) | Ủy quyền (phân quyền tạm thời)
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from database import init_db, read_table, insert_row, update_row, delete_row, now_str
from utils import require_login, sidebar_user_box, inject_css, sheet_header, style_chart, export_excel_button, empty_chart_placeholder

st.set_page_config(page_title="Ký duyệt & Ủy quyền — SHT/PBG", page_icon="✍️", layout="wide")
init_db()
inject_css()
require_login()
sidebar_user_box()

st.title("✍️ KÝ DUYỆT ĐIỆN TỬ & ỦY QUYỀN")

menu_con = st.tabs(["✅ Ký duyệt", "🔑 Ủy quyền"])

# ====================================================================
# MENU CON 1: KÝ DUYỆT  (SHEET)
# ====================================================================
with menu_con[0]:
    sheet_header("✅", "SHEET: Ký duyệt điện tử", "Luồng phê duyệt cho đơn hàng, hợp đồng, chi phí, thay đổi định mức...")
    tab_list, tab_form, tab_action, tab_chart = st.tabs(["📋 Danh sách", "➕ Tạo yêu cầu", "🖊️ Phê duyệt", "📊 Biểu đồ"])

    approvals = read_table("approvals", order_by="requested_at DESC")

    with tab_list:
        st.dataframe(approvals, use_container_width=True, hide_index=True)
        export_excel_button({"Ky_duyet": approvals}, "ky_duyet.xlsx")
        if not approvals.empty:
            st.markdown("###### 🗑️ Xoá yêu cầu")
            sel_id = st.selectbox("Chọn theo id", approvals["id"], key="kd_del_sel")
            if st.button("🗑️ Xoá", key="kd_del"):
                delete_row("approvals", int(sel_id))
                st.warning("Đã xoá.")
                st.rerun()

    with tab_form:
        st.markdown("###### ➕ Tạo yêu cầu ký duyệt mới (dùng phím Tab để chuyển ô)")
        with st.form("form_kd", clear_on_submit=True):
            c1, c2 = st.columns(2)
            ref_type = c1.selectbox("Loại yêu cầu *", [
                "Đơn hàng", "Hợp đồng", "Chi phí", "Thay đổi định mức BOM", "Báo giá NCC", "Khác",
            ])
            approval_level = c2.selectbox("Cấp phê duyệt", ["Cấp 1 (Trưởng bộ phận)", "Cấp 2 (Giám đốc)", "Cấp 3 (Tổng giám đốc)"])
            ref_description = st.text_input("Mô tả nội dung cần duyệt *")
            c3, c4 = st.columns(2)
            requested_by = c3.text_input("Người đề xuất *")
            approver = c4.text_input("Người duyệt (dự kiến)")
            submitted = st.form_submit_button("💾 Gửi yêu cầu ký duyệt", use_container_width=True)
        if submitted:
            if not ref_description.strip() or not requested_by.strip():
                st.error("Vui lòng nhập đủ Mô tả và Người đề xuất.")
            else:
                insert_row("approvals", {
                    "ref_type": ref_type, "ref_description": ref_description, "requested_by": requested_by,
                    "approver": approver, "approval_level": approval_level, "status": "Chờ duyệt",
                    "requested_at": now_str(), "decided_at": None, "comment": None,
                })
                st.success("Đã tạo yêu cầu ký duyệt.")
                st.rerun()

    with tab_action:
        st.markdown("###### 🖊️ Xử lý các yêu cầu đang chờ duyệt")
        pending = approvals[approvals["status"] == "Chờ duyệt"] if not approvals.empty else approvals
        if pending.empty:
            st.info("Không có yêu cầu nào đang chờ duyệt. ✅")
        else:
            sel_id = st.selectbox(
                "Chọn yêu cầu cần xử lý",
                pending["id"],
                format_func=lambda i: f"#{i} - {pending[pending['id']==i]['ref_description'].values[0]}",
                key="kd_action_sel",
            )
            row = pending[pending["id"] == sel_id].iloc[0]
            st.write(f"**Loại:** {row['ref_type']} · **Cấp duyệt:** {row['approval_level']} · **Người đề xuất:** {row['requested_by']}")
            c1, c2 = st.columns(2)
            decision_comment = c1.text_input("Ý kiến / lý do (nếu từ chối)")
            decided_by = c2.text_input("Người ký duyệt thực tế *")
            b1, b2 = st.columns(2)
            if b1.button("✅ Phê duyệt", use_container_width=True, key="kd_approve"):
                if not decided_by.strip():
                    st.error("Vui lòng nhập tên người ký duyệt.")
                else:
                    update_row("approvals", int(sel_id), {
                        "status": "Đã duyệt", "approver": decided_by, "decided_at": now_str(), "comment": decision_comment,
                    })
                    st.success("Đã phê duyệt.")
                    st.rerun()
            if b2.button("❌ Từ chối", use_container_width=True, key="kd_reject"):
                if not decided_by.strip():
                    st.error("Vui lòng nhập tên người từ chối.")
                else:
                    update_row("approvals", int(sel_id), {
                        "status": "Từ chối", "approver": decided_by, "decided_at": now_str(), "comment": decision_comment,
                    })
                    st.warning("Đã từ chối yêu cầu.")
                    st.rerun()

    with tab_chart:
        if approvals.empty:
            empty_chart_placeholder()
        else:
            a = approvals.copy()
            a["requested_at_dt"] = pd.to_datetime(a["requested_at"], errors="coerce")

            g1, g2 = st.columns(2)
            with g1:
                cnt = a.groupby("status").size().reset_index(name="Số lượng")
                fig1 = px.pie(cnt, names="status", values="Số lượng", title="① Cơ cấu trạng thái ký duyệt")
                st.plotly_chart(style_chart(fig1), use_container_width=True)
            with g2:
                cnt2 = a.groupby("ref_type").size().reset_index(name="Số lượng")
                fig2 = px.bar(cnt2.sort_values("Số lượng", ascending=False), x="ref_type", y="Số lượng",
                               title="② Số yêu cầu theo loại")
                st.plotly_chart(style_chart(fig2), use_container_width=True)

            g3, g4 = st.columns(2)
            with g3:
                cnt3 = a.groupby("approval_level").size().reset_index(name="Số lượng")
                fig3 = px.bar(cnt3, x="approval_level", y="Số lượng", title="③ Số yêu cầu theo cấp phê duyệt")
                st.plotly_chart(style_chart(fig3), use_container_width=True)
            with g4:
                trend = a.groupby(a["requested_at_dt"].dt.date).size().reset_index(name="Số yêu cầu")
                fig4 = px.line(trend, x="requested_at_dt", y="Số yêu cầu", markers=True, title="④ Số yêu cầu ký duyệt theo ngày")
                st.plotly_chart(style_chart(fig4), use_container_width=True)

            fig5 = px.bar(a.groupby("requested_by").size().reset_index(name="Số yêu cầu").sort_values("Số yêu cầu", ascending=False),
                           x="requested_by", y="Số yêu cầu", title="⑤ Số yêu cầu theo người đề xuất")
            st.plotly_chart(style_chart(fig5, height=420), use_container_width=True)

# ====================================================================
# MENU CON 2: ỦY QUYỀN  (SHEET)
# ====================================================================
with menu_con[1]:
    sheet_header("🔑", "SHEET: Ủy quyền", "Ủy quyền tạm thời cho người khác ký duyệt thay khi vắng mặt")
    tab_list, tab_form, tab_chart = st.tabs(["📋 Danh sách", "➕ Nhập liệu", "📊 Biểu đồ"])

    delegations = read_table("delegations", order_by="valid_from DESC")

    with tab_list:
        st.dataframe(delegations, use_container_width=True, hide_index=True)
        export_excel_button({"Uy_quyen": delegations}, "uy_quyen.xlsx")
        if not delegations.empty:
            st.markdown("###### ✏️ Cập nhật trạng thái / 🗑️ Xoá")
            sel_id = st.selectbox("Chọn theo id", delegations["id"], key="uq_sel")
            row = delegations[delegations["id"] == sel_id].iloc[0]
            new_status = st.selectbox("Trạng thái", ["Hiệu lực", "Hết hạn", "Thu hồi"],
                                       index=["Hiệu lực", "Hết hạn", "Thu hồi"].index(row["status"]) if row["status"] in ["Hiệu lực", "Hết hạn", "Thu hồi"] else 0,
                                       key="uq_edit_status")
            b1, b2 = st.columns(2)
            if b1.button("💾 Lưu cập nhật", use_container_width=True, key="uq_save"):
                update_row("delegations", int(sel_id), {"status": new_status})
                st.success("Đã cập nhật.")
                st.rerun()
            if b2.button("🗑️ Xoá bản ghi này", use_container_width=True, key="uq_del"):
                delete_row("delegations", int(sel_id))
                st.warning("Đã xoá.")
                st.rerun()

    with tab_form:
        st.markdown("###### ➕ Tạo ủy quyền mới (dùng phím Tab để chuyển ô)")
        with st.form("form_uq", clear_on_submit=True):
            c1, c2 = st.columns(2)
            delegator = c1.text_input("Người ủy quyền (đi vắng) *")
            delegate = c2.text_input("Người được ủy quyền *")
            scope = st.text_input("Phạm vi ủy quyền (vd: Ký duyệt đơn hàng ≤ 50 triệu)")
            c3, c4 = st.columns(2)
            valid_from = c3.date_input("Hiệu lực từ")
            valid_to = c4.date_input("Hiệu lực đến")
            note = st.text_input("Ghi chú")
            submitted = st.form_submit_button("💾 Lưu vào cơ sở dữ liệu", use_container_width=True)
        if submitted:
            if not delegator.strip() or not delegate.strip():
                st.error("Vui lòng nhập đủ Người ủy quyền và Người được ủy quyền.")
            else:
                insert_row("delegations", {
                    "delegator": delegator, "delegate": delegate, "scope": scope,
                    "valid_from": str(valid_from), "valid_to": str(valid_to), "status": "Hiệu lực", "note": note,
                })
                st.success("Đã lưu ủy quyền.")
                st.rerun()

    with tab_chart:
        if delegations.empty:
            empty_chart_placeholder()
        else:
            d = delegations.copy()
            d["valid_from_dt"] = pd.to_datetime(d["valid_from"], errors="coerce")
            d["valid_to_dt"] = pd.to_datetime(d["valid_to"], errors="coerce")
            d["so_ngay"] = (d["valid_to_dt"] - d["valid_from_dt"]).dt.days

            g1, g2 = st.columns(2)
            with g1:
                cnt = d.groupby("status").size().reset_index(name="Số lượng")
                fig1 = px.pie(cnt, names="status", values="Số lượng", title="① Cơ cấu trạng thái ủy quyền")
                st.plotly_chart(style_chart(fig1), use_container_width=True)
            with g2:
                fig2 = px.bar(d.groupby("delegator").size().reset_index(name="Số lần ủy quyền"),
                               x="delegator", y="Số lần ủy quyền", title="② Số lần ủy quyền theo người ủy quyền")
                st.plotly_chart(style_chart(fig2), use_container_width=True)

            g3, g4 = st.columns(2)
            with g3:
                fig3 = px.bar(d.groupby("delegate").size().reset_index(name="Số lần nhận ủy quyền"),
                               x="delegate", y="Số lần nhận ủy quyền", title="③ Số lần nhận ủy quyền theo người được ủy quyền")
                st.plotly_chart(style_chart(fig3), use_container_width=True)
            with g4:
                fig4 = px.histogram(d, x="so_ngay", nbins=10, title="④ Phân bố thời lượng ủy quyền (số ngày)")
                st.plotly_chart(style_chart(fig4), use_container_width=True)

            fig5 = px.timeline(d, x_start="valid_from_dt", x_end="valid_to_dt", y="delegator", color="status",
                                title="⑤ Dòng thời gian hiệu lực các ủy quyền")
            st.plotly_chart(style_chart(fig5, height=420), use_container_width=True)
