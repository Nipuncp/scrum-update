# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## About This App

`scrum_update` is a Frappe v16 app that sits on top of ERPNext. Its purpose is to streamline daily scrum updates by:
- Letting team members claim tasks directly from ERPNext Task records each morning
- Giving the scrum master a dashboard showing task/project/timeline data pulled from ERPNext
- Tracking resource availability based on timesheets and task expected timelines

The bench root is at `/workspace/frappe-bench`. All bench commands must be run from there.

## Common Commands

```bash
# Start development server
cd /workspace/frappe-bench && bench start

# Install the Python package into the bench virtualenv (required once, or after a fresh clone)
cd /workspace/frappe-bench && ./env/bin/pip install -e apps/scrum_update

# Register the app on a site and run migrations
bench --site <site-name> install-app scrum_update
bench --site <site-name> migrate

# Run Python tests
bench --site <site-name> run-tests --app scrum_update
# Run a single test
bench --site <site-name> run-tests --module scrum_update.tests.test_module

# Build JS/CSS assets
bench build --app scrum_update

# Watch assets during development
bench watch

# Clear cache after Python changes
bench --site <site-name> clear-cache

# Run linting manually (ruff)
cd apps/scrum_update && ruff check .
cd apps/scrum_update && ruff format .
```

## Frappe App Architecture

Frappe apps follow a specific structure under `scrum_update/scrum_update/`:

- **`hooks.py`** — App-level configuration: scheduled tasks, document event hooks, JS/CSS includes, permission hooks. This is the primary wiring file.
- **`modules.txt`** — Lists module names (currently just "Scrum Update").
- **DocTypes** — Each DocType lives in `scrum_update/<module_name>/<doctype_name>/` and contains:
  - `<doctype_name>.json` — Schema definition (fields, permissions, links)
  - `<doctype_name>.py` — Controller class (Python business logic, hooks like `validate`, `on_submit`)
  - `<doctype_name>.js` — Client-side logic (form buttons, field behavior)
- **`config/`** — Desktop icons, module configuration.
- **`patches/`** + `patches.txt` — Database migration patches run on `bench migrate`.
- **`templates/`** — Jinja web templates.
- **`public/`** — Static assets (JS, CSS, images).

## App Components

### `Scrum Claim` DocType (`scrum_update/doctype/scrum_claim/`)
One record per employee-per-task-per-day. Autoname: `SC-.YYYY.-.MM.-.DD.-.####`.

**Important:** `fetch_from` fields (employee_name, task_subject, project, etc.) are populated explicitly in `before_insert` rather than relying on Frappe's server-side fetch mechanism. This ensures values are stored in the DB even when records are created via Python.

Task assignment lookup for resource load uses `tabToDo` (not a child table): ERPNext's "Assign To" desk button creates `ToDo` records with `reference_type="Task"` and `allocated_to=<user email>`.

### API (`scrum_update/api.py`)
Three whitelisted endpoints called from the Task form JS:
- `claim_task(task, notes)` — creates today's Scrum Claim
- `unclaim_task(task)` — deletes today's claim
- `get_today_claim_status(task)` — returns `{is_claimed, claim_name}` to toggle button label

### Task Form JS (`public/js/task.js`)
Injected into the ERPNext Task form via `hooks.py` `doctype_js`. On `refresh`, calls `get_today_claim_status` then adds either "Claim" or "Unclaim" button under a "Scrum" button group. Uses `frappe.prompt` to collect optional notes.

### Reports (`scrum_update/report/`)
Both are **Script Reports** (Python-generated, not SQL Query Reports):

- **Scrum Daily Report** — `ref_doctype: Scrum Claim`. Filters: date, project, employee. Shows who claimed what for the selected day.
- **Resource Availability** — `ref_doctype: Employee`. Filters: from/to date, department. Computes open task load (via `tabToDo` join), logged hours (submitted timesheets), and `next_free_date` by walking forward consuming 8 hrs/working day. Respects `Employee.holiday_list`.

### Demo Data (`scrum_update/demo/setup_demo.py`)
Seeds 5 employees, 3 projects, 10 tasks, 3 submitted timesheets, 4 scrum claims for today. Idempotent.

```bash
bench --site v16.localhost execute scrum_update.scrum_update.demo.setup_demo.run
```

### Scheduler (`scrum_update/tasks.py`)
`expire_old_claims()` — runs daily, deletes Scrum Claims older than 7 days.

## Key ERPNext Doctypes

- **`Task`** — `project`, `expected_time`, `actual_time`, `status`, `exp_start_date`, `exp_end_date`
- **`ToDo`** — `reference_type="Task"`, `reference_name`, `allocated_to` (user email), `status="Open"` — how task assignment is tracked
- **`Timesheet`** / **`Timesheet Detail`** — `employee`, `docstatus=1` for submitted; hours in `from_time`/`to_time`/`hours`
- **`Employee`** — `user_id` links to User; `holiday_list` for working day calculation

## Frappe Patterns

**Whitelisted API methods** (callable from JS):
```python
@frappe.whitelist()
def my_function(arg1, arg2):
    ...
```
Call from JS: `frappe.call({ method: "scrum_update.scrum_update.api.my_function", args: {...} })`

Wire custom JS into ERPNext forms in `hooks.py`: `doctype_js = {"Task": "public/js/task.js"}`

## Code Style

- Python: tabs for indentation, 110-char line length, ruff-enforced. Target Python 3.10.
- JS: prettier + eslint via pre-commit.
- Enable pre-commit: `cd apps/scrum_update && pre-commit install`
