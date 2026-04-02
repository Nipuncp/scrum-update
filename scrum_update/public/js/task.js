frappe.ui.form.on("Task", {
	refresh(frm) {
		if (frm.is_new()) return;

		const non_claimable = ["Completed", "Cancelled", "Template"];
		if (non_claimable.includes(frm.doc.status)) return;

		frappe.call({
			method: "scrum_update.scrum_update.api.get_today_claim_status",
			args: { task: frm.doc.name },
			callback(r) {
				if (!r.message) return;

				if (r.message.is_claimed) {
					frm.add_custom_button(
						__("Unclaim from Today's Scrum"),
						() => {
							frappe.confirm(
								__("Remove your scrum claim for task {0}?", [frm.doc.subject]),
								() => {
									frappe.call({
										method: "scrum_update.scrum_update.api.unclaim_task",
										args: { task: frm.doc.name },
										callback() {
											frappe.show_alert({
												message: __("Task unclaimed from today's scrum"),
												indicator: "orange",
											});
											frm.refresh();
										},
									});
								}
							);
						},
						__("Scrum")
					);
				} else {
					frm.add_custom_button(
						__("Claim for Today's Scrum"),
						() => {
							frappe.prompt(
								{
									fieldname: "notes",
									fieldtype: "Small Text",
									label: __("Update Notes (optional)"),
								},
								(values) => {
									frappe.call({
										method: "scrum_update.scrum_update.api.claim_task",
										args: {
											task: frm.doc.name,
											notes: values.notes || "",
										},
										callback(res) {
											if (res.message && res.message.claimed) {
												frappe.show_alert({
													message: __("Task claimed for today's scrum"),
													indicator: "green",
												});
												frm.refresh();
											}
										},
									});
								},
								__("Claim Task for Today's Scrum"),
								__("Claim")
							);
						},
						__("Scrum")
					);
				}
			},
		});
	},
});
