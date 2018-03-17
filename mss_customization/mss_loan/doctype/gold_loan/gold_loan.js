// Copyright (c) 2018, Libermatic and contributors
// For license information, please see license.txt

frappe.ui.form.on('Gold Loan', {
  refresh: function(frm) {
    if (frm.doc['docstatus'] === 1 && frm.doc['status'] === 'Open') {
      const can_foreclose = moment().isAfter(frm.doc['foreclosure_date']);
      const btn = frm.add_custom_button(__('Forclose'), function() {
        async function forclose() {
          await frappe.call({
            method:
              'mss_customization.mss_loan.doctype.gold_loan.gold_loan.make_foreclosure_jv',
            args: {
              loan_name: frm.doc['name'],
              posting_date: frappe.datetime.nowdate(),
            },
          });
          frm.reload_doc();
        }
        const warning = can_foreclose
          ? ''
          : 'It seems the Foreclosure Date is after the current date. ';
        frappe.confirm(
          `${warning}Are you sure you want to continue?`,
          forclose
        );
      });
      if (can_foreclose) {
        btn.addClass('btn-primary');
      }
    }
    if (frm.doc['docstatus'] === 1 && frm.doc['status'] === 'Foreclosed') {
      const btn = frm.add_custom_button(__('Undo Forclosure'), function() {
        async function unforclose() {
          await frappe.call({
            method:
              'mss_customization.mss_loan.doctype.gold_loan.gold_loan.cancel_foreclosure_jv',
            args: { loan_name: frm.doc['name'] },
          });
          frm.reload_doc();
        }
        frappe.confirm(
          'This will cancel reverse foreclosure Journal Entries. Are you sure?',
          unforclose
        );
      });
    }
  },
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
