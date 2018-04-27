
'''
Bluetooth Low Energy support using CoreBluetooth
================================================
'''

from kivy.app import App
from kivy.event import EventDispatcher
from kivy.properties import AliasProperty
from kivy.clock import Clock
from pyobjus import autoclass, protocol
import decoder
import time
# import notifications

DEBUG = False

(CBCentralManagerStateUnknown, CBCentralManagerStateResetting,
 CBCentralManagerStateUnsupported, CBCentralManagerStateUnauthorized,
 CBCentralManagerStatePoweredOff, CBCentralManagerStatePoweredOn) = range(6)

NSDictionary = autoclass("NSDictionary")
NSMutableDictionary = autoclass("NSMutableDictionary")
NSNumber = autoclass("NSNumber")
NSString = autoclass("NSString")
NSArray = autoclass("NSArray")
CBUUID = autoclass("CBUUID")

visited = {}
visited_failed = {}
visited_connecting = False
CBCentralManager = autoclass('CBCentralManager')


class CoreBluetoothScanner(EventDispatcher):

    __events__ = ('on_state', )

    app = AliasProperty(lambda *args: App.get_running_app(), None)

    def __init__(self, **kwargs):
        super(CoreBluetoothScanner, self).__init__(**kwargs)
        self.decoder = decoder.BluetoothDecoder()
        self.previous_scan_results = []
        self.state = "none"
        self.start_button_pressed = False
        self.central = None
        self.last_central = None
        self.CBCentralManager = CBCentralManager
        self.check_bluetooth_enabled()

    
    @protocol('CBCentralManagerDelegate')
    def centralManager_didConnectPeripheral_(self, central, peripheral):
        global visited_connecting
        visited_connecting = False
        if DEBUG:
            print '-> connected to device', peripheral
            print peripheral.state
            print '-> GREAT!'
        # peripheral.discoverServices_(None)
        central.cancelPeripheralConnection_(peripheral)
        uuid = peripheral.identifier.UUIDString().cString()
        visited[uuid] = True


    @protocol('CBCentralManagerDelegate')
    def centralManager_didFailToConnectPeripheral_error_(self, central,
                                                         peripheral, error):
        global visited_connecting
        visited_connecting = False
        uuid = peripheral.identifier.UUIDString().cString()
        if DEBUG:
            print uuid, '! err: failed to connect to periph'
        if uuid not in visited_failed:
            visited_failed[uuid] = 1
        else:
            visited_failed[uuid] += 1


    @protocol('CBCentralManagerDelegate')
    def centralManager_didDisconnectPeripheral_error_(self, central,
                                                      peripheral, error):
        global visited_connecting
        visited_connecting = False
        uuid = peripheral.identifier.UUIDString().cString()
        if DEBUG:
            print uuid, '! err: disconnect to periph'
        if uuid not in visited_failed:
            visited_failed[uuid] = 1
        else:
            visited_failed[uuid] += 1


    @protocol('CBCentralManagerDelegate')
    def centralManager_didDiscoverPeripheral_advertisementData_RSSI_(
            self, central, peripheral, data, rssi):
        # print "Incoming central:", central.description().UTF8String()
        # print "Incoming peripheral:", peripheral.description().UTF8String()
        # time1 = time.time()
        data_object = data.objectForKey_("kCBAdvDataServiceData")
        if data_object:
            # time2 = time.time()
            ble_data_string = data_object.description().UTF8String()
            print ble_data_string
            # validating key
            if self.app.appix_beacon_key == ble_data_string[18:24].replace(" ", "").upper():
                # time3 = time.time()
                if not self.app.ADMIN_APP:
                    self.process_ble_packets(ble_data_string)
                else:
                    rssi = str(rssi.description().UTF8String())
                    self.process_ble_packets(ble_data_string, rssi)
                # else
                # self.process_ble_packets(ble_data_string)

                # time4 = time.time()
                # print "TIME TO EDDYSTONE:", (time2-time1)*1000.
                # print "TIME TO VALIDATE: ", (time3-time2)*1000.
                # print "TIME TO PROCESS:  ", (time4-time3)*1000.
                # print "TOTAL TIME:      ", (time4-time1)*1000.
                # print " "


    @protocol('CBCentralManagerDelegate')
    def centralManagerDidUpdateState_(self, central):
        state = central.state() if callable(central.state) else central.state
        # print "centralManagerDidUpdateState_, state is", state
        if state == CBCentralManagerStateUnknown:
            kstate = 'unknown'
        elif state == CBCentralManagerStatePoweredOn:
            kstate = 'ready'
        elif state == CBCentralManagerStatePoweredOff:
            # place an alert box here with uialertcontroller?
            kstate = 'poweroff'
        elif state == CBCentralManagerStateUnauthorized:
            kstate = 'nopermission'
        elif state == CBCentralManagerStateUnsupported:
            kstate = 'nohardware'
        elif state == CBCentralManagerStateResetting:
            kstate = 'resetting'
        if DEBUG:
            print '---------> CENTRAL UPDATE', kstate
        self.schedule_dispatch('on_state', kstate)


    def on_state(self, state, *args):
        '''Event called when the Bluetooth manager state change. Can be one of:
        'unknown', 'ready', 'poweroff', 'nopermission', 'nohardware'
        '''
        self.state = state
        if self.last_central != str(self.central):
            if state == "ready":
                # start the scanning when bluetooth is ready to use
                self.start()
                if self.start_button_pressed:
                    Clock.schedule_once(self.app.appix_base.start_show, 0.1)
                self.last_central = str(self.central)
            else:
                # print "Bluetooth error, state is ", state
                pass


    def schedule_dispatch(self, eventname, *args, **kwargs):
        def _dispatch(dt):
            self.dispatch(eventname, *args, **kwargs)
        Clock.schedule_once(_dispatch)


    def check_bluetooth_enabled(self):
        # print "check_bluetooth_enabled():", self.state, self.central
        if self.state in ["none", "poweroff"]:
            self.central = self.CBCentralManager.alloc().initWithDelegate_queue_(self, None)
        elif self.state == "ready":
            Clock.schedule_once(self.app.appix_base.start_show, 0.1)
        else:
            print "Bluetooth Error:", self.state


    def process_ble_packets(self, ble_data_string, *args):
        # print args
        start_index, end_index = ble_data_string.index("FEAA = <")+12, ble_data_string.index(">;")-4
        scan_results = ble_data_string[start_index:end_index]
        print scan_results
        if self.app.ADMIN_APP:
            sr = scan_results.replace(" ", "")
            self.app.appix_base.update_data_labels(sr, args[0])
        if scan_results != self.previous_scan_results:
            # print "bluetooth in:", scan_results
            decoded_data = self.decoder.decode_beacon_data(scan_results)
            self.app.appix_base.run_bluetooth_commands(decoded_data)
            self.previous_scan_results = scan_results


    def start(self):
        key = NSString.alloc().initWithUTF8String_('kCBScanOptionAllowDuplicates')
        value = NSNumber.alloc().initWithInt_(1)
        options = NSMutableDictionary.alloc().init()
        options.setObject_forKey_(value, key)
        # comment following line if you do not have notifications compiled in kivy-ios
        # notifications.IOSNotif().show('Appix', 'App is running')
        # scan_list = NSArray.arrayWithObject_(CBUUID.UUIDWithString_('78B4'))
        # set scan list to None to blankly scan for every beacon/bluetooth peripheral
        # This only works when app is in foreground.
        scan_list = None
        self.central.scanForPeripheralsWithServices_options_(scan_list, options)


    def stop(self):
        self.central.stopScan()

