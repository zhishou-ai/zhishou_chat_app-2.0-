// 群发消息功能相关JavaScript代码（TreeView版）
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
    const WS_URL = "ws://192.168.3.250:8765"; // 替换为你的服务器地址
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
            fetchStudents();
        };

        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            console.log("收到消息：", data);

            if (data.action === "all_users") {
                // 按权限分组
                const teachers = (data.users || []).filter(u => u.permission === "teacher" && u.user_id != currentUserId);
                const studentsList = (data.users || []).filter(u => u.permission === "student" && u.user_id != currentUserId);
                
                // 更新数据
                students = [
                    ...teachers.map(teacher => ({
                        id: teacher.user_id,
                        name: teacher.username,
                        permission: teacher.permission,
                        selected: false,
                        group: 'teachers'
                    })),
                    ...studentsList.map(student => ({
                        id: student.user_id,
                        name: student.username,
                        permission: student.permission,
                        selected: false,
                        group: 'students'
                    }))
                ];
                
                initRecipientsTreeView();
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

    // 初始化TreeView形式的接收人列表
    // 在qunfa.js中修改initRecipientsTreeView函数
function initRecipientsTreeView() {
    if (!recipientsList) {
        console.error('错误：找不到recipientsList元素');
        return;
    }
    
    recipientsList.innerHTML = '';
    
    // 创建树形结构
    const tree = document.createElement('div');
    tree.className = 'tree-view';
    
    // 添加教师分组
    const teacherGroup = students.filter(s => s.permission === "teacher");
    if (teacherGroup.length > 0) {
        const teacherItem = createGroupItem('teachers', '教师', teacherGroup);
        tree.appendChild(teacherItem);
    }
    
    // 添加学生分组
    const studentGroup = students.filter(s => s.permission === "student");
    if (studentGroup.length > 0) {
        const studentItem = createGroupItem('students', '学生', studentGroup);
        tree.appendChild(studentItem);
    }
    
    // 添加一个占位容器确保宽度
    const spacer = document.createElement('div');
    spacer.className = 'spacer';
    tree.appendChild(spacer);
    
    recipientsList.appendChild(tree);
}

// 在qunfa.js中修改createGroupItem函数
    function createGroupItem(groupId, groupName, members) {
        const groupContainer = document.createElement('div');
        groupContainer.className = 'group-container';
        
        // 分组标题
        const groupHeader = document.createElement('div');
        groupHeader.className = 'group-header';
        groupHeader.innerHTML = `
            <label class="group-label">
                <input type="checkbox" class="group-checkbox" id="group-${groupId}">
                <span class="group-name">${groupName} (${members.length}人)</span>
            </label>
        `;
        
        // 成员列表
        const memberList = document.createElement('div');
        memberList.className = 'member-list';
        
        // 添加成员
        members.forEach(member => {
            const memberItem = document.createElement('div');
            memberItem.className = 'member-item';
            memberItem.innerHTML = `
                <label class="member-label">
                    <input type="checkbox" class="recipient-checkbox" id="recipient-${member.id}" ${member.selected ? 'checked' : ''}>
                    <span class="member-avatar">${member.name.charAt(0)}</span>
                    <span class="member-name">${member.name}</span>
                </label>
            `;
            
            // 监听单个成员选择
            memberItem.querySelector('.recipient-checkbox').addEventListener('change', function(e) {
                member.selected = this.checked;
                updateGroupCheckbox(groupId);
            });
            
            memberList.appendChild(memberItem);
        });
        
        // 分组选择逻辑
        groupHeader.querySelector('.group-checkbox').addEventListener('change', function(e) {
            const isChecked = this.checked;
            members.forEach(member => {
                member.selected = isChecked;
                const checkbox = memberList.querySelector(`#recipient-${member.id}`);
                if (checkbox) checkbox.checked = isChecked;
            });
        });
        
        groupContainer.appendChild(groupHeader);
        groupContainer.appendChild(memberList);
        return groupContainer;
    }

    function createGroupItem(groupId, groupName, members) {
        const groupContainer = document.createElement('div');
        groupContainer.className = 'group-container';
        
        // 分组标题 - 使用flex布局确保宽度
        const groupHeader = document.createElement('div');
        groupHeader.className = 'group-header';
        groupHeader.innerHTML = `
            <label class="group-label">
                <input type="checkbox" class="group-checkbox" id="group-${groupId}">
                <span class="group-name">${groupName} (${members.length}人)</span>
            </label>
        `;
        
        // 成员列表 - 使用grid布局
        const memberList = document.createElement('div');
        memberList.className = 'member-list';
        
        // 添加成员
        members.forEach(member => {
            const memberItem = document.createElement('div');
            memberItem.className = 'member-item';
            memberItem.innerHTML = `
                <label class="member-label">
                    <input type="checkbox" class="recipient-checkbox" id="recipient-${member.id}" ${member.selected ? 'checked' : ''}>
                    <span class="member-avatar">${member.name.charAt(0)}</span>
                    <span class="member-name">${member.name}</span>
                </label>
            `;
            
            // 监听单个成员选择
            memberItem.querySelector('.recipient-checkbox').addEventListener('change', function(e) {
                member.selected = this.checked;
                updateGroupCheckbox(groupId);
            });
            
            memberList.appendChild(memberItem);
        });
        
        // 分组选择逻辑
        groupHeader.querySelector('.group-checkbox').addEventListener('change', function(e) {
            const isChecked = this.checked;
            members.forEach(member => {
                member.selected = isChecked;
                const checkbox = memberList.querySelector(`#recipient-${member.id}`);
                if (checkbox) checkbox.checked = isChecked;
            });
        });
        
        groupContainer.appendChild(groupHeader);
        groupContainer.appendChild(memberList);
        return groupContainer;
    }
 
    

    // 创建分组项
    function createGroupItem(groupId, groupName, members) {
        const groupItem = document.createElement('li');
        groupItem.className = 'tree-node';
        groupItem.dataset.groupId = groupId;
        
        // 分组标题
        const groupHeader = document.createElement('div');
        groupHeader.className = 'tree-node-header';
        groupHeader.innerHTML = `
            <i class="fas fa-caret-right tree-caret"></i>
            <span class="tree-node-label">${groupName} (${members.length}人)</span>
            <input type="checkbox" class="group-checkbox" id="group-${groupId}">
        `;
        
        // 成员列表（初始隐藏）
        const memberList = document.createElement('ul');
        memberList.className = 'tree-node-children';
        memberList.style.display = 'none';
        
        // 添加成员
        members.forEach(member => {
            const memberItem = document.createElement('li');
            memberItem.className = 'tree-leaf';
            memberItem.innerHTML = `
                <div class="tree-leaf-content">
                    <input type="checkbox" class="recipient-checkbox" id="recipient-${member.id}" ${member.selected ? 'checked' : ''}>
                    <div class="recipient-avatar">${member.name.charAt(0)}</div>
                    <div class="recipient-name">${member.name}</div>
                </div>
            `;
            
            // 监听单个成员选择
            memberItem.querySelector('.recipient-checkbox').addEventListener('change', function(e) {
                member.selected = this.checked;
                updateGroupCheckbox(groupId);
                e.stopPropagation();
            });
            
            memberList.appendChild(memberItem);
        });
        
        // 分组选择逻辑
        groupHeader.querySelector('.group-checkbox').addEventListener('change', function(e) {
            const isChecked = this.checked;
            
            // 更新所有成员的选择状态
            members.forEach(member => {
                member.selected = isChecked;
                const checkbox = memberList.querySelector(`#recipient-${member.id}`);
                if (checkbox) checkbox.checked = isChecked;
            });
            
            e.stopPropagation();
        });
        
        // 分组展开/折叠
        groupHeader.addEventListener('click', function(e) {
            if (e.target.tagName !== 'INPUT') { // 避免点击checkbox时触发
                const caret = this.querySelector('.tree-caret');
                const isExpanded = memberList.style.display === 'block';
                
                if (isExpanded) {
                    memberList.style.display = 'none';
                    caret.classList.remove('fa-caret-down');
                    caret.classList.add('fa-caret-right');
                } else {
                    memberList.style.display = 'block';
                    caret.classList.remove('fa-caret-right');
                    caret.classList.add('fa-caret-down');
                }
            }
        });
        
        groupItem.appendChild(groupHeader);
        groupItem.appendChild(memberList);
        return groupItem;
    }
    
    // 更新分组选择框状态
    function updateGroupCheckbox(groupId) {
        const groupMembers = students.filter(s => s.group === groupId);
        const allSelected = groupMembers.every(member => member.selected);
        const groupCheckbox = document.querySelector(`#group-${groupId}`);
        if (groupCheckbox) groupCheckbox.checked = allSelected;
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
        initRecipientsTreeView();
        sendBulk.disabled = false;
    }

    // 在聊天界面显示已发送的群发消息
    function displaySentMessage(messageContent, recipients) {
        const successMessage = document.createElement('div');
        successMessage.className = 'message sent';
        successMessage.innerHTML = `
            <div class="message-header">
                <div class="message-avatar">我</div>
                <div class="message-sender">我（群发）</div>
            </div>
            <div class="message-content">${messageContent}</div>
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