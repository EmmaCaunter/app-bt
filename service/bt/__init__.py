'''Appix Bluetooth Service
'''

import os
appixbt = None
DEBUG = True
from plyer.utils import platform

# print 'APPIX_SERVICE' in os.environ, 'APPIX_APP' in os.environ, 'service/app'
if 'APPIX_SERVICE' in os.environ and 'ANDROID_DATA' in os.environ:
    from jnius import autoclass
    import android_bluetooth
    appixbt = android_bluetooth.AndroidBLEScanReader()

elif platform == "ios":
    from . import ios_bluetooth
    appixbt = ios_bluetooth.CoreBluetoothScanner()

AppixBT = appixbt
