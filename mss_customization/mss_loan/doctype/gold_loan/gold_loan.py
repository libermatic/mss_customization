# -*- coding: utf-8 -*-
# Copyright (c) 2018, Libermatic and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, add_months
from erpnext.controllers.accounts_controller import AccountsController
from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.accounts.doctype.sales_invoice.sales_invoice \
    import get_bank_cash_account


class GoldLoan(AccountsController):
    def before_save(self):
        settings = frappe.get_single('MSS Loan Settings')
        if not self.mode_of_payment:
            self.mode_of_payment = settings.mode_of_payment
        if not self.loan_account:
            self.loan_account = settings.loan_account
        if not self.interest_income_account:
            self.interest_income_account = settings.interest_income_account

    def before_submit(self):
        months_to_foreclosure = cint(
            frappe.get_value(
                'MSS Loan Settings', None, 'months_to_foreclosure'
            )
        )
        self.foreclosure_date = add_months(
            self.posting_date, months_to_foreclosure
        )

    def on_submit(self):
        self.make_gl_entries()

    def on_cancel(self):
        self.make_gl_entries(cancel=1)

    def make_gl_entries(self, cancel=0):
        payment_account = get_bank_cash_account(
            self.mode_of_payment, self.company
        )
        gl_entries = [
            self.get_gl_dict({
                'account': self.loan_account,
                'debit': self.principal,
            }),
            self.get_gl_dict({
                'account': payment_account.get('account'),
                'credit': self.principal,
                'against': self.customer,
            })
        ]
        make_gl_entries(gl_entries, cancel=cancel, adv_adj=0)
