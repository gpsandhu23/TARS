const express = require('express');
const axios = require('axios');
const { AgentManager } = require('../../graphs/agent');
const { github_oauth_settings } = require('../../config/config');
const { traceable } = require('langsmith');
const dotenv = require('dotenv');

dotenv.config();

const app = express();
app.use(express.json());

const agentManager = new AgentManager();

app.post('/chat', traceable('API Chat Endpoint'), async (req, res) => {
  const { messages } = req.body;
  const recentMessage = messages[messages.length - 1].content;

  const requestBody = {
    stream: true,
    messages: [{ role: 'user', content: recentMessage }],
    max_tokens: 5000,
    temperature: 0.5,
  };

  try {
    const response = await axios.post('https://api.githubcopilot.com/chat/completions', requestBody, {
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${req.headers['x-github-token']}`,
      },
    });

    res.status(response.status).json(response.data);
  } catch (error) {
    res.status(error.response.status).json(error.response.data);
  }
});

app.get('/auth/github/callback', async (req, res) => {
  const { code } = req.query;

  if (!code) {
    return res.status(400).json({ detail: "Missing 'code' in the callback request" });
  }

  try {
    const accessTokenResponse = await axios.post('https://github.com/login/oauth/access_token', {
      client_id: github_oauth_settings.client_id,
      client_secret: github_oauth_settings.client_secret,
      code,
    }, {
      headers: { Accept: 'application/json' },
    });

    const accessToken = accessTokenResponse.data.access_token;

    if (!accessToken) {
      return res.status(500).json({ detail: "Failed to exchange 'code' for an access token" });
    }

    const userInfoResponse = await axios.get('https://api.github.com/user', {
      headers: { Authorization: `token ${accessToken}` },
    });

    const userInfo = userInfoResponse.data;

    res.json({ status: 'success', user_info: userInfo, user_token: accessToken });
  } catch (error) {
    res.status(500).json({ detail: "Failed to validate access token or retrieve user information" });
  }
});

app.get('/test', (req, res) => {
  res.json({ message: 'Hola! Welcome to our API!' });
});

module.exports = app;
