// Copyright (c) 2016, Libermatic and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports['Account Statement'] = {
  filters: [
    {
      fieldname: 'from_date',
      label: __('From Date'),
      fieldtype: 'Date',
      default: frappe.datetime.month_start(),
      reqd: 1,
      width: '60px',
    },
    {
      fieldname: 'to_date',
      label: __('To Date'),
      fieldtype: 'Date',
      default: frappe.datetime.month_end(),
      reqd: 1,
      width: '60px',
    },
    {
      fieldname: 'loan',
      label: __('Gold Loan'),
      fieldtype: 'Link',
      options: 'Gold Loan',
      get_query: function() {
        return { doctype: 'Gold Loan', filters: { docstatus: 1 } };
      },
      reqd: 1,
    },
  ],
};
