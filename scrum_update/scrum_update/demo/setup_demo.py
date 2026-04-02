"""
Demo data setup for Scrum Update app.

Run via:
    bench --site <site-name> execute scrum_update.scrum_update.demo.setup_demo.run

Idempotent: skips records that already exist.
"""

from datetime import datetime

import frappe
from frappe.utils import add_days, getdate, now_datetime, today


def get_prev_working_day(date_str):
	date = getdate(date_str)
	weekday = date.weekday()  # 0=Mon … 6=Sun
	if weekday == 0:
		return add_days(date_str, -3)
	elif weekday in (5, 6):
		return add_days(date_str, -(weekday - 4))
	return add_days(date_str, -1)

DEMO_EMPLOYEES = [
	{"email": "alice@demo.scrum", "first_name": "Alice", "last_name": "Demo", "department": "Engineering"},
	{"email": "bob@demo.scrum", "first_name": "Bob", "last_name": "Demo", "department": "Engineering"},
	{"email": "carol@demo.scrum", "first_name": "Carol", "last_name": "Demo", "department": "Quality"},
	{"email": "dave@demo.scrum", "first_name": "Dave", "last_name": "Demo", "department": "Engineering"},
	{"email": "eve@demo.scrum", "first_name": "Eve", "last_name": "Demo", "department": "Design"},
]

DEMO_PROJECTS = [
	{"name": "DEMO-ALPHA", "project_name": "Platform Rewrite"},
	{"name": "DEMO-BETA", "project_name": "Mobile App"},
	{"name": "DEMO-GAMMA", "project_name": "Infrastructure"},
]

DEMO_TASKS = [
	# (subject, project_name, expected_hours, assigned_to_email)
	("Design new auth module", "Platform Rewrite", 8, "alice@demo.scrum"),
	("Write API tests for auth", "Platform Rewrite", 6, "bob@demo.scrum"),
	("Refactor database layer", "Platform Rewrite", 12, "alice@demo.scrum"),
	("Build login screen", "Mobile App", 6, "eve@demo.scrum"),
	("Implement push notifications", "Mobile App", 8, "dave@demo.scrum"),
	("Write mobile E2E tests", "Mobile App", 4, "carol@demo.scrum"),
	("Set up CI/CD pipeline", "Infrastructure", 8, "bob@demo.scrum"),
	("Configure monitoring alerts", "Infrastructure", 4, "dave@demo.scrum"),
	("Migrate prod database", "Infrastructure", 6, "carol@demo.scrum"),
	("Document deployment process", "Infrastructure", 3, "eve@demo.scrum"),
]

# Tasks claimed today (index into DEMO_TASKS)
DEMO_CLAIMS = [0, 3, 6, 8]


def run():
	print("Setting up Scrum Update demo data...")
	company = _ensure_company()
	_ensure_departments(company)
	employees = _create_employees(company)
	_create_projects(company)
	tasks = _create_tasks()
	_create_timesheets(employees, tasks, company)
	_create_scrum_claims(tasks, employees)
	_create_yesterday_scrum_claims(tasks, employees)
	frappe.db.commit()
	yesterday = get_prev_working_day(today())
	print("Demo data seeded successfully.")
	print(f"  - {len(employees)} employees")
	print(f"  - {len(DEMO_PROJECTS)} projects")
	print(f"  - {len(tasks)} tasks")
	print(f"  - Scrum claims for today ({today()}) and yesterday ({yesterday})")
	print("\nOpen 'Scrum Daily Report' and 'Resource Availability' to verify.")


def _ensure_company():
	companies = frappe.get_all("Company", pluck="name", limit=1)
	if companies:
		return companies[0]
	company = frappe.get_doc(
		{
			"doctype": "Company",
			"company_name": "Demo Company",
			"abbr": "DC",
			"default_currency": "USD",
			"country": "United States",
		}
	)
	company.insert(ignore_permissions=True)
	print(f"  Created company: {company.name}")
	return company.name


def _ensure_departments(company):
	for dept_name in ["Engineering", "Quality", "Design"]:
		if not frappe.db.exists("Department", {"department_name": dept_name, "company": company}):
			dept = frappe.get_doc(
				{
					"doctype": "Department",
					"department_name": dept_name,
					"company": company,
				}
			)
			dept.insert(ignore_permissions=True)


