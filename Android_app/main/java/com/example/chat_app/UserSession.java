package com.example.chat_app;

public class UserSession {
    private static String currentUserId;
    public static void setCurrentUserId(String id) { currentUserId = id; }
    public static String getCurrentUserId() { return currentUserId; }
}