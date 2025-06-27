package com.example.chat_app;

import android.graphics.drawable.Drawable;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.core.content.ContextCompat;
import androidx.fragment.app.Fragment;
import androidx.recyclerview.widget.DividerItemDecoration;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

public class Private_chat_Fragment extends Fragment {

    private List<ChatItem> chatList = new ArrayList<>();
    private PrivateChatAdapter adapter;

    private final MyWebSocketClient.MessageCallback messageCallback = message -> {
        requireActivity().runOnUiThread(() -> handleServerMessage(message));
    };

    @Override
    public void onResume() {
        super.onResume();
        requireActivity().setTitle("私聊");
    }
    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState) {
        View view = inflater.inflate(R.layout.fragment_private_chat, container, false);

        RecyclerView recyclerView = view.findViewById(R.id.recyclerView_private);
        recyclerView.setLayoutManager(new LinearLayoutManager(getContext()));

        // 微信风格分割线
        DividerItemDecoration divider = new DividerItemDecoration(getContext(), DividerItemDecoration.VERTICAL);
        Drawable drawable = ContextCompat.getDrawable(getContext(), R.drawable.main_divider);
        if (drawable != null) {
            divider.setDrawable(drawable);
            recyclerView.addItemDecoration(divider);
        }

        // 初始化适配器
        adapter = new PrivateChatAdapter(chatList);
        recyclerView.setAdapter(adapter);

        // 只在私聊Fragment注册回调
        MyWebSocketClient client = WebSocketManager.getClient();
        if (client != null) {
            client.addMessageCallback(messageCallback);
        }

        return view;
    }

    private void handleServerMessage(String message) {
        try {
            JSONObject json = new JSONObject(message);
            String action = json.optString("action");
            if ("all_users".equals(action)) {
                JSONArray users = json.getJSONArray("users");
                chatList.clear();
                for (int i = 0; i < users.length(); i++) {
                    JSONObject user = users.getJSONObject(i);
                    int userId = user.getInt("user_id"); // 新增
                    String username = user.getString("username");
                    // 头像用本地模拟
                    chatList.add(new ChatItem(userId, username, R.drawable.item_private_image));
                }
                adapter.notifyDataSetChanged();
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        MyWebSocketClient client = WebSocketManager.getClient();
        if (client != null) {
            client.removeMessageCallback(messageCallback);
        }
    }
}

