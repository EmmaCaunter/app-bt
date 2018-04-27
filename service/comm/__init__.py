'''Communication layer for communicating
between the service and app. This is the service Communication layer
'''
from time import sleep
from plyer.platforms.android import SDK_INT
from plyer.utils import platform
from kivy.lib import osc
from kivy.app import App
import threading
if platform == 'android':
    from jnius import autoclass, cast
    from android import python_act
import os
import ast
from datetime import datetime

import time

service = None


# ------------------  CHANGE FOR RELEASE ------------------

DEBUG = True
ADMIN_APP = True

# ------------------  CHANGE FOR RELEASE ------------------



try:
    PythonService = autoclass('org.renpy.android.PythonService')
    # actm = cast('android.app.ActivityManager', service.getSystemService('activity'))
    service = PythonService.mService
    from bt import AppixBT
except Exception:
    pass

from subprocess import check_output
import weakref


class AppixComm(object):

    def read_message(self, app_code, *args):

        # millis = int(round(time.time() * 1000))
        # print "2. read message", millis
        
        if app_code[0] != '/AppixCom':
            return

        message = ''.join(app_code[2:])
        # try:
        #     print(
        #         'app' if service else 'service'
        #          + ' got message: {}'.format(message))
        # except IndexError:
        #     print "SAVED FROM PRINT ERROR"
        #     pass


        if service:
            if message == 'pause':
                self.appixservice._app_state = 'paused'
                AppixBT._last_notification_time = datetime.now()
                # AppixBT.refresh_bluetooth()
                # self.app_state = 'paused'
                return
            if message == 'resume':
                self.time_since_app_paused = 0
                self.appixservice._app_state = 'running'
                # self.app_state = 'running'
                AppixBT.allow_notification = True
                AppixBT.restart_bluetooth()
                return
            if message == 'heartbeat_timeout' or message == 'missed_instruction':
                AppixBT.restart_bluetooth()
                # AppixBT.restart_service()
                return
            if message == 'is_running?':
                self.send_message('{"running": True}')
                return
            if message == 'refresh_bluetooth' and service:
                AppixBT.restart_bluetooth()
                # AppixBT.restart_service()
                return
            if message == 'stop':
                print "STOPPING SERVICE"
                # stop this service
                # self.appixservice.clean_up()
                self.stop()
        else:
            # Not service
            app = App.get_running_app()

            if message == 'start_show':
                app.appix_base.start_show()
                return

            if message == '{"running": True}':
                # App comm layer is up and running.
                app_running = True
                return

            if 'rssi' in message:
                msg = ast.literal_eval(message)
                app.appix_base.update_data_labels(msg["data"], msg["rssi"])

            if 'message_type' in message:
                # millis = int(round(time.time() * 1000))
                # print "3. send data", millis
                # print "SENDING MESSAGE"
                app.appix_base.run_bluetooth_commands(ast.literal_eval(message))
                # print "SENT MESSAGE"
                # millis = int(round(time.time() * 1000))
                # print "4. done data", millis

            if message == 'stop':
                if platform == 'android':
                    python_act.mActivity.finish()

    def send_message(self, message, *args):
        # print(
        #     ('app' if not service else 'service')+
        #    ' sending message: {}'.format(message))
        #  print " "
        # print " "
        #  print message

        # if 'message_type' in message:
        #     # print " "
        #     # print "DATA CHECKS OUT"
        #     # print " "
        #     app = App.get_running_app()
        #     millis = int(round(time.time() * 1000))
        #     print "1. send data", millis
        #     app.appix_base.run_bluetooth_commands(ast.literal_eval(message))
        #     millis = int(round(time.time() * 1000))
        #     print "2. done data", millis
        # millis = int(round(time.time() * 1000))
        # print "1. send message", millis
        osc.sendMsg('/AppixCom', message, port=self.send_port)

    def __init__(self, **kwargs):
        if platform == 'android':
            sp = {'service':3000, 'app':3001}
            serv = 'APPIX_SERVICE' in os.environ
            self.send_port = sp['service' if serv else 'app']
            self.listen_port = sp['service' if not serv else 'app']
            print self.listen_port, 'port', serv,  'APPIX_APP' in os.environ
            super(AppixComm, self).__init__()
            osc.init()
            self.keep_listening = False
            self.oscid = osc.listen(ipAddr='127.0.0.1', port=self.listen_port)
            osc.bind(self.oscid, self.read_message, '/AppixCom')
            self.bluetooth_standby_time = 0
            self.app = App.get_running_app()
            self.time_since_app_paused = 0

            self.debug = DEBUG
            self.admin_app = ADMIN_APP


    def listen(self):
        if self.keep_listening:
            return
        self.keep_listening = True
        t = threading.Thread(target=self._listen)
        t.daemon = True
        t.start()


    def _listen(self):
        # Logger.debug('Appix: started and listening')
        count = 0
        while self.keep_listening:
            osc.readQueue(self.oscid)
            #print osc.readQueue(self.oscid)
            sleep(.1)
            count += 1
            if count >= 20:
                count = 0
                # if service and not self.is_app_running():
                #     self.stop()
                #     break
                # print " "
                # print " "
                # print os.environ
                # print " "
                # print " "

                if service and "APPIX_SERVICE" in os.environ and not self.is_app_running():
                    self.keep_listening = False
                    self.stop()
                    break
            if not service:
                #print '>>', autoclass('android.os.Process').myPid(), '<<'
                continue
            self.bluetooth_standby_time -= 1
            # print "self.bluetooth_standby_time", self.bluetooth_standby_time
            if self.bluetooth_standby_time == 0:
                AppixBT.initiate_bluetooth()


    # def _listen(self):
    # # Logger.debug('Appix: started and listening')
    #     while self.keep_listening:
    #         osc.readQueue(self.oscid)
    #         #print osc.readQueue(self.oscid)
    #         sleep(.1)
    #         if not service:
    #             continue
    #         if self.appixservice._app_state == 'paused':
    #             self.time_since_app_paused += 1
    #             # print self.time_since_app_paused
    #             if SDK_INT < 22 and self.time_since_app_paused >= 180000:
    #                 self.stop()
    #         self.bluetooth_standby_time -= 1
    #         if self.bluetooth_standby_time == 0:
    #             self.appix_service.bt_service.initiate_bluetooth()

    # def _listen(self):
    #     # Logger.debug('Appix: started and listening')
    #     count = 0
    #     while self.keep_listening:
    #         osc.readQueue(self.oscid)
    #         #print osc.readQueue(self.oscid)
    #         sleep(.1)
    #         count += 1
    #         if count >= 20:
    #             count = 0
    #             # if service and not self.is_app_running():
    #             #     self.stop()
    #             #     break
    #             # print " "
    #             # print " "
    #             # print os.environ
    #             # print " "
    #             # print " "
    #
    #             if service and "APPIX_SERVICE" in os.environ and not self.is_app_running():
    #                 self.keep_listening = False
    #                 self.stop()
    #                 break
    #         if not service:
    #             continue
    #         self.bluetooth_standby_time -= 1
    #         # print "self.bluetooth_standby_time", self.bluetooth_standby_time
    #         if self.bluetooth_standby_time == 0:
    #             AppixBT.initiate_bluetooth()

    # def _listen(self):
    #     print('Appix: started and listening')
    #     count = 0
    #     while self.keep_listening:
    #         osc.readQueue(self.oscid)
    #         sleep(.1)
    #         count += 1
    #         # print count
    #         if count >= 20:
    #             count = 0
    #             if "APPIX_SERVICE" in os.environ and not self.is_app_running():
    #                 self.keep_listening = False
    #                 self.stop()
    #                 break

    # def is_app_running(self):
    #     for package in check_output('ps').split():
    #
    #         # print " "
    #         # print "PACKAGE", package
    #         # print " "
    #
    #         if package == 'com.appix.appix:python':
    #             # print('Appix: Appix Application is running')
    #             return True
    #     print('APPIX: Application is no longer running')
    #     return False


    def is_app_running(self):
        # if self.debug:
            # return True
        actm = cast('android.app.ActivityManager', service.getSystemService('activity'))
        itr = actm.getRunningAppProcesses().iterator()
        while itr.hasNext():
            name = itr.next().processName.lower()
            if 'appix' in name and 'service' not in name:
                return True
        print('Appix: Appix Application is no longer running')
        return False




    # def stop(self):
    #     print('CSG Pixels: Exiting service')
    #     self.keep_listening = False
    #     if service:
    #         AppixBT.close_all_notifications()
    #         #self.appixservice.stop_service = True
    #         service.onDestroy()
    #         return
    #     # self.app.stop()


    def stop(self):
       #  Logger.debug('Appix: Exiting service')

        self.keep_listening = False
        if self.app:
            self.app.stop()
            return
        if service:
            self.appixservice.bt_service.close_all_notifications()
            self.appixservice.stop_service = True
            service.onDestroy()
            return