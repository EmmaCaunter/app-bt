# coding=utf-8
"""
Bluetooth Low Energy support using CoreLocation
================================================

iBeacon Scanner
===============

This scanner works exclusively on iOS real devices, simulator don't support
iBeacon ranging API at all.

The usage is quite simple:

0. Add CoreLocation framework to your app (should be done by default),
   and a key `NSLocationAlwaysUsageDescription` to a string value `My app
   want to access to your location`

1. Create a scanner with `scanner = IBeaconScanner()`
2. Register your iBeacon using the ibeacon uuid like:

    scanner.register_beacon("E2C56DB5-DFFB-48D2-B060-D0F5A71096E0")

3. Monitor the event you want

    scanner.bind(on_beacon_update=do_something)

4. Start the scanner

    scanner.start_monitoring()

Output example captured from a test run:

(('on_beacon_entered', <__main__.IBeaconScanner object at 0x1704bd238>), {'uuid': 'E2C56DB5-DFFB-48D2-B060-D0F5A71096E0'})
(('on_beacon_update', <__main__.IBeaconScanner object at 0x1704bd238>), {'rssi': -57, 'proximity': 'near', 'major': 4250, 'minor': 9865, 'uuid': 'E2C56DB5-DFFB-48D2-B060-D0F5A71096E0'})
(('on_beacon_update', <__main__.IBeaconScanner object at 0x1704bd238>), {'rssi': -54, 'proximity': 'near', 'major': 4250, 'minor': 9865, 'uuid': 'E2C56DB5-DFFB-48D2-B060-D0F5A71096E0'})
(('on_beacon_update', <__main__.IBeaconScanner object at 0x1704bd238>), {'rssi': -52, 'proximity': 'immediate', 'major': 4250, 'minor': 9865, 'uuid': 'E2C56DB5-DFFB-48D2-B060-D0F5A71096E0'})
(('on_beacon_update', <__main__.IBeaconScanner object at 0x1704bd238>), {'rssi': -52, 'proximity': 'immediate', 'major': 4250, 'minor': 9865, 'uuid': 'E2C56DB5-DFFB-48D2-B060-D0F5A71096E0'})
(('on_beacon_update', <__main__.IBeaconScanner object at 0x1704bd238>), {'rssi': -53, 'proximity': 'immediate', 'major': 4250, 'minor': 9865, 'uuid': 'E2C56DB5-DFFB-48D2-B060-D0F5A71096E0'})
(('on_beacon_update', <__main__.IBeaconScanner object at 0x1704bd238>), {'rssi': -65, 'proximity': 'immediate', 'major': 4250, 'minor': 9865, 'uuid': 'E2C56DB5-DFFB-48D2-B060-D0F5A71096E0'})
(('on_beacon_update', <__main__.IBeaconScanner object at 0x1704bd238>), {'rssi': -74, 'proximity': 'near', 'major': 4250, 'minor': 9865, 'uuid': 'E2C56DB5-DFFB-48D2-B060-D0F5A71096E0'})
(('on_beacon_update', <__main__.IBeaconScanner object at 0x1704bd238>), {'rssi': -76, 'proximity': 'near', 'major': 4250, 'minor': 9865, 'uuid': 'E2C56DB5-DFFB-48D2-B060-D0F5A71096E0'})
(('on_beacon_update', <__main__.IBeaconScanner object at 0x1704bd238>), {'rssi': -77, 'proximity': 'near', 'major': 4250, 'minor': 9865, 'uuid': 'E2C56DB5-DFFB-48D2-B060-D0F5A71096E0'})
(('on_beacon_update', <__main__.IBeaconScanner object at 0x1704bd238>), {'rssi': -77, 'proximity': 'near', 'major': 4250, 'minor': 9865, 'uuid': 'E2C56DB5-DFFB-48D2-B060-D0F5A71096E0'})
(('on_beacon_leaved', <__main__.IBeaconScanner object at 0x1704bd238>), {'uuid': 'E2C56DB5-DFFB-48D2-B060-D0F5A71096E0'})

"""
from kivy.app import App
from kivy.event import EventDispatcher
from pyobjus import autoclass, protocol

CLLocationManager = autoclass("CLLocationManager")
CLBeaconRegion = autoclass("CLBeaconRegion")
NSUUID = autoclass("NSUUID")

# TODO; place variables below in appropriate places
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty




