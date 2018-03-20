# Copyright (c) 2013, Libermatic and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from functools import reduce
import frappe
from frappe import _


def data_reducer(a, x):
    if not x:
        return a
    try:
        cum = a[-1][5]
    except IndexError:
        cum = 0
    remarks = x.remarks if not x.voucher_type == 'Journal Entry' \
        else x.remarks.replace('Note: ', '')
    return a + [[
        x.posting_date,
        x.account,
        x.credit,
        x.debit,
        x.amount,
        cum + x.amount,
        remarks,
    ]]


def sum_reducer(key):
    def fn(a, x):
        return a + x.get(key)
    return fn


def execute(filters=None):
    columns = [
        _("Posting Date") + ":Date:90",
        _("Account") + ":Link/Account:160",
        _("Credit") + ":Currency/currency:90",
        _("Debit") + ":Currency/currency:90",
        _("Amount") + ":Currency/currency:90",
        _("Cummulative") + ":Currency/currency:90",
        _("Remarks") + "::300",
    ]

    loan_account = frappe.get_value(
        'Gold Loan', filters.get('loan'), 'loan_account'
    )
    conds = [
        "against_voucher_type = 'Gold Loan'",
        "against_voucher = '{}'".format(filters.get('loan')),
        "account NOT IN ({})".format(', '.join(
            map(lambda x: "'{}'".format(x), [loan_account])
        ))
    ]
    opening = frappe.db.sql(
        """
            SELECT
                SUM(credit) AS credit,
                SUM(debit) AS debit,
                SUM(credit - debit) AS amount
            FROM `tabGL Entry`
            WHERE {conds} AND posting_date < '{from_date}'
        """.format(
            conds=" AND ".join(conds),
            from_date=filters.get('from_date'),
        ),
        as_dict=True,
    )
    entries = frappe.db.sql(
        """
            SELECT
                posting_date,
                account,
                SUM(credit) AS credit,
                SUM(debit) AS debit,
                SUM(credit - debit) AS amount,
                remarks,
                voucher_type
            FROM `tabGL Entry`
            WHERE {conds}
            AND posting_date BETWEEN '{from_date}' AND '{to_date}'
            GROUP BY voucher_type, voucher_no, account, remarks
            ORDER BY posting_date, debit
        """.format(
            conds=" AND ".join(conds),
            from_date=filters.get('from_date'),
            to_date=filters.get('to_date'),
        ),
        as_dict=True,
    )

    opening_credit = opening[0].get('credit') or 0
    opening_debit = opening[0].get('debit') or 0
    total_credit = reduce(sum_reducer('credit'), entries, 0)
    total_debit = reduce(sum_reducer('debit'), entries, 0)

    data = [
        [
            None,
            _("Opening"),
            opening_credit,
            opening_debit,
            opening_credit - opening_debit,
            opening_credit - opening_debit,
            None,
        ],
    ] + reduce(data_reducer, entries, []) + [
        [
            None,
            _("Total"),
            total_credit,
            total_debit,
            total_credit - total_debit,
            None,
            None,
        ],
        [
            None,
            _("Closing"),
            opening_credit + total_credit,
            opening_debit + total_debit,
            opening_credit - opening_debit + total_credit - total_debit,
            None,
            None,
        ],
    ]
    return columns, data
