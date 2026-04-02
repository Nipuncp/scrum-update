// Copyright (c) 2026, nipuncp123@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Scrum Claim", {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.set_intro(
				__("Claimed on {0} by {1}", [frm.doc.claim_date, frm.doc.employee_name]),
				"blue"
			);
		}
	},
});
