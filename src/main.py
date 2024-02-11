import sys
import json
import os
import time
from datetime import timedelta
sys.path.append('/app')
from timer import *
from shortcuts_window import SHORTCUTS_WINDOW
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, GLib, Adw, Gio

# Units of day, minute, hour and second
def strfdelta(tdelta, fmt):
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)

# Path for config files
CONFIG = os.path.expanduser('~') + '/.var/app/com.github.vikdevelop.timer/config'
DATA = os.path.expanduser('~') + '/.var/app/com.github.vikdevelop.timer/data'
# Print about timer status
print(jT["timer_running"])

if not os.path.exists(f"{DATA}/shortcuts.txt"):
    with open(f"{DATA}/shortcuts.txt", "w") as w:
        w.write("")
        

# Reset all timer settings dialog
class Dialog_reset(Adw.MessageDialog):
    def __init__(self, parent, **kwargs):
        super().__init__(transient_for=app.get_active_window(), **kwargs)

        self.set_heading(heading=jT["delete_timer_settings"])
        self.set_body(body=jT["dialog_remove_warning"])
        self.add_response('no', jT["cancel"])
        self.add_response('yes', jT["reset"])
        self.set_response_appearance(
            response='yes',
            appearance=Adw.ResponseAppearance.DESTRUCTIVE
        )
        self.connect('response', self.dialog_response)
        self.show()

    def dialog_response(self, dialog, response):
        if response == 'yes':
            os.popen(f'rm -rf {CONFIG}/*')
            app = sys.executable
            os.execl(app, app, *sys.argv)

# Shortcuts window
@Gtk.Template(string=SHORTCUTS_WINDOW) # from shortcuts_window.py
class ShortcutsWindow(Gtk.ShortcutsWindow):
    __gtype_name__ = 'ShortcutsWindow'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

