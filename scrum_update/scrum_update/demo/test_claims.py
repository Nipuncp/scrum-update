"""
Quick smoke-test for claim count and status sync.

Run with:
    bench --site v16.localhost execute scrum_update.scrum_update.demo.test_claims.run
"""

import frappe
from frappe.utils import today, add_days


def run():
	frappe.set_user("Administrator")

	# ── 1. Pick or create a test task ─────────────────────────────────────────
	task_name = frappe.db.get_value("Task", {"status": "Open"}, "name")
	if not task_name:
		task = frappe.get_doc({
			"doctype": "Task",
			"subject": "Test Claim Count Task",
			"status": "Open",
		})
		task.insert(ignore_permissions=True)
		task_name = task.name
		print(f"Created task: {task_name}")
	else:
		print(f"Using existing task: {task_name}")

	# ── 2. Pick a user who has an Employee record ──────────────────────────────
	user_id = frappe.db.get_value("Employee", {}, "user_id")
	if not user_id:
		print("ERROR: No Employee with a linked User found. Run demo setup first.")
		return

	# ── 3. Create 3 claims on different dates ──────────────────────────────────
	dates = [add_days(today(), -2), add_days(today(), -1), today()]
	created = []
	for d in dates:
		existing = frappe.db.exists("Scrum Claim", {
			"task": task_name, "claimed_by": user_id, "claim_date": d
		})
		if existing:
			print(f"  Claim already exists for {d}, skipping")
			created.append(existing)
			continue
		claim = frappe.get_doc({
			"doctype": "Scrum Claim",
			"task": task_name,
			"claimed_by": user_id,
			"claim_date": d,
			"notes": f"Test claim for {d}",
		})
		claim.insert(ignore_permissions=True)
		created.append(claim.name)
		print(f"  Created claim {claim.name} (status={claim.status}) for {d}")

	frappe.db.commit()

	# ── 4. Check claim count on the task ───────────────────────────────────────
	count = frappe.db.get_value("Task", task_name, "scrum_claim_count")
	print(f"\nTask {task_name} → scrum_claim_count = {count}  (expected >= 3)")

	# ── 5. Change task to Completed and check status sync ──────────────────────
	print("\nChanging task status to Completed...")
	task_doc = frappe.get_doc("Task", task_name)
	task_doc.status = "Completed"
	task_doc.save(ignore_permissions=True)
	frappe.db.commit()

	for name in created:
		status = frappe.db.get_value("Scrum Claim", name, "status")
		print(f"  Claim {name} → status = {status}  (expected Completed)")

	# ── 6. Reopen task and verify claims go back to Active ──────────────────────
	print("\nReopening task (status = Open)...")
	task_doc.reload()
	task_doc.status = "Open"
	task_doc.save(ignore_permissions=True)
	frappe.db.commit()

	for name in created:
		status = frappe.db.get_value("Scrum Claim", name, "status")
		print(f"  Claim {name} → status = {status}  (expected Active)")

	print("\nDone.")
