import sqlite3

class DatabaseManager:
    def __init__(self, db_name='chat_app.db'):
        self.db_name = db_name
        self.initialize_database()

    def initialize_database(self):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    sender_id INTEGER NOT NULL,
                    sender_name TEXT NOT NULL,
                    receiver_id INTEGER NOT NULL,
                    receiver_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_sent INTEGER DEFAULT 0,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    group_name TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contact_id INTEGER NOT NULL,
                    contact_name TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """)

            conn.commit()
        except sqlite3.Error as e:
            print(f"数据库初始化错误: {e}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def save_user(self, user_id, username, password):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO users (id, username, password) VALUES (?, ?, ?)",
                (user_id, username, password)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"保存用户错误: {e}")
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def save_message(self, user_id, sender_id, sender_name, receiver_id, receiver_type, content, timestamp, is_sent=0):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO messages 
                (user_id, sender_id, sender_name, receiver_id, receiver_type, content, timestamp, is_sent) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, sender_id, sender_name, receiver_id, receiver_type, content, timestamp, is_sent)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"保存消息错误: {e}")
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def get_messages(self, user_id, receiver_id, receiver_type, limit=50):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(
                """SELECT sender_id, sender_name, content, timestamp, is_sent 
                FROM messages 
                WHERE user_id=? AND receiver_id=? AND receiver_type=?
                ORDER BY timestamp DESC LIMIT ?""",
                (user_id, receiver_id, receiver_type, limit)
            )
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"获取消息错误: {e}")
            return []
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def save_contact(self, user_id, contact_id, contact_name):
        if not user_id or not contact_id or not contact_name:
            return False
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO contacts (user_id, contact_id, contact_name) VALUES (?, ?, ?)",
                (user_id, contact_id, contact_name)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"保存联系人错误: {e}")
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def get_contacts(self, user_id):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT contact_id, contact_name FROM contacts WHERE user_id=?",
                (user_id,)
            )
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"获取联系人错误: {e}")
            return []
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def save_group(self, user_id, group_id, group_name):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO groups (user_id, group_id, group_name) VALUES (?, ?, ?)",
                (user_id, group_id, group_name)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"保存群组错误: {e}")
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def get_groups(self, user_id):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT group_id, group_name FROM groups WHERE user_id=?",
                (user_id,)
            )
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"获取群组错误: {e}")
            return []
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()