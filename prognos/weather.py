# -*- coding: utf-8 -*-

# weather.py
#
# Copyright (c) 2015
# Leodanis Pozo Ramos <lpozo@openmailbox.org>
# Ozkar L. Garcell <ozkar.garcell@gmail.com>
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

"""Module containing the CubanWeather class."""

import itertools
import re
import urllib2
import datetime
from lxml import etree
from collections import OrderedDict
from functools import partial

from .utils import get_current_date
from .utils import convert_temp
from .proxyauthdialog import ProxyAuthDialog
from .msgbox import MsgBox
from .database import PrognosDB
from .daysdialog import DaysDialog
from .forecastdialog import ExtendedForecastDialog


class CubanWeather(object):
    """Cuban Weather class."""

    # Locations tuple for avoiding malformed xml
    locations = (u'Pinar del Río',
                 u'La Habana',
                 u'Varadero',
                 u'Cienfuegos',
                 u'Cayo Coco',
                 u'Camagüey',
                 u'Holguín',
                 u'Santiago de Cuba')

    # OrderedDict to store weather statuses and deal with malformed xml
    weather_statuses = OrderedDict([
        (u'No disponible', u'images/weather-none-available.png'),
        (u'Lluvias Ocasionales', u'images/weather-showers-scattered-day.png'),
        (u'Lluvias dispersas', u'images/weather-showers-scattered-day.png'),
        (u'Lluvias aisladas', u'images/weather-showers-scattered-day.png'),
        (u'Isolated Showers', u'images/weather-showers-scattered-day.png'),
        (u'Lluvias en la Tarde', u'images/weather-showers-scattered-night.png'),
        (u'Chubascos', u'images/weather-showers-day.png'),
        (u'Parcialmente Nublado', u'images/weather-few-clouds.png'),
        (u'Partly Cloudy', u'images/weather-few-clouds.png'),
        (u'Nublado', u'images/weather-many-clouds.png'),
        (u'Soleado', u'images/weather-clear.png'),
        (u'sunny', u'images/weather-clear.png'),
        (u'Tormentas', u'images/weather-storm-day.png'),
        (u'Vientos', u'images/weather-mist.png')])

    def __init__(self, prognos_app):
        """Initialize CubanWeather objects."""
        # Keep a reference to Prognos app
        self.prognos_app = prognos_app

        # Create a Database, a connection and a table
        self.prognos_db = PrognosDB()

        # Initialize variables
        self.xml_forecast_data = OrderedDict()
        self.forecast_data = []
        self.weather_forecast = {}

        # Set default forecast data and store them in DB
        self.set_default_forecast_data()

        # Dialog for proxy authentication
        self.proxy_auth_dialog = ProxyAuthDialog()
        self.proxy_auth_dialog.ok_button.bind(on_release=self._handle_proxy)

        # Dialog to set the number of days for extended forecast
        self.days_dialog = DaysDialog()
        self.days_dialog.ok_button.bind(on_release=self._display_data)

    def _handle_proxy(self, *args):
        """Handle the connection to weather site through a proxy."""
        # Delete the args parameter cause we don't use it
        del args

        # Get authentication info
        user, password = self.proxy_auth_dialog.get_auth_data()

        # Clear user name and password for security
        self.proxy_auth_dialog.user_text.text = u''
        self.proxy_auth_dialog.password_text.text = u''

        # TODO: Fix the problem with scape characters in passwords
        http_proxy_uri = ''.join([u'http://',
                                  user,
                                  u':',
                                  r'%s' % password,
                                  u'@',
                                  self.prognos_app.host,
                                  u':',
                                  self.prognos_app.port])
        proxy_handler = urllib2.ProxyHandler({'http': http_proxy_uri})
        proxy_auth_handler = urllib2.ProxyBasicAuthHandler()

        # Build and install an opener for using it globally
        proxy_opener = urllib2.build_opener(proxy_handler,
                                            proxy_auth_handler)
        urllib2.install_opener(opener=proxy_opener)

        # Connect to weather site through the proxy
        self._connect_to_weather_site()

    def _parse_weather_site_xml(self, xml_content):
        """Parse the content of the weather site to get weather forecast data.

        :param xml_content: Content of weather site xml file.
        """
        tree_root = etree.fromstring(xml_content)

        # Get forecast data
        xml_descriptions = [element.text for element in tree_root.findall(
            'channel/item/description')[1:-1]]

        # Store forecast data in an OrderedDict
        for item, value in itertools.izip(xml_descriptions, self.locations):
            self.xml_forecast_data[value] = re.findall(
                r'<td>\W*?.*?</td>', item)

    def _transform_forecast_data(self):
        """Transform forecast data into a list to be stored in DB."""
        for key, value in self.xml_forecast_data.iteritems():
            # Clean data from xml tags and spaces: ' </td>'
            for i, item in enumerate(value):
                self.xml_forecast_data[key][i] = self.xml_forecast_data[
                    key][i].strip(' </td>')

            # Insert locations
            for i in xrange(0, len(value) + 1, 5):
                self.xml_forecast_data[key].insert(i, key)

            # Fill in empty (u'') items with default values:
            # u'0', u'0', u'0', u'No disponible'
            for i in xrange(len(value)):
                if not self.xml_forecast_data[key][i]:
                    if i not in range(4, len(value), 5):
                        self.xml_forecast_data[key][i] = u'0'
                    else:
                        self.xml_forecast_data[key][i] = (
                            self.weather_statuses.keys()[0])

        # Put values in a list
        data = []
        for value in self.xml_forecast_data.values():
            data += value

        # List of tuples containing forecast data
        online_data = [(data[i],  # Location
                        u'%s' % int(data[i + 1]),  # Day
                        u'%s' % int(get_current_date('month_int')),  # Month
                        u'%s' % int(get_current_date('year')))  # Year
                       for i in xrange(0, len(data), 5)]

        # Get DB current forecast
        current_data = (self.prognos_db.get_current_forecast() if
                        self.prognos_db.current_forecast_in_db() else None)

        # Convert int data to unicode for comparison purposes
        data_to_inset = []
        for i, item in enumerate(current_data):
            current_data[i] = list(current_data[i])
            for j in xrange(len(item)):
                current_data[i][j] = unicode(current_data[i][j])
            data_to_inset.append(tuple(current_data[i][:2] +
                                       current_data[i][4:]))
            current_data[i] = tuple(current_data[i][0:4])

        # Test if DB data for current day is in online data, otherwise
        # insert them
        for c_datum, key, i_datum in itertools.izip(
                current_data,
                self.xml_forecast_data.keys(),
                data_to_inset):

            if c_datum not in online_data:
                for i, item in enumerate(i_datum):
                    self.xml_forecast_data[key].insert(i, item)

        # Fixing the change of month and year issue
        month, year = self._get_months_years()

        # Variable to store forecast data
        self.forecast_data = []

        # Final forecast data ready to be store in prognos_db
        self.forecast_data = [(int(year[j]),  # Year
                               int(month[j]),  # Month
                               int(data[i + 1]),  # Day
                               data[i],  # Location
                               int(data[i + 2]),  # Day temp
                               int(data[i + 3]),  # Night temp
                               unicode(data[i + 4]))  # Weather status
                              for i, j in itertools.izip(
                                  xrange(0, len(data), 5),
                                  xrange(0, len(data)))]

    def _get_months_years(self):
        """"""
        def test_month_year(days_, test='month_int'):
            """Test for month and year.

            :param days_: A list of integers representing a logical sequence of day
            :param test: Take values 'month_int' or 'year'
            """
            current_month = int(get_current_date('month_int'))
            current_test = value_ = int(get_current_date(test))
            result = []

            if test == 'month_int':
                value_ = 1 if current_month == 12 else current_test + 1
            elif test == 'year':
                value_ = current_test + 1 if current_month == 12 else current_test

            for day in days_:
                if day < days_[0]:
                    result.append(value_)
                else:
                    result.append(current_test)

            return result

        days = []
        months = []
        years = []
        for value in self.xml_forecast_data.values():
            for i, datum in enumerate(value):
                if i in range(1, len(value), 5):
                    days.append(datum)
            months += test_month_year(days_=days)
            years += test_month_year(days_=days, test='year')

        return months, years

    def _display_data(self, *args):
        """Manage the data displaying for extended forecast."""
        # Delete the args parameter cause we don't use it
        del args

        # Get data to show from prognos_db
        data = self.prognos_db.get_extended_forecast(
            location_=self.prognos_app.location,
            days=self.days_dialog.days)

        # Create the dialog to display the info for extended forecast
        forecast_dialog = ExtendedForecastDialog()

        # Display the data
        i = 0
        for item in data:
            data_to_show = list(item)

            # Append the corresponding weather image
            data_to_show.append(self.weather_statuses[data_to_show[4]])

            for datum in data_to_show:
                if i > 0 and not (i + 1) % 6:
                    forecast_dialog.data_labels[i].source = datum
                elif (i in range(3, 41, 6) + range(2, 40, 6) and
                        self.prognos_app.temp_unit == u'Fahrenheit ºF'):
                    if data_to_show[4] == self.weather_statuses.keys()[0]:
                        forecast_dialog.data_labels[i].text = (
                            '0' + ' ' + self.prognos_app.temp_unit[-2:])
                    else:
                        forecast_dialog.data_labels[i].text = (
                            unicode(convert_temp(datum))
                            + ' ' + self.prognos_app.temp_unit[-2:])
                elif i in range(3, 41, 6) + range(2, 40, 6):
                    forecast_dialog.data_labels[i].text = (
                        unicode(datum) + ' ' + self.prognos_app.temp_unit[-2:])
                else:
                    forecast_dialog.data_labels[i].text = unicode(datum)
                i += 1

        # Show the dialog
        forecast_dialog.open()

    @staticmethod
    def _get_day(year, month, day):
        try:
            datetime.date(year, month, day)
            return year, month, day
        except ValueError:
            year = year if month + 1 <= 12 else year + 1
            month = month + 1 if month + 1 <= 12 else 1
            return year, month, 1

    def set_default_forecast_data(self):
        """Set default forecast data and store them in db."""
        # Weather forecast default data
        self.weather_forecast = {
            'location': self.prognos_app.location,
            'day': get_current_date(),
            'month_int': get_current_date('month_int'),
            'year': get_current_date('year'),
            'day_temp': 0,
            'night_temp': 0,
            'weather_status': self.weather_statuses.keys()[0]}

        # Store the default forecast data in DB
        if self.prognos_db.db_is_empty or self.prognos_db.db_is_obsolete:
            # Store default data if no connection and no data is available
            self.forecast_data = []
            for location in self.locations:
                day = int(get_current_date())
                month = int(get_current_date('month_int'))
                year = int(get_current_date('year'))
                default_days = 0

                while default_days < 5:
                    year, month, day = self._get_day(year, month, day)
                    self.forecast_data.append(
                        (year,  # Year
                         month,  # Month
                         day,  # Day
                         location,  # Location
                         0,  # Day temp
                         0,  # Night temp
                         self.weather_statuses.keys()[0]))  # Weather status

                    day += 1
                    default_days += 1

            self.prognos_db.store_weather_forecast_data(
                forecast_data=self.forecast_data)

    def _connect_to_weather_site(self, *args):
        """Method for fetching the weather forecast data from Met site.

        This method parses the cuban weather site xml to get the weather
        forecast data to update DB.
        """
        # Delete the args parameter cause we don't use it
        del args

        # Weather URL for Cuba
        weather_site_url = u'http://www.met.inf.cu/asp/genesis.asp?TB0=RSSFEED'

        # Variables for storing weather site content as string
        weather_site_content = None

        # Connect to weather site and retrieve the forecast information
        try:
            # Connect only if database is not up to date
            if self.prognos_db.db_is_not_updated:
                # This code is for debugging purposes:
                # with open('data_file.xml', 'r') as weather_site:
                #     weather_site_content = weather_site.read()
                weather_site = urllib2.urlopen(url=weather_site_url)
                weather_site_content = weather_site.read()
                # This code is for debugging purposes:
                with open('data_file.xml', 'w') as xml:
                    xml.write(weather_site_content)
        except urllib2.URLError:
            # Show error message on URLError
            msg_box = MsgBox()
            msg_box.msg_label.text = 'Su conexión no está disponible o ' \
                                     'los datos de conexión son incorrectos. ' \
                                     'Verifíquelos e inténtelo nuevamente.'
            msg_box.title = 'Error de conexión'
            msg_box.open()

        if weather_site_content:
            # Parse the content of the weather site
            self._parse_weather_site_xml(xml_content=weather_site_content)

            # Transform forecast data to be stored in DB
            self._transform_forecast_data()

            # Store weather forecast data in prognos_db
            self.prognos_db.store_weather_forecast_data(
                forecast_data=self.forecast_data)

        # Fetch weather forecast from prognos_db and update the UI
        self.prognos_app.root.update_prognos(
            location_=self.prognos_app.location,
            weather_forecast_=self.weather_forecast)

    def fetch_weather_locally(self, location):
        """Fetch the weather data from prognos_db."""
        # Get the forecast data from DB
        data = self.prognos_db.get_current_forecast(location)

        # Put forecast data in a dict for displaying purposes
        if data:
            (self.weather_forecast['location'],
             self.weather_forecast['day'],
             self.weather_forecast['month_int'],
             self.weather_forecast['year'],
             self.weather_forecast['day_temp'],
             self.weather_forecast['night_temp'],
             self.weather_forecast['weather_status']) = data[0]

    def fetch_weather_online(self, use_proxy, host, port):
        """Manage the beginning of proxy authentication process if needed."""
        if use_proxy:
            if host and port:
                # Updating weather image on cancel
                self.proxy_auth_dialog.cancel_button.bind(on_release=partial(
                    self.prognos_app.root.set_weather_image,
                    self.weather_statuses[self.weather_forecast[
                        'weather_status']]))

                # Open authentication dialog
                self.proxy_auth_dialog.open()
            else:
                # Show error message on URLError
                msg_box = MsgBox()
                msg_box.msg_label.text = 'Sus datos de conexión son ' \
                                         'incorrectos. Verifíquelos e ' \
                                         'inténtelo nuevamente.'
                msg_box.title = 'Error de conexión'
                msg_box.open()
                self.prognos_app.root.set_weather_image(self.weather_statuses[
                    self.weather_forecast['weather_status']])
        else:
            self._connect_to_weather_site()
