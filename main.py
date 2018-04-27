__version__ = "1.1.9.2"

# Kivy Libs
import kivy
kivy.require('1.10.0')  # replace with your current kivy version !
from kivy.app import App
from kivy.config import Config
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.utils import platform
from kivy.properties import ObjectProperty, BooleanProperty, ListProperty, StringProperty, NumericProperty
from kivy.network.urlrequest import UrlRequest
from distutils.version import LooseVersion
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout

from datetime import datetime, date
from time import sleep
from raven import Client
from raven.transport.threaded_requests import ThreadedRequestsHTTPTransport
raven_client = Client('https://a8ae0c320ce84f5ebd43babb96209667:cc72349bf57046909ed8f7608000162f@app.getsentry.com/59721?verify_ssl=0')
client = Client('https://a8ae0c320ce84f5ebd43babb96209667:cc72349bf57046909ed8f7608000162f@app.getsentry.com/59721',
                transport=ThreadedRequestsHTTPTransport)
# print "raven client ------------------>", raven_client

# Local Libs
# from comm import AppixComm
if platform == 'android':
    from service.comm import AppixComm

import appix


# ------------------  CHANGE FOR RELEASE ------------------

DEBUG = False        # TODO: <----------------------- Change to False for release
LIVE_DEPLOY = False  # TODO: <----------------------- Change to True for release
ADMIN_APP = True     # TODO: <----------------------- Change to False for release
EXPIRE_DATE = "March 28, 2018"     # format = "January 1, 2000", needs to be the DATE AFTER THE EVENT

# ------------------  CHANGE FOR RELEASE ------------------



appix_beacon_key = "BA115"

appix_google_play_url = "market://details?id=com.appix.appix"
appix_itunes_url = "itms://itunes.apple.com/app/appix/id1058564165?mt=8"
# package name: com.appix.appix

Config.set('graphics', 'fullscreen', 'auto')
Window.fullscreen = True




def event_expired():
    if not EXPIRE_DATE:
        return False
    date_today = datetime.combine(date.today(), datetime.min.time())
    date_expires = datetime.strptime(EXPIRE_DATE, '%B %d, %Y')
    if date_today >= date_expires:
        return True
    else:
        return False

if platform == "android":
    from jnius import autoclass
    # import android_bluetooth
    from service.bt import android_bluetooth
    import android_hardware
    Build = autoclass("android.os.Build")
    BuildVERSION = autoclass('android.os.Build$VERSION')
    BuildVERSION_CODES = autoclass('android.os.Build$VERSION_CODES')

    print "Build", Build
    print "BuildVERSION", BuildVERSION
    print "BuildVERSION.SDK_INT", BuildVERSION.SDK_INT

elif platform == "ios":
    from pyobjus import autoclass, protocol
    # import ios_bluetooth
    # from service.bt import ios_bluetooth
    # from service.bt import AppixBT
    import ios_hardware
    UIDevice = autoclass('UIDevice')
    NSProcessInfo = autoclass('NSProcessInfo')
    processInfo = NSProcessInfo.processInfo()
    currentDevice = UIDevice.currentDevice()


def handle_error_request(**kwargs):
    if platform == 'android':
        raven_client.user_context({
            "BuildVERSION.codename": BuildVERSION.CODENAME,
            "BuildVERSION.incremental": BuildVERSION.INCREMENTAL,
            "BuildVERSION.release": BuildVERSION.RELEASE,
            "BuildVERSION.sdk_int": BuildVERSION.SDK_INT,
            "Build.model": Build.MODEL,
            "Build.manufacturer": Build.MANUFACTURER,
            "Build.brand": Build.BRAND,
            "Build.device": Build.DEVICE,
            "Build.hardware": Build.HARDWARE,
            "Build.product": Build.PRODUCT,
            "Build.serial": Build.SERIAL,
            "Build.radio": Build.getRadioVersion(),
            "Xtra": kwargs
        })
    elif platform == 'ios':
        raven_client.user_context({
            "ProcessName": processInfo.processName.cString(),
            "HostName": processInfo.hostName.cString(),
            "OS Version": processInfo.operatingSystemVersionString.cString(),
            "ProcessorCount": processInfo.processorCount,
            "DeviceName": currentDevice.name.cString(),
            "SystemName": currentDevice.systemName.cString(),
            "UI Idiom": currentDevice.userInterfaceIdiom,
            "Orientation": currentDevice.orientation,
            "SystemVersion": currentDevice.systemVersion.cString(),
            "DeviceModel": currentDevice.model.cString(),
            "LocalizedModel": currentDevice.localizedModel.cString(),
            "IdentifierForVendor": currentDevice.identifierForVendor.UUIDString().cString(),
            "BatteryState": currentDevice.batteryState,
            "Xtra": kwargs
        })
        try:
            raven_client.captureException()
        except Exception as e:
            pass
            # print "here is the exception: ", e



