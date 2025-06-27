package com.example.chat_app;

import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import com.google.gson.Gson;

import org.java_websocket.handshake.ServerHandshake;
import org.json.JSONObject;

import java.net.URI;




public class Sign_In_Activity extends AppCompatActivity {

    private MyWebSocketClient webSocketClient;
    private EditText etUsername, etPassword;
    private Button btnLogin, btnSignUp;
    private boolean wsReady = false; // 添加 WebSocket 准备状态


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_sign_in);

        // 初始化视图
        etUsername = findViewById(R.id.SignInUsername);
        etPassword = findViewById(R.id.SignInPassword);
        btnLogin = findViewById(R.id.SignInButton);
        btnSignUp = findViewById(R.id.SignUpButton);


        // 初始化 WebSocket
        initWebSocket();

        // 登录按钮点击事件
        btnLogin.setOnClickListener(v -> attemptLogin());
        btnSignUp.setOnClickListener(v -> {
            Intent intent = new Intent(Sign_In_Activity.this, Sign_Up_Activity.class);
            startActivity(intent);
        });
    }

    private void initWebSocket() {
        try {
            URI serverUri = new URI("ws://192.168.3.15:8765");

            webSocketClient = new MyWebSocketClient(serverUri, message -> {
                runOnUiThread(() -> handleServerResponse(message));
            }) {
                @Override
                public void onOpen(ServerHandshake handshakedata) {
                    super.onOpen(handshakedata);
                    wsReady = true;
                    runOnUiThread(() -> {
                        // 启用按钮
                        btnLogin.setEnabled(true); // 或 btnSignUp.setEnabled(true)
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

    private void attemptLogin() {
        if (!wsReady) {
            showToast("正在连接服务器，请稍后重试");
            return;
        }

        String username = etUsername.getText().toString().trim();
        String password = etPassword.getText().toString().trim();

        // 验证输入
        if (username.isEmpty()) {
            etUsername.setError("请输入用户名");
            return;
        }
        if (password.isEmpty()) {
            etPassword.setError("请输入密码");
            return;
        }

        // 显示加载状态
        showToast("正在登录...");
        btnLogin.setEnabled(false);

        // 构建 JSON 数据
        LoginData loginData = new LoginData(username, password);
        String json = new Gson().toJson(loginData);

        // 发送登录数据
        if (webSocketClient != null && webSocketClient.isOpen()) {
            webSocketClient.send(json);
        } else {
            showToast("连接未就绪，请重试");
            resetLoginButton();
        }
    }

    private void handleServerResponse(String response) {

        System.out.println("原始响应：" + response);
        // 解析服务器响应
        try {

            JSONObject json = new JSONObject(response.toLowerCase());
            String action = json.getString("action");
            if("login_response".equals(action)) {

                if (json.getBoolean("success")) {
                    int userId = json.getInt("user_id");
                    UserSession.setCurrentUserId(String.valueOf(userId));
                    showToast("登录成功");
                    WebSocketManager.setClient(webSocketClient);
                    Intent intent = new Intent(Sign_In_Activity.this, MainActivity.class);
                    startActivity(intent);
                    finish();
                } else {
                    showToast("登录失败: " + response);
                }
            }

        } catch (Exception e) {
            showToast("解析响应出错: " + e.getMessage());

        } finally {
            resetLoginButton();
        }
    }

    private void resetLoginButton() {
        btnLogin.setEnabled(true);
    }

    private void showToast(String message) {
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();

    }

    // 登录数据模型
    private static class LoginData {
        String username;
        String password;
        String action;

        LoginData(String username, String password) {
            this.action = "login";
            this.username = username;
            this.password = password;
        }
    }
}



