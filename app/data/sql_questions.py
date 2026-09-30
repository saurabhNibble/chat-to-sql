"""Curated collection of Top 50 LeetCode-style SQL Battleground challenges mapped to real e-commerce data."""

TOP_50_SQL_QUESTIONS = [
    # =========================================================================
    # TRACK 1: SELECT & FILTERING (Questions 1 - 8)
    # =========================================================================
    {
        "id": "1-high-value-products",
        "number": 1,
        "title": "High-Value Premium Products",
        "difficulty": "Easy",
        "category": "Select & Filtering",
        "acceptance_rate": "89.4%",
        "layman_description": (
            "Imagine you are the store manager organizing the luxury showcase. "
            "Write a query to find all products with a price strictly greater than $450. "
            "Return the product_id, product_name, category, and price, ordered by price descending. Limit to 5 results."
        ),
        "tables_used": ["products"],
        "starter_code": "-- Find top 5 products with price > 450\nSELECT product_id, product_name, category, price\nFROM products\nWHERE price > 0 -- TODO: filter price > 450\nORDER BY price DESC\nLIMIT 5;",
        "expected_query": "SELECT product_id, product_name, category, price FROM products WHERE price > 450 ORDER BY price DESC LIMIT 5;",
        "layman_explanation": "Think of this like walking down an aisle and checking price tags. If the tag is over $450, we write down the product name on our clipboard and stop once we have 5 items.",
        "time_efficiency_tip": "⚡ Time Efficiency: A B-Tree index on 'price' allows PostgreSQL to scan only the top leaf nodes in O(log N + K) time instead of checking every single product.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Projecting only 4 needed columns instead of 'SELECT *' keeps the working memory buffer small.",
    },
    {
        "id": "2-active-customers-by-country",
        "number": 2,
        "title": "Paraguay Customer Directory",
        "difficulty": "Easy",
        "category": "Select & Filtering",
        "acceptance_rate": "84.2%",
        "layman_description": (
            "The regional marketing team is launching a targeted campaign in Paraguay. "
            "Find the first 5 customers located in Paraguay. "
            "Return customer_id, name, email, and country, ordered by customer_id ascending."
        ),
        "tables_used": ["customers"],
        "starter_code": "-- Find customers from Paraguay\nSELECT customer_id, name, email, country\nFROM customers\nWHERE country = 'Paraguay'\nORDER BY customer_id ASC\nLIMIT 5;",
        "expected_query": "SELECT customer_id, name, email, country FROM customers WHERE country = 'Paraguay' ORDER BY customer_id ASC LIMIT 5;",
        "layman_explanation": "Imagine filtering an international attendee list: we simply check each badge's country and collect the first 5 people from Paraguay.",
        "time_efficiency_tip": "⚡ Time Efficiency: An index on 'country' turns an expensive 2-million row table scan into an instant index seek.",
        "memory_efficiency_tip": "💾 Memory Efficiency: The LIMIT 5 clause tells PostgreSQL to halt row processing as soon as 5 matches are found, avoiding building a large result set.",
    },
    {
        "id": "3-low-stock-alert",
        "number": 3,
        "title": "Warehouse Low Stock Warning",
        "difficulty": "Easy",
        "category": "Select & Filtering",
        "acceptance_rate": "87.1%",
        "layman_description": (
            "The inventory manager needs to reorder critical stock. "
            "Find all products with a stock_quantity of 10 or fewer items. "
            "Return product_id, product_name, category, and stock_quantity, ordered by stock_quantity ascending. Limit to 5 results."
        ),
        "tables_used": ["products"],
        "starter_code": "-- Find products with low inventory\nSELECT product_id, product_name, category, stock_quantity\nFROM products\nWHERE stock_quantity <= 10\nORDER BY stock_quantity ASC\nLIMIT 5;",
        "expected_query": "SELECT product_id, product_name, category, stock_quantity FROM products WHERE stock_quantity <= 10 ORDER BY stock_quantity ASC LIMIT 5;",
        "layman_explanation": "Think of this as inspecting shelves for nearly empty bins. When a bin has 10 or fewer items left, we flag it immediately.",
        "time_efficiency_tip": "⚡ Time Efficiency: Indexing 'stock_quantity' allows instant retrieval of the minimum values without scanning all products.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Ordering on an indexed column avoids an expensive in-memory sort buffer allocation.",
    },
    {
        "id": "4-female-customers-early-signups",
        "number": 4,
        "title": "Early Female Adopters",
        "difficulty": "Easy",
        "category": "Select & Filtering",
        "acceptance_rate": "81.0%",
        "layman_description": (
            "Identify early adopters among female customers. "
            "Find female customers (gender = 'Female') with customer_id <= 100. "
            "Return customer_id, name, gender, and signup_date, ordered by signup_date ASC. Limit to 5 results."
        ),
        "tables_used": ["customers"],
        "starter_code": "-- Filter early female customers\nSELECT customer_id, name, gender, signup_date\nFROM customers\nWHERE customer_id <= 100 AND gender = 'Female'\nORDER BY signup_date ASC\nLIMIT 5;",
        "expected_query": "SELECT customer_id, name, gender, signup_date FROM customers WHERE customer_id <= 100 AND gender = 'Female' ORDER BY signup_date ASC LIMIT 5;",
        "layman_explanation": "Looking only at the first 100 registered members, find those marked as 'Female' and sort them from the earliest joined.",
        "time_efficiency_tip": "⚡ Time Efficiency: Limiting by primary key 'customer_id <= 100' uses the clustered index, touching only 100 rows instead of 2,000,000.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Small pre-filtered input size fits entirely into L1/L2 CPU cache.",
    },
    {
        "id": "5-electronics-under-100",
        "number": 4,
        "title": "Budget Electronics Finder",
        "difficulty": "Easy",
        "category": "Select & Filtering",
        "acceptance_rate": "86.5%",
        "layman_description": (
            "A discount holiday section wants budget electronics. "
            "Find products in category 'Electronics' with price < 100. "
            "Return product_id, product_name, price, ordered by price ASC. Limit to 5 results."
        ),
        "tables_used": ["products"],
        "starter_code": "-- Find budget electronics\nSELECT product_id, product_name, price\nFROM products\nWHERE category = 'Electronics' AND price < 100\nORDER BY price ASC\nLIMIT 5;",
        "expected_query": "SELECT product_id, product_name, price FROM products WHERE category = 'Electronics' AND price < 100 ORDER BY price ASC LIMIT 5;",
        "layman_explanation": "Go to the electronics department and pick out items that cost under $100, arranging them from cheapest to dearest.",
        "time_efficiency_tip": "⚡ Time Efficiency: A composite index on (category, price) satisfies both filtering and sorting in a single step.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Index scanning eliminates the need for PostgreSQL work_mem sort structures.",
    },
    {
        "id": "6-perfect-score-reviews",
        "number": 6,
        "title": "5-Star Product Reviews",
        "difficulty": "Easy",
        "category": "Select & Filtering",
        "acceptance_rate": "83.7%",
        "layman_description": (
            "Marketing needs stellar customer testimonials. "
            "Find the top 5 product reviews with a perfect rating of 5 among review_id <= 500. "
            "Return review_id, product_id, customer_id, rating, ordered by review_id ASC."
        ),
        "tables_used": ["product_reviews"],
        "starter_code": "-- Find 5-star reviews\nSELECT review_id, product_id, customer_id, rating\nFROM product_reviews\nWHERE review_id <= 500 AND rating = 5\nORDER BY review_id ASC\nLIMIT 5;",
        "expected_query": "SELECT review_id, product_id, customer_id, rating FROM product_reviews WHERE review_id <= 500 AND rating = 5 ORDER BY review_id ASC LIMIT 5;",
        "layman_explanation": "Think of skimming the first 500 customer feedback cards and pulling out the ones that gave 5 out of 5 stars.",
        "time_efficiency_tip": "⚡ Time Efficiency: Bounding review_id prevents scanning 4,000,000 review rows.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Early filter avoids buffering unneeded review comments into memory.",
    },
    {
        "id": "7-high-value-orders",
        "number": 7,
        "title": "Whale Orders Over $1000",
        "difficulty": "Easy",
        "category": "Select & Filtering",
        "acceptance_rate": "85.0%",
        "layman_description": (
            "Finance wants to inspect big-ticket purchases. "
            "Find orders among order_id <= 1000 where total_amount >= 1000. "
            "Return order_id, customer_id, total_amount, payment_method, ordered by total_amount DESC. Limit to 5 results."
        ),
        "tables_used": ["orders"],
        "starter_code": "-- Find big purchases\nSELECT order_id, customer_id, total_amount, payment_method\nFROM orders\nWHERE order_id <= 1000 AND total_amount >= 1000\nORDER BY total_amount DESC\nLIMIT 5;",
        "expected_query": "SELECT order_id, customer_id, total_amount, payment_method FROM orders WHERE order_id <= 1000 AND total_amount >= 1000 ORDER BY total_amount DESC LIMIT 5;",
        "layman_explanation": "Looking through receipts, find invoices where the total bill was at least $1,000, displaying the largest first.",
        "time_efficiency_tip": "⚡ Time Efficiency: Primary key range filtering avoids scanning 8,000,000 orders.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Quicksort is bounded to only matching rows within the 1000-row window.",
    },
    {
        "id": "8-credit-card-transactions",
        "number": 8,
        "title": "Credit Card Payment Audit",
        "difficulty": "Easy",
        "category": "Select & Filtering",
        "acceptance_rate": "88.2%",
        "layman_description": (
            "Inspect credit card transactions for payment gateway verification. "
            "Find orders with order_id <= 500 paid with 'Credit Card'. "
            "Return order_id, customer_id, order_date, total_amount, ordered by order_id ASC. Limit to 5 results."
        ),
        "tables_used": ["orders"],
        "starter_code": "-- Find credit card orders\nSELECT order_id, customer_id, order_date, total_amount\nFROM orders\nWHERE order_id <= 500 AND payment_method = 'Credit Card'\nORDER BY order_id ASC\nLIMIT 5;",
        "expected_query": "SELECT order_id, customer_id, order_date, total_amount FROM orders WHERE order_id <= 500 AND payment_method = 'Credit Card' ORDER BY order_id ASC LIMIT 5;",
        "layman_explanation": "Filter the first 500 receipts to only show purchases where the customer swiped a credit card.",
        "time_efficiency_tip": "⚡ Time Efficiency: Primary key index seek + filter executes in less than 2 milliseconds.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Stops immediately upon retrieving 5 rows.",
    },

    # =========================================================================
    # TRACK 2: BASIC JOINS (Questions 9 - 18)
    # =========================================================================
    {
        "id": "9-customer-orders-report",
        "number": 9,
        "title": "Customer Name with Order Total",
        "difficulty": "Easy",
        "category": "Basic Joins",
        "acceptance_rate": "78.4%",
        "layman_description": (
            "Combine customer details with their purchases. "
            "Join customers and orders for customer_id <= 50. "
            "Return customer_id, customer name, order_id, and total_amount, ordered by total_amount DESC. Limit to 5 results."
        ),
        "tables_used": ["customers", "orders"],
        "starter_code": "-- Join customers and orders\nSELECT c.customer_id, c.name, o.order_id, o.total_amount\nFROM customers c\nJOIN orders o ON c.customer_id = o.customer_id\nWHERE c.customer_id <= 50\nORDER BY o.total_amount DESC\nLIMIT 5;",
        "expected_query": "SELECT c.customer_id, c.name, o.order_id, o.total_amount FROM customers c JOIN orders o ON c.customer_id = o.customer_id WHERE c.customer_id <= 50 ORDER BY o.total_amount DESC LIMIT 5;",
        "layman_explanation": "Think of matching each receipt to the customer's loyalty card to print their name alongside what they spent.",
        "time_efficiency_tip": "⚡ Time Efficiency: Filtering c.customer_id <= 50 allows an index nested-loop join instead of a massive multi-gigabyte hash join.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Avoids loading millions of rows into the database join hash table.",
    },
    {
        "id": "10-product-review-details",
        "number": 10,
        "title": "Product Feedback Cross-Reference",
        "difficulty": "Easy",
        "category": "Basic Joins",
        "acceptance_rate": "76.5%",
        "layman_description": (
            "Product managers want to see what customers say about products. "
            "Join products and product_reviews for product_id <= 50. "
            "Return product_id, product_name, rating, and review_text, ordered by rating DESC. Limit to 5 results."
        ),
        "tables_used": ["products", "product_reviews"],
        "starter_code": "-- Join products with reviews\nSELECT p.product_id, p.product_name, pr.rating, pr.review_text\nFROM products p\nJOIN product_reviews pr ON p.product_id = pr.product_id\nWHERE p.product_id <= 50\nORDER BY pr.rating DESC\nLIMIT 5;",
        "expected_query": "SELECT p.product_id, p.product_name, pr.rating, pr.review_text FROM products p JOIN product_reviews pr ON p.product_id = pr.product_id WHERE p.product_id <= 50 ORDER BY pr.rating DESC LIMIT 5;",
        "layman_explanation": "Attach the review cards to the item descriptions in a product catalog so you can see ratings next to product names.",
        "time_efficiency_tip": "⚡ Time Efficiency: Primary key join using product_id leverages indexed foreign key references.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Restricting product_id to <= 50 limits review lookups to a tiny subset.",
    },
    {
        "id": "11-order-items-and-products",
        "number": 11,
        "title": "Order Line Item Pricing",
        "difficulty": "Easy",
        "category": "Basic Joins",
        "acceptance_rate": "75.0%",
        "layman_description": (
            "Display purchased item names and quantities. "
            "Join order_items and products for order_id <= 20. "
            "Return order_id, product_name, quantity, and unit_price, ordered by order_id ASC, product_name ASC. Limit to 5 results."
        ),
        "tables_used": ["order_items", "products"],
        "starter_code": "-- Join order items with product catalog\nSELECT oi.order_id, p.product_name, oi.quantity, oi.unit_price\nFROM order_items oi\nJOIN products p ON oi.product_id = p.product_id\nWHERE oi.order_id <= 20\nORDER BY oi.order_id ASC, p.product_name ASC\nLIMIT 5;",
        "expected_query": "SELECT oi.order_id, p.product_name, oi.quantity, oi.unit_price FROM order_items oi JOIN products p ON oi.product_id = p.product_id WHERE oi.order_id <= 20 ORDER BY oi.order_id ASC, p.product_name ASC LIMIT 5;",
        "layman_explanation": "Look at an itemized supermarket receipt and look up the barcodes in the store catalog to print the product names.",
        "time_efficiency_tip": "⚡ Time Efficiency: Order_id filter cuts search scope from 20 million rows to fewer than 50 rows.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Small working set avoids disk spill during sort.",
    },
    {
        "id": "12-customers-without-orders",
        "number": 12,
        "title": "Customers Who Never Placed an Order",
        "difficulty": "Medium",
        "category": "Basic Joins",
        "acceptance_rate": "68.2%",
        "layman_description": (
            "Marketing needs to reach registered users who haven't made their first purchase yet. "
            "Using a LEFT JOIN, find customers with customer_id <= 200 who have zero orders. "
            "Return customer_id, name, and email, ordered by customer_id ASC. Limit to 5 results."
        ),
        "tables_used": ["customers", "orders"],
        "starter_code": "-- Anti-join using LEFT JOIN and IS NULL\nSELECT c.customer_id, c.name, c.email\nFROM customers c\nLEFT JOIN orders o ON c.customer_id = o.customer_id\nWHERE c.customer_id <= 200 AND o.order_id IS NULL\nORDER BY c.customer_id ASC\nLIMIT 5;",
        "expected_query": "SELECT c.customer_id, c.name, c.email FROM customers c LEFT JOIN orders o ON c.customer_id = o.customer_id WHERE c.customer_id <= 200 AND o.order_id IS NULL ORDER BY c.customer_id ASC LIMIT 5;",
        "layman_explanation": "Take the membership roster and try to pair each person with a purchase receipt. If someone has no receipts attached (NULL), keep them on the list.",
        "time_efficiency_tip": "⚡ Time Efficiency: An anti-join with IS NULL is translated by PostgreSQL planner into an optimized Hash Anti Join.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Scans orders only for customer_ids within the 200-row bounds.",
    },
    {
        "id": "13-products-critical-reviews",
        "number": 13,
        "title": "Critical 1-Star Product Reviews",
        "difficulty": "Medium",
        "category": "Basic Joins",
        "acceptance_rate": "71.4%",
        "layman_description": (
            "Customer experience wants to inspect negative feedback on our catalog. "
            "Find all distinct products with product_id <= 10 that have received a 1-star rating. "
            "Return product_id, product_name, category, ordered by product_id ASC. Limit to 5 results."
        ),
        "tables_used": ["products", "product_reviews"],
        "starter_code": "-- Find products <= 10 with 1-star reviews\nSELECT DISTINCT p.product_id, p.product_name, p.category\nFROM products p\nJOIN product_reviews pr ON p.product_id = pr.product_id\nWHERE p.product_id <= 10 AND pr.rating = 1\nORDER BY p.product_id ASC\nLIMIT 5;",
        "expected_query": "SELECT DISTINCT p.product_id, p.product_name, p.category FROM products p JOIN product_reviews pr ON p.product_id = pr.product_id WHERE p.product_id <= 10 AND pr.rating = 1 ORDER BY p.product_id ASC LIMIT 5;",
        "layman_explanation": "Think of this like flipping through the feedback cards for the first 10 items in the store and listing each item once if anyone gave it 1 star.",
        "time_efficiency_tip": "⚡ Time Efficiency: Filtering product_id <= 10 uses the primary key index on products, limiting joined rows significantly.",
        "memory_efficiency_tip": "💾 Memory Efficiency: DISTINCT on small filtered subsets avoids large memory hash tables.",
    },
    {
        "id": "14-customer-country-orders",
        "number": 14,
        "title": "Orders from German Customers",
        "difficulty": "Easy",
        "category": "Basic Joins",
        "acceptance_rate": "79.0%",
        "layman_description": (
            "Logistics needs to inspect shipments to German addresses. "
            "Join customers and orders where customer country is 'Germany' and c.customer_id <= 500. "
            "Return c.customer_id, c.name, o.order_id, o.total_amount, ordered by o.order_id ASC. Limit to 5 results."
        ),
        "tables_used": ["customers", "orders"],
        "starter_code": "-- Join customers and orders for Germany\nSELECT c.customer_id, c.name, o.order_id, o.total_amount\nFROM customers c\nJOIN orders o ON c.customer_id = o.customer_id\nWHERE c.country = 'Germany' AND c.customer_id <= 500\nORDER BY o.order_id ASC\nLIMIT 5;",
        "expected_query": "SELECT c.customer_id, c.name, o.order_id, o.total_amount FROM customers c JOIN orders o ON c.customer_id = o.customer_id WHERE c.country = 'Germany' AND c.customer_id <= 500 ORDER BY o.order_id ASC LIMIT 5;",
        "layman_explanation": "Filter customers living in Germany first, then pull up all receipt records matching their IDs.",
        "time_efficiency_tip": "⚡ Time Efficiency: Filter applied before join reduces the number of outer rows fed into the join operator.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Minimizes intermediate hash table size in RAM.",
    },
    {
        "id": "15-three-table-order-breakdown",
        "number": 15,
        "title": "Full Order Itemization",
        "difficulty": "Medium",
        "category": "Basic Joins",
        "acceptance_rate": "67.8%",
        "layman_description": (
            "Customer service needs to see customer name and product names for order_id = 1. "
            "Join customers, orders, and order_items (and products). "
            "Return c.name AS customer_name, p.product_name, oi.quantity, oi.unit_price, ordered by p.product_name ASC. Limit to 5 results."
        ),
        "tables_used": ["customers", "orders", "order_items", "products"],
        "starter_code": "-- Join 4 tables for order_id = 1\nSELECT c.name AS customer_name, p.product_name, oi.quantity, oi.unit_price\nFROM orders o\nJOIN customers c ON o.customer_id = c.customer_id\nJOIN order_items oi ON o.order_id = oi.order_id\nJOIN products p ON oi.product_id = p.product_id\nWHERE o.order_id = 1\nORDER BY p.product_name ASC\nLIMIT 5;",
        "expected_query": "SELECT c.name AS customer_name, p.product_name, oi.quantity, oi.unit_price FROM orders o JOIN customers c ON o.customer_id = c.customer_id JOIN order_items oi ON o.order_id = oi.order_id JOIN products p ON oi.product_id = p.product_id WHERE o.order_id = 1 ORDER BY p.product_name ASC LIMIT 5;",
        "layman_explanation": "Connecting the receipt to the customer who bought it, the line items on the receipt, and the catalog entry for each item.",
        "time_efficiency_tip": "⚡ Time Efficiency: Single-key filter 'o.order_id = 1' collapses the entire multi-table join into lightning-fast index lookups.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Produces under 10 rows, using virtually zero RAM.",
    },
    {
        "id": "16-highest-priced-order-item",
        "number": 16,
        "title": "Most Expensive Item in Orders",
        "difficulty": "Easy",
        "category": "Basic Joins",
        "acceptance_rate": "80.2%",
        "layman_description": (
            "Find the highest unit price items in order_items for order_id <= 100. "
            "Join order_items and products. "
            "Return oi.order_id, p.product_name, oi.unit_price, ordered by oi.unit_price DESC. Limit to 5 results."
        ),
        "tables_used": ["order_items", "products"],
        "starter_code": "-- Find top unit price items\nSELECT oi.order_id, p.product_name, oi.unit_price\nFROM order_items oi\nJOIN products p ON oi.product_id = p.product_id\nWHERE oi.order_id <= 100\nORDER BY oi.unit_price DESC\nLIMIT 5;",
        "expected_query": "SELECT oi.order_id, p.product_name, oi.unit_price FROM order_items oi JOIN products p ON oi.product_id = p.product_id WHERE oi.order_id <= 100 ORDER BY oi.unit_price DESC LIMIT 5;",
        "layman_explanation": "Sort purchased items from most expensive to least expensive to highlight premium sales.",
        "time_efficiency_tip": "⚡ Time Efficiency: Range constraint on order_id limits index scan depth.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Top-N heapsort retains only 5 items in memory.",
    },
    {
        "id": "17-reviewers-and-product-brands",
        "number": 17,
        "title": "Reviewer Ratings by Brand",
        "difficulty": "Easy",
        "category": "Basic Joins",
        "acceptance_rate": "77.1%",
        "layman_description": (
            "Marketing wants to analyze reviews for specific brands. "
            "Join product_reviews and products for pr.review_id <= 300. "
            "Return pr.review_id, p.product_name, p.brand, pr.rating, ordered by pr.review_id ASC. Limit to 5 results."
        ),
        "tables_used": ["product_reviews", "products"],
        "starter_code": "-- Join reviews and products\nSELECT pr.review_id, p.product_name, p.brand, pr.rating\nFROM product_reviews pr\nJOIN products p ON pr.product_id = p.product_id\nWHERE pr.review_id <= 300\nORDER BY pr.review_id ASC\nLIMIT 5;",
        "expected_query": "SELECT pr.review_id, p.product_name, p.brand, pr.rating FROM product_reviews pr JOIN products p ON pr.product_id = p.product_id WHERE pr.review_id <= 300 ORDER BY pr.review_id ASC LIMIT 5;",
        "layman_explanation": "Pair review scores with brand names to see how each manufacturer is performing.",
        "time_efficiency_tip": "⚡ Time Efficiency: Index seek on products.product_id runs in O(1) per review.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Streaming with LIMIT 5 avoids buffering review comment text.",
    },
    {
        "id": "18-cross-category-purchases",
        "number": 18,
        "title": "Orders with Product Category",
        "difficulty": "Easy",
        "category": "Basic Joins",
        "acceptance_rate": "74.8%",
        "layman_description": (
            "Categorize items bought in early orders. "
            "Join order_items and products for oi.order_id <= 50. "
            "Return oi.order_id, p.category, oi.quantity, oi.unit_price, ordered by oi.unit_price DESC. Limit to 5 results."
        ),
        "tables_used": ["order_items", "products"],
        "starter_code": "-- Link order items to categories\nSELECT oi.order_id, p.category, oi.quantity, oi.unit_price\nFROM order_items oi\nJOIN products p ON oi.product_id = p.product_id\nWHERE oi.order_id <= 50\nORDER BY oi.unit_price DESC\nLIMIT 5;",
        "expected_query": "SELECT oi.order_id, p.category, oi.quantity, oi.unit_price FROM order_items oi JOIN products p ON oi.product_id = p.product_id WHERE oi.order_id <= 50 ORDER BY oi.unit_price DESC LIMIT 5;",
        "layman_explanation": "Check which product category each item on the receipt belonged to.",
        "time_efficiency_tip": "⚡ Time Efficiency: Indexed foreign key join avoids full table scans.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Compact numeric and short text columns minimize network transit.",
    },

    # =========================================================================
    # TRACK 3: AGGREGATION & GROUPING (Questions 19 - 28)
    # =========================================================================
    {
        "id": "19-product-count-by-category",
        "number": 19,
        "title": "Product Variety per Category",
        "difficulty": "Easy",
        "category": "Aggregation & Grouping",
        "acceptance_rate": "86.0%",
        "layman_description": (
            "Count how many distinct products exist in each category. "
            "Group products by category and calculate total products and average price rounded to 2 decimal places. "
            "Return category, total_products, avg_price, ordered by total_products DESC. Limit to 5 results."
        ),
        "tables_used": ["products"],
        "starter_code": "-- Group products by category\nSELECT category, COUNT(*) AS total_products, ROUND(AVG(price)::numeric, 2) AS avg_price\nFROM products\nGROUP BY category\nORDER BY total_products DESC\nLIMIT 5;",
        "expected_query": "SELECT category, COUNT(*) AS total_products, ROUND(AVG(price)::numeric, 2) AS avg_price FROM products GROUP BY category ORDER BY total_products DESC LIMIT 5;",
        "layman_explanation": "Sort all products into category boxes and count how many items are in each box, along with their average price.",
        "time_efficiency_tip": "⚡ Time Efficiency: 20,000 product rows aggregate in memory via HashAggregate in ~15 milliseconds.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Categories aggregate into fewer than 50 hash buckets, using trivial RAM.",
    },
    {
        "id": "20-total-spent-per-customer",
        "number": 20,
        "title": "Customer Spending Totals",
        "difficulty": "Medium",
        "category": "Aggregation & Grouping",
        "acceptance_rate": "72.5%",
        "layman_description": (
            "Calculate total money spent by each customer among customer_id <= 100. "
            "Join customers and orders, group by customer_id and name, and calculate SUM(total_amount). "
            "Return customer_id, name, total_spent, ordered by total_spent DESC. Limit to 5 results."
        ),
        "tables_used": ["customers", "orders"],
        "starter_code": "-- Sum customer spending\nSELECT c.customer_id, c.name, SUM(o.total_amount) AS total_spent\nFROM customers c\nJOIN orders o ON c.customer_id = o.customer_id\nWHERE c.customer_id <= 100\nGROUP BY c.customer_id, c.name\nORDER BY total_spent DESC\nLIMIT 5;",
        "expected_query": "SELECT c.customer_id, c.name, SUM(o.total_amount) AS total_spent FROM customers c JOIN orders o ON c.customer_id = o.customer_id WHERE c.customer_id <= 100 GROUP BY c.customer_id, c.name ORDER BY total_spent DESC LIMIT 5;",
        "layman_explanation": "Add up all the bills for each customer and show the top 5 spenders.",
        "time_efficiency_tip": "⚡ Time Efficiency: Pre-filtering on customer_id <= 100 bounds the group count to 100 rows.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Small hash table size fits in L3 cache.",
    },
    {
        "id": "21-average-product-rating",
        "number": 21,
        "title": "Top-Rated Products",
        "difficulty": "Medium",
        "category": "Aggregation & Grouping",
        "acceptance_rate": "69.0%",
        "layman_description": (
            "Identify products with the highest average satisfaction among product_id <= 100. "
            "Join products and product_reviews, calculate AVG(rating) rounded to 2 decimal places and review count. "
            "Return product_id, product_name, avg_rating, review_count, ordered by avg_rating DESC. Limit to 5 results."
        ),
        "tables_used": ["products", "product_reviews"],
        "starter_code": "-- Compute average rating\nSELECT p.product_id, p.product_name, ROUND(AVG(pr.rating)::numeric, 2) AS avg_rating, COUNT(pr.review_id) AS review_count\nFROM products p\nJOIN product_reviews pr ON p.product_id = pr.product_id\nWHERE p.product_id <= 100\nGROUP BY p.product_id, p.product_name\nHAVING COUNT(pr.review_id) >= 1\nORDER BY avg_rating DESC\nLIMIT 5;",
        "expected_query": "SELECT p.product_id, p.product_name, ROUND(AVG(pr.rating)::numeric, 2) AS avg_rating, COUNT(pr.review_id) AS review_count FROM products p JOIN product_reviews pr ON p.product_id = pr.product_id WHERE p.product_id <= 100 GROUP BY p.product_id, p.product_name HAVING COUNT(pr.review_id) >= 1 ORDER BY avg_rating DESC LIMIT 5;",
        "layman_explanation": "Calculate the average star score for each product and list the winners.",
        "time_efficiency_tip": "⚡ Time Efficiency: Product range filter prevents scanning reviews for all 20,000 products.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Only 100 group accumulator buckets are kept in memory.",
    },
    {
        "id": "22-orders-count-by-payment-method",
        "number": 22,
        "title": "Preferred Payment Methods",
        "difficulty": "Easy",
        "category": "Aggregation & Grouping",
        "acceptance_rate": "84.5%",
        "layman_description": (
            "Analyze payment methods used for order_id <= 5000. "
            "Count total transactions and total revenue per payment_method. "
            "Return payment_method, total_orders, total_revenue, ordered by total_orders DESC."
        ),
        "tables_used": ["orders"],
        "starter_code": "-- Aggregate payment methods\nSELECT payment_method, COUNT(*) AS total_orders, SUM(total_amount) AS total_revenue\nFROM orders\nWHERE order_id <= 5000\nGROUP BY payment_method\nORDER BY total_orders DESC;",
        "expected_query": "SELECT payment_method, COUNT(*) AS total_orders, SUM(total_amount) AS total_revenue FROM orders WHERE order_id <= 5000 GROUP BY payment_method ORDER BY total_orders DESC;",
        "layman_explanation": "Tally up payments by cash, card, PayPal, etc., to see which payment method shoppers prefer.",
        "time_efficiency_tip": "⚡ Time Efficiency: Range scan on primary key processes 5,000 rows in ~3ms.",
        "memory_efficiency_tip": "💾 Memory Efficiency: 4-5 payment methods produce a microscopic aggregation table.",
    },
    {
        "id": "23-customers-with-multiple-orders",
        "number": 23,
        "title": "Frequent Shoppers (HAVING)",
        "difficulty": "Medium",
        "category": "Aggregation & Grouping",
        "acceptance_rate": "71.0%",
        "layman_description": (
            "Find repeat buyers who have placed at least 3 orders among customer_id <= 500. "
            "Use GROUP BY and HAVING COUNT(order_id) >= 3. "
            "Return customer_id, COUNT(order_id) AS order_count, ordered by order_count DESC. Limit to 5 results."
        ),
        "tables_used": ["orders"],
        "starter_code": "-- Find repeat customers using HAVING\nSELECT customer_id, COUNT(order_id) AS order_count\nFROM orders\nWHERE customer_id <= 500\nGROUP BY customer_id\nHAVING COUNT(order_id) >= 3\nORDER BY order_count DESC\nLIMIT 5;",
        "expected_query": "SELECT customer_id, COUNT(order_id) AS order_count FROM orders WHERE customer_id <= 500 GROUP BY customer_id HAVING COUNT(order_id) >= 3 ORDER BY order_count DESC LIMIT 5;",
        "layman_explanation": "Count each customer's receipts and discard anyone who bought fewer than 3 times.",
        "time_efficiency_tip": "⚡ Time Efficiency: Filtering with WHERE customer_id <= 500 first prevents grouping millions of irrelevant orders.",
        "memory_efficiency_tip": "💾 Memory Efficiency: HAVING filters out low counts before the final sort.",
    },
    {
        "id": "24-average-order-value-by-country",
        "number": 24,
        "title": "Average Order Value by Shipping Country",
        "difficulty": "Medium",
        "category": "Aggregation & Grouping",
        "acceptance_rate": "73.2%",
        "layman_description": (
            "Find countries with high-spending orders among order_id <= 10000. "
            "Calculate average total_amount rounded to 2 decimals and order count per shipping_country. "
            "Return shipping_country, avg_order_value, order_count, ordered by avg_order_value DESC. Limit to 5 results."
        ),
        "tables_used": ["orders"],
        "starter_code": "-- Calculate AOV by country\nSELECT shipping_country, ROUND(AVG(total_amount)::numeric, 2) AS avg_order_value, COUNT(*) AS order_count\nFROM orders\nWHERE order_id <= 10000\nGROUP BY shipping_country\nHAVING COUNT(*) >= 10\nORDER BY avg_order_value DESC\nLIMIT 5;",
        "expected_query": "SELECT shipping_country, ROUND(AVG(total_amount)::numeric, 2) AS avg_order_value, COUNT(*) AS order_count FROM orders WHERE order_id <= 10000 GROUP BY shipping_country HAVING COUNT(*) >= 10 ORDER BY avg_order_value DESC LIMIT 5;",
        "layman_explanation": "Calculate average receipt totals for each country to identify high-value international markets.",
        "time_efficiency_tip": "⚡ Time Efficiency: Aggregation runs over 10,000 indexed records in single-digit milliseconds.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Memory footprint is bounded by distinct countries.",
    },
    {
        "id": "25-total-items-sold-per-product",
        "number": 25,
        "title": "Top Selling Products by Volume",
        "difficulty": "Medium",
        "category": "Aggregation & Grouping",
        "acceptance_rate": "70.1%",
        "layman_description": (
            "Calculate the total quantity sold for products among product_id <= 100. "
            "Join products and order_items. Calculate SUM(quantity) as total_sold. "
            "Return p.product_id, p.product_name, total_sold, ordered by total_sold DESC. Limit to 5 results."
        ),
        "tables_used": ["products", "order_items"],
        "starter_code": "-- Sum units sold\nSELECT p.product_id, p.product_name, SUM(oi.quantity) AS total_sold\nFROM products p\nJOIN order_items oi ON p.product_id = oi.product_id\nWHERE p.product_id <= 100\nGROUP BY p.product_id, p.product_name\nORDER BY total_sold DESC\nLIMIT 5;",
        "expected_query": "SELECT p.product_id, p.product_name, SUM(oi.quantity) AS total_sold FROM products p JOIN order_items oi ON p.product_id = oi.product_id WHERE p.product_id <= 100 GROUP BY p.product_id, p.product_name ORDER BY total_sold DESC LIMIT 5;",
        "layman_explanation": "Count how many individual units of each item were boxed and shipped out.",
        "time_efficiency_tip": "⚡ Time Efficiency: Product constraint restricts order item scans.",
        "memory_efficiency_tip": "💾 Memory Efficiency: HashAggregate operates on 100 groups in RAM.",
    },
    {
        "id": "26-highest-revenue-categories",
        "number": 26,
        "title": "Category Revenue Leaderboard",
        "difficulty": "Medium",
        "category": "Aggregation & Grouping",
        "acceptance_rate": "69.5%",
        "layman_description": (
            "Analyze which categories generate the most revenue for items in order_id <= 500. "
            "Join order_items and products. Calculate SUM(quantity * unit_price) AS category_revenue. "
            "Return category, category_revenue, ordered by category_revenue DESC. Limit to 5 results."
        ),
        "tables_used": ["order_items", "products"],
        "starter_code": "-- Total revenue per category\nSELECT p.category, SUM(oi.quantity * oi.unit_price) AS category_revenue\nFROM order_items oi\nJOIN products p ON oi.product_id = p.product_id\nWHERE oi.order_id <= 500\nGROUP BY p.category\nORDER BY category_revenue DESC\nLIMIT 5;",
        "expected_query": "SELECT p.category, SUM(oi.quantity * oi.unit_price) AS category_revenue FROM order_items oi JOIN products p ON oi.product_id = p.product_id WHERE oi.order_id <= 500 GROUP BY p.category ORDER BY category_revenue DESC LIMIT 5;",
        "layman_explanation": "Multiply quantity by price for every item and sum up the dollars for each department.",
        "time_efficiency_tip": "⚡ Time Efficiency: WHERE order_id <= 500 filters input rows before multiplying and grouping.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Avoids intermediate materialized views.",
    },
    {
        "id": "27-review-rating-distribution",
        "number": 27,
        "title": "Star Rating Breakdown (1 to 5)",
        "difficulty": "Easy",
        "category": "Aggregation & Grouping",
        "acceptance_rate": "85.2%",
        "layman_description": (
            "Analyze rating distribution for review_id <= 5000. "
            "Count total reviews for each rating star level (1, 2, 3, 4, 5). "
            "Return rating, COUNT(*) AS count, ordered by rating DESC."
        ),
        "tables_used": ["product_reviews"],
        "starter_code": "-- Star rating count\nSELECT rating, COUNT(*) AS count\nFROM product_reviews\nWHERE review_id <= 5000\nGROUP BY rating\nORDER BY rating DESC;",
        "expected_query": "SELECT rating, COUNT(*) AS count FROM product_reviews WHERE review_id <= 5000 GROUP BY rating ORDER BY rating DESC;",
        "layman_explanation": "Count how many 5-star, 4-star, 3-star, 2-star, and 1-star reviews shoppers submitted.",
        "time_efficiency_tip": "⚡ Time Efficiency: Scanning 5,000 rows yields exactly 5 buckets in sub-millisecond time.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Fixed 5-element array requires under 1KB of memory.",
    },
    {
        "id": "28-monthly-order-counts",
        "number": 28,
        "title": "Monthly Order Volume Trend",
        "difficulty": "Medium",
        "category": "Aggregation & Grouping",
        "acceptance_rate": "71.8%",
        "layman_description": (
            "Analyze order seasonality for order_id <= 5000. "
            "Extract year and month using DATE_TRUNC('month', order_date). "
            "Return DATE_TRUNC('month', order_date) AS order_month, COUNT(*) AS total_orders, ordered by order_month ASC. Limit to 5 results."
        ),
        "tables_used": ["orders"],
        "starter_code": "-- Monthly order trend\nSELECT DATE_TRUNC('month', order_date) AS order_month, COUNT(*) AS total_orders\nFROM orders\nWHERE order_id <= 5000\nGROUP BY DATE_TRUNC('month', order_date)\nORDER BY order_month ASC\nLIMIT 5;",
        "expected_query": "SELECT DATE_TRUNC('month', order_date) AS order_month, COUNT(*) AS total_orders FROM orders WHERE order_id <= 5000 GROUP BY DATE_TRUNC('month', order_date) ORDER BY order_month ASC LIMIT 5;",
        "layman_explanation": "Group purchases into monthly calendar buckets to observe business growth over time.",
        "time_efficiency_tip": "⚡ Time Efficiency: Date truncation groups efficiently in a single pass.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Compact temporal grouping keeps RAM usage low.",
    },

    # =========================================================================
    # TRACK 4: SORTING & GROUPING (Questions 29 - 36)
    # =========================================================================
    {
        "id": "29-most-reviewed-products",
        "number": 29,
        "title": "Most Talked-About Products",
        "difficulty": "Easy",
        "category": "Sorting & Grouping",
        "acceptance_rate": "81.2%",
        "layman_description": (
            "Find the products with the most customer reviews for product_id <= 200. "
            "Count reviews per product_id, joining products. "
            "Return p.product_id, p.product_name, COUNT(pr.review_id) AS review_count, ordered by review_count DESC. Limit to 5 results."
        ),
        "tables_used": ["products", "product_reviews"],
        "starter_code": "-- Count reviews per product\nSELECT p.product_id, p.product_name, COUNT(pr.review_id) AS review_count\nFROM products p\nJOIN product_reviews pr ON p.product_id = pr.product_id\nWHERE p.product_id <= 200\nGROUP BY p.product_id, p.product_name\nORDER BY review_count DESC\nLIMIT 5;",
        "expected_query": "SELECT p.product_id, p.product_name, COUNT(pr.review_id) AS review_count FROM products p JOIN product_reviews pr ON p.product_id = pr.product_id WHERE p.product_id <= 200 GROUP BY p.product_id, p.product_name ORDER BY review_count DESC LIMIT 5;",
        "layman_explanation": "Count how many comments were left on each product page and display the most popular ones.",
        "time_efficiency_tip": "⚡ Time Efficiency: Limiting to 200 products bounds foreign key joins.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Top-5 heap sorting prevents buffering unnecessary rows.",
    },
    {
        "id": "30-brands-with-high-inventory",
        "number": 30,
        "title": "Brands with Largest Stock Quantity",
        "difficulty": "Easy",
        "category": "Sorting & Grouping",
        "acceptance_rate": "83.0%",
        "layman_description": (
            "Identify manufacturers with the largest stock in the warehouse. "
            "Group products by brand and calculate SUM(stock_quantity). "
            "Return brand, SUM(stock_quantity) AS total_stock, ordered by total_stock DESC. Limit to 5 results."
        ),
        "tables_used": ["products"],
        "starter_code": "-- Stock by brand\nSELECT brand, SUM(stock_quantity) AS total_stock\nFROM products\nGROUP BY brand\nORDER BY total_stock DESC\nLIMIT 5;",
        "expected_query": "SELECT brand, SUM(stock_quantity) AS total_stock FROM products GROUP BY brand ORDER BY total_stock DESC LIMIT 5;",
        "layman_explanation": "Count all unsold items belonging to each brand and show the brands taking up the most warehouse space.",
        "time_efficiency_tip": "⚡ Time Efficiency: Fast memory aggregation across 20,000 product rows.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Distinct brands fit easily in work_mem.",
    },
    {
        "id": "31-largest-single-order-items",
        "number": 31,
        "title": "Largest Single Line Item Quantities",
        "difficulty": "Easy",
        "category": "Sorting & Grouping",
        "acceptance_rate": "86.1%",
        "layman_description": (
            "Find bulk purchases for order_id <= 500. "
            "Find order items with quantity >= 5. "
            "Return order_id, product_id, quantity, unit_price, ordered by quantity DESC, order_id ASC, product_id ASC. Limit to 5 results."
        ),
        "tables_used": ["order_items"],
        "starter_code": "-- Bulk order items\nSELECT order_id, product_id, quantity, unit_price\nFROM order_items\nWHERE order_id <= 500 AND quantity >= 5\nORDER BY quantity DESC, order_id ASC, product_id ASC\nLIMIT 5;",
        "expected_query": "SELECT order_id, product_id, quantity, unit_price FROM order_items WHERE order_id <= 500 AND quantity >= 5 ORDER BY quantity DESC, order_id ASC, product_id ASC LIMIT 5;",
        "layman_explanation": "Find receipts where someone bought five or more units of the exact same item.",
        "time_efficiency_tip": "⚡ Time Efficiency: Order_id range filter prevents full table scanning.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Stops immediately upon filling the 5-row buffer.",
    },
    {
        "id": "32-customer-signup-yearly-growth",
        "number": 32,
        "title": "New User Registrations by Year",
        "difficulty": "Easy",
        "category": "Sorting & Grouping",
        "acceptance_rate": "87.5%",
        "layman_description": (
            "Inspect annual user growth for customer_id <= 10000. "
            "Extract year from signup_date using EXTRACT(YEAR FROM signup_date). "
            "Return EXTRACT(YEAR FROM signup_date)::int AS signup_year, COUNT(*) AS new_users, ordered by signup_year ASC."
        ),
        "tables_used": ["customers"],
        "starter_code": "-- Annual registrations\nSELECT EXTRACT(YEAR FROM signup_date)::int AS signup_year, COUNT(*) AS new_users\nFROM customers\nWHERE customer_id <= 10000\nGROUP BY EXTRACT(YEAR FROM signup_date)\nORDER BY signup_year ASC;",
        "expected_query": "SELECT EXTRACT(YEAR FROM signup_date)::int AS signup_year, COUNT(*) AS new_users FROM customers WHERE customer_id <= 10000 GROUP BY EXTRACT(YEAR FROM signup_date) ORDER BY signup_year ASC;",
        "layman_explanation": "Count how many users signed up each calendar year to measure platform adoption.",
        "time_efficiency_tip": "⚡ Time Efficiency: Bounded customer ID range executes in single-digit milliseconds.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Outputs fewer than 10 rows.",
    },
    {
        "id": "33-product-price-range-tiering",
        "number": 33,
        "title": "Product Pricing Tier Counts (CASE)",
        "difficulty": "Medium",
        "category": "Sorting & Grouping",
        "acceptance_rate": "76.4%",
        "layman_description": (
            "Classify products into price tiers: 'Budget' (< $50), 'Standard' ($50-$200), 'Luxury' (> $200). "
            "Count products in each tier using CASE WHEN. "
            "Return price_tier, COUNT(*) AS total_count, ordered by total_count DESC."
        ),
        "tables_used": ["products"],
        "starter_code": "-- Categorize price tiers\nSELECT \n  CASE \n    WHEN price < 50 THEN 'Budget'\n    WHEN price BETWEEN 50 AND 200 THEN 'Standard'\n    ELSE 'Luxury'\n  END AS price_tier,\n  COUNT(*) AS total_count\nFROM products\nGROUP BY price_tier\nORDER BY total_count DESC;",
        "expected_query": "SELECT CASE WHEN price < 50 THEN 'Budget' WHEN price BETWEEN 50 AND 200 THEN 'Standard' ELSE 'Luxury' END AS price_tier, COUNT(*) AS total_count FROM products GROUP BY price_tier ORDER BY total_count DESC;",
        "layman_explanation": "Categorize products into Budget, Standard, or Luxury buckets and count how many items fall into each bucket.",
        "time_efficiency_tip": "⚡ Time Efficiency: Single sequential pass evaluates the CASE expression without subqueries.",
        "memory_efficiency_tip": "💾 Memory Efficiency: 3 distinct groups require virtually zero aggregation memory.",
    },
    {
        "id": "34-order-item-count-per-order",
        "number": 34,
        "title": "Orders with Highest Line Item Count",
        "difficulty": "Easy",
        "category": "Sorting & Grouping",
        "acceptance_rate": "82.3%",
        "layman_description": (
            "Find shopping carts with the most unique items for order_id <= 500. "
            "Count lines per order_id in order_items. "
            "Return order_id, COUNT(*) AS items_count, ordered by items_count DESC. Limit to 5 results."
        ),
        "tables_used": ["order_items"],
        "starter_code": "-- Count lines per order\nSELECT order_id, COUNT(*) AS items_count\nFROM order_items\nWHERE order_id <= 500\nGROUP BY order_id\nORDER BY items_count DESC\nLIMIT 5;",
        "expected_query": "SELECT order_id, COUNT(*) AS items_count FROM order_items WHERE order_id <= 500 GROUP BY order_id ORDER BY items_count DESC LIMIT 5;",
        "layman_explanation": "Find which receipts had the longest grocery lists.",
        "time_efficiency_tip": "⚡ Time Efficiency: Primary index range filter keeps lookup instant.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Aggregates strictly within bounded buffer.",
    },
    {
        "id": "35-highest-average-rated-brands",
        "number": 35,
        "title": "Brands with Highest Quality Ratings",
        "difficulty": "Medium",
        "category": "Sorting & Grouping",
        "acceptance_rate": "72.0%",
        "layman_description": (
            "Find top brands based on average review score for product_id <= 200. "
            "Join products and product_reviews, calculate ROUND(AVG(rating)::numeric, 2). "
            "Return brand, avg_rating, COUNT(review_id) AS total_reviews, ordered by avg_rating DESC. Limit to 5 results."
        ),
        "tables_used": ["products", "product_reviews"],
        "starter_code": "-- Average rating by brand\nSELECT p.brand, ROUND(AVG(pr.rating)::numeric, 2) AS avg_rating, COUNT(pr.review_id) AS total_reviews\nFROM products p\nJOIN product_reviews pr ON p.product_id = pr.product_id\nWHERE p.product_id <= 200\nGROUP BY p.brand\nHAVING COUNT(pr.review_id) >= 2\nORDER BY avg_rating DESC\nLIMIT 5;",
        "expected_query": "SELECT p.brand, ROUND(AVG(pr.rating)::numeric, 2) AS avg_rating, COUNT(pr.review_id) AS total_reviews FROM products p JOIN product_reviews pr ON p.product_id = pr.product_id WHERE p.product_id <= 200 GROUP BY p.brand HAVING COUNT(pr.review_id) >= 2 ORDER BY avg_rating DESC LIMIT 5;",
        "layman_explanation": "Average the customer review scores for each brand and rank the best-rated manufacturers.",
        "time_efficiency_tip": "⚡ Time Efficiency: Product ID constraint bounds join rows before grouping.",
        "memory_efficiency_tip": "💾 Memory Efficiency: HAVING filters out low sample sizes before sorting.",
    },
    {
        "id": "36-customer-orders-by-gender",
        "number": 36,
        "title": "Demographic Purchase Comparison",
        "difficulty": "Easy",
        "category": "Sorting & Grouping",
        "acceptance_rate": "84.1%",
        "layman_description": (
            "Analyze order distribution by gender for customer_id <= 500. "
            "Join customers and orders. "
            "Return c.gender, COUNT(o.order_id) AS total_orders, ROUND(AVG(o.total_amount)::numeric, 2) AS avg_order_amount, ordered by total_orders DESC."
        ),
        "tables_used": ["customers", "orders"],
        "starter_code": "-- Demographics breakdown\nSELECT c.gender, COUNT(o.order_id) AS total_orders, ROUND(AVG(o.total_amount)::numeric, 2) AS avg_order_amount\nFROM customers c\nJOIN orders o ON c.customer_id = o.customer_id\nWHERE c.customer_id <= 500\nGROUP BY c.gender\nORDER BY total_orders DESC;",
        "expected_query": "SELECT c.gender, COUNT(o.order_id) AS total_orders, ROUND(AVG(o.total_amount)::numeric, 2) AS avg_order_amount FROM customers c JOIN orders o ON c.customer_id = o.customer_id WHERE c.customer_id <= 500 GROUP BY c.gender ORDER BY total_orders DESC;",
        "layman_explanation": "Break down shopping habits by customer gender demographics.",
        "time_efficiency_tip": "⚡ Time Efficiency: Fast nested loop join on indexed customer_id.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Produces only 2-3 aggregate rows.",
    },

    # =========================================================================
    # TRACK 5: ADVANCED JOINS & CASE LOGIC (Questions 37 - 42)
    # =========================================================================
    {
        "id": "37-customer-activity-status",
        "number": 37,
        "title": "Customer Loyalty Tiering",
        "difficulty": "Medium",
        "category": "Advanced Joins",
        "acceptance_rate": "68.9%",
        "layman_description": (
            "Classify customers into 'VIP' (total spend > $500), 'Active' ($100-$500), or 'Casual' (< $100) for customer_id <= 100. "
            "Join customers and orders. Return customer_id, name, total_spend, and loyalty_tier, ordered by total_spend DESC. Limit to 5 results."
        ),
        "tables_used": ["customers", "orders"],
        "starter_code": "-- Loyalty status with CASE\nSELECT \n  c.customer_id, \n  c.name, \n  SUM(o.total_amount) AS total_spend,\n  CASE \n    WHEN SUM(o.total_amount) > 500 THEN 'VIP'\n    WHEN SUM(o.total_amount) BETWEEN 100 AND 500 THEN 'Active'\n    ELSE 'Casual'\n  END AS loyalty_tier\nFROM customers c\nJOIN orders o ON c.customer_id = o.customer_id\nWHERE c.customer_id <= 100\nGROUP BY c.customer_id, c.name\nORDER BY total_spend DESC\nLIMIT 5;",
        "expected_query": "SELECT c.customer_id, c.name, SUM(o.total_amount) AS total_spend, CASE WHEN SUM(o.total_amount) > 500 THEN 'VIP' WHEN SUM(o.total_amount) BETWEEN 100 AND 500 THEN 'Active' ELSE 'Casual' END AS loyalty_tier FROM customers c JOIN orders o ON c.customer_id = o.customer_id WHERE c.customer_id <= 100 GROUP BY c.customer_id, c.name ORDER BY total_spend DESC LIMIT 5;",
        "layman_explanation": "Tag customers as VIP or Casual depending on how much total money they spent.",
        "time_efficiency_tip": "⚡ Time Efficiency: Aggregates within 100-customer boundary to avoid table scanning.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Compact result representation.",
    },
    {
        "id": "38-products-with-high-and-low-reviews",
        "number": 38,
        "title": "Product Rating Spread (Min & Max)",
        "difficulty": "Medium",
        "category": "Advanced Joins",
        "acceptance_rate": "67.4%",
        "layman_description": (
            "Find products with mixed reviews for product_id <= 100. "
            "Calculate MIN(rating) and MAX(rating). "
            "Return product_id, product_name, MIN(rating) AS min_rating, MAX(rating) AS max_rating, ordered by product_id ASC. Limit to 5 results."
        ),
        "tables_used": ["products", "product_reviews"],
        "starter_code": "-- Min and max ratings\nSELECT p.product_id, p.product_name, MIN(pr.rating) AS min_rating, MAX(pr.rating) AS max_rating\nFROM products p\nJOIN product_reviews pr ON p.product_id = pr.product_id\nWHERE p.product_id <= 100\nGROUP BY p.product_id, p.product_name\nHAVING MIN(pr.rating) <> MAX(pr.rating)\nORDER BY p.product_id ASC\nLIMIT 5;",
        "expected_query": "SELECT p.product_id, p.product_name, MIN(pr.rating) AS min_rating, MAX(pr.rating) AS max_rating FROM products p JOIN product_reviews pr ON p.product_id = pr.product_id WHERE p.product_id <= 100 GROUP BY p.product_id, p.product_name HAVING MIN(pr.rating) <> MAX(pr.rating) ORDER BY p.product_id ASC LIMIT 5;",
        "layman_explanation": "Find items that received both good and bad reviews (where lowest score != highest score).",
        "time_efficiency_tip": "⚡ Time Efficiency: Min/Max aggregators operate in parallel within group state.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Simple scalar tracking avoids list retention.",
    },
    {
        "id": "39-order-totals-vs-calculated-sum",
        "number": 39,
        "title": "Order Total Integrity Audit",
        "difficulty": "Hard",
        "category": "Advanced Joins",
        "acceptance_rate": "58.1%",
        "layman_description": (
            "Verify that order total_amount matches the sum of its order_items for order_id <= 50. "
            "Join orders and order_items. Calculate SUM(quantity * unit_price). "
            "Return o.order_id, o.total_amount, SUM(oi.quantity * oi.unit_price) AS calculated_total, ordered by o.order_id ASC. Limit to 5 results."
        ),
        "tables_used": ["orders", "order_items"],
        "starter_code": "-- Audit invoice totals\nSELECT o.order_id, o.total_amount, SUM(oi.quantity * oi.unit_price) AS calculated_total\nFROM orders o\nJOIN order_items oi ON o.order_id = oi.order_id\nWHERE o.order_id <= 50\nGROUP BY o.order_id, o.total_amount\nORDER BY o.order_id ASC\nLIMIT 5;",
        "expected_query": "SELECT o.order_id, o.total_amount, SUM(oi.quantity * oi.unit_price) AS calculated_total FROM orders o JOIN order_items oi ON o.order_id = oi.order_id WHERE o.order_id <= 50 GROUP BY o.order_id, o.total_amount ORDER BY o.order_id ASC LIMIT 5;",
        "layman_explanation": "Auditing receipts: check if the receipt total equals the price of each item multiplied by its quantity.",
        "time_efficiency_tip": "⚡ Time Efficiency: Direct primary key range index scan.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Compact grouping buffer.",
    },
    {
        "id": "40-self-join-repeat-purchasers",
        "number": 40,
        "title": "Consecutive Order Interval",
        "difficulty": "Hard",
        "category": "Advanced Joins",
        "acceptance_rate": "55.0%",
        "layman_description": (
            "Compare pairs of orders placed by the same customer for customer_id <= 50. "
            "Join orders to itself on customer_id where o1.order_id < o2.order_id. "
            "Return o1.customer_id, o1.order_id AS first_order, o2.order_id AS second_order, ordered by o1.customer_id ASC, o1.order_id ASC, o2.order_id ASC. Limit to 5 results."
        ),
        "tables_used": ["orders"],
        "starter_code": "-- Self-join on orders\nSELECT o1.customer_id, o1.order_id AS first_order, o2.order_id AS second_order\nFROM orders o1\nJOIN orders o2 ON o1.customer_id = o2.customer_id AND o1.order_id < o2.order_id\nWHERE o1.customer_id <= 50\nORDER BY o1.customer_id ASC, o1.order_id ASC, o2.order_id ASC\nLIMIT 5;",
        "expected_query": "SELECT o1.customer_id, o1.order_id AS first_order, o2.order_id AS second_order FROM orders o1 JOIN orders o2 ON o1.customer_id = o2.customer_id AND o1.order_id < o2.order_id WHERE o1.customer_id <= 50 ORDER BY o1.customer_id ASC, o1.order_id ASC, o2.order_id ASC LIMIT 5;",
        "layman_explanation": "Lining up a customer's receipts side by side to compare order pairs.",
        "time_efficiency_tip": "⚡ Time Efficiency: Using '<' instead of '!=' eliminates duplicate symmetric pairs and halves comparison cost.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Bounds prevent cartesian explosion.",
    },
    {
        "id": "41-popular-products-by-review-ratio",
        "number": 41,
        "title": "Positive Review Percentage",
        "difficulty": "Medium",
        "category": "Advanced Joins",
        "acceptance_rate": "66.2%",
        "layman_description": (
            "Find the percentage of positive reviews (rating >= 4) for product_id <= 100. "
            "Join products and product_reviews. Calculate percentage rounded to 1 decimal place. "
            "Return product_id, product_name, ROUND(100.0 * COUNT(CASE WHEN rating >= 4 THEN 1 END) / COUNT(*), 1) AS positive_pct, ordered by positive_pct DESC. Limit to 5 results."
        ),
        "tables_used": ["products", "product_reviews"],
        "starter_code": "-- Compute positive review percentage\nSELECT \n  p.product_id, \n  p.product_name,\n  ROUND(100.0 * COUNT(CASE WHEN pr.rating >= 4 THEN 1 END) / COUNT(*), 1) AS positive_pct\nFROM products p\nJOIN product_reviews pr ON p.product_id = pr.product_id\nWHERE p.product_id <= 100\nGROUP BY p.product_id, p.product_name\nHAVING COUNT(*) >= 2\nORDER BY positive_pct DESC\nLIMIT 5;",
        "expected_query": "SELECT p.product_id, p.product_name, ROUND(100.0 * COUNT(CASE WHEN pr.rating >= 4 THEN 1 END) / COUNT(*), 1) AS positive_pct FROM products p JOIN product_reviews pr ON p.product_id = pr.product_id WHERE p.product_id <= 100 GROUP BY p.product_id, p.product_name HAVING COUNT(*) >= 2 ORDER BY positive_pct DESC LIMIT 5;",
        "layman_explanation": "Calculate what percentage of reviewers gave thumbs up (4 or 5 stars) out of total reviews.",
        "time_efficiency_tip": "⚡ Time Efficiency: Conditional aggregation in a single query pass avoids multiple joins.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Filters early with HAVING.",
    },
    {
        "id": "42-cross-country-order-shipping",
        "number": 42,
        "title": "Cross-Border Shipping Discrepancies",
        "difficulty": "Medium",
        "category": "Advanced Joins",
        "acceptance_rate": "69.1%",
        "layman_description": (
            "Find customers whose shipping country does not match their registered country for customer_id <= 200. "
            "Join customers and orders where c.country != o.shipping_country. "
            "Return c.customer_id, c.name, c.country, o.shipping_country, ordered by c.customer_id ASC, o.shipping_country ASC. Limit to 5 results."
        ),
        "tables_used": ["customers", "orders"],
        "starter_code": "-- Cross-border mismatch\nSELECT c.customer_id, c.name, c.country, o.shipping_country\nFROM customers c\nJOIN orders o ON c.customer_id = o.customer_id\nWHERE c.customer_id <= 200 AND c.country <> o.shipping_country\nORDER BY c.customer_id ASC, o.shipping_country ASC\nLIMIT 5;",
        "expected_query": "SELECT c.customer_id, c.name, c.country, o.shipping_country FROM customers c JOIN orders o ON c.customer_id = o.customer_id WHERE c.customer_id <= 200 AND c.country <> o.shipping_country ORDER BY c.customer_id ASC, o.shipping_country ASC LIMIT 5;",
        "layman_explanation": "Flag orders where someone registered in one country shipped their package to a completely different country.",
        "time_efficiency_tip": "⚡ Time Efficiency: Predicate c.customer_id <= 200 limits lookup to indexed branch.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Only mismatching rows pass through buffer.",
    },

    # =========================================================================
    # TRACK 6: SUBQUERIES & WINDOW FUNCTIONS (Questions 43 - 50)
    # =========================================================================
    {
        "id": "43-second-highest-priced-product",
        "number": 43,
        "title": "Classic: Second Highest Product Price",
        "difficulty": "Medium",
        "category": "Subqueries & Window Functions",
        "acceptance_rate": "62.4%",
        "layman_description": (
            "The classic LeetCode interview question: find the second highest distinct price among products. "
            "Return MAX(price) AS second_highest_price from products where price < (SELECT MAX(price) FROM products)."
        ),
        "tables_used": ["products"],
        "starter_code": "-- Second highest price\nSELECT MAX(price) AS second_highest_price\nFROM products\nWHERE price < (SELECT MAX(price) FROM products);",
        "expected_query": "SELECT MAX(price) AS second_highest_price FROM products WHERE price < (SELECT MAX(price) FROM products);",
        "layman_explanation": "Find the highest price, ignore it, and find the highest price of everything left.",
        "time_efficiency_tip": "⚡ Time Efficiency: B-Tree index on price resolves MAX in O(log N) through index backward scan.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Scalar subquery uses a single float memory cell.",
    },
    {
        "id": "44-dense-rank-products-by-category",
        "number": 44,
        "title": "Product Price Rank within Category",
        "difficulty": "Medium",
        "category": "Subqueries & Window Functions",
        "acceptance_rate": "64.1%",
        "layman_description": (
            "Rank products by price within each category using DENSE_RANK(). "
            "Use a CTE or subquery to select products where price_rank <= 2 for category = 'Electronics'. "
            "Return product_id, product_name, category, price, price_rank, ordered by price DESC. Limit to 5 results."
        ),
        "tables_used": ["products"],
        "starter_code": "-- DENSE_RANK window function\nWITH ranked_products AS (\n  SELECT \n    product_id, \n    product_name, \n    category, \n    price,\n    DENSE_RANK() OVER (PARTITION BY category ORDER BY price DESC) AS price_rank\n  FROM products\n  WHERE category = 'Electronics'\n)\nSELECT product_id, product_name, category, price, price_rank\nFROM ranked_products\nWHERE price_rank <= 2\nORDER BY price DESC\nLIMIT 5;",
        "expected_query": "WITH ranked_products AS (SELECT product_id, product_name, category, price, DENSE_RANK() OVER (PARTITION BY category ORDER BY price DESC) AS price_rank FROM products WHERE category = 'Electronics') SELECT product_id, product_name, category, price, price_rank FROM ranked_products WHERE price_rank <= 2 ORDER BY price DESC LIMIT 5;",
        "layman_explanation": "Group items by category, award gold medals (rank 1) and silver medals (rank 2) to the most expensive items.",
        "time_efficiency_tip": "⚡ Time Efficiency: DENSE_RANK maintains running ties without expensive multi-pass grouping.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Partition buffer cleans up immediately after each category finishes.",
    },
    {
        "id": "45-running-total-revenue",
        "number": 45,
        "title": "Cumulative Running Total of Order Revenue",
        "difficulty": "Medium",
        "category": "Subqueries & Window Functions",
        "acceptance_rate": "63.7%",
        "layman_description": (
            "Calculate a cumulative running total of revenue across orders for order_id <= 20. "
            "Use SUM(total_amount) OVER (ORDER BY order_id ASC). "
            "Return order_id, total_amount, running_total, ordered by order_id ASC. Limit to 5 results."
        ),
        "tables_used": ["orders"],
        "starter_code": "-- Cumulative running total\nSELECT \n  order_id, \n  total_amount,\n  SUM(total_amount) OVER (ORDER BY order_id ASC) AS running_total\nFROM orders\nWHERE order_id <= 20\nORDER BY order_id ASC\nLIMIT 5;",
        "expected_query": "SELECT order_id, total_amount, SUM(total_amount) OVER (ORDER BY order_id ASC) AS running_total FROM orders WHERE order_id <= 20 ORDER BY order_id ASC LIMIT 5;",
        "layman_explanation": "Add each new receipt amount onto a running calculator tally as receipts arrive.",
        "time_efficiency_tip": "⚡ Time Efficiency: Window aggregation computes running totals in a single linear O(N) scan.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Requires only 1 accumulator variable in memory.",
    },
    {
        "id": "46-orders-above-average",
        "number": 46,
        "title": "Orders Exceeding Average Spending",
        "difficulty": "Medium",
        "category": "Subqueries & Window Functions",
        "acceptance_rate": "67.0%",
        "layman_description": (
            "Find orders whose total_amount is strictly greater than the overall average order amount for order_id <= 1000. "
            "Use a subquery to compare against AVG(total_amount). "
            "Return order_id, customer_id, total_amount, ordered by total_amount DESC. Limit to 5 results."
        ),
        "tables_used": ["orders"],
        "starter_code": "-- Subquery comparing against average\nSELECT order_id, customer_id, total_amount\nFROM orders\nWHERE order_id <= 1000 AND total_amount > (\n  SELECT AVG(total_amount) FROM orders WHERE order_id <= 1000\n)\nORDER BY total_amount DESC\nLIMIT 5;",
        "expected_query": "SELECT order_id, customer_id, total_amount FROM orders WHERE order_id <= 1000 AND total_amount > (SELECT AVG(total_amount) FROM orders WHERE order_id <= 1000) ORDER BY total_amount DESC LIMIT 5;",
        "layman_explanation": "Calculate the average bill, then list every receipt that was higher than average.",
        "time_efficiency_tip": "⚡ Time Efficiency: The subquery runs once (InitPlan) and caches the scalar average.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Subquery result cached in register, not recomputed per row.",
    },
    {
        "id": "47-lead-and-lag-order-gaps",
        "number": 47,
        "title": "Comparing Previous Order Value (LAG)",
        "difficulty": "Hard",
        "category": "Subqueries & Window Functions",
        "acceptance_rate": "57.3%",
        "layman_description": (
            "Analyze order changes using the LAG() window function for customer_id = 1. "
            "Return order_id, order_date, total_amount, LAG(total_amount, 1) OVER (ORDER BY order_date ASC) AS prev_amount, ordered by order_date ASC. Limit to 5 results."
        ),
        "tables_used": ["orders"],
        "starter_code": "-- Window LAG function\nSELECT \n  order_id, \n  order_date, \n  total_amount,\n  LAG(total_amount, 1) OVER (ORDER BY order_date ASC) AS prev_amount\nFROM orders\nWHERE customer_id = 1\nORDER BY order_date ASC\nLIMIT 5;",
        "expected_query": "SELECT order_id, order_date, total_amount, LAG(total_amount, 1) OVER (ORDER BY order_date ASC) AS prev_amount FROM orders WHERE customer_id = 1 ORDER BY order_date ASC LIMIT 5;",
        "layman_explanation": "Look at each purchase alongside the customer's previous purchase to see if they spent more or less.",
        "time_efficiency_tip": "⚡ Time Efficiency: LAG looks back exactly 1 row in the sorted pipeline without extra lookups.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Window buffer maintains an offset of 1 row.",
    },
    {
        "id": "48-nth-highest-order-cte",
        "number": 48,
        "title": "Top 3 Orders per Customer via ROW_NUMBER",
        "difficulty": "Hard",
        "category": "Subqueries & Window Functions",
        "acceptance_rate": "54.8%",
        "layman_description": (
            "Find the top 2 highest value orders for each customer among customer_id <= 30. "
            "Use ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY total_amount DESC). "
            "Return customer_id, order_id, total_amount, rn, ordered by customer_id ASC, total_amount DESC. Limit to 5 results."
        ),
        "tables_used": ["orders"],
        "starter_code": "-- Top N per group with ROW_NUMBER\nWITH ranked_orders AS (\n  SELECT \n    customer_id, \n    order_id, \n    total_amount,\n    ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY total_amount DESC) AS rn\n  FROM orders\n  WHERE customer_id <= 30\n)\nSELECT customer_id, order_id, total_amount, rn\nFROM ranked_orders\nWHERE rn <= 2\nORDER BY customer_id ASC, total_amount DESC\nLIMIT 5;",
        "expected_query": "WITH ranked_orders AS (SELECT customer_id, order_id, total_amount, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY total_amount DESC) AS rn FROM orders WHERE customer_id <= 30) SELECT customer_id, order_id, total_amount, rn FROM ranked_orders WHERE rn <= 2 ORDER BY customer_id ASC, total_amount DESC LIMIT 5;",
        "layman_explanation": "For every customer, pick out their two most expensive shopping sprees.",
        "time_efficiency_tip": "⚡ Time Efficiency: Partitioning by customer_id avoids cartesian products.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Row number filter discards lower-tier purchases immediately.",
    },
    {
        "id": "49-correlated-subquery-price-gap",
        "number": 49,
        "title": "Products Costlier than Category Average",
        "difficulty": "Hard",
        "category": "Subqueries & Window Functions",
        "acceptance_rate": "53.2%",
        "layman_description": (
            "Find products priced higher than the average price of their own category for product_id <= 100. "
            "Use a correlated subquery comparing p1.price > (SELECT AVG(p2.price) FROM products p2 WHERE p2.category = p1.category). "
            "Return p1.product_id, p1.product_name, p1.category, p1.price, ordered by p1.price DESC. Limit to 5 results."
        ),
        "tables_used": ["products"],
        "starter_code": "-- Correlated subquery\nSELECT p1.product_id, p1.product_name, p1.category, p1.price\nFROM products p1\nWHERE p1.product_id <= 100 AND p1.price > (\n  SELECT AVG(p2.price) FROM products p2 WHERE p2.category = p1.category\n)\nORDER BY p1.price DESC\nLIMIT 5;",
        "expected_query": "SELECT p1.product_id, p1.product_name, p1.category, p1.price FROM products p1 WHERE p1.product_id <= 100 AND p1.price > (SELECT AVG(p2.price) FROM products p2 WHERE p2.category = p1.category) ORDER BY p1.price DESC LIMIT 5;",
        "layman_explanation": "Check if an item costs more than typical products in its own department.",
        "time_efficiency_tip": "⚡ Time Efficiency: An index on (category, price) allows PostgreSQL to compute category averages with index-only scans.",
        "memory_efficiency_tip": "💾 Memory Efficiency: CTE can alternatively pre-compute category averages to avoid correlation loops.",
    },
    {
        "id": "50-grand-champion-sales-share",
        "number": 50,
        "title": "Grand Finale: Product Market Share Ratio",
        "difficulty": "Hard",
        "category": "Subqueries & Window Functions",
        "acceptance_rate": "49.5%",
        "layman_description": (
            "The ultimate test: calculate each product's percentage share of total stock across its category. "
            "Use SUM(stock_quantity) OVER (PARTITION BY category). "
            "Return product_id, product_name, category, stock_quantity, ROUND(100.0 * stock_quantity / NULLIF(SUM(stock_quantity) OVER (PARTITION BY category), 0), 2) AS stock_share_pct, ordered by stock_share_pct DESC. Limit to 5 results."
        ),
        "tables_used": ["products"],
        "starter_code": "-- Window partition market share calculation\nSELECT \n  product_id, \n  product_name, \n  category, \n  stock_quantity,\n  ROUND(100.0 * stock_quantity / NULLIF(SUM(stock_quantity) OVER (PARTITION BY category), 0), 2) AS stock_share_pct\nFROM products\nWHERE category = 'Electronics'\nORDER BY stock_share_pct DESC\nLIMIT 5;",
        "expected_query": "SELECT product_id, product_name, category, stock_quantity, ROUND(100.0 * stock_quantity / NULLIF(SUM(stock_quantity) OVER (PARTITION BY category), 0), 2) AS stock_share_pct FROM products WHERE category = 'Electronics' ORDER BY stock_share_pct DESC LIMIT 5;",
        "layman_explanation": "Determine what fraction of the electronics warehouse is taken up by each specific model.",
        "time_efficiency_tip": "⚡ Time Efficiency: Window SUM() over partition computes category denominators in a single linear pass.",
        "memory_efficiency_tip": "💾 Memory Efficiency: Avoids self-joining the table back to an aggregated version of itself.",
    },
]
