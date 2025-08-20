// auth.js
const fs = require('fs').promises;
const { google } = require('googleapis');
const { saveToken, getToken } = require('./database.js');

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
        prompt: 'consent', // Luôn hỏi lại sự đồng ý để nhận refresh_token
        scope: SCOPES,
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
            refresh_token: dbToken.refresh_token,
            access_token: dbToken.access_token,
            expiry_date: dbToken.expiry_date
        });
        return oAuth2Client;
    }
    return null;
}

module.exports = { createOAuthClient, getAuthUrl, getTokensFromCode, getAuthenticatedClient, saveToken };
