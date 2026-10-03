import io
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.db.connection import get_db_connection


@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_admin_csv_preview(client: TestClient):
    csv_content = (
        "Customer Name,Age,Balance,Active,Joined At\n"
        "Alice Smith,29,1250.50,true,2024-01-15\n"
        "Bob Jones,35,850.00,false,2024-02-20\n"
        "Charlie,42,3200.75,true,2024-03-05\n"
    )
    files = {"file": ("test_customers.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = client.post("/api/v1/admin/preview-csv", files=files)
    assert response.status_code == 200
    data = response.json()

    assert data["suggested_table_name"] == "test_customers"
    assert data["total_columns"] == 5

    col_types = {c["sanitized_name"]: c["inferred_type"] for c in data["columns"]}
    assert col_types["customer_name"] == "TEXT"
    assert col_types["age"] == "INTEGER"
    assert col_types["balance"] == "NUMERIC"
    assert col_types["active"] == "BOOLEAN"
    assert col_types["joined_at"] == "DATE"

    assert len(data["sample_rows"]) == 3
    assert data["sample_rows"][0]["customer_name"] == "Alice Smith"


def test_admin_csv_import_flow(client: TestClient):
    table_name = "test_admin_ingest_tmp"
    csv_content = (
        "Item Name,Unit Price,Quantity\n"
        "Keyboard,49.99,10\n"
        "Mouse,19.99,25\n"
        "Monitor,199.99,5\n"
    )

    try:
        # Import CSV
        files = {"file": ("items.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        data = {
            "table_name": table_name,
            "mode": "replace",
        }
        res = client.post("/api/v1/admin/import-csv", files=files, data=data)
        assert res.status_code == 200, res.text
        json_data = res.json()
        assert json_data["status"] == "success"
        assert json_data["table"] == table_name
        assert json_data["rows_inserted"] == 3

        # Verify through /tables endpoint
        tables_res = client.get("/api/v1/admin/tables")
        assert tables_res.status_code == 200
        tables = tables_res.json()
        target = next((t for t in tables if t["table_name"] == table_name), None)
        assert target is not None
        assert target["row_count"] == 3
        assert "item_name" in target["columns"]
        assert "unit_price" in target["columns"]

        # Test duplicate import with mode="fail"
        files2 = {"file": ("items.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        fail_res = client.post(
            "/api/v1/admin/import-csv",
            files=files2,
            data={"table_name": table_name, "mode": "fail"},
        )
        assert fail_res.status_code == 400

    finally:
        # Clean up created table
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE;')
                conn.commit()
        except Exception:
            pass


def test_admin_list_tables_and_databases(client: TestClient):
    # Test GET /admin/databases
    res_db = client.get("/api/v1/admin/databases")
    assert res_db.status_code == 200
    dbs = res_db.json()
    assert isinstance(dbs, list)
    assert any(d["is_current"] for d in dbs)

    # Test GET /admin/tables
    res_tbl = client.get("/api/v1/admin/tables")
    assert res_tbl.status_code == 200
    tables = res_tbl.json()
    assert isinstance(tables, list)
    assert len(tables) > 0
    assert "table_name" in tables[0]
    assert "columns" in tables[0]
    assert "row_count" in tables[0]


def test_admin_excel_multi_sheet_flow(client: TestClient):
    import pandas as pd

    # Generate in-memory Excel workbook with 2 sheets
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df_cat = pd.DataFrame([
            {"category_id": 1, "category_name": "SUV", "description": "Sport Utility Vehicle"},
            {"category_id": 2, "category_name": "Sedan", "description": "4-door passenger car"},
            {"category_id": 3, "category_name": "Electric", "description": "Battery electric vehicle"},
        ])
        df_cat.to_excel(writer, sheet_name="carCategories", index=False)

        df_mod = pd.DataFrame([
            {"model_id": 101, "model_name": "Tesla Model Y", "category_id": 3, "price": 52990.00, "in_stock": True},
            {"model_id": 102, "model_name": "Toyota RAV4", "category_id": 1, "price": 31500.50, "in_stock": True},
            {"model_id": 103, "model_name": "Honda Civic", "category_id": 2, "price": 24950.00, "in_stock": False},
        ])
        df_mod.to_excel(writer, sheet_name="carModels", index=False)

    excel_bytes = buf.getvalue()

    # 1. Preview default sheet (carCategories)
    files = {"file": ("carDB.xlsx", io.BytesIO(excel_bytes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    res_preview = client.post("/api/v1/admin/preview-csv", files=files)
    assert res_preview.status_code == 200, res_preview.text
    prev_data = res_preview.json()
    assert prev_data["is_excel"] is True
    assert prev_data["sheet_names"] == ["carCategories", "carModels"]
    assert prev_data["active_sheet"] == "carCategories"
    assert prev_data["suggested_table_name"] == "car_categories"

    # 2. Preview second sheet (carModels)
    files2 = {"file": ("carDB.xlsx", io.BytesIO(excel_bytes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    res_preview2 = client.post("/api/v1/admin/preview-csv", files=files2, data={"sheet_name": "carModels"})
    assert res_preview2.status_code == 200
    prev_data2 = res_preview2.json()
    assert prev_data2["active_sheet"] == "carModels"
    assert prev_data2["suggested_table_name"] == "car_models"

    # 3. Batch import all sheets into PostgreSQL
    try:
        files3 = {"file": ("carDB.xlsx", io.BytesIO(excel_bytes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        res_import = client.post("/api/v1/admin/import-all-sheets", files=files3, data={"mode": "replace"})
        assert res_import.status_code == 200, res_import.text
        import_data = res_import.json()
        assert import_data["status"] == "success"
        assert import_data["total_rows_inserted"] == 6
        assert len(import_data["tables"]) == 2

        # Verify tables in database
        tables_res = client.get("/api/v1/admin/tables")
        tables = {t["table_name"]: t for t in tables_res.json()}
        assert "car_categories" in tables
        assert "car_models" in tables
        assert tables["car_categories"]["row_count"] == 3
        assert tables["car_models"]["row_count"] == 3

    finally:
        # Clean up created tables
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute('DROP TABLE IF EXISTS "car_models" CASCADE;')
                    cur.execute('DROP TABLE IF EXISTS "car_categories" CASCADE;')
                conn.commit()
        except Exception:
            pass


def test_admin_explorer_schema_and_records(client: TestClient):
    # Fetch tables first to pick an existing table in e-commerce
    tbl_res = client.get("/api/v1/admin/tables")
    assert tbl_res.status_code == 200
    tables = tbl_res.json()
    assert len(tables) > 0
    sample_table = tables[0]["table_name"]

    # 1. Test GET /tables/{table_name}/schema
    schema_res = client.get(f"/api/v1/admin/tables/{sample_table}/schema")
    assert schema_res.status_code == 200, schema_res.text
    schema_data = schema_res.json()
    assert schema_data["table"] == sample_table
    assert "columns" in schema_data
    assert len(schema_data["columns"]) > 0
    col0 = schema_data["columns"][0]
    assert "name" in col0
    assert "type" in col0
    assert "is_nullable" in col0
    assert "is_primary_key" in col0

    # 2. Test GET /tables/{table_name}/records with pagination
    rec_res = client.get(f"/api/v1/admin/tables/{sample_table}/records?limit=10&offset=0")
    assert rec_res.status_code == 200, rec_res.text
    rec_data = rec_res.json()
    assert rec_data["table"] == sample_table
    assert rec_data["limit"] == 10
    assert rec_data["offset"] == 0
    assert "columns" in rec_data
    assert "rows" in rec_data
    assert "total_records" in rec_data
    assert isinstance(rec_data["rows"], list)

    # 3. Test non-existent table schema returns 404
    non_existent = client.get("/api/v1/admin/tables/non_existent_table_9999/schema")
    assert non_existent.status_code == 404


def test_admin_switch_database(client: TestClient):
    from app.core.config import get_settings

    settings = get_settings()
    current_db = settings.DB_NAME

    # Switch to current database
    res = client.post("/api/v1/admin/switch-db", json={"database_name": current_db})
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "success"
    assert data["active_database"] == current_db
    assert "message" in data


def test_admin_multiple_csv_import(client: TestClient):
    csv1 = "sku,product_name,stock\nSKU-1,Laptop,15\nSKU-2,Phone,30\n"
    csv2 = "branch_id,city,manager\n101,New York,Alice\n102,Chicago,Bob\n"

    tbl1 = "test_multi_prod"
    tbl2 = "test_multi_branches"

    try:
        files = [
            ("files", (f"{tbl1}.csv", io.BytesIO(csv1.encode("utf-8")), "text/csv")),
            ("files", (f"{tbl2}.csv", io.BytesIO(csv2.encode("utf-8")), "text/csv")),
        ]
        res = client.post("/api/v1/admin/import-multiple-csvs", files=files, data={"mode": "replace"})
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["status"] == "success"
        assert data["total_rows_inserted"] == 4
        assert len(data["tables"]) == 2

        created_tables = {t["table"] for t in data["tables"]}
        assert tbl1 in created_tables
        assert tbl2 in created_tables

        # Check records from each table
        r1 = client.get(f"/api/v1/admin/tables/{tbl1}/records")
        assert r1.status_code == 200
        assert r1.json()["total_records"] == 2

        r2 = client.get(f"/api/v1/admin/tables/{tbl2}/records")
        assert r2.status_code == 200
        assert r2.json()["total_records"] == 2

    finally:
        for t in (tbl1, tbl2):
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(f'DROP TABLE IF EXISTS "{t}" CASCADE;')
                    conn.commit()
            except Exception:
                pass


def test_admin_column_row_table_deletion_flow(client: TestClient):
    table_name = "test_crud_deletions"

    # Setup table with raw SQL
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE;')
            cur.execute(f"""
                CREATE TABLE "{table_name}" (
                    id SERIAL PRIMARY KEY,
                    item_code TEXT NOT NULL,
                    notes TEXT,
                    price NUMERIC
                );
                INSERT INTO "{table_name}" (item_code, notes, price) VALUES
                    ('A100', 'First item', 10.50),
                    ('B200', 'Second item', 20.00),
                    ('C300', 'Third item', 30.25);
            """)
        conn.commit()

    try:
        # 1. Test Drop Column
        res_col = client.delete(f"/api/v1/admin/tables/{table_name}/columns/notes")
        assert res_col.status_code == 200, res_col.text
        assert "Column 'notes' was successfully dropped" in res_col.json()["message"]

        schema_res = client.get(f"/api/v1/admin/tables/{table_name}/schema")
        assert schema_res.status_code == 200
        col_names = [c["name"] for c in schema_res.json()["columns"]]
        assert "notes" not in col_names
        assert "item_code" in col_names

        # 2. Test Delete Row with condition
        res_del_row = client.post(
            f"/api/v1/admin/tables/{table_name}/rows/delete",
            json={"condition": {"item_code": "B200"}},
        )
        assert res_del_row.status_code == 200, res_del_row.text
        assert res_del_row.json()["affected_count"] == 1

        rec_res = client.get(f"/api/v1/admin/tables/{table_name}/records")
        assert rec_res.json()["total_records"] == 2

        # 3. Test Truncate Table
        res_trunc = client.post(f"/api/v1/admin/tables/{table_name}/truncate")
        assert res_trunc.status_code == 200, res_trunc.text

        rec_res2 = client.get(f"/api/v1/admin/tables/{table_name}/records")
        assert rec_res2.json()["total_records"] == 0

        # 4. Test Drop Table
        res_drop_tbl = client.delete(f"/api/v1/admin/tables/{table_name}")
        assert res_drop_tbl.status_code == 200, res_drop_tbl.text

        # Verify table is gone
        tbls = client.get("/api/v1/admin/tables").json()
        assert not any(t["table_name"] == table_name for t in tbls)

    finally:
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE;')
                conn.commit()
        except Exception:
            pass


def test_admin_drop_database(client: TestClient):
    import psycopg2
    from app.core.config import get_settings

    settings = get_settings()
    test_db = "test_admin_drop_temp_db"

    # Create temporary database via postgres maintenance DB
    conn = psycopg2.connect(
        dbname="postgres",
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(f'CREATE DATABASE "{test_db}";')
    conn.close()

    try:
        # 1. Attempt to drop protected system db -> must fail
        res_forbidden = client.delete("/api/v1/admin/databases/postgres")
        assert res_forbidden.status_code == 400
        assert "cannot be deleted" in res_forbidden.json()["detail"]

        # 2. Successfully drop test_db
        res_drop = client.delete(f"/api/v1/admin/databases/{test_db}")
        assert res_drop.status_code == 200, res_drop.text
        assert res_drop.json()["status"] == "success"

        # Verify database is gone
        dbs = [d["database_name"] for d in client.get("/api/v1/admin/databases").json()]
        assert test_db not in dbs

    finally:
        # Fallback cleanup
        try:
            conn = psycopg2.connect(
                dbname="postgres",
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                host=settings.DB_HOST,
                port=settings.DB_PORT,
            )
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(f'DROP DATABASE IF EXISTS "{test_db}";')
            conn.close()
        except Exception:
            pass




