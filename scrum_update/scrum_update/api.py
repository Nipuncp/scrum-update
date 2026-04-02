import frappe
from frappe.utils import today


@frappe.whitelist()
def claim_task(task: str, notes: str = "") -> dict:
	"""
	Creates a Scrum Claim for today for the calling user.
	Returns {"claimed": True, "name": "<doc name>"} or throws.
	"""
	user = frappe.session.user
	claim_date = today()

	existing = frappe.db.get_value(
		"Scrum Claim",
		{"task": task, "claimed_by": user, "claim_date": claim_date},
		"name",
	)
	if existing:
		return {"claimed": False, "name": existing, "message": "Already claimed"}

	doc = frappe.get_doc(
		{
			"doctype": "Scrum Claim",
			"task": task,
			"claimed_by": user,
			"claim_date": claim_date,
			"notes": notes,
		}
	)
	doc.insert(ignore_permissions=False)
	frappe.db.commit()
	return {"claimed": True, "name": doc.name}


@frappe.whitelist()
def unclaim_task(task: str) -> dict:
	"""
	Deletes today's Scrum Claim for the calling user on the given task.
	"""
	user = frappe.session.user
	claim_date = today()
	name = frappe.db.get_value(
		"Scrum Claim",
		{"task": task, "claimed_by": user, "claim_date": claim_date},
		"name",
	)
	if not name:
		return {"unclaimed": False, "message": "No claim found"}
	frappe.delete_doc("Scrum Claim", name, ignore_permissions=False)
	frappe.db.commit()
	return {"unclaimed": True}


@frappe.whitelist()
def get_today_claim_status(task: str) -> dict:
	"""
	Returns whether the current user has claimed this task today.
	Used by the Task form JS to toggle the button label.
	"""
	user = frappe.session.user
	claim_date = today()
	name = frappe.db.get_value(
		"Scrum Claim",
		{"task": task, "claimed_by": user, "claim_date": claim_date},
		"name",
	)
	return {"is_claimed": bool(name), "claim_name": name}
