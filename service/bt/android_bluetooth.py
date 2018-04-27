import struct
from collections import namedtuple

from jnius import PythonJavaClass, java_method, autoclass
# from android import AndroidService
from android import activity
from kivy.app import App
# from time import sleep
from plyer.platforms.android import SDK_INT
from android.broadcast import BroadcastReceiver
import time
from datetime import datetime
import os
import decoder
import binascii

from .constants import *

# ------------------  CHANGE FOR RELEASE ------------------
DEBUG = True
ADMIN_APP = True


# ------------------  CHANGE FOR RELEASE ------------------


def debug(*args):
    if DEBUG:
        if len(args) == 0:
            return
        if len(args) == 1:
            print(args[0])
        else:
            print(" ".join([str(arg) for arg in args]))


# FIX: maybe use os.environ to set a environ var
appix_beacon_key = "BA115"
scan_appix_beacon_key = list([0xBA, 0x11, 0x50])
NOTIFICATION_TIMEOUT = 30
# show a notification once every timeout seconds
service = None

Context = autoclass('android.content.Context')
if 'APPIX_SERVICE' in os.environ:
    PythonService = autoclass('org.renpy.android.PythonService')
    service = PythonService.mService
    _ns = service.getSystemService(Context.NOTIFICATION_SERVICE)
    Drawable = autoclass("{}.R$drawable".format(service.getPackageName()))

# activity = PythonActivity.mActivity

AndroidString = autoclass('java.lang.String')
BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
NotificationBuilder = autoclass('android.app.Notification$Builder')
Intent = autoclass('android.content.Intent')
PendingIntent = autoclass('android.app.PendingIntent')
Uri = autoclass('android.net.Uri')
Notification = autoclass('android.app.Notification')

List = autoclass('java.util.List')

UUID = autoclass('java.util.UUID')
ParcelUuid = autoclass('android.os.ParcelUuid')

# New Android BT scan settings and filter classes
ScanResult = autoclass('android.bluetooth.le.ScanResult')
ScanFilter = autoclass('android.bluetooth.le.ScanFilter')
ScanFilterBuilder = autoclass('android.bluetooth.le.ScanFilter$Builder')
ScanSettings = autoclass('android.bluetooth.le.ScanSettings')
ScanSettingsBuilder = autoclass('android.bluetooth.le.ScanSettings$Builder')

# Custom scan callback
ScanCallbackImpl = autoclass('com.appix.bt.ScanCallbackImpl')

# Typed List<com.appix.bt.ScanFilterList> bridge class. Not sure how/if we can instantiate generics with PyJnius...
ScanFilterList = autoclass('com.appix.bt.ScanFilterList')

# BitmapFactory = autoclass('android.graphics.BitmapFactory')
# NotificationCompat = autoclass('android.app.NotificationCompat.Builder')


# Eddystone UID Service
UID_SERVICE = ParcelUuid.fromString("0000feaa-0000-1000-8000-00805f9b34fb");

# Default namespace id for Appix Eddystone beacons (ba1150...)
NAMESPACE_FILTER = bytearray([
    0x00,  # Type = UID
    0x00,  # Tx Power
    0xBA, 0x11, 0x50,  # The only parts we care about
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00
])

# Force frame type and namespace id to match
NAMESPACE_FILTER_MASK = bytearray([
    0xFF,
    0x00,
    0xFF, 0xFF, 0xF0,  # or maybe 0xFF, 0xFF, 0xF0 ?
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00
])


