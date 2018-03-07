# -*- coding: utf-8 -*-
# Copyright (c) 2018, Libermatic and Contributors
# See license.txt

from __future__ import unicode_literals

import frappe
import unittest
from mss_customization.mss_loan.doctype.gold_loan.test_gold_loan \
    import make_gold_loan
from mss_customization.utils.queries import get_gle_by

get_loan_payment_gle = get_gle_by('Loan Payment')


class TestLoanPayment(unittest.TestCase):
    loan_fixture = None
    fixture = None

    def setUp(self):
        self.loan_fixture = make_gold_loan(posting_date='2017-08-19')

    def tearDown(self):
        if self.fixture:
            if self.fixture.docstatus == 1:
                self.fixture.cancel()
            frappe.delete_doc_if_exists(
                'Loan Payment', self.fixture.name, force=1
            )
            self.fixture = None
        if self.loan_fixture:
            self.loan_fixture.cancel()
            frappe.delete_doc_if_exists(
                'Gold Loan', self.loan_fixture.name, force=1
            )
            self.loan_fixture = None

    def test_gl_entries(self):
        payment = make_loan_payment(loan=self.loan_fixture.name)
        self.fixture = payment
        exp_gle = dict((d[0], d) for d in [
            ['Cash - _TC', 1000, 0, '_Test Customer'],
            ['Interests on Loans - _TC', 0, 500, '_Test Customer'],
            ['Loans on Collateral - _TC', 0, 500, 'Cash - _TC'],
        ])
        gl_entries = get_loan_payment_gle(payment.name)
        self.assertNotEqual(len(gl_entries), 0)
        for gle in gl_entries:
            self.assertEquals(exp_gle[gle.account][0], gle.account)
            self.assertEquals(exp_gle[gle.account][1], gle.debit)
            self.assertEquals(exp_gle[gle.account][2], gle.credit)
            self.assertEquals(exp_gle[gle.account][3], gle.against)
            self.assertEquals(exp_gle[gle.account][4], self.loan_fixture.name)


def make_loan_payment(**kwargs):
    args = frappe._dict(kwargs)
    doc = frappe.new_doc('Loan Payment')
    doc.update({
        'loan': args.loan or '_Test Loan',
        'posting_date': args.posting_date or '2017-09-20',
        'company': args.company or '_Test Company',
        'paid_amount': 1000.0,
    })
    if args.interests:
        for item in args.interests:
            doc.append('interests', item)
    else:
        doc.append('interests', {
            'period_label': 'Aug, 2017',
            'period_code': '2017-08-19 - 2017-09-18',
            'interest_amount': 500.0,
        })
    if not args.do_not_insert:
        doc.insert()
        if not args.do_not_submit:
            doc.submit()
    return doc
