"""
InsightFlow seed data generator.

Run from the backend directory with:
    python -m app.utils.seed_data

Creates deterministic, business-consistent showcase data for development,
testing, and product walkthroughs.
"""

import argparse
import calendar
import json
import random
import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

# ---------------------------------------------------------------------------
# Local imports — these work when invoked via `python -m app.utils.seed_data`
# from the backend directory.
# ---------------------------------------------------------------------------
from app.database import SessionLocal, engine
from app.models.user import Role, User
from app.models.customer import Customer
from app.models.product import Product, Supplier
from app.models.order import Order, OrderItem
from app.models.inventory import Inventory, Payment, Shipment
from app.models.audit_log import AuditLog, SalesTarget
from app.services.auth_service import hash_password

# Ensure tables exist before seeding
from app.database import Base
import app.models  # noqa: F401 — registers all models with Base.metadata

Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# Static seed data definitions
# ---------------------------------------------------------------------------

ROLES = [
    {"name": "admin", "permissions": "all"},
    {"name": "manager", "permissions": "read,write,analytics,reports"},
    {"name": "staff", "permissions": "read,write"},
]

USERS = [
    {
        "email": "admin@insightflow.com",
        "full_name": "Olivia Hart",
        "role_name": "admin",
    },
    {
        "email": "manager@insightflow.com",
        "full_name": "Marcus Lee",
        "role_name": "manager",
    },
    {
        "email": "staff1@insightflow.com",
        "full_name": "Aisha Rahman",
        "role_name": "staff",
    },
    {
        "email": "staff2@insightflow.com",
        "full_name": "Daniel Kim",
        "role_name": "staff",
    },
    {
        "email": "analyst@insightflow.com",
        "full_name": "Sofia Chen",
        "role_name": "manager",
    },
]

DEFAULT_PASSWORD = "password123"

SUPPLIERS = [
    {"name": "Vertex Computing", "contact_person": "Nora Patel", "email": "partnerdesk@vertex.example", "phone": "+1-415-555-0101", "address": "180 Market Street, San Francisco, CA"},
    {"name": "Northstar Collaboration", "contact_person": "Ethan Brooks", "email": "channel@northstar.example", "phone": "+1-206-555-0102", "address": "420 Lakeview Avenue, Seattle, WA"},
    {"name": "ErgoWorks Contract", "contact_person": "Maya Wilson", "email": "accounts@ergoworks.example", "phone": "+1-312-555-0103", "address": "75 Fulton Plaza, Chicago, IL"},
    {"name": "SignalGrid Networks", "contact_person": "Lucas Martin", "email": "distribution@signalgrid.example", "phone": "+1-512-555-0104", "address": "900 Innovation Drive, Austin, TX"},
    {"name": "CoreOffice Logistics", "contact_person": "Grace Liu", "email": "fulfillment@coreoffice.example", "phone": "+1-201-555-0105", "address": "88 Commerce Way, Newark, NJ"},
]