class CoreLocationScanner(EventDispatcher):
    """
    iBeacon Scanner class that works exclusively on iOS real device.
    """

    PROXIMITY = ["unknown", "immediate", "near", "far"]
    __events__ = ("on_beacon_entered", "on_beacon_update", "on_beacon_leaved",
                  "on_error")
    
    # Appix Specific Variables
    ios_major_minor = ListProperty(["0", "0", "0", "0"])
    ios_mac_address = ListProperty(["0", "0", "0", "0", "0", "0"])

    ios_beacon_reset_flag = "5"
    ios_filter_start_record_flag = StringProperty("10")
    ios_filter_stop_record_flag = StringProperty("15")
    ios_beacon_start_record_flag = StringProperty("20")
    ios_beacon_stop_record_flag = StringProperty("25")
    ios_beacon_start_show_flag = StringProperty("30")
    ios_beacon_stop_show_flag = StringProperty("35")
    ios_send_octave_flag = "40"
    ios_send_blink_data_flag = "50"
    ios_send_color_data_flag = "60"
    ios_engage_color_data_flag = "65"
    ios_toggle_blink_on_flag = "70"
    ios_toggle_blink_off_flag = "72"
    ios_engage_blink_flag = "74"
    ios_toggle_random_on_flag = "76"
    ios_toggle_random_off_flag = "78"
    ios_vibrate_warning_flag = "80"
    ios_toggle_debug_mode_on_flag = "90"
    ios_toggle_debug_mode_off_flag = "92"
    # ios_single_vibrate_flag = "80"
    # ios_double_vibrate_flag = "82"
    # ios_triple_vibrate_flag = "84"


    ios_mode = StringProperty("Standby")
    ios_filtered_list = ListProperty()
    ios_collected_beacon_list = ListProperty()
    ios_master_beacon_list = ListProperty()
    ios_midi_key_list = ListProperty()
    ios_midi_extras_list = ListProperty()
    last_ios_master_beacon_list = ListProperty()
    filtering_started_flag = BooleanProperty(False)   
    recording_started_flag = BooleanProperty(False)
    show_started_flag = BooleanProperty(False)
    reset_iphone_flag = BooleanProperty(False)
    recording_success = BooleanProperty(False)
    midi_checksum = NumericProperty(0)
    current_octave = NumericProperty(0)
    current_note = NumericProperty(0)
    beacon_repeat_count = NumericProperty(0)
    # allow_next_instruction = True
    # End Appix Specific Variables

    def __init__(self):
        super(CoreLocationScanner, self).__init__()
        self.app = App.get_running_app()
        self._regions = {}
        self._regions_nsuuid = {}
        self._regions_seen = []
        self._region_activated = False
        self.last_ios_major_minor = 0
        self.register_beacon("4253A5FC-BF34-4E6D-AC71-B349064EC17F")
        self.start_monitoring()

    # Appix Specific Functions
    def process_beacon_input(self, major, minor):
        self.ios_major_minor = self.decode_major_minor(major, minor)
        if self.app.DEBUG:
            print "self.ios_major_minor", self.ios_major_minor
        # print "self.ios_major_minor", self.ios_major_minor

        # print "low", int(self.ios_send_color_data_flag, 16)
        # print "flag", int(self.ios_major_minor[0])
        # print "high", int(self.ios_send_color_data_flag, 16)+15
        #if self.ios_major_minor != self.last_ios_major_minor:
        if self.ios_major_minor[0] == self.ios_beacon_reset_flag:
            if self.app.DEBUG:
                print "RESET"
            self.ios_mode = 'Standby'
            self.ios_filtered_list = []
            self.ios_master_beacon_list = []
            self.ios_collected_beacon_list = []
            self.filtering_started_flag = False
            self.recording_started_flag = False
            self.show_started_flag = False
            if self.app.show_started:
                self.app.appix_base.status_label.text = "[color=7d8486]Waiting for show data[/color]"
            self.app.appix_base.animation_layer.clear_stage()
            self.app.appix_base.remove_flash_label()

        elif self.ios_major_minor[0] == self.ios_filter_start_record_flag and not self.filtering_started_flag:
            if self.app.DEBUG:
                print "FILTER STARTED"
            self.ios_mode = 'Filtering'
            # self.app.appix_base.animation_layer.clear_stage()
            if self.app.show_started:
                self.app.appix_base.status_label.text = "[color=7d8486]Transmission started[/color]"
            self.filtering_started_flag = True
            self.recording_started_flag = False
            self.show_started_flag = False
            self.beacon_repeat_count = int(self.ios_major_minor[2])
            self.app.appix_base.remove_flash_label()
            Clock.schedule_once(self.stop_filtering, 5)  # Todo: !!!!!!!!!!!!!!!!!!!!!!!!!! tweak as necessary
            if self.ios_major_minor[1] == "1":
                self.ios_filtered_list = []

        elif self.ios_major_minor[0] == self.ios_beacon_start_record_flag and not self.recording_started_flag:
            if self.app.DEBUG:
                print "RECORDING DATA"
            self.ios_mode = 'Recording'
            if self.app.show_started:
                self.app.appix_base.status_label.text = "[color=7d8486]Receiving show data[/color]"
            self.recording_started_flag = True
            self.filtering_started_flag = False
            self.show_started_flag = False
            self.midi_checksum = int(self.ios_major_minor[2])
            self.ios_master_beacon_list = []
            self.ios_collected_beacon_list = []
            self.app.appix_base.remove_flash_label()
            stop_timeout = 8  # Todo: !!!!!!!!!!!!!!!!!!!!!!!!!! tweak as necessary
            Clock.schedule_once(self.stop_recording, stop_timeout)

        elif self.ios_major_minor[0] == self.ios_beacon_start_show_flag and not self.show_started_flag:
            if self.app.DEBUG:
                print "PRESENTING"
            self.ios_mode = 'Presenting'
            if self.app.show_started:
                self.app.appix_base.status_label.text = "[color=3a3e3f]Ready[/color]"
            self.show_started_flag = True
            self.filtering_started_flag = False
            self.recording_started_flag = False
            self.app.appix_base.remove_flash_label()
            self.current_octave = int(self.ios_major_minor[1])

        elif self.ios_major_minor[0] == self.ios_beacon_stop_show_flag and self.show_started_flag:
            if self.app.DEBUG:
                print "STANDBY"
            self.ios_mode = 'Standby'
            if self.app.show_started:
                self.app.appix_base.status_label.text = "[color=7d8486]Standby[/color]"
            self.show_started_flag = False
            self.filtering_started_flag = False
            self.recording_started_flag = False
            self.app.appix_base.animation_layer.clear_stage()
            self.app.appix_base.remove_flash_label()

        elif self.ios_major_minor[0] == self.ios_send_octave_flag:
            self.current_octave = int(self.ios_major_minor[1])

        elif int(self.ios_send_color_data_flag, 16) <= int(self.ios_major_minor[0]) <= int(self.ios_send_color_data_flag, 16)+15:
            self.app.appix_base.animation_layer.receive_color_data(int(self.ios_major_minor[0]),
                                                                   int(self.ios_major_minor[1]),
                                                                   int(self.ios_major_minor[2]),
                                                                   int(self.ios_major_minor[3]))
        elif self.ios_major_minor[0] == self.ios_engage_color_data_flag:
            self.app.appix_base.animation_layer.update_current_fade_id(int(self.ios_major_minor[2]))

        elif self.ios_major_minor[0] == self.ios_send_blink_data_flag:
            self.app.appix_base.animation_layer.queue_blink_info(self.ios_major_minor[1],
                                                                 self.ios_major_minor[2],
                                                                 self.ios_major_minor[3])

        elif self.ios_major_minor[0] == self.ios_toggle_random_on_flag:
            self.app.appix_base.animation_layer.random_blink_mode = True

        elif self.ios_major_minor[0] == self.ios_toggle_random_off_flag:
            self.app.appix_base.animation_layer.random_blink_mode = False

        elif self.ios_major_minor[0] == self.ios_vibrate_warning_flag:
            self.app.appix_base.vibrate_warning(int(self.ios_major_minor[1], 16))

        elif self.ios_major_minor[0] == self.ios_toggle_debug_mode_on_flag:
            self.app.DEBUG = True

        elif self.ios_major_minor[0] == self.ios_toggle_debug_mode_off_flag:
            self.app.DEBUG = False
        #
            # elif self.ios_major_minor[0] == self.ios_toggle_blink_off_flag:
            #     self.app.appix_base.animation_layer.toggle_blink(False)

            # self.last_ios_major_minor = self.ios_major_minor

    def stop_filtering(self, *args):
        if self.app.DEBUG:
            print "FINISHED FILTERING"
        self.ios_mode = 'Standby'
        self.filtering_started_flag = False
        self.show_started_flag = False
        self.recording_started_flag = False
        self.ios_filtered_list = set(self.ios_filtered_list)
        # print self.ios_filtered_list

    def stop_recording(self, *args):
        if self.app.DEBUG:
            print "FINISHED RECORDING"
        self.ios_mode = 'Standby'
        self.recording_started_flag = False
        self.show_started_flag = False
        self.recording_started_flag = False
        # print self.ios_collected_beacon_list
        self.process_collected_beacon_list(self.ios_collected_beacon_list)

    def decode_major_minor(self, major, minor):
        major_hex = format(major, 'x').zfill(4)
        major_list = list(major_hex)
        major_a = major_list[0] + major_list[1]
        major_b = major_list[2] + major_list[3]
        minor_hex = format(minor, 'x').zfill(4)
        minor_list = list(minor_hex)
        minor_a = minor_list[0] + minor_list[1]
        minor_b = minor_list[2] + minor_list[3]
        return str(int(major_a, 16)), str(int(major_b, 16)), str(int(minor_a, 16)), str(int(minor_b, 16))

    def decode_mac_address(self, mac_add):
        pass


    def process_collected_beacon_list(self, collected_beacon_list):

        filtered = False

        for beacon in collected_beacon_list:
            count = collected_beacon_list.count(beacon)
            if count > self.beacon_repeat_count*2:
                collected_beacon_list = filter(lambda a: a != beacon, collected_beacon_list)
                self.ios_filtered_list.append(beacon)
                filtered = True
                # print "this was filtered"

            # print "COUNT:", count
        # print "after collected_beacon_list", collected_beacon_list

        seen = set()
        seen_add = seen.add
        unique_beacon_list = [x for x in collected_beacon_list if not (x in seen or seen_add(x))]

        # TODO: if a device is jamming bluetooth with advertising packets, then we need to catch that as well
        # TODO: because unique_beacon_list will be scrambled (so far on iphone 5)
        # print "filtered", filtered
        # print "self.midi_checksum", self.midi_checksum
        # print "len(unique_beacon_list)", len(unique_beacon_list)

        if len(unique_beacon_list) != self.midi_checksum or filtered is True:
            self.ios_master_beacon_list = self.last_ios_master_beacon_list
            self.recording_success = False
            if self.app.DEBUG:
                print "recording failed"
            if self.app.show_started:
                self.app.appix_base.status_label.text = "[color=7d8486]Standby[/color]"
        else:
            self.ios_master_beacon_list = unique_beacon_list
            self.last_ios_master_beacon_list = self.ios_master_beacon_list
            self.ios_midi_key_list = self.ios_master_beacon_list[:12]
            self.ios_midi_extras_list = self.ios_master_beacon_list[-8:]
            # self.ios_midi_key_list = self.ios_master_beacon_list[:24]
            # self.ios_midi_octave_list = self.ios_master_beacon_list[24:32]
            # self.ios_midi_extras_list = self.ios_master_beacon_list[-4:]
            self.recording_success = True
            if self.app.show_started:
                self.app.appix_base.status_label.text = "[color=7d8486]Show data received[/color]"

            # print " "
            # print "self.ios_master_beacon_list", self.ios_master_beacon_list
            # print " "
            # print "self.ios_midi_key_list", self.ios_midi_key_list
            # print " "
            # print "self.ios_midi_octave_list", self.ios_midi_octave_list
            # print " "
            # print "self.ios_midi_extras_list", self.ios_midi_extras_list
            # print " "

        # print "last_ios_master_beacon_list", self.last_ios_master_beacon_list
        # print " "
        # print "self.ios_master_beacon_list", self.ios_master_beacon_list
        # print " "

    # End Appix Specific Functions




    def on_beacon_entered(self, *largs, **kwargs):
        # print "on_beacon_entered", largs, kwargs
        pass

    def on_beacon_update(self, *largs, **kwargs):
        print " "
        print "on_beacon_update", largs, kwargs
        print " "
        #self.process_beacon_input(kwargs['major'], kwargs['minor'])
        pass

    def on_corelocation_beacon_update(self, cl, **kwargs):
        #print kwargs
        pass

    def on_beacon_leaved(self, *largs, **kwargs):
        # print "on_beacon_leaved", largs, kwargs
        pass

    def on_beacon_error(self, *largs, **kwargs):
        # print "on_beacon_error", largs, kwargs
        pass

    def start_monitoring(self):
        """Start the scanner monitoring"""
        self._clm = CLLocationManager.alloc().init()
        self._clm.allowsBackgroundLocationUpdates = True
        self._clm.delegate = self
        
        status = CLLocationManager.authorizationStatus()
        # 1 restricted
        # 2 denied
        if status in (1, 2):
            # show message and exit app
            # TODO: Show app can not work without bluetooth and exit.
            # stop service here 
            return
        # 3 authorized always
        # 4 authorized whenInUse
        if status in (3, 4):
            return
        # 0 not determined
        if status != 0:
            self._clm.requestAlwaysAuthorization()
            return

    def stop_monitoring(self):
        """Stop the scanner monitoring"""
        self._deactivate_ibeacons()
        self._regions_seen = []
        self._clm.delegate = None
        del self._clm

    def register_beacon(self, uuid, name=None):
        """Register a beacon to be tracked, using the ibeacon `uuid`"""
        assert(len(uuid) == 36)
        uuid = uuid.upper()
        nsuuid = NSUUID.alloc().initWithUUIDString_(uuid)
        self._regions[uuid] = CLBeaconRegion.alloc(
        ).initWithProximityUUID_identifier_(nsuuid, name or uuid)
        self._regions_nsuuid[uuid] = nsuuid

    def unregister_beacon(self, uuid):
        """Unregister a beacon to be tracked."""
        if uuid not in self._regions:
            return
        self._regions_nsuuid.pop(uuid)
        region = self._regions.pop(uuid)
        if self._region_activated:
            self._clm.stopRangingBeaconsInRegion_(region)
        if uuid in self._regions_seen:
            self._regions_seen.remove(uuid)
            self.dispatch("on_beacon_leaved", uuid=uuid)

    def on_error(self, uuid, msg):
        """Event fired when a beacon have an issue / monitoring issues"""
        # print 'beacon error'
        pass

    # (implementation internal)

    @protocol("CLLocationManagerDelegate")
    def locationManager_didChangeAuthorizationStatus_(self, manager, status):
        # print 'locationManager_didChangeAuthorizationStatus_', status
        if status == 3:  # kCLAuthorizationStatusAuthorized
            self._activate_ibeacons()
        elif status == 2:  # kCLAuthorizationStatusDenied
            pass
        elif status == 1:  # kCLAuthorizationStatusRestricted
            pass
        else:  # kCLAuthorizationStatusNotDetermined
            pass

    @protocol("CLLocationManagerDelegate")
    def locationManager_didRangeBeacons_inRegion_(self, manager, beacons,
                                                  region):
        uuid = region.proximityUUID.UUIDString().UTF8String()
        print 'uuid', uuid
        # print 'locationManager_didRangeBeacons_inRegion_', uuid, self._regions
        if uuid not in self._regions:
            return

        beacon = None
        count = beacons.count()
        # print "got", count
        if count:
            beacon = beacons.objectAtIndex_(0)
            # print "rssi", beacon.rssi
            if beacon.rssi == 0:
                beacon = None

        if beacon:
            # print "yes!"
            if uuid not in self._regions_seen:
                self._regions_seen.append(uuid)
                self.dispatch("on_beacon_entered", uuid=uuid)
            self.dispatch("on_beacon_update",
                          uuid=uuid,
                          major=beacon.major.integerValue(),
                          minor=beacon.minor.integerValue(),
                          proximity=self.PROXIMITY[beacon.proximity],
                          rssi=beacon.rssi)
        else:
            # print "no:("
            if uuid in self._regions_seen:
                self._regions_seen.remove(uuid)
                self.dispatch("on_beacon_leaved", uuid=uuid)


    @protocol("CLLocationManagerDelegate")
    def locationManager_rangingBeaconsDidFailForRegion_withError_(
        self, manager, region, error
    ):
        uuid = region.proximityUUID.UUIDString().UTF8String()
        msg = error.localizedDescription.UTF8String()
        self.dispatch("on_error", uuid=uuid, msg=msg)

    def _activate_ibeacons(self):
        for region in self._regions.values():
            self._clm.startRangingBeaconsInRegion_(region)
        self._region_activated = True

    def _deactivate_ibeacons(self):
        for region in self._regions.values():
            self._clm.stopRangingBeaconsInRegion_(region)
        self._region_activated = False



