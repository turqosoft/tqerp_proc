import frappe
from frappe.utils import nowdate, add_days, getdate

def execute():
    print("Reminder Scheduler Started")
    frappe.logger().info("Reminder Scheduler Started")

    # ✅ Fetch Default Sender Email
    default_sender = frappe.db.get_value(
        "Email Account",
        {"default_outgoing": 1},
        "email_id"
    )
    print(f" Default Sender Email: {default_sender}")

    if not default_sender:
        print(" No default outgoing Email Account found!")
        frappe.logger().warning(" No default outgoing Email Account found!")
        return

    reminder_days = int(frappe.db.get_single_value("Buying Settings", "reminder_days") or 3)
    today = getdate(nowdate())

    po_list = frappe.get_all(
        "Purchase Order",
        filters={
            "docstatus": 1,
            "status": ("not in", ["Completed", "Closed"])
        },
        fields=["name", "supplier", "schedule_date"]
    )

    for po in po_list:
        if not po.schedule_date:
            continue

        reminder_trigger_date = add_days(getdate(po.schedule_date), -reminder_days)

        if reminder_trigger_date == today:
            supplier_email = frappe.db.get_value("Supplier", po.supplier, "email")

            if not supplier_email:
                frappe.logger().info(f"No email found for supplier {po.supplier}")
                continue

            subject = f"Delivery Reminder – Purchase Order {po.name}"
            message = f"""
                Dear {po.supplier},<br><br>
                This is a kind reminder that delivery is due on 
                <b>{po.schedule_date}</b> for <b>Purchase Order {po.name}</b>.<br><br>
                Kindly arrange dispatch accordingly.<br><br>
                Regards,<br>
                {frappe.defaults.get_global_default("company")}
            """

            try:
                #  Send Email through Queue
                frappe.enqueue(
                    method=frappe.sendmail,
                    queue="default",
                    timeout=300,
                    recipients=[supplier_email],
                    sender=default_sender,
                    subject=subject,
                    message=message,
                    reference_doctype="Purchase Order",
                    reference_name=po.name
                )
                frappe.enqueue("frappe.email.doctype.email_queue.email_queue.flush")

                print(f" Queued Email to be sent → {supplier_email}")
                frappe.logger().info(f"Email Queued for PO: {po.name}")

            except Exception as e:
                print(f" Queue Failed for PO {po.name}: {str(e)}")
                frappe.log_error(
                    title=f"Reminder Email Queue Failed - {po.name}",
                    message=str(e)
                )

    print("✅ Reminder Scheduler Completed")
    frappe.logger().info("Reminder Scheduler Completed")
