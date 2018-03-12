# -*- coding: utf-8 -*-
# Copyright (c) 2018, Libermatic and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import add_months, cint
from erpnext.controllers.accounts_controller import AccountsController
from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.accounts.doctype.sales_invoice.sales_invoice \
    import get_bank_cash_account
from mss_customization.utils.queries import get_paid_interests, get_outstanding
from mss_customization.utils.transform import make_period


class LoanPayment(AccountsController):
    def before_save(self):
        gold_loan = frappe.get_doc('Gold Loan', self.loan)
        if not self.mode_of_payment:
            self.mode_of_payment = gold_loan.mode_of_payment
        if not self.payment_account:
            self.payment_account = get_bank_cash_account(
                self.mode_of_payment, self.company
            ).get('account')
        if not self.loan_account:
            self.loan_account = gold_loan.loan_account
        if not self.interest_income_account:
            self.interest_income_account = gold_loan.interest_income_account
        outstanding = get_outstanding(
            gold_loan.name, posting_date=self.posting_date
        )
        interest = outstanding * gold_loan.interest / 100.0
        self.total_interest = self.interest_months * interest
        if self.interest_months > 0:
            self.make_interests(gold_loan, interest)

    def make_interests(self, loan, interest_amount):
        paid_interests = get_paid_interests(
            self.loan, posting_date=self.posting_date
        )
        interest_days = map(
            lambda x: add_months(loan.posting_date, x),
            range(
                paid_interests.count,
                self.interest_months + paid_interests.count
            )
        )
        for day in interest_days:
            self.append('interests', {
                'period_label': '',
                'period_code': make_period(day),
                'interest_amount': interest_amount
            })

    def on_submit(self):
        self.make_gl_entries()
        self.update_foreclosure_date()

    def on_cancel(self):
        self.make_gl_entries(cancel=1)
        self.update_foreclosure_date()

    def get_gl_dict(self, args):
        gl_dict = frappe._dict({
                'against_voucher_type': 'Gold Loan',
                'against_voucher': self.loan
            })
        gl_dict.update(args)
        return super(LoanPayment, self).get_gl_dict(gl_dict)

    def make_gl_entries(self, cancel=0):
        gl_entries = []
        if self.interest_months > 0:
            gl_entries.append(
                self.get_gl_dict({
                    'account': self.payment_account,
                    'debit': self.total_interest,
                    'against': self.customer,
                })
            )
            gl_entries.append(
                self.get_gl_dict({
                    'account': self.interest_income_account,
                    'credit': self.total_interest,
                    'cost_center': frappe.db.get_value(
                        'MSS Loan Settings',
                        None,
                        'cost_center'
                    ),
                    'against': self.customer,
                })
            )
        make_gl_entries(gl_entries, cancel=cancel, adv_adj=0)

    def update_foreclosure_date(self):
        """
            Updates foreclosure date of the Loan.
            Also works for on cancel because paid_interests contains only items
            with docstatus = 1 and this method is run after the cancel is
            complete
        """
        paid_interests = get_paid_interests(self.loan)
        months_to_foreclosure = frappe.get_value(
            'MSS Loan Settings', None, 'months_to_foreclosure'
        )
        loan = frappe.get_doc('Gold Loan', self.loan)
        loan.foreclosure_date = add_months(
            loan.posting_date,
            cint(months_to_foreclosure) + paid_interests.count
        )
        loan.save()
