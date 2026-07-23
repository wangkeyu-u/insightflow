"""End-to-end API workflow coverage for interview-critical features."""

from datetime import date, timedelta

from app.config import settings
from app.dependencies import get_current_user
from app.models.customer import Customer
from app.models.inventory import Inventory, Payment, Shipment
from app.models.order import Order
from app.models.product import Product
from app.models.user import Role, User


def create_customer(client, name="Northstar Retail"):
    response = client.post(
        "/customers",
        json={
            "name": name,
            "company": f"{name} Ltd",
            "email": f"{name.lower().replace(' ', '.')}@example.com",
            "region": "Central",
            "customer_type": "enterprise",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_product(client, name="Edge Gateway", stock=24, reorder_level=5):
    response = client.post(
        "/products",
        json={
            "name": name,
            "category": "Infrastructure",
            "unit_price": 480.0,
            "cost_price": 310.0,
            "current_stock": stock,
            "reorder_level": reorder_level,
        },
    )
    assert response.status_code == 201
    return response.json()


def create_order(client, customer_id, product_id, quantity=2, unit_price=480.0):
    response = client.post(
        "/orders",
        json={
            "customer_id": customer_id,
            "items": [
                {
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": unit_price,
                }
            ],
            "region": "Central",
            "salesperson": "Maya Chen",
            "payment_status": "pending",
            "shipment_status": "processing",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_full_commercial_lifecycle_and_exports(client, db):
    first_customer = create_customer(client)
    second_customer = create_customer(client, "Summit Systems")
    product = create_product(client, stock=0, reorder_level=0)

    assert product["current_stock"] == 0
    assert product["reorder_level"] == 0

    inventory = client.get("/products/inventory").json()
    assert inventory[0]["product_id"] == product["id"]
    assert inventory[0]["quantity"] == 0
    assert inventory[0]["reorder_level"] == 0

    updated_product = client.put(
        f"/products/{product['id']}", json={"current_stock": 18}
    )
    assert updated_product.status_code == 200
    assert db.query(Inventory).filter_by(product_id=product["id"]).one().quantity == 18

    order = create_order(client, first_customer["id"], product["id"])
    assert order["total_amount"] == 960.0

    assert client.get("/dashboard/sales-trend").status_code == 200
    assert client.get("/analytics/revenue").status_code == 200
    assert client.get("/analytics/sales-targets").status_code == 200

    for search_term in ("Northstar", "Edge Gateway", "Maya Chen", str(order["id"])):
        result = client.get("/orders", params={"search": search_term}).json()
        assert result["total"] == 1
        assert result["items"][0]["id"] == order["id"]

    customer_orders = client.get(
        f"/customers/{first_customer['id']}/orders"
    ).json()
    assert [item["id"] for item in customer_orders] == [order["id"]]

    moved = client.put(
        f"/orders/{order['id']}",
        json={
            "customer_id": second_customer["id"],
            "payment_status": "paid",
            "shipment_status": "shipped",
        },
    )
    assert moved.status_code == 200
    assert moved.json()["customer_id"] == second_customer["id"]
    db.expire_all()
    assert db.get(Customer, first_customer["id"]).total_spending == 0
    assert db.get(Customer, second_customer["id"]).total_spending == 960.0

    for path, expected_header in (
        ("/export/sales.csv", b"Order ID"),
        ("/export/customers.csv", b"Total Spending"),
        ("/export/inventory.csv", b"Reorder Level"),
    ):
        exported = client.get(path)
        assert exported.status_code == 200
        assert exported.headers["content-type"].startswith("text/csv")
        assert expected_header in exported.content

    for path in (
        "/export/business-report.pdf",
        f"/export/orders/{order['id']}.pdf",
    ):
        exported = client.get(path)
        assert exported.status_code == 200
        assert exported.content.startswith(b"%PDF")

    assert client.delete(f"/orders/{order['id']}").status_code == 200
    db.expire_all()
    assert db.get(Customer, second_customer["id"]).total_spending == 0
    assert client.get(f"/orders/{order['id']}").status_code == 404
    assert client.delete(f"/products/{product['id']}").status_code == 200
    assert client.delete(f"/customers/{first_customer['id']}").status_code == 200


def test_order_deletion_cleans_payment_shipment_and_batch_relations(client, db):
    customer = create_customer(client)
    product = create_product(client)
    order = create_order(client, customer["id"], product["id"])

    db.add(
        Payment(
            order_id=order["id"],
            amount=order["total_amount"],
            method="bank_transfer",
            status="pending",
            due_date=date.today() + timedelta(days=14),
        )
    )
    db.add(
        Shipment(
            order_id=order["id"],
            carrier="DHL",
            tracking_number="IF-TEST-001",
            status="processing",
        )
    )
    db.commit()

    customer_result = client.post(
        "/batch/customers/delete", json={"ids": [customer["id"], 99999]}
    )
    assert customer_result.status_code == 200
    assert customer_result.json() == {
        "deleted": 1,
        "failed": 1,
        "errors": ["Customer #99999 not found"],
    }
    assert db.get(Customer, customer["id"]).customer_type == "archived"

    product_result = client.post(
        "/batch/products/delete", json={"ids": [product["id"]]}
    )
    assert product_result.status_code == 200
    assert db.get(Product, product["id"]).status == "archived"

    order_result = client.post(
        "/batch/orders/delete", json={"ids": [order["id"]]}
    )
    assert order_result.status_code == 200
    assert order_result.json()["deleted"] == 1
    assert db.get(Order, order["id"]) is None
    assert db.query(Payment).filter_by(order_id=order["id"]).count() == 0
    assert db.query(Shipment).filter_by(order_id=order["id"]).count() == 0


def test_csv_imports_keep_operational_metrics_in_sync(client, db):
    minimal_customer = client.post(
        "/upload/customers",
        files={"file": ("customers.csv", b"name\nCSV Customer\n", "text/csv")},
    )
    assert minimal_customer.status_code == 200
    assert minimal_customer.json()["success_rows"] == 1

    product_upload = client.post(
        "/upload/products",
        files={
            "file": (
                "products.csv",
                b"name,unit_price,stock\nCSV Sensor,125.50,9\n",
                "text/csv",
            )
        },
    )
    assert product_upload.status_code == 200
    assert product_upload.json()["success_rows"] == 1

    product = db.query(Product).filter_by(name="CSV Sensor").one()
    assert product.current_stock == 9
    assert db.query(Inventory).filter_by(product_id=product.id).one().quantity == 9

    inventory_upload = client.post(
        "/upload/inventory",
        files={
            "file": (
                "inventory.csv",
                b"product_name,quantity\nCSV Sensor,4\n",
                "text/csv",
            )
        },
    )
    assert inventory_upload.status_code == 200
    assert inventory_upload.json()["success_rows"] == 1
    db.expire_all()
    assert db.query(Product).filter_by(name="CSV Sensor").one().current_stock == 4

    order_upload = client.post(
        "/upload/orders",
        files={
            "file": (
                "orders.csv",
                (
                    b"customer_name,product_name,quantity,unit_price,order_date\n"
                    b"CSV Customer,CSV Sensor,3,125.50,2026-07-20\n"
                ),
                "text/csv",
            )
        },
    )
    assert order_upload.status_code == 200
    assert order_upload.json()["success_rows"] == 1
    db.expire_all()
    customer = db.query(Customer).filter_by(name="CSV Customer").one()
    assert customer.total_spending == 376.5
    assert customer.last_purchase_date.date().isoformat() == "2026-07-20"

    history = client.get("/upload/history").json()
    assert len(history) == 4
    assert {record["file_type"] for record in history} == {
        "customers",
        "products",
        "inventory",
        "orders",
    }

    invalid = client.post(
        "/upload/customers",
        files={"file": ("customers.txt", b"name\nNope\n", "text/plain")},
    )
    assert invalid.status_code == 400


def test_user_roles_audit_log_and_offline_ai(client, db, monkeypatch):
    manager_role = db.query(Role).filter_by(name="manager").one()
    created = client.post(
        "/users",
        json={
            "email": "manager@example.com",
            "password": "secure-password",
            "full_name": "Operations Manager",
            "role_id": manager_role.id,
        },
    )
    assert created.status_code == 201
    assert created.json()["role"]["name"] == "manager"

    user_id = created.json()["id"]
    updated = client.put(
        f"/users/{user_id}", json={"full_name": "Revenue Operations Manager"}
    )
    assert updated.status_code == 200
    assert updated.json()["full_name"] == "Revenue Operations Manager"

    admin = db.query(User).filter_by(email="admin@test.com").one()
    audit = client.post(
        "/audit-logs",
        json={
            "user_id": admin.id,
            "action": "interview_check",
            "entity_type": "system",
            "details": "Validated end-to-end workflows",
        },
    )
    assert audit.status_code == 201
    logs = client.get(
        "/audit-logs", params={"action": "interview_check"}
    ).json()
    assert len(logs) == 1
    assert logs[0]["user_email"] == "admin@test.com"

    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    ai_calls = (
        ("/ai/ask", {"question": "What needs attention?"}),
        ("/ai/generate-report", {"report_type": "weekly"}),
        ("/ai/explain-trend", {"metric": "revenue", "period": "last_month"}),
        ("/ai/inventory-suggestion", {"category": None}),
    )
    for path, payload in ai_calls:
        response = client.post(path, json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["short_answer"]
        assert body["data_evidence"]
        assert body["suggested_actions"]
        assert body["confidence"] in {"high", "medium", "low"}

    assert client.delete(f"/users/{user_id}").status_code == 200
    db.expire_all()
    assert db.get(User, user_id).is_active is False


def test_staff_permissions_are_read_only(client, db):
    from app.main import app

    staff_role = db.query(Role).filter_by(name="staff").one()
    staff = User(
        email="staff@example.com",
        hashed_password="not-used-by-dependency-override",
        full_name="Read Only Staff",
        role_id=staff_role.id,
        is_active=True,
    )
    db.add(staff)
    db.commit()

    app.dependency_overrides[get_current_user] = lambda: staff

    assert client.get("/orders").status_code == 200
    assert client.get("/customers").status_code == 200
    assert client.get("/products").status_code == 200
    assert client.get("/users").status_code == 403
    assert client.get("/audit-logs").status_code == 403
    assert client.post("/customers", json={"name": "Blocked Write"}).status_code == 403
    assert client.post("/batch/orders/delete", json={"ids": []}).status_code == 403


def test_public_registration_cannot_escalate_role(client, db):
    response = client.post(
        "/auth/register",
        json={
            "email": "self-register@example.com",
            "password": "secure-password",
            "full_name": "Self Registered",
            "role": "admin",
        },
    )
    assert response.status_code == 200
    user = db.query(User).filter_by(email="self-register@example.com").one()
    assert user.role.name == "staff"

    short_password = client.post(
        "/users",
        json={
            "email": "weak@example.com",
            "password": "short",
            "full_name": "Weak Password",
        },
    )
    assert short_password.status_code == 422

    admin = db.query(User).filter_by(email="admin@test.com").one()
    assert client.delete(f"/users/{admin.id}").status_code == 400
