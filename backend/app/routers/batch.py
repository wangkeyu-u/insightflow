"""Batch operations router for bulk delete and export."""

from typing import List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_role
from app.models.user import User
from app.models.order import Order, OrderItem
from app.models.customer import Customer
from app.models.product import Product
from app.models.inventory import Inventory, Payment, Shipment
from app.utils.audit import log_action

router = APIRouter(prefix="/batch", tags=["batch"])


class BatchDeleteRequest(BaseModel):
    ids: List[int]


class BatchDeleteResponse(BaseModel):
    deleted: int
    failed: int
    errors: List[str] = []


@router.post("/orders/delete", response_model=BatchDeleteResponse)
def batch_delete_orders(
    payload: BatchDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager")),
):
    deleted = 0
    failed = 0
    errors = []
    for oid in payload.ids:
        order = db.query(Order).filter(Order.id == oid).first()
        if order:
            customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
            if customer:
                customer.total_spending = max(
                    0.0,
                    (customer.total_spending or 0.0) - (order.total_amount or 0.0),
                )
                customer.last_purchase_date = (
                    db.query(func.max(Order.order_date))
                    .filter(Order.customer_id == customer.id, Order.id != order.id)
                    .scalar()
                )
            db.query(Payment).filter(Payment.order_id == oid).delete(synchronize_session=False)
            db.query(Shipment).filter(Shipment.order_id == oid).delete(synchronize_session=False)
            db.delete(order)
            deleted += 1
        else:
            failed += 1
            errors.append(f"Order #{oid} not found")
    db.commit()
    log_action(db, user_id=current_user.id, action="batch_delete", entity_type="order",
               details=f"Batch deleted {deleted} orders", entity_id=None)
    return BatchDeleteResponse(deleted=deleted, failed=failed, errors=errors)


@router.post("/customers/delete", response_model=BatchDeleteResponse)
def batch_delete_customers(
    payload: BatchDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager")),
):
    deleted = 0
    failed = 0
    errors = []
    for cid in payload.ids:
        customer = db.query(Customer).filter(Customer.id == cid).first()
        if customer:
            order_count = db.query(Order).filter(Order.customer_id == cid).count()
            if order_count:
                customer.customer_type = "archived"
            else:
                db.delete(customer)
            deleted += 1
        else:
            failed += 1
            errors.append(f"Customer #{cid} not found")
    db.commit()
    log_action(db, user_id=current_user.id, action="batch_delete", entity_type="customer",
               details=f"Batch deleted {deleted} customers", entity_id=None)
    return BatchDeleteResponse(deleted=deleted, failed=failed, errors=errors)


@router.post("/products/delete", response_model=BatchDeleteResponse)
def batch_delete_products(
    payload: BatchDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager")),
):
    deleted = 0
    failed = 0
    errors = []
    for pid in payload.ids:
        product = db.query(Product).filter(Product.id == pid).first()
        if product:
            order_item_count = (
                db.query(OrderItem).filter(OrderItem.product_id == pid).count()
            )
            if order_item_count:
                product.status = "archived"
            else:
                db.query(Inventory).filter(Inventory.product_id == pid).delete(
                    synchronize_session=False
                )
                db.delete(product)
            deleted += 1
        else:
            failed += 1
            errors.append(f"Product #{pid} not found")
    db.commit()
    log_action(db, user_id=current_user.id, action="batch_delete", entity_type="product",
               details=f"Batch deleted {deleted} products", entity_id=None)
    return BatchDeleteResponse(deleted=deleted, failed=failed, errors=errors)
