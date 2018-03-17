# Copyright (c) 2013, Libermatic and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import today
from mss_customization.utils.queries import get_paid_interests, get_outstanding
from mss_customization.utils.transform import month_diff


def make_row(current_date):
    def fn(loan):
        paid_interests = get_paid_interests(loan.name)
        latest = paid_interests.get('latest')
        last_paid_date = latest.get('period_code').split(' - ')[0] \
            if latest else loan.posting_date
        unpaid_months = month_diff(current_date, last_paid_date)
        outstanding = get_outstanding(loan.name)
        interest = outstanding * loan.interest / 100.0
        print(latest)
        return [
            loan.name,
            loan.posting_date,
            loan.customer,
            loan.principal,
            loan.foreclosure_date,
            outstanding,
            interest * unpaid_months,
            interest and unpaid_months,
            latest and latest.get('posting_date'),
            latest and latest.get('period_label'),
        ]
    return fn


def execute(filters=None):
    columns = [
        _("Loan ID") + ":Link/Gold Loan:90",
        _("Loan Date") + ":Date:90",
        _("Customer") + ":Link/Customer:160",
        _("Loan Amount") + ":Currency/currency:90",
        _("Foreclosure Date") + ":Date:90",
        _("Outstanding") + ":Currency/currency:90",
        _("Current Due") + ":Currency/currency:90",
        _("Pending Months") + "::90",
        _("Last Payment Date") + ":Date:90",
        _("Last Paid Period") + "::160",
    ]
    loans = frappe.get_list(
        'Gold Loan',
        fields=[
            'name', 'customer', 'principal', 'foreclosure_date', 'interest',
            'posting_date'
        ],
        filters=filters,
        order_by='posting_date',
    )
    data = map(make_row(today()), loans)
    return columns, data
