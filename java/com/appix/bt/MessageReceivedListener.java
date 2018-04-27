package appix.appix.com.appixandroidbtlibrary;

public interface MessageReceivedListener {

    boolean onMessageReceived(byte[] message, int rssi);

}