"""
if __name__ == "__main__":
    from kivy.app import App
    from kivy.uix.button import Button

    def dprint(*args, **kwargs):
        print(args, kwargs)

    class IbeaconScanner(App):
        def build(self):
            self._scanner = IBeaconScanner()
            self._scanner.register_beacon(
                "E2C56DB5-DFFB-48D2-B060-D0F5A71096E0")
            from functools import partial
            self._scanner.bind(
                on_beacon_entered=partial(dprint, "on_beacon_entered"),
                on_beacon_update=partial(dprint, "on_beacon_update"),
                on_beacon_leaved=partial(dprint, "on_beacon_leaved"),
                on_error=partial(dprint, "on_error"))
            return Button(text="Start Scanner", on_release=self.start_scanner)

        def start_scanner(self, *args):
            self._scanner.start_monitoring()

        def on_pause(self):
            return True

    IbeaconScanner().run()
"""



# '''
# Bluetooth Low Energy support using CoreBluetooth
# ================================================
# '''

# import struct
# from kivy.app import App
# from kivy.event import EventDispatcher
# from kivy.utils import platform
# from kivy.clock import Clock
# from pyobjus import autoclass, protocol
# from pyobjus.dylib_manager import load_framework, INCLUDE

# DEBUG = True

# (CBCentralManagerStateUnknown, CBCentralManagerStateResetting,
#  CBCentralManagerStateUnsupported, CBCentralManagerStateUnauthorized,
#  CBCentralManagerStatePoweredOff, CBCentralManagerStatePoweredOn) = range(6)

