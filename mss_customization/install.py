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
    'liquidated_collateral_account': {
        'account_name': 'Liquidated Collateral',
        'account_type': 'Stock',
        'parent_account': 'Stock Assets',
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
    if not frappe.db.exists('Company', '_Test Company'):
        return
    settings = frappe.get_single('MSS Loan Settings')
    settings.update({
        'months_to_foreclosure': 10,
        'mode_of_payment': 'Cash',
        'cost_center': 'Main - _TC',
    })
    for key, value in settings_accounts.items():
        settings.update({
            key: _create_account(value, '_Test Company', '_TC'),
        })
    settings.save()
    frappe.db.commit()


def after_install():
    df = frappe.get_meta('Journal Entry Account').get_field('reference_type')
    if '\nGold Loan' not in df.options:
        doc = frappe.new_doc('Property Setter')
        value = df.options + '\nGold Loan'
        doc.update({
                'doc_type': 'Journal Entry Account',
                'doctype_or_field': 'DocField',
                'field_name': 'reference_type',
                'property': 'options',
                'property_type': 'Text',
                'value': value
            })
        doc.insert(ignore_permissions=True)


def after_wizard_complete(args=None):
    """
    Create new accounts and set Loan Settings.
    """
    print(args)
    if frappe.defaults.get_global_default('country') != "India":
        return
    settings = frappe.get_doc('MSS Loan Settings', None)
    settings.update({
            'mode_of_payment': 'Cash',
            'cost_center': frappe.db.get_value(
                'Company', args.get('company_name'), 'cost_center'
            ),
        })
    for key, value in settings_accounts.items():
        account_name = _create_account(
                value,
                args.get('company_name'),
                args.get('company_abbr')
            )
        settings.update({key: account_name})
    settings.save()
