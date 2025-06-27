package com.example.chat_app;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import android.widget.ImageView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import java.util.List;

public class MessageAdapter extends RecyclerView.Adapter<RecyclerView.ViewHolder> {
    private final List<MessageItem> messageList;

    // 当前用户id，用于判断左右气泡
    private final String myUserId = UserSession.getCurrentUserId();

    // 区分左右气泡
    @Override
    public int getItemViewType(int position) {
        MessageItem item = messageList.get(position);
        if (item.getFrom().equals(myUserId)) {
            return 1; // 右侧（自己）
        } else {
            return 0; // 左侧（别人）
        }
    }

    @NonNull
    @Override
    public RecyclerView.ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        if (viewType == 1) {
            View view = LayoutInflater.from(parent.getContext())
                    .inflate(R.layout.item_message_right, parent, false);
            return new RightViewHolder(view);
        } else {
            View view = LayoutInflater.from(parent.getContext())
                    .inflate(R.layout.item_message_left, parent, false);
            return new LeftViewHolder(view);
        }
    }

    @Override
    public void onBindViewHolder(@NonNull RecyclerView.ViewHolder holder, int position) {
        MessageItem item = messageList.get(position);
        System.out.println("onBindViewHolder: from=" + item.getFrom() + ", myUserId=" + myUserId + ", content=" + item.getContent());
        if (holder instanceof RightViewHolder) {
            ((RightViewHolder) holder).msgContent.setText(item.getContent());
            ((RightViewHolder) holder).avatar.setImageResource(R.drawable.item_private_image);
        } else if (holder instanceof LeftViewHolder) {
            ((LeftViewHolder) holder).msgContent.setText(item.getContent());
            ((LeftViewHolder) holder).senderName.setText(item.getFromName()); // 绑定昵称
            ((LeftViewHolder) holder).avatar.setImageResource(R.drawable.item_image);
        }
    }

    @Override
    public int getItemCount() {
        return messageList.size();
    }

    static class LeftViewHolder extends RecyclerView.ViewHolder {
        TextView msgContent;
        TextView senderName; // 新增
        ImageView avatar;
        LeftViewHolder(View itemView) {
            super(itemView);
            msgContent = itemView.findViewById(R.id.msg_content_left);
            senderName = itemView.findViewById(R.id.msg_sender_name); // 新增
            avatar = itemView.findViewById(R.id.avatar_left);
        }
    }

    static class RightViewHolder extends RecyclerView.ViewHolder {
        TextView msgContent;
        ImageView avatar;
        RightViewHolder(View itemView) {
            super(itemView);
            msgContent = itemView.findViewById(R.id.msg_content_right);
            avatar = itemView.findViewById(R.id.avatar_right);
        }
    }

    public MessageAdapter(List<MessageItem> messageList) {
        this.messageList = messageList;
    }
}