# NSDictionary = autoclass("NSDictionary")
# NSMutableDictionary = autoclass("NSMutableDictionary")
# NSNumber = autoclass("NSNumber")
# NSString = autoclass("NSString")

# visited = {}
# visited_failed = {}
# visited_connecting = False


# class CoreBluetoothScanner(EventDispatcher):
#     __events__ = ('on_peripheral', 'on_state')

#     midi_note_number = ListProperty()
#     note_open = BooleanProperty(True)
#     last_uuid = StringProperty()
#     latest_uuid = StringProperty()

#     def __init__(self, **kwargs):
#         super(CoreBluetoothScanner, self).__init__(**kwargs)
#         try:
#             load_framework(INCLUDE.IOBluetooth)
#         except:
#             pass
#         CBCentralManager = autoclass('CBCentralManager')
#         self.central = CBCentralManager.alloc().initWithDelegate_queue_(self,
#                                                                         None)
#         self.app = App.get_running_app()

#     def on_peripheral(self, uuid):
#         '''Event called everytime a peripheral send an advertissement
#         '''
#         #self.app.appix_base.temp_generated_uuid = uuid
#         pass

#     def on_state(self, state):
#         '''Event called when the Bluetooth manager state change. Can be one of:
#         'unknown', 'ready', 'poweroff', 'nopermission', 'nohardware'
#         '''
#         pass