class AppixApp(App):

    def __init__(self):
        super(AppixApp, self).__init__()
        self.appix_version = __version__
        self.appix_beacon_key = appix_beacon_key
        self.service_running = False
        self.show_started = False
        Window.bind(on_keyboard=self.on_back_button)
        # self.bluetooth_available = False
        self.initiated = False
        self.DEBUG = DEBUG
        self.ADMIN_APP = ADMIN_APP

        #Start checking for updates on app start. The job will only be scheduled once.
        UpdateManager = autoclass('com.appix.update.UpdateManager')
        PythonActivity = autoclass('org.renpy.android.PythonActivity')
        updateManager = UpdateManager(PythonActivity.mActivity)
        updateManager.setUpdateSchedule()

    def app_update_android(self):
        try:
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            PythonActivity = autoclass('org.renpy.android.PythonActivity')
            intent = Intent(Intent.ACTION_VIEW, Uri.parse(appix_google_play_url))
            PythonActivity.mActivity.startActivity(intent)

        except TypeError:
            pass

    def app_update_ios(self):
        from pyobjus import objc_str
        url = appix_itunes_url
        UIApplication = autoclass("UIApplication")
        NSURL = autoclass("NSURL")
        objc_str = objc_str
        nsurl = NSURL.alloc().initWithString_(objc_str(url))
        UIApplication.sharedApplication().openURL_(nsurl)


    def on_url_success(self, req, results):
        if self.DEBUG:
            print "on_url_success", req, results
        server_version = "0"
        # print "version", version
        for key, value in results.items():
            if key == "version":
                # print key, value
                server_version = value
        if LooseVersion(server_version) > LooseVersion(self.appix_version):
            if platform == "android":
                self.app_update_android()
                pass
            else:
                self.app_update_ios()
                pass

    def on_url_redirect(self, *args):
        if self.DEBUG:
            print "on_url_redirect", args
        pass

    def on_url_error(self, *args):
        if self.DEBUG:
            print "on_url_error", args
        pass

    def on_url_progress(self, *args):
        if self.DEBUG:
            print "on_url_progress", args
        pass

    def on_url_failure(self, *args):
        if self.DEBUG:
            print "on_url_failure", args
        pass

    # ##### End version check


    def on_pause(self):
        try:
            try:
                self.appix_base.solid_layer.clear_stage()
                self.appix_base.add_status_label()
            except AttributeError:
                pass
            if platform == "android":
                # pass
                if self.comm_layer.isRunning():
                    self.comm_layer.setAppInBackground(True)
                self.flash_torch.release()
            if self.DEBUG:
                print 'PAUSING APP'
        except Exception as e:
            print "pause failed", e
            pass
        finally:
            try:
                self.comm_layer.send_message('pause')
                return True
            except AttributeError:
                return True

    def on_resume(self):
        try:
            if platform == "android":
               # print "RESUMING APP, BLUETOOTH AVAILABLE?", self.bluetooth_available
                if self.comm_layer.isRunning():
                    #self.comm_layer.send_message('resume')
                    self.comm_layer.setAppInBackground(False)

                # put bool bluetooth notify window active here so it doesn't trigger on_resume function

        except AttributeError:
            print "ERROR 1"
            pass
        try:
            self.appix_base.solid_layer.clear_stage()
        except AttributeError:
            print "ERROR 2"
            pass



    def on_back_button(self, window, key, *args):
        """ To be called whenever user presses Back/Esc Key """
        # If user presses Back/Esc Key
        if key == 27:
            if self.show_started:
                self.appix_base.goto_home_screen()
                return True
            # movetasktoback
            if platform == 'android':
                from jnius import cast
                from jnius import autoclass
                PythonActivity = autoclass('org.renpy.android.PythonActivity')
                currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
                currentActivity.moveTaskToBack(True)
                return True
            # return True if you don't want to close app
            # return False if you do


    def on_stop(self):
        print "STOPPING"
        if platform == "android":
            self.flash_torch.release()
            self.comm_layer.stop()

    # def on_activity_result(self, request_code, result_code, intent):
    #     if request_code == 200:
    #         if result_code == -1:
    #             Clock.schedule_once(self.appix_base.start_show, 0.5)
    #     return


    def restart_service(self):
        if platform == 'android':
            print "SERVICE RESTARTING"
            # self.comm_layer.stop()
            #self.comm_layer.send_message('stop')
            self.comm_layer.stop()
            del self.comm_layer
            # self.service_running = Fal
            print "SERVICE STOPPED"
            sleep(2)
            self.initiate_service()


    def start_service(self):
        if platform == 'android':
            # from android import activity
            # activity.bind(on_activity_result=self.on_activity_result)
            # If service is not already running, `service_running`
            # would be false.
            if not self.comm_layer.isRunning():
                #from android import AndroidService
                #service = AndroidService('Appix', 'Be The Show')
                #service.start('service started')
                self.comm_layer.startService()
                print "SERVICE STARTED"

    def initiate_service(self):
        print "SERVICE ABOUT TO INITIATE"
        if platform == 'android':
            from jnius import cast
            AndroidBtManager = autoclass('com.appix.bt.AndroidBTManager')
            PythonActivity = autoclass('org.renpy.android.PythonActivity')
            currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
            self.comm_layer = AndroidBtManager(currentActivity)
            self.comm_layer.enableBluetooth()
            #self.comm_layer = AppixComm()
            #self.comm_layer.listen()
            #self.comm_layer.send_message('enable_bluetooth')
            # initiate a communication layer
            # start listening on the comm layer for Appix App
            # send a message to the service to check if the
            # service is already running.
            #self.comm_layer.send_message('is_running?')
            # use a clock to start service as if the service is already
            # running, the comm layer will set `service_running` to True.
            # by that time.
            print "SERVICE INITIATED"
            self.start_service()
            #Clock.schedule_once(lambda dt: self.start_service(), 1)




    def build(self):
        # version_check = UpdateAppVersion()
        # print "version_check", version_check

        self.req = UrlRequest('http://www.appixapp.com/app/appix-config.json',
                              on_success=self.on_url_success,
                              on_failure=self.on_url_failure,
                              on_progress=self.on_url_progress,
                              on_error=self.on_url_error,
                              debug=True)

        # print "self.req", self.req
        # print "version_check.start_version_request()", version_check.start_version_request()

        if platform == "android":

            self.android_screen_manager = android_hardware.AndroidScreenManager()
            self.android_screen_manager.set_screen_on_flag()

            self.android_vibrator = android_hardware.Vibrator()
            self.flash_torch = android_hardware.FlashTorch()

            if BuildVERSION.SDK_INT >= 18:    # Go-Live is 18, TODO add restricted device list to this
                if not event_expired():
                    # self.comm_layer = AppixComm()
                    #


                    # put bool bluetooth notify window active here so it doesn't trigger on_resume function




                    android_bluetooth.check_bluetooth_enabled(True)

                    # print " "
                    # print "RESULT", bluetooth_result
                    # print " "
                    # if bluetooth_result:
                        # self.bluetooth_available = True
                        # self.initiate_service()
                    self.appix_base = appix.AppixBase()

                    # self.comm_layer.listen()
                    # self.comm_layer.send_message('enable_bluetooth')
                    # initiate a communication layer
                    # start listening on the comm layer for Appix App
                    # send a message to the service to check if the
                    # service is already running.
                    # self.comm_layer.send_message('is_running?')
                    # use a clock to start service as if the service is already
                    # running, the comm layer will set `service_running` to True.
                    # by that time.
                    # Clock.schedule_once(lambda dt: self.start_service(), 1)
                    return self.appix_base
                else:
                    return appix.ScreenMessage('expired')

            else:
                return appix.ScreenMessage('incompatible')

                # if self.DEBUG:
                #     print "Appix is not compatible with this device"
                # return Label(text="Appix is not compatible with this device")


        # Boot up as iOS
        elif platform == "ios":

            if not event_expired():
                # keeps the screen alive
                UIApplication = autoclass("UIApplication")
                UIApplication.sharedApplication().setIdleTimerDisabled_(True)

                self.ios_vibrator = ios_hardware.vibrator()
                # print "Vibrator:", self.ios_vibrator

                self.flash_torch = ios_hardware.IosFlashTorch()

                # CoreBluetooth
                from service.bt import AppixBT
                self.ios_bluetooth = AppixBT

                # self.core_bluetooth = ios_bluetooth.CoreBluetoothScanner()
                # self.core_bluetooth.bind(
                #     on_state=self.core_bluetooth.on_corebluetooth_state,
                #     on_peripheral=self.core_bluetooth.on_corebluetooth_peripheral)

                self.appix_base = appix.AppixBase()

                return self.appix_base
            else:
                return appix.ScreenMessage('expired')



if LIVE_DEPLOY:
    try:
        AppixApp().run()
    except Exception as e:
        handle_error_request(Appix_Version=__version__)
else:
    AppixApp().run()



# try:
#     AppixApp().run()
# except Exception as e:
#     if LIVE_DEPLOY:
#         handle_error_request(Appix_Version=__version__)
#     else:
#         print e
#         pass
