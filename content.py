from kivy.app import App
from kivy.uix.scatterlayout import ScatterLayout
from kivy.animation import Animation
from kivy.graphics import Rectangle, Color
from kivy.clock import Clock
from kivy.utils import platform


# import logging
# import logger
# ####### Setup Logging #########
# logger.setup()
# console = logging.getLogger('clogger')
# logging.root.disabled = False


from functools import partial
import random
import json
from math import ceil, modf
from collections import deque
import datetime
import pprint

from animator import ColorTrack, KeyFrame, RectangleTrack, TransformationTrack, RelativeAttributeTrack, Animator, Expr

# platform specific variables
if platform == 'ios' or platform == 'android':
    from kivy.core.window import Window
    window_width = Window.width
    window_height = Window.height
    window_position = (0, 0)
else:
    window_width = 200
    window_height = 300
    window_position = (5, 5)

class SolidContent(ScatterLayout):

    def __init__(self, **kwargs):
        super(SolidContent, self).__init__(**kwargs)
        self.app = App.get_running_app()
        color_json_data = open('media/colors.json')
        self.color_palette = json.load(color_json_data)
        color_json_data.close()
        self.do_rotation = False
        self.do_translation = False
        self.do_scale = False
        self.auto_bring_to_front = False
        self.window_width = window_width
        self.window_height = window_height
        self.window_position = window_position

        # Todo: take these from the solid number total
        # 0: scene is stopped
        # 1: scene is playing regularly (play button down and white)
        # 2: scene is waiting to play regularly, but hasn't started yet (play button down and black)
        # 3: scene is playing as phrased and will stop (phrase button is down and white)
        # 4: scene is waiting to play phrased and will stop (phrase button down and black)
        self.scenes_running = [0] * 100
        self.scheduled_color_data = [''] * 100
        self.flash_running = 0
        self.scheduled_flash_data = {}
        self.layers = [''] * 100    # Todo: take these from the solid number total
        self.animations = [''] * 100  # Todo: take these from the solid number total


        self.note_length_values = [0, 0.015625,  0.03125, 0.0625, 0.125, 0.25, 0.5, 1, 2, 4, 8, 16, 32, 64]
        # self.effect_option_values = [0, 0.015625,  0.03125, 0.0625, 0.125, 0.25, 0.5, 1, 2, 4, 8, 16, 32, 64]

        self.effect_option_values = [100, 90, 80, 70, 60, 50, 40, 30, 20, 10, 5, 0]
        self.blink_fill_option_values = [3, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90]
        self.bpm = 120
        # Phone Only -------------------
        self.heartbeats_since_bpm_reset = 0
        self.beat_mode = 2
        self.active_bars = 4
        self.time_between_first_beats = (60/float(self.bpm)*4)*1000
        self.time_signature = 4
        self.bar_offset = 0
        self.last_first_beat = datetime.datetime.now()
        self.this_first_beat = datetime.datetime.now()
        self.earliest_difference_offset = 0
        self.scene_playing = False  # used for adding and removing the status label appropriately.
        self.scene_order = []


        self.pp = pprint.PrettyPrinter(indent=4)


    # ###################### SOLID CONTENT CREATION ################################



    def remove_blink_duplicates(self, seq):
        seen = set()
        seen_add = seen.add
        return [x for x in seq if not (x in seen or seen_add(x))]


    def remove_gradient_duplicates(self, seq):
        unique_set = []
        for i in range(0, len(seq)-1):
            if str(seq[i]) != str(seq[i+1]):
                unique_set.append(seq[i])
        if str(seq[-1]) != str(seq[-2]):
            unique_set.append(seq[-1])
        return unique_set


    def calculate_loop_extensions(self, data):
        """
        Calculate and return the number of cycles required for both gradient and blink animation loops, along with
        the full duration required.

        :param data: UI data values
        :return: a list with [<gradient_cycles>, <blink_cycles>, <full_duration>]
        """
        gradient_speed = float(self.note_length_values[data["gradient_speed"]])*2
        blink_speed = float(self.note_length_values[data["blink_speed"]])
        blink_cycles = 1
        gradient_cycles = 1

        full_duration = gradient_speed * 60 / float(self.bpm) * 4

        if blink_speed:
            if gradient_speed > blink_speed:
                blink_cycles = int(gradient_speed / blink_speed)
                full_duration = blink_cycles * blink_speed * 60 / float(self.bpm) * 4
                # blink_cycles # -= 1
            elif gradient_speed < blink_speed:
                gradient_cycles = int(blink_speed / gradient_speed)
                full_duration = gradient_cycles * gradient_speed * 60 / float(self.bpm) * 4

        return gradient_cycles, blink_cycles, full_duration


    def round_thirds(self, num):
        frac, whole = modf(num)
        if 32 <= int(frac*100) <= 34:
            value = whole + 0.33
            return value
        elif 65 <= int(frac*100) <= 67:
            value = whole + 0.67
            return value
        elif int(frac*100) == 0 or int(frac*100) == 1:
            value = float(whole)
            return value
        else:
            return num


    def rendered_color(self, color_id):
        """
        Returns the rendered RGBA color for the given color_id
        :param color_id: the color ID in the color_palette dict
        :return: the rgba color tuple
        """
        return tuple([round(float(x)/255, 2) for x in self.color_palette['color'][str(color_id)]])


    def adjust_keyframe_offsets(self, keyframes, offset, offset_start=False):
        """
        Offset the KeyFrame times in the list, keeping the same total duration.
        Assumes the offset is a reasonable value.

        This modifies the original list.

        TODO: value checking on the offset

        :param keyframes: list of KeyFrame objects
        :param offset: decimal, the amount to offset each frame, can be positive or negative
        :return: the modified list
        """

        if len(keyframes) < 3 or offset == 0.0:
            # nothing to offset
            return

        start = keyframes[0].at
        end = keyframes[-1].at

        for i in range(0, len(keyframes)):
            kf = keyframes[i]
            if (offset_start or kf.at > start) and kf.at < end:
                if kf.at + offset <= end:
                    kf.at += offset
                    if kf.at < 0.0:
                        kf.at = 0.0
                else:
                    kf.at = end

        return keyframes


    def play_solid_scene(self, data, *args):

        # print " "
        # print "BUILDING SCENE", data
        # print " "

        if platform == 'ios' or platform == 'android':
            self.app.appix_base.clear_all_labels()
            self.app.appix_base.event_manager.sports_manager.stop_sports_scene()
        else:
            try:
                self.window_width = self.app.main_stage.ids["content_stencil"].width
                self.window_height = self.app.main_stage.ids["content_stencil"].height
            except AttributeError:
                pass

        # print "BPM ----------> ", self.bpm

        # if platform == 'ios' or platform == 'android':
            # self.app.appix_base.clear_all_labels()

        self.scene_playing = True   # Needed for labels on phone

        scene_num = int(data['scene_num'])

        if self.layers[scene_num]:
            self.stop_solid_scene(data)

        element_layout = ScatterLayout(do_rotation=False, do_translation=False, do_scale=False)
        element_layout.auto_bring_to_front = False
        element_layout.width = self.window_width   # * element_settings['size_x']
        element_layout.height = self.window_height  # * element_settings['size_y']
        self.layers[scene_num] = element_layout

        gradient_cycles, blink_cycles, full_duration = self.calculate_loop_extensions(data)

        if len(data["color_ids"]) == 1:
            color = self.rendered_color(data["color_ids"][0])
            color_key_frames = [KeyFrame(at=0, rgba=color),
                                KeyFrame(at=full_duration, rgba=color)]
        else:
            original_color_length = len(data["color_ids"])
            color_key_frames = self.build_gradient_parameters(data, original_color_length, gradient_cycles, full_duration)


        if data["blink_speed"]:
            blink_key_frames, blink_random_offset = self.build_blink_parameters(data, blink_cycles)
        else:
            blink_key_frames = [KeyFrame(at=0, opacity=1), KeyFrame(at=full_duration, opacity=1)]
            blink_random_offset = 0
        # TODO: END BLINK CODE HERE


        track = (ColorTrack(
            RectangleTrack(
                KeyFrame(at=0., pos=Expr("widget.pos"), size=Expr("widget.size")),
                KeyFrame(at=full_duration, pos=Expr("widget.x, widget.y")),
                canvas="before"
            ),

            *color_key_frames,
            canvas="before"
        ),
            RelativeAttributeTrack(
                *blink_key_frames
            ),
        )

        # Offset the start time
        # TODO: this will also offset the start of the gradients animation - probably don't want this?
        # Clock.schedule_once(partial(self.start_animation, track, scene_num), blink_random_offset)
        self.start_animation(track, scene_num)


    def start_animation(self, track, scene_num, *args):

        # print " "
        # print "STARTING ANIMATION"
        # print " "

        my_animator = Animator(*track)
        my_animator.loop = True
        self.animations[scene_num] = my_animator

        try:
            self.layers[scene_num].opacity = 0  # or 0 to start off
            my_animator.do(self.layers[scene_num])
            if platform == 'ios' or platform == 'android':
                self.app.appix_base.solid_layer.add_widget(self.layers[scene_num])
            else:
                self.app.main_stage.ids["content_preview"].add_widget(self.layers[scene_num])
        except AttributeError:
            "this was an attribute error"
            pass


    def build_gradient_parameters(self, data, original_color_length, gradient_cycles, full_duration, *args):

        # Extend the colours list according to the number of cycles
        data["color_ids"].extend(data["color_ids"] * gradient_cycles)

        base_frame_time = (60 / float(self.bpm) * 4) * 2   # TODO Because we're dealing with 2 colors at a time

        gradient_bar_length = float(self.note_length_values[data["gradient_speed"]])
        gradient_a_percent = float(self.effect_option_values[data["gradient_a"]]) / 100
        gradient_b_percent = float(self.effect_option_values[data["gradient_b"]]) / 100

        gradient_full_duration = (gradient_cycles * gradient_bar_length * base_frame_time) / len(data['color_ids'])

        gradient_a_duration = gradient_a_percent * gradient_full_duration
        hold_duration = gradient_full_duration - gradient_a_duration
        gradient_b_duration = gradient_b_percent * gradient_full_duration
        hold_b_duration = gradient_full_duration - gradient_b_duration

        key_frames = []
        color_ids = data['color_ids']

        if data["play_type"] in [1, 3]:
            gradient_random_offset = random.uniform(-gradient_full_duration/2, gradient_full_duration/2)
            gradient_random_offset = ceil(round(gradient_random_offset, 3)*100)/100
            random_color_shift = random.randint(0, original_color_length-1)
            d = deque(color_ids)
            d.rotate(random_color_shift)
            color_ids = list(d)
        else:
            gradient_random_offset = 0.0

        color = self.rendered_color(color_ids[0])

        key_frames.append(KeyFrame(at=0.0, rgba=color))

        for i in range(0, len(color_ids), 2):

            offset = self.round_thirds(ceil(round((gradient_full_duration * i), 3)*100)/100)

            # HOLD COLOR A
            color = self.rendered_color(color_ids[i])
            key_frames.append(KeyFrame(at=offset, rgba=color))

            color_a_stop = self.round_thirds(round(offset + hold_duration, 2))
            key_frames.append(KeyFrame(at=color_a_stop, rgba=color))

            # GRADIENT FROM COLOR A TO COLOR B
            gradient_a_stop = self.round_thirds(round(offset + hold_duration + gradient_a_duration, 2))
            color = self.rendered_color(color_ids[(i+1) % (len(color_ids))])
            key_frames.append(KeyFrame(at=gradient_a_stop, rgba=color))

            # We only need this transition if we are not yet at the end
            if (i+1) < len(color_ids):

                # HOLD COLOR B
                color_b_stop = self.round_thirds(round(offset + hold_duration + gradient_a_duration + hold_b_duration, 2))
                key_frames.append(KeyFrame(at=color_b_stop, rgba=color))

                # GRADIENT FROM COLOR B TO NEXT (OR FIRST) COLOR
                gradient_b_stop = self.round_thirds(round(offset + hold_duration + gradient_a_duration + hold_b_duration + gradient_b_duration, 2))
                color = self.rendered_color(color_ids[(i+2) % len(color_ids)])
                key_frames.append(KeyFrame(at=gradient_b_stop, rgba=color))

        clean_key_frames = self.remove_gradient_duplicates(key_frames)

        self.adjust_keyframe_offsets(clean_key_frames, gradient_random_offset)

        return clean_key_frames



    def build_blink_parameters(self, data, blink_cycles, *args):
        """
        Create the Blink animation KeyFrames.

        :param data: dict settings
        :param blink_cycles: number of blink iterations to generate
        :return: tuple with (list of KeyFrames, random_offset value)
        """

        # Blink Settings
        play_type = data["play_type"]
        blink_speed = self.note_length_values[data["blink_speed"]]
        blink_fill_ratio = float(self.blink_fill_option_values[data["blink_fill"]]) / 100
        blink_in_ratio = float(self.effect_option_values[data["blink_in"]]) / 100
        blink_out_ratio = float(self.effect_option_values[data["blink_out"]]) / 100

        # The full duration of the animation
        blink_duration = (60 / float(self.bpm) * 4) * blink_speed
        # The time the the blink is 'on', including fade in and out
        blink_fill_duration = blink_duration * blink_fill_ratio
        # Time for fade in
        blink_in_duration = blink_fill_duration/2 * blink_in_ratio
        # Time for fade out
        blink_out_duration = blink_fill_duration/2 * blink_out_ratio
        # Blink is fully on for remainder of fill time
        blink_on_duration = blink_fill_duration - (blink_in_duration + blink_out_duration)
        # The 'off' time, which is the everything outside of the fill
        blink_off_duration = blink_duration - blink_fill_duration
        # Random offset
        blink_random_offset = 0.0

        if play_type in [2, 3]:
            # In order to have a random start time, but still show the full animation, we only have the time the blink
            # is 'off' to work with.
            # Example:
            #  - If the fill is 5%, have 95% of the range that we can shift within.
            #  - If the fill is 90%, we can only randomly shift forward or back 10% of total animation time.
            max_offset = blink_off_duration
            blink_random_offset = random.uniform(0, max_offset-0.001)

        key_frames = list([KeyFrame(at=0, opacity=0)])

        for i in range(0, int(blink_cycles)):
            duration_modifier = round(i*blink_duration, 2)
            key_frames.append(KeyFrame(at=round(duration_modifier + blink_in_duration, 2), opacity=1, easing="linear"))
            key_frames.append(KeyFrame(at=round(duration_modifier + blink_in_duration + blink_on_duration, 2), opacity=1, easing="linear"))
            key_frames.append(KeyFrame(at=round(duration_modifier + blink_in_duration + blink_on_duration + blink_out_duration, 2), opacity=0, easing="linear"))
            key_frames.append(KeyFrame(at=round(duration_modifier + blink_in_duration + blink_on_duration + blink_out_duration + blink_off_duration, 2), opacity=0, easing="linear"))

        unique_frames = self.remove_blink_duplicates(key_frames)

        # Introduce random offset
        self.adjust_keyframe_offsets(unique_frames, blink_random_offset, True)

        # After adjustments, make sure we have a proper starting point.
        if unique_frames[0].at > 0.0:
            unique_frames.insert(0, KeyFrame(at=0.0, opacity=0))

        return unique_frames, blink_random_offset



    def stop_solid_scene(self, data, *args):
        try:
            scene_num = data['scene_num']
            if self.animations[scene_num] != '':
                self.animations[scene_num].executors[0].stop()
                self.animations[scene_num] = ''

            if self.layers[scene_num] != '':
                if platform == 'ios' or platform == 'android':
                    self.app.appix_base.solid_layer.remove_widget(self.layers[scene_num])
                    if scene_num == self.app.appix_base.event_manager.sports_manager.sports_strip_number:
                        self.app.appix_base.event_manager.sports_manager.clear_logo_and_number()
                else:
                    self.app.main_stage.ids["content_preview"].remove_widget(self.layers[scene_num])
                self.layers[scene_num] = ''
            open_scenes = False
            for i in range(0, len(self.layers)):
                if self.layers[i] != '':
                    open_scenes = True
            if not open_scenes:
                self.scene_playing = False

        except IndexError as e:
            # print e
            pass


    # 0: scene is stopped
    # 1: scene is playing regularly (play button down and white)
    # 2: scene is waiting to play regularly, but hasn't started yet (play button down and black)
    # 3: scene is playing as phrased and will stop (phrase button is down and white)
    # 4: scene is waiting to play phrased and will stop (phrase button down and black)

    def phrase_all(self, *args, **kwargs):
        if self.beat_mode == 0:
            self.clear_stage()
        else:
            for i in range(0, len(self.scenes_running)):
                if self.scenes_running[i] == 1:
                    self.scenes_running[i] = 3
                elif self.scenes_running[i] in [2, 4]:
                    self.scenes_running[i] = 0
                    self.scheduled_color_data[i] = ''

            # print " "
            # print "SCENES RUNNING"
            # print self.scenes_running

            if self.flash_running == 1:
                self.flash_running = 3
            elif self.flash_running in [2, 4]:
                self.flash_running = 0
                self.stop_flash()
            self.scheduled_flash_data = {}
            # print "Phrased All Flash"
            # print "flash running", self.flash_running


    def clear_stage(self, *args, **kwargs):

        self.scene_playing = False

        for i in range(0, len(self.animations)):
            if self.animations[i] != '':
                self.animations[i].executors[0].stop()
                self.animations[i] = ''

        self.app.appix_base.solid_layer.clear_widgets()
        self.app.appix_base.event_manager.remove_event_image()
        self.app.appix_base.event_manager.sports_manager.clear_logo_and_number()
        self.app.appix_base.event_manager.sponsor_manager.remove_sponsor_image()

        for i in range(0, len(self.layers)):
            self.layers[i] = ''
            self.scenes_running[i] = 0
            self.scheduled_color_data[i] = ''

        self.flash_running = 0
        self.scheduled_flash_data = {}
        self.stop_flash()




    # 0: scene is stopped
    # 1: scene is playing regularly (play button down and white)
    # 2: scene is waiting to play regularly, but hasn't started yet (play button down and black)
    # 3: scene is playing as phrased and will stop (phrase button is down and white)
    # 4: scene is waiting to play phrased and will stop (phrase button down and black)

    def schedule_play_data(self, data):

        # print " "
        # print "SCHEDULING DATA"
        # print " "

        scene_num = data['scene_num']

        # print " "
        # print "Scheduling data:"
        # print "pre self.scenes_running", self.scenes_running

        if data['message_type'] == 2:
            # if self.scenes_running[scene_num] == 1:
            self.scheduled_color_data[scene_num] = data
            self.scenes_running[scene_num] = 2

        elif data['message_type'] == 3:
            if self.scenes_running[scene_num] in [1]:
                self.scenes_running[scene_num] = 3
            elif self.scenes_running[scene_num] in [0, 2, 3]:
                self.scheduled_color_data[scene_num] = data
                self.scenes_running[scene_num] = 4

        if scene_num in self.scene_order:
            self.scene_order.remove(scene_num)
        self.scene_order.append(scene_num)

        # print "post self.scenes_running", self.scenes_running
        # print " "
        # print " "


    def commit_scenes(self):

        # print " "
        # print "committing here"
        # print "COMMIT DATA", self.scheduled_color_data
        # print " "

        commit_order = list(self.scene_order)
        commit_data = list(self.scheduled_color_data)
        self.scene_order = []

        for i in range(0, len(self.scenes_running)):

            if self.scenes_running[i] == 3:
                self.scenes_running[i] = 0
                data = {'scene_num': i}
                self.stop_solid_scene(data)
                # self.app.appix_base.sports_manager.stop_sports_scene()

        for i in range(0, len(commit_order)):

            if self.scenes_running[commit_order[i]] == 2:
                self.scenes_running[commit_order[i]] = 1
                if commit_data[commit_order[i]]:
                    try:
                        self.play_solid_scene(commit_data[commit_order[i]])
                    except IndexError:
                        print "SAVED FROM BAD BEACON DATA"
                        pass
                else:
                    pass
                    # print "saved from no data in play"
                self.scheduled_color_data[commit_order[i]] = ''

            elif self.scenes_running[commit_order[i]] == 4:
                self.scenes_running[commit_order[i]] = 3
                if commit_data[commit_order[i]]:
                    try:
                        self.play_solid_scene(commit_data[commit_order[i]])
                    except IndexError:
                        print "SAVED FROM BAD BEACON DATA"
                        pass
                else:
                    pass
                    # print "saved from no data in phrase"
                self.scheduled_color_data[commit_order[i]] = ''



