package com.example.chat_app;

public class GroupItem {
    private final String groupName;
    private final int groupId;

    public GroupItem(String groupName, int groupId) {
        this.groupName = groupName;
        this.groupId = groupId;
    }

    public String getGroupName() {
        return groupName;
    }

    public int getGroupId() {
        return groupId;
    }
}

