// server.js
const express = require('express');
const { createOAuthClient, getTokensFromCode, saveToken } = require('./auth.js');

const app = express();
const port = 3000; // Cổng mà server sẽ lắng nghe

// Route này Google sẽ gọi lại sau khi người dùng đăng nhập thành công
app.get('/oauth2callback', async (req, res) => {
    const code = req.query.code;
    const state = JSON.parse(Buffer.from(req.query.state, 'base64').toString());
    const userId = state.userId;

    if (!code || !userId) {
        return res.status(400).send('Thiếu thông tin xác thực.');
    }

    try {
        const oAuth2Client = await createOAuthClient();
        const tokens = await getTokensFromCode(oAuth2Client, code);
        await saveToken(userId, 'google', tokens);

        res.send(`
            <html><body>
                <h1>✅ Xác thực thành công!</h1>
                <p>Bây giờ bạn có thể quay lại và sử dụng bot.</p>
                <a href="https://t.me/ChucNangBot">Mở Telegram</a>
            </body></html>
        `);
    } catch (error) {
        console.error('Lỗi khi lấy token:', error);
        res.status(500).send('Đã xảy ra lỗi, vui lòng thử lại.');
    }
});

app.listen(port, () => {
    console.log(`🚀 Web server cho OAuth đang lắng nghe tại cổng ${port}`);
});
