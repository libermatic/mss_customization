# Copyright (c) 2013, Libermatic and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _


def execute(filters=None):
    columns = [
        _("Loan ID") + ":Link/Gold Loan:160",
        _("Customer") + ":Link/Customer:160",
        _("Loan Amount") + ":Currency/currency:90",
        _("Outstanding") + ":Currency/currency:90",
        _("Current Due") + ":Currency/currency:90",
        _("Foreclosure Date") + ":Date:90",
        _("Last Payment Date") + ":Date:90",
        _("Last Paid Period") + "::120",
    ]
    data = []
    return columns, data
