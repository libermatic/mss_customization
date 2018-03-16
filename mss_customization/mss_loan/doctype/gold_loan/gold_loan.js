// Copyright (c) 2018, Libermatic and contributors
// For license information, please see license.txt

frappe.ui.form.on('Gold Loan', {
  refresh: function(frm) {},
  onload: async function(frm) {
    const { message: settings = {} } = await frappe.db.get_value(
      'MSS Loan Settings',
      null,
      ['mode_of_payment', 'loan_account', 'interest_income_account']
    );
    frm.set_value('mode_of_payment', settings['mode_of_payment']);
    frm.set_value('loan_account', settings['loan_account']);
    frm.set_value(
      'interest_income_account',
      settings['interest_income_account']
    );
  },
});
