# -*- coding: utf-8 -*-
# Copyright (c) 2018, Libermatic and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import add_months, cint, getdate, fmt_money
from erpnext.controllers.accounts_controller import AccountsController
from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.accounts.doctype.sales_invoice.sales_invoice \
    import get_bank_cash_account
from mss_customization.utils.queries import get_paid_interests, get_outstanding
from mss_customization.utils.transform import make_period


class LoanPayment(AccountsController):
    def validate(self):
        outstanding = get_outstanding(
            self.loan, posting_date=self.posting_date
        )
        if self.capital_amount > outstanding:
            frappe.throw('Capital amount cannot exceed outstanding amount')

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
            self.loan, posting_date=self.posting_date
        )
        interest = outstanding * gold_loan.interest / 100.0
        self.total_interest = cint(self.interest_months) * interest
        if not self.capital_amount and not self.total_interest:
            return frappe.throw('Cannot transaction with zero amount')
        self.interests = []
        if self.interest_months > 0:
            self.make_interests(gold_loan, interest)
        self.total_amount = self.capital_amount + self.total_interest

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
                'period_label': getdate(day).strftime('%b, %Y'),
                'period_code': make_period(day),
                'interest_amount': interest_amount
            })

    def on_submit(self):
        self.make_gl_entries()
        self.update_loan()

    def on_cancel(self):
        self.make_gl_entries(cancel=1)
        self.update_loan()

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
            gl_entries += map(self.get_gl_dict, [
                {
                    'account': self.payment_account,
                    'debit': self.total_interest,
                    'against': self.customer,
                    'remarks': self.make_remarks('payment'),
                },
                {
                    'account': self.interest_income_account,
                    'credit': self.total_interest,
                    'cost_center': frappe.db.get_value(
                        'MSS Loan Settings',
                        None,
                        'cost_center'
                    ),
                    'against': self.customer,
                    'remarks': self.make_remarks('interest_income'),
                }
            ])
        if self.capital_amount > 0:
            gl_entries += map(self.get_gl_dict, [
                {
                    'account': self.payment_account,
                    'debit': self.capital_amount,
                    'against': self.customer,
                    'remarks': self.make_remarks('payment'),
                },
                {
                    'account': self.loan_account,
                    'credit': self.capital_amount,
                    'against': self.payment_account,
                }
            ])
        make_gl_entries(gl_entries, cancel=cancel, adv_adj=0)

    def update_loan(self):
        """
            Updates foreclosure date and status of the Gold Loan.
            Also works for on cancel because paid_interests contains only items
            with docstatus = 1 and this method is run after the cancel is
            complete
        """
        loan = frappe.get_doc('Gold Loan', self.loan)

        paid_interests = get_paid_interests(self.loan)
        months_to_foreclosure = frappe.get_value(
            'MSS Loan Settings', None, 'months_to_foreclosure'
        )
        loan.foreclosure_date = add_months(
            loan.posting_date,
            cint(months_to_foreclosure) + paid_interests.count
        )

        outstanding = get_outstanding(
            self.loan, posting_date=self.posting_date
        )
        if outstanding == 0:
            loan.status = 'Repaid'
        elif loan.status != 'Open':
            loan.status = 'Open'

        loan.save()

    def make_remarks(self, type):
        if type == 'payment':
            if self.capital_amount > 0:
                return 'Payment received with capital {}'.format(
                    fmt_money(
                        self.capital_amount,
                        precision=0,
                        currency=frappe.defaults.get_user_default('currency')
                    )
                )
            return 'Payment received'
        if type == 'interest_income':
            if self.interest_months == 1:
                return 'Interest for {}'.format(
                    self.interests[0].period_label
                )
            if self.interest_months > 1:
                return 'Interests for {} months ({} - {})'.format(
                    self.interest_months,
                    self.interests[0].period_label,
                    self.interests[-1].period_label,
                )
            return None
        return None
