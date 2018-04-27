package appix.appix.com.appixandroidbtlibrary;

import android.content.Intent;
import android.app.Activity;
import android.content.Context;
import android.content.ComponentName;
import android.content.ServiceConnection;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothAdapter;
import android.os.IBinder;
import android.util.Log;
import java.util.Arrays;

public class AndroidBTManager implements BTScanCallback {

    private static byte[] appixBeaconKey = { (byte)0xBA, (byte)0x11, (byte)0x50 };
    private static String hexConv = "0123456789abcdef";

    private BluetoothLEService btService;
    boolean mBound;
    private Activity activity;
    private long timeSinceAppPaused;

    private byte[] previousMessage;

    private MessageReceivedListener messageListener;

    public BTConfig btConfig = new BTConfig();

    public AndroidBTManager(Activity activity) {
        this.activity = activity;
    }

    public void start() {
        if (checkConnection()) {
            btService.start();
        }
    }

    public void setMessageListener(MessageReceivedListener listener) {
        this.messageListener = listener;
    }

    public boolean isStandbyMode() {
        if (checkConnection()) {
            return this.btService.isStandbyMode();
        }
        return true;
    }

    public void missedInstruction() {
        Log.e("BT MANAGER", "Missed Instruction");
        if (checkConnection()) {
            this.btService.restart();
        }
    }

    public void heartbeatTimeout() {
        Log.e("BT MANAGER", "Heartbeat Timeout");
        if (checkConnection()) {
            this.btService.restart();
        } else {
            startService();
        }
    }

    public void onScanResult(BluetoothDevice device, int rssi, byte[] scanRecord) {
        byte[] beaconKey = { scanRecord[13], scanRecord[14], scanRecord[15] };
        if (Arrays.equals(beaconKey, appixBeaconKey)) {
            byte[] uuid = Arrays.copyOfRange(scanRecord, 13, 29);
            if (!Arrays.equals(uuid, previousMessage)) {

                this.previousMessage = uuid;
                this.timeSinceAppPaused = 0;
                boolean sendNotification;
                if (this.btService.isInBackground()) {
                    Log.e("MEssager", "Message Listener is dead");
                    sendNotification = quickDecode(uuid, rssi);
                } else {
                    sendNotification = messageListener.onMessageReceived(scanRecord, rssi);

                }
                if (sendNotification) {
                    this.btService.createNotification("We're Back!", "Join the show?");
                }
            }

        }

    }

    public int[] bytesToHex(byte[] bytes) {
        int[] hexChars = new int[bytes.length * 2];
        for ( int j = 0; j < bytes.length; j++ ) {
            int v = bytes[j] & 0xFF;
            hexChars[j * 2] = v >>> 4;
            hexChars[j * 2 + 1] = v & 0x0F;
        }
        return hexChars;
    }

    private boolean quickDecode(byte[] uuid, int rssi) {
        int[] hex = bytesToHex(uuid);
        int messageType = hex[btConfig.messageIndex];
        int locationMode = hex[btConfig.locationIndex];
        int vibrationCode = hex[btConfig.vibrationIndex];
        Log.e("message type", "type: " + messageType);
        if (messageType == btConfig.heartbeat) {
            Log.e("Heartbeat", "Heartbeat");
            if (locationMode == btConfig.shortStandby) {
                Log.e("Heartbeat", "Short Standby");
                btService.setStandbyMode(btConfig.shortDuration);
            } else if (locationMode == btConfig.longStandby) {
                Log.e("Heartbeat", "Long Standby");
                btService.setStandbyMode(btConfig.shortDuration);
            } else {
                btService.wakeUpScan();
            }
        } else if (messageType == btConfig.play || messageType == btConfig.playPhrase || messageType == btConfig.playDynamic ||
                messageType == btConfig.phraseDynamic || messageType == btConfig.flash || messageType == btConfig.sports) {
            Log.e("play", "play");
            return true;
        } else if (messageType == btConfig.vibrations && vibrationCode == btConfig.vibrateOn) {
            return true;
        }
        return false;
    }

    public void setStandbyMode(int timeout) {
        if (mBound) {
            this.btService.setStandbyMode(timeout);
        } else {
            startService();
        }
    }

    public void wakeUpScan() {
        if (mBound) {
            this.btService.wakeUpScan();
        } else {
            startService();
        }
    }

    public void setBTConfig() {
        if (mBound) {
            Log.e("Setting", "BT Config");
            this.btService.setBTConfig(this.btConfig);
        }
    }

    public void enableBluetooth() {
        BluetoothAdapter mBluetoothAdapter = BluetoothAdapter.getDefaultAdapter();
        if (mBluetoothAdapter == null) {
            // Device does not support Bluetooth
        } else {
            if (!mBluetoothAdapter.isEnabled()) {
                // Bluetooth is not enabled :)
            } else {
                Log.e("Bluetooth", "Enabled");
            }
        }
    }

    public boolean isRunning() {
        return mBound;
    }

    public void stop() {
        if (mBound) {
            btService.stop();
            this.activity.unbindService(mConnection);
            mBound = false;
        }
    }

    public void setAppInBackground(boolean appInBackground) {
        if (this.btService != null) {
            this.btService.setAppInBackground(appInBackground);
        }
    }

    public void startService() {
        Intent intent = new Intent(this.activity, BluetoothLEService.class);
        this.activity.bindService(intent, mConnection, Context.BIND_AUTO_CREATE);
    }

    private boolean checkConnection() {
        if (mBound) {
            return true;
        }
        startService();
        return false;
    }

    private ServiceConnection mConnection = new ServiceConnection() {

        @Override
        public void onServiceConnected(ComponentName className,
                IBinder service) {
            // We've bound to LocalService, cast the IBinder and get LocalService instance
            Log.e("BOund", "SERVICE");
            BluetoothLEService.LocalBinder binder = (BluetoothLEService.LocalBinder) service;
            btService = binder.getService();
            mBound = true;
            btService.setCallback(AndroidBTManager.this);
            btService.setActivity(AndroidBTManager.this.activity);
            btService.setBTConfig(btConfig);
            btService.start();

        }

        @Override
        public void onServiceDisconnected(ComponentName arg0) {
            Log.e("UNBOund", "SERVICE");
            mBound = false;
            startService();
        }
    };

}