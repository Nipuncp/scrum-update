import frappe
from frappe.utils import add_days, getdate, today


def get_prev_working_day(date_str):
	"""Return the previous working day (skips Saturday/Sunday back to Friday)."""
	date = getdate(date_str)
	weekday = date.weekday()  # 0=Mon … 6=Sun
	if weekday == 0:  # Monday → Friday
		return add_days(date_str, -3)
	elif weekday in (5, 6):  # Sat/Sun → Friday
		return add_days(date_str, -(weekday - 4))
	return add_days(date_str, -1)


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters or {})
	return columns, data


def get_columns():
	return [
		{
			"fieldname": "employee_name",
			"label": "Employee",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"fieldname": "update_status",
			"label": "Status",
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"fieldname": "today_tasks",
			"label": "Today's Tasks",
			"fieldtype": "Data",
			"width": 360,
		},
		{
			"fieldname": "yesterday_tasks",
			"label": "Yesterday's Tasks",
			"fieldtype": "Data",
			"width": 360,
		},
	]


def get_claims_by_employee(date, project_filter=None):
	"""Return {employee_id: [claim_dict, ...]} for the given date."""
	conditions = {"claim_date": date}
	if project_filter:
		conditions["project"] = project_filter

	claims = frappe.get_all(
		"Scrum Claim",
		filters=conditions,
		fields=["employee", "project", "task_subject", "notes"],
	)

	by_employee = {}
	for c in claims:
		by_employee.setdefault(c.employee, []).append(c)
	return by_employee


def format_tasks(claims):
	"""Aggregate claims into a readable string.

	Groups tasks by project: "ProjectA – task1, task2; ProjectB – task3".
	If a claim has notes, appends them in parentheses after the task subject.
	"""
	if not claims:
		return ""

	# Group by project
	project_tasks: dict[str, list[str]] = {}
	for c in claims:
		project = c.project or "—"
		task_label = c.task_subject or ""
		if c.notes:
			task_label = f"{task_label} ({c.notes})" if task_label else c.notes
		project_tasks.setdefault(project, []).append(task_label)

	parts = []
	for project, tasks in project_tasks.items():
		task_str = ", ".join(t for t in tasks if t)
		parts.append(f"{project} – {task_str}" if task_str else project)
	return "; ".join(parts)


def get_data(filters):
	date = filters.get("claim_date") or today()
	prev_date = get_prev_working_day(date)

	emp_filters = {"status": "Active"}
	if filters.get("department"):
		emp_filters["department"] = filters["department"]
	if filters.get("employee"):
		emp_filters["name"] = filters["employee"]

	employees = frappe.get_all(
		"Employee",
		filters=emp_filters,
		fields=["name", "employee_name"],
		order_by="employee_name asc",
	)

	today_map = get_claims_by_employee(date, filters.get("project"))
	yesterday_map = get_claims_by_employee(prev_date, filters.get("project"))

	rows = []
	for emp in employees:
		today_claims = today_map.get(emp.name, [])
		yesterday_claims = yesterday_map.get(emp.name, [])
		has_update = bool(today_claims)

		rows.append(
			{
				"employee": emp.name,
				"employee_name": emp.employee_name,
				"update_status": "Present" if has_update else "No Update",
				"today_tasks": format_tasks(today_claims),
				"yesterday_tasks": format_tasks(yesterday_claims),
			}
		)

	# Sort: employees without updates float to the top, then alphabetical
	rows.sort(key=lambda r: (r["update_status"] == "Present", r["employee_name"]))
	return rows
