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

