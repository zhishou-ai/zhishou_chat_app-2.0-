-- 启用外键支持（SQLite默认关闭）
PRAGMA foreign_keys = ON;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL CHECK(length(username) >= 3),
    password_hash TEXT NOT NULL,
    email TEXT UNIQUE,
    avatar TEXT DEFAULT 'default.jpg',
    status TEXT CHECK(status IN ('online','offline','busy','invisible')) DEFAULT 'offline',
    last_active INTEGER, -- 使用UNIX时间戳存储
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    UNIQUE(username)
);

-- 好友关系表
CREATE TABLE IF NOT EXISTS friends (
    relation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user1_id INTEGER NOT NULL,
    user2_id INTEGER NOT NULL,
    relation_type TEXT CHECK(relation_type IN ('friend','blocked')) DEFAULT 'friend',
    status TEXT CHECK(status IN ('pending','accepted','rejected')) NOT NULL DEFAULT 'pending',
    action_user_id INTEGER,
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    UNIQUE(user1_id, user2_id),
    CHECK(user1_id < user2_id),
    FOREIGN KEY (user1_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (user2_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 群组表
CREATE TABLE IF NOT EXISTS groups (
    group_id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name TEXT NOT NULL,
    creator_id INTEGER NOT NULL,
    description TEXT,
    announcement TEXT,
    avatar TEXT DEFAULT 'group_default.jpg',
    max_members INTEGER DEFAULT 500,
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    FOREIGN KEY (creator_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 群组成员表
CREATE TABLE IF NOT EXISTS group_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role TEXT CHECK(role IN ('owner','admin','member')) DEFAULT 'member',
    is_muted BOOLEAN NOT NULL DEFAULT 0,
    joined_at INTEGER DEFAULT (strftime('%s', 'now')),
    UNIQUE(group_id, user_id),
    FOREIGN KEY (group_id) REFERENCES groups(group_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 消息表
CREATE TABLE IF NOT EXISTS messages (
    msg_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL,
    receiver_type TEXT CHECK(receiver_type IN ('private','group')) NOT NULL,
    receiver_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_type TEXT CHECK(content_type IN ('text','image','file','video')) DEFAULT 'text',
    file_url TEXT,
    is_read BOOLEAN DEFAULT 0,
    status TEXT CHECK(status IN ('sent','delivered','deleted')) NOT NULL DEFAULT 'sent',
    recalled_at INTEGER,
    recalled_by INTEGER,
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 消息已读表
CREATE TABLE IF NOT EXISTS message_reads (
    read_id INTEGER PRIMARY KEY AUTOINCREMENT,
    msg_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    read_at INTEGER DEFAULT (strftime('%s', 'now')),
    UNIQUE(msg_id, user_id),
    FOREIGN KEY (msg_id) REFERENCES messages(msg_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 登录尝试记录表
CREATE TABLE IF NOT EXISTS login_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    last_attempt INTEGER, -- UNIX时间戳
    UNIQUE(username)
);

-- IP与用户关联表
CREATE TABLE IF NOT EXISTS ip_id (
    ip TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    PRIMARY KEY (ip),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 创建索引提高查询性能
CREATE INDEX IF NOT EXISTS idx_friends_user1 ON friends(user1_id);
CREATE INDEX IF NOT EXISTS idx_friends_user2 ON friends(user2_id);
CREATE INDEX IF NOT EXISTS idx_group_members_group ON group_members(group_id);
CREATE INDEX IF NOT EXISTS idx_group_members_user ON group_members(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_messages_receiver ON messages(receiver_type, receiver_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);