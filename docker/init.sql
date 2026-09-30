CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    price NUMERIC(10,2) NOT NULL,
    stock_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    total_amount NUMERIC(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO products (name, category, price, stock_count)
VALUES
    ('Laptop', 'electronics', 899.99, 12),
    ('Mouse', 'electronics', 29.99, 40),
    ('Desk Chair', 'furniture', 149.50, 8)
ON CONFLICT DO NOTHING;

INSERT INTO orders (product_id, quantity, total_amount)
VALUES
    (1, 2, 1799.98),
    (2, 5, 149.95),
    (3, 1, 149.50)
ON CONFLICT DO NOTHING;
