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
