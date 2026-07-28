"""
seed_data.py — Nạp dữ liệu THẬT từ file JSON gốc (sht-pbg-data...json) vào
database SQLite (sht_pbg.db) của app SHT/PBG.

Cách chạy:
    python3 seed_data.py duong_dan_toi_file.json

Chạy 1 lần duy nhất trên máy có sht_pbg.db (hoặc chưa có, script sẽ tự tạo).
An toàn để chạy lại nhiều lần: mỗi lần chạy sẽ XOÁ SẠCH dữ liệu cũ trong các
bảng liên quan rồi nạp lại từ JSON (không tạo trùng lặp).
"""

import json
import sys
from datetime import datetime

from database import init_db, get_connection, now_str


def to_frac(v):
    """Chuyển số phần trăm kiểu 95 (nghĩa là 95%) sang tỉ lệ 0.95. Nếu đã <=1 thì giữ nguyên."""
    if v is None:
        return 1.0
    v = float(v)
    return v / 100.0 if v > 1 else v


def norm_tx_type(v):
    if v and "Nhập" in v:
        return "Nhập"
    if v and "Xuất" in v:
        return "Xuất"
    return v or "Nhập"


def main(json_path):
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    init_db()
    conn = get_connection()
    cur = conn.cursor()

    # Xoá dữ liệu cũ (giữ nguyên schema) để tránh trùng lặp khi chạy lại
    tables = [
        "supplier_quotes", "bom", "routing", "warehouse_tx", "qc_inbound", "qc_outbound",
        "customer_surveys", "approvals", "delegations", "orders", "contracts",
        "materials", "products", "customers", "suppliers", "direct_costs",
        "indirect_costs", "labor_machine_hours",
    ]
    for t in tables:
        cur.execute(f"DELETE FROM {t}")
    conn.commit()

    # ---- Map role id -> tên vai trò hiển thị ----
    role_name = {r["id"]: r["name"] for r in data.get("roles", [])}

    # ---- SUPPLIERS ----
    sup_map = {}
    for s in data.get("suppliers", []):
        cur.execute(
            "INSERT INTO suppliers (name, contact, lead_time_days, payment_terms, rating, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (s.get("name"), s.get("contact"), s.get("leadTime", 0), s.get("payment"),
             s.get("rating", 0), now_str()),
        )
        sup_map[s["id"]] = cur.lastrowid

    # ---- CUSTOMERS ----
    cust_map = {}
    for c in data.get("customers", []):
        cur.execute(
            "INSERT INTO customers (name, contract_type, min_volume, price_adj, status, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (c.get("name"), c.get("contractType"), c.get("minVolume", 0), 0, c.get("status"), now_str()),
        )
        cust_map[c["id"]] = cur.lastrowid

    # ---- MATERIALS ----
    mat_map = {}
    for m in data.get("materials", []):
        cur.execute(
            "INSERT INTO materials (code, name, category, unit, price, supplier_id, min_stock, created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (m.get("code"), m.get("name"), m.get("category"), m.get("unit"), m.get("price", 0),
             sup_map.get(m.get("supplierRef")), m.get("minStock", 0), now_str()),
        )
        mat_map[m["id"]] = cur.lastrowid

    # ---- PRODUCTS ----
    prod_map = {}
    for p in data.get("products", []):
        cur.execute(
            "INSERT INTO products (code, name, dish_group, selling_price, target_food_cost_max, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (p.get("code"), p.get("name"), p.get("dishGroup"), p.get("sellingPrice", 0),
             p.get("targetFoodCostMax", 0), now_str()),
        )
        prod_map[p["id"]] = cur.lastrowid

    # ---- BOM ----
    for b in data.get("bom", []):
        pid = prod_map.get(b.get("productRef"))
        mid = mat_map.get(b.get("materialRef"))
        if not pid or not mid:
            continue
        cur.execute(
            "INSERT INTO bom (product_id, material_id, stage, raw_qty, yield_prep, yield_cook, transport_loss) "
            "VALUES (?,?,?,?,?,?,?)",
            (pid, mid, b.get("stage"), b.get("rawQty", 0), to_frac(b.get("yieldPrep")),
             to_frac(b.get("yieldCook")), to_frac(b.get("transportLoss", 0))),
        )

    # ---- ROUTING ----
    for r in data.get("routing", []):
        pid = prod_map.get(r.get("productRef"))
        if not pid:
            continue
        cur.execute(
            "INSERT INTO routing (product_id, seq, step_name, station, alloc_base, cycle_time_sec, "
            "operators, wait_before_sec, wait_after_sec, downtime_sec) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (pid, r.get("seq", 1), r.get("stepName"), r.get("station"), "Theo giờ công trực tiếp",
             r.get("cycleTime", 0), r.get("operators", 1), r.get("waitBefore", 0),
             r.get("waitAfter", 0), r.get("downtime", 0)),
        )

    # ---- DIRECT COSTS ----
    for d in data.get("directCosts", []):
        cur.execute(
            "INSERT INTO direct_costs (period, category, item, amount) VALUES (?,?,?,?)",
            (d.get("period"), d.get("category"), d.get("item"), d.get("amount", 0)),
        )

    # ---- INDIRECT COSTS ----
    for ic in data.get("indirectCosts", []):
        cur.execute(
            "INSERT INTO indirect_costs (period, group_name, amount, alloc_base) VALUES (?,?,?,?)",
            (ic.get("period"), ic.get("group"), ic.get("amount", 0), ic.get("allocBase")),
        )

    # ---- SUPPLIER QUOTES ----
    for q in data.get("supplierQuotes", []):
        sid = sup_map.get(q.get("supplierRef"))
        mid = mat_map.get(q.get("materialRef"))
        if not sid or not mid:
            continue
        cur.execute(
            "INSERT INTO supplier_quotes (supplier_id, material_id, price, quote_date, note, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (sid, mid, q.get("gia", 0), q.get("ngayBaoGia"), q.get("ghiChu"), now_str()),
        )

    # ---- CONTRACTS ----
    for c in data.get("contracts", []):
        cid = cust_map.get(c.get("customerRef"))
        if not cid:
            continue
        cur.execute(
            "INSERT INTO contracts (customer_id, contract_no, sign_date, effective_from, effective_to, "
            "contract_value, status) VALUES (?,?,?,?,?,?,?)",
            (cid, c.get("contractNo"), c.get("signDate"), c.get("effectiveFrom"), c.get("effectiveTo"),
             c.get("contractValue", 0), c.get("status")),
        )

    # ---- ORDERS ----
    for o in data.get("orders", []):
        cid = cust_map.get(o.get("customerRef"))
        pid = prod_map.get(o.get("productRef"))
        if not cid:
            continue
        cur.execute(
            "INSERT INTO orders (customer_id, product_id, order_date, delivery_date, servings, priority, status) "
            "VALUES (?,?,?,?,?,?,?)",
            (cid, pid, o.get("orderDate"), o.get("deliveryDate"), o.get("servings", 0),
             o.get("priority"), o.get("status")),
        )

    # ---- WAREHOUSE TX ----
    for w in data.get("warehouseTx", []):
        mid = mat_map.get(w.get("materialRef"))
        if not mid:
            continue
        cur.execute(
            "INSERT INTO warehouse_tx (material_id, tx_type, qty, tx_date, reference, keeper, note) "
            "VALUES (?,?,?,?,?,?,?)",
            (mid, norm_tx_type(w.get("type")), w.get("qty", 0), w.get("date"), w.get("reference"),
             w.get("keeper"), w.get("note")),
        )

    # ---- QC INBOUND ----
    for qi in data.get("qcInbound", []):
        mid = mat_map.get(qi.get("materialRef"))
        sid = sup_map.get(qi.get("supplierRef"))
        if not mid:
            continue
        cur.execute(
            "INSERT INTO qc_inbound (material_id, supplier_id, lot_no, received_qty, sample_size, "
            "defects_found, result, inspector, approver, inspected_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (mid, sid, qi.get("lotNo"), qi.get("receivedQty", 0), qi.get("sampleSizeOverride") or 5,
             qi.get("defectsFound", 0), qi.get("result"), qi.get("inspector"), qi.get("approver"),
             qi.get("inspectedAt")),
        )

    # ---- QC OUTBOUND ----
    for qo in data.get("qcOutbound", []):
        cur.execute(
            "INSERT INTO qc_outbound (order_id, check_date, servings_checked, temp_check, portion_check, "
            "packaging_check, label_check, inspector, approver, overall_result) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (None, qo.get("checkDate"), qo.get("servingsChecked", 0), str(qo.get("tempCheck")),
             qo.get("portionCheck"), qo.get("packagingCheck"), qo.get("labelCheck"),
             qo.get("inspector"), qo.get("approver"), qo.get("overallResult")),
        )

    # ---- CUSTOMER SURVEYS ---- (JSON chỉ có 1 điểm chung -> gán cho cả 4 tiêu chí)
    for sv in data.get("surveys", []):
        cid = cust_map.get(sv.get("customerRef"))
        if not cid:
            continue
        score = sv.get("score", 0)
        cur.execute(
            "INSERT INTO customer_surveys (customer_id, order_id, survey_date, taste_score, service_score, "
            "packaging_score, delivery_score, comment, respondent) VALUES (?,?,?,?,?,?,?,?,?)",
            (cid, None, sv.get("date"), score, score, score, score, sv.get("feedback"), sv.get("method")),
        )

    # ---- USERS ---- (giữ tài khoản admin mặc định nếu trùng username)
    for u in data.get("users", []):
        cur.execute("SELECT id FROM users WHERE username = ?", (u.get("username"),))
        if cur.fetchone():
            continue
        cur.execute(
            "INSERT INTO users (username, password, full_name, role, created_at) VALUES (?,?,?,?,?)",
            (u.get("username"), u.get("password"), u.get("fullName"),
             role_name.get(u.get("roleRef"), "user"), now_str()),
        )

    conn.commit()
    conn.close()
    print("Đã nạp xong dữ liệu mẫu từ JSON vào sht_pbg.db")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Cách dùng: python3 seed_data.py duong_dan_file.json")
        sys.exit(1)
    main(sys.argv[1])
