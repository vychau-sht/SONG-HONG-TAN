"""
costing_engine.py — Cài đặt ĐÚNG 5 bước công thức trong file
"Công thức tính chi phí mỗi công đoạn.docx" mà bạn cung cấp:

Bước 1: Đơn giá lao động/giờ = Tổng Nhân công trực tiếp kỳ ÷ Tổng giờ công trực tiếp kỳ
Bước 2: Chi phí nhân công công đoạn = Cycle Time (giờ) × Operators × Đơn giá lao động/giờ
Bước 3: Phân bổ SXC theo đúng cơ sở phân bổ đã chọn (giờ công trực tiếp HOẶC giờ máy)
Bước 4: Chi phí công đoạn = Chi phí nhân công + Chi phí SXC phân bổ
Bước 5: Giá vốn/suất = Tổng chi phí NVL (BOM) + Σ Chi phí tất cả công đoạn (routing)
"""

import pandas as pd
from database import read_table, read_query


def get_labor_rate(period: str) -> float:
    """Bước 1: Đơn giá lao động / giờ cho 1 kỳ chi phí cụ thể."""
    dc = read_query(
        "SELECT COALESCE(SUM(amount),0) AS total FROM direct_costs "
        "WHERE period = ? AND category = 'Nhân công trực tiếp'",
        (period,),
    )
    hrs = read_query(
        "SELECT COALESCE(SUM(total_labor_hours),0) AS total FROM labor_machine_hours WHERE period = ?",
        (period,),
    )
    total_labor_cost = float(dc["total"].iloc[0])
    total_hours = float(hrs["total"].iloc[0])
    if total_hours <= 0:
        return 0.0
    return total_labor_cost / total_hours


def get_overhead_rates(period: str) -> dict:
    """Bước 3: Đơn giá SXC/giờ công VÀ đơn giá SXC/giờ máy cho 1 kỳ."""
    ind = read_table("indirect_costs")
    ind = ind[ind["period"] == period]
    hrs = read_query(
        "SELECT COALESCE(SUM(total_labor_hours),0) AS lh, COALESCE(SUM(total_machine_hours),0) AS mh "
        "FROM labor_machine_hours WHERE period = ?",
        (period,),
    )
    total_labor_hours = float(hrs["lh"].iloc[0])
    total_machine_hours = float(hrs["mh"].iloc[0])

    sxc_labor_based = ind[ind["alloc_base"] == "Theo giờ công trực tiếp"]["amount"].sum()
    sxc_machine_based = ind[ind["alloc_base"] == "Theo giờ máy"]["amount"].sum()

    rate_labor = (sxc_labor_based / total_labor_hours) if total_labor_hours > 0 else 0.0
    rate_machine = (sxc_machine_based / total_machine_hours) if total_machine_hours > 0 else 0.0
    return {"rate_per_labor_hour": rate_labor, "rate_per_machine_hour": rate_machine}


def cost_of_routing_step(row, labor_rate: float, oh_rates: dict) -> dict:
    """Bước 2 + Bước 3 + Bước 4 cho MỘT dòng routing (1 công đoạn)."""
    cycle_hours = float(row["cycle_time_sec"]) / 3600.0
    operators = float(row["operators"])

    labor_cost = cycle_hours * operators * labor_rate

    if row["alloc_base"] == "Theo giờ máy":
        overhead_cost = cycle_hours * oh_rates["rate_per_machine_hour"]
    else:
        overhead_cost = cycle_hours * operators * oh_rates["rate_per_labor_hour"]

    step_cost = labor_cost + overhead_cost
    return {
        "labor_cost": round(labor_cost, 2),
        "overhead_cost": round(overhead_cost, 2),
        "step_cost": round(step_cost, 2),
    }


def bom_cost_of_product(product_id: int) -> float:
    """Tổng chi phí NVL của 1 sản phẩm theo BOM, có tính hao hụt sơ chế/chế biến/vận chuyển."""
    bom = read_table("bom")
    materials = read_table("materials")
    rows = bom[bom["product_id"] == product_id]
    if rows.empty:
        return 0.0

    merged = rows.merge(materials, left_on="material_id", right_on="id", suffixes=("", "_mat"))
    total = 0.0
    for _, r in merged.iterrows():
        yield_prep = r["yield_prep"] if r["yield_prep"] else 1
        yield_cook = r["yield_cook"] if r["yield_cook"] else 1
        transport_loss = r["transport_loss"] if r["transport_loss"] else 0
        # Định mức thực tế cần mua = định mức thô ÷ (hiệu suất sơ chế × hiệu suất chế biến) × (1 + hao hụt vận chuyển)
        effective_qty = r["raw_qty"] / (yield_prep * yield_cook) * (1 + transport_loss)
        total += effective_qty * r["price"]
    return round(total, 2)


def routing_cost_of_product(product_id: int, period: str) -> pd.DataFrame:
    """Bảng chi tiết chi phí từng công đoạn (routing) của 1 sản phẩm trong 1 kỳ."""
    routing = read_table("routing", order_by="seq")
    rows = routing[routing["product_id"] == product_id]
    if rows.empty:
        return pd.DataFrame(
            columns=["seq", "step_name", "station", "alloc_base", "labor_cost", "overhead_cost", "step_cost"]
        )

    labor_rate = get_labor_rate(period)
    oh_rates = get_overhead_rates(period)

    out = []
    for _, r in rows.iterrows():
        costs = cost_of_routing_step(r, labor_rate, oh_rates)
        out.append(
            {
                "seq": r["seq"],
                "step_name": r["step_name"],
                "station": r["station"],
                "alloc_base": r["alloc_base"],
                **costs,
            }
        )
    return pd.DataFrame(out)


def full_product_cost(product_id: int, period: str) -> dict:
    """Bước 5: Giá vốn/suất đầy đủ = Chi phí NVL (BOM) + Tổng chi phí routing."""
    bom_cost = bom_cost_of_product(product_id)
    routing_df = routing_cost_of_product(product_id, period)
    routing_cost = routing_df["step_cost"].sum() if not routing_df.empty else 0.0
    return {
        "bom_cost": bom_cost,
        "routing_cost": round(routing_cost, 2),
        "total_cost": round(bom_cost + routing_cost, 2),
        "routing_detail": routing_df,
    }
