# -*- coding: utf-8 -*-
# Copyright (c) 2018, Libermatic and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
from frappe.utils import getdate
import unittest
from mss_customization.utils.queries import get_gle_by

get_gold_loan_gle = get_gle_by('Gold Loan')


class TestGoldLoan(unittest.TestCase):
    fixture = None

    def tearDown(self):
        if self.fixture:
            if self.fixture.docstatus == 1:
                self.fixture.cancel()
            frappe.delete_doc_if_exists(
                'Gold Loan', self.fixture.name, force=1
            )
            collateral = frappe.get_all(
                'Loan Collateral', filters={'loan': self.fixture.name}
            )
            for item in collateral:
                frappe.delete_doc_if_exists(
                    'Loan Collateral', item.name, force=1
                )
            self.fixture = None

    def test_foreclosure_date(self):
        loan = make_gold_loan()
        self.fixture = loan
        self.assertEqual(
            getdate(loan.foreclosure_date), getdate('2018-10-12')
        )

    def test_gl_entries(self):
        loan = make_gold_loan()
        self.fixture = loan
        exp_gle = dict((d[0], d) for d in [
            ['Loans on Collateral - _TC', 10000, 0, None],
            ['Cash - _TC', 0, 10000, '_Test Customer']
        ])
        gl_entries = get_gold_loan_gle(loan.name)
        self.assertNotEqual(len(gl_entries), 0)
        for gle in gl_entries:
            self.assertEquals(exp_gle[gle.account][0], gle.account)
            self.assertEquals(exp_gle[gle.account][1], gle.debit)
            self.assertEquals(exp_gle[gle.account][2], gle.credit)
            self.assertEquals(exp_gle[gle.account][3], gle.against)
            self.assertEquals(loan.name, gle.against_voucher)

    def test_cancel_on_gl_entries(self):
        loan = make_gold_loan()
        self.fixture = loan
        loan.cancel()
        gl_entries = get_gold_loan_gle(loan.name)
        self.assertEqual(len(gl_entries), 0)

    def test_collaterals(self):
        collaterals = [frappe._dict({
            'type': '_Test Collateral 1',
            'qty': 1,
            'value': 12000.0
        })]
        loan = make_gold_loan(collaterals=collaterals)
        self.fixture = loan
        assets = frappe.get_list(
            'Loan Collateral',
            fields='*',
            filters={'loan': loan.name}
        )
        self.assertEqual(len(assets), 1)
        for idx, asset in enumerate(assets):
            self.assertEquals(
                asset.name,
                loan.collaterals[idx].ref_loan_collateral
            )
            self.assertEquals(asset.type, collaterals[idx].type)
            self.assertEquals(asset.quantity, collaterals[idx].qty)
            self.assertEquals(asset.value, collaterals[idx].value)
            self.assertEquals(asset.status, 'Open')

    def test_cancel_on_collaterals(self):
        loan = make_gold_loan()
        self.fixture = loan
        loan.cancel()
        assets = frappe.get_list(
            'Loan Collateral',
            filters={'loan': loan.name}
        )
        self.assertEquals(len(assets), 0)


def make_gold_loan(**kwargs):
    args = frappe._dict(kwargs)
    doc = frappe.new_doc('Gold Loan')
    doc.update({
        'customer': args.customer or '_Test Customer',
        'posting_date': args.posting_date or '2017-12-12',
        'company': args.company or '_Test Company',
        'principal': args.principal or 10000.0,
        'interest': args.interest or 5.0,
    })
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
