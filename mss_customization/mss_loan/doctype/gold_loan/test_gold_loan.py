# -*- coding: utf-8 -*-
# Copyright (c) 2018, Libermatic and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
from frappe.utils import getdate
import unittest
from mss_customization.utils.queries import get_gle_by
from mss_customization.mss_loan.doctype.gold_loan.gold_loan \
    import make_foreclosure_jv, cancel_foreclosure_jv

get_gold_loan_gle = get_gle_by('Gold Loan')
get_jv_gle = get_gle_by('Journal Entry')


class TestGoldLoan(unittest.TestCase):
    fixture = None

    def tearDown(self):
        if self.fixture:
            self.fixture.reload()
            if self.fixture.foreclosure_jv:
                jv = frappe.get_doc(
                    'Journal Entry', self.fixture.foreclosure_jv
                )
                if jv.docstatus == 1:
                    jv.cancel()
                frappe.delete_doc_if_exists(
                    'Journal Entry', self.fixture.foreclosure_jv, force=1
                )
            self.fixture.reload()
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
        self.assertEqual(len(gl_entries), 2)
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

    def test_make_foreclosure_jv(self):
        loan = make_gold_loan()
        self.fixture = loan
        jv_name = make_foreclosure_jv(loan.name, posting_date='2018-03-12')
        exp_gle = dict((d[0], d) for d in [
            ['Loans on Collateral - _TC', 0, 10000],
            ['Foreclosed Collateral - _TC', 10000, 0]
        ])
        gl_entries = get_jv_gle(jv_name)
        self.assertEqual(len(gl_entries), 2)
        for gle in gl_entries:
            self.assertEquals(exp_gle[gle.account][0], gle.account)
            self.assertEquals(exp_gle[gle.account][1], gle.debit)
            self.assertEquals(exp_gle[gle.account][2], gle.credit)
            self.assertEquals(loan.name, gle.against_voucher)

    def test_foreclosure_jv(self):
        loan = make_gold_loan()
        self.fixture = loan
        jv_name = make_foreclosure_jv(loan.name, posting_date='2018-03-12')
        foreclosure_jv = frappe.get_value(
            'Gold Loan', loan.name, 'foreclosure_jv'
        )
        self.assertEqual(jv_name, foreclosure_jv)

    def test_cancel_foreclosure_jv(self):
        loan = make_gold_loan()
        self.fixture = loan
        jv_name = make_foreclosure_jv(loan.name, posting_date='2018-03-12')
        cancel_foreclosure_jv(loan.name)
        jv = frappe.get_doc('Journal Entry', jv_name)
        self.assertEqual(jv.docstatus, 2)
        gl_entries = get_jv_gle(jv_name)
        self.assertEqual(len(gl_entries), 0)
        loan_status, foreclosure_jv = frappe.get_value(
            'Gold Loan', loan.name, ['status', 'foreclosure_jv']
        )
        self.assertEqual(loan_status, 'Open')
        self.assertEqual(foreclosure_jv, None)
        frappe.delete_doc_if_exists(
            'Journal Entry', jv_name, force=1
        )

    def test_loan_on_jv_cancel(self):
        loan = make_gold_loan()
        self.fixture = loan
        jv_name = make_foreclosure_jv(loan.name, posting_date='2018-03-12')
        jv = frappe.get_doc('Journal Entry', jv_name)
        jv.cancel()
        loan_status, foreclosure_jv = frappe.get_value(
            'Gold Loan', loan.name, ['status', 'foreclosure_jv']
        )
        self.assertEqual(loan_status, 'Open')
        self.assertEqual(foreclosure_jv, None)
        frappe.delete_doc_if_exists(
            'Journal Entry', jv_name, force=1
        )

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
            self.assertEquals(asset.status, 'Blocked')

    def test_cancel_on_collaterals(self):
        loan = make_gold_loan()
        self.fixture = loan
        loan.cancel()
        assets = frappe.get_list(
            'Loan Collateral',
            filters={'loan': loan.name}
        )
        self.assertEquals(len(assets), 0)

    def test_update_status_on_collaterals(self):
        loan = make_gold_loan()
        loan.status = 'Repaid'
        loan.save()
        self.fixture = loan
        assets = frappe.get_list(
            'Loan Collateral',
            fields=['status'],
            filters={'loan': loan.name}
        )
        for asset in assets:
            self.assertEqual(asset.status, 'Returned')

        loan.status = 'Open'
        loan.save()
        assets = frappe.get_list(
            'Loan Collateral',
            fields=['status'],
            filters={'loan': loan.name}
        )
        for asset in assets:
            self.assertEqual(asset.status, 'Blocked')


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
    if not args.collaterals == None:
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
