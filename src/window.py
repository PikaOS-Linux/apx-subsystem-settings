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

from .driver import VanillaDriverRow, VanillaDriversGroup
from .program import VanillaApxProgram
from .container import VanillaApxContainer
from .ubuntu_drivers import UbuntuDrivers
from .apx import Apx
from .vso import Vso
from .dialog_installation import VanillaDialogInstallation
from .run_async import RunAsync


logger = logging.getLogger("Vanilla")


@Gtk.Template(resource_path='/org/vanillaos/ControlCenter/gtk/window.ui')
class VanillaWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'VanillaWindow'
    __gsignals__ = {
        "installation-finished": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    page_drivers = Gtk.Template.Child()
    status_drivers = Gtk.Template.Child()
    status_no_drivers = Gtk.Template.Child()
    status_updates = Gtk.Template.Child()
    btn_apply = Gtk.Template.Child()
    toasts = Gtk.Template.Child()
    row_update_status = Gtk.Template.Child()
    combo_update_schedule = Gtk.Template.Child()
    str_update_schedule = Gtk.Template.Child()
    switch_update_smart = Gtk.Template.Child()
    page_apx = Gtk.Template.Child()
    group_containers = Gtk.Template.Child()
    group_apps = Gtk.Template.Child()
    
    __selected_drivers = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__selected_default = None
        self.ubuntu_drivers = UbuntuDrivers()
        self.vso = Vso()
        self.apx = Apx()
        self.__build_ui()

    def __build_ui(self):
        self.__setup_devices()
        self.__setup_vso()
        self.__setup_apx()

        self.connect("installation-finished", self.__on_installation_finished)
    
    # region Devices
    def __setup_devices(self):
        def run_async():
            result = []
            for vendor in self.ubuntu_drivers.get_devices():
                result.append(VanillaDriversGroup(
                        vendor["vendor"], 
                        vendor["model"], 
                        vendor["drivers"]))

            return result

        def callback(result, *args):
            if result is None or type(result) is bool or len(result) == 0:
                self.status_no_drivers.set_visible(True)
                self.status_drivers.set_visible(False)
                return

            self.btn_apply.connect("clicked", self.__on_apply_clicked)

            for item in result:
                item.connect("installation-needed", self.__on_installation_needed)
                self.page_drivers.add(item)

            self.status_drivers.set_visible(False)
            self.page_drivers.set_visible(True)

        RunAsync(run_async, callback)
    
    def __on_installation_needed(self, widget, model, driver):
        logging.info("Installation requested: {}".format(driver))
        self.__selected_drivers[model] = driver
        self.btn_apply.set_visible(len(self.__selected_drivers) > 0)
    
    def __on_installation_finished(self, widget, result, *args):
        self.__selected_drivers = {}
        self.btn_apply.set_visible(False)

        if not result:
            self.toast(_("Installation Failed."))
            return

        self.toast(_("New Drivers Installed."))
        logger.info("Installation finished.")
        subprocess.run(['gnome-session-quit', '--reboot'])


    def __on_apply_clicked(self, widget):
        if not self.ubuntu_drivers.can_install():
            self.toast(_("Another transaction is running or the system needs to be restarted."))
            return

        self.btn_apply.set_visible(False)

        res = []
        for model in self.__selected_drivers:
            res.append(self.__selected_drivers[model])

        command = self.ubuntu_drivers.get_install_command(res)
        VanillaDialogInstallation(self, command).show()
    # endregion

    # region Vso
    def __setup_vso(self):
        if latest_check := self.vso.get_latest_check_beautified():
            self.row_update_status.set_subtitle(latest_check)

        if scheduling := self.vso.scheduling:
            state = 1
            if scheduling == "weekly":
                state = 0
            elif scheduling == "monthly":
                state = 1
            self.combo_update_schedule.set_selected(state)

        if smart := self.vso.smart:
            print(smart)
            self.switch_update_smart.set_active(smart)

        self.combo_update_schedule.connect("notify::selected", self.__on_update_schedule_changed)
        self.switch_update_smart.connect("state-set", self.__on_update_smart_changed)

    def __on_update_smart_changed(self, widget, state, *args):
        if self.vso.set_smartupdate(state):
            self.toast(_("SmartUpdate Changed."))
            return

    def __on_update_schedule_changed(self, widget, *args):
        new_state = widget.get_selected()
        old_state = 0 if new_state == 1 else 1

        if self.vso.set_scheduling(new_state):
            self.toast(_("Update Schedule Changed."))
            return
            
    # endregion

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
