// index.js (phiên bản hoàn chỉnh)
require('dotenv').config();
const TelegramBot = require('node-telegram-bot-api');
const fs = require('fs');
const { initDatabase, findOrCreateUser } = require('./database.js');
const { createOAuthClient, getAuthUrl, getAuthenticatedClient } = require('./auth.js');
// const { uploadVideo } = require('./youtubeUploader.js'); // Sẽ thêm lại sau

initDatabase();
const token = process.env.TELEGRAM_BOT_TOKEN;
const bot = new TelegramBot(token, { polling: true });
console.log('✅ Bot đã khởi động và đang lắng nghe...');

// ... (code xử lý lỗi polling, mainMenu giữ nguyên) ...

const handleInteraction = async (msg) => {
    const chatId = msg.chat.id;
    const userId = msg.from.id;
    const firstName = msg.from.first_name;
    const username = msg.from.username;

    const user = findOrCreateUser(userId, firstName, username);
    console.log(`Tương tác từ người dùng: ${user.first_name} (ID: ${user.user_id})`);

    if (msg.text) {
        if (msg.text === '/start' || msg.text === '/menu') {
            return bot.sendMessage(chatId, `Chào mừng trở lại, ${firstName}!`, mainMenu);
        }

        switch (msg.text) {
            case '🚀 Đăng bài Mới':
                bot.sendMessage(chatId, 'OK, gửi video để đăng bài nhé.');
                break;
            case '🔗 Quản lý Kết nối':
                const oAuth2Client = await createOAuthClient();
                const authUrl = await getAuthUrl(oAuth2Client, user.user_id);

                const connectionMenu = {
                    reply_markup: {
                        inline_keyboard: [
                            [{ text: 'Bắt đầu Kết nối Google', url: authUrl }]
                        ]
                    }
                };
                bot.sendMessage(chatId, 'Nhấn nút bên dưới để bắt đầu kết nối với tài khoản Google của bạn:', connectionMenu);
                break;
            // ... các case khác
        }
    }
};

bot.on('message', handleInteraction);
