"""Regression tests for executive dashboard metric semantics."""

from datetime import date, timedelta

from app.models.customer import Customer
from app.models.inventory import Payment
from app.models.order import Order
from app.services.dashboard_service import get_summary


def test_ar_at_risk_only_counts_explicitly_overdue_payments(db):
    customer = Customer(name="Metric Test Account", region="East")
    db.add(customer)
    db.flush()

    paid_order = Order(
        customer_id=customer.id,
        order_date=date.today() - timedelta(days=90),
        payment_status="paid",
        total_amount=1200,
    )
    overdue_order = Order(
        customer_id=customer.id,
        order_date=date.today() - timedelta(days=60),
        payment_status="overdue",
        total_amount=450,
    )
    db.add_all([paid_order, overdue_order])
    db.flush()
    db.add_all([
        Payment(
            order_id=paid_order.id,
            amount=1200,
            method="bank_transfer",
            status="completed",
            due_date=date.today() - timedelta(days=60),
        ),
        Payment(
            order_id=overdue_order.id,
            amount=450,
            method="net30",
            status="overdue",
            due_date=date.today() - timedelta(days=30),
        ),
    ])
    db.commit()

    summary = get_summary(db)

    assert summary.total_revenue == 1650
    assert summary.overdue_amount == 450
