# window.py
#
# Copyright 2022 Mirko Brombin
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-only

import logging
import subprocess
from gi.repository import Adw
from gi.repository import Gtk, GLib, GObject

from .program import VanillaApxProgram
from .container import VanillaApxContainer
from .backends.apx import Apx
from .run_async import RunAsync


logger = logging.getLogger("Vanilla")


@Gtk.Template(resource_path='/com/cosmo/ApxSubsystemSettings/gtk/window.ui')
class VanillaWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'VanillaWindow'
    __gsignals__ = {
        "installation-finished": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    btn_apply = Gtk.Template.Child()
    toasts = Gtk.Template.Child()
    page_apx = Gtk.Template.Child()
    group_containers = Gtk.Template.Child()
    group_apps = Gtk.Template.Child()
    
    __selected_drivers = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__selected_default = None
        self.apx = Apx()
        self.__build_ui()

    def __build_ui(self):
        self.__setup_apx()

    # region Apx
    def __setup_apx(self):
        if not self.apx.supported:
            self.page_apx.set_visible(False)
            return
            
        for container in self.apx.containers:
            _row = VanillaApxContainer(self, container)
            self.group_containers.add(_row)
            
        for app in self.apx.apps:
            _row = VanillaApxProgram(app)
            _row.connect("run-requested", self.__on_apx_run_requested)
            self.group_apps.add(_row)
    
    def __on_apx_run_requested(self, widget, name):
        def run_async():
            return self.apx.run(name)

        def callback(result, *args):
            widget.emit("program-exited", name)

            if result in [None, False]:
                self.toast(_("{} Exited With Error.").format(name))
                return

            self.toast(_("{} Exited.").format(name))

        RunAsync(run_async, callback)
        self.toast(_("{} Launched.").format(name))
    # endregion
    
    def toast(self, message, timeout=2):
        toast = Adw.Toast.new(message)
        toast.props.timeout = timeout
        self.toasts.add_toast(toast)
