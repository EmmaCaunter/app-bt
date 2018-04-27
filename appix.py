# Kivy Libs
from kivy.app import App
from kivy.event import EventDispatcher
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Rectangle, Color
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty
from kivy.uix.widget import WidgetException
from kivy.utils import platform
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout



# from kivy.config import Config



# Standard Libs
import json
import random
from functools import partial
import time
import pprint
import os
import datetime

# Local Libs

import instructions


class NavigationButton(ButtonBehavior, Image):
    pass


from kivy.core.window import Window

class AppixBase(FloatLayout):

    # json_data = open('media/content_map.json')
    # content_map = json.load(json_data)
    # json_data.close()
    print " "
    print "WINDOW SIZE", Window.size, Window.size[0], Window.size[1]
    print " "
    # incoming_rssi = StringProperty("0")
    pp = pprint.PrettyPrinter(indent=4)
    status_label_text = StringProperty("[color=a9a98c]Appix is ready. Waiting for signal.[/color]")
    incoming_rssi = StringProperty("None")
    incoming_scan = StringProperty("")

    def __init__(self, **kwargs):
        super(AppixBase, self).__init__(**kwargs)
        self.app = App.get_running_app()

    def start_show(self, *args):
        print "SHOW STARTED"  # , self.app.show_started

    def update_data_labels(self, *args):
        return


    def run_bluetooth_commands(self, decoded_data):
        # print "In from service", decoded_data
        return


class ScreenMessage(RelativeLayout):

    screen_message_image = StringProperty()

    def __init__(self, message, **kwargs):
        super(ScreenMessage, self).__init__(**kwargs)
        self.app = App.get_running_app()
        self.screen_message_image = "assets/%s_message.png" % message


class ExitButton(BoxLayout):

    button_name = StringProperty('exit')

    def __init__(self, **kwargs):
        super(ExitButton, self).__init__(**kwargs)
        self.app = App.get_running_app()
        exit_button = self.add_exit_button()
        self.add_widget(exit_button)

    def add_exit_button(self):

        # print " "
        # print " "
        # print " "
        # print " "
        # print "BUTTON NAME IS", self.button_name
        # print " "
        # print " "

        exit_button = instructions.NavigationButton()
        exit_button.source = "assets/button-%s.png" % self.button_name
        exit_button.bind(on_release=self.exit_app)
        return exit_button

    def exit_app(self, *args):
        self.app.stop()
