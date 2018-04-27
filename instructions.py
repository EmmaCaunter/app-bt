from kivy.app import App
from kivy.uix.carousel import Carousel
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.relativelayout import RelativeLayout
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.utils import platform
from kivy.uix.widget import WidgetException
from kivy.uix.label import Label
from functools import partial



# ---------------------------------------------------------------------------------
class InstructionContainer(RelativeLayout):

    pass


# ---------------------------------------------------------------------------------
class InstructionPages(Carousel):

    def __init__(self, *args, **kwargs):
        super(InstructionPages, self).__init__(*args, **kwargs)
        self.app = App.get_running_app()
        self.min_move = 0.1
        self.direction = "right"
        self.loop = True
        self.anim_move_duration = 0.1
        self.create_instruction_pages()

    def create_instruction_pages(self):
        source = list()
        source.append("assets/instruction-pg-2.png")
        source.append("assets/instruction-pg-3.png")
        source.append("assets/instruction-pg-4.png")

        layout = BoxLayout(padding=[self.width/4, self.width/3, self.width/4, self.width/3])
        layout.add_widget(NavigationButton(source="assets/button-enter-large.png", size_hint=(1, 1),
                                           on_press=self.start_show, allow_stretch=True,
                                           keep_ratio=True))
        self.add_widget(layout)
        for src in source:
            self.add_widget(Image(source=src, allow_stretch=True, keep_ratio=True))

    # def navigate(self, direction):
    #     if direction == 'prev':
    #         self.load_previous()
    #     else:
    #         self.load_next()

    def start_show(self, *args):
        self.app.root.ids.instruction_navigation.check_bluetooth_to_start()

        # if platform == 'android':

        #     self.app.appix_base.start_show()
        # else:
            # self.check_bluetooth_to_start()
            # print " "
            # print "SHOW SHOULD START HERE ONLY IF BLUETOOTH IS ON, OTHERWISE THE NOTIFY AGAIN."
            # print " "
            # self.app.appix_base.start_show()


    # def check_bluetooth_to_start(self, *args):
    #     self.app.root.ids.instruction_navigation.check_bluetooth_to_start()


# ---------------------------------------------------------------------------------
class InstructionNavigation(BoxLayout):

    def __init__(self, *args, **kwargs):
        super(InstructionNavigation, self).__init__(*args, **kwargs)
        self.id = "navigation_instructions"
        self.app = App.get_running_app()
        self.add_widget(self.add_instruction_button())
        self.back_next_present = False

    def add_back_button(self):
        back_button = NavigationButton()
        back_button.id = "back_button"
        back_button.source = "assets/button-left.png"
        back_button.bind(on_release=partial(self.navigate, 'prev'))
        return back_button

    def add_next_button(self):
        next_button = NavigationButton()
        next_button.id = "next_button"
        next_button.source = "assets/button-right.png"
        next_button.bind(on_release=partial(self.navigate, 'next'))
        return next_button
#
    def add_instruction_button(self):
        self.instruction_button = NavigationButton()
        self.instruction_button.id = "instruction_button"
        self.instruction_button.source = "assets/button-instructions.png"
        self.instruction_button.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.instruction_button.bind(on_release=partial(self.navigate, 'next'))
        return self.instruction_button

    def add_back_next(self):
        self.back_next = BoxLayout(orientation="horizontal")
        self.back_next.add_widget(self.add_back_button())
        self.back_next.add_widget(Label(size_hint_x=None, width=30))
        self.back_next.add_widget(self.add_next_button())
        self.back_next.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        return self.back_next

    def navigate(self, direction, *args):
        if direction == 'prev':
            self.app.root.ids.instruction_pages.load_previous()
        elif direction == 'next':
            self.app.root.ids.instruction_pages.load_next()

    def update_navigation(self, index):
        if index == 0:
            try:
                self.remove_widget(self.back_next)
                self.back_next_present = False
            except AttributeError:
                pass
            self.add_widget(self.add_instruction_button())

        elif index in [1, 2, 3]:
            try:
                self.remove_widget(self.instruction_button)
                if not self.back_next_present:
                    self.add_widget(self.add_back_next())
                    self.back_next_present = True
            except (AttributeError, WidgetException):
                pass

    # def start_show(self):
    #     self.app.appix_base.start_show()

    def check_bluetooth_to_start(self, *args):
        if platform == 'android':
            # pass
            # self.app.bluetooth_dialog_open = True
            from service.bt import android_bluetooth
            android_bluetooth.check_bluetooth_enabled(False)
            # self.app.comm_layer.send_message('check_bluetooth_enabled')
            # self.app.appix_base.start_show()
            # self.app.bluetooth_dialog_open = False
        elif platform == 'ios':
            self.app.ios_bluetooth.start_button_pressed = True
            self.app.ios_bluetooth.check_bluetooth_enabled()


    def test_flash(self, *args):
        # print "testing flash"
        Clock.schedule_once(self.app.root.ids.instruction_demo.run_flash_demo, 0.01)
        # self.app.root.ids.instruction_demo.run_flash_demo()

    def test_screen(self, *args):
        # print "testing screen"
        self.app.root.ids.instruction_demo.run_screen_demo()


