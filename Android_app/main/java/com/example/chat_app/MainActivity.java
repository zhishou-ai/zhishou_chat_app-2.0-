package com.example.chat_app;

import android.os.Bundle;
import android.view.View;
import android.widget.LinearLayout;

import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.fragment.app.Fragment;
import androidx.fragment.app.FragmentTransaction;

public class MainActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_main);

        // 设置初始显示的Fragment
        showFragment(new Private_chat_Fragment());

        // 设置底部导航点击事件
        setupBottomNavigation();
    }

    private void setupBottomNavigation() {
        LinearLayout privateChatLayout = findViewById(R.id.private_chat_layout);
        LinearLayout groupChatLayout = findViewById(R.id.group_chat_layout);
        LinearLayout workGroupLayout = findViewById(R.id.work_group_layout);
        LinearLayout myselfLayout = findViewById(R.id.self_layout);

        privateChatLayout.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                showFragment(new Private_chat_Fragment());
            }
        });

        groupChatLayout.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                showFragment(new Group_chat_Fragment());
            }
        });

        workGroupLayout.setOnClickListener(new View.OnClickListener(){
            @Override
            public void onClick(View v){
                showFragment(new Work_group_Fragment());
            }
        });

        myselfLayout.setOnClickListener((new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                showFragment(new Myself_Fragment());
            }
        }));
    }

    private void showFragment(Fragment fragment) {
        FragmentTransaction transaction = getSupportFragmentManager().beginTransaction();
        transaction.replace(R.id.fragment, fragment);
        transaction.commit();
    }
}