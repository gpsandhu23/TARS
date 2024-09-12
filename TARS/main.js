const express = require('express');
const { spawn } = require('child_process');
const SlackBot = require('./surfaces/slack/slack_app');
const apiRoutes = require('./surfaces/API/api');

const app = express();
const port = process.env.PORT || 3000;

app.use(express.json());
app.use('/api', apiRoutes);

const slackBot = new SlackBot();
slackBot.start();

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