#     def schedule_dispatch(self, eventname, *args, **kwargs):
#         def _dispatch(dt):
#             self.dispatch(eventname, *args, **kwargs)

#         Clock.schedule_once(_dispatch)

#     def start(self):
#         key = NSString.alloc().initWithUTF8String_('kCBScanOptionAllowDuplicates')
#         value = NSNumber.alloc().initWithInt_(1)
#         options = NSMutableDictionary.alloc().init()
#         options.setObject_forKey_(value, key)
#         self.central.scanForPeripheralsWithServices_options_(None, options)

#     def stop(self):
#         self.central.stopScan()

#     @protocol('CBCentralManagerDelegate')
#     def centralManagerDidUpdateState_(self, central):

#         state = central.state() if callable(central.state) else central.state

#         # print "centralManagerDidUpdateState_, state is", state

#         if state == CBCentralManagerStateUnknown:
#             kstate = 'unknown'
#         elif state == CBCentralManagerStatePoweredOn:
#             kstate = 'ready'
#         elif state == CBCentralManagerStatePoweredOff:
#             kstate = 'poweroff'
#         elif state == CBCentralManagerStateUnauthorized:
#             kstate = 'nopermission'
#         elif state == CBCentralManagerStateUnsupported:
#             kstate = 'nohardware'
#         elif state == CBCentralManagerStateResetting:
#             kstate = 'resetting'
#         if DEBUG:
#             print '---------> CENTRAL UPDATE', kstate
#         self.schedule_dispatch('on_state', kstate)

