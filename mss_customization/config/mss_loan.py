# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _


def get_data():
    return [
        {
            'label': _("Documents"),
            'items': [
                {
                    'type': 'doctype',
                    'name': 'Gold Loan',
                    'description': _("Gold loans")
                },
                {
                    'type': 'doctype',
                    'name': 'Loan Payment',
                    'description': _("Payments receipt from Customer")
                },
            ],
        },
        {
            'label': _("Setup"),
            'items': [
                {
                    'type': 'doctype',
                    'name': 'MSS Loan Settings',
                    'description': _("MSS Loan Settings")
                },
            ],
        },
    ]
