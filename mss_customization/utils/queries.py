# -*- coding: utf-8 -*-
# Copyright (c) 2018, Libermatic and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe


def get_gle_by(voucher_type):
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