#     @protocol('CBCentralManagerDelegate')
#     def centralManager_didConnectPeripheral_(self, central, peripheral):
#         global visited_connecting
#         visited_connecting = False
#         if DEBUG:
#             print '-> connected to device', peripheral
#             print peripheral.state
#             print '-> GREAT!'
#         #peripheral.discoverServices_(None)
#         central.cancelPeripheralConnection_(peripheral)
#         uuid = peripheral.identifier.UUIDString().cString()
#         visited[uuid] = True

#     @protocol('CBCentralManagerDelegate')
#     def centralManager_didFailToConnectPeripheral_error_(self, central,
#                                                          peripheral, error):
#         global visited_connecting
#         visited_connecting = False
#         uuid = peripheral.identifier.UUIDString().cString()
#         if DEBUG:
#             print uuid, '! err: failed to connect to periph'
#         if uuid not in visited_failed:
#             visited_failed[uuid] = 1
#         else:
#             visited_failed[uuid] += 1

#     @protocol('CBCentralManagerDelegate')
#     def centralManager_didDisconnectPeripheral_error_(self, central,
#                                                       peripheral, error):
#         global visited_connecting
#         visited_connecting = False
#         uuid = peripheral.identifier.UUIDString().cString()
#         if DEBUG:
#             print uuid, '! err: disconnect to periph'
#         if uuid not in visited_failed:
#             visited_failed[uuid] = 1
#         else:
#             visited_failed[uuid] += 1