CUSTOMERS = [
    {"name": "NorthBridge Retail Group", "company": "NorthBridge Retail Group", "email": "procurement@northbridge.example", "phone": "+1-617-555-1001", "region": "North", "customer_type": "enterprise"},
    {"name": "Meridian Health Network", "company": "Meridian Health Network", "email": "sourcing@meridianhealth.example", "phone": "+1-612-555-1002", "region": "North", "customer_type": "enterprise"},
    {"name": "Lakefront Legal Partners", "company": "Lakefront Legal Partners", "email": "operations@lakefrontlegal.example", "phone": "+1-312-555-1003", "region": "North", "customer_type": "wholesale"},
    {"name": "Boreal Insurance Services", "company": "Boreal Insurance Services", "email": "workplace@borealinsurance.example", "phone": "+1-651-555-1004", "region": "North", "customer_type": "retail"},
    {"name": "Harborview Hospitality", "company": "Harborview Hospitality Group", "email": "purchasing@harborview.example", "phone": "+1-305-555-1101", "region": "South", "customer_type": "enterprise"},
    {"name": "Cypress Education Alliance", "company": "Cypress Education Alliance", "email": "technology@cypressedu.example", "phone": "+1-404-555-1102", "region": "South", "customer_type": "enterprise"},
    {"name": "BluePeak Property Management", "company": "BluePeak Property Management", "email": "facilities@bluepeak.example", "phone": "+1-214-555-1103", "region": "South", "customer_type": "wholesale"},
    {"name": "Sunline Advisory", "company": "Sunline Advisory LLC", "email": "office@sunlineadvisory.example", "phone": "+1-813-555-1104", "region": "South", "customer_type": "retail"},
    {"name": "Apex Financial Services", "company": "Apex Financial Services", "email": "vendor@apexfinancial.example", "phone": "+1-212-555-1201", "region": "East", "customer_type": "enterprise"},
    {"name": "NovaCare Clinics", "company": "NovaCare Clinics", "email": "procurement@novacare.example", "phone": "+1-215-555-1202", "region": "East", "customer_type": "enterprise"},
    {"name": "Elm & Stone Architects", "company": "Elm & Stone Architects", "email": "studioops@elmandstone.example", "phone": "+1-718-555-1203", "region": "East", "customer_type": "wholesale"},
    {"name": "Beacon Media Collective", "company": "Beacon Media Collective", "email": "itops@beaconmedia.example", "phone": "+1-646-555-1204", "region": "East", "customer_type": "retail"},
    {"name": "Atlas Manufacturing", "company": "Atlas Manufacturing Co.", "email": "supplychain@atlasmanufacturing.example", "phone": "+1-503-555-1301", "region": "West", "customer_type": "enterprise"},
    {"name": "Redwood Mobility", "company": "Redwood Mobility Inc.", "email": "workplace@redwoodmobility.example", "phone": "+1-408-555-1302", "region": "West", "customer_type": "enterprise"},
    {"name": "Summit Renewable Energy", "company": "Summit Renewable Energy", "email": "purchasing@summitrenewable.example", "phone": "+1-720-555-1303", "region": "West", "customer_type": "wholesale"},
    {"name": "Pacific Crest Studios", "company": "Pacific Crest Studios", "email": "operations@pacificcrest.example", "phone": "+1-323-555-1304", "region": "West", "customer_type": "retail"},
    {"name": "Ironwood Distribution", "company": "Ironwood Distribution", "email": "buyers@ironwood.example", "phone": "+1-816-555-1401", "region": "Central", "customer_type": "enterprise"},
    {"name": "Prairie State Foods", "company": "Prairie State Foods", "email": "corporateit@prairiestate.example", "phone": "+1-515-555-1402", "region": "Central", "customer_type": "enterprise"},
    {"name": "CedarWorks Engineering", "company": "CedarWorks Engineering", "email": "admin@cedarworks.example", "phone": "+1-314-555-1403", "region": "Central", "customer_type": "wholesale"},
    {"name": "Union Square Accounting", "company": "Union Square Accounting", "email": "office@unionsquare.example", "phone": "+1-402-555-1404", "region": "Central", "customer_type": "retail"},
]

