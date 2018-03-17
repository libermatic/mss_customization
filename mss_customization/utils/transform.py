# -*- coding: utf-8 -*-
# Copyright (c) 2018, Libermatic and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from functools import partial
from dateutil.relativedelta import relativedelta
from frappe.utils import getdate, add_months, add_days
from mss_customization.utils.fp import compose


date_str = compose(str, getdate)
next_month = partial(add_months, months=1)
prev_day = partial(add_days, days=-1)


def make_period(date):
    return '{start_date} - {end_date}'.format(
        start_date=date_str(date),
        end_date=compose(prev_day, next_month, date_str)(date)
    )


def get_bound_dates(period, as_date=False):
    start_date, end_date = period.split(' - ')
    if not as_date:
        return {'start_date': start_date, 'end_date': end_date}
    return {'start_date': getdate(start_date), 'end_date': getdate(end_date)}


def month_diff(d1, d2):
    """Return d1 - d2 in months without the days portion"""
    r = relativedelta(getdate(d1), getdate(d2))
    return r.years * 12 + r.months
