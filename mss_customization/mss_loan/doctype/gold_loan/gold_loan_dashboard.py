# -*- coding: utf-8 -*-
# Copyright (c) 2018, Libermatic and Contributors
# See license.txt

from __future__ import unicode_literals
from frappe import _


def get_data():
    return {
        'fieldname': 'loan',
        'transactions': [
            {
                'label': _('Transactions'),
                'items': ['Loan Payment'],
            },
        ],
    }