PRODUCTS = [
    {"name": "Vertex ProBook 14", "category": "Computing", "supplier_idx": 0, "unit_price": 1249.0, "cost_price": 910.0, "reorder_level": 12, "stock": 42, "demand_weight": 10},
    {"name": "Vertex Mini Desktop", "category": "Computing", "supplier_idx": 0, "unit_price": 899.0, "cost_price": 650.0, "reorder_level": 10, "stock": 36, "demand_weight": 7},
    {"name": "27-inch 4K USB-C Monitor", "category": "Displays", "supplier_idx": 0, "unit_price": 489.0, "cost_price": 315.0, "reorder_level": 18, "stock": 64, "demand_weight": 12},
    {"name": "Dual Monitor Arm", "category": "Workspace", "supplier_idx": 2, "unit_price": 179.0, "cost_price": 92.0, "reorder_level": 24, "stock": 78, "demand_weight": 8},
    {"name": "USB-C Docking Station", "category": "Accessories", "supplier_idx": 0, "unit_price": 229.0, "cost_price": 138.0, "reorder_level": 25, "stock": 91, "demand_weight": 13},
    {"name": "Noise-Canceling Business Headset", "category": "Collaboration", "supplier_idx": 1, "unit_price": 249.0, "cost_price": 142.0, "reorder_level": 20, "stock": 58, "demand_weight": 9},
    {"name": "4K Conference Room Camera", "category": "Collaboration", "supplier_idx": 1, "unit_price": 699.0, "cost_price": 455.0, "reorder_level": 18, "stock": 11, "demand_weight": 6},
    {"name": "Meeting Room Speakerphone", "category": "Collaboration", "supplier_idx": 1, "unit_price": 429.0, "cost_price": 265.0, "reorder_level": 14, "stock": 33, "demand_weight": 5},
    {"name": "Wi-Fi 6 Managed Access Point", "category": "Networking", "supplier_idx": 3, "unit_price": 389.0, "cost_price": 248.0, "reorder_level": 15, "stock": 9, "demand_weight": 7},
    {"name": "24-Port Managed Network Switch", "category": "Networking", "supplier_idx": 3, "unit_price": 749.0, "cost_price": 520.0, "reorder_level": 8, "stock": 21, "demand_weight": 4},
    {"name": "Ergonomic Task Chair", "category": "Workspace", "supplier_idx": 2, "unit_price": 529.0, "cost_price": 310.0, "reorder_level": 16, "stock": 47, "demand_weight": 8},
    {"name": "Electric Standing Desk", "category": "Workspace", "supplier_idx": 2, "unit_price": 849.0, "cost_price": 505.0, "reorder_level": 10, "stock": 7, "demand_weight": 5},
    {"name": "Wireless Keyboard and Mouse Set", "category": "Accessories", "supplier_idx": 4, "unit_price": 119.0, "cost_price": 61.0, "reorder_level": 35, "stock": 126, "demand_weight": 14},
    {"name": "65W USB-C Power Adapter", "category": "Accessories", "supplier_idx": 4, "unit_price": 69.0, "cost_price": 34.0, "reorder_level": 40, "stock": 148, "demand_weight": 11},
    {"name": "Laptop Privacy Filter 14-inch", "category": "Accessories", "supplier_idx": 4, "unit_price": 59.0, "cost_price": 27.0, "reorder_level": 30, "stock": 84, "demand_weight": 6},
    {"name": "Portable Full-HD Projector", "category": "Displays", "supplier_idx": 1, "unit_price": 779.0, "cost_price": 498.0, "reorder_level": 7, "stock": 19, "demand_weight": 3},
    {"name": "Smart Power Management Strip", "category": "Accessories", "supplier_idx": 4, "unit_price": 89.0, "cost_price": 44.0, "reorder_level": 30, "stock": 97, "demand_weight": 7},
    {"name": "IT Asset Tag Kit (100)", "category": "IT Operations", "supplier_idx": 4, "unit_price": 149.0, "cost_price": 68.0, "reorder_level": 20, "stock": 55, "demand_weight": 4},
]

REGIONS = ["North", "South", "East", "West", "Central"]
SALESPERSONS_BY_REGION = {
    "North": ["Aisha Rahman", "Noah Williams"],
    "South": ["Daniel Kim", "Maya Thompson"],
    "East": ["Sofia Chen", "Ethan Brooks"],
    "West": ["Lucas Martin", "Priya Shah"],
    "Central": ["Marcus Lee", "Grace Liu"],
}
PAYMENT_METHODS = ["credit_card", "bank_transfer", "check", "cash", "net30"]
CARRIERS = ["FedEx Express", "UPS Ground", "USPS Priority", "DHL Express", "Amazon Logistics"]
TARGET_COMPLETION = {"North": 91.0, "South": 84.0, "East": 106.0, "West": 97.0, "Central": 88.0}
MONTHLY_ORDER_COUNTS = [10, 11, 12, 12, 13, 13, 14, 14, 15, 16, 16, 17, 17, 18, 18, 19, 20, 22]


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _month_window(months_ago: int) -> tuple[date, date]:
    """Return the usable date window for a month relative to today."""
    today = date.today()
    month_index = today.year * 12 + today.month - 1 - months_ago
    year, month_zero = divmod(month_index, 12)
    month = month_zero + 1
    start = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end = today if months_ago == 0 else date(year, month, last_day)
    return start, end


def _generate_tracking_number() -> str:
    """Generate a pseudo tracking number."""
    return f"TRK{uuid.uuid4().hex[:12].upper()}"


# ---------------------------------------------------------------------------
# Seed functions
# ---------------------------------------------------------------------------

def seed_roles(db: Session) -> dict:
    """Create roles and return a name -> Role mapping."""
    print("  Creating roles...")
    role_map = {}
    for role_data in ROLES:
        role = Role(**role_data)
        db.add(role)
        role_map[role_data["name"]] = role
    db.flush()
    print(f"    -> {len(role_map)} roles created")
    return role_map


