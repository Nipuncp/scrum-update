"""
1. Ensure the scrum_claim_count custom field exists on Task.
2. Backfill Scrum Claim.status for pre-existing records.
3. Backfill Task.scrum_claim_count for pre-existing records.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	# --- 1. Create custom field on Task if missing ---
	create_custom_fields(
		{
			"Task": [
				{
					"fieldname": "scrum_claim_count",
					"label": "Times Claimed",
					"fieldtype": "Int",
					"read_only": 1,
					"insert_after": "status",
					"default": "0",
					"description": "Number of times this task has been claimed in a daily scrum",
				}
			]
		},
		update=True,
	)

	# --- 2. Backfill Scrum Claim.status ---
	claims = frappe.get_all(
		"Scrum Claim",
		filters=[["status", "in", ["", None]]],
		fields=["name", "task"],
	)
	for claim in claims:
		if not claim.task:
			frappe.db.set_value("Scrum Claim", claim.name, "status", "Active", update_modified=False)
			continue
		task_status = frappe.db.get_value("Task", claim.task, "status") or ""
		if task_status == "Completed":
			claim_status = "Completed"
		elif task_status == "Cancelled":
			claim_status = "Cancelled"
		else:
			claim_status = "Active"
		frappe.db.set_value("Scrum Claim", claim.name, "status", claim_status, update_modified=False)

	# --- 3. Backfill Task.scrum_claim_count ---
	task_names = frappe.db.sql_list(
		"SELECT DISTINCT task FROM `tabScrum Claim` WHERE task IS NOT NULL AND task != ''"
	)
	for task_name in task_names:
		count = frappe.db.count("Scrum Claim", {"task": task_name})
		frappe.db.set_value("Task", task_name, "scrum_claim_count", count, update_modified=False)

	frappe.db.commit()