# Timer Application window
class TimerWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connect('close-request', self.close_action, self)
        self.application = kwargs.get('application')
        self.style_manager = self.application.get_style_manager()
        self.set_title(title=jT["timer_title"])
        self.headerbar = Gtk.HeaderBar.new()
        self.set_titlebar(titlebar=self.headerbar)
        
        self.settings = Gio.Settings.new_with_path("com.github.vikdevelop.timer", "/com/github/vikdevelop/timer/")
        
        self.get_from_gsettings = False
        self.use_shortcut_text = False
        self.continue_shortcut = False
        
        self.set_size_request(425, 425)
        (width, height) = self.settings["window-size"]
        self.set_default_size(width, height)
        
        if self.settings["maximized"]:
            self.maximize()
            
        if self.settings["resizable"] == False:
            self.set_resizable(False)
        
        if self.settings["dark-theme"]:
            self.style_manager.set_color_scheme(
                color_scheme=Adw.ColorScheme.PREFER_DARK
            )
        
        # Set up keyboard shortcuts
        keycont = Gtk.EventControllerKey()
        keycont.connect('key-pressed', self.keys, self)
        self.add_controller(keycont)
        
        # Gtk.Switches
        self.switch_01 = Gtk.Switch.new()
        if self.settings["dark-theme"]:
            self.switch_01.set_active(True)
        self.switch_01.set_valign(align=Gtk.Align.CENTER)
        self.switch_01.connect('notify::active', self.on_switch_01_toggled)
        
        self.switch_02 = Gtk.Switch.new()
        if self.settings["resizable"]:
            self.switch_02.set_active(True)
        self.switch_02.set_valign(align=Gtk.Align.CENTER)
        self.switch_02.connect('notify::active', self.on_switch_02_toggled)
        
        self.switch_04 = Gtk.Switch.new()
        if self.settings["show-notification-icon"]:
            self.switch_04.set_active(True)
        self.switch_04.set_valign(align=Gtk.Align.CENTER)
        
        self.switch_05 = Gtk.Switch.new()
        if self.settings["use-in-alarm-clock"]:
            self.switch_05.set_active(True)
        self.switch_05.set_valign(align=Gtk.Align.CENTER)
        
        self.switch_06 = Gtk.Switch.new()
        if self.settings["vertical-time-text"]:
            self.switch_06.set_active(True)
        self.switch_06.set_valign(align=Gtk.Align.CENTER)
        
        self.switch_07 = Gtk.Switch.new()
        if self.settings["show-appname"]:
            self.switch_07.set_active(True)
        self.switch_07.set_valign(align=Gtk.Align.CENTER)
        
        self.switch_08 = Gtk.Switch.new()
        if self.settings["save-expander-row"]:
            self.switch_08.set_active(True)
        self.switch_08.set_valign(align=Gtk.Align.CENTER)

        # Gtk.Box() layout
        self.mainBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.mainBox.set_halign(Gtk.Align.CENTER)
        self.mainBox.set_valign(Gtk.Align.CENTER)
        self.mainBox.set_margin_start(47)
        self.mainBox.set_margin_end(47)
        self.set_child(self.mainBox)
        
        # App menu
        self.menu_button_model = Gio.Menu()
        self.menu_button_model.append(jT["keyboard_shortcuts"], 'app.shortcuts')
        self.menu_button_model.append(jT["about_app"], 'app.about')
        self.menu_button = Gtk.MenuButton.new()
        self.menu_button.set_icon_name(icon_name='open-menu-symbolic')
        self.menu_button.set_menu_model(menu_model=self.menu_button_model)
        self.headerbar.pack_end(child=self.menu_button)
        
        self.back_type = ""
        self.stop_timing = False
        
        # Gtk Box layout for timing page
        self.timingBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        # Label for countdown timing and Label for describing the action in progress
        self.label = Gtk.Label()
        self.label_action = Gtk.Label()
        self.label_action.set_wrap(True)
        self.label_action.set_justify(Gtk.Justification.CENTER)
        
        # button for edit options
        self.editButton = Gtk.Button.new()
        self.edit_button_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)
        self.edit_button_box.set_halign(Gtk.Align.CENTER)
        self.edit_button_box.append(Gtk.Image.new_from_icon_name( \
            'list-edit-symbolic'))
        self.edit_button_box.append(Gtk.Label.new(jT["edit_options"]))
        self.editButton.set_child(self.edit_button_box)
        self.editButton.add_css_class('flat')
        self.editButton.set_can_focus(False)
        self.editButton.connect('clicked', self.on_editButton_clicked)
        
        # Entry
        self.make_timer_box()
        
        # Properities
        self.properties()
        
        # Load latest translations from GitHub
        #app.load_locales()
        
        # Start timer button
        self.buttonStart = Gtk.Button.new()
        self.start_button_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)
        self.start_button_box.set_halign(Gtk.Align.CENTER)
        self.start_button_box.append(Gtk.Image.new_from_icon_name( \
            'media-playback-start-symbolic'))
        self.start_button_box.append(Gtk.Label.new(jT["start"]))
        self.buttonStart.set_child(self.start_button_box)
        self.buttonStart.add_css_class('suggested-action')
        self.buttonStart.set_can_focus(False)
        self.buttonStart.connect('clicked', self.on_buttonStart_clicked)
        self.headerbar.pack_start(self.buttonStart)
        
        # Reset timer button
        ## Gio.Menu()
        self.ResetMenu = Gio.Menu.new()
        self.reset_item = Gio.MenuItem.new()
        self.reset_item.set_label(label=jT["delete_timer_settings"])
        self.reset_item.set_detailed_action(
            detailed_action='app.reset_settings',
        )
        self.ResetMenu.append_item(self.reset_item)
        
        ## Gtk.Popover()
        self.rPopover = Gtk.PopoverMenu.new_from_model(self.ResetMenu)
        
        ## Adw.SplitButton()
        self.buttonReset = Adw.SplitButton.new()
        self.buttonReset.set_popover(popover=self.rPopover)
        self.buttonReset.set_halign(align=Gtk.Align.CENTER)
        self.buttonReset.connect('clicked', self.on_buttonReset_clicked)
        self.headerbar.pack_end(child=self.buttonReset)
        
        ## Adw.ButtonContent()
        self.rButtonContent = Adw.ButtonContent.new()
        self.rButtonContent.set_icon_name(icon_name='view-refresh-symbolic')
        self.rButtonContent.set_tooltip_text(jT["reset_counter"])
        self.rButtonContent.set_use_underline(use_underline=True)
        self.buttonReset.set_child(self.rButtonContent)
        
        # Stop timer button
        self.buttonStop = Gtk.Button.new()
        self.stop_button_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)
        self.stop_button_box.append(Gtk.Image.new_from_icon_name( \
            'media-playback-stop-symbolic'))
        self.stop_button_box.append(Gtk.Label.new(jT["stop"]))
        self.buttonStop.set_child(self.stop_button_box)
        self.buttonStop.set_can_focus(True)
        self.buttonStop.add_css_class('destructive-action')
        self.buttonStop.connect("clicked", self.on_buttonStop_clicked)
        
        # Pause timer button
        self.buttonPause = Gtk.Button.new_from_icon_name("media-playback-pause-symbolic")
        self.buttonPause.add_css_class("circular")
        self.buttonPause.remove_css_class("flat")
        self.buttonPause.connect("clicked", self.on_buttonPause_clicked)
        
        # Continue timer button
        self.buttonCont = Gtk.Button.new_from_icon_name("media-playback-start-symbolic")
        self.buttonCont.add_css_class("circular")
        self.buttonCont.add_css_class("suggested-action")
        self.buttonCont.connect("clicked", self.on_buttonCont_clicked)
        
        self.timeout_id = None
        self.connect("destroy", self.on_SpinnerWindow_destroy)
        
        self.start_again_dialog()
    
    # Entries of seconds, minutes and hours
    def make_timer_box(self):
        # Layout
        self.timerBox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        self.timerBox.set_margin_start(0)
        self.timerBox.set_margin_end(0)
        
        self.lbox = Gtk.ListBox.new()
        self.lbox.set_selection_mode(mode=Gtk.SelectionMode.NONE)
        self.lbox.get_style_context().add_class(class_name='boxed-list')
        
        # Hour entry and label
        self.hour_entry = Adw.EntryRow()
        self.hour_entry.set_text(str(self.settings["hours"]))
        self.hour_entry.set_title(jT["hours"])
        self.hour_entry.set_alignment(xalign=1)
        self.timerBox.append(self.hour_entry)
        
        # Minute entry and label
        self.minute_entry = Adw.EntryRow()
        self.minute_entry.set_text(str(self.settings["mins"]))
        self.minute_entry.set_title(jT["mins"])
        self.minute_entry.set_alignment(xalign=1)
        self.timerBox.append(self.minute_entry)
        
        # Second entry and label
        self.secs_entry = Adw.EntryRow()
        self.secs_entry.set_text(str(self.settings["seconds"]))
        self.secs_entry.set_title(jT["secs"])
        self.secs_entry.set_alignment(xalign=1)
        self.timerBox.append(self.secs_entry)
        
        self.adw_action_row_time = Adw.ActionRow.new()
        self.adw_action_row_time.set_icon_name(icon_name='com.github.vikdevelop.timer')
        self.adw_action_row_time.add_suffix(widget=self.timerBox)
        self.lbox.append(child=self.adw_action_row_time)
        
        self.mainBox.append(self.lbox)
    
    # Properties
    def properties(self):
        self.adw_expander_row = Adw.ExpanderRow.new()
        self.adw_expander_row.set_title(title=jT["preferences"])
        self.adw_expander_row.set_subtitle(subtitle=jT["preferences_desc"])
        self.load_expander_row_state()
        self.lbox.append(child=self.adw_expander_row)
        
        # Adw.ComboRow - Actions
        actions = Gtk.StringList.new(strings=[
            jT["default"], jT["shut_down"], jT["reboot"], jT["suspend"], jT["play_alarm_clock"]
        ])
        
        self.adw_action_row_timer = Adw.ComboRow.new()
        self.adw_action_row_timer.set_icon_name(icon_name='timer-symbolic')
        self.adw_action_row_timer.set_title(title=jT["action_after_timing"])
        self.adw_action_row_timer.set_title_lines(2)
        self.adw_action_row_timer.set_model(model=actions)
        self.adw_expander_row.add_row(child=self.adw_action_row_timer)
        
        if self.settings["action"] == "Default":
            self.adw_action_row_timer.set_selected(0)
        elif self.settings["action"] == "Shut down":
            self.adw_action_row_timer.set_selected(1)
        elif self.settings["action"] == "Reboot":
            self.adw_action_row_timer.set_selected(2)
        elif self.settings["action"] == "Suspend":
            self.adw_action_row_timer.set_selected(3)
        elif self.settings["action"] == "Play alarm clock":
            self.adw_action_row_timer.set_selected(4)
            
        self.btn = Gtk.Button.new_from_icon_name("go-next-symbolic")
        self.btn.add_css_class("flat")
        self.btn.connect("clicked", self.open_shortcuts_dialog)
        
        ## Adw.ActionRow
        self.adw_action_row_sh = Adw.ActionRow.new()
        self.adw_action_row_sh.set_icon_name(icon_name='shortcuts')
        self.adw_action_row_sh.set_title(title=jT["manage_shortcuts"])
        self.adw_action_row_sh.add_suffix(widget=self.btn)     
        self.adw_action_row_sh.set_activatable_widget(widget=self.btn)
        self.adw_expander_row.add_row(child=self.adw_action_row_sh)    
        
        # Adw ActionRow - play beep
        ## Gtk.Switch
        self.switch_03 = Gtk.Switch.new()
        if self.settings["play-beep"]:
            self.switch_03.set_active(True)
        self.switch_03.set_valign(align=Gtk.Align.CENTER)
        
        ## Adw.ActionRow
        self.adw_action_row_beep = Adw.ActionRow.new()
        self.adw_action_row_beep.set_icon_name(icon_name='folder-music-symbolic')
        self.adw_action_row_beep.set_title(title=jT["play_beep"])
        self.adw_action_row_beep.add_suffix(widget=self.switch_03)     
        self.adw_action_row_beep.set_activatable_widget(widget=self.switch_03)
        self.adw_expander_row.add_row(child=self.adw_action_row_beep)
        
        # Adw ActionRow - custom notification
        ## Gtk.Button
        self.setButton = Gtk.Button.new_from_icon_name('go-next-symbolic')
        self.setButton.add_css_class('circular')
        self.setButton.add_css_class('flat')
        self.setButton.connect('clicked', self.on_notification_button_clicked)
        
        ## Adw.EntryRow
        self.entry = Adw.EntryRow()
        self.entry.set_text(self.settings["notification-text"])
        self.entry.set_title(jT["custom_notification"])
        self.entry.set_show_apply_button(True)
        self.entry.set_enable_emoji_completion(True)
        
        ## Adw.ActionRow
        self.adw_action_row_notification = Adw.ActionRow.new()
        self.adw_action_row_notification.set_icon_name(icon_name='notification-symbolic')
        self.adw_action_row_notification.add_suffix(widget=self.entry)
        self.adw_action_row_notification.add_suffix(widget=self.setButton)
        self.adw_action_row_notification.set_activatable_widget(widget=self.setButton)
        self.adw_expander_row.add_row(child=self.adw_action_row_notification)
        
        # Adw.ActionRow - advanced settings
        ## Gtk.Button
        self.advButton = Gtk.Button.new_from_icon_name('go-next-symbolic')
        self.advButton.add_css_class('circular')
        self.advButton.add_css_class('flat')
        self.advButton.connect('clicked', self.on_advButton_clicked)
        
        ## Adw.ActionRow
        self.adw_action_row_adv = Adw.ActionRow.new()
        self.adw_action_row_adv.set_icon_name(icon_name='preferences-other-symbolic')
        self.adw_action_row_adv.set_title(title=jT["advanced"])
        self.adw_action_row_adv.set_title_lines(2)
        self.adw_action_row_adv.add_suffix(widget=self.advButton)
        self.adw_action_row_adv.set_activatable_widget(widget=self.advButton)
        self.adw_expander_row.add_row(child=self.adw_action_row_adv)
        
    ### Load Adw.ExpanderRow state
    def load_expander_row_state(self):
        if self.settings["save-expander-row"]:
            self.adw_expander_row.set_expanded(True)
    
    # Edit options in ongoing timing
    def edit_options(self):
        self.back_type = "edit_options"
        self.pause_timer()
        self.headerbar.remove(self.buttonStop)
        self.headerbar.remove(self.buttonCont)
        self.set_title(jT["edit_options"])
        
        self.applyButton = Gtk.Button.new()
        self.applyButton.add_css_class('suggested-action')
        self.app_button_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)
        self.app_button_box.append(Gtk.Image.new_from_icon_name( \
            'adw-entry-apply-symbolic'))
        self.app_button_box.append(Gtk.Label.new(jT["apply"]))
        self.applyButton.set_child(self.app_button_box)
        self.applyButton.connect('clicked', self.cancel_edit_options)
        
        self.headerbar.pack_start(self.applyButton)
        self.ebox = Gtk.ListBox.new()
        self.ebox.set_selection_mode(mode=Gtk.SelectionMode.NONE)
        self.ebox.get_style_context().add_class(class_name='boxed-list')
        self.mainBox.append(self.ebox)
        self.mainBox.remove(self.lbox)
        self.mainBox.remove(self.timingBox)
        
        self.adw_expander_row.remove(child=self.adw_action_row_notification)
        self.adw_expander_row.remove(child=self.adw_action_row_timer)
        self.adw_expander_row.remove(child=self.adw_action_row_beep)
        self.adw_expander_row.remove(child=self.adw_action_row_adv)
        
        self.ebox.append(child=self.adw_action_row_timer)
        self.ebox.append(child=self.adw_action_row_beep)
        self.ebox.append(child=self.adw_action_row_notification)
        
    def cancel_edit_options(self, w):
        self.headerbar.remove(self.applyButton)
        self.headerbar.pack_start(self.buttonStop)
        self.headerbar.pack_start(self.buttonPause)
        self.ebox.remove(child=self.adw_action_row_timer)
        self.ebox.remove(child=self.adw_action_row_beep)
        self.ebox.remove(child=self.adw_action_row_notification)
        self.mainBox.remove(self.ebox)
        self.adw_expander_row.add_row(child=self.adw_action_row_timer)
        self.adw_expander_row.add_row(child=self.adw_action_row_beep)
        self.adw_expander_row.add_row(child=self.adw_action_row_notification)
        self.adw_expander_row.add_row(child=self.adw_action_row_adv)
        try:
            self.timingBox.remove(self.label_pause)
            self.timingBox.remove(self.label_paused_status)
        except:
            print("")
        self.set_title(jT["timer_title"])
        self.continue_timer()
        
    ## Set custom notification text
    def custom_notification(self):
        if self.back_type == "edit_options":
            self.back_type = "edit_options"
        else:
            self.back_type = "custom_notification"
        self.mainBox.remove(self.lbox)
        self.mainBox.set_valign(Gtk.Align.START)
        self.mainBox.set_margin_top(15)
        self.headerbar.remove(self.buttonStart)
        self.headerbar.remove(self.buttonReset)
        if self.back_type == 'edit_options':
            self.mainBox.remove(self.ebox)
            self.headerbar.remove(self.applyButton)
        else:
            self.mainBox.remove(self.lbox)
        self.set_title(jT["custom_notification"])
        
        # Back button
        self.backButton = Gtk.Button.new_from_icon_name('go-next-symbolic-rtl')
        self.backButton.connect('clicked', self.cancel_custom_notification)
        self.headerbar.pack_start(self.backButton)
        
        self.label_n = Gtk.Label.new()
        self.label_n.set_markup(jT["notification_text"])
        self.label_n.set_justify(Gtk.Justification.LEFT)
        self.label_n.set_xalign(-1)
        self.label_n.set_yalign(-1)
        self.mainBox.append(self.label_n)
        
        self.cbox = Gtk.ListBox.new()
        self.cbox.set_selection_mode(mode=Gtk.SelectionMode.NONE)
        self.cbox.get_style_context().add_class(class_name='boxed-list')
        self.mainBox.append(self.cbox)
        
        self.label_d = Gtk.Label.new()
        self.label_d.set_markup(jT["alarm_clock_dialog_text"])
        self.label_d.set_justify(Gtk.Justification.LEFT)
        self.label_d.set_xalign(-1)
        self.label_d.set_yalign(-1)
        self.mainBox.append(self.label_d)
        
        self.dbox = Gtk.ListBox.new()
        self.dbox.set_selection_mode(mode=Gtk.SelectionMode.NONE)
        self.dbox.get_style_context().add_class(class_name='boxed-list')
        self.mainBox.append(self.dbox)
        
        # Adw.ActionRow - use in alarm clock dialog
        
        ## Adw.ActionRow
        self.adw_action_row_06 = Adw.ActionRow.new()
        self.adw_action_row_06.set_title(title=jT["show_appicon"])
        self.adw_action_row_06.set_title_lines(6)
        self.adw_action_row_06.add_suffix(widget=self.switch_04)
        self.adw_action_row_06.set_activatable_widget(widget=self.switch_04)
        self.cbox.append(self.adw_action_row_06)
        
        # Adw.ActionRow - use in alarm clock dialog
        
        ## Adw.ActionRow
        self.adw_action_row_08 = Adw.ActionRow.new()
        self.adw_action_row_08.set_title(title=jT["show_appname"])
        self.adw_action_row_08.add_suffix(widget=self.switch_07)
        self.adw_action_row_08.set_activatable_widget(widget=self.switch_07)
        self.cbox.append(self.adw_action_row_08)
        
        # Adw.ActionRow - use in alarm clock dialog
        
        ## Adw.ActionRow
        self.adw_action_row_07 = Adw.ActionRow.new()
        self.adw_action_row_07.set_title(title=jT["use_in_alarm_clock"])
        self.adw_action_row_07.add_suffix(widget=self.switch_05)
        self.adw_action_row_07.set_activatable_widget(widget=self.switch_05)
        self.dbox.append(self.adw_action_row_07)
        
    def cancel_custom_notification(self, widget, *args):
        self.mainBox.remove(self.cbox)
        self.mainBox.remove(self.dbox)
        self.mainBox.remove(self.label_n)
        self.mainBox.remove(self.label_d)
        if self.back_type == 'custom_notification':
            self.mainBox.append(self.lbox)
            self.headerbar.pack_start(self.buttonStart)
            self.headerbar.pack_end(self.buttonReset)
        else:
            self.mainBox.append(self.ebox)
            self.headerbar.remove(self.buttonStart)
            self.headerbar.remove(self.buttonReset)
            self.headerbar.pack_start(self.applyButton)
            self.mainBox.remove(self.lbox)
        self.mainBox.set_valign(Gtk.Align.CENTER)
        self.mainBox.set_margin_top(0)
        self.headerbar.remove(self.backButton)
        self.set_title(jT["timer_title"])
        
    ## Advanced settings section
    def advanced(self):
        self.mainBox.remove(self.lbox)
        self.mainBox.set_valign(Gtk.Align.START)
        self.mainBox.set_margin_top(15)
        self.headerbar.remove(self.buttonStart)
        self.headerbar.remove(self.buttonReset)
        self.set_title(jT["advanced"])
        try:
            self.mainBox.remove(self.ebox)
        except:
            print("")
        
        # Back button
        self.backButton_A = Gtk.Button.new_from_icon_name('go-next-symbolic-rtl')
        self.backButton_A.connect('clicked', self.cancel_advanced)
        self.headerbar.pack_start(self.backButton_A)
        
        self.abox = Gtk.ListBox.new()
        self.abox.set_selection_mode(mode=Gtk.SelectionMode.NONE)
        self.abox.get_style_context().add_class(class_name='boxed-list')
        self.mainBox.append(self.abox)
            
        # Adw ActionRow - Theme configuration
        
        ## Adw.ActionRow
        self.adw_action_row_theme = Adw.ActionRow.new()
        self.adw_action_row_theme.set_icon_name(icon_name='weather-clear-night-symbolic')
        self.adw_action_row_theme.set_title(title=jT["dark_theme"])
        self.adw_action_row_theme.set_subtitle(subtitle=jT["theme_desc"])
        self.adw_action_row_theme.add_suffix(widget=self.switch_01)
        self.adw_action_row_theme.set_activatable_widget(self.switch_01)
        self.abox.append(self.adw_action_row_theme)
        
        # Adw ActionRow - Resizable of Window configuration
        
        ## Adw.ActionRow
        self.adw_action_row_window = Adw.ActionRow.new()
        self.adw_action_row_window.set_icon_name(icon_name='window-maximize-symbolic')
        self.adw_action_row_window.set_title(title=jT["resizable_of_window"])
        self.adw_action_row_window.add_suffix(widget=self.switch_02)
        self.adw_action_row_window.set_activatable_widget(widget=self.switch_02)
        self.abox.append(self.adw_action_row_window)
        
        # Adw.ActionRow - show vertical countdown timer text
        
        ## Adw.ActionRow
        self.adw_action_row_verText = Adw.ActionRow.new()
        self.adw_action_row_verText.set_icon_name(icon_name='history-symbolic')
        self.adw_action_row_verText.set_title(title=jT["vertical_text"])
        self.adw_action_row_verText.set_subtitle(subtitle=jT["vertical_text_desc"])
        self.adw_action_row_verText.add_suffix(widget=self.switch_06)
        self.adw_action_row_verText.set_activatable_widget(widget=self.switch_06)
        self.abox.append(self.adw_action_row_verText)
        
        # Adw.ActionRow - expand Preferences dropdown row
        
        ## Adw.ActionRow
        self.adw_action_row_expander = Adw.ActionRow.new()
        self.adw_action_row_expander.set_icon_name(icon_name='desktop-symbolic')
        self.adw_action_row_expander.set_title(title=jT["save_expander_row_state"])
        self.adw_action_row_expander.set_subtitle(subtitle=jT["save_expander_row_state_desc"])
        self.adw_action_row_expander.add_suffix(widget=self.switch_08)
        self.adw_action_row_expander.set_activatable_widget(widget=self.switch_08)
        self.abox.append(self.adw_action_row_expander)
        
    def cancel_advanced(self, widget, *args):
        self.mainBox.append(self.lbox)
        self.mainBox.remove(self.abox)
        self.mainBox.set_valign(Gtk.Align.CENTER)
        self.mainBox.set_margin_top(0)
        self.headerbar.pack_start(self.buttonStart)
        self.headerbar.pack_end(self.buttonReset)
        self.headerbar.remove(self.backButton_A)
        self.set_title(jT["timer_title"])
    
    def open_shortcuts_dialog(self, w):
        self.shortcuts_dialog()
    
    def shortcuts_dialog(self):
        self.setDialog = Adw.MessageDialog.new(self)
        self.setDialog.set_heading(jT["manage_shortcuts"])
        self.setDialog.set_body_use_markup(True)
        
        self.setDialog.add_response('cancel', jT["cancel"])
        self.setDialog.add_response('remove', jT["remove"])
        self.setDialog.add_response('ok', jT["apply"])
        self.setDialog.set_response_appearance('ok', Adw.ResponseAppearance.SUGGESTED)
        self.setDialog.set_response_appearance('remove', Adw.ResponseAppearance.DESTRUCTIVE)
        self.setDialog.connect('response', self.setDialog_closed)
        
        # Box for appending widgets
        self.mBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.setDialog.set_extra_child(self.mBox)
        
        self.setdBox = Gtk.ListBox.new()
        self.setdBox.set_selection_mode(mode=Gtk.SelectionMode.NONE)
        self.setdBox.get_style_context().add_class(class_name='boxed-list')
        
        self.setdBox_02 = Gtk.ListBox.new()
        self.setdBox_02.set_selection_mode(mode=Gtk.SelectionMode.NONE)
        self.setdBox_02.get_style_context().add_class(class_name='boxed-list')
        
        if os.stat(f"{DATA}/shortcuts.txt").st_size == 0:
            self.label_not = Gtk.Label.new(str=jT["shortcuts_warning"])
            self.mBox.append(self.label_not)
            self.setDialog.set_response_enabled('remove', False)
        else:
            self.label_y = Gtk.Label.new(str=jT["existing_shortcut"])
            self.label_y.set_use_markup(True)
            self.mBox.append(self.label_y)
            
            os.system(f"awk -i inplace 'NF' {DATA}/shortcuts.txt")
            get_data = subprocess.getoutput(f"cat {DATA}/shortcuts.txt")
            split_data = get_data.splitlines()
                    
            model = Gtk.StringList.new(strings=split_data)
            
            self.row = Adw.ComboRow.new()
            self.row.set_title("")
            self.row.set_model(model)
            self.setdBox.append(self.row)
            self.mBox.append(self.setdBox)
        
        self.label_add = Gtk.Label.new(str=f"<b>{jT['new_shortcut']}</b>")
        self.label_add.set_use_markup(True)
        self.mBox.append(self.label_add)
        
        self.expand = Adw.ExpanderRow.new()
        self.expand.set_title(title=jT['new_shortcut'])
        self.setdBox_02.append(self.expand)
        self.mBox.append(self.setdBox_02)
        
        self.entry_add = Adw.EntryRow.new()
        self.entry_add.set_title(jT["shortcut_name"])
        self.expand.add_row(self.entry_add)
        
        self.entry_h = Adw.EntryRow.new()
        self.entry_h.set_title(jT["hours"])
        
        self.entry_m = Adw.EntryRow.new()
        self.entry_m.set_title(jT["mins"])
        
        self.entry_s = Adw.EntryRow.new()
        self.entry_s.set_title(jT["secs"])
        
        self.time_row = Adw.ActionRow.new()
        self.time_row.add_suffix(self.entry_h)
        self.time_row.add_suffix(self.entry_m)
        self.time_row.add_suffix(self.entry_s)
        self.expand.add_row(self.time_row)
        
        self.add_btn = Gtk.Button.new_with_label(jT["add"])
        self.add_btn.add_css_class("suggested-action")
        self.add_btn.connect("clicked", self.on_add)
        self.add_btn.set_valign(Gtk.Align.CENTER)
        self.add_btn.set_margin_start(60)
        self.add_btn.set_margin_end(60)
        self.expand.add_row(self.add_btn)
        
        self.setDialog.show()

    def setDialog_closed(self, w, response):
        item = self.row.get_selected_item()
        get = item.get_string()
        get_split = get.split()
        if response == 'ok':
            self.settings["shortcut-name"] = get_split[0]
            self.settings["hours-shortcut"] = int(get_split[1])
            self.settings["mins-shortcut"] = int(get_split[2])
            self.settings["seconds-shortcut"] = int(get_split[3])
            
            self.get_from_gsettings = True
            self.use_shortcut_text = True
            self.continue_shortcut = True
            
            self.start_timer()
        elif response == 'remove':
            os.system(f"sed -i 's\%s\ \ ' %s/shortcuts.txt" % (get, DATA))
            os.system(f"notify-send \"{jT['shortcut_removed'].format(get)}\" -i com.github.vikdevelop.timer")
            
    def on_add(self, w):
        if " " in self.entry_add.get_text():
            incorrect_text = self.entry_add.get_text()
            correct_text = incorrect_text.replace(" ", "_")
        else:
            correct_text = self.entry_add.get_text()
        with open(f"{DATA}/shortcuts.txt", "a") as d:
            d.write(f"\n{correct_text} {self.entry_h.get_text()} {self.entry_m.get_text()} {self.entry_s.get_text()}")
        self.setDialog.close()
        self.shortcuts_dialog()
        
    # Timer actionsuse_shortcut_text
    ## On timeout function
    tick_counter = timedelta(milliseconds = 250) # static object so we don't recreate the object every time
    zero_counter = timedelta()
    def on_timeout(self, *args, **kwargs):
        self.counter -= self.tick_counter
        if self.counter <= self.zero_counter:
            self.stop_timer()
            self.session()
            print(jT["timing_finished"])
            return False
        self.set_time_text()
        return True
    
    ## Start timer function
    def start_timer(self):
        """ Run Timer. """
        self.check_and_save()
        self.back_type = "edit_options"
        self.headerbar.pack_start(self.buttonStop)
        self.headerbar.pack_start(self.buttonPause)
        self.headerbar.remove(self.buttonStart)
        self.headerbar.remove(self.buttonReset)
        self.mainBox.remove(self.lbox)
        if not self.get_from_gsettings == True:
            self.counter = timedelta(hours = int(self.hour_entry.get_text()), minutes = int(self.minute_entry.get_text()), seconds = int(self.secs_entry.get_text()))
        else:
            self.counter = timedelta(hours = int(self.settings["hours-shortcut"]), minutes = int(self.settings["mins-shortcut"]), seconds = int(self.settings["seconds-shortcut"]))
        #self.play_beep()
        self.set_time_text()
        self.non_activated_session()
        self.timeout_id = GLib.timeout_add(250, self.on_timeout, None)
        
    ### Set time text function
    def set_time_text(self):
        if self.switch_06.get_active() == True:
            self.label.set_text("<span size='31200'>{}</span>".format(
                strfdelta(self.counter, "<b>{hours}</b> %s \n<b>{minutes}</b> %s \n<b>{seconds}</b> %s" % (jT["hours"], jT["mins"], jT["secs"]))
            ))
        else:
            self.label.set_text("<span size='25600'>{}</span>".format(
                strfdelta(self.counter, "<b>{hours}</b> %s <b>{minutes}</b> %s <b>{seconds}</b> %s" % (jT["hours"], jT["mins"], jT["secs"]))
            ))
        self.label.set_use_markup(True)
        
    ## Stop timer function
    def stop_timer(self):
        """ Stop Timer """
        if self.timeout_id:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None
        self.headerbar.remove(self.buttonStop)
        self.headerbar.pack_start(self.buttonStart)
        self.headerbar.pack_end(self.buttonReset)
        self.mainBox.append(self.lbox)
        self.mainBox.remove(self.timingBox)
        self.headerbar.remove(self.buttonPause)
        self.headerbar.remove(self.buttonCont)
        self.back_type = "custom_notification"
        self.stop_timing = True
        self.get_from_gsettings = False
        try:
            self.timingBox.remove(self.label_pause)
            self.timingBox.remove(self.label_paused_status)
        except AttributeError:
            print("")
    
    ## Reset time counter values action
    def reset_timer(self):
        self.hour_entry.set_text('0')
        self.minute_entry.set_text('0')
        self.secs_entry.set_text('0')
        
    ## Pause timer
    def pause_timer(self):
        if self.timeout_id:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None
        self.label_pause = Gtk.Label.new()
        self.label_paused_status = Gtk.Label.new(str=jT["paused"])
        self.timingBox.remove(self.label_action)
        self.timingBox.remove(self.editButton)
        self.timingBox.append(self.label_paused_status)
        if self.switch_06.get_active() == True: 
            self.label_pause.set_markup("<b><span size='31200'>{}</span></b>".format(self.label.get_text()))
        else:
            self.label_pause.set_markup("<b><span size='25600'>{}</span></b>".format(self.label.get_text()))
        self.timingBox.append(self.label_pause)
        self.timingBox.remove(self.label)
        self.timingBox.append(self.editButton)
        self.headerbar.remove(self.buttonPause)
        self.headerbar.pack_start(self.buttonCont)
        self.stop_timing = True
        
    ## Continue timer
    def continue_timer(self):
        #self.spinner.start()
        get_label_time = self.label.get_text()
        res = [int(i) for i in get_label_time.split() if i.isdigit()]
        print(str(res))
        self.hour_entry.set_text(str(res[0]))
        self.minute_entry.set_text(str(res[1]))
        self.secs_entry.set_text(str(res[2]))
        self.timingBox.remove(self.label_pause)
        self.timingBox.remove(self.label_paused_status)
        self.headerbar.pack_start(self.buttonPause)
        self.headerbar.remove(self.buttonCont)
        self.stop_timing = False
        self.get_from_gsettings = False
        self.start_timer()
    
    # Function, that allocates labels in the current timing
    def non_activated_session(self):
        self.timingBox.append(self.label_action)
        self.timingBox.append(self.label)
        try:
            self.timingBox.remove(self.editButton)
        except:
            print("")
        self.timingBox.append(self.editButton)
        self.mainBox.append(self.timingBox)
        at = self.adw_action_row_timer.get_selected_item()
        action = at.get_string()
        if action == jT["default"]:
            self.label_action.set_text(jT["notification_desc"])
        elif action == jT["shut_down"]:
            self.label_action.set_text(jT["shut_down_desc"])
        elif action == jT["reboot"]:
            self.label_action.set_text(jT["reboot_desc"])
        elif action == jT["suspend"]:
            self.label_action.set_text(jT["suspend_desc"])
        elif action == jT["play_alarm_clock"]:
            self.label_action.set_text(jT["play_alarm_clock_desc"])
        else:
            self.label_action.set_text(jT["notification_desc"])
    
    # After finished timer
    ## Function, that allocates actions after finished timer (e.gself.continue_shortcut = True. shut down/reboot/suspend system)
    def session(self):
        at = self.adw_action_row_timer.get_selected_item()
        action = at.get_string()
        if action == jT["default"]:
            self.play_beep()
            self.notification()
        elif action == jT["shut_down"]:
            self.play_beep()
            time.sleep(2)
            os.system('dbus-send --system --print-reply --dest=org.freedesktop.login1 /org/freedesktop/login1 "org.freedesktop.login1.Manager.PowerOff" boolean:true')
        elif action == jT["reboot"]:
            self.play_beep()
            time.sleep(2)
            os.system('dbus-send --system --print-reply --dest=org.freedesktop.login1 /org/freedesktop/login1 "org.freedesktop.login1.Manager.Reboot" boolean:true')
        elif action == jT["suspend"]:
            self.play_beep()
            time.sleep(2)
            os.system('dbus-send --system --print-reply --dest=org.freedesktop.login1 /org/freedesktop/login1 "org.freedesktop.login1.Manager.Suspend" boolean:true')
        elif action == jT["play_alarm_clock"]:
            self.alarm_clock()
            
    ## Play alarm clock
    def alarm_clock(self):
        self.dialogRingstone = Adw.MessageDialog.new(self)
        self.rLabel = Gtk.Label.new()
        self.use_custom_text()
        rBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        self.adw_action_row_beep.add_suffix(widget=self.switch_03)      
        rImage = Gtk.Image.new_from_icon_name("history")
        rImage.set_pixel_size(40)
        rBox.append(rImage)
        rBox.append(self.rLabel)
        self.dialogRingstone.set_extra_child(rBox)
        self.dialogRingstone.add_response('cancel', jT["cancel"])
        self.dialogRingstone.add_response('start', jT["start_again"])
        self.dialogRingstone.set_response_appearance('start', Adw.ResponseAppearance.SUGGESTED)
        self.dialogRingstone.connect('response', self.start_again)
        self.dialogRingstone.show()
        os.popen("bash /app/src/alarm.sh")
        
    def start_again(self, w, response):
        if response == 'start':
            if self.continue_shortcut == True:
                self.get_from_gsettings = True
                self.use_shortcut_text = True
            self.present()
            self.start_timer()
            os.popen('pkill -15 bash && pkill -15 ffplay')
        elif response == 'cancel':
            self.present()
            os.popen('pkill -15 bash && pkill -15 ffplay')
            if self.get_from_gsettings == True:
                self.get_from_gsettings = False
                self.use_shortcut_text = False
                self.continue_shortcut = False
        else:
            os.popen('pkill -15 bash && pkill -15 ffplay')
            if self.get_from_gsettings == True:
                self.get_from_gsettings = False
                self.use_shortcut_text = False
                self.continue_shortcut = False
            
    def use_custom_text(self):
        print(self.use_shortcut_text)
        if self.use_shortcut_text == True:
            if self.settings["shortcut-name"] == "":
                text = f'{jT["timing_finished"]}'
            else:
                text = f'{self.settings["shortcut-name"]}'
            self.rLabel.set_markup("{} {} {} {} {} {}".format(self.settings["hours-shortcut"], jT["hours"], self.settings["mins-shortcut"], jT["mins"], self.settings["seconds-shortcut"], jT["secs"]))
            
        else:
            if self.entry.get_text() == "":
                text = f'{jT["timing_finished"]}'
            else:
                text = f'{self.entry.get_text()}'
            self.rLabel.set_markup("{} {} {} {} {} {}".format(self.hour_entry.get_text(), jT["hours"], self.minute_entry.get_text(), jT["mins"], self.secs_entry.get_text(), jT["secs"]))
            
        if self.switch_05.get_active() == True:
            self.dialogRingstone.set_heading(text)
        else:
            self.dialogRingstone.set_heading(jT["timing_finished"])
    
    ## Send notification after finished timer (if this action is selected in actions.json config file)
    def notification(self):
        if self.switch_07.get_active():
            timer_name = f'{jT["timer_title"]}'
        else:
            timer_name = ''
        if self.switch_04.get_active() == True:
            timer_icon = '-i com.github.vikdevelop.timer'
        else:
            timer_icon = '-i d'
        if not self.get_from_gsettings:
            if self.settings["notification-text"] == "":
                time_text = jT["timing_finished"]
            else:
                time_text = self.settings["notification-text"]
            if self.entry.get_text() == "":
                self.set_text_of_notification(timer_name, timer_icon, time_text)
            else:
                self.set_text_of_notification(timer_name, timer_icon, time_text)
        else:
            time_text = self.settings["shortcut-name"]
            self.set_text_of_notification(timer_name, timer_icon, time_text)
        
    def set_text_of_notification(self, timer_name, timer_icon, time_text):
        if timer_name == "":
            os.system('notify-send "{}" {}'.format(time_text,timer_icon))
        else:
            os.system('notify-send {} "{}" {}'.format(timer_name, time_text ,timer_icon))
    
    ## Play beep after finished timer
    def play_beep(self):
        if self.switch_03.get_active() == True:
            print("")
        else:
            os.popen("ffplay -nodisp -autoexit /app/share/beeps/Oxygen.ogg > /dev/null 2>&1")
    
    # Checking whether the entered values are correct and then saving them
    def check_and_save(self):
        if self.hour_entry.get_text() == "":
            self.hour_entry.set_text('0')
        elif self.minute_entry.get_text() == "":
            self.minute_entry.set_text('0')
        elif self.secs_entry.get_text() == "":
            self.secs_entry.set_text('0')
    
    # Keyboard shortcuts action
    def keys(self, keyval, keycode, state, user_data, win):
        if keycode == ord('q'):
            win.close()
        if keycode == ord('s'):
            self.menu_button.set_can_focus(True)
            self.menu_button.do_focus(self.menu_button, True)
            self.start_timer()
        if keycode == ord('c'):
            print(jT["timing_ended"])
            self.stop_timer()
        if keycode == 0xFF0D:
            self.start_timer()
        if keycode == 0xFF1B: # Alternative key for stop timer and close Notification settings and More settings (EsC)
            print(jT["timing_ended"])
            self.stop_timer()
            try:
                self.mainBox.remove(self.cbox)
                self.headerbar.remove(self.backButton)
                self.mainBox.set_valign(Gtk.Align.CENTER)
                self.mainBox.set_margin_top(0)
                self.mainBox.remove(self.dbox)
                self.mainBox.remove(self.label_n)
                self.mainBox.remove(self.label_d)
                self.set_title(jT["timer_title"])
            except:
                print("")
            try:
                self.mainBox.remove(self.abox)
                self.headerbar.remove(self.backButton_A)
                self.mainBox.set_valign(Gtk.Align.CENTER)
                self.mainBox.set_margin_top(0)
                self.set_title(jT["timer_title"])
            except:
                print("")
        if keycode == ord('r'):
            self.reset_timer()
        if keycode == ord('p'):
            self.pause_timer()
        if keycode == ord('t'):
            try:
                self.timingBox.remove(label_pause)
            except:
                print("")
            self.continue_timer()
        if keycode == ord('n'):
            self.custom_notification()
        if keycode == ord('m'):
            self.advanced()
        if keycode == 0xFFBF:
            self.style_manager.set_color_scheme(
                    color_scheme=Adw.ColorScheme.PREFER_DARK
                )
            self.switch_01.set_active(True)
            self.settings["dark-theme"] = self.switch_01.get_active()
        if keycode == 0xFFC0:
            self.style_manager.set_color_scheme(
                    color_scheme=Adw.ColorScheme.FORCE_LIGHT
                )
            self.switch_01.set_active(False)
            self.settings["dark-theme"] = self.switch_01.get_active()
        if keycode == 0xFFC2:
            self.dialog_reset = Dialog_reset(self)
    
    # Action after closing Timer window
    def close_action(self, widget, *args):
        (width, height) = self.get_default_size()
        straction = self.adw_action_row_timer.get_selected_item()
        pr_action = straction.get_string()
        if pr_action == jT["default"]:
            action = "default"
        elif pr_action == jT["shut_down"]:
            action = "Shut down"
        elif pr_action == jT["reboot"]:
            action = "Reboot"
        elif pr_action == jT["suspend"]:
            action = "Suspend"
        elif pr_action == jT["play_alarm_clock"]:
            action = "Play alarm clock"
        
        if self.label.get_text() == "":
            print("")
            start_background = False
        elif self.stop_timing == True:
            start_background = False
        else:
            o_text = self.label.get_text()
            htext = o_text.replace(f'{jT["hours"]}', "")
            mtext = htext.replace(f'{jT["mins"]}', "")
            stext = mtext.replace(f'{jT["secs"]}', "")
            text = stext.split()
            start_background = True  
        
        self.settings["window-size"] = (width, height)
        self.settings["maximized"] = self.is_maximized()
        self.settings["dark-theme"] = self.switch_01.get_active()
        self.settings["resizable"] = self.switch_02.get_active()
        self.settings["play-beep"] = self.switch_03.get_active()
        self.settings["show-notification-icon"] = self.switch_04.get_active()
        self.settings["use-in-alarm-clock"] = self.switch_05.get_active()
        self.settings["vertical-time-text"] = self.switch_06.get_active()
        self.settings["show-appname"] = self.switch_07.get_active()
        self.settings["save-expander-row"] = self.switch_08.get_active()
        self.settings["action"] = action
        self.settings["notification-text"] = self.entry.get_text()
        if start_background == True:
            self.set_hide_on_close(True)
            self.settings["hours"] = int(text[0])
            self.settings["mins"] = int(text[1])
            self.settings["seconds"] = int(text[2])
            self.hide()
            self.start_timer()
            return True
            #GLib.timeout_add(2, self.exit)
        else:
            self.settings["hours"] = int(self.hour_entry.get_text())
            self.settings["mins"] = int(self.minute_entry.get_text())
            self.settings["seconds"] = int(self.secs_entry.get_text())
            exit()
        
    def exit(self):
        os.popen("python3 /app/src/background.py")
        
    def start_again_dialog(self):
        if os.path.exists(f"{DATA}/start_timer_again.json"):
            with open(f"{DATA}/start_timer_again.json") as s:
                rs = json.load(s)
            if rs["start_timer_again"] == "true":
                self.start_timer()
                os.popen(f"rm -rf {DATA}/*")
    
    # Button actions
    ## Start button action
    def on_buttonStart_clicked(self, widget, *args):
        """ button "clicked" in event buttonStart. """
        self.menu_button.set_can_focus(True)
        self.menu_button.do_focus(self.menu_button, True)
        self.start_timer()
        return True
    
    ## Stop button action
    def on_buttonStop_clicked(self, buttonStop):
        """ button "clicked" in event buttonStop. """
        self.menu_button.set_can_focus(True)
        self.menu_button.do_focus(self.menu_button, True)
        self.stop_timer()
        print(jT["timing_ended"])
    
    ## Reset button action
    def on_buttonReset_clicked(self, buttonReset):
        self.reset_timer()
        
    ## Pause button action
    def on_buttonPause_clicked(self, buttonPause):
        self.pause_timer()
        
    ## Continue button action
    def on_buttonCont_clicked(self, buttonPause):
        self.continue_timer()
    
    ## edit button action
    def on_editButton_clicked(self, buttonStart):
        self.edit_options()
        
    ## action of notification button
    def on_notification_button_clicked(self, widget, *args):
        self.custom_notification()
    
    ## action of advButton
    def on_advButton_clicked(self, widget, *args):
        self.advanced()
    
    def on_SpinnerWindow_destroy(self, widget, *args):
        """ procesing closing window """
        if self.timeout_id:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None
        Gtk.main_quit()
    
    ## Save app theme configuration
    def on_switch_01_toggled(self, switch01, GParamBoolean):
        if switch01.get_active():
            self.style_manager.set_color_scheme(
                    color_scheme=Adw.ColorScheme.PREFER_DARK
                )
        else:
            self.style_manager.set_color_scheme(
                    color_scheme=Adw.ColorScheme.FORCE_LIGHT
                )
    
    ## Save resizable window configuration
    def on_switch_02_toggled(self, switch02, GParamBoolean):
        if switch02.get_active():
                self.set_resizable(True)
        else:
            self.set_resizable(False)
            self.set_default_size(425, 425)
            self.set_size_request(425, 425)
        
