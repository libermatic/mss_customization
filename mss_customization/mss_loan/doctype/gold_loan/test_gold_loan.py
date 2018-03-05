# -*- coding: utf-8 -*-
# Copyright (c) 2018, Libermatic and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
from frappe.utils import getdate
import unittest


class TestGoldLoan(unittest.TestCase):
    fixture = None

    def tearDown(self):
        if self.fixture:
            collateral = frappe.get_all(
                'Loan Collateral', filters={'loan': self.fixture.name}
            )
            if self.fixture.docstatus == 1:
                self.fixture.cancel()
                for item in collateral:
                    item.cancel()
            frappe.delete_doc_if_exists(
                'Gold Loan', self.fixture.name, force=1
            )
            for item in collateral:
                frappe.delete_doc_if_exists(
                    'Loan Collateral', item.name, force=1
                )
            self.fixture = None

    def test_foreclosure_date(self):
        loan = make_gold_loan()
        self.assertEqual(loan.foreclosure_date, getdate('2018-10-12'))
        self.fixture = loan

    def test_gl_entries(self):
        loan = make_gold_loan()
        exp_gle = dict((d[0], d) for d in [
            ['Loans on Collateral - _TC', 10000, 0, loan.name],
            ['Cash - _TC', 0, 10000, None]
        ])
        gl_entries = get_gold_loan_gle(loan.name)
        self.assertNotEqual(len(gl_entries), 0)
        for gle in gl_entries:
            self.assertEquals(exp_gle[gle.account][0], gle.account)
            self.assertEquals(exp_gle[gle.account][1], gle.debit)
            self.assertEquals(exp_gle[gle.account][2], gle.credit)
            self.assertEquals(exp_gle[gle.account][3], gle.against_voucher)
        self.fixture = loan

    def test_cancel_on_gl_entries(self):
        loan = make_gold_loan()
        gl_entries = get_gold_loan_gle(loan.name)
        loan.cancel()
        self.assertEqual(len(gl_entries), 0)
        self.fixture = loan

    def test_collaterals(self):
        collateral = frappe._dict({
            'type': '_Test Collateral 1',
            'qty': 1,
            'value': 12000.0
        })
        loan = make_gold_loan(collaterals=[collateral])
        assets = frappe.get_list(
            'Loan Collateral',
            filters={'loan': loan.name}
        )
        self.assertEqual(len(assets), 1)
        for asset in assets:
            self.assertEquals(asset.type, collateral.type)
            self.assertEquals(asset.quantity, collateral.qty)
            self.assertEquals(asset.value, collateral.value)
            self.assertEquals(asset.status, 'Open')
            self.assertEquals(asset.docstatus, 1)
        self.fixture = loan

    def test_cancel_on_collaterals(self):
        loan = make_gold_loan()
        assets = frappe.get_list(
            'Loan Collateral',
            filters={'loan': loan.name}
        )
        loan.cancel()
        for asset in assets:
            self.assertEquals(asset.docstatus, 2)
        self.fixture = loan


def get_gold_loan_gle(voucher_no):
    return frappe.db.sql("""
        SELECT account, debit, credit, against_voucher
        FROM `tabGL Entry`
        WHERE voucher_type='Gold Loan' AND voucher_no='{}'
        ORDER BY account ASC
    """.format(voucher_no), as_dict=1)


def make_gold_loan(**kwargs):
    args = frappe._dict(kwargs)
    doc = frappe.new_doc('Gold Loan')
    doc.customer = args.customer or '_Test Customer'
    doc.posting_date = args.posting_date or '2017-12-12'
    doc.company = args.company or '_Test Company'
    doc.principal = args.principal or 10000.0
    doc.interest = args.interest or 5.0
    if args.collaterals:
        for item in args.collaterals:
            doc.append('collaterals', item)
    else:
        doc.append('collaterals', {
            'type': '_Test Collateral Asset',
            'qty': 2,
            'value': 15000.0,
        })
    if not args.do_not_insert:
        doc.insert()
        if not args.do_not_submit:
            doc.submit()
    return doc
