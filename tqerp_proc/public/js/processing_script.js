frappe.ui.form.on("Material Request", {
    refresh(frm) {
        // Run only if doc is not submitted and amount field exists
        if (!frm.is_new() && frm.doc.docstatus === 0) {
            let amount = frm.doc.amount || 0;

            if (amount > 10000) {
                // Hide Approve button
                frm.page.hide_actions_menu_item("Approve");

                // Automatically run Auto Approve workflow action
                frm.call({
                    method: "frappe.model.workflow.apply_workflow",
                    args: {
                        doc: frm.doc,
                        action: "Autoapprove"
                    },
                    callback: function (r) {
                        frm.reload_doc();
                        frappe.msgprint("Auto Approved as Amount > 10000");
                    }
                });
            }
        }
    }
});
