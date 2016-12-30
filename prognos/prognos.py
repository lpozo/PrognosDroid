# -*- coding: utf-8 -*-

# prognos.py.
#
# Copyright 2015
# Leodanis Pozo Ramos <lpozo@openmailbox.org>
# Ozkar L. Garcell <ozkar.garcell@gmail.com>
#
# Important: This module is intended to be imported
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

from os import makedirs
from os.path import expanduser, join, exists

from kivy import platform
from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.settings import SettingsWithSidebar

from .aboutdialog import AboutDialog
from .msgbox import MsgBox
from .utils import convert_temp
from .utils import get_current_date
from .weather import CubanWeather


Builder.load_file('prognos/kv/toolbar.kv')


class PrognosRoot(AnchorLayout, object):
    """Prognos root Widget.

    In this widget, the basic UI of Prognos is defined.
    """

    location_label = ObjectProperty(None)
    date_label = ObjectProperty(None)
    max_temp_label = ObjectProperty(None)
    min_temp_label = ObjectProperty(None)
    weather_image = ObjectProperty(None)
    status_label = ObjectProperty(None)

    def __init__(self, prognos_app, **kwargs):
        """Initialize Prognos's root widget."""
        super(PrognosRoot, self).__init__(**kwargs)

        # Keep a reference to Prognos App
        self.prognos_app = prognos_app

        # Instance of CubanWeather class
        self.cuban_weather = CubanWeather(self.prognos_app)

        self.update_prognos(
            location_=self.prognos_app.location,
            weather_forecast_=self.cuban_weather.weather_forecast)

    # Private methods
    @staticmethod
    def _get_date():
        """Get current date."""
        return (unicode(get_current_date('week_day')) + ', ' +
                unicode(get_current_date()) + ' ' +
                unicode(get_current_date('month')) + ' ' +
                unicode(get_current_date('year')))

    def _set_date(self, date):
        """Set the date in the UI.

        :param date: Current date as a string.
        """
        self.date_label.text = date

    def _set_location(self, location):
        """Set the location in the UI.

        :param location: Current location.
        """
        self.location_label.text = location

    def _set_weather_status(self, weather_status):
        """Set the weather status in the UI."""
        self.status_label.text = (u'Pronóstico para hoy:' + ' ' +
                                  unicode(weather_status))

    def _set_temp(self, temp, label, hour):
        """Set the min and max temperature in the UI."""
        if self.cuban_weather.weather_forecast[temp]:
            temp_ = int(self.cuban_weather.weather_forecast[temp])
            temp_ = convert_temp(temp_value=temp_,
                                 to_temp=self.prognos_app.temp_unit[:-3])
        else:
            temp_ = 0

        label.text = (hour + ' ' + unicode(temp_) + ' ' +
                      self.prognos_app.temp_unit[-2:])

    # Public interface
    def update_prognos(self, location_, weather_forecast_, *args):
        """Update Prognos forecast data and UI.

        :param location_:
        :param weather_forecast_:
        :param args: For binding purpose only
        """
        # Delete the args parameter cause we don't use it
        del args

        # Fetch the weather forecast from the DB
        self.cuban_weather.fetch_weather_locally(location=location_)

        # Update UI
        self.update_ui(weather_forecast=weather_forecast_)

    def update_ui(self, weather_forecast):
        """Update all elements in the UI.

        This method update all the elements in UI.
        :param weather_forecast: dictionary with forecast data
        """
        # First, the Location Label
        self._set_location(location=weather_forecast['location'])

        # Then the Date Label
        self._set_date(date=self._get_date())

        # Then the Status Label
        self._set_weather_status(weather_forecast['weather_status'])

        # Then the main weather image
        self.set_weather_image(image_path=self.cuban_weather.weather_statuses[
            weather_forecast['weather_status']])

        # Then the minimum temperature label
        self._set_temp(temp='night_temp',
                       label=self.min_temp_label,
                       hour=u'En la madrugada:')

        # Then the maximum temperature label
        self._set_temp(temp='day_temp',
                       label=self.max_temp_label,
                       hour=u'En la tarde:')

    def set_weather_image(self, image_path, *args):
        """Set the weather image in the UI.

        :param image_path: Path to the weather image in the file system.
        :param args: For binding purpose only.
        """
        # Delete the args parameter cause we don't use it
        del args

        self.weather_image.source = image_path

    def update_weather_forecast(self):
        """Update the weather forecast information in the UI."""
        # Loading...
        self.set_weather_image(image_path='images/image-loading.gif')

        self.cuban_weather.fetch_weather_online(
            use_proxy=self.prognos_app.use_proxy,
            host=self.prognos_app.host,
            port=self.prognos_app.port)

    def extend_weather_forecast(self):
        """Display information for extended forecast."""
        # Reset number of days in extended forecast, default to 3
        self.cuban_weather.days_dialog.days_spinner.text = '3 Días'

        # Open days_dialog to set days in extended forecast
        self.cuban_weather.days_dialog.open()

    def open_options(self):
        """Prognos' configuration open_options."""
        # Open the configuration dialog
        self.prognos_app.open_settings()

    @staticmethod
    def show_about_info():
        """About Prognos' Authors."""
        about_dialog = AboutDialog()
        about_dialog.open()


