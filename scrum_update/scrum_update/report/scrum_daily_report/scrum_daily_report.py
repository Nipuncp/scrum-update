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
			"width": 160,
		},
		{
			"fieldname": "update_status",
			"label": "Status",
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"fieldname": "task",
			"label": "Task",
			"fieldtype": "Link",
			"options": "Task",
			"width": 140,
		},
		{
			"fieldname": "task_subject",
			"label": "Task Subject",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"fieldname": "project",
			"label": "Project",
			"fieldtype": "Link",
			"options": "Project",
			"width": 150,
		},
		{
			"fieldname": "task_status",
			"label": "Task Status",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"fieldname": "expected_time",
			"label": "Expected Hrs",
			"fieldtype": "Float",
			"width": 110,
		},
		{
			"fieldname": "exp_end_date",
			"label": "Due Date",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"fieldname": "notes",
			"label": "Scrum Notes",
			"fieldtype": "Small Text",
			"width": 220,
		},
		{
			"fieldname": "yesterday_tasks",
			"label": "Yesterday's Tasks",
			"fieldtype": "Data",
			"width": 300,
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
	"""Aggregate claims into "ProjectA – task1, task2; ProjectB – task3"."""
	if not claims:
		return ""

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

	# Today's claims with full task detail
	today_conditions = {"claim_date": date}
	if filters.get("project"):
		today_conditions["project"] = filters["project"]
	if filters.get("employee"):
		today_conditions["employee"] = filters["employee"]

	today_claims = frappe.get_all(
		"Scrum Claim",
		filters=today_conditions,
		fields=[
			"employee",
			"employee_name",
			"task",
			"task_subject",
			"project",
			"task_status",
			"expected_time",
			"exp_end_date",
			"notes",
		],
		order_by="employee_name asc, project asc",
	)

	# Yesterday's claims aggregated per employee (for the summary column)
	yesterday_map = get_claims_by_employee(prev_date, filters.get("project"))

	# Build a set of employee IDs that have today's claims
	employees_with_update = {c.employee for c in today_claims}

	rows = []

	# Rows for employees WITH today's claims — one row per claim
	for c in today_claims:
		rows.append(
			{
				"employee": c.employee,
				"employee_name": c.employee_name,
				"update_status": "Present",
				"task": c.task,
				"task_subject": c.task_subject,
				"project": c.project,
				"task_status": c.task_status,
				"expected_time": c.expected_time,
				"exp_end_date": c.exp_end_date,
				"notes": c.notes,
				"yesterday_tasks": format_tasks(yesterday_map.get(c.employee, [])),
			}
		)

	# Sentinel rows for employees WITHOUT today's claims
	for emp in employees:
		if emp.name in employees_with_update:
			continue
		rows.append(
			{
				"employee": emp.name,
				"employee_name": emp.employee_name,
				"update_status": "No Update",
				"task": None,
				"task_subject": None,
				"project": None,
				"task_status": None,
				"expected_time": None,
				"exp_end_date": None,
				"notes": None,
				"yesterday_tasks": format_tasks(yesterday_map.get(emp.name, [])),
			}
		)

	# Sort: No Update rows first, then by employee name
	rows.sort(key=lambda r: (r["update_status"] == "Present", r["employee_name"]))
	return rows
