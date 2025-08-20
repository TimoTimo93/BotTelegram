// index.js
require('dotenv').config();
const TelegramBot = require('node-telegram-bot-api');
const { initDatabase, findOrCreateUser } = require('./database.js');

// Khởi tạo Database trước tiên
initDatabase();

const token = process.env.TELEGRAM_BOT_TOKEN;
if (!token) {
    console.error('Lỗi: Vui lòng cung cấp TELEGRAM_BOT_TOKEN trong file .env');
    process.exit(1);
}

const bot = new TelegramBot(token, { polling: true });
console.log('✅ Bot đã khởi động và đang lắng nghe...');

bot.on('polling_error', (error) => {
    console.log(`[Lỗi Polling]: ${error.code} - ${error.message}`);
});

const mainMenu = {
    reply_markup: {
        keyboard: [
            ['🚀 Đăng bài Mới', '🗓️ Quản lý Bài đăng'],
            ['🔗 Quản lý Kết nối', '⚙️ Cài đặt & Trợ giúp']
        ],
        resize_keyboard: true,
        one_time_keyboard: false
    }
};

const handleInteraction = async (msg) => {
    const chatId = msg.chat.id;
    const userId = msg.from.id;
    const firstName = msg.from.first_name;
    const username = msg.from.username;

    try {
        // Luôn nhận diện và ghi danh người dùng
        const user = findOrCreateUser(userId, firstName, username);
        console.log(`Tương tác từ người dùng: ${user.first_name} (ID: ${user.user_id})`);
    } catch (error) {
        console.error('Lỗi database khi xử lý người dùng:', error);
    }

    // Chỉ xử lý tin nhắn văn bản cho menu
    if (msg.text) {
        if (msg.text === '/start' || msg.text === '/menu') {
            return bot.sendMessage(chatId, `Chào mừng trở lại, ${firstName}!`, mainMenu);
        }

        switch (msg.text) {
            case '🚀 Đăng bài Mới':
                bot.sendMessage(chatId, 'OK, gửi video để đăng bài nhé.');
                break;
            case '🗓️ Quản lý Bài đăng':
                bot.sendMessage(chatId, 'Chức năng này sẽ sớm được cập nhật.');
                break;
            case '🔗 Quản lý Kết nối':
                bot.sendMessage(chatId, 'Chức năng này sẽ sớm được cập nhật.');
                break;
            case '⚙️ Cài đặt & Trợ giúp':
                bot.sendMessage(chatId, 'Chức năng này sẽ sớm được cập nhật.');
                break;
        }
    }
};

bot.on('message', handleInteraction);
