import psycopg2

from app.core.config import get_settings

s = get_settings()
conn = psycopg2.connect(
    dbname=s.DB_NAME,
    user=s.DB_USER,
    password=s.DB_PASSWORD,
    host=s.DB_HOST,
    port=s.DB_PORT,
)
cur = conn.cursor()

output_lines = [
    "-- ==============================================================================",
    "-- ChatSQL Pro - Schema & Sample Dataset for Free Cloud Deployment",
    "-- Compatible with: Neon.tech, Supabase, Render PostgreSQL, Railway, Aiven",
    "-- ==============================================================================",
    "",
    "DROP TABLE IF EXISTS product_reviews CASCADE;",
    "DROP TABLE IF EXISTS order_items CASCADE;",
    "DROP TABLE IF EXISTS orders CASCADE;",
    "DROP TABLE IF EXISTS products CASCADE;",
    "DROP TABLE IF EXISTS customers CASCADE;",
    "",
    "CREATE TABLE IF NOT EXISTS customers (",
    "    customer_id INTEGER PRIMARY KEY,",
    "    name TEXT NOT NULL,",
    "    email TEXT NOT NULL,",
    "    gender TEXT,",
    "    signup_date DATE,",
    "    country TEXT",
    ");",
    "",
    "CREATE TABLE IF NOT EXISTS products (",
    "    product_id INTEGER PRIMARY KEY,",
    "    product_name TEXT NOT NULL,",
    "    category TEXT,",
    "    price NUMERIC(10,2) NOT NULL,",
    "    stock_quantity INTEGER NOT NULL,",
    "    brand TEXT",
    ");",
    "",
    "CREATE TABLE IF NOT EXISTS orders (",
    "    order_id INTEGER PRIMARY KEY,",
    "    customer_id INTEGER,",
    "    order_date DATE,",
    "    total_amount NUMERIC(10,2),",
    "    payment_method TEXT,",
    "    shipping_country TEXT",
    ");",
    "",
    "CREATE TABLE IF NOT EXISTS order_items (",
    "    order_item_id INTEGER PRIMARY KEY,",
    "    order_id INTEGER,",
    "    product_id INTEGER,",
    "    quantity INTEGER,",
    "    unit_price NUMERIC(10,2)",
    ");",
    "",
    "CREATE TABLE IF NOT EXISTS product_reviews (",
    "    review_id INTEGER PRIMARY KEY,",
    "    product_id INTEGER,",
    "    customer_id INTEGER,",
    "    rating INTEGER,",
    "    review_text TEXT,",
    "    review_date DATE",
    ");",
    "",
    "-- Create Performance Indexes",
    "CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);",
    "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);",
    "CREATE INDEX IF NOT EXISTS idx_customers_country ON customers(country);",
    "CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);",
    "CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders(order_date);",
    "CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);",
    "",
]


def dump_table(t: str, limit: int, where_clause: str = ""):
    query = f"SELECT * FROM {t} {where_clause} LIMIT {limit}"
    cur.execute(query)
    cols = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    output_lines.append(f"-- Seed data for {t} ({len(rows)} rows)")
    for r in rows:
        vals = []
        for v in r:
            if v is None:
                vals.append("NULL")
            elif isinstance(v, (int, float)):
                vals.append(str(v))
            else:
                escaped = str(v).replace("'", "''")
                vals.append(f"'{escaped}'")
        output_lines.append(
            f"INSERT INTO {t} ({', '.join(cols)}) VALUES ({', '.join(vals)}) ON CONFLICT DO NOTHING;"
        )
    output_lines.append("")


print("Exporting seed data from local PostgreSQL...")
# 1. Products
dump_table("products", 300)

# 2. Customers (include some from Paraguay to support Battleground challenge #2)
dump_table("customers", 300)

# Get exported customer IDs and product IDs for referential integrity
cur.execute("SELECT customer_id FROM customers LIMIT 300")
valid_cust_ids = [r[0] for r in cur.fetchall()]
cur.execute("SELECT product_id FROM products LIMIT 300")
valid_prod_ids = [r[0] for r in cur.fetchall()]

cust_filter = f"WHERE customer_id IN ({','.join(map(str, valid_cust_ids[:200]))})"
dump_table("orders", 500, where_clause=cust_filter)

cur.execute(f"SELECT order_id FROM orders {cust_filter} LIMIT 500")
valid_order_ids = [r[0] for r in cur.fetchall()]

if valid_order_ids and valid_prod_ids:
    order_filter = (
        f"WHERE order_id IN ({','.join(map(str, valid_order_ids[:300]))}) "
        f"AND product_id IN ({','.join(map(str, valid_prod_ids[:300]))})"
    )
    dump_table("order_items", 800, where_clause=order_filter)

if valid_prod_ids and valid_cust_ids:
    review_filter = (
        f"WHERE product_id IN ({','.join(map(str, valid_prod_ids[:200]))}) "
        f"AND customer_id IN ({','.join(map(str, valid_cust_ids[:200]))})"
    )
    dump_table("product_reviews", 300, where_clause=review_filter)

with open("schema_seed.sql", "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print(f"Generated schema_seed.sql successfully! Total lines: {len(output_lines)}")
conn.close()
