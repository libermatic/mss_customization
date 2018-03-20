// Copyright (c) 2018, Libermatic and contributors
// For license information, please see license.txt

frappe.ui.form.on('Loan Payment', {
  loan: async function(frm) {
    if (frm.doc['loan']) {
      const { message: loan } = await frappe.db.get_value(
        'Gold Loan',
        frm.doc['loan'],
        ['mode_of_payment', 'loan_account', 'interest_income_account']
      );
      frm.set_value('mode_of_payment', loan['mode_of_payment']);
      frm.set_value('loan_account', loan['loan_account']);
      frm.set_value('interest_income_account', loan['interest_income_account']);
    }
  },
  mode_of_payment: async function(frm) {
    if (frm.doc['mode_of_payment']) {
      const { message = {} } = await frappe.call({
        method:
          'erpnext.accounts.doctype.sales_invoice.sales_invoice.get_bank_cash_account',
        args: {
          mode_of_payment: frm.doc['mode_of_payment'],
          company: frm.doc['company'],
        },
      });
      frm.set_value('payment_account', message['account']);
    }
  },
});
