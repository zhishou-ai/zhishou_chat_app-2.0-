package com.example.chat_app;

import android.app.AlertDialog;
import android.graphics.drawable.Drawable;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Toast;

import androidx.core.content.ContextCompat;
import androidx.fragment.app.Fragment;
import androidx.recyclerview.widget.DividerItemDecoration;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.google.android.material.floatingactionbutton.FloatingActionButton;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

public class Group_chat_Fragment extends Fragment {

    private List<GroupItem> groupList = new ArrayList<>();
    private GroupChatAdapter adapter;

    // 定义回调对象
    private final MyWebSocketClient.MessageCallback messageCallback = message -> {
        requireActivity().runOnUiThread(() -> handleServerMessage(message));
    };

    private List<ChatItem> allUserList = new ArrayList<>();

    @Override
    public void onResume() {
        super.onResume();
        requireActivity().setTitle("群聊");
    }

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState) {
        View view = inflater.inflate(R.layout.fragment_group_chat, container, false);

        RecyclerView recyclerView = view.findViewById(R.id.recyclerView_group);
        recyclerView.setLayoutManager(new LinearLayoutManager(getContext()));


        DividerItemDecoration divider = new DividerItemDecoration(getContext(), DividerItemDecoration.VERTICAL);
        Drawable drawable = ContextCompat.getDrawable(getContext(), R.drawable.main_divider);
        if (drawable != null) {
            divider.setDrawable(drawable);
            recyclerView.addItemDecoration(divider);
        }

        adapter = new GroupChatAdapter(groupList);
        recyclerView.setAdapter(adapter);

        // 建群按钮
        FloatingActionButton btnCreateGroup = view.findViewById(R.id.btn_create_group);
        btnCreateGroup.setOnClickListener(v -> {
            if (allUserList.isEmpty()) {
                Toast.makeText(getContext(), "成员列表加载中，请稍后再试", Toast.LENGTH_SHORT).show();
                return;
            }
            showCreateGroupDialog();
        });

        // 注册回调
        MyWebSocketClient client = WebSocketManager.getClient();
        if (client != null) {
            client.addMessageCallback(messageCallback);
            // 主动请求所有用户
            try {
                JSONObject req = new JSONObject();
                req.put("action", "get_all_users");
                client.send(req.toString());
            } catch (Exception e) {
                e.printStackTrace();
            }
        }

        return view;

    }

    private void handleServerMessage(String message) {
        try {
            JSONObject json = new JSONObject(message);
            String action = json.optString("action");
            if ("group_list".equals(action)) {
                JSONArray groups = json.getJSONArray("groups");
                groupList.clear();
                for (int i = 0; i < groups.length(); i++) {
                    JSONObject group = groups.getJSONObject(i);
                    String groupName = group.getString("group_name");
                    int groupId = group.getInt("group_id");
                    groupList.add(new GroupItem(groupName, groupId));
                }
                adapter.notifyDataSetChanged();
            } else if ("all_users".equals(action)) {
                JSONArray users = json.getJSONArray("users");
                allUserList.clear();
                for (int i = 0; i < users.length(); i++) {
                    JSONObject user = users.getJSONObject(i);
                    int userId = user.getInt("user_id");
                    String username = user.getString("username");
                    allUserList.add(new ChatItem(userId, username, R.drawable.item_group_image));
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    // 弹窗方法
    private void showCreateGroupDialog() {
        AlertDialog.Builder builder = new AlertDialog.Builder(getContext());
        builder.setTitle("创建群聊");

        // 嵌套布局
        LinearLayout layout = new LinearLayout(getContext());
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(40, 20, 40, 10);

        // 群名输入
        final EditText inputGroupName = new EditText(getContext());
        inputGroupName.setHint("请输入群名称");
        layout.addView(inputGroupName);

        // 多选成员（假设你有 allUserList: List<ChatItem>，每个 ChatItem 有 userId 和 name）
        ScrollView scrollView = new ScrollView(getContext());
        LinearLayout memberLayout = new LinearLayout(getContext());
        memberLayout.setOrientation(LinearLayout.VERTICAL);

        List<CheckBox> checkBoxList = new ArrayList<>();
        for (ChatItem user : allUserList) {
            CheckBox cb = new CheckBox(getContext());
            cb.setText(user.getName() + " (ID:" + user.getUserId() + ")");
            cb.setTag(user.getUserId());
            memberLayout.addView(cb);
            checkBoxList.add(cb);
        }
        scrollView.addView(memberLayout);
        layout.addView(scrollView);

        builder.setView(layout);

        builder.setPositiveButton("创建", (dialog, which) -> {
            String groupName = inputGroupName.getText().toString().trim();
            if (groupName.isEmpty()) {
                Toast.makeText(getContext(), "群名称不能为空", Toast.LENGTH_SHORT).show();
                return;
            }
            List<Integer> memberIdList = new ArrayList<>();
            for (CheckBox cb : checkBoxList) {
                if (cb.isChecked()) {
                    memberIdList.add((Integer) cb.getTag());
                }
            }
            // 把自己加进去
            try {
                int myId = Integer.parseInt(UserSession.getCurrentUserId());
                if (!memberIdList.contains(myId)) memberIdList.add(myId);
            } catch (Exception ignore) {}

            if (memberIdList.size() < 2) {
                Toast.makeText(getContext(), "请选择至少两位成员", Toast.LENGTH_SHORT).show();
                return;
            }
            sendCreateGroupRequest(groupName, memberIdList);
        });
        builder.setNegativeButton("取消", null);
        builder.show();
    }

    // 发送建群请求
    private void sendCreateGroupRequest(String groupName, List<Integer> memberIds) {
        try {
            JSONObject req = new JSONObject();
            req.put("action", "create_group");
            req.put("group_name", groupName);
            req.put("creator_id", Integer.parseInt(UserSession.getCurrentUserId()));
            req.put("initial_members", new JSONArray(memberIds));
            MyWebSocketClient client = WebSocketManager.getClient();
            if (client != null && client.isOpen()) {
                client.send(req.toString());
            }
        } catch (Exception e) {
            e.printStackTrace();
            Toast.makeText(getContext(), "建群失败", Toast.LENGTH_SHORT).show();
        }
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        // 注销回调，防止内存泄漏
        MyWebSocketClient client = WebSocketManager.getClient();
        if (client != null) {
            client.removeMessageCallback(messageCallback);
        }
    }


}