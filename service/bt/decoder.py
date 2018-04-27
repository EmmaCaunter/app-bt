from kivy.event import EventDispatcher
import time

class BluetoothDecoder(EventDispatcher):

    def __init__(self, **kwargs):
        super(BluetoothDecoder, self).__init__(**kwargs)

    def decode_beacon_data(self, beacon_data):
        decoded_data = {"message_type": -1}
        return decoded_data
