# -*- coding: utf-8 -*-
# Copyright (c) 2018, Libermatic and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import getdate


def get_gle_by(voucher_type):
    """
        Build a function that returns GL Entries of a particular voucher_type
    """
    def fn(voucher_no):
        return frappe.db.sql("""
            SELECT account, debit, credit, against, against_voucher
            FROM `tabGL Entry`
            WHERE voucher_type='{voucher_type}' AND voucher_no='{voucher_no}'
            ORDER BY account ASC
        """.format(
            voucher_type=voucher_type,
            voucher_no=voucher_no
        ), as_dict=1)
    return fn


def get_paid_interests(loan, posting_date=None):
    """
        Return a list of interests of a Gold Loan
    """
    conds = ["LoanPayment.loan = '{}'".format(loan)]
    if posting_date:
        conds.append("LoanPayment.posting_date <= '{}'".format(
            getdate(posting_date))
        )
    existing = frappe.db.sql("""
        SELECT
            LoanPaymentInterest.period_code as period_code,
            LoanPaymentInterest.period_label as period_label,
            LoanPaymentInterest.interest_amount as interest_amount,
            LoanPayment.posting_date as posting_date
        FROM
            `tabLoan Payment Interest` as LoanPaymentInterest,
            `tabLoan Payment` as LoanPayment
        WHERE LoanPaymentInterest.parent = LoanPayment.name
        AND LoanPayment.docstatus = 1
        AND {conds}
        ORDER BY LoanPaymentInterest.period_code
    """.format(
        conds=" AND ".join(conds),
    ), as_dict=1)
    if len(existing) > 0:
        return frappe._dict({
            'interests': existing,
            'latest': existing[-1],
            'count': len(existing),
        })
    return frappe._dict({'interests': [], 'latest': None, 'count': 0})


def get_outstanding(loan, posting_date=None):
    """
        Return the outstanding principal of a Gold Loan
    """
    conds = ["GoldLoan.name = '{}'".format(loan)]
    if posting_date:
        conds.append("GLEntry.posting_date <= '{}'".format(
            getdate(posting_date))
        )
    outstanding = frappe.db.sql("""
        SELECT SUM(debit - credit)
        FROM
            `tabGL Entry` as GLEntry,
            `tabGold Loan` as GoldLoan
        WHERE GLEntry.against_voucher_type = 'Gold Loan'
        AND GLEntry.account = GoldLoan.loan_account
        AND {}
    """.format(" AND ".join(conds)))
    try:
        return outstanding[0][0] or 0
    except IndexError:
        return 0
