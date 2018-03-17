// Copyright (c) 2018, Libermatic and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports['Loan Summary'] = {
  filters: [
    {
      fieldname: 'customer',
      label: __('Customer'),
      fieldtype: 'Link',
      options: 'Customer',
    },
    {
      fieldname: 'status',
      label: __('Status'),
      fieldtype: 'Select',
      options: '\nOpen\nRepaid\nForeclosed',
    },
  ],
};
