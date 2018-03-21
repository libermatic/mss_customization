# -*- coding: utf-8 -*-
# Copyright (c) 2018, Libermatic and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest
from mss_customization.mss_loan.doctype.loan_collateral.loan_collateral \
    import create_loan_collateral
from mss_customization.mss_loan.doctype.gold_loan.test_gold_loan \
    import make_gold_loan


class TestLoanCollateral(unittest.TestCase):
    loan_name = None
    fixture = None

    def setUp(self):
        loan = make_gold_loan(
            collaterals=[]
        )
        self.loan_name = loan.name

    def tearDown(self):
        if self.fixture:
            frappe.delete_doc_if_exists(
                'Loan Collateral', self.fixture.name, force=1
            )
            self.fixture = None
        if self.loan_name:
            loan = frappe.get_doc('Gold Loan', self.loan_name)
            loan.cancel()
            frappe.delete_doc_if_exists(
                'Gold Loan', self.loan_name, force=1
            )
            self.loan_name = None

    def test_create_loan_collateral(self):
        params = {
            'loan': self.loan_name,
            'value': 12000.0,
            'type': '_Test Type',
            'quantity': 3,
            'weight': 3.14,
        }
        collateral = create_loan_collateral(params)
        self.assertEquals(collateral.loan, params['loan'])
        self.assertEquals(collateral.value, params['value'])
        self.assertEquals(collateral.type, params['type'])
        self.assertEquals(collateral.quantity, params['quantity'])
        self.assertEquals(collateral.weight, params['weight'])
        self.assertEquals(collateral.status, 'Blocked')
        self.fixture = collateral
