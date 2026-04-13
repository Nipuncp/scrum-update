import frappe
from frappe.model.document import Document
from frappe.utils import today


class ScrumClaim(Document):
	def before_insert(self):
		emp_name, emp_full_name = frappe.db.get_value(
			"Employee", {"user_id": self.claimed_by}, ["name", "employee_name"]
		) or (None, None)
		if not emp_name:
			frappe.throw(
				f"No Employee record found for user {self.claimed_by}. "
				"Please ask HR to link your User to an Employee."
			)
		self.employee = emp_name
		self.employee_name = emp_full_name
		if not self.claim_date:
			self.claim_date = today()

		# Populate fetch_from fields explicitly so they're stored on insert
		task = frappe.db.get_value(
			"Task", self.task, ["subject", "project", "status", "expected_time", "exp_end_date"], as_dict=True
		)
		if task:
			self.task_subject = task.subject
			self.project = task.project
			self.task_status = task.status
			self.expected_time = task.expected_time
			self.exp_end_date = task.exp_end_date
			self.status = _task_status_to_claim_status(task.status)

	def validate(self):
		existing = frappe.db.exists(
			"Scrum Claim",
			{
				"task": self.task,
				"claimed_by": self.claimed_by,
				"claim_date": self.claim_date,
				"name": ("!=", self.name),
			},
		)
		if existing:
			frappe.throw(
				f"You have already claimed task {self.task} for {self.claim_date}."
			)

	def after_insert(self):
		_update_task_claim_count(self.task)

	def on_trash(self):
		_update_task_claim_count(self.task)


def _task_status_to_claim_status(task_status: str) -> str:
	"""Map ERPNext Task status to Scrum Claim status."""
	if task_status == "Completed":
		return "Completed"
	if task_status == "Cancelled":
		return "Cancelled"
	return "Active"


def _update_task_claim_count(task_name: str) -> None:
	"""Recalculate and store the total number of times a task has been claimed."""
	count = frappe.db.count("Scrum Claim", {"task": task_name})
	frappe.db.set_value("Task", task_name, "scrum_claim_count", count, update_modified=False)


def sync_claims_on_task_update(doc, method=None):
	"""Called via doc_events when a Task is saved. Syncs task_status and claim status."""
	new_task_status = doc.status
	new_claim_status = _task_status_to_claim_status(new_task_status)

	claims = frappe.get_all(
		"Scrum Claim",
		filters={"task": doc.name},
		fields=["name", "status", "task_status"],
	)
	for claim in claims:
		updates = {}
		if claim.task_status != new_task_status:
			updates["task_status"] = new_task_status
		if claim.status != new_claim_status:
			updates["status"] = new_claim_status
		if updates:
			frappe.db.set_value("Scrum Claim", claim.name, updates, update_modified=False)
