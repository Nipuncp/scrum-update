frappe.query_reports["Scrum Daily Report"] = {
	filters: [
		{
			fieldname: "claim_date",
			label: __("Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
		},
	],
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "update_status") {
			const color = data && data.update_status === "Present" ? "green" : "red";
			value = `<span class="indicator-pill ${color}">${data && data.update_status}</span>`;
		}
		return value;
	},
};
