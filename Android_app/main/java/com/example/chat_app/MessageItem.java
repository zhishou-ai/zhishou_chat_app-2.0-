package com.example.chat_app;

public class MessageItem {
    private final String from; // userId
    private final String fromName; // 新增：发送者昵称
    private final String content;
    private final long timestamp;

    public MessageItem(String from, String fromName, String content, long timestamp) {
        this.from = from;
        this.fromName = fromName;
        this.content = content;
        this.timestamp = timestamp;
    }

    public String getFrom() { return from; }
    public String getFromName() { return fromName; }
    public String getContent() { return content; }
    public long getTimestamp() { return timestamp; }
}