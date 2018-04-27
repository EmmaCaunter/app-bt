'''Implementation Vibrator for iOS.

Install: Add AudioToolbox framework to your application.
'''

import ctypes
from plyer.facades import Vibrator  # TODO: INSTALL PLYER
from kivy.event import EventDispatcher

class IosVibrator(Vibrator):
    '''iOS Vibrator class.

    iOS doesn't support any feature.
    All times, patterns, repetition are ignored.
    '''

    def __init__(self):
        super(IosVibrator, self).__init__()
        try:
            self._func = ctypes.CDLL(None).AudioServicesPlayAlertSound  #(1352)
        except AttributeError:
            self._func = None

    def vibrate(self, time=None, **kwargs):
        # kSystemSoundID_Vibrate is 0x00000FFF
        self._func(0xFFF)

    def pattern(self, pattern=None, repeat=None, **kwargs):
        self._vibrate()

    def exists(self, **kwargs):
        return self._func is not None

    def cancel(self, **kwargs):
        pass


def vibrator():
    '''Returns Vibrator

    :return: instance of class IosVibrator
    '''
    return IosVibrator()



"""
iOS Torch
=========
"""

from pyobjus import autoclass
from kivy.utils import platform

if platform == "macosx":
    from pyobjus.dylib_manager import load_framework, INCLUDE
    load_framework(INCLUDE.AVFoundation)

NSString = autoclass("NSString")
AVCaptureDevice = autoclass("AVCaptureDevice")
AVMediaTypeVideo = NSString.alloc().initWithUTF8String_("vide")
AVCaptureTorchModeOff = 0
AVCaptureTorchModeOn = 1


class IosFlashTorch(EventDispatcher):

    def __init__(self, **kwargs):
        super(IosFlashTorch, self).__init__(**kwargs)
        self.device = AVCaptureDevice.defaultDeviceWithMediaType_(AVMediaTypeVideo)
        if not self.device:
            # print "ERROR: No video device found"
            return
        # if not device.hasTorch():
        #    print "ERROR: Default video device have no torch"
        #    return

    def flash(self, command, *args):
        self.device.lockForConfiguration_(None)
        try:
            if command:
                self.device.setTorchMode_(AVCaptureTorchModeOn)
            else:
                self.device.setTorchMode_(AVCaptureTorchModeOff)
        finally:
            self.device.unlockForConfiguration()





# def set_torch_level(level):
#     device = AVCaptureDevice.defaultDeviceWithMediaType_(AVMediaTypeVideo)
#     if not device:
#         print "ERROR: No video device found"
#         return
#     #if not device.hasTorch():
#     #    print "ERROR: Default video device have no torch"
#     #    return
#     device.lockForConfiguration_(None)
#     try:
#         if level <= 0:
#             device.setTorchMode_(AVCaptureTorchModeOff)
#         else:
#             device.setTorchMode_(AVCaptureTorchModeOn)
#     finally:
#         device.unlockForConfiguration()


# if __name__ == "__main__":
#     import time
#     for x in range(1):
#         set_torch_level(0)
#         time.sleep(.5)
#         set_torch_level(1)
#         time.sleep(.5)