def check_bluetooth_enabled(init):
    app = App.get_running_app()
    debug("init 1 ", init)
    if not init:
        app.appix_base.start_show()
        return

    def on_activity_result(request_code, result_code, *args):
        # request codes - 50: gui function, 100: app start, 150:, heartbeat, 200: instructions,
        debug("-----------------> request code: %s %s %s" % (request_code, result_code, args))
        # del args
        debug("init 2 %s" % init)
        if result_code == -1:
            debug("THEY CHOSE YES")
            if init:
                debug("init or not app.bluetooth_available")
                app.initiate_service()
            # elif not init and not app.bluetooth_available:
            # check_bluetooth_enabled()

            # if init:
            #     debug("They Chose Yes")
            #     return 1 if init else 2
        else:
            debug("They Chose No")
            return 0

    PythonActivity = autoclass('org.renpy.android.PythonActivity')
    if init:
        activity.bind(on_activity_result=on_activity_result)
    BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')

    PythonActivity.mActivity.startActivityForResult(
        Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE), 0)
    # debug("RESPONSE", response)
    # return response
    # if BluetoothAdapter.getDefaultAdapter():
    #     debug("STARTED BLUETOOTH")
    #     return True
    # debug("DENIED BLUETOOTH")
    # return False


class LeScanCallback(PythonJavaClass):
    """ Old (< API 21) callback class """

    __javainterfaces__ = ['android/bluetooth/BluetoothAdapter$LeScanCallback']

    def __init__(self, callback):
        super(LeScanCallback, self).__init__()
        self.callback = callback

    @java_method('(Landroid/bluetooth/BluetoothDevice;I[B)V')
    def onLeScan(self, device, rssi, scanRecord):
        self.callback(device, rssi, scanRecord)


class AppixScanCallback(PythonJavaClass):
    """ New (>= API 21) callback class """

    __javainterfaces__ = ['com/appix/bt/ScanCallbackImpl$IScanCallback']
    __javacontext__ = 'app'

    def __init__(self, process_packet_callback):
        super(AppixScanCallback, self).__init__()
        self.process_packet_callback = process_packet_callback

    @java_method('(I)V')
    def onScanFailed(self, errorCode):
        debug("Scan Failed: %s" % errorCode)

    @java_method('(ILandroid/bluetooth/le/ScanResult;)V')
    def onScanResult(self, callbackType, result):
        record = result.getScanRecord()

        device = result.getDevice()
        rssi = result.getRssi()
        scan_bytes = record.getBytes()

        # txPower = result.getTxPower()
        deviceName = record.getDeviceName()
        manufacturer_data = record.getManufacturerSpecificData()
        service_uuids = record.getServiceUuids()

        debug("rssi: {0}".format(rssi))
        debug(''.join('{:02x} '.format(x) for x in result.getScanRecord().getBytes()))

        self.process_packet_callback(device, rssi, scan_bytes)


