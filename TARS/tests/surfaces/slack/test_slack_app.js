const { App, ExpressReceiver } = require('@slack/bolt');
const request = require('supertest');
const express = require('express');
const SlackBot = require('../../../surfaces/slack/slack_app');
const AgentManager = require('../../../graphs/agent');

jest.mock('@slack/bolt');
jest.mock('../../../graphs/agent');

describe('SlackBot', () => {
  let app;
  let agentManagerMock;
  let slackBot;

  beforeAll(() => {
    agentManagerMock = new AgentManager();
    AgentManager.mockImplementation(() => agentManagerMock);

    const receiver = new ExpressReceiver({ signingSecret: 'test-signing-secret' });
    app = express();
    app.use(receiver.app);

    slackBot = new SlackBot();
    slackBot.start();
  });

  it('should initialize Slack bot and handle incoming messages', async () => {
    const userMessage = 'Hello, Slack!';
    const botResponse = 'Hello, User!';

    agentManagerMock.processUserTask.mockResolvedValue(botResponse);

    const res = await request(app)
      .post('/slack/events')
      .send({
        type: 'event_callback',
        event: {
          type: 'message',
          text: userMessage,
          user: 'U123456',
          channel: 'C123456',
        },
      });

    expect(res.statusCode).toEqual(200);
    expect(agentManagerMock.processUserTask).toHaveBeenCalledWith(userMessage);
  });
});