#     @protocol('CBCentralManagerDelegate')
#     def centralManager_didDiscoverPeripheral_advertisementData_RSSI_(
#         self, central, peripheral, data, rssi
#     ):
#         global visited_connecting
#         # if DEBUG:
#         #     print 'centralManager_didDiscoverPeripheral_advertisementData_RSSI_', central, peripheral, data, rssi

#         if not data:
#             return

#         uuid = peripheral.identifier().UUIDString().cString()
#         # print uuid, 'entralManager_didDiscoverPeripheral_advertisementData_RSSI'
#         # if hasattr(rssi, 'floatValue'):
#         #     rssi = rssi.floatValue()
#         # name = ''
#         # if peripheral.name:
#         #     name = peripheral.name.cString()
#         #
#         # if DEBUG:
#         #     print '---> GET', (uuid, name, rssi)
#         #     if data:
#         #         print data.description().cString()
#         # if not name:
#         #     if DEBUG:
#         #         print uuid, '! avoid no name'
#         #     return
#         #
#         # if DEBUG:
#         #     print uuid, '! yes, name is', name
#         # if len(name) != 16:
#         #     if DEBUG:
#         #         print uuid, '! avoid using this beacon, invalid name length'
#         #
#         #     if visited_failed.get(uuid, 0) > 10:
#         #         if DEBUG:
#         #             print uuid, '! already tried 10 times, stop.'
#         #         return
#         #
#         #     if -85 < rssi < 0:
#         #         if DEBUG:
#         #             print uuid, '! rssi in acceptable range, try to connect to it'
#         #     else:
#         #         if DEBUG:
#         #             print uuid, '! uuid too far, dont do anything'
#         #         return
#         #
#         #     #if visited_connecting:
#         #     #    if DEBUG:
#         #     #        print uuid, '! connection already in progress to {}'.format(visited_connecting)
#         #     #    return
#         #
#         #     if uuid not in visited and name.lower() in ('b1',
#         #                                                 'redbear beacon'):
#         #         if DEBUG:
#         #             print uuid, '! we recognized the name, connect to it'
#         #         # try to visit it
#         #         visited_connecting = uuid
#         #         central.connectPeripheral_options_(peripheral, None)
#         #         pass
#         #
#         #     return
#         #
#         # uuid = name
#         #
#         # #uuid = self._decode_puid_from_adv(uuid, data)
#         # #if not uuid:
#         # #    return
#         #
#         # self.schedule_dispatch('on_peripheral', uuid, name, rssi)
#         self.schedule_dispatch('on_peripheral', uuid)


