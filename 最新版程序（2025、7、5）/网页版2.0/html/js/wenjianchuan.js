//文件上传功能模块
//处理文件选择、预览、删除和图片放大查看功能

document.addEventListener('DOMContentLoaded', function() {
    // ==================== 1. DOM元素获取 ====================
    const fileUpload = document.getElementById('fileUpload');         // 隐藏的文件input元素
    const previewArea = document.getElementById('previewArea');       // 文件预览区域容器
    const messageInput = document.querySelector('.message-input');     // 消息输入框（用于关联文件发送）
    const sendButton = document.querySelector('.send-button');         // 发送按钮
    const imagePreviewModal = document.getElementById('imagePreviewModal'); // 图片预览模态框
    const previewedImage = document.getElementById('previewedImage');   // 模态框中显示的图片元素
    const closePreview = document.querySelector('.close-preview');      // 关闭预览按钮

    // ==================== 2. 状态管理 ====================
    let filesToSend = [];  // 存储待发送的文件列表

    // ==================== 3. 事件监听绑定 ====================
    
    // 点击回形针图标触发文件选择
    document.querySelector('.file-upload-btn').addEventListener('click', function(e) {
        e.preventDefault();  // 阻止默认行为
        fileUpload.click();   // 触发隐藏的file input点击
    });

    // 文件选择变化事件处理
    fileUpload.addEventListener('change', function(e) {
        const files = Array.from(e.target.files);  // 将FileList转换为数组
        if (files.length === 0) return;  // 没有文件选择则返回

        // 过滤掉重复文件（通过文件名和大小判断）
        const newFiles = files.filter(file => 
            !filesToSend.some(f => f.name === file.name && f.size === file.size)
        );

        // 检查文件大小限制（10MB）
        const oversizeFiles = newFiles.filter(file => file.size > 10 * 1024 * 1024);
        if (oversizeFiles.length > 0) {
            showToast(`以下文件超过10MB限制: ${oversizeFiles.map(f => f.name).join(', ')}`);
        }

        // 添加符合要求的文件（≤10MB）
        const validFiles = newFiles.filter(file => file.size <= 10 * 1024 * 1024);
        filesToSend.push(...validFiles);
        
        // 重新渲染预览区域
        renderPreview();
        fileUpload.value = '';  // 重置input，允许重复选择相同文件
    });

    // 发送按钮点击事件
    sendButton.addEventListener('click', async function() {
        // 只在这里判断
        if (!window.currentChat || !window.currentChat.id) {
            alert('请先选择聊天对象');
            return;
        }
        // 先发送文本消息（如果有）
        const text = messageInput.value.trim();
        if (text) {
            ws.send(JSON.stringify({
                action: "send_message",
                sender_id: localStorage.getItem('currentUserId'),
                receiver_type: window.currentChat.type,
                receiver_id: window.currentChat.id,
                content: text
            }));
            messageInput.value = '';
        }

        // 再发送所有附件
        for (const file of filesToSend) {
            // 1. 先发文件信息
            ws.send(JSON.stringify({
                type: "file_info",
                filename: file.name,
                filesize: file.size,
                receiver_id: Number(window.currentChat.id), // 强制转为数字
                receiver_type: window.currentChat.type
            }));
            // 2. 再发二进制内容
            const arrayBuffer = await file.arrayBuffer();
            ws.send(arrayBuffer);
        }
        // 清空附件
        filesToSend.length = 0;
        renderPreview();
        
        // 新增：发送成功后刷新消息列表
        refreshMessages();
    });

    // ==================== 4. 核心功能函数 ====================
    
    // 新增：刷新消息列表
    function refreshMessages() {
        // 确保当前有活跃的聊天窗口
        if (window.currentChat && window.currentChat.id) {
            // 延迟100ms确保消息已保存到数据库
            setTimeout(() => {
                // 调用加载消息的函数
                if (typeof loadChatMessages === 'function') {
                    loadChatMessages();
                    console.log('文件发送成功后刷新消息列表');
                }
            }, 100);
        }
    }
    
     //渲染所有文件预览
     
    function renderPreview() {
        previewArea.innerHTML = '';  // 清空现有预览
        
        // 为每个文件创建预览元素
        filesToSend.forEach((file, index) => {
            const previewItem = createPreviewElement(file, index);
            previewArea.appendChild(previewItem);
        });
    }

    
     // 创建单个文件预览元素
     // @param {File} file - 文件对象
     // @param {number} index - 文件在数组中的索引
     // @returns {HTMLElement} 预览元素DOM节点
     
    function createPreviewElement(file, index) {
        const previewItem = document.createElement('div');
        previewItem.className = 'preview-item';
        previewItem.dataset.fileIndex = index;  // 存储索引用于后续操作

        // 图片类型文件处理
        if (file.type.startsWith('image/')) {
            const imgPreview = document.createElement('div');
            imgPreview.className = 'image-preview';
            
            // 创建图片元素
            const img = document.createElement('img');
            img.src = URL.createObjectURL(file);  // 创建本地对象URL
            img.onclick = () => showImagePreview(img.src);  // 点击放大
            
            // 创建删除按钮
            const removeBtn = createRemoveButton(index);
            
            // 组装元素
            imgPreview.appendChild(img);
            imgPreview.appendChild(removeBtn);
            previewItem.appendChild(imgPreview);
        } 
        // 非图片文件处理
        else {
            const filePreview = document.createElement('div');
            filePreview.className = 'file-preview';
            
            // 文件图标
            const icon = document.createElement('div');
            icon.className = 'file-icon';
            icon.innerHTML = getFileIcon(file);  // 根据文件类型获取对应图标
            
            // 文件信息
            const info = document.createElement('div');
            info.className = 'file-info';
            info.innerHTML = `
                <div class="file-name">${escapeHtml(file.name)}</div>
                <div class="file-size">${formatFileSize(file.size)}</div>
            `;
            
            // 删除按钮
            const removeBtn = createRemoveButton(index);
            
            // 组装元素
            filePreview.appendChild(icon);
            filePreview.appendChild(info);
            filePreview.appendChild(removeBtn);
            previewItem.appendChild(filePreview);
        }

        return previewItem;
    }

    
     //创建文件删除按钮
     // @param {number} index - 文件索引
     // @returns {HTMLElement} 删除按钮元素
     
    function createRemoveButton(index) {
        const btn = document.createElement('button');
        btn.className = 'remove-file';
        btn.innerHTML = '&times;';  // 使用×图标
        btn.addEventListener('click', (e) => {
            e.stopPropagation();  // 阻止事件冒泡
            filesToSend.splice(index, 1);  // 从数组中移除文件
            renderPreview();  // 重新渲染预览
        });
        return btn;
    }

    // ==================== 5. 图片预览功能 ====================
    
    
     //显示图片预览模态框
     // @param {string} src - 图片URL
     
    function showImagePreview(src) {
        previewedImage.src = src;
        imagePreviewModal.style.display = 'flex';  // 显示模态框
    }

    
     // 隐藏图片预览模态框
     
    function hideImagePreview() {
        imagePreviewModal.style.display = 'none';
    }

    // 点击关闭按钮隐藏预览
    closePreview.addEventListener('click', hideImagePreview);
    
    // 点击模态框空白处也隐藏预览
    imagePreviewModal.addEventListener('click', function(e) {
        if (e.target === imagePreviewModal) {
            hideImagePreview();
        }
    });

    // ==================== 6. 工具函数 ====================

    
     //格式化文件大小
     //@param {number} bytes - 文件大小（字节）
     // @returns {string} 格式化后的字符串（如"1.23 MB"）
     
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    
    //根据文件扩展名获取对应的FontAwesome图标
     //@param {File} file - 文件对象
     //@returns {string} HTML图标标签
     
    function getFileIcon(file) {
        const ext = file.name.split('.').pop().toLowerCase();
        const iconMap = {
            pdf: 'fa-file-pdf',
            doc: 'fa-file-word',
            docx: 'fa-file-word',
            xls: 'fa-file-excel',
            xlsx: 'fa-file-excel',
            ppt: 'fa-file-powerpoint',
            pptx: 'fa-file-powerpoint',
            zip: 'fa-file-archive',
            rar: 'fa-file-archive',
            mp3: 'fa-file-audio',
            mp4: 'fa-file-video'
        };
        return `<i class="fas ${iconMap[ext] || 'fa-file'}"></i>`;
    }

    
      //HTML特殊字符转义（防止XSS攻击）
      //@param {string} unsafe - 原始字符串
      //@returns {string} 转义后的安全字符串
     
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    
      //显示临时通知消息
      //@param {string} message - 要显示的消息内容
     
    function showToast(message) {
        const toast = document.createElement('div');
        toast.className = 'toast-message';
        toast.textContent = message;
        document.body.appendChild(toast);
        
        // 3秒后自动消失
        setTimeout(() => {
            toast.classList.add('fade-out');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }


});

// 发送文件的函数（不再绑定 send-button 事件）
window.sendFiles = async function() {
    if (!window.currentChat || !window.currentChat.id) {
        alert('请先选择聊天对象');
        return;
    }
    // 发送所有附件
    for (const file of filesToSend) {
        ws.send(JSON.stringify({
            type: "file_info",
            filename: file.name,
            filesize: file.size,
            receiver_id: Number(window.currentChat.id), // 强制转为数字
            receiver_type: window.currentChat.type
        }));
        const arrayBuffer = await file.arrayBuffer();
        ws.send(arrayBuffer);
    }
    // 清空附件
    filesToSend.length = 0;
    renderPreview();
    
    // 新增：发送成功后刷新消息列表
    refreshMessages();
};

// 新增：全局刷新函数
function refreshMessages() {
    // 确保当前有活跃的聊天窗口
    if (window.currentChat && window.currentChat.id) {
        // 延迟100ms确保消息已保存到数据库
        setTimeout(() => {
            // 调用加载消息的函数
            if (typeof loadChatMessages === 'function') {
                loadChatMessages();
                console.log('文件发送成功后刷新消息列表');
            }
        }, 100);
    }
}