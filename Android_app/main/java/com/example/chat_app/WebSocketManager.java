package com.example.chat_app;

public class WebSocketManager {
    private static MyWebSocketClient client;
    public static void setClient(MyWebSocketClient c) { client = c; }
    public static MyWebSocketClient getClient() { return client; }
}