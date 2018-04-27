package appix.appix.com.appixandroidbtlibrary;

import android.bluetooth.BluetoothDevice;

public interface BTScanCallback {

    void onScanResult(BluetoothDevice device, int rssi, byte[] scanRecord);

}