def seed_users(db: Session, role_map: dict) -> List[User]:
    """Create users with hashed passwords."""
    print("  Creating users...")
    users = []
    hashed = hash_password(DEFAULT_PASSWORD)
    for user_data in USERS:
        user = User(
            email=user_data["email"],
            hashed_password=hashed,
            full_name=user_data["full_name"],
            role_id=role_map[user_data["role_name"]].id,
            is_active=True,
        )
        db.add(user)
        users.append(user)
    db.flush()
    print(f"    -> {len(users)} users created (password: {DEFAULT_PASSWORD})")
    return users


def seed_suppliers(db: Session) -> List[Supplier]:
    """Create supplier records."""
    print("  Creating suppliers...")
    suppliers = []
    for s in SUPPLIERS:
        supplier = Supplier(**s)
        db.add(supplier)
        suppliers.append(supplier)
    db.flush()
    print(f"    -> {len(suppliers)} suppliers created")
    return suppliers


def seed_customers(db: Session) -> List[Customer]:
    """Create customer records."""
    print("  Creating customers...")
    customers = []
    for c in CUSTOMERS:
        customer = Customer(
            name=c["name"],
            company=c["company"],
            email=c["email"],
            phone=c["phone"],
            region=c["region"],
            customer_type=c["customer_type"],
            total_spending=0.0,
        )
        db.add(customer)
        customers.append(customer)
    db.flush()
    print(f"    -> {len(customers)} customers created")
    return customers


def seed_products(db: Session, suppliers: List[Supplier]) -> List[Product]:
    """Create products linked to suppliers."""
    print("  Creating products...")
    products = []
    for p in PRODUCTS:
        product = Product(
            name=p["name"],
            category=p["category"],
            supplier_id=suppliers[p["supplier_idx"]].id,
            unit_price=p["unit_price"],
            cost_price=p["cost_price"],
            current_stock=p["stock"],
            reorder_level=p["reorder_level"],
            status="active",
        )
        db.add(product)
        products.append(product)
    db.flush()
    print(f"    -> {len(products)} products created")
    return products


def seed_orders(
    db: Session,
    customers: List[Customer],
    products: List[Product],
) -> List[Order]:
    """Create an 18-month B2B order history with coherent business signals."""
    print("  Creating 18 months of customer orders...")
    orders = []
    today = date.today()
    customer_weights = {"enterprise": 5, "wholesale": 3, "retail": 1}
    product_weights = [p["demand_weight"] for p in PRODUCTS]

    # The list is oldest -> newest so the dashboard shows steady growth rather
    # than a flat wall of random records.
    for months_ago, order_count in enumerate(reversed(MONTHLY_ORDER_COUNTS)):
        start, end = _month_window(months_ago)
        for _ in range(order_count):
            region = random.choices(REGIONS, weights=[20, 17, 24, 22, 17], k=1)[0]
            regional_customers = [c for c in customers if c.region == region]
            customer = random.choices(
                regional_customers,
                weights=[customer_weights[c.customer_type] for c in regional_customers],
                k=1,
            )[0]
            order_date = start + timedelta(days=random.randint(0, (end - start).days))
            days_ago = (today - order_date).days

            if days_ago < 30:
                payment_status = random.choices(["paid", "pending"], weights=[68, 32], k=1)[0]
            elif days_ago < 60:
                payment_status = random.choices(["paid", "overdue"], weights=[90, 10], k=1)[0]
            elif days_ago < 150:
                payment_status = random.choices(["paid", "overdue"], weights=[96, 4], k=1)[0]
            else:
                # Very old open invoices undermine the credibility of an
                # actively managed portfolio; historical balances are closed.
                payment_status = random.choices(["paid", "overdue"], weights=[100, 0], k=1)[0]

            if days_ago > 12:
                shipment_status = random.choices(["delivered", "shipped"], weights=[96, 4], k=1)[0]
            elif days_ago > 4:
                shipment_status = random.choices(["delivered", "shipped", "preparing"], weights=[45, 45, 10], k=1)[0]
            else:
                shipment_status = random.choices(["shipped", "preparing", "pending"], weights=[35, 45, 20], k=1)[0]

            order = Order(
                customer_id=customer.id,
                order_date=order_date,
                payment_status=payment_status,
                shipment_status=shipment_status,
                region=region,
                salesperson=random.choice(SALESPERSONS_BY_REGION[region]),
                total_amount=0.0,
                created_at=datetime.combine(order_date, datetime.min.time()) + timedelta(hours=random.randint(8, 17)),
            )
            db.add(order)
            db.flush()

            item_count = random.randint(2, 5)
            selected_products = []
            while len(selected_products) < item_count:
                candidate = random.choices(products, weights=product_weights, k=1)[0]
                if candidate not in selected_products:
                    selected_products.append(candidate)

            total_amount = 0.0
            quantity_ranges = {
                "enterprise": (8, 28),
                "wholesale": (5, 18),
                "retail": (2, 8),
            }
            qty_low, qty_high = quantity_ranges[customer.customer_type]
            discount = {"enterprise": 0.91, "wholesale": 0.95, "retail": 1.0}[customer.customer_type]

            for product in selected_products:
                quantity = random.randint(qty_low, qty_high)
                unit_price = round(product.unit_price * discount * random.uniform(0.985, 1.015), 2)
                item_total = round(unit_price * quantity, 2)
                total_amount += item_total
                db.add(OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=unit_price,
                    total=item_total,
                ))

            order.total_amount = round(total_amount, 2)
            customer.total_spending = round((customer.total_spending or 0.0) + order.total_amount, 2)
            if customer.last_purchase_date is None or order_date > customer.last_purchase_date.date():
                customer.last_purchase_date = datetime.combine(order_date, datetime.min.time())
            orders.append(order)

    db.flush()
    print(f"    -> {len(orders)} orders created with line items")
    return orders


