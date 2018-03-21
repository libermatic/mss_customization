# -*- coding: utf-8 -*-
# Copyright (c) 2018, Libermatic and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document


class LoanCollateral(Document):
    pass


def create_loan_collateral(opts):
    doc = frappe.new_doc('Loan Collateral')
    args = frappe._dict(opts)
    doc.update({
        'loan': args.loan,
        'value': args.value or 0,
        'type': args.type,
        'quantity': args.quantity,
        'weight': args.weight,
        'description': args.description,
        'status': 'Blocked',
    })
    doc.insert(ignore_permissions=True)
    return doc


def update_loan_collateral_status(collateral, status):
    doc = frappe.get_doc('Loan Collateral', collateral)
    if doc.status != status:
        doc.update({'status': status})
        doc._save(ignore_permissions=True)
