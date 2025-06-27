package com.example.chat_app;

public class ChatItem {
    private final int userId; // 新增
    private final String name;
    private final int avatarResId;

    public ChatItem(int userId, String name, int avatarResId) {
        this.userId = userId;
        this.name = name;
        this.avatarResId = avatarResId;
    }

    public int getUserId() { return userId; }
    public String getName() { return name; }
    public int getAvatarResId() { return avatarResId; }
}