# #####################  FLASH CONTROL  ##########################


    # 0: scene is stopped
    # 1: scene is playing regularly (play button down and white)
    # 2: scene is waiting to play regularly, but hasn't started yet (play button down and black)
    # 3: scene is playing as phrased and will stop (phrase button is down and white)
    # 4: scene is waiting to play phrased and will stop (phrase button down and black)

    def commit_flash(self):

        # print " "
        # print "committing flash", self.flash_running
        # print 'data', self.scheduled_flash_data
        # print " "

        if self.flash_running == 3:
            self.flash_running = 0
            self.stop_flash()

        elif self.flash_running == 2:
            self.flash_running = 1
            try:
                Clock.schedule_once(partial(self.play_flash, self.scheduled_flash_data), 0.005)
            except TypeError:
                print "saved from no data in play flash"
            self.scheduled_flash_data = {}


        elif self.flash_running == 4:
            self.flash_running = 3
            try:
                Clock.schedule_once(partial(self.play_flash, self.scheduled_flash_data), 0.005)
            except TypeError:
                print "saved from no data in phrase flash"
            self.scheduled_flash_data = {}



    def play_flash(self, data, *args):

        # print "FLASH MODE: ", self.flash_mode
        # print " "
        # print "CONTENT FLASH DATA"
        # print data
        # print " "

        Clock.unschedule(self.schedule_blinks)
        Clock.unschedule(self.scheduled_blink_on)
        Clock.unschedule(self.scheduled_blink_off)
        # print "before flash off"
        self.app.flash_torch.flash(False)
        # print "after flash off"

        blink_speed = self.note_length_values[data["blink_speed"]]
        # print "BLINK SPEED", blink_speed

        if blink_speed != 0:
            # bpm = self.solid_layer.bpm
            # print "BPM:", self.bpm
            blink_fill = self.blink_fill_option_values[data["blink_fill"]]
            # print "BLINK FILL:", blink_fill
            self.blink_hold_duration = blink_speed * 60 / float(self.bpm) * 4
            # print "BLINK HOLD DURATION:", self.blink_hold_duration
            self.blink_hold_on_duration = float(self.blink_hold_duration) * (float(blink_fill)/100)
            # print "BLINK HOLD ON DURATION:", self.blink_hold_on_duration
            self.blink_random_offset = random.uniform(0, self.blink_hold_duration) if data["blink_random"] == 1 else 0
            # print "BLINK RANDOM OFFSET:", self.blink_random_offset
            Clock.schedule_once(self.schedule_blinks, self.blink_random_offset)
        else:
            self.app.flash_torch.flash(True)


    def schedule_blinks(self, *args):
        self.app.flash_torch.flash(True)
        Clock.schedule_interval(self.scheduled_blink_on, self.blink_hold_duration)
        Clock.schedule_once(self.scheduled_blink_off, self.blink_hold_on_duration)

    def scheduled_blink_on(self, *args):
        Clock.schedule_once(self.scheduled_blink_off, self.blink_hold_on_duration)
        self.app.flash_torch.flash(True)

    def scheduled_blink_off(self, *args):
        self.app.flash_torch.flash(False)

    def stop_flash(self, *args):
        # print " "
        # print "STOPPING FLASH"
        # print " "
        Clock.unschedule(self.schedule_blinks)
        Clock.unschedule(self.scheduled_blink_on)
        Clock.unschedule(self.scheduled_blink_off)
        self.app.flash_torch.flash(False)
        if platform == 'android':
            self.app.flash_torch.release()



