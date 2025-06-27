package com.example.chat_app;

import android.util.Log;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;
import java.net.URI;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.List;

public class MyWebSocketClient extends WebSocketClient {

    public interface MessageCallback {
        void onMessageReceived(String message);
    }

    private final List<MessageCallback> callbacks = new CopyOnWriteArrayList<>();
    private String AllUsersMessage = null;
    private String GroupListMessage = null;


    public MyWebSocketClient(URI serverUri, MessageCallback callback) {
        super(serverUri);
        if (callback != null) {
            callbacks.add(callback);
        }
    }

    public void addMessageCallback(MessageCallback callback) {
        if (callback != null && !callbacks.contains(callback)) {
            callbacks.add(callback);
            if (AllUsersMessage != null) {
                callback.onMessageReceived(AllUsersMessage);
            }

            if (GroupListMessage != null){
                callback.onMessageReceived(GroupListMessage);
            }
        }
    }

    public void removeMessageCallback(MessageCallback callback) {
        callbacks.remove(callback);
    }

    @Override
    public void onMessage(String message) {
        // 缓存 all_users 消息
        if (message.contains("\"action\"") && message.contains("\"all_users\"")) {
            AllUsersMessage = message;
        }
        if (message.contains("\"action\"") && message.contains("\"group_list\"")){
            GroupListMessage = message;
        }
        for (MessageCallback cb : callbacks) {
            cb.onMessageReceived(message);
        }
    }

    @Override
    public void onOpen(ServerHandshake handshakedata) {
        Log.d("WebSocket", "连接已建立");
    }

    @Override
    public void onClose(int code, String reason, boolean remote) {
        Log.d("WebSocket", "连接关闭: " + reason);
    }

    @Override
    public void onError(Exception ex) {
        Log.e("WebSocket", "错误: ", ex);
    }
}