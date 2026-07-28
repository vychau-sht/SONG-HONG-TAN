"""
database.py — Lớp truy cập dữ liệu (Data Access Layer) dùng SQLite.
Toàn bộ ứng dụng SHT/PBG dùng chung 1 file DB: sht_pbg.db (tự tạo lần đầu chạy).
Không còn phụ thuộc Google Sheets / Google Docs.
"""

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "sht_pbg.db"


def get_connection():
    """Mở kết nối SQLite. check_same_thread=False vì Streamlit chạy đa luồng."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Tạo toàn bộ bảng nếu chưa tồn tại. Gọi 1 lần khi app khởi động."""
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact TEXT,
            lead_time_days REAL DEFAULT 0,
            payment_terms TEXT,
            rating REAL DEFAULT 0,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            name TEXT NOT NULL,
            category TEXT,
            unit TEXT,
            price REAL DEFAULT 0,
            supplier_id INTEGER,
            min_stock REAL DEFAULT 0,
            created_at TEXT,
            FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
        );

        CREATE TABLE IF NOT EXISTS supplier_quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            material_id INTEGER NOT NULL,
            price REAL NOT NULL,
            quote_date TEXT,
            note TEXT,
            created_at TEXT,
            FOREIGN KEY(supplier_id) REFERENCES suppliers(id),
            FOREIGN KEY(material_id) REFERENCES materials(id)
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            name TEXT NOT NULL,
            dish_group TEXT,
            selling_price REAL DEFAULT 0,
            target_food_cost_max REAL DEFAULT 0,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS bom (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            material_id INTEGER NOT NULL,
            stage TEXT,
            raw_qty REAL DEFAULT 0,
            yield_prep REAL DEFAULT 1,
            yield_cook REAL DEFAULT 1,
            transport_loss REAL DEFAULT 0,
            FOREIGN KEY(product_id) REFERENCES products(id),
            FOREIGN KEY(material_id) REFERENCES materials(id)
        );

        CREATE TABLE IF NOT EXISTS routing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            seq INTEGER DEFAULT 1,
            step_name TEXT,
            station TEXT,
            alloc_base TEXT DEFAULT 'Theo giờ công trực tiếp',
            cycle_time_sec REAL DEFAULT 0,
            operators REAL DEFAULT 1,
            wait_before_sec REAL DEFAULT 0,
            wait_after_sec REAL DEFAULT 0,
            downtime_sec REAL DEFAULT 0,
            FOREIGN KEY(product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS direct_costs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period TEXT NOT NULL,
            category TEXT,
            item TEXT,
            amount REAL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS indirect_costs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period TEXT NOT NULL,
            group_name TEXT,
            amount REAL DEFAULT 0,
            alloc_base TEXT DEFAULT 'Theo giờ công trực tiếp'
        );

        CREATE TABLE IF NOT EXISTS labor_machine_hours (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period TEXT NOT NULL,
            total_labor_hours REAL DEFAULT 0,
            total_machine_hours REAL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'user',
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contract_type TEXT,
            min_volume REAL DEFAULT 0,
            price_adj REAL DEFAULT 0,
            status TEXT DEFAULT 'Đang hoạt động',
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            contract_no TEXT,
            sign_date TEXT,
            effective_from TEXT,
            effective_to TEXT,
            contract_value REAL DEFAULT 0,
            status TEXT DEFAULT 'Hiệu lực',
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            product_id INTEGER,
            order_date TEXT,
            delivery_date TEXT,
            servings REAL DEFAULT 0,
            priority TEXT DEFAULT 'Bình thường',
            status TEXT DEFAULT 'Mới',
            FOREIGN KEY(customer_id) REFERENCES customers(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS warehouse_tx (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_id INTEGER NOT NULL,
            tx_type TEXT NOT NULL,
            qty REAL DEFAULT 0,
            tx_date TEXT,
            reference TEXT,
            keeper TEXT,
            note TEXT,
            FOREIGN KEY(material_id) REFERENCES materials(id)
        );

        CREATE TABLE IF NOT EXISTS qc_inbound (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_id INTEGER NOT NULL,
            supplier_id INTEGER,
            lot_no TEXT,
            received_qty REAL DEFAULT 0,
            sample_size INTEGER DEFAULT 0,
            defects_found INTEGER DEFAULT 0,
            result TEXT DEFAULT 'Đạt',
            inspector TEXT,
            approver TEXT,
            inspected_at TEXT,
            FOREIGN KEY(material_id) REFERENCES materials(id),
            FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
        );

        CREATE TABLE IF NOT EXISTS qc_outbound (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            check_date TEXT,
            servings_checked REAL DEFAULT 0,
            temp_check TEXT DEFAULT 'Đạt',
            portion_check TEXT DEFAULT 'Đạt',
            packaging_check TEXT DEFAULT 'Đạt',
            label_check TEXT DEFAULT 'Đạt',
            inspector TEXT,
            approver TEXT,
            overall_result TEXT DEFAULT 'Đạt',
            FOREIGN KEY(order_id) REFERENCES orders(id)
        );
        """
    )
    conn.commit()

    # Tài khoản admin mặc định nếu bảng users rỗng
    cur.execute("SELECT COUNT(*) AS c FROM users")
    if cur.fetchone()["c"] == 0:
        cur.execute(
            "INSERT INTO users (username, password, full_name, role, created_at) VALUES (?,?,?,?,?)",
            ("admin", "admin123", "Quản trị viên", "admin", now_str()),
        )
        conn.commit()

    conn.close()


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ------------------------------------------------------------------
# Hàm tiện ích chung: đọc / ghi / xoá / cập nhật theo bảng
# ------------------------------------------------------------------
def read_table(table: str, order_by: str = "id") -> pd.DataFrame:
    conn = get_connection()
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table} ORDER BY {order_by}", conn)
    finally:
        conn.close()
    return df


def read_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    conn = get_connection()
    try:
        df = pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()
    return df


def insert_row(table: str, data: dict) -> int:
    """data: dict {cột: giá trị}. Trả về id vừa tạo."""
    conn = get_connection()
    cur = conn.cursor()
    cols = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    cur.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", tuple(data.values()))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def update_row(table: str, row_id: int, data: dict):
    conn = get_connection()
    cur = conn.cursor()
    set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
    cur.execute(f"UPDATE {table} SET {set_clause} WHERE id = ?", tuple(data.values()) + (row_id,))
    conn.commit()
    conn.close()


def delete_row(table: str, row_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {table} WHERE id = ?", (row_id,))
    conn.commit()
    conn.close()
