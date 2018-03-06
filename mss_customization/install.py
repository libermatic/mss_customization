# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe

settings_accounts = {
    'loan_account': {
        'account_name': 'Loans on Collateral',
        'parent_account': 'Loans and Advances (Assets)',
    },
    'interest_income_account': {
        'account_name': 'Interests on Loans',
        'account_type': 'Income Account',
        'parent_account': 'Direct Income',
    },
}


def _create_account(doc, company_name, company_abbr):
    account = frappe.get_doc({
        'doctype': 'Account',
        'account_name': doc['account_name'],
        'parent_account': "{} - {}".format(
            doc['parent_account'], company_abbr
        ),
        'is_group': 0,
        'company': company_name,
        'account_type': doc.get('account_type'),
    }).insert(ignore_if_duplicate=True)
    return account.name


def before_tests():
    frappe.clear_cache()
    settings = frappe.get_single('MSS Loan Settings')
    settings.update({
        'months_to_foreclosure': 10,
        'mode_of_payment': 'Cash',
    })
    for key, value in settings_accounts.items():
        settings.update({
            key: _create_account(value, '_Test Company', '_TC'),
        })
    settings.save()
    frappe.db.commit()
