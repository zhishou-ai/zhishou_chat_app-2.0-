import asyncio
import websockets
import json
import time
import datetime
import logging
import os
from sql_program import DatabaseManager, AuthService, FriendService, GroupService, MessageService
from typing import Dict, List, Set, Optional

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("server.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChatServer:
    def __init__(self):
        self.db = DatabaseManager()
        self.auth = AuthService(self.db)
        self.friend_service = FriendService(self.db)
        self.group_service = GroupService(self.db)
        self.message_service = MessageService()
        
        self.online_users: Dict[int, websockets.WebSocketServerProtocol] = {}
        self.user_subscriptions: Dict[int, Set[int]] = {}
        self.pending_file_info = {}

    @staticmethod
    def json_serial(obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    async def broadcast_all_users(self):
        """向所有在线用户，发送所有用户列表，包含权限"""
        online_user_ids = list(self.online_users.keys())
        users = []
        user = self.db.execute_query("SELECT user_id, username, permission FROM users")
        if user:
            for uid in user:
                users.append({
                    "user_id": uid["user_id"],
                    "username": uid["username"],
                    "permission": uid.get("permission", "")
                })
        data = {
            "action": "all_users",
            "users": users
        }
        for uid in online_user_ids:
            await self.send_to_user(uid, data)

    async def handle_connection(self, websocket):
        logger.info(f"新客户端连接: {websocket.remote_address}")
        try:
            while True:
                message = await websocket.recv()
                if isinstance(message, bytes):
                    file_info = self.pending_file_info.get(websocket)
                    if file_info:
                        filename = file_info['filename']
                        receiver_id = file_info['receiver_id']
                        save_dir = "received_files"
                        os.makedirs(save_dir, exist_ok=True)
                        save_path = os.path.join(save_dir, filename)
                        logger.info(f"准备保存文件到: {save_dir}")
                        try:
                            with open(save_path, "wb") as f:
                                f.write(message)
                            logger.info(f"文件已保存到: {save_path}")
                            
                            # 获取发送者ID
                            sender_id = None
                            for uid, ws in self.online_users.items():
                                if ws == websocket:
                                    sender_id = uid
                                    break
                                    
                            if sender_id and receiver_id:
                                # 保存文件消息到数据库
                                self.message_service.send_message(
                                    sender_id=sender_id,
                                    receiver_type=file_info.get("receiver_type", "private"),
                                    receiver_id=receiver_id,
                                    content=filename,
                                    content_type="file",
                                    file_url=save_path  # 使用绝对路径
                                )
                                
                                # 发送文件信息通知给接收方
                            receiver_type = file_info.get("receiver_type", "private")
                            if receiver_type == "group":
                                # 获取群组成员
                                members = self.db.execute_query(
                                    "SELECT user_id FROM group_members WHERE group_id = %s",
                                    (receiver_id,)
                                )
                                for member in members:
                                    user_id = member['user_id']
                                    if user_id != sender_id and user_id in self.online_users:
                                        await self.send_to_user(user_id, {
                                            "action": "file_received",
                                            "filename": filename,
                                            "file_url": save_path,
                                            "sender_id": sender_id,
                                            "file_path": save_path
                                        })
                            else:
                                if receiver_id in self.online_users:
                                    await self.send_to_user(receiver_id, {
                                        "action": "file_received",
                                        "filename": filename,
                                        "file_url": save_path,
                                        "sender_id": sender_id,
                                        "file_path": save_path
                                    })
                                    
                            # 通知发送方文件已保存
                            await websocket.send(json.dumps({
                                "action": "file_saved",
                                "filename": filename,
                                "path": save_path
                            }))
                            
                        except Exception as e:
                            logger.error(f"保存文件失败: {e}", exc_info=True)
                        finally:
                            self.pending_file_info.pop(websocket, None)
                    else:
                        logger.warning("收到二进制数据但没有 file_info")
                else:
                    try:
                        data = json.loads(message)

                        if data.get("type") == "file_info":
                            self.pending_file_info[websocket] = {
                                "filename": data["filename"],
                                "filesize": data["filesize"],
                                "receiver_id": data.get("receiver_id"),
                                "receiver_type": data.get("receiver_type", "private")
                            }
                            await websocket.send(json.dumps({
                                "action": "file_info_received",
                                "filename": data["filename"]
                            }))
                            
                        else:
                            action = data.get("action")
                            if action == "login":
                                await self.handle_login(websocket, data)
                            elif action == "register":
                                await self.handle_register(websocket, data)
                            elif action == "web_online":
                                await self.web_online(websocket, data)
                            elif action == "send_message":
                                await self.handle_send_message(websocket, data)
                            elif action == "get_messages":
                                await self.handle_get_messages(websocket, data)
                            elif action == "create_group":
                                await self.handle_create_group(websocket, data)
                            elif action == "update_nickname":
                                await self.handle_update_nickname(websocket, data)
                            elif action == "logout":
                                await self.handle_disconnect(websocket)
                                return
                            elif action == "send_qunfamessage":
                                await self.handle_send_qunfamessage(websocket, data)
                                print("发群聊")
                            elif action == "get_online_users":
                                await self.broadcast_all_users()
                            elif action == "download_file":
                                filename = data.get("filename")
                                # 使用相对路径确保跨平台兼容性
                                base_dir = os.path.dirname(os.path.abspath(__file__))
                                file_path = os.path.join(base_dir, "received_files", filename)
                                
                                if os.path.exists(file_path):
                                    # 发送文件数据
                                    try:
                                        with open(file_path, "rb") as f:
                                            file_data = f.read()
                                        # 合并发送文件信息和数据
                                        # 使用base64编码传输二进制文件
                                        import base64
                                        file_data_base64 = base64.b64encode(file_data).decode('utf-8')
                                        await websocket.send(json.dumps({
                                            "action": "file_download_completed",
                                            "filename": filename,
                                            "file_data": file_data_base64
                                        }))
                                    except Exception as e:
                                        logger.error(f"发送文件失败: {e}")
                                        await self.send_error(websocket, f"发送文件失败: {str(e)}")
                                else:
                                    await self.send_error(websocket, "文件不存在")
                    except json.JSONDecodeError:
                        logger.warning("收到无法解析的消息")
        except websockets.exceptions.ConnectionClosedOK:
            logger.info(f"客户端正常断开: {websocket.remote_address}")
        except websockets.exceptions.ConnectionClosedError as e:
            logger.warning(f"客户端异常断开: {websocket.remote_address}, 原因: {e}")
        except Exception as e:
            logger.error(f"连接处理异常: {type(e).__name__}: {e}", exc_info=True)
        finally:
            await self.handle_disconnect(websocket)
            logger.info(f"连接清理完成: {websocket.remote_address}")

    async def send_error(self, websocket, message: str):
        await websocket.send(json.dumps({
            'action': 'error',
            'message': message
        }))


    async def handle_register(self, websocket, data):
        """处理用户注册请求，支持教师/学生注册"""
        try:
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            is_teacher = data.get('is_teacher', False)
            yanzheng = data.get('yanzheng', '').strip() if is_teacher else None

            if not username or not password:
                await self.send_error(websocket, '用户名和密码不能为空')
                return

            # 调用AuthService进行注册
            result = self.auth.register_user(
                username=username, 
                password=password,
                isteacher=is_teacher,
                yanzheng=yanzheng
            ) if 'is_teacher' in data else self.auth.register_user(username, password)

            # 关键修复：使用服务返回的实际权限
            response = {
                'action': 'register_response',
                'success': result['success'],
                "username": username,
                "user_id": result.get("user_id"),
                'permission': result.get('permission', 'student')  # 使用服务返回的权限
            }

            if result['success']:
                user_id = result.get('user_id')
                response['user_id'] = user_id  
                self.online_users[user_id] = websocket
                await self.broadcast_all_users()
            else:
                response['error'] = result.get('error', '注册失败')
            await websocket.send(json.dumps(response))
        except Exception as e:
            logger.error(f"注册处理出错: {e}", exc_info=True)
            await self.send_error(websocket, '注册过程中发生错误')

    # 修改 handle_login 函数
    async def handle_login(self, websocket, data):
        try:
            username = data.get('username')
            password = data.get('password', '').strip()
            if not username or not password:
                await self.send_error(websocket, '用户名和密码不能为空')
                return

            auth_result = self.auth.login_user(username, password)
            if not auth_result['success']:
                await self.send_error(websocket, auth_result.get('error', '登录失败'))
                return

            user_id = auth_result['user_id']
            if user_id in self.online_users:
                await self.send_error(websocket, '该用户已在线')
                return

            self.online_users[user_id] = websocket
            logger.info(f"User {user_id} logged in")
            await self.broadcast_all_users()
            await self.send_offline_messages(user_id)

            # 修复：在响应中添加permission字段
            response = {
                'action': 'login_response',
                'success': True,
                'user_id': user_id,
                'username': auth_result.get('username'),
                'permission': auth_result.get('permission')  # 关键修复：返回实际权限
            }
            
            await self.send_to_user(user_id, response)
            await self.send_friend_list(user_id)
            await self.send_group_list(user_id)
            await self.broadcast_all_users()
        except Exception as e:
            logger.error(f"登录处理出错: {e}", exc_info=True)
            await self.send_error(websocket, '登录过程中发生错误')
            
    async def web_online(self, websocket, data):
        user_id = data.get('user_id')
        if not user_id:
            logger.error("web_online 缺少 user_id")
            return
        self.online_users[user_id] = websocket
        await self.broadcast_all_users()

    async def send_friend_list(self, user_id):
        try:
            friends = self.friend_service.get_friends(user_id)
            if friends['success']:
                response = {
                    'action': 'friend_list',
                    'friends': friends['friends']
                }
                await self.send_to_user(user_id, response)
        except Exception as e:
            logger.error(f"发送好友列表出错: {e}", exc_info=True)

    async def send_group_list(self, user_id):
        try:
            groups = self.group_service.get_user_groups(user_id)
            if groups['success']:
                response = {
                    'action': 'group_list',
                    'groups': groups['groups']
                }
                await self.send_to_user(user_id, response)
        except Exception as e:
            logger.error(f"发送群组列表出错: {e}", exc_info=True)

    async def handle_disconnect(self, websocket):
        try:
            for user_id, ws in list(self.online_users.items()):
                if ws == websocket:
                    self.online_users.pop(user_id, None)
                    self.user_subscriptions.pop(user_id, None)
                    logger.info(f"User {user_id} disconnected")
                    await self.notify_friends_status(user_id, False)
                    await self.broadcast_all_users()
                    break
        except Exception as e:
            logger.error(f"断开连接处理出错: {e}", exc_info=True)

    async def notify_friends_status(self, user_id: int, is_online: bool):
        try:
            friends = self.friend_service.get_friends(user_id)
            if friends['success']:
                for friend in friends['friends']:
                    friend_id = friend['user_id']
                    if friend_id in self.online_users:
                        await self.send_to_user(friend_id, {
                            'action': 'friend_status',
                            'friend_id': user_id,
                            'is_online': is_online
                        })
        except Exception as e:
            logger.error(f"通知好友状态出错: {e}", exc_info=True)

    async def send_to_user(self, user_id: int, data: dict):
        try:
            ws = self.online_users.get(user_id)
            if ws and not ws.closed:
                await ws.send(json.dumps(data, default=self.json_serial))
            else:
                logger.warning(f"用户 {user_id} 的连接不存在或已关闭")
                if user_id in self.online_users:
                    self.online_users.pop(user_id, None)
                    self.user_subscriptions.pop(user_id, None)
                    await self.notify_friends_status(user_id, False)
        except Exception as e:
            logger.error(f"向用户 {user_id} 发送消息失败: {e}")
            if user_id in self.online_users:
                self.online_users.pop(user_id, None)
                self.user_subscriptions.pop(user_id, None)
                await self.notify_friends_status(user_id, False)

    async def send_offline_messages(self, user_id):
        try:
            private_messages = self.message_service.get_messages(
                user_id, "private", user_id, 1, 100
            )
            groups = self.group_service.get_user_groups(user_id)
            if groups['success']:
                for group in groups['groups']:
                    group_messages = self.message_service.get_messages(
                        user_id, "group", group['group_id'], 1, 100
                    )
                    if group_messages['success']:
                        response = {
                            'action': 'group_messages',
                            'group_id': group['group_id'],
                            'messages': group_messages['messages']
                        }
                        await self.send_to_user(user_id, response)
            if private_messages['success']:
                response = {
                    'action': 'private_messages',
                    'messages': private_messages['messages']
                }
                await self.send_to_user(user_id, response)
        except Exception as e:
            logger.error(f"发送离线消息出错: {e}", exc_info=True)

    async def handle_get_messages(self, websocket, data):
        try:
            user_id = data.get('user_id')
            receiver_type = data.get('receiver_type')
            receiver_id = data.get('receiver_id')
            page = data.get('page', 1)
            page_size = data.get('page_size', 20)
            if not user_id or not receiver_type or not receiver_id:
                await self.send_error(websocket, '缺少必要参数')
                return
            messages = self.message_service.get_messages(
                user_id, receiver_type, receiver_id, page, page_size
            )
            if messages['success']:
                sender_names = {}
                for msg in messages['messages']:
                    if msg['sender_id'] not in sender_names:
                        user = self.db.execute_query(
                            "SELECT username FROM users WHERE user_id = %s",
                            (msg['sender_id'],)
                        )
                        sender_names[msg['sender_id']] = user[0]['username'] if user else "未知用户"
                enriched_messages = []
                for msg in messages['messages']:
                    enriched_msg = dict(msg)
                    enriched_msg['sender_name'] = sender_names.get(msg['sender_id'], "未知用户")
                    enriched_messages.append(enriched_msg)
                response = {
                    'action': 'message_history',
                    'receiver_type': receiver_type,
                    'receiver_id': receiver_id,
                    'messages': enriched_messages
                }
                await self.send_to_user(user_id, response)
            else:
                await self.send_error(websocket, messages.get('error', '获取消息历史失败'))
        except Exception as e:
            logger.error(f"获取消息历史出错: {e}", exc_info=True)
            await self.send_error(websocket, '获取消息历史失败')

    async def handle_send_qunfamessage(self, websocket, data):
        try:
            sender_id = int(data.get('sender_id')) if data.get('sender_id') is not None else None
            receivers_id = list(data.get("receivers_id")) if data.get('receivers_id') is not None else None
            content = data.get('content', '').strip()
            if not sender_id or not receivers_id:
                await self.send_error(websocket, '缺少必要参数')
                return
            if not content:
                await self.send_error(websocket, '消息内容不能为空')
                return
            sql = "SELECT `permission` FROM users WHERE user_id = %s"
            a = self.db.execute_query(sql, (sender_id,))
            if not a or a[0].get("permission") != "teacher":
                await self.send_error(websocket, "没有足够权限")
            else:
                for receiver_id in receivers_id:
                    msg_data = {
                        "action": "send_message",
                        "sender_id": sender_id,
                        "receiver_type": "private",
                        "receiver_id": receiver_id,
                        "content": content
                    }
                    await self.handle_send_message(websocket, msg_data)  # 必须加 await

        except Exception as e:
            logger.error(f"发送群发消息处理出错: {e}", exc_info=True)
            await self.send_error(websocket, '发送消息失败')

    async def handle_send_message(self, websocket, data):
        try:
            sender_id = int(data.get('sender_id')) if data.get('sender_id') is not None else None
            receiver_id = int(data.get('receiver_id')) if data.get('receiver_id') is not None else None
            receiver_type = data.get('receiver_type')
            content = data.get('content', '').strip()
            if not sender_id or not receiver_type or not receiver_id:
                await self.send_error(websocket, '缺少必要参数')
                return
            if not content:
                await self.send_error(websocket, '消息内容不能为空')
                return
            result = self.message_service.send_message(
                sender_id, receiver_type, receiver_id, content
            )
            if not result['success']:
                await self.send_error(websocket, result.get('error', '发送消息失败'))
                return
            sender_name = None
            try:
                user = self.db.execute_query("SELECT username FROM users WHERE user_id = %s", (sender_id,))
                if user and len(user) > 0:
                    sender_name = user[0]['username']
            except Exception as e:
                logger.error(f"获取用户信息出错: {e}")
                sender_name = None
            message = {
                'message_id': result['msg_id'],
                'sender_id': sender_id,
                'receiver_type': receiver_type,
                'receiver_id': receiver_id,
                'content': content,
                'sender_name': sender_name,
                'timestamp': datetime.datetime.now().isoformat()
            }
            if receiver_type == 'private':
                await self.handle_private_message(sender_id, message)
            elif receiver_type == 'group':
                await self.handle_group_message(sender_id, message)
            else:
                await self.send_error(websocket, '无效的接收者类型')
        except Exception as e:
            logger.error(f"发送消息处理出错: {e}", exc_info=True)
            await self.send_error(websocket, '发送消息失败')

    async def handle_private_message(self, sender_id: int, message: dict):
        try:
            sender_name = self.db.execute_query(
                "SELECT username FROM users WHERE user_id = %s",
                (sender_id,)
            )
            receiver_id = message['receiver_id']
            response_to_sender = {
                'action': 'new_private_message',
                'message': {
                    'message_id': message['message_id'],
                    'sender_id': sender_id,
                    'receiver_id': receiver_id,
                    'content': message['content'],
                    'timestamp': message['timestamp'],
                    'sender_name': sender_name[0]['username'],
                    'direction': 'sent',
                    'content_type': message.get('content_type', 'text'),  # 添加内容类型
                    'file_url': message.get('file_url', '')  # 添加文件路径
                }
            }
            response_to_receiver = {
                'action': 'new_private_message',
                'message': {
                    'message_id': message['message_id'],
                    'sender_id': sender_id,
                    'receiver_id': receiver_id,
                    'content': message['content'],
                    'direction': 'received',
                    'timestamp': message['timestamp'],
                    'sender_name': sender_name[0]['username'],
                    'content_type': message.get('content_type', 'text'),  # 添加内容类型
                    'file_url': message.get('file_url', '')  # 添加文件路径
                }
            }
            await self.send_to_user(sender_id, response_to_sender)
            if receiver_id in self.online_users:
                await self.send_to_user(receiver_id, response_to_receiver)
        except Exception as e:
            logger.error(f"处理私聊消息出错: {e}", exc_info=True)

    async def handle_group_message(self, sender_id: int, message: dict):
        try:
            group_id = message['receiver_id']
            members = self.db.execute_query(
                "SELECT user_id FROM group_members WHERE group_id = %s",
                (group_id,)
            )
            for member in members:
                user_id = member['user_id']
                if user_id == sender_id:
                    continue
                if user_id in self.online_users:
                    response = {
                        'action': 'new_group_message',
                        'group_id': group_id,
                        'message': {
                            **message,
                            'is_self': False,
                            'content_type': message.get('content_type', 'text'),
                            'file_url': message.get('file_url', '')
                        }
                    }
                    await self.send_to_user(user_id, response)
        except Exception as e:
            logger.error(f"处理群聊消息出错: {e}", exc_info=True)

    async def handle_create_group(self, websocket, data):
        try:
            creator_id = data.get('creator_id')
            group_name = data.get('group_name', '').strip()
            initial_members = data.get('initial_members', [])
            if not creator_id or not group_name:
                await self.send_error(websocket, '缺少必要参数')
                return
            if len(group_name) < 3 or len(group_name) > 20:
                await self.send_error(websocket, '群组名称长度应在3到20个字符之间')
                return
            result = self.group_service.create_group(creator_id, group_name, initial_members)
            if not result['success']:
                await self.send_error(websocket, result.get('error', '创建群组失败'))
                return
            response = {
                'action': 'group_created',
                'group_id': result['group_id'],
                'group_name': result['group_name']
            }
            await self.send_to_user(creator_id, response)
            for member_id in initial_members:
                if member_id in self.online_users:
                    await self.send_to_user(member_id, {
                        'action': 'added_to_group',
                        'group_id': result['group_id'],
                        'group_name': result['group_name']
                    })
                    await self.send_group_list(member_id)
            await self.broadcast_all_users()
        except Exception as e:
            logger.error(f"创建群组处理出错: {e}", exc_info=True)
            await self.send_error(websocket, '创建群组失败')

    async def handle_update_nickname(self, websocket, data):
        try:
            user_name = data.get('username')
            new_nickname = data.get('nickname', '').strip()
            if not user_name or not new_nickname:
                await self.send_error(websocket, '缺少必要参数')
                return
            if len(new_nickname) < 3 or len(new_nickname) > 20:
                await self.send_error(websocket, '昵称过长或过短')
                return
            result = self.db.execute_update(
                "UPDATE users SET username = %s WHERE username = %s",
                (new_nickname, user_name)
            )
            user_id = self.db.execute_query("SELECT user_id FROM users WHERE username = %s", (user_name,))
            user_id = user_id[0]['user_id'] if user_id else None
            if result > 0:
                await self.send_to_user(user_id, {
                    'action': 'nickname_updated',
                    'success': True,
                    'new_nickname': new_nickname
                })
                friends = self.friend_service.get_friends(user_id)
                if friends['success']:
                    for friend in friends['friends']:
                        friend_id = friend['user_id']
                        if friend_id in self.online_users:
                            await self.send_to_user(friend_id, {
                                'action': 'friend_nickname_updated',
                                'friend_id': user_id,
                                'new_nickname': new_nickname
                            })
            else:
                await self.send_error(websocket, '更新昵称失败')
        except Exception as e:
            logger.error(f"更新昵称处理出错: {e}", exc_info=True)
            await self.send_error(websocket, '更新昵称失败')

# 启动服务器
async def main():
    server = ChatServer()
    async with websockets.serve(server.handle_connection, "0.0.0.0", 8765):
        logger.info("Chat server started on ws://0.0.0.0:8765")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())