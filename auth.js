// auth.js
const fs = require('fs').promises;
const { google } = require('googleapis');
const { saveToken, getToken } = require('./database.js');
const { OAuth2Client } = require('google-auth-library');

const CREDENTIALS_PATH = './credentials.json';
const SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/drive.file'
];

async function createOAuthClient() {
    const content = await fs.readFile(CREDENTIALS_PATH);
    const keys = JSON.parse(content);
    const { client_id, client_secret, redirect_uris } = keys.web;
    return new google.auth.OAuth2(client_id, client_secret, redirect_uris[0]);
}

async function getAuthUrl(oAuth2Client, userId) {
    return oAuth2Client.generateAuthUrl({
        access_type: 'offline',
        scope: SCOPES,
        // Mã hóa userId vào state để nhận lại sau khi xác thực
        state: Buffer.from(JSON.stringify({ userId })).toString('base64')
    });
}

async function getTokensFromCode(oAuth2Client, code) {
    const { tokens } = await oAuth2Client.getToken(code);
    return tokens;
}

async function getAuthenticatedClient(userId) {
    const oAuth2Client = await createOAuthClient();
    const dbToken = await getToken(userId, 'google');

    if (dbToken && dbToken.refresh_token) {
        oAuth2Client.setCredentials({
            refresh_token: dbToken.refresh_token
        });
        // Tự động làm mới access_token nếu cần
        await oAuth2Client.getAccessToken();
        return oAuth2Client;
    }
    return null; // Trả về null nếu chưa có token
}

module.exports = { createOAuthClient, getAuthUrl, getTokensFromCode, saveToken, getAuthenticatedClient };
