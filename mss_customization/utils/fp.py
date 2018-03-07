# -*- coding: utf-8 -*-
# Copyright (c) 2018, Libermatic and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from functools import reduce


def compose(*funcs):
    return reduce(lambda f, g: lambda x: f(g(x)), funcs, lambda x: x)
