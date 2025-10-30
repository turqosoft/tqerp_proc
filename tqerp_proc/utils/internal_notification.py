import frappe
from frappe.utils import nowdate, getdate

def execute():
    today = getdate(nowdate())
    store_users = get_store_users()

    # Get Purchase Orders that are still open
    po_list = frappe.get_all(
        "Purchase Order",
        filters={
            "docstatus": 1,
            "status": ("not in", ["Completed", "Closed"])
        },
        fields=["name", "supplier", "expected_delivery_date"]
    )

    for po in po_list:

        if not po.expected_delivery_date:
            continue

        #  Check pending quantity
        pending_qty = frappe.db.sql("""
            SELECT SUM(qty - received_qty)
            FROM `tabPurchase Order Item`
            WHERE parent=%s
        """, po.name)[0][0] or 0

        if pending_qty <= 0:
            continue  #  Fully received — no alert

        #  Check if expected delivery is overdue
        if getdate(po.expected_delivery_date) < today:
            message = (
                f"🚨 <b>PO Overdue:</b> {po.name}<br>"
                f"Supplier: <b>{po.supplier}</b><br>"
                f"Pending Qty: <b>{pending_qty}</b><br>"
                f"Expected Delivery: <b>{po.expected_delivery_date}</b>"
            )

            #  Fire internal notification
            notify_users(store_users, message)

            frappe.logger().info(f"Internal Alert Sent for PO: {po.name}")


def get_store_users():
    """Fetch users having Store related roles"""
    return frappe.db.get_all(
        "Has Role",
        filters={"role": ["in", ["Stores User", "Stock User"]]},
        pluck="parent"
    )


def notify_users(users, message):
    """Trigger Internal System Notification"""
    for user in users:
        frappe.publish_realtime(
            event="msgprint",
            message=message,
            user=user
        )