def _create_employees(company):
	employees = {}
	for emp_data in DEMO_EMPLOYEES:
		email = emp_data["email"]

		# Create User if missing
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": emp_data["first_name"],
					"last_name": emp_data["last_name"],
					"send_welcome_email": 0,
					"roles": [{"role": "Employee"}, {"role": "Projects User"}],
				}
			)
			user.insert(ignore_permissions=True)
			print(f"  Created user: {email}")

		# Create Employee if missing
		existing = frappe.db.get_value("Employee", {"user_id": email}, "name")
		if existing:
			employees[email] = existing
			continue

		dept_name = emp_data["department"]
		# Find full department name (company-qualified)
		dept = frappe.db.get_value(
			"Department",
			{"department_name": dept_name, "company": company},
			"name",
		)

		employee = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": emp_data["first_name"],
				"last_name": emp_data["last_name"],
				"employee_name": f"{emp_data['first_name']} {emp_data['last_name']}",
				"user_id": email,
				"company": company,
				"department": dept,
				"status": "Active",
				"date_of_joining": today(),
				"date_of_birth": "1990-01-01",
				"gender": "Other",
			}
		)
		employee.insert(ignore_permissions=True)
		employees[email] = employee.name
		print(f"  Created employee: {employee.name} ({email})")

	return employees


def _create_projects(company):
	for proj in DEMO_PROJECTS:
		if frappe.db.exists("Project", {"project_name": proj["project_name"]}):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Project",
				"project_name": proj["project_name"],
				"status": "Open",
				"company": company,
				"expected_start_date": today(),
				"expected_end_date": add_days(today(), 90),
			}
		)
		doc.insert(ignore_permissions=True)
		print(f"  Created project: {doc.name} — {proj['project_name']}")


def _create_tasks():
	tasks = []
	for subject, project_name, expected_hrs, assignee_email in DEMO_TASKS:
		# Find project by project_name
		project = frappe.db.get_value("Project", {"project_name": project_name}, "name")
		if not project:
			print(f"  WARNING: Project '{project_name}' not found, skipping task '{subject}'")
			tasks.append(None)
			continue

		# Skip if task with same subject+project already exists
		existing = frappe.db.get_value("Task", {"subject": subject, "project": project}, "name")
		if existing:
			tasks.append(existing)
			_assign_task_to_user(existing, assignee_email)
			continue

		task = frappe.get_doc(
			{
				"doctype": "Task",
				"subject": subject,
				"project": project,
				"status": "Open",
				"expected_time": expected_hrs,
				"exp_start_date": today(),
				"exp_end_date": add_days(today(), 5),
				"description": f"Demo task: {subject}",
			}
		)
		task.insert(ignore_permissions=True)
		tasks.append(task.name)
		_assign_task_to_user(task.name, assignee_email)
		print(f"  Created task: {task.name} — {subject}")

	return tasks


def _assign_task_to_user(task_name: str, user_email: str):
	"""Assign a task to a user via the ToDo mechanism (same as desk 'Assign To')."""
	if not frappe.db.exists("User", user_email):
		return
	# Skip if ToDo assignment already exists
	existing = frappe.db.exists(
		"ToDo",
		{
			"reference_type": "Task",
			"reference_name": task_name,
			"allocated_to": user_email,
			"status": "Open",
		},
	)
	if existing:
		return
	try:
		from frappe.desk.form.assign_to import add as assign_to_add

		assign_to_add(
			{
				"assign_to": [user_email],
				"doctype": "Task",
				"name": task_name,
				"description": "Assigned by Scrum Update demo script",
			},
			ignore_permissions=True,
		)
	except Exception as e:
		# DuplicateToDoError or similar — safe to ignore
		print(f"  Note: Could not assign {task_name} to {user_email}: {e}")