#     # CoreBluetooth

#     def on_corebluetooth_state(self, corebluetooth, state):
#         if state == "ready":
#             # start the scanning when bluetooth is ready to use
#             # print "-- start corebluetooth"
#             corebluetooth.start()


#     def on_corebluetooth_peripheral(self, corebluetooth, uuid):
#         #print "cb <<>>", uuid
#         self.latest_uuid = uuid
#         # if not self.app:
#         #     self.app = App.get_running_app()
#         # if self.app.core_location.ios_mode == 'Recording':
#         #     if uuid not in self.app.core_location.ios_filtered_list:
#         #         self.app.core_location.ios_collected_beacon_list.append(uuid)

#         # if self.app.core_location.ios_mode == 'Filtering':
#         #     self.app.core_location.ios_filtered_list.append(uuid)

#         # if self.app.core_location.ios_mode == 'Presenting':
#         #     if uuid not in self.app.core_location.ios_filtered_list:
#         #         if self.app.core_location.recording_success:
#         #             self.process_presentation_uuid(uuid)


#     def process_presentation_uuid(self, uuid):

#         # print "UUID ------->", uuid

#         if uuid != self.last_uuid:

#             if uuid in self.app.core_location.ios_midi_extras_list:
#                 extra_id = self.app.core_location.ios_midi_extras_list.index(uuid)

#                 if extra_id == 0:
#                     self.app.appix_base.animation_layer.clear_stage()

#                 elif extra_id == 1:
#                     if self.app.DEBUG:
#                         print "note on!"
#                     if self.app.appix_base.animation_layer.midi_note_list[self.app.core_location.current_note] == 0 \
#                             and self.note_open:
#                         self.note_open = False
#                         self.app.appix_base.animation_layer.midi_note_list[self.app.core_location.current_note] = 1
#                         self.app.appix_base.process_content_instruction(self.app.core_location.current_note, True)
#                         Clock.schedule_once(self.reopen_note, 0.37)   # based on a 20 time beacon send

#                 elif extra_id == 2:
#                     if self.app.DEBUG:
#                         print "note off!"
#                     if self.app.appix_base.animation_layer.midi_note_list[self.app.core_location.current_note] == 1 \
#                             and self.note_open:
#                         self.note_open = False
#                         self.app.appix_base.animation_layer.midi_note_list[self.app.core_location.current_note] = 0
#                         self.app.appix_base.process_content_instruction(self.app.core_location.current_note, False)
#                         Clock.schedule_once(self.reopen_note, 0.37)   # based on a 20 time beacon send

#                 elif extra_id == 3:
#                     self.app.appix_base.animation_layer.toggle_blink(True)

#                 elif extra_id == 4:
#                     self.app.appix_base.animation_layer.toggle_blink(False)

#                 elif extra_id == 5:
#                     self.app.appix_base.animation_layer.engage_blink()

#                 elif extra_id == 6:
#                     self.app.appix_base.toggle_flash(True)

#                 elif extra_id == 7:
#                     self.app.appix_base.toggle_flash(False)

#             else:
#                 midi_note_number = self.derive_midi_note_number(uuid)
#                 if midi_note_number != -1:
#                     content_slot = self.app.core_location.ios_midi_key_list.index(uuid)
#                     self.app.core_location.current_note = content_slot + (12 * (self.app.core_location.current_octave - 1))
#                     current_note = self.app.core_location.current_note
#                     if self.app.appix_base.animation_layer.midi_note_list[current_note] == 0:
#                         note_press = True
#                         self.app.appix_base.animation_layer.midi_note_list[current_note] = 1
#                     else:
#                         note_press = False
#                         self.app.appix_base.animation_layer.midi_note_list[current_note] = 0
#                     # print "self.current_note", current_note
#                     # print "note press", note_press
#                     # print "note list", self.app.appix_base.animation_layer.midi_note_list
#                     #if self.note_open:
#                     self.app.appix_base.process_content_instruction(current_note, note_press)

#             self.last_uuid = uuid

#     def reopen_note(self, *args):
#         self.note_open = True

#     def derive_midi_note_number(self, uuid):
#         try:
#             content_slot = self.app.core_location.ios_midi_key_list.index(uuid)
#             return content_slot
#         except ValueError:
#             if self.app.DEBUG:
#                 print "uuid not in list"
#             return -1
