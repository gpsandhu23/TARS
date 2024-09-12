const { App, ExpressReceiver } = require('@slack/bolt');
const { AgentManager } = require('../../graphs/agent');
const dotenv = require('dotenv');

dotenv.config();

class SlackBot {
  constructor() {
    this.agentManager = new AgentManager();
    this.receiver = new ExpressReceiver({
      signingSecret: process.env.SLACK_SIGNING_SECRET,
    });
    this.app = new App({
      token: process.env.SLACK_BOT_TOKEN,
      receiver: this.receiver,
    });

    this.app.message(async ({ message, say }) => {
      if (message.subtype && message.subtype === 'bot_message') {
        return;
      }

      const userMessage = message.text;
      const response = await this.agentManager.processUserTask(userMessage);
      await say(response);
    });
  }

  start() {
    this.receiver.app.listen(process.env.PORT || 3000, () => {
      console.log('Slack bot is running!');
    });
  }
}

module.exports = SlackBot;
