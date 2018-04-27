from kivy.event import EventDispatcher
from jnius import PythonJavaClass, java_method, autoclass
from android.runnable import run_on_ui_thread

# Standard Libs
import time

Context = autoclass('android.content.Context')
PythonActivity = autoclass('org.renpy.android.PythonActivity')
PackageManager = autoclass('android.content.pm.PackageManager')
Activity = PythonActivity.mActivity


class AndroidScreenManager(EventDispatcher):

    # from https://gist.github.com/kived/4b3c1a78b0104e52b2a1

    View = autoclass('android.view.View')
    Params = autoclass('android.view.WindowManager$LayoutParams')

    def __init__(self):
        super(AndroidScreenManager, self).__init__()

    @run_on_ui_thread
    def android_setflag(self):
        PythonActivity.mActivity.getWindow().addFlags(self.Params.FLAG_KEEP_SCREEN_ON)
        print "Set Screen Flag"

    def set_screen_on_flag(self, *args):
        self.android_setflag()

    @run_on_ui_thread
    def android_clearflag(self):
        PythonActivity.mActivity.getWindow().clearFlags(self.Params.FLAG_KEEP_SCREEN_ON)
        print "Remove Screen Flag"

    def clearflag(self, *args):
        self.android_clearflag()


# ### Vibrate ###

class Vibrator(EventDispatcher):

    vibratorService = Activity.getSystemService(Context.VIBRATOR_SERVICE)

    def __init__(self):
        super(Vibrator, self).__init__()

    def vibrate(self, pattern, repeat, command, *args):
        if self.vibratorService.hasVibrator():
            if command:
                self.vibratorService.vibrate(pattern, repeat)
            else:
                self.vibrator_service.cancel()
        else:
            # print("Your device does not have a vibration motor.")
            pass


# ### Flash Torch ###

class FlashTorch(EventDispatcher):

    Camera = autoclass('android.hardware.Camera')
    CameraParameters = autoclass('android.hardware.Camera$Parameters')
    SurfaceTexture = autoclass('android.graphics.SurfaceTexture')
    pm = Activity.getPackageManager()
    flash_available = pm.hasSystemFeature(PackageManager.FEATURE_CAMERA_FLASH)
    # print "flash available:", flash_available

    def __init__(self):
        super(FlashTorch, self).__init__()
        self.cam = None

    def open_camera(self):
        if not self.cam:
            # print "OPENING CAMERA"
            self.cam = self.Camera.open()
            # print self.cam
            self.f_on = self.cam.getParameters()
            self.f_off = self.cam.getParameters()
            self.f_on.setFlashMode(self.CameraParameters.FLASH_MODE_TORCH)
            self.f_off.setFlashMode(self.CameraParameters.FLASH_MODE_OFF)
            self.cam.setParameters(self.f_off)
            self.cam.startPreview()
            self.cam.setPreviewTexture(self.SurfaceTexture(0))  # Need this for Nexus 5


    def flash(self, command, *args):
        if not self.cam and command:
            self.open_camera()
            print "OPENED CAMERA"
            return
        try:
            if command:
                self.cam.setParameters(self.f_on)
            else:
                self.cam.setParameters(self.f_off)
        except AttributeError:
            pass


    def release(self):
        try:
            self.cam.stopPreview()
            self.cam.release()
            self.cam = None
            print "CAMERA RELEASED"
        except AttributeError:
            # print "CAMERA RELEASE SAVED"
            pass


