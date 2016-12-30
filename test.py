#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from utils import get_current_date


def _test_month_year(days, test='month_int'):
    """Test for month and year.

    :param days: A list of integers representing a logical sequence of day
    :param test: Take values 'month_int' or 'year'
    """
    current_month = int(get_current_date('month_int'))
    current_test = value = int(get_current_date(test))
    result = []

    if test == 'month_int':
        value = 1 if current_month == 12 else current_test + 1
    elif test == 'year':
        value = current_test + 1 if current_month == 12 else current_test

    for day in days:
        if day < days[0]:
            result.append(value)
        else:
            result.append(current_test)

    return result


def _get_day(year, month, day):
    try:
        datetime.date(year, month, day)
        return year, month, day
    except ValueError:
        year = year if month + 1 <= 12 else year + 1
        month = month + 1 if month + 1 <= 12 else 1
        return year, month, 1

if __name__ == '__main__':
    print(_get_day(2016, 2, 31))
    print(_get_day(2016, 2, 32))