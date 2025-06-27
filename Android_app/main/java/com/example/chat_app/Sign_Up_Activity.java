package com.example.chat_app;

import android.annotation.SuppressLint;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.os.Bundle;
import android.text.Html;
import android.text.InputType;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import org.java_websocket.handshake.ServerHandshake;

import com.google.gson.Gson;

import org.json.JSONObject;

import java.net.URI;

public class Sign_Up_Activity extends AppCompatActivity {

    private MyWebSocketClient webSocketClient;
    private EditText etUsername, etPassword, etSePassword;
    private Button btnSignUp, btnSignIn;
    private boolean wsReady = false; // 添加的成员变量


    @SuppressLint("MissingInflatedId")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_sign_up);

        // 初始化视图
        etUsername = findViewById(R.id.SignUpUsername);
        etPassword = findViewById(R.id.SignUpPassword);
        etSePassword = findViewById(R.id.SignUpSepassword);
        btnSignUp = findViewById(R.id.SignUpButton);
        btnSignIn = findViewById(R.id.to_SignInButton);


        // 初始化 WebSocket
        initWebSocket();

        // 登录按钮点击事件
        btnSignUp.setOnClickListener(v -> attemptSignUp());
        btnSignIn.setOnClickListener(v -> {
            Intent intent = new Intent(Sign_Up_Activity.this, Sign_In_Activity.class);
            startActivity(intent);
        });


    }

    private void initWebSocket() {
        try {
            URI serverUri = new URI("ws://192.168.3.15:8765");

            webSocketClient = new MyWebSocketClient(serverUri, message -> {
                // 在主线程更新UI
                runOnUiThread(() -> handleServerResponse(message));
            }) {
                @Override
                public void onOpen(ServerHandshake handshakedata) {
                    super.onOpen(handshakedata);
                    wsReady = true;
                    runOnUiThread(() -> {
                        // 启用按钮
                        btnSignUp.setEnabled(true);
                    });
                }
            };

            // 连接超时设置（可选）
            webSocketClient.setConnectionLostTimeout(30);
            webSocketClient.connect();

        } catch (Exception e) {
            e.printStackTrace();
            showToast("无法连接服务器");
        }
    }

    private void attemptSignUp() {
        if (!wsReady) {
            showToast("正在连接服务器，请稍后重试");
            return;
        }

        String username = etUsername.getText().toString().trim();
        String password = etPassword.getText().toString().trim();
        String sepassword = etSePassword.getText().toString().trim();

        // 验证输入
        if (username.isEmpty()) {
            etUsername.setError("请输入用户名！");
            return;
        }
        if (password.isEmpty()) {
            etPassword.setError("请输入密码！");
            return;
        }
        if (sepassword.isEmpty()) {
            etSePassword.setError("请再次输入一遍密码！");
        }
        if (!sepassword.equals(password)) {
            etPassword.setError("两次输入的密码不一致！");
            etSePassword.setError("两次输入的密码不一致！");
            return;
        }

        // 显示加载状态
        showToast("正在注册...");
        btnSignUp.setEnabled(false);

        // 构建 JSON 数据
        SignUpdata SignUpdata = new SignUpdata(username, password);
        String json = new Gson().toJson(SignUpdata);

        // 发送登录数据
        if (webSocketClient != null && webSocketClient.isOpen()) {
            webSocketClient.send(json);
        } else {
            showToast("连接未就绪，请重试");
            resetSignUpButton();
        }
    }

    private void handleServerResponse(String response) {
        System.out.println("原始响应：" + response);
        try {
            JSONObject json = new JSONObject(response.toLowerCase());
            String action = json.getString("action");
            if ("register_response".equals(action)) {
                if (json.getBoolean("success")) {
                    int userId = json.getInt("user_id");
                    UserSession.setCurrentUserId(String.valueOf(userId));
                    showToast("注册成功");
                    // 保存WebSocketClient到全局
                    WebSocketManager.setClient(webSocketClient);
                    Intent intent = new Intent(Sign_Up_Activity.this, MainActivity.class);
                    startActivity(intent);
                } else {
                    showToast("注册失败: " + response);
                }
            }
        } catch (Exception e) {
            showToast("解析响应出错: " + e.getMessage());
        } finally {
            resetSignUpButton();
        }
    }

    private void resetSignUpButton() {
        btnSignUp.setEnabled(true);
    }

    private void showToast(String message) {
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();

    }

    // 登录数据模型
    private static class SignUpdata {
        String username;
        String password;
        String action;

        SignUpdata(String username, String password) {
            this.action = "register";
            this.username = username;
            this.password = password;
        }
    }
}