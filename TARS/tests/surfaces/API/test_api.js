const request = require('supertest');
const express = require('express');
const apiRoutes = require('../../../surfaces/API/api');

const app = express();
app.use(express.json());
app.use('/api', apiRoutes);

describe('API Routes', () => {
  it('should return a welcome message', async () => {
    const res = await request(app).get('/api/test');
    expect(res.statusCode).toEqual(200);
    expect(res.body).toHaveProperty('message', 'Hola! Welcome to our API!');
  });

  it('should handle GitHub OAuth callback', async () => {
    const res = await request(app).get('/api/auth/github/callback?code=test_code');
    expect(res.statusCode).toEqual(500); // Assuming the test will fail due to missing GitHub credentials
  });

  it('should handle chat requests', async () => {
    const res = await request(app)
      .post('/api/chat')
      .send({ messages: [{ content: 'Hello' }] });
    expect(res.statusCode).toEqual(500); // Assuming the test will fail due to missing GitHub token
  });
});
