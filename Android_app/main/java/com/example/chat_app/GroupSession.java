package com.example.chat_app;

public class GroupSession {
    private static String currentGroupId;
    public static void setCurrentGroupId(String id) { currentGroupId = id; }
    public static String getCurrentGroupId() { return currentGroupId; }
}