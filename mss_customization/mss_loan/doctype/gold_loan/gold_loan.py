# -*- coding: utf-8 -*-
# Copyright (c) 2018, Libermatic and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from copy import deepcopy
from functools import partial
import frappe
from frappe.utils import cint, add_months
from erpnext.controllers.accounts_controller import AccountsController
from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.accounts.doctype.sales_invoice.sales_invoice \
    import get_bank_cash_account
from mss_customization.utils.fp import compose
from mss_customization.mss_loan.doctype.loan_collateral.loan_collateral \
    import create_loan_collateral


def update(key, value):
    def fn(item):
        new_item = deepcopy(item)
        new_item.update({key: value})
        return new_item
    return fn


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
        make_args = partial(
            map, compose(
                update('loan', self.name),
                lambda x: {
                    'type': x.type,
                    'value': x.value,
                    'description': x.description,
                    'quantity': x.qty,
                }
            )
        )
        collateral_names = compose(
            partial(map, lambda x: x.name),
            partial(map, create_loan_collateral),
            make_args,
        )(self.collaterals)
        for idx, item in enumerate(self.collaterals):
            item.ref_loan_collateral = collateral_names[idx]

    def on_submit(self):
        self.make_gl_entries()

    def on_cancel(self):
        self.make_gl_entries(cancel=1)
        for item in self.collaterals:
            frappe.delete_doc('Loan Collateral', item.ref_loan_collateral)

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