# #####################  TIMING CONTROL  ##########################


    def play_initial_beat(self, *args):
        self.commit_scenes()
        self.commit_flash()
        Clock.schedule_interval(self.start_beat_event, 0)

    def start_beat_event(self, dt):
        now = Clock.get_time()
        if not self.start_time:
            self.start_time = now
            self._start_time = now
        beat = now - self.start_time
        if beat > self.time_between_first_beats:
            self.start_time = now
            try:
                self.start_time -= (now - self._start_time) % self.time_between_first_beats
                # print "now", now
                # print "self._start_time", self._start_time
                # print "self.start_time", self.start_time
                # print "self.time_between_first_beats", self.time_between_first_beats
                self.on_beat()
            except ZeroDivisionError:
                print " "
                print " "
                print " "
                print "saved from ZeroDivisionError in start_beat_event()"
                print "now", now
                print "self._start_time", self._start_time
                print "self.start_time", self.start_time
                print "self.time_between_first_beats", self.time_between_first_beats
                print " "
                print " "
                print " "



    def on_beat(self):
        self.commit_scenes()
        self.commit_flash()



    def set_first_beat(self, offset, heartbeats_since_reset, *args):

        Clock.unschedule(self.play_initial_beat)
        Clock.unschedule(self.start_beat_event)

        if self.beat_mode > 1:
            self.active_bars = self.beat_mode - 1

        self.time_between_first_beats = (60/float(self.app.appix_base.solid_layer.bpm)*self.time_signature)
        if 2 <= self.beat_mode <= 10:
            self.time_between_first_beats *= self.active_bars

        first_offset = self.time_between_first_beats - float(offset)/1000

        # ########## MESSAGE OFFSET ALGORITHM ################

        # print "FIRST OFFSET        ", first_offset
        self.this_first_beat = datetime.datetime.now() + datetime.timedelta(seconds=first_offset)
        # print "NOW                ", datetime.datetime.now()
        # print "LAST FIRST BEAT WAS", self.last_first_beat
        # print "THIS FIRST BEAT WAS", self.this_first_beat
        # print "PROPER TIME BB     ", self.time_between_first_beats
        time_between_beat_ones = self.this_first_beat - self.last_first_beat

        #  print "ACTUAL TIME BB      ", time_between_beat_ones.total_seconds()
        difference_offset = time_between_beat_ones.total_seconds() - self.time_between_first_beats
        # print " "
        # print "ORIGINAL DIFF OFFSET", difference_offset
        # print " "

        difference_offset = 0 if difference_offset > 0 else difference_offset

        # print "NEW HEARTBEAT NUM   ", heartbeats_since_reset
        # print "LAST HEARTBEAT NUM  ", self.heartbeats_since_bpm_reset
        # print "DIFFERENCE OFFSET   ", difference_offset

        if self.heartbeats_since_bpm_reset > heartbeats_since_reset or self.heartbeats_since_bpm_reset == 0:
            self.earliest_difference_offset = 0

        if difference_offset < self.earliest_difference_offset and not abs(difference_offset) > 0.5:
            self.earliest_difference_offset = difference_offset

        # print "EARLIEST OFFSET     ", self.earliest_difference_offset
        self.earliest_difference_offset = 0   # TODO: <---------------------- this overrides the offset algorithm for now
        # ########## MESSAGE OFFSET ALGORITHM ################

        self.start_time = 0.
        Clock.schedule_once(self.update_last_first_beat, first_offset - abs(self.earliest_difference_offset))
        Clock.schedule_once(self.play_initial_beat, first_offset - abs(self.earliest_difference_offset))
        self.heartbeats_since_bpm_reset = heartbeats_since_reset
        # print " "
        # print " "


    def update_last_first_beat(self, *args):
        self.last_first_beat = self.this_first_beat

