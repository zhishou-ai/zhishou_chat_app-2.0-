package com.example.chat_app;

import android.os.Bundle;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import android.view.View;
import android.content.Intent;
import android.widget.ImageView;
import android.widget.TextView;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.List;

public class ChatActivity extends AppCompatActivity {

    private RecyclerView recyclerView;
    private MessageAdapter adapter;
    private List<MessageItem> messageList = new ArrayList<>();
    private String receiverType;

    private ImageView return_button;
    private String receiverId;
    private String userId; // 当前用户id

    private final MyWebSocketClient.MessageCallback messageCallback = message -> {
        runOnUiThread(() -> handleServerMessage(message));
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_chat);

        recyclerView = findViewById(R.id.recyclerView_chat);
        recyclerView.setLayoutManager(new LinearLayoutManager(this));
        adapter = new MessageAdapter(messageList);
        recyclerView.setAdapter(adapter);
        return_button = findViewById(R.id.btn_back);

        // 获取聊天对象信息
        receiverType = getIntent().getStringExtra("receiver_type");
        receiverId = String.valueOf(getIntent().getIntExtra("receiver_id", -1));
        userId = getIntent().getStringExtra("user_id");

        // 设置顶部标题
        TextView chatTitle = findViewById(R.id.chat_title);
        if ("group".equals(receiverType)) {
            // 群聊，显示群名（需要通过 groupList 查找群名）
            String groupName = getIntent().getStringExtra("group_name");
            if (groupName != null && !groupName.isEmpty()) {
                chatTitle.setText(groupName);
            } else {
                chatTitle.setText("群聊");
            }
        } else {
            // 私聊，显示对方昵称（需要通过 allUserList 或 chatList 查找）
            String userName = getIntent().getStringExtra("user_name");
            if (userName != null && !userName.isEmpty()) {
                chatTitle.setText(userName);
            } else {
                chatTitle.setText("私聊");
            }
        }

        // 注册回调
        MyWebSocketClient client = WebSocketManager.getClient();
        if (client != null) {
            client.addMessageCallback(messageCallback);
            // 请求历史消息
            requestHistory();
        }

        return_button.setOnClickListener(v ->{
            finish();
        });

    TextView inputMessage = findViewById(R.id.input_message);
    View btnSend = findViewById(R.id.btn_send);

    btnSend.setOnClickListener(v ->{
        String content = inputMessage.getText().toString().trim();
        if (content.isEmpty()) return;

        try {
            JSONObject req = new JSONObject();
            req.put("action", "send_message");
            req.put("sender_id", userId);
            req.put("content", content);
            req.put("content_type", "text");
            req.put("timestamp", System.currentTimeMillis() / 1000);

            if ("group".equals(receiverType)){
                req.put("receiver_type", "group");
                req.put("receiver_id", receiverId);
            } else {
                req.put("receiver_type", "private");
                req.put("receiver_id", receiverId);
            }

            MyWebSocketClient wsClient = WebSocketManager.getClient();
            if (wsClient != null && wsClient.isOpen()){
                wsClient.send(req.toString());
                inputMessage.setText("");
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    });
}

    private void requestHistory() {
        try {
            JSONObject req = new JSONObject();
            req.put("action", "get_messages");
            req.put("user_id", userId); // userId 是数字字符串
            req.put("receiver_type", receiverType);
            req.put("receiver_id", receiverId); // receiverId 也是数字字符串
            req.put("page", 1);
            req.put("page_size", 50);
            MyWebSocketClient client = WebSocketManager.getClient();
            if (client != null && client.isOpen()) {
                client.send(req.toString());
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void handleServerMessage(String message) {
        try {
            JSONObject json = new JSONObject(message);
            String action = json.optString("action");
            if ("message_history".equals(action)
                    && receiverType.equals(json.optString("receiver_type"))
                    && receiverId.equals(json.optString("receiver_id"))) {
                // 历史消息加载
                JSONArray messages = json.getJSONArray("messages");
                messageList.clear();
                for (int i = messages.length() - 1; i >= 0; i--) {
                    JSONObject msg = messages.getJSONObject(i);
                    String senderId = String.valueOf(msg.optInt("sender_id", -1));
                    String senderName = msg.optString("sender_name", "未知");
                    String content = msg.optString("content", "");
                    long timestamp = msg.optLong("timestamp", 0);
                    messageList.add(new MessageItem(senderId, senderName, content, timestamp));
                }
                adapter.notifyDataSetChanged();
                recyclerView.scrollToPosition(messageList.size() - 1);
            
            } else if ("send_message".equals(action)
                    && receiverType.equals(json.optString("receiver_type"))
                    && receiverId.equals(json.optString("receiver_id"))) {
                String senderId = String.valueOf(json.optInt("sender_id", -1));
                String senderName = json.optString("sender_name", "未知");
                String content = json.optString("content", "");
                long timestamp = json.optLong("timestamp", 0);
                messageList.add(new MessageItem(senderId, senderName, content, timestamp));
                adapter.notifyDataSetChanged();
                recyclerView.scrollToPosition(messageList.size() - 1);
            
            } else if ("new_private_message".equals(action)) {
                JSONObject msg = json.getJSONObject("message");
                String senderId = String.valueOf(msg.optInt("sender_id", -1));
                String content = msg.optString("content", "");

                if ("private".equals(receiverType)
                        && ((senderId.equals(receiverId) && msg.optInt("receiver_id", -1) == Integer.parseInt(userId))
                            || (senderId.equals(userId) && msg.optInt("receiver_id", -1) == Integer.parseInt(receiverId)))) {
                    messageList.add(new MessageItem(senderId, "对方", content, System.currentTimeMillis()/1000));
                    adapter.notifyDataSetChanged();
                    recyclerView.scrollToPosition(messageList.size() - 1);
                }
            
            } else if ("new_group_message".equals(action)) {
                int groupId = json.optInt("group_id", -1);
                JSONObject msg = json.getJSONObject("message");
                String senderId = String.valueOf(msg.optInt("sender_id", -1));
                String senderName = msg.optString("sender_name", "未知");
                String content = msg.optString("content", "");
                if ("group".equals(receiverType) && String.valueOf(groupId).equals(receiverId)) {
                    messageList.add(new MessageItem(senderId, senderName, content, System.currentTimeMillis()/1000));
                    adapter.notifyDataSetChanged();
                    recyclerView.scrollToPosition(messageList.size() - 1);
                }
            }
            
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        MyWebSocketClient client = WebSocketManager.getClient();
        if (client != null) {
            client.removeMessageCallback(messageCallback);
        }
    }
}