# ---------------------------------------------------------------------------------
class NavigationButton(ButtonBehavior, Image):
    pass


# ---------------------------------------------------------------------------------
class InstructionDemo(FloatLayout):

    def __init__(self, **kwargs):
        super(InstructionDemo, self).__init__(**kwargs)
        self.app = App.get_running_app()
        self.element_layout = FloatLayout()
        self.flash_demo_running = False

    def hide_instructions(self):
        self.app.root.ids.instruction_container.x = -self.app.root.ids.instruction_container.width

    def show_instructions(self, *args):
        self.app.root.ids.instruction_container.x = 0

    def show_stage_color(self, color, *args):
        c = Color(*color)
        self.element_layout.canvas.add(c)
        self.element_layout.canvas.add(Rectangle(size=self.size))
        try:
            self.add_widget(self.element_layout, 2)
        except WidgetException:
            self.remove_stage_color()

    def remove_stage_color(self, *args):
        self.remove_widget(self.element_layout)

    def run_screen_demo(self):
        self.hide_instructions()
        # Clock.schedule_once(self.app.appix_base.engage_dim_logo, 0.01)
        self.app.appix_base.status_label.text = "[color=4e5254]Appix screen color demonstration.[/color]"
        Clock.schedule_once(partial(self.app.appix_base.vibrate_warning, 2), 0.1)
        Clock.schedule_once(partial(self.show_stage_color, (0.94, 0.59, 0.03)), 1.75)
        Clock.schedule_once(self.remove_stage_color, 2.0)
        Clock.schedule_once(partial(self.show_stage_color, (0.14, 0.41, 0.83)), 2.25)
        Clock.schedule_once(self.remove_stage_color, 2.5)
        Clock.schedule_once(partial(self.show_stage_color, (1, 1, 1)), 2.75)
        Clock.schedule_once(self.remove_stage_color, 3)
        Clock.schedule_once(partial(self.show_stage_color, (0.94, 0.59, 0.03)), 3.25)
        Clock.schedule_once(self.remove_stage_color, 3.5)
        Clock.schedule_once(partial(self.show_stage_color, (0.14, 0.41, 0.83)), 3.75)
        Clock.schedule_once(self.remove_stage_color, 4)
        Clock.schedule_once(partial(self.show_stage_color, (1, 1, 1)), 4.25)
        Clock.schedule_once(self.remove_stage_color, 4.5)
        Clock.schedule_once(partial(self.app.appix_base.vibrate_warning, 1), 4.75)
        Clock.schedule_once(self.reset_status_label_text, 4.8)
        Clock.schedule_once(self.show_instructions, 4.85)

    def reset_status_label_text(self, *args):
        self.app.appix_base.status_label.text = self.app.appix_base.status_label_text

    def run_flash_demo(self, *args):
        if not self.flash_demo_running:
            self.hide_instructions()
            self.app.appix_base.status_label.text = "[color=4e5254]Appix flash demonstration.[/color]"
            Clock.schedule_once(self.app.appix_base.add_flash_label, 0.01)
            self.flash_demo_running = True
            Clock.schedule_once(partial(self.app.appix_base.vibrate_warning, 3), 0.1)
            Clock.schedule_once(partial(self.app.flash_torch.flash, True), 3.5)
            Clock.schedule_once(partial(self.app.flash_torch.flash, False), 3.7)
            Clock.schedule_once(partial(self.app.flash_torch.flash, True), 3.9)
            Clock.schedule_once(partial(self.app.flash_torch.flash, False), 4.1)
            Clock.schedule_once(partial(self.app.flash_torch.flash, True), 4.3)
            Clock.schedule_once(partial(self.app.flash_torch.flash, False), 4.5)
            Clock.schedule_once(partial(self.app.flash_torch.flash, True), 4.7)
            Clock.schedule_once(partial(self.app.flash_torch.flash, False), 4.9)
            Clock.schedule_once(partial(self.app.flash_torch.flash, True), 5.1)
            Clock.schedule_once(partial(self.app.flash_torch.flash, False), 5.3)
            Clock.schedule_once(partial(self.app.flash_torch.flash, True), 5.7)
            Clock.schedule_once(partial(self.app.flash_torch.flash, False), 6.7)
            Clock.schedule_once(partial(self.app.appix_base.vibrate_warning, 1), 7.2)
            Clock.schedule_once(self.finish_flash_demo, 8)
            Clock.schedule_once(self.reset_status_label_text, 8.05)
            Clock.schedule_once(self.show_instructions, 8.1)

    def finish_flash_demo(self, *args):
        self.app.appix_base.remove_flash_label()
        self.flash_demo_running = False
