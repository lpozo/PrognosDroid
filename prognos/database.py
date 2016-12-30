# -*- coding: utf-8 -*-

# database.py
#
# Copyright 2015
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

"""Module containing the PrognosDB class."""

import sqlite3 as db_api  # So you can change the db manager any time you like
import datetime
from os.path import expanduser
from os.path import join

from kivy import platform

from .utils import get_current_date
from .utils import get_today_date
from .msgbox import MsgBox


class PrognosDB(object):
    """Database for storing forecast data."""

    def __init__(self):
        if platform == 'linux':
            self.database_path = join(expanduser('~'), '.prognos/prognos.db')
        elif platform == 'android':
            self.database_path = '/sdcard/.prognos/prognos.db'

        self.connection = None
        self.cursor_ = None

        try:
            # Create a connection to prognos DB
            self._create_db_connection(db_path=self.database_path)

            # Create the table
            self._create_table()
        except db_api.Error:
            # If an error occur, create a connection to a :memory: DB
            self._create_db_connection(db_path=':memory:')

            # Create the table
            self._create_table()

            # Message to notify that DB could not be created on hdd or sdcard
            msg_box = MsgBox()
            msg_box.msg_label.text = 'No ha sido posible crear la base ' \
                                     'de datos de Prognos en su carpeta' \
                                     'personal, en su lugar se ha creado'\
                                     'una base de datos temporal en la' \
                                     'memoria de su dispositivo.'
            msg_box.open()

    def _create_db_connection(self, db_path):
        """Create a connection to prognos.db.

        :param db_path: Path to the DB
        """
        # Create the connection to prognos.db
        self.connection = db_api.connect(database=db_path)

        # Create a cursor
        self.cursor_ = self.connection.cursor()

    def _create_table(self):
        """Create a table in prognos.db."""
        self.cursor_.executescript("""
            PRAGMA encoding="UTF-8";
            CREATE TABLE IF NOT EXISTS prognos
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INT,
                month INT,
                day INT,
                location TEXT,
                day_temp INT,
                night_temp INT,
                weather_status TEXT,
                date_created DATETIME DEFAULT current_timestamp,
                UNIQUE(year, month, day, location));
            CREATE INDEX IF NOT EXISTS idx_date ON prognos
                (year, month, day);""")

        # Save changes
        self.connection.commit()

    def store_weather_forecast_data(self, forecast_data):
        """Store the forecast data into the database.

        :param forecast_data: Data to store in DB. A list of tuples.
        Every tuple in the list must include information for every field in the
        DB, this is: (year, month, day, location, day_temp, night_temp,
        weather_status) in that order.
        """
        # Delete old information
        self.cursor_.execute(u"DELETE FROM 'main'.'prognos' ")

        # Inset data into the database
        self.cursor_.executemany(u"INSERT INTO"
                                 " prognos("
                                 " year,"
                                 " month,"
                                 " day,"
                                 " location,"
                                 " day_temp,"
                                 " night_temp,"
                                 " weather_status) "
                                 "VALUES(?, ?, ?, ?, ?, ?, ?)",
                                 forecast_data)
        # Save data
        self.connection.commit()

    def get_extended_forecast(self, location_, days):
        """Get extended forecast data.

        :param location_: Current location.
        :param days: Number of days to include in extended forecast.
        """
        # TODO: Take into account the month
        sql_cmd = (u"SELECT"
                   " day,"
                   " location,"
                   " day_temp,"
                   " night_temp,"
                   " weather_status "
                   "FROM 'main'.'prognos' "
                   "WHERE"
                   " location = '{l}';").format(l=location_)

        data = self.cursor_.execute(sql_cmd)

        return data.fetchall()[:days]

    def get_current_forecast(self, location_=None):
        """Get the forecast for the current day.

        :param location_: If a location_ is given, returns data only for that
        location, otherwise returns data for all locations.
        """
        sql_cmd = (u"SELECT"
                   " location,"
                   " day,"
                   " month,"
                   " year,"
                   " day_temp,"
                   " night_temp, "
                   " weather_status "
                   "FROM 'main'.'prognos' "
                   "WHERE"
                   " year = '{0}' AND"
                   " month = '{1}' AND"
                   " day = '{2}' AND")

        if location_ is None:
            sql_cmd += u" weather_status != '{ws}';"
            sql_cmd = sql_cmd.format(*get_today_date(), ws=u'No disponible')
        else:
            sql_cmd += u" location= '{l}';"
            sql_cmd = sql_cmd.format(*get_today_date(), l=location_)

        data = self.cursor_.execute(sql_cmd)

        if data:
            return data.fetchall()

        return None

    def current_forecast_in_db(self, location_=None):
        """Test if current day forecast data is in db.

        :param location_: If a location_ is given, check data only for that
        location, otherwise check data for all locations.
        """
        sql_cmd = (u"SELECT"
                   " year,"
                   " month,"
                   " day "
                   "FROM 'main'.'prognos' "
                   "WHERE"
                   " year='{0}' AND"
                   " month='{1}' AND"
                   " day='{2}'")

        if location_ is None:
            sql_cmd += u';'
            sql_cmd = sql_cmd.format(*get_today_date())
        else:
            sql_cmd += u" AND location='{l}';"
            sql_cmd = sql_cmd.format(*get_today_date(), l=location_)

        today = self.cursor_.execute(sql_cmd).fetchall()

        if today:
            return True

        return False

    @property
    def db_is_not_updated(self):
        """Check if the database is up to date."""
        # Is data up to date?
        sql_cmd = (u"SELECT"
                   " year,"
                   " month,"
                   " day,"
                   " weather_status "
                   "FROM 'main'.'prognos';")

        first_day = self.cursor_.execute(sql_cmd).fetchone()

        if (first_day is None or
                datetime.date(*first_day[:-1]) < datetime.date.today() or
                first_day[3] == u'No disponible'):
            return True

        return False

    @property
    def db_is_empty(self):
        """Check if the database is empty."""
        # Is DB empty?
        sql_cmd = u"SELECT * FROM 'main'.'prognos';"
        db_content = self.cursor_.execute(sql_cmd).fetchall()
        if not db_content:
            return True

        return False

    @property
    def db_is_obsolete(self):
        """Check if the data stored in database is obsolete."""
        sql_cmd = u"SELECT year, month, day FROM 'main'.'prognos';"
        stored_days = self.cursor_.execute(sql_cmd).fetchall()
        today = get_today_date(int_format=True)

        if today not in stored_days:
            return True

        return False

    def close_connection(self):
        """Close the connection to database."""
        if self.connection:
            self.connection.close()