# Adw Application class
class MyApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect('activate', self.on_activate)
        self.create_action('shortcuts', self.on_shortcuts_action, ["<primary>question"])
        self.create_action('about', self.on_about_action, ["F1"])
        self.create_action('reset_settings', self.on_reset_settings_action, ["F5"])

    # Run Keyboard shortcuts dialog
    def on_shortcuts_action(self, action, param):
        shortcuts_window = ShortcutsWindow(
            transient_for=self.get_active_window())
        shortcuts_window.present()
    
    # Run About dialog
    def on_about_action(self, action, param):
        dialog = Adw.AboutWindow(transient_for=app.get_active_window())
        dialog.set_application_name(jT["timer_title"])
        dialog.set_version("3.3.3")
        dialog.set_developer_name("vikdevelop")
        self.add_translations_link(dialog)
        dialog.set_release_notes("<p>Fixed bug when continuing timing in the shortcut mode, the time is countdown from scratch. From now on, the time continues on. Also improved the Keyboard shortcuts window</p>")
        dialog.set_license_type(Gtk.License(Gtk.License.GPL_3_0))
        dialog.set_website("https://github.com/vikdevelop/timer")
        dialog.set_issue_url("https://github.com/vikdevelop/timer/issues")
        dialog.set_translator_credits(jT["translator_credits"])
        dialog.set_copyright("© 2022 vikdevelop")
        dialog.set_developers(["vikdevelop https://github.com/vikdevelop"])
        dialog.set_application_icon("com.github.vikdevelop.timer")
        dialog.show()
    
    def add_translations_link(self, dialog):
        if r_lang == "en":
            dialog.add_link("Translate Timer to your language", "https://hosted.weblate.org/projects/vikdevelop/timer/")
        else:
            dialog.add_link("Contribute to translations", "https://hosted.weblate.org/projects/vikdevelop/timer/")

    def on_reset_settings_action(self, action, param):
        self.dialog_reset = Dialog_reset(self)
        
    def load_locales(self):
        os.popen("cd ~/.var/app/com.github.vikdevelop.timer/cache && wget -c {}/{} > /dev/null 2>&1 && pkill -15 wget && pkill -15 sh".format(BASE_URL, lang))
        
    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect('activate', callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f'app.{name}', shortcuts)
    
    def on_activate(self, app):
        self.win = TimerWindow(application=app)
        self.win.present()
app = MyApp(application_id="com.github.vikdevelop.timer")
app.run(sys.argv)
print(jT["timer_quit"])
