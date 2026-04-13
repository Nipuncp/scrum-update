"""
Ensure the scrum_claim_count custom field exists on Task and backfill counts.
Separated from v1 because the original patch did not call create_custom_fields.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
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

	# Backfill counts for any tasks already claimed
	task_names = frappe.db.sql_list(
		"SELECT DISTINCT task FROM `tabScrum Claim` WHERE task IS NOT NULL AND task != ''"
	)
	for task_name in task_names:
		count = frappe.db.count("Scrum Claim", {"task": task_name})
		frappe.db.set_value("Task", task_name, "scrum_claim_count", count, update_modified=False)

	frappe.db.commit()