class AndroidBLEScanReader(object):

    def __init__(self):
        super(AndroidBLEScanReader, self).__init__()
        self.decoder = decoder.BluetoothDecoder()
        self._message = ''
        self._last_notification_time = datetime.now()

        self.previous_scan_results = ""
        self.previous_unique_message_id = 0
        self.allow_notification = True

        # One-time BT initialization
        self.btManager = service.getSystemService(Context.BLUETOOTH_SERVICE)
        self.btAdapter = self.btManager.getAdapter()

        self.setup_bluetooth()

    def setup_bluetooth(self):

        if SDK_INT < 21:
            self.mybtLeScan = LeScanCallback(self.process_ble_packets)
        else:
            self.myLEScanner = self.btAdapter.getBluetoothLeScanner()
            self.scanCallbackImpl = ScanCallbackImpl()
            self.scanCallbackImpl.setCallback(AppixScanCallback(self.process_ble_packets))

            #
            # Scan Settings
            #
            # Trying different combinations of scan settings and filters to determine which works best in live
            # environment.
            #

            # Default setting
            settingsBuilder0 = ScanSettingsBuilder()

            # Kitchen Sink
            settingsBuilder1 = ScanSettingsBuilder()
            settingsBuilder1.setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
            settingsBuilder1.setCallbackType(ScanSettings.CALLBACK_TYPE_ALL_MATCHES)
            if SDK_INT > 22:
                settingsBuilder1.setMatchMode(ScanSettings.MATCH_MODE_AGGRESSIVE)
                settingsBuilder1.setNumOfMatches(ScanSettings.MATCH_NUM_MAX_ADVERTISEMENT)
            settingsBuilder1.setReportDelay(0)

            # Match Mode Aggressive Only
            settingsBuilder2 = ScanSettingsBuilder()
            if SDK_INT > 22:
                settingsBuilder2.setMatchMode(ScanSettings.MATCH_MODE_AGGRESSIVE)

            # Scan Mode Low Latency Only
            settingsBuilder3 = ScanSettingsBuilder()
            settingsBuilder3.setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)

            # Callback Type All Matches
            settingsBuilder4 = ScanSettingsBuilder()
            settingsBuilder4.setCallbackType(ScanSettings.CALLBACK_TYPE_ALL_MATCHES)

            # Scan Mode Low Latency + Callback All matches
            settingsBuilder5 = ScanSettingsBuilder()
            settingsBuilder5.setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
            settingsBuilder5.setCallbackType(ScanSettings.CALLBACK_TYPE_ALL_MATCHES)

            # Low Latency + Match Mode Aggressive
            settingsBuilder6 = ScanSettingsBuilder()
            settingsBuilder6.setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
            settingsBuilder6.setCallbackType(ScanSettings.CALLBACK_TYPE_ALL_MATCHES)
            if SDK_INT > 22:
                settingsBuilder6.setMatchMode(ScanSettings.MATCH_MODE_AGGRESSIVE)

            # Command/uncomment for now to apply different settings here:
            # scanSettings = settingsBuilder0.build()
            # scanSettings = settingsBuilder1.build()
            # scanSettings = settingsBuilder2.build()
            scanSettings = settingsBuilder3.build()
            # scanSettings = settingsBuilder4.build()
            # scanSettings = settingsBuilder5.build()
            # scanSettings = settingsBuilder6.build()

            self.scanSettings = scanSettings

            #
            # Scan Filter
            #
            filters = ScanFilterList()
            serviceUuidFilter = ScanFilterBuilder().setServiceData(UID_SERVICE, NAMESPACE_FILTER,
                                                                   NAMESPACE_FILTER_MASK).build()
            filters.addFilter(serviceUuidFilter)

            self.filters = filters

            # Note: Not currently making use of filtering

            # filterBuilder.setDeviceAddress("01:02:03:04:05:06")

            # filterBuilder.setDeviceName("")

            # filterBuilder.setManufacturerData(11, bytearray([0x01, 0x02,]))
            # filterBuilder.setManufacturerData(11, bytearray([0x01, 0x02,], bytearray([0x01, 0x02,])))

            # filterBuilder.setServiceData(ParcelUuid serviceDataUuid, byte[] serviceData)

            # filterBuilder.setServiceUuid(ParcelUuid serviceUuid, ParcelUuid uuidMask)
            # filterBuilder.setServiceUuid(ParcelUuid serviceUuid)

            debug(" ")
            debug(" ")
            debug("STARTING SCAN")

            # New method

            # Default scan settings
            # self.myLEScanner.startScan(self.scanCallbackImpl)

    def initiate_bluetooth(self, *args):
        print "SDK_INT is", SDK_INT

        try:
            if SDK_INT < 21:
                # Old method
                self.btAdapter.startLeScan(self.mybtLeScan)
                debug("startLeScan")
            else:
                # New method
                self.myLEScanner.startScan(self.filters.getFilters(), self.scanSettings, self.scanCallbackImpl)
                debug("\n\n> SCAN STARTED")
        except Exception as err:
            debug(err)
            pass
        finally:
            pass

    def scan_standby(self, pause_time):
        # stop scan here, set bluetooth_standby_time here
        # this bluetooth_standby_time would be decreased in the
        # _listen method while loop, on timeout bluetooth would be enabled back again.
        self.appixservice.comm_service.bluetooth_standby_time = pause_time
        if SDK_INT < 21:
            self.btAdapter.stopLeScan(self.mybtLeScan)
            debug("StopLeScan")
        else:
            self.myLEScanner.stopScan(self.scanCallbackImpl)
            debug("StopScan")
        debug("PAUSING SCAN FOR %s" % pause_time)

    def refresh_bluetooth(self):
        # debug("REFRESHING BLUETOOTH")
        if SDK_INT < 21:
            # time1 = time.time()
            self.btAdapter.stopLeScan(self.mybtLeScan)
            # time2 = time.time()
            # self.btAdapter.startLeScan(self.mybtLeScan)
            # time3 = time.time()
            # debug("TIME TO STOP:  ", (time2-time1)*1000.)
            # debug("TIME TO START: ", (time3-time2)*1000.)
            # debug("StopLeScan")
        else:
            self.myLEScanner.stopScan(self.scanCallbackImpl)
            debug("StopScan")

        time.sleep(.2)

        self.initiate_bluetooth()
        debug("REFRESHED BLUETOOTH")

    def restart_bluetooth(self):
        debug("RESTARTING BLUETOOTH")
        if SDK_INT < 21:
            debug("STOPPING LE SCAN")
            self.btAdapter.stopLeScan(self.mybtLeScan)
            debug("STOPPED LE SCAN")
        else:
            debug("STOPPING SCAN")
            self.myLEScanner.stopScan(self.scanCallbackImpl)
            debug("STOPPED SCAN")
        time.sleep(.2)
        self.initiate_bluetooth()
        debug("INITIATED BLUETOOTH")

    # def restart_service(self):
    #     debug("RESTARTING SERVICE")
    #     self.stop()
    #     time.sleep(.1)
    #     self.start_service()

    # def start_service(self):
    #     debug("ABOUT TO START")
    #     global service
    #     service = AndroidService('Appix service', 'running')
    #     debug("ANDROID SERVICE INSTANTIATED")
    #     service.start('service started')
    #     debug("SERVICE STARTED")
    #     time.sleep(.1)
    #     self.initiate_bluetooth()

    def stop(self):
        self.close_all_notifications()
        if SDK_INT < 21:
            self.btAdapter.stopLeScan(self.mybtLeScan)
            debug("StopLeScan")
        else:
            self.myLEScanner.stopScan(self.scanCallbackImpl)
            debug("StopScan")

    def process_ble_packets(self, device, rssi, scan_record, *args):
        # time1 = time.time()

        # debug("Raw Scan Bytes -->",)
        # debug(''.join('{:02x} '.format(x) for x in scan_record[:32]))

        '''
        Raw Scan Bytes:
        02 01 06 03 03 aa fe 17 16 aa fe 00 14 ba 11 50 ff ff ff ff ff ff ff ff ff ff 11 22 33 00 00 ...
        '''
        if scan_appix_beacon_key == list([scan_record[13], scan_record[14], scan_record[15]]):

            # Decode Eddystone UID data (without reserved bytes)
            uuid = ''.join('{:02x}'.format(x) for x in scan_record[13:29])

            # Grab the data portion (UUID + remainder)
            beacon_data = ''.join('{:02x} '.format(x) for x in scan_record[13:])

            debug(" ")
            debug(">> Signal Validated!!! <<")
            # debug("Full Hex Beacon Signal -->", ''.join('{:02x} '.format(x) for x in scan_record))
            debug("Beacon Data -->", beacon_data)
            debug("RSSI -->", rssi)
            debug("UUID -->", uuid)
            debug(" ")

            if ADMIN_APP:
                data = {"data": beacon_data, "rssi": rssi}
                self.appixservice.comm_service.send_message(str(data))

            if uuid != self.previous_scan_results:
                self.dispatch_bluetooth_commands(uuid)
                self.appixservice.comm_service.time_since_app_paused = 0
                self.previous_scan_results = uuid

    # TODO: LAST FUNCTION CALL IN SERVICE,
    def dispatch_bluetooth_commands(self, data_results):

        decoded_data = self.decoder.decode_beacon_data(data_results)

        if decoded_data['message_type'] == 0:
            if decoded_data['location_mode'] == 14:
                self.scan_standby(75)

            elif decoded_data['location_mode'] == 15:
                self.scan_standby(150)

        if self.appixservice._app_state == 'paused':
            if decoded_data['message_type'] in [2, 3, 4, 5, 7, 10, 11]:
                self.notify("We're Back", "Join the Show?")
            elif decoded_data['message_type'] == 8:
                if decoded_data['vibrate_code'] == 1:
                    self.notify("We're Back", "Join the Show?")

        # do not allow a stop or phrase through
        if (self.appixservice._app_state == 'paused' and decoded_data['message_type'] not in [3, 6]) \
                or self.appixservice._app_state == 'running':
            self.appixservice.comm_service.send_message(str(decoded_data))

        # refresh bluetooth if message is play, stop, sports...
        if decoded_data['message_type'] not in [0, 1, 7, 12, 13, 14, 15]:
            self.refresh_bluetooth()

    def format_beacon_data(self, data_string):
        d = data_string.replace(" ", "")
        return ' '.join(d[i:i + 4] for i in range(0, len(d), 4)).upper()

    def close_all_notifications(self):
        _ns.cancel(0)

    def check_notification_timeout(self):
        dift = datetime.now() - self._last_notification_time
        if dift.total_seconds() > NOTIFICATION_TIMEOUT and self.allow_notification:
            self.allow_notification = False
            return True
        return False

    def notify(self, title, message):
        global service
        if not self.check_notification_timeout():
            return
        self._last_notification_time = datetime.now()
        icon = getattr(Drawable, 'icon')
        noti = NotificationBuilder(service)

        noti.setPriority(
            Notification.PRIORITY_MAX)  # //HIGH, MAX, FULL_SCREEN and setDefaults(Notification.DEFAULT_ALL) will make it a Heads noti.Up Display Style
        noti.setDefaults(
            Notification.DEFAULT_ALL)  # //HIGH, MAX, FULL_SCREEN and setDefaults(Notification.DEFAULT_ALL) will make it a Heads Up Display Style

        noti.setContentTitle(AndroidString((title).encode('utf-8')))
        noti.setContentText(AndroidString((message).encode('utf-8')))
        noti.setTicker(AndroidString(('Appix').encode('utf-8')))
        noti.setSmallIcon(icon)
        noti.setAutoCancel(True)
        id = 996543

        appintent = Intent(Intent.ACTION_PROVIDER_CHANGED)
        pi_app = PendingIntent.getBroadcast(service, id, appintent, PendingIntent.FLAG_UPDATE_CURRENT)
        appintent.setData(Uri.parse('close'))

        # closeintent = Intent(Intent.ACTION_RUN)
        # pi_close = PendingIntent.getBroadcast(service, id, closeintent, PendingIntent.FLAG_UPDATE_CURRENT)
        # closeintent.setData(Uri.parse('open'))

        if not hasattr(self, 'br'):
            self.br = BroadcastReceiver(
                self.on_broadcast, actions=['provider_changed', 'run'])
            self.br.start()

        noti.addAction(0, AndroidString("Launch App"), pi_app)
        # noti.addAction(0, AndroidString("Close Service"), pi_close)
        if SDK_INT >= 16:
            noti = noti.build()
        else:
            noti = noti.getNotification()
        _ns.notify(0, noti)

    def on_broadcast(self, context, intent):
        global service
        # called when a device is found
        # close notification
        _ns.cancel(0)

        # close notification drawer
        it = Intent(Intent.ACTION_CLOSE_SYSTEM_DIALOGS)
        context.sendBroadcast(it)
        PythonActivity = autoclass('org.renpy.android.PythonActivity')

        action = str(intent.getAction())

        # Start Application
        intent = Intent(
            service.getApplicationContext(),
            PythonActivity)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_REORDER_TO_FRONT)
        service.getApplicationContext().startActivity(intent)

        if action.endswith('RUN'):
            debug('clean_up_service')
            # import time
            # time.sleep(1)
            self.appixservice.comm_service.send_message('stop')
            self.appixservice.clean_up()