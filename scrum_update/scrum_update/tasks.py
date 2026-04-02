import frappe
from frappe.utils import add_days, today


def expire_old_claims():
	"""Delete Scrum Claims older than 7 days to keep the table lean."""
	cutoff = add_days(today(), -7)
	frappe.db.delete("Scrum Claim", {"claim_date": ("<", cutoff)})
	frappe.db.commit()
