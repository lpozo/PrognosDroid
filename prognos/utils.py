# -*- coding: utf-8 -*-

# utils.py
#
# Copyright 2015
# Leodanis Pozo Ramos <lpozo@openmailbox.org>
# Ozkar L. Garcell <ozkar.garcell@gmail.com>
#
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""

"""

import time


def convert_temp(temp_value=0.0, from_temp='Celsius', to_temp='Fahrenheit'):
    """Convert temperature from celsius to fahrenheit and vice versa.

    :param temp_value: temperature value
    :param from_temp: Celsius or Fahrenheit
    :param to_temp: Celsius or Fahrenheit
    """

    if from_temp == 'Fahrenheit' and to_temp == 'Celsius':
        return round((temp_value - 32.0) * 5.0 / 9.0)
    elif from_temp == 'Celsius' and to_temp == 'Fahrenheit':
        return round((temp_value * 9.0 / 5) + 32)
    else:
        return round(temp_value)


def get_today_date(int_format=False):
    """Get current date in (y, m, d) format."""
    if int_format:
        return (int(get_current_date('year')),
                int(get_current_date('month_int')),
                int(get_current_date()))

    return (get_current_date('year'),
            get_current_date('month_int'),
            get_current_date())


def get_current_date(date_element='day'):
    """Getting current time element by element.

    :param date_element: is a string default to 'day' and can take the
    fallowing values: 'day_hour', 'week_day', 'month', 'month_int', 'day',
    'year'.
    """
    current_date = {'day_hour': time.strftime("%H"),
                    'week_day': time.strftime("%A"),
                    'month': time.strftime("%b"),
                    'month_int': time.strftime("%m"),
                    'day': time.strftime("%d"),
                    'year': time.strftime("%Y")}

    try:
        return current_date[date_element]
    except KeyError as error:
        raise ValueError('Wrong parameter: %s' % error)


class _Times:
    """Run while loops a given number of times.

    This class is not design to be used directly.
    Use the times object defined in this module to run while loops.
    e.g:

    from utils import times

    while times(5):
        print('Runs the loop 5 times.')
    """
    def __init__(self):
        self._times = 0
        self._times_count = 1

    def __call__(self, times_):
        self._times = times_
        if self._times_count <= self._times:
            self._times_count += 1
            return True
        else:
            return False

times = _Times()

if __name__ == '__main__':
    # Self test code
    # print(convert_temp(77, 'Fahrenheit', 'Celsius'))
    # print(convert_temp(25, 'Celsius', 'Fahrenheit'))
    # print(convert_temp(25))
    # print(convert_temp(25, 'Fahrenheit', 'Fahrenheit'))
    # print(convert_temp(0))
    # print(convert_temp(40))
    # print(convert_temp(100))
    print(get_current_date('month'))
    # print(get_current_date())
    # print(get_current_date())
    # print(int(get_current_date()) - 1)
    get_current_date()
    print(get_today_date())
