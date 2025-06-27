// 群发消息功能相关JavaScript代码（WebSocket版）
document.addEventListener('DOMContentLoaded', function() {
    // 获取群发功能相关DOM元素
    const bulkSendBtn = document.getElementById('bulkSendBtn');
    const bulkModal = document.getElementById('bulkModal');
    const closeModal = document.getElementById('closeModal');
    const cancelBulk = document.getElementById('cancelBulk');
    const sendBulk = document.getElementById('sendBulk');
    const recipientsList = document.getElementById('recipientsList');
    const messageInput = document.querySelector('.bulk-message-input');
    const chatBody = document.querySelector('.messages');

    // WebSocket配置
    const WS_URL = "ws://192.168.3.106:8765"; // 替换为你的服务器地址
    let ws = null;
    let students = [];
    let currentUserId = localStorage.getItem('currentUserId');
    let currentUserPermission = localStorage.getItem('currentUserPermission') || '';

    if (!currentUserId) {
        alert('请先登录');
        window.location.href = '../index.html';
    }

    // 建立WebSocket连接
    function connectWebSocket() {
        ws = new WebSocket(WS_URL);

        ws.onopen = function() {
            console.log("WebSocket已连接");
        };

        // 建立WebSocket连接后收到 all_users
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            // 调试日志
            console.log("收到消息：", data);

            if (data.action === "all_users") {
                // 不再只筛选学生，显示所有人（除自己）
                students = (data.users || []).filter(u => u.user_id != currentUserId);
                students = students.map(user => ({
                    id: user.user_id,
                    name: user.username,
                    permission: user.permission,
                    selected: false
                }));
                initRecipientsList();
            } else if (data.action === "error") {
                alert(data.message || "操作失败");
            } else if (data.action === "send_message") {
                alert("群发消息已发送！");
            }
        };

        ws.onclose = function() {
            console.log("WebSocket已断开");
        };

        ws.onerror = function(e) {
            console.error("WebSocket错误", e);
        };
    }

    // 获取学生列表
    function fetchStudents() {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({action: "web_online", user_id: currentUserId}));
        } else {
            setTimeout(fetchStudents, 200); // 等待连接建立
        }
    }

    // 初始化接收人列表
    function initRecipientsList() {
        if (!recipientsList) {
            console.error('错误：找不到recipientsList元素');
            return;
        }
        recipientsList.innerHTML = '';
        if (students.length === 0) {
            recipientsList.innerHTML = '<div class="no-students">暂无学生可选</div>';
            return;
        }
        students.forEach(student => {
            const recipientItem = document.createElement('div');
            recipientItem.className = 'recipient-item';
            recipientItem.innerHTML = `
                <input type="checkbox" class="recipient-checkbox" id="recipient-${student.id}" ${student.selected ? 'checked' : ''}>
                <div class="recipient-avatar">${student.name.charAt(0)}</div>
                <div class="recipient-name">${student.name} <span style="color:#888;font-size:12px;">(${student.permission === 'teacher' ? '教师' : '学生'})</span></div>
            `;
            // 只监听checkbox的change事件
            recipientItem.querySelector('.recipient-checkbox').addEventListener('change', function(e) {
                student.selected = this.checked;
                recipientItem.classList.toggle('selected', this.checked);
            });
            if (student.selected) {
                recipientItem.classList.add('selected');
            }
            recipientsList.appendChild(recipientItem);
        });
    }

    // 显示群发消息模态框
    bulkSendBtn.addEventListener('click', function() {
        bulkModal.style.display = 'flex';
        // 每次打开都重新请求学生列表
        fetchStudents();
    });

    // 关闭模态框
    closeModal.addEventListener('click', function() {
        bulkModal.style.display = 'none';
    });

    // 取消群发操作
    cancelBulk.addEventListener('click', function() {
        bulkModal.style.display = 'none';
    });

    // 发送群发消息到后端
    function sendBulkMessage() {
        const selectedStudents = students.filter(student => student.selected);
        const messageContent = messageInput.value.trim();

        if (!messageContent) {
            alert('请输入消息内容');
            return;
        }
        if (selectedStudents.length === 0) {
            alert('请选择至少一个接收人');
            return;
        }

        // 权限校验
        if (currentUserPermission !== 'teacher') {
            alert('只有教师才能使用群发功能！');
            return;
        }

        sendBulk.disabled = true;

        // 发送群发消息
        ws.send(JSON.stringify({
            action: "send_qunfamessage",
            sender_id: currentUserId,
            receivers_id: selectedStudents.map(s => s.id),
            content: messageContent
        }));

        // 本地显示消息
        displaySentMessage(messageContent, selectedStudents);

        // 重置
        bulkModal.style.display = 'none';
        messageInput.value = '';
        students.forEach(student => student.selected = false);
        initRecipientsList();
        sendBulk.disabled = false;
    }

    // 在聊天界面显示已发送的群发消息
    function displaySentMessage(messageContent, recipients) {
        const successMessage = document.createElement('div');
        successMessage.className = 'message sent';
        successMessage.innerHTML = `
            <div class="message-header">
                <div class="avatar">我</div>
                <div class="sender-name">我（群发）</div>
            </div>
            <div>${messageContent}</div>
            <div class="message-time">${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
            <div class="recipients-info">发送给: ${recipients.map(s => s.name).join(', ')}</div>
        `;
        chatBody.appendChild(successMessage);
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    // 绑定发送按钮事件
    sendBulk.addEventListener('click', sendBulkMessage);

    // 初始化WebSocket
    connectWebSocket();
});