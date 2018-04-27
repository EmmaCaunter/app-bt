package appix.appix.com.appixandroidbtlibrary;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothManager;
import android.app.Service;
import android.app.Activity;
import android.content.Context;
import android.bluetooth.BluetoothDevice;
import no.nordicsemi.android.support.v18.scanner.BluetoothLeScannerCompat;
import no.nordicsemi.android.support.v18.scanner.ScanCallback;
import no.nordicsemi.android.support.v18.scanner.ScanSettings;
import no.nordicsemi.android.support.v18.scanner.ScanResult;
import no.nordicsemi.android.support.v18.scanner.ScanFilter;
import android.util.Log;
import android.os.Handler;
import android.os.Looper;
import java.lang.System;
import android.app.Notification;
import android.content.Intent;
import android.app.NotificationManager;
import android.os.Binder;
import android.os.IBinder;
import java.lang.Runnable;
import java.lang.Thread;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.IntentFilter;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import android.os.ParcelUuid;

public class BluetoothLEService extends Service {

    // Eddystone UID Service
    private ParcelUuid UID_SERVICE;

    //Default namespace id for Appix Eddystone beacons (ba1150...)
    private byte[] NAMESPACE_FILTER = {
        (byte) 0x00,  // Type = UID
        (byte) 0x00,  // Tx Power
        (byte) 0xBA, (byte) 0x11, (byte) 0x50,  // The only parts we care about
        (byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x00,
        (byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x00
    };

    //Force frame type and namespace id to match
    private byte[] NAMESPACE_FILTER_MASK = {
        (byte) 0xFF,
        (byte) 0x00,
        (byte) 0xFF, (byte) 0xFF, (byte) 0xF0,  // or maybe 0xFF, 0xFF, 0xF0 ?
        (byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x00,
        (byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x00
    };

    private static String CANCEL_NOTIFICATION = "CancelNotification";
    private static String OPEN_APPLICATION = "OpenApplication";

    private Activity activity;
    public BluetoothAdapter btAdapter;
    public long last_notification_time;
    private boolean newApi;
    public boolean allowNotification = true;
    public static long NOTIFICATION_TIMEOUT;

    private BTScanCallback callback;
    private IBinder mBinder = new LocalBinder();
    private Thread serviceThread;
    private BroadcastReceiver broadcastReceiver;
    private boolean appInBackground = false;

    private int currentScanTime;
    private int currentSleepTime;
    private int minuteScanTime;

    private Handler startHandler;
    private Handler stopHandler;
    private List<ScanFilter> scanFilters;
    private ScanSettings scanSettings;
    private ScanningMode scanningMode = ScanningMode.MINUTE;
    private BTConfig btConfig;

    private ScanCallback scanCallback = new ScanCallback() {
                @Override
                public void onScanResult(int callbackType, ScanResult result) {
                    // get the discovered device as you wish
                    // this will trigger each time a new device is found
                    BluetoothDevice device = result.getDevice();
                    int rssi = result.getRssi();
                    byte[] scanRecord = result.getScanRecord().getBytes();
                    callback.onScanResult(device, rssi, scanRecord);
                }
            };

    public BluetoothLEService() {

    }

    public BluetoothLEService(BTScanCallback scanCallback) {
        this.callback = scanCallback;
    }

    public void setCallback(BTScanCallback scanCallback) {
        this.callback = scanCallback;
    }

    public void setBTConfig(BTConfig config) {
        Log.e("Set", "Bt config uuid: " + config.uuid);
        this.btConfig = config;
        this.UID_SERVICE = ParcelUuid.fromString(this.btConfig.uuid);
        if (this.btConfig.debugMode) {
            Log.e("Debug", "Debug Settings");
            NOTIFICATION_TIMEOUT = this.btConfig.debugNotificationTimeout;
            this.currentScanTime = this.btConfig.debugDuration;
            this.currentSleepTime = this.btConfig.debugDuration;
            this.minuteScanTime = this.btConfig.debugMinuteDuration;
        } else {
            Log.e("Release", "Release Settings");
            NOTIFICATION_TIMEOUT = this.btConfig.notificationTimeout;
            this.currentScanTime = this.btConfig.shortDuration;
            this.currentSleepTime = this.btConfig.shortDuration;
            this.minuteScanTime = this.btConfig.minuteDuration;
        }
    }

    private void setConfiguration() {
        this.UID_SERVICE = ParcelUuid.fromString(this.btConfig.uuid);
    }

    public boolean isStandbyMode() {
        return this.scanningMode == ScanningMode.STANDBY;
    }

    public void setStandbyMode(int timeout) {
        if (this.scanningMode != ScanningMode.STANDBY) {
            this.scanningMode = ScanningMode.STANDBY;
            this.currentSleepTime = timeout;
            this.currentScanTime = timeout;
            restartBluetooth();
            Log.e("Sleep", "IN STANDBY MODE: " + timeout);
        }
    }

    public void wakeUpScan() {

        if (scanningMode == ScanningMode.STANDBY || scanningMode == ScanningMode.MINUTE) {
            Log.e("Wake", "WAKE UP SCAN");
            scanningMode = ScanningMode.SCAN;
            this.stopHandler.removeCallbacksAndMessages(null);
            stopScan();
            startScan();
        }
    }

    public void start() {
        startForeground(0, getServiceNotification());
        serviceThread = new Thread(new Runnable() {

            @Override
            public void run() {
                Log.e("Running", "Thread");
                startHandler = new Handler(Looper.getMainLooper());
                stopHandler = new Handler(Looper.getMainLooper());
                scanFilters = new ArrayList<ScanFilter>();
                scanFilters.add(new ScanFilter.Builder().setServiceData(UID_SERVICE, NAMESPACE_FILTER,
                                                               NAMESPACE_FILTER_MASK).build());
                scanSettings = new ScanSettings.Builder().setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY).build();
                stopScan();     // stop any handlers running
                startScan();
            }

        });
        serviceThread.setDefaultUncaughtExceptionHandler(new ExceptionLogHandler());
        serviceThread.start();
    }

    private Notification getServiceNotification() {
        Notification.Builder builder = new Notification.Builder(this)
         .setContentTitle("Appix")
         .setContentText("Bluetooth Service")
         .setSmallIcon(R.drawable.icon);

        return builder.build();
    }

    @Override
    public void onCreate() {

    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        Log.i("LocalService", "Received start id " + startId + ": " + intent);
        return START_NOT_STICKY;
    }

    @Override
    public void onDestroy() {
        Log.e("destroying", "Service");
        this.activity.unregisterReceiver(broadcastReceiver);
        stop();

    }

    public void stop() {
        Log.e("destroying", "Service on stop");
        if (startHandler != null) {
            this.startHandler.removeCallbacksAndMessages(null);
        }
        if (stopHandler != null) {
            this.stopHandler.removeCallbacksAndMessages(null);
        }
        stopScan();
        this.serviceThread.interrupt();
        stopSelf();

    }

    public void restart() {
        Log.e("Restart", "Restart bluetooth");
        this.scanningMode = ScanningMode.MINUTE;
        restartBluetooth();
    }

    private void restartBluetooth() {
        stopScan();
        startScan();
    }

    public void setAppInBackground(boolean inBackground) {

        this.appInBackground = inBackground;
        if (this.appInBackground) {     // switch to background mode

        } else {
            Log.e("APP", "IN FOREGROUND");// switch to foreground mode
            // Notifications again permitted
            this.allowNotification = true;
        }
    }

    public void initiate_bluetooth() {
        startScan();
    }

    private void createStopScanTimer() {
        Log.e("Timeout", "Scan timeout: " + currentScanTime);
        stopHandler.postDelayed(new Runnable() {
            public void run() {
                stopScan();
                createStartScanTimer();
            }
        }, currentScanTime);
    }

    private void createStartScanTimer() {
        startHandler.postDelayed(new Runnable() {
            @Override
            public void run() {
                startScan();
            }
        }, currentSleepTime);
    }

    public void setActivity(Activity activity) {
        this.activity = activity;
        final BluetoothManager bluetoothManager =
        (BluetoothManager) getSystemService(Context.BLUETOOTH_SERVICE);
        this.btAdapter = bluetoothManager.getAdapter();
        int apiVersion = android.os.Build.VERSION.SDK_INT;
        if (apiVersion > android.os.Build.VERSION_CODES.KITKAT) {
            newApi = true;
        } else {
            newApi = false;
        }
    }

    private void stopScan() {
        Log.e("Stop", "Scan");
        BluetoothLeScannerCompat scanner = BluetoothLeScannerCompat.getScanner();
	    scanner.stopScan(scanCallback);
        this.startHandler.removeCallbacksAndMessages(null);
    }

    public void startScan() {
        Log.e("Start", "Scan");
        this.stopHandler.removeCallbacksAndMessages(null);

        BluetoothLeScannerCompat scanner = BluetoothLeScannerCompat.getScanner();
        scanner.startScan(this.scanFilters, this.scanSettings, this.scanCallback);

        if (this.scanningMode == ScanningMode.STANDBY) {
            Log.e("Scanning", "Scanning mode standby");
            createStopScanTimer();

        } else if (scanningMode == ScanningMode.MINUTE) {
            Log.e("Scanning", "Scanning mode minute");
            stopHandler.postDelayed(new Runnable() {
                @Override
                public void run() {
                    setStandbyMode(currentSleepTime);
                    restartBluetooth();
                }
            }, minuteScanTime);
        } else {
            Log.e("Scanning", "Scanning mode scan");
        }
    }


    public boolean check_notification_timeout() {
        Log.e("Notification time", "time: " + this.last_notification_time);
        long dift = System.currentTimeMillis() - this.last_notification_time;
        if (dift > NOTIFICATION_TIMEOUT && this.allowNotification) {
            //this.allow_notification = false;
            return true;
        }
        return false;
    }

    public boolean isInBackground() {
        return this.appInBackground;
    }

    public void createNotification(String title, String message) {
        if (!this.check_notification_timeout()) {
            Log.e("notification", "timeout");
            return;
        }
        Log.e("Creating", "Notification");
        this.last_notification_time = System.currentTimeMillis();

        Intent closeIntent = new Intent(CANCEL_NOTIFICATION);
        PendingIntent closePendingIntent = PendingIntent.getBroadcast(this, 12345, closeIntent, PendingIntent.FLAG_UPDATE_CURRENT);

        Intent notificationIntent = new Intent(OPEN_APPLICATION);
        PendingIntent pendingIntentYes = PendingIntent.getBroadcast(this, 12346, notificationIntent, PendingIntent.FLAG_UPDATE_CURRENT);

        Notification.Builder builder = new Notification.Builder(this)
         .setContentTitle(title)
         .setContentText(message)
         .setAutoCancel(true)
         .setSmallIcon(R.drawable.ic_bookmark_white_48dp)
         .addAction(0, "Cancel", closePendingIntent)
         .addAction(0, "Launch App", pendingIntentYes)
         .setPriority(Notification.PRIORITY_HIGH);

         if (newApi) {
            builder.setVibrate(new long[0]);
         }

        Notification noti = builder.build();
        NotificationManager notificationManager = (NotificationManager)getSystemService(Context.NOTIFICATION_SERVICE);
        notificationManager.notify(0, noti);

        IntentFilter filter = new IntentFilter();
        filter.addAction(CANCEL_NOTIFICATION);
        filter.addAction(OPEN_APPLICATION);
        // Add other actions as needed

        broadcastReceiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context context, Intent intent) {
                if (intent.getAction().equals(CANCEL_NOTIFICATION)) {

                } else if (intent.getAction().equals(OPEN_APPLICATION)) {
                    if (activity == null) {
                        Log.e("Activity", "Null");
                    }
                    Intent startIntent = new Intent(activity, activity.getClass());
                    //Intent startIntent = getPackageManager().getLaunchIntentForPackage("com.appix.java");
                    startIntent.addCategory(Intent.CATEGORY_LAUNCHER);
                    startIntent.addFlags(Intent.FLAG_ACTIVITY_BROUGHT_TO_FRONT|
                            Intent.FLAG_ACTIVITY_SINGLE_TOP);
                    startIntent.setAction(Intent.ACTION_MAIN);
                    activity.startActivity(startIntent);
                }
                NotificationManager notificationManager = (NotificationManager)getSystemService(Context.NOTIFICATION_SERVICE);
                notificationManager.cancel(0);
            }
        };
        allowNotification = false;
        this.activity.registerReceiver(broadcastReceiver, filter);
    }

     public class LocalBinder extends Binder {
        BluetoothLEService getService() {
            // Return this instance of LocalService so clients can call public methods
            return BluetoothLEService.this;
        }
    }

    @Override
    public IBinder onBind(Intent intent) {
        Log.e("BOUND", "IN SERVICE");
        return mBinder;
    }

}