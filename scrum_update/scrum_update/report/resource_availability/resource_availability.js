frappe.query_reports["Resource Availability"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_days(frappe.datetime.get_today(), 14),
			reqd: 1,
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
		},
	],
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "next_free_date" && data) {
			const today = frappe.datetime.get_today();
			if (data.next_free_date === today) {
				value = `<span style="color: green; font-weight: bold;">${value} (Available Now)</span>`;
			} else if (data.next_free_date && data.next_free_date < today) {
				value = `<span style="color: green;">${value}</span>`;
			} else if (data.available_hours <= 0) {
				value = `<span style="color: red;">${value}</span>`;
			}
		}
		return value;
	},
};