def seed_inventory(db: Session, products: List[Product]) -> None:
    """Create inventory records for all products."""
    print("  Creating inventory records...")
    count = 0
    for product in products:
        inv = Inventory(
            product_id=product.id,
            warehouse="Main",
            quantity=product.current_stock,
        )
        db.add(inv)
        count += 1
    db.flush()
    print(f"    -> {count} inventory records created")


def seed_sales_targets(db: Session, orders: List[Order]) -> None:
    """Create current-year targets that encode a realistic regional story."""
    print("  Creating sales targets...")
    revenue_by_region = defaultdict(float)
    current_year = date.today().year
    for order in orders:
        if order.order_date.year == current_year:
            revenue_by_region[order.region] += order.total_amount
    for region in REGIONS:
        completion = TARGET_COMPLETION[region]
        target_amount = round(revenue_by_region[region] / (completion / 100), 2)
        db.add(SalesTarget(
            region=region,
            target_amount=target_amount,
            period="annual",
            year=current_year,
        ))
    db.flush()
    print(f"    -> {len(REGIONS)} current-year sales targets created")


def seed_payments(db: Session, orders: List[Order]) -> None:
    """Create payment records for all orders."""
    print("  Creating payment records...")
    count = 0

    for order in orders:
        method = random.choice(PAYMENT_METHODS)
        due_date = order.order_date + timedelta(days=30)

        if order.payment_status == "paid":
            status = "paid"
            paid_date = order.order_date + timedelta(days=random.randint(1, 25))
        elif order.payment_status == "overdue":
            status = "overdue"
            paid_date = None
        else:
            status = "pending"
            paid_date = None

        payment = Payment(
            order_id=order.id,
            amount=order.total_amount,
            method=method,
            status=status,
            due_date=due_date,
            paid_date=paid_date,
        )
        db.add(payment)
        count += 1

    db.flush()
    print(f"    -> {count} payment records created")


def seed_shipments(db: Session, orders: List[Order]) -> None:
    """Create shipment records for orders that have progressed beyond 'preparing'."""
    print("  Creating shipment records...")
    count = 0

    for order in orders:
        if order.shipment_status in ("pending", "preparing"):
            continue

        carrier = random.choice(CARRIERS)
        tracking = _generate_tracking_number()

        if order.shipment_status == "delivered":
            shipped_date = order.order_date + timedelta(days=random.randint(1, 5))
            delivered_date = shipped_date + timedelta(days=random.randint(2, 10))
            status = "delivered"
        elif order.shipment_status == "shipped":
            shipped_date = order.order_date + timedelta(days=random.randint(1, 5))
            delivered_date = None
            status = "in_transit"
        else:
            shipped_date = None
            delivered_date = None
            status = "pending"

        shipment = Shipment(
            order_id=order.id,
            carrier=carrier,
            tracking_number=tracking,
            status=status,
            shipped_date=shipped_date,
            delivered_date=delivered_date,
        )
        db.add(shipment)
        count += 1

    db.flush()
    print(f"    -> {count} shipment records created")


