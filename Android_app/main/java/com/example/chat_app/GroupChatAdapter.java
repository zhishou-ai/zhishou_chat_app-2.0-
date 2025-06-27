package com.example.chat_app;

import android.content.Intent;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import java.util.List;

public class GroupChatAdapter extends RecyclerView.Adapter<GroupChatAdapter.ViewHolder> {
    private final List<GroupItem> groupList;

    public static class ViewHolder extends RecyclerView.ViewHolder {
        public TextView groupName;
        public ImageView avatar;

        public ViewHolder(View itemView) {
            super(itemView);
            groupName = itemView.findViewById(R.id.group_name);
            avatar = itemView.findViewById(R.id.group_img);
        }
    }

    public GroupChatAdapter(List<GroupItem> groupList) {
        this.groupList = groupList;
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_group, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        GroupItem item = groupList.get(position);
        holder.avatar.setImageResource(R.drawable.item_group_image);
        holder.groupName.setText(item.getGroupName());
        holder.itemView.setOnClickListener(v -> {
            Intent intent = new Intent(v.getContext(), ChatActivity.class);
            intent.putExtra("receiver_type", "group");
            intent.putExtra("receiver_id", item.getGroupId());
            intent.putExtra("user_id", UserSession.getCurrentUserId());
            intent.putExtra("group_name", item.getGroupName()); // 传递群名
            v.getContext().startActivity(intent);
        });
    }

    @Override
    public int getItemCount() {

        return groupList.size();
    }
}