def _create_timesheets(employees, tasks, company):
	"""Create a few submitted timesheets for realistic resource availability data."""
	timesheet_data = [
		# (employee_email, task_index, hours, days_ago)
		("alice@demo.scrum", 0, 3.0, 1),
		("bob@demo.scrum", 3, 5.0, 2),
		("carol@demo.scrum", 6, 2.0, 1),
	]

	for emp_email, task_idx, hours, days_ago in timesheet_data:
		emp_name = employees.get(emp_email)
		task_name = tasks[task_idx] if task_idx < len(tasks) else None
		if not emp_name or not task_name:
			continue

		work_date = add_days(today(), -days_ago)
		from_time = datetime.strptime(f"{work_date} 09:00:00", "%Y-%m-%d %H:%M:%S")
		to_time = datetime.strptime(
			f"{work_date} {9 + int(hours):02d}:00:00", "%Y-%m-%d %H:%M:%S"
		)

		# Skip if a submitted timesheet for this employee+task+date already exists
		existing = frappe.db.exists(
			"Timesheet",
			{"employee": emp_name, "docstatus": 1},
		)
		if existing:
			continue

		ts = frappe.get_doc(
			{
				"doctype": "Timesheet",
				"employee": emp_name,
				"company": company,
				"time_logs": [
					{
						"activity_type": "Planning",
						"task": task_name,
						"from_time": from_time,
						"to_time": to_time,
						"hours": hours,
						"completed": 0,
					}
				],
			}
		)
		ts.insert(ignore_permissions=True)
		ts.submit()
		print(f"  Created timesheet: {ts.name} ({emp_email}, {hours}h)")


def _create_scrum_claims(tasks, employees):
	"""Create today's scrum claims for a few employees."""
	claim_map = [
		(0, "alice@demo.scrum"),
		(3, "eve@demo.scrum"),
		(6, "bob@demo.scrum"),
		(8, "carol@demo.scrum"),
	]

	for task_idx, emp_email in claim_map:
		task_name = tasks[task_idx] if task_idx < len(tasks) else None
		if not task_name:
			continue

		existing = frappe.db.exists(
			"Scrum Claim",
			{"task": task_name, "claimed_by": emp_email, "claim_date": today()},
		)
		if existing:
			continue

		try:
			claim = frappe.get_doc(
				{
					"doctype": "Scrum Claim",
					"task": task_name,
					"claimed_by": emp_email,
					"claim_date": today(),
					"notes": "Working on this in today's sprint.",
				}
			)
			claim.insert(ignore_permissions=True)
			print(f"  Created scrum claim: {claim.name} ({emp_email})")
		except Exception as e:
			print(f"  Note: Could not create claim for {emp_email} on {task_name}: {e}")


def _create_yesterday_scrum_claims(tasks, employees):
	"""Create previous-working-day claims with different tasks to populate the comparison column."""
	yesterday = get_prev_working_day(today())

	# Different task mix from today so the comparison column is visibly distinct.
	# Dave and Eve swap; Carol has a different task; Alice has two tasks.
	# Dave has no TODAY claim → will appear as "No Update" with yesterday data visible.
	claim_map = [
		(2, "alice@demo.scrum", "Finished the DB layer refactor"),
		(1, "alice@demo.scrum", "Wrote unit tests"),
		(6, "bob@demo.scrum", "CI pipeline green"),
		(5, "carol@demo.scrum", "E2E suite passing"),
		(4, "dave@demo.scrum", "Push notifications wired up"),
		(9, "eve@demo.scrum", "Deployment docs drafted"),
	]

	for task_idx, emp_email, notes in claim_map:
		task_name = tasks[task_idx] if task_idx < len(tasks) else None
		if not task_name:
			continue

		existing = frappe.db.exists(
			"Scrum Claim",
			{"task": task_name, "claimed_by": emp_email, "claim_date": yesterday},
		)
		if existing:
			continue

		try:
			claim = frappe.get_doc(
				{
					"doctype": "Scrum Claim",
					"task": task_name,
					"claimed_by": emp_email,
					"claim_date": yesterday,
					"notes": notes,
				}
			)
			claim.insert(ignore_permissions=True)
			print(f"  Created yesterday's scrum claim: {claim.name} ({emp_email})")
		except Exception as e:
			print(f"  Note: Could not create yesterday's claim for {emp_email} on {task_name}: {e}")
