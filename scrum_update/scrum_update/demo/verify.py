"""Quick verification of reports. Run via bench execute."""
import frappe


def run():
	from scrum_update.scrum_update.report.scrum_daily_report.scrum_daily_report import execute as daily
	from scrum_update.scrum_update.report.resource_availability.resource_availability import execute as avail

	cols, data = daily({"claim_date": frappe.utils.today()})
	print(f"\nScrum Daily Report — {len(data)} rows for {frappe.utils.today()}")
	for row in data:
		print(f"  {row['employee_name']:20} | {row['task_subject']:40} | {row['project']}")

	cols, data = avail({"from_date": frappe.utils.today(), "to_date": frappe.utils.add_days(frappe.utils.today(), 14)})
	print(f"\nResource Availability — {len(data)} employees")
	for row in data:
		print(f"  {row['employee_name']:20} | open={row['open_task_hours']:5.1f}h | next_free={row['next_free_date']}")
