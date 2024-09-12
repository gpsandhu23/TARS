const { Configuration, OpenAIApi } = require('openai');
const dotenv = require('dotenv');

dotenv.config();

const configuration = new Configuration({
  apiKey: process.env.OPENAI_API_KEY,
});

const openai = new OpenAIApi(configuration);

const openaiLlm = {
  async generateResponse(prompt) {
    try {
      const response = await openai.createCompletion({
        model: process.env.OPENAI_MODEL,
        prompt: prompt,
        max_tokens: 150,
        temperature: 0.7,
      });
      return response.data.choices[0].text.trim();
    } catch (error) {
      console.error('Error generating response:', error);
      return 'An error occurred while generating the response.';
    }
  },
};

module.exports = openaiLlm;
