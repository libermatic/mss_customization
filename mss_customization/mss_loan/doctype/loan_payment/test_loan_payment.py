# -*- coding: utf-8 -*-
# Copyright (c) 2018, Libermatic and Contributors
# See license.txt

from __future__ import unicode_literals

import unittest
import frappe
from frappe.utils import getdate
from mss_customization.mss_loan.doctype.gold_loan.test_gold_loan \
    import make_gold_loan
from mss_customization.utils.queries import get_gle_by

get_loan_payment_gle = get_gle_by('Loan Payment')


class TestLoanPayment(unittest.TestCase):
    loan_name_fixture = None
    fixtures = []

    def setUp(self):
        self.loan_name_fixture = make_gold_loan(posting_date='2017-08-19').name

    def tearDown(self):
        if len(self.fixtures) > 0:
            for fixture in self.fixtures:
                if fixture.docstatus == 1:
                    fixture.cancel()
                frappe.delete_doc_if_exists(
                    'Loan Payment', fixture.name, force=1
                )
        if self.loan_name_fixture:
            loan = frappe.get_doc('Gold Loan', self.loan_name_fixture)
            loan.cancel()
            frappe.delete_doc_if_exists(
                'Gold Loan', self.loan_name_fixture, force=1
            )
            self.loan_fixture = None
        frappe.db.commit()

    def test_total_interest(self):
        payment = make_loan_payment(
            loan=self.loan_name_fixture,
            interest_months=2,
            do_not_submit=True,
        )
        self.fixtures = [payment]
        self.assertEqual(payment.total_interest, 1000.0)

    def test_adds_proper_interest(self):
        first = make_loan_payment(loan=self.loan_name_fixture, capital_amount=0)
        self.fixtures = [first]
        payment = make_loan_payment(
            loan=self.loan_name_fixture,
            posting_date='2017-10-21',
            interest_months=2,
            do_not_submit=True,
        )
        self.fixtures.append(payment)
        self.assertEqual(len(payment.interests), 2)
        for interest in payment.interests:
            self.assertEqual(interest.interest_amount, 500)
            self.assertIn(interest.period_code, [
                '2017-09-19 - 2017-10-18', '2017-10-19 - 2017-11-18'
            ])

    def test_gl_entries(self):
        payment = make_loan_payment(
            loan=self.loan_name_fixture,
            interest_months=2,
            capital_amount=2000,
        )
        self.fixtures = [payment]
        exp_gle = dict((d[0], d) for d in [
            ['Cash - _TC', 3000, 0, '_Test Customer'],
            ['Interests on Loans - _TC', 0, 1000, '_Test Customer'],
            ['Loans on Collateral - _TC', 0, 2000, 'Cash - _TC'],
        ])
        gl_entries = get_loan_payment_gle(payment.name)
        self.assertEqual(len(gl_entries), 3)
        for gle in gl_entries:
            self.assertEquals(exp_gle[gle.account][0], gle.account)
            self.assertEquals(exp_gle[gle.account][1], gle.debit)
            self.assertEquals(exp_gle[gle.account][2], gle.credit)
            self.assertEquals(exp_gle[gle.account][3], gle.against)
            self.assertEquals(self.loan_name_fixture, gle.against_voucher)

    def test_raises_validation_error_when_capital_exceeds_outstanding(self):
        with self.assertRaises(frappe.exceptions.ValidationError):
            make_loan_payment(loan=self.loan_name_fixture, capital_amount=10001)

    def test_extends_foreclosure_date(self):
        first = make_loan_payment(loan=self.loan_name_fixture)
        payment = make_loan_payment(loan=self.loan_name_fixture)
        self.fixtures = [first, payment]
        foreclosure_date = frappe.get_value(
            'Gold Loan', self.loan_name_fixture, 'foreclosure_date'
        )
        self.assertEqual(
            getdate(foreclosure_date), getdate('2018-08-19')
        )

    def test_resets_foreclosure_date_on_cancel(self):
        first = make_loan_payment(loan=self.loan_name_fixture)
        payment = make_loan_payment(loan=self.loan_name_fixture)
        payment.cancel()
        self.fixtures = [first, payment]
        foreclosure_date = frappe.get_value(
            'Gold Loan', self.loan_name_fixture, 'foreclosure_date'
        )
        self.assertEqual(
            getdate(foreclosure_date), getdate('2018-07-19')
        )

    def test_sets_loan_status(self):
        first = make_loan_payment(loan=self.loan_name_fixture)
        payment = make_loan_payment(
            loan=self.loan_name_fixture,
            capital_amount=9000,
        )
        self.fixtures = [first, payment]
        status = frappe.get_value(
            'Gold Loan', self.loan_name_fixture, 'status'
        )
        self.assertEqual(status, 'Repaid')

    def test_sets_loan_status_on_cancel(self):
        first = make_loan_payment(loan=self.loan_name_fixture)
        payment = make_loan_payment(
            loan=self.loan_name_fixture,
            capital_amount=9000,
        )
        payment.cancel()
        self.fixtures = [first, payment]
        status = frappe.get_value(
            'Gold Loan', self.loan_name_fixture, 'status'
        )
        self.assertEqual(status, 'Open')


def make_loan_payment(**kwargs):
    args = frappe._dict(kwargs)
    doc = frappe.new_doc('Loan Payment')
    doc.update({
        'loan': args.loan or '_Test Loan',
        'posting_date': args.posting_date or '2017-09-20',
        'company': args.company or '_Test Company',
        'interest_months':
            args.interest_months if args.interest_months is not None else 1,
        'capital_amount':
            args.capital_amount if args.capital_amount is not None else 1000.0,
    })
    if not args.do_not_insert:
        doc.insert()
        if not args.do_not_submit:
            doc.submit()
    return doc
