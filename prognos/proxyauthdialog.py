# -*- coding: utf-8 -*-

# proxyauthdialog.py
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

"""Dialog for proxy authentication."""

from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup


Builder.load_file('prognos/kv/proxyauthdialog.kv')


class ProxyAuthDialog(Popup):

    ok_button = ObjectProperty(None)
    cancel_button = ObjectProperty(None)
    user_text = ObjectProperty(None)
    password_text = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(ProxyAuthDialog, self).__init__(**kwargs)

    def get_auth_data(self):
        return u'{u}'.format(u=self.user_text.text), r'{p}'.format(
            p=self.password_text.text)

    def on_open(self):
        self.user_text.focus = True
