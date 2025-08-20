// index.js (phiên bản có menu lựa chọn kết nối)
require('dotenv').config();
const TelegramBot = require('node-telegram-bot-api');
const { initDatabase, findOrCreateUser } = require('./database.js');
const { createOAuthClient, getAuthUrl } = require('./auth.js');

initDatabase();
const token = process.env.TELEGRAM_BOT_TOKEN;
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
    // Chỉ xử lý tin nhắn văn bản
    if (!msg.text) return;

    const chatId = msg.chat.id;
    const userId = msg.from.id;
    const firstName = msg.from.first_name;
    const username = msg.from.username;

    const user = findOrCreateUser(userId, firstName, username);
    console.log(`Tương tác từ người dùng: ${user.first_name} (ID: ${user.user_id})`);

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
            // --- PHẦN THAY ĐỔI ---
            // TODO: Lấy trạng thái kết nối từ DB để hiển thị (ví dụ: ✅ hoặc ❌)
            const connectionStatus = `Chọn nền tảng bạn muốn kết nối hoặc quản lý:`;
            
            const connectionChoiceMenu = {
                reply_markup: {
                    inline_keyboard: [
                        // Mỗi nút có một 'callback_data' riêng để chúng ta biết người dùng đã chọn gì
                        [{ text: '🔵 Google (YouTube & Drive)', callback_data: 'connect_google' }],
                        [{ text: '📘 Facebook', callback_data: 'connect_facebook' }],
                        [{ text: '🎵 TikTok', callback_data: 'connect_tiktok' }]
                    ]
                }
            };
            bot.sendMessage(chatId, connectionStatus, connectionChoiceMenu);
            break;
        case '⚙️ Cài đặt & Trợ giúp':
            bot.sendMessage(chatId, 'Chức năng này sẽ sớm được cập nhật.');
            break;
    }
};

bot.on('message', handleInteraction);

// --- BỘ LẮNG NGHE MỚI CHO CÁC NÚT BẤM NỘI TUYẾN (INLINE KEYBOARD) ---
bot.on('callback_query', async (callbackQuery) => {
    const msg = callbackQuery.message;
    const chatId = msg.chat.id;
    const userId = callbackQuery.from.id;
    const data = callbackQuery.data; // Dữ liệu từ nút bấm (vd: 'connect_google')

    // Gửi một phản hồi để nút bấm không hiển thị trạng thái "đang tải" mãi mãi
    bot.answerCallbackQuery(callbackQuery.id);

    switch (data) {
        case 'connect_google':
            try {
                const oAuth2Client = await createOAuthClient();
                const authUrl = await getAuthUrl(oAuth2Client, userId);
                
                const googleConnectionMenu = {
                    reply_markup: {
                        inline_keyboard: [
                            [{ text: 'Nhấn vào đây để Đăng nhập Google', url: authUrl }]
                        ]
                    }
                };
                bot.sendMessage(chatId, 'OK, hãy nhấn vào nút bên dưới để bắt đầu kết nối với tài khoản Google của bạn:', googleConnectionMenu);
            } catch (error) {
                console.error("Lỗi khi tạo link kết nối Google:", error);
                bot.sendMessage(chatId, "Đã có lỗi xảy ra, không thể tạo link kết nối.");
            }
            break;
        case 'connect_facebook':
            bot.sendMessage(chatId, 'Chức năng kết nối Facebook sẽ được phát triển trong thời gian tới.');
            break;
        case 'connect_tiktok':
            bot.sendMessage(chatId, 'Chức năng kết nối TikTok sẽ được phát triển trong thời gian tới.');
            break;
    }
});
