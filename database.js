// database.js
const Database = require('better-sqlite3');
const DB_PATH = './bot_database.sqlite';

let db;
try {
    // Kết nối tới file database SQLite, file sẽ được tự động tạo nếu chưa có
    db = new Database(DB_PATH);
    console.log('✅ Đã kết nối thành công tới database bằng better-sqlite3.');
} catch (err) {
    console.error('Lỗi khi kết nối database', err.message);
    throw err;
}

// Hàm khởi tạo, tạo bảng 'users' và 'connections' nếu chúng chưa tồn tại
const initDatabase = () => {
    const createUsersTable = `
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            username TEXT,
            plan_type TEXT DEFAULT 'free',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    `;
    const createConnectionsTable = `
        CREATE TABLE IF NOT EXISTS connections (
            connection_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            access_token TEXT,
            refresh_token TEXT,
            expiry_date INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        );
    `;
    db.exec(createUsersTable);
    db.exec(createConnectionsTable);
    console.log('Bảng "users" và "connections" đã sẵn sàng.');
};

/**
 * Tìm một người dùng bằng user_id. Nếu không có, tự động tạo mới.
 */
const findOrCreateUser = (userId, firstName, username) => {
    const selectSql = db.prepare("SELECT * FROM users WHERE user_id = ?");
    let user = selectSql.get(userId);

    if (!user) {
        const insertSql = db.prepare("INSERT INTO users (user_id, first_name, username) VALUES (?, ?, ?)");
        insertSql.run(userId, firstName, username);
        user = selectSql.get(userId); // Lấy lại thông tin người dùng vừa tạo
    }
    return user;
};


module.exports = { db, initDatabase, findOrCreateUser };