def seed_audit_logs(db: Session, users: List[User], orders: List[Order]) -> None:
    """Create a concise, credible operations trail for the audit workspace."""
    print("  Creating audit trail...")
    actions = [
        ("order.reviewed", "order"),
        ("payment.follow_up", "payment"),
        ("inventory.reorder_flagged", "product"),
        ("customer.profile_updated", "customer"),
        ("report.exported", "analytics"),
    ]
    for index in range(36):
        action, entity_type = actions[index % len(actions)]
        order = orders[-(index + 1)]
        db.add(AuditLog(
            user_id=users[index % len(users)].id,
            action=action,
            entity_type=entity_type,
            entity_id=order.id if entity_type in ("order", "payment") else None,
            details=json.dumps({
                "source": "operations_console",
                "region": order.region,
                "reference": f"ORD-{order.id:05d}",
            }),
            ip_address=f"10.24.8.{20 + (index % 12)}",
            timestamp=datetime.now() - timedelta(hours=index * 7 + 2),
        ))
    db.flush()
    print("    -> 36 audit events created")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_seed(reset: bool = False) -> None:
    """Main seed function — checks for existing data then creates all records."""
    print("=" * 60)
    print("InsightFlow — Seed Data Generator")
    print("=" * 60)

    random.seed(20260722)
    if reset:
        print("Reset requested: rebuilding local InsightFlow tables...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()

    try:
        # ------------------------------------------------------------------
        # Guard: skip if database already has data
        # ------------------------------------------------------------------
        existing_users = db.query(User).count()
        if existing_users > 0:
            print(f"\nDatabase already contains {existing_users} user(s).")
            print("Seeding skipped to avoid duplicate data.")
            print("To re-seed, drop all tables or use an empty database.")
            return

        print("\nSeeding database...")

        # ------------------------------------------------------------------
        # Create data in foreign-key order
        # ------------------------------------------------------------------
        role_map = seed_roles(db)
        users = seed_users(db, role_map)
        suppliers = seed_suppliers(db)
        customers = seed_customers(db)
        products = seed_products(db, suppliers)
        orders = seed_orders(db, customers, products)
        seed_inventory(db, products)
        seed_sales_targets(db, orders)
        seed_payments(db, orders)
        seed_shipments(db, orders)
        seed_audit_logs(db, users, orders)

        # ------------------------------------------------------------------
        # Final commit
        # ------------------------------------------------------------------
        db.commit()

        print("\n" + "=" * 60)
        print("Seeding completed successfully!")
        print("=" * 60)
        print(f"  Roles:        {db.query(Role).count()}")
        print(f"  Users:        {db.query(User).count()}")
        print(f"  Suppliers:    {db.query(Supplier).count()}")
        print(f"  Customers:    {db.query(Customer).count()}")
        print(f"  Products:     {db.query(Product).count()}")
        print(f"  Orders:       {db.query(Order).count()}")
        print(f"  Order Items:  {db.query(OrderItem).count()}")
        print(f"  Inventory:    {db.query(Inventory).count()}")
        print(f"  Sales Targets:{db.query(SalesTarget).count()}")
        print(f"  Payments:     {db.query(Payment).count()}")
        print(f"  Shipments:    {db.query(Shipment).count()}")
        print(f"  Audit Events: {db.query(AuditLog).count()}")
        print()
        print("Login credentials (all passwords: password123):")
        print("  admin@insightflow.com    — Admin")
        print("  manager@insightflow.com  — Manager")
        print("  staff1@insightflow.com   — Staff")
        print("  staff2@insightflow.com   — Staff")
        print("  analyst@insightflow.com  — Manager (Analyst)")
        print()

    except Exception as exc:
        db.rollback()
        print(f"\nSeeding failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the InsightFlow database")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="drop and recreate local tables before seeding",
    )
    run_seed(reset=parser.parse_args().reset)