class PrognosApp(App, object):
    """Prognos App class."""

    # Do not use Kivy config panel
    use_kivy_settings = False

    # Defining the kv files directory to load prognos.kv
    kv_directory = 'prognos/kv'

    # App settings panel style
    settings_cls = SettingsWithSidebar

    def __init__(self, **kwargs):
        """Initialize PrognosApp's objects."""
        super(PrognosApp, self).__init__(**kwargs)

        # Bind Window.on_close to close DB connection
        Window.bind(on_close=self._on_close)

        # Initialize config variables
        self.location = u''
        self.temp_unit = u''
        self.host = u''
        self.port = u''
        self.use_proxy = False

    def _on_close(self):
        """Triggered when app/window is closed to close DB connection."""
        # Close prognos_db connection on window close or app exit
        self.root.cuban_weather.prognos_db.close_connection()

    def build_config(self, config):
        """Build the Prognos' config and set default values."""
        config.setdefaults('general', {
            'location_': u'La Habana',
            'temp_unit_': u'Celsius ºC'
        })

        config.setdefaults('network', {
            'use_proxy_': '0',
            'host_': u'',
            'port_': u''
        })

    def build(self):
        """Build Prognos application."""
        # App icon
        self.icon = 'images/prognos.png'

        # Get current location
        self.location = self.config.get('general', 'location_')

        # Get current temperature unit
        self.temp_unit = self.config.get('general', 'temp_unit_')

        # Get current use_proxy
        self.use_proxy = bool(int(self.config.get('network', 'use_proxy_')))

        # Get current proxy host
        self.host = self.config.get('network', 'host_')

        # Get current proxy port
        try:
            int(self.config.get('network', 'port_'))
        except ValueError:
            pass
        else:
            self.port = self.config.get('network', 'port_')

        # Root widget
        self.root = PrognosRoot(self)

        return self.root

    def build_settings(self, settings):
        """Build Prognos' settings panel."""
        settings.add_json_panel('Prognos',
                                self.config,
                                'prognos/prognos.json')
        settings.interface.menu.width = 150
        settings.interface.menu.close_button.text = 'OK'
        settings.interface.content.current_panel.children[0].disabled = (
            not self.use_proxy)
        settings.interface.content.current_panel.children[1].disabled = (
            not self.use_proxy)

    def on_config_change(self, config, section, key, value):
        """Fired on config change."""
        if config is self.config:
            token = (section, key)
            if token == ('general', 'location_'):
                self.location = value
                # On location change Update UI if forecast info is available
                # in DB, else use default info
                if self.root.cuban_weather.prognos_db.current_forecast_in_db(
                        location_=self.location):
                    self.root.cuban_weather.fetch_weather_locally(
                        self.location)
                else:
                    self.root.cuban_weather.set_default_forecast_data()

                self.root.update_ui(self.root.cuban_weather.weather_forecast)
            elif token == ('general', 'temp_unit_'):
                self.temp_unit = value
                # On temperature unit change, update UI
                self.root.update_ui(self.root.cuban_weather.weather_forecast)
            elif token == ('network', 'use_proxy_'):
                self.use_proxy = bool(int(value))
                self._app_settings.interface.content.current_panel.\
                    children[0].disabled = not self.use_proxy
                self._app_settings.interface.content.current_panel.\
                    children[1].disabled = not self.use_proxy
            elif token == ('network', 'host_'):
                if value:
                    self.host = value
                else:
                    msg_box = MsgBox()
                    msg_box.msg_label.text = 'Debe introducir un nombre ' \
                                             'de servidor proxy válido.'
                    msg_box.open()
                    self.port = None
            elif token == ('network', 'port_') and value != u'':
                try:
                    int(value)
                except ValueError:
                    # Dialog for messages
                    msg_box = MsgBox()
                    msg_box.msg_label.text = 'Debe introducir un número ' \
                                             'de puerto válido.'
                    msg_box.open()
                    self.port = None
                else:
                    self.port = value

    def get_application_config(self, defaultpath='%(appdir)s/%(appname)s.ini'):
        """Get application config from config DB."""
        if platform == 'linux':
            if not exists(join(expanduser("~"), '.prognos')):
                makedirs(join(expanduser("~"), '.prognos'))
            return super(PrognosApp, self).get_application_config(
                '~/.prognos/%(appname)s.ini')

        elif platform == 'android':
            if not exists('/sdcard/.{app_conf_dir}'.format(
                    app_conf_dir=self.get_application_name().lower())):
                makedirs('/sdcard/.{app_conf_dir}'.format(
                    app_conf_dir=self.get_application_name().lower()))

            return '/sdcard/.{app_conf_dir}/{appname}.ini'.format(
                app_conf_dir=self.get_application_name().lower(),
                appname=self.get_application_name().lower())


def main():
    """Prognos' main function."""
    PrognosApp().run()
