'''This is the service part that is responsible for::

1) Communicating with the main app
2) Starting and managing the bluetooth service for the main app


'''

import os
os.environ['APPIX_SERVICE'] = 'True'
import time
from comm import AppixComm
from bt import AppixBT
import weakref
from plyer.utils import platform


class AppixService(object):
    '''
    '''

    def __init__(self, **kwargs):
        if platform == 'android':
            self.stop_service = False
            self._app_state = 'running'
            super(AppixService, self).__init__()

            # Service is not running
            self.comm_service = AppixComm()
            AppixBT.appixservice = weakref.proxy(self)
            AppixBT.initiate_bluetooth()

            self.bt_service = AppixBT
            # use a weakref here to avoid circular deps
            self.comm_service.appixservice = weakref.proxy(self)
            self.comm_service.listen()
            self.run_service()

    def run_service(self):

        while not self.stop_service:
            time.sleep(.001)
            if not AppixBT.btAdapter.isEnabled():
                AppixBT.btAdapter.enable()

        self.clean_up()

    def clean_up(self):
        # clean up service here'
        self.comm_service.stop()
        self.bt_service.stop()
        


if __name__ == '__main__':
    AppixService()