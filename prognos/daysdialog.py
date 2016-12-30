# -*- coding: utf-8 -*-

# daysdialog.py
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


from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup


Builder.load_file('prognos/kv/daysdialog.kv')


class DaysDialog(Popup):
    days_spinner = ObjectProperty(None)
    ok_button = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(DaysDialog, self).__init__(**kwargs)
        # Number of days in extended forecast
        self.days = None

    def _get_days(self):
        return int(self.days_spinner.text[0])

    def on_dismiss(self):
        self.days = self._get_days()
