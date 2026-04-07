import os
import sqlite3

# DATABASE_URL can be set to a PostgreSQL connection string (e.g. from DigitalOcean Managed Databases)
# to automatically swap out SQLite. Example:
#   export DATABASE_URL="postgresql://user:password@host:port/dbname?sslmode=require"
# When DATABASE_URL is not set (or is empty), the app defaults to a local SQLite file (orders.db).
DATABASE_URL = os.environ.get("DATABASE_URL", "")

if DATABASE_URL:
    import psycopg2
    import psycopg2.extras

    def _get_conn():
        return psycopg2.connect(DATABASE_URL)

    def create_tables():
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                session_id TEXT NOT NULL,
                total REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id SERIAL PRIMARY KEY,
                order_id INTEGER NOT NULL REFERENCES orders(id),
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                price REAL NOT NULL,
                qty INTEGER NOT NULL
            )
        """)
        conn.commit()
        cur.close()
        conn.close()

    def save_order(session_id, cart_items, total):
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO orders (session_id, total, status) VALUES (%s, %s, 'Pending') RETURNING id",
            (session_id, total)
        )
        order_id = cur.fetchone()[0]
        for item in cart_items:
            cur.execute(
                "INSERT INTO order_items (order_id, product_id, product_name, price, qty) VALUES (%s, %s, %s, %s, %s)",
                (order_id, item['id'], item['name'], item['price'], item['qty'])
            )
        conn.commit()
        cur.close()
        conn.close()
        return order_id

    def get_orders_by_session(session_id):
        conn = _get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM orders WHERE session_id = %s ORDER BY created_at DESC", (session_id,))
        orders = [dict(row) for row in cur.fetchall()]
        for order in orders:
            cur.execute("SELECT * FROM order_items WHERE order_id = %s", (order['id'],))
            order['lines'] = [dict(r) for r in cur.fetchall()]
        cur.close()
        conn.close()
        return orders

    def get_all_orders():
        conn = _get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM orders ORDER BY created_at DESC")
        orders = [dict(row) for row in cur.fetchall()]
        for order in orders:
            cur.execute("SELECT * FROM order_items WHERE order_id = %s", (order['id'],))
            order['lines'] = [dict(r) for r in cur.fetchall()]
        cur.close()
        conn.close()
        return orders

    def update_order_status(order_id, status):
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE orders SET status = %s WHERE id = %s", (status, order_id))
        conn.commit()
        cur.close()
        conn.close()

else:
    DB_PATH = os.path.join(os.path.dirname(__file__), "orders.db")

    def _get_conn():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def create_tables():
        conn = _get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                total REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL REFERENCES orders(id),
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                price REAL NOT NULL,
                qty INTEGER NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def save_order(session_id, cart_items, total):
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO orders (session_id, total, status) VALUES (?, ?, 'Pending')",
            (session_id, total)
        )
        order_id = cur.lastrowid
        for item in cart_items:
            cur.execute(
                "INSERT INTO order_items (order_id, product_id, product_name, price, qty) VALUES (?, ?, ?, ?, ?)",
                (order_id, item['id'], item['name'], item['price'], item['qty'])
            )
        conn.commit()
        conn.close()
        return order_id

    def get_orders_by_session(session_id):
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM orders WHERE session_id = ? ORDER BY created_at DESC", (session_id,))
        orders = [dict(row) for row in cur.fetchall()]
        for order in orders:
            cur.execute("SELECT * FROM order_items WHERE order_id = ?", (order['id'],))
            order['lines'] = [dict(r) for r in cur.fetchall()]
        conn.close()
        return orders

    def get_all_orders():
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM orders ORDER BY created_at DESC")
        orders = [dict(row) for row in cur.fetchall()]
        for order in orders:
            cur.execute("SELECT * FROM order_items WHERE order_id = ?", (order['id'],))
            order['lines'] = [dict(r) for r in cur.fetchall()]
        conn.close()
        return orders

    def update_order_status(order_id, status):
        conn = _get_conn()
        conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        conn.commit()
        conn.close()
