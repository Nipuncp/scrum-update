from datetime import date, timedelta

import frappe
from frappe.utils import add_days, getdate, today

WORK_HOURS_PER_DAY = 8


def execute(filters=None):
	columns = get_columns()
	data = build_rows(filters or {})
	return columns, data


def get_columns():
	return [
		{
			"fieldname": "employee",
			"label": "Employee ID",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120,
		},
		{
			"fieldname": "employee_name",
			"label": "Employee Name",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"fieldname": "department",
			"label": "Department",
			"fieldtype": "Link",
			"options": "Department",
			"width": 140,
		},
		{
			"fieldname": "open_task_hours",
			"label": "Assigned Task Hours",
			"fieldtype": "Float",
			"width": 150,
		},
		{
			"fieldname": "logged_hours",
			"label": "Logged Hours (Period)",
			"fieldtype": "Float",
			"width": 150,
		},
		{
			"fieldname": "available_hours",
			"label": "Available Hours",
			"fieldtype": "Float",
			"width": 130,
		},
		{
			"fieldname": "next_free_date",
			"label": "Next Free Day",
			"fieldtype": "Date",
			"width": 130,
		},
	]


def get_active_employees(filters):
	conditions = {"status": "Active"}
	if filters.get("department"):
		conditions["department"] = filters["department"]
	return frappe.get_all(
		"Employee",
		filters=conditions,
		fields=["name", "employee_name", "user_id", "department", "holiday_list"],
	)


def get_logged_hours(employee_name: str, from_date: str, to_date: str) -> float:
	"""Sum submitted timesheet hours for this employee in the date range."""
	result = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(tsd.hours), 0)
		FROM `tabTimesheet Detail` tsd
		JOIN `tabTimesheet` ts ON ts.name = tsd.parent
		WHERE ts.employee = %s
		  AND ts.docstatus = 1
		  AND DATE(tsd.from_time) BETWEEN %s AND %s
		""",
		(employee_name, from_date, to_date),
	)
	return float(result[0][0]) if result else 0.0


def get_open_task_load(user_id: str) -> float:
	"""
	Sum of (expected_time - actual_time) for all open Tasks assigned to this user
	via the ToDo assignment mechanism.
	"""
	assigned_tasks = frappe.db.sql(
		"""
		SELECT t.expected_time, t.actual_time
		FROM `tabTask` t
		JOIN `tabToDo` td ON td.reference_type = 'Task'
			AND td.reference_name = t.name
			AND td.allocated_to = %s
			AND td.status = 'Open'
		WHERE t.status IN ('Open', 'Working', 'Pending Review')
		""",
		(user_id,),
		as_dict=True,
	)
	total = 0.0
	for row in assigned_tasks:
		remaining = (row.expected_time or 0) - (row.actual_time or 0)
		total += max(remaining, 0)
	return total


def get_holiday_dates(holiday_list: str, from_date: str, to_date: str) -> set:
	if not holiday_list:
		return set()
	rows = frappe.get_all(
		"Holiday",
		filters={"parent": holiday_list, "holiday_date": ("between", [from_date, to_date])},
		pluck="holiday_date",
	)
	return {getdate(d) for d in rows}


def is_working_day(d: date, holidays: set) -> bool:
	return d.weekday() < 5 and d not in holidays


def count_working_days(from_date: str, to_date: str, holiday_list: str) -> int:
	start = getdate(from_date)
	end = getdate(to_date)
	look_ahead = add_days(to_date, 0)
	holidays = get_holiday_dates(holiday_list or "", from_date, look_ahead)
	count = 0
	current = start
	while current <= end:
		if is_working_day(current, holidays):
			count += 1
		current += timedelta(days=1)
	return count


def compute_next_free_date(open_task_hours: float, holiday_list: str) -> date | None:
	"""
	Walk forward from today consuming WORK_HOURS_PER_DAY per working day until
	open_task_hours are exhausted. Returns the date when the employee is free.
	"""
	if open_task_hours <= 0:
		return getdate(today())

	look_ahead_end = add_days(today(), 365)
	holidays = get_holiday_dates(holiday_list or "", today(), look_ahead_end)

	remaining = open_task_hours
	current = getdate(today())
	for _ in range(366):
		if is_working_day(current, holidays):
			remaining -= WORK_HOURS_PER_DAY
			if remaining <= 0:
				return current
		current += timedelta(days=1)
	return None


def build_rows(filters):
	employees = get_active_employees(filters)
	from_date = filters.get("from_date") or today()
	to_date = filters.get("to_date") or add_days(today(), 14)

	rows = []
	for emp in employees:
		if not emp.user_id:
			continue

		logged = get_logged_hours(emp.name, from_date, to_date)
		open_load = get_open_task_load(emp.user_id)
		working_days = count_working_days(from_date, to_date, emp.holiday_list or "")
		available = max(0.0, (working_days * WORK_HOURS_PER_DAY) - open_load)
		next_free = compute_next_free_date(open_load, emp.holiday_list or "")

		rows.append(
			{
				"employee": emp.name,
				"employee_name": emp.employee_name,
				"department": emp.department,
				"open_task_hours": open_load,
				"logged_hours": logged,
				"available_hours": available,
				"next_free_date": next_free,
			}
		)

	rows.sort(key=lambda r: r["next_free_date"] or date(9999, 1, 1))